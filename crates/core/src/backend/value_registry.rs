//! One compiled vocabulary owner supplies bounded ordinary-screen labels.
use super::{BackendError, Result};
use serde_json::Value;
use std::sync::OnceLock;
pub fn registry() -> &'static Value {
    static REGISTRY: OnceLock<Value> = OnceLock::new();
    REGISTRY.get_or_init(|| {
        serde_json::from_str(include_str!("../../resources/value-registry.json"))
            .expect("validated compiled value registry")
    })
}
fn failure(message: impl Into<String>) -> BackendError {
    BackendError::new(500, "value-registry", message)
}
fn key(value: &Value) -> String {
    match value {
        Value::Null => "__null__".into(),
        Value::Bool(value) => if *value { "1" } else { "0" }.into(),
        Value::String(value) => value.clone(),
        Value::Number(_) => super::json::canonical(value).unwrap_or_else(|_| value.to_string()),
        _ => value.to_string(),
    }
}
pub fn value_family(id: &str) -> Result<&'static Value> {
    registry()["families"]
        .as_array()
        .and_then(|families| families.iter().find(|family| family["id"] == id))
        .ok_or_else(|| failure(format!("unknown value family: {id}")))
}
pub fn visible_value_label(id: &str, value: &Value, fallback: Option<&str>) -> Result<String> {
    let family = value_family(id)?;
    let presentation = &family["presentation"];
    let mode = presentation["mode"].as_str().unwrap_or("");
    if mode == "internal-only" {
        return Err(failure(format!("{id} is not visible")));
    }
    let key = key(value);
    if !family["values"]
        .as_array()
        .is_some_and(|values| values.iter().any(|value| self::key(value) == key))
    {
        let selected = fallback.unwrap_or(if value.is_null() { "null" } else { "unknown" });
        let policy = &family["fallbacks"][selected];
        if policy["action"] != "label" {
            return Err(failure(format!("{id} rejects {selected} fallback")));
        }
        return policy["label"]
            .as_str()
            .map(str::to_owned)
            .ok_or_else(|| failure(format!("{id} has no fallback label")));
    }
    if mode == "direct" {
        return Ok(key);
    }
    presentation["labels"][&key]
        .as_str()
        .map(str::to_owned)
        .ok_or_else(|| failure(format!("{id} has no label for {key}")))
}
pub fn display_value_label(id: &str, value: &Value) -> String {
    visible_value_label(id, value, None).unwrap_or_else(|_| "표시할 수 없음".into())
}
pub fn visible_value_help(id: &str) -> Result<String> {
    let family = value_family(id)?;
    if family["presentation"]["mode"] == "internal-only" {
        return Err(failure(format!("{id} is not visible")));
    }
    Ok(family["presentation"]["help"].as_str().unwrap_or("").into())
}
