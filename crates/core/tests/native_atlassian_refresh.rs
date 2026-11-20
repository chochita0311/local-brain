//! Full local preview/result effects and actual one-batch preparation envelopes.
use localbrain_core::backend::{
    atlassian::{refresh, sync},
    db, Config, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
#[path = "native_atlassian_support/mod.rs"]
mod support;
fn call(db: &Connection, name: &str, v: &Value) -> Result<Value> {
    match name {
        "refresh_preview" => refresh::refresh_preview(db, v),
        "build_item_refresh_target" => refresh::build_item_refresh_target(&v["item"]),
        "apply_atlassian_refresh_result" => refresh::apply_atlassian_refresh_result(
            db,
            &v["manifest"],
            &v["result"],
            v["checked_at"].as_str(),
        ),
        "is_atlassian_refresh_manifest" => Ok(json!(refresh::is_atlassian_refresh_manifest(
            &v["manifest"]
        ))),
        "refresh_run_result" => Ok(json!(refresh::refresh_run_result(
            db,
            v["run_id"].as_str().unwrap()
        )?)),
        other => panic!("uncaptured Refresh operation {other}"),
    }
}
#[test]
fn complete_refresh_previews_mapping_failures_and_application_effects_match_frozen_calls() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/refresh.json")).unwrap();
    assert!(!cases.is_empty());
    support::replay(&cases, call);
}
fn normalize_manifest(mut v: Value) -> Value {
    v.as_object_mut().unwrap().remove("generated_at");
    v["run_id"] = json!("__run_id__");
    v
}
#[test]
fn refresh_preparation_keeps_mixed_binding_targets_and_twenty_call_authority() {
    let cases: Vec<Value> = serde_json::from_str(include_str!(
        "native_atlassian_fixtures/refresh_prepare.json"
    ))
    .unwrap();
    assert!(!cases.is_empty());
    for case in cases {
        let temp = tempfile::Builder::new()
            .prefix("lb-atlassian-refresh-")
            .tempdir()
            .unwrap();
        let config = Config::for_data_dir(temp.path().join("data"));
        let db = Connection::open_in_memory().unwrap();
        db.execute_batch(db::SCHEMA).unwrap();
        support::restore(&db, &case["before"]);
        let result = refresh::prepare_atlassian_refresh_run(
            &db,
            &config,
            &case["values"],
            Some(&temp.path().join("runs")),
        );
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
        let (manifest, _) = sync::load_external_sync_manifest(&db, &config, &row).unwrap();
        let original = case["after"]["maintenance_runs"]
            .as_array()
            .unwrap()
            .iter()
            .find(|row| row["id"] == case["expected"])
            .unwrap();
        let expected: Value =
            serde_json::from_str(original["source_snapshot_json"].as_str().unwrap()).unwrap();
        assert_eq!(normalize_manifest(manifest), normalize_manifest(expected));
        assert_eq!(row["mcp_call_budget"], 20);
        assert_eq!(row["status"], "queued");
    }
}
