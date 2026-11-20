//! Pure versioned descriptors. This module performs no I/O or persistence.
use crate::backend::{clock, unicode, BackendError, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const WORKFLOW_PROJECTION_VERSION: &str = "localbrain.workflow-projection.v1";
pub const ACTIVITY_STATES: &[&str] = &["active", "quiet", "unknown"];
pub const LIFECYCLE_STATES: &[&str] = &["open", "closed", "unknown"];
pub const CLOSURE_REASONS: &[&str] = &["completed", "abandoned", "superseded", "merged", "other"];
pub const AUTHORITY_STATES: &[&str] = &[
    "observed",
    "deterministic-candidate",
    "explicit-organization",
    "user-confirmed",
];
pub const WORKFLOW_RELATION_KINDS: &[&str] = &["continues", "branches-from", "merged-into"];
pub const STRONG_REASON_KINDS: &[&str] = &[
    "direct-source-relation",
    "shared-reference",
    "thread-membership",
    "workstream-membership",
    "user-assertion",
];
pub const SUPPORTING_REASON_KINDS: &[&str] = &[
    "same-workspace",
    "same-git-root",
    "same-git-branch",
    "lexical-overlap",
    "temporal-proximity",
];
pub const MAX_TITLE_CODE_POINTS: usize = 500;
pub const MAX_EXPLICIT_FIELD_CODE_POINTS: usize = 2_000;
pub const MAX_REASON_IDENTITY_CODE_POINTS: usize = 500;
pub const MAX_EVIDENCE_KIND_CODE_POINTS: usize = 80;

pub(super) fn invalid(message: &str) -> BackendError {
    BackendError::new(422, "workflow", message)
}
pub(super) fn trim(value: &str) -> &str {
    value.trim_matches(unicode::python_space)
}
pub(super) fn bounded(value: Option<&Value>, limit: usize) -> Option<String> {
    value
        .and_then(Value::as_str)
        .map(trim)
        .filter(|s| !s.is_empty())
        .map(|s| s.chars().take(limit).collect())
}
pub(super) fn utc(value: Option<&Value>) -> Option<String> {
    value
        .and_then(Value::as_str)
        .and_then(clock::parse_timestamp)
        .map(clock::isoformat)
}
pub(super) fn positive(value: Option<&Value>, field: &str) -> Result<i64> {
    value
        .and_then(Value::as_i64)
        .filter(|n| *n > 0)
        .ok_or_else(|| invalid(&format!("{field} must be a positive integer")))
}
pub(super) fn opaque_identity(prefix: &str, values: &[&str]) -> String {
    let mut hash = Sha256::new();
    for value in values {
        hash.update((value.len() as u64).to_be_bytes());
        hash.update(value.as_bytes());
    }
    format!("{prefix}:{hash:x}", hash = hash.finalize())
}
pub(super) fn canonical_json(value: &Value) -> Result<String> {
    fn ordered(value: &Value) -> Value {
        match value {
            Value::Object(map) => {
                let mut keys: Vec<_> = map.keys().collect();
                keys.sort();
                Value::Object(
                    keys.into_iter()
                        .map(|key| (key.clone(), ordered(&map[key])))
                        .collect(),
                )
            }
            Value::Array(values) => Value::Array(values.iter().map(ordered).collect()),
            v => v.clone(),
        }
    }
    Ok(serde_json::to_string(&ordered(value))?)
}
pub fn workflow_episode_key(source_id: i64, external_id: &str) -> Result<String> {
    if source_id <= 0 {
        return Err(invalid("source_id must be a positive integer"));
    }
    let external_id = trim(external_id);
    if external_id.is_empty() {
        return Err(invalid("external_id must be non-empty text"));
    }
    Ok(opaque_identity(
        "session",
        &[&source_id.to_string(), external_id],
    ))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowEpisode {
    pub episode_key: String,
    pub session_id: i64,
    pub source_id: i64,
    pub destination: String,
    pub observed_start_at: Option<String>,
    pub last_observed_at: Option<String>,
    pub display_title: Option<String>,
    pub workspace_id: Option<i64>,
    pub workspace_name: Option<String>,
    pub git_branch: Option<String>,
    pub intent: Option<String>,
    pub outcome: Option<String>,
    pub next_action: Option<String>,
    pub evidence_counts: BTreeMap<String, u64>,
    pub activity_state: String,
    pub lifecycle_state: String,
    pub closure_reason: Option<String>,
    pub authority: String,
    pub projection_version: String,
}
#[derive(Debug, Clone)]
pub struct EpisodeOptions {
    pub first_event_at: Option<Value>,
    pub intent: Option<Value>,
    pub outcome: Option<Value>,
    pub next_action: Option<Value>,
    pub evidence_counts: BTreeMap<String, u64>,
    pub activity_state: String,
    pub lifecycle_state: String,
    pub closure_reason: Option<String>,
    pub authority: String,
}
impl Default for EpisodeOptions {
    fn default() -> Self {
        Self {
            first_event_at: None,
            intent: None,
            outcome: None,
            next_action: None,
            evidence_counts: BTreeMap::new(),
            activity_state: "unknown".into(),
            lifecycle_state: "unknown".into(),
            closure_reason: None,
            authority: "observed".into(),
        }
    }
}
pub fn workflow_episode_from_session(
    row: &Value,
    options: &EpisodeOptions,
) -> Result<WorkflowEpisode> {
    if row["session_class"] != "work" {
        return Err(invalid("workflow Episode requires a work Session"));
    }
    if row["session_role"] != "primary" {
        return Err(invalid("workflow Episode requires a primary Session"));
    }
    let session_id = positive(row.get("id"), "session_id")?;
    let source_id = positive(row.get("source_id"), "source_id")?;
    let external = row["external_id"]
        .as_str()
        .ok_or_else(|| invalid("external_id must be non-empty text"))?;
    if !ACTIVITY_STATES.contains(&options.activity_state.as_str()) {
        return Err(invalid("unsupported activity_state"));
    }
    if !LIFECYCLE_STATES.contains(&options.lifecycle_state.as_str()) {
        return Err(invalid("unsupported lifecycle_state"));
    }
    if !AUTHORITY_STATES.contains(&options.authority.as_str()) {
        return Err(invalid("unsupported authority"));
    }
    if options.lifecycle_state == "closed" {
        if !options
            .closure_reason
            .as_deref()
            .is_some_and(|s| CLOSURE_REASONS.contains(&s))
        {
            return Err(invalid(
                "closed lifecycle requires a supported closure_reason",
            ));
        }
    } else if options.closure_reason.is_some() {
        return Err(invalid(
            "closure_reason is allowed only for closed lifecycle",
        ));
    }
    let workspace_id = match row.get("workspace_id").filter(|v| !v.is_null()) {
        Some(v) => Some(positive(Some(v), "workspace_id")?),
        None => None,
    };
    let first = options
        .first_event_at
        .as_ref()
        .filter(|v| !v.is_null())
        .or_else(|| row.get("first_event_at"));
    let mut times: Vec<_> = [
        row.get("started_at"),
        first,
        row.get("last_event_at"),
        row.get("ended_at"),
    ]
    .into_iter()
    .flatten()
    .filter_map(Value::as_str)
    .filter_map(clock::parse_timestamp)
    .collect();
    times.sort();
    let mut evidence_counts = BTreeMap::new();
    for (kind, count) in &options.evidence_counts {
        let kind = trim(kind);
        if kind.is_empty() {
            return Err(invalid("evidence kind must be non-empty text"));
        }
        if kind.chars().count() > MAX_EVIDENCE_KIND_CODE_POINTS {
            return Err(invalid("evidence kind exceeds the supported bound"));
        }
        evidence_counts.insert(kind.into(), *count);
    }
    Ok(WorkflowEpisode {
        episode_key: workflow_episode_key(source_id, external)?,
        session_id,
        source_id,
        destination: format!("/sessions/{session_id}"),
        observed_start_at: times.first().copied().map(clock::isoformat),
        last_observed_at: times.last().copied().map(clock::isoformat),
        display_title: bounded(row.get("title"), 500),
        workspace_id,
        workspace_name: bounded(row.get("workspace_name"), 500),
        git_branch: bounded(row.get("git_branch"), 500),
        intent: bounded(options.intent.as_ref(), 2000),
        outcome: bounded(options.outcome.as_ref(), 2000),
        next_action: bounded(options.next_action.as_ref(), 2000),
        evidence_counts,
        activity_state: options.activity_state.clone(),
        lifecycle_state: options.lifecycle_state.clone(),
        closure_reason: options.closure_reason.clone(),
        authority: options.authority.clone(),
        projection_version: WORKFLOW_PROJECTION_VERSION.into(),
    })
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct WorkflowRelationReason {
    pub kind: String,
    pub identity: String,
    pub observed_at: Option<String>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowRelation {
    pub source_episode_key: String,
    pub target_episode_key: String,
    pub kind: String,
    pub authority: String,
    pub reasons: Vec<WorkflowRelationReason>,
    pub source_observed_at: Option<String>,
    pub target_observed_at: Option<String>,
    pub projection_version: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowDiagnostic {
    pub code: String,
    pub source_episode_key: Option<String>,
    pub target_episode_key: Option<String>,
    pub relation_kind: Option<String>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizedWorkflowRelations {
    pub relations: Vec<WorkflowRelation>,
    pub diagnostics: Vec<WorkflowDiagnostic>,
    pub projection_version: String,
}
pub(super) fn path_exists(
    adjacency: &BTreeMap<String, BTreeSet<String>>,
    start: &str,
    target: &str,
) -> bool {
    let mut pending = vec![start];
    let mut visited = BTreeSet::new();
    while let Some(current) = pending.pop() {
        if current == target {
            return true;
        }
        if visited.insert(current) {
            if let Some(next) = adjacency.get(current) {
                pending.extend(next.iter().rev().map(String::as_str));
            }
        }
    }
    false
}
fn relation_key(
    r: &WorkflowRelation,
) -> (
    String,
    String,
    String,
    String,
    String,
    Vec<WorkflowRelationReason>,
) {
    let mut reasons = r.reasons.clone();
    reasons.sort();
    (
        r.source_observed_at.clone().unwrap_or_default(),
        r.target_observed_at.clone().unwrap_or_default(),
        r.source_episode_key.clone(),
        r.target_episode_key.clone(),
        r.kind.clone(),
        reasons,
    )
}
pub fn normalize_workflow_relations(
    relations: impl IntoIterator<Item = WorkflowRelation>,
) -> NormalizedWorkflowRelations {
    let mut sorted: Vec<_> = relations.into_iter().collect();
    sorted.sort_by_key(relation_key);
    let mut result = NormalizedWorkflowRelations {
        relations: vec![],
        diagnostics: vec![],
        projection_version: WORKFLOW_PROJECTION_VERSION.into(),
    };
    let mut adjacency = BTreeMap::<String, BTreeSet<String>>::new();
    let mut seen = BTreeSet::new();
    for mut r in sorted {
        let diagnostic = |code: &str| WorkflowDiagnostic {
            code: code.into(),
            source_episode_key: Some(r.source_episode_key.clone()),
            target_episode_key: Some(r.target_episode_key.clone()),
            relation_kind: Some(r.kind.clone()),
        };
        let source = trim(&r.source_episode_key).to_string();
        let target = trim(&r.target_episode_key).to_string();
        let mut omission = None;
        if source.is_empty()
            || target.is_empty()
            || !WORKFLOW_RELATION_KINDS.contains(&r.kind.as_str())
            || !AUTHORITY_STATES.contains(&r.authority.as_str())
        {
            omission = Some("invalid-value");
        } else if source == target {
            omission = Some("self-edge");
        }
        let source_time = r
            .source_observed_at
            .as_deref()
            .and_then(clock::parse_timestamp);
        let target_time = r
            .target_observed_at
            .as_deref()
            .and_then(clock::parse_timestamp);
        if omission.is_none() {
            match (source_time, target_time) {
                (Some(a), Some(b)) if b > a => {}
                (Some(_), Some(_)) => omission = Some("non-forward-time"),
                _ => omission = Some("invalid-value"),
            }
        }
        let mut reasons = BTreeSet::new();
        if omission.is_none() {
            for reason in &r.reasons {
                let identity = trim(&reason.identity);
                if !(STRONG_REASON_KINDS.contains(&reason.kind.as_str())
                    || SUPPORTING_REASON_KINDS.contains(&reason.kind.as_str()))
                    || identity.is_empty()
                    || identity.chars().count() > 500
                {
                    omission = Some("invalid-value");
                    break;
                }
                let observed_at = reason
                    .observed_at
                    .as_deref()
                    .and_then(clock::parse_timestamp)
                    .map(clock::isoformat);
                if reason.observed_at.is_some() && observed_at.is_none() {
                    omission = Some("invalid-value");
                    break;
                }
                reasons.insert(WorkflowRelationReason {
                    kind: reason.kind.clone(),
                    identity: identity.into(),
                    observed_at,
                });
            }
        }
        let kinds: BTreeSet<_> = reasons.iter().map(|r| r.kind.as_str()).collect();
        if omission.is_none() && !kinds.iter().any(|k| STRONG_REASON_KINDS.contains(k)) {
            omission = Some("missing-strong-reason");
        }
        if omission.is_none()
            && ((r.authority == "user-confirmed" && !kinds.contains("user-assertion"))
                || (r.authority == "explicit-organization"
                    && !kinds.contains("thread-membership")
                    && !kinds.contains("workstream-membership")))
        {
            omission = Some("authority-reason-mismatch");
        }
        if let Some(code) = omission {
            result.diagnostics.push(diagnostic(code));
            continue;
        }
        r.source_episode_key = source.clone();
        r.target_episode_key = target.clone();
        r.source_observed_at = source_time.map(clock::isoformat);
        r.target_observed_at = target_time.map(clock::isoformat);
        r.reasons = reasons.into_iter().collect();
        r.projection_version = WORKFLOW_PROJECTION_VERSION.into();
        let key = (
            source.clone(),
            target.clone(),
            r.kind.clone(),
            r.authority.clone(),
            r.reasons.clone(),
        );
        if seen.contains(&key) {
            continue;
        }
        if path_exists(&adjacency, &target, &source) {
            result.diagnostics.push(WorkflowDiagnostic {
                code: "cycle-omitted".into(),
                source_episode_key: Some(source),
                target_episode_key: Some(target),
                relation_kind: Some(r.kind),
            });
            continue;
        }
        seen.insert(key);
        adjacency.entry(source).or_default().insert(target);
        result.relations.push(r);
    }
    result
}
