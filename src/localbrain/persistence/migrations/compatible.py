"""Ordered compatible structure and data steps; no implicit discovery."""

import sqlite3
from localbrain.foundation.config import settings
from localbrain.persistence.migrations.indexes import _migrate_schema_indexes
from localbrain.persistence.migrations.local_context import _migrate_context_roots
from localbrain.persistence.migrations.maintenance import _repair_maintenance_workstream_fk
from localbrain.persistence.migrations.resources import (
    _repair_external_resource_url_scope,
    migrate_shared_resources,
)
from localbrain.persistence.migrations.session_revisions import (
    REVISION_CHECK,
    migrate_session_revisions,
)
from localbrain.persistence.migrations.sessions import (
    _remove_unused_activity_event_metadata,
    _repair_maintenance_session_contract,
)
from localbrain.persistence.migrations.sources import _repair_source_provider_identity_contract
from localbrain.persistence.migrations.support import _drop_column, _ensure_column
from localbrain.persistence.migrations.usage import _repair_usage_attribution_check


def _run_compatible_migrations(
    connection: sqlite3.Connection, *, include_data_migrations: bool = True, config=settings
) -> None:
    # The local index is rebuildable, but user-curated workstreams are not. Keep
    # upgrades additive so both kinds of data survive normal application updates.
    _ensure_column(connection, "sources", "profile_color", "TEXT CHECK(profile_color IN ('green','blue','orange','yellow','red','gray'))")
    _ensure_column(connection, "sources", "profile_position", "INTEGER NOT NULL DEFAULT 2147483647 CHECK(profile_position >= 0)")
    session_contract_changed = any(
        (
            _ensure_column(connection, "sessions", "git_branch", "TEXT"),
            _ensure_column(
                connection,
                "sessions",
                "session_role",
                "TEXT NOT NULL DEFAULT 'primary' "
                "CHECK(session_role IN ('primary', 'subsession'))",
            ),
            _ensure_column(connection, "sessions", "parent_external_id", "TEXT"),
            _ensure_column(
                connection,
                "sessions",
                "parent_session_id",
                "INTEGER REFERENCES sessions(id) ON DELETE SET NULL",
            ),
            _ensure_column(
                connection, "sessions", "session_class", "TEXT NOT NULL DEFAULT 'work'"
            ),
            _ensure_column(
                connection, "sessions", "index_policy", "TEXT NOT NULL DEFAULT 'full'"
            ),
            _ensure_column(connection, "sessions", "maintenance_run_id", "TEXT"),
        )
    )
    usage_normalizer_contract_changed = _ensure_column(
        connection, "source_files", "usage_contract_version", "TEXT"
    )
    _ensure_column(
        connection, "source_files", "session_contract_version", "INTEGER " + REVISION_CHECK
    )
    _ensure_column(
        connection,
        "source_files",
        "session_id",
        "INTEGER REFERENCES sessions(id) ON DELETE SET NULL",
    )
    _ensure_column(
        connection, "source_files", "reference_contract_version", "TEXT"
    )
    migrate_session_revisions(connection)
    atlassian_space_url_added = _ensure_column(
        connection,
        "atlassian_spaces",
        "canonical_url",
        "TEXT NOT NULL DEFAULT ''",
    )
    atlassian_space_coverage_added = _ensure_column(
        connection,
        "atlassian_spaces",
        "coverage",
        "TEXT NOT NULL DEFAULT 'selected-content'",
    )
    _ensure_column(
        connection,
        "atlassian_spaces",
        "source_instance_id",
        "INTEGER REFERENCES external_source_instances(id) ON DELETE SET NULL",
    )
    _ensure_column(
        connection,
        "atlassian_items",
        "source_instance_id",
        "INTEGER REFERENCES external_source_instances(id) ON DELETE SET NULL",
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO atlassian_site_bindings(
            site_id, source_instance_id
        )
        SELECT id, source_instance_id
        FROM atlassian_sites
        WHERE source_instance_id IS NOT NULL
        """
    )
    connection.execute(
        """
        UPDATE atlassian_spaces
        SET source_instance_id = (
            SELECT atlassian_sites.source_instance_id
            FROM atlassian_sites
            WHERE atlassian_sites.id = atlassian_spaces.site_id
        )
        WHERE source_instance_id IS NULL
          AND EXISTS (
            SELECT 1
            FROM atlassian_sites
            WHERE atlassian_sites.id = atlassian_spaces.site_id
              AND atlassian_sites.source_instance_id IS NOT NULL
          )
        """
    )
    connection.execute(
        """
        UPDATE atlassian_items
        SET source_instance_id = (
            SELECT atlassian_sites.source_instance_id
            FROM atlassian_sites
            WHERE atlassian_sites.id = atlassian_items.site_id
        )
        WHERE source_instance_id IS NULL
          AND EXISTS (
            SELECT 1
            FROM atlassian_sites
            WHERE atlassian_sites.id = atlassian_items.site_id
              AND atlassian_sites.source_instance_id IS NOT NULL
          )
        """
    )
    _repair_source_provider_identity_contract(connection, config)
    _drop_column(connection, "sources", "enabled")
    _drop_column(connection, "workspaces", "git_branch")

    for table, column, definition in (
        ("sources", "last_scan_success_at", "TEXT"),
        ("sources", "last_scan_status", "TEXT"),
        ("sources", "last_scan_error", "TEXT"),
        (
            "context_documents",
            "context_root_id",
            "INTEGER REFERENCES context_roots(id) ON DELETE SET NULL",
        ),
        (
            "context_documents",
            "content_type",
            "TEXT NOT NULL DEFAULT 'text/markdown'",
        ),
        ("context_roots", "source_type", "TEXT NOT NULL DEFAULT 'folder'"),
        ("context_roots", "display_order", "INTEGER CHECK(display_order >= 0)"),
        ("context_roots", "readable", "INTEGER NOT NULL DEFAULT 1"),
        ("context_roots", "status", "TEXT NOT NULL DEFAULT 'ready'"),
        ("context_roots", "error", "TEXT"),
        ("workstream_links", "relation_type", "TEXT NOT NULL DEFAULT 'related-to'"),
        ("checkpoints", "based_on_activity_at", "TEXT"),
        ("checkpoints", "version", "INTEGER NOT NULL DEFAULT 1"),
        ("checkpoints", "updated_at", "TEXT"),
        ("maintenance_runs", "workstream_id", "INTEGER"),
        ("maintenance_runs", "task_type", "TEXT"),
        ("maintenance_runs", "runner", "TEXT NOT NULL DEFAULT 'claude'"),
        ("maintenance_runs", "cwd", "TEXT"),
        ("maintenance_runs", "pid", "INTEGER"),
        ("maintenance_runs", "manifest_path", "TEXT"),
        ("maintenance_runs", "prompt_path", "TEXT"),
        ("maintenance_runs", "stream_path", "TEXT"),
        ("maintenance_runs", "result_path", "TEXT"),
        ("maintenance_runs", "stderr_path", "TEXT"),
        ("maintenance_runs", "structured_result_json", "TEXT"),
        ("maintenance_runs", "suggestions_created", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "refresh_suggestions", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "mcp_call_budget", "INTEGER NOT NULL DEFAULT 20"),
        ("maintenance_runs", "mcp_calls_used", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "mcp_tool_calls_json", "TEXT"),
        ("maintenance_runs", "mcp_budget_exceeded", "INTEGER NOT NULL DEFAULT 0"),
        ("maintenance_runs", "error", "TEXT"),
        ("maintenance_runs", "updated_at", "TEXT"),
        ("suggestions", "origin_run_id", "TEXT"),
        ("usage_records", "workspace_id_snapshot", "INTEGER"),
        ("usage_records", "project_key", "TEXT"),
        ("usage_records", "project_name_snapshot", "TEXT"),
        ("usage_records", "project_path_snapshot", "TEXT"),
        ("usage_records", "project_git_root_snapshot", "TEXT"),
        (
            "usage_records",
            "normalizer_version",
            "TEXT NOT NULL DEFAULT 'legacy-v1'",
        ),
        (
            "usage_model_prices",
            "long_context_threshold_tokens",
            "INTEGER CHECK(long_context_threshold_tokens IS NULL OR long_context_threshold_tokens > 0)",
        ),
        ("usage_model_prices", "long_context_input_usd_per_million", "TEXT"),
        ("usage_model_prices", "long_context_output_usd_per_million", "TEXT"),
        (
            "usage_model_prices",
            "long_context_cache_write_usd_per_million",
            "TEXT",
        ),
        (
            "usage_model_prices",
            "long_context_cache_read_usd_per_million",
            "TEXT",
        ),
    ):
        _ensure_column(connection, table, column, definition)

    _ensure_column(
        connection,
        "usage_records",
        "attribution_basis",
        "TEXT NOT NULL DEFAULT 'unassigned'",
    )
    usage_attributed_at_added = _ensure_column(
        connection, "usage_records", "attributed_at", "TEXT"
    )

    if include_data_migrations:
        if atlassian_space_url_added:
            connection.execute(
                """
                UPDATE atlassian_spaces
                SET canonical_url = (
                    SELECT atlassian_sites.canonical_base_url ||
                           CASE atlassian_spaces.service
                               WHEN 'jira' THEN '/projects/'
                               ELSE '/spaces/'
                           END ||
                           COALESCE(
                               atlassian_spaces.space_key,
                               atlassian_spaces.remote_id
                           ) ||
                           CASE atlassian_spaces.service
                               WHEN 'confluence' THEN '/overview'
                               ELSE ''
                           END
                    FROM atlassian_sites
                    WHERE atlassian_sites.id = atlassian_spaces.site_id
                )
                WHERE canonical_url = ''
                """
            )
        if atlassian_space_coverage_added:
            connection.execute(
                """
                UPDATE atlassian_spaces
                SET coverage = 'full-content'
                WHERE service = 'confluence'
                """
            )
        if session_contract_changed or usage_normalizer_contract_changed:
            connection.execute(
                """
                UPDATE source_files
                SET status = 'stale'
                WHERE source_id IN (
                    SELECT id FROM sources
                    WHERE provider_kind IN ('claude', 'codex')
                )
                """
            )

        connection.execute(
            "UPDATE checkpoints SET updated_at = COALESCE(updated_at, created_at)"
        )
        connection.execute(
            "UPDATE maintenance_runs SET updated_at = COALESCE(updated_at, created_at)"
        )
        if usage_attributed_at_added:
            connection.execute(
                """
                UPDATE usage_records
                SET attributed_at = imported_at
                WHERE attributed_at IS NULL
                """
            )
        _migrate_context_roots(connection, config)
        _repair_external_resource_url_scope(connection)
        _repair_usage_attribution_check(connection)
        _repair_maintenance_workstream_fk(connection)
        _repair_maintenance_session_contract(connection)

    migrate_shared_resources(connection)
    _remove_unused_activity_event_metadata(connection)
    _ensure_column(
        connection, "activity_events", "message_phase",
        "TEXT CHECK(message_phase IN ('commentary', 'final_answer'))",
    )
    _migrate_schema_indexes(connection)

    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_class
            ON sessions(session_class, last_event_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sessions_role
            ON sessions(session_role, last_event_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sessions_parent
            ON sessions(parent_session_id, last_event_at DESC);
        CREATE INDEX IF NOT EXISTS idx_threads_workstream
            ON threads(workstream_id, status, position);
        CREATE INDEX IF NOT EXISTS idx_thread_links_entity
            ON thread_links(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_workstream_links_entity
            ON workstream_links(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_suggestions_target
            ON suggestions(target_type, target_id, status);
        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_workstream
            ON maintenance_runs(workstream_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_maintenance_runs_status
            ON maintenance_runs(status, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_external_sync_runs_source_instance
            ON external_sync_runs(source_instance_id, maintenance_run_id);
        CREATE INDEX IF NOT EXISTS idx_external_sync_runs_scope
            ON external_sync_runs(requested_scope_kind, maintenance_run_id);
        CREATE INDEX IF NOT EXISTS idx_atlassian_sites_source
            ON atlassian_sites(source_instance_id, normalized_domain);
        CREATE INDEX IF NOT EXISTS idx_atlassian_spaces_site
            ON atlassian_spaces(site_id, service, name);
        CREATE INDEX IF NOT EXISTS idx_atlassian_items_site
            ON atlassian_items(site_id, service, coverage);
        CREATE INDEX IF NOT EXISTS idx_atlassian_items_space
            ON atlassian_items(space_id, service);
        CREATE INDEX IF NOT EXISTS idx_atlassian_item_urls_item
            ON atlassian_item_urls(external_resource_id, url_role);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_atlassian_item_urls_canonical
            ON atlassian_item_urls(external_resource_id)
            WHERE url_role = 'canonical';
        CREATE INDEX IF NOT EXISTS idx_atlassian_remote_state_check
            ON atlassian_item_remote_state(last_successful_at, last_outcome);
        CREATE INDEX IF NOT EXISTS idx_atlassian_item_classifications_classification
            ON atlassian_item_classifications(
                classification_id, external_resource_id
            );
        CREATE INDEX IF NOT EXISTS idx_suggestions_origin_run
            ON suggestions(origin_run_id, status);
        CREATE INDEX IF NOT EXISTS idx_documents_context_root
            ON context_documents(context_root_id, mtime_ns DESC);
        """
    )
