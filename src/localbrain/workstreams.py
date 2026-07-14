import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ENTITY_TYPES = {"session", "document", "project", "external", "local"}
WORKSTREAM_STATUSES = {"active", "paused", "done", "archived"}
THREAD_STATUSES = {"active", "blocked", "paused", "done"}
RESOURCE_TYPES = {"jira", "wiki", "slack", "git", "document", "url"}

RESOURCE_LABELS = {
    "document": "Local Context",
    "project": "Project",
    "local_path": "Local Path",
    "jira": "Jira",
    "wiki": "Wiki",
    "slack": "Slack",
    "git": "Git",
    "url": "URL",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row else None


def _latest_activity(connection: sqlite3.Connection, workstream_id: int) -> Optional[str]:
    row = connection.execute(
        """
        SELECT MAX(activity_at) AS activity_at
        FROM (
            SELECT sessions.last_event_at AS activity_at
            FROM workstream_links
            JOIN sessions ON workstream_links.entity_type = 'session'
                AND CAST(workstream_links.entity_id AS INTEGER) = sessions.id
            WHERE workstream_links.workstream_id = ?
              AND sessions.session_class = 'work'
            UNION ALL
            SELECT sessions.last_event_at
            FROM threads
            JOIN thread_links ON thread_links.thread_id = threads.id
            JOIN sessions ON thread_links.entity_type = 'session'
                AND CAST(thread_links.entity_id AS INTEGER) = sessions.id
            WHERE threads.workstream_id = ?
              AND sessions.session_class = 'work'
            UNION ALL
            SELECT datetime(context_documents.mtime_ns / 1000000000, 'unixepoch')
            FROM workstream_links
            JOIN context_documents ON workstream_links.entity_type = 'document'
                AND CAST(workstream_links.entity_id AS INTEGER) = context_documents.id
            WHERE workstream_links.workstream_id = ?
            UNION ALL
            SELECT datetime(context_documents.mtime_ns / 1000000000, 'unixepoch')
            FROM threads
            JOIN thread_links ON thread_links.thread_id = threads.id
            JOIN context_documents ON thread_links.entity_type = 'document'
                AND CAST(thread_links.entity_id AS INTEGER) = context_documents.id
            WHERE threads.workstream_id = ?
            UNION ALL
            SELECT sessions.last_event_at
            FROM workstream_links
            JOIN sessions ON workstream_links.entity_type = 'project'
            JOIN workspaces ON CAST(workstream_links.entity_id AS INTEGER) = workspaces.id
                AND sessions.workspace_id = workspaces.id
            WHERE workstream_links.workstream_id = ?
              AND sessions.session_class = 'work'
            UNION ALL
            SELECT sessions.last_event_at
            FROM threads
            JOIN thread_links ON thread_links.thread_id = threads.id
            JOIN workspaces ON thread_links.entity_type = 'project'
                AND CAST(thread_links.entity_id AS INTEGER) = workspaces.id
            JOIN sessions ON sessions.workspace_id = workspaces.id
            WHERE threads.workstream_id = ?
              AND sessions.session_class = 'work'
            UNION ALL
            SELECT external_resources.updated_at
            FROM workstream_links
            JOIN external_resources ON workstream_links.entity_type = 'external'
                AND CAST(workstream_links.entity_id AS INTEGER) = external_resources.id
            WHERE workstream_links.workstream_id = ?
            UNION ALL
            SELECT external_resources.updated_at
            FROM threads
            JOIN thread_links ON thread_links.thread_id = threads.id
            JOIN external_resources ON thread_links.entity_type = 'external'
                AND CAST(thread_links.entity_id AS INTEGER) = external_resources.id
            WHERE threads.workstream_id = ?
            UNION ALL
            SELECT local_resources.updated_at
            FROM workstream_links
            JOIN local_resources ON workstream_links.entity_type = 'local'
                AND CAST(workstream_links.entity_id AS INTEGER) = local_resources.id
            WHERE workstream_links.workstream_id = ?
            UNION ALL
            SELECT local_resources.updated_at
            FROM threads
            JOIN thread_links ON thread_links.thread_id = threads.id
            JOIN local_resources ON thread_links.entity_type = 'local'
                AND CAST(thread_links.entity_id AS INTEGER) = local_resources.id
            WHERE threads.workstream_id = ?
        )
        """,
        (workstream_id,) * 10,
    ).fetchone()
    return row["activity_at"] if row else None


def _latest_checkpoint(connection: sqlite3.Connection, workstream_id: int) -> Optional[dict]:
    checkpoint = _row_dict(
        connection.execute(
            """
            SELECT * FROM checkpoints
            WHERE workstream_id = ?
            ORDER BY version DESC, id DESC
            LIMIT 1
            """,
            (workstream_id,),
        ).fetchone()
    )
    if checkpoint:
        references = connection.execute(
            """
            SELECT checkpoint_resource_refs.*, threads.title AS thread_title
            FROM checkpoint_resource_refs
            LEFT JOIN threads ON threads.id = checkpoint_resource_refs.thread_id
            WHERE checkpoint_resource_refs.checkpoint_id = ?
            ORDER BY CASE WHEN checkpoint_resource_refs.thread_id IS NULL THEN 1 ELSE 0 END,
                     threads.position, checkpoint_resource_refs.created_at
            """,
            (checkpoint["id"],),
        ).fetchall()
        checkpoint["resources"] = resolve_links(connection, references)
        checkpoint["resource_count"] = len(checkpoint["resources"])
    return checkpoint


def _workstream_summary(connection: sqlite3.Connection, row: sqlite3.Row) -> dict:
    item = dict(row)
    item["threads"] = [
        dict(thread)
        for thread in connection.execute(
            """
            SELECT threads.*,
                   (SELECT COUNT(*) FROM thread_links
                    WHERE thread_links.thread_id = threads.id) AS link_count
            FROM threads
            WHERE workstream_id = ?
            ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'blocked' THEN 1
                         WHEN 'paused' THEN 2 ELSE 3 END,
                     position, updated_at DESC
            """,
            (row["id"],),
        ).fetchall()
    ]
    item["checkpoint"] = _latest_checkpoint(connection, row["id"])
    linked_activity = _latest_activity(connection, row["id"])
    item["latest_activity_at"] = linked_activity or row["last_activity_at"]
    checkpoint_time = None
    if item["checkpoint"]:
        checkpoint_time = (
            item["checkpoint"].get("confirmed_at")
            or item["checkpoint"].get("updated_at")
            or item["checkpoint"].get("created_at")
        )
    item["needs_review"] = not item["checkpoint"] or bool(
        linked_activity and checkpoint_time and linked_activity > checkpoint_time
    )
    return item


def list_workstreams(
    connection: sqlite3.Connection, include_archived: bool = True
) -> List[dict]:
    where = "" if include_archived else "WHERE status != 'archived'"
    rows = connection.execute(
        """
        SELECT workstreams.*,
               (SELECT COUNT(*) FROM threads
                WHERE threads.workstream_id = workstreams.id) AS thread_count,
               (SELECT COUNT(*) FROM workstream_links
                WHERE workstream_links.workstream_id = workstreams.id) +
               (SELECT COUNT(*) FROM thread_links
                JOIN threads ON threads.id = thread_links.thread_id
                WHERE threads.workstream_id = workstreams.id) AS link_count,
               (SELECT COUNT(*) FROM suggestions
                WHERE suggestions.status = 'pending'
                  AND ((suggestions.target_type = 'workstream'
                        AND suggestions.target_id = workstreams.id)
                       OR (suggestions.target_type = 'thread'
                           AND suggestions.target_id IN
                               (SELECT id FROM threads
                                WHERE workstream_id = workstreams.id)))) AS suggestion_count
        FROM workstreams
        {where}
        ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'paused' THEN 1
                     WHEN 'done' THEN 2 ELSE 3 END,
                 COALESCE(last_activity_at, updated_at) DESC
        """.format(where=where)
    ).fetchall()
    return [_workstream_summary(connection, row) for row in rows]


def get_workstream(connection: sqlite3.Connection, workstream_id: int) -> Optional[dict]:
    row = connection.execute(
        "SELECT * FROM workstreams WHERE id = ?", (workstream_id,)
    ).fetchone()
    if not row:
        return None
    item = _workstream_summary(connection, row)
    item["links"] = resolve_links(
        connection,
        connection.execute(
            "SELECT * FROM workstream_links WHERE workstream_id = ? ORDER BY created_at DESC",
            (workstream_id,),
        ).fetchall(),
    )
    for thread in item["threads"]:
        thread["links"] = resolve_links(
            connection,
            connection.execute(
                "SELECT * FROM thread_links WHERE thread_id = ? ORDER BY created_at DESC",
                (thread["id"],),
            ).fetchall(),
        )
    item["suggestions"] = _workstream_suggestions(
        connection, workstream_id, "pending"
    )
    item["excluded_suggestions"] = _workstream_suggestions(
        connection, workstream_id, "rejected"
    )
    return item


def _workstream_suggestions(
    connection: sqlite3.Connection, workstream_id: int, status: str
) -> List[dict]:
    rows = connection.execute(
        """
        SELECT suggestions.*,
               CASE WHEN target_type = 'thread'
                    THEN (SELECT title FROM threads WHERE id = target_id)
                    ELSE (SELECT name FROM workstreams WHERE id = target_id)
               END AS target_name
        FROM suggestions
        WHERE status = ?
          AND ((target_type = 'workstream' AND target_id = ?)
               OR (target_type = 'thread' AND target_id IN
                   (SELECT id FROM threads WHERE workstream_id = ?)))
        ORDER BY CASE WHEN suggestion_type = 'checkpoint_draft' THEN 1 ELSE 0 END,
                 confidence DESC, COALESCE(resolved_at, created_at) DESC
        """,
        (status, workstream_id, workstream_id),
    ).fetchall()
    return [_suggestion_view(connection, row) for row in rows]


def _suggestion_view(connection: sqlite3.Connection, row: sqlite3.Row) -> dict:
    item = dict(row)
    try:
        payload = json.loads(item.get("payload_json") or "{}")
    except json.JSONDecodeError:
        payload = {}
    item["payload"] = payload
    item["resource_label"] = _suggestion_resource_label(
        connection, item["suggestion_type"], payload
    )
    item["origin_label"] = (
        "Claude Run" if item.get("origin_run_id") else "Quick match"
    )
    return item


def _suggestion_resource_label(
    connection: sqlite3.Connection, suggestion_type: str, payload: dict
) -> str:
    if suggestion_type == "checkpoint_draft":
        return "Checkpoint"

    entity_type = payload.get("entity_type")
    entity_id = payload.get("entity_id")
    resource_type = payload.get("resource_type")
    locator = payload.get("locator")
    if entity_type == "session" or resource_type == "session":
        session_id = entity_id if entity_type == "session" else locator
        row = connection.execute(
            """
            SELECT sources.kind
            FROM sessions JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.id = ?
            """,
            (session_id,),
        ).fetchone()
        source_kind = (row["kind"] if row else "").lower()
        if source_kind == "claude":
            return "Claude Session"
        if source_kind == "codex":
            return "Codex Session"
        return "Session"
    if entity_type == "external":
        row = connection.execute(
            "SELECT resource_type FROM external_resources WHERE id = ?",
            (entity_id,),
        ).fetchone()
        return RESOURCE_LABELS.get(row["resource_type"], "External") if row else "External"
    if entity_type == "local":
        row = connection.execute(
            "SELECT resource_type FROM local_resources WHERE id = ?", (entity_id,)
        ).fetchone()
        return {
            "repository": "Local Repository",
            "directory": "Local Directory",
            "file": "Local File",
            "path": "Local Path",
        }.get(row["resource_type"] if row else "path", "Local Path")
    if entity_type:
        return RESOURCE_LABELS.get(entity_type, entity_type.replace("_", " ").title())
    return RESOURCE_LABELS.get(
        resource_type, (resource_type or "Resource").replace("_", " ").title()
    )


def create_workstream(
    connection: sqlite3.Connection, name: str, summary: Optional[str]
) -> int:
    cursor = connection.execute(
        "INSERT INTO workstreams(name, summary, updated_at) VALUES (?, ?, ?)",
        (name.strip(), (summary or "").strip() or None, utc_now()),
    )
    return int(cursor.lastrowid)


def update_workstream(
    connection: sqlite3.Connection,
    workstream_id: int,
    name: str,
    status: str,
    summary: Optional[str],
) -> None:
    if status not in WORKSTREAM_STATUSES:
        raise ValueError("Unsupported workstream status")
    cursor = connection.execute(
        """
        UPDATE workstreams
        SET name = ?, status = ?, summary = ?, updated_at = ?
        WHERE id = ?
        """,
        (name.strip(), status, (summary or "").strip() or None, utc_now(), workstream_id),
    )
    if cursor.rowcount == 0:
        raise LookupError("Workstream not found")


def create_thread(
    connection: sqlite3.Connection,
    workstream_id: int,
    title: str,
    summary: Optional[str],
    current_goal: Optional[str],
    next_action: Optional[str],
) -> int:
    position = connection.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS position FROM threads WHERE workstream_id = ?",
        (workstream_id,),
    ).fetchone()["position"]
    cursor = connection.execute(
        """
        INSERT INTO threads(
            workstream_id, title, summary, current_goal, next_action, position, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            workstream_id,
            title.strip(),
            (summary or "").strip() or None,
            (current_goal or "").strip() or None,
            (next_action or "").strip() or None,
            position,
            utc_now(),
        ),
    )
    thread_id = int(cursor.lastrowid)
    _touch_workstream(connection, workstream_id)
    return thread_id


def update_thread(
    connection: sqlite3.Connection,
    thread_id: int,
    title: str,
    status: str,
    summary: Optional[str],
    current_goal: Optional[str],
    next_action: Optional[str],
) -> None:
    if status not in THREAD_STATUSES:
        raise ValueError("Unsupported thread status")
    row = connection.execute(
        "SELECT workstream_id FROM threads WHERE id = ?", (thread_id,)
    ).fetchone()
    if not row:
        raise LookupError("Thread not found")
    connection.execute(
        """
        UPDATE threads
        SET title = ?, status = ?, summary = ?, current_goal = ?,
            next_action = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            title.strip(),
            status,
            (summary or "").strip() or None,
            (current_goal or "").strip() or None,
            (next_action or "").strip() or None,
            utc_now(),
            thread_id,
        ),
    )
    _touch_workstream(connection, row["workstream_id"])


