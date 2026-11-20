//! Named, preserving migrations from the established SQLite contracts.
//!
//! There is intentionally no global database version: each owner admits only
//! known historical shapes, validates retained values and repairs its contract.
mod compatible;
mod contracts;
pub(crate) mod identity;
mod resources;
mod revisions;
pub(crate) mod support;
use crate::backend::{db, Config, Result};
pub(crate) use contracts::migration_contracts_current;
use rusqlite::Connection;
use support::*;

pub fn initialize(connection: &Connection, config: &Config) -> Result<()> {
    // Preflight and recovery copies precede every mutation, including schema DDL.
    if exists(connection, "sessions")? && !contracts::display_title_current(connection)? {
        backup(connection, config, "-pre-session-display-title-v1.bak")?;
    }
    if exists(connection, "sessions")? && !resources::current(connection)? {
        backup(connection, config, "-pre-shared-resources-v1.bak")?;
    }
    revisions::prepare(connection, config)?;
    contracts::validate_structure(connection, true)?;
    let source_repair =
        exists(connection, "sources")? && !contracts::source_identity_current(connection)?;
    if source_repair {
        backup(connection, config, "-pre-source-primary-key-v1.bak")?;
    }
    let atlassian_repair =
        exists(connection, "atlassian_sites")? && !contracts::site_access_current(connection)?;
    if atlassian_repair {
        backup(connection, config, "-pre-atlassian-site-access-v1.bak")?;
    }
    if exists(connection, "external_resources")?
        && unique_columns(connection, "external_resources")?.contains(&vec!["url".into()])
    {
        backup(
            connection,
            config,
            "-pre-external-resource-url-scope-v1.bak",
        )?;
    }
    let usage_table = contracts::usage_table(connection)?;
    if exists(connection, "maintenance_runs")? && !contracts::maintenance_fk_current(connection)? {
        backup(connection, config, "-pre-maintenance-workstream-fk-v1.bak")?;
    }
    if exists(connection, "sessions")? && !contracts::session_contract_current(connection)? {
        backup(
            connection,
            config,
            "-pre-maintenance-session-contract-v1.bak",
        )?;
    }
    if let Some(table) = &usage_table {
        if !contracts::attribution_current(connection, table)? {
            backup(connection, config, "-pre-usage-attribution-check-v1.bak")?;
        }
    }
    contracts::rename_usage(connection)?;
    identity::migrate(connection, config)?;
    contracts::migrate_skill(connection)?;
    resources::migrate(connection, config)?;
    connection.execute_batch(db::SCHEMA)?;
    contracts::validate_structure(connection, false)?;
    if atlassian_repair {
        contracts::repair_site(connection)?;
    }
    compatible::run(connection, config)?;
    if !migration_contracts_current(connection)? {
        return Err(support::fail(
            "Database initialization found an unsupported migration contract",
        ));
    }
    if connection.is_autocommit() {
        connection.execute_batch("BEGIN")?;
    }
    crate::backend::usage::initialize_prices(connection)?;
    if usage_table.is_none() {
        connection.execute("UPDATE source_files SET status='stale' WHERE source_id IN (SELECT id FROM sources WHERE provider_kind IN ('claude','codex'))",[])?;
    }
    if !connection.is_autocommit() {
        connection.execute_batch("COMMIT")?;
    }
    super::accounting::maintain_migration_backups(&config.database_path, connection, true, None)?;
    Ok(())
}
