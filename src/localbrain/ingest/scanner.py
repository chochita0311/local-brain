import hashlib
import json
import mimetypes
import sqlite3
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple
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
from ..session_sources import (
    SessionSourceRegistration,
    load_and_reconcile_session_sources,
)
from ..session_references import (
    SessionReferenceLookupCache,
    clear_session_reference_source,
    finalize_session_references,
    mark_session_reference_error,
    reconcile_session_references,
    session_reference_scan_is_current,
)
from ..usage import (
    UsagePersistenceCache,
    reconcile_usage_record_contract,
    store_usage_records,
)
from .claude import (
    CLAUDE_SESSION_CONTRACT_VERSION,
    CLAUDE_USAGE_CONTRACT_VERSION,
    parse_claude_session,
)
from .codex import (
    CODEX_SESSION_CONTRACT_VERSION,
    CODEX_USAGE_CONTRACT_VERSION,
    parse_codex_session,
)
from .common import ParsedSession, REFERENCE_EXTRACTOR_VERSION, stable_id


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

ScanProgressCallback = Callable[[Dict[str, Any]], None]

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


def _emit_scan_progress(
    progress: Optional[ScanProgressCallback], event: Dict[str, Any]
) -> None:
    if progress is None:
        return
    try:
        progress(event)
    except Exception:
        return


def _upsert_source(
    connection: sqlite3.Connection,
    source_key: str,
    provider_kind: str,
    name: str,
    root: Path,
) -> int:
    existing = connection.execute(
        "SELECT id, provider_kind FROM sources WHERE kind = ?", (source_key,)
    ).fetchone()
    if existing and existing["provider_kind"] != provider_kind:
        raise ValueError(
            "Source key {!r} is already bound to provider {!r}".format(
                source_key, existing["provider_kind"]
            )
        )
    connection.execute(
        """
        INSERT INTO sources(kind, provider_kind, name, root_path)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(kind) DO UPDATE SET
            name = excluded.name,
            root_path = excluded.root_path
        """,
        (source_key, provider_kind, name, str(root)),
    )
    row = connection.execute(
        "SELECT id FROM sources WHERE kind = ?", (source_key,)
    ).fetchone()
    return int(row["id"])


def _source_file_row_is_current(
    row: Optional[sqlite3.Row],
    stat,
    usage_contract_version: Optional[str] = None,
    reference_contract_version: Optional[str] = None,
    session_contract_version: Optional[str] = None,
) -> bool:
    return bool(
        row
        and row["size_bytes"] == stat.st_size
        and row["mtime_ns"] == stat.st_mtime_ns
        and row["status"] == "ok"
        and (
            usage_contract_version is None
            or row["usage_contract_version"] == usage_contract_version
        )
        and (
            reference_contract_version is None
            or row["reference_contract_version"]
            == reference_contract_version
        )
        and (
            session_contract_version is None
            or row["session_contract_version"] == session_contract_version
        )
    )


