//! Exact local registration outputs/DB effects and policy-owned discovery envelopes.
use localbrain_core::backend::{
    atlassian::{registration as r, sync},
    db, Config, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
#[path = "native_atlassian_support/mod.rs"]
mod support;
fn call(db: &Connection, name: &str, v: &Value) -> Result<Value> {
    match name {
        "recognize_registration_url" => Ok(serde_json::to_value(r::recognize_registration_url(
            v["url"].as_str().unwrap(),
            v["expected_service"].as_str(),
        )?)?),
        "registration_sites" => Ok(json!(r::registration_sites(
            db,
            v["service"].as_str().unwrap()
        )?)),
        "registration_preview" => r::registration_preview(db, v),
        "register_atlassian_site_access" => r::register_atlassian_site_access(db, v),
        "update_atlassian_connection" => r::update_atlassian_connection(db, v),
        "resolve_registration_site" => r::resolve_registration_site(
            db,
            &serde_json::from_value(v["locator"].clone())?,
            v["site_id"].as_i64(),
        ),
        "register_atlassian_url" => r::register_atlassian_url(db, v),
        "registration_inventory" => r::registration_inventory(db, v["service"].as_str().unwrap()),
        "registered_scope_overview" => Ok(json!(r::registered_scope_overview(
            db,
            v["service"].as_str().unwrap()
        )?)),
        "register_space_candidate" => r::register_space_candidate(db, v),
        "space_catalog_candidates" => {
            r::space_catalog_candidates(db, v["run_id"].as_str().unwrap(), v["service"].as_str())
        }
        "register_space_catalog_candidate" => r::register_space_catalog_candidate(db, v),
        other => panic!("uncaptured registration operation {other}"),
    }
}
#[test]
fn complete_local_registration_contracts_match_frozen_calls() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/registration.json")).unwrap();
    assert_eq!(cases.len(), 65);
    support::replay(&cases, call);
}
#[test]
fn registration_rolls_back_a_new_site_when_late_native_item_storage_fails() {
    // The old test monkeypatched the Python catalog helper to throw. A real
    // SQLite trigger reaches the corresponding native late-failure boundary.
    let cases: Vec<Value> = serde_json::from_str(include_str!(
        "native_atlassian_fixtures/registration_mock_failure.json"
    ))
    .unwrap();
    assert_eq!(cases.len(), 1);
    let db = Connection::open_in_memory().unwrap();
    db.execute_batch(db::SCHEMA).unwrap();
    support::restore(&db, &cases[0]["before"]);
    let before = db::rows(&db, "SELECT * FROM atlassian_sites ORDER BY id", []).unwrap();
    db.execute_batch("CREATE TRIGGER synthetic_late_failure BEFORE INSERT ON atlassian_items BEGIN SELECT RAISE(ABORT,'synthetic late failure');END").unwrap();
    assert!(r::register_atlassian_url(&db, &cases[0]["values"]).is_err());
    assert_eq!(
        db::rows(&db, "SELECT * FROM atlassian_sites ORDER BY id", []).unwrap(),
        before
    );
    for table in [
        "atlassian_items",
        "external_resources",
        "resource_external_links",
        "search_index",
    ] {
        assert_eq!(
            db.query_row::<i64, _, _>(&format!("SELECT count(*) FROM {table}"), [], |r| r.get(0))
                .unwrap(),
            0
        );
    }
}
fn normalize_manifest(mut v: Value) -> Value {
    v.as_object_mut().unwrap().remove("generated_at");
    v["run_id"] = json!("__run_id__");
    v
}
#[test]
fn connected_discovery_keeps_one_authorized_call_and_never_registers_candidates_implicitly() {
    let cases: Vec<Value> = serde_json::from_str(include_str!(
        "native_atlassian_fixtures/registration_prepare.json"
    ))
    .unwrap();
    assert!(!cases.is_empty());
    for case in cases {
        let temp = tempfile::Builder::new()
            .prefix("lb-atlassian-discovery-")
            .tempdir()
            .unwrap();
        let config = Config::for_data_dir(temp.path().join("data"));
        let db = Connection::open_in_memory().unwrap();
        db.execute_batch(db::SCHEMA).unwrap();
        support::restore(&db, &case["before"]);
        let root = temp.path().join("runs");
        let result = r::prepare_space_catalog_run(&db, &config, &case["values"], Some(&root));
        if let Some(error) = case.get("error") {
            let actual = result.unwrap_err();
            assert_eq!(actual.code, error["code"]);
            assert_eq!(actual.message, error["message"]);
            continue;
        }
        let run = result.unwrap();
        let row = db::row(&db, "SELECT * FROM maintenance_runs WHERE id=?", [&run])
            .unwrap()
            .unwrap();
        let (manifest, dispatches) = sync::load_external_sync_manifest(&db, &config, &row).unwrap();
        let expected_row = case["after"]["maintenance_runs"]
            .as_array()
            .unwrap()
            .iter()
            .find(|row| row["id"] == case["expected"])
            .unwrap();
        let expected: Value =
            serde_json::from_str(expected_row["source_snapshot_json"].as_str().unwrap()).unwrap();
        assert_eq!(normalize_manifest(manifest), normalize_manifest(expected));
        assert_eq!(dispatches.len(), 1);
        assert_eq!(row["mcp_call_budget"], 1);
        assert_eq!(row["status"], "queued");
        let before_count = case["before"]["atlassian_spaces"]
            .as_array()
            .map(Vec::len)
            .unwrap_or(0);
        assert_eq!(
            db.query_row::<i64, _, _>("SELECT count(*) FROM atlassian_spaces", [], |r| r.get(0))
                .unwrap(),
            before_count as i64
        );
    }
}
