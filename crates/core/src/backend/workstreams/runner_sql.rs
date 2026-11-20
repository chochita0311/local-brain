//! Verbatim SQL contracts from existing Workstream task preparation/application.
pub(super) const RESOURCE_MANIFEST_0: &str = r########"
            SELECT sessions.title, sessions.source_path, sessions.cwd_raw,
                   sessions.git_branch,
                   sessions.last_event_at, sources.provider_kind AS source_kind
            FROM sessions JOIN sources ON sources.id = sessions.source_id
            WHERE sessions.id = ? AND sessions.session_class = 'work'
              AND sessions.session_role = 'primary'
            "########;
pub(super) const RESOURCE_MANIFEST_1: &str =
    r########"SELECT title, path, relative_path FROM context_documents WHERE id = ?"########;
pub(super) const RESOURCE_MANIFEST_2: &str = r########"
            SELECT display_name AS title, canonical_path, git_root,
                   exists_now, last_activity_at
            FROM workspaces WHERE id = ?
            "########;
pub(super) const RESOURCE_MANIFEST_3: &str = r########"
            SELECT title, resource_type, url, summary, source_role
            FROM external_resources WHERE id = ?
            "########;
pub(super) const RESOURCE_MANIFEST_4: &str = r########"
            SELECT title, resource_type, path, summary, exists_now, discovered_by
            FROM local_resources WHERE id = ?
            "########;
pub(super) const PREVIOUS_ANALYSIS_0: &str = r########"
        SELECT id, completed_at, source_snapshot_json, structured_result_json
        FROM maintenance_runs
        WHERE workstream_id = ? AND task_type = ? AND status = 'completed'
          AND structured_result_json IS NOT NULL
        ORDER BY completed_at DESC LIMIT 8
        "########;
pub(super) const PREPARE_RUN_0: &str = r########"
        INSERT INTO maintenance_runs(
            id, workstream_id, task_type, runner, cwd, status,
            source_snapshot_json, manifest_path, prompt_path, stream_path,
            result_path, stderr_path, refresh_suggestions, mcp_call_budget, updated_at
        ) VALUES (?, ?, ?, 'claude', ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        "########;
pub(super) const LIST_RUNS_0: &str = r########"
        SELECT maintenance_runs.*, workstreams.name AS workstream_name
        FROM maintenance_runs
        LEFT JOIN workstreams ON workstreams.id = maintenance_runs.workstream_id
        WHERE maintenance_runs.workstream_id = ?
          AND maintenance_runs.task_type IS NOT NULL
        ORDER BY maintenance_runs.created_at DESC
        LIMIT ?
        "########;
pub(super) const PERSIST_STRUCTURED_SUGGESTIONS_0: &str =
    r########"SELECT id FROM threads WHERE workstream_id = ?"########;
pub(super) const PERSIST_STRUCTURED_SUGGESTIONS_1: &str = r########"
            INSERT INTO suggestions(
                suggestion_type, target_type, target_id, title, description,
                rationale, payload_json, fingerprint, origin_run_id, confidence
            ) VALUES ('resource_link', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                rationale = excluded.rationale,
                payload_json = excluded.payload_json,
                origin_run_id = excluded.origin_run_id,
                confidence = excluded.confidence,
                status = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.status ELSE 'pending' END,
                resolved_at = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.resolved_at ELSE NULL END
            "########;
pub(super) const PERSIST_STRUCTURED_SUGGESTIONS_2: &str =
    r########"SELECT status, origin_run_id FROM suggestions WHERE fingerprint = ?"########;
pub(super) const PERSIST_STRUCTURED_SUGGESTIONS_3: &str = r########"
            INSERT INTO suggestions(
                suggestion_type, target_type, target_id, title, description,
                rationale, payload_json, fingerprint, origin_run_id, confidence
            ) VALUES ('checkpoint_draft', 'workstream', ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                rationale = excluded.rationale,
                payload_json = excluded.payload_json,
                origin_run_id = excluded.origin_run_id,
                confidence = excluded.confidence,
                status = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.status ELSE 'pending' END,
                resolved_at = CASE
                    WHEN suggestions.status IN ('accepted', 'rejected')
                    THEN suggestions.resolved_at ELSE NULL END
            "########;
pub(super) const PERSIST_STRUCTURED_SUGGESTIONS_4: &str =
    r########"SELECT status, origin_run_id FROM suggestions WHERE fingerprint = ?"########;
pub(super) const SUPERSEDE_RUNNER_SUGGESTIONS_0: &str = r########"
        UPDATE suggestions
        SET status = 'superseded', resolved_at = ?
        WHERE status = 'pending' AND origin_run_id IS NOT NULL
          AND ((target_type = 'workstream' AND target_id = ?)
               OR (target_type = 'thread' AND target_id IN
                   (SELECT id FROM threads WHERE workstream_id = ?)))
        "########;