def _file_is_current(
    connection: sqlite3.Connection,
    source_id: int,
    path: Path,
    usage_contract_version: Optional[str] = None,
    reference_contract_version: Optional[str] = None,
    session_contract_version: Optional[str] = None,
) -> bool:
    stat = path.stat()
    row = connection.execute(
        """
        SELECT size_bytes, mtime_ns, status, session_contract_version,
               usage_contract_version, reference_contract_version
        FROM source_files WHERE source_id = ? AND path = ?
        """,
        (source_id, str(path)),
    ).fetchone()
    return _source_file_row_is_current(
        row,
        stat,
        usage_contract_version,
        reference_contract_version,
        session_contract_version,
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
    session_id: Optional[int] = None,
    reference_contract_version: Optional[str] = None,
    session_contract_version: Optional[str] = None,
) -> None:
    stat = path.stat()
    size_bytes = stat.st_size if scanned_size_bytes is None else scanned_size_bytes
    mtime_ns = stat.st_mtime_ns if scanned_mtime_ns is None else scanned_mtime_ns
    connection.execute(
        """
        INSERT INTO source_files(
            source_id, session_id, path, size_bytes, mtime_ns,
            last_scanned_at, status, error, usage_contract_version,
            reference_contract_version, session_contract_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id, path) DO UPDATE SET
            session_id = COALESCE(excluded.session_id, source_files.session_id),
            size_bytes = excluded.size_bytes,
            mtime_ns = excluded.mtime_ns,
            last_scanned_at = excluded.last_scanned_at,
            status = excluded.status,
            error = excluded.error,
            usage_contract_version = COALESCE(
                excluded.usage_contract_version,
                source_files.usage_contract_version
            ),
            reference_contract_version = COALESCE(
                excluded.reference_contract_version,
                source_files.reference_contract_version
            ),
            session_contract_version = COALESCE(
                excluded.session_contract_version,
                source_files.session_contract_version
            )
        """,
        (
            source_id,
            session_id,
            str(path),
            size_bytes,
            mtime_ns,
            utc_now(),
            status,
            error,
            usage_contract_version,
            reference_contract_version,
            session_contract_version,
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
    reference_rows = connection.execute(
        """
        SELECT session_id, path
        FROM source_files
        WHERE source_id = ? AND session_id IS NOT NULL
        """,
        (source_id,),
    ).fetchall()
    valid_session_paths = {}
    for row in reference_rows:
        if row["path"] in valid:
            valid_session_paths.setdefault(int(row["session_id"]), []).append(
                row["path"]
            )
    rows = connection.execute(
        "SELECT id, source_path FROM sessions WHERE source_id = ?",
        (source_id,),
    ).fetchall()
    for row in rows:
        if row["source_path"] in valid:
            continue
        remaining_paths = valid_session_paths.get(int(row["id"]), [])
        if remaining_paths:
            connection.execute(
                "UPDATE sessions SET source_path = ? WHERE id = ?",
                (sorted(remaining_paths)[0], row["id"]),
            )
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
    for row in reference_rows:
        if row["path"] in valid:
            continue
        if connection.execute(
            "SELECT 1 FROM sessions WHERE id = ?", (row["session_id"],)
        ).fetchone():
            clear_session_reference_source(
                connection,
                session_id=int(row["session_id"]),
                source_path=row["path"],
            )


def _parsed_session_is_meaningful(parsed: ParsedSession) -> bool:
    return bool(parsed.events or parsed.usage_records)


def _session_eligibility_repair_required(
    connection: sqlite3.Connection, source_id: int
) -> bool:
    return bool(
        connection.execute(
            """
            SELECT 1
            FROM sessions
            WHERE source_id = ?
              AND index_policy = 'full'
              AND event_count = 0
              AND NOT EXISTS (
                  SELECT 1 FROM activity_events
                  WHERE activity_events.session_id = sessions.id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM usage_records
                  WHERE usage_records.session_id = sessions.id
              )
            LIMIT 1
            """,
            (source_id,),
        ).fetchone()
    )


def _remove_empty_session_candidates(
    connection: sqlite3.Connection,
    source_id: int,
    candidates: Iterable[Tuple[Path, ParsedSession]],
) -> None:
    for path, parsed in candidates:
        source_path = str(path)
        reference_source = connection.execute(
            """
            SELECT session_id FROM source_files
            WHERE source_id = ? AND path = ?
            """,
            (source_id, source_path),
        ).fetchone()
        if reference_source and reference_source["session_id"] is not None:
            clear_session_reference_source(
                connection,
                session_id=int(reference_source["session_id"]),
                source_path=source_path,
            )
        scan_rows = connection.execute(
            """
            SELECT atlassian_evidence_scans.id,
                   atlassian_evidence_scans.session_id
            FROM atlassian_evidence_scans
            JOIN sessions
              ON sessions.id = atlassian_evidence_scans.session_id
            WHERE sessions.source_id = ?
              AND atlassian_evidence_scans.source_path = ?
            """,
            (source_id, source_path),
        ).fetchall()
        for scan_row in scan_rows:
            connection.execute(
                """
                DELETE FROM atlassian_item_evidence
                WHERE session_id = ? AND source_path = ?
                """,
                (scan_row["session_id"], source_path),
            )
            connection.execute(
                "DELETE FROM atlassian_evidence_scans WHERE id = ?",
                (scan_row["id"],),
            )

        session_rows = connection.execute(
            """
            SELECT id
            FROM sessions
            WHERE source_id = ?
              AND index_policy = 'full'
              AND (external_id = ? OR source_path = ?)
            """,
            (source_id, parsed.external_id, source_path),
        ).fetchall()
        for session_row in session_rows:
            session_id = int(session_row["id"])
            meaningful = connection.execute(
                """
                SELECT
                    EXISTS(
                        SELECT 1 FROM activity_events WHERE session_id = ?
                    )
                    OR EXISTS(
                        SELECT 1 FROM usage_records WHERE session_id = ?
                    )
                """,
                (session_id, session_id),
            ).fetchone()[0]
            if meaningful:
                continue
            connection.execute(
                """
                DELETE FROM search_index
                WHERE entity_type = 'session' AND entity_id = ?
                """,
                (str(session_id),),
            )
            connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

        connection.execute(
            "DELETE FROM source_files WHERE source_id = ? AND path = ?",
            (source_id, source_path),
        )


def _usage_identity_scope(source_key: str, provider_kind: str) -> Optional[str]:
    return source_key if source_key != provider_kind else None


def _store_parsed_usage(
    connection: sqlite3.Connection,
    *,
    source_id: int,
    session_id: int,
    source_key: str,
    provider_kind: str,
    workspace_id: Optional[int],
    usage_contract_version: Optional[str],
    parsed: ParsedSession,
    usage_cache: Optional[UsagePersistenceCache] = None,
) -> None:
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
                if provider_kind == "claude"
                else CODEX_USAGE_CONTRACT_VERSION
                if provider_kind == "codex"
                else "legacy-v1"
            )
        ),
        identity_scope=_usage_identity_scope(source_key, provider_kind),
        cache=usage_cache,
    )