def create_checkpoint(
    connection: sqlite3.Connection,
    workstream_id: int,
    current_goal: Optional[str],
    confirmed_facts: Optional[str],
    recent_decisions: Optional[str],
    open_questions: Optional[str],
    next_actions: Optional[str],
    files_to_open: Optional[str],
) -> int:
    version = connection.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 AS version FROM checkpoints WHERE workstream_id = ?",
        (workstream_id,),
    ).fetchone()["version"]
    now = utc_now()
    cursor = connection.execute(
        """
        INSERT INTO checkpoints(
            workstream_id, current_goal, confirmed_facts, recent_decisions,
            open_questions, next_actions, files_to_open, confirmed_at,
            based_on_activity_at, version, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            workstream_id,
            _clean(current_goal),
            _clean(confirmed_facts),
            _clean(recent_decisions),
            _clean(open_questions),
            _clean(next_actions),
            _clean(files_to_open),
            now,
            _latest_activity(connection, workstream_id),
            version,
            now,
        ),
    )
    checkpoint_id = int(cursor.lastrowid)
    _snapshot_checkpoint_resources(connection, checkpoint_id, workstream_id)
    _touch_workstream(connection, workstream_id)
    return checkpoint_id


def _snapshot_checkpoint_resources(
    connection: sqlite3.Connection, checkpoint_id: int, workstream_id: int
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO checkpoint_resource_refs(
            checkpoint_id, thread_id, entity_type, entity_id, relation_type
        )
        SELECT ?, NULL, entity_type, entity_id, relation_type
        FROM workstream_links WHERE workstream_id = ?
        """,
        (checkpoint_id, workstream_id),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO checkpoint_resource_refs(
            checkpoint_id, thread_id, entity_type, entity_id, relation_type
        )
        SELECT ?, threads.id, thread_links.entity_type, thread_links.entity_id,
               thread_links.relation_type
        FROM threads
        JOIN thread_links ON thread_links.thread_id = threads.id
        WHERE threads.workstream_id = ?
        """,
        (checkpoint_id, workstream_id),
    )


def create_external_resource(
    connection: sqlite3.Connection,
    resource_type: str,
    title: str,
    url: str,
    summary: Optional[str],
    source_role: Optional[str],
) -> int:
    if resource_type not in RESOURCE_TYPES:
        raise ValueError("Unsupported resource type")
    now = utc_now()
    connection.execute(
        """
        INSERT INTO external_resources(
            resource_type, title, url, summary, source_role, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            resource_type = excluded.resource_type,
            title = excluded.title,
            summary = excluded.summary,
            source_role = excluded.source_role,
            updated_at = excluded.updated_at
        """,
        (
            resource_type,
            title.strip(),
            url.strip(),
            _clean(summary),
            _clean(source_role),
            now,
        ),
    )
    return int(
        connection.execute(
            "SELECT id FROM external_resources WHERE url = ?", (url.strip(),)
        ).fetchone()["id"]
    )


def create_local_resource(
    connection: sqlite3.Connection,
    path: str,
    title: Optional[str],
    summary: Optional[str],
    discovered_by: str = "user",
) -> int:
    candidate = Path(path).expanduser()
    exists_now = candidate.exists()
    canonical = str(candidate.resolve()) if exists_now else str(candidate)
    if exists_now and candidate.is_dir() and (candidate / ".git").exists():
        resource_type = "repository"
    elif exists_now and candidate.is_dir():
        resource_type = "directory"
    elif exists_now and candidate.is_file():
        resource_type = "file"
    else:
        resource_type = "path"
    now = utc_now()
    connection.execute(
        """
        INSERT INTO local_resources(
            path, resource_type, title, summary, exists_now, discovered_by, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            resource_type = excluded.resource_type,
            title = excluded.title,
            summary = COALESCE(excluded.summary, local_resources.summary),
            exists_now = excluded.exists_now,
            discovered_by = excluded.discovered_by,
            updated_at = excluded.updated_at
        """,
        (
            canonical,
            resource_type,
            _clean(title) or candidate.name or canonical,
            _clean(summary),
            int(exists_now),
            discovered_by,
            now,
        ),
    )
    return int(
        connection.execute(
            "SELECT id FROM local_resources WHERE path = ?", (canonical,)
        ).fetchone()["id"]
    )


def add_link(
    connection: sqlite3.Connection,
    scope_type: str,
    scope_id: int,
    entity_type: str,
    entity_id: str,
    relation_type: str = "related-to",
    linked_by: str = "user",
    confidence: Optional[float] = None,
) -> int:
    _validate_entity(connection, entity_type, entity_id)
    if scope_type == "workstream":
        table, owner_column = "workstream_links", "workstream_id"
        workstream_id = scope_id
    elif scope_type == "thread":
        table, owner_column = "thread_links", "thread_id"
        row = connection.execute(
            "SELECT workstream_id FROM threads WHERE id = ?", (scope_id,)
        ).fetchone()
        if not row:
            raise LookupError("Thread not found")
        workstream_id = row["workstream_id"]
    else:
        raise ValueError("Unsupported link scope")
    connection.execute(
        """
        INSERT INTO {table}(
            {owner_column}, entity_type, entity_id, relation_type, confidence, linked_by
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT({owner_column}, entity_type, entity_id) DO UPDATE SET
            relation_type = excluded.relation_type,
            confidence = excluded.confidence,
            linked_by = excluded.linked_by
        """.format(table=table, owner_column=owner_column),
        (scope_id, entity_type, str(entity_id), relation_type.strip(), confidence, linked_by),
    )
    _touch_workstream(connection, workstream_id)
    return int(
        connection.execute(
            "SELECT id FROM {table} WHERE {owner_column} = ? AND entity_type = ? AND entity_id = ?".format(
                table=table, owner_column=owner_column
            ),
            (scope_id, entity_type, str(entity_id)),
        ).fetchone()["id"]
    )


def remove_link(
    connection: sqlite3.Connection, scope_type: str, scope_id: int, link_id: int
) -> None:
    if scope_type == "workstream":
        connection.execute(
            "DELETE FROM workstream_links WHERE id = ? AND workstream_id = ?",
            (link_id, scope_id),
        )
        _touch_workstream(connection, scope_id)
        return
    if scope_type == "thread":
        row = connection.execute(
            "SELECT workstream_id FROM threads WHERE id = ?", (scope_id,)
        ).fetchone()
        connection.execute(
            "DELETE FROM thread_links WHERE id = ? AND thread_id = ?",
            (link_id, scope_id),
        )
        if row:
            _touch_workstream(connection, row["workstream_id"])
        return
    raise ValueError("Unsupported link scope")


def picker_resources(connection: sqlite3.Connection) -> dict:
    return {
        "sessions": connection.execute(
            """
            SELECT sessions.id, sessions.title, sessions.cwd_raw, sessions.last_event_at,
                   sources.kind AS source_kind
            FROM sessions JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.session_class = 'work'
            ORDER BY sessions.last_event_at DESC LIMIT 80
            """
        ).fetchall(),
        "documents": connection.execute(
            """
            SELECT context_documents.id, context_documents.title,
                   context_documents.relative_path
            FROM context_documents
            LEFT JOIN context_roots
              ON context_roots.id = context_documents.context_root_id
            WHERE context_documents.context_root_id IS NULL
               OR context_roots.enabled = 1
            ORDER BY context_documents.mtime_ns DESC LIMIT 80
            """
        ).fetchall(),
        "projects": connection.execute(
            "SELECT id, display_name, canonical_path FROM workspaces ORDER BY last_activity_at DESC LIMIT 80"
        ).fetchall(),
        "external": connection.execute(
            "SELECT id, resource_type, title, url FROM external_resources ORDER BY updated_at DESC"
        ).fetchall(),
        "local": connection.execute(
            "SELECT id, resource_type, title, path, exists_now FROM local_resources ORDER BY updated_at DESC"
        ).fetchall(),
    }


def resolve_links(connection: sqlite3.Connection, links: Iterable[sqlite3.Row]) -> List[dict]:
    resolved = []
    for link in links:
        item = dict(link)
        item["link_id"] = item["id"]
        entity_type = item["entity_type"]
        entity_id = item["entity_id"]
        item["resource_id"] = entity_id
        if entity_type == "session":
            entity = connection.execute(
                """
                SELECT sessions.id, sessions.title, sessions.cwd_raw AS detail,
                       sessions.last_event_at AS activity_at, sources.kind AS source_kind
                FROM sessions JOIN sources ON sources.id = sessions.source_id
                WHERE sessions.id = ?
                """,
                (entity_id,),
            ).fetchone()
            item["href"] = "/sessions/{}".format(entity_id)
        elif entity_type == "document":
            entity = connection.execute(
                """
                SELECT id, title, relative_path AS detail,
                       datetime(mtime_ns / 1000000000, 'unixepoch') AS activity_at
                FROM context_documents WHERE id = ?
                """,
                (entity_id,),
            ).fetchone()
            item["href"] = "/documents/{}".format(entity_id)
        elif entity_type == "project":
            entity = connection.execute(
                "SELECT id, display_name AS title, canonical_path AS detail, last_activity_at AS activity_at FROM workspaces WHERE id = ?",
                (entity_id,),
            ).fetchone()
            item["href"] = "/sessions?workspace={}".format(entity_id)
        elif entity_type == "external":
            entity = connection.execute(
                "SELECT id, title, url AS detail, updated_at AS activity_at, resource_type FROM external_resources WHERE id = ?",
                (entity_id,),
            ).fetchone()
            item["href"] = entity["detail"] if entity else "#"
            item["external"] = True
        else:
            entity = connection.execute(
                """
                SELECT id, title, path AS detail, updated_at AS activity_at,
                       resource_type, exists_now
                FROM local_resources WHERE id = ?
                """,
                (entity_id,),
            ).fetchone()
            item["href"] = "/local-resources/{}".format(entity_id)
        if entity:
            item.update(dict(entity))
            item["resource_label"] = _resolved_resource_label(item)
            resolved.append(item)
    return resolved


def _resolved_resource_label(item: dict) -> str:
    entity_type = item["entity_type"]
    if entity_type == "session":
        source_kind = (item.get("source_kind") or "").lower()
        if source_kind == "claude":
            return "Claude Session"
        if source_kind == "codex":
            return "Codex Session"
        return "Session"
    if entity_type == "document":
        return "Local Context"
    if entity_type == "project":
        return "Project"
    if entity_type == "external":
        return RESOURCE_LABELS.get(item.get("resource_type"), "External")
    return {
        "repository": "Local Repository",
        "directory": "Local Directory",
        "file": "Local File",
        "path": "Local Path",
    }.get(item.get("resource_type"), "Local Path")


def entity_memberships(
    connection: sqlite3.Connection, entity_type: str, entity_id: int
) -> List[dict]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT workstreams.id AS workstream_id, workstreams.name AS workstream_name,
                   NULL AS thread_id, NULL AS thread_title, workstream_links.relation_type
            FROM workstream_links
            JOIN workstreams ON workstreams.id = workstream_links.workstream_id
            WHERE workstream_links.entity_type = ? AND workstream_links.entity_id = ?
            UNION ALL
            SELECT workstreams.id, workstreams.name, threads.id, threads.title,
                   thread_links.relation_type
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            JOIN workstreams ON workstreams.id = threads.workstream_id
            WHERE thread_links.entity_type = ? AND thread_links.entity_id = ?
            ORDER BY workstream_name, thread_title
            """,
            (entity_type, str(entity_id), entity_type, str(entity_id)),
        ).fetchall()
    ]


def local_resource_detail(
    connection: sqlite3.Connection, resource_id: int
) -> Optional[dict]:
    row = connection.execute(
        "SELECT * FROM local_resources WHERE id = ?", (resource_id,)
    ).fetchone()
    return dict(row) if row else None


def dashboard_overview(connection: sqlite3.Connection) -> dict:
    workstreams = [
        item for item in list_workstreams(connection, include_archived=False)
        if item["status"] in {"active", "paused"}
    ]
    unlinked_sessions = connection.execute(
        """
        SELECT sessions.id, sessions.title, sessions.last_event_at,
               workspaces.display_name AS workspace_name, sources.kind AS source_kind
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.session_class = 'work'
          AND NOT EXISTS (SELECT 1 FROM workstream_links
                          WHERE entity_type = 'session'
                            AND entity_id = CAST(sessions.id AS TEXT))
          AND NOT EXISTS (SELECT 1 FROM thread_links
                          WHERE entity_type = 'session'
                            AND entity_id = CAST(sessions.id AS TEXT))
        ORDER BY sessions.last_event_at DESC
        """
    ).fetchall()
    unlinked_document_count = connection.execute(
        """
        SELECT COUNT(*) AS count FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE (context_documents.context_root_id IS NULL OR context_roots.enabled = 1)
          AND NOT EXISTS (SELECT 1 FROM workstream_links
                          WHERE entity_type = 'document'
                            AND entity_id = CAST(context_documents.id AS TEXT))
          AND NOT EXISTS (SELECT 1 FROM thread_links
                          WHERE entity_type = 'document'
                            AND entity_id = CAST(context_documents.id AS TEXT))
        """
    ).fetchone()["count"]
    pending = connection.execute(
        "SELECT COUNT(*) AS count FROM suggestions WHERE status = 'pending'"
    ).fetchone()["count"]
    return {
        "workstreams": workstreams,
        "metrics": {
            "active_workstreams": sum(1 for item in workstreams if item["status"] == "active"),
            "active_threads": sum(
                1 for item in workstreams for thread in item["threads"]
                if thread["status"] in {"active", "blocked"}
            ),
            "needs_review": sum(1 for item in workstreams if item["needs_review"]),
            "unlinked_sessions": len(unlinked_sessions),
            "unlinked_documents": unlinked_document_count,
            "pending_suggestions": pending,
        },
        "unlinked_sessions": unlinked_sessions[:8],
    }


def generate_suggestions(connection: sqlite3.Connection, workstream_id: int) -> int:
    workstream = get_workstream(connection, workstream_id)
    if not workstream:
        raise LookupError("Workstream not found")
    targets = [
        (
            "thread",
            thread["id"],
            " ".join(
                filter(
                    None,
                    [
                        workstream["name"],
                        workstream.get("summary"),
                        thread["title"],
                        thread.get("summary"),
                        thread.get("current_goal"),
                    ],
                )
            ),
        )
        for thread in workstream["threads"]
        if thread["status"] in {"active", "blocked"}
    ]
    if not targets:
        targets = [
            (
                "workstream",
                workstream_id,
                " ".join(filter(None, [workstream["name"], workstream.get("summary")])),
            )
        ]

    candidates = []
    for row in connection.execute(
        """
        SELECT sessions.id, sessions.title, sessions.cwd_raw AS detail,
               sessions.last_event_at AS activity_at, 'session' AS entity_type
        FROM sessions
        WHERE session_class = 'work'
        ORDER BY last_event_at DESC LIMIT 120
        """
    ).fetchall():
        candidates.append(dict(row))
    for row in connection.execute(
        """
        SELECT context_documents.id, context_documents.title,
               context_documents.relative_path AS detail,
               datetime(context_documents.mtime_ns / 1000000000, 'unixepoch') AS activity_at,
               'document' AS entity_type
        FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
        ORDER BY context_documents.mtime_ns DESC LIMIT 120
        """
    ).fetchall():
        candidates.append(dict(row))

    created = 0
    for target_type, target_id, target_text in targets:
        target_tokens = _tokens(target_text)
        scored = []
        for candidate in candidates:
            if _target_has_link(
                connection,
                target_type,
                target_id,
                candidate["entity_type"],
                candidate["id"],
            ):
                continue
            overlap = target_tokens & _tokens(
                "{} {}".format(candidate["title"], candidate.get("detail") or "")
            )
            if not overlap:
                continue
            score = min(0.94, 0.48 + len(overlap) * 0.12)
            scored.append((score, overlap, candidate))
        for score, overlap, candidate in sorted(scored, reverse=True, key=lambda value: value[0])[:3]:
            fingerprint = hashlib.sha256(
                "{}:{}:{}:{}".format(
                    target_type, target_id, candidate["entity_type"], candidate["id"]
                ).encode("utf-8")
            ).hexdigest()
            before = connection.total_changes
            connection.execute(
                """
                INSERT OR IGNORE INTO suggestions(
                    suggestion_type, target_type, target_id, title, description,
                    rationale, payload_json, fingerprint, confidence
                ) VALUES ('link', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_type,
                    target_id,
                    candidate["title"],
                    candidate.get("detail"),
                    "공통 키워드: {}".format(", ".join(sorted(overlap))),
                    json.dumps(
                        {
                            "entity_type": candidate["entity_type"],
                            "entity_id": str(candidate["id"]),
                            "relation_type": "related-to",
                        },
                        ensure_ascii=False,
                    ),
                    fingerprint,
                    score,
                ),
            )
            created += int(connection.total_changes > before)
    return created


def resolve_suggestion(
    connection: sqlite3.Connection, suggestion_id: int, action: str
) -> None:
    row = connection.execute(
        "SELECT * FROM suggestions WHERE id = ?",
        (suggestion_id,),
    ).fetchone()
    if not row:
        raise LookupError("Suggestion not found")
    if action == "restore":
        if row["status"] != "rejected":
            raise ValueError("Only rejected suggestions can be restored")
        connection.execute(
            "UPDATE suggestions SET status = 'pending', resolved_at = NULL WHERE id = ?",
            (suggestion_id,),
        )
        return
    if row["status"] != "pending":
        raise ValueError("Only pending suggestions can be resolved")
    if action == "accept":
        payload = json.loads(row["payload_json"] or "{}")
        if row["suggestion_type"] == "checkpoint_draft":
            if row["target_type"] != "workstream":
                raise ValueError("Checkpoint draft must target a Workstream")
            create_checkpoint(
                connection,
                row["target_id"],
                payload.get("current_goal"),
                payload.get("confirmed_facts"),
                payload.get("recent_decisions"),
                payload.get("open_questions"),
                payload.get("next_actions"),
                payload.get("files_to_open"),
            )
        else:
            entity_type, entity_id = _materialize_suggestion_resource(
                connection, payload
            )
            add_link(
                connection,
                row["target_type"],
                row["target_id"],
                entity_type,
                entity_id,
                payload.get("relation_type", "related-to"),
                linked_by="suggestion",
                confidence=row["confidence"],
            )
        status = "accepted"
    elif action == "reject":
        status = "rejected"
    else:
        raise ValueError("Unsupported suggestion action")
    connection.execute(
        "UPDATE suggestions SET status = ?, resolved_at = ? WHERE id = ?",
        (status, utc_now(), suggestion_id),
    )


def _materialize_suggestion_resource(
    connection: sqlite3.Connection, payload: dict
) -> tuple:
    if payload.get("entity_type") and payload.get("entity_id"):
        return payload["entity_type"], str(payload["entity_id"])
    resource_type = payload.get("resource_type")
    locator = payload.get("locator")
    if not resource_type or not locator:
        raise ValueError("Suggestion does not contain a usable resource")
    if resource_type == "local_path":
        resource_id = create_local_resource(
            connection,
            locator,
            payload.get("title"),
            payload.get("summary") or payload.get("evidence") or payload.get("rationale"),
            discovered_by="task_runner",
        )
        return "local", str(resource_id)
    if resource_type in {"session", "document", "project"}:
        return resource_type, str(locator)
    external_type = resource_type if resource_type in RESOURCE_TYPES else "url"
    resource_id = create_external_resource(
        connection,
        external_type,
        payload.get("title") or locator,
        locator,
        payload.get("summary") or payload.get("evidence") or payload.get("rationale"),
        payload.get("source_role"),
    )
    return "external", str(resource_id)


def _clean(value: Optional[str]) -> Optional[str]:
    return (value or "").strip() or None


def _touch_workstream(connection: sqlite3.Connection, workstream_id: int) -> None:
    now = utc_now()
    connection.execute(
        "UPDATE workstreams SET updated_at = ?, last_activity_at = ? WHERE id = ?",
        (now, now, workstream_id),
    )


def _validate_entity(
    connection: sqlite3.Connection, entity_type: str, entity_id: str
) -> None:
    if entity_type not in ENTITY_TYPES:
        raise ValueError("Unsupported entity type")
    table = {
        "session": "sessions",
        "document": "context_documents",
        "project": "workspaces",
        "external": "external_resources",
        "local": "local_resources",
    }[entity_type]
    extra = " AND session_class = 'work'" if entity_type == "session" else ""
    row = connection.execute(
        "SELECT id FROM {} WHERE id = ?{}".format(table, extra), (entity_id,)
    ).fetchone()
    if not row:
        raise LookupError("Linked resource not found")


STOP_WORDS = {
    "about", "and", "context", "for", "from", "local", "project", "the", "this",
    "with", "개발", "관련", "대한", "작업", "정보", "프로젝트", "확인",
}


def _tokens(value: str) -> set:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9가-힣_.-]{2,}", value or "")
        if token.lower() not in STOP_WORDS
    }


def _target_has_link(
    connection: sqlite3.Connection,
    target_type: str,
    target_id: int,
    entity_type: str,
    entity_id: int,
) -> bool:
    table, column = (
        ("thread_links", "thread_id")
        if target_type == "thread"
        else ("workstream_links", "workstream_id")
    )
    return bool(
        connection.execute(
            "SELECT 1 FROM {} WHERE {} = ? AND entity_type = ? AND entity_id = ?".format(
                table, column
            ),
            (target_id, entity_type, str(entity_id)),
        ).fetchone()
    )
