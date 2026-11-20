//! Supplied-fact candidate descriptors and identities; no source access or I/O.
use super::projection::{canonical_json, workflow_episode_key};
use super::projection::{invalid, opaque_identity, trim};
use crate::backend::Result;
use crate::backend::{clock, unicode, BackendError};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
pub const WORKSTREAM_CANDIDATE_VERSION: &str = "localbrain.workstream-candidate.v1";
pub const ARTIFACT_KINDS: &[&str] = &[
    "context-document",
    "wiki-item",
    "jira-item",
    "local-resource",
    "external-resource",
];
pub const REFERENCE_KINDS: &[&str] = &[
    "user_mention",
    "assistant_mention",
    "resource_read",
    "tool_result",
];
pub const MAX_ARTIFACTS: usize = 2000;
pub const MAX_SESSIONS: usize = 2000;
pub const MAX_REFERENCES: usize = 20000;
pub const MAX_PAIRS: usize = 200;
pub const MAX_MEMBERSHIPS: usize = 2000;
pub const MAX_REFERENCE_SAMPLES: usize = 5;
pub const MAX_LATEST_SAMPLES: usize = 5;
pub const MAX_OVERLAP_SAMPLES: usize = 20;
pub const MAX_IDENTITY_LENGTH: usize = 4096;
pub const MAX_SOURCE_LENGTH: usize = 300;
pub const MAX_TITLE_LENGTH: usize = 500;
fn text<'a>(value: &'a str, field: &str, limit: usize) -> Result<&'a str> {
    let value = trim(value);
    if value.is_empty()
        || value.chars().count() > limit
        || value.chars().any(|ch| (ch as u32) < 32 || ch == '\u{7f}')
    {
        return Err(invalid(&format!(
            "{field} has invalid length or characters"
        )));
    }
    Ok(value)
}
fn opaque<'a>(value: &'a str, prefix: &str) -> Result<&'a str> {
    if value.strip_prefix(&format!("{prefix}:")).is_none_or(|hex| {
        hex.len() != 64
            || !hex
                .bytes()
                .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
    }) {
        return Err(invalid(&format!("invalid {prefix} key")));
    }
    Ok(value)
}
/// The caller supplies the canonical resolved identity, never a guessed alias.
pub fn candidate_artifact_key(
    kind: &str,
    source_scope: &str,
    source_identity: &str,
) -> Result<String> {
    if !ARTIFACT_KINDS.contains(&kind) {
        return Err(invalid("unsupported artifact kind"));
    }
    Ok(opaque_identity(
        "artifact",
        &[
            kind,
            text(source_scope, "source_scope", 300)?,
            text(source_identity, "source_identity", 4096)?,
        ],
    ))
}
pub fn workstream_candidate_key(first: &str, second: &str) -> Result<String> {
    let mut anchors = [opaque(first, "artifact")?, opaque(second, "artifact")?];
    anchors.sort_unstable();
    if anchors[0] == anchors[1] {
        return Err(invalid("candidate requires distinct artifacts"));
    }
    Ok(opaque_identity(
        "candidate",
        &[WORKSTREAM_CANDIDATE_VERSION, anchors[0], anchors[1]],
    ))
}