def _store_session(
    connection: sqlite3.Connection,
    source_id: int,
    source_key: str,
    parsed: ParsedSession,
    usage_contract_version: Optional[str] = None,
    provider_kind: Optional[str] = None,
    include_usage: bool = True,
    usage_cache: Optional[UsagePersistenceCache] = None,
) -> int:
    effective_provider_kind = provider_kind or source_key
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
    identity_scope = _usage_identity_scope(source_key, effective_provider_kind)
    if include_usage:
        _store_parsed_usage(
            connection,
            source_id=source_id,
            session_id=session_id,
            source_key=source_key,
            provider_kind=effective_provider_kind,
            workspace_id=workspace_id,
            usage_contract_version=usage_contract_version,
            parsed=parsed,
            usage_cache=usage_cache,
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
                    stable_id(
                        "source-scoped-event", source_key, event.event_id
                    )
                    if identity_scope
                    else event.event_id,
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
                source_key,
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
    connection: sqlite3.Connection, source_id: int, provider_kind: str
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
        if not parent and provider_kind == "claude":
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
    source_key: str,
    name: str,
    root: Path,
    parser,
    usage_contract_version: str,
    force: bool = False,
    provider_kind: Optional[str] = None,
    path_filter: Optional[Callable[[Path, Path], bool]] = None,
    session_contract_version: Optional[str] = None,
    reference_lookup_cache: Optional[SessionReferenceLookupCache] = None,
    progress: Optional[ScanProgressCallback] = None,
) -> Tuple[int, int, int]:
    effective_provider_kind = provider_kind or source_key
    source_id = _upsert_source(
        connection, source_key, effective_provider_kind, name, root
    )
    imported = skipped = failed = 0
    usage_cache = UsagePersistenceCache()
    if reference_lookup_cache is None:
        reference_lookup_cache = SessionReferenceLookupCache()
    if not root.exists():
        return imported, skipped, failed

    paths = sorted(
        path
        for path in root.rglob("*.jsonl")
        if path_filter is None or path_filter(root, path)
    )
    if session_contract_version is not None:
        connection.execute(
            """
            UPDATE source_files
            SET session_contract_version = ?
            WHERE source_id = ?
              AND session_contract_version IS NULL
              AND usage_contract_version = ?
            """,
            (session_contract_version, source_id, usage_contract_version),
        )
    session_contract_repair_required = bool(
        session_contract_version is not None
        and connection.execute(
            """
            SELECT 1 FROM source_files
            WHERE source_id = ?
              AND COALESCE(session_contract_version, '') != ?
            LIMIT 1
            """,
            (source_id, session_contract_version),
        ).fetchone()
    )
    usage_contract_repair_required = bool(
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
    reference_contract_repair_required = bool(
        connection.execute(
            """
            SELECT 1 FROM source_files
            WHERE source_id = ?
              AND COALESCE(reference_contract_version, '') != ?
            LIMIT 1
            """,
            (source_id, REFERENCE_EXTRACTOR_VERSION),
        ).fetchone()
    )
    source_contract_repair_required = bool(
        session_contract_repair_required
        or usage_contract_repair_required
        or reference_contract_repair_required
    )
    repair_kinds = [
        kind
        for kind, required in (
            ("session", session_contract_repair_required),
            ("usage", usage_contract_repair_required),
            ("reference", reference_contract_repair_required),
        )
        if required
    ]
    _emit_scan_progress(
        progress,
        {
            "type": "source_plan",
            "source_key": source_key,
            "display_label": name,
            "mode": (
                "forced"
                if force
                else "contract_repair"
                if repair_kinds
                else "incremental"
            ),
            "repair_kinds": repair_kinds,
            "total_files": len(paths),
        },
    )
    eligibility_repair_required = _session_eligibility_repair_required(
        connection, source_id
    )
    if source_contract_repair_required:
        connection.execute("SAVEPOINT source_contract_repair")
    _remove_stale_sessions(connection, source_id, paths)
    forced_reference_paths = set()
    if not source_contract_repair_required:
        dirty_session_ids = set()
        has_unmapped_path = False
        for path in paths:
            row = connection.execute(
                """
                SELECT session_id, size_bytes, mtime_ns, status,
                       reference_contract_version
                FROM source_files
                WHERE source_id = ? AND path = ?
                """,
                (source_id, str(path)),
            ).fetchone()
            if not row or row["session_id"] is None:
                has_unmapped_path = True
                continue
            stat = path.stat()
            if (
                row["size_bytes"] != stat.st_size
                or row["mtime_ns"] != stat.st_mtime_ns
                or row["status"] != "ok"
                or row["reference_contract_version"]
                != REFERENCE_EXTRACTOR_VERSION
            ):
                dirty_session_ids.add(int(row["session_id"]))
        partial_ids = set()
        if dirty_session_ids:
            placeholders = ",".join("?" for _ in dirty_session_ids)
            partial_ids.update(
                int(row["session_id"])
                for row in connection.execute(
                    """
                    SELECT session_id
                    FROM session_reference_scans
                    WHERE status = 'partial'
                      AND session_id IN ({})
                    """.format(placeholders),
                    tuple(sorted(dirty_session_ids)),
                ).fetchall()
            )
        if has_unmapped_path:
            partial_ids.update(
                int(row["session_id"])
                for row in connection.execute(
                    """
                    SELECT session_reference_scans.session_id
                    FROM session_reference_scans
                    JOIN sessions
                      ON sessions.id = session_reference_scans.session_id
                    WHERE sessions.source_id = ?
                      AND session_reference_scans.status = 'partial'
                    """,
                    (source_id,),
                ).fetchall()
            )
        if partial_ids:
            placeholders = ",".join("?" for _ in partial_ids)
            forced_reference_paths = {
                row["path"]
                for row in connection.execute(
                    """
                    SELECT path FROM source_files
                    WHERE source_id = ?
                      AND session_id IN ({})
                    """.format(placeholders),
                    (source_id,) + tuple(sorted(partial_ids)),
                ).fetchall()
            }
    expected_usage_record_ids = set()
    repair_errors = []
    empty_candidates = []
    reference_sessions_to_finalize = set()
    failed_reference_sessions = {}
    tracked_files = {
        row["path"]: row
        for row in connection.execute(
            """
            SELECT session_id, path, size_bytes, mtime_ns, status,
                   session_contract_version, usage_contract_version,
                   reference_contract_version
            FROM source_files
            WHERE source_id = ?
            """,
            (source_id,),
        ).fetchall()
    }
    progress_interval = max(1, (len(paths) + 19) // 20)

    def report_file_progress(processed_files: int) -> None:
        if (
            processed_files != len(paths)
            and processed_files % progress_interval != 0
        ):
            return
        _emit_scan_progress(
            progress,
            {
                "type": "source_progress",
                "source_key": source_key,
                "display_label": name,
                "processed_files": processed_files,
                "total_files": len(paths),
                "imported": imported,
                "unchanged": skipped,
                "failed_files": failed,
            },
        )

    for processed_files, path in enumerate(paths, start=1):
        source_path = str(path)
        current_stat = path.stat()
        tracked_file = tracked_files.get(source_path)
        mapped_session_id = (
            int(tracked_file["session_id"])
            if tracked_file and tracked_file["session_id"] is not None
            else None
        )
        native_file_current = _source_file_row_is_current(
            tracked_file, current_stat
        )
        evidence_source_fingerprint = session_evidence_source_fingerprint(
            source_id=source_id,
            source_path=source_path,
            size_bytes=current_stat.st_size,
            mtime_ns=current_stat.st_mtime_ns,
        )
        reference_scan_current = bool(
            mapped_session_id is not None
            and session_reference_scan_is_current(
                connection, mapped_session_id
            )
        )
        evidence_current = bool(
            mapped_session_id is not None
            and evidence_scan_is_current(
                connection,
                session_id=mapped_session_id,
                source_path=source_path,
                source_fingerprint=evidence_source_fingerprint,
            )
        )
        if (
            not force
            and not source_contract_repair_required
            and not eligibility_repair_required
            and source_path not in forced_reference_paths
            and _source_file_row_is_current(
                tracked_file,
                current_stat,
                usage_contract_version,
                REFERENCE_EXTRACTOR_VERSION,
                session_contract_version,
            )
            and reference_scan_current
            and evidence_current
        ):
            skipped += 1
            report_file_progress(processed_files)
            continue
        missing_session = mapped_session_id is None
        refresh_session = bool(
            force
            or eligibility_repair_required
            or session_contract_repair_required
            or not native_file_current
            or missing_session
        )
        refresh_usage = bool(
            force
            or usage_contract_repair_required
            or not native_file_current
            or missing_session
        )
        refresh_references = bool(
            force
            or session_contract_repair_required
            or reference_contract_repair_required
            or not native_file_current
            or missing_session
            or source_path in forced_reference_paths
            or not reference_scan_current
        )
        refresh_atlassian_evidence = bool(
            force
            or session_contract_repair_required
            or reference_contract_repair_required
            or not native_file_current
            or missing_session
            or not evidence_current
        )
        current_session_id = None
        try:
            scanned_stat = current_stat
            parsed = parser(path)
            if not _parsed_session_is_meaningful(parsed):
                empty_candidates.append((path, parsed))
                report_file_progress(processed_files)
                continue
            if refresh_session:
                session_id = _store_session(
                    connection,
                    source_id,
                    source_key,
                    parsed,
                    usage_contract_version=usage_contract_version,
                    provider_kind=effective_provider_kind,
                    include_usage=refresh_usage,
                    usage_cache=usage_cache,
                )
            else:
                session_row = connection.execute(
                    """
                    SELECT id, workspace_id
                    FROM sessions WHERE id = ? AND source_id = ?
                    """,
                    (mapped_session_id, source_id),
                ).fetchone()
                if session_row is None:
                    raise RuntimeError("Mapped Session is unavailable")
                session_id = int(session_row["id"])
                if refresh_usage:
                    _store_parsed_usage(
                        connection,
                        source_id=source_id,
                        session_id=session_id,
                        source_key=source_key,
                        provider_kind=effective_provider_kind,
                        workspace_id=session_row["workspace_id"],
                        usage_contract_version=usage_contract_version,
                        parsed=parsed,
                        usage_cache=usage_cache,
                    )
            current_session_id = session_id
            if refresh_atlassian_evidence:
                reconcile_session_evidence(
                    connection,
                    session_id=session_id,
                    source_path=source_path,
                    source_fingerprint=evidence_source_fingerprint,
                    candidates=parsed.url_evidence,
                )
            if refresh_references:
                reconcile_session_references(
                    connection,
                    session_id=session_id,
                    source_path=source_path,
                    source_size_bytes=scanned_stat.st_size,
                    source_mtime_ns=scanned_stat.st_mtime_ns,
                    candidates=parsed.reference_candidates,
                    finalize=False,
                    lookup=reference_lookup_cache.get(connection),
                )
            _record_source_file(
                connection,
                source_id,
                path,
                usage_contract_version=usage_contract_version,
                scanned_size_bytes=scanned_stat.st_size,
                scanned_mtime_ns=scanned_stat.st_mtime_ns,
                session_id=session_id,
                reference_contract_version=REFERENCE_EXTRACTOR_VERSION,
                session_contract_version=session_contract_version,
            )
            if refresh_references:
                reference_sessions_to_finalize.add(session_id)
            if usage_contract_repair_required:
                expected_usage_record_ids.update(
                    stable_id(
                        "source-scoped-usage", source_key, record.usage_record_id
                    )
                    if source_key != effective_provider_kind
                    else record.usage_record_id
                    for record in parsed.usage_records
                )
            imported += 1
            report_file_progress(processed_files)
        except Exception as exc:
            if current_session_id is None:
                mapped = connection.execute(
                    """
                    SELECT session_id FROM source_files
                    WHERE source_id = ? AND path = ?
                    """,
                    (source_id, str(path)),
                ).fetchone()
                if mapped and mapped["session_id"] is not None:
                    current_session_id = int(mapped["session_id"])
            if current_session_id is not None:
                failed_reference_sessions[current_session_id] = str(exc)
            if source_contract_repair_required:
                repair_errors.append((path, str(exc)))
            else:
                _record_source_file(connection, source_id, path, "error", str(exc))
            failed += 1
            report_file_progress(processed_files)
    for session_id in sorted(
        reference_sessions_to_finalize - set(failed_reference_sessions)
    ):
        try:
            finalize_session_references(connection, session_id)
        except Exception as exc:
            failed_reference_sessions[session_id] = str(exc)
            failed += 1
            session_paths = connection.execute(
                "SELECT path FROM source_files WHERE session_id = ? ORDER BY path",
                (session_id,),
            ).fetchall()
            if source_contract_repair_required:
                repair_errors.extend(
                    (Path(row["path"]), str(exc)) for row in session_paths
                )
            else:
                connection.execute(
                    """
                    UPDATE source_files
                    SET status = 'error', error = ?
                    WHERE session_id = ?
                    """,
                    (str(exc), session_id),
                )
    if source_contract_repair_required and failed:
        connection.execute("ROLLBACK TO source_contract_repair")
        connection.execute("RELEASE source_contract_repair")
        imported = 0
        empty_candidates = []
        for path, error in repair_errors:
            _record_source_file(connection, source_id, path, "error", error)
    elif source_contract_repair_required:
        try:
            if usage_contract_repair_required:
                reconcile_usage_record_contract(
                    connection, source_id, expected_usage_record_ids
                )
            connection.execute("RELEASE source_contract_repair")
        except Exception:
            connection.execute("ROLLBACK TO source_contract_repair")
            connection.execute("RELEASE source_contract_repair")
            raise
    for session_id, error in failed_reference_sessions.items():
        if connection.execute(
            "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
        ).fetchone():
            mark_session_reference_error(
                connection,
                session_id=session_id,
                error_message=error,
            )
    _remove_empty_session_candidates(connection, source_id, empty_candidates)
    _reconcile_session_parents(connection, source_id, effective_provider_kind)
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
        connection,
        "context",
        "context",
        "Local Contexts",
        settings.context_root,
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


def _is_claude_session_candidate(root: Path, path: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    ancestors = relative_parts[:-1]
    return "subagents" not in ancestors or path.parent.name == "subagents"


SESSION_SCAN_ADAPTERS = {
    "claude": (
        parse_claude_session,
        CLAUDE_SESSION_CONTRACT_VERSION,
        CLAUDE_USAGE_CONTRACT_VERSION,
    ),
    "codex": (
        parse_codex_session,
        CODEX_SESSION_CONTRACT_VERSION,
        CODEX_USAGE_CONTRACT_VERSION,
    ),
}
SESSION_SCAN_PATH_FILTERS = {
    "claude": _is_claude_session_candidate,
}
SESSION_SCAN_SUCCESS_STATUSES = {"completed", "empty"}


def _source_scan_counts(
    connection: sqlite3.Connection, source_id: Optional[int]
) -> Tuple[int, int]:
    if source_id is None:
        return 0, 0
    row = connection.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM sessions
             WHERE source_id = ? AND session_class = 'work'
               AND session_role = 'primary') AS eligible_sessions,
            (SELECT COUNT(*) FROM source_files
             WHERE source_id = ?) AS tracked_files
        """,
        (source_id, source_id),
    ).fetchone()
    return int(row["eligible_sessions"]), int(row["tracked_files"])


def _source_row(connection: sqlite3.Connection, source_key: str):
    return connection.execute(
        """
        SELECT id, kind, provider_kind, name, root_path,
               last_scanned_at, last_scan_success_at
        FROM sources WHERE kind = ?
        """,
        (source_key,),
    ).fetchone()


def _bounded_scan_failure(provider_kind: str) -> str:
    label = "Claude" if provider_kind == "claude" else "Codex"
    return "{} Session files could not be synchronized; existing data was retained.".format(label)


def _record_scan_health(
    connection: sqlite3.Connection,
    source_id: Optional[int],
    status: str,
    attempted_at: str,
    error: Optional[str] = None,
) -> None:
    if source_id is None:
        return
    bounded_error = error[:500] if error else None
    if status in SESSION_SCAN_SUCCESS_STATUSES:
        connection.execute(
            """
            UPDATE sources
            SET last_scanned_at = ?, last_scan_success_at = ?,
                last_scan_status = ?, last_scan_error = NULL
            WHERE id = ?
            """,
            (attempted_at, attempted_at, status, source_id),
        )
    else:
        connection.execute(
            """
            UPDATE sources
            SET last_scanned_at = ?, last_scan_status = ?, last_scan_error = ?
            WHERE id = ?
            """,
            (attempted_at, status, bounded_error, source_id),
        )


def _source_report(
    *,
    source_key: str,
    display_label: str,
    provider_kind: str,
    root: str,
    status: str,
    imported: int = 0,
    unchanged: int = 0,
    failed_files: int = 0,
    eligible_sessions: int = 0,
    tracked_files: int = 0,
    last_attempt_at: Optional[str] = None,
    last_success_at: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "source_key": source_key,
        "display_label": display_label,
        "provider_kind": provider_kind,
        "root": root,
        "status": status,
        "imported": imported,
        "unchanged": unchanged,
        "failed_files": failed_files,
        "eligible_sessions": eligible_sessions,
        "tracked_files": tracked_files,
        "last_attempt_at": last_attempt_at,
        "last_success_at": last_success_at,
        "error_code": error_code,
        "error_message": error_message,
        "retained_data": status not in SESSION_SCAN_SUCCESS_STATUSES,
    }


def _aggregate_scan_report(sources: list) -> Dict[str, Any]:
    success_count = sum(
        1 for source in sources if source["status"] in SESSION_SCAN_SUCCESS_STATUSES
    )
    issue_count = len(sources) - success_count
    if issue_count == 0:
        outcome = "complete"
    elif success_count:
        outcome = "partial"
    else:
        outcome = "failed"
    return {
        "outcome": outcome,
        "summary": {
            "source_count": len(sources),
            "completed_sources": success_count,
            "attention_sources": issue_count,
            "imported": sum(source["imported"] for source in sources),
            "unchanged": sum(source["unchanged"] for source in sources),
            "failed_files": sum(source["failed_files"] for source in sources),
        },
        "sources": sources,
    }


def _configuration_source_report(registration, diagnostic=None) -> Dict[str, Any]:
    attempted_at = utc_now()
    error_code = diagnostic.code if diagnostic else registration.status
    if diagnostic:
        error_message = "{} This source was not synchronized; existing data was retained.".format(
            diagnostic.message
        )
    else:
        error_message = "This source was not synchronized because its configuration needs attention; existing data was retained."
    error_message = error_message[:500]
    with transaction() as connection:
        row = _source_row(connection, registration.source_key)
        source_id = int(row["id"]) if row else registration.source_id
        eligible, tracked = _source_scan_counts(connection, source_id)
        _record_scan_health(
            connection,
            source_id,
            "configuration_error",
            attempted_at,
            error_message,
        )
        last_success = row["last_scan_success_at"] if row else None
    return _source_report(
        source_key=registration.source_key,
        display_label=registration.display_label,
        provider_kind=registration.provider_kind,
        root=registration.root,
        status="configuration_error",
        eligible_sessions=eligible,
        tracked_files=tracked,
        last_attempt_at=attempted_at,
        last_success_at=last_success,
        error_code=error_code,
        error_message=error_message,
    )


def _scan_registered_session_source(
    registration,
    force: bool,
    reference_lookup_cache: Optional[SessionReferenceLookupCache] = None,
    progress: Optional[ScanProgressCallback] = None,
) -> Dict[str, Any]:
    attempted_at = utc_now()
    if registration.status == "unavailable":
        message = "This source root is unavailable; it was not synchronized and existing data was retained."
        with transaction() as connection:
            row = _source_row(connection, registration.source_key)
            source_id = int(row["id"]) if row else registration.source_id
            eligible, tracked = _source_scan_counts(connection, source_id)
            _record_scan_health(
                connection, source_id, "unavailable", attempted_at, message
            )
            last_success = row["last_scan_success_at"] if row else None
        return _source_report(
            source_key=registration.source_key,
            display_label=registration.display_label,
            provider_kind=registration.provider_kind,
            root=registration.root,
            status="unavailable",
            eligible_sessions=eligible,
            tracked_files=tracked,
            last_attempt_at=attempted_at,
            last_success_at=last_success,
            error_code="root_unavailable",
            error_message=message,
        )

    if registration.status != "ready":
        return _configuration_source_report(registration)

    adapter = SESSION_SCAN_ADAPTERS.get(registration.provider_kind)
    if adapter is None:
        return _configuration_source_report(registration)
    parser, session_contract, usage_contract = adapter
    try:
        with transaction() as connection:
            values = _scan_session_source(
                connection,
                registration.source_key,
                registration.display_label,
                Path(registration.root),
                parser,
                usage_contract,
                force,
                provider_kind=registration.provider_kind,
                path_filter=SESSION_SCAN_PATH_FILTERS.get(
                    registration.provider_kind
                ),
                session_contract_version=session_contract,
                reference_lookup_cache=reference_lookup_cache,
                progress=progress,
            )
            row = _source_row(connection, registration.source_key)
            source_id = int(row["id"])
            eligible, tracked = _source_scan_counts(connection, source_id)
            status = "scan_failed" if values[2] else ("empty" if tracked == 0 else "completed")
            message = (
                "{} files could not be processed; existing data for those files was retained.".format(values[2])
                if values[2]
                else None
            )
            _record_scan_health(connection, source_id, status, attempted_at, message)
            last_success = attempted_at if status in SESSION_SCAN_SUCCESS_STATUSES else row["last_scan_success_at"]
        return _source_report(
            source_key=registration.source_key,
            display_label=registration.display_label,
            provider_kind=registration.provider_kind,
            root=registration.root,
            status=status,
            imported=values[0],
            unchanged=values[1],
            failed_files=values[2],
            eligible_sessions=eligible,
            tracked_files=tracked,
            last_attempt_at=attempted_at,
            last_success_at=last_success,
            error_code="file_scan_failed" if values[2] else None,
            error_message=message,
        )
    except Exception:
        message = _bounded_scan_failure(registration.provider_kind)
        with transaction() as connection:
            row = _source_row(connection, registration.source_key)
            source_id = int(row["id"]) if row else registration.source_id
            eligible, tracked = _source_scan_counts(connection, source_id)
            _record_scan_health(
                connection, source_id, "scan_failed", attempted_at, message
            )
            last_success = row["last_scan_success_at"] if row else None
        return _source_report(
            source_key=registration.source_key,
            display_label=registration.display_label,
            provider_kind=registration.provider_kind,
            root=registration.root,
            status="scan_failed",
            eligible_sessions=eligible,
            tracked_files=tracked,
            last_attempt_at=attempted_at,
            last_success_at=last_success,
            error_code="source_scan_failed",
            error_message=message,
        )


def _scan_session_sources(
    force: bool = False,
    selected_keys: Optional[Set[str]] = None,
    progress: Optional[ScanProgressCallback] = None,
) -> Dict[str, Any]:
    with transaction() as connection:
        registry = load_and_reconcile_session_sources(connection, settings)

    reports = []
    reference_lookup_cache = SessionReferenceLookupCache()
    registrations = list(registry.registrations)
    represented = {item.source_key for item in registrations}
    diagnostics_by_key = {
        item.source_key: item
        for item in registry.diagnostics
        if item.source_key and item.source_key not in represented
    }
    if registry.settings.file_error:
        with transaction() as connection:
            rows = connection.execute(
                """
                SELECT id, kind, provider_kind, name, root_path
                FROM sources
                WHERE provider_kind IN ('claude', 'codex')
                ORDER BY id
                """
            ).fetchall()
        registrations = [
            SessionSourceRegistration(
                source_key=row["kind"],
                provider_kind=row["provider_kind"],
                display_label=row["name"],
                root=row["root_path"],
                status="configuration_error",
                source_id=int(row["id"]),
            )
            for row in rows
        ]
        if not registrations:
            diagnostic = registry.diagnostics[0]
            message = "{} Session sources were not synchronized; existing data was retained.".format(
                diagnostic.message
            )[:500]
            reports.append(
                _source_report(
                    source_key="settings",
                    display_label="Session source settings",
                    provider_kind="unknown",
                    root=str(registry.settings.settings_path),
                    status="configuration_error",
                    last_attempt_at=utc_now(),
                    error_code=diagnostic.code,
                    error_message=message,
                )
            )
    else:
        by_key = {item.source_key: item for item in registrations}
        for source_key, diagnostic in diagnostics_by_key.items():
            with transaction() as connection:
                row = _source_row(connection, source_key)
            by_key[source_key] = SessionSourceRegistration(
                source_key=source_key,
                provider_kind=row["provider_kind"] if row else "unknown",
                display_label=row["name"] if row else source_key,
                root=row["root_path"] if row else "",
                status="configuration_error",
                source_id=int(row["id"]) if row else None,
            )
        registrations = [
            by_key[key] for key in registry.settings.declared_source_keys if key in by_key
        ] + [
            item for item in registrations if item.source_key not in registry.settings.declared_source_keys
        ]

    selected_registrations = [
        registration
        for registration in registrations
        if selected_keys is None or registration.source_key in selected_keys
    ]
    _emit_scan_progress(
        progress,
        {
            "type": "sync_started",
            "source_count": len(selected_registrations),
        },
    )
    for source_index, registration in enumerate(selected_registrations, start=1):
        _emit_scan_progress(
            progress,
            {
                "type": "source_started",
                "source_key": registration.source_key,
                "display_label": registration.display_label,
                "source_index": source_index,
                "source_count": len(selected_registrations),
            },
        )
        diagnostic = diagnostics_by_key.get(registration.source_key)
        if registry.settings.file_error:
            diagnostic = registry.diagnostics[0]
        if diagnostic or registration.status not in {"ready", "unavailable"}:
            source_report = _configuration_source_report(
                registration, diagnostic
            )
        else:
            source_report = _scan_registered_session_source(
                registration,
                force,
                reference_lookup_cache=reference_lookup_cache,
                progress=progress,
            )
        reports.append(source_report)
        _emit_scan_progress(
            progress,
            {
                "type": "source_result",
                "source_key": source_report["source_key"],
                "display_label": source_report["display_label"],
                "status": source_report["status"],
                "imported": source_report["imported"],
                "unchanged": source_report["unchanged"],
                "failed_files": source_report["failed_files"],
            },
        )
    report = _aggregate_scan_report(reports)
    _emit_scan_progress(
        progress,
        {
            "type": "sync_complete",
            "outcome": report["outcome"],
            "summary": report["summary"],
        },
    )
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
        provider_kind="claude",
        path_filter=_is_claude_session_candidate,
        session_contract_version=CLAUDE_SESSION_CONTRACT_VERSION,
    )


def scan_claude_sessions(force: bool = False) -> Dict[str, int]:
    init_db()
    report = _scan_session_sources(force=force, selected_keys={"claude"})
    source = report["sources"][0] if report["sources"] else {}
    return {
        "imported": source.get("imported", 0),
        "skipped": source.get("unchanged", 0),
        "failed": source.get("failed_files", 0),
    }


def scan_codex_sessions(force: bool = False) -> Dict[str, int]:
    init_db()
    report = _scan_session_sources(force=force, selected_keys={"codex"})
    source = report["sources"][0] if report["sources"] else {}
    return {
        "imported": source.get("imported", 0),
        "skipped": source.get("unchanged", 0),
        "failed": source.get("failed_files", 0),
    }


def scan_session_sources(
    force: bool = False,
    progress: Optional[ScanProgressCallback] = None,
) -> Dict[str, Any]:
    init_db()
    return _scan_session_sources(force=force, progress=progress)


def scan_all(force: bool = False) -> Dict[str, Any]:
    init_db()
    report = _scan_session_sources(force=force)
    attempted_at = utc_now()
    context_report = None
    try:
        with transaction() as connection:
            values = _scan_context_documents(connection, force=force)
            row = _source_row(connection, "context")
            source_id = int(row["id"]) if row else None
            eligible, tracked = _source_scan_counts(connection, source_id)
            status = "scan_failed" if values[2] else ("empty" if tracked == 0 else "completed")
            message = "{} Context files could not be processed.".format(values[2]) if values[2] else None
            _record_scan_health(connection, source_id, status, attempted_at, message)
            last_success = attempted_at if status in SESSION_SCAN_SUCCESS_STATUSES else (row["last_scan_success_at"] if row else None)
            context_report = _source_report(
                source_key="context", display_label="Local Contexts",
                provider_kind="context", root=str(settings.context_root),
                status=status, imported=values[0], unchanged=values[1],
                failed_files=values[2], tracked_files=tracked,
                last_attempt_at=attempted_at, last_success_at=last_success,
                error_code="file_scan_failed" if values[2] else None,
                error_message=message,
            )
    except Exception:
        message = "Local Context files could not be scanned; existing data was retained."
        with transaction() as connection:
            row = _source_row(connection, "context")
            source_id = int(row["id"]) if row else None
            _, tracked = _source_scan_counts(connection, source_id)
            _record_scan_health(connection, source_id, "scan_failed", attempted_at, message)
            last_success = row["last_scan_success_at"] if row else None
        context_report = _source_report(
            source_key="context", display_label="Local Contexts",
            provider_kind="context", root=str(settings.context_root),
            status="scan_failed", tracked_files=tracked,
            last_attempt_at=attempted_at, last_success_at=last_success,
            error_code="source_scan_failed", error_message=message,
        )
    return _aggregate_scan_report(report["sources"] + [context_report])
