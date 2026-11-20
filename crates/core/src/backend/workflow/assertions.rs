//! Append-only user assertions, immutable base provenance and deterministic overlay.
use super::{focus::WorkflowFocusProjection, projection::*};
use crate::backend::{clock, db, BackendError, Result};
use rusqlite::Connection;
use serde::Serialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const WORKFLOW_ASSERTION_VERSION: &str = "localbrain.workflow-assertion.v1";
pub const WORKFLOW_ASSERTION_OVERLAY_VERSION: &str = "localbrain.workflow-assertion-overlay.v1";
pub const WORKFLOW_ASSERTION_KINDS: &[&str] =
    &["same-flow", "split-here", "merge-into", "close", "reopen"];
pub const WORKFLOW_BOUNDARY_KINDS: &[&str] = &["relation", "lifecycle"];
pub const WORKFLOW_ASSERTION_AUTHORITIES: &[&str] = &["user-confirmed"];
pub const WORKFLOW_ASSERTION_MEANINGS: &[&str] = &[
    "relation:absent",
    "relation:continues",
    "relation:branches-from",
    "relation:merged-into",
    "lifecycle:unknown",
    "lifecycle:open",
    "lifecycle:closed",
];
pub const MAX_WORKFLOW_ASSERTION_NOTE_CODE_POINTS: usize = 1000;
pub const MAX_WORKFLOW_ASSERTION_HISTORY: usize = 100;
pub const WORKFLOW_ACTION_AFTER_MEANINGS: &[(&str, &str)] = &[
    ("same-flow", "relation:continues"),
    ("split-here", "relation:branches-from"),
    ("merge-into", "relation:merged-into"),
    ("close", "lifecycle:closed"),
    ("reopen", "lifecycle:open"),
];
pub fn action_after_meaning(action: &str) -> Option<&'static str> {
    WORKFLOW_ACTION_AFTER_MEANINGS
        .iter()
        .find(|(key, _)| *key == action)
        .map(|(_, meaning)| *meaning)
        .filter(|meaning| WORKFLOW_ASSERTION_MEANINGS.contains(meaning))
}
fn reject(code: &str, message: &str) -> BackendError {
    BackendError::new(
        if matches!(
            code,
            "conflict"
                | "duplicate-active"
                | "assertion-not-active"
                | "assertion-not-found"
                | "requires-active-closure"
                | "not-tip"
                | "missing-endpoint"
                | "cycle"
                | "contradictory-boundary"
        ) {
            409
        } else {
            422
        },
        code,
        message,
    )
}
fn episode_key(value: &str, field: &str) -> Result<String> {
    let normalized = trim(value);
    if normalized.strip_prefix("session:").is_none_or(|hex| {
        hex.len() != 64
            || !hex
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    }) {
        return Err(reject(
            "invalid-request",
            &format!("{field} must be a stable Episode key"),
        ));
    }
    Ok(normalized.into())
}
pub fn workflow_boundary_key(
    boundary_kind: &str,
    source: &str,
    target: Option<&str>,
) -> Result<String> {
    if !WORKFLOW_BOUNDARY_KINDS.contains(&boundary_kind) {
        return Err(reject("invalid-request", "unsupported boundary kind"));
    }
    let source = episode_key(source, "source_episode_key")?;
    let mut parts = vec![boundary_kind, source.as_str()];
    let normalized_target;
    if boundary_kind == "lifecycle" {
        if target.is_some() {
            return Err(reject(
                "invalid-request",
                "lifecycle boundary has no target Episode",
            ));
        }
    } else {
        normalized_target = episode_key(
            target.ok_or_else(|| {
                reject(
                    "invalid-request",
                    "target_episode_key must be an Episode key",
                )
            })?,
            "target_episode_key",
        )?;
        parts.push(&normalized_target);
    }
    let mut digest = Sha256::new();
    for part in parts {
        digest.update((part.len() as u64).to_be_bytes());
        digest.update(part.as_bytes());
    }
    Ok(format!("{:x}", digest.finalize()))
}
fn undo(row: &Value) -> bool {
    row["is_undo"]
        .as_bool()
        .unwrap_or_else(|| row["is_undo"].as_i64().unwrap_or(0) != 0)
}
fn active_assertion(connection: &Connection, boundary: &str) -> Result<Option<Value>> {
    db::row(connection,"SELECT assertions.* FROM workflow_assertions AS assertions WHERE assertions.boundary_key=? AND NOT EXISTS(SELECT 1 FROM workflow_assertions AS successor WHERE successor.supersedes_assertion_id=assertions.id) ORDER BY assertions.boundary_version DESC,assertions.id DESC LIMIT 1",[boundary])
}
fn active_assertions_for_keys(connection: &Connection, keys: &[String]) -> Result<Vec<Value>> {
    if keys.is_empty() {
        return Ok(vec![]);
    }
    let placeholders = vec!["?"; keys.len()].join(", ");
    db::rows(connection,&format!("SELECT assertions.* FROM workflow_assertions AS assertions WHERE (assertions.source_episode_key IN ({placeholders}) OR assertions.target_episode_key IN ({placeholders})) AND NOT EXISTS(SELECT 1 FROM workflow_assertions AS successor WHERE successor.supersedes_assertion_id=assertions.id) ORDER BY assertions.created_at,assertions.id"),rusqlite::params_from_iter(keys.iter().chain(keys)))
}
fn assertion_predecessor(connection: &Connection, assertion: &Value) -> Result<Option<Value>> {
    let Some(id) = assertion["supersedes_assertion_id"].as_i64() else {
        return Ok(None);
    };
    let Some(predecessor) = db::row(
        connection,
        "SELECT * FROM workflow_assertions WHERE id=?",
        [id],
    )?
    else {
        return Ok(None);
    };
    match predecessor["supersedes_assertion_id"].as_i64() {
        Some(id) => db::row(
            connection,
            "SELECT * FROM workflow_assertions WHERE id=?",
            [id],
        ),
        None => Ok(None),
    }
}
fn base_relations(projection: &WorkflowFocusProjection) -> Vec<WorkflowRelation> {
    if projection
        .assertion_overlay_version
        .as_deref()
        .is_some_and(|s| !s.is_empty())
    {
        projection.base_relations.clone()
    } else {
        projection.relations.clone()
    }
}
fn base_lifecycle(projection: &WorkflowFocusProjection) -> BTreeMap<String, Value> {
    if projection
        .assertion_overlay_version
        .as_deref()
        .is_some_and(|s| !s.is_empty())
    {
        projection
            .base_episode_lifecycle
            .iter()
            .map(|v| (v["episode_key"].as_str().unwrap().into(), v.clone()))
            .collect()
    } else {
        projection.episodes.iter().map(|view|{let e=&view.episode;(e.episode_key.clone(),json!({"episode_key":e.episode_key,"lifecycle_state":e.lifecycle_state,"closure_reason":e.closure_reason,"authority":e.authority}))}).collect()
    }
}
fn relation_pair(relation: &WorkflowRelation) -> (String, String) {
    (
        relation.source_episode_key.clone(),
        relation.target_episode_key.clone(),
    )
}
fn kind_from_meaning(meaning: &str) -> Option<&str> {
    if meaning == "relation:absent" {
        None
    } else {
        Some(
            meaning
                .split_once(':')
                .expect("ledger meaning is schema-checked")
                .1,
        )
    }
}
fn meaning_for_relation(relation: Option<&WorkflowRelation>) -> String {
    relation
        .map(|r| format!("relation:{}", r.kind))
        .unwrap_or_else(|| "relation:absent".into())
}
fn relation_path_exists(
    relations: impl IntoIterator<Item = WorkflowRelation>,
    start: &str,
    target: &str,
) -> bool {
    let mut adjacency = BTreeMap::<String, BTreeSet<String>>::new();
    for relation in relations {
        adjacency
            .entry(relation.source_episode_key)
            .or_default()
            .insert(relation.target_episode_key);
    }
    path_exists(&adjacency, start, target)
}
fn episode_time(episode: &WorkflowEpisode) -> Option<String> {
    episode
        .observed_start_at
        .as_deref()
        .filter(|s| !s.is_empty())
        .or(episode.last_observed_at.as_deref())
        .and_then(clock::parse_timestamp)
        .map(clock::isoformat)
}
fn strictly_forward(source: &WorkflowEpisode, target: &WorkflowEpisode) -> bool {
    match (
        episode_time(source)
            .as_deref()
            .and_then(clock::parse_timestamp),
        episode_time(target)
            .as_deref()
            .and_then(clock::parse_timestamp),
    ) {
        (Some(a), Some(b)) => b > a,
        _ => false,
    }
}
fn summary(
    assertion: &Value,
    resolution: &str,
    resolution_reason: Option<&str>,
    base_relation: Option<&WorkflowRelation>,
    restored: Option<i64>,
) -> Value {
    let mut result = serde_json::Map::new();
    for key in [
        "id",
        "boundary_key",
        "boundary_version",
        "boundary_kind",
        "assertion_kind",
        "source_episode_key",
        "target_episode_key",
        "before_meaning",
        "after_meaning",
        "before_closure_reason",
        "after_closure_reason",
        "note",
        "authority",
        "contract_version",
        "supersedes_assertion_id",
        "created_at",
    ] {
        result.insert(key.into(), assertion[key].clone());
    }
    result.insert("is_undo".into(), json!(undo(assertion)));
    result.insert("resolution".into(), json!(resolution));
    result.insert("resolution_reason".into(), json!(resolution_reason));
    result.insert("base_relation".into(), json!(base_relation));
    result.insert("restored_assertion_id".into(), json!(restored));
    Value::Object(result)
}
fn revision(
    projection: &WorkflowFocusProjection,
    relations: &[WorkflowRelation],
    assertions: &[Value],
) -> Result<String> {
    let episodes=projection.episodes.iter().map(|view|json!({"episode_key":view.episode.episode_key,"observed_start_at":view.episode.observed_start_at,"last_observed_at":view.episode.last_observed_at})).collect::<Vec<_>>();
    let assertions = assertions
        .iter()
        .map(|item| {
            let mut fields = serde_json::Map::new();
            for key in [
                "id",
                "boundary_key",
                "boundary_version",
                "source_episode_key",
                "target_episode_key",
                "after_meaning",
                "after_closure_reason",
                "resolution",
            ] {
                fields.insert(key.into(), item[key].clone());
            }
            Value::Object(fields)
        })
        .collect::<Vec<_>>();
    let serialized = canonical_json(
        &json!({"selected_episode_key":projection.selected_episode_key,"episodes":episodes,"base_relations":relations,"assertions":assertions}),
    )?;
    Ok(format!(
        "workflow-revision:{:x}",
        Sha256::digest(serialized.as_bytes())
    ))
}

