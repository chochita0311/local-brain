use localbrain_core::backend::{db, insights::evidence::*};
use rusqlite::Connection;
use serde_json::Value;
fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../src/backend/insights/fixtures/evidence-golden.json"
    ))
    .unwrap()
}
fn database(sql: &str) -> Connection {
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection.execute_batch("PRAGMA foreign_keys=OFF").unwrap();
    connection.execute_batch(sql).unwrap();
    connection.execute_batch("PRAGMA foreign_keys=ON").unwrap();
    connection
}
#[test]
fn complete_frozen_evidence_selection_coverage_and_offsets_match() {
    for (index, case) in fixture()["cases"].as_array().unwrap().iter().enumerate() {
        let connection = database(case["setup_sql"].as_str().unwrap());
        let before = connection.total_changes();
        connection.execute_batch("PRAGMA query_only=ON").unwrap();
        let request = serde_json::from_value::<EvidenceRequest>(case["request"].clone());
        let request = match request {
            Ok(value) => value,
            Err(_) => {
                assert!(
                    case.get("error").is_some(),
                    "fixture {index} cannot deserialize"
                );
                continue;
            }
        };
        match build_insight_evidence_manifest(&connection, &request) {
            Ok(value) => {
                assert!(
                    case.get("error").is_none(),
                    "fixture {index} unexpectedly admitted"
                );
                assert_eq!(value, case["expected"], "fixture {index}");
                assert_eq!(
                    value,
                    build_insight_evidence_manifest(&connection, &request).unwrap()
                );
            }
            Err(error) => assert_eq!(error.message, case["error"], "fixture {index}"),
        }
        assert_eq!(connection.total_changes(), before);
    }
}
#[test]
fn frozen_evidence_reference_revisions_staleness_and_unavailability_match() {
    for (index, case) in fixture()["references"]
        .as_array()
        .unwrap()
        .iter()
        .enumerate()
    {
        let connection = database(case["setup_sql"].as_str().unwrap());
        let before = connection.total_changes();
        assert_eq!(
            resolve_insight_evidence_reference(&connection, &case["reference"]).unwrap(),
            case["expected"],
            "reference {index}"
        );
        assert_eq!(connection.total_changes(), before);
    }
}
#[test]
fn scope_validation_precedes_every_message_select() {
    use rusqlite::hooks::{AuthAction, AuthContext, Authorization};
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection.authorizer(Some(|context: AuthContext<'_>| match context.action {
        AuthAction::Read {
            table_name: "activity_events",
            ..
        } => panic!("invalid scope must not read messages"),
        _ => Authorization::Allow,
    }));
    let now = "2026-09-30T00:00:00Z".parse().unwrap();
    let mut request = EvidenceRequest::new("ask", now);
    assert!(build_insight_evidence_manifest(&connection, &request).is_err());
    request.mode = "discover".into();
    request.source_ids = Some(vec![999]);
    assert!(build_insight_evidence_manifest(&connection, &request).is_err());
    request.source_ids = None;
    request.timezone = "Not/A_Zone".into();
    assert!(build_insight_evidence_manifest(&connection, &request).is_err());
}
