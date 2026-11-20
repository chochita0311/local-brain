//! Frozen catalog/query ownership. Values always use bound parameters.
pub const SITES: &str = r#"
        SELECT atlassian_sites.id AS site_id,
               atlassian_site_bindings.id AS binding_id,
               atlassian_sites.normalized_domain,
               atlassian_sites.canonical_base_url,
               atlassian_sites.display_name AS site_display_name,
               external_source_instances.id AS source_instance_id,
               external_source_instances.instance_key,
               external_source_instances.display_name,
               external_source_instances.display_name AS source_display_name,
               external_source_instances.provider_kind,
               external_source_instances.enabled,
               CASE WHEN external_source_instances.config_ref IS NULL
                    THEN 0 ELSE 1 END AS config_bound
        FROM atlassian_sites
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.site_id = atlassian_sites.id
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_site_bindings.source_instance_id
        WHERE external_source_instances.service = ?
        ORDER BY external_source_instances.display_name,
                 atlassian_sites.normalized_domain,
                 atlassian_sites.id
        "#;
pub const CONNECTION: &str = r#"
        SELECT external_source_instances.*,
               atlassian_site_bindings.id AS binding_id,
               atlassian_sites.id AS site_id,
               atlassian_sites.canonical_base_url,
               atlassian_sites.display_name AS site_display_name
        FROM external_source_instances
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.source_instance_id =
             external_source_instances.id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_site_bindings.site_id
        WHERE external_source_instances.id = ?
          AND atlassian_sites.id = ?
        "#;
pub const INVENTORY_ITEMS: &str = r#"
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               external_resources.title,
               atlassian_sites.id AS site_id,
               atlassian_sites.normalized_domain,
               external_source_instances.id AS source_instance_id,
               COALESCE(
                   external_source_instances.display_name, '로컬 전용'
               ) AS source_name,
               atlassian_item_urls.normalized_url AS canonical_url,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale
        FROM atlassian_items
        JOIN external_resources
          ON external_resources.id = atlassian_items.external_resource_id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_items.source_instance_id
        LEFT JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        LEFT JOIN atlassian_item_remote_state
          ON atlassian_item_remote_state.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.service = ?
        ORDER BY atlassian_items.updated_at DESC,
                 atlassian_items.external_resource_id DESC
        "#;
pub const INVENTORY_SPACES: &str = r#"
            SELECT atlassian_spaces.*,
                   atlassian_sites.normalized_domain,
                   external_source_instances.id AS source_instance_id,
                   COALESCE(
                       external_source_instances.display_name, '로컬 전용'
                   ) AS source_name
            FROM atlassian_spaces
            JOIN atlassian_sites
              ON atlassian_sites.id = atlassian_spaces.site_id
            LEFT JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_spaces.source_instance_id
            WHERE atlassian_spaces.service = ?
            ORDER BY atlassian_spaces.name, atlassian_spaces.id
            "#;
pub const SCOPE_SITES: &str = r#"
        SELECT atlassian_sites.id AS site_id,
               atlassian_sites.normalized_domain,
               atlassian_sites.display_name,
               COALESCE(item_counts.item_count, 0) AS item_count
        FROM atlassian_sites
        LEFT JOIN (
            SELECT site_id, COUNT(*) AS item_count
            FROM atlassian_items
            WHERE service = ?
            GROUP BY site_id
        ) AS item_counts ON item_counts.site_id = atlassian_sites.id
        WHERE EXISTS (
            SELECT 1 FROM atlassian_spaces
            WHERE atlassian_spaces.site_id = atlassian_sites.id
              AND atlassian_spaces.service = ?
        ) OR item_counts.item_count IS NOT NULL OR EXISTS (
            SELECT 1
            FROM atlassian_site_bindings
            JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_site_bindings.source_instance_id
            WHERE atlassian_site_bindings.site_id = atlassian_sites.id
              AND external_source_instances.service = ?
        )
        ORDER BY atlassian_sites.normalized_domain, atlassian_sites.id
        "#;
pub const SCOPE_SPACES: &str = r#"
        SELECT atlassian_spaces.id, atlassian_spaces.site_id,
               atlassian_spaces.service, atlassian_spaces.remote_id,
               atlassian_spaces.space_key, atlassian_spaces.name,
               atlassian_spaces.canonical_url, atlassian_spaces.coverage,
               atlassian_sites.normalized_domain
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        WHERE atlassian_spaces.service = ?
        ORDER BY atlassian_spaces.name, atlassian_spaces.id
        "#;
pub const CATALOG_SITE: &str = r#"
        SELECT atlassian_sites.*, external_source_instances.id AS source_instance_id,
               external_source_instances.service
        FROM atlassian_sites
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.site_id = atlassian_sites.id
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_site_bindings.source_instance_id
        WHERE atlassian_sites.id = ?
          AND external_source_instances.enabled = 1
          AND (? IS NULL OR external_source_instances.id = ?)
        ORDER BY
          CASE WHEN external_source_instances.id =
                    atlassian_sites.source_instance_id
               THEN 0 ELSE 1 END,
          external_source_instances.id
        "#;
pub const CANDIDATE_SITE: &str = r#"
        SELECT atlassian_sites.*,
               external_source_instances.id AS source_instance_id,
               external_source_instances.service
        FROM atlassian_sites
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.site_id = atlassian_sites.id
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_site_bindings.source_instance_id
        WHERE atlassian_sites.id = ?
          AND external_source_instances.service = ?
          AND external_source_instances.enabled = 1
          AND (? IS NULL OR external_source_instances.id = ?)
        ORDER BY external_source_instances.id
        "#;
pub const CANDIDATE_EXISTING: &str = r#"
        SELECT id FROM atlassian_spaces
        WHERE site_id = ? AND service = ? AND space_key = ?
        "#;
pub const CATALOG_RUN: &str = r#"
        SELECT maintenance_runs.status, maintenance_runs.structured_result_json,
               external_sync_runs.service,
               external_sync_runs.source_instance_id
        FROM maintenance_runs
        JOIN external_sync_runs
          ON external_sync_runs.maintenance_run_id = maintenance_runs.id
        WHERE maintenance_runs.id = ?
        "#;