/// Overlay only the effective boundary/lifecycle. Complete base relations and
/// lifecycle remain available for Trace, including unresolved historical rows.
pub fn overlay_workflow_assertions(
    connection: &Connection,
    mut projection: WorkflowFocusProjection,
) -> Result<WorkflowFocusProjection> {
    if projection.status != "ready" {
        return Ok(projection);
    }
    let relations = base_relations(&projection);
    let lifecycle = base_lifecycle(&projection);
    let mut views = projection.episodes.clone();
    for view in &mut views {
        let base = &lifecycle[&view.episode.episode_key];
        view.episode.lifecycle_state = base["lifecycle_state"].as_str().unwrap().into();
        view.episode.closure_reason = base["closure_reason"].as_str().map(str::to_string);
        view.episode.authority = base["authority"].as_str().unwrap().into();
    }
    let mut base_projection = projection.clone();
    base_projection.episodes = views.clone();
    base_projection.relations = relations.clone();
    let episodes: BTreeMap<_, _> = views
        .iter()
        .map(|view| (view.episode.episode_key.clone(), view.episode.clone()))
        .collect();
    let keys = episodes.keys().cloned().collect::<Vec<_>>();
    let active = active_assertions_for_keys(connection, &keys)?;
    let mut effective: BTreeMap<_, _> = relations
        .iter()
        .map(|relation| (relation_pair(relation), relation.clone()))
        .collect();
    let mut summaries = vec![];
    let mut diagnostics = vec![];
    let mut lifecycle_assertions = BTreeMap::<String, (Value, Option<Value>)>::new();
    for assertion in active {
        let source_key = assertion["source_episode_key"]
            .as_str()
            .unwrap()
            .to_string();
        let target_key = assertion["target_episode_key"]
            .as_str()
            .unwrap_or("")
            .to_string();
        let restored = if undo(&assertion) {
            assertion_predecessor(connection, &assertion)?
        } else {
            None
        };
        let restored_id = restored.as_ref().and_then(|row| row["id"].as_i64());
        if assertion["boundary_kind"] == "lifecycle" {
            if !episodes.contains_key(&source_key) {
                let reason = "missing-source-episode";
                summaries.push(summary(
                    &assertion,
                    "unresolved",
                    Some(reason),
                    None,
                    restored_id,
                ));
                diagnostics.push(json!({"code":reason,"assertion_id":assertion["id"]}));
                continue;
            }
            summaries.push(summary(&assertion, "applied", None, None, restored_id));
            lifecycle_assertions.insert(source_key, (assertion, restored));
            continue;
        }
        let pair = (source_key, target_key);
        let base_relation = relations
            .iter()
            .find(|relation| relation_pair(relation) == pair);
        let source = episodes.get(&pair.0);
        let target = episodes.get(&pair.1);
        let omission = match (source, target) {
            (Some(source), Some(target)) => {
                if !strictly_forward(source, target) {
                    Some("endpoint-time-order")
                } else {
                    let proposed = kind_from_meaning(assertion["after_meaning"].as_str().unwrap());
                    let other: Vec<_> = effective
                        .iter()
                        .filter(|(key, _)| **key != pair)
                        .map(|(_, relation)| relation.clone())
                        .collect();
                    if proposed.is_some() && relation_path_exists(other.clone(), &pair.1, &pair.0) {
                        Some("cycle")
                    } else if proposed
                        .is_some_and(|kind| ["continues", "branches-from"].contains(&kind))
                        && other.iter().any(|relation| {
                            relation.target_episode_key == pair.1
                                && relation.source_episode_key != pair.0
                                && ["continues", "branches-from"].contains(&relation.kind.as_str())
                        })
                    {
                        Some("contradictory-incoming-boundary")
                    } else {
                        None
                    }
                }
            }
            _ => Some("missing-endpoint"),
        };
        if let Some(reason) = omission {
            summaries.push(summary(
                &assertion,
                "unresolved",
                Some(reason),
                base_relation,
                restored_id,
            ));
            diagnostics.push(json!({"code":reason,"assertion_id":assertion["id"]}));
            continue;
        }
        effective.remove(&pair);
        let kind = kind_from_meaning(assertion["after_meaning"].as_str().unwrap());
        let restore_base = undo(&assertion) && restored.is_none();
        if let Some(kind) = kind {
            if restore_base && base_relation.is_some_and(|relation| relation.kind == kind) {
                effective.insert(pair.clone(), base_relation.unwrap().clone());
            } else {
                effective.insert(
                    pair.clone(),
                    WorkflowRelation {
                        source_episode_key: pair.0.clone(),
                        target_episode_key: pair.1.clone(),
                        kind: kind.into(),
                        authority: WORKFLOW_ASSERTION_AUTHORITIES[0].into(),
                        reasons: vec![WorkflowRelationReason {
                            kind: "user-assertion".into(),
                            identity: format!("assertion:{}", assertion["id"].as_i64().unwrap()),
                            observed_at: assertion["created_at"].as_str().map(str::to_string),
                        }],
                        source_observed_at: episode_time(source.unwrap()),
                        target_observed_at: episode_time(target.unwrap()),
                        projection_version: WORKFLOW_PROJECTION_VERSION.into(),
                    },
                );
            }
        }
        summaries.push(summary(
            &assertion,
            "applied",
            None,
            base_relation,
            restored_id,
        ));
    }
    for view in &mut views {
        if let Some((assertion, restored)) = lifecycle_assertions.get(&view.episode.episode_key) {
            view.episode.lifecycle_state = assertion["after_meaning"]
                .as_str()
                .unwrap()
                .split_once(':')
                .unwrap()
                .1
                .into();
            view.episode.closure_reason = assertion["after_closure_reason"]
                .as_str()
                .map(str::to_string);
            if !(undo(assertion) && restored.is_none()) {
                view.episode.authority = WORKFLOW_ASSERTION_AUTHORITIES[0].into();
            }
        }
    }
    let mut effective: Vec<_> = effective.into_values().collect();
    effective.sort_by(|a, b| {
        a.source_observed_at
            .as_deref()
            .unwrap_or("")
            .cmp(b.source_observed_at.as_deref().unwrap_or(""))
            .then(
                a.target_observed_at
                    .as_deref()
                    .unwrap_or("")
                    .cmp(b.target_observed_at.as_deref().unwrap_or("")),
            )
            .then(a.source_episode_key.cmp(&b.source_episode_key))
            .then(a.target_episode_key.cmp(&b.target_episode_key))
            .then(a.kind.cmp(&b.kind))
    });
    summaries.sort_by(|a, b| {
        a["created_at"]
            .as_str()
            .cmp(&b["created_at"].as_str())
            .then(a["id"].as_i64().cmp(&b["id"].as_i64()))
    });
    projection.assertion_revision = Some(revision(&base_projection, &relations, &summaries)?);
    projection.episodes = views;
    projection.relations = effective;
    projection.base_relations = relations;
    projection.base_episode_lifecycle = lifecycle.into_values().collect();
    projection.assertions = summaries;
    projection.assertion_diagnostics = diagnostics;
    projection.assertion_overlay_version = Some(WORKFLOW_ASSERTION_OVERLAY_VERSION.into());
    Ok(projection)
}

