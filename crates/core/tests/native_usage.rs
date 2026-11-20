use localbrain_core::backend::{
    db,
    usage::{calculate_estimated_cost, select_snapshot, store_usage_records, ParsedUsageRecord},
};
use rusqlite::Connection;
use serde_json::{json, Value};

#[test]
fn frozen_python_usage_pricing_and_snapshot_contract() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/native-usage-prices.json")).unwrap();
    for (index, case) in fixture["cost"].as_array().unwrap().iter().enumerate() {
        let record: ParsedUsageRecord = serde_json::from_value(case["record"].clone()).unwrap();
        let result = calculate_estimated_cost(
            &record,
            (!case["price"].is_null()).then_some(&case["price"]),
        );
        if case["expected"].is_object() {
            assert!(result.is_err(), "cost case {index}");
        } else {
            assert_eq!(
                serde_json::to_value(result.unwrap()).unwrap(),
                case["expected"],
                "cost case {index}"
            );
        }
    }
    for (index, case) in fixture["selection"].as_array().unwrap().iter().enumerate() {
        let args = &case["args"];
        assert_eq!(
            select_snapshot(
                args[0].as_str().unwrap(),
                args[1].as_str(),
                args[2].as_str(),
                args[3].as_str().unwrap(),
                args[4].as_i64().map(i128::from)
            ),
            case["expected"].as_str().unwrap(),
            "snapshot case {index}"
        );
    }
}

#[test]
fn one_batch_preserves_per_record_attribution_time_across_reimport() {
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Synthetic','/synthetic');
        INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (1,1,'s','/synthetic/s','Synthetic');").unwrap();
    let records = (0..32)
        .map(|i| {
            serde_json::from_value(json!({
                "usage_record_id":format!("usage-{i}"), "source_record_id":format!("record-{i}"),
                "source_line":i, "total_tokens":1, "total_semantics":"normalized"
            }))
            .unwrap()
        })
        .collect::<Vec<ParsedUsageRecord>>();
    store_usage_records(&connection, 1, 1, &records, None, "synthetic").unwrap();
    let facts = db::rows(
        &connection,
        "SELECT id,attributed_at FROM usage_records ORDER BY id",
        [],
    )
    .unwrap();
    let incorrect = db::row(
        &connection,
        "SELECT count(*) AS count FROM usage_records WHERE attributed_at > imported_at",
        [],
    )
    .unwrap()
    .unwrap();
    assert_eq!(incorrect["count"], 0);
    assert!(facts
        .iter()
        .any(|row| row["attributed_at"] != facts[0]["attributed_at"]));
    store_usage_records(&connection, 1, 1, &records, None, "synthetic").unwrap();
    assert_eq!(
        facts,
        db::rows(
            &connection,
            "SELECT id,attributed_at FROM usage_records ORDER BY id",
            []
        )
        .unwrap()
    );
}
