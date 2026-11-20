//! Frozen FastAPI query/path admission. This layer does not read a body, apply
//! defaults, or change raw URI/string data. Coercions publish only after success.
use crate::transport::RequestContext;
use localbrain_core::backend::{BackendError, Result};
use regex::Regex;
use serde_json::{json, Value};
use std::{cmp::Ordering, collections::BTreeMap, sync::LazyLock};

const MODE_PATTERN: &str = "^(auto|keyword|ai)$";
static MODE: LazyLock<Regex> = LazyLock::new(|| Regex::new(MODE_PATTERN).unwrap());

fn implementation() -> BackendError {
    BackendError::new(
        500,
        "parameter_schema",
        "Unsupported frozen HTTP parameter schema",
    )
}
fn placeholder(segment: &str) -> Option<&str> {
    segment.strip_prefix('{')?.strip_suffix('}').map(|name| {
        name.strip_prefix('*')
            .unwrap_or(name)
            .split(':')
            .next()
            .unwrap()
    })
}
fn same_shape(left: &str, right: &str) -> bool {
    let mut left = left.split('/');
    let mut right = right.split('/');
    loop {
        match (left.next(), right.next()) {
            (None, None) => return true,
            (Some(a), Some(b))
                if a == b || placeholder(a).is_some() && placeholder(b).is_some() => {}
            _ => return false,
        }
    }
}

pub fn validate(
    pattern: &str,
    method: &str,
    context: &mut RequestContext,
    params: &mut BTreeMap<String, String>,
) -> Result<()> {
    let paths = crate::api_contract::full()["paths"]
        .as_object()
        .ok_or_else(implementation)?;
    let method = method.to_ascii_lowercase();
    if let Some(path) = paths.get(pattern) {
        return match path.get(&method) {
            Some(operation) => validate_operation(pattern, pattern, operation, context, params),
            None => Ok(()),
        };
    }
    let mut matched = None;
    for (public_pattern, path) in paths {
        if same_shape(pattern, public_pattern) {
            if let Some(operation) = path.get(&method) {
                if matched.is_some() {
                    return Err(implementation());
                }
                matched = Some((public_pattern, operation));
            }
        }
    }
    match matched {
        Some((public, operation)) => {
            validate_operation(pattern, public, operation, context, params)
        }
        None => Ok(()),
    }
}

fn validate_operation(
    native: &str,
    public: &str,
    operation: &Value,
    context: &mut RequestContext,
    params: &mut BTreeMap<String, String>,
) -> Result<()> {
    let Some(parameters) = operation.get("parameters") else {
        return Ok(());
    };
    let parameters = parameters.as_array().ok_or_else(implementation)?;
    let aliases = public
        .split('/')
        .zip(native.split('/'))
        .filter_map(|(old, new)| Some((placeholder(old)?, placeholder(new)?)))
        .collect::<Vec<_>>();
    let mut errors = Vec::new();
    let mut changes = Vec::new();
    for parameter in parameters {
        let location = parameter["in"].as_str().ok_or_else(implementation)?;
        if matches!(location, "header" | "cookie") {
            continue;
        }
        if !matches!(location, "path" | "query") {
            return Err(implementation());
        }
        let name = parameter["name"].as_str().ok_or_else(implementation)?;
        // Validate metadata even for an absent optional field; an unsupported
        // contract must never silently become a successful request.
        let schema = Schema::read(&parameter["schema"])?;
        let required = match parameter.get("required") {
            Some(value) => value.as_bool().ok_or_else(implementation)?,
            None => false,
        };
        let key = if location == "path" {
            aliases
                .iter()
                .find(|(old, _)| *old == name)
                .map(|(_, new)| *new)
                .ok_or_else(implementation)?
        } else {
            name
        };
        let raw = if location == "path" {
            params.get(key)
        } else {
            context.query.get(key)
        };
        let Some(raw) = raw else {
            if required {
                errors.push(error(
                    location,
                    name,
                    None,
                    "missing",
                    "Field required".into(),
                    None,
                ));
            }
            continue;
        };
        match schema.check(raw) {
            Ok(Some(value)) if value != *raw => {
                changes.push((location == "path", key.to_owned(), value))
            }
            Ok(_) => {}
            Err(failure) => errors.push(error(
                location,
                name,
                Some(raw),
                failure.kind,
                failure.message,
                failure.context,
            )),
        }
    }
    if !errors.is_empty() {
        return Err(
            BackendError::new(422, "validation", "Request validation failed")
                .with_details(Value::Array(errors)),
        );
    }
    for (path, key, value) in changes {
        if path {
            params.insert(key, value);
        } else {
            context.query.insert(key, value);
        }
    }
    Ok(())
}

