"""Normalized Session lifecycle, activity and Usage persistence."""

import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Tuple
from localbrain.sessions.references import clear_session_reference_source
from localbrain.usage.records import UsagePersistenceCache, store_usage_records
from localbrain.ingest.contracts import CLAUDE_USAGE_CONTRACT_VERSION
from localbrain.ingest.contracts import CODEX_USAGE_CONTRACT_VERSION
from localbrain.ingest.contracts import ParsedSession
from localbrain.ingest.common import stable_id
from localbrain.ingest import extensions
from . import storage


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
        """SELECT id, source_path FROM sessions WHERE source_id = ?
        AND NOT (
            sessions.session_class = 'maintenance'
            AND sessions.index_policy = 'metadata_only'
            AND sessions.external_id IN (
                SELECT 'localbrain-insight:' || id FROM personal_insight_runs
            )
        )""",
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
        storage._delete_source_owner(
            connection, session_id=int(row["id"])
        )
    extensions.session_sources_pruned(connection, source_id, valid)
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
    return bool(parsed.events or parsed.usage_records or parsed.skill_observations)


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
              AND NOT EXISTS (
                  SELECT 1 FROM skill_observations
                  JOIN sources AS skill_sources
                    ON skill_sources.id = skill_observations.source_id
                  WHERE skill_sources.id = sessions.source_id
                    AND skill_observations.external_session_id = sessions.external_id
                    AND skill_observations.state = 'observed'
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
    candidates = list(candidates)
    empty_paths = {str(path) for path, _ in candidates}
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
        extensions.empty_session_source(connection, source_id, source_path)

        session_rows = connection.execute(
            """
            SELECT id, source_path
            FROM sessions
            WHERE source_id = ?
              AND index_policy = 'full'
              AND (external_id = ? OR source_path = ?)
            """,
            (source_id, parsed.external_id, source_path),
        ).fetchall()
        for session_row in session_rows:
            session_id = int(session_row["id"])
            tracked_paths = connection.execute(
                "SELECT path FROM source_files WHERE session_id = ?",
                (session_id,),
            ).fetchall()
            if (
                session_row["source_path"] not in empty_paths
                or any(row["path"] not in empty_paths for row in tracked_paths)
            ):
                # An empty sibling cannot retire another owner, including a
                # meaningful source containing only admitted skill observations.
                continue
            # Only a confirmed empty owner can retire its old conversation.
            # Historical Usage remains independent evidence for the Session.
            connection.execute(
                "DELETE FROM activity_events WHERE session_id = ?", (session_id,)
            )
            connection.execute(
                "DELETE FROM search_index WHERE entity_type = 'session' AND entity_id = ?",
                (str(session_id),),
            )
            connection.execute(
                """UPDATE sessions SET event_count = 0, user_message_count = 0,
                   assistant_message_count = 0 WHERE id = ?""",
                (session_id,),
            )
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
            storage._delete_source_owner(
                connection, session_id=session_id
            )

        connection.execute(
            "DELETE FROM source_files WHERE source_id = ? AND path = ?",
            (source_id, source_path),
        )


def _store_parsed_usage(
    connection: sqlite3.Connection,
    *,
    source_id: int,
    session_id: int,
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
        cache=usage_cache,
    )


def _store_session(
    connection: sqlite3.Connection,
    source_id: int,
    parsed: ParsedSession,
    usage_contract_version: Optional[str] = None,
    provider_kind: Optional[str] = None,
    include_usage: bool = True,
    usage_cache: Optional[UsagePersistenceCache] = None,
) -> int:
    effective_provider_kind = provider_kind or connection.execute("SELECT provider_kind FROM sources WHERE id=?", (source_id,)).fetchone()["provider_kind"]
    workspace_id = storage._upsert_workspace(connection, parsed.cwd_raw, parsed.last_event_at)
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
            storage.utc_now(),
        ),
    )
    session_row = connection.execute(
        "SELECT id FROM sessions WHERE source_id = ? AND external_id = ?",
        (source_id, parsed.external_id),
    ).fetchone()
    session_id = int(session_row["id"])
    if include_usage:
        _store_parsed_usage(
            connection,
            source_id=source_id,
            session_id=session_id,
            provider_kind=effective_provider_kind,
            workspace_id=workspace_id,
            usage_contract_version=usage_contract_version,
            parsed=parsed,
            usage_cache=usage_cache,
        )
    event_ids = {(row["sequence"], row["event_type"], row["source_line"]): row["id"] for row in connection.execute(
        "SELECT id,sequence,event_type,source_line FROM activity_events WHERE session_id=?", (session_id,))}
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
                tool_name, source_line, message_phase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    event_ids.get((event.sequence, event.event_type, event.source_line),
                                  stable_id("source-event", source_id, event.event_id)),
                    session_id,
                    event.sequence,
                    event.occurred_at,
                    event.event_type,
                    event.role,
                    event.text,
                    event.tool_name,
                    event.source_line,
                    event.message_phase,
                )
                for event in parsed.events
            ],
        )
        body = "\n".join(event.text for event in parsed.events if event.text)
        if parsed.session_role == "primary":
            storage._replace_search_item(
                connection,
                "session",
                str(session_id),
                effective_provider_kind,
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
