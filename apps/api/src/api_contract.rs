//! Retained public protocol metadata and feature admission.
use localbrain_core::backend::Config;
use serde_json::Value;
use std::{collections::BTreeSet, sync::OnceLock};
pub(crate) fn full() -> &'static Value {
    static CONTRACT: OnceLock<Value> = OnceLock::new();
    CONTRACT.get_or_init(|| {
        serde_json::from_str(include_str!("../resources/openapi.json"))
            .expect("frozen API contract")
    })
}
pub(crate) fn configured(config: &Config) -> Value {
    static FEATURES: OnceLock<Value> = OnceLock::new();
    let mut contract = full().clone();
    let features = FEATURES.get_or_init(|| {
        serde_json::from_str(include_str!("../resources/openapi-features.json"))
            .expect("frozen feature admission")
    });
    contract["paths"]
        .as_object_mut()
        .unwrap()
        .retain(|path, operations| {
            operations.as_object_mut().unwrap().retain(|method, _| {
                features[format!("{} {path}", method.to_ascii_uppercase())]
                    .as_array()
                    .is_some_and(|alternatives| {
                        alternatives.iter().any(|required| {
                            required
                                .as_array()
                                .unwrap()
                                .iter()
                                .all(|name| config.feature(name.as_str().unwrap()))
                        })
                    })
            });
            !operations.as_object().unwrap().is_empty()
        });
    fn references(value: &Value, pending: &mut Vec<String>) {
        let mut items = vec![value];
        while let Some(value) = items.pop() {
            match value {
                Value::Array(values) => items.extend(values),
                Value::Object(values) => {
                    if let Some(reference) = values
                        .get("$ref")
                        .and_then(Value::as_str)
                        .and_then(|value| value.strip_prefix("#/components/schemas/"))
                    {
                        pending.push(reference.into());
                    }
                    items.extend(values.values());
                }
                _ => {}
            }
        }
    }
    let mut pending = Vec::new();
    references(&contract["paths"], &mut pending);
    let mut selected = BTreeSet::new();
    while let Some(name) = pending.pop() {
        if selected.insert(name.clone()) {
            references(&contract["components"]["schemas"][&name], &mut pending);
        }
    }
    if let Some(schemas) = contract["components"]["schemas"].as_object_mut() {
        schemas.retain(|name, _| selected.contains(name));
    }
    contract
}
