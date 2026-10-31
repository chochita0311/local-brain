"""Context readers and persistence within the caller transaction."""

import hashlib
import json
import mimetypes
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote
from localbrain.resources.catalog import bind_document
from localbrain.ingest import extensions
from . import control, storage


IGNORED_CONTEXT_DIRECTORIES = {
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
}


TEXT_FILE_EXTENSIONS = {
    ".cfg", ".conf", ".csv", ".html", ".ini", ".java", ".js", ".json",
    ".kt", ".log", ".md", ".properties", ".py", ".rst", ".sh", ".sql",
    ".toml", ".ts", ".txt", ".xml", ".yaml", ".yml",
}


APPLE_NOTES_SCRIPT = r"""
const Notes = Application('Notes');
const results = [];

function text(value) {
  return value === undefined || value === null ? '' : String(value);
}

function visitFolder(accountName, folder, parentNames) {
  const folderName = text(folder.name()) || 'Notes';
  const folderNames = parentNames.concat([folderName]);
  const notes = folder.notes();
  notes.forEach((note) => {
    let body = '';
    try { body = text(note.plaintext()); }
    catch (_error) {
      try { body = text(note.body()); } catch (_ignored) { body = ''; }
    }
    let modifiedAt = null;
    try { modifiedAt = new Date(note.modificationDate()).toISOString(); }
    catch (_error) { modifiedAt = null; }
    results.push({
      id: text(note.id()),
      account: accountName,
      folders: folderNames,
      title: text(note.name()) || 'Untitled Note',
      body: body,
      modified_at: modifiedAt,
    });
  });
  try {
    folder.folders().forEach((child) => visitFolder(accountName, child, folderNames));
  } catch (_error) {}
}

Notes.accounts().forEach((account) => {
  const accountName = text(account.name()) || 'Notes';
  account.folders().forEach((folder) => visitFolder(accountName, folder, []));
});
JSON.stringify(results);
"""


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _plain_text(value: str) -> str:
    if "<" not in value or ">" not in value:
        return value
    parser = _HTMLTextExtractor()
    parser.feed(value)
    return "\n".join(part.strip() for part in parser.parts if part.strip())


