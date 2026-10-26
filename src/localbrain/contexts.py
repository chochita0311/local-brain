import sqlite3
from pathlib import Path, PurePosixPath
from typing import Optional

from .atlassian_evidence import clear_context_root_evidence
from .markdown import render_markdown
from .markdown_references import MarkdownDocumentReference, MarkdownReferenceContext
from .path_display import home_relative_path
from .workstreams import utc_now


_SOURCE_ORDER = """
    context_roots.display_order IS NULL, context_roots.display_order,
    CASE context_roots.source_type WHEN 'folder' THEN 0 WHEN 'apple_notes' THEN 1 ELSE 2 END,
    context_roots.label, context_roots.path
"""


class ContextOrderConflict(ValueError):
    """The caller's source list no longer matches the saved order."""


def reorder_context_sources(connection, source_ids, expected_source_ids) -> None:
    current = [row[0] for row in connection.execute(
        "SELECT id FROM context_roots WHERE enabled = 1 ORDER BY " + _SOURCE_ORDER
    )]
    if expected_source_ids != current:
        raise ContextOrderConflict("목록이 변경되었습니다. 새 목록을 확인한 뒤 다시 이동해 주세요.")
    if (any(type(value) is not int for value in source_ids)
            or len(source_ids) != len(set(source_ids)) or set(source_ids) != set(current)):
        raise ValueError("등록된 Local Context 전체의 순서를 지정해 주세요.")
    connection.executemany(
        "UPDATE context_roots SET display_order = ? WHERE id = ?",
        enumerate(source_ids),
    )