#[derive(Debug, Clone, Serialize)]
pub struct WorkflowAssertionMutation {
    pub assertion: Value,
    pub projection: WorkflowFocusProjection,
}
fn request_episode(request: &Value, field: &str) -> Result<String> {
    episode_key(
        request.get(field).and_then(Value::as_str).ok_or_else(|| {
            reject(
                "invalid-request",
                &format!("{field} must be an Episode key"),
            )
        })?,
        field,
    )
}
fn positive_optional(value: Option<&Value>, field: &str) -> Result<Option<i64>> {
    match value.filter(|v| !v.is_null()) {
        None => Ok(None),
        Some(value) => value
            .as_i64()
            .filter(|value| *value > 0)
            .map(Some)
            .ok_or_else(|| {
                reject(
                    "invalid-request",
                    &format!("{field} must be a positive integer"),
                )
            }),
    }
}
fn normalized_note(value: Option<&Value>) -> Result<Option<String>> {
    let Some(value) = value.filter(|v| !v.is_null()) else {
        return Ok(None);
    };
    let value = value
        .as_str()
        .ok_or_else(|| reject("invalid-note", "note must be text"))?;
    let normalized = trim(value);
    if normalized.is_empty() {
        return Ok(None);
    }
    if normalized.chars().count() > MAX_WORKFLOW_ASSERTION_NOTE_CODE_POINTS {
        return Err(reject("invalid-note", "note exceeds the supported bound"));
    }
    Ok(Some(normalized.into()))
}
fn created_at(value: Option<&Value>) -> Result<String> {
    match value.filter(|v| !v.is_null()) {
        None => Ok(clock::isoformat(chrono::Utc::now())),
        Some(value) => value
            .as_str()
            .and_then(clock::parse_timestamp)
            .map(clock::isoformat)
            .ok_or_else(|| reject("invalid-created-at", "created_at must be a valid timestamp")),
    }
}
fn projection_episode<'a>(
    projection: &'a WorkflowFocusProjection,
    key: &str,
) -> Option<&'a WorkflowEpisode> {
    projection
        .episodes
        .iter()
        .map(|view| &view.episode)
        .find(|episode| episode.episode_key == key)
}
fn effective_relation<'a>(
    projection: &'a WorkflowFocusProjection,
    source: &str,
    target: &str,
) -> Option<&'a WorkflowRelation> {
    projection.relations.iter().find(|relation| {
        relation.source_episode_key == source && relation.target_episode_key == target
    })
}
fn current_projection(
    connection: &Connection,
    projection: &WorkflowFocusProjection,
    expected: Option<&Value>,
) -> Result<WorkflowFocusProjection> {
    let expected = expected
        .and_then(Value::as_str)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| reject("conflict", "current projection revision is required"))?;
    let current = overlay_workflow_assertions(connection, projection.clone())?;
    if current.assertion_revision.as_deref() != Some(expected) {
        return Err(reject("conflict", "workflow projection changed"));
    }
    Ok(current)
}
fn assert_expected_active(active: Option<&Value>, expected: Option<&Value>) -> Result<()> {
    let expected = positive_optional(expected, "expected_active_assertion_id")?;
    let actual = active.and_then(|row| row["id"].as_i64());
    if expected != actual {
        return Err(reject("conflict", "workflow assertion boundary changed"));
    }
    Ok(())
}
struct NewAssertion {
    boundary_key: String,
    boundary_kind: String,
    assertion_kind: String,
    is_undo: bool,
    source_episode_key: String,
    target_episode_key: Option<String>,
    source_session_id: Option<i64>,
    target_session_id: Option<i64>,
    before_meaning: String,
    after_meaning: String,
    before_closure_reason: Option<String>,
    after_closure_reason: Option<String>,
    note: Option<String>,
    supersedes_assertion_id: Option<i64>,
    created_at: String,
}
fn write_conflict(error: &rusqlite::Error) -> bool {
    matches!(error,rusqlite::Error::SqliteFailure(cause,Some(message)) if cause.code==rusqlite::ErrorCode::ConstraintViolation&&["workflow_assertions.boundary_key, workflow_assertions.boundary_version","workflow_assertions.supersedes_assertion_id"].iter().any(|constraint|message.contains(constraint)))
}
fn insert_assertion(connection: &Connection, record: &NewAssertion) -> Result<i64> {
    let version: i64 = connection.query_row(
        "SELECT COALESCE(MAX(boundary_version),0)+1 FROM workflow_assertions WHERE boundary_key=?",
        [&record.boundary_key],
        |row| row.get(0),
    )?;
    connection.execute("INSERT INTO workflow_assertions(boundary_key,boundary_version,boundary_kind,assertion_kind,is_undo,source_episode_key,target_episode_key,source_session_id,target_session_id,before_meaning,after_meaning,before_closure_reason,after_closure_reason,note,authority,contract_version,supersedes_assertion_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",rusqlite::params![record.boundary_key,version,record.boundary_kind,record.assertion_kind,i64::from(record.is_undo),record.source_episode_key,record.target_episode_key,record.source_session_id,record.target_session_id,record.before_meaning,record.after_meaning,record.before_closure_reason,record.after_closure_reason,record.note,WORKFLOW_ASSERTION_AUTHORITIES[0],WORKFLOW_ASSERTION_VERSION,record.supersedes_assertion_id,record.created_at]).map_err(|error|if write_conflict(&error){reject("conflict","workflow assertion boundary changed")}else{error.into()})?;
    Ok(connection.last_insert_rowid())
}
fn append_and_overlay(
    connection: &Connection,
    projection: WorkflowFocusProjection,
    record: NewAssertion,
    savepoint: &str,
) -> Result<WorkflowAssertionMutation> {
    // Both callers supply fixed local savepoint names; request text is bound.
    connection.execute_batch(&format!("SAVEPOINT {savepoint}"))?;
    let result = (|| {
        let id = insert_assertion(connection, &record)?;
        let effective = overlay_workflow_assertions(connection, projection)?;
        Ok::<_, BackendError>((id, effective))
    })();
    let (id, effective) = match result {
        Ok(value) => value,
        Err(error) => {
            connection.execute_batch(&format!(
                "ROLLBACK TO SAVEPOINT {savepoint}; RELEASE SAVEPOINT {savepoint}"
            ))?;
            return Err(error);
        }
    };
    connection.execute_batch(&format!("RELEASE SAVEPOINT {savepoint}"))?;
    let assertion = db::row(
        connection,
        "SELECT * FROM workflow_assertions WHERE id=?",
        [id],
    )?
    .ok_or_else(|| {
        BackendError::new(
            500,
            "workflow_assertion",
            "Appended workflow assertion is missing",
        )
    })?;
    Ok(WorkflowAssertionMutation {
        assertion,
        projection: effective,
    })
}

