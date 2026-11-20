//! Python str/repr over native values, with optional scoped surrogate units.
use super::{SourceCharacter, SourceCharacters};
use serde_json::Value;

pub(super) fn string(value: &Value, marker: Option<char>) -> String {
    match value {
        Value::String(value) => value.clone(),
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::Number(value) => {
            let text = value.to_string();
            if text == "-0" {
                return "0".into();
            }
            if text
                .trim_start_matches('-')
                .bytes()
                .all(|b| b.is_ascii_digit())
            {
                return text;
            }
            let value = match text.as_str() {
                "NaN" => f64::NAN,
                "Infinity" => f64::INFINITY,
                "-Infinity" => f64::NEG_INFINITY,
                _ => text.parse::<f64>().unwrap_or(f64::NAN),
            };
            if value.is_nan() {
                return "nan".into();
            }
            if value.is_infinite() {
                return if value.is_sign_negative() {
                    "-inf"
                } else {
                    "inf"
                }
                .into();
            }
            let text = format!("{value:?}");
            if let Some((mantissa, exponent)) = text.split_once('e') {
                let exponent: i32 = exponent.parse().unwrap();
                format!("{mantissa}e{exponent:+03}")
            } else {
                text
            }
        }
        _ => container_string(value, marker),
    }
}
fn container_string(value: &Value, marker: Option<char>) -> String {
    if let Some(value) = value.as_str() {
        return value.into();
    }
    enum Part<'a> {
        Value(&'a Value),
        Key(&'a str),
        Literal(&'static str),
    }
    fn quoted(value: &str, marker: Option<char>) -> String {
        let quote = if value.contains('\'') && !value.contains('"') {
            '"'
        } else {
            '\''
        };
        let mut result = String::new();
        result.push(quote);
        for point in SourceCharacters::new(value, marker) {
            let ch = match point {
                SourceCharacter::Scalar(ch) => ch,
                SourceCharacter::Surrogate(point) => {
                    result.push_str(&format!("\\u{point:04x}"));
                    continue;
                }
            };
            match ch {
                '\\' => result.push_str("\\\\"),
                '\t' => result.push_str("\\t"),
                '\n' => result.push_str("\\n"),
                '\r' => result.push_str("\\r"),
                _ if ch == quote => {
                    result.push('\\');
                    result.push(ch);
                }
                _ if !crate::backend::unicode::python_printable(ch) => {
                    let point = ch as u32;
                    result.push_str(&if point <= 255 {
                        format!("\\x{point:02x}")
                    } else if point <= 65535 {
                        format!("\\u{point:04x}")
                    } else {
                        format!("\\U{point:08x}")
                    });
                }
                _ => result.push(ch),
            }
        }
        result.push(quote);
        result
    }
    let mut result = String::new();
    let mut pending = vec![Part::Value(value)];
    while let Some(part) = pending.pop() {
        match part {
            Part::Literal(value) => result.push_str(value),
            Part::Key(value) => result.push_str(&quoted(value, marker)),
            Part::Value(Value::String(value)) => result.push_str(&quoted(value, marker)),
            Part::Value(Value::Array(values)) => {
                result.push('[');
                pending.push(Part::Literal("]"));
                for (index, value) in values.iter().enumerate().rev() {
                    if index + 1 < values.len() {
                        pending.push(Part::Literal(", "));
                    }
                    pending.push(Part::Value(value));
                }
            }
            Part::Value(Value::Object(values)) => {
                result.push('{');
                pending.push(Part::Literal("}"));
                for (index, (key, value)) in values.iter().enumerate().rev() {
                    if index + 1 < values.len() {
                        pending.push(Part::Literal(", "));
                    }
                    pending.push(Part::Value(value));
                    pending.push(Part::Literal(": "));
                    pending.push(Part::Key(key));
                }
            }
            Part::Value(value) => result.push_str(&string(value, marker)),
        }
    }
    result
}