fn error(
    location: &str,
    name: &str,
    input: Option<&str>,
    kind: &str,
    message: String,
    context: Option<Value>,
) -> Value {
    let mut value = json!({"type":kind,"loc":[location,name],"msg":message,"input":input});
    if let Some(context) = context {
        value["ctx"] = context;
    }
    value
}
struct Failure {
    kind: &'static str,
    message: String,
    context: Option<Value>,
}
fn failure(kind: &'static str, message: impl Into<String>, context: Option<Value>) -> Failure {
    Failure {
        kind,
        message: message.into(),
        context,
    }
}

enum Schema<'a> {
    Integer {
        minimum: Option<&'a Value>,
        maximum: Option<&'a Value>,
    },
    Boolean,
    String {
        minimum: Option<usize>,
        maximum: Option<usize>,
        pattern: Option<&'a str>,
    },
}
impl<'a> Schema<'a> {
    fn read(value: &'a Value) -> Result<Self> {
        let object = value.as_object().ok_or_else(implementation)?;
        if let Some(branches) = object.get("anyOf") {
            if object
                .keys()
                .any(|key| !["anyOf", "title", "default"].contains(&key.as_str()))
            {
                return Err(implementation());
            }
            let branches = branches
                .as_array()
                .filter(|values| values.len() == 2)
                .ok_or_else(implementation)?;
            let mut typed = None;
            let mut nulls = 0;
            for branch in branches {
                if branch.as_object().is_some_and(|value| {
                    value.len() == 1 && value.get("type").and_then(Value::as_str) == Some("null")
                }) {
                    nulls += 1;
                } else {
                    typed = Some(branch);
                }
            }
            if nulls != 1 {
                return Err(implementation());
            }
            return Self::read(typed.ok_or_else(implementation)?);
        }
        let kind = object
            .get("type")
            .and_then(Value::as_str)
            .ok_or_else(implementation)?;
        let allowed: &[&str] = match kind {
            "integer" => &["type", "title", "default", "minimum", "maximum"],
            "boolean" => &["type", "title", "default"],
            "string" => &[
                "type",
                "title",
                "default",
                "minLength",
                "maxLength",
                "pattern",
            ],
            _ => return Err(implementation()),
        };
        if object.keys().any(|key| !allowed.contains(&key.as_str())) {
            return Err(implementation());
        }
        Ok(match kind {
            "integer" => {
                for key in ["minimum", "maximum"] {
                    if let Some(value) = object.get(key) {
                        if !value.is_number()
                            || !matches!(ascii_integer(&value.to_string()), Integer::Value(_))
                        {
                            return Err(implementation());
                        }
                    }
                }
                Self::Integer {
                    minimum: object.get("minimum"),
                    maximum: object.get("maximum"),
                }
            }
            "boolean" => Self::Boolean,
            _ => {
                let length = |key| {
                    object
                        .get(key)
                        .map(|value| {
                            value
                                .as_u64()
                                .and_then(|value| usize::try_from(value).ok())
                                .ok_or_else(implementation)
                        })
                        .transpose()
                };
                let pattern = object
                    .get("pattern")
                    .map(|value| {
                        value
                            .as_str()
                            .filter(|value| *value == MODE_PATTERN)
                            .ok_or_else(implementation)
                    })
                    .transpose()?;
                Self::String {
                    minimum: length("minLength")?,
                    maximum: length("maxLength")?,
                    pattern,
                }
            }
        })
    }
    fn check(&self, raw: &str) -> std::result::Result<Option<String>, Failure> {
        match self {
            Self::Integer { minimum, maximum } => {
                let value = integer(raw).map_err(|size| {
                    if size {
                        failure(
                            "int_parsing_size",
                            "Unable to parse input string as an integer, exceeded maximum size",
                            None,
                        )
                    } else {
                        failure(
                            "int_parsing",
                            "Input should be a valid integer, unable to parse string as an integer",
                            None,
                        )
                    }
                })?;
                if let Some(bound) = minimum {
                    if compare(&value, &bound.to_string()) == Ordering::Less {
                        return Err(failure(
                            "greater_than_equal",
                            format!("Input should be greater than or equal to {bound}"),
                            Some(json!({"ge":bound})),
                        ));
                    }
                }
                if let Some(bound) = maximum {
                    if compare(&value, &bound.to_string()) == Ordering::Greater {
                        return Err(failure(
                            "less_than_equal",
                            format!("Input should be less than or equal to {bound}"),
                            Some(json!({"le":bound})),
                        ));
                    }
                }
                Ok(Some(value))
            }
            Self::Boolean => {
                if ["1", "t", "y", "on", "yes", "true"]
                    .iter()
                    .any(|value| raw.eq_ignore_ascii_case(value))
                {
                    Ok(Some("1".into()))
                } else if ["0", "f", "n", "no", "off", "false"]
                    .iter()
                    .any(|value| raw.eq_ignore_ascii_case(value))
                {
                    Ok(Some("0".into()))
                } else {
                    Err(failure(
                        "bool_parsing",
                        "Input should be a valid boolean, unable to interpret input",
                        None,
                    ))
                }
            }
            Self::String {
                minimum,
                maximum,
                pattern,
            } => {
                let length = if minimum.is_some() || maximum.is_some() {
                    raw.chars().count()
                } else {
                    0
                };
                if let Some(bound) = minimum {
                    if length < *bound {
                        return Err(failure(
                            "string_too_short",
                            format!(
                                "String should have at least {bound} character{}",
                                if *bound == 1 { "" } else { "s" }
                            ),
                            Some(json!({"min_length":bound})),
                        ));
                    }
                }
                if let Some(bound) = maximum {
                    if length > *bound {
                        return Err(failure(
                            "string_too_long",
                            format!(
                                "String should have at most {bound} character{}",
                                if *bound == 1 { "" } else { "s" }
                            ),
                            Some(json!({"max_length":bound})),
                        ));
                    }
                }
                if let Some(pattern) = pattern {
                    if !MODE.is_match(raw) {
                        return Err(failure(
                            "string_pattern_mismatch",
                            format!("String should match pattern '{pattern}'"),
                            Some(json!({"pattern":pattern})),
                        ));
                    }
                }
                Ok(None)
            }
        }
    }
}

