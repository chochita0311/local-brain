import sqlite3
from localbrain.ingest.contracts import ParsedSession
from localbrain.ingest.common import stable_id


"""Durable skill evidence and use/reference Session counts for Insights."""


def normalized_skill_name(value: str) -> str:
    return value.strip().casefold()


def store_skill_observations(
    connection: sqlite3.Connection,
    *,
    source_id: int,
    provider_kind: str,
    parsed: ParsedSession,
) -> int:
    """Insert only new native events; never retract on ordinary source removal."""
    if parsed.session_class != "work":
        connection.execute(
            """
            UPDATE skill_observations SET state = 'corrected'
            WHERE source_id = ? AND external_session_id = ? AND state = 'observed'
            """,
            (source_id, parsed.external_id),
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
        multiple_skills = item.signal_kind.endswith(("_read", "_declaration", "_mention", "_script"))
        legacy_id = ("declaration:" + native_id[len("mention:"):]
                     if item.signal_kind.endswith("_mention") and native_id.startswith("mention:")
                     else native_id)
        existing = connection.execute(
            """
            SELECT id, request_key FROM skill_observations
            WHERE source_id = ? AND external_session_id = ?
              AND native_event_id IN (?, ?)
              AND (? = 0 OR skill_group_key = ?)
            LIMIT 1
            """,
            (source_id, parsed.external_id, native_id, legacy_id, int(multiple_skills), group_key),
        ).fetchone()
        request_key = item.request_key
        if request_key is not None and (not request_key or len(request_key) > 160):
            request_key = None
        if existing:
            if existing["request_key"] is None and request_key:
                connection.execute(
                    "UPDATE skill_observations SET request_key = ? WHERE id = ?",
                    (request_key, existing["id"]),
                )
            continue
        observation_id = stable_id(
            ("skill-observation-declaration-v1" if item.signal_kind.endswith("_declaration")
             else "skill-observation-reference-v1" if item.signal_kind.endswith(("_mention", "_script"))
             else "skill-observation-read-v1" if multiple_skills else "skill-observation-v2"),
            source_id, parsed.external_id, native_id,
            *([group_key] if multiple_skills else []),
        )
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO skill_observations(
                id, source_id, provider_kind, external_session_id,
                native_event_id, skill_name, skill_group_key, skill_locator,
                signal_kind, source_line, occurred_at, request_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                observation_id,
                source_id,
                provider_kind,
                parsed.external_id,
                native_id,
                name,
                group_key,
                locator,
                item.signal_kind,
                item.source_line,
                item.occurred_at,
                request_key,
            ),
        )
        inserted += cursor.rowcount
    return inserted


def correct_skill_observation(
    connection: sqlite3.Connection,
    *,
    source_id: int,
    external_session_id: str,
    native_event_id: str,
) -> int:
    """Invalidate one proven erroneous native event without touching missing files."""
    cursor = connection.execute(
        """
        UPDATE skill_observations SET state = 'corrected'
        WHERE source_id = ? AND external_session_id = ?
          AND native_event_id = ? AND state = 'observed'
        """,
        (source_id, external_session_id, native_event_id),
    )
    return cursor.rowcount
