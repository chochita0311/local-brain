import sqlite3
from typing import Any, Dict
from localbrain.ingest.contracts import CLAUDE_SESSION_REVISION, CODEX_SESSION_REVISION


def skill_insights_data(connection: sqlite3.Connection) -> Dict[str, Any]:
    """Read a full all-time ranking without touching Session transcripts."""
    grouped = connection.execute(
        """
        WITH reference_sessions AS (
            SELECT skill_group_key, MIN(skill_name) AS skill_name,
                   MAX(julianday(occurred_at)) AS occurred_at
            FROM skill_observations
            WHERE state = 'observed'
            GROUP BY source_id, external_session_id, skill_group_key
        )
        SELECT skill_group_key, MIN(skill_name) AS skill_name,
               COUNT(*) AS use_count,
               strftime('%Y-%m-%dT%H:%M:%SZ', MAX(occurred_at))
                   AS last_used_at
        FROM reference_sessions
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
            CLAUDE_SESSION_REVISION,
            CODEX_SESSION_REVISION,
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
