use crate::backend::{db, unicode, BackendError, Result};
use rusqlite::{Connection, Params};
use serde_json::{Number, Value};

pub(super) fn fail(code: &str, message: impl Into<String>) -> BackendError {
    BackendError::invalid(code, message)
}
pub(super) fn trim(value: &str) -> &str {
    value.trim_matches(unicode::python_space)
}
pub(super) fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(value) => *value,
        Value::Number(value) => value.as_f64().is_none_or(|value| value != 0.0),
        Value::String(value) => !value.is_empty(),
        Value::Array(value) => !value.is_empty(),
        Value::Object(value) => !value.is_empty(),
    }
}
pub(super) fn python_string(value: &Value) -> String {
    crate::backend::json::python_string(value)
}

pub(super) fn text(value: &Value, label: &str, maximum: usize, code: &str) -> Result<String> {
    let value = value
        .as_str()
        .map(trim)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| fail(code, format!("{label} must be a non-empty string")))?;
    if value.chars().count() > maximum {
        return Err(fail(code, format!("{label} exceeds {maximum} characters")));
    }
    Ok(value.into())
}
pub(super) fn optional_text(
    value: &Value,
    label: &str,
    maximum: usize,
    code: &str,
) -> Result<Option<String>> {
    if value.is_null() {
        Ok(None)
    } else {
        text(value, label, maximum, code).map(Some)
    }
}
pub(super) fn matches(pattern: &str, value: &str) -> bool {
    // Policy patterns are static, bounded and owned by the versioned contract.
    regex::Regex::new(pattern)
        .expect("static Atlassian policy pattern")
        .is_match(value)
}
pub(super) fn exact_keys(
    value: &Value,
    required: &[&str],
    optional: &[&str],
    label: &str,
    code: &str,
) -> Result<()> {
    let object = value
        .as_object()
        .ok_or_else(|| fail(code, format!("{label} must be an object")))?;
    let mut missing: Vec<_> = required
        .iter()
        .filter(|key| !object.contains_key(**key))
        .copied()
        .collect();
    missing.sort();
    if !missing.is_empty() {
        return Err(fail(
            code,
            format!("{label} is missing: {}", missing.join(", ")),
        ));
    }
    if object
        .keys()
        .any(|key| !required.contains(&key.as_str()) && !optional.contains(&key.as_str()))
    {
        return Err(fail(code, format!("{label} has unsupported fields")));
    }
    Ok(())
}
pub(super) fn is_integer(value: &Value) -> bool {
    value.as_number().is_some_and(|number| {
        let raw = number.to_string();
        let digits = raw.strip_prefix('-').unwrap_or(&raw);
        !digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit())
    })
}
pub(super) fn bounded_integer(
    value: &Value,
    label: &str,
    minimum: i64,
    maximum: i64,
    default: i64,
    code: &str,
) -> Result<i64> {
    if value.is_null() {
        return Ok(default);
    }
    if !is_integer(value) {
        return Err(fail(code, format!("{label} must be an integer")));
    }
    value
        .as_i64()
        .filter(|value| *value >= minimum && *value <= maximum)
        .ok_or_else(|| {
            fail(
                code,
                format!("{label} must be between {minimum} and {maximum}"),
            )
        })
}
pub(super) fn canonical(value: &Value) -> Result<String> {
    crate::backend::json::canonical(value)
}
pub(super) fn decode_json(text: &str) -> Result<Value> {
    crate::backend::json::decode(text)
}
pub(super) fn json_size(value: &Value, label: &str, maximum: usize, code: &str) -> Result<String> {
    let encoded =
        canonical(value).map_err(|_| fail(code, format!("{label} must be JSON serializable")))?;
    if encoded.len() > maximum {
        return Err(fail(code, format!("{label} exceeds {maximum} bytes")));
    }
    Ok(encoded)
}
pub(super) fn now() -> String {
    crate::backend::clock::isoformat(chrono::Utc::now())
}
pub(super) fn access_now() -> String {
    now().replace("+00:00", "Z")
}
pub(super) fn required_row<P: Params>(
    connection: &Connection,
    sql: &str,
    params: P,
    code: &str,
    message: &str,
) -> Result<Value> {
    db::row(connection, sql, params)?.ok_or_else(|| fail(code, message))
}
pub(super) fn id(value: &Value) -> Result<i64> {
    value.as_i64().ok_or_else(|| {
        fail(
            "invalid-input",
            "Local identity is outside the SQLite integer range",
        )
    })
}
pub(super) fn python_integer(value: &Value, label: &str, reject_bool: bool) -> Result<Number> {
    let invalid = || fail("invalid-input", format!("{label} must be an integer"));
    match value {
        Value::Bool(value) if !reject_bool => Ok(Number::from(i64::from(*value))),
        Value::String(value) => integer_text(value).ok_or_else(invalid),
        Value::Number(number) if is_integer(value) => {
            let value = num_bigint::BigInt::parse_bytes(number.to_string().as_bytes(), 10)
                .ok_or_else(invalid)?;
            Ok(Number::from_string_unchecked(value.to_string()))
        }
        Value::Number(number) => {
            let value = number.as_f64().ok_or_else(invalid)?;
            if value.is_nan() {
                return Err(invalid());
            }
            if value.is_infinite() {
                return Err(BackendError::new(
                    500,
                    "integer-overflow",
                    "cannot convert float infinity to integer",
                ));
            }
            integer_text(&format!("{:.0}", value.trunc())).ok_or_else(invalid)
        }
        _ => Err(invalid()),
    }
}
pub(super) fn sql_integer(number: &Number) -> Result<i64> {
    number.as_i64().ok_or_else(|| {
        BackendError::new(
            500,
            "database",
            "Python int too large to convert to SQLite INTEGER",
        )
    })
}
pub(super) fn atomic<T>(
    connection: &Connection,
    name: &'static str,
    operation: impl FnOnce() -> Result<T>,
) -> Result<T> {
    struct Guard<'a> {
        connection: &'a Connection,
        name: &'static str,
        active: bool,
    }
    impl Drop for Guard<'_> {
        fn drop(&mut self) {
            if self.active {
                let _ = self
                    .connection
                    .execute_batch(&format!("ROLLBACK TO {}; RELEASE {}", self.name, self.name));
            }
        }
    }
    connection.execute_batch(&format!("SAVEPOINT {name}"))?;
    let mut guard = Guard {
        connection,
        name,
        active: true,
    };
    let value = operation()?;
    connection.execute_batch(&format!("RELEASE {name}"))?;
    guard.active = false;
    Ok(value)
}

