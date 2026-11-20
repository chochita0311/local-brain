//! Deterministic read-only Focus over normalized SQLite metadata and references.
use super::projection::*;
use crate::backend::{clock, db, unicode, Result};
use chrono::{DateTime, Utc};
use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{
    cmp::Ordering,
    collections::{BTreeMap, BTreeSet},
};

pub const WORKFLOW_FOCUS_VERSION: &str = "localbrain.workflow-focus.v1";
pub const MAX_WORKFLOW_CANDIDATES: usize = 200;
pub const MAX_WORKFLOW_EPISODES: usize = 24;
pub const MAX_WORKFLOW_BRANCH_ROOTS: usize = 4;
pub const MAX_WORKFLOW_BRANCH_EPISODES: usize = 4;
pub const MAX_WORKFLOW_EVIDENCE_PER_FAMILY: usize = 5;
const AVAILABILITIES: &[&str] = &[
    "available",
    "stale",
    "unavailable",
    "missing",
    "archived",
    "unknown",
];
const EVIDENCE_AUTHORITIES: &[&str] = &["observed", "explicit-organization"];

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowEvidenceItem {
    pub evidence_key: String,
    pub source_family: String,
    pub identity: String,
    pub destination: Option<String>,
    pub source_id: Option<i64>,
    pub evidence_kind: String,
    pub admission_reasons: Vec<String>,
    pub observed_at: Option<String>,
    pub availability: String,
    pub authority: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowEvidenceGroup {
    pub source_family: String,
    pub items: Vec<WorkflowEvidenceItem>,
    pub retained_total: usize,
    pub observed_total: usize,
    pub partial: bool,
    pub stale: bool,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowEpisodeView {
    pub episode: WorkflowEpisode,
    pub evidence_groups: Vec<WorkflowEvidenceGroup>,
    pub evidence_retained_total: usize,
    pub evidence_observed_total: usize,
    pub evidence_partial: bool,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowFocusProjection {
    pub status: String,
    pub selected_episode_key: Option<String>,
    pub episodes: Vec<WorkflowEpisodeView>,
    pub relations: Vec<WorkflowRelation>,
    pub diagnostics: Vec<WorkflowDiagnostic>,
    pub candidate_observed_total: usize,
    pub candidate_retained_total: usize,
    pub episode_observed_total: usize,
    pub episode_retained_total: usize,
    pub branch_root_observed_total: usize,
    pub branch_root_retained_total: usize,
    pub projection_version: String,
    pub base_relations: Vec<WorkflowRelation>,
    pub base_episode_lifecycle: Vec<Value>,
    pub assertions: Vec<Value>,
    pub assertion_diagnostics: Vec<Value>,
    pub assertion_revision: Option<String>,
    pub assertion_overlay_version: Option<String>,
}
impl WorkflowFocusProjection {
    pub(super) fn empty(status: &str) -> Self {
        Self {
            status: status.into(),
            selected_episode_key: None,
            episodes: vec![],
            relations: vec![],
            diagnostics: vec![],
            candidate_observed_total: 0,
            candidate_retained_total: 0,
            episode_observed_total: 0,
            episode_retained_total: 0,
            branch_root_observed_total: 0,
            branch_root_retained_total: 0,
            projection_version: WORKFLOW_FOCUS_VERSION.into(),
            base_relations: vec![],
            base_episode_lifecycle: vec![],
            assertions: vec![],
            assertion_diagnostics: vec![],
            assertion_revision: None,
            assertion_overlay_version: None,
        }
    }
}
#[derive(Debug, Clone)]
struct SessionFact {
    episode: WorkflowEpisode,
    instant: Option<DateTime<Utc>>,
    workspace_id: Option<i64>,
    git_root: Option<String>,
    git_branch: Option<String>,
    thread_ids: BTreeSet<i64>,
    workstream_ids: BTreeSet<i64>,
    reference_keys: BTreeSet<(String, String)>,
}
type EdgeKey = (String, String, String);
#[derive(Debug, Clone)]
struct EdgeProposal {
    source_key: String,
    target_key: String,
    kind: String,
    priority: u8,
    reasons: Vec<WorkflowRelationReason>,
    source_at: String,
    target_at: String,
}

/// Shares the precise work/primary/full/meaningful predicate with Focus, and
/// reads only metadata. No source refresh, transcript parse or mutation occurs.
pub fn workflow_session_is_eligible(connection: &Connection, session_id: i64) -> Result<bool> {
    if session_id <= 0 {
        return Err(invalid("session_id must be a positive integer"));
    }
    Ok(connection.query_row("SELECT EXISTS(SELECT 1 FROM sessions JOIN sources ON sources.id=sessions.source_id WHERE sessions.id=? AND sessions.session_class='work' AND sessions.session_role='primary' AND sessions.index_policy='full' AND (sessions.event_count>0 OR EXISTS(SELECT 1 FROM activity_events WHERE session_id=sessions.id) OR EXISTS(SELECT 1 FROM usage_records WHERE session_id=sessions.id)))",[session_id],|row|row.get(0))?)
}
fn session_row(connection: &Connection, id: i64) -> Result<Option<Value>> {
    db::row(connection,"SELECT sessions.*, workspaces.display_name AS workspace_name, workspaces.git_root, (SELECT activity_events.occurred_at FROM activity_events WHERE activity_events.session_id=sessions.id AND julianday(activity_events.occurred_at) IS NOT NULL ORDER BY julianday(activity_events.occurred_at),activity_events.occurred_at,activity_events.id LIMIT 1) AS first_event_at FROM sessions JOIN sources ON sources.id=sessions.source_id LEFT JOIN workspaces ON workspaces.id=sessions.workspace_id WHERE sessions.id=?",[id])
}
fn eligible_rows(connection: &Connection) -> Result<Vec<Value>> {
    db::rows(connection,"SELECT sessions.*,workspaces.display_name AS workspace_name,workspaces.git_root,(SELECT activity_events.occurred_at FROM activity_events WHERE activity_events.session_id=sessions.id AND julianday(activity_events.occurred_at) IS NOT NULL ORDER BY julianday(activity_events.occurred_at),activity_events.occurred_at,activity_events.id LIMIT 1) AS first_event_at,(SELECT COUNT(*) FROM sessions AS children WHERE children.parent_session_id=sessions.id AND children.source_id=sessions.source_id AND children.session_class='work' AND children.session_role='subsession') AS subsession_count FROM sessions JOIN sources ON sources.id=sessions.source_id LEFT JOIN workspaces ON workspaces.id=sessions.workspace_id WHERE sessions.session_class='work' AND sessions.session_role='primary' AND sessions.index_policy='full' AND (sessions.event_count>0 OR EXISTS(SELECT 1 FROM activity_events WHERE activity_events.session_id=sessions.id) OR EXISTS(SELECT 1 FROM usage_records WHERE usage_records.session_id=sessions.id)) ORDER BY sessions.id",[])
}
fn entity_id(value: &Value) -> Option<i64> {
    if let Some(value) = value.as_i64() {
        return (value > 0).then_some(value);
    }
    let value = value.as_str()?.trim_matches(|ch| {
        matches!(ch, '\t'..='\r' | ' ') || (ch as u32 >= 128 && unicode::python_space(ch))
    });
    let value = value.strip_prefix('+').unwrap_or(value);
    if value.is_empty() {
        return None;
    }
    let mut result = 0i64;
    let mut previous_digit = false;
    for ch in value.chars() {
        if ch == '_' {
            if !previous_digit {
                return None;
            }
            previous_digit = false;
            continue;
        }
        if unicode_general_category::get_general_category(ch)
            != unicode_general_category::GeneralCategory::DecimalNumber
        {
            return None;
        }
        let mut start = ch as u32;
        while start > 0
            && char::from_u32(start - 1).is_some_and(|ch| {
                unicode_general_category::get_general_category(ch)
                    == unicode_general_category::GeneralCategory::DecimalNumber
            })
        {
            start -= 1;
        }
        result = result
            .checked_mul(10)?
            .checked_add(((ch as u32 - start) % 10) as i64)?;
        previous_digit = true;
    }
    (previous_digit && result > 0).then_some(result)
}
type Memberships = BTreeMap<i64, BTreeSet<i64>>;
fn user_memberships(connection: &Connection) -> Result<(Memberships, Memberships)> {
    let mut threads = Memberships::new();
    let mut workstreams = Memberships::new();
    for row in db::rows(connection,"SELECT 'workstream' AS scope_kind,workstream_links.workstream_id AS workstream_id,NULL AS thread_id,workstream_links.entity_id AS session_id FROM workstream_links WHERE workstream_links.entity_type='session' AND workstream_links.linked_by='user' UNION ALL SELECT 'thread',threads.workstream_id,thread_links.thread_id,thread_links.entity_id FROM thread_links JOIN threads ON threads.id=thread_links.thread_id WHERE thread_links.entity_type='session' AND thread_links.linked_by='user' ORDER BY scope_kind,workstream_id,thread_id,session_id",[])? {
        let Some(session)=entity_id(&row["session_id"])else{continue};
        workstreams.entry(session).or_default().insert(row["workstream_id"].as_i64().unwrap());if let Some(thread)=row["thread_id"].as_i64(){threads.entry(session).or_default().insert(thread);}
    }
    Ok((threads, workstreams))
}
fn reference_keys(connection: &Connection) -> Result<BTreeMap<i64, BTreeSet<(String, String)>>> {
    let mut result = BTreeMap::<i64, BTreeSet<_>>::new();
    for row in db::rows(connection,"SELECT e.session_id,r.kind AS target_kind,e.target_key FROM session_reference_evidence e JOIN reference_resources r ON r.id=e.resource_id GROUP BY e.session_id,r.kind,e.target_key ORDER BY e.session_id,r.kind,e.target_key",[])? {result.entry(row["session_id"].as_i64().unwrap()).or_default().insert((row["target_kind"].as_str().unwrap().into(),row["target_key"].as_str().unwrap().into()));}
    Ok(result)
}
fn session_facts(connection: &Connection) -> Result<BTreeMap<i64, SessionFact>> {
    let (threads, workstreams) = user_memberships(connection)?;
    let references = reference_keys(connection)?;
    let mut result = BTreeMap::new();
    for row in eligible_rows(connection)? {
        let id = row["id"].as_i64().unwrap();
        let thread_ids = threads.get(&id).cloned().unwrap_or_default();
        let workstream_ids = workstreams.get(&id).cloned().unwrap_or_default();
        let reference_keys = references.get(&id).cloned().unwrap_or_default();
        let counts = BTreeMap::from([
            ("references".into(), reference_keys.len() as u64),
            ("threads".into(), thread_ids.len() as u64),
            ("workstreams".into(), workstream_ids.len() as u64),
            (
                "subsessions".into(),
                row["subsession_count"].as_i64().unwrap_or(0).max(0) as u64,
            ),
        ]);
        let episode = workflow_episode_from_session(
            &row,
            &EpisodeOptions {
                first_event_at: row.get("first_event_at").cloned(),
                evidence_counts: counts,
                ..Default::default()
            },
        )?;
        let instant = episode
            .last_observed_at
            .as_deref()
            .or(episode.observed_start_at.as_deref())
            .and_then(clock::parse_timestamp);
        result.insert(
            id,
            SessionFact {
                episode,
                instant,
                workspace_id: row["workspace_id"].as_i64(),
                git_root: bounded(row.get("git_root"), 8000),
                git_branch: bounded(row.get("git_branch"), 500),
                thread_ids,
                workstream_ids,
                reference_keys,
            },
        );
    }
    Ok(result)
}
fn same_root(a: &SessionFact, b: &SessionFact) -> bool {
    a.git_root.is_some() && a.git_root == b.git_root
}
fn same_branch(a: &SessionFact, b: &SessionFact) -> bool {
    a.git_branch.is_some() && a.git_branch == b.git_branch
}
fn candidate_strength(a: &SessionFact, b: &SessionFact) -> Option<u8> {
    let threads = !a.thread_ids.is_disjoint(&b.thread_ids);
    let workstreams = !a.workstream_ids.is_disjoint(&b.workstream_ids);
    let references = !a.reference_keys.is_disjoint(&b.reference_keys);
    if threads {
        Some(0)
    } else if references && workstreams {
        Some(1)
    } else if references && same_root(a, b) && same_branch(a, b) {
        Some(2)
    } else if references
        && ((a.workspace_id.is_some() && a.workspace_id == b.workspace_id) || same_root(a, b))
    {
        Some(3)
    } else if workstreams && same_root(a, b) {
        Some(if same_branch(a, b) { 4 } else { 5 })
    } else {
        None
    }
}
fn temporal_distance(a: Option<DateTime<Utc>>, b: Option<DateTime<Utc>>) -> f64 {
    match (a, b) {
        (Some(a), Some(b)) => {
            (a.timestamp_micros() - b.timestamp_micros()).unsigned_abs() as f64 / 1e6
        }
        _ => f64::INFINITY,
    }
}
fn instant_order(a: Option<DateTime<Utc>>, b: Option<DateTime<Utc>>) -> Ordering {
    match (a, b) {
        (None, None) => Ordering::Equal,
        (None, Some(_)) => Ordering::Greater,
        (Some(_), None) => Ordering::Less,
        (Some(a), Some(b)) => {
            (a.timestamp_micros() as f64 / 1e6).total_cmp(&(b.timestamp_micros() as f64 / 1e6))
        }
    }
}
fn ordered_candidates(
    selected: &SessionFact,
    facts: &BTreeMap<i64, SessionFact>,
) -> (Vec<SessionFact>, usize) {
    let mut result: Vec<_> = facts
        .values()
        .filter(|fact| fact.episode.episode_key != selected.episode.episode_key)
        .filter_map(|fact| candidate_strength(selected, fact).map(|strength| (strength, fact)))
        .collect();
    result.sort_by(|(a, fa), (b, fb)| {
        a.cmp(b)
            .then(
                temporal_distance(selected.instant, fa.instant)
                    .total_cmp(&temporal_distance(selected.instant, fb.instant)),
            )
            .then(instant_order(fa.instant, fb.instant))
            .then(fa.episode.episode_key.cmp(&fb.episode.episode_key))
    });
    let total = result.len();
    (
        result
            .into_iter()
            .take(200)
            .map(|(_, fact)| fact.clone())
            .collect(),
        total,
    )
}
fn ordered_group<'a>(facts: impl IntoIterator<Item = &'a SessionFact>) -> Vec<&'a SessionFact> {
    let mut values: Vec<_> = facts
        .into_iter()
        .filter(|fact| fact.instant.is_some())
        .collect();
    values.sort_by(|a, b| {
        a.instant
            .cmp(&b.instant)
            .then(a.episode.episode_key.cmp(&b.episode.episode_key))
    });
    values
}
fn reason(kind: &str, identity: String) -> WorkflowRelationReason {
    WorkflowRelationReason {
        kind: kind.into(),
        identity,
        observed_at: None,
    }
}
fn reference_reason(reference: &(String, String)) -> WorkflowRelationReason {
    reason(
        "shared-reference",
        format!("reference:{}:{}", reference.0, reference.1),
    )
}
fn git_reasons(fact: &SessionFact) -> Vec<WorkflowRelationReason> {
    let Some(root) = &fact.git_root else {
        return vec![];
    };
    let mut result = vec![reason(
        "same-git-root",
        opaque_identity("git-root", &[root]),
    )];
    if let Some(branch) = &fact.git_branch {
        result.push(reason(
            "same-git-branch",
            opaque_identity("git-branch", &[root, branch]),
        ));
    }
    result
}
fn add_edge(
    proposals: &mut BTreeMap<EdgeKey, EdgeProposal>,
    a: &SessionFact,
    b: &SessionFact,
    kind: &str,
    priority: u8,
    reasons: Vec<WorkflowRelationReason>,
) {
    let (Some(at), Some(bt)) = (a.instant, b.instant) else {
        return;
    };
    if at == bt {
        return;
    }
    let (source, target) = if at < bt { (a, b) } else { (b, a) };
    let (Some(source_at), Some(target_at)) = (
        source
            .episode
            .last_observed_at
            .as_ref()
            .or(source.episode.observed_start_at.as_ref()),
        target
            .episode
            .last_observed_at
            .as_ref()
            .or(target.episode.observed_start_at.as_ref()),
    ) else {
        return;
    };
    let reasons: BTreeSet<_> = reasons.into_iter().collect();
    let key = (
        source.episode.episode_key.clone(),
        target.episode.episode_key.clone(),
        kind.into(),
    );
    match proposals.get_mut(&key) {
        Some(old) if priority > old.priority => {}
        Some(old) if priority == old.priority => {
            old.reasons.extend(reasons);
            old.reasons.sort();
            old.reasons.dedup();
        }
        _ => {
            proposals.insert(
                key.clone(),
                EdgeProposal {
                    source_key: key.0,
                    target_key: key.1,
                    kind: key.2,
                    priority,
                    reasons: reasons.into_iter().collect(),
                    source_at: source_at.clone(),
                    target_at: target_at.clone(),
                },
            );
        }
    }
}
fn normalized_relations(
    facts: &[SessionFact],
) -> (NormalizedWorkflowRelations, BTreeMap<EdgeKey, u8>) {
    let mut proposals = BTreeMap::new();
    let mut by_thread = BTreeMap::<i64, Vec<&SessionFact>>::new();
    let mut by_ref_stream = BTreeMap::<((String, String), i64), Vec<&SessionFact>>::new();
    let mut by_ref_git = BTreeMap::<((String, String), String, String), Vec<&SessionFact>>::new();
    for fact in facts {
        for id in &fact.thread_ids {
            by_thread.entry(*id).or_default().push(fact);
        }
        for reference in &fact.reference_keys {
            for id in &fact.workstream_ids {
                by_ref_stream
                    .entry((reference.clone(), *id))
                    .or_default()
                    .push(fact);
            }
            if let (Some(root), Some(branch)) = (&fact.git_root, &fact.git_branch) {
                by_ref_git
                    .entry((reference.clone(), root.clone(), branch.clone()))
                    .or_default()
                    .push(fact);
            }
        }
    }
    for (thread, members) in by_thread {
        for pair in ordered_group(members).windows(2) {
            add_edge(
                &mut proposals,
                pair[0],
                pair[1],
                "continues",
                20,
                vec![reason("thread-membership", format!("thread:{thread}"))],
            );
        }
    }
    for ((reference, stream), members) in by_ref_stream {
        for pair in ordered_group(members).windows(2) {
            add_edge(
                &mut proposals,
                pair[0],
                pair[1],
                "continues",
                30,
                vec![
                    reference_reason(&reference),
                    reason("workstream-membership", format!("workstream:{stream}")),
                ],
            );
        }
    }
    for ((reference, _, _), members) in by_ref_git {
        for pair in ordered_group(members).windows(2) {
            let mut reasons = vec![reference_reason(&reference)];
            reasons.extend(git_reasons(pair[0]));
            add_edge(&mut proposals, pair[0], pair[1], "continues", 40, reasons);
        }
    }
    let ordered = ordered_group(facts);
    for (index, target) in ordered.iter().enumerate() {
        if target.git_root.is_none() || target.git_branch.is_none() {
            continue;
        }
        if ordered[..index].iter().any(|source| {
            source.git_root == target.git_root
                && source.git_branch == target.git_branch
                && (!source.thread_ids.is_disjoint(&target.thread_ids)
                    || !source.reference_keys.is_disjoint(&target.reference_keys))
        }) {
            continue;
        }
        let mut candidates = vec![];
        for source in &ordered[..index] {
            if !same_root(source, target)
                || source.git_branch.is_none()
                || source.git_branch == target.git_branch
            {
                continue;
            }
            let refs: BTreeSet<_> = source
                .reference_keys
                .intersection(&target.reference_keys)
                .cloned()
                .collect();
            let threads: BTreeSet<_> = source
                .thread_ids
                .intersection(&target.thread_ids)
                .copied()
                .collect();
            let streams: BTreeSet<_> = source
                .workstream_ids
                .intersection(&target.workstream_ids)
                .copied()
                .collect();
            if refs.is_empty() && threads.is_empty() && streams.is_empty() {
                continue;
            }
            let rank = if !refs.is_empty() {
                0
            } else if !threads.is_empty() {
                1
            } else {
                2
            };
            candidates.push((source, rank, refs, threads, streams));
        }
        candidates.sort_by(|(a, ra, ..), (b, rb, ..)| {
            temporal_distance(a.instant, target.instant)
                .total_cmp(&temporal_distance(b.instant, target.instant))
                .then(ra.cmp(rb))
                .then(a.episode.episode_key.cmp(&b.episode.episode_key))
        });
        if let Some((source, rank, refs, threads, streams)) = candidates.first() {
            let mut reasons = vec![if let Some(reference) = refs.first() {
                reference_reason(reference)
            } else if let Some(thread) = threads.first() {
                reason("thread-membership", format!("thread:{thread}"))
            } else {
                reason(
                    "workstream-membership",
                    format!("workstream:{}", streams.first().unwrap()),
                )
            }];
            reasons.extend(git_reasons(source).into_iter().take(1));
            add_edge(
                &mut proposals,
                source,
                target,
                "branches-from",
                *rank,
                reasons,
            );
        }
    }
    let mut by_target = BTreeMap::<String, Vec<EdgeProposal>>::new();
    for proposal in proposals.into_values() {
        by_target
            .entry(proposal.target_key.clone())
            .or_default()
            .push(proposal);
    }
    let mut selected = vec![];
    let mut priorities = BTreeMap::new();
    for (_, mut proposals) in by_target {
        proposals.sort_by(|a, b| {
            a.priority
                .cmp(&b.priority)
                .then(
                    temporal_distance(
                        clock::parse_timestamp(&a.source_at),
                        clock::parse_timestamp(&a.target_at),
                    )
                    .total_cmp(&temporal_distance(
                        clock::parse_timestamp(&b.source_at),
                        clock::parse_timestamp(&b.target_at),
                    )),
                )
                .then(a.source_key.cmp(&b.source_key))
                .then(a.kind.cmp(&b.kind))
        });
        let proposal = proposals.remove(0);
        priorities.insert(
            (
                proposal.source_key.clone(),
                proposal.target_key.clone(),
                proposal.kind.clone(),
            ),
            proposal.priority,
        );
        selected.push(WorkflowRelation {
            source_episode_key: proposal.source_key,
            target_episode_key: proposal.target_key,
            kind: proposal.kind,
            authority: "deterministic-candidate".into(),
            reasons: proposal.reasons,
            source_observed_at: Some(proposal.source_at),
            target_observed_at: Some(proposal.target_at),
            projection_version: WORKFLOW_PROJECTION_VERSION.into(),
        });
    }
    (normalize_workflow_relations(selected), priorities)
}

fn focus_neighborhood(
    selected: &SessionFact,
    facts: &BTreeMap<String, SessionFact>,
    normalized: &NormalizedWorkflowRelations,
    priorities: &BTreeMap<EdgeKey, u8>,
    ranks: &BTreeMap<String, usize>,
) -> (BTreeSet<String>, BTreeSet<EdgeKey>, usize, usize, usize) {
    let mut adjacency = BTreeMap::<String, Vec<(usize, bool)>>::new();
    for (index, relation) in normalized.relations.iter().enumerate() {
        adjacency
            .entry(relation.source_episode_key.clone())
            .or_default()
            .push((index, true));
        adjacency
            .entry(relation.target_episode_key.clone())
            .or_default()
            .push((index, false));
    }
    let selected = selected.episode.episode_key.clone();
    let mut connected = BTreeSet::from([selected.clone()]);
    let mut pending = vec![selected.clone()];
    while let Some(current) = pending.pop() {
        for (index, forward) in adjacency.get(&current).into_iter().flatten() {
            let relation = &normalized.relations[*index];
            let neighbor = if *forward {
                &relation.target_episode_key
            } else {
                &relation.source_episode_key
            };
            if connected.insert(neighbor.clone()) {
                pending.push(neighbor.clone());
            }
        }
    }
    let observed_roots: BTreeSet<_> = normalized
        .relations
        .iter()
        .filter(|r| {
            r.kind == "branches-from"
                && connected.contains(&r.source_episode_key)
                && connected.contains(&r.target_episode_key)
        })
        .map(|r| r.target_episode_key.clone())
        .collect();
    let mut retained = BTreeSet::from([selected.clone()]);
    let mut owners = BTreeMap::from([(selected, None::<String>)]);
    let mut branch_counts = BTreeMap::<String, usize>::new();
    let mut retained_roots = BTreeSet::new();
    let mut traversed = BTreeSet::new();
    while retained.len() < MAX_WORKFLOW_EPISODES {
        let mut options = vec![];
        for current in &retained {
            for (index, forward) in adjacency.get(current).into_iter().flatten() {
                let relation = &normalized.relations[*index];
                let neighbor = if *forward {
                    &relation.target_episode_key
                } else {
                    &relation.source_episode_key
                };
                if retained.contains(neighbor) || !connected.contains(neighbor) {
                    continue;
                }
                let key = (
                    relation.source_episode_key.clone(),
                    relation.target_episode_key.clone(),
                    relation.kind.clone(),
                );
                options.push((
                    *ranks
                        .get(neighbor)
                        .unwrap_or(&(MAX_WORKFLOW_CANDIDATES + 1)),
                    if relation.kind == "continues" {
                        0u8
                    } else {
                        1u8
                    },
                    *priorities.get(&key).unwrap_or(&99),
                    facts[neighbor].instant,
                    neighbor.clone(),
                    current.clone(),
                    *index,
                    *forward,
                ));
            }
        }
        options.sort_by(|a, b| {
            a.0.cmp(&b.0)
                .then(a.1.cmp(&b.1))
                .then(a.2.cmp(&b.2))
                .then(instant_order(a.3, b.3))
                .then(a.4.cmp(&b.4))
        });
        let mut accepted = false;
        for (_, _, _, _, neighbor, current, index, forward) in options {
            let relation = &normalized.relations[index];
            let owner = owners.get(&current).cloned().flatten();
            let next_owner = if relation.kind == "branches-from" {
                let root = relation.target_episode_key.clone();
                if !retained_roots.contains(&root) {
                    if retained_roots.len() >= MAX_WORKFLOW_BRANCH_ROOTS {
                        continue;
                    }
                    retained_roots.insert(root.clone());
                    branch_counts.insert(root.clone(), if forward { 0 } else { 1 });
                }
                if forward {
                    Some(root)
                } else {
                    None
                }
            } else {
                owner
            };
            if next_owner.as_ref().is_some_and(|owner| {
                branch_counts.get(owner).copied().unwrap_or(0) >= MAX_WORKFLOW_BRANCH_EPISODES
            }) {
                continue;
            }
            retained.insert(neighbor.clone());
            owners.insert(neighbor, next_owner.clone());
            if let Some(owner) = next_owner {
                *branch_counts.entry(owner).or_default() += 1;
            }
            traversed.insert((
                relation.source_episode_key.clone(),
                relation.target_episode_key.clone(),
                relation.kind.clone(),
            ));
            accepted = true;
            break;
        }
        if !accepted {
            break;
        }
    }
    (
        retained,
        traversed,
        connected.len(),
        observed_roots.len(),
        retained_roots.len(),
    )
}

fn related_family(item: &Value) -> &'static str {
    let kind = item["entity_type"].as_str().unwrap_or("");
    let label = unicode::casefold(item["kind_label"].as_str().unwrap_or(""));
    if kind == "document" {
        "local-context"
    } else if kind == "atlassian" || ["jira", "confluence", "wiki"].contains(&label.as_str()) {
        "atlassian"
    } else if kind == "local" {
        "local-resource"
    } else if label == "slack" {
        "slack"
    } else if label == "git" {
        "git"
    } else {
        "external"
    }
}
fn availability(value: Option<&Value>, stale: bool) -> String {
    let value = value.and_then(Value::as_str).unwrap_or("unknown");
    if stale && value == "available" {
        "stale".into()
    } else if AVAILABILITIES.contains(&value) {
        value.into()
    } else {
        "unknown".into()
    }
}
fn array(value: Option<&Value>) -> Result<&[Value]> {
    match value {
        None => Ok(&[]),
        Some(Value::Array(values)) => Ok(values),
        _ => Err(crate::backend::BackendError::new(
            500,
            "workflow_projection",
            "Invalid normalized Related Context projection",
        )),
    }
}
type EvidenceHints = BTreeMap<String, usize>;
fn related_evidence(
    connection: &Connection,
    fact: &SessionFact,
) -> Result<(Vec<WorkflowEvidenceItem>, EvidenceHints, BTreeSet<String>)> {
    let projection = crate::backend::resources::related_context::session_related_context(
        connection,
        fact.episode.session_id,
    )?;
    let mut items = vec![];
    let mut hints = EvidenceHints::new();
    let mut stale_families = BTreeSet::new();
    for group in array(projection.get("groups"))? {
        let group_items = array(group.get("items"))?;
        let stale = group["stale"].as_bool().unwrap_or(false);
        for raw in group_items {
            let family = related_family(raw).to_string();
            *hints.entry(family.clone()).or_default() += 1;
            let direct = group["key"] == "direct";
            let mut reasons = BTreeSet::from([if direct {
                "direct-reference".to_string()
            } else {
                "organization".to_string()
            }]);
            for organization in array(raw.get("organization"))? {
                if let Some(kind) = organization["kind"]
                    .as_str()
                    .filter(|kind| ["thread", "workstream"].contains(kind))
                {
                    reasons.insert(format!("{kind}-membership"));
                }
            }
            let evidence = array(raw.get("evidence"))?;
            let kind = if direct && !evidence.is_empty() {
                evidence[0]["kind"].as_str().unwrap_or("None").to_string()
            } else {
                "organization-link".into()
            };
            let identity =
                bounded(raw.get("identity"), 500).unwrap_or_else(|| "Unknown evidence".into());
            let target = bounded(raw.get("target_key"), 500)
                .unwrap_or_else(|| opaque_identity("evidence", &[&family, &identity]));
            items.push(WorkflowEvidenceItem {
                evidence_key: format!("related:{target}"),
                source_family: family.clone(),
                identity,
                destination: bounded(raw.get("href"), 8000),
                source_id: direct.then_some(fact.episode.source_id),
                evidence_kind: kind,
                admission_reasons: reasons.into_iter().collect(),
                observed_at: utc(raw.get("observed_at")),
                availability: availability(raw.get("availability"), stale),
                authority: if direct {
                    "observed".into()
                } else {
                    "explicit-organization".into()
                },
            });
            if stale {
                stale_families.insert(family);
            }
        }
        let unresolved = group["total"]
            .as_u64()
            .unwrap_or(0)
            .saturating_sub(group_items.len() as u64) as usize;
        if unresolved > 0 {
            *hints.entry("unknown".into()).or_default() += unresolved;
            if stale {
                stale_families.insert("unknown".into());
            }
        }
    }
    Ok((items, hints, stale_families))
}
fn membership_evidence(connection: &Connection, id: i64) -> Result<Vec<WorkflowEvidenceItem>> {
    let mut result = vec![];
    for row in db::rows(connection,"SELECT 'workstream' AS scope_kind,workstreams.id AS workstream_id,NULL AS thread_id,workstreams.name AS identity,workstream_links.created_at,workstream_links.linked_by FROM workstream_links JOIN workstreams ON workstreams.id=workstream_links.workstream_id WHERE workstream_links.entity_type='session' AND workstream_links.entity_id=? UNION ALL SELECT 'thread',workstreams.id,threads.id,threads.title,thread_links.created_at,thread_links.linked_by FROM thread_links JOIN threads ON threads.id=thread_links.thread_id JOIN workstreams ON workstreams.id=threads.workstream_id WHERE thread_links.entity_type='session' AND thread_links.entity_id=? ORDER BY scope_kind,workstream_id,thread_id",[id.to_string(),id.to_string()])? {
        let stream=row["workstream_id"].as_i64().unwrap();let thread=row["thread_id"].as_i64();let scope=row["scope_kind"].as_str().unwrap();let suffix=thread.map(|id|format!("thread:{id}")).unwrap_or_else(||"workstream".into());let mut destination=format!("/workstreams/{stream}");if let Some(thread)=thread{destination.push_str(&format!("#thread-{thread}"));}
        result.push(WorkflowEvidenceItem{evidence_key:format!("organization:{stream}:{suffix}"),source_family:"organization".into(),identity:bounded(row.get("identity"),500).unwrap_or_else(||"Untitled".into()),destination:Some(destination),source_id:None,evidence_kind:format!("{scope}-membership"),admission_reasons:vec![format!("{scope}-membership")],observed_at:utc(row.get("created_at")),availability:"available".into(),authority:"explicit-organization".into()});
    }
    Ok(result)
}
fn subsession_evidence(
    connection: &Connection,
    id: i64,
) -> Result<(Vec<WorkflowEvidenceItem>, usize)> {
    let rows=db::rows(connection,"SELECT children.id,children.title,children.started_at,children.last_event_at,sources.id AS source_id,COUNT(*) OVER () AS observed_total FROM sessions AS parents JOIN sessions AS children ON children.parent_session_id=parents.id JOIN sources ON sources.id=children.source_id WHERE parents.id=? AND parents.session_class='work' AND parents.session_role='primary' AND children.session_class='work' AND children.session_role='subsession' AND children.source_id=parents.source_id ORDER BY COALESCE(children.last_event_at,children.started_at) DESC,children.id DESC LIMIT ?",rusqlite::params![id,(MAX_WORKFLOW_EVIDENCE_PER_FAMILY+1) as i64])?;
    let total = rows
        .first()
        .and_then(|row| row["observed_total"].as_u64())
        .unwrap_or(0) as usize;
    let items = rows
        .into_iter()
        .map(|row| {
            let child = row["id"].as_i64().unwrap();
            WorkflowEvidenceItem {
                evidence_key: format!("subsession:{child}"),
                source_family: "session".into(),
                identity: bounded(row.get("title"), 500)
                    .unwrap_or_else(|| "Untitled Session".into()),
                destination: Some(format!("/sessions/{child}")),
                source_id: row["source_id"].as_i64(),
                evidence_kind: "subsession".into(),
                admission_reasons: vec!["subsession".into()],
                observed_at: utc(row
                    .get("last_event_at")
                    .filter(|value| value.as_str().is_some_and(|s| !s.is_empty()))
                    .or_else(|| row.get("started_at"))),
                availability: "available".into(),
                authority: "observed".into(),
            }
        })
        .collect();
    Ok((items, total))
}
fn structure_evidence(
    connection: &Connection,
    id: i64,
) -> Result<(Vec<WorkflowEvidenceItem>, usize, bool)> {
    let rows=db::rows(connection,"SELECT structure_refs.id,structure_refs.service,structure_refs.reference_kind,structure_refs.reference_identity,MAX(evidence.observed_at) AS observed_at,scans.status AS scan_status,COUNT(*) OVER () AS observed_total FROM atlassian_structure_reference_evidence AS evidence JOIN atlassian_structure_references AS structure_refs ON structure_refs.id=evidence.reference_id LEFT JOIN session_reference_scans AS scans ON scans.session_id=evidence.session_id WHERE evidence.session_id=? GROUP BY structure_refs.id,structure_refs.service,structure_refs.reference_kind,structure_refs.reference_identity,scans.status ORDER BY CASE WHEN MAX(evidence.observed_at) IS NULL THEN 1 ELSE 0 END,MAX(evidence.observed_at),structure_refs.id",[id])?;
    let total = rows
        .first()
        .and_then(|row| row["observed_total"].as_u64())
        .unwrap_or(0) as usize;
    let stale = rows.iter().any(|row| row["scan_status"] == "error");
    let items = rows
        .into_iter()
        .map(|row| {
            let key = row["id"].as_i64().unwrap();
            let status = row["scan_status"].as_str().unwrap_or("");
            WorkflowEvidenceItem {
                evidence_key: format!("atlassian-structure:{key}"),
                source_family: "atlassian".into(),
                identity: bounded(row.get("reference_identity"), 500)
                    .unwrap_or_else(|| row["reference_kind"].as_str().unwrap_or("None").into()),
                destination: Some(format!("/atlassian/references/{key}")),
                source_id: None,
                evidence_kind: "structure-reference".into(),
                admission_reasons: vec!["structure-reference".into()],
                observed_at: utc(row.get("observed_at")),
                availability: if ["ok", "partial"].contains(&status) {
                    "available".into()
                } else if status == "error" {
                    "stale".into()
                } else {
                    "unknown".into()
                },
                authority: "observed".into(),
            }
        })
        .collect();
    Ok((items, total, stale))
}
fn evidence_groups(
    connection: &Connection,
    fact: &SessionFact,
) -> Result<(Vec<WorkflowEvidenceGroup>, usize, usize, bool)> {
    let (mut values, mut observed_hints, mut stale_families) = related_evidence(connection, fact)?;
    let mut retained_hints = EvidenceHints::new();
    values.extend(membership_evidence(connection, fact.episode.session_id)?);
    let (subsessions, subsession_total) = subsession_evidence(connection, fact.episode.session_id)?;
    values.extend(subsessions);
    if subsession_total > 0 {
        retained_hints.insert("session".into(), subsession_total);
        let total = observed_hints.entry("session".into()).or_default();
        *total = (*total).max(subsession_total);
    }
    let (structures, structure_total, structure_stale) =
        structure_evidence(connection, fact.episode.session_id)?;
    values.extend(structures);
    if structure_total > 0 {
        let total = observed_hints.entry("atlassian".into()).or_default();
        *total = (*total).max(structure_total);
    }
    if structure_stale {
        stale_families.insert("atlassian".into());
    }
    let mut deduplicated = BTreeMap::<(String, String), WorkflowEvidenceItem>::new();
    for item in values {
        if !AVAILABILITIES.contains(&item.availability.as_str())
            || !EVIDENCE_AUTHORITIES.contains(&item.authority.as_str())
        {
            continue;
        }
        let key = (item.source_family.clone(), item.evidence_key.clone());
        if deduplicated.get(&key).is_none_or(|current| {
            current.authority == "explicit-organization" && item.authority == "observed"
        }) {
            deduplicated.insert(key, item);
        }
    }
    let mut by_family = BTreeMap::<String, Vec<WorkflowEvidenceItem>>::new();
    for item in deduplicated.into_values() {
        by_family
            .entry(item.source_family.clone())
            .or_default()
            .push(item);
    }
    let families: BTreeSet<_> = by_family
        .keys()
        .chain(observed_hints.keys())
        .cloned()
        .collect();
    let mut groups = vec![];
    for family in families {
        let mut items = by_family.remove(&family).unwrap_or_default();
        items.sort_by(|a, b| {
            (if a.authority == "observed" { 0 } else { 1 })
                .cmp(&(if b.authority == "observed" { 0 } else { 1 }))
                .then(a.observed_at.is_none().cmp(&b.observed_at.is_none()))
                .then(
                    a.observed_at
                        .as_deref()
                        .unwrap_or("")
                        .cmp(b.observed_at.as_deref().unwrap_or("")),
                )
                .then(unicode::casefold(&a.identity).cmp(&unicode::casefold(&b.identity)))
                .then(a.evidence_key.cmp(&b.evidence_key))
        });
        let retained_total = items.len().max(*retained_hints.get(&family).unwrap_or(&0));
        let observed_total = retained_total.max(*observed_hints.get(&family).unwrap_or(&0));
        items.truncate(5);
        let partial = observed_total > retained_total || retained_total > items.len();
        let stale = stale_families.contains(&family);
        groups.push(WorkflowEvidenceGroup {
            source_family: family,
            items,
            retained_total,
            observed_total,
            partial,
            stale,
        });
    }
    let retained = groups.iter().map(|g| g.retained_total).sum();
    let observed = groups.iter().map(|g| g.observed_total).sum();
    let partial = groups.iter().any(|g| g.partial || g.stale);
    Ok((groups, retained, observed, partial))
}

