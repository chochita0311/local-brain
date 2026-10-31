import sqlite3
from typing import Optional


def dashboard_stats(
    connection: sqlite3.Connection, source_id: Optional[str] = None
) -> dict:
    source_condition = (
        " AND sessions.source_id = ?"
        if source_id
        else ""
    )
    source_params = (source_id,) if source_id else ()
    result = {
        "sessions": connection.execute(
            "SELECT COUNT(*) AS count FROM sessions "
            "WHERE session_class = 'work' AND session_role = 'primary'"
            + source_condition,
            source_params,
        ).fetchone()["count"],
        "events": connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM activity_events
            JOIN sessions ON sessions.id = activity_events.session_id
            WHERE sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
            """ + source_condition,
            source_params,
        ).fetchone()["count"],
        "documents": connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM context_documents
            LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
            WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
            """
        ).fetchone()["count"],
        "workspaces": connection.execute(
            "SELECT COUNT(*) AS count FROM workspaces"
        ).fetchone()["count"],
    }
    if source_id:
        result["missing_workspaces"] = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM workspaces
            WHERE exists_now = 0
              AND EXISTS (
                  SELECT 1 FROM sessions
                  WHERE sessions.workspace_id = workspaces.id
                    AND sessions.session_class = 'work'
                    AND sessions.session_role = 'primary'
            """ + source_condition + ")",
            source_params,
        ).fetchone()["count"]
    else:
        result["missing_workspaces"] = connection.execute(
            "SELECT COUNT(*) AS count FROM workspaces WHERE exists_now = 0"
        ).fetchone()["count"]
    result["recent_sessions"] = connection.execute(
        """
        SELECT COUNT(*) AS count FROM sessions
        WHERE session_class = 'work'
          AND session_role = 'primary'
          AND datetime(last_event_at) >= datetime('now', '-7 days')
        """ + source_condition,
        source_params,
    ).fetchone()["count"]
    result["active_workspaces"] = connection.execute(
        """
        SELECT COUNT(DISTINCT workspace_id) AS count FROM sessions
        WHERE workspace_id IS NOT NULL
          AND session_class = 'work'
          AND session_role = 'primary'
          AND datetime(last_event_at) >= datetime('now', '-7 days')
        """ + source_condition,
        source_params,
    ).fetchone()["count"]
    result["context_switches"] = connection.execute(
        """
        WITH ordered AS (
            SELECT workspace_id,
                   LAG(workspace_id) OVER (ORDER BY last_event_at) AS previous_workspace
            FROM sessions
            WHERE workspace_id IS NOT NULL
              AND session_class = 'work'
              AND session_role = 'primary'
              AND datetime(last_event_at) >= datetime('now', '-7 days')
        """ + source_condition + """
        )
        SELECT COUNT(*) AS count
        FROM ordered
        WHERE previous_workspace IS NOT NULL
          AND workspace_id != previous_workspace
        """,
        source_params,
    ).fetchone()["count"]
    return result


def daily_activity(connection: sqlite3.Connection, days: int = 14):
    return connection.execute(
        """
        WITH RECURSIVE dates(day, position) AS (
            SELECT date('now', ?), 1
            UNION ALL
            SELECT date(day, '+1 day'), position + 1
            FROM dates
            WHERE position < ?
        ), activity AS (
            SELECT date(last_event_at) AS day, COUNT(*) AS session_count
            FROM sessions
            WHERE last_event_at IS NOT NULL AND session_class = 'work'
              AND session_role = 'primary'
            GROUP BY date(last_event_at)
        )
        SELECT dates.day, COALESCE(activity.session_count, 0) AS session_count
        FROM dates
        LEFT JOIN activity ON activity.day = dates.day
        ORDER BY dates.day
        """,
        ("-{} days".format(days - 1), days),
    ).fetchall()


def source_activity(connection: sqlite3.Connection):
    return connection.execute(
        """
        SELECT sources.id, sources.provider_kind, sources.name,
               COUNT(DISTINCT sessions.id) AS session_count,
               COUNT(activity_events.id) AS event_count,
               MAX(sessions.last_event_at) AS last_activity_at
        FROM sources
        LEFT JOIN sessions ON sessions.source_id = sources.id
            AND sessions.session_class = 'work'
            AND sessions.session_role = 'primary'
        LEFT JOIN activity_events ON activity_events.session_id = sessions.id
        WHERE sources.provider_kind IN ('claude', 'codex')
        GROUP BY sources.id
        ORDER BY event_count DESC
        """
    ).fetchall()


def top_tools(connection: sqlite3.Connection, limit: int = 8):
    return connection.execute(
        """
        SELECT tool_name, COUNT(*) AS use_count
        FROM activity_events
        JOIN sessions ON sessions.id = activity_events.session_id
        WHERE event_type = 'tool_call' AND tool_name IS NOT NULL
          AND sessions.session_class = 'work'
          AND sessions.session_role = 'primary'
        GROUP BY tool_name
        ORDER BY use_count DESC, tool_name
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def top_workspace_activity(connection: sqlite3.Connection, limit: int = 8):
    return connection.execute(
        """
        SELECT workspaces.id, workspaces.display_name, workspaces.canonical_path,
               workspaces.git_root, workspaces.exists_now,
               COUNT(sessions.id) AS session_count,
               COALESCE(SUM(sessions.event_count), 0) AS event_count,
               MAX(sessions.last_event_at) AS last_activity_at
        FROM workspaces
        JOIN sessions ON sessions.workspace_id = workspaces.id
            AND sessions.session_class = 'work'
            AND sessions.session_role = 'primary'
        GROUP BY workspaces.id
        ORDER BY session_count DESC, last_activity_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
