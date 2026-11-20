//! Verbatim SQL shapes from the existing Workstream service.
pub(super) const LATEST_ACTIVITY_0: &str = r########"
        SELECT MAX(activity_at) AS activity_at
        FROM (
            SELECT sessions.last_event_at AS activity_at
            FROM workstream_links
            JOIN sessions ON workstream_links.entity_type = 'session'
                AND CAST(workstream_links.entity_id AS INTEGER) = sessions.id
            WHERE workstream_links.workstream_id = ?
              AND sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
            UNION ALL
            SELECT sessions.last_event_at
            FROM threads
            JOIN thread_links ON thread_links.thread_id = threads.id
            JOIN sessions ON thread_links.entity_type = 'session'
                AND CAST(thread_links.entity_id AS INTEGER) = sessions.id
            WHERE threads.workstream_id = ?
              AND sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
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
              AND sessions.session_role = 'primary'
            UNION ALL
            SELECT sessions.last_event_at
            FROM threads
            JOIN thread_links ON thread_links.thread_id = threads.id
            JOIN workspaces ON thread_links.entity_type = 'project'
                AND CAST(thread_links.entity_id AS INTEGER) = workspaces.id
            JOIN sessions ON sessions.workspace_id = workspaces.id
            WHERE threads.workstream_id = ?
              AND sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
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
        "########;
pub(super) const LATEST_CHECKPOINT_0: &str = r########"
            SELECT * FROM checkpoints
            WHERE workstream_id = ?
            ORDER BY version DESC, id DESC
            LIMIT 1
            "########;
pub(super) const LATEST_CHECKPOINT_1: &str = r########"
            SELECT checkpoint_resource_refs.*, threads.title AS thread_title
            FROM checkpoint_resource_refs
            LEFT JOIN threads ON threads.id = checkpoint_resource_refs.thread_id
            WHERE checkpoint_resource_refs.checkpoint_id = ?
            ORDER BY CASE WHEN checkpoint_resource_refs.thread_id IS NULL THEN 1 ELSE 0 END,
                     threads.position, checkpoint_resource_refs.created_at
            "########;
pub(super) const WORKSTREAM_SUMMARY_0: &str = r########"
            SELECT threads.*,
                   (SELECT COUNT(*) FROM thread_links
                    WHERE thread_links.thread_id = threads.id) AS link_count
            FROM threads
            WHERE workstream_id = ?
            ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'blocked' THEN 1
                         WHEN 'paused' THEN 2 ELSE 3 END,
                     position, updated_at DESC
            "########;
pub(super) const LIST_WORKSTREAMS_0: &str = r########"
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
        "########;
pub(super) const GET_WORKSTREAM_0: &str = r########"SELECT * FROM workstreams WHERE id = ?"########;
pub(super) const GET_WORKSTREAM_1: &str = r########"SELECT * FROM workstream_links WHERE workstream_id = ? ORDER BY created_at DESC"########;
pub(super) const GET_WORKSTREAM_2: &str =
    r########"SELECT * FROM thread_links WHERE thread_id = ? ORDER BY created_at DESC"########;
pub(super) const WORKSTREAM_SUGGESTIONS_0: &str = r########"
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
        "########;
pub(super) const SUGGESTION_RESOURCE_LABEL_0: &str = r########"
            SELECT sources.provider_kind
            FROM sessions JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.id = ?
            "########;
pub(super) const SUGGESTION_RESOURCE_LABEL_1: &str =
    r########"SELECT resource_type FROM external_resources WHERE id = ?"########;
pub(super) const SUGGESTION_RESOURCE_LABEL_2: &str =
    r########"SELECT resource_type FROM local_resources WHERE id = ?"########;
pub(super) const CREATE_WORKSTREAM_0: &str =
    r########"INSERT INTO workstreams(name, summary, updated_at) VALUES (?, ?, ?)"########;
pub(super) const UPDATE_WORKSTREAM_0: &str = r########"
        UPDATE workstreams
        SET name = ?, status = ?, summary = ?, updated_at = ?
        WHERE id = ?
        "########;
pub(super) const CREATE_THREAD_0: &str = r########"SELECT COALESCE(MAX(position), -1) + 1 AS position FROM threads WHERE workstream_id = ?"########;
pub(super) const CREATE_THREAD_1: &str = r########"
        INSERT INTO threads(
            workstream_id, title, summary, current_goal, next_action, position, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        "########;
pub(super) const UPDATE_THREAD_0: &str =
    r########"SELECT workstream_id FROM threads WHERE id = ?"########;
pub(super) const UPDATE_THREAD_1: &str = r########"
        UPDATE threads
        SET title = ?, status = ?, summary = ?, current_goal = ?,
            next_action = ?, updated_at = ?
        WHERE id = ?
        "########;
pub(super) const CREATE_CHECKPOINT_0: &str = r########"SELECT COALESCE(MAX(version), 0) + 1 AS version FROM checkpoints WHERE workstream_id = ?"########;
pub(super) const CREATE_CHECKPOINT_1: &str = r########"
        INSERT INTO checkpoints(
            workstream_id, current_goal, confirmed_facts, recent_decisions,
            open_questions, next_actions, files_to_open, confirmed_at,
            based_on_activity_at, version, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        "########;
pub(super) const SNAPSHOT_CHECKPOINT_RESOURCES_0: &str = r########"
        INSERT OR IGNORE INTO checkpoint_resource_refs(
            checkpoint_id, thread_id, entity_type, entity_id, relation_type
        )
        SELECT ?, NULL, entity_type, entity_id, relation_type
        FROM workstream_links WHERE workstream_id = ?
        "########;
pub(super) const SNAPSHOT_CHECKPOINT_RESOURCES_1: &str = r########"
        INSERT OR IGNORE INTO checkpoint_resource_refs(
            checkpoint_id, thread_id, entity_type, entity_id, relation_type
        )
        SELECT ?, threads.id, thread_links.entity_type, thread_links.entity_id,
               thread_links.relation_type
        FROM threads
        JOIN thread_links ON thread_links.thread_id = threads.id
        WHERE threads.workstream_id = ?
        "########;
pub(super) const ADD_LINK_0: &str =
    r########"SELECT workstream_id FROM threads WHERE id = ?"########;
pub(super) const ADD_LINK_1: &str = r########"
        INSERT INTO {table}(
            {owner_column}, entity_type, entity_id, resource_id, relation_type, confidence, linked_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT({owner_column}, entity_type, entity_id) DO UPDATE SET
            resource_id = excluded.resource_id,
            relation_type = excluded.relation_type,
            confidence = excluded.confidence,
            linked_by = excluded.linked_by
        "########;
pub(super) const ADD_LINK_2: &str = r########"SELECT id FROM {table} WHERE {owner_column} = ? AND entity_type = ? AND entity_id = ?"########;
pub(super) const REMOVE_LINK_0: &str =
    r########"DELETE FROM workstream_links WHERE id = ? AND workstream_id = ?"########;
pub(super) const REMOVE_LINK_1: &str =
    r########"SELECT workstream_id FROM threads WHERE id = ?"########;
pub(super) const REMOVE_LINK_2: &str =
    r########"DELETE FROM thread_links WHERE id = ? AND thread_id = ?"########;
pub(super) const PICKER_RESOURCES_0: &str = r########"
            SELECT sessions.id, sessions.title, sessions.cwd_raw, sessions.last_event_at,
                   sources.provider_kind AS source_kind
            FROM sessions JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
            ORDER BY sessions.last_event_at DESC LIMIT 80
            "########;
pub(super) const PICKER_RESOURCES_1: &str = r########"
            SELECT context_documents.id, context_documents.title,
                   context_documents.relative_path
            FROM context_documents
            LEFT JOIN context_roots
              ON context_roots.id = context_documents.context_root_id
            WHERE context_documents.context_root_id IS NULL
               OR context_roots.enabled = 1
            ORDER BY context_documents.mtime_ns DESC LIMIT 80
            "########;
pub(super) const PICKER_RESOURCES_2: &str = r########"SELECT id, display_name, canonical_path FROM workspaces ORDER BY last_activity_at DESC LIMIT 80"########;
pub(super) const PICKER_RESOURCES_3: &str = r########"SELECT id, resource_type, title, url FROM external_resources ORDER BY updated_at DESC"########;
pub(super) const PICKER_RESOURCES_4: &str = r########"SELECT id, resource_type, title, path, exists_now FROM local_resources ORDER BY updated_at DESC"########;
pub(super) const RESOLVE_LINKS_0: &str = r########"
                SELECT sessions.id, sessions.title, sessions.cwd_raw AS detail,
                       sessions.last_event_at AS activity_at, sources.provider_kind AS source_kind
                FROM sessions JOIN sources ON sources.id = sessions.source_id
                WHERE sessions.id = ?
                "########;
pub(super) const RESOLVE_LINKS_1: &str = r########"
                SELECT id, title, relative_path AS detail,
                       datetime(mtime_ns / 1000000000, 'unixepoch') AS activity_at
                FROM context_documents WHERE id = ?
                "########;
pub(super) const RESOLVE_LINKS_2: &str = r########"SELECT id, display_name AS title, canonical_path AS detail, last_activity_at AS activity_at FROM workspaces WHERE id = ?"########;
pub(super) const RESOLVE_LINKS_3: &str = r########"SELECT id, title, url AS detail, updated_at AS activity_at, resource_type FROM external_resources WHERE id = ?"########;
pub(super) const RESOLVE_LINKS_4: &str = r########"
                SELECT id, title, path AS detail, updated_at AS activity_at,
                       resource_type, exists_now
                FROM local_resources WHERE id = ?
                "########;
pub(super) const ENTITY_MEMBERSHIPS_0: &str = r########"
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
            "########;
pub(super) const DASHBOARD_OVERVIEW_0: &str = r########"
        SELECT sessions.id, sessions.title, sessions.last_event_at,
               workspaces.display_name AS workspace_name, sources.provider_kind AS source_kind
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.session_class = 'work'
          AND sessions.session_role = 'primary'
          AND NOT EXISTS (SELECT 1 FROM workstream_links
                          WHERE entity_type = 'session'
                            AND entity_id = CAST(sessions.id AS TEXT))
          AND NOT EXISTS (SELECT 1 FROM thread_links
                          WHERE entity_type = 'session'
                            AND entity_id = CAST(sessions.id AS TEXT))
        ORDER BY sessions.last_event_at DESC
        "########;
pub(super) const DASHBOARD_OVERVIEW_1: &str = r########"
        SELECT COUNT(*) AS count FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE (context_documents.context_root_id IS NULL OR context_roots.enabled = 1)
          AND NOT EXISTS (SELECT 1 FROM workstream_links
                          WHERE entity_type = 'document'
                            AND entity_id = CAST(context_documents.id AS TEXT))
          AND NOT EXISTS (SELECT 1 FROM thread_links
                          WHERE entity_type = 'document'
                            AND entity_id = CAST(context_documents.id AS TEXT))
        "########;
pub(super) const DASHBOARD_OVERVIEW_2: &str =
    r########"SELECT COUNT(*) AS count FROM suggestions WHERE status = 'pending'"########;
pub(super) const GENERATE_SUGGESTIONS_0: &str = r########"
        SELECT sessions.id, sessions.title, sessions.cwd_raw AS detail,
               sessions.last_event_at AS activity_at, 'session' AS entity_type
        FROM sessions
        WHERE session_class = 'work'
          AND session_role = 'primary'
        ORDER BY last_event_at DESC LIMIT 120
        "########;
pub(super) const GENERATE_SUGGESTIONS_1: &str = r########"
        SELECT context_documents.id, context_documents.title,
               context_documents.relative_path AS detail,
               datetime(context_documents.mtime_ns / 1000000000, 'unixepoch') AS activity_at,
               'document' AS entity_type
        FROM context_documents
        LEFT JOIN context_roots ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.context_root_id IS NULL OR context_roots.enabled = 1
        ORDER BY context_documents.mtime_ns DESC LIMIT 120
        "########;
pub(super) const GENERATE_SUGGESTIONS_2: &str = r########"
                INSERT OR IGNORE INTO suggestions(
                    suggestion_type, target_type, target_id, title, description,
                    rationale, payload_json, fingerprint, confidence
                ) VALUES ('link', ?, ?, ?, ?, ?, ?, ?, ?)
                "########;
pub(super) const RESOLVE_SUGGESTION_0: &str =
    r########"SELECT * FROM suggestions WHERE id = ?"########;
pub(super) const RESOLVE_SUGGESTION_1: &str =
    r########"UPDATE suggestions SET status = 'pending', resolved_at = NULL WHERE id = ?"########;
pub(super) const RESOLVE_SUGGESTION_2: &str =
    r########"UPDATE suggestions SET status = ?, resolved_at = ? WHERE id = ?"########;
pub(super) const TOUCH_WORKSTREAM_0: &str =
    r########"UPDATE workstreams SET updated_at = ?, last_activity_at = ? WHERE id = ?"########;
pub(super) const VALIDATE_ENTITY_0: &str = r########"SELECT id FROM {} WHERE id = ?{}"########;
pub(super) const TARGET_HAS_LINK_0: &str =
    r########"SELECT 1 FROM {} WHERE {} = ? AND entity_type = ? AND entity_id = ?"########;
