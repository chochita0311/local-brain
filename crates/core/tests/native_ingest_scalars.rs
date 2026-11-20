//! Complete outputs from the frozen Python providers, including Python repr
//! of container identities and parent IDs. No interpreter is used by this test.
use localbrain_core::backend::ingest::parse_session;
use serde_json::{json, Value};
use std::fs;

#[test]
fn selected_container_identities_match_complete_frozen_provider_dtos() {
    let cases: Vec<Value> = serde_json::from_str(include_str!(
        "native_ingest_fixtures/structured_scalars.json"
    ))
    .unwrap();
    assert_eq!(cases.len(), 36);
    let root = tempfile::Builder::new()
        .prefix("lb-native-structured-scalars-")
        .tempdir()
        .unwrap();
    for case in cases {
        let provider = case["provider"].as_str().unwrap();
        let path = root.path().join(
            case["expected"]["source_path"]
                .as_str()
                .unwrap()
                .strip_prefix("/synthetic/")
                .unwrap(),
        );
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(&path, case["raw"].as_str().unwrap()).unwrap();
        let actual = parse_session(provider, &path).unwrap().unwrap();
        let mut expected = case["expected"].clone();
        expected["source_path"] = json!(path);
        assert_eq!(
            serde_json::to_value(actual).unwrap(),
            expected,
            "{provider}: {}",
            case["raw"]
        );
    }
}

#[test]
fn selected_primitive_surrogate_identity_retains_explicit_utf8_refusal() {
    let root = tempfile::Builder::new()
        .prefix("lb-native-structured-scalar-refusal-")
        .tempdir()
        .unwrap();
    for provider in ["claude", "codex"] {
        let path = root.path().join(format!("{provider}.jsonl"));
        let raw = if provider == "claude" {
            r#"{"type":"user","sessionId":"\ud800","message":{"content":"Keep source message"}}"#
        } else {
            r#"{"type":"session_meta","payload":{"id":"\ud800"}}
{"type":"event_msg","payload":{"type":"user_message","message":"Keep source message"}}"#
        };
        fs::write(&path, raw).unwrap();
        assert_eq!(
            parse_session(provider, &path).unwrap_err().code,
            "source_unicode"
        );
    }
}
