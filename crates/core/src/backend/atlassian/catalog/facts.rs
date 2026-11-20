use super::super::common::*;
use super::{
    content::{self, SOURCE_FORMATS},
    projection, store, FAILURES, METADATA_SCHEMA, NORMALIZER_VERSION, SERVICES, SUCCESS,
};
use crate::backend::{clock, db, Result};
use chrono::{DateTime, Utc};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub(super) fn parse_time(value: &Value) -> Result<Option<DateTime<Utc>>> {
    if !truth(value) {
        return Ok(None);
    }
    let value = value
        .as_str()
        .ok_or_else(|| fail("invalid-timestamp", "Timestamp must be ISO-8601"))?;
    clock::parse_timestamp(value)
        .map(Some)
        .ok_or_else(|| fail("invalid-timestamp", "Timestamp must be ISO-8601"))
}
pub fn derive_atlassian_freshness(
    service: &str,
    state: Option<&Value>,
    at: Option<DateTime<Utc>>,
) -> Result<String> {
    if !SERVICES.contains(&service) {
        return Err(fail("invalid-service", "Unsupported Atlassian service"));
    }
    let empty = json!({});
    let state = state.unwrap_or(&empty);
    if state["last_outcome"]
        .as_str()
        .is_some_and(|s| FAILURES.contains(&s))
    {
        return Ok("unavailable".into());
    }
    if truth(&state["known_changed"]) || truth(&state["projection_stale"]) {
        return Ok("stale".into());
    }
    let Some(last) = parse_time(&state["last_successful_at"])? else {
        return Ok("unknown".into());
    };
    let interval = chrono::Duration::days(if service == "jira" { 7 } else { 30 });
    Ok(if at.unwrap_or_else(Utc::now) - last >= interval {
        "due"
    } else {
        "current"
    }
    .into())
}
pub fn atlassian_item_state(
    connection: &Connection,
    resource: i64,
    at: Option<DateTime<Utc>>,
) -> Result<Value> {
    let mut item = store::item_row(connection, resource)?;
    let remote = db::row(
        connection,
        "SELECT * FROM atlassian_item_remote_state WHERE external_resource_id=?",
        [resource],
    )?;
    item["freshness"] = json!(derive_atlassian_freshness(
        item["service"].as_str().unwrap_or(""),
        remote.as_ref(),
        at
    )?);
    item["remote_state"] = json!(remote);
    item["urls"] = json!(db::rows(
        connection,
        "SELECT * FROM atlassian_item_urls WHERE external_resource_id=? ORDER BY url_role DESC,id",
        [resource]
    )?);
    Ok(item)
}
fn single_fact(requests: &[Value], key: &str) -> Result<Option<Value>> {
    let mut fingerprints = BTreeSet::new();
    let mut result = None;
    for request in requests {
        if !request.is_object() {
            return Err(fail(
                "invalid-provider-result",
                "Validated request result must be an object",
            ));
        }
        let value = &request[key];
        if value.is_null() || value.as_object().is_some_and(|v| v.is_empty()) {
            continue;
        }
        let fingerprint = json_size(value, key, 2_000_000, "invalid-input")?;
        if fingerprints.insert(fingerprint) {
            if result.is_some() {
                return Err(fail(
                    "conflicting-provider-facts",
                    format!("Validated requests returned conflicting {key}"),
                ));
            }
            result = Some(value.clone());
        }
    }
    Ok(result)
}
const FORBIDDEN: &[&str] = &[
    "body",
    "content",
    "description",
    "renderedbody",
    "rendered_body",
];
fn validate_metadata(root: &Value) -> Result<()> {
    enum Task<'a> {
        Value(&'a Value, usize),
        Field(&'a str, &'a Value, usize),
    }
    let mut pending = vec![Task::Value(root, 0)];
    while let Some(task) = pending.pop() {
        let (value, depth) = match task {
            Task::Value(value, depth) => (value, depth),
            Task::Field(key, value, depth) => {
                if FORBIDDEN.contains(&crate::backend::unicode::lowercase(trim(key)).as_str()) {
                    return Err(fail(
                        "remote-content-in-metadata",
                        "Remote body content cannot be stored as metadata",
                    ));
                }
                pending.push(Task::Value(value, depth + 1));
                continue;
            }
        };
        if depth > 20 {
            return Err(fail(
                "invalid-provider-result",
                "Remote metadata nesting is too deep",
            ));
        }
        match value {
            Value::Object(values) => {
                for (key, child) in values.iter().rev() {
                    pending.push(Task::Field(key, child, depth));
                }
            }
            Value::Array(values) => {
                pending.extend(values.iter().rev().map(|v| Task::Value(v, depth + 1)))
            }
            _ => {}
        }
    }
    Ok(())
}
fn metadata(requests: &[Value]) -> Result<Value> {
    let mut merged = json!({});
    let mut fingerprints = BTreeMap::new();
    for request in requests {
        let empty = json!({});
        let metadata = if truth(&request["metadata"]) {
            &request["metadata"]
        } else {
            &empty
        };
        let values = metadata.as_object().ok_or_else(|| {
            fail(
                "invalid-provider-result",
                "Remote metadata must be an object",
            )
        })?;
        if values.len() > 100 {
            return Err(fail(
                "invalid-provider-result",
                "Remote metadata is not bounded",
            ));
        }
        for (raw, value) in values {
            let key = trim(raw);
            if key.is_empty() {
                return Err(fail(
                    "invalid-provider-result",
                    "Remote metadata field names must be text",
                ));
            }
            if key.chars().count() > 120 {
                return Err(fail(
                    "invalid-provider-result",
                    "Remote metadata field name is too long",
                ));
            }
            if FORBIDDEN.contains(&crate::backend::unicode::lowercase(key).as_str()) {
                return Err(fail(
                    "remote-content-in-metadata",
                    "Remote body content cannot be stored as metadata",
                ));
            }
            validate_metadata(value)?;
            let fingerprint = json_size(value, "metadata field", 100_000, "invalid-input")?;
            if fingerprints.get(key).is_some_and(|v| v != &fingerprint) {
                return Err(fail(
                    "conflicting-provider-facts",
                    "Validated requests returned conflicting metadata",
                ));
            }
            fingerprints.insert(key.to_owned(), fingerprint);
            merged[key] = value.clone();
        }
    }
    json_size(&merged, "remote metadata", 500_000, "invalid-input")?;
    Ok(merged)
}
fn identity(requests: &[Value]) -> Result<Value> {
    let mut merged = json!({});
    for request in requests {
        if !request.is_object() {
            return Err(fail(
                "invalid-provider-result",
                "Validated request result must be an object",
            ));
        }
        let empty = json!({});
        let identity = if truth(&request["identity"]) {
            &request["identity"]
        } else {
            &empty
        };
        let values = identity.as_object().ok_or_else(|| {
            fail(
                "invalid-provider-result",
                "Remote identity must be an object",
            )
        })?;
        if values
            .keys()
            .any(|key| !["remote_id", "remote_key", "canonical_url"].contains(&key.as_str()))
        {
            return Err(fail(
                "invalid-provider-result",
                "Remote identity contains unsupported fields",
            ));
        }
        for (key, value) in values {
            if merged.get(key).is_some_and(|v| v != value) {
                return Err(fail(
                    "conflicting-provider-facts",
                    "Validated requests returned conflicting identity",
                ));
            }
            merged[key] = value.clone();
        }
    }
    Ok(merged)
}
fn content_fact(
    service: &str,
    requests: &[Value],
    explicit: Option<&str>,
) -> Result<Option<(String, Value)>> {
    let Some(mut body) = single_fact(requests, "content")? else {
        return Ok(None);
    };
    let mut format = explicit.map(ToOwned::to_owned);
    if body
        .as_object()
        .is_some_and(|m| m.len() == 2 && m.contains_key("format") && m.contains_key("body"))
    {
        let inferred = match body["format"].as_str().unwrap_or("") {
            "jira_adf" => "jira_adf",
            "confluence_adf" => "confluence_adf",
            "adf" | "atlas_doc_format" => {
                if service == "jira" {
                    "jira_adf"
                } else {
                    "confluence_adf"
                }
            }
            "storage" | "html" => "confluence_html",
            "markdown" => "confluence_markdown",
            "plain_text" | "text" => "plain_text",
            _ => {
                return Err(fail(
                    "unsupported-content-format",
                    "Provider content format is unsupported",
                ))
            }
        };
        if format.as_ref().is_some_and(|f| f != inferred) {
            return Err(fail(
                "content-format-mismatch",
                "Explicit and provider content formats do not match",
            ));
        }
        format = Some(inferred.into());
        body = body["body"].clone();
    }
    let format = match format {
        Some(format) => format,
        None if body.is_object() => {
            if service == "jira" {
                "jira_adf".into()
            } else {
                "confluence_adf".into()
            }
        }
        None if body.is_string() => "plain_text".into(),
        None => {
            return Err(fail(
                "invalid-content",
                "Provider content must be text or ADF",
            ))
        }
    };
    if !SOURCE_FORMATS.contains(&format.as_str()) {
        return Err(fail(
            "unsupported-content-format",
            "Unsupported Atlassian content format",
        ));
    }
    if service == "jira" && !["jira_adf", "plain_text"].contains(&format.as_str()) {
        return Err(fail(
            "content-format-mismatch",
            "Jira content format is invalid",
        ));
    }
    if service == "confluence" && format == "jira_adf" {
        return Err(fail(
            "content-format-mismatch",
            "Confluence content format is invalid",
        ));
    }
    Ok(Some((format, body)))
}
fn versions(requests: &[Value]) -> Result<(Option<String>, Option<String>)> {
    let version = single_fact(requests, "remote_version")?
        .map(|value| text(&value, "remote_version", 300, "invalid-input"))
        .transpose()?;
    let updated = single_fact(requests, "remote_updated_at")?
        .map(|value| text(&value, "remote_updated_at", 100, "invalid-input"))
        .transpose()?;
    if let Some(value) = updated.as_ref() {
        parse_time(&json!(value))?;
    }
    Ok((version, updated))
}
struct RemoteUpdate<'a> {
    metadata: Option<&'a Value>,
    version: Option<&'a str>,
    updated: Option<&'a str>,
    attempt: &'a str,
    outcome: &'a str,
    error: Option<&'a str>,
    changed: Option<bool>,
    stale: Option<bool>,
}
fn upsert_remote(connection: &Connection, resource: i64, update: RemoteUpdate<'_>) -> Result<()> {
    let old=db::row(connection,"SELECT metadata_json,last_successful_at,last_confirmed_at,known_changed,projection_stale FROM atlassian_item_remote_state WHERE external_resource_id=?",[resource])?;
    let mut metadata = if let Some(old) = &old {
        let value = old["metadata_json"]
            .as_str()
            .and_then(|s| decode_json(s).ok())
            .ok_or_else(|| {
                fail(
                    "invalid-stored-state",
                    "Stored Atlassian metadata is invalid",
                )
            })?;
        if !value.is_object() {
            return Err(fail(
                "invalid-stored-state",
                "Stored Atlassian metadata must be an object",
            ));
        }
        value
    } else {
        json!({})
    };
    if let Some(values) = update.metadata {
        for (key, value) in values.as_object().unwrap() {
            metadata[key] = value.clone();
        }
    }
    let metadata = json_size(&metadata, "remote metadata", 500_000, "invalid-input")?;
    let successful = SUCCESS.contains(&update.outcome);
    let successful_at = if successful {
        Some(update.attempt)
    } else {
        old.as_ref().and_then(|v| v["last_successful_at"].as_str())
    };
    let confirmed_at = if successful {
        Some(update.attempt)
    } else {
        old.as_ref().and_then(|v| v["last_confirmed_at"].as_str())
    };
    let changed = update
        .changed
        .unwrap_or_else(|| old.as_ref().is_some_and(|v| truth(&v["known_changed"])));
    let stale = update
        .stale
        .unwrap_or_else(|| old.as_ref().is_some_and(|v| truth(&v["projection_stale"])));
    connection.execute("INSERT INTO atlassian_item_remote_state(external_resource_id,metadata_schema_version,metadata_json,remote_version,remote_updated_at,last_attempted_at,last_successful_at,last_confirmed_at,last_outcome,last_error_code,known_changed,projection_stale,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(external_resource_id) DO UPDATE SET metadata_schema_version=excluded.metadata_schema_version,metadata_json=excluded.metadata_json,remote_version=COALESCE(excluded.remote_version,atlassian_item_remote_state.remote_version),remote_updated_at=COALESCE(excluded.remote_updated_at,atlassian_item_remote_state.remote_updated_at),last_attempted_at=excluded.last_attempted_at,last_successful_at=excluded.last_successful_at,last_confirmed_at=excluded.last_confirmed_at,last_outcome=excluded.last_outcome,last_error_code=excluded.last_error_code,known_changed=excluded.known_changed,projection_stale=excluded.projection_stale,updated_at=excluded.updated_at",params![resource,METADATA_SCHEMA,metadata,update.version,update.updated,update.attempt,successful_at,confirmed_at,update.outcome,update.error,changed,stale,update.attempt])?;
    Ok(())
}
pub fn apply_atlassian_target_result(
    connection: &Connection,
    resource: i64,
    target: &Value,
    checked_at: Option<&str>,
    source_format: Option<&str>,
) -> Result<Value> {
    let item = store::item_row(connection, resource)?;
    let object = target
        .as_object()
        .ok_or_else(|| fail("invalid-provider-result", "Target result must be an object"))?;
    if object
        .keys()
        .any(|key| !["target_id", "locator", "outcome", "requests"].contains(&key.as_str()))
    {
        return Err(fail(
            "invalid-provider-result",
            "Target result contains unsupported fields",
        ));
    }
    let outcome = target["outcome"]
        .as_str()
        .filter(|s| SUCCESS.contains(s) || FAILURES.contains(s))
        .ok_or_else(|| fail("invalid-provider-result", "Target outcome is unsupported"))?;
    let requests = target["requests"]
        .as_array()
        .filter(|a| !a.is_empty())
        .ok_or_else(|| {
            fail(
                "invalid-provider-result",
                "Target result requires validated request results",
            )
        })?;
    let attempt = checked_at
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
        .unwrap_or_else(now);
    parse_time(&json!(attempt))?;
    let failure_state = atomic(connection, "atlassian_target_application", || {
        if FAILURES.contains(&outcome) {
            let mut codes = BTreeSet::new();
            for request in requests {
                if request.is_object()
                    && request["error"].is_object()
                    && truth(&request["error"]["code"])
                {
                    let code = request["error"]["code"].as_str().ok_or_else(|| {
                        fail(
                            "invalid-provider-result",
                            "Provider error code must be text",
                        )
                    })?;
                    codes.insert(code.to_owned());
                }
            }
            let error = codes
                .first()
                .map(String::as_str)
                .unwrap_or(outcome)
                .chars()
                .take(80)
                .collect::<String>();
            upsert_remote(
                connection,
                resource,
                RemoteUpdate {
                    metadata: None,
                    version: None,
                    updated: None,
                    attempt: &attempt,
                    outcome,
                    error: Some(&error),
                    changed: None,
                    stale: None,
                },
            )?;
            return atlassian_item_state(connection, resource, None).map(Some);
        }
        let identity = identity(requests)?;
        if item["remote_id"].is_null() && identity["remote_id"].is_null() {
            return Err(fail(
                "missing-remote-identity",
                "A successful first check requires a remote ID",
            ));
        }
        if !identity["remote_id"].is_null() {
            let mut values = identity.clone();
            values["confirmed_at"] = json!(attempt);
            store::bind_atlassian_remote_identity(connection, resource, &values)?;
        } else if !identity["remote_key"].is_null() || !identity["canonical_url"].is_null() {
            return Err(fail(
                "incomplete-remote-identity",
                "Remote identity details require a remote ID",
            ));
        }
        let metadata = metadata(requests)?;
        let metadata_update = metadata
            .as_object()
            .filter(|m| !m.is_empty())
            .map(|_| &metadata);
        let (version, updated) = versions(requests)?;
        let content = content_fact(
            item["service"].as_str().unwrap_or(""),
            requests,
            source_format,
        )?;
        if item["coverage"] == "reference" && metadata_update.is_some() {
            return Err(fail(
                "coverage-mismatch",
                "Reference coverage cannot store remote metadata",
            ));
        }
        if item["coverage"] != "indexed" && content.is_some() {
            return Err(fail(
                "coverage-mismatch",
                "Only indexed coverage can store remote content",
            ));
        }
        let mut content_changed = false;
        if let Some((format, body)) = &content {
            let normalized = content::normalize_atlassian_content(format, body)?;
            let old=db::row(connection,"SELECT source_hash,normalizer_version FROM external_resource_content WHERE external_resource_id=?",[resource])?;
            if old.as_ref().is_none_or(|old| {
                old["source_hash"] != normalized.source_hash
                    || old["normalizer_version"] != NORMALIZER_VERSION
            }) {
                connection.execute("INSERT INTO external_resource_content(external_resource_id,source_format,source_body,source_hash,normalized_document_json,normalized_text,normalizer_version,normalization_warning,remote_version,remote_updated_at,applied_at,search_projection_hash,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,NULL,?) ON CONFLICT(external_resource_id) DO UPDATE SET source_format=excluded.source_format,source_body=excluded.source_body,source_hash=excluded.source_hash,normalized_document_json=excluded.normalized_document_json,normalized_text=excluded.normalized_text,normalizer_version=excluded.normalizer_version,normalization_warning=excluded.normalization_warning,remote_version=excluded.remote_version,remote_updated_at=excluded.remote_updated_at,applied_at=excluded.applied_at,search_projection_hash=NULL,updated_at=excluded.updated_at",params![resource,normalized.source_format,normalized.source_body,normalized.source_hash,normalized.normalized_document_json,normalized.normalized_text,NORMALIZER_VERSION,normalized.warning,version,updated,attempt,attempt])?;
                content_changed = true;
            }
        }
        let content_exists = db::row(
            connection,
            "SELECT 1 FROM external_resource_content WHERE external_resource_id=?",
            [resource],
        )?
        .is_some();
        let indexed = item["coverage"] == "indexed";
        upsert_remote(
            connection,
            resource,
            RemoteUpdate {
                metadata: metadata_update,
                version: version.as_deref(),
                updated: updated.as_deref(),
                attempt: &attempt,
                outcome,
                error: None,
                changed: Some(outcome == "changed" && indexed && content.is_none()),
                stale: Some(indexed && !content_exists),
            },
        )?;
        if content_changed || metadata_update.is_some() || indexed && content_exists {
            projection::project_internal(connection, resource, &attempt)?;
        }
        Ok(None)
    })?;
    if let Some(state) = failure_state {
        return Ok(state);
    }
    atlassian_item_state(connection, resource, None)
}
