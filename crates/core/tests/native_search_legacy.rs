#[path = "native_atlassian_support/mod.rs"]
mod support;
use localbrain_core::backend::search::keyword::legacy_search;
use serde_json::{json, Value};
#[test]
fn historical_unregistered_private_disabled_orphan_and_mixed_results_match_frozen_python() {
    let mut cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/legacy-search.json")).unwrap();
    // SQLite scores are IEEE f64. Normalize only JSON exponent spelling while
    // retaining the exact f64 value (no tolerance or decimal rounding).
    for case in &mut cases {
        if let Some(rows) = case["expected"].as_array_mut() {
            for row in rows {
                if let Some(score) = row["score"].as_f64() {
                    row["score"] = json!(score);
                }
            }
        }
    }
    assert_eq!(cases.len(), 110);
    support::replay(&cases, |db, _, values| {
        Ok(json!(legacy_search(
            db,
            values["query"].as_str().unwrap(),
            values["scope"].as_str().unwrap(),
            &values["filters"],
            values["limit"].as_i64().unwrap()
        )?))
    });
}
