//! Verbatim SQL shapes from the existing deterministic retriever.
pub(super) const MATCHING_SEARCH_ROWS_0: &str = r########"
            SELECT entity_type, entity_id, title, path, bm25(search_index) AS fts_score
            FROM search_index
            WHERE search_index MATCH ?
              AND entity_type IN ('session', 'document')
            ORDER BY fts_score, entity_type, entity_id
            "########;
pub(super) const THREAD_LINK_MAPS_0: &str = r########"
            SELECT thread_links.thread_id, thread_links.entity_type,
                   thread_links.entity_id, thread_links.relation_type
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            WHERE threads.workstream_id = ?
            "########;
pub(super) const THREAD_LINK_MAPS_1: &str =
    r########"SELECT entity_type, entity_id FROM workstream_links WHERE workstream_id = ?"########;
pub(super) const SUGGESTION_STATES_0: &str = r########"
        SELECT suggestions.target_id, suggestions.status, suggestions.payload_json
        FROM suggestions
        JOIN threads ON suggestions.target_type = 'thread'
            AND threads.id = suggestions.target_id
        WHERE threads.workstream_id = ?
          AND suggestions.status IN ('pending', 'rejected')
        "########;
pub(super) const SESSION_RESOURCE_0: &str = r########"
        SELECT sessions.id, sessions.workspace_id, sessions.title, sessions.source_path,
               sessions.cwd_raw, sessions.started_at, sessions.ended_at,
               sessions.last_event_at, sessions.event_count,
               sessions.user_message_count, sessions.assistant_message_count,
               sessions.git_branch,
               sources.provider_kind AS source_kind,
               workspaces.display_name AS workspace_name,
               workspaces.canonical_path AS workspace_path,
               workspaces.git_root
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.id = ? AND sessions.session_class = 'work'
          AND sessions.session_role = 'primary'
        "########;
pub(super) const DOCUMENT_RESOURCE_0: &str = r########"
        SELECT id, workspace_id, title, path, relative_path, size_bytes, mtime_ns,
               content_hash
        FROM context_documents WHERE id = ?
        "########;
pub(super) const BUILD_CANDIDATE_BUNDLE_0: &str = r########"
                            SELECT id, sequence, occurred_at, event_type, role, text, tool_name
                            FROM activity_events WHERE session_id = ? ORDER BY sequence
                            "########;
pub(super) const BUILD_CANDIDATE_BUNDLE_1: &str =
    r########"SELECT body FROM context_documents WHERE id = ?"########;
pub(super) const ADD_DERIVED_RESOURCES_0: &str = r########"
            SELECT id, display_name AS title, canonical_path, git_root,
                   exists_now, last_activity_at, updated_at
            FROM workspaces WHERE id = ?
            "########;
pub(super) const ADD_DERIVED_RESOURCES_1: &str = r########"
            SELECT id, title, summary, current_goal, next_action
            FROM threads WHERE workstream_id = ? AND status != 'done'
            "########;
pub(super) const ADD_DERIVED_RESOURCES_2: &str = r########"
                SELECT id, display_name AS title, canonical_path, git_root,
                       exists_now, last_activity_at, updated_at
                FROM workspaces
                "########;
pub(super) const ADD_DERIVED_RESOURCES_3: &str = r########"SELECT id, title, path, resource_type, summary, exists_now, discovered_by, updated_at FROM local_resources"########;
pub(super) const ADD_DERIVED_RESOURCES_4: &str = r########"SELECT id, title, url, resource_type, summary, source_role, updated_at FROM external_resources"########;
