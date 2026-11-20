use localbrain_core::backend::workflow::{correction::*, focus::WorkflowFocusProjection, map::*};
use serde_json::{json, Value};

fn presentation() -> Value {
    serde_json::from_str(include_str!(
        "../src/backend/workflow/fixtures/presentation-golden.json"
    ))
    .unwrap()
}
fn difference(expected: &Value, actual: &Value, path: &str) -> Option<String> {
    match (expected, actual) {
        (Value::Object(a), Value::Object(b)) => {
            if a.len() != b.len() {
                return Some(format!("{path}: object lengths {} != {}", a.len(), b.len()));
            }
            for (key, value) in a {
                if let Some(error) = difference(value, &b[key], &format!("{path}/{key}")) {
                    return Some(error);
                }
            }
            None
        }
        (Value::Array(a), Value::Array(b)) => {
            if a.len() != b.len() {
                return Some(format!("{path}: array lengths {} != {}", a.len(), b.len()));
            }
            for (index, (a, b)) in a.iter().zip(b).enumerate() {
                if let Some(error) = difference(a, b, &format!("{path}/{index}")) {
                    return Some(error);
                }
            }
            None
        }
        _ => {
            (expected != actual).then(|| format!("{path}: expected {expected}, received {actual}"))
        }
    }
}
#[test]
fn full_map_controls_provenance_and_client_projection_match_frozen_python() {
    let fixture = presentation();
    for case in fixture["cases"].as_array().unwrap() {
        let projection: WorkflowFocusProjection =
            serde_json::from_value(case["projection"].clone()).unwrap();
        let view = workflow_map_view(&projection, case["selected"].as_i64().unwrap()).unwrap();
        if let Some(error) = difference(&case["expected"], &view, "") {
            panic!("{}: {error}", case["name"]);
        }
        let serialized = serde_json::to_string(&view).unwrap();
        assert!(!serialized.contains("PRIVATE-SYNTHETIC-NOTE"));
        for episode in view["client_projection"]["episodes"].as_array().unwrap() {
            assert_eq!(episode.as_object().unwrap().len(), 9);
            assert!(episode.get("evidence_groups").is_none());
        }
    }
    for state in fixture["states"].as_array().unwrap() {
        assert_eq!(
            workflow_map_state_view(
                state["status"].as_str().unwrap(),
                state["selected"].as_i64().unwrap()
            )
            .unwrap(),
            state["expected"]
        );
    }
}
#[test]
fn malformed_presentation_is_rejected_without_erasing_or_fabricating_boundaries() {
    let fixture = presentation();
    let source = &fixture["cases"][5]["projection"];
    let mut variants = vec![];
    for field in [
        "boundary_key",
        "boundary_kind",
        "assertion_kind",
        "source_episode_key",
        "before_meaning",
        "after_meaning",
        "authority",
        "resolution",
        "created_at",
    ] {
        let mut value = source.clone();
        value["assertions"][0][field] = Value::Null;
        variants.push(value);
    }
    for (field, value) in [
        ("id", json!(true)),
        ("supersedes_assertion_id", json!(0)),
        ("restored_assertion_id", json!(-1)),
        ("boundary_key", json!("wrong")),
        ("resolution", json!("future")),
        ("resolution_reason", json!("future")),
        ("target_episode_key", Value::Null),
    ] {
        let mut projection = source.clone();
        projection["assertions"][0][field] = value;
        variants.push(projection);
    }
    let mut value = source.clone();
    value["assertions"]
        .as_array_mut()
        .unwrap()
        .push(source["assertions"][0].clone());
    variants.push(value);
    let mut value = source.clone();
    value["relations"][0]["target_episode_key"] = json!("session:".to_owned() + &"0".repeat(64));
    variants.push(value);
    let mut value = source.clone();
    value["base_relations"][0]["source_episode_key"] = json!("absent");
    variants.push(value);
    let mut value = source.clone();
    value["base_episode_lifecycle"][0]["episode_key"] = json!("absent");
    variants.push(value);
    let mut value = source.clone();
    value["assertion_revision"] = Value::Null;
    variants.push(value);
    for (index, value) in variants.into_iter().enumerate() {
        let projection: WorkflowFocusProjection = serde_json::from_value(value).unwrap();
        assert!(
            workflow_map_view(&projection, 10).is_err(),
            "variant {index}"
        );
    }
    let projection: WorkflowFocusProjection = serde_json::from_value(source.clone()).unwrap();
    assert!(workflow_map_view(&projection, 0).is_err());
    assert!(workflow_map_state_view("future", 10).is_err());
}
#[test]
fn strict_forms_match_frozen_python_acceptance_errors_and_precedence() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../src/backend/workflow/fixtures/correction-form-golden.json"
    ))
    .unwrap();
    for case in fixture["cases"].as_array().unwrap() {
        let hex = case["hex_body"].as_str().unwrap();
        let body = (0..hex.len())
            .step_by(2)
            .map(|i| u8::from_str_radix(&hex[i..i + 2], 16).unwrap())
            .collect::<Vec<_>>();
        match parse_workflow_correction_form(case["content_type"].as_str(), &body) {
            Ok(request) => {
                assert!(
                    case.get("error").is_none(),
                    "{} unexpectedly admitted",
                    case["name"]
                );
                assert_eq!(
                    serde_json::to_value(&request).unwrap(),
                    case["expected"],
                    "{}",
                    case["name"]
                );
                let domain = request.domain_request();
                assert!(domain.get("action").is_none());
                if request.action == "undo" {
                    assert_eq!(domain.as_object().unwrap().len(), 2);
                } else {
                    assert_eq!(domain["assertion_kind"], request.action);
                }
            }
            Err(error) => assert_eq!(
                json!({"status":error.status,"code":error.code,"message":error.message}),
                case["error"],
                "{}",
                case["name"]
            ),
        }
    }
}
#[test]
fn explicit_cross_site_is_rejected_before_form_or_database_work() {
    for value in [Some("cross-site"), Some("\u{1c}CROSS-SITE\u{a0}")] {
        let error = reject_cross_site_workflow_correction(value).unwrap_err();
        assert_eq!(
            (error.status, error.code.as_str()),
            (400, "cross-site-request")
        );
    }
    for value in [
        None,
        Some("same-origin"),
        Some("none"),
        Some(""),
        Some("future-value"),
    ] {
        reject_cross_site_workflow_correction(value).unwrap();
    }
}
