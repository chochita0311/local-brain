//! Complete outputs and database effects captured from18 frozen synthetic tests.
use localbrain_core::backend::{atlassian::catalog, clock, Result};
use rusqlite::Connection;
use serde_json::{json, Value};
#[path = "native_atlassian_support/mod.rs"]
mod support;
fn time(value: &Value) -> Option<chrono::DateTime<chrono::Utc>> {
    value.as_str().and_then(clock::parse_timestamp)
}
fn call(db: &Connection, operation: &str, v: &Value) -> Result<Value> {
    let id = v["external_resource_id"].as_i64().unwrap_or(0);
    match operation {
        "normalize_atlassian_content" => {
            Ok(serde_json::to_value(catalog::normalize_atlassian_content(
                v["source_format"].as_str().unwrap(),
                &v["content"],
            )?)?)
        }
        "register_atlassian_site" => catalog::register_atlassian_site(db, v),
        "register_atlassian_space" => catalog::register_atlassian_space(db, v),
        "create_or_reuse_atlassian_stub" => catalog::create_or_reuse_atlassian_stub(db, v),
        "bind_atlassian_remote_identity" => catalog::bind_atlassian_remote_identity(db, id, v),
        "set_atlassian_item_axes" => catalog::set_atlassian_item_axes(db, id, v),
        "purge_atlassian_item" => catalog::purge_atlassian_item(db, id),
        "apply_atlassian_target_result" => catalog::apply_atlassian_target_result(
            db,
            id,
            &v["target_result"],
            v["checked_at"].as_str(),
            v["source_format"].as_str(),
        ),
        "atlassian_item_state" => catalog::atlassian_item_state(db, id, time(&v["now"])),
        "derive_atlassian_freshness" => Ok(json!(catalog::derive_atlassian_freshness(
            v["service"].as_str().unwrap(),
            (!v["remote_state"].is_null()).then_some(&v["remote_state"]),
            time(&v["now"])
        )?)),
        "rebuild_atlassian_search_index" => Ok(json!(catalog::rebuild_atlassian_search_index(
            db,
            v["rebuilt_at"].as_str()
        )?)),
        other => panic!("uncaptured native operation {other}"),
    }
}

#[test]
fn catalog_writer_reader_failure_and_content_contracts_match_complete_frozen_calls() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/catalog.json")).unwrap();
    assert_eq!(cases.len(), 62);
    support::replay(&cases, call);
}
