import re
import sqlite3
from typing import List, Optional


SESSION_PAGE_SIZE = 15


def pagination_items(current_page: int, total_pages: int) -> List[Optional[int]]:
    """Return a compact, ordered page list with ``None`` as an ellipsis."""
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    window_start = max(2, current_page - 1)
    window_end = min(total_pages - 1, current_page + 1)
    if current_page <= 3:
        window_end = 4
    elif current_page >= total_pages - 2:
        window_start = total_pages - 3

    items: List[Optional[int]] = [1]
    if window_start > 2:
        items.append(None)
    items.extend(range(window_start, window_end + 1))
    if window_end < total_pages - 1:
        items.append(None)
    items.append(total_pages)
    return items


def compact_pagination_items(
    current_page: int, total_pages: int
) -> List[Optional[int]]:
    """Return at most five pagination tokens for the narrow viewport."""
    if total_pages <= 5:
        return list(range(1, total_pages + 1))
    if current_page <= 2:
        return [1, 2, 3, None, total_pages]
    if current_page >= total_pages - 1:
        return [1, None, total_pages - 2, total_pages - 1, total_pages]
    return [1, None, current_page, None, total_pages]


def dashboard_stats(connection: sqlite3.Connection) -> dict:
    result = {
        "sessions": connection.execute(
            "SELECT COUNT(*) AS count FROM sessions "
            "WHERE session_class = 'work' AND session_role = 'primary'"
        ).fetchone()["count"],
        "events": connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM activity_events
            JOIN sessions ON sessions.id = activity_events.session_id
            WHERE sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
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
          AND session_role = 'primary'
          AND datetime(last_event_at) >= datetime('now', '-7 days')
        """
    ).fetchone()["count"]
    result["active_workspaces"] = connection.execute(
        """
        SELECT COUNT(DISTINCT workspace_id) AS count FROM sessions
        WHERE workspace_id IS NOT NULL
          AND session_class = 'work'
          AND session_role = 'primary'
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
              AND session_role = 'primary'
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
        SELECT sources.kind, sources.name,
               COUNT(DISTINCT sessions.id) AS session_count,
               COUNT(activity_events.id) AS event_count,
               MAX(sessions.last_event_at) AS last_activity_at
        FROM sources
        LEFT JOIN sessions ON sessions.source_id = sources.id
            AND sessions.session_class = 'work'
            AND sessions.session_role = 'primary'
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


def recent_sessions(
    connection: sqlite3.Connection,
    source_kind: Optional[str] = None,
    workspace_id: Optional[int] = None,
    limit: int = 100,
) -> List[sqlite3.Row]:
    conditions = [
        "sessions.session_class = 'work'",
        "sessions.session_role = 'primary'",
    ]
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


def session_inventory_page(
    connection: sqlite3.Connection,
    source_kind: Optional[str] = None,
    workspace_id: Optional[int] = None,
    page: int = 1,
) -> dict:
    conditions = [
        "sessions.session_class = 'work'",
        "sessions.session_role = 'primary'",
    ]
    params = []
    if source_kind:
        conditions.append("sources.kind = ?")
        params.append(source_kind)
    if workspace_id is not None:
        conditions.append("sessions.workspace_id = ?")
        params.append(workspace_id)
    where = " AND ".join(conditions)
    total = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        WHERE {where}
        """.format(where=where),
        tuple(params),
    ).fetchone()["count"]
    total_pages = max(1, (total + SESSION_PAGE_SIZE - 1) // SESSION_PAGE_SIZE)
    bounded_page = min(max(page, 1), total_pages)
    offset = (bounded_page - 1) * SESSION_PAGE_SIZE
    rows = connection.execute(
        """
        SELECT
            sessions.*,
            sources.kind AS source_kind,
            sources.name AS source_name,
            workspaces.display_name AS workspace_name,
            workspaces.canonical_path AS workspace_path,
            workspaces.git_root,
            workspaces.exists_now
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE {where}
        ORDER BY COALESCE(sessions.last_event_at, sessions.started_at) DESC,
                 sessions.id DESC
        LIMIT ? OFFSET ?
        """.format(where=where),
        tuple(params + [SESSION_PAGE_SIZE, offset]),
    ).fetchall()
    items = [dict(row) for row in rows]
    parent_ids = [item["id"] for item in items]
    children_by_parent = {parent_id: [] for parent_id in parent_ids}
    if parent_ids:
        placeholders = ", ".join("?" for _ in parent_ids)
        child_rows = connection.execute(
            """
            SELECT children.*, sources.kind AS source_kind,
                   sources.name AS source_name,
                   workspaces.display_name AS workspace_name,
                   workspaces.canonical_path AS workspace_path,
                   workspaces.exists_now
            FROM sessions AS children
            JOIN sessions AS parents ON parents.id = children.parent_session_id
            JOIN sources ON sources.id = children.source_id
            LEFT JOIN workspaces ON workspaces.id = children.workspace_id
            WHERE children.parent_session_id IN ({placeholders})
              AND children.session_class = 'work'
              AND children.session_role = 'subsession'
              AND parents.session_class = 'work'
              AND parents.session_role = 'primary'
              AND parents.source_id = children.source_id
            ORDER BY children.parent_session_id,
                     COALESCE(children.last_event_at, children.started_at) DESC,
                     children.id DESC
            """.format(placeholders=placeholders),
            tuple(parent_ids),
        ).fetchall()
        for row in child_rows:
            children_by_parent[row["parent_session_id"]].append(dict(row))
    for item in items:
        item["subsessions"] = children_by_parent[item["id"]]

    return {
        "items": items,
        "total": total,
        "page": bounded_page,
        "page_size": SESSION_PAGE_SIZE,
        "total_pages": total_pages,
        "page_items": pagination_items(bounded_page, total_pages),
        "compact_page_items": compact_pagination_items(bounded_page, total_pages),
        "previous_page": bounded_page - 1 if bounded_page > 1 else None,
        "next_page": bounded_page + 1 if bounded_page < total_pages else None,
    }


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
               workspaces.git_root, workspaces.exists_now,
               (SELECT COUNT(*) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work'
                  AND sessions.session_role = 'primary') AS session_count,
               (SELECT COUNT(*) FROM context_documents
                LEFT JOIN context_roots
                  ON context_roots.id = context_documents.context_root_id
                WHERE context_documents.workspace_id = workspaces.id
                  AND (context_documents.context_root_id IS NULL
                       OR context_roots.enabled = 1)) AS document_count,
               (SELECT COALESCE(SUM(event_count), 0) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work'
                  AND sessions.session_role = 'primary') AS event_count,
               (SELECT MAX(last_event_at) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work'
                  AND sessions.session_role = 'primary') AS last_activity_at,
               (SELECT COUNT(DISTINCT source_id) FROM sessions
                WHERE sessions.workspace_id = workspaces.id
                  AND sessions.session_class = 'work'
                  AND sessions.session_role = 'primary') AS source_count
        FROM workspaces
        WHERE EXISTS (
            SELECT 1 FROM sessions
            WHERE sessions.workspace_id = workspaces.id
              AND sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
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
                                      AND sessions.session_role = 'primary'
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
               workspaces.git_root, workspaces.exists_now
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        LEFT JOIN sessions AS parent_sessions
          ON parent_sessions.id = sessions.parent_session_id
        WHERE sessions.id = ?
          AND sessions.session_class = 'work'
          AND (
            sessions.session_role = 'primary'
            OR (
              sessions.session_role = 'subsession'
              AND parent_sessions.session_role = 'primary'
              AND parent_sessions.source_id = sessions.source_id
            )
          )
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


def session_conversation_events(connection: sqlite3.Connection, session_id: int):
    """Return the message-only presentation timeline without mutating raw events."""
    return connection.execute(
        """
        SELECT * FROM activity_events
        WHERE session_id = ? AND event_type = 'message'
        ORDER BY sequence, id
        """,
        (session_id,),
    ).fetchall()


def session_parent(connection: sqlite3.Connection, session_id: int):
    return connection.execute(
        """
        SELECT parents.*, sources.kind AS source_kind,
               sources.name AS source_name,
               workspaces.display_name AS workspace_name,
               workspaces.canonical_path AS workspace_path,
               workspaces.git_root, workspaces.exists_now
        FROM sessions AS children
        JOIN sessions AS parents ON parents.id = children.parent_session_id
        JOIN sources ON sources.id = parents.source_id
        LEFT JOIN workspaces ON workspaces.id = parents.workspace_id
        WHERE children.id = ?
          AND children.session_class = 'work'
          AND children.session_role = 'subsession'
          AND parents.session_class = 'work'
          AND parents.session_role = 'primary'
          AND parents.source_id = children.source_id
        """,
        (session_id,),
    ).fetchone()


def session_subsessions(connection: sqlite3.Connection, session_id: int):
    return connection.execute(
        """
        SELECT children.*, sources.kind AS source_kind,
               sources.name AS source_name,
               workspaces.display_name AS workspace_name,
               workspaces.canonical_path AS workspace_path,
               workspaces.git_root, workspaces.exists_now
        FROM sessions AS parents
        JOIN sessions AS children ON children.parent_session_id = parents.id
        JOIN sources ON sources.id = children.source_id
        LEFT JOIN workspaces ON workspaces.id = children.workspace_id
        WHERE parents.id = ?
          AND parents.session_class = 'work'
          AND parents.session_role = 'primary'
          AND children.session_class = 'work'
          AND children.session_role = 'subsession'
          AND children.source_id = parents.source_id
        ORDER BY COALESCE(children.last_event_at, children.started_at) DESC,
                 children.id DESC
        """,
        (session_id,),
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


def search(
    connection: sqlite3.Connection,
    query: str,
    limit: int = 80,
    *,
    source_scope: str = "all",
    atlassian_filters: Optional[dict] = None,
):
    expression = _fts_expression(query)
    if not expression:
        return []
    results = []
    if source_scope != "atlassian":
        entity_filter = {
            "sessions": "AND entity_type = 'session'",
            "documents": "AND entity_type = 'document'",
        }.get(source_scope, "AND entity_type IN ('session', 'document')")
        results.extend(
            dict(row)
            for row in connection.execute(
                """
                SELECT entity_type, entity_id, source_kind, title, path,
                       snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
                       bm25(search_index) AS score
                FROM search_index
                WHERE search_index MATCH ?
                  {entity_filter}
                ORDER BY score
                LIMIT ?
                """.format(entity_filter=entity_filter),
                (expression, limit),
            ).fetchall()
        )
    if source_scope not in {"sessions", "documents"}:
        from .atlassian_browse import atlassian_search_results

        results.extend(
            atlassian_search_results(
                connection,
                query,
                atlassian_filters,
                limit=limit,
            )
        )
    return sorted(
        results,
        key=lambda result: (
            result.get("score", 0),
            result.get("title") or "",
            result.get("entity_id") or "",
        ),
    )[:limit]
