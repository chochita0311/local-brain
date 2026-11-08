"""User-owned Session titles; imported title and provenance stay source-owned."""

import sqlite3


class SessionTitleError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def set_display_title(connection: sqlite3.Connection, session_id: int, value: str) -> dict:
    if not isinstance(value, str):
        raise SessionTitleError("invalid-title")
    value = value.strip()
    if len(value) > 500 or any(ord(char) < 32 or char in "\x85\u2028\u2029" for char in value):
        raise SessionTitleError("invalid-title")
    row = connection.execute(
        "SELECT id, title, session_class, session_role FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if row is None:
        raise SessionTitleError("session-not-found")
    if row["session_class"] != "work" or row["session_role"] != "primary":
        raise SessionTitleError("ineligible-session")
    override = value or None
    connection.execute("UPDATE sessions SET display_title = ? WHERE id = ?", (override, session_id))
    return {"id": row["id"], "title": row["title"], "display_title": override,
            "effective_title": override or row["title"]}
