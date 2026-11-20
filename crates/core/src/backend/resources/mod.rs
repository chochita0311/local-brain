//! Stable reference resources; bindings retain the original row identity.
use crate::backend::{db, references, BackendError, Config, Result};
use rusqlite::Connection;
use sha2::{Digest, Sha256};
use std::path::Path;
fn upsert(
    connection: &Connection,
    key: &str,
    kind: &str,
    locator: &str,
    product: Option<&str>,
    remote: Option<&str>,
) -> Result<i64> {
    connection.execute("INSERT INTO reference_resources(identity_key,kind,locator,product,remote_key) VALUES (?,?,?,?,?) ON CONFLICT(identity_key) DO NOTHING",rusqlite::params![key,kind,locator,product,remote])?;
    Ok(connection.query_row(
        "SELECT id FROM reference_resources WHERE identity_key=?",
        [key],
        |row| row.get(0),
    )?)
}
pub fn url_resource(connection: &Connection, value: &str) -> Result<Option<i64>> {
    references::parse_url(value)
        .map(|parsed| parsed_url_resource(connection, &parsed))
        .transpose()
}
pub fn parsed_url_resource(connection: &Connection, parsed: &references::ParsedUrl) -> Result<i64> {
    let locator = parsed.locator.as_ref();
    upsert(
        connection,
        &parsed.target_key,
        "url",
        &parsed.normalized_url,
        locator.and_then(|locator| locator.service.as_deref()),
        locator
            .filter(|locator| locator.kind == "item")
            .and_then(|locator| locator.item_identity.as_deref()),
    )
}
pub fn path_resource(connection: &Connection, value: &str, config: &Config) -> Result<i64> {
    let kind = if value.starts_with("apple-notes:") {
        "note"
    } else {
        "path"
    };
    let locator = if kind == "note" {
        value.into()
    } else {
        let expanded = crate::backend::storage::files::expand(Path::new(value), config);
        crate::backend::storage::files::lexical_absolute(&expanded)?
            .to_str()
            .ok_or_else(|| BackendError::invalid("resource", "Path is not valid UTF-8"))?
            .to_string()
    };
    let key = format!("{kind}:{:x}", Sha256::digest(locator.as_bytes()));
    upsert(connection, &key, kind, &locator, None, None)
}
fn path_binding(
    connection: &Connection,
    table: &str,
    binding: &str,
    key: &str,
    id: i64,
    config: &Config,
) -> Result<i64> {
    let row = db::row(
        connection,
        &format!("SELECT path FROM {table} WHERE id=?"),
        [id],
    )?
    .ok_or_else(|| BackendError::not_found("Local resource not found"))?;
    let resource = path_resource(connection, row["path"].as_str().unwrap_or(""), config)?;
    connection.execute(&format!("INSERT INTO {binding}({key},resource_id) VALUES (?,?) ON CONFLICT({key}) DO UPDATE SET resource_id=excluded.resource_id"),[id,resource])?;
    Ok(resource)
}
pub fn bind_document(connection: &Connection, id: i64, config: &Config) -> Result<i64> {
    path_binding(
        connection,
        "context_documents",
        "resource_documents",
        "document_id",
        id,
        config,
    )
}
pub fn bind_local_path(connection: &Connection, id: i64, config: &Config) -> Result<i64> {
    path_binding(
        connection,
        "local_resources",
        "resource_local_paths",
        "local_resource_id",
        id,
        config,
    )
}
pub fn bind_external_link(connection: &Connection, id: i64) -> Result<Option<i64>> {
    let row = db::row(
        connection,
        "SELECT url FROM external_resources WHERE id=?",
        [id],
    )?
    .ok_or_else(|| BackendError::not_found("External resource not found"))?;
    let resource = url_resource(connection, row["url"].as_str().unwrap_or(""))?;
    if let Some(resource) = resource {
        connection.execute("INSERT INTO resource_external_links(external_resource_id,resource_id) VALUES (?,?) ON CONFLICT(external_resource_id) DO UPDATE SET resource_id=excluded.resource_id",[id,resource])?;
    } else {
        connection.execute(
            "DELETE FROM resource_external_links WHERE external_resource_id=?",
            [id],
        )?;
    }
    Ok(resource)
}
pub fn bind_entity(
    connection: &Connection,
    kind: &str,
    id: &str,
    config: &Config,
) -> Result<Option<i64>> {
    if !["document", "local", "external"].contains(&kind) {
        return Ok(None);
    }
    let id = id
        .parse::<i64>()
        .map_err(|_| BackendError::invalid("resource", "Invalid resource ID"))?;
    match kind {
        "document" => bind_document(connection, id, config).map(Some),
        "local" => bind_local_path(connection, id, config).map(Some),
        _ => bind_external_link(connection, id),
    }
}
pub fn resource_by_hint(
    connection: &Connection,
    kind: &str,
    value: &str,
) -> Result<Option<serde_json::Value>> {
    let product = match kind {
        "jira_key" => "jira",
        "confluence_page_id" => "confluence",
        _ => return Ok(None),
    };
    let mut rows=db::rows(connection,"SELECT * FROM reference_resources WHERE kind='url' AND product=? AND UPPER(remote_key)=UPPER(?) ORDER BY id LIMIT 2",[product,value])?;
    Ok((rows.len() == 1).then(|| rows.remove(0)))
}
pub mod related_context;
pub mod store;
pub use store::{create_external_resource, create_local_resource, local_resource_detail};