// int(text) admits Unicode Decimal_Number characters, signs and underscores.
// Frozen UCD14 decimal runs contain complete groups of ten (including the
// contiguous mathematical alphabets), so no newer Unicode digit table is used.
pub(super) fn integer_text(text: &str) -> Option<Number> {
    use unicode_general_category::{get_general_category, GeneralCategory};
    let text = trim(text);
    let (negative, body) = if let Some(v) = text.strip_prefix('-') {
        (true, v)
    } else {
        (false, text.strip_prefix('+').unwrap_or(text))
    };
    let mut digits = String::new();
    let mut previous_digit = false;
    for ch in body.chars() {
        if ch == '_' {
            if !previous_digit {
                return None;
            }
            previous_digit = false;
            continue;
        }
        if get_general_category(ch) != GeneralCategory::DecimalNumber {
            return None;
        }
        let point = ch as u32;
        let mut first = point;
        while let Some(previous) = first.checked_sub(1).and_then(char::from_u32) {
            if get_general_category(previous) != GeneralCategory::DecimalNumber {
                break;
            }
            first -= 1;
        }
        digits.push(char::from(b'0' + ((point - first) % 10) as u8));
        previous_digit = true;
    }
    if !previous_digit || digits.len() > 4300 {
        return None;
    }
    let digits = digits.trim_start_matches('0');
    let digits = if digits.is_empty() { "0" } else { digits };
    Some(Number::from_string_unchecked(format!(
        "{}{digits}",
        if negative && digits != "0" { "-" } else { "" }
    )))
}
