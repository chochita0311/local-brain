//! Imported Sessions, independent user metadata, and derived read projections.
pub mod activity;
pub mod dashboard;
mod dashboard_sql;
mod metadata;
mod queries;
pub mod reading;
mod reference_sql;
pub mod references;
pub mod skills;
mod sql;
pub mod subagents;
pub use metadata::*;
pub use queries::*;

pub fn source_presence_columns(alias: &str) -> String {
    // Only callers in this module supply fixed SQL identifiers.
    assert!(["sessions", "children"].contains(&alias));
    sql::SOURCE_PRESENCE.replace("{session}", alias)
}
