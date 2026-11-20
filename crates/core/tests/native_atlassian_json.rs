use localbrain_core::backend::{ingest::parse_session, json};
use serde_json::{json as j, Value};
use std::fs;

#[test]
fn stored_catalog_and_refresh_readers_preserve_ignored_scalars_and_refuse_selected_output() {
    use localbrain_core::backend::{
        atlassian::{access, refresh, registration, sync},
        db,
    };
    let db = rusqlite::Connection::open_in_memory().unwrap();
    db.execute_batch(db::SCHEMA).unwrap();
    db.execute("INSERT INTO external_source_instances(instance_key,provider_kind,service,display_name) VALUES ('synthetic-json','mcp_gateway','jira','Synthetic')",[]).unwrap();
    let raw = r#"{"ignored":NaN,"ignored_unicode":"\ud800","targets":[{"target_id":"space-catalog-site-1","outcome":"changed","requests":[{"metadata":{"project":{"key":"SYN","name":"Source candidate","id":1234567890123456789012345678901234567890,"ignored":"\udfff"}}}]}]}"#;
    db.execute("INSERT INTO maintenance_runs(id,task_type,runner,cwd,status,structured_result_json) VALUES ('lb-json','external_source_sync','claude','/synthetic','completed',?)",[raw]).unwrap();
    db.execute("INSERT INTO external_sync_runs(maintenance_run_id,source_instance_id,source_kind,service,requested_scope_kind,selected_target_count,manifest_schema_version,read_policy_version) VALUES ('lb-json',1,'atlassian','jira','space',1,?,?)",rusqlite::params![sync::MANIFEST_SCHEMA,access::READ_POLICY_VERSION]).unwrap();
    let catalog = registration::space_catalog_candidates(&db, "lb-json", None).unwrap();
    assert_eq!(
        catalog["candidates"][0]["remote_id"],
        "1234567890123456789012345678901234567890"
    );
    json::strict_output(&catalog).unwrap();
    json::strict_output(
        &refresh::refresh_run_result(&db, "lb-json")
            .unwrap()
            .unwrap(),
    )
    .unwrap();
    let selected_name = raw.replace("\"Source candidate\"", r#""\ud800""#);
    db.execute(
        "UPDATE maintenance_runs SET structured_result_json=?",
        [selected_name],
    )
    .unwrap();
    assert_eq!(
        registration::space_catalog_candidates(&db, "lb-json", None)
            .unwrap_err()
            .code,
        "source_unicode"
    );
    assert!(refresh::refresh_run_result(&db, "lb-json").is_ok());
    let selected_target = raw.replace("\"space-catalog-site-1\"", r#""\ud800""#);
    db.execute(
        "UPDATE maintenance_runs SET structured_result_json=?",
        [selected_target],
    )
    .unwrap();
    assert!(registration::space_catalog_candidates(&db, "lb-json", None).is_ok());
    assert_eq!(
        refresh::refresh_run_result(&db, "lb-json")
            .unwrap_err()
            .code,
        "source_unicode"
    );
    let selected_nonfinite = raw.replace("\"changed\"", "NaN");
    db.execute(
        "UPDATE maintenance_runs SET structured_result_json=?",
        [selected_nonfinite],
    )
    .unwrap();
    let result = refresh::refresh_run_result(&db, "lb-json")
        .unwrap()
        .unwrap();
    assert!(result["targets"][0]["outcome"].is_number());
    assert_eq!(
        json::strict_output(&result).unwrap_err().code,
        "json_nonfinite"
    );
    for scalar in [
        r#"{"$serde_json::private::Number":"NaN"}"#,
        r#"{"$serde_json::private::Number":"1"}"#,
    ] {
        let literal_tag = raw.replace("\"changed\"", scalar);
        db.execute(
            "UPDATE maintenance_runs SET structured_result_json=?",
            [literal_tag],
        )
        .unwrap();
        let result = refresh::refresh_run_result(&db, "lb-json")
            .unwrap()
            .unwrap();
        assert_eq!(
            json::canonical(&result["targets"][0]["outcome"]).unwrap(),
            scalar
        );
        assert!(result["targets"][0]["outcome"].is_object());
        json::strict_output(&result).unwrap();
    }
    let oversized = raw.replace(
        "1234567890123456789012345678901234567890",
        &"1".repeat(4301),
    );
    db.execute(
        "UPDATE maintenance_runs SET structured_result_json=?",
        [oversized],
    )
    .unwrap();
    assert_eq!(
        registration::space_catalog_candidates(&db, "lb-json", None)
            .unwrap_err()
            .status,
        500
    );
    assert_eq!(
        refresh::refresh_run_result(&db, "lb-json")
            .unwrap_err()
            .status,
        500
    );
}

#[test]
fn private_pretty_artifact_bytes_match_python_without_recursive_serialization() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/json_pretty.json")).unwrap();
    assert_eq!(cases.len(), 4);
    for case in cases {
        let value = json::decode(case["raw"].as_str().unwrap()).unwrap();
        assert_eq!(
            json::pretty(&value).unwrap(),
            case["expected"].as_str().unwrap()
        );
    }
}

#[test]
fn stored_numbers_and_canonical_bytes_match_python_without_coercion() {
    let cases: Vec<Value> = serde_json::from_str(CASES).unwrap();
    for case in cases {
        let value = json::decode(case["raw"].as_str().unwrap()).unwrap();
        assert_eq!(
            json::canonical(&value).unwrap(),
            case["canonical"].as_str().unwrap()
        );
        let db = rusqlite::Connection::open_in_memory().unwrap();
        db.execute_batch("CREATE TABLE facts(body TEXT NOT NULL)")
            .unwrap();
        db.execute(
            "INSERT INTO facts(body) VALUES (?)",
            [json::canonical(&value).unwrap()],
        )
        .unwrap();
        let stored: String = db
            .query_row("SELECT body FROM facts", [], |r| r.get(0))
            .unwrap();
        assert_eq!(
            json::canonical(&json::decode(&stored).unwrap()).unwrap(),
            case["canonical"].as_str().unwrap()
        );
    }
    let value = json::decode(r#"{"count":NaN,"overflow":1e999}"#).unwrap();
    assert!(value["count"].is_number());
    assert!(value["overflow"].is_number());
    assert_eq!(
        json::strict_output(&value).unwrap_err().code,
        "json_nonfinite"
    );
    assert!(json::encode_http(&value).is_err());
    let named =
        json::decode(r#"{"NaN":"Infinity","other":"-Infinity","exponent":"1e999"}"#).unwrap();
    assert!(json::strict_output(&named).is_ok());
    assert_eq!(
        json::decode(&json::encode_http(&named).unwrap()).unwrap(),
        named
    );
}

#[test]
fn scoped_unicode_ignores_unselected_values_and_refuses_selected_keys_and_strings() {
    let raw = r#"{"selected":"Keep visible message","literal":"\u0000","ignored":"\ud800"}"#;
    let scope = json::Scope::for_document(raw);
    let value = scope.parse(raw).unwrap();
    scope
        .materialized(&j!({"selected":value["selected"],"literal":value["literal"]}))
        .unwrap();
    assert_eq!(value["literal"], "\0");
    assert_eq!(
        scope.materialized(&value["ignored"]).unwrap_err().code,
        "source_unicode"
    );
    assert!(json::decode(r#"{"\ud800":"text"}"#).is_err());
    let controls = (0..=255)
        .map(|v| char::from_u32(v).unwrap())
        .collect::<String>();
    let raw = format!(
        r#"{{"literal":{},"ignored":"\udfff"}}"#,
        serde_json::to_string(&controls).unwrap()
    );
    let scope = json::Scope::for_document(&raw);
    let value = scope.parse(&raw).unwrap();
    scope.materialized(&value["literal"]).unwrap();
    assert_eq!(value["literal"], controls);
    assert!(scope.materialized(&value["ignored"]).is_err());
    let raw = r#"{"ignored":"\ud800","selected":{"n":NaN,"literal":{"$serde_json::private::Number":"NaN"}}}"#;
    let scope = json::Scope::for_document(raw);
    let value = scope.parse(raw).unwrap();
    scope.materialized(&value["selected"]).unwrap();
    assert_eq!(
        json::canonical(&value["selected"]).unwrap(),
        r#"{"literal":{"$serde_json::private::Number":"NaN"},"n":NaN}"#
    );
    assert_eq!(
        json::strict_output(&value["selected"]).unwrap_err().status,
        500
    );
}

#[test]
fn nested_decoding_cannot_turn_a_real_escape_into_the_opaque_surrogate_marker() {
    let nested = r#"{"value":"\"\u005c\u0075\u0030\u0030\u0030\u0030\"","ignored":"\ud800"}"#;
    let raw = format!(
        r#"{{"nested":{},"ignored":"\ud800"}}"#,
        serde_json::to_string(nested).unwrap()
    );
    let scope = json::Scope::for_document(&raw);
    let outer = scope.parse(&raw).unwrap();
    let inner = scope.parse(outer["nested"].as_str().unwrap()).unwrap();
    let selected = scope.parse(inner["value"].as_str().unwrap()).unwrap();
    assert_eq!(selected, "\0");
    scope.materialized(&selected).unwrap();
    assert!(scope.materialized(&inner["ignored"]).is_err());
}

#[test]
fn strict_protocol_rejects_decoded_duplicates_nonfinite_and_lossy_integers() {
    for raw in [
        r#"{"x":1,"\u0078":2}"#,
        r#"{"array":[{"x":1,"x":2}]}"#,
        "NaN",
        "Infinity",
        "-Infinity",
        "1e999",
        r#""\ud800""#,
    ] {
        assert!(json::decode_unique(raw.as_bytes()).is_err(), "{raw}");
    }
    let integer = "1".repeat(100);
    let raw = format!(r#"{{"integer":{integer},"$serde_json::private::Number":"NaN"}}"#);
    let value = json::decode_unique(raw.as_bytes()).unwrap();
    assert_eq!(value["integer"].as_number().unwrap().to_string(), integer);
    assert!(value["$serde_json::private::Number"].is_string());
    assert!(json::decode_unique("1".repeat(4300).as_bytes()).is_ok());
    assert!(json::decode_unique("1".repeat(4301).as_bytes()).is_err());
    let oversized = Value::Number(serde_json::Number::from_string_unchecked("1".repeat(4301)));
    assert_eq!(json::strict_output(&oversized).unwrap_err().status, 500);
    let deep = format!("{}0{}", "[".repeat(190), "]".repeat(190));
    let value = json::decode_unique(deep.as_bytes()).unwrap();
    assert_eq!(json::encode_http(&value).unwrap(), deep);
}

#[test]
fn provider_metadata_with_literal_reserved_number_keys_retains_valid_messages() {
    let temp = tempfile::Builder::new()
        .prefix("lb-native-reserved-json-")
        .tempdir()
        .unwrap();
    for provider in ["claude", "codex"] {
        let path = temp.path().join(format!("{provider}.jsonl"));
        let raw = if provider == "claude" {
            r#"{"type":"user","sessionId":"reserved","message":{"content":"Keep message"},"ignored":{"$serde_json::private::Number":"not a number"}}"#
        } else {
            r#"{"type":"event_msg","payload":{"type":"user_message","message":"Keep message"},"ignored":{"\u0024serde_json::private::Number":"not a number"}}"#
        };
        fs::write(&path, raw).unwrap();
        let parsed = parse_session(provider, &path).unwrap().unwrap();
        assert_eq!(parsed.events.len(), 1);
        assert_eq!(parsed.skipped_lines, 0);
        assert_eq!(parsed.events[0].text.as_deref(), Some("Keep message"));
    }
}

const CASES: &str = r####"[{"raw":"{\"z\":NaN,\"a\":Infinity,\"negative\":-Infinity,\"overflow\":1e999,\"zero\":-0.0,\"small\":1e-5,\"large\":1e16,\"integer\":10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000,\"words\":[\"NaN\",\"Infinity\",\"-Infinity\"],\"unicode\":\"한글\\u0000\\u2028\"}","canonical":"{\"a\":Infinity,\"integer\":10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000,\"large\":1e+16,\"negative\":-Infinity,\"overflow\":Infinity,\"small\":1e-05,\"unicode\":\"한글\\u0000 \",\"words\":[\"NaN\",\"Infinity\",\"-Infinity\"],\"z\":NaN,\"zero\":-0.0}"},{"raw":"{\"$serde_json::private::Number\":\"NaN\",\"x\":[{\"\\u0024serde_json::private::Number\":\"1\"}],\"n\":123456789012345678901234567890}","canonical":"{\"$serde_json::private::Number\":\"NaN\",\"n\":123456789012345678901234567890,\"x\":[{\"$serde_json::private::Number\":\"1\"}]}"},{"raw":"{\"a\":1,\"a\":2,\"b\":{\"x\":1,\"x\":3}}","canonical":"{\"a\":2,\"b\":{\"x\":3}}"},{"raw":"{\"quote\": \"single'double\\\"slash\\\\\", \"tiny\": 1.234567891234568e-19}","canonical":"{\"quote\":\"single'double\\\"slash\\\\\",\"tiny\":1.234567891234568e-19}"}]"####;
