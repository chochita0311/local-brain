use localbrain_core::backend::clock;
use serde_json::Value;
#[test]
fn frozen_python_source_timestamps() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/native-timestamps.json")).unwrap();
    for case in cases {
        let input = case["input"].as_str().unwrap();
        let parsed = clock::parse_iso_datetime(input);
        if case["local"].is_null() {
            assert!(
                parsed.is_none() || parsed.unwrap().utc().is_none(),
                "unexpected admission: {input:?}"
            );
        } else {
            let parsed = parsed.unwrap_or_else(|| panic!("source rejected: {input:?}"));
            assert_eq!(
                parsed.isoformat(),
                case["local"].as_str().unwrap(),
                "local {input:?}"
            );
            assert_eq!(
                parsed.utc().map(clock::isoformat).as_deref(),
                case["utc"].as_str(),
                "UTC {input:?}"
            );
        }
    }
}
