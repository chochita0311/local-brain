//! Original read ownership and parameterized refresh queries.
pub const SCOPE_ITEM: &str = r#"
            SELECT external_resources.title
            FROM atlassian_items
            JOIN external_resources
              ON external_resources.id =
                 atlassian_items.external_resource_id
            WHERE atlassian_items.external_resource_id = ?
            "#;
pub const SCOPE_SPACE: &str = r#"SELECT name AS title FROM atlassian_spaces WHERE id = ?"#;
pub const SCOPE_THREAD: &str = r#"
            SELECT threads.title, threads.workstream_id
            FROM threads WHERE id = ?
            "#;
pub const SCOPE_WORKSTREAM: &str = r#"SELECT name AS title FROM workstreams WHERE id = ?"#;
pub const IDS_SPACE: &str = r#"
            SELECT external_resource_id
            FROM atlassian_items
            WHERE space_id = ?
            ORDER BY external_resource_id
            "#;
pub const IDS_THREAD: &str = r#"
            SELECT DISTINCT atlassian_items.external_resource_id
            FROM thread_links
            JOIN atlassian_items
              ON atlassian_items.external_resource_id =
                 CAST(thread_links.entity_id AS INTEGER)
            WHERE thread_links.thread_id = ?
              AND thread_links.entity_type = 'external'
            ORDER BY atlassian_items.external_resource_id
            "#;
pub const IDS_WORKSTREAM: &str = r#"
            SELECT external_resource_id
            FROM (
                SELECT atlassian_items.external_resource_id
                FROM workstream_links
                JOIN atlassian_items
                  ON atlassian_items.external_resource_id =
                     CAST(workstream_links.entity_id AS INTEGER)
                WHERE workstream_links.workstream_id = ?
                  AND workstream_links.entity_type = 'external'
                UNION
                SELECT atlassian_items.external_resource_id
                FROM threads
                JOIN thread_links
                  ON thread_links.thread_id = threads.id
                JOIN atlassian_items
                  ON atlassian_items.external_resource_id =
                     CAST(thread_links.entity_id AS INTEGER)
                WHERE threads.workstream_id = ?
                  AND thread_links.entity_type = 'external'
            )
            ORDER BY external_resource_id
            "#;
pub const IDS_ALL: &str = r#"
            SELECT external_resource_id
            FROM atlassian_items
            ORDER BY external_resource_id
            "#;
pub const ITEMS: &str = r#"
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.service,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               external_resources.title,
               atlassian_spaces.id AS space_id,
               atlassian_spaces.name AS space_name,
               atlassian_sites.id AS site_id,
               atlassian_sites.normalized_domain,
               external_source_instances.id AS source_instance_id,
               external_source_instances.display_name AS source_name,
               external_source_instances.enabled AS source_enabled,
               atlassian_item_urls.normalized_url AS canonical_url,
               atlassian_item_remote_state.remote_version,
               atlassian_item_remote_state.remote_updated_at,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale,
               external_resource_content.source_hash AS content_hash,
               external_resource_content.applied_at AS content_applied_at
        FROM atlassian_items
        JOIN external_resources
          ON external_resources.id = atlassian_items.external_resource_id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_items.source_instance_id
        LEFT JOIN atlassian_spaces
          ON atlassian_spaces.id = atlassian_items.space_id
        LEFT JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        LEFT JOIN atlassian_item_remote_state
          ON atlassian_item_remote_state.external_resource_id =
             atlassian_items.external_resource_id
        LEFT JOIN external_resource_content
          ON external_resource_content.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.external_resource_id IN ({})
        "#;
pub const PREVIEW_SPACE: &str = r#"
            SELECT atlassian_spaces.*, atlassian_sites.normalized_domain,
                   external_source_instances.id AS source_instance_id,
                   external_source_instances.display_name AS source_name,
                   external_source_instances.enabled
            FROM atlassian_spaces
            JOIN atlassian_sites
              ON atlassian_sites.id = atlassian_spaces.site_id
            LEFT JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_spaces.source_instance_id
            WHERE atlassian_spaces.id = ?
            "#;
pub const CATALOG_SPACE: &str = r#"
        SELECT atlassian_spaces.*, atlassian_sites.canonical_base_url,
               external_source_instances.id AS source_instance_id
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_spaces.source_instance_id
        WHERE atlassian_spaces.id = ?
          AND atlassian_spaces.service = 'confluence'
        "#;
pub const APPLICATION_ITEM: &str = r#"
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.coverage,
               atlassian_items.site_id,
               atlassian_items.service,
               external_source_instances.id AS source_instance_id,
               atlassian_item_urls.normalized_url AS canonical_url
        FROM atlassian_items
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_items.source_instance_id
        LEFT JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        WHERE atlassian_items.external_resource_id = ?
        "#;
pub const APPLY_SPACE: &str = r#"
        SELECT atlassian_spaces.*, atlassian_sites.id AS site_id,
               atlassian_sites.canonical_base_url,
               external_source_instances.id AS source_instance_id
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_spaces.source_instance_id
        WHERE atlassian_spaces.id = ?
          AND atlassian_spaces.service = 'confluence'
        "#;
pub const APPLY_EXISTING: &str = r#"
            SELECT atlassian_items.external_resource_id
            FROM atlassian_item_urls
            JOIN atlassian_items
              ON atlassian_items.external_resource_id =
                 atlassian_item_urls.external_resource_id
            WHERE atlassian_item_urls.site_id = ?
              AND atlassian_item_urls.normalized_url = ?
            "#;
pub const RUN_RESULT: &str = r#"
        SELECT maintenance_runs.status,
               maintenance_runs.structured_result_json,
               external_sync_runs.requested_scope_kind,
               external_sync_runs.service
        FROM maintenance_runs
        JOIN external_sync_runs
          ON external_sync_runs.maintenance_run_id = maintenance_runs.id
        WHERE maintenance_runs.id = ?
          AND maintenance_runs.task_type = 'external_source_sync'
        "#;
