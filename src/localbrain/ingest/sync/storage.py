"""Shared source, file, workspace and search persistence operations."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from ...atlassian_structure_references import project_structure_reference_search
from ...path_display import home_relative_path
from ..contracts import SessionRevisionError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _upsert_source(connection, source_id, provider_kind, name, root) -> int:
    if source_id is None:
        return connection.execute(
            "INSERT INTO sources(provider_kind,name,root_path) VALUES (?,?,?)",
            (provider_kind, name, str(root)),
        ).lastrowid
    existing = connection.execute("SELECT provider_kind FROM sources WHERE id=?", (source_id,)).fetchone()
    if not existing or existing["provider_kind"] != provider_kind:
        raise ValueError("Source ID is not registered with this provider")
    connection.execute("UPDATE sources SET name=?,root_path=? WHERE id=?", (name, str(root), source_id))
    return source_id


def _source_file_row_is_current(
    row: Optional[sqlite3.Row],
    stat,
    usage_contract_version: Optional[str] = None,
    reference_contract_version: Optional[str] = None,
    session_contract_version: Optional[int] = None,
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
    session_contract_version: Optional[int] = None,
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
    session_contract_version: Optional[int] = None,
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
    display_name = home_relative_path(canonical)

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


def _delete_structure_evidence_owner(
    connection: sqlite3.Connection,
    *,
    session_id: Optional[int] = None,
    document_id: Optional[int] = None,
) -> None:
    if (session_id is None) == (document_id is None):
        raise ValueError("Exactly one structure evidence owner is required")
    if session_id is not None:
        reference_query = """
            SELECT DISTINCT reference_id
            FROM atlassian_structure_reference_evidence
            WHERE session_id = ?
            ORDER BY reference_id
        """
        delete_query = "DELETE FROM sessions WHERE id = ?"
        owner_id = session_id
    else:
        reference_query = """
            SELECT DISTINCT reference_id
            FROM atlassian_structure_reference_evidence
            WHERE document_id = ?
            ORDER BY reference_id
        """
        delete_query = "DELETE FROM context_documents WHERE id = ?"
        owner_id = document_id
    reference_ids = tuple(
        int(row["reference_id"])
        for row in connection.execute(
            reference_query,
            (owner_id,),
        ).fetchall()
    )
    connection.execute(delete_query, (owner_id,))
    for reference_id in reference_ids:
        project_structure_reference_search(connection, reference_id)


def _context_source_id(connection):
    row = connection.execute("SELECT id FROM sources WHERE provider_kind='context' ORDER BY id LIMIT 1").fetchone()
    return row["id"] if row else None


def _check_session_revision(connection, source_id, revision):
    if revision is None:
        return
    if type(revision) is not int or revision <= 0:
        raise SessionRevisionError("A positive numeric Session revision is required.")
    rows = connection.execute(
        "SELECT DISTINCT session_contract_version FROM source_files "
        "WHERE source_id=? AND session_contract_version IS NOT NULL", (source_id,)
    ).fetchall()
    for row in rows:
        stored = row["session_contract_version"]
        if type(stored) is not int or stored <= 0:
            raise SessionRevisionError("This source has an unsupported Session revision.")
        if stored > revision:
            raise SessionRevisionError(
                "This source was processed by a newer Session parser ({} > {}). "
                "Update LocalBrain before synchronizing it.".format(stored, revision)
            )