pub(super) fn base_workflow_focus_projection(
    connection: &Connection,
    session_id: i64,
) -> Result<WorkflowFocusProjection> {
    if session_id <= 0 {
        return Err(invalid("session_id must be a positive integer"));
    }
    let Some(row) = session_row(connection, session_id)? else {
        return Ok(WorkflowFocusProjection::empty("missing"));
    };
    if row["session_class"] != "work"
        || row["session_role"] != "primary"
        || row["index_policy"] != "full"
    {
        return Ok(WorkflowFocusProjection::empty("ineligible"));
    }
    let facts = session_facts(connection)?;
    let Some(selected) = facts.get(&session_id) else {
        return Ok(WorkflowFocusProjection::empty("ineligible"));
    };
    let (candidates, observed_candidates) = ordered_candidates(selected, &facts);
    let ranks = candidates
        .iter()
        .enumerate()
        .map(|(rank, fact)| (fact.episode.episode_key.clone(), rank))
        .collect();
    let mut classification = vec![selected.clone()];
    classification.extend(candidates.iter().cloned());
    let by_key: BTreeMap<_, _> = classification
        .iter()
        .map(|fact| (fact.episode.episode_key.clone(), fact.clone()))
        .collect();
    let (normalized, priorities) = normalized_relations(&classification);
    let (keys, traversed, observed_episodes, observed_roots, retained_roots) =
        focus_neighborhood(selected, &by_key, &normalized, &priorities, &ranks);
    let relations = normalized
        .relations
        .into_iter()
        .filter(|r| {
            traversed.contains(&(
                r.source_episode_key.clone(),
                r.target_episode_key.clone(),
                r.kind.clone(),
            ))
        })
        .collect();
    let mut retained: Vec<_> = keys.iter().map(|key| &by_key[key]).collect();
    retained.sort_by(|a, b| {
        instant_order(a.instant, b.instant).then(a.episode.episode_key.cmp(&b.episode.episode_key))
    });
    let mut episodes = vec![];
    for fact in retained {
        let (groups, retained, observed, partial) = evidence_groups(connection, fact)?;
        episodes.push(WorkflowEpisodeView {
            episode: fact.episode.clone(),
            evidence_groups: groups,
            evidence_retained_total: retained,
            evidence_observed_total: observed,
            evidence_partial: partial,
        });
    }
    let mut projection = WorkflowFocusProjection::empty("ready");
    projection.selected_episode_key = Some(selected.episode.episode_key.clone());
    projection.episode_retained_total = episodes.len();
    projection.episodes = episodes;
    projection.relations = relations;
    projection.diagnostics = normalized.diagnostics;
    projection.candidate_observed_total = observed_candidates;
    projection.candidate_retained_total = candidates.len();
    projection.episode_observed_total = observed_episodes;
    projection.branch_root_observed_total = observed_roots;
    projection.branch_root_retained_total = retained_roots;
    Ok(projection)
}

pub fn workflow_focus_projection(
    connection: &Connection,
    session_id: i64,
) -> Result<WorkflowFocusProjection> {
    super::assertions::overlay_workflow_assertions(
        connection,
        base_workflow_focus_projection(connection, session_id)?,
    )
}