enum Integer {
    Value(String),
    Invalid,
    Size,
}
// Pydantic's first integer attempt has JSON integer syntax and a 4300-byte
// numeric prefix budget (including a minus). Cleanup retries map size failures
// to int_parsing, preserving the frozen distinction instead of parsing as f64.
fn ascii_integer(raw: &str) -> Integer {
    let digits = raw.strip_prefix('-').unwrap_or(raw);
    if digits.is_empty() || !digits.as_bytes()[0].is_ascii_digit() {
        return Integer::Invalid;
    }
    if digits.starts_with('0') && digits.len() > 1 {
        return Integer::Invalid;
    }
    for (index, byte) in raw
        .bytes()
        .enumerate()
        .skip(usize::from(raw.starts_with('-')))
    {
        if !byte.is_ascii_digit() {
            return Integer::Invalid;
        }
        if index >= 4300 {
            return Integer::Size;
        }
    }
    Integer::Value(if raw == "-0" { "0".into() } else { raw.into() })
}
fn integer(raw: &str) -> std::result::Result<String, bool> {
    match ascii_integer(raw) {
        Integer::Value(value) => return Ok(value),
        Integer::Size => return Err(true),
        _ => {}
    }
    let mut text = raw.trim();
    if let Some(value) = text.strip_prefix('+') {
        if value.starts_with('-') {
            return Err(false);
        }
        text = value;
    }
    let negative = text.starts_with('-');
    if negative {
        text = &text[1..];
        if text.starts_with(['-', '+']) {
            return Err(false);
        }
    }
    // Match the frozen cleanup's leading-zero pass, including underscores in
    // that prefix and its treatment of an embedded minus after leading zeros.
    let bytes = text.as_bytes();
    match bytes.first() {
        Some(b'0') => {
            let mut start = bytes.len() - 1;
            for (index, byte) in bytes.iter().enumerate().skip(1) {
                match byte {
                    b'0' | b'_' => {}
                    b'1'..=b'9' | b'-' => {
                        start = index;
                        break;
                    }
                    b'.' => {
                        start = index - 1;
                        break;
                    }
                    _ => return Err(false),
                }
            }
            text = &text[start..];
        }
        Some(b'1'..=b'9') | Some(b'-') => {}
        _ => return Err(false),
    }
    if let Some((whole, fraction)) = text.split_once('.') {
        if !fraction.is_empty() && fraction.bytes().all(|byte| byte == b'0') {
            text = whole;
        }
    }
    let stripped;
    if text.contains('_') && !text.starts_with('_') && !text.ends_with('_') && !text.contains("__")
    {
        stripped = text.replace('_', "");
        text = &stripped;
    }
    let signed = if negative {
        format!("-{text}")
    } else {
        text.to_owned()
    };
    match ascii_integer(&signed) {
        Integer::Value(value) => Ok(value),
        _ => Err(false),
    }
}
fn compare(left: &str, right: &str) -> Ordering {
    let negative = left.starts_with('-');
    match (negative, right.starts_with('-')) {
        (true, false) => Ordering::Less,
        (false, true) => Ordering::Greater,
        _ => {
            let left = left.trim_start_matches('-');
            let right = right.trim_start_matches('-');
            let order = left.len().cmp(&right.len()).then_with(|| left.cmp(right));
            if negative {
                order.reverse()
            } else {
                order
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unsupported_schema_is_an_implementation_failure_even_when_optional_is_absent() {
        let mut headers = axum::http::HeaderMap::new();
        headers.insert("host", "127.0.0.1".parse().unwrap());
        let mut context = RequestContext::new(
            axum::http::Method::GET,
            headers,
            "/synthetic".parse().unwrap(),
        )
        .unwrap();
        context.query.insert("valid".into(), "+0002.0".into());
        let before = context.query.clone();
        for schema in [
            json!({"type":"array","items":{"type":"integer"}}),
            json!({"type":"integer","multipleOf":2}),
            json!({"anyOf":[{"type":"string"},{"type":"integer"}]}),
            json!({"type":"string","pattern":"unsupported"}),
        ] {
            let operation = json!({"parameters":[{"in":"query","name":"valid","required":false,"schema":{"type":"integer"}},{"in":"query","name":"optional","required":false,"schema":schema}]});
            let error = validate_operation(
                "/synthetic",
                "/synthetic",
                &operation,
                &mut context,
                &mut BTreeMap::new(),
            )
            .unwrap_err();
            assert_eq!(error.status, 500);
            assert_eq!(error.code, "parameter_schema");
            assert_eq!(context.query, before);
        }
    }
}
