import hashlib
import json
import mimetypes
import sqlite3
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from urllib.parse import quote

from ..atlassian_evidence import (
    document_evidence_source_fingerprint,
    evidence_scan_is_current,
    reconcile_document_evidence,
    reconcile_session_evidence,
    session_evidence_source_fingerprint,
)
from ..config import settings
from ..db import init_db, transaction
from ..usage import reconcile_usage_record_contract, store_usage_records
from .claude import CLAUDE_USAGE_CONTRACT_VERSION, parse_claude_session
from .codex import CODEX_USAGE_CONTRACT_VERSION, parse_codex_session
from .common import ParsedSession


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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _upsert_source(
    connection: sqlite3.Connection, kind: str, name: str, root: Path
) -> int:
    connection.execute(
        """
        INSERT INTO sources(kind, name, root_path)
        VALUES (?, ?, ?)
        ON CONFLICT(kind) DO UPDATE SET
            name = excluded.name,
            root_path = excluded.root_path,
            enabled = 1
        """,
        (kind, name, str(root)),
    )
    row = connection.execute(
        "SELECT id FROM sources WHERE kind = ?", (kind,)
    ).fetchone()
    return int(row["id"])


def _file_is_current(
    connection: sqlite3.Connection,
    source_id: int,
    path: Path,
    usage_contract_version: Optional[str] = None,
) -> bool:
    stat = path.stat()
    row = connection.execute(
        """
        SELECT size_bytes, mtime_ns, status, usage_contract_version
        FROM source_files WHERE source_id = ? AND path = ?
        """,
        (source_id, str(path)),
    ).fetchone()
    return bool(
        row
        and row["size_bytes"] == stat.st_size
        and row["mtime_ns"] == stat.st_mtime_ns
        and row["status"] == "ok"
        and (
            usage_contract_version is None
            or row["usage_contract_version"] == usage_contract_version
        )
    )


def _record_source_file(
    connection: sqlite3.Connection,
    source_id: int,
    path: Path,
    status: str = "ok",
    error: Optional[str] = None,
    usage_contract_version: Optional[str] = None,
    scanned_size_bytes: Optional[int] = None,
    scanned_mtime_ns: Optional[int] = None,
) -> None:
    stat = path.stat()
    size_bytes = stat.st_size if scanned_size_bytes is None else scanned_size_bytes
    mtime_ns = stat.st_mtime_ns if scanned_mtime_ns is None else scanned_mtime_ns
    connection.execute(
        """
        INSERT INTO source_files(
            source_id, path, size_bytes, mtime_ns, last_scanned_at, status, error,
            usage_contract_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id, path) DO UPDATE SET
            size_bytes = excluded.size_bytes,
            mtime_ns = excluded.mtime_ns,
            last_scanned_at = excluded.last_scanned_at,
            status = excluded.status,
            error = excluded.error,
            usage_contract_version = COALESCE(
                excluded.usage_contract_version,
                source_files.usage_contract_version
            )
        """,
        (
            source_id,
            str(path),
            size_bytes,
            mtime_ns,
            utc_now(),
            status,
            error,
            usage_contract_version,
        ),
    )


