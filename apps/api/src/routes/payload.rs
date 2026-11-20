//! Validation for the existing JSON form contracts; unknown keys remain ignored.
use localbrain_core::backend::{BackendError, Result};
use serde_json::{json, Value};
fn invalid(value: &Value, key: &str, kind: &str, message: &str) -> BackendError {
    let mut error = json!({"type":kind,"loc":["body",key],"msg":message,"input":value.get(key).cloned().unwrap_or(Value::Null)});
    if !value.as_object().is_some_and(|map| map.contains_key(key)) {
        error["type"] = json!("missing");
        error["msg"] = json!("Field required");
    }
    BackendError::new(422, "validation", "Invalid request").with_details(json!([error]))
}
pub fn string<'a>(
    value: &'a Value,
    key: &str,
    min: usize,
    max: usize,
    optional: bool,
) -> Result<Option<&'a str>> {
    let Some(field) = value.get(key).filter(|field| !field.is_null()) else {
        return if optional {
            Ok(None)
        } else {
            Err(invalid(
                value,
                key,
                "string_type",
                "Input should be a valid string",
            ))
        };
    };
    let string = field
        .as_str()
        .ok_or_else(|| invalid(value, key, "string_type", "Input should be a valid string"))?;
    let count = string.chars().count();
    if count < min {
        return Err(invalid(
            value,
            key,
            "string_too_short",
            &format!(
                "String should have at least {min} character{}",
                if min == 1 { "" } else { "s" }
            ),
        ));
    }
    if count > max {
        return Err(invalid(
            value,
            key,
            "string_too_long",
            &format!("String should have at most {max} characters"),
        ));
    }
    Ok(Some(string))
}
pub fn required<'a>(value: &'a Value, key: &str, min: usize, max: usize) -> Result<&'a str> {
    Ok(string(value, key, min, max, false)?.unwrap())
}
pub fn integer(value: &Value, key: &str) -> Result<i64> {
    let field = &value[key];
    let parsed = field
        .as_i64()
        .or_else(|| field.as_bool().map(i64::from))
        .or_else(|| {
            field
                .as_str()
                .and_then(|value| value.trim().parse::<i64>().ok())
        })
        .or_else(|| {
            field
                .as_f64()
                .filter(|value| {
                    value.is_finite()
                        && value.fract() == 0.0
                        && *value >= i64::MIN as f64
                        && *value < i64::MAX as f64
                })
                .map(|value| value as i64)
        });
    parsed.ok_or_else(|| {
        invalid(
            value,
            key,
            "int_parsing",
            "Input should be a valid integer, unable to parse string as an integer",
        )
    })
}
pub fn boolean(value: &Value, key: &str, default: bool) -> Result<bool> {
    let Some(field) = value.get(key) else {
        return Ok(default);
    };
    field
        .as_bool()
        .or_else(|| {
            field.as_i64().and_then(|value| match value {
                0 => Some(false),
                1 => Some(true),
                _ => None,
            })
        })
        .or_else(|| {
            field
                .as_str()
                .and_then(|value| match value.to_ascii_lowercase().as_str() {
                    "1" | "true" | "t" | "on" | "y" | "yes" => Some(true),
                    "0" | "false" | "f" | "off" | "n" | "no" => Some(false),
                    _ => None,
                })
        })
        .ok_or_else(|| {
            invalid(
                value,
                key,
                "bool_parsing",
                "Input should be a valid boolean, unable to interpret input",
            )
        })
}
