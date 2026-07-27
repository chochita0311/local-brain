import sqlite3
from typing import List, Optional

from .workstreams import utc_now


class SessionPinError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _eligible_session(connection: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT id, session_class, session_role
        FROM sessions
        WHERE id = ?
        """,
        (session_id,),
    ).fetchone()
    if row is None:
        raise SessionPinError("session-not-found", "Session not found.")
    if row["session_class"] != "work":
        raise SessionPinError(
            "maintenance-session-ineligible",
            "Maintenance Sessions cannot be pinned.",
        )
    if row["session_role"] != "primary":
        raise SessionPinError(
            "subsession-ineligible",
            "Subsessions cannot be pinned.",
        )
    return row


def pin_session(
    connection: sqlite3.Connection,
    session_id: int,
    *,
    pinned_at: Optional[str] = None,
) -> sqlite3.Row:
    _eligible_session(connection, session_id)
    timestamp = (pinned_at or utc_now()).strip()
    if not timestamp:
        raise SessionPinError("invalid-pinned-at", "Pin time is required.")
    connection.execute(
        """
        INSERT INTO session_pins(session_id, pinned_at)
        VALUES (?, ?)
        ON CONFLICT(session_id) DO NOTHING
        """,
        (session_id, timestamp),
    )
    return connection.execute(
        "SELECT session_id, pinned_at FROM session_pins WHERE session_id = ?",
        (session_id,),
    ).fetchone()


def unpin_session(connection: sqlite3.Connection, session_id: int) -> bool:
    cursor = connection.execute(
        "DELETE FROM session_pins WHERE session_id = ?",
        (session_id,),
    )
    return cursor.rowcount > 0


def is_session_pinned(connection: sqlite3.Connection, session_id: int) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM session_pins WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        is not None
    )


_PINNED_SESSION_SELECT = """
        SELECT
            sessions.id,
            sessions.title,
            sessions.last_event_at,
            sessions.started_at,
            sessions.cwd_raw,
            sessions.source_path,
            sessions.workspace_id,
            sources.kind AS source_kind,
            sources.name AS source_name,
            workspaces.display_name AS workspace_name,
            workspaces.canonical_path AS workspace_path,
            workspaces.exists_now AS workspace_exists_now,
            session_pins.pinned_at
        FROM session_pins
        JOIN sessions ON sessions.id = session_pins.session_id
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.session_class = 'work'
          AND sessions.session_role = 'primary'
        ORDER BY
            COALESCE(sessions.last_event_at, sessions.started_at) DESC,
            session_pins.pinned_at DESC,
            sessions.id DESC
"""


def list_pinned_sessions(
    connection: sqlite3.Connection,
    *,
    limit: int = 8,
) -> List[sqlite3.Row]:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise SessionPinError(
            "invalid-limit",
            "Pinned Session limit must be between 1 and 100.",
        )
    return connection.execute(
        _PINNED_SESSION_SELECT + "\nLIMIT ?",
        (limit,),
    ).fetchall()


def list_all_pinned_sessions(
    connection: sqlite3.Connection,
) -> List[sqlite3.Row]:
    return connection.execute(_PINNED_SESSION_SELECT).fetchall()
