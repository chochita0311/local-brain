//! Local-only Atlassian browse, bounded preview, classification and grouped search.

const SQL_NORMALIZE_BROWSE_STRUCTURE_0: &str = r#"
            SELECT site_id, service
            FROM atlassian_spaces
            WHERE id = ?
            "#;

const SQL_NORMALIZE_BROWSE_STRUCTURE_1: &str = r#"
                SELECT DISTINCT service
                FROM atlassian_items
                WHERE site_id = ?
                "#;

const SQL_NORMALIZE_BROWSE_STRUCTURE_2: &str = r#"
                    SELECT DISTINCT service
                    FROM atlassian_spaces
                    WHERE site_id = ?
                    "#;

const SQL_NORMALIZE_BROWSE_STRUCTURE_3: &str = r#"
                    SELECT DISTINCT service
                    FROM atlassian_structure_references AS reference
                    WHERE site_id = ?
                      AND EXISTS (
                          SELECT 1
                          FROM atlassian_structure_reference_evidence AS evidence
                          WHERE evidence.reference_id = reference.id
                      )
                    "#;

const SQL_VALIDATE_BROWSE_STRUCTURAL_SCOPE_0: &str = r#"
        SELECT 1
        FROM atlassian_items
        JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        WHERE atlassian_items.site_id = ?
          AND atlassian_items.space_id IS NULL
          AND (? IS NULL OR atlassian_items.service = ?)
          AND localbrain_atlassian_container_scope(
                  atlassian_item_urls.normalized_url
              ) = ?
        LIMIT 1
        "#;

const SQL_VALIDATE_BROWSE_STRUCTURAL_SCOPE_1: &str = r#"
            SELECT 1
            FROM atlassian_structure_references AS reference
            WHERE reference.site_id = ?
              AND (? IS NULL OR reference.service = ?)
              AND EXISTS (
                  SELECT 1
                  FROM atlassian_structure_reference_evidence
                  WHERE reference_id = reference.id
              )
              AND CASE
                    WHEN (
                        SELECT COUNT(DISTINCT container_hint)
                        FROM atlassian_structure_reference_evidence
                        WHERE reference_id = reference.id
                    ) = 1
                    THEN 'url:' || reference.service || ':' ||
                         (
                             SELECT MIN(container_hint)
                             FROM atlassian_structure_reference_evidence
                             WHERE reference_id = reference.id
                         )
                    ELSE 'unclassified'
                  END = ?
            LIMIT 1
            "#;

const SQL_CLASSIFICATION_MAPS_0: &str = r#"
            SELECT * FROM atlassian_classifications
            ORDER BY kind, normalized_name, id
            "#;

const SQL_CLASSIFICATION_MAPS_1: &str = r#"
        SELECT atlassian_item_classifications.external_resource_id,
               atlassian_classifications.*
        FROM atlassian_item_classifications
        JOIN atlassian_classifications
          ON atlassian_classifications.id =
             atlassian_item_classifications.classification_id
        ORDER BY atlassian_classifications.kind,
                 atlassian_classifications.normalized_name
        "#;

const SQL_WORKSTREAM_MEMBERSHIP_MAP_0: &str = r#"
        SELECT CAST(workstream_links.entity_id AS INTEGER) AS item_id,
               workstream_links.workstream_id
        FROM workstream_links
        JOIN atlassian_items
          ON atlassian_items.external_resource_id =
             CAST(workstream_links.entity_id AS INTEGER)
        WHERE workstream_links.entity_type = 'external'
        UNION
        SELECT CAST(thread_links.entity_id AS INTEGER),
               threads.workstream_id
        FROM thread_links
        JOIN threads ON threads.id = thread_links.thread_id
        JOIN atlassian_items
          ON atlassian_items.external_resource_id =
             CAST(thread_links.entity_id AS INTEGER)
        WHERE thread_links.entity_type = 'external'
        "#;

const SQL_ITEM_ROWS_0: &str = r#"
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.service,
               atlassian_items.item_type,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               atlassian_items.confirmed_at,
               atlassian_items.updated_at AS item_updated_at,
               external_resources.title AS local_title,
               external_resources.summary AS local_summary,
               atlassian_sites.id AS site_id,
               atlassian_sites.display_name AS site_name,
               atlassian_sites.normalized_domain,
               atlassian_spaces.id AS space_id,
               atlassian_spaces.name AS space_name,
               atlassian_spaces.space_key,
               external_source_instances.id AS source_instance_id,
               COALESCE(
                   external_source_instances.display_name, '로컬 전용'
               ) AS source_name,
               atlassian_item_urls.normalized_url AS canonical_url,
               atlassian_item_remote_state.metadata_json,
               atlassian_item_remote_state.remote_version,
               atlassian_item_remote_state.remote_updated_at,
               atlassian_item_remote_state.last_attempted_at,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.last_error_code,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale,
               external_resource_content.normalized_text,
               external_resource_content.normalization_warning,
               external_resource_content.applied_at AS content_applied_at,
               external_resource_notes.note
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
        LEFT JOIN external_resource_notes
          ON external_resource_notes.external_resource_id =
             atlassian_items.external_resource_id
        {item_filter}
        ORDER BY CASE atlassian_items.attention WHEN 'pinned' THEN 0 ELSE 1 END,
                 atlassian_items.updated_at DESC,
                 atlassian_items.external_resource_id DESC
        "#;

const SQL_ITEM_URL_MAP_0: &str = r#"
        SELECT external_resource_id, url_role, normalized_url
        FROM atlassian_item_urls
        ORDER BY external_resource_id,
                 CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END,
                 id
        "#;

const SQL_REFERENCE_URL_MAP_0: &str = r#"
            SELECT reference_id, safe_locator_url
            FROM atlassian_structure_reference_urls
            WHERE reference_id IN ({})
            ORDER BY reference_id,
                     CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END,
                     id
            "#;

const SQL_SELECTED_ZERO_SPACE_0: &str = r#"
        SELECT atlassian_spaces.id, atlassian_spaces.site_id,
               atlassian_spaces.service, atlassian_spaces.name,
               atlassian_spaces.space_key,
               atlassian_sites.display_name AS site_name,
               atlassian_sites.normalized_domain
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        WHERE atlassian_spaces.id = ?
          AND atlassian_spaces.site_id = ?
        "#;

const SQL_BROWSE_INVENTORY_0: &str = r#"
                    SELECT DISTINCT external_source_instances.id,
                           external_source_instances.display_name,
                           external_source_instances.service
                    FROM external_source_instances
                    JOIN atlassian_site_bindings
                      ON atlassian_site_bindings.source_instance_id =
                         external_source_instances.id
                    ORDER BY external_source_instances.display_name,
                             external_source_instances.id
                    "#;

const SQL_BROWSE_INVENTORY_1: &str = r#"
                    SELECT DISTINCT atlassian_sites.id,
                           NULL AS source_instance_id,
                           atlassian_sites.normalized_domain,
                           atlassian_sites.display_name,
                           scoped_sites.service
                    FROM atlassian_sites
                    JOIN (
                        SELECT site_id, service FROM atlassian_items
                        UNION
                        SELECT site_id, service FROM atlassian_spaces
                        UNION
                        SELECT reference.site_id, reference.service
                        FROM atlassian_structure_references AS reference
                        WHERE EXISTS (
                            SELECT 1
                            FROM atlassian_structure_reference_evidence AS evidence
                            WHERE evidence.reference_id = reference.id
                        )
                    ) AS scoped_sites
                      ON scoped_sites.site_id = atlassian_sites.id
                    ORDER BY atlassian_sites.normalized_domain,
                             atlassian_sites.id
                    "#;

const SQL_BROWSE_INVENTORY_2: &str = r#"
                    SELECT id, site_id, service, name, space_key
                    FROM atlassian_spaces
                    ORDER BY service, name, id
                    "#;

const SQL_BROWSE_INVENTORY_3: &str = r#"
                    SELECT id, name, status FROM workstreams
                    ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END,
                             name, id
                    "#;

const SQL_LATEST_REFRESH_RUN_0: &str = r#"
        SELECT maintenance_runs.id, maintenance_runs.status,
               maintenance_runs.runner, maintenance_runs.summary,
               maintenance_runs.error, maintenance_runs.created_at,
               maintenance_runs.started_at, maintenance_runs.completed_at,
               maintenance_runs.source_snapshot_json
        FROM maintenance_runs
        JOIN external_sync_runs
          ON external_sync_runs.maintenance_run_id = maintenance_runs.id
        WHERE maintenance_runs.task_type = 'external_source_sync'
        ORDER BY maintenance_runs.created_at DESC, maintenance_runs.id DESC
        LIMIT 200
        "#;

const SQL_PREVIEW_ITEM_ROW_0: &str = r#"
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.service,
               atlassian_items.item_type,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               atlassian_items.source_instance_id,
               external_resources.title AS local_title,
               atlassian_sites.id AS site_id,
               atlassian_sites.display_name AS site_name,
               atlassian_sites.normalized_domain,
               atlassian_spaces.id AS space_id,
               atlassian_spaces.name AS space_name,
               atlassian_spaces.space_key,
               (
                   SELECT atlassian_item_urls.normalized_url
                   FROM atlassian_item_urls
                   WHERE atlassian_item_urls.external_resource_id =
                         atlassian_items.external_resource_id
                     AND atlassian_item_urls.url_role = 'canonical'
                   ORDER BY atlassian_item_urls.id
                   LIMIT 1
               ) AS canonical_url,
               atlassian_item_remote_state.metadata_json,
               atlassian_item_remote_state.remote_version,
               atlassian_item_remote_state.remote_updated_at,
               atlassian_item_remote_state.last_attempted_at,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.last_error_code,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale
        FROM atlassian_items
        JOIN external_resources
          ON external_resources.id = atlassian_items.external_resource_id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN atlassian_spaces
          ON atlassian_spaces.id = atlassian_items.space_id
        LEFT JOIN atlassian_item_remote_state
          ON atlassian_item_remote_state.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.external_resource_id = ?
        "#;

const SQL_PREVIEW_ITEM_URLS_0: &str = r#"
            SELECT url_role, normalized_url
            FROM atlassian_item_urls
            WHERE external_resource_id = ?
            ORDER BY CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END, id
            "#;

const SQL_PREVIEW_ALL_CLASSIFICATIONS_0: &str = r#"
        SELECT atlassian_classifications.id,
               atlassian_classifications.kind,
               atlassian_classifications.name,
               atlassian_classifications.normalized_name,
               atlassian_classifications.description
        FROM atlassian_item_classifications
        JOIN atlassian_classifications
          ON atlassian_classifications.id =
             atlassian_item_classifications.classification_id
        WHERE atlassian_item_classifications.external_resource_id = ?
        ORDER BY atlassian_classifications.kind,
                 atlassian_classifications.normalized_name,
                 atlassian_classifications.id
        "#;

