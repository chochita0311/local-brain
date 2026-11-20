// Ordered compatible migration steps. SQL and additive definitions mirror the legacy owners.
use super::{contracts, identity, resources, revisions, support::*};
use crate::backend::{db, Config, Result};
use rusqlite::Connection;
use std::{fs, path::Path};
fn remove_metadata(connection: &Connection) -> Result<()> {
    if has(connection, "activity_events", "metadata_json")? {
        let count: i64 = connection.query_row(
            "SELECT COUNT(*) FROM activity_events WHERE metadata_json IS NOT NULL",
            [],
            |row| row.get(0),
        )?;
        if count != 0 {
            return Err(fail(&format!(
                "Activity Event metadata removal refused {count} non-null row(s)"
            )));
        }
        drop_column(connection, "activity_events", "metadata_json")?;
    }
    Ok(())
}
fn index_keys(connection: &Connection, name: &str) -> Result<Vec<String>> {
    Ok(db::rows(
        connection,
        &format!("PRAGMA index_xinfo({})", quote(name)),
        [],
    )?
    .into_iter()
    .filter(|row| row["key"].as_i64() == Some(1))
    .filter_map(|row| row["name"].as_str().map(str::to_owned))
    .collect())
}
fn indexes(connection: &Connection) -> Result<()> {
    let mut drop = Vec::new();
    for (table, index, required) in [
        (
            "activity_events",
            "idx_events_session_sequence",
            vec!["session_id", "sequence"],
        ),
        ("local_resources", "idx_local_resources_path", vec!["path"]),
        (
            "checkpoint_resource_refs",
            "idx_checkpoint_resource_refs",
            vec!["checkpoint_id", "thread_id"],
        ),
    ] {
        let indexes = db::rows(
            connection,
            &format!("PRAGMA index_list({})", quote(table)),
            [],
        )?;
        if !indexes.iter().any(|row| row["name"] == index) {
            continue;
        }
        let mut covered = false;
        for row in indexes {
            if row["origin"] == "u"
                && index_keys(connection, row["name"].as_str().unwrap_or(""))?.starts_with(
                    &required
                        .iter()
                        .map(|name| name.to_string())
                        .collect::<Vec<_>>(),
                )
            {
                covered = true;
            }
        }
        if !covered {
            return Err(fail(&format!(
                "Cannot remove {index}: required UNIQUE index coverage is missing"
            )));
        }
        drop.push(index);
    }
    for index in drop {
        connection.execute_batch(&format!("DROP INDEX {}", quote(index)))?;
    }
    connection.execute_batch("CREATE INDEX IF NOT EXISTS idx_checkpoints_workstream_version ON checkpoints(workstream_id,version DESC); CREATE INDEX IF NOT EXISTS idx_documents_source ON context_documents(source_id); CREATE INDEX IF NOT EXISTS idx_documents_workspace ON context_documents(workspace_id,mtime_ns DESC); CREATE INDEX IF NOT EXISTS idx_source_files_session ON source_files(session_id,path)")?;
    Ok(())
}
fn markdown_inside(path: &Path, recursive: bool) -> bool {
    if recursive {
        walkdir::WalkDir::new(path)
            .into_iter()
            .filter_map(std::result::Result::ok)
            .any(|entry| entry.path().extension().is_some_and(|value| value == "md"))
    } else {
        fs::read_dir(path).is_ok_and(|entries| {
            entries
                .filter_map(std::result::Result::ok)
                .any(|entry| entry.path().extension().is_some_and(|value| value == "md"))
        })
    }
}
fn context_roots(connection: &Connection, config: &Config) -> Result<()> {
    let root = crate::backend::storage::files::expand(&config.context_root, config);
    let root = if root.exists() {
        crate::backend::storage::files::resolve(&root)?
    } else {
        root
    };
    if db::row(connection, "SELECT id FROM context_roots LIMIT 1", [])?.is_none()
        && root.is_dir()
        && db::row(connection, "SELECT 1 FROM context_documents LIMIT 1", [])?.is_some()
    {
        let mut children = fs::read_dir(&root)?
            .filter_map(std::result::Result::ok)
            .map(|entry| entry.path())
            .filter(|path| {
                path.is_dir()
                    && !path
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .starts_with('.')
                    && markdown_inside(path, true)
            })
            .collect::<Vec<_>>();
        children.sort();
        if children.is_empty() && markdown_inside(&root, false) {
            children.push(root.clone());
        }
        for path in children {
            let path = crate::backend::storage::files::resolve(&path)?;
            connection.execute(
                "INSERT OR IGNORE INTO context_roots(path,label) VALUES (?,?)",
                [
                    path.to_string_lossy().as_ref(),
                    path.file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .as_ref(),
                ],
            )?;
        }
    }
    let roots = db::rows(
        connection,
        "SELECT id,path FROM context_roots ORDER BY length(path) DESC",
        [],
    )?;
    for document in db::rows(
        connection,
        "SELECT id,path FROM context_documents WHERE context_root_id IS NULL",
        [],
    )? {
        for root in &roots {
            if let Ok(relative) = Path::new(document["path"].as_str().unwrap_or(""))
                .strip_prefix(Path::new(root["path"].as_str().unwrap_or("")))
            {
                connection.execute(
                    "UPDATE context_documents SET context_root_id=?,relative_path=? WHERE id=?",
                    rusqlite::params![
                        root["id"].as_i64(),
                        relative.to_string_lossy(),
                        document["id"].as_i64()
                    ],
                )?;
                break;
            }
        }
    }
    Ok(())
}
pub fn run(connection: &Connection, config: &Config) -> Result<()> {
    ensure(
        connection,
        "sources",
        "profile_color",
        "TEXT CHECK(profile_color IN ('green','blue','orange','yellow','red','gray'))",
    )?;
    ensure(
        connection,
        "sources",
        "profile_position",
        "INTEGER NOT NULL DEFAULT 2147483647 CHECK(profile_position >= 0)",
    )?;
    let session_contract_changed = (ensure(connection, "sessions", "git_branch", "TEXT")?)
        | (ensure(
            connection,
            "sessions",
            "session_role",
            "TEXT NOT NULL DEFAULT 'primary' CHECK(session_role IN ('primary', 'subsession'))",
        )?)
        | (ensure(connection, "sessions", "parent_external_id", "TEXT")?)
        | (ensure(
            connection,
            "sessions",
            "parent_session_id",
            "INTEGER REFERENCES sessions(id) ON DELETE SET NULL",
        )?)
        | (ensure(
            connection,
            "sessions",
            "session_class",
            "TEXT NOT NULL DEFAULT 'work'",
        )?)
        | (ensure(
            connection,
            "sessions",
            "index_policy",
            "TEXT NOT NULL DEFAULT 'full'",
        )?)
        | (ensure(connection, "sessions", "maintenance_run_id", "TEXT")?);
    let usage_normalizer_contract_changed =
        ensure(connection, "source_files", "usage_contract_version", "TEXT")?;
    ensure(connection,"source_files","session_contract_version","INTEGER CHECK(session_contract_version IS NULL OR (typeof(session_contract_version) = 'integer' AND session_contract_version > 0))")?;
    ensure(
        connection,
        "source_files",
        "session_id",
        "INTEGER REFERENCES sessions(id) ON DELETE SET NULL",
    )?;
    ensure(
        connection,
        "source_files",
        "reference_contract_version",
        "TEXT",
    )?;
    ensure(
        connection,
        "source_files",
        "presence_state",
        "TEXT NOT NULL DEFAULT 'UNKNOWN' CHECK(presence_state IN ('PRESENT','MISSING','UNKNOWN'))",
    )?;
    ensure(connection, "source_files", "presence_checked_at", "TEXT")?;
    ensure(connection, "source_files", "presence_error", "TEXT")?;
    revisions::migrate(connection)?;
    let atlassian_space_url_added = ensure(
        connection,
        "atlassian_spaces",
        "canonical_url",
        "TEXT NOT NULL DEFAULT ''",
    )?;
    let atlassian_space_coverage_added = ensure(
        connection,
        "atlassian_spaces",
        "coverage",
        "TEXT NOT NULL DEFAULT 'selected-content'",
    )?;
    ensure(
        connection,
        "atlassian_spaces",
        "source_instance_id",
        "INTEGER REFERENCES external_source_instances(id) ON DELETE SET NULL",
    )?;
    ensure(
        connection,
        "atlassian_items",
        "source_instance_id",
        "INTEGER REFERENCES external_source_instances(id) ON DELETE SET NULL",
    )?;
    // Python sqlite begins a transaction at the first compatible DML.
    if connection.is_autocommit() {
        connection.execute_batch("BEGIN")?;
    }
    connection.execute_batch("\n        INSERT OR IGNORE INTO atlassian_site_bindings(\n            site_id, source_instance_id\n        )\n        SELECT id, source_instance_id\n        FROM atlassian_sites\n        WHERE source_instance_id IS NOT NULL\n        ")?;
    connection.execute_batch("\n        UPDATE atlassian_spaces\n        SET source_instance_id = (\n            SELECT atlassian_sites.source_instance_id\n            FROM atlassian_sites\n            WHERE atlassian_sites.id = atlassian_spaces.site_id\n        )\n        WHERE source_instance_id IS NULL\n          AND EXISTS (\n            SELECT 1\n            FROM atlassian_sites\n            WHERE atlassian_sites.id = atlassian_spaces.site_id\n              AND atlassian_sites.source_instance_id IS NOT NULL\n          )\n        ")?;
    connection.execute_batch("\n        UPDATE atlassian_items\n        SET source_instance_id = (\n            SELECT atlassian_sites.source_instance_id\n            FROM atlassian_sites\n            WHERE atlassian_sites.id = atlassian_items.site_id\n        )\n        WHERE source_instance_id IS NULL\n          AND EXISTS (\n            SELECT 1\n            FROM atlassian_sites\n            WHERE atlassian_sites.id = atlassian_items.site_id\n              AND atlassian_sites.source_instance_id IS NOT NULL\n          )\n        ")?;
    identity::migrate(connection, config)?;
    drop_column(connection, "sources", "enabled")?;
    drop_column(connection, "workspaces", "git_branch")?;
    for (table,column,definition) in [
        ("sources","last_scan_success_at","TEXT"),
        ("sources","last_scan_status","TEXT"),
        ("sources","last_scan_error","TEXT"),
        ("context_documents","context_root_id","INTEGER REFERENCES context_roots(id) ON DELETE SET NULL"),
        ("context_documents","content_type","TEXT NOT NULL DEFAULT 'text/markdown'"),
        ("context_roots","source_type","TEXT NOT NULL DEFAULT 'folder'"),
        ("context_roots","display_order","INTEGER CHECK(display_order >= 0)"),
        ("context_roots","readable","INTEGER NOT NULL DEFAULT 1"),
        ("context_roots","status","TEXT NOT NULL DEFAULT 'ready'"),
        ("context_roots","error","TEXT"),
        ("workstream_links","relation_type","TEXT NOT NULL DEFAULT 'related-to'"),
        ("checkpoints","based_on_activity_at","TEXT"),
        ("checkpoints","version","INTEGER NOT NULL DEFAULT 1"),
        ("checkpoints","updated_at","TEXT"),
        ("maintenance_runs","workstream_id","INTEGER"),
        ("maintenance_runs","task_type","TEXT"),
        ("maintenance_runs","runner","TEXT NOT NULL DEFAULT 'claude'"),
        ("maintenance_runs","cwd","TEXT"),
        ("maintenance_runs","pid","INTEGER"),
        ("maintenance_runs","manifest_path","TEXT"),
        ("maintenance_runs","prompt_path","TEXT"),
        ("maintenance_runs","stream_path","TEXT"),
        ("maintenance_runs","result_path","TEXT"),
        ("maintenance_runs","stderr_path","TEXT"),
        ("maintenance_runs","structured_result_json","TEXT"),
        ("maintenance_runs","suggestions_created","INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs","refresh_suggestions","INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs","mcp_call_budget","INTEGER NOT NULL DEFAULT 20"),
        ("maintenance_runs","mcp_calls_used","INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs","mcp_tool_calls_json","TEXT"),
        ("maintenance_runs","mcp_budget_exceeded","INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs","error","TEXT"),
        ("maintenance_runs","updated_at","TEXT"),
        ("suggestions","origin_run_id","TEXT"),
        ("usage_records","workspace_id_snapshot","INTEGER"),
        ("usage_records","project_key","TEXT"),
        ("usage_records","project_name_snapshot","TEXT"),
        ("usage_records","project_path_snapshot","TEXT"),
        ("usage_records","project_git_root_snapshot","TEXT"),
        ("usage_records","normalizer_version","TEXT NOT NULL DEFAULT 'legacy-v1'"),
        ("usage_model_prices","long_context_threshold_tokens","INTEGER CHECK(long_context_threshold_tokens IS NULL OR long_context_threshold_tokens > 0)"),
        ("usage_model_prices","long_context_input_usd_per_million","TEXT"),
        ("usage_model_prices","long_context_output_usd_per_million","TEXT"),
        ("usage_model_prices","long_context_cache_write_usd_per_million","TEXT"),
        ("usage_model_prices","long_context_cache_read_usd_per_million","TEXT"),
    ] { ensure(connection,table,column,definition)?; }
    ensure(
        connection,
        "usage_records",
        "attribution_basis",
        "TEXT NOT NULL DEFAULT 'unassigned'",
    )?;
    let usage_attributed_at_added = ensure(connection, "usage_records", "attributed_at", "TEXT")?;
    if true {
        if atlassian_space_url_added {
            connection.execute_batch("\n                UPDATE atlassian_spaces\n                SET canonical_url = (\n                    SELECT atlassian_sites.canonical_base_url ||\n                           CASE atlassian_spaces.service\n                               WHEN 'jira' THEN '/projects/'\n                               ELSE '/spaces/'\n                           END ||\n                           COALESCE(\n                               atlassian_spaces.space_key,\n                               atlassian_spaces.remote_id\n                           ) ||\n                           CASE atlassian_spaces.service\n                               WHEN 'confluence' THEN '/overview'\n                               ELSE ''\n                           END\n                    FROM atlassian_sites\n                    WHERE atlassian_sites.id = atlassian_spaces.site_id\n                )\n                WHERE canonical_url = ''\n                ")?;
        }
        if atlassian_space_coverage_added {
            connection.execute_batch("\n                UPDATE atlassian_spaces\n                SET coverage = 'full-content'\n                WHERE service = 'confluence'\n                ")?;
        }
        if session_contract_changed || usage_normalizer_contract_changed {
            connection.execute_batch("\n                UPDATE source_files\n                SET status = 'stale'\n                WHERE source_id IN (\n                    SELECT id FROM sources\n                    WHERE provider_kind IN ('claude', 'codex')\n                )\n                ")?;
        }
        connection.execute_batch("UPDATE checkpoints SET updated_at = COALESCE(updated_at, created_at) WHERE updated_at IS NULL")?;
        connection.execute_batch("UPDATE maintenance_runs SET updated_at = COALESCE(updated_at, created_at) WHERE updated_at IS NULL")?;
        if usage_attributed_at_added {
            connection.execute_batch("\n                UPDATE usage_records\n                SET attributed_at = imported_at\n                WHERE attributed_at IS NULL\n                ")?;
        }
        context_roots(connection, config)?;
        resources::repair_external(connection)?;
        contracts::repair_attribution(connection)?;
        contracts::repair_maintenance(connection)?;
        contracts::repair_session(connection)?;
    }
    resources::migrate(connection, config)?;
    remove_metadata(connection)?;
    ensure(
        connection,
        "activity_events",
        "message_phase",
        "TEXT CHECK(message_phase IN ('commentary', 'final_answer'))",
    )?;
    indexes(connection)?;
    // The legacy executescript commits compatible data before index DDL.
    if !connection.is_autocommit() {
        connection.execute_batch("COMMIT")?;
    }
    connection.execute_batch("\n        CREATE INDEX IF NOT EXISTS idx_sessions_class\n            ON sessions(session_class, last_event_at DESC);\n        CREATE INDEX IF NOT EXISTS idx_sessions_role\n            ON sessions(session_role, last_event_at DESC);\n        CREATE INDEX IF NOT EXISTS idx_sessions_parent\n            ON sessions(parent_session_id, last_event_at DESC);\n        CREATE INDEX IF NOT EXISTS idx_threads_workstream\n            ON threads(workstream_id, status, position);\n        CREATE INDEX IF NOT EXISTS idx_thread_links_entity\n            ON thread_links(entity_type, entity_id);\n        CREATE INDEX IF NOT EXISTS idx_workstream_links_entity\n            ON workstream_links(entity_type, entity_id);\n        CREATE INDEX IF NOT EXISTS idx_suggestions_target\n            ON suggestions(target_type, target_id, status);\n        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_workstream\n            ON maintenance_runs(workstream_id, created_at DESC);\n        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_status\n            ON maintenance_runs(status, updated_at DESC);\n        CREATE INDEX IF NOT EXISTS idx_external_sync_runs_source_instance\n            ON external_sync_runs(source_instance_id, maintenance_run_id);\n        CREATE INDEX IF NOT EXISTS idx_external_sync_runs_scope\n            ON external_sync_runs(requested_scope_kind, maintenance_run_id);\n        CREATE INDEX IF NOT EXISTS idx_atlassian_sites_source\n            ON atlassian_sites(source_instance_id, normalized_domain);\n        CREATE INDEX IF NOT EXISTS idx_atlassian_spaces_site\n            ON atlassian_spaces(site_id, service, name);\n        CREATE INDEX IF NOT EXISTS idx_atlassian_items_site\n            ON atlassian_items(site_id, service, coverage);\n        CREATE INDEX IF NOT EXISTS idx_atlassian_items_space\n            ON atlassian_items(space_id, service);\n        CREATE INDEX IF NOT EXISTS idx_atlassian_item_urls_item\n            ON atlassian_item_urls(external_resource_id, url_role);\n        CREATE UNIQUE INDEX IF NOT EXISTS idx_atlassian_item_urls_canonical\n            ON atlassian_item_urls(external_resource_id)\n            WHERE url_role = 'canonical';\n        CREATE INDEX IF NOT EXISTS idx_atlassian_remote_state_check\n            ON atlassian_item_remote_state(last_successful_at, last_outcome);\n        CREATE INDEX IF NOT EXISTS idx_atlassian_item_classifications_classification\n            ON atlassian_item_classifications(\n                classification_id, external_resource_id\n            );\n        CREATE INDEX IF NOT EXISTS idx_suggestions_origin_run\n            ON suggestions(origin_run_id, status);\n        CREATE INDEX IF NOT EXISTS idx_documents_context_root\n            ON context_documents(context_root_id, mtime_ns DESC);\n        ")?;
    Ok(())
}