/// Append exactly one explicit correction. `request` uses the frozen keyword
/// names; caller owns its outer transaction and HTTP/form authorization.
pub fn apply_workflow_assertion(
    connection: &Connection,
    projection: &WorkflowFocusProjection,
    request: &Value,
) -> Result<WorkflowAssertionMutation> {
    if projection.status != "ready" {
        return Err(reject(
            "invalid-projection",
            "workflow projection must be ready",
        ));
    }
    let projection = current_projection(connection, projection, request.get("expected_revision"))?;
    let kind = request["assertion_kind"]
        .as_str()
        .filter(|kind| WORKFLOW_ASSERTION_KINDS.contains(kind))
        .ok_or_else(|| reject("invalid-action", "unsupported workflow assertion"))?;
    let source_key = request_episode(request, "source_episode_key")?;
    let source = projection_episode(&projection, &source_key).ok_or_else(|| {
        reject(
            "missing-endpoint",
            "source Episode is not in the projection",
        )
    })?;
    let note = normalized_note(request.get("note"))?;
    let created = created_at(request.get("created_at"))?;
    let (
        boundary_kind,
        boundary_key,
        target_key,
        target_id,
        before_meaning,
        after_meaning,
        before_reason,
        after_reason,
        active,
    ) = if ["same-flow", "split-here", "merge-into"].contains(&kind) {
        let target_key = request_episode(request, "target_episode_key")?;
        let target = projection_episode(&projection, &target_key).ok_or_else(|| {
            reject(
                "missing-endpoint",
                "target Episode is not in the projection",
            )
        })?;
        if source_key == target_key {
            return Err(reject(
                "self-relation",
                "workflow relation cannot target itself",
            ));
        }
        if !strictly_forward(source, target) {
            return Err(reject(
                if kind == "merge-into" {
                    "merge-before-source"
                } else {
                    "non-forward-time"
                },
                "workflow relation must move forward in observed time",
            ));
        }
        let boundary = workflow_boundary_key("relation", &source_key, Some(&target_key))?;
        let active = active_assertion(connection, &boundary)?;
        let before =
            meaning_for_relation(effective_relation(&projection, &source_key, &target_key));
        let after = action_after_meaning(kind).unwrap().to_string();
        if kind == "split-here" && before != "relation:continues" {
            return Err(reject(
                "requires-continues",
                "split requires a continues boundary",
            ));
        }
        if active.as_ref().is_some_and(|row| {
            row["after_meaning"] == after && row["after_closure_reason"].is_null()
        }) {
            return Err(reject(
                "duplicate-active",
                "the same assertion is already active",
            ));
        }
        assert_expected_active(active.as_ref(), request.get("expected_active_assertion_id"))?;
        let other: Vec<_> = projection
            .relations
            .iter()
            .filter(|relation| {
                relation.source_episode_key != source_key
                    || relation.target_episode_key != target_key
            })
            .cloned()
            .collect();
        if relation_path_exists(other.clone(), &target_key, &source_key) {
            return Err(reject("cycle", "workflow assertion would create a cycle"));
        }
        if kind_from_meaning(&after)
            .is_some_and(|kind| ["continues", "branches-from"].contains(&kind))
            && other.iter().any(|relation| {
                relation.target_episode_key == target_key
                    && relation.source_episode_key != source_key
                    && ["continues", "branches-from"].contains(&relation.kind.as_str())
            })
        {
            return Err(reject(
                "contradictory-boundary",
                "target Episode already has an active incoming boundary",
            ));
        }
        (
            "relation",
            boundary,
            Some(target_key),
            Some(target.session_id),
            before,
            after,
            None,
            None,
            active,
        )
    } else {
        if request
            .get("target_episode_key")
            .is_some_and(|value| !value.is_null())
        {
            return Err(reject(
                "invalid-request",
                "lifecycle assertion has no target Episode",
            ));
        }
        let boundary = workflow_boundary_key("lifecycle", &source_key, None)?;
        let active = active_assertion(connection, &boundary)?;
        let before = format!("lifecycle:{}", source.lifecycle_state);
        let after = action_after_meaning(kind).unwrap().to_string();
        let after_reason = if kind == "close" {
            let reason = request["close_reason"]
                .as_str()
                .filter(|reason| CLOSURE_REASONS.contains(reason))
                .ok_or_else(|| {
                    reject("invalid-close-reason", "close requires a supported reason")
                })?;
            if projection
                .relations
                .iter()
                .any(|relation| relation.source_episode_key == source_key)
            {
                return Err(reject(
                    "not-tip",
                    "only a current workflow tip can be closed",
                ));
            }
            Some(reason.to_string())
        } else {
            if request
                .get("close_reason")
                .is_some_and(|value| !value.is_null())
            {
                return Err(reject(
                    "invalid-close-reason",
                    "reopen does not accept a reason",
                ));
            }
            if active
                .as_ref()
                .is_none_or(|row| row["after_meaning"] != "lifecycle:closed")
            {
                return Err(reject(
                    "requires-active-closure",
                    "reopen requires an active closure",
                ));
            }
            None
        };
        if active.as_ref().is_some_and(|row| {
            row["after_meaning"] == after
                && row["after_closure_reason"].as_str() == after_reason.as_deref()
        }) {
            return Err(reject(
                "duplicate-active",
                "the same assertion is already active",
            ));
        }
        assert_expected_active(active.as_ref(), request.get("expected_active_assertion_id"))?;
        (
            "lifecycle",
            boundary,
            None,
            None,
            before,
            after,
            source.closure_reason.clone(),
            after_reason,
            active,
        )
    };
    let record = NewAssertion {
        boundary_key,
        boundary_kind: boundary_kind.into(),
        assertion_kind: kind.into(),
        is_undo: false,
        source_episode_key: source_key,
        target_episode_key: target_key,
        source_session_id: Some(source.session_id),
        target_session_id: target_id,
        before_meaning,
        after_meaning,
        before_closure_reason: before_reason,
        after_closure_reason: after_reason,
        note,
        supersedes_assertion_id: active.as_ref().and_then(|row| row["id"].as_i64()),
        created_at: created,
    };
    append_and_overlay(connection, projection, record, "workflow_assertion_apply")
}