const SQL_PREVIEW_REQUESTED_CLASSIFICATIONS_0: &str = r#"
        SELECT atlassian_classifications.id,
               atlassian_classifications.kind
        FROM atlassian_item_classifications
        JOIN atlassian_classifications
          ON atlassian_classifications.id =
             atlassian_item_classifications.classification_id
        WHERE atlassian_item_classifications.external_resource_id = ?
          AND (
              (atlassian_classifications.kind = 'topic'
               AND ? IS NOT NULL
               AND atlassian_classifications.id = ?)
              OR
              (atlassian_classifications.kind = 'tag'
               AND ? IS NOT NULL
               AND atlassian_classifications.id = ?)
          )
        "#;

const SQL_PREVIEW_CLASSIFICATION_PROJECTION_0: &str = r#"
        WITH ranked_classifications AS (
            SELECT atlassian_classifications.id,
                   atlassian_classifications.kind,
                   atlassian_classifications.name,
                   atlassian_classifications.normalized_name,
                   COUNT(*) OVER (
                       PARTITION BY atlassian_classifications.kind
                   ) AS preview_total,
                   ROW_NUMBER() OVER (
                       PARTITION BY atlassian_classifications.kind
                       ORDER BY atlassian_classifications.normalized_name,
                                atlassian_classifications.id
                   ) AS preview_rank
            FROM atlassian_item_classifications
            JOIN atlassian_classifications
              ON atlassian_classifications.id =
                 atlassian_item_classifications.classification_id
            WHERE atlassian_item_classifications.external_resource_id = ?
        )
        SELECT id, kind, name, normalized_name, preview_total
        FROM ranked_classifications
        WHERE preview_rank <= ?
        ORDER BY kind, normalized_name, id
        "#;

const SQL_PREVIEW_TEXT_VALUES_0: &str = r#"
        SELECT SUBSTR(
                   external_resource_content.normalized_text, 1, ?
               ) AS normalized_text,
               SUBSTR(
                   external_resource_notes.note, 1, ?
               ) AS note
        FROM atlassian_items
        LEFT JOIN external_resource_content
          ON external_resource_content.external_resource_id =
             atlassian_items.external_resource_id
        LEFT JOIN external_resource_notes
          ON external_resource_notes.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.external_resource_id = ?
        "#;

const SQL_PREVIEW_TEXT_MATCHES_0: &str = r#"
            SELECT CASE
                     WHEN ? = 1
                      AND atlassian_items.coverage = 'indexed'
                     THEN localbrain_atlassian_exact_phrase(
                              external_resource_content.normalized_text
                          )
                     ELSE 0
                   END AS content_matches,
                   localbrain_atlassian_exact_phrase(
                       external_resource_notes.note
                   ) AS note_matches
            FROM atlassian_items
            LEFT JOIN external_resource_content
              ON external_resource_content.external_resource_id =
                 atlassian_items.external_resource_id
            LEFT JOIN external_resource_notes
              ON external_resource_notes.external_resource_id =
                 atlassian_items.external_resource_id
            WHERE atlassian_items.external_resource_id = ?
            "#;

const SQL_PREVIEW_HAS_WORKSTREAM_0: &str = r#"
            SELECT 1
            FROM workstream_links
            WHERE workstream_links.entity_type = 'external'
              AND workstream_links.entity_id = ?
              AND workstream_links.workstream_id = ?
            UNION ALL
            SELECT 1
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            WHERE thread_links.entity_type = 'external'
              AND thread_links.entity_id = ?
              AND threads.workstream_id = ?
            LIMIT 1
            "#;

const SQL_PREVIEW_EVIDENCE_0: &str = r#"
        WITH ranked_evidence AS (
            SELECT atlassian_item_evidence.id,
                   atlassian_item_evidence.session_id,
                   atlassian_item_evidence.document_id,
                   atlassian_item_evidence.source_channel,
                   atlassian_item_evidence.source_line,
                   atlassian_item_evidence.observed_url,
                   atlassian_item_evidence.observed_at,
                   atlassian_item_evidence.last_observed_at,
                   sessions.title AS session_title,
                   context_documents.title AS document_title,
                   context_documents.relative_path AS document_path,
                   COALESCE(
                       atlassian_item_evidence.observed_at,
                       atlassian_item_evidence.last_observed_at
                   ) AS observed_order,
                   COUNT(*) OVER () AS preview_total,
                   ROW_NUMBER() OVER (
                       ORDER BY COALESCE(
                                    atlassian_item_evidence.observed_at,
                                    atlassian_item_evidence.last_observed_at
                                ) DESC,
                                atlassian_item_evidence.id DESC
                   ) AS preview_rank
            FROM atlassian_item_evidence
            LEFT JOIN sessions
              ON sessions.id = atlassian_item_evidence.session_id
            LEFT JOIN context_documents
              ON context_documents.id =
                 atlassian_item_evidence.document_id
            WHERE atlassian_item_evidence.external_resource_id = ?
        )
        SELECT id, session_id, document_id, source_channel, source_line,
               observed_url, observed_at, last_observed_at,
               session_title, document_title, document_path,
               observed_order, preview_total
        FROM ranked_evidence
        WHERE preview_rank <= ?
        ORDER BY observed_order DESC, id DESC
        "#;

const SQL_PREVIEW_ORGANIZATION_0: &str = r#"
        WITH item_organization AS (
            SELECT workstream_links.id AS link_id,
                   'workstream' AS scope_type,
                   workstreams.id AS scope_id,
                   workstreams.id AS workstream_id,
                   workstreams.name AS workstream_name,
                   NULL AS thread_id,
                   NULL AS thread_title,
                   workstream_links.relation_type
            FROM workstream_links
            JOIN workstreams
              ON workstreams.id = workstream_links.workstream_id
            WHERE workstream_links.entity_type = 'external'
              AND workstream_links.entity_id = ?
            UNION ALL
            SELECT thread_links.id,
                   'thread',
                   threads.id,
                   workstreams.id,
                   workstreams.name,
                   threads.id,
                   threads.title,
                   thread_links.relation_type
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            JOIN workstreams
              ON workstreams.id = threads.workstream_id
            WHERE thread_links.entity_type = 'external'
              AND thread_links.entity_id = ?
        )
        SELECT item_organization.*, COUNT(*) OVER () AS preview_total
        FROM item_organization
        ORDER BY workstream_name, thread_title
        LIMIT ?
        "#;

const SQL_ATLASSIAN_ITEM_DETAIL_0: &str = r#"
            SELECT workstream_links.id AS link_id,
                   'workstream' AS scope_type,
                   workstreams.id AS scope_id,
                   workstreams.id AS workstream_id,
                   workstreams.name AS workstream_name,
                   NULL AS thread_id,
                   NULL AS thread_title,
                   workstream_links.relation_type
            FROM workstream_links
            JOIN workstreams
              ON workstreams.id = workstream_links.workstream_id
            WHERE workstream_links.entity_type = 'external'
              AND workstream_links.entity_id = ?
            UNION ALL
            SELECT thread_links.id,
                   'thread',
                   threads.id,
                   workstreams.id,
                   workstreams.name,
                   threads.id,
                   threads.title,
                   thread_links.relation_type
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            JOIN workstreams
              ON workstreams.id = threads.workstream_id
            WHERE thread_links.entity_type = 'external'
              AND thread_links.entity_id = ?
            ORDER BY workstream_name, thread_title
            "#;

const SQL_ATLASSIAN_ITEM_DETAIL_1: &str = r#"
            SELECT atlassian_item_evidence.id,
                   atlassian_item_evidence.session_id,
                   atlassian_item_evidence.document_id,
                   atlassian_item_evidence.source_channel,
                   atlassian_item_evidence.source_line,
                   atlassian_item_evidence.observed_url,
                   atlassian_item_evidence.observed_at,
                   sessions.title AS session_title,
                   context_documents.title AS document_title,
                   context_documents.relative_path AS document_path
            FROM atlassian_item_evidence
            LEFT JOIN sessions
              ON sessions.id = atlassian_item_evidence.session_id
            LEFT JOIN context_documents
              ON context_documents.id =
                 atlassian_item_evidence.document_id
            WHERE atlassian_item_evidence.external_resource_id = ?
            ORDER BY COALESCE(
                         atlassian_item_evidence.observed_at,
                         atlassian_item_evidence.last_observed_at
                     ) DESC,
                     atlassian_item_evidence.id DESC
            "#;

const SQL_ATLASSIAN_ITEM_DETAIL_2: &str = r#"
        SELECT id, name, status FROM workstreams
        ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, name, id
        "#;

const SQL_ATLASSIAN_ITEM_DETAIL_3: &str = r#"
                SELECT id, title, status FROM threads
                WHERE workstream_id = ?
                ORDER BY position, title, id
                "#;

