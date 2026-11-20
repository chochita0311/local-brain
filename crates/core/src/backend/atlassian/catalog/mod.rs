//! Stable Site/Space/Item identities and authority-separated remote memory.
mod content;
mod facts;
mod projection;
mod store;
pub use crate::backend::references::{
    normalize_atlassian_catalog_url as normalize_atlassian_url, NormalizedAtlassianUrl,
};
pub use content::{
    normalize_atlassian_content, NormalizedContent, NORMALIZED_DOCUMENT_SCHEMA, NORMALIZER_VERSION,
    SOURCE_FORMATS,
};
pub use facts::{apply_atlassian_target_result, atlassian_item_state, derive_atlassian_freshness};
pub use projection::{project_atlassian_item_search, rebuild_atlassian_search_index};
pub use store::*;
pub const METADATA_SCHEMA: &str = "localbrain.atlassian-metadata.v1";
pub const SERVICES: &[&str] = &["jira", "confluence"];
pub const COVERAGE_VALUES: &[&str] = &["reference", "metadata", "indexed"];
pub const ATTENTION_VALUES: &[&str] = &["normal", "pinned", "ignored", "archived"];
pub(super) const SUCCESS: &[&str] = &["resolved", "unchanged", "changed"];
pub(super) const FAILURES: &[&str] = &["unavailable", "not_found", "error"];
