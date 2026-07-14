import re
import sqlite3
from typing import List, Optional


def dashboard_stats(connection: sqlite3.Connection) -> dict:
    result = {
        "sessions": connection.execute(
            "SELECT COUNT(*) AS count FROM sessions WHERE session_class = 'work'"
        ).fetchone()["count"],
        "events": connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM activity_events
            JOIN sessions ON sessions.id = activity_events.session_id
            WHERE sessions.session_class = 'work'
            """
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
    result["missing_workspaces"] = connection.execute(
        "SELECT COUNT(*) AS count FROM workspaces WHERE exists_now = 0"
    ).fetchone()["count"]
    result["recent_sessions"] = connection.execute(
        """
        SELECT COUNT(*) AS count FROM sessions
        WHERE session_class = 'work'
          AND datetime(last_event_at) >= datetime('now', '-7 days')
        """
    ).fetchone()["count"]
    result["active_workspaces"] = connection.execute(
        """
        SELECT COUNT(DISTINCT workspace_id) AS count FROM sessions
        WHERE workspace_id IS NOT NULL
          AND session_class = 'work'
          AND datetime(last_event_at) >= datetime('now', '-7 days')
        """
    ).fetchone()["count"]
    result["context_switches"] = connection.execute(
        """
        WITH ordered AS (
            SELECT workspace_id,
                   LAG(workspace_id) OVER (ORDER BY last_event_at) AS previous_workspace
            FROM sessions
            WHERE workspace_id IS NOT NULL
              AND session_class = 'work'
              AND datetime(last_event_at) >= datetime('now', '-7 days')
        )
        SELECT COUNT(*) AS count
        FROM ordered
        WHERE previous_workspace IS NOT NULL
          AND workspace_id != previous_workspace
        """
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
        SELECT sources.kind, sources.name,
               COUNT(DISTINCT sessions.id) AS session_count,
               COUNT(activity_events.id) AS event_count,
               MAX(sessions.last_event_at) AS last_activity_at
        FROM sources
        LEFT JOIN sessions ON sessions.source_id = sources.id
            AND sessions.session_class = 'work'
        LEFT JOIN activity_events ON activity_events.session_id = sessions.id
        WHERE sources.kind IN ('claude', 'codex')
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
        GROUP BY workspaces.id
        ORDER BY session_count DESC, last_activity_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def recent_sessions(
    connection: sqlite3.Connection,
    source_kind: Optional[str] = None,
    workspace_id: Optional[int] = None,
    limit: int = 100,
) -> List[sqlite3.Row]:
    conditions = ["sessions.session_class = 'work'"]
    params = []
    if source_kind:
        conditions.append("sources.kind = ?")
        params.append(source_kind)
    if workspace_id:
        conditions.append("sessions.workspace_id = ?")
        params.append(workspace_id)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limit)
    return connection.execute(
        """
        SELECT
            sessions.*,
            sources.kind AS source_kind,
            sources.name AS source_name,
            workspaces.display_name AS workspace_name,
            workspaces.canonical_path AS workspace_path,
            workspaces.git_root,
            workspaces.git_branch,
            workspaces.exists_now
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        {where}
        ORDER BY COALESCE(sessions.last_event_at, sessions.started_at) DESC
        LIMIT ?
        """.format(where=where),
        tuple(params),
    ).fetchall()


def recent_documents(connection: sqlite3.Connection, limit: int = 8):
    return connection.execute(
        """
        SELECT context_documents.id, context_documents.title,
               context_documents.relative_path, context_documents.path,
               context_documents.mtime_ns
        FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
        ORDER BY mtime_ns DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def context_documents(
    connection: sqlite3.Connection, root_id: Optional[int] = None, limit: int = 240
):
    if root_id is not None:
        return connection.execute(
            """
            SELECT context_documents.id, context_documents.title,
                   context_documents.relative_path, context_documents.path,
                   context_documents.size_bytes, context_documents.mtime_ns,
                   context_roots.label AS root_label,
                   context_roots.path AS root_path
            FROM context_documents
            JOIN context_roots ON context_roots.id = context_documents.context_root_id
            WHERE context_roots.enabled = 1 AND context_roots.id = ?
            ORDER BY context_documents.mtime_ns DESC
            LIMIT ?
            """,
            (root_id, limit),
        ).fetchall()
    return connection.execute(
        """
        SELECT context_documents.id, context_documents.title,
               context_documents.relative_path, context_documents.path,
               context_documents.size_bytes, context_documents.mtime_ns,
               context_roots.label AS root_label,
               context_roots.path AS root_path
        FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
        ORDER BY context_documents.mtime_ns DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def project_activity(connection: sqlite3.Connection):
    return connection.execute(
        """
        SELECT workspaces.id, workspaces.display_name, workspaces.canonical_path,
               workspaces.git_root, workspaces.git_branch, workspaces.exists_now,
               (SELECT COUNT(*) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work') AS session_count,
               (SELECT COUNT(*) FROM context_documents
                LEFT JOIN context_roots
                  ON context_roots.id = context_documents.context_root_id
                WHERE context_documents.workspace_id = workspaces.id
                  AND (context_documents.context_root_id IS NULL
                       OR context_roots.enabled = 1)) AS document_count,
               (SELECT COALESCE(SUM(event_count), 0) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work') AS event_count,
               (SELECT MAX(last_event_at) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work') AS last_activity_at,
               (SELECT COUNT(DISTINCT source_id) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work') AS source_count
        FROM workspaces
        WHERE EXISTS (
            SELECT 1 FROM sessions
            WHERE sessions.workspace_id = workspaces.id
              AND sessions.session_class = 'work'
        ) OR workspaces.git_root IS NOT NULL
        ORDER BY last_activity_at DESC, workspaces.display_name
        """
    ).fetchall()


def source_inventory(connection: sqlite3.Connection):
    return connection.execute(
        """
        SELECT sources.id, sources.kind, sources.name, sources.root_path,
               sources.enabled, sources.last_scanned_at,
               COUNT(DISTINCT source_files.id) AS file_count,
               COUNT(DISTINCT CASE WHEN sessions.session_class = 'work'
                     THEN sessions.id END) AS session_count,
               COUNT(DISTINCT CASE
                     WHEN context_documents.context_root_id IS NULL
                       OR context_roots.enabled = 1
                     THEN context_documents.id END) AS document_count,
               COUNT(DISTINCT CASE WHEN source_files.status != 'ok'
                     THEN source_files.id END) AS error_count
        FROM sources
        LEFT JOIN source_files ON source_files.source_id = sources.id
        LEFT JOIN sessions ON sessions.source_id = sources.id
        LEFT JOIN context_documents ON context_documents.source_id = sources.id
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        GROUP BY sources.id
        ORDER BY sources.name
        """
    ).fetchall()


def session_detail(connection: sqlite3.Connection, session_id: int):
    return connection.execute(
        """
        SELECT sessions.*, sources.kind AS source_kind, sources.name AS source_name,
               workspaces.display_name AS workspace_name,
               workspaces.canonical_path AS workspace_path,
               workspaces.git_root, workspaces.git_branch, workspaces.exists_now
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.id = ?
        """,
        (session_id,),
    ).fetchone()


def session_events(connection: sqlite3.Connection, session_id: int, limit: int = 600):
    return connection.execute(
        """
        SELECT * FROM activity_events
        WHERE session_id = ?
        ORDER BY sequence
        LIMIT ?
        """,
        (session_id, limit),
    ).fetchall()


def document_detail(connection: sqlite3.Connection, document_id: int):
    return connection.execute(
        """
        SELECT context_documents.*, sources.name AS source_name,
               workspaces.display_name AS workspace_name,
               context_roots.label AS context_root_label,
               context_roots.path AS context_root_path
        FROM context_documents
        JOIN sources ON sources.id = context_documents.source_id
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        LEFT JOIN workspaces ON workspaces.id = context_documents.workspace_id
        WHERE context_documents.id = ?
        """,
        (document_id,),
    ).fetchone()


def _fts_expression(query: str) -> str:
    tokens = re.findall(r"[\w.-]+", query, flags=re.UNICODE)
    return " AND ".join('"{}"'.format(token.replace('"', '""')) for token in tokens[:12])


def search(connection: sqlite3.Connection, query: str, limit: int = 80):
    expression = _fts_expression(query)
    if not expression:
        return []
    return connection.execute(
        """
        SELECT entity_type, entity_id, source_kind, title, path,
               snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
               bm25(search_index) AS score
        FROM search_index
        WHERE search_index MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (expression, limit),
    ).fetchall()
