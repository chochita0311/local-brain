"""Independent presence observations for retained native Session inputs."""

from pathlib import Path
import stat

from . import control, storage


def record_presence(connection, source_id, path, state, error=None, checked_at=None):
    connection.execute(
        """UPDATE source_files
           SET presence_state=?, presence_checked_at=?, presence_error=?
           WHERE source_id=? AND path=?""",
        (state, checked_at or storage.utc_now(), error[:500] if error else None,
         source_id, str(path)),
    )


def mark_source_unknown(connection, source_id, error):
    connection.execute(
        """UPDATE source_files
           SET presence_state='UNKNOWN', presence_checked_at=?, presence_error=?
           WHERE source_id=? AND session_id IS NOT NULL""",
        (storage.utc_now(), error[:500], source_id),
    )


def observe_session_files(connection, source_id, root, paths, replacements,
                          provider_kind, path_filter=None):
    """Keep missing accepted originals; leave eligibility/replacement pruning owned.

    Discovery has completed before this call. A failed stat is not negative
    evidence. Last parsed fingerprints, versions and scan errors remain intact.
    """
    selected = {str(path) for path in paths}
    replaced = {row["path"] for row in replacements.values()}
    checked_at = storage.utc_now()
    accounting = connection.execute(
        """SELECT id,source_path FROM sessions WHERE source_id=?
           AND session_class='maintenance' AND index_policy='metadata_only'
           AND external_id IN (SELECT 'localbrain-insight:'||id FROM personal_insight_runs)""",
        (source_id,),
    ).fetchall()
    accounting_ids = {row["id"] for row in accounting}
    accounting_paths = {row["source_path"] for row in accounting}
    rows = connection.execute(
        """SELECT path, session_id FROM source_files WHERE source_id=?
           UNION
           SELECT source_path, id FROM sessions WHERE source_id=?""",
        (source_id, source_id),
    ).fetchall()
    retained_paths, retained_session_ids = set(), set()
    for row in rows:
        control._check_scan_cancelled()
        if row["session_id"] in accounting_ids or row["path"] in accounting_paths:
            # Ephemeral analysis has a retained accounting parent, not a native
            # rollout. Its private stream path must never become a source file.
            continue
        path = Path(row["path"])
        if str(path) in selected:
            record_presence(connection, source_id, path, "PRESENT", checked_at=checked_at)
            continue
        if not (path.name.endswith(".jsonl") or
                provider_kind == "codex" and path.name.endswith(".jsonl.zst")):
            continue
        outside_root = not path.is_relative_to(root)
        if not outside_root and path_filter is not None and not path_filter(root, path):
            # A provider-internal artifact is an eligibility correction, not an
            # unavailable original. Keep the established normalized-only cleanup.
            continue
        state, error = "UNKNOWN", None
        if outside_root:
            error = "The original path is outside the current source root."
        else:
            try:
                state = "PRESENT" if stat.S_ISREG(path.stat().st_mode) else "MISSING"
            except (FileNotFoundError, NotADirectoryError):
                state = "MISSING"
            except OSError as exc:
                error = "Original presence could not be checked: {}".format(type(exc).__name__)
        if row["session_id"] is not None:
            # Older imports may have a Session but no file mapping. Its metadata
            # supplies provenance, not a fabricated parsed revision or fingerprint.
            connection.execute(
                """INSERT INTO source_files(
                       source_id,session_id,path,size_bytes,mtime_ns,last_scanned_at,status)
                   SELECT source_id,id,source_path,0,0,imported_at,'stale'
                   FROM sessions WHERE id=? AND source_path=?
                   ON CONFLICT(source_id,path) DO UPDATE SET
                       session_id=COALESCE(source_files.session_id,excluded.session_id)""",
                (row["session_id"], str(path)),
            )
        record_presence(connection, source_id, path, state, error, checked_at)
        if str(path) not in replaced:
            retained_paths.add(path)
            if row["session_id"] is not None:
                retained_session_ids.add(int(row["session_id"]))
    return retained_paths, retained_session_ids