/// Append a reversal only for the current assertion. History is never deleted.
pub fn undo_workflow_assertion(
    connection: &Connection,
    projection: &WorkflowFocusProjection,
    request: &Value,
) -> Result<WorkflowAssertionMutation> {
    if projection.status != "ready" {
        return Err(reject(
            "invalid-projection",
            "workflow projection must be ready",
        ));
    }
    let projection = current_projection(connection, projection, request.get("expected_revision"))?;
    let id = positive_optional(request.get("assertion_id"), "assertion_id")?;
    let active = db::row(
        connection,
        "SELECT * FROM workflow_assertions WHERE id=?",
        [id],
    )?
    .ok_or_else(|| reject("assertion-not-found", "workflow assertion does not exist"))?;
    let current = active_assertion(connection, active["boundary_key"].as_str().unwrap())?;
    if current.as_ref().and_then(|row| row["id"].as_i64()) != id {
        return Err(reject(
            "assertion-not-active",
            "only the current assertion can be undone",
        ));
    }
    let source_key = active["source_episode_key"].as_str().unwrap();
    let target_key = active["target_episode_key"].as_str();
    let source = projection_episode(&projection, source_key);
    let target = target_key.and_then(|key| projection_episode(&projection, key));
    if source.is_none() || (active["boundary_kind"] == "relation" && target.is_none()) {
        return Err(reject(
            "missing-endpoint",
            "assertion endpoint is not in the projection",
        ));
    }
    let record = NewAssertion {
        boundary_key: active["boundary_key"].as_str().unwrap().into(),
        boundary_kind: active["boundary_kind"].as_str().unwrap().into(),
        assertion_kind: active["assertion_kind"].as_str().unwrap().into(),
        is_undo: true,
        source_episode_key: source_key.into(),
        target_episode_key: target_key.map(str::to_string),
        source_session_id: source.map(|e| e.session_id),
        target_session_id: target.map(|e| e.session_id),
        before_meaning: active["after_meaning"].as_str().unwrap().into(),
        after_meaning: active["before_meaning"].as_str().unwrap().into(),
        before_closure_reason: active["after_closure_reason"].as_str().map(str::to_string),
        after_closure_reason: active["before_closure_reason"].as_str().map(str::to_string),
        note: None,
        supersedes_assertion_id: id,
        created_at: created_at(request.get("created_at"))?,
    };
    append_and_overlay(connection, projection, record, "workflow_assertion_undo")
}
pub fn workflow_assertion_history(
    connection: &Connection,
    boundary: &str,
    limit: usize,
) -> Result<Value> {
    if boundary.len() != 64
        || !boundary
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(reject(
            "invalid-request",
            "boundary_key must be a stable digest",
        ));
    }
    if !(1..=100).contains(&limit) {
        return Err(reject(
            "invalid-request",
            "history limit must be between 1 and 100",
        ));
    }
    let total: i64 = connection.query_row(
        "SELECT COUNT(*) FROM workflow_assertions WHERE boundary_key=?",
        [boundary],
        |row| row.get(0),
    )?;
    let mut rows=db::rows(connection,"SELECT assertions.*,NOT EXISTS(SELECT 1 FROM workflow_assertions AS successor WHERE successor.supersedes_assertion_id=assertions.id) AS is_active FROM workflow_assertions AS assertions WHERE assertions.boundary_key=? ORDER BY assertions.boundary_version DESC,assertions.id DESC LIMIT ?",rusqlite::params![boundary,limit as i64])?;
    rows.reverse();
    let active = rows
        .iter()
        .find(|row| row["is_active"].as_i64().unwrap_or(0) != 0)
        .and_then(|row| row["id"].as_i64());
    Ok(
        json!({"boundary_key":boundary,"observed_total":total,"retained_total":rows.len(),"partial":total as usize>rows.len(),"active_assertion_id":active,"contract_version":WORKFLOW_ASSERTION_VERSION,"assertions":rows}),
    )
}
