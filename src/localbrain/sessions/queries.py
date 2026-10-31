import posixpath
import sqlite3
from pathlib import Path
from typing import List, Optional
from localbrain.sessions.activity import parse_timestamp
from localbrain.foundation.paths import home_relative_path
from localbrain.foundation.pagination import compact_pagination_items
from localbrain.foundation.pagination import pagination_items


SESSION_PAGE_SIZE = 15


def recent_sessions(
    connection: sqlite3.Connection,
    source_id: Optional[str] = None,
    workspace_id: Optional[int] = None,
    limit: int = 100,
) -> List[sqlite3.Row]:
    conditions = [
        "sessions.session_class = 'work'",
        "sessions.session_role = 'primary'",
    ]
    params = []
    if source_id:
        conditions.append("sources.id = ?")
        params.append(source_id)
    if workspace_id:
        conditions.append("sessions.workspace_id = ?")
        params.append(workspace_id)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limit)
    return connection.execute(
        """
        SELECT
            sessions.*,

            sources.provider_kind,
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
    source_id: Optional[str] = None,
    workspace_id: Optional[int] = None,
    page: int = 1,
) -> dict:
    conditions = [
        "sessions.session_class = 'work'",
        "sessions.session_role = 'primary'",
    ]
    params = []
    if source_id:
        conditions.append("sources.id = ?")
        params.append(source_id)
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

            sources.provider_kind,
            sources.name AS source_name,
            workspaces.display_name AS workspace_name,
            workspaces.canonical_path AS workspace_path,
            workspaces.git_root,
            workspaces.exists_now,
            session_pins.pinned_at
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        LEFT JOIN session_pins ON session_pins.session_id = sessions.id
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
            SELECT children.*,
                   sources.provider_kind,
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


def session_chart_inventory(
    connection: sqlite3.Connection,
    source_id: Optional[str] = None,
    workspace_id: Optional[int] = None,
) -> list:
    """Read the complete inventory's metadata without pagination or inference."""
    conditions = [
        "sessions.session_class = 'work'",
        "sessions.session_role = 'primary'",
    ]
    params = []
    if source_id:
        conditions.append("sources.id = ?")
        params.append(source_id)
    if workspace_id is not None:
        conditions.append("sessions.workspace_id = ?")
        params.append(workspace_id)
    rows = connection.execute(
        """
        SELECT sessions.id, sessions.source_id, sessions.title, sessions.started_at,
               sessions.last_event_at, sessions.cwd_raw, sessions.git_branch,
                sources.provider_kind,
               sources.name AS source_name
        FROM sessions JOIN sources ON sources.id = sessions.source_id
        WHERE {where}
        ORDER BY sessions.id
        """.format(where=" AND ".join(conditions)),
        tuple(params),
    ).fetchall()
    items = []
    home = str(Path.home())
    for row in rows:
        item = dict(row)
        cwd = row["cwd_raw"]
        if cwd == "~" or (cwd and cwd.startswith("~/")):
            cwd = home + cwd[1:]
        folder = posixpath.normpath(cwd) if cwd else ""
        item["project_key"] = folder
        item["project_name"] = (
            "~" if folder == home
            else posixpath.basename(folder) or folder or "실행 폴더 없음"
        )
        item["project_path"] = home_relative_path(folder)
        times = [
            parsed for parsed in (
                parse_timestamp(row["last_event_at"]),
                parse_timestamp(row["started_at"]),
            ) if parsed is not None
        ]
        time_source = "metadata"
        if not times:
            # Only undated metadata needs an Event fallback; never read bodies.
            times = [
                parsed for event in connection.execute(
                    "SELECT occurred_at FROM activity_events WHERE session_id = ?",
                    (row["id"],),
                ) if (parsed := parse_timestamp(event["occurred_at"])) is not None
            ]
            time_source = "event"
        item["first_observed_at"] = min(times).isoformat() if times else None
        item["observed_at"] = max(times).isoformat() if times else None
        item["time_source"] = time_source if times else None
        items.append(item)
    return items


def session_chart_activity(
    connection: sqlite3.Connection, session_id: int
) -> Optional[dict]:
    """Return retained timestamp occurrences for an eligible primary Session."""
    session = connection.execute(
        """
        SELECT id, started_at, last_event_at FROM sessions
        WHERE id = ? AND session_class = 'work' AND session_role = 'primary'
        """,
        (session_id,),
    ).fetchone()
    if session is None:
        return None
    times = []
    undated = 0
    for row in connection.execute(
        "SELECT occurred_at FROM activity_events WHERE session_id = ?",
        (session_id,),
    ):
        parsed = parse_timestamp(row["occurred_at"])
        if parsed is None:
            undated += 1
        else:
            times.append(parsed)
    metadata = []
    for field in ("started_at", "last_event_at"):
        parsed = parse_timestamp(session[field])
        if parsed is not None:
            metadata.append({"field": field, "at": parsed.isoformat()})
    return {
        "session_id": session_id,
        "timestamps": [value.isoformat() for value in sorted(times)],
        "total_events": len(times) + undated,
        "undated_events": undated,
        "metadata_times": metadata,
    }


def project_activity(
    connection: sqlite3.Connection, source_id: Optional[str] = None
):
    source_condition = "AND sources.id = ?" if source_id else ""
    params = (source_id,) if source_id else ()
    workspace_condition = (
        "session_activity.workspace_id IS NOT NULL"
        if source_id
        else "session_activity.workspace_id IS NOT NULL OR workspaces.git_root IS NOT NULL"
    )
    return connection.execute(
        """
        WITH session_activity AS (
            SELECT sessions.workspace_id,
                   COUNT(*) AS session_count,
                   COALESCE(SUM(sessions.event_count), 0) AS event_count,
                   MAX(sessions.last_event_at) AS last_activity_at,
                   COUNT(DISTINCT sessions.source_id) AS source_count
            FROM sessions
            JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.workspace_id IS NOT NULL
              AND sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
              {source_condition}
            GROUP BY sessions.workspace_id
        )
        SELECT workspaces.id, workspaces.display_name, workspaces.canonical_path,
               workspaces.git_root, workspaces.exists_now,
               COALESCE(session_activity.session_count, 0) AS session_count,
               (SELECT COUNT(*) FROM context_documents
                LEFT JOIN context_roots
                  ON context_roots.id = context_documents.context_root_id
                WHERE context_documents.workspace_id = workspaces.id
                  AND (context_documents.context_root_id IS NULL
                       OR context_roots.enabled = 1)) AS document_count,
               COALESCE(session_activity.event_count, 0) AS event_count,
               session_activity.last_activity_at,
               COALESCE(session_activity.source_count, 0) AS source_count
        FROM workspaces
        LEFT JOIN session_activity
          ON session_activity.workspace_id = workspaces.id
        WHERE {workspace_condition}
        ORDER BY session_activity.last_activity_at DESC, workspaces.display_name
        """.format(
            source_condition=source_condition,
            workspace_condition=workspace_condition,
        ),
        params,
    ).fetchall()


def session_source_scopes(connection: sqlite3.Connection):
    return connection.execute(
        """
        SELECT sources.id,
               sources.profile_color AS color, sources.provider_kind, sources.name AS display_label,
               COUNT(CASE WHEN sessions.session_class = 'work'
                                AND sessions.session_role = 'primary'
                          THEN 1 END) AS eligible_session_count
        FROM sources
        LEFT JOIN sessions ON sessions.source_id = sources.id
        WHERE sources.provider_kind != 'context'
        GROUP BY sources.id
        ORDER BY sources.profile_position, sources.id
        """
    ).fetchall()


def session_id_prefix(connection: sqlite3.Connection, external_id: str) -> str:
    """Abbreviate a native ID, extending past eight characters on collisions."""
    length = min(8, len(external_id))
    prefix = external_id[:length]
    candidates = [
        row["external_id"]
        for row in connection.execute(
            """
            SELECT DISTINCT external_id FROM sessions
            WHERE substr(external_id, 1, ?) = ? AND external_id != ?
            """,
            (length, prefix, external_id),
        ).fetchall()
    ]
    while length < len(external_id) and any(
        candidate.startswith(external_id[:length]) for candidate in candidates
    ):
        length += 1
    return external_id[:length]


def session_detail(connection: sqlite3.Connection, session_id: int):
    return connection.execute(
        """
        SELECT sessions.*,
               sources.provider_kind, sources.name AS source_name,
               workspaces.display_name AS workspace_name,
               workspaces.canonical_path AS workspace_path,
               workspaces.git_root, workspaces.exists_now,
               session_pins.pinned_at
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        LEFT JOIN session_pins ON session_pins.session_id = sessions.id
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
        SELECT parents.*,
               sources.provider_kind,
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
        SELECT children.*,
               sources.provider_kind,
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
