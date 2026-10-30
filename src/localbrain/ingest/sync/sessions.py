"""Session-source file orchestration within the caller transaction."""

import sqlite3
from pathlib import Path
from typing import Callable, Optional, Tuple
from ...atlassian_evidence import (
    evidence_scan_is_current,
    reconcile_session_evidence,
    session_evidence_source_fingerprint,
)
from ...session_references import (
    SessionReferenceLookupCache,
    finalize_session_references,
    mark_session_reference_error,
    reconcile_session_references,
    session_reference_scan_is_current,
)
from ...skill_observations import store_skill_observations
from ...usage import UsagePersistenceCache, reconcile_usage_record_contract
from localbrain.ingest.evidence.reference_candidates import REFERENCE_EXTRACTOR_VERSION
from . import control, session_store, storage


def _session_paths(root, path_filter):
    for path in root.rglob("*.jsonl"):
        control._check_scan_cancelled()
        if path_filter is None or path_filter(root, path):
            yield path




def _scan_session_source(
    connection: sqlite3.Connection,
    source_id: int,
    name: str,
    root: Path,
    parser,
    usage_contract_version: str,
    force: bool = False,
    provider_kind: Optional[str] = None,
    path_filter: Optional[Callable[[Path, Path], bool]] = None,
    session_contract_version: Optional[int] = None,
    reference_lookup_cache: Optional[SessionReferenceLookupCache] = None,
    progress: Optional[control.ScanProgressCallback] = None,
) -> Tuple[int, int, int]:
    effective_provider_kind = provider_kind or connection.execute("SELECT provider_kind FROM sources WHERE id=?", (source_id,)).fetchone()["provider_kind"]
    storage._check_session_revision(connection, source_id, session_contract_version)
    source_id = storage._upsert_source(
        connection, source_id, effective_provider_kind, name, root
    )
    imported = skipped = failed = 0
    usage_cache = UsagePersistenceCache()
    if reference_lookup_cache is None:
        reference_lookup_cache = SessionReferenceLookupCache()
    if not root.exists():
        return imported, skipped, failed

    paths = sorted(_session_paths(root, path_filter))
    session_contract_repair_required = bool(
        session_contract_version is not None
        and connection.execute(
            """
            SELECT 1 FROM source_files
            WHERE source_id = ?
              AND COALESCE(session_contract_version, 0) != ?
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
    control._emit_scan_progress(
        progress,
        {
            "type": "source_plan",
            "source_id": source_id,
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
    eligibility_repair_required = session_store._session_eligibility_repair_required(
        connection, source_id
    )
    if source_contract_repair_required:
        connection.execute("SAVEPOINT source_contract_repair")
    session_store._remove_stale_sessions(connection, source_id, paths)
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
        control._emit_scan_progress(
            progress,
            {
                "type": "source_progress",
                "source_id": source_id,
                "display_label": name,
                "processed_files": processed_files,
                "total_files": len(paths),
                "imported": imported,
                "unchanged": skipped,
                "failed_files": failed,
            },
        )

    for processed_files, path in enumerate(paths, start=1):
        control._check_scan_cancelled()
        source_path = str(path)
        current_stat = path.stat()
        tracked_file = tracked_files.get(source_path)
        mapped_session_id = (
            int(tracked_file["session_id"])
            if tracked_file and tracked_file["session_id"] is not None
            else None
        )
        native_file_current = storage._source_file_row_is_current(
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
            and storage._source_file_row_is_current(
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
            if not session_store._parsed_session_is_meaningful(parsed):
                empty_candidates.append((path, parsed))
                report_file_progress(processed_files)
                continue
            if refresh_session:
                session_id = session_store._store_session(
                    connection,
                    source_id,
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
                    session_store._store_parsed_usage(
                        connection,
                        source_id=source_id,
                        session_id=session_id,
                        provider_kind=effective_provider_kind,
                        workspace_id=session_row["workspace_id"],
                        usage_contract_version=usage_contract_version,
                        parsed=parsed,
                        usage_cache=usage_cache,
                    )
            current_session_id = session_id
            store_skill_observations(
                connection,
                source_id=source_id,
                provider_kind=effective_provider_kind,
                parsed=parsed,
            )
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
            storage._record_source_file(
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
                native_ids = {record.source_record_id for record in parsed.usage_records}
                expected_usage_record_ids.update(row["id"] for row in connection.execute(
                    "SELECT id,source_record_id FROM usage_records WHERE session_id=?", (session_id,))
                    if row["source_record_id"] in native_ids)
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
                storage._record_source_file(connection, source_id, path, "error", str(exc))
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
            storage._record_source_file(connection, source_id, path, "error", error)
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
    session_store._remove_empty_session_candidates(connection, source_id, empty_candidates)
    session_store._reconcile_session_parents(connection, source_id, effective_provider_kind)
    connection.execute(
        """
        UPDATE skill_observations SET state = 'corrected'
        WHERE source_id = ? AND state = 'observed'
          AND external_session_id IN (
              SELECT external_id FROM sessions
              WHERE source_id = ? AND session_class = 'maintenance'
          )
        """,
        (source_id, source_id),
    )
    connection.execute(
        "UPDATE sources SET last_scanned_at = ? WHERE id = ?", (storage.utc_now(), source_id)
    )
    return imported, skipped, failed