def _document_title(path: Path, body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("-", " ").replace("_", " ")


def _upsert_context_document(
    connection: sqlite3.Connection,
    source_id: int,
    context_root_id: int,
    path: str,
    relative_path: str,
    title: str,
    body: str,
    size_bytes: int,
    mtime_ns: int,
    content_type: str,
    workspace_id: Optional[int] = None,
) -> int:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    connection.execute(
        """
        INSERT INTO context_documents(
            source_id, context_root_id, workspace_id, path, relative_path,
            title, body, content_type, size_bytes, mtime_ns, content_hash,
            imported_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            source_id = excluded.source_id,
            context_root_id = excluded.context_root_id,
            workspace_id = excluded.workspace_id,
            relative_path = excluded.relative_path,
            title = excluded.title,
            body = excluded.body,
            content_type = excluded.content_type,
            size_bytes = excluded.size_bytes,
            mtime_ns = excluded.mtime_ns,
            content_hash = excluded.content_hash,
            imported_at = excluded.imported_at
        """,
        (
            source_id,
            context_root_id,
            workspace_id,
            path,
            relative_path,
            title,
            body,
            content_type,
            size_bytes,
            mtime_ns,
            digest,
            storage.utc_now(),
        ),
    )
    document_id = int(
        connection.execute(
            "SELECT id FROM context_documents WHERE path = ?", (path,)
        ).fetchone()["id"]
    )
    storage._replace_search_item(
        connection,
        "document",
        str(document_id),
        "context",
        title,
        body,
        path,
    )
    bind_document(connection, document_id)
    return document_id


def _remove_context_source_documents(
    connection: sqlite3.Connection, context_root_id: int, valid_paths: set
) -> None:
    rows = connection.execute(
        "SELECT id, path FROM context_documents WHERE context_root_id = ?",
        (context_root_id,),
    ).fetchall()
    for row in rows:
        if row["path"] in valid_paths:
            continue
        connection.execute(
            "DELETE FROM search_index WHERE entity_type = 'document' AND entity_id = ?",
            (str(row["id"]),),
        )
        storage._delete_source_owner(
            connection, document_id=int(row["id"])
        )


def _read_context_file(path: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    extension = path.suffix.lower()
    media_type = mimetypes.guess_type(path.name)[0]
    if extension in TEXT_FILE_EXTENSIONS or (media_type or "").startswith("text/"):
        body = path.read_text(encoding="utf-8", errors="replace")
        content_type = "text/markdown" if extension == ".md" else (media_type or "text/plain")
        return body, content_type, None
    if extension == ".pdf":
        result = subprocess.run(
            ["/usr/bin/mdls", "-raw", "-name", "kMDItemTextContent", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        body = result.stdout.strip()
        if result.returncode == 0 and body and body != "(null)":
            return body, "application/pdf+text", None
        return None, None, "PDF text is not available from the local Spotlight index"
    return None, None, "Unsupported or unreadable file type"


def _scan_context_file(
    connection: sqlite3.Connection,
    source_id: int,
    root_row: sqlite3.Row,
    force: bool = False,
) -> Tuple[int, int, int]:
    path = Path(root_row["path"])
    if not path.is_file():
        raise FileNotFoundError("Context file does not exist: {}".format(path))
    if not force and storage._file_is_current(connection, source_id, path):
        document = connection.execute(
            """
            SELECT id, content_hash FROM context_documents
            WHERE context_root_id = ? AND path = ?
            """,
            (root_row["id"], str(path)),
        ).fetchone()
        if document and extensions.document_is_current(
            connection,
            document_id=int(document["id"]),
            content_hash=document["content_hash"],
        ):
            return 0, 1, 0
    body, content_type, error = _read_context_file(path)
    if body is None or content_type is None:
        _remove_context_source_documents(connection, root_row["id"], set())
        connection.execute(
            """
            UPDATE context_roots
            SET readable = 0, status = 'unreadable', error = ?,
                last_scanned_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (error, storage.utc_now(), storage.utc_now(), root_row["id"]),
        )
        return 0, 0, 0
    stat = path.stat()
    title = _document_title(path, body) if path.suffix.lower() == ".md" else path.stem
    workspace_id = storage._upsert_workspace(
        connection,
        str(path.parent),
        datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    )
    document_id = _upsert_context_document(
        connection,
        source_id,
        root_row["id"],
        str(path),
        path.name,
        title,
        body,
        stat.st_size,
        stat.st_mtime_ns,
        content_type,
        workspace_id,
    )
    extensions.document_indexed(
        connection,
        document_id=document_id,
        content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        body=body,
    )
    storage._record_source_file(connection, source_id, path)
    now = storage.utc_now()
    connection.execute(
        """
        UPDATE context_roots
        SET readable = 1, status = 'ready', error = NULL,
            last_scanned_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (now, now, root_row["id"]),
    )
    return 1, 0, 0


def _safe_virtual_component(value: str) -> str:
    cleaned = " ".join((value or "").replace("/", "_").split())
    return cleaned or "Untitled"


def _scan_apple_notes(
    connection: sqlite3.Connection, source_id: int, root_row: sqlite3.Row
) -> Tuple[int, int, int]:
    with subprocess.Popen(
        ["/usr/bin/osascript", "-l", "JavaScript", "-e", APPLE_NOTES_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        deadline = time.monotonic() + 120
        try:
            while True:
                control._check_scan_cancelled()
                try:
                    stdout, stderr = process.communicate(timeout=0.5)
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Apple Notes could not be read within 120 seconds") from None
        except BaseException:
            process.kill()
            process.communicate()
            raise
    if process.returncode != 0:
        raise RuntimeError(stderr.strip() or "Apple Notes could not be read")
    notes = json.loads(stdout or "[]")
    valid_paths = set()
    imported = 0
    for note in notes:
        control._check_scan_cancelled()
        note_id = str(note.get("id") or "").strip()
        if not note_id:
            continue
        virtual_path = "apple-notes://note/{}".format(quote(note_id, safe=""))
        valid_paths.add(virtual_path)
        title = str(note.get("title") or "Untitled Note").strip()
        components = [_safe_virtual_component(str(note.get("account") or "Notes"))]
        components.extend(
            _safe_virtual_component(str(folder)) for folder in note.get("folders") or []
        )
        suffix = hashlib.sha256(note_id.encode("utf-8")).hexdigest()[:8]
        relative_path = "/".join(
            components + ["{} [{}].note".format(_safe_virtual_component(title), suffix)]
        )
        modified_at = note.get("modified_at")
        try:
            modified = datetime.fromisoformat(
                str(modified_at).replace("Z", "+00:00")
            )
            mtime_ns = int(modified.timestamp() * 1_000_000_000)
        except (TypeError, ValueError):
            mtime_ns = 0
        body = _plain_text(str(note.get("body") or ""))
        document_id = _upsert_context_document(
            connection,
            source_id,
            root_row["id"],
            virtual_path,
            relative_path,
            title,
            body,
            len(body.encode("utf-8")),
            mtime_ns,
            "application/x-apple-note",
        )
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        source_fingerprint = content_hash
        if not extensions.document_is_current(
            connection,
            document_id=document_id,
            content_hash=source_fingerprint,
        ):
            extensions.document_indexed(
                connection,
                document_id=document_id,
                content_hash=source_fingerprint,
                body=body,
            )
        imported += 1
    _remove_context_source_documents(connection, root_row["id"], valid_paths)
    now = storage.utc_now()
    connection.execute(
        """
        UPDATE context_roots
        SET readable = 1, status = 'ready', error = NULL,
            last_scanned_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (now, now, root_row["id"]),
    )
    return imported, 0, 0


def _scan_context_documents(
    connection: sqlite3.Connection,
    force: bool = False,
    root_id: Optional[int] = None,
    *,
    config,
) -> Tuple[int, int, int]:
    source_id = storage._upsert_source(
        connection,
        storage._context_source_id(connection),
        "context",
        "Local Contexts",
        config.context_root,
    )
    imported = skipped = failed = 0
    params = []
    where = "WHERE enabled = 1"
    if root_id is not None:
        where += " AND id = ?"
        params.append(root_id)
    roots = connection.execute(
        "SELECT * FROM context_roots {} ORDER BY path".format(where), tuple(params)
    ).fetchall()
    if root_id is not None and not roots:
        raise LookupError("Local Context root not found")

    for root_row in roots:
        control._check_scan_cancelled()
        if root_row["source_type"] in {"file", "apple_notes"}:
            try:
                if root_row["source_type"] == "file":
                    values = _scan_context_file(
                        connection, source_id, root_row, force=force
                    )
                else:
                    values = _scan_apple_notes(connection, source_id, root_row)
                imported += values[0]
                skipped += values[1]
                failed += values[2]
            except InterruptedError:
                raise
            except Exception as exc:
                failed += 1
                now = storage.utc_now()
                connection.execute(
                    """
                    UPDATE context_roots
                    SET readable = 0, status = 'error', error = ?,
                        last_scanned_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (str(exc)[-2000:], now, now, root_row["id"]),
                )
            continue

        root = Path(root_row["path"])
        if not root.is_dir():
            failed += 1
            now = storage.utc_now()
            connection.execute(
                """
                UPDATE context_roots
                SET readable = 0, status = 'missing', error = ?,
                    last_scanned_at = ?, updated_at = ?
                WHERE id = ?
                """,
                ("Folder does not exist", now, now, root_row["id"]),
            )
            continue

        paths = []
        for path in root.rglob("*.md"):
            control._check_scan_cancelled()
            if not any(part.startswith(".") or part in IGNORED_CONTEXT_DIRECTORIES
                       for part in path.relative_to(root).parts):
                paths.append(path)
        paths.sort()
        valid_paths = {str(path) for path in paths}
        existing = connection.execute(
            "SELECT id, path FROM context_documents WHERE context_root_id = ?",
            (root_row["id"],),
        ).fetchall()
        for row in existing:
            if row["path"] in valid_paths:
                continue
            connection.execute(
                "DELETE FROM search_index WHERE entity_type = 'document' AND entity_id = ?",
                (str(row["id"]),),
            )
            storage._delete_source_owner(
                connection, document_id=int(row["id"])
            )
            connection.execute(
                "DELETE FROM source_files WHERE source_id = ? AND path = ?",
                (source_id, row["path"]),
            )

        for path in paths:
            control._check_scan_cancelled()
            if not force and storage._file_is_current(connection, source_id, path):
                document = connection.execute(
                    """
                    SELECT id, content_hash FROM context_documents
                    WHERE context_root_id = ? AND path = ?
                    """,
                    (root_row["id"], str(path)),
                ).fetchone()
                if document and extensions.document_is_current(
                    connection,
                    document_id=int(document["id"]),
                    content_hash=document["content_hash"],
                ):
                    skipped += 1
                    continue
            try:
                body = path.read_text(encoding="utf-8", errors="replace")
                stat = path.stat()
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                relative_path = str(path.relative_to(root))
                title = _document_title(path, body)
                workspace_id = storage._upsert_workspace(
                    connection,
                    str(path.parent),
                    datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                )
                connection.execute(
                    """
                    INSERT INTO context_documents(
                        source_id, context_root_id, workspace_id, path, relative_path,
                        title, body, size_bytes, mtime_ns, content_hash, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        source_id = excluded.source_id,
                        context_root_id = excluded.context_root_id,
                        workspace_id = excluded.workspace_id,
                        relative_path = excluded.relative_path,
                        title = excluded.title,
                        body = excluded.body,
                        size_bytes = excluded.size_bytes,
                        mtime_ns = excluded.mtime_ns,
                        content_hash = excluded.content_hash,
                        imported_at = excluded.imported_at
                    """,
                    (
                        source_id,
                        root_row["id"],
                        workspace_id,
                        str(path),
                        relative_path,
                        title,
                        body,
                        stat.st_size,
                        stat.st_mtime_ns,
                        digest,
                        storage.utc_now(),
                    ),
                )
                document_row = connection.execute(
                    """
                    SELECT id, content_hash FROM context_documents
                    WHERE path = ?
                    """,
                    (str(path),),
                ).fetchone()
                storage._replace_search_item(
                    connection,
                    "document",
                    str(document_row["id"]),
                    "context",
                    title,
                    body,
                    str(path),
                )
                bind_document(connection, int(document_row["id"]))
                extensions.document_indexed(
                    connection,
                    document_id=int(document_row["id"]),
                    content_hash=document_row["content_hash"],
                    body=body,
                )
                storage._record_source_file(connection, source_id, path)
                imported += 1
            except Exception as exc:
                storage._record_source_file(connection, source_id, path, "error", str(exc))
                failed += 1
        now = storage.utc_now()
        connection.execute(
            """
            UPDATE context_roots
            SET readable = 1, status = 'ready', error = NULL,
                last_scanned_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (now, now, root_row["id"]),
        )
    connection.execute(
        "UPDATE sources SET last_scanned_at = ? WHERE id = ?", (storage.utc_now(), source_id)
    )
    return imported, skipped, failed
