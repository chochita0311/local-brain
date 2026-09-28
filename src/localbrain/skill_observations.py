"""Durable, source-backed skill load observations and first Insights projection."""

import sqlite3
from typing import Any, Dict

from .ingest.claude import CLAUDE_SESSION_CONTRACT_VERSION
from .ingest.codex import CODEX_SESSION_CONTRACT_VERSION
from .ingest.common import ParsedSession, stable_id


def normalized_skill_name(value: str) -> str:
    return value.strip().casefold()


def store_skill_observations(
    connection: sqlite3.Connection,
    *,
    source_key: str,
    provider_kind: str,
    parsed: ParsedSession,
) -> int:
    """Insert only new native events; never retract on ordinary source removal."""
    if parsed.session_class != "work":
        connection.execute(
            """
            UPDATE skill_observations SET state = 'corrected'
            WHERE source_key = ? AND external_session_id = ? AND state = 'observed'
            """,
            (source_key, parsed.external_id),
        )
        return 0
    inserted = 0
    for item in parsed.skill_observations:
        name = item.skill_name.strip()
        native_id = item.native_event_id.strip()
        if (
            not name
            or len(name) > 160
            or any(ord(character) < 32 for character in name)
            or not native_id
            or item.source_line <= 0
        ):
            continue
        group_key = normalized_skill_name(name)
        locator = item.skill_locator.strip() or None if item.skill_locator else None
        if locator and len(locator) > 4096:
            locator = None
        if connection.execute(
            """
            SELECT 1 FROM skill_observations
            WHERE source_key = ? AND external_session_id = ?
              AND native_event_id = ?
            LIMIT 1
            """,
            (source_key, parsed.external_id, native_id),
        ).fetchone():
            continue
        observation_id = stable_id(
            "skill-observation-v2", source_key, parsed.external_id, native_id
        )
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO skill_observations(
                id, source_key, provider_kind, external_session_id,
                native_event_id, skill_name, skill_group_key, skill_locator,
                signal_kind, source_line, occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                observation_id,
                source_key,
                provider_kind,
                parsed.external_id,
                native_id,
                name,
                group_key,
                locator,
                item.signal_kind,
                item.source_line,
                item.occurred_at,
            ),
        )
        inserted += cursor.rowcount
    return inserted


def correct_skill_observation(
    connection: sqlite3.Connection,
    *,
    source_key: str,
    external_session_id: str,
    native_event_id: str,
) -> int:
    """Invalidate one proven erroneous native event without touching missing files."""
    cursor = connection.execute(
        """
        UPDATE skill_observations SET state = 'corrected'
        WHERE source_key = ? AND external_session_id = ?
          AND native_event_id = ? AND state = 'observed'
        """,
        (source_key, external_session_id, native_event_id),
    )
    return cursor.rowcount


def skill_insights_data(connection: sqlite3.Connection) -> Dict[str, Any]:
    """Read a full all-time ranking without touching Session transcripts."""
    grouped = connection.execute(
        """
        SELECT skill_group_key, MIN(skill_name) AS skill_name,
               COUNT(*) AS use_count,
               strftime('%Y-%m-%dT%H:%M:%SZ', MAX(julianday(occurred_at)))
                   AS last_used_at
        FROM skill_observations
        WHERE state = 'observed'
        GROUP BY skill_group_key
        ORDER BY use_count DESC, skill_group_key ASC
        """
    ).fetchall()
    ranking = [
        {
            "rank": index,
            "name": row["skill_name"],
            "use_count": row["use_count"],
            "last_used_at": row["last_used_at"],
        }
        for index, row in enumerate(grouped, start=1)
    ]
    coverage = connection.execute(
        """
        SELECT COUNT(*) AS file_count,
               SUM(CASE WHEN source_files.status = 'ok'
                         AND (
                             (sources.provider_kind = 'claude'
                              AND source_files.session_contract_version = ?)
                             OR (sources.provider_kind = 'codex'
                                 AND source_files.session_contract_version = ?)
                         ) THEN 1 ELSE 0 END) AS current_file_count
        FROM source_files
        JOIN sources ON sources.id = source_files.source_id
        WHERE sources.provider_kind IN ('claude', 'codex')
        """,
        (
            CLAUDE_SESSION_CONTRACT_VERSION,
            CODEX_SESSION_CONTRACT_VERSION,
        ),
    ).fetchone()
    file_count = int(coverage["file_count"] or 0)
    current_count = int(coverage["current_file_count"] or 0)
    return {
        "ranking": ranking,
        "top": ranking[0] if ranking else None,
        "coverage": {
            "file_count": file_count,
            "current_file_count": current_count,
            "state": (
                "not_scanned"
                if file_count == 0
                else "partial"
                if current_count < file_count
                else "current"
            ),
        },
    }
