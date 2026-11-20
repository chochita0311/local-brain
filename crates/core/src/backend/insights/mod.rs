//! Explicit local personal-improvement evidence and analysis runs.
pub mod evidence;
pub mod guidance;
pub mod presentation;
pub mod runs;
pub mod skills;
pub mod usage;

use crate::backend::{BackendError, Result};
use serde_json::Value;
fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(v) => v.as_f64().is_none_or(|n| n != 0.0),
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
fn invalid(message: &str) -> BackendError {
    BackendError::new(422, "insight", message)
}
fn values(value: &Value) -> &[Value] {
    value.as_array().map(Vec::as_slice).unwrap_or(&[])
}
fn text<'a>(value: &'a Value, fallback: &'a str) -> &'a str {
    value.as_str().filter(|s| !s.is_empty()).unwrap_or(fallback)
}
fn required<'a>(value: &'a Value, field: &str) -> Result<&'a str> {
    value[field]
        .as_str()
        .ok_or_else(|| invalid(&format!("{field} is missing or malformed")))
}
