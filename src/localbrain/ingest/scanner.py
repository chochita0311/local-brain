"""Public scan composition, source registry, reports and outer transactions."""

import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, Tuple
from ..config import settings
from ..db import init_db, transaction
from ..session_sources import (
    SessionSourceRegistration,
    load_and_reconcile_session_sources,
)
from ..session_references import SessionReferenceLookupCache
from localbrain.ingest.contracts import CLAUDE_SESSION_REVISION, CLAUDE_USAGE_CONTRACT_VERSION
from localbrain.ingest.providers.claude import parse_claude_session
from localbrain.ingest.contracts import CODEX_SESSION_REVISION, CODEX_USAGE_CONTRACT_VERSION
from localbrain.ingest.providers.codex import parse_codex_session
from .contracts import SessionRevisionError
from .sync import contexts, control, sessions, storage


def scan_context_root(
    connection: sqlite3.Connection, root_id: int, force: bool = False
) -> Tuple[int, int, int]:
    return contexts._scan_context_documents(connection, force=force, root_id=root_id, config=settings)


def _is_claude_session_candidate(root: Path, path: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    ancestors = relative_parts[:-1]
    return "subagents" not in ancestors or path.parent.name == "subagents"


SESSION_SCAN_ADAPTERS = {
    "claude": (
        parse_claude_session,
        CLAUDE_SESSION_REVISION,
        CLAUDE_USAGE_CONTRACT_VERSION,
    ),
    "codex": (
        parse_codex_session,
        CODEX_SESSION_REVISION,
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


def _source_row(connection: sqlite3.Connection, source_id: int):
    return connection.execute(
        """
        SELECT id, provider_kind, name, root_path,
               last_scanned_at, last_scan_success_at
        FROM sources WHERE id = ?
        """,
        (source_id,),
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
    source_id: int,
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
        "source_id": source_id,
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
    attempted_at = storage.utc_now()
    error_code = diagnostic.code if diagnostic else registration.status
    if diagnostic:
        error_message = "{} This source was not synchronized; existing data was retained.".format(
            diagnostic.message
        )
    else:
        error_message = "This source was not synchronized because its configuration needs attention; existing data was retained."
    error_message = error_message[:500]
    with transaction() as connection:
        row = _source_row(connection, registration.source_id)
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
        source_id=registration.source_id,
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
    progress: Optional[control.ScanProgressCallback] = None,
) -> Dict[str, Any]:
    attempted_at = storage.utc_now()
    if registration.status == "unavailable":
        message = "This source root is unavailable; it was not synchronized and existing data was retained."
        with transaction() as connection:
            row = _source_row(connection, registration.source_id)
            source_id = int(row["id"]) if row else registration.source_id
            eligible, tracked = _source_scan_counts(connection, source_id)
            _record_scan_health(
                connection, source_id, "unavailable", attempted_at, message
            )
            last_success = row["last_scan_success_at"] if row else None
        return _source_report(
            source_id=registration.source_id,
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
            values = sessions._scan_session_source(
                connection,
                registration.source_id,
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
            row = _source_row(connection, registration.source_id)
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
            source_id=registration.source_id,
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
    except InterruptedError:
        raise
    except Exception as error:
        revision_error = isinstance(error, SessionRevisionError)
        message = str(error) if revision_error else _bounded_scan_failure(registration.provider_kind)
        with transaction() as connection:
            row = _source_row(connection, registration.source_id)
            source_id = int(row["id"]) if row else registration.source_id
            eligible, tracked = _source_scan_counts(connection, source_id)
            _record_scan_health(
                connection, source_id, "scan_failed", attempted_at, message
            )
            last_success = row["last_scan_success_at"] if row else None
        return _source_report(
            source_id=registration.source_id,
            display_label=registration.display_label,
            provider_kind=registration.provider_kind,
            root=registration.root,
            status="scan_failed",
            eligible_sessions=eligible,
            tracked_files=tracked,
            last_attempt_at=attempted_at,
            last_success_at=last_success,
            error_code="session_revision_unsupported" if revision_error else "source_scan_failed",
            error_message=message,
        )


def _scan_session_sources(
    force: bool = False,
    selected_ids: Optional[Set[int]] = None,
    selected_provider: Optional[str] = None,
    progress: Optional[control.ScanProgressCallback] = None,
) -> Dict[str, Any]:
    from ..source_settings import migrate_source_settings
    migrate_source_settings(settings)
    with transaction() as connection:
        registry = load_and_reconcile_session_sources(connection, settings)

    reports = []
    reference_lookup_cache = SessionReferenceLookupCache()
    registrations = list(registry.registrations)
    represented = {item.source_id for item in registrations}
    diagnostics_by_key = {
        item.source_id: item
        for item in registry.diagnostics
        if item.source_id and item.source_id not in represented
    }
    if registry.settings.file_error:
        with transaction() as connection:
            rows = connection.execute(
                """
                SELECT id, provider_kind, name, root_path
                FROM sources
                WHERE provider_kind IN ('claude', 'codex')
                ORDER BY id
                """
            ).fetchall()
        registrations = [
            SessionSourceRegistration(
                source_id=int(row["id"]),
                provider_kind=row["provider_kind"],
                display_label=row["name"],
                root=row["root_path"],
                status="configuration_error",
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
                    source_id=None,
                    display_label="Session source settings",
                    provider_kind="unknown",
                    root=str(registry.settings.settings_path),
                    status="configuration_error",
                    last_attempt_at=storage.utc_now(),
                    error_code=diagnostic.code,
                    error_message=message,
                )
            )
    else:
        by_key = {item.source_id: item for item in registrations}
        for source_id, diagnostic in diagnostics_by_key.items():
            with transaction() as connection:
                row = _source_row(connection, source_id)
            by_key[source_id] = SessionSourceRegistration(
                source_id=source_id,
                provider_kind=row["provider_kind"] if row else "unknown",
                display_label=row["name"] if row else str(source_id),
                root=row["root_path"] if row else "",
                status="configuration_error",
            )
        registrations = [
            by_key[key] for key in registry.settings.declared_source_ids if key in by_key
        ] + [
            item for item in registrations if item.source_id not in registry.settings.declared_source_ids
        ]

    disabled_keys = {entry.source_id for entry in registry.settings.entries if not entry.enabled}
    selected_registrations = [
        registration
        for registration in registrations
        if registration.source_id not in disabled_keys
        and (selected_ids is None or registration.source_id in selected_ids)
        and (selected_provider is None or registration.provider_kind == selected_provider)
    ]
    control._emit_scan_progress(
        progress,
        {
            "type": "sync_started",
            "source_count": len(selected_registrations),
        },
    )
    for source_index, registration in enumerate(selected_registrations, start=1):
        control._check_scan_cancelled()
        control._emit_scan_progress(
            progress,
            {
                "type": "source_started",
                "source_id": registration.source_id,
                "display_label": registration.display_label,
                "source_index": source_index,
                "source_count": len(selected_registrations),
            },
        )
        diagnostic = diagnostics_by_key.get(registration.source_id)
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
        control._emit_scan_progress(
            progress,
            {
                "type": "source_result",
                "source_id": source_report["source_id"],
                "display_label": source_report["display_label"],
                "status": source_report["status"],
                "imported": source_report["imported"],
                "unchanged": source_report["unchanged"],
                "failed_files": source_report["failed_files"],
            },
        )
    report = _aggregate_scan_report(reports)
    control._emit_scan_progress(
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
    return sessions._scan_session_source(
        connection,
        "claude",
        "Claude Code",
        settings.claude_root,
        parse_claude_session,
        CLAUDE_USAGE_CONTRACT_VERSION,
        force,
        provider_kind="claude",
        path_filter=_is_claude_session_candidate,
        session_contract_version=CLAUDE_SESSION_REVISION,
    )


def _scan_provider_sessions(provider: str, force: bool) -> Dict[str, int]:
    from ..local_operations import operation_lock
    with operation_lock(settings, "session-sync"):
        init_db()
        report = _scan_session_sources(force=force, selected_provider=provider)
    return {name: sum(source.get(field, 0) for source in report["sources"])
            for name, field in (("imported", "imported"), ("skipped", "unchanged"), ("failed", "failed_files"))}


def scan_claude_sessions(force: bool = False) -> Dict[str, int]:
    return _scan_provider_sessions("claude", force)


def scan_codex_sessions(force: bool = False) -> Dict[str, int]:
    return _scan_provider_sessions("codex", force)


def scan_session_sources(
    force: bool = False,
    progress: Optional[control.ScanProgressCallback] = None,
    cancelled: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    from ..local_operations import operation_lock
    token = control._SCAN_CANCELLED.set(cancelled)
    try:
        with operation_lock(settings, "session-sync"):
            control._check_scan_cancelled()
            init_db()
            return _scan_session_sources(force=force, progress=progress)
    finally:
        control._SCAN_CANCELLED.reset(token)


def scan_all(force: bool = False) -> Dict[str, Any]:
    from ..local_operations import operation_lock
    with operation_lock(settings, "scan-all"):
        return _scan_all(force)


def _scan_all(force: bool = False) -> Dict[str, Any]:
    init_db()
    report = _scan_session_sources(force=force)
    context = _scan_context_sources(force=force)
    return _aggregate_scan_report(report["sources"] + context["sources"])


def scan_context_sources(
    force: bool = False,
    progress: Optional[control.ScanProgressCallback] = None,
    cancelled: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Collect registered Context sources without scanning Session profiles."""
    from ..local_operations import operation_lock
    token = control._SCAN_CANCELLED.set(cancelled)
    try:
        with operation_lock(settings, "context-sync"):
            control._check_scan_cancelled()
            init_db()
            report = _scan_context_sources(force=force)
            control._emit_scan_progress(progress, {"type": "sync_complete", "report": report})
            return report
    finally:
        control._SCAN_CANCELLED.reset(token)


def _scan_context_sources(force: bool = False) -> Dict[str, Any]:
    attempted_at = storage.utc_now()
    context_report = None
    try:
        with transaction() as connection:
            values = contexts._scan_context_documents(connection, force=force, config=settings)
            row = _source_row(connection, storage._context_source_id(connection))
            source_id = int(row["id"]) if row else None
            eligible, tracked = _source_scan_counts(connection, source_id)
            status = "scan_failed" if values[2] else ("empty" if tracked == 0 else "completed")
            message = "{} Context files could not be processed.".format(values[2]) if values[2] else None
            _record_scan_health(connection, source_id, status, attempted_at, message)
            last_success = attempted_at if status in SESSION_SCAN_SUCCESS_STATUSES else (row["last_scan_success_at"] if row else None)
            context_report = _source_report(
                source_id=source_id, display_label="Local Contexts",
                provider_kind="context", root=str(settings.context_root),
                status=status, imported=values[0], unchanged=values[1],
                failed_files=values[2], tracked_files=tracked,
                last_attempt_at=attempted_at, last_success_at=last_success,
                error_code="file_scan_failed" if values[2] else None,
                error_message=message,
            )
    except InterruptedError:
        raise
    except Exception:
        message = "Local Context files could not be scanned; existing data was retained."
        with transaction() as connection:
            row = _source_row(connection, storage._context_source_id(connection))
            source_id = int(row["id"]) if row else None
            _, tracked = _source_scan_counts(connection, source_id)
            _record_scan_health(connection, source_id, "scan_failed", attempted_at, message)
            last_success = row["last_scan_success_at"] if row else None
        context_report = _source_report(
            source_id=source_id, display_label="Local Contexts",
            provider_kind="context", root=str(settings.context_root),
            status="scan_failed", tracked_files=tracked,
            last_attempt_at=attempted_at, last_success_at=last_success,
            error_code="source_scan_failed", error_message=message,
        )
    return _aggregate_scan_report([context_report])