def _find_git_root(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    current = path if path.is_dir() else path.parent
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
        if candidate == Path.home():
            break
    return None


def _upsert_workspace(
    connection: sqlite3.Connection,
    cwd_raw: Optional[str],
    last_activity_at: Optional[str],
) -> Optional[int]:
    if not cwd_raw:
        return None
    path = Path(cwd_raw).expanduser()
    exists_now = path.exists()
    canonical = str(path.resolve()) if exists_now else str(path)
    git_root = _find_git_root(path)
    projects_root = Path.home() / "Projects"
    try:
        display_name = str(path.relative_to(projects_root))
    except ValueError:
        display_name = path.name or canonical

    connection.execute(
        """
        INSERT INTO workspaces(
            canonical_path, display_name, git_root, exists_now,
            last_activity_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(canonical_path) DO UPDATE SET
            display_name = excluded.display_name,
            git_root = excluded.git_root,
            exists_now = excluded.exists_now,
            last_activity_at = CASE
                WHEN workspaces.last_activity_at IS NULL THEN excluded.last_activity_at
                WHEN excluded.last_activity_at > workspaces.last_activity_at THEN excluded.last_activity_at
                ELSE workspaces.last_activity_at
            END,
            updated_at = excluded.updated_at
        """,
        (
            canonical,
            display_name,
            str(git_root) if git_root else None,
            int(exists_now),
            last_activity_at,
            utc_now(),
        ),
    )
    row = connection.execute(
        "SELECT id FROM workspaces WHERE canonical_path = ?", (canonical,)
    ).fetchone()
    return int(row["id"])


def _replace_search_item(
    connection: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    source_kind: str,
    title: str,
    body: str,
    path: str,
) -> None:
    connection.execute(
        "DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id),
    )
    connection.execute(
        "INSERT INTO search_index(entity_type, entity_id, source_kind, title, body, path) VALUES (?, ?, ?, ?, ?, ?)",
        (entity_type, entity_id, source_kind, title, body, path),
    )


def _remove_stale_sessions(
    connection: sqlite3.Connection, source_id: int, valid_paths: Iterable[Path]
) -> None:
    valid = {str(path) for path in valid_paths}
    rows = connection.execute(
        "SELECT id, source_path FROM sessions WHERE source_id = ?",
        (source_id,),
    ).fetchall()
    for row in rows:
        if row["source_path"] in valid:
            continue
        connection.execute(
            "DELETE FROM search_index WHERE entity_type = 'session' AND entity_id = ?",
            (str(row["id"]),),
        )
        connection.execute("DELETE FROM sessions WHERE id = ?", (row["id"],))
    scan_rows = connection.execute(
        """
        SELECT atlassian_evidence_scans.id,
               atlassian_evidence_scans.session_id,
               atlassian_evidence_scans.source_path
        FROM atlassian_evidence_scans
        JOIN sessions ON sessions.id = atlassian_evidence_scans.session_id
        WHERE sessions.source_id = ?
        """,
        (source_id,),
    ).fetchall()
    for row in scan_rows:
        if row["source_path"] in valid:
            continue
        connection.execute(
            """
            DELETE FROM atlassian_item_evidence
            WHERE session_id = ? AND source_path = ?
            """,
            (row["session_id"], row["source_path"]),
        )
        connection.execute(
            "DELETE FROM atlassian_evidence_scans WHERE id = ?",
            (row["id"],),
        )
    source_file_rows = connection.execute(
        "SELECT id, path FROM source_files WHERE source_id = ?", (source_id,)
    ).fetchall()
    for row in source_file_rows:
        if row["path"] not in valid:
            connection.execute("DELETE FROM source_files WHERE id = ?", (row["id"],))


def _store_session(
    connection: sqlite3.Connection,
    source_id: int,
    source_kind: str,
    parsed: ParsedSession,
    usage_contract_version: Optional[str] = None,
) -> int:
    workspace_id = _upsert_workspace(connection, parsed.cwd_raw, parsed.last_event_at)
    maintenance_run_id = parsed.maintenance_run_id
    if maintenance_run_id and not connection.execute(
        "SELECT 1 FROM maintenance_runs WHERE id = ?", (maintenance_run_id,)
    ).fetchone():
        maintenance_run_id = None
    user_count = sum(
        1
        for event in parsed.events
        if event.event_type == "message" and event.role == "user"
    )
    assistant_count = sum(
        1
        for event in parsed.events
        if event.event_type == "message" and event.role == "assistant"
    )
    connection.execute(
        """
        INSERT INTO sessions(
            source_id, workspace_id, external_id, source_path, cwd_raw, git_branch, title,
            started_at, ended_at, last_event_at, event_count,
            user_message_count, assistant_message_count, session_class, session_role,
            parent_external_id, parent_session_id,
            index_policy, maintenance_run_id, imported_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
        ON CONFLICT(source_id, external_id) DO UPDATE SET
            workspace_id = excluded.workspace_id,
            source_path = excluded.source_path,
            cwd_raw = excluded.cwd_raw,
            git_branch = excluded.git_branch,
            title = excluded.title,
            started_at = excluded.started_at,
            ended_at = excluded.ended_at,
            last_event_at = excluded.last_event_at,
            event_count = excluded.event_count,
            user_message_count = excluded.user_message_count,
            assistant_message_count = excluded.assistant_message_count,
            session_class = excluded.session_class,
            session_role = excluded.session_role,
            parent_external_id = excluded.parent_external_id,
            parent_session_id = NULL,
            index_policy = excluded.index_policy,
            maintenance_run_id = excluded.maintenance_run_id,
            imported_at = excluded.imported_at
        """,
        (
            source_id,
            workspace_id,
            parsed.external_id,
            parsed.source_path,
            parsed.cwd_raw,
            parsed.git_branch,
            parsed.title,
            parsed.started_at,
            parsed.ended_at,
            parsed.last_event_at,
            len(parsed.events) if parsed.index_policy == "full" else 0,
            user_count if parsed.index_policy == "full" else 0,
            assistant_count if parsed.index_policy == "full" else 0,
            parsed.session_class,
            parsed.session_role,
            parsed.parent_external_id,
            parsed.index_policy,
            maintenance_run_id,
            utc_now(),
        ),
    )
    session_row = connection.execute(
        "SELECT id FROM sessions WHERE source_id = ? AND external_id = ?",
        (source_id, parsed.external_id),
    ).fetchone()
    session_id = int(session_row["id"])
    store_usage_records(
        connection,
        source_id,
        session_id,
        parsed.usage_records,
        workspace_id=workspace_id,
        normalizer_version=(
            usage_contract_version
            or (
                CLAUDE_USAGE_CONTRACT_VERSION
                if source_kind == "claude"
                else CODEX_USAGE_CONTRACT_VERSION
                if source_kind == "codex"
                else "legacy-v1"
            )
        ),
    )
    connection.execute("DELETE FROM activity_events WHERE session_id = ?", (session_id,))
    connection.execute(
        "DELETE FROM search_index WHERE entity_type = 'session' AND entity_id = ?",
        (str(session_id),),
    )
    if parsed.index_policy == "full":
        connection.executemany(
            """
            INSERT INTO activity_events(
                id, session_id, sequence, occurred_at, event_type, role, text,
                tool_name, source_line
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    event.event_id,
                    session_id,
                    event.sequence,
                    event.occurred_at,
                    event.event_type,
                    event.role,
                    event.text,
                    event.tool_name,
                    event.source_line,
                )
                for event in parsed.events
            ],
        )
        body = "\n".join(event.text for event in parsed.events if event.text)
        if parsed.session_role == "primary":
            _replace_search_item(
                connection,
                "session",
                str(session_id),
                source_kind,
                parsed.title,
                body,
                parsed.cwd_raw or parsed.source_path,
            )
    return session_id


def _claude_parent_source_path(source_path: str) -> Optional[str]:
    path = Path(source_path)
    if path.parent.name != "subagents":
        return None
    return str(path.parent.parent.with_suffix(".jsonl"))


def _reconcile_session_parents(
    connection: sqlite3.Connection, source_id: int, source_kind: str
) -> None:
    rows = connection.execute(
        """
        SELECT id, external_id, source_path, session_class, session_role,
               parent_external_id, index_policy, maintenance_run_id
        FROM sessions WHERE source_id = ?
        """,
        (source_id,),
    ).fetchall()
    by_external_id = {row["external_id"]: row for row in rows}
    by_source_path = {row["source_path"]: row for row in rows}
    by_id = {row["id"]: row for row in rows}
    candidate_parents = {}
    normalized_parent_ids = {}

    for row in rows:
        if row["session_role"] != "subsession":
            connection.execute(
                """
                UPDATE sessions
                SET parent_external_id = NULL, parent_session_id = NULL
                WHERE id = ?
                """,
                (row["id"],),
            )
            continue
        parent = by_external_id.get(row["parent_external_id"])
        if not parent and source_kind == "claude":
            parent_path = _claude_parent_source_path(row["source_path"])
            parent = by_source_path.get(parent_path) if parent_path else None
        if not parent or parent["id"] == row["id"]:
            continue
        candidate_parents[row["id"]] = parent["id"]
        normalized_parent_ids[row["id"]] = parent["external_id"]

    def relation_is_safe(child_id: int) -> bool:
        seen = {child_id}
        current = candidate_parents.get(child_id)
        while current is not None:
            if current in seen:
                return False
            seen.add(current)
            current = candidate_parents.get(current)
        return True

    for row in rows:
        if row["session_role"] != "subsession":
            continue
        parent_id = candidate_parents.get(row["id"])
        if parent_id is None or not relation_is_safe(row["id"]):
            connection.execute(
                "UPDATE sessions SET parent_session_id = NULL WHERE id = ?",
                (row["id"],),
            )
            continue
        connection.execute(
            """
            UPDATE sessions
            SET parent_external_id = ?, parent_session_id = ?
            WHERE id = ?
            """,
            (normalized_parent_ids[row["id"]], parent_id, row["id"]),
        )
        parent = by_id[parent_id]
        if parent["session_class"] == "maintenance":
            connection.execute(
                """
                UPDATE sessions
                SET session_class = 'maintenance', index_policy = 'metadata_only',
                    maintenance_run_id = NULL, event_count = 0,
                    user_message_count = 0, assistant_message_count = 0
                WHERE id = ?
                """,
                (row["id"],),
            )
            connection.execute(
                "DELETE FROM activity_events WHERE session_id = ?", (row["id"],)
            )
            connection.execute(
                "DELETE FROM search_index WHERE entity_type = 'session' AND entity_id = ?",
                (str(row["id"]),),
            )


def _scan_session_source(
    connection: sqlite3.Connection,
    source_kind: str,
    name: str,
    root: Path,
    parser,
    usage_contract_version: str,
    force: bool = False,
) -> Tuple[int, int, int]:
    source_id = _upsert_source(connection, source_kind, name, root)
    imported = skipped = failed = 0
    if not root.exists():
        return imported, skipped, failed

    paths = sorted(root.rglob("*.jsonl"))
    contract_repair_required = bool(
        connection.execute(
            """
            SELECT 1 FROM source_files
            WHERE source_id = ?
              AND COALESCE(usage_contract_version, '') != ?
            LIMIT 1
            """,
            (source_id, usage_contract_version),
        ).fetchone()
    )
    if contract_repair_required:
        connection.execute("SAVEPOINT source_usage_contract_repair")
    _remove_stale_sessions(connection, source_id, paths)
    expected_usage_record_ids = set()
    repair_errors = []

    for path in paths:
        current_stat = path.stat()
        evidence_source_fingerprint = session_evidence_source_fingerprint(
            source_id=source_id,
            source_path=str(path),
            size_bytes=current_stat.st_size,
            mtime_ns=current_stat.st_mtime_ns,
        )
        if not force and not contract_repair_required and _file_is_current(
            connection, source_id, path, usage_contract_version
        ):
            session_row = connection.execute(
                """
                SELECT sessions.id
                FROM atlassian_evidence_scans
                JOIN sessions
                  ON sessions.id = atlassian_evidence_scans.session_id
                WHERE sessions.source_id = ?
                  AND atlassian_evidence_scans.source_path = ?
                """,
                (source_id, str(path)),
            ).fetchone()
            if session_row and evidence_scan_is_current(
                connection,
                session_id=int(session_row["id"]),
                source_path=str(path),
                source_fingerprint=evidence_source_fingerprint,
            ):
                skipped += 1
                continue
        try:
            scanned_stat = current_stat
            parsed = parser(path)
            session_id = _store_session(
                connection,
                source_id,
                source_kind,
                parsed,
                usage_contract_version=usage_contract_version,
            )
            reconcile_session_evidence(
                connection,
                session_id=session_id,
                source_path=str(path),
                source_fingerprint=evidence_source_fingerprint,
                candidates=parsed.url_evidence,
            )
            _record_source_file(
                connection,
                source_id,
                path,
                usage_contract_version=usage_contract_version,
                scanned_size_bytes=scanned_stat.st_size,
                scanned_mtime_ns=scanned_stat.st_mtime_ns,
            )
            expected_usage_record_ids.update(record.usage_record_id for record in parsed.usage_records)
            imported += 1
        except Exception as exc:
            if contract_repair_required:
                repair_errors.append((path, str(exc)))
            else:
                _record_source_file(connection, source_id, path, "error", str(exc))
            failed += 1
    if contract_repair_required and failed:
        connection.execute("ROLLBACK TO source_usage_contract_repair")
        connection.execute("RELEASE source_usage_contract_repair")
        imported = 0
        for path, error in repair_errors:
            _record_source_file(connection, source_id, path, "error", error)
    elif contract_repair_required:
        try:
            reconcile_usage_record_contract(
                connection, source_id, expected_usage_record_ids
            )
            connection.execute("RELEASE source_usage_contract_repair")
        except Exception:
            connection.execute("ROLLBACK TO source_usage_contract_repair")
            connection.execute("RELEASE source_usage_contract_repair")
            raise
    _reconcile_session_parents(connection, source_id, source_kind)
    connection.execute(
        "UPDATE sources SET last_scanned_at = ? WHERE id = ?", (utc_now(), source_id)
    )
    return imported, skipped, failed


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
            utc_now(),
        ),
    )
    document_id = int(
        connection.execute(
            "SELECT id FROM context_documents WHERE path = ?", (path,)
        ).fetchone()["id"]
    )
    _replace_search_item(
        connection,
        "document",
        str(document_id),
        "context",
        title,
        body,
        path,
    )
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
        connection.execute("DELETE FROM context_documents WHERE id = ?", (row["id"],))


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
    if not force and _file_is_current(connection, source_id, path):
        document = connection.execute(
            """
            SELECT id, content_hash FROM context_documents
            WHERE context_root_id = ? AND path = ?
            """,
            (root_row["id"], str(path)),
        ).fetchone()
        if document and evidence_scan_is_current(
            connection,
            document_id=int(document["id"]),
            source_fingerprint=document_evidence_source_fingerprint(
                document["content_hash"]
            ),
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
            (error, utc_now(), utc_now(), root_row["id"]),
        )
        return 0, 0, 0
    stat = path.stat()
    title = _document_title(path, body) if path.suffix.lower() == ".md" else path.stem
    workspace_id = _upsert_workspace(
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
    reconcile_document_evidence(
        connection,
        document_id=document_id,
        source_fingerprint=document_evidence_source_fingerprint(
            hashlib.sha256(body.encode("utf-8")).hexdigest()
        ),
        body=body,
    )
    _record_source_file(connection, source_id, path)
    now = utc_now()
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
    result = subprocess.run(
        ["/usr/bin/osascript", "-l", "JavaScript", "-e", APPLE_NOTES_SCRIPT],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Apple Notes could not be read")
    notes = json.loads(result.stdout or "[]")
    valid_paths = set()
    imported = 0
    for note in notes:
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
        source_fingerprint = document_evidence_source_fingerprint(content_hash)
        if not evidence_scan_is_current(
            connection,
            document_id=document_id,
            source_fingerprint=source_fingerprint,
        ):
            reconcile_document_evidence(
                connection,
                document_id=document_id,
                source_fingerprint=source_fingerprint,
                body=body,
            )
        imported += 1
    _remove_context_source_documents(connection, root_row["id"], valid_paths)
    now = utc_now()
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
) -> Tuple[int, int, int]:
    source_id = _upsert_source(
        connection, "context", "Local Contexts", settings.context_root
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
            except Exception as exc:
                failed += 1
                now = utc_now()
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
            now = utc_now()
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

        paths = [
            path
            for path in sorted(root.rglob("*.md"))
            if not any(
                part.startswith(".") or part in IGNORED_CONTEXT_DIRECTORIES
                for part in path.relative_to(root).parts
            )
        ]
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
            connection.execute(
                "DELETE FROM context_documents WHERE id = ?", (row["id"],)
            )
            connection.execute(
                "DELETE FROM source_files WHERE source_id = ? AND path = ?",
                (source_id, row["path"]),
            )

        for path in paths:
            if not force and _file_is_current(connection, source_id, path):
                document = connection.execute(
                    """
                    SELECT id, content_hash FROM context_documents
                    WHERE context_root_id = ? AND path = ?
                    """,
                    (root_row["id"], str(path)),
                ).fetchone()
                if document and evidence_scan_is_current(
                    connection,
                    document_id=int(document["id"]),
                    source_fingerprint=document_evidence_source_fingerprint(
                        document["content_hash"]
                    ),
                ):
                    skipped += 1
                    continue
            try:
                body = path.read_text(encoding="utf-8", errors="replace")
                stat = path.stat()
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                relative_path = str(path.relative_to(root))
                title = _document_title(path, body)
                workspace_id = _upsert_workspace(
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
                        utc_now(),
                    ),
                )
                document_row = connection.execute(
                    """
                    SELECT id, content_hash FROM context_documents
                    WHERE path = ?
                    """,
                    (str(path),),
                ).fetchone()
                _replace_search_item(
                    connection,
                    "document",
                    str(document_row["id"]),
                    "context",
                    title,
                    body,
                    str(path),
                )
                reconcile_document_evidence(
                    connection,
                    document_id=int(document_row["id"]),
                    source_fingerprint=document_evidence_source_fingerprint(
                        document_row["content_hash"]
                    ),
                    body=body,
                )
                _record_source_file(connection, source_id, path)
                imported += 1
            except Exception as exc:
                _record_source_file(connection, source_id, path, "error", str(exc))
                failed += 1
        now = utc_now()
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
        "UPDATE sources SET last_scanned_at = ? WHERE id = ?", (utc_now(), source_id)
    )
    return imported, skipped, failed


def scan_context_root(
    connection: sqlite3.Connection, root_id: int, force: bool = False
) -> Tuple[int, int, int]:
    return _scan_context_documents(connection, force=force, root_id=root_id)


def _scan_session_sources(
    connection: sqlite3.Connection, force: bool = False
) -> Dict[str, Dict[str, int]]:
    report: Dict[str, Dict[str, int]] = {}
    for key, values in (
        (
            "claude",
            _scan_claude_source(connection, force),
        ),
        (
            "codex",
            _scan_session_source(
                connection,
                "codex",
                "Codex",
                settings.codex_root,
                parse_codex_session,
                CODEX_USAGE_CONTRACT_VERSION,
                force,
            ),
        ),
    ):
        report[key] = {
            "imported": values[0],
            "skipped": values[1],
            "failed": values[2],
        }
    return report


def _scan_claude_source(
    connection: sqlite3.Connection, force: bool = False
) -> Tuple[int, int, int]:
    return _scan_session_source(
        connection,
        "claude",
        "Claude Code",
        settings.claude_root,
        parse_claude_session,
        CLAUDE_USAGE_CONTRACT_VERSION,
        force,
    )


def scan_claude_sessions(force: bool = False) -> Dict[str, int]:
    init_db()
    with transaction() as connection:
        values = _scan_claude_source(connection, force=force)
    return {"imported": values[0], "skipped": values[1], "failed": values[2]}


def scan_codex_sessions(force: bool = False) -> Dict[str, int]:
    init_db()
    with transaction() as connection:
        values = _scan_session_source(
            connection,
            "codex",
            "Codex",
            settings.codex_root,
            parse_codex_session,
            CODEX_USAGE_CONTRACT_VERSION,
            force,
        )
    return {"imported": values[0], "skipped": values[1], "failed": values[2]}


def scan_session_sources(force: bool = False) -> Dict[str, Dict[str, int]]:
    init_db()
    with transaction() as connection:
        return _scan_session_sources(connection, force=force)


def scan_all(force: bool = False) -> Dict[str, Dict[str, int]]:
    init_db()
    with transaction() as connection:
        report = _scan_session_sources(connection, force=force)
        values = _scan_context_documents(connection, force=force)
        report["context"] = {
            "imported": values[0],
            "skipped": values[1],
            "failed": values[2],
        }
    return report
