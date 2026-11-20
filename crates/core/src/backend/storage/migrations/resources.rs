use super::support::*;
use crate::backend::{db, resources, Config, Result};
use rusqlite::Connection;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
const TABLES: [&str; 4] = [
    "reference_resources",
    "resource_documents",
    "resource_local_paths",
    "resource_external_links",
];
const PAYLOADS: [(&str, &str); 2] = [
    ("atlassian_item_content", "external_resource_content"),
    ("atlassian_item_local_state", "external_resource_notes"),
];
pub fn current(connection: &Connection) -> Result<bool> {
    for table in TABLES {
        if !exists(connection, table)? {
            return Ok(false);
        }
    }
    for (old, new) in PAYLOADS {
        if exists(connection, old)? || !exists(connection, new)? {
            return Ok(false);
        }
        let targets = db::rows(
            connection,
            &format!("PRAGMA foreign_key_list({})", quote(new)),
            [],
        )?
        .iter()
        .filter_map(|row| row["table"].as_str().map(str::to_owned))
        .collect::<BTreeSet<_>>();
        if targets != BTreeSet::from(["external_resources".into()]) {
            return Ok(false);
        }
    }
    if !exists(connection, "session_reference_evidence")? {
        return Ok(false);
    }
    for table in ["workstream_links", "thread_links"] {
        if exists(connection, table)? && !has(connection, table, "resource_id")? {
            return Ok(false);
        }
    }
    let targets = db::rows(
        connection,
        "PRAGMA foreign_key_list(session_reference_evidence)",
        [],
    )?
    .iter()
    .filter_map(|row| row["table"].as_str().map(str::to_owned))
    .collect::<BTreeSet<_>>();
    Ok(targets == BTreeSet::from(["sessions".into(), "reference_resources".into()]))
}
fn payload(connection: &Connection, old: &str, new: &str) -> Result<()> {
    if !exists(connection, old)? {
        return Ok(());
    }
    connection.execute_batch(&ddl(new)?)?;
    let columns = columns(connection, old)?;
    if columns != super::support::columns(connection, new)? {
        return Err(fail(
            "Unrecognized external content contract; original content preserved",
        ));
    }
    let fields = columns.join(",");
    connection.execute_batch(&format!(
        "INSERT OR IGNORE INTO {new} ({fields}) SELECT {fields} FROM {old}"
    ))?;
    if !values(
        connection,
        &format!("SELECT {fields} FROM {old} EXCEPT SELECT {fields} FROM {new}"),
    )?
    .is_empty()
    {
        return Err(fail(
            "Conflicting external content; original content preserved",
        ));
    }
    connection.execute_batch(&format!("DROP TABLE {old}"))?;
    Ok(())
}
fn evidence(connection: &Connection, config: &Config) -> Result<()> {
    if !exists(connection, "session_reference_evidence")?
        || has(connection, "session_reference_evidence", "resource_id")?
    {
        return Ok(());
    }
    let rows = db::rows(
        connection,
        "SELECT * FROM session_reference_evidence ORDER BY id",
        [],
    )?;
    let mut sessions = BTreeSet::new();
    connection.execute_batch(
        "ALTER TABLE session_reference_evidence RENAME TO legacy_session_reference_evidence",
    )?;
    connection.execute_batch(&ddl("session_reference_evidence")?)?;
    let columns = columns(connection, "session_reference_evidence")?;
    let statement = format!(
        "INSERT INTO session_reference_evidence ({}) VALUES ({})",
        columns.join(","),
        vec!["?"; columns.len()].join(",")
    );
    for mut row in rows.iter().cloned() {
        let resource = if row["target_kind"] == "context_document" {
            resources::bind_document(
                connection,
                row["context_document_id"]
                    .as_i64()
                    .ok_or_else(|| fail("Missing document reference identity"))?,
                config,
            )?
        } else {
            let locator = row["normalized_url"].as_str().unwrap_or("");
            match resources::url_resource(connection, locator)? {
                Some(id) => id,
                None => {
                    let identity =
                        format!("unavailable-url:{:x}", Sha256::digest(locator.as_bytes()));
                    connection.execute("INSERT OR IGNORE INTO reference_resources(identity_key,kind,locator) VALUES (?,'url',?)",[identity.as_str(),locator])?;
                    connection.query_row(
                        "SELECT id FROM reference_resources WHERE identity_key=?",
                        [identity],
                        |row| row.get(0),
                    )?
                }
            }
        };
        row["resource_id"] = resource.into();
        row["target_key"] = connection
            .query_row(
                "SELECT identity_key FROM reference_resources WHERE id=?",
                [resource],
                |row| row.get::<_, String>(0),
            )?
            .into();
        let parameters = columns
            .iter()
            .map(|column| json_value(&row[column]))
            .collect::<Result<Vec<_>>>()?;
        connection.execute(&statement, rusqlite::params_from_iter(parameters))?;
        sessions.insert(row["session_id"].as_i64().unwrap());
    }
    let count: i64 = connection.query_row(
        "SELECT COUNT(*) FROM session_reference_evidence",
        [],
        |row| row.get(0),
    )?;
    if count != rows.len() as i64 {
        return Err(fail("Session reference migration lost evidence"));
    }
    connection.execute_batch("DROP TABLE legacy_session_reference_evidence")?;
    for session in sessions {
        let count: i64 = connection.query_row(
            "SELECT COUNT(DISTINCT target_key) FROM session_reference_evidence WHERE session_id=?",
            [session],
            |row| row.get(0),
        )?;
        connection.execute("UPDATE session_reference_scans SET retained_target_count=?,observed_target_count=CASE WHEN status='ok' THEN ? ELSE MAX(observed_target_count,?) END,error_code=CASE WHEN status='partial' THEN 'resource-identity-migration' ELSE error_code END,error_message=CASE WHEN status='partial' THEN 'Reference identities changed; rescan required' ELSE error_message END,status=CASE WHEN status='partial' THEN 'error' ELSE status END WHERE session_id=?",[count,count,count,session])?;
    }
    Ok(())
}
pub fn json_value(value: &serde_json::Value) -> Result<rusqlite::types::Value> {
    Ok(match value {
        serde_json::Value::Null => rusqlite::types::Value::Null,
        serde_json::Value::String(value) => rusqlite::types::Value::Text(value.clone()),
        serde_json::Value::Number(value) if value.is_i64() => {
            rusqlite::types::Value::Integer(value.as_i64().unwrap())
        }
        serde_json::Value::Number(value) => rusqlite::types::Value::Real(
            value
                .as_f64()
                .ok_or_else(|| fail("Invalid SQLite number"))?,
        ),
        _ => return Err(fail("Unsupported SQLite field value")),
    })
}
pub fn migrate(connection: &Connection, config: &Config) -> Result<()> {
    if current(connection)? {
        return Ok(());
    }
    savepoint(connection, "shared_resource_migration", || {
        for table in TABLES {
            connection.execute_batch(&ddl(table)?)?;
        }
        for table in ["context_documents", "local_resources", "external_resources"] {
            if exists(connection, table)? {
                for row in db::rows(
                    connection,
                    &format!("SELECT id FROM {table} ORDER BY id"),
                    [],
                )? {
                    let id = row["id"].as_i64().unwrap();
                    match table {
                        "context_documents" => {
                            resources::bind_document(connection, id, config)?;
                        }
                        "local_resources" => {
                            resources::bind_local_path(connection, id, config)?;
                        }
                        _ => {
                            resources::bind_external_link(connection, id)?;
                        }
                    }
                }
            }
        }
        for table in ["workstream_links", "thread_links"] {
            if !exists(connection, table)? {
                continue;
            }
            ensure(
                connection,
                table,
                "resource_id",
                "INTEGER REFERENCES reference_resources(id) ON DELETE RESTRICT",
            )?;
            for row in db::rows(
                connection,
                &format!("SELECT id,entity_type,entity_id FROM {table}"),
                [],
            )? {
                let entity = row["entity_id"]
                    .as_str()
                    .map(str::to_owned)
                    .unwrap_or_else(|| row["entity_id"].to_string());
                let resource = match resources::bind_entity(
                    connection,
                    row["entity_type"].as_str().unwrap_or(""),
                    &entity,
                    config,
                ) {
                    Ok(value) => value,
                    Err(error) if error.status == 400 || error.status == 404 => continue,
                    Err(error) => return Err(error),
                };
                connection.execute(
                    &format!("UPDATE {table} SET resource_id=? WHERE id=?"),
                    rusqlite::params![resource, row["id"].as_i64()],
                )?;
            }
        }
        evidence(connection, config)?;
        for (old, new) in PAYLOADS {
            payload(connection, old, new)?;
        }
        for table in TABLES.into_iter().chain([
            "session_reference_evidence",
            "external_resource_content",
            "external_resource_notes",
        ]) {
            if exists(connection, table)? {
                foreign_check(connection, Some(table))?;
            }
        }
        Ok(())
    })
}
fn relation_snapshot(
    connection: &Connection,
) -> Result<BTreeMap<String, Vec<Vec<rusqlite::types::Value>>>> {
    let mut result = BTreeMap::new();
    for table in [
        "workstream_links",
        "thread_links",
        "checkpoint_resource_refs",
    ] {
        if exists(connection, table)? {
            result.insert(
                table.into(),
                values(
                    connection,
                    &format!(
                        "SELECT * FROM {} WHERE entity_type='external' ORDER BY id",
                        quote(table)
                    ),
                )?,
            );
        }
    }
    Ok(result)
}
pub fn repair_external(connection: &Connection) -> Result<()> {
    if !exists(connection, "external_resources")?
        || !unique_columns(connection, "external_resources")?.contains(&vec!["url".into()])
    {
        return Ok(());
    }
    let reference = canonical()?;
    if info(connection, "external_resources")? != info(&reference, "external_resources")? {
        return Err(fail(
            "External Resource URL migration found an unexpected table shape",
        ));
    }
    if db::rows(connection, "PRAGMA index_list(external_resources)", [])?
        .iter()
        .any(|row| row["origin"] != "u")
    {
        return Err(fail(
            "External Resource URL migration found an unexpected explicit index",
        ));
    }
    if unique_columns(connection, "external_resources")? != vec![vec!["url".to_string()]] {
        return Err(fail(
            "External Resource URL migration found unexpected uniqueness",
        ));
    }
    triggers_absent(
        connection,
        "external_resources",
        "External Resource URL migration found an unexpected trigger",
    )?;
    let before = relation_snapshot(connection)?;
    rebuild(
        connection,
        "external_resources",
        "external_resources__url_scope_legacy",
        &ddl("external_resources")?,
        &columns(connection, "external_resources")?,
        false,
    )?;
    if before != relation_snapshot(connection)? {
        return Err(fail(
            "External Resource URL migration changed Resource relations",
        ));
    }
    if unique_columns(connection, "external_resources")?.contains(&vec!["url".into()]) {
        return Err(fail(
            "External Resource URL migration did not remove global uniqueness",
        ));
    }
    foreign_check(connection, None)
}
