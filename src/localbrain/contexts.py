import sqlite3
from pathlib import Path, PurePosixPath
from typing import Optional

from .workstreams import utc_now


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
        ORDER BY CASE context_roots.source_type
                    WHEN 'folder' THEN 0 WHEN 'apple_notes' THEN 1 ELSE 2 END,
                 context_roots.label, context_roots.path
        """
    ).fetchall()
    home = Path.home()
    result = []
    for row in rows:
        item = dict(row)
        if item["source_type"] == "apple_notes":
            item["display_path"] = "Notes.app"
            item["exists_now"] = Path("/System/Applications/Notes.app").exists()
        else:
            path = Path(item["path"])
            try:
                item["display_path"] = "~/{}".format(path.relative_to(home))
            except ValueError:
                item["display_path"] = str(path)
            item["exists_now"] = (
                path.is_file() if item["source_type"] == "file" else path.is_dir()
            )
        result.append(item)
    return result


def list_context_roots(connection: sqlite3.Connection) -> list:
    return list_context_sources(connection)


def context_source_tree(connection: sqlite3.Connection, source_id: int) -> list:
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
                    **document,
                }
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
