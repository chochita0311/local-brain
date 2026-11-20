use super::{super::common::*, store};
use crate::backend::{db, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

pub(super) fn canonical_item_url(connection: &Connection, resource: i64) -> Result<String> {
    Ok(db::row(connection,"SELECT normalized_url FROM atlassian_item_urls WHERE external_resource_id=? AND url_role='canonical'",[resource])?.and_then(|r|r["normalized_url"].as_str().map(ToOwned::to_owned)).unwrap_or_default())
}
fn flatten(value: &Value, prefix: &str, out: &mut Vec<String>) {
    match value {
        Value::Object(values) => {
            let mut keys: Vec<_> = values.keys().collect();
            keys.sort();
            for key in keys {
                let prefix = if prefix.is_empty() {
                    key.clone()
                } else {
                    format!("{prefix}.{key}")
                };
                flatten(&values[key], &prefix, out);
            }
        }
        Value::Array(values) => {
            for value in values {
                flatten(value, prefix, out);
            }
        }
        Value::Null => {}
        value => {
            let text = python_string(value);
            let text = trim(&text);
            if !text.is_empty() {
                out.push(if prefix.is_empty() {
                    text.into()
                } else {
                    format!("{prefix}: {text}")
                });
            }
        }
    }
}
fn chosen(values: &[&Value]) -> String {
    values
        .iter()
        .find(|value| truth(value))
        .map(|value| python_string(value))
        .unwrap_or_default()
}
pub(super) fn projection_values(connection: &Connection, resource: i64) -> Result<Vec<Value>> {
    let row=db::row(connection,"SELECT atlassian_items.service,atlassian_items.coverage,atlassian_items.remote_key,external_resources.title AS local_title,atlassian_item_remote_state.metadata_json,external_resource_content.normalized_text,external_resource_notes.note FROM atlassian_items JOIN external_resources ON external_resources.id=atlassian_items.external_resource_id LEFT JOIN atlassian_item_remote_state ON atlassian_item_remote_state.external_resource_id=atlassian_items.external_resource_id LEFT JOIN external_resource_content ON external_resource_content.external_resource_id=atlassian_items.external_resource_id LEFT JOIN external_resource_notes ON external_resource_notes.external_resource_id=atlassian_items.external_resource_id WHERE atlassian_items.external_resource_id=?",[resource])?;
    let Some(row) = row else { return Ok(vec![]) };
    let metadata = row["metadata_json"]
        .as_str()
        .filter(|s| !s.is_empty())
        .and_then(|s| decode_json(s).ok())
        .unwrap_or(json!({}));
    if !metadata.is_object() {
        return Err(fail(
            "invalid-stored-state",
            "Stored Atlassian metadata must be an object",
        ));
    }
    let remote_title = chosen(&[
        &metadata["title"],
        &metadata["summary"],
        &row["local_title"],
    ]);
    let local_title = chosen(&[&row["local_title"], &json!(remote_title)]);
    let canonical = canonical_item_url(connection, resource)?;
    let service = row["service"].as_str().unwrap_or("");
    let body = [
        row["remote_key"].as_str().filter(|s| !s.is_empty()),
        (!canonical.is_empty()).then_some(canonical.as_str()),
    ]
    .into_iter()
    .flatten()
    .collect::<Vec<_>>()
    .join("\n");
    let base =
        json!({"entity_type":"atlassian_item","entity_id":resource.to_string(),"path":canonical});
    let mut values = vec![];
    let mut role = |kind: String, title: String, body: String| {
        let mut value = base.clone();
        value["source_kind"] = json!(kind);
        value["title"] = json!(title);
        value["body"] = json!(body);
        values.push(value);
    };
    role(
        format!("atlassian:{service}:identity"),
        local_title.clone(),
        body,
    );
    let mut metadata_parts = vec![];
    flatten(&metadata, "", &mut metadata_parts);
    let metadata_text = metadata_parts.join("\n");
    if !metadata_text.is_empty() {
        role(
            format!("atlassian:{service}:metadata"),
            remote_title.clone(),
            metadata_text,
        );
    }
    if row["coverage"] == "indexed" && truth(&row["normalized_text"]) {
        role(
            format!("atlassian:{service}:content"),
            remote_title.clone(),
            python_string(&row["normalized_text"]),
        );
    }
    let classifications=db::rows(connection,"SELECT atlassian_classifications.kind,atlassian_classifications.name,atlassian_classifications.description FROM atlassian_item_classifications JOIN atlassian_classifications ON atlassian_classifications.id=atlassian_item_classifications.classification_id WHERE atlassian_item_classifications.external_resource_id=? ORDER BY atlassian_classifications.kind,atlassian_classifications.normalized_name",[resource])?;
    let mut local = vec![];
    if truth(&row["note"]) {
        local.push(format!("note: {}", python_string(&row["note"])));
    }
    for classification in classifications {
        local.push(format!(
            "{}: {}",
            python_string(&classification["kind"]),
            python_string(&classification["name"])
        ));
        if truth(&classification["description"]) {
            local.push(format!(
                "topic description: {}",
                python_string(&classification["description"])
            ));
        }
    }
    if !local.is_empty() {
        role("atlassian:local".into(), local_title, local.join("\n"));
    }
    Ok(values)
}
pub(super) fn project_internal(
    connection: &Connection,
    resource: i64,
    changed_at: &str,
) -> Result<bool> {
    let mut values = projection_values(connection, resource)?;
    let current=db::rows(connection,"SELECT entity_type,entity_id,source_kind,title,body,path FROM search_index WHERE entity_type='atlassian_item' AND entity_id=? ORDER BY source_kind,title,body,path",[resource.to_string()])?;
    values.sort_by(|a, b| {
        for key in ["source_kind", "title", "body", "path"] {
            let ordering = a[key].as_str().unwrap().cmp(b[key].as_str().unwrap());
            if !ordering.is_eq() {
                return ordering;
            }
        }
        std::cmp::Ordering::Equal
    });
    let hash = format!(
        "{:x}",
        Sha256::digest(
            json_size(
                &json!(values),
                "search projection",
                2_000_000,
                "invalid-input"
            )?
            .as_bytes()
        )
    );
    let content = db::row(
        connection,
        "SELECT search_projection_hash FROM external_resource_content WHERE external_resource_id=?",
        [resource],
    )?;
    if current == values {
        if content
            .as_ref()
            .is_some_and(|v| v["search_projection_hash"] != hash)
        {
            connection.execute("UPDATE external_resource_content SET search_projection_hash=?,updated_at=? WHERE external_resource_id=?",params![hash,changed_at,resource])?;
        }
        return Ok(false);
    }
    connection.execute(
        "DELETE FROM search_index WHERE entity_type='atlassian_item' AND entity_id=?",
        [resource.to_string()],
    )?;
    for value in values {
        connection.execute("INSERT INTO search_index(entity_type,entity_id,source_kind,title,body,path) VALUES (?,?,?,?,?,?)",params![value["entity_type"].as_str(),value["entity_id"].as_str(),value["source_kind"].as_str(),value["title"].as_str(),value["body"].as_str(),value["path"].as_str()])?;
    }
    if content.is_some() {
        connection.execute("UPDATE external_resource_content SET search_projection_hash=?,updated_at=? WHERE external_resource_id=?",params![hash,changed_at,resource])?;
    }
    Ok(true)
}
pub fn project_atlassian_item_search(
    connection: &Connection,
    resource: i64,
    changed_at: Option<&str>,
) -> Result<bool> {
    store::item_row(connection, resource)?;
    project_internal(
        connection,
        resource,
        &changed_at
            .filter(|s| !s.is_empty())
            .map(ToOwned::to_owned)
            .unwrap_or_else(now),
    )
}
pub fn rebuild_atlassian_search_index(
    connection: &Connection,
    rebuilt_at: Option<&str>,
) -> Result<i64> {
    let timestamp = rebuilt_at
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
        .unwrap_or_else(now);
    let items = db::rows(
        connection,
        "SELECT external_resource_id FROM atlassian_items ORDER BY external_resource_id",
        [],
    )?;
    atomic(connection, "atlassian_search_rebuild", || {
        connection.execute(
            "DELETE FROM search_index WHERE entity_type='atlassian_item'",
            [],
        )?;
        connection.execute(
            "UPDATE external_resource_content SET search_projection_hash=NULL,updated_at=?",
            [&timestamp],
        )?;
        let mut projected = 0;
        for item in items {
            projected += i64::from(project_internal(
                connection,
                id(&item["external_resource_id"])?,
                &timestamp,
            )?);
        }
        Ok(projected)
    })
}