fn object(row: &Value) -> Result<()> {
    if row.is_object() {
        Ok(())
    } else {
        Err(invalid("normalized fact must be a mapping"))
    }
}
fn field_text<'a>(row: &'a Value, key: &str, limit: usize) -> Result<&'a str> {
    text(
        row.get(key)
            .and_then(Value::as_str)
            .ok_or_else(|| invalid(&format!("{key} must be text")))?,
        key,
        limit,
    )
}
fn enumeration(
    row: &Value,
    key: &str,
    default: Option<&str>,
    allowed: &[&str],
    field: &str,
) -> Result<String> {
    let value = match row.get(key) {
        Some(value) => value.as_str(),
        None => default,
    };
    value
        .filter(|value| allowed.contains(value))
        .map(str::to_string)
        .ok_or_else(|| invalid(&format!("unsupported {field}")))
}
fn flag(row: &Value, key: &str) -> Result<bool> {
    match row.get(key) {
        None => Ok(false),
        Some(value) => value
            .as_bool()
            .ok_or_else(|| invalid(&format!("{key} must be boolean"))),
    }
}
fn title(row: &Value) -> Option<String> {
    row.get("title")
        .and_then(Value::as_str)
        .map(|s| {
            s.split(unicode::python_space)
                .filter(|s| !s.is_empty())
                .collect::<Vec<_>>()
                .join(" ")
                .chars()
                .take(500)
                .collect::<String>()
        })
        .filter(|s| !s.is_empty())
}
fn revision(prefix: &str, value: &Value) -> Result<String> {
    Ok(opaque_identity(prefix, &[&canonical_json(value)?]))
}
fn increment(diagnostics: &mut BTreeMap<String, usize>, key: &str, count: usize) {
    *diagnostics.entry(key.into()).or_default() += count;
}
fn limit(length: usize, max: usize, field: &str) -> Result<()> {
    if length > max {
        Err(BackendError::new(
            422,
            "candidate_limit",
            format!("{field} exceeds the supported bound"),
        ))
    } else {
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateArtifact {
    pub artifact_key: String,
    pub kind: String,
    pub source_scope_key: String,
    pub display_title: Option<String>,
    pub identity_state: String,
    pub enabled: bool,
    pub is_container: bool,
    pub availability: String,
    pub freshness: String,
}
pub fn candidate_artifact_from_record(row: &Value) -> Result<CandidateArtifact> {
    object(row)?;
    let kind = enumeration(row, "kind", None, ARTIFACT_KINDS, "artifact kind")?;
    let scope = field_text(row, "source_scope", 300)?;
    Ok(CandidateArtifact {
        artifact_key: candidate_artifact_key(
            &kind,
            scope,
            field_text(row, "source_identity", 4096)?,
        )?,
        source_scope_key: opaque_identity("source", &[&kind, scope]),
        kind,
        display_title: title(row),
        identity_state: enumeration(
            row,
            "identity_state",
            Some("unresolved"),
            &["resolved", "unresolved", "ambiguous"],
            "identity state",
        )?,
        enabled: flag(row, "enabled")?,
        is_container: flag(row, "is_container")?,
        availability: enumeration(
            row,
            "availability",
            Some("unknown"),
            &["available", "unavailable", "missing", "unknown"],
            "availability",
        )?,
        freshness: enumeration(
            row,
            "freshness",
            Some("unknown"),
            &["current", "stale", "unknown"],
            "freshness",
        )?,
    })
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateSession {
    pub episode_key: String,
    pub session_id: i64,
    pub source_id: i64,
    pub display_title: Option<String>,
    pub destination: String,
}
pub fn candidate_session_from_record(row: &Value) -> Result<CandidateSession> {
    object(row)?;
    if row["session_class"] != "work"
        || row["session_role"] != "primary"
        || row["index_policy"] != "full"
    {
        return Err(BackendError::new(
            422,
            "ineligible-session",
            "ineligible-session",
        ));
    }
    let count = match row.get("event_count") {
        None => 0,
        Some(v) => v
            .as_u64()
            .ok_or_else(|| invalid("event_count must be a non-negative integer"))?,
    };
    let events = flag(row, "has_activity_events")?;
    let usage = flag(row, "has_usage_records")?;
    if count == 0 && !events && !usage {
        return Err(BackendError::new(
            422,
            "ineligible-session",
            "ineligible-session",
        ));
    }
    let id = super::projection::positive(row.get("id"), "session_id")?;
    let source_id = super::projection::positive(row.get("source_id"), "source_id")?;
    Ok(CandidateSession {
        episode_key: workflow_episode_key(source_id, field_text(row, "external_id", 4096)?)?,
        session_id: id,
        source_id,
        display_title: title(row),
        destination: format!("/sessions/{id}"),
    })
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateReference {
    pub reference_key: String,
    pub episode_key: String,
    pub artifact_key: String,
    pub evidence_kind: String,
    pub read_outcome: Option<String>,
    pub observed_at: Option<String>,
    pub authority: String,
}
impl CandidateReference {
    pub fn supports_membership(&self) -> bool {
        if ["user_mention", "assistant_mention"].contains(&self.evidence_kind.as_str()) {
            self.read_outcome.is_none()
        } else {
            self.read_outcome.as_deref() == Some("success")
        }
    }
}
pub fn candidate_reference_from_record(row: &Value) -> Result<CandidateReference> {
    object(row)?;
    let episode = opaque(row["episode_key"].as_str().unwrap_or(""), "session")?;
    let artifact = opaque(row["artifact_key"].as_str().unwrap_or(""), "artifact")?;
    let occurrence = field_text(row, "reference_identity", 4096)?;
    let outcome = match row.get("read_outcome").filter(|v| !v.is_null()) {
        Some(_) => Some(enumeration(
            row,
            "read_outcome",
            None,
            &["success", "failure"],
            "read outcome",
        )?),
        None => None,
    };
    Ok(CandidateReference {
        reference_key: opaque_identity("reference", &[episode, artifact, occurrence]),
        episode_key: episode.into(),
        artifact_key: artifact.into(),
        evidence_kind: enumeration(row, "evidence_kind", None, REFERENCE_KINDS, "evidence kind")?,
        read_outcome: outcome,
        observed_at: row
            .get("observed_at")
            .and_then(Value::as_str)
            .and_then(clock::parse_timestamp)
            .map(clock::stamp),
        authority: "observed".into(),
    })
}
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct CandidateCoverage {
    pub complete: bool,
    pub unexamined_session_count: Option<u64>,
}
impl CandidateCoverage {
    pub fn new(complete: bool, count: Option<u64>) -> Result<Self> {
        let result = Self {
            complete,
            unexamined_session_count: count,
        };
        result.validate()?;
        Ok(result)
    }
    fn validate(&self) -> Result<()> {
        if self.complete && self.unexamined_session_count != Some(0) {
            Err(invalid(
                "complete coverage requires zero unexamined Sessions",
            ))
        } else {
            Ok(())
        }
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateAnchorSupport {
    pub artifact_key: String,
    pub references: Vec<CandidateReference>,
    pub reference_count: usize,
    pub observed_start_at: Option<String>,
    pub last_observed_at: Option<String>,
    pub unknown_time_count: usize,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateMembership {
    pub session: CandidateSession,
    pub supports: Vec<CandidateAnchorSupport>,
    pub authority: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateOverlap {
    pub candidate_key: String,
    pub shared_artifact_count: usize,
    pub shared_session_count: usize,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkstreamCandidate {
    pub candidate_key: String,
    pub anchors: Vec<CandidateArtifact>,
    pub label: String,
    pub label_authority: String,
    pub label_artifact_key: Option<String>,
    pub members: Vec<CandidateMembership>,
    pub membership_revision: String,
    pub observed_start_at: Option<String>,
    pub last_observed_at: Option<String>,
    pub latest_observations: Vec<CandidateReference>,
    pub latest_observation_count: usize,
    pub unknown_time_count: usize,
    pub overlaps: Vec<CandidateOverlap>,
    pub overlap_count: usize,
    pub authority: String,
    pub outcome: Option<String>,
    pub next_action: Option<String>,
    pub activity_state: String,
    pub lifecycle_state: String,
    pub closure_reason: Option<String>,
    pub contract_version: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateDiagnostic {
    pub code: String,
    pub count: usize,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizedWorkstreamCandidates {
    pub candidates: Vec<WorkstreamCandidate>,
    pub diagnostics: Vec<CandidateDiagnostic>,
    pub coverage: CandidateCoverage,
    pub revision: String,
    pub scope: String,
    pub contract_version: String,
}

fn unique_facts<T: PartialEq>(
    rows: &[Value],
    factory: impl Fn(&Value) -> Result<T>,
    key: impl Fn(&T) -> &String,
    kind: &str,
    diagnostics: &mut BTreeMap<String, usize>,
) -> BTreeMap<String, T> {
    let mut facts = BTreeMap::new();
    let mut conflicts = BTreeSet::new();
    for row in rows {
        match factory(row) {
            Err(error) => increment(
                diagnostics,
                if error.code == "ineligible-session" {
                    "ineligible-session"
                } else {
                    match kind {
                        "artifact" => "invalid-artifact",
                        "session" => "invalid-session",
                        _ => "invalid-reference",
                    }
                },
                1,
            ),
            Ok(fact) => {
                let identity = key(&fact).clone();
                if facts.get(&identity).is_some_and(|old| old != &fact) {
                    conflicts.insert(identity);
                } else {
                    facts.insert(identity, fact);
                }
            }
        }
    }
    for identity in &conflicts {
        facts.remove(identity);
    }
    if !conflicts.is_empty() {
        increment(diagnostics, &format!("conflicting-{kind}"), conflicts.len());
    }
    facts
}
fn ordered_references(
    references: impl IntoIterator<Item = CandidateReference>,
) -> Vec<CandidateReference> {
    let mut result: Vec<_> = references.into_iter().collect();
    result.sort_by(|a, b| {
        b.observed_at
            .as_deref()
            .unwrap_or("")
            .cmp(a.observed_at.as_deref().unwrap_or(""))
            .then(a.reference_key.cmp(&b.reference_key))
    });
    result
}
fn bounds(references: &[CandidateReference]) -> (Option<String>, Option<String>) {
    let mut times = references
        .iter()
        .filter_map(|r| r.observed_at.clone())
        .collect::<Vec<_>>();
    times.sort();
    (times.first().cloned(), times.last().cloned())
}
fn candidate(
    anchors: Vec<CandidateArtifact>,
    members: Vec<CandidateMembership>,
    references: Vec<CandidateReference>,
) -> Result<WorkstreamCandidate> {
    let key = workstream_candidate_key(&anchors[0].artifact_key, &anchors[1].artifact_key)?;
    let label_source = anchors
        .iter()
        .filter(|a| a.display_title.is_some())
        .min_by_key(|a| {
            (
                ARTIFACT_KINDS
                    .iter()
                    .position(|kind| *kind == a.kind)
                    .unwrap(),
                a.artifact_key.clone(),
            )
        });
    let (label, label_authority, label_artifact_key) = match label_source {
        Some(a) => (
            a.display_title.clone().unwrap(),
            "source-metadata".into(),
            Some(a.artifact_key.clone()),
        ),
        None => ("Unnamed work candidate".into(), "fallback".into(), None),
    };
    let observations = ordered_references(references);
    let (first, last) = bounds(&observations);
    let latest: Vec<_> = observations
        .iter()
        .filter(|r| last.is_some() && r.observed_at == last)
        .cloned()
        .collect();
    let mut by_key = observations.clone();
    by_key.sort_by(|a, b| a.reference_key.cmp(&b.reference_key));
    let membership_revision = revision(
        "membership",
        &json!({"candidate_key":key,"references":by_key}),
    )?;
    Ok(WorkstreamCandidate {
        candidate_key: key,
        anchors,
        label,
        label_authority,
        label_artifact_key,
        members,
        membership_revision,
        observed_start_at: first,
        last_observed_at: last,
        latest_observations: latest.iter().take(5).cloned().collect(),
        latest_observation_count: latest.len(),
        unknown_time_count: observations
            .iter()
            .filter(|r| r.observed_at.is_none())
            .count(),
        overlaps: vec![],
        overlap_count: 0,
        authority: "deterministic-candidate".into(),
        outcome: None,
        next_action: None,
        activity_state: "unknown".into(),
        lifecycle_state: "unknown".into(),
        closure_reason: None,
        contract_version: WORKSTREAM_CANDIDATE_VERSION.into(),
    })
}
/// Validate the complete supplied scope. A hard limit fails the whole call;
/// bounded reference/overlap samples retain their observed totals and revision.
pub fn normalize_workstream_candidates(
    artifacts: &[Value],
    sessions: &[Value],
    references: &[Value],
    pairs: &[Value],
    coverage: Option<CandidateCoverage>,
) -> Result<NormalizedWorkstreamCandidates> {
    let coverage = coverage.unwrap_or_default();
    coverage.validate()?;
    for (rows, max, name) in [
        (artifacts, MAX_ARTIFACTS, "artifacts"),
        (sessions, MAX_SESSIONS, "sessions"),
        (references, MAX_REFERENCES, "references"),
        (pairs, MAX_PAIRS, "pairs"),
    ] {
        limit(rows.len(), max, name)?;
    }
    let mut diagnostics = BTreeMap::new();
    let artifact_facts = unique_facts(
        artifacts,
        candidate_artifact_from_record,
        |a| &a.artifact_key,
        "artifact",
        &mut diagnostics,
    );
    let session_facts = unique_facts(
        sessions,
        candidate_session_from_record,
        |a| &a.episode_key,
        "session",
        &mut diagnostics,
    );
    let reference_facts = unique_facts(
        references,
        candidate_reference_from_record,
        |a| &a.reference_key,
        "reference",
        &mut diagnostics,
    );
    let mut admitted = BTreeMap::new();
    for (key, fact) in &artifact_facts {
        let omission = if !fact.enabled {
            Some("disabled-artifact")
        } else if fact.identity_state != "resolved" {
            Some(if fact.identity_state == "ambiguous" {
                "ambiguous-artifact"
            } else {
                "unresolved-artifact"
            })
        } else if fact.is_container {
            Some("container-artifact")
        } else {
            None
        };
        if let Some(code) = omission {
            increment(&mut diagnostics, code, 1);
        } else {
            admitted.insert(key.clone(), fact.clone());
        }
    }
    let mut supports = BTreeMap::<String, BTreeMap<String, Vec<CandidateReference>>>::new();
    for reference in reference_facts.into_values() {
        let omission = if !session_facts.contains_key(&reference.episode_key) {
            Some("missing-session")
        } else if !artifact_facts.contains_key(&reference.artifact_key) {
            Some("missing-artifact")
        } else if !admitted.contains_key(&reference.artifact_key) {
            Some("excluded-reference")
        } else if !reference.supports_membership() {
            Some("weak-reference")
        } else {
            None
        };
        if let Some(code) = omission {
            increment(&mut diagnostics, code, 1);
        } else {
            supports
                .entry(reference.episode_key.clone())
                .or_default()
                .entry(reference.artifact_key.clone())
                .or_default()
                .push(reference);
        }
    }
    let mut unique_pairs = BTreeSet::new();
    for pair in pairs {
        let valid = pair
            .as_array()
            .filter(|pair| pair.len() == 2)
            .and_then(|pair| {
                Some((
                    opaque(pair[0].as_str()?, "artifact").ok()?.to_string(),
                    opaque(pair[1].as_str()?, "artifact").ok()?.to_string(),
                ))
            })
            .filter(|(a, b)| a != b);
        if let Some((a, b)) = valid {
            unique_pairs.insert(if a < b { [a, b] } else { [b, a] });
        } else {
            increment(&mut diagnostics, "invalid-pair", 1);
        }
    }
    let mut candidates = vec![];
    let mut membership_count = 0;
    for pair in unique_pairs {
        if pair.iter().any(|key| !artifact_facts.contains_key(key)) {
            increment(&mut diagnostics, "missing-pair-anchor", 1);
            continue;
        }
        if pair.iter().any(|key| !admitted.contains_key(key)) {
            increment(&mut diagnostics, "excluded-pair", 1);
            continue;
        }
        let mut members = vec![];
        let mut full_evidence = vec![];
        for (episode, evidence) in &supports {
            if !pair.iter().all(|key| evidence.contains_key(key)) {
                continue;
            }
            let mut anchor_supports = vec![];
            for key in &pair {
                let ordered = ordered_references(evidence[key].clone());
                let (first, last) = bounds(&ordered);
                anchor_supports.push(CandidateAnchorSupport {
                    artifact_key: key.clone(),
                    references: ordered.iter().take(5).cloned().collect(),
                    reference_count: ordered.len(),
                    observed_start_at: first,
                    last_observed_at: last,
                    unknown_time_count: ordered.iter().filter(|r| r.observed_at.is_none()).count(),
                });
                full_evidence.extend(ordered);
            }
            members.push(CandidateMembership {
                session: session_facts[episode].clone(),
                supports: anchor_supports,
                authority: "deterministic-candidate".into(),
            });
        }
        if members.len() < 2 {
            increment(&mut diagnostics, "insufficient-sessions", 1);
            continue;
        }
        membership_count += members.len();
        limit(membership_count, MAX_MEMBERSHIPS, "memberships")?;
        candidates.push(candidate(
            pair.iter().map(|key| admitted[key].clone()).collect(),
            members,
            full_evidence,
        )?);
    }
    candidates.sort_by(|a, b| a.candidate_key.cmp(&b.candidate_key));
    let member_keys: Vec<BTreeSet<_>> = candidates
        .iter()
        .map(|candidate| {
            candidate
                .members
                .iter()
                .map(|m| m.session.episode_key.clone())
                .collect()
        })
        .collect();
    let anchor_keys: Vec<BTreeSet<_>> = candidates
        .iter()
        .map(|candidate| {
            candidate
                .anchors
                .iter()
                .map(|a| a.artifact_key.clone())
                .collect()
        })
        .collect();
    for i in 0..candidates.len() {
        let mut overlaps = vec![];
        for j in 0..candidates.len() {
            if i == j {
                continue;
            }
            let shared_artifact_count = anchor_keys[i].intersection(&anchor_keys[j]).count();
            let shared_session_count = member_keys[i].intersection(&member_keys[j]).count();
            if shared_artifact_count > 0 || shared_session_count > 0 {
                overlaps.push(CandidateOverlap {
                    candidate_key: candidates[j].candidate_key.clone(),
                    shared_artifact_count,
                    shared_session_count,
                });
            }
        }
        candidates[i].overlap_count = overlaps.len();
        overlaps.truncate(20);
        candidates[i].overlaps = overlaps;
    }
    let mut result = NormalizedWorkstreamCandidates {
        candidates,
        diagnostics: diagnostics
            .into_iter()
            .map(|(code, count)| CandidateDiagnostic { code, count })
            .collect(),
        coverage,
        revision: String::new(),
        scope: "supplied-facts".into(),
        contract_version: WORKSTREAM_CANDIDATE_VERSION.into(),
    };
    result.revision = revision("projection", &serde_json::to_value(&result)?)?;
    Ok(result)
}
