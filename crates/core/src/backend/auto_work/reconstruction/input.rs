use super::super::common::*;
use super::{contract::*, sql};
use crate::backend::{db, references, usage, workflow, Result};
use chrono::{DateTime, Utc};
use rusqlite::{params, Connection, OptionalExtension};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
    time::Duration,
};
pub(super) fn format_sql(template: &str, values: &[&str]) -> String {
    values.iter().fold(template.to_owned(), |sql, value| {
        sql.replacen("{}", value, 1)
    })
}
pub(super) fn value_id(value: &Value) -> String {
    value
        .as_str()
        .map(str::to_owned)
        .unwrap_or_else(|| value.to_string())
}
fn ids(value: &Value, limit: usize) -> Result<()> {
    let rows = array(value, limit)?;
    let values = rows
        .iter()
        .map(|value| {
            int(value)
                .filter(|id| *id > 0)
                .ok_or_else(|| failure("INVALID_INPUT"))
        })
        .collect::<Result<BTreeSet<_>>>()?;
    require(values.len() == rows.len(), "INVALID_INPUT")
}
fn exact_keys(value: &Value, expected: &[&str]) -> Result<()> {
    keys(value, expected)?;
    require(
        value.as_object().unwrap().len() == expected.len(),
        "INVALID_INPUT",
    )
}
pub fn validate_manifest(value: &Value) -> Result<()> {
    exact_keys(
        value,
        &[
            "version",
            "source_ids",
            "start",
            "end",
            "snapshots",
            "owner",
            "expires_at",
        ],
    )?;
    require(
        value["version"] == 1 || value["version"] == true || value["version"].as_f64() == Some(1.0),
        "INVALID_INPUT",
    )?;
    ids(&value["source_ids"], 8)?;
    require(
        !value["source_ids"].as_array().unwrap().is_empty(),
        "INVALID_INPUT",
    )?;
    let start = utc(string(&value["start"])?)?;
    let end = utc(string(&value["end"])?)?;
    require(start <= end, "INVALID_INPUT")?;
    identifier(&value["owner"])?;
    timestamp(string(&value["expires_at"])?)?;
    let snapshots = array(&value["snapshots"], 12)?;
    require(!snapshots.is_empty(), "INVALID_INPUT")?;
    let mut names = BTreeSet::new();
    let mut previous = start;
    for scope in snapshots {
        keys(
            scope,
            &[
                "name",
                "as_of",
                "session_ids",
                "events",
                "documents",
                "items",
                "organization",
                "organization_links",
                "coverage",
            ],
        )?;
        require(
            scope.as_object().unwrap().len() == 8 + usize::from(scope.get("coverage").is_some()),
            "INVALID_INPUT",
        )?;
        if scope.get("coverage").is_some() {
            let coverage = &scope["coverage"];
            exact_keys(coverage, &["complete", "unexamined"])?;
            require(
                coverage["complete"].is_boolean()
                    && int(&coverage["unexamined"]).is_some_and(|n| n >= 0)
                    && (!coverage["complete"].as_bool().unwrap() || coverage["unexamined"] == 0),
                "INVALID_INPUT",
            )?;
        }
        let name = identifier(&scope["name"])?;
        require(names.insert(name), "INVALID_INPUT")?;
        let cutoff = utc(string(&scope["as_of"])?)?;
        require(previous <= cutoff && cutoff <= end, "INVALID_INPUT")?;
        previous = cutoff;
        ids(&scope["session_ids"], 60)?;
        for (field, count, limit) in [
            ("events", 12000, 4000),
            ("documents", 20, 8000),
            ("items", 20, 8000),
            ("organization", 20, 2000),
        ] {
            let mut seen = BTreeSet::new();
            for choice in array(&scope[field], count)? {
                keys(choice, &["id", "start", "end", "sha256", "table"])?;
                let id = value_id(&choice["id"]);
                let number = choice["id"].is_number()
                    && id
                        .trim_start_matches('-')
                        .bytes()
                        .all(|byte| byte.is_ascii_digit());
                require(
                    (choice["id"].is_string() || number)
                        && !id.is_empty()
                        && id.chars().count() <= 500,
                    "INVALID_INPUT",
                )?;
                let start = int(&choice["start"])
                    .filter(|n| *n >= 0)
                    .ok_or_else(|| failure("INVALID_INPUT"))?;
                let end = int(&choice["end"]).ok_or_else(|| failure("INVALID_INPUT"))?;
                require(start < end && end - start <= limit, "INPUT_LIMIT")?;
                let hash = string(&choice["sha256"])?;
                require(
                    hash.len() == 64
                        && hash
                            .bytes()
                            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)),
                    "INVALID_INPUT",
                )?;
                let table = choice["table"].as_str().unwrap_or(field);
                require(seen.insert((table.to_owned(), id)), "INVALID_INPUT")?;
                if field == "organization" {
                    require(
                        ["workstreams", "threads", "checkpoints"].contains(&table)
                            && choice.get("table").is_some(),
                        "INVALID_INPUT",
                    )?;
                } else {
                    require(choice.get("table").is_none(), "INVALID_INPUT")?;
                }
            }
        }
        ids(&scope["organization_links"], 200)?;
    }
    Ok(())
}
fn selected_text(
    connection: &Connection,
    table: &str,
    column: &str,
    identity: &str,
    choice: &Value,
) -> Result<String> {
    let id = usage::sql_value(&choice["id"])?;
    let size = connection
        .query_row(
            &format_sql(sql::INPUT_TEXT_0, &[column, table, identity]),
            [&id],
            |row| row.get::<_, Option<i64>>(0),
        )
        .optional()?
        .flatten();
    let end = int(&choice["end"]).unwrap();
    require(size.is_some_and(|size| end <= size), "SOURCE_CHANGED")?;
    let start = int(&choice["start"]).unwrap();
    let text = connection
        .query_row(
            &format_sql(sql::INPUT_TEXT_1, &[column, "?", table, identity]),
            params![start + 1, end - start, id],
            |row| row.get::<_, String>(0),
        )
        .optional()?
        .ok_or_else(|| failure("SOURCE_UNAVAILABLE"))?;
    require(sha(&text) == choice["sha256"], "SOURCE_CHANGED")?;
    Ok(text)
}
fn key(prefix: &str, values: Value) -> String {
    format!("{prefix}:{}", digest(&values))
}
fn record(choice: &Value, kind: &str, text: &str, at: &Value, role: &str, session: Value) -> Value {
    json!({"key":key("record",json!([choice["table"].as_str().unwrap_or(kind),value_id(&choice["id"])])),"kind":kind,"role":role,"session_id":session,"offset":choice["start"],"at":at,"text":text})
}
fn in_time(value: &Value, start: DateTime<Utc>, cutoff: DateTime<Utc>) -> Result<()> {
    let at = utc(value
        .as_str()
        .ok_or_else(|| failure("OUTSIDE_TIME_SCOPE"))?)?;
    require(start <= at && at <= cutoff, "OUTSIDE_TIME_SCOPE")
}
pub fn load_snapshots(database: &Path, manifest: &Value) -> Result<Vec<Value>> {
    validate_manifest(manifest)?;
    let source = read_only_database(database, Duration::from_secs(120))?;
    let mut results = Vec::new();
    for scope in manifest["snapshots"].as_array().unwrap() {
        let start = utc(string(&manifest["start"])?)?;
        let cutoff = utc(string(&scope["as_of"])?)?;
        let mut data = json!({"version":1,"name":scope["name"],"sessions":[],"records":[],"artifacts":[],"references":[],"organization_links":[],"coverage":scope.get("coverage").cloned().unwrap_or_else(||json!({"complete":true,"unexamined":0}))});
        for session in scope["session_ids"].as_array().unwrap() {
            let row = db::row(
                &source,
                sql::INPUT_LOAD_SNAPSHOTS_0,
                [int(session).unwrap()],
            )?
            .ok_or_else(|| failure("INELIGIBLE_SOURCE"))?;
            require(
                manifest["source_ids"]
                    .as_array()
                    .unwrap()
                    .contains(&row["source_id"])
                    && eligible(&row),
                "INELIGIBLE_SOURCE",
            )?;
            data["sessions"].as_array_mut().unwrap().push(row);
        }
        let mut chars: BTreeMap<i64, i64> = BTreeMap::new();
        let mut events: BTreeMap<i64, usize> = BTreeMap::new();
        for choice in scope["events"].as_array().unwrap() {
            let row = db::row(
                &source,
                sql::INPUT_LOAD_SNAPSHOTS_1,
                [usage::sql_value(&choice["id"])?],
            )?
            .ok_or_else(|| failure("INELIGIBLE_SOURCE"))?;
            require(
                scope["session_ids"]
                    .as_array()
                    .unwrap()
                    .contains(&row["session_id"])
                    && row["event_type"] == "message"
                    && ["user", "assistant"].contains(&string(&row["role"])?),
                "INELIGIBLE_SOURCE",
            )?;
            in_time(&row["occurred_at"], start, cutoff)?;
            let sid = int(&row["session_id"]).unwrap();
            *chars.entry(sid).or_default() +=
                int(&choice["end"]).unwrap() - int(&choice["start"]).unwrap();
            *events.entry(sid).or_default() += 1;
            require(chars[&sid] <= 32000 && events[&sid] <= 200, "INPUT_LIMIT")?;
            let text = selected_text(&source, "activity_events", "text", "id", choice)?;
            data["records"].as_array_mut().unwrap().push(record(
                choice,
                "session",
                &text,
                &row["occurred_at"],
                string(&row["role"])?,
                sid.into(),
            ));
        }
        for choice in scope["documents"].as_array().unwrap() {
            let row = db::row(
                &source,
                sql::INPUT_LOAD_SNAPSHOTS_2,
                [usage::sql_value(&choice["id"])?],
            )?
            .ok_or_else(|| failure("INELIGIBLE_SOURCE"))?;
            require(
                row["enabled"] == 1 && row["readable"] == 1 && row["status"] == "ready",
                "INELIGIBLE_SOURCE",
            )?;
            in_time(&row["imported_at"], start, cutoff)?;
            let text = selected_text(&source, "context_documents", "body", "id", choice)?;
            data["records"].as_array_mut().unwrap().push(record(
                choice,
                "document",
                &text,
                &row["imported_at"],
                "document",
                Value::Null,
            ));
        }
        for choice in scope["items"].as_array().unwrap() {
            let row = db::row(
                &source,
                sql::INPUT_LOAD_SNAPSHOTS_3,
                [usage::sql_value(&choice["id"])?],
            )?
            .ok_or_else(|| failure("INELIGIBLE_SOURCE"))?;
            require(
                row["coverage"] == "indexed"
                    && (row["source_instance_id"].is_null() || row["enabled"] == 1),
                "INELIGIBLE_SOURCE",
            )?;
            in_time(&row["applied_at"], start, cutoff)?;
            let text = selected_text(
                &source,
                "external_resource_content",
                "normalized_text",
                "external_resource_id",
                choice,
            )?;
            data["records"].as_array_mut().unwrap().push(record(
                choice,
                "item",
                &text,
                &row["applied_at"],
                "document",
                Value::Null,
            ));
        }
        let mut workstreams = BTreeSet::new();
        for choice in scope["organization"].as_array().unwrap() {
            let table = string(&choice["table"])?;
            let column = if table == "workstreams" {
                "summary"
            } else {
                "current_goal"
            };
            let owner = if table == "workstreams" {
                "id"
            } else {
                "workstream_id"
            };
            let row = db::row(
                &source,
                &format_sql(sql::INPUT_LOAD_SNAPSHOTS_4, &[owner, table]),
                [usage::sql_value(&choice["id"])?],
            )?
            .ok_or_else(|| failure("SOURCE_UNAVAILABLE"))?;
            in_time(&row["updated_at"], start, cutoff)?;
            workstreams.insert(int(&row["owner"]).unwrap());
            let text = selected_text(&source, table, column, "id", choice)?;
            data["records"].as_array_mut().unwrap().push(record(
                choice,
                "organization",
                &text,
                &row["updated_at"],
                "owner",
                Value::Null,
            ));
        }
        for link in scope["organization_links"].as_array().unwrap() {
            let row = db::row(&source, sql::INPUT_LOAD_SNAPSHOTS_5, [int(link).unwrap()])?
                .ok_or_else(|| failure("INELIGIBLE_SOURCE"))?;
            require(
                workstreams.contains(&int(&row["workstream_id"]).unwrap())
                    && row["linked_by"] == "user"
                    && row["entity_type"] == "session"
                    && scope["session_ids"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .any(|sid| value_id(sid) == value_id(&row["entity_id"])),
                "INELIGIBLE_SOURCE",
            )?;
            in_time(&row["created_at"], start, cutoff)?;
            data["organization_links"].as_array_mut().unwrap().push(json!({"key":key("owner-link",json!([link])),"session_id":value_id(&row["entity_id"]).parse::<i64>().map_err(|_|failure("INVALID_INPUT"))?,"authority":"owner"}));
        }
        collect_references(&source, &mut data, scope, start, cutoff)?;
        validate_snapshot(&data)?;
        results.push(data);
    }
    Ok(results)
}
fn incomplete(data: &mut Value) {
    data["coverage"]["complete"] = false.into();
    data["coverage"]["unexamined"] = (data["coverage"]["unexamined"].as_i64().unwrap() + 1).into();
}
fn canonical_reference(
    connection: &Connection,
    row: &Value,
) -> Result<Option<(String, String, String)>> {
    match row["target_kind"].as_str().unwrap_or_default() {
        "context_document" => {
            if let Some(document) = db::row(
                connection,
                sql::INPUT_CANONICAL_REFERENCE_0,
                [usage::sql_value(&row["context_document_id"])?],
            )? {
                if let Some(path) = document["relative_path"].as_str().filter(|v| !v.is_empty()) {
                    return Ok(Some((
                        "context-document".into(),
                        key(
                            "source-scope",
                            json!([document["source_id"], document["path"]]),
                        ),
                        path.into(),
                    )));
                }
            }
        }
        "atlassian_item" => {
            if let Some(item) = db::row(
                connection,
                sql::INPUT_CANONICAL_REFERENCE_1,
                [usage::sql_value(&row["external_resource_id"])?],
            )? {
                let jira = item["service"] == "jira";
                let identity = if jira {
                    &item["remote_key"]
                } else {
                    &item["remote_id"]
                };
                if let Some(identity) = identity.as_str().filter(|v| !v.is_empty()) {
                    return Ok(Some((
                        if jira { "jira-item" } else { "wiki-item" }.into(),
                        key(
                            "source-scope",
                            json!([item["service"], item["normalized_domain"]]),
                        ),
                        identity.into(),
                    )));
                }
            }
        }
        "url" => {
            if let Some(url) = row["normalized_url"].as_str().filter(|url| !url.is_empty()) {
                if references::external_href(url).is_some() {
                    return Ok(Some((
                        "external-resource".into(),
                        "persisted-normalized-url".into(),
                        url.into(),
                    )));
                }
            }
        }
        _ => {}
    }
    Ok(None)
}
fn collect_references(
    connection: &Connection,
    data: &mut Value,
    scope: &Value,
    start: DateTime<Utc>,
    cutoff: DateTime<Utc>,
) -> Result<()> {
    let mut artifacts = BTreeMap::new();
    let document_ids = scope["documents"]
        .as_array()
        .unwrap()
        .iter()
        .map(|choice| value_id(&choice["id"]))
        .collect::<BTreeSet<_>>();
    let item_ids = scope["items"]
        .as_array()
        .unwrap()
        .iter()
        .map(|choice| value_id(&choice["id"]))
        .collect::<BTreeSet<_>>();
    let mut scanned = 0;
    for session in data["sessions"].as_array().unwrap().clone() {
        let scan = db::row(
            connection,
            sql::INPUT_REFERENCES_0,
            [int(&session["id"]).unwrap()],
        )?;
        if scan.as_ref().is_none_or(|row| row["status"] != "ok") {
            incomplete(data);
        }
        let rows = db::rows(
            connection,
            sql::INPUT_REFERENCES_1,
            params![int(&session["id"]).unwrap(), 12001 - scanned],
        )?;
        scanned += rows.len();
        require(scanned <= 12000, "INPUT_LIMIT")?;
        for row in rows {
            if row["observed_at"].is_null() {
                incomplete(data);
                continue;
            }
            let at = utc(string(&row["observed_at"])?)?;
            if at < start || at > cutoff {
                continue;
            }
            if row["target_kind"] == "context_document"
                && !document_ids.contains(&value_id(&row["context_document_id"]))
                || row["target_kind"] == "atlassian_item"
                    && !item_ids.contains(&value_id(&row["external_resource_id"]))
            {
                continue;
            }
            let Some((kind, source_scope, identity)) = canonical_reference(connection, &row)?
            else {
                incomplete(data);
                continue;
            };
            let artifact =
                workflow::candidates::candidate_artifact_key(&kind, &source_scope, &identity)?;
            artifacts.insert(artifact.clone(),json!({"kind":kind,"source_scope":source_scope,"source_identity":identity,"identity_state":"resolved","enabled":true,"is_container":false,"availability":"available","freshness":"unknown"}));
            data["references"].as_array_mut().unwrap().push(json!({"episode_key":workflow::projection::workflow_episode_key(int(&session["source_id"]).unwrap(),string(&session["external_id"])?)?,"artifact_key":artifact,"reference_identity":value_id(&row["id"]),"evidence_kind":row["evidence_kind"],"read_outcome":row["read_outcome"],"observed_at":row["observed_at"]}));
        }
    }
    data["artifacts"] = artifacts.into_values().collect::<Vec<_>>().into();
    Ok(())
}
