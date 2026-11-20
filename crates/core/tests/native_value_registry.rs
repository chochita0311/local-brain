use localbrain_core::backend::value_registry;
use serde_json::Value;
#[test]
fn all_native_labels_and_fallback_refusals_match_frozen_python() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/native-value-labels.json")).unwrap();
    for case in cases {
        let id = case["family"].as_str().unwrap();
        let result =
            value_registry::visible_value_label(id, &case["value"], case["fallback"].as_str());
        if let Some(error) = case["expected"]["error"].as_str() {
            assert_eq!(result.unwrap_err().message, error, "{case}");
        } else {
            assert_eq!(result.unwrap(), case["expected"]["label"], "{case}");
        }
        assert_eq!(
            value_registry::display_value_label(id, &case["value"]),
            case["display"],
            "{case}"
        );
    }
    assert_eq!(
        value_registry::display_value_label("unknown", &Value::Null),
        "표시할 수 없음"
    );
}