def _canonical_directory(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.exists():
        raise ValueError("Folder does not exist")
    if not candidate.is_dir():
        raise ValueError("Local Context root must be a folder")
    return candidate.resolve()


def _canonical_file(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.exists():
        raise ValueError("File does not exist")
    if not candidate.is_file():
        raise ValueError("Local Context file must be a file")
    return candidate.resolve()


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def add_context_root(connection: sqlite3.Connection, path: str) -> int:
    candidate = _canonical_directory(path)
    existing = connection.execute(
        "SELECT id, enabled FROM context_roots WHERE path = ?", (str(candidate),)
    ).fetchone()
    for row in connection.execute(
        """
        SELECT id, path FROM context_roots
        WHERE enabled = 1 AND source_type = 'folder' AND path != ?
        """,
        (str(candidate),),
    ).fetchall():
        if _paths_overlap(candidate, Path(row["path"])):
            raise ValueError(
                "Folder overlaps an existing Local Context root: {}".format(row["path"])
            )
    now = utc_now()
    if existing:
        connection.execute(
            """
            UPDATE context_roots
            SET enabled = 1, label = ?, source_type = 'folder', readable = 1,
                status = 'ready', error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (candidate.name or str(candidate), now, existing["id"]),
        )
        return int(existing["id"])
    cursor = connection.execute(
        """
        INSERT INTO context_roots(path, label, source_type, updated_at)
        VALUES (?, ?, 'folder', ?)
        """,
        (str(candidate), candidate.name or str(candidate), now),
    )
    return int(cursor.lastrowid)


def add_context_file(connection: sqlite3.Connection, path: str) -> int:
    candidate = _canonical_file(path)
    for row in connection.execute(
        """
        SELECT path FROM context_roots
        WHERE enabled = 1 AND source_type = 'folder'
        """
    ).fetchall():
        if Path(row["path"]) in candidate.parents:
            raise ValueError(
                "File is already covered by Local Context folder: {}".format(
                    row["path"]
                )
            )
    now = utc_now()
    existing = connection.execute(
        "SELECT id FROM context_roots WHERE path = ?", (str(candidate),)
    ).fetchone()
    if existing:
        connection.execute(
            """
            UPDATE context_roots
            SET enabled = 1, label = ?, source_type = 'file', readable = 1,
                status = 'pending', error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (candidate.name, now, existing["id"]),
        )
        return int(existing["id"])
    cursor = connection.execute(
        """
        INSERT INTO context_roots(
            path, label, source_type, status, updated_at
        ) VALUES (?, ?, 'file', 'pending', ?)
        """,
        (str(candidate), candidate.name, now),
    )
    return int(cursor.lastrowid)


def add_apple_notes_source(connection: sqlite3.Connection) -> int:
    path = "apple-notes://default"
    now = utc_now()
    existing = connection.execute(
        "SELECT id FROM context_roots WHERE path = ?", (path,)
    ).fetchone()
    if existing:
        connection.execute(
            """
            UPDATE context_roots
            SET enabled = 1, label = 'Apple Notes', source_type = 'apple_notes',
                readable = 1, status = 'pending', error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (now, existing["id"]),
        )
        return int(existing["id"])
    cursor = connection.execute(
        """
        INSERT INTO context_roots(
            path, label, source_type, status, updated_at
        ) VALUES (?, 'Apple Notes', 'apple_notes', 'pending', ?)
        """,
        (path, now),
    )
    return int(cursor.lastrowid)


def remove_context_root(connection: sqlite3.Connection, root_id: int) -> None:
    row = connection.execute(
        "SELECT id FROM context_roots WHERE id = ? AND enabled = 1", (root_id,)
    ).fetchone()
    if not row:
        raise LookupError("Local Context root not found")
    clear_context_root_evidence(connection, root_id)
    connection.execute(
        """
        DELETE FROM search_index
        WHERE entity_type = 'document'
          AND entity_id IN (
              SELECT CAST(id AS TEXT) FROM context_documents
              WHERE context_root_id = ?
          )
        """,
        (root_id,),
    )
    connection.execute(
        """
        DELETE FROM source_files
        WHERE path IN (
            SELECT path FROM context_documents WHERE context_root_id = ?
        )
        """,
        (root_id,),
    )
    connection.execute(
        "UPDATE context_roots SET enabled = 0, updated_at = ? WHERE id = ?",
        (utc_now(), root_id),
    )


def list_context_sources(connection: sqlite3.Connection) -> list:
    rows = connection.execute(
        """
        SELECT context_roots.*,
               COUNT(context_documents.id) AS document_count,
               COALESCE(SUM(context_documents.size_bytes), 0) AS total_bytes,
               MAX(context_documents.mtime_ns) AS latest_mtime_ns
        FROM context_roots
        LEFT JOIN context_documents
          ON context_documents.context_root_id = context_roots.id
        WHERE context_roots.enabled = 1
        GROUP BY context_roots.id
        ORDER BY """ + _SOURCE_ORDER
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        if item["source_type"] == "apple_notes":
            item["display_path"] = "Notes.app"
            item["exists_now"] = Path("/System/Applications/Notes.app").exists()
        else:
            path = Path(item["path"])
            item["display_path"] = home_relative_path(path)
            item["exists_now"] = (
                path.is_file() if item["source_type"] == "file" else path.is_dir()
            )
        result.append(item)
    return result


def list_context_roots(connection: sqlite3.Connection) -> list:
    return list_context_sources(connection)


def context_source_tree(
    connection: sqlite3.Connection,
    source_id: int,
    selected_document_id: Optional[int] = None,
) -> list:
    documents = connection.execute(
        """
        SELECT id, title, relative_path, content_type
        FROM context_documents
        WHERE context_root_id = ?
        ORDER BY relative_path, title
        """,
        (source_id,),
    ).fetchall()
    root = {"directories": {}, "documents": []}
    for row in documents:
        parts = list(PurePosixPath(row["relative_path"]).parts)
        node = root
        for part in parts[:-1]:
            node = node["directories"].setdefault(
                part, {"directories": {}, "documents": []}
            )
        node["documents"].append(dict(row))

    def materialize(node: dict) -> list:
        entries = []
        for name, child in sorted(node["directories"].items()):
            entries.append(
                {
                    "kind": "directory",
                    "name": name,
                    "children": materialize(child),
                }
            )
        for document in sorted(
            node["documents"], key=lambda item: (item["title"], item["relative_path"])
        ):
            entries.append(
                {
                    "kind": "document",
                    "name": PurePosixPath(document["relative_path"]).name,
                    "contains_selected": document["id"] == selected_document_id,
                    **document,
                }
            )
        for entry in entries:
            if entry["kind"] == "directory":
                entry["contains_selected"] = any(
                    child["contains_selected"] for child in entry["children"]
                )
        return entries

    return materialize(root)


def get_context_root(
    connection: sqlite3.Connection, root_id: Optional[int]
) -> Optional[dict]:
    if root_id is None:
        return None
    row = connection.execute(
        "SELECT * FROM context_roots WHERE id = ? AND enabled = 1", (root_id,)
    ).fetchone()
    return dict(row) if row else None


def build_markdown_reference_context(
    connection: sqlite3.Connection, document_id: int
) -> Optional[MarkdownReferenceContext]:
    current = connection.execute(
        """
        SELECT context_documents.id, context_documents.context_root_id
        FROM context_documents
        JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.id = ?
          AND context_roots.enabled = 1
          AND context_roots.source_type = 'folder'
        """,
        (document_id,),
    ).fetchone()
    if not current:
        return None

    rows = connection.execute(
        """
        SELECT id, context_root_id, relative_path, title, body, content_type
        FROM context_documents
        WHERE context_root_id = ?
        ORDER BY relative_path, id
        """,
        (current["context_root_id"],),
    ).fetchall()
    documents = tuple(
        MarkdownDocumentReference(
            id=int(row["id"]),
            context_root_id=int(row["context_root_id"]),
            relative_path=row["relative_path"],
            title=row["title"],
            body=row["body"],
            content_type=row["content_type"],
        )
        for row in rows
    )
    return MarkdownReferenceContext(documents, int(current["id"]))


def context_document_preview(connection: sqlite3.Connection, document) -> dict:
    view = dict(document)
    reference_context = build_markdown_reference_context(connection, int(view["id"]))
    rendered = render_markdown(
        view["body"],
        reference_context=reference_context,
    )
    view["rendered_body"] = rendered.html
    view["render_state"] = rendered.state
    view["render_properties"] = rendered.properties
    return view


def context_document_reader(connection: sqlite3.Connection, document) -> dict:
    view = context_document_preview(connection, document)
    source = get_context_root(connection, view.get("context_root_id"))
    has_context_tree = bool(source and source["source_type"] == "folder")
    tree = (
        context_source_tree(connection, int(source["id"]), int(view["id"]))
        if has_context_tree
        else []
    )
    if source:
        source["document_count"] = connection.execute(
            "SELECT COUNT(*) FROM context_documents WHERE context_root_id = ?",
            (source["id"],),
        ).fetchone()[0]
        return_href = "/context?root={}&document={}".format(
            source["id"], view["id"]
        )
    else:
        return_href = "/context"
    return {
        "document": view,
        "context_source": source,
        "context_tree": tree,
        "has_context_tree": has_context_tree,
        "return_href": return_href,
    }
