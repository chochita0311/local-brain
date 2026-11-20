use localbrain_core::backend::workflow::{candidates::*, projection::*};
use serde_json::{json, Value};

fn golden() -> Value {
    serde_json::from_str(include_str!(
        "../src/backend/workflow/fixtures/candidates-golden.json"
    ))
    .unwrap()
}
#[test]
fn complete_candidate_descriptors_and_revisions_match_frozen_python() {
    for case in golden()["cases"].as_array().unwrap() {
        let coverage = if case["coverage"].is_null() {
            None
        } else {
            Some(serde_json::from_value(case["coverage"].clone()).unwrap())
        };
        let result = normalize_workstream_candidates(
            case["artifacts"].as_array().unwrap(),
            case["sessions"].as_array().unwrap(),
            case["references"].as_array().unwrap(),
            case["pairs"].as_array().unwrap(),
            coverage,
        )
        .unwrap();
        assert_eq!(
            serde_json::to_value(result).unwrap(),
            case["expected"],
            "{}",
            case["name"]
        );
    }
}
#[test]
fn supplied_order_aliases_and_duplicates_do_not_change_candidate_projection() {
    let value = golden();
    let case = &value["cases"][0];
    let mut a = case["artifacts"].as_array().unwrap().clone();
    let mut s = case["sessions"].as_array().unwrap().clone();
    let mut r = case["references"].as_array().unwrap().clone();
    let mut p = case["pairs"].as_array().unwrap().clone();
    a.extend(a.clone());
    s.extend(s.clone());
    r.extend(r.clone());
    p.extend(p.clone());
    a.reverse();
    s.reverse();
    r.reverse();
    p.reverse();
    assert_eq!(
        serde_json::to_value(normalize_workstream_candidates(&a, &s, &r, &p, None).unwrap())
            .unwrap(),
        case["expected"]
    );
}
#[test]
fn membership_revision_retains_all_evidence_and_ignores_navigation_metadata() {
    let value = golden();
    let case = &value["cases"][2];
    let mut a = case["artifacts"].as_array().unwrap().clone();
    let mut s = case["sessions"].as_array().unwrap().clone();
    let mut r = case["references"].as_array().unwrap().clone();
    let p = case["pairs"].as_array().unwrap();
    let before = normalize_workstream_candidates(&a, &s, &r, p, None).unwrap();
    a[0]["title"] = json!("Renamed source metadata");
    a[0]["availability"] = json!("missing");
    a[0]["freshness"] = json!("stale");
    s[0]["id"] = json!(99);
    let renamed = normalize_workstream_candidates(&a, &s, &r, p, None).unwrap();
    assert_ne!(before.revision, renamed.revision);
    assert_eq!(
        before
            .candidates
            .iter()
            .map(|c| &c.membership_revision)
            .collect::<Vec<_>>(),
        renamed
            .candidates
            .iter()
            .map(|c| &c.membership_revision)
            .collect::<Vec<_>>()
    );
    let last = r.len() - 1;
    r[last]["reference_identity"] = json!("changed-unsampled-occurrence");
    let changed = normalize_workstream_candidates(&a, &s, &r, p, None).unwrap();
    assert!(renamed
        .candidates
        .iter()
        .zip(&changed.candidates)
        .any(|(a, b)| a.membership_revision != b.membership_revision));
}
#[test]
fn all_hard_input_bounds_refuse_the_whole_supplied_scope() {
    for (a, s, r, p) in [
        (vec![Value::Null; MAX_ARTIFACTS + 1], vec![], vec![], vec![]),
        (vec![], vec![Value::Null; MAX_SESSIONS + 1], vec![], vec![]),
        (
            vec![],
            vec![],
            vec![Value::Null; MAX_REFERENCES + 1],
            vec![],
        ),
        (vec![], vec![], vec![], vec![Value::Null; MAX_PAIRS + 1]),
    ] {
        assert_eq!(
            normalize_workstream_candidates(&a, &s, &r, &p, None)
                .unwrap_err()
                .code,
            "candidate_limit"
        );
    }
    assert!(CandidateCoverage::new(true, None).is_err());
    assert!(CandidateCoverage::new(true, Some(1)).is_err());
}
#[test]
fn opaque_identities_are_scoped_and_never_expose_source_locators() {
    let a = candidate_artifact_key("context-document", "ab", "c").unwrap();
    let b = candidate_artifact_key("context-document", "a", "bc").unwrap();
    assert_ne!(a, b);
    assert_eq!(
        workstream_candidate_key(&a, &b).unwrap(),
        workstream_candidate_key(&b, &a).unwrap()
    );
    assert!(workstream_candidate_key(&a, &a).is_err());
    assert_ne!(
        workflow_episode_key(12, "3").unwrap(),
        workflow_episode_key(1, "23").unwrap()
    );
    assert!(candidate_artifact_key("context-document", "source", "private\nlocator").is_err());
    let result = serde_json::to_string(&golden()["cases"][0]["expected"]).unwrap();
    assert!(!result.contains("native-session"));
    assert!(!result.contains("goal.md"));
    assert!(!result.contains("source_identity"));
}
