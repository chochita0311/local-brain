use localbrain_core::backend::{
    db,
    usage::{usage_dashboard_data, UsageOptions},
};
use rusqlite::Connection;
use serde_json::json;
fn seed() -> Connection {
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Synthetic','/synthetic'); INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (1,1,'s','/synthetic/s','Synthetic'); INSERT INTO usage_price_snapshots VALUES ('s','Synthetic','synthetic','fixed','2026-01-01');").unwrap();
    connection
}
fn add(
    connection: &Connection,
    id: &str,
    time: Option<&str>,
    tokens: Option<i64>,
    cost: Option<&str>,
) {
    connection.execute("INSERT INTO usage_records(id,source_id,session_id,source_record_id,source_line,occurred_at,raw_model,model_name,total_tokens,total_semantics,capability_state,capability_json,calculation_state,estimated_cost_usd,price_snapshot_id,calculator_version,calculated_at,attributed_at) VALUES (?,1,1,?,1,?,'test','test',?,'normalized','complete','{}',?,?,'s','fixed','2026-11-18','2026-11-18')",rusqlite::params![id,id,time,tokens,if cost.is_some(){"priced"}else{"unpriced"},cost]).unwrap();
}
fn options() -> UsageOptions {
    UsageOptions {
        today: Some(chrono::NaiveDate::from_ymd_opt(2026, 11, 18).unwrap()),
        ..UsageOptions::default()
    }
}
#[test]
fn visible_read_avoids_full_detail_columns_and_does_not_mutate_facts() {
    let connection = seed();
    add(
        &connection,
        "r",
        Some("2026-11-04T12:00:00Z"),
        Some(170),
        Some("0.000000000000000000000000000000000000123456789"),
    );
    connection
        .execute("UPDATE sessions SET title=CAST(X'FF' AS TEXT)", [])
        .unwrap();
    connection
        .execute(
            "UPDATE usage_price_snapshots SET label=CAST(X'FF' AS TEXT)",
            [],
        )
        .unwrap();
    let before = db::rows(&connection, "SELECT * FROM usage_records", []).unwrap();
    let mut selected = options();
    selected.visible_only = true;
    let result = usage_dashboard_data(&connection, &selected).unwrap();
    assert_eq!(result["aggregate"]["usage_record_count"], 1);
    assert_eq!(
        result["aggregate"]["estimated_cost"].to_string(),
        "0.000000000000000000000000000000000000123456789"
    );
    for field in [
        "activity",
        "month_to_date",
        "freshness",
        "projection",
        "last_calculated_at",
    ] {
        assert!(result[field].is_null(), "{field}");
    }
    assert_eq!(result["snapshot_labels"], json!([]));
    assert_eq!(
        before,
        db::rows(&connection, "SELECT * FROM usage_records", []).unwrap()
    );
    selected.visible_only = false;
    assert!(usage_dashboard_data(&connection, &selected).is_err());
}
#[test]
fn exceptional_untimed_rows_count_globally_and_source_empty_differs_from_filtered() {
    let connection = seed();
    add(&connection, "old", Some("2020-01-01"), Some(1), None);
    add(&connection, "bad", Some("2999-broken"), None, None);
    add(&connection, "null", None, None, None);
    let mut selected = options();
    selected.visible_only = true;
    let result = usage_dashboard_data(&connection, &selected).unwrap();
    assert_eq!(result["empty_kind"], "filtered");
    assert_eq!(
        result["limitations"][0],
        "2 usage records have no usable occurrence time and are excluded from history."
    );
    assert_eq!(result["summary"][0]["value"], "Unavailable");
    assert_eq!(result["history"].as_array().unwrap().len(), 30);
    connection.execute("DELETE FROM usage_records", []).unwrap();
    assert_eq!(
        usage_dashboard_data(&connection, &selected).unwrap()["empty_kind"],
        "source"
    );
}
#[test]
fn very_large_integer_totals_and_half_even_formatting_remain_exact() {
    let connection = seed();
    for id in ["a", "b", "c"] {
        add(
            &connection,
            id,
            Some("2026-11-04"),
            Some(i64::MAX),
            Some("0.00005"),
        );
    }
    let result = usage_dashboard_data(&connection, &options()).unwrap();
    assert_eq!(
        result["aggregate"]["total_tokens"].to_string(),
        "27670116110564327421"
    );
    assert_eq!(result["aggregate"]["estimated_cost"].to_string(), "0.00015");
    assert_eq!(result["summary"][0]["value"], "$0.0002");
    assert_eq!(result["history"][0]["bar_label"], "<$1");
}
#[test]
fn projection_uses_wall_calendar_month_and_preserves_fractional_instant() {
    let connection = seed();
    add(
        &connection,
        "r",
        Some("2026-11-04T12:00:00Z"),
        Some(1),
        Some("1"),
    );
    let mut selected = options();
    selected.today = None;
    selected.timezone_name = "America/New_York".into();
    selected.now = Some(
        chrono::DateTime::parse_from_rfc3339("2026-11-16T05:00:00.000001Z")
            .unwrap()
            .with_timezone(&chrono::Utc),
    );
    let result = usage_dashboard_data(&connection, &selected).unwrap();
    // DST ended Nov 1. Calendar elapsed is 15 days plus one microsecond,
    // rather than elapsed UTC hours since local month start.
    assert_eq!(result["projection"]["elapsed_fraction"], "0.500000");
    assert_eq!(
        result["projection"]["projected_cost"].to_string(),
        "1.999999999998456790123457981"
    );
    assert_eq!(
        result["projection"]["calculated_at"],
        "2026-11-16T05:00:00.000001+00:00"
    );
}
