mod native_atlassian_support;
use localbrain_core::backend::{atlassian::browse, Result};
use rusqlite::Connection;
use serde_json::{json, Value};
fn call(db: &Connection, operation: &str, value: &Value) -> Result<Value> {
    let resource = || value["external_resource_id"].as_i64().unwrap();
    let reference = || value["reference_id"].as_i64().unwrap();
    match operation {
        "normalize_browse_filters" => browse::normalize_browse_filters(&value["values"]),
        "normalize_browse_structure" => browse::normalize_browse_structure(db, &value["filters"]),
        "validate_browse_structural_scope" => {
            browse::validate_browse_structural_scope(db, &value["filters"])?;
            Ok(Value::Null)
        }
        "browse_inventory" => browse::browse_inventory(db, &value["values"]),
        "project_atlassian_item_container" => {
            browse::project_atlassian_item_container(&value["item"])
        }
        "atlassian_item_detail" => {
            Ok(browse::atlassian_item_detail(db, resource())?.unwrap_or(Value::Null))
        }
        "atlassian_item_preview" => {
            Ok(
                browse::atlassian_item_preview(db, resource(), &value["values"])?
                    .unwrap_or(Value::Null),
            )
        }
        "atlassian_structure_reference_detail" => Ok(browse::atlassian_structure_reference_detail(
            db,
            reference(),
        )?
        .unwrap_or(Value::Null)),
        "atlassian_structure_reference_preview" => Ok(
            browse::atlassian_structure_reference_preview(db, reference(), &value["values"])?
                .unwrap_or(Value::Null),
        ),
        "update_atlassian_local_state" => {
            browse::update_atlassian_local_state(db, resource(), value)
        }
        "atlassian_search_results" => Ok(json!(browse::atlassian_search_results(
            db,
            value["query"].as_str().unwrap(),
            &value["values"],
            value["limit"].as_i64().unwrap()
        )?)),
        _ => panic!("unknown replay operation {operation}"),
    }
}
#[test]
fn full_browse_preview_local_mutation_and_grouped_fts_calls_match_frozen_python() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/browse-calls.json")).unwrap();
    native_atlassian_support::replay(&cases, call);
}
