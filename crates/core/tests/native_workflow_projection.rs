use localbrain_core::backend::workflow::projection::*;
use serde_json::json;
fn session() -> serde_json::Value {
    json!({"id":17,"source_id":2,"external_id":"native-session-1","session_class":"work","session_role":"primary","title":"Synthetic workflow investigation","started_at":"2026-09-14T10:00:00+09:00","first_event_at":"2026-09-14T01:01:00Z","last_event_at":"2026-09-14T02:30:00Z","ended_at":"2026-09-14T02:20:00Z","workspace_id":3,"workspace_name":"Synthetic Project","git_branch":"feature/workflow-map"})
}
fn relation(source: &str, target: &str, hour: u32) -> WorkflowRelation {
    WorkflowRelation {
        source_episode_key: source.into(),
        target_episode_key: target.into(),
        kind: "continues".into(),
        authority: "deterministic-candidate".into(),
        reasons: vec![WorkflowRelationReason {
            kind: "shared-reference".into(),
            identity: "target:synthetic".into(),
            observed_at: None,
        }],
        source_observed_at: Some(format!("2026-09-14T{hour:02}:00:00Z")),
        target_observed_at: Some(format!("2026-09-14T{:02}:00:00Z", hour + 1)),
        projection_version: WORKFLOW_PROJECTION_VERSION.into(),
    }
}
#[test]
fn source_scoped_opaque_episode_identity_survives_local_reimport_and_field_changes() {
    let a = workflow_episode_from_session(&session(), &EpisodeOptions::default()).unwrap();
    let mut row = session();
    row["id"] = json!(99);
    row["title"] = json!("Renamed");
    row["workspace_id"] = json!(7);
    assert_eq!(
        a.episode_key,
        workflow_episode_from_session(&row, &EpisodeOptions::default())
            .unwrap()
            .episode_key
    );
    row["source_id"] = json!(1);
    assert_ne!(
        a.episode_key,
        workflow_episode_from_session(&row, &EpisodeOptions::default())
            .unwrap()
            .episode_key
    );
    assert_ne!(
        workflow_episode_key(12, "3").unwrap(),
        workflow_episode_key(1, "23").unwrap()
    );
    assert_eq!(
        a.observed_start_at.as_deref(),
        Some("2026-09-14T01:00:00+00:00")
    );
    assert_eq!(
        a.last_observed_at.as_deref(),
        Some("2026-09-14T02:30:00+00:00")
    );
    assert_eq!(a.lifecycle_state, "unknown");
    assert!(a.closure_reason.is_none());
    let text = serde_json::to_string(&a).unwrap();
    assert!(!text.contains("native-session-1"));
    assert!(!text.contains("external_id"));
}
#[test]
fn explicit_lifecycle_provenance_and_codepoint_bounds_are_enforced() {
    let mut row = session();
    row["title"] = json!("文".repeat(700));
    row["ended_at"] = json!("2026-09-14T05:00:00Z");
    let options = EpisodeOptions {
        intent: Some(json!("I".repeat(2100))),
        outcome: Some(json!("O".repeat(2100))),
        next_action: Some(json!("N".repeat(2100))),
        lifecycle_state: "open".into(),
        activity_state: "active".into(),
        ..Default::default()
    };
    let episode = workflow_episode_from_session(&row, &options).unwrap();
    assert_eq!(episode.display_title.unwrap().chars().count(), 500);
    assert_eq!(episode.intent.unwrap().len(), 2000);
    assert_eq!(episode.outcome.unwrap().len(), 2000);
    assert_eq!(episode.next_action.unwrap().len(), 2000);
    assert_eq!(episode.lifecycle_state, "open");
    assert!(episode.closure_reason.is_none());
    assert_eq!(
        episode.last_observed_at.as_deref(),
        Some("2026-09-14T05:00:00+00:00")
    );
    for (field, value) in [
        ("session_class", json!("maintenance")),
        ("session_role", json!("subsession")),
        ("id", json!(true)),
        ("source_id", json!(0)),
    ] {
        let mut row = session();
        row[field] = value;
        assert!(workflow_episode_from_session(&row, &EpisodeOptions::default()).is_err());
    }
    for options in [
        EpisodeOptions {
            lifecycle_state: "closed".into(),
            ..Default::default()
        },
        EpisodeOptions {
            closure_reason: Some("completed".into()),
            ..Default::default()
        },
        EpisodeOptions {
            authority: "guessed".into(),
            ..Default::default()
        },
        EpisodeOptions {
            activity_state: "stale".into(),
            ..Default::default()
        },
    ] {
        assert!(workflow_episode_from_session(&session(), &options).is_err());
    }
    let mut row = session();
    for field in ["started_at", "first_event_at", "last_event_at", "ended_at"] {
        row[field] = json!("invalid");
    }
    let episode = workflow_episode_from_session(&row, &EpisodeOptions::default()).unwrap();
    assert!(episode.observed_start_at.is_none() && episode.last_observed_at.is_none());
}
#[test]
fn relation_normalizer_rejects_unsupported_authority_time_and_support_only_edges() {
    let mut support = relation("a", "b", 1);
    support.reasons = vec![WorkflowRelationReason {
        kind: "same-workspace".into(),
        identity: "workspace:3".into(),
        observed_at: None,
    }];
    let mut reverse = relation("b", "c", 3);
    reverse.target_observed_at = Some("2026-09-14T02:00:00Z".into());
    let mut user = relation("c", "d", 4);
    user.authority = "user-confirmed".into();
    let mut org = relation("d", "e", 5);
    org.authority = "explicit-organization".into();
    let result = normalize_workflow_relations(vec![
        support,
        reverse,
        user,
        org,
        relation("self", "self", 6),
    ]);
    assert!(result.relations.is_empty());
    let mut codes = result
        .diagnostics
        .iter()
        .map(|d| d.code.as_str())
        .collect::<Vec<_>>();
    codes.sort();
    assert_eq!(
        codes,
        vec![
            "authority-reason-mismatch",
            "authority-reason-mismatch",
            "missing-strong-reason",
            "non-forward-time",
            "self-edge"
        ]
    );
    let mut user = relation("a", "b", 1);
    user.authority = "user-confirmed".into();
    user.reasons[0].kind = "user-assertion".into();
    let mut org = relation("b", "c", 2);
    org.authority = "explicit-organization".into();
    org.reasons[0].kind = "thread-membership".into();
    let result = normalize_workflow_relations([user, org]);
    assert_eq!(result.relations.len(), 2);
    assert!(result.diagnostics.is_empty());
}
#[test]
fn relations_are_deterministic_deduplicated_acyclic_and_reason_bounded() {
    let first = relation("a", "b", 1);
    let conflict = relation("b", "a", 3);
    let result = normalize_workflow_relations([first.clone(), conflict.clone()]);
    assert_eq!(
        result,
        normalize_workflow_relations([conflict, first.clone()])
    );
    assert_eq!(result.relations.len(), 1);
    assert_eq!(result.diagnostics[0].code, "cycle-omitted");
    let mut reasoned = first;
    reasoned.reasons[0].identity = " target:synthetic ".into();
    reasoned.reasons[0].observed_at = Some("2026-09-14T10:00:00+09:00".into());
    let extra = WorkflowRelationReason {
        kind: "same-git-root".into(),
        identity: "repo:synthetic".into(),
        observed_at: None,
    };
    reasoned.reasons.extend([extra.clone(), extra]);
    let result = normalize_workflow_relations([reasoned.clone(), reasoned]);
    assert_eq!(result.relations.len(), 1);
    assert_eq!(result.relations[0].reasons.len(), 2);
    assert_eq!(result.relations[0].reasons[1].identity, "target:synthetic");
    assert_eq!(
        result.relations[0].reasons[1].observed_at.as_deref(),
        Some("2026-09-14T01:00:00+00:00")
    );
    let mut overlong = relation("c", "d", 4);
    overlong.reasons[0].identity = "文".repeat(501);
    assert_eq!(
        normalize_workflow_relations([overlong]).diagnostics[0].code,
        "invalid-value"
    );
    let mut kinds = vec![];
    for (index, kind) in WORKFLOW_RELATION_KINDS.iter().enumerate() {
        let mut value = relation(
            &index.to_string(),
            &(index + 1).to_string(),
            index as u32 + 1,
        );
        value.kind = (*kind).into();
        kinds.push(value);
    }
    let result = normalize_workflow_relations(kinds);
    assert_eq!(result.relations.len(), 3);
    assert!(result.diagnostics.is_empty());
}
