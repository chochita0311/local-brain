"""Session-source file orchestration within the caller transaction."""

import sqlite3
import os
import stat
from pathlib import Path
from typing import Callable, Optional, Tuple
from localbrain.sessions.references import (
    SessionReferenceLookupCache,
    finalize_session_references,
    mark_session_reference_error,
    reconcile_session_references,
    session_reference_scan_is_current,
)
from localbrain.sessions.skills import store_skill_observations
from localbrain.usage.records import UsagePersistenceCache, reconcile_usage_record_contract
from localbrain.ingest.evidence.reference_candidates import REFERENCE_EXTRACTOR_VERSION
from localbrain.ingest import extensions
from . import control, session_files, session_store, storage


def _session_paths(root, path_filter, provider_kind=None):
    def fail_walk(error):
        raise error

    # Path.rglob can silently omit unreadable directories. Negative presence
    # evidence requires a complete walk that propagates enumeration failures.
    for directory, _, names in os.walk(root, onerror=fail_walk):
        control._check_scan_cancelled()
        for name in names:
            control._check_scan_cancelled()
            path = Path(directory) / name
            if name.endswith(".jsonl"):
                pass
            elif provider_kind == "codex" and name.endswith(".jsonl.zst"):
                try:
                    if stat.S_ISREG(path.with_suffix("").stat().st_mode):
                        continue
                except FileNotFoundError:
                    pass
            else:
                continue
            if not stat.S_ISREG(path.stat().st_mode):
                continue
            if path_filter is None or path_filter(root, path):
                yield path


def _session_container_replacements(connection, source_id, paths):
    selected_paths = {str(path) for path in paths}
    if not selected_paths:
        return {}
    replacements = {}
    rows = connection.execute(
        """SELECT id AS session_id, external_id, source_path AS path
           FROM sessions WHERE source_id = ?
           UNION
           SELECT files.session_id, sessions.external_id, files.path
           FROM source_files AS files JOIN sessions ON sessions.id = files.session_id
           WHERE files.source_id = ?""",
        (source_id, source_id),
    )
    for row in rows:
        prior_path = row["path"]
        if prior_path in selected_paths:
            continue
        if prior_path.endswith(".jsonl.zst"):
            replacement_path = prior_path[:-4]
        elif prior_path.endswith(".jsonl"):
            replacement_path = prior_path + ".zst"
        else:
            continue
        if replacement_path in selected_paths:
            prior = replacements.get(replacement_path)
            if prior and prior["session_id"] != row["session_id"]:
                raise RuntimeError("Session container has conflicting prior owners")
            replacements[replacement_path] = row
    return replacements




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
    storage._refresh_workspace_presence(connection, source_id)
    imported = skipped = failed = 0
    usage_cache = UsagePersistenceCache()
    if reference_lookup_cache is None:
        reference_lookup_cache = SessionReferenceLookupCache()
    if not root.exists():
        session_files.mark_source_unknown(connection, source_id, "The source root is unavailable.")
        return imported, skipped, failed

    paths = sorted(_session_paths(root, path_filter, effective_provider_kind))
    container_replacements = (
        _session_container_replacements(connection, source_id, paths)
        if effective_provider_kind == "codex" else {}
    )
    retained_prior_paths = {Path(row["path"]) for row in container_replacements.values()}
    retained_missing_paths, retained_session_ids = session_files.observe_session_files(
        connection, source_id, root, paths, container_replacements,
        effective_provider_kind, path_filter,
    )
    selected_paths = {str(path) for path in paths}
    current_files = [row for row in connection.execute(
        """SELECT path,session_contract_version,usage_contract_version,reference_contract_version
           FROM source_files WHERE source_id=?""", (source_id,))
        if row["path"] in selected_paths]
    session_contract_repair_required = bool(
        session_contract_version is not None
        and any(row["session_contract_version"] != session_contract_version for row in current_files)
    )
    usage_contract_repair_required = any(
        row["usage_contract_version"] != usage_contract_version for row in current_files
    )
    reference_contract_repair_required = any(
        row["reference_contract_version"] != REFERENCE_EXTRACTOR_VERSION for row in current_files
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
    # Keep the prior owner until either replacement container has parsed completely.
    session_store._remove_stale_sessions(
        connection, source_id, [*paths, *retained_prior_paths, *retained_missing_paths]
    )
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
    forced_reference_paths = set()
    if not source_contract_repair_required:
        dirty_session_ids = set()
        has_unmapped_path = False
        for path in paths:
            row = tracked_files.get(str(path))
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
        source_observation = dict(
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
            and extensions.session_is_current(
                connection,
                session_id=mapped_session_id,
                **source_observation,
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
        refresh_extensions = bool(
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
            replacement = container_replacements.get(source_path)
            if replacement and parsed.external_id != replacement["external_id"]:
                raise RuntimeError("Session container identity differs from its prior owner")
            if not session_store._parsed_session_is_meaningful(parsed):
                if replacement:
                    connection.execute(
                        "UPDATE sessions SET source_path = ? WHERE id = ?",
                        (source_path, replacement["session_id"]),
                    )
                    retained_prior_paths.discard(Path(replacement["path"]))
                    empty_candidates.append((Path(replacement["path"]), parsed))
                empty_candidates.append((path, parsed))
                report_file_progress(processed_files)
                continue
            if refresh_session:
                retained_owner = connection.execute(
                    "SELECT id FROM sessions WHERE source_id=? AND external_id=?",
                    (source_id, parsed.external_id),
                ).fetchone()
                session_id = session_store._store_session(
                    connection,
                    source_id,
                    parsed,
                    usage_contract_version=usage_contract_version,
                    provider_kind=effective_provider_kind,
                    include_usage=refresh_usage,
                    usage_cache=usage_cache,
                    preserve_existing_events=bool(
                        retained_owner and retained_owner["id"] in retained_session_ids
                    ),
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
            if refresh_extensions:
                extensions.session_indexed(
                    connection,
                    session_id=session_id,
                    **source_observation,
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
            session_files.record_presence(connection, source_id, path, "PRESENT")
            if replacement:
                retained_prior_paths.discard(Path(replacement["path"]))
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
                elif source_path in container_replacements:
                    current_session_id = int(container_replacements[source_path]["session_id"])
            if current_session_id is not None:
                failed_reference_sessions[current_session_id] = str(exc)
            if source_contract_repair_required:
                repair_errors.append((path, str(exc)))
            else:
                storage._record_source_file(connection, source_id, path, "error", str(exc))
                session_files.record_presence(connection, source_id, path, "PRESENT")
            failed += 1
            report_file_progress(processed_files)
    if container_replacements and not (source_contract_repair_required and failed):
        session_store._remove_stale_sessions(
            connection, source_id, [*paths, *retained_prior_paths, *retained_missing_paths]
        )
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
            session_files.record_presence(connection, source_id, path, "PRESENT")
    elif source_contract_repair_required:
        try:
            if usage_contract_repair_required:
                # A missing sibling prevents proving the Session's complete
                # replacement union. Keep its old direct Usage, with old versions.
                expected_usage_record_ids.update(
                    row["id"] for row in connection.execute(
                        "SELECT id,session_id FROM usage_records WHERE source_id=?", (source_id,))
                    if row["session_id"] in retained_session_ids
                )
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
