//! Differential outputs from the frozen routes' actual FastAPI dependants.
//! No interpreter, application lifecycle, database or model is used at runtime.
use axum::http::{HeaderMap, Method};
use localbrain_api::{parameters, transport::RequestContext};
use serde_json::{json, Value};
use std::collections::BTreeMap;

fn context(method: &str, uri: &str) -> RequestContext {
    let mut headers = HeaderMap::new();
    headers.insert("host", "127.0.0.1:8123".parse().unwrap());
    RequestContext::new(
        Method::from_bytes(method.as_bytes()).unwrap(),
        headers,
        uri.parse().unwrap(),
    )
    .unwrap()
}
fn strings(value: &Value) -> BTreeMap<String, String> {
    value
        .as_object()
        .unwrap()
        .iter()
        .map(|(name, value)| (name.clone(), value.as_str().unwrap().into()))
        .collect()
}

#[test]
fn frozen_dependency_errors_coercions_aliases_and_atomicity_match() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/native-http-parameters.json")).unwrap();
    assert_eq!(fixture["schema_shapes"], 14);
    assert_eq!(fixture["fields"], 148);
    assert_eq!(fixture["operations"], 124);
    let cases = fixture["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 1309);
    for case in cases {
        let method = case["method"].as_str().unwrap();
        let uri = case["uri"].as_str().unwrap();
        let mut context = context(method, uri);
        let before_uri = context.uri.clone();
        let before_path = context.path.clone();
        let before_query = context.query.clone();
        let mut params = strings(&case["params"]);
        let before_params = params.clone();
        let result = parameters::validate(
            case["pattern"].as_str().unwrap(),
            method,
            &mut context,
            &mut params,
        );
        if case["errors"].as_array().unwrap().is_empty() {
            result.unwrap_or_else(|error| {
                panic!("{}: {} {}", case["case"], error.code, error.message)
            });
        } else {
            let error = result.unwrap_err();
            assert_eq!(error.status, 422, "{}", case["case"]);
            assert_eq!(error.detail(), case["errors"], "{}", case["case"]);
            assert_eq!(
                context.query, before_query,
                "{} published query coercions on error",
                case["case"]
            );
            assert_eq!(
                params, before_params,
                "{} published path coercions on error",
                case["case"]
            );
        }
        assert_eq!(context.uri, before_uri, "{} changed raw URI", case["case"]);
        assert_eq!(
            context.path, before_path,
            "{} changed decoded path",
            case["case"]
        );
        assert_eq!(
            context.query,
            strings(&case["expected_query"]),
            "{} query",
            case["case"]
        );
        assert_eq!(
            params,
            strings(&case["expected_params"]),
            "{} params",
            case["case"]
        );
    }
}

#[test]
fn native_helpers_unknown_fields_and_other_methods_remain_untouched() {
    for (pattern, method, uri, params) in [
        (
            "/__native_helper/{id}",
            "GET",
            "/__native_helper/1.0?launch=invalid&page=1.25",
            json!({"id":"1.0"}),
        ),
        (
            "/api/health",
            "GET",
            "/api/health?launch=invalid&page=1.25",
            json!({}),
        ),
        (
            "/natural-search",
            "POST",
            "/natural-search?page=invalid&mode=invalid",
            json!({}),
        ),
    ] {
        let mut context = context(method, uri);
        let mut params = strings(&params);
        let original_query = context.query.clone();
        let original_params = params.clone();
        parameters::validate(pattern, method, &mut context, &mut params).unwrap();
        assert_eq!(context.query, original_query);
        assert_eq!(params, original_params);
        assert_eq!(context.uri.to_string(), uri);
    }
}
