//! Frozen datetime.timestamp semantics, with TZ confined to isolated test children.
use localbrain_core::backend::{
    contexts::{self, scan::notes_timestamp_ns},
    db,
    ingest::{NoObservers, ScanControl},
    Config, Result,
};
use serde_json::{json, Value};
#[test]
fn notes_timestamp_matches_frozen_aware_naive_dst_precision_and_range_cases() {
    for zone in [
        "UTC",
        "Asia/Seoul",
        "America/New_York",
        "Australia/Lord_Howe",
        "Pacific/Apia",
    ] {
        let output = std::process::Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "notes_timestamp_child",
                "--ignored",
                "--test-threads=1",
            ])
            .env("TZ", zone)
            .env("LOCALBRAIN_NATIVE_NOTES_TIMESTAMP_ZONE", zone)
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "zone={zone}\n{}\n{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
    }
}
#[test]
#[ignore = "isolated OS-timezone scalar oracle"]
fn notes_timestamp_child() {
    let Ok(zone) = std::env::var("LOCALBRAIN_NATIVE_NOTES_TIMESTAMP_ZONE") else {
        return;
    };
    let cases: Vec<Value> = serde_json::from_str(include_str!(
        "native_context_fixtures/notes_timestamps.json"
    ))
    .unwrap();
    assert_eq!(cases.len(), 100);
    let mut failures = vec![];
    for case in cases.into_iter().filter(|c| c["zone"] == zone) {
        let actual = notes_timestamp_ns(&case["value"]);
        if case.get("error").is_some() {
            if actual.is_ok() {
                failures.push(format!("{case} unexpectedly {actual:?}"));
            }
        } else if actual.as_ref().ok() != case["expected"].as_i64().as_ref() {
            failures.push(format!("{case} actual {actual:?}"));
        }
    }
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}
#[test]
fn notes_scanner_derives_system_zone_independently_of_presentation_preferences() {
    for zone in ["Asia/Seoul", "America/New_York", "Australia/Lord_Howe"] {
        let output = std::process::Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "notes_use_system_zone_child",
                "--ignored",
                "--test-threads=1",
            ])
            .env("TZ", zone)
            .env("LOCALBRAIN_NATIVE_NOTES_ZONE_PROBE", zone)
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "zone={zone}\n{}\n{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
    }
}
#[test]
#[ignore = "only launched by the isolated system-timezone regression"]
fn notes_use_system_zone_child() {
    let Ok(zone) = std::env::var("LOCALBRAIN_NATIVE_NOTES_ZONE_PROBE") else {
        return;
    };
    struct Reader;
    impl contexts::scan::ContextReader for Reader {
        fn apple_notes(&self, _: &ScanControl) -> Result<Value> {
            Ok(
                json!([{"id":"synthetic-naive-note","title":"Synthetic","modified_at":"2026-01-01T01:02:03.123456","body":"<p>Only synthetic Notes adapter data</p>"}]),
            )
        }
        fn spotlight_pdf(&self, _: &std::path::Path, _: &ScanControl) -> Result<Option<String>> {
            panic!("Notes-only synthetic source must not access Spotlight")
        }
    }
    let temp = tempfile::Builder::new()
        .prefix("lb-notes-zone-")
        .tempdir()
        .unwrap();
    let config = Config::for_data_dir(temp.path().join("data"));
    assert_eq!(config.timezone_name, "UTC");
    db::initialize(&config).unwrap();
    let db = db::connect(&config).unwrap();
    contexts::add_apple_notes_source(&db).unwrap();
    contexts::scan::scan_documents(
        &db,
        &config,
        false,
        None,
        &ScanControl::default(),
        &NoObservers,
        &Reader,
    )
    .unwrap();
    let actual: i64 = db
        .query_row("SELECT mtime_ns FROM context_documents", [], |r| r.get(0))
        .unwrap();
    let cases: Vec<Value> = serde_json::from_str(include_str!(
        "native_context_fixtures/notes_timestamps.json"
    ))
    .unwrap();
    let expected = cases
        .iter()
        .find(|c| c["zone"] == zone && c["value"] == "2026-01-01T01:02:03.123456")
        .unwrap()["expected"]
        .as_i64()
        .unwrap();
    assert_eq!(actual, expected);
}