const SQL_UPSERT_CLASSIFICATION_0: &str = r#"
        INSERT INTO atlassian_classifications(
            kind, name, normalized_name, description, updated_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(kind, normalized_name) DO UPDATE SET
            name = excluded.name,
            description = CASE
                WHEN excluded.kind = 'topic'
                THEN excluded.description
                ELSE NULL
            END,
            updated_at = excluded.updated_at
        "#;

const SQL_UPSERT_CLASSIFICATION_1: &str = r#"
            SELECT id FROM atlassian_classifications
            WHERE kind = ? AND normalized_name = ?
            "#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_0: &str = r#"
        SELECT 1 FROM atlassian_items WHERE external_resource_id = ?
        "#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_1: &str = r#"
                SELECT id FROM atlassian_classifications
                WHERE kind = 'topic' AND id IN ({})
                "#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_2: &str = r#"SAVEPOINT atlassian_local_state"#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_3: &str = r#"
                INSERT INTO external_resource_notes(
                    external_resource_id, note, updated_at
                ) VALUES (?, ?, ?)
                ON CONFLICT(external_resource_id) DO UPDATE SET
                    note = excluded.note,
                    updated_at = excluded.updated_at
                "#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_4: &str = r#"
                DELETE FROM external_resource_notes
                WHERE external_resource_id = ?
                "#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_5: &str = r#"
                DELETE FROM atlassian_item_classifications
                WHERE external_resource_id = ?
                  AND classification_id IN (
                      SELECT id FROM atlassian_classifications
                      WHERE kind = ?
                  )
                "#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_6: &str = r#"
            INSERT INTO atlassian_item_classifications(
                external_resource_id, classification_id
            ) VALUES (?, ?)
            "#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_7: &str = r#"ROLLBACK TO atlassian_local_state"#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_8: &str = r#"RELEASE atlassian_local_state"#;

const SQL_UPDATE_ATLASSIAN_LOCAL_STATE_9: &str = r#"RELEASE atlassian_local_state"#;

const SQL_ATLASSIAN_SEARCH_RESULTS_0: &str = r#"
        SELECT entity_type, entity_id, source_kind, title, path,
               snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
               highlight(search_index, 3, '[[', ']]') AS matched_title,
               bm25(search_index) AS score
        FROM search_index
        WHERE search_index MATCH ?
          AND entity_type IN (
              'atlassian_item', 'atlassian_structure_reference'
          )
        ORDER BY score
        LIMIT 400
        "#;
use super::{
    catalog,
    common::{fail, python_string, trim, truth},
    evidence::{
        atlassian_url_container_hint, normalize_atlassian_structural_scope,
        structural_scope_service,
    },
    structure_references,
};
use crate::backend::{db, unicode, Result};
use rusqlite::{
    functions::FunctionFlags, params, params_from_iter, types::Value as SqlValue, Connection,
};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use unicode_normalization::UnicodeNormalization;
pub const CLASSIFICATION_KINDS: &[&str] = &["topic", "tag"];
pub const COVERAGE_VALUES: &[&str] = &["reference", "metadata", "indexed"];
pub const FRESHNESS_VALUES: &[&str] = &["unknown", "current", "due", "stale", "unavailable"];
pub const SERVICE_VALUES: &[&str] = &["jira", "confluence"];
pub const ITEM_TYPE_VALUES: &[&str] = &["jira_issue", "confluence_page"];
const ADVANCED_FILTER_FIELDS: &[&str] = &[
    "coverage",
    "freshness",
    "attention",
    "topic_id",
    "tag_id",
    "workstream_id",
];
const REFERENCE_EXCLUDING_FILTER_FIELDS: &[&str] = &[
    "source_instance_id",
    "space_id",
    "item_type",
    "coverage",
    "freshness",
    "attention",
    "topic_id",
    "tag_id",
    "workstream_id",
];
fn s<'a>(value: &'a Value, key: &str) -> &'a str {
    value[key].as_str().unwrap_or("")
}
fn id(value: &Value) -> i64 {
    value["id"].as_i64().unwrap_or(0)
}
fn arr(value: &Value) -> &[Value] {
    value.as_array().map(Vec::as_slice).unwrap_or(&[])
}
fn obj(values: &Value, keys: &[&str]) -> Value {
    let mut out = serde_json::Map::new();
    for key in keys {
        out.insert(
            (*key).into(),
            values.get(key).cloned().unwrap_or(Value::Null),
        );
    }
    Value::Object(out)
}
fn merge(target: &mut Value, value: Value) {
    if let Some(values) = value.as_object() {
        for (k, v) in values {
            target[k] = v.clone();
        }
    }
}
fn sql_value(value: &Value) -> SqlValue {
    match value {
        Value::Null => SqlValue::Null,
        Value::String(s) => SqlValue::Text(s.clone()),
        Value::Bool(v) => SqlValue::Integer(i64::from(*v)),
        Value::Number(v) => {
            if let Some(n) = v.as_i64() {
                SqlValue::Integer(n)
            } else if let Some(n) = v.as_f64() {
                SqlValue::Real(n)
            } else {
                SqlValue::Text(v.to_string())
            }
        }
        _ => SqlValue::Text(value.to_string()),
    }
}
fn query(db: &Connection, sql: &str, args: &[&Value]) -> Result<Vec<Value>> {
    db::rows(db, sql, params_from_iter(args.iter().map(|v| sql_value(v))))
}
fn one(db: &Connection, sql: &str, args: &[&Value]) -> Result<Option<Value>> {
    db::row(db, sql, params_from_iter(args.iter().map(|v| sql_value(v))))
}
fn clean(value: &Value) -> String {
    if truth(value) {
        python_string(value)
    } else {
        String::new()
    }
}
fn integer_value(value: &Value) -> Option<i128> {
    match value {
        Value::Bool(v) => Some(i128::from(*v)),
        Value::Number(n) => n
            .as_i64()
            .map(i128::from)
            .or_else(|| n.as_u64().map(i128::from))
            .or_else(|| {
                n.as_f64()
                    .filter(|n| n.is_finite())
                    .map(|v| v.trunc() as i128)
            }),
        Value::String(s) => {
            let mut out = String::new();
            let chars = trim(s).chars().collect::<Vec<_>>();
            for (i, c) in chars.iter().enumerate() {
                if i == 0 && matches!(c, '+' | '-') {
                    out.push(*c)
                } else if *c == '_'
                    && i > 0
                    && i + 1 < chars.len()
                    && decimal(chars[i - 1]).is_some()
                    && decimal(chars[i + 1]).is_some()
                {
                } else if let Some(n) = decimal(*c) {
                    out.push(char::from(b'0' + n))
                } else {
                    return None;
                }
            }
            if out.bytes().filter(u8::is_ascii_digit).count() > 4300 {
                return None;
            }
            match out.parse::<i128>() {
                Ok(v) => Some(v),
                Err(e) => match e.kind() {
                    std::num::IntErrorKind::PosOverflow => Some(i128::MAX),
                    std::num::IntErrorKind::NegOverflow => Some(i128::MIN),
                    _ => None,
                },
            }
        }
        _ => None,
    }
}
fn decimal(c: char) -> Option<u8> {
    if unicode_general_category::get_general_category(c)
        != unicode_general_category::GeneralCategory::DecimalNumber
    {
        return None;
    }
    let point = c as u32;
    let mut start = point;
    while start > 0
        && char::from_u32(start - 1).is_some_and(|c| {
            unicode_general_category::get_general_category(c)
                == unicode_general_category::GeneralCategory::DecimalNumber
        })
    {
        start -= 1
    }
    Some(((point - start) % 10) as u8)
}
fn integer(value: &Value, label: &str) -> Result<Value> {
    if value.is_null() || value == "" {
        return Ok(Value::Null);
    }
    if value.is_boolean() {
        return Err(fail(
            "invalid-filter",
            format!("{label} must be an integer"),
        ));
    }
    let n = integer_value(value)
        .ok_or_else(|| fail("invalid-filter", format!("{label} must be an integer")))?;
    if !(1..=i64::MAX as i128).contains(&n) {
        return Err(fail(
            "invalid-filter",
            format!("{label} is outside the supported range"),
        ));
    }
    Ok(json!(n as i64))
}
fn choice(value: &Value, allowed: &[&str], label: &str) -> Result<Value> {
    if value.is_null() || value == "" {
        return Ok(Value::Null);
    }
    let normalized = python_string(value);
    let normalized = trim(&normalized);
    if !allowed.contains(&normalized) {
        return Err(fail(
            "invalid-filter",
            format!("Unsupported {label} filter"),
        ));
    }
    Ok(json!(normalized))
}
pub fn normalize_browse_filters(values: &Value) -> Result<Value> {
    let query = clean(&values["q"]);
    let query = trim(&query);
    if query.chars().count() > 300 {
        return Err(fail("invalid-query", "Query exceeds 300 characters"));
    }
    let mut attention = catalog::ATTENTION_VALUES.to_vec();
    attention.push("all");
    let scope = normalize_atlassian_structural_scope(&values["structural_scope"]);
    if !values["structural_scope"].is_null() && values["structural_scope"] != "" && scope.is_none()
    {
        return Err(fail(
            "invalid-filter",
            "Unsupported structural_scope filter",
        ));
    }
    let mut filters = json!({"q":query,"service":choice(&values["service"],SERVICE_VALUES,"service")?,"structural_scope":scope,"item_type":choice(&values["item_type"],ITEM_TYPE_VALUES,"item_type")?,"coverage":choice(&values["coverage"],COVERAGE_VALUES,"coverage")?,"freshness":choice(&values["freshness"],FRESHNESS_VALUES,"freshness")?,"attention":choice(&values["attention"],&attention,"attention")?});
    for field in [
        "source_instance_id",
        "site_id",
        "space_id",
        "topic_id",
        "tag_id",
        "workstream_id",
    ] {
        filters[field] = integer(&values[field], field)?;
    }
    if !filters["space_id"].is_null() && truth(&filters["structural_scope"]) {
        return Err(fail(
            "invalid-filter",
            "space_id and structural_scope cannot be combined",
        ));
    }
    if truth(&filters["structural_scope"]) && filters["site_id"].is_null() {
        return Err(fail("invalid-filter", "structural_scope requires site_id"));
    }
    Ok(filters)
}
pub fn normalize_browse_structure(db: &Connection, filters: &Value) -> Result<Value> {
    let mut out = filters.clone();
    if !out["space_id"].is_null() {
        if let Some(owner) = one(db, SQL_NORMALIZE_BROWSE_STRUCTURE_0, &[&out["space_id"]])? {
            if !out["service"].is_null() && owner["service"] != out["service"] {
                return Err(fail(
                    "invalid-filter",
                    "Space is unavailable for the selected service",
                ));
            }
            out["site_id"] = owner["site_id"].clone();
        }
    }
    let scope_service = structural_scope_service(out["structural_scope"].as_str());
    if out["service"]
        .as_str()
        .zip(scope_service)
        .is_some_and(|(s, t)| s != t)
    {
        return Err(fail(
            "invalid-filter",
            "URL container is unavailable for the selected service",
        ));
    }
    if !out["site_id"].is_null() && !out["service"].is_null() {
        let mut services = query(db, SQL_NORMALIZE_BROWSE_STRUCTURE_1, &[&out["site_id"]])?;
        if out["space_id"].is_null() {
            services.extend(query(
                db,
                SQL_NORMALIZE_BROWSE_STRUCTURE_2,
                &[&out["site_id"]],
            )?);
            services.extend(query(
                db,
                SQL_NORMALIZE_BROWSE_STRUCTURE_3,
                &[&out["site_id"]],
            )?);
        }
        if !services.is_empty() && !services.iter().any(|v| v["service"] == out["service"]) {
            return Err(fail(
                "invalid-filter",
                "Site is unavailable for the selected service",
            ));
        }
    }
    Ok(out)
}
pub fn validate_browse_structural_scope(db: &Connection, filters: &Value) -> Result<()> {
    if filters["structural_scope"].is_null() {
        return Ok(());
    }
    db.create_scalar_function(
        "localbrain_atlassian_container_scope",
        1,
        FunctionFlags::SQLITE_UTF8 | FunctionFlags::SQLITE_DETERMINISTIC,
        |ctx| {
            let value = ctx.get::<Option<String>>(0)?;
            Ok(atlassian_url_container_hint(value.as_deref())
                .and_then(|v| v["structural_scope"].as_str().map(str::to_owned))
                .unwrap_or("unclassified".into()))
        },
    )?;
    let args = [
        &filters["site_id"],
        &filters["service"],
        &filters["service"],
        &filters["structural_scope"],
    ];
    if one(db, SQL_VALIDATE_BROWSE_STRUCTURAL_SCOPE_0, &args)?.is_none()
        && one(db, SQL_VALIDATE_BROWSE_STRUCTURAL_SCOPE_1, &args)?.is_none()
    {
        return Err(fail(
            "invalid-filter",
            "Structural scope is unavailable for the selected Site",
        ));
    }
    Ok(())
}
fn exact_tokens(value: &Value) -> Vec<String> {
    clean(value)
        .split(|c: char| c != '_' && !unicode::python_alnum(c))
        .filter(|s| !s.is_empty())
        .map(|s| unicode::casefold(&s.nfkc().collect::<String>()))
        .collect()
}
fn exact_query_tokens(query: &str) -> Result<Vec<String>> {
    let tokens = exact_tokens(&json!(query));
    if !query.is_empty() && tokens.is_empty() {
        return Err(fail("invalid-query", "Query has no searchable words"));
    }
    if tokens.len() > 12 {
        return Err(fail("invalid-query", "Query supports at most 12 words"));
    }
    Ok(tokens)
}
fn exact_phrase(value: &Value, tokens: &[String]) -> bool {
    let values = exact_tokens(value);
    !tokens.is_empty() && values.windows(tokens.len()).any(|v| v == tokens)
}
fn prefix(value: &str, limit: usize) -> String {
    value.chars().take(limit).collect()
}
fn bounded_exact_excerpt(value: &Value, tokens: &[String]) -> String {
    let text = clean(value)
        .split(unicode::python_space)
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    let chars = text.chars().collect::<Vec<_>>();
    if chars.len() <= 240 {
        return text;
    }
    let folded = unicode::casefold(&text);
    let index = tokens.first().and_then(|token| {
        folded
            .find(token)
            .map(|byte| folded[..byte].chars().count())
    });
    let mut start = index.unwrap_or(0).saturating_sub(72);
    let end = chars.len().min(start.saturating_add(240));
    if end - start < 240 {
        start = end.saturating_sub(240)
    }
    let text = chars[start..end].iter().collect::<String>();
    let mut excerpt = format!(
        "{}{}{}",
        if start > 0 { "... " } else { "" },
        trim(&text),
        if end < chars.len() { " ..." } else { "" }
    );
    if excerpt.chars().count() > 240 {
        excerpt = format!(
            "{} ...",
            prefix(&excerpt, 236).trim_end_matches(unicode::python_space)
        );
    }
    excerpt
}
fn flatten(value: &Value) -> Vec<String> {
    let mut output = Vec::new();
    let mut pending = vec![value];
    while let Some(value) = pending.pop() {
        match value {
            Value::Object(values) => {
                let mut keys = values.keys().collect::<Vec<_>>();
                keys.sort();
                pending.extend(keys.into_iter().rev().map(|k| &values[k]));
            }
            Value::Array(values) => pending.extend(values.iter().rev()),
            Value::Null => {}
            _ => {
                let value = python_string(value);
                let value = trim(&value);
                if !value.is_empty() {
                    output.push(value.into());
                }
            }
        }
    }
    output
}
type Memberships = BTreeMap<i64, Value>;
type Workstreams = BTreeMap<i64, BTreeSet<i64>>;
fn classification_maps(db: &Connection) -> Result<(Value, Memberships)> {
    let classes = db::rows(db, SQL_CLASSIFICATION_MAPS_0, [])?;
    let mut memberships = Memberships::new();
    for row in db::rows(db, SQL_CLASSIFICATION_MAPS_1, [])? {
        let entry = memberships
            .entry(row["external_resource_id"].as_i64().unwrap())
            .or_insert(json!({"topics":[],"tags":[]}));
        let field = if row["kind"] == "topic" {
            "topics"
        } else {
            "tags"
        };
        entry[field].as_array_mut().unwrap().push(obj(
            &row,
            &["id", "kind", "name", "normalized_name", "description"],
        ));
    }
    Ok((
        json!({"topics":classes.iter().filter(|v|v["kind"]=="topic").collect::<Vec<_>>(),"tags":classes.iter().filter(|v|v["kind"]=="tag").collect::<Vec<_>>()}),
        memberships,
    ))
}
fn workstream_memberships(db: &Connection) -> Result<Workstreams> {
    let mut map = Workstreams::new();
    for row in db::rows(db, SQL_WORKSTREAM_MEMBERSHIP_MAP_0, [])? {
        map.entry(row["item_id"].as_i64().unwrap())
            .or_default()
            .insert(row["workstream_id"].as_i64().unwrap());
    }
    Ok(map)
}
fn service_label(service: &str) -> &'static str {
    if service == "jira" {
        "Jira"
    } else {
        "Wiki"
    }
}
pub fn project_atlassian_item_container(value: &Value) -> Result<Value> {
    let mut item = value.clone();
    let service = s(&item, "service").to_owned();
    let fields = if !item["space_id"].is_null() {
        json!({"container_kind":"space","container_label":if truth(&item["space_name"]){item["space_name"].clone()}else{json!("이름 없음")},"container_service":service,"container_cue":service_label(&service),"container_structural_scope":null})
    } else if let Some(hint) = atlassian_url_container_hint(item["canonical_url"].as_str()) {
        json!({"container_kind":"url","container_label":hint["label"],"container_service":hint["service"],"container_cue":format!("{} · URL 기준",service_label(s(&hint,"service"))),"container_structural_scope":hint["structural_scope"]})
    } else {
        json!({"container_kind":"unclassified","container_label":"소속 미확인","container_service":null,"container_cue":null,"container_structural_scope":"unclassified"})
    };
    merge(&mut item, fields);
    Ok(item)
}
fn prepare_item(mut item: Value, preview: bool) -> Result<Value> {
    let raw = item
        .as_object_mut()
        .unwrap()
        .remove("metadata_json")
        .unwrap_or(Value::Null);
    let mut metadata =
        crate::backend::json::decode(raw.as_str().filter(|s| !s.is_empty()).unwrap_or("{}"))
            .unwrap_or(json!({}));
    if preview && !metadata.is_object() {
        metadata = json!({});
    }
    item["freshness"] = json!(catalog::derive_atlassian_freshness(
        s(&item, "service"),
        Some(&item),
        None
    )?);
    item["display_title"] = if truth(&metadata["title"]) {
        metadata["title"].clone()
    } else if truth(&metadata["summary"]) {
        metadata["summary"].clone()
    } else {
        item["local_title"].clone()
    };
    item["metadata"] = metadata;
    if !preview {
        item["entity_kind"] = json!("item");
        item["entity_id"] = item["id"].clone();
        item["stable_key"] = json!(format!("item:{}", item["id"]));
        item["updated_at"] = item["item_updated_at"].clone();
    }
    project_atlassian_item_container(&item)
}
fn item_rows(db: &Connection, resource: Option<i64>) -> Result<Vec<Value>> {
    let sql = SQL_ITEM_ROWS_0.replace(
        "{item_filter}",
        if resource.is_some() {
            "WHERE atlassian_items.external_resource_id = ?"
        } else {
            ""
        },
    );
    let args = resource
        .into_iter()
        .map(SqlValue::Integer)
        .collect::<Vec<_>>();
    db::rows(db, &sql, params_from_iter(args))?
        .into_iter()
        .map(|item| prepare_item(item, false))
        .collect()
}
fn normalized_query_url(query: &str) -> Result<Option<String>> {
    if !query.to_ascii_lowercase().starts_with("http://")
        && !query.to_ascii_lowercase().starts_with("https://")
    {
        return Ok(None);
    }
    catalog::normalize_atlassian_url(query)
        .map(|v| Some(v.normalized_url))
        .map_err(|_| fail("invalid-query", "HTTP(S) query URL is invalid"))
}
fn title_values(item: &Value) -> Vec<Value> {
    let mut values = Vec::new();
    for value in [
        &item["local_title"],
        &item["metadata"]["title"],
        &item["metadata"]["summary"],
    ] {
        if !value.is_null() {
            let value = json!(python_string(value));
            if !values.contains(&value) {
                values.push(value)
            }
        }
    }
    values
}
fn other_values(item: &Value, memberships: &Value) -> Vec<(&'static str, Value)> {
    let mut metadata = item["metadata"].clone();
    if let Some(m) = metadata.as_object_mut() {
        m.remove("title");
        m.remove("summary");
    } else {
        metadata = json!({});
    }
    let mut values = flatten(&metadata)
        .into_iter()
        .map(|v| ("metadata", json!(v)))
        .collect::<Vec<_>>();
    if item["coverage"] == "indexed"
        && item["freshness"] != "unavailable"
        && truth(&item["normalized_text"])
    {
        values.push(("content", json!(python_string(&item["normalized_text"]))));
    }
    if truth(&item["note"]) {
        values.push(("local", json!(python_string(&item["note"]))));
    }
    for topic in arr(&memberships["topics"]) {
        for key in ["name", "description"] {
            if truth(&topic[key]) {
                values.push(("local", json!(python_string(&topic[key]))));
            }
        }
    }
    for tag in arr(&memberships["tags"]) {
        if truth(&tag["name"]) {
            values.push(("local", json!(python_string(&tag["name"]))));
        }
    }
    values
}
fn identity_value(
    item: &Value,
    urls: &[Value],
    query: &str,
    normalized: Option<&str>,
) -> Option<Value> {
    let folded = unicode::casefold(query);
    for key in ["remote_key", "remote_id"] {
        if !item[key].is_null() && unicode::casefold(&python_string(&item[key])) == folded {
            return Some(json!(python_string(&item[key])));
        }
    }
    normalized.and_then(|normalized| {
        urls.iter()
            .find(|url| url["normalized_url"] == normalized)
            .map(|url| url["normalized_url"].clone())
    })
}
fn exact_item_matches(
    db: &Connection,
    items: &[Value],
    memberships: &Memberships,
    query: &str,
) -> Result<Option<BTreeMap<i64, Value>>> {
    let query = trim(query);
    if query.is_empty() {
        return Ok(None);
    }
    let tokens = exact_query_tokens(query)?;
    let normalized = normalized_query_url(query)?;
    let mut urls: BTreeMap<i64, Vec<Value>> = BTreeMap::new();
    for url in db::rows(db, SQL_ITEM_URL_MAP_0, [])? {
        urls.entry(url["external_resource_id"].as_i64().unwrap())
            .or_default()
            .push(url);
    }
    let mut matches = BTreeMap::new();
    for item in items {
        let item_id = id(item);
        let identity = identity_value(
            item,
            urls.get(&item_id).map(Vec::as_slice).unwrap_or(&[]),
            query,
            normalized.as_deref(),
        );
        let title = title_values(item)
            .into_iter()
            .find(|v| exact_phrase(v, &tokens));
        let matching = identity
            .map(|v| (0, "identity", v))
            .or_else(|| title.map(|v| (1, "title", v)))
            .or_else(|| {
                other_values(item, memberships.get(&item_id).unwrap_or(&Value::Null))
                    .into_iter()
                    .find(|(_, v)| exact_phrase(v, &tokens))
                    .map(|(role, v)| (2, role, v))
            });
        if let Some((rank, role, value)) = matching {
            matches.insert(
                item_id,
                json!({"rank":rank,"role":role,"excerpt":bounded_exact_excerpt(&value,&tokens)}),
            );
        }
    }
    Ok(Some(matches))
}
fn reference_url_map(db: &Connection, references: &[Value]) -> Result<BTreeMap<i64, Vec<String>>> {
    let ids = references
        .iter()
        .map(id)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    let mut out: BTreeMap<i64, Vec<String>> = BTreeMap::new();
    for batch in ids.chunks(400) {
        let sql = SQL_REFERENCE_URL_MAP_0.replace("{}", &vec!["?"; batch.len()].join(","));
        for row in db::rows(db, &sql, params_from_iter(batch))? {
            out.entry(row["reference_id"].as_i64().unwrap())
                .or_default()
                .push(s(&row, "safe_locator_url").into());
        }
    }
    Ok(out)
}
fn exact_reference_matches(
    db: &Connection,
    references: &[Value],
    query: &str,
) -> Result<Option<BTreeMap<i64, Value>>> {
    let query = trim(query);
    if query.is_empty() {
        return Ok(None);
    }
    let tokens = exact_query_tokens(query)?;
    let urls = reference_url_map(db, references)?;
    let normalized = if query.to_ascii_lowercase().starts_with("http://")
        || query.to_ascii_lowercase().starts_with("https://")
    {
        let locator = crate::backend::references::describe_atlassian_url(query);
        if locator.kind == "unsafe" {
            return Err(fail("invalid-query", "HTTP(S) query URL is invalid"));
        }
        locator.safe_locator_url
    } else {
        None
    };
    let folded = unicode::casefold(&query.nfkc().collect::<String>());
    let mut matches = BTreeMap::new();
    for reference in references {
        let identity = s(reference, "reference_identity");
        let exact = if unicode::casefold(&identity.nfkc().collect::<String>()) == folded {
            Some(("identity", identity.to_owned()))
        } else {
            normalized.as_ref().and_then(|n| {
                urls.get(&id(reference))
                    .and_then(|u| u.iter().find(|u| *u == n))
                    .map(|u| ("url", u.clone()))
            })
        };
        let generated = format!("{} {}", s(reference, "family_label"), identity);
        let exact = exact.map(|(role, v)| (0, role, v)).or_else(|| {
            exact_phrase(&json!(generated), &tokens).then_some((1, "title", generated))
        });
        if let Some((rank, role, value)) = exact {
            matches.insert(id(reference),json!({"rank":rank,"role":role,"excerpt":bounded_exact_excerpt(&json!(value),&tokens)}));
        }
    }
    Ok(Some(matches))
}
fn filter_reference(
    reference: &Value,
    filters: &Value,
    matches: Option<&BTreeMap<i64, Value>>,
) -> bool {
    if reference["lifecycle"] == "archived"
        || matches.is_some_and(|m| !m.contains_key(&id(reference)))
    {
        return false;
    }
    if REFERENCE_EXCLUDING_FILTER_FIELDS
        .iter()
        .any(|field| !filters[field].is_null() && filters[field] != "")
    {
        return false;
    }
    for field in ["service", "site_id"] {
        if !filters[field].is_null() && reference[field] != filters[field] {
            return false;
        }
    }
    filters["structural_scope"].is_null()
        || reference["container_structural_scope"] == filters["structural_scope"]
}
fn filter_item(
    item: &Value,
    filters: &Value,
    matches: Option<&BTreeMap<i64, Value>>,
    memberships: &Memberships,
    workstreams: &Workstreams,
) -> bool {
    let key = id(item);
    if matches.is_some_and(|m| !m.contains_key(&key)) {
        return false;
    }
    for field in [
        "service",
        "source_instance_id",
        "site_id",
        "space_id",
        "item_type",
        "coverage",
        "freshness",
    ] {
        if !filters[field].is_null() && item[field] != filters[field] {
            return false;
        }
    }
    if !filters["structural_scope"].is_null()
        && item["container_structural_scope"] != filters["structural_scope"]
    {
        return false;
    }
    let attention = &filters["attention"];
    if attention.is_null() && item["attention"] == "archived" {
        return false;
    }
    if !attention.is_null() && attention != "all" && item["attention"] != *attention {
        return false;
    }
    for (field, list) in [("topic_id", "topics"), ("tag_id", "tags")] {
        if !filters[field].is_null()
            && !memberships
                .get(&key)
                .is_some_and(|v| arr(&v[list]).iter().any(|v| v["id"] == filters[field]))
        {
            return false;
        }
    }
    filters["workstream_id"].as_i64().is_none_or(|wid| {
        workstreams
            .get(&key)
            .is_some_and(|values| values.contains(&wid))
    })
}
fn selected_zero_space(
    db: &Connection,
    filters: &Value,
    eligible: &[Value],
) -> Result<Option<Value>> {
    if filters["site_id"].is_null() || filters["space_id"].is_null() {
        return Ok(None);
    }
    if eligible.iter().any(|v| {
        (filters["service"].is_null() || v["service"] == filters["service"])
            && v["site_id"] == filters["site_id"]
            && v["space_id"] == filters["space_id"]
    }) {
        return Ok(None);
    }
    Ok(one(
        db,
        SQL_SELECTED_ZERO_SPACE_0,
        &[&filters["space_id"], &filters["site_id"]],
    )?
    .filter(|v| filters["service"].is_null() || v["service"] == filters["service"]))
}
fn selected_zero_structure(
    filters: &Value,
    eligible: &[Value],
    all: &[Value],
) -> Result<Option<Value>> {
    if filters["structural_scope"].is_null() || filters["site_id"].is_null() {
        return Ok(None);
    }
    let matches = |v: &&Value| {
        v["site_id"] == filters["site_id"]
            && (filters["service"].is_null() || v["service"] == filters["service"])
            && v["container_structural_scope"] == filters["structural_scope"]
    };
    if eligible.iter().any(|v| matches(&v)) {
        return Ok(None);
    }
    all.iter().find(matches).cloned().map(Some).ok_or_else(|| {
        fail(
            "invalid-filter",
            "Structural scope is unavailable for the selected Site",
        )
    })
}
fn container(item: &Value) -> Value {
    let space = item["container_kind"] == "space";
    json!({"kind":item["container_kind"],"id":if space{item["space_id"].clone()}else{Value::Null},"structural_scope":if space{Value::Null}else{item["container_structural_scope"].clone()},"name":item["container_label"],"count":0,"item_count":0,"reference_count":0,"service":item["container_service"],"cue":item["container_cue"]})
}
fn hierarchy(
    items: &[Value],
    empty_space: Option<&Value>,
    empty_structure: Option<&Value>,
) -> Value {
    type SiteGroup = (Value, BTreeMap<(String, String), Value>);
    let mut sites: BTreeMap<i64, SiteGroup> = BTreeMap::new();
    let all = items
        .iter()
        .map(|item| (item, false, false))
        .chain(empty_space.map(|item| (item, true, true)))
        .chain(empty_structure.map(|item| (item, true, false)));
    for (item, is_empty, is_empty_space) in all {
        let site_id = item["site_id"].as_i64().unwrap();
        let(owner,containers)=sites.entry(site_id).or_insert_with(||(json!({"id":site_id,"name":item["normalized_domain"],"display_name":item["site_name"],"normalized_domain":item["normalized_domain"],"count":0,"item_count":0,"reference_count":0}),BTreeMap::new()));
        let c = if is_empty_space {
            json!({"kind":"space","id":item["id"],"structural_scope":null,"name":if truth(&item["name"]){item["name"].clone()}else{json!("이름 없음")},"count":0,"item_count":0,"reference_count":0,"service":item["service"],"cue":service_label(s(item,"service"))})
        } else {
            container(item)
        };
        let key = (
            s(&c, "kind").to_owned(),
            if c["kind"] == "space" {
                c["id"].to_string()
            } else {
                s(&c, "structural_scope").to_owned()
            },
        );
        let c = containers.entry(key).or_insert(c);
        if !is_empty {
            let kind = if item["entity_kind"] == "reference" {
                "reference_count"
            } else {
                "item_count"
            };
            for target in [owner, c] {
                for field in ["count", kind] {
                    target[field] = json!(target[field].as_u64().unwrap_or(0) + 1);
                }
            }
        }
    }
    let mut sites = sites
        .into_values()
        .map(|(mut owner, containers)| {
            let mut containers = containers.into_values().collect::<Vec<_>>();
            containers.sort_by_key(|v| {
                (
                    v["kind"] == "unclassified",
                    unicode::casefold(s(v, "name")),
                    s(v, "kind").to_owned(),
                    v["id"].as_i64().unwrap_or(0),
                    s(v, "structural_scope").to_owned(),
                )
            });
            owner["containers"] = json!(containers);
            owner
        })
        .collect::<Vec<_>>();
    sites.sort_by_key(|v| (unicode::casefold(s(v, "normalized_domain")), id(v)));
    let count = |field: &str| {
        sites
            .iter()
            .map(|v| v[field].as_u64().unwrap_or(0))
            .sum::<u64>()
    };
    json!({"eligible_count":count("count"),"count":count("count"),"item_count":count("item_count"),"reference_count":count("reference_count"),"sites":sites})
}
fn active_structure(
    filters: &Value,
    items: &[Value],
    empty_space: Option<&Value>,
    empty_structure: Option<&Value>,
) -> Value {
    if ["site_id", "space_id", "structural_scope"]
        .iter()
        .all(|k| filters[k].is_null())
    {
        return json!({"kind":"root","label":"모든 도메인"});
    }
    let site_label = |v: &Value| {
        if truth(&v["normalized_domain"]) {
            v["normalized_domain"].clone()
        } else {
            v["site_name"].clone()
        }
    };
    if let Some(v) = empty_space {
        return json!({"kind":"space","label":format!("{} / {}",python_string(&site_label(v)),if truth(&v["name"]){python_string(&v["name"])}else{"이름 없음".into()}),"empty_registered_space":true});
    }
    if let Some(v) = empty_structure {
        return json!({"kind":v["container_kind"],"label":format!("{} / {}",python_string(&v["normalized_domain"]),python_string(&v["container_label"])),"empty_selected_structure":true});
    }
    let Some(v) = items.iter().find(|v| {
        ["service", "site_id", "space_id"]
            .iter()
            .all(|k| filters[k].is_null() || v[k] == filters[k])
            && (filters["structural_scope"].is_null()
                || v["container_structural_scope"] == filters["structural_scope"])
    }) else {
        return json!({"kind":"unavailable","label":"Unavailable scope"});
    };
    let site = python_string(&site_label(v));
    if !filters["space_id"].is_null() {
        return json!({"kind":"space","label":format!("{} / {}",site,if truth(&v["space_name"]){python_string(&v["space_name"])}else{"이름 없음".into()})});
    }
    if filters["structural_scope"] == "unclassified" {
        return json!({"kind":"unclassified","label":format!("{site} / 소속 미확인")});
    }
    if !filters["structural_scope"].is_null() {
        return json!({"kind":"url","label":format!("{} / {}",site,python_string(&v["container_label"]))});
    }
    json!({"kind":"site","label":site})
}
pub fn browse_inventory(db: &Connection, values: &Value) -> Result<Value> {
    let filters = normalize_browse_structure(db, &normalize_browse_filters(values)?)?;
    let (mut options, memberships) = classification_maps(db)?;
    let workstreams = workstream_memberships(db)?;
    let all_items = item_rows(db, None)?;
    let all_references = structure_references::structure_reference_rows(db, true, None)?;
    let exact = exact_item_matches(db, &all_items, &memberships, s(&filters, "q"))?;
    let exact_refs = exact_reference_matches(db, &all_references, s(&filters, "q"))?;
    let mut eligible_filters = filters.clone();
    for key in ["site_id", "space_id", "structural_scope"] {
        eligible_filters[key] = Value::Null;
    }
    let eligible_items = all_items
        .iter()
        .filter(|v| {
            filter_item(
                v,
                &eligible_filters,
                exact.as_ref(),
                &memberships,
                &workstreams,
            )
        })
        .cloned()
        .collect::<Vec<_>>();
    let eligible_refs = all_references
        .iter()
        .filter(|v| filter_reference(v, &eligible_filters, exact_refs.as_ref()))
        .cloned()
        .collect::<Vec<_>>();
    let mut items = all_items
        .iter()
        .filter(|v| filter_item(v, &filters, exact.as_ref(), &memberships, &workstreams))
        .cloned()
        .map(|mut v| {
            let key = id(&v);
            merge(
                &mut v,
                memberships
                    .get(&key)
                    .cloned()
                    .unwrap_or(json!({"topics":[],"tags":[]})),
            );
            let key = id(&v);
            v["workstream_ids"] = json!(workstreams.get(&key).cloned().unwrap_or_default());
            if let Some(exact) = &exact {
                v["exact_match"] = exact[&key].clone();
            }
            v
        })
        .collect::<Vec<_>>();
    if exact.is_some() {
        items.sort_by_key(|v| (v["exact_match"]["rank"].as_i64().unwrap_or(0), id(v)));
    }
    let mut references = all_references
        .iter()
        .filter(|v| filter_reference(v, &filters, exact_refs.as_ref()))
        .cloned()
        .map(|mut v| {
            if let Some(exact) = &exact_refs {
                let key = id(&v);
                v["exact_match"] = exact[&key].clone();
            }
            v
        })
        .collect::<Vec<_>>();
    if exact_refs.is_some() {
        references.sort_by_key(|v| (v["exact_match"]["rank"].as_i64().unwrap_or(0), id(v)));
    }
    let mut entries = items.iter().chain(&references).cloned().collect::<Vec<_>>();
    if !s(&filters, "q").is_empty() {
        entries.sort_by_key(|v| {
            (
                v["exact_match"]["rank"].as_i64().unwrap_or(0),
                v["entity_kind"] != "item",
                id(v),
            )
        });
    } else {
        entries.sort_by_key(|v| std::cmp::Reverse(id(v)));
        entries.sort_by_key(|v| v["entity_kind"] != "item");
        entries.sort_by_key(|v| std::cmp::Reverse(s(v, "updated_at").to_owned()));
        entries.sort_by_key(|v| !(v["entity_kind"] == "item" && v["attention"] == "pinned"));
    }
    let eligible = eligible_items
        .iter()
        .chain(&eligible_refs)
        .cloned()
        .collect::<Vec<_>>();
    let all = all_items
        .iter()
        .chain(
            all_references
                .iter()
                .filter(|v| v["lifecycle"] != "archived"),
        )
        .cloned()
        .collect::<Vec<_>>();
    let empty_space = selected_zero_space(db, &filters, &eligible_items)?;
    let empty_structure = selected_zero_structure(&filters, &eligible, &all)?;
    for (key, sql) in [
        ("sources", SQL_BROWSE_INVENTORY_0),
        ("sites", SQL_BROWSE_INVENTORY_1),
        ("spaces", SQL_BROWSE_INVENTORY_2),
        ("workstreams", SQL_BROWSE_INVENTORY_3),
    ] {
        options[key] = json!(db::rows(db, sql, [])?);
    }
    let known_items = all_items
        .iter()
        .filter(|v| filters["service"].is_null() || v["service"] == filters["service"])
        .count();
    let known_refs = all_references
        .iter()
        .filter(|v| {
            v["lifecycle"] != "archived"
                && (filters["service"].is_null() || v["service"] == filters["service"])
        })
        .count();
    let active_count = ADVANCED_FILTER_FIELDS
        .iter()
        .filter(|k| !filters[k].is_null())
        .count();
    let mut result = json!({"filters":filters,"items":null,"references":null,"entries":null,"hierarchy":hierarchy(&eligible,empty_space.as_ref(),empty_structure.as_ref()),"eligible_count":eligible.len(),"eligible_item_count":eligible_items.len(),"eligible_reference_count":eligible_refs.len(),"known_item_count":known_items,"known_reference_count":known_refs,"known_count":known_items+known_refs,"matching_count":entries.len(),"matching_item_count":items.len(),"matching_reference_count":references.len(),"has_filters":filters.as_object().unwrap().values().any(|v|!v.is_null()&&v!=""),"has_advanced_filters":active_count>0,"active_filter_count":active_count,"active_structure":active_structure(&filters,&all,empty_space.as_ref(),empty_structure.as_ref()),"options":options});
    // Stored metadata admits Python JSON numbers such as NaN. Keep those
    // values intact for core callers; strict JSON output validates separately.
    result["items"] = Value::Array(items);
    result["references"] = Value::Array(references);
    result["entries"] = Value::Array(entries);
    Ok(result)
}
fn latest_refresh(db: &Connection, resource: i64) -> Result<Value> {
    let target = format!("atlassian-item-{resource}");
    for mut row in db::rows(db, SQL_LATEST_REFRESH_RUN_0, [])? {
        let manifest = crate::backend::json::decode(
            row["source_snapshot_json"]
                .as_str()
                .filter(|s| !s.is_empty())
                .unwrap_or("{}"),
        )
        .unwrap_or(Value::Null);
        if manifest.is_object()
            && arr(&manifest["targets"])
                .iter()
                .any(|v| v.is_object() && v["target_id"] == target)
        {
            row.as_object_mut().unwrap().remove("source_snapshot_json");
            return Ok(row);
        }
    }
    Ok(Value::Null)
}
fn preview_excerpt(value: &Value, limit: usize) -> (Value, bool) {
    if value.is_null() {
        return (Value::Null, false);
    }
    let text = python_string(value);
    if text.chars().count() <= limit {
        (json!(text), false)
    } else {
        (
            json!(format!("{}…", prefix(&text, limit.saturating_sub(1)))),
            true,
        )
    }
}
fn metadata_summary(value: &Value) -> (Vec<Value>, usize) {
    let mut scalars = Vec::new();
    let mut pending = vec![(value, String::new(), true)];
    while let Some((value, path, top)) = pending.pop() {
        match value {
            Value::Object(values) => {
                let mut keys = values.keys().collect::<Vec<_>>();
                keys.sort();
                for key in keys.into_iter().rev() {
                    if top && ["title", "summary"].contains(&key.as_str()) {
                        continue;
                    }
                    let escaped = key
                        .replace('\\', "\\\\")
                        .replace('.', "\\.")
                        .replace('[', "\\[")
                        .replace(']', "\\]");
                    let path = if path.is_empty() {
                        escaped
                    } else {
                        format!("{path}.{escaped}")
                    };
                    pending.push((&values[key], path, false));
                }
            }
            Value::Array(values) => {
                for (index, value) in values.iter().enumerate().rev() {
                    pending.push((value, format!("{path}[{index}]"), false));
                }
            }
            Value::Null => {}
            _ if !path.is_empty() => {
                let value = if value.is_string() {
                    value.as_str().unwrap().to_owned()
                } else {
                    value.to_string()
                };
                scalars.push((path, value));
            }
            _ => {}
        }
    }
    scalars.sort_by(|a, b| a.0.cmp(&b.0));
    let total = scalars.len();
    let summary = scalars
        .into_iter()
        .take(12)
        .map(|(path, value)| {
            let (path, p) = preview_excerpt(&json!(path), 160);
            let (value, v) = preview_excerpt(&json!(value), 240);
            json!({"path":path,"value":value,"path_truncated":p,"value_truncated":v})
        })
        .collect();
    (summary, total)
}
fn preview_item_row(db: &Connection, resource: i64) -> Result<Option<Value>> {
    one(db, SQL_PREVIEW_ITEM_ROW_0, &[&json!(resource)])?
        .map(|v| prepare_item(v, true))
        .transpose()
}
fn preview_identity(item: &Value, eligible: bool) -> Value {
    let mut value = obj(
        item,
        &[
            "id",
            "service",
            "item_type",
            "display_title",
            "local_title",
            "remote_key",
            "source_instance_id",
            "site_id",
            "site_name",
            "normalized_domain",
            "space_id",
            "space_name",
            "space_key",
            "container_kind",
            "container_label",
            "container_service",
            "container_cue",
            "container_structural_scope",
            "canonical_url",
            "coverage",
            "freshness",
            "attention",
        ],
    );
    value["eligible"] = json!(eligible);
    value
}
fn preview_all_classes(db: &Connection, resource: i64) -> Result<Value> {
    let mut values = json!({"topics":[],"tags":[]});
    for row in query(db, SQL_PREVIEW_ALL_CLASSIFICATIONS_0, &[&json!(resource)])? {
        let key = if row["kind"] == "topic" {
            "topics"
        } else {
            "tags"
        };
        values[key].as_array_mut().unwrap().push(row);
    }
    Ok(values)
}
fn preview_requested_classes(db: &Connection, resource: i64, filters: &Value) -> Result<Value> {
    let mut values = json!({"topics":[],"tags":[]});
    if filters["topic_id"].is_null() && filters["tag_id"].is_null() {
        return Ok(values);
    }
    for row in query(
        db,
        SQL_PREVIEW_REQUESTED_CLASSIFICATIONS_0,
        &[
            &json!(resource),
            &filters["topic_id"],
            &filters["topic_id"],
            &filters["tag_id"],
            &filters["tag_id"],
        ],
    )? {
        let key = if row["kind"] == "topic" {
            "topics"
        } else {
            "tags"
        };
        values[key]
            .as_array_mut()
            .unwrap()
            .push(json!({"id":row["id"]}));
    }
    Ok(values)
}
fn preview_classification_projection(db: &Connection, resource: i64) -> Result<(Value, Value)> {
    let mut values = json!({"topic":{"items":[],"total":0,"truncated":false},"tag":{"items":[],"total":0,"truncated":false}});
    for row in query(
        db,
        SQL_PREVIEW_CLASSIFICATION_PROJECTION_0,
        &[&json!(resource), &json!(30)],
    )? {
        let key = s(&row, "kind");
        values[key]["total"] = row["preview_total"].clone();
        values[key]["items"]
            .as_array_mut()
            .unwrap()
            .push(obj(&row, &["id", "name", "normalized_name"]));
    }
    for key in CLASSIFICATION_KINDS {
        values[key]["truncated"] = json!(
            values[key]["total"].as_u64().unwrap_or(0) > arr(&values[key]["items"]).len() as u64
        );
    }
    Ok((values["topic"].clone(), values["tag"].clone()))
}
fn preview_classes_from_memberships(memberships: &Value) -> (Value, Value) {
    let mut values = Vec::new();
    for key in ["topics", "tags"] {
        let mut rows = arr(&memberships[key]).to_vec();
        rows.sort_by_key(|v| (s(v, "normalized_name").to_owned(), id(v)));
        let items = rows
            .iter()
            .take(30)
            .map(|v| obj(v, &["id", "name", "normalized_name"]))
            .collect::<Vec<_>>();
        values.push(json!({"items":items,"total":rows.len(),"truncated":rows.len()>items.len()}));
    }
    (values[0].clone(), values[1].clone())
}
fn preview_text_matches(
    db: &Connection,
    resource: i64,
    tokens: &[String],
    include_content: bool,
) -> Result<bool> {
    let tokens = tokens.to_vec();
    db.create_scalar_function(
        "localbrain_atlassian_exact_phrase",
        1,
        FunctionFlags::SQLITE_UTF8 | FunctionFlags::SQLITE_DETERMINISTIC,
        move |ctx| {
            let value = ctx.get::<Option<String>>(0)?;
            Ok(i64::from(exact_phrase(&json!(value), &tokens)))
        },
    )?;
    let result = one(
        db,
        SQL_PREVIEW_TEXT_MATCHES_0,
        &[&json!(i64::from(include_content)), &json!(resource)],
    );
    let removed = db.remove_function("localbrain_atlassian_exact_phrase", 1);
    let row = result?;
    removed?;
    Ok(row.is_some_and(|v| truth(&v["content_matches"]) || truth(&v["note_matches"])))
}
fn preview_evidence(db: &Connection, resource: i64) -> Result<Value> {
    let rows = query(db, SQL_PREVIEW_EVIDENCE_0, &[&json!(resource), &json!(5)])?;
    bounded_group(rows, &["observed_order"])
}
fn preview_organization(db: &Connection, resource: i64) -> Result<Value> {
    bounded_group(
        query(
            db,
            SQL_PREVIEW_ORGANIZATION_0,
            &[
                &json!(resource.to_string()),
                &json!(resource.to_string()),
                &json!(5),
            ],
        )?,
        &[],
    )
}
fn bounded_group(mut rows: Vec<Value>, omit: &[&str]) -> Result<Value> {
    let total = rows
        .first()
        .map(|v| v["preview_total"].clone())
        .unwrap_or(json!(0));
    for row in &mut rows {
        let map = row.as_object_mut().unwrap();
        map.remove("preview_total");
        for key in omit {
            map.remove(*key);
        }
    }
    Ok(json!({"items":rows,"total":total,"truncated":total.as_u64().unwrap_or(0)>rows.len()as u64}))
}
pub fn atlassian_item_preview(
    db: &Connection,
    resource: i64,
    values: &Value,
) -> Result<Option<Value>> {
    let filters = normalize_browse_structure(db, &normalize_browse_filters(values)?)?;
    let query = s(&filters, "q");
    let tokens = if query.is_empty() {
        vec![]
    } else {
        exact_query_tokens(query)?
    };
    let normalized = if query.is_empty() {
        None
    } else {
        normalized_query_url(query)?
    };
    let Some(item) = preview_item_row(db, resource)? else {
        return Ok(None);
    };
    let mut scalar = filters.clone();
    for key in ["topic_id", "tag_id", "workstream_id"] {
        scalar[key] = Value::Null;
    }
    if !filter_item(
        &item,
        &scalar,
        None,
        &Memberships::new(),
        &Workstreams::new(),
    ) {
        return Ok(Some(preview_identity(&item, false)));
    }
    let mut exact_memberships = None;
    if !query.is_empty() {
        let urls = query_rows_for_urls(db, resource)?;
        let mut matches = identity_value(&item, &urls, query, normalized.as_deref()).is_some()
            || title_values(&item).iter().any(|v| exact_phrase(v, &tokens));
        if !matches {
            let memberships = preview_all_classes(db, resource)?;
            matches = other_values(&item, &memberships)
                .iter()
                .any(|(_, v)| exact_phrase(v, &tokens));
            exact_memberships = Some(memberships);
        }
        if !matches {
            matches =
                preview_text_matches(db, resource, &tokens, item["freshness"] != "unavailable")?;
        }
        if !matches {
            return Ok(Some(preview_identity(&item, false)));
        }
    }
    let memberships = if let Some(m) = &exact_memberships {
        m.clone()
    } else {
        preview_requested_classes(db, resource, &filters)?
    };
    let mut workstreams = Workstreams::new();
    if let Some(wid) = filters["workstream_id"].as_i64() {
        if one(
            db,
            SQL_PREVIEW_HAS_WORKSTREAM_0,
            &[
                &json!(resource.to_string()),
                &json!(wid),
                &json!(resource.to_string()),
                &json!(wid),
            ],
        )?
        .is_some()
        {
            workstreams.entry(resource).or_default().insert(wid);
        }
    }
    let memberships_map = BTreeMap::from([(resource, memberships)]);
    let matching = BTreeMap::from([(resource, Value::Null)]);
    if !filter_item(
        &item,
        &filters,
        (!query.is_empty()).then_some(&matching),
        &memberships_map,
        &workstreams,
    ) {
        return Ok(Some(preview_identity(&item, false)));
    }
    let (topics, tags) = match exact_memberships {
        Some(m) => preview_classes_from_memberships(&m),
        None => preview_classification_projection(db, resource)?,
    };
    let texts = one(
        db,
        SQL_PREVIEW_TEXT_VALUES_0,
        &[&json!(1201), &json!(601), &json!(resource)],
    )?
    .unwrap_or(json!({"normalized_text":null,"note":null}));
    let (content, content_truncated) = preview_excerpt(&texts["normalized_text"], 1200);
    let (note, note_truncated) = preview_excerpt(&texts["note"], 600);
    let (summary, total) = metadata_summary(&item["metadata"]);
    let recent = latest_refresh(db, resource)?;
    let mut value = preview_identity(&item, true);
    merge(
        &mut value,
        obj(
            &item,
            &[
                "last_attempted_at",
                "last_successful_at",
                "last_outcome",
                "remote_id",
                "remote_version",
                "remote_updated_at",
                "last_error_code",
            ],
        ),
    );
    merge(
        &mut value,
        json!({"metadata_summary":summary,"metadata_summary_total":total,"metadata_summary_truncated":total>summary.len(),"content_excerpt":content,"content_truncated":content_truncated,"note_excerpt":note,"note_truncated":note_truncated,"topics":topics,"tags":tags,"evidence":preview_evidence(db,resource)?,"organization":preview_organization(db,resource)?,"recent_refresh_run":recent,"history_scope":"recent-200","history_complete":false,"history_absence":if recent.is_null(){json!("not found in recent history")}else{Value::Null}}),
    );
    Ok(Some(value))
}
fn query_rows_for_urls(db: &Connection, resource: i64) -> Result<Vec<Value>> {
    query(db, SQL_PREVIEW_ITEM_URLS_0, &[&json!(resource)])
}
pub fn atlassian_structure_reference_preview(
    db: &Connection,
    reference: i64,
    values: &Value,
) -> Result<Option<Value>> {
    let filters = normalize_browse_structure(db, &normalize_browse_filters(values)?)?;
    let Some(mut value) = structure_references::structure_reference_preview(db, reference)? else {
        return Ok(None);
    };
    let matches = exact_reference_matches(db, std::slice::from_ref(&value), s(&filters, "q"))?;
    value["eligible"] = json!(filter_reference(&value, &filters, matches.as_ref()));
    if let Some(exact) = matches.and_then(|mut v| v.remove(&reference)) {
        value["exact_match"] = exact;
    }
    Ok(Some(value))
}
pub fn atlassian_structure_reference_detail(
    db: &Connection,
    reference: i64,
) -> Result<Option<Value>> {
    structure_references::structure_reference_detail(db, reference)
}
pub fn atlassian_item_detail(db: &Connection, resource: i64) -> Result<Option<Value>> {
    let Some(mut item) = item_rows(db, Some(resource))?.into_iter().next() else {
        return Ok(None);
    };
    let (options, memberships) = classification_maps(db)?;
    merge(
        &mut item,
        memberships
            .get(&resource)
            .cloned()
            .unwrap_or(json!({"topics":[],"tags":[]})),
    );
    item["selected_topic_ids"] =
        json!(arr(&item["topics"]).iter().map(id).collect::<BTreeSet<_>>());
    item["memberships"] = json!(query(
        db,
        SQL_ATLASSIAN_ITEM_DETAIL_0,
        &[&json!(resource.to_string()), &json!(resource.to_string())]
    )?);
    item["evidence"] = json!(query(db, SQL_ATLASSIAN_ITEM_DETAIL_1, &[&json!(resource)])?);
    item["latest_refresh_run"] = latest_refresh(db, resource)?;
    item["classification_options"] = options;
    let mut workstreams = db::rows(db, SQL_ATLASSIAN_ITEM_DETAIL_2, [])?;
    for row in &mut workstreams {
        row["threads"] = json!(query(db, SQL_ATLASSIAN_ITEM_DETAIL_3, &[&row["id"]])?);
    }
    item["workstreams"] = json!(workstreams);
    Ok(Some(item))
}
fn classification_name(value: &Value, label: &str) -> Result<(String, String)> {
    let name = clean(value)
        .split(unicode::python_space)
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    if name.is_empty() || name.chars().count() > 160 {
        return Err(fail(
            "invalid-classification",
            format!("{label} must be 1-160 characters"),
        ));
    }
    let key = unicode::casefold(&name);
    Ok((name, key))
}
fn upsert_classification(
    db: &Connection,
    kind: &str,
    name: &str,
    description: Option<&str>,
    changed: &str,
) -> Result<i64> {
    if !CLASSIFICATION_KINDS.contains(&kind) {
        return Err(fail(
            "invalid-classification",
            "Unsupported classification kind",
        ));
    }
    let (name, key) = classification_name(&json!(name), kind)?;
    let description = if kind == "tag" {
        None
    } else {
        description.map(trim).filter(|s| !s.is_empty())
    };
    if description.is_some_and(|s| s.chars().count() > 4000) {
        return Err(fail(
            "invalid-topic-description",
            "Topic description exceeds 4000 characters",
        ));
    }
    db.execute(
        SQL_UPSERT_CLASSIFICATION_0,
        params![kind, name, key, description, changed],
    )?;
    Ok(one(
        db,
        SQL_UPSERT_CLASSIFICATION_1,
        &[&json!(kind), &json!(key)],
    )?
    .unwrap()["id"]
        .as_i64()
        .unwrap())
}
pub fn update_atlassian_local_state(
    db: &Connection,
    resource: i64,
    values: &Value,
) -> Result<Value> {
    if one(db, SQL_UPDATE_ATLASSIAN_LOCAL_STATE_0, &[&json!(resource)])?.is_none() {
        return Err(fail(
            "item-not-found",
            "Atlassian 링크/문서를 찾을 수 없습니다",
        ));
    }
    let note = clean(&values["note"]);
    let note = trim(&note);
    if note.chars().count() > 50000 {
        return Err(fail("invalid-note", "Local note exceeds 50000 characters"));
    }
    let attention = values["attention"]
        .as_str()
        .filter(|s| catalog::ATTENTION_VALUES.contains(s))
        .ok_or_else(|| fail("invalid-attention", "Unsupported attention state"))?;
    let changed = values["changed_at"]
        .as_str()
        .filter(|s| !s.is_empty())
        .map(str::to_owned)
        .unwrap_or_else(super::common::now);
    let mut topic_ids = Vec::new();
    for value in arr(&values["topic_ids"]) {
        let integer = integer_value(value)
            .and_then(|v| i64::try_from(v).ok())
            .ok_or_else(|| fail("invalid-topic", "A selected Topic was not found"))?;
        if !topic_ids.contains(&integer) {
            topic_ids.push(integer);
        }
    }
    if !topic_ids.is_empty() {
        let sql =
            SQL_UPDATE_ATLASSIAN_LOCAL_STATE_1.replace("{}", &vec!["?"; topic_ids.len()].join(","));
        let valid = db::rows(db, &sql, params_from_iter(&topic_ids))?
            .iter()
            .map(id)
            .collect::<BTreeSet<_>>();
        if valid != topic_ids.iter().copied().collect() {
            return Err(fail("invalid-topic", "A selected Topic was not found"));
        }
    }
    let new_topic = clean(&values["new_topic_name"]);
    let has_new_topic = !trim(&new_topic).is_empty();
    let description = clean(&values["new_topic_description"]);
    if has_new_topic {
        classification_name(&json!(new_topic), "topic")?;
        if trim(&description).chars().count() > 4000 {
            return Err(fail(
                "invalid-topic-description",
                "Topic description exceeds 4000 characters",
            ));
        }
    }
    let mut tags = Vec::new();
    let mut seen = BTreeSet::new();
    for value in clean(&values["tags"]).split(',') {
        let name = trim(value);
        if !name.is_empty() && seen.insert(unicode::casefold(name)) {
            tags.push(name.to_owned());
        }
    }
    if tags.len() > 30 {
        return Err(fail(
            "too-many-tags",
            "링크/문서는 Tag를 최대 30개까지 지원합니다",
        ));
    }
    for tag in &tags {
        classification_name(&json!(tag), "tag")?;
    }
    db.execute_batch(SQL_UPDATE_ATLASSIAN_LOCAL_STATE_2)?;
    let result = (|| -> Result<()> {
        if has_new_topic {
            let id = upsert_classification(db, "topic", &new_topic, Some(&description), &changed)?;
            if !topic_ids.contains(&id) {
                topic_ids.push(id);
            }
        }
        let tag_ids = tags
            .iter()
            .map(|name| upsert_classification(db, "tag", name, None, &changed))
            .collect::<Result<Vec<_>>>()?;
        if !note.is_empty() {
            db.execute(
                SQL_UPDATE_ATLASSIAN_LOCAL_STATE_3,
                params![resource, note, changed],
            )?;
        } else {
            db.execute(SQL_UPDATE_ATLASSIAN_LOCAL_STATE_4, [resource])?;
        }
        for kind in CLASSIFICATION_KINDS {
            db.execute(SQL_UPDATE_ATLASSIAN_LOCAL_STATE_5, params![resource, kind])?;
        }
        for id in topic_ids.iter().chain(&tag_ids) {
            db.execute(SQL_UPDATE_ATLASSIAN_LOCAL_STATE_6, params![resource, id])?;
        }
        catalog::set_atlassian_item_axes(
            db,
            resource,
            &json!({"attention":attention,"changed_at":changed}),
        )?;
        catalog::project_atlassian_item_search(db, resource, Some(&changed))?;
        Ok(())
    })();
    if let Err(e) = result {
        db.execute_batch(SQL_UPDATE_ATLASSIAN_LOCAL_STATE_7)?;
        db.execute_batch(SQL_UPDATE_ATLASSIAN_LOCAL_STATE_8)?;
        return Err(e);
    }
    db.execute_batch(SQL_UPDATE_ATLASSIAN_LOCAL_STATE_9)?;
    Ok(atlassian_item_detail(db, resource)?.unwrap_or(json!({})))
}
fn fts_expression(query: &str) -> String {
    query
        .split(|c: char| c != '_' && c != '.' && c != '-' && !unicode::python_alnum(c))
        .filter(|s| !s.is_empty())
        .take(12)
        .map(|s| format!("\"{}\"", s.replace('"', "\"\"")))
        .collect::<Vec<_>>()
        .join(" AND ")
}
pub fn atlassian_search_results(
    db: &Connection,
    query: &str,
    values: &Value,
    limit: i64,
) -> Result<Vec<Value>> {
    let expression = fts_expression(query);
    if expression.is_empty() {
        return Ok(vec![]);
    }
    let mut filters = if values.is_object() {
        values.clone()
    } else {
        json!({})
    };
    filters["q"] = json!("");
    let inventory = browse_inventory(db, &filters)?;
    let allowed = arr(&inventory["items"])
        .iter()
        .map(|v| (id(v), v))
        .collect::<BTreeMap<_, _>>();
    let refs = arr(&inventory["references"]);
    let reference_matches = exact_reference_matches(db, refs, query)?.unwrap_or_default();
    let references = refs.iter().map(|v| (id(v), v)).collect::<BTreeMap<_, _>>();
    let mut grouped: BTreeMap<(String, i64), Value> = BTreeMap::new();
    for row in query_rows(db, &expression)? {
        let entity = s(&row, "entity_type");
        let Some(item_id) = integer_value(&row["entity_id"]).and_then(|v| i64::try_from(v).ok())
        else {
            continue;
        };
        let key = (entity.to_owned(), item_id);
        if entity == "atlassian_structure_reference" {
            let Some(reference) = references.get(&item_id) else {
                continue;
            };
            let exact = reference_matches.get(&item_id);
            let role = exact.map(|v| v["role"].clone()).unwrap_or(json!("url"));
            let mut result = obj(
                reference,
                &[
                    "service",
                    "normalized_domain",
                    "reference_kind",
                    "reference_identity",
                    "family_label",
                    "availability",
                    "provenance",
                    "container_kind",
                    "container_label",
                    "container_service",
                    "container_cue",
                ],
            );
            merge(
                &mut result,
                json!({"entity_type":entity,"entity_id":item_id.to_string(),"source_kind":format!("atlassian:{}",s(reference,"service")),"title":format!("{} · {}",s(reference,"family_label"),s(reference,"reference_identity")),"path":reference["canonical_url"],"excerpt":exact.map(|v|v["excerpt"].clone()).unwrap_or_else(||if truth(&row["excerpt"]){row["excerpt"].clone()}else{row["matched_title"].clone()}),"score":row["score"],"match_roles":[role],"entity_kind":"reference"}),
            );
            grouped.insert(key, result);
            continue;
        }
        let Some(item) = allowed.get(&item_id) else {
            continue;
        };
        let result=grouped.entry(key).or_insert_with(||{let mut result=obj(item,&["service","item_type","source_name","normalized_domain","space_name","container_kind","container_label","container_service","container_cue","coverage","freshness","attention"]);merge(&mut result,json!({"entity_type":"atlassian_item","entity_id":item_id.to_string(),"source_kind":format!("atlassian:{}",s(item,"service")),"title":item["display_title"],"path":item["canonical_url"],"excerpt":if truth(&row["excerpt"]){row["excerpt"].clone()}else{row["matched_title"].clone()},"score":row["score"],"match_roles":[]}));result});
        let role = s(&row, "source_kind").rsplit(':').next().unwrap_or("");
        if !arr(&result["match_roles"]).contains(&json!(role)) {
            result["match_roles"]
                .as_array_mut()
                .unwrap()
                .push(json!(role));
        }
        if row["score"].as_f64().unwrap_or(0.0) < result["score"].as_f64().unwrap_or(0.0) {
            result["score"] = row["score"].clone();
            result["excerpt"] = if truth(&row["excerpt"]) {
                row["excerpt"].clone()
            } else {
                row["matched_title"].clone()
            };
        }
    }
    let mut results = grouped.into_values().collect::<Vec<_>>();
    results.sort_by(|a, b| {
        a["score"]
            .as_f64()
            .unwrap_or(0.0)
            .total_cmp(&b["score"].as_f64().unwrap_or(0.0))
            .then_with(|| s(a, "title").cmp(s(b, "title")))
            .then_with(|| s(a, "entity_type").cmp(s(b, "entity_type")))
            .then_with(|| s(a, "entity_id").cmp(s(b, "entity_id")))
    });
    let length = if limit >= 0 {
        usize::try_from(limit).unwrap_or(usize::MAX)
    } else {
        results
            .len()
            .saturating_sub(limit.unsigned_abs().try_into().unwrap_or(usize::MAX))
    };
    results.truncate(length);
    Ok(results)
}
fn query_rows(db: &Connection, expression: &str) -> Result<Vec<Value>> {
    db::rows(db, SQL_ATLASSIAN_SEARCH_RESULTS_0, [expression])
}
