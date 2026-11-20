use localbrain_core::backend::insights::guidance::*;
use serde_json::{json, Value};
fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../src/backend/insights/fixtures/guidance-golden.json"
    ))
    .unwrap()
}
#[test]
fn all_frozen_guide_bytes_hashes_and_both_report_schemas_match() {
    let all = fixture();
    let bundle=build_guide_bundle(&json!({"version":"personal-insight-evidence-v2","scope":{"mode":"discover","question":null}})).unwrap();
    assert_eq!(bundle, all["bundle"]);
    assert_eq!(guide_text(&bundle).unwrap(), all["guide_text"]);
    for case in all["schemas"].as_array().unwrap() {
        let ids: Vec<String> = serde_json::from_value(case["ids"].clone()).unwrap();
        assert_eq!(
            result_schema(&ids, case["version"].as_str().unwrap()).unwrap(),
            case["expected"]
        );
    }
    for scope in [
        json!({"mode":"future"}),
        json!({"mode":"ask","question":" "}),
        json!({"mode":"discover","question":"unexpected"}),
    ] {
        assert!(build_guide_bundle(
            &json!({"version":"personal-insight-evidence-v2","scope":scope})
        )
        .is_err());
    }
}
#[test]
fn all_original_result_validation_and_historical_provenance_cases_match() {
    let all = fixture();
    for (index, case) in all["cases"].as_array().unwrap().iter().enumerate() {
        let manifest = &all["manifests"][case["manifest"].as_u64().unwrap() as usize];
        let bundle = &all["bundles"][case["bundle"].as_u64().unwrap() as usize];
        match validate_guided_result(&case["value"], manifest, bundle) {
            Ok(value) => {
                assert!(
                    case.get("error").is_none(),
                    "case {index} unexpectedly admitted"
                );
                assert_eq!(value, case["expected"], "case {index}");
            }
            Err(error) => {
                assert_eq!(error.message, case["error"], "case {index}");
                if case["error_type"] == "SuppliedMessageRequestError" {
                    assert_eq!(error.code, "insight-supplied-message");
                }
            }
        }
    }
}
