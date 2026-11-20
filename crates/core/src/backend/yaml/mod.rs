//! Safe, ordered YAML with Python SafeLoader scalar resolution (YAML1.1).
//! Parsing uses public native scalar-style/tag/alias events, never string rewriting.
use crate::backend::{BackendError, Result};
use base64::{engine::general_purpose::STANDARD, Engine};
use chrono::{NaiveDate, NaiveTime};
use regex::Regex;
use serde_json::{json, Value};
use std::{collections::HashMap, sync::LazyLock};
use yaml_rust2::{
    parser::{Event, Parser, Tag},
    scanner::TScalarStyle,
};

#[derive(Debug, Clone, PartialEq)]
pub enum SafeYaml {
    Null,
    Boolean(bool),
    Integer(String),
    Real(f64),
    String(String),
    Date(String),
    Timestamp(String),
    Sequence(Vec<SafeYaml>),
    Mapping(Vec<(SafeYaml, SafeYaml)>),
    Binary(Vec<u8>),
    Set(Vec<SafeYaml>),
    Pairs(Vec<(SafeYaml, SafeYaml)>),
    #[doc(hidden)]
    Merge,
    #[doc(hidden)]
    ValueMarker,
    /// A back-reference to a currently constructed collection. This preserves
    /// recursive YAML graphs for readers that only select unrelated fields.
    RecursiveAlias(usize),
}
impl SafeYaml {
    pub fn as_str(&self) -> Option<&str> {
        if let Self::String(value) = self {
            Some(value)
        } else {
            None
        }
    }
    pub fn as_mapping(&self) -> Option<&[(SafeYaml, SafeYaml)]> {
        if let Self::Mapping(value) = self {
            Some(value)
        } else {
            None
        }
    }
    pub fn as_sequence(&self) -> Option<&[SafeYaml]> {
        if let Self::Sequence(value) = self {
            Some(value)
        } else {
            None
        }
    }
    pub fn get(&self, key: &str) -> Option<&Self> {
        self.as_mapping()?
            .iter()
            .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
    }
    pub fn has_recursive_alias(&self) -> bool {
        match self {
            Self::RecursiveAlias(_) => true,
            Self::Sequence(values) | Self::Set(values) => {
                values.iter().any(Self::has_recursive_alias)
            }
            Self::Mapping(values) | Self::Pairs(values) => values
                .iter()
                .any(|(key, value)| key.has_recursive_alias() || value.has_recursive_alias()),
            _ => false,
        }
    }
    /// Markdown's property display: lowercase null/bool, recursive lists/maps,
    /// ISO dates and literal strings, matching its former Python helper.
    pub fn property_value(&self) -> String {
        match self {
            Self::Null => "null".into(),
            Self::Boolean(value) => value.to_string(),
            Self::Integer(value)
            | Self::String(value)
            | Self::Date(value)
            | Self::Timestamp(value) => value.clone(),
            Self::Real(value) => python_float(*value),
            Self::Sequence(values) => format!(
                "[{}]",
                values
                    .iter()
                    .map(Self::property_value)
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Self::Mapping(values) => format!(
                "{{{}}}",
                values
                    .iter()
                    .map(|(key, value)| format!(
                        "{}: {}",
                        key.python_string(),
                        value.property_value()
                    ))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Self::Binary(value) => format!(
                "b'{}'",
                value
                    .iter()
                    .map(
                        |byte| if byte.is_ascii_graphic() && *byte != b'\'' && *byte != b'\\' {
                            (*byte as char).to_string()
                        } else {
                            format!("\\x{byte:02x}")
                        }
                    )
                    .collect::<String>()
            ),
            Self::Set(values) => {
                if values.is_empty() {
                    "set()".into()
                } else {
                    format!(
                        "{{{}}}",
                        values
                            .iter()
                            .map(Self::python_repr)
                            .collect::<Vec<_>>()
                            .join(", ")
                    )
                }
            }
            Self::Pairs(values) => format!(
                "[{}]",
                values
                    .iter()
                    .map(|(key, value)| format!("({}, {})", key.python_repr(), value.python_repr()))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Self::Merge => "<<".into(),
            Self::ValueMarker => "=".into(),
            Self::RecursiveAlias(_) => "...".into(),
        }
    }
    /// Python str(value), for skill metadata consumers. Dates retain their type
    /// here even though JSON cannot represent a Python date object.
    pub fn python_string(&self) -> String {
        match self {
            Self::Null => "None".into(),
            Self::Boolean(value) => if *value { "True" } else { "False" }.into(),
            Self::Sequence(values) => format!(
                "[{}]",
                values
                    .iter()
                    .map(Self::python_repr)
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Self::Mapping(values) => format!(
                "{{{}}}",
                values
                    .iter()
                    .map(|(key, value)| format!("{}: {}", key.python_repr(), value.python_repr()))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            Self::Timestamp(value) => value.replacen('T', " ", 1),
            value => value.property_value(),
        }
    }
    fn python_repr(&self) -> String {
        match self {
            Self::String(value) => format!(
                "'{}'",
                value
                    .replace('\\', "\\\\")
                    .replace('\'', "\\'")
                    .replace('\n', "\\n")
                    .replace('\r', "\\r")
                    .replace('\t', "\\t")
            ),
            value => value.python_string(),
        }
    }
    /// JSON projection for consumers that explicitly require string-key objects.
    pub fn to_json(&self) -> Result<Value> {
        Ok(match self {
            Self::Null => Value::Null,
            Self::Boolean(value) => json!(value),
            Self::String(value) | Self::Date(value) | Self::Timestamp(value) => json!(value),
            Self::Integer(value) => {
                if let Ok(value) = value.parse::<i64>() {
                    json!(value)
                } else if let Ok(value) = value.parse::<u64>() {
                    json!(value)
                } else {
                    return Err(invalid());
                }
            }
            Self::Real(value) => serde_json::Number::from_f64(*value)
                .map(Value::Number)
                .ok_or_else(invalid)?,
            Self::Sequence(values) => {
                Value::Array(values.iter().map(Self::to_json).collect::<Result<_>>()?)
            }
            Self::Mapping(values) => {
                let mut result = serde_json::Map::new();
                for (key, value) in values {
                    result.insert(key.as_str().ok_or_else(invalid)?.into(), value.to_json()?);
                }
                Value::Object(result)
            }
            _ => return Err(invalid()),
        })
    }
}
fn invalid() -> BackendError {
    BackendError::invalid("yaml", "YAML 구조, 자료형과 안전한 태그를 확인해 주세요.")
}
fn python_float(value: f64) -> String {
    if value.is_nan() {
        return "nan".into();
    }
    if value == f64::INFINITY {
        return "inf".into();
    }
    if value == f64::NEG_INFINITY {
        return "-inf".into();
    }
    let value = format!("{value:?}");
    if let Some((mantissa, exponent)) = value.split_once('e') {
        let exponent: i32 = exponent.parse().unwrap();
        format!(
            "{mantissa}e{}{:02}",
            if exponent >= 0 { "+" } else { "-" },
            exponent.unsigned_abs()
        )
    } else {
        value
    }
}

static BOOL: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?:yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)$")
        .unwrap()
});
static INTEGER: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?:[-+]?0b[0-1_]+|[-+]?0[0-7_]+|[-+]?(?:0|[1-9][0-9_]*)|[-+]?0x[0-9a-fA-F_]+|[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$").unwrap()
});
static REAL: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?:[-+]?[0-9][0-9_]*\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?|[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$").unwrap()
});
static DATE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})$").unwrap());
static DATE_CONSTRUCTOR: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})$").unwrap());
static TIMESTAMP: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})(?:[Tt]|[ \t]+)([0-9]{1,2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]*))?(?:[ \t]*(Z|([-+])([0-9]{1,2})(?::([0-9]{2}))?))?$").unwrap()
});

fn tag_name(tag: Option<&Tag>) -> Option<String> {
    tag.map(|tag| format!("{}{}", tag.handle, tag.suffix))
}
fn scalar(value: String, style: TScalarStyle, tag: Option<Tag>) -> Result<SafeYaml> {
    let explicit = tag_name(tag.as_ref()).filter(|tag| tag != "!");
    let kind = if let Some(tag) = explicit.as_deref() {
        tag.strip_prefix("tag:yaml.org,2002:").ok_or_else(invalid)?
    } else if style != TScalarStyle::Plain {
        "str"
    } else if BOOL.is_match(&value) {
        "bool"
    } else if REAL.is_match(&value) {
        "float"
    } else if INTEGER.is_match(&value) {
        "int"
    } else if matches!(value.as_str(), "" | "~" | "null" | "Null" | "NULL") {
        "null"
    } else if value == "<<" {
        "merge"
    } else if value == "=" {
        "value"
    } else if DATE.is_match(&value) || TIMESTAMP.is_match(&value) {
        "timestamp"
    } else {
        "str"
    };
    Ok(match kind {
        "str" => SafeYaml::String(value),
        "value" => SafeYaml::ValueMarker,
        "merge" => SafeYaml::Merge,
        "null" => SafeYaml::Null,
        "bool" => SafeYaml::Boolean(match value.to_ascii_lowercase().as_str() {
            "true" | "yes" | "on" => true,
            "false" | "no" | "off" => false,
            _ => return Err(invalid()),
        }),
        "int" => SafeYaml::Integer(parse_integer(&value)?),
        "float" => SafeYaml::Real(parse_real(&value)?),
        "timestamp" => parse_date(&value)?,
        "binary" => {
            if !value.is_ascii() {
                return Err(invalid());
            }
            let filtered: Vec<_> = value
                .bytes()
                .filter(|ch| ch.is_ascii_alphanumeric() || b"+/=".contains(ch))
                .collect();
            SafeYaml::Binary(STANDARD.decode(filtered).map_err(|_| invalid())?)
        }
        _ => return Err(invalid()),
    })
}
fn decimal_multiply_add(number: &str, base: u32, add: u32) -> String {
    let mut carry = add;
    let mut digits = Vec::new();
    for digit in number.bytes().rev() {
        let value = u32::from(digit - b'0') * base + carry;
        digits.push(b'0' + (value % 10) as u8);
        carry = value / 10;
    }
    while carry > 0 {
        digits.push(b'0' + (carry % 10) as u8);
        carry /= 10;
    }
    while digits.len() > 1 && digits.last() == Some(&b'0') {
        digits.pop();
    }
    digits.reverse();
    String::from_utf8(digits).unwrap()
}
fn parse_integer(value: &str) -> Result<String> {
    let value = value.replace('_', "");
    let negative = value.starts_with('-');
    let unsigned = value.trim_start_matches(['+', '-']);
    let decimal = if unsigned.contains(':') {
        let mut pieces = unsigned.split(':');
        let first = pieces.next().unwrap();
        let mut result = decimal_digits(first, 10)?;
        for piece in pieces {
            result = decimal_multiply_add(&result, 60, piece.parse().map_err(|_| invalid())?);
        }
        result
    } else if let Some(value) = unsigned.strip_prefix("0b") {
        decimal_digits(value, 2)?
    } else if let Some(value) = unsigned.strip_prefix("0x") {
        decimal_digits(value, 16)?
    } else if unsigned.starts_with('0') && unsigned.len() > 1 {
        decimal_digits(unsigned, 8)?
    } else {
        decimal_digits(unsigned, 10)?
    };
    Ok(if negative && decimal != "0" {
        format!("-{decimal}")
    } else {
        decimal
    })
}
fn decimal_digits(value: &str, base: u32) -> Result<String> {
    if value.is_empty() {
        return Err(invalid());
    }
    let mut number = "0".to_string();
    for digit in value.chars() {
        number = decimal_multiply_add(&number, base, digit.to_digit(base).ok_or_else(invalid)?);
    }
    Ok(number)
}
fn parse_real(value: &str) -> Result<f64> {
    let value = value.replace('_', "").to_ascii_lowercase();
    let negative = value.starts_with('-');
    let unsigned = value.trim_start_matches(['+', '-']);
    let result = if unsigned == ".inf" {
        f64::INFINITY
    } else if unsigned == ".nan" {
        f64::NAN
    } else if unsigned.contains(':') {
        let mut result = 0f64;
        for piece in unsigned.split(':') {
            result = result * 60.0 + piece.parse::<f64>().map_err(|_| invalid())?;
        }
        result
    } else {
        unsigned.parse::<f64>().map_err(|_| invalid())?
    };
    Ok(if negative { -result } else { result })
}
fn parse_date(value: &str) -> Result<SafeYaml> {
    if let Some(parts) = DATE_CONSTRUCTOR.captures(value) {
        let year = parts[1].parse::<i32>().map_err(|_| invalid())?;
        if year < 1 {
            return Err(invalid());
        }
        let date = NaiveDate::from_ymd_opt(
            year,
            parts[2].parse().map_err(|_| invalid())?,
            parts[3].parse().map_err(|_| invalid())?,
        )
        .ok_or_else(invalid)?;
        return Ok(SafeYaml::Date(date.to_string()));
    }
    let captures = TIMESTAMP.captures(value).ok_or_else(invalid)?;
    let number = |index| {
        captures.get(index).map_or(Ok(0), |value| {
            value.as_str().parse::<u32>().map_err(|_| invalid())
        })
    };
    let date =
        NaiveDate::from_ymd_opt(number(1)? as i32, number(2)?, number(3)?).ok_or_else(invalid)?;
    let time = NaiveTime::from_hms_opt(number(4)?, number(5)?, number(6)?).ok_or_else(invalid)?;
    let mut fraction = captures
        .get(7)
        .map_or("", |value| value.as_str())
        .chars()
        .take(6)
        .collect::<String>();
    while fraction.len() < 6 {
        fraction.push('0');
    }
    let fraction = if fraction == "000000" {
        String::new()
    } else {
        format!(".{fraction}")
    };
    let offset = if captures.get(8).is_none() {
        String::new()
    } else if captures.get(8).unwrap().as_str() == "Z" {
        "+00:00".into()
    } else {
        let minutes = number(10)? * 60 + number(11)?;
        if minutes >= 24 * 60 {
            return Err(invalid());
        }
        format!(
            "{}{:02}:{:02}",
            if minutes == 0 {
                "+"
            } else {
                captures.get(9).unwrap().as_str()
            },
            minutes / 60,
            minutes % 60
        )
    };
    Ok(SafeYaml::Timestamp(format!(
        "{date}T{}{fraction}{offset}",
        time.format("%H:%M:%S")
    )))
}

fn equivalent(a: &SafeYaml, b: &SafeYaml) -> bool {
    if a == b {
        return true;
    }
    match (a, b) {
        (SafeYaml::Boolean(a), SafeYaml::Integer(b))
        | (SafeYaml::Integer(b), SafeYaml::Boolean(a)) => b == if *a { "1" } else { "0" },
        (SafeYaml::Real(a), SafeYaml::Integer(b)) | (SafeYaml::Integer(b), SafeYaml::Real(a)) => {
            a.is_finite()
                && a.fract() == 0.0
                && *b
                    == if *a == 0.0 {
                        "0".into()
                    } else {
                        format!("{a:.0}")
                    }
        }
        (SafeYaml::Boolean(a), SafeYaml::Real(b)) | (SafeYaml::Real(b), SafeYaml::Boolean(a)) => {
            *b == if *a { 1.0 } else { 0.0 }
        }
        _ => false,
    }
}
fn mapping(entries: Vec<(SafeYaml, SafeYaml)>) -> Result<SafeYaml> {
    let mut merged = Vec::new();
    let mut explicit = Vec::new();
    for (mut key, value) in entries {
        if matches!(value, SafeYaml::Merge | SafeYaml::ValueMarker) {
            return Err(invalid());
        }
        if key == SafeYaml::ValueMarker {
            key = SafeYaml::String("=".into());
        }
        if key == SafeYaml::Merge {
            match value {
                SafeYaml::Mapping(values) => merged.extend(values),
                SafeYaml::Sequence(values) => {
                    for value in values.into_iter().rev() {
                        if let SafeYaml::Mapping(values) = value {
                            merged.extend(values);
                        } else {
                            return Err(invalid());
                        }
                    }
                }
                _ => return Err(invalid()),
            }
        } else {
            if matches!(
                key,
                SafeYaml::Sequence(_)
                    | SafeYaml::Mapping(_)
                    | SafeYaml::Set(_)
                    | SafeYaml::Pairs(_)
                    | SafeYaml::RecursiveAlias(_)
            ) {
                return Err(invalid());
            }
            explicit.push((key, value));
        }
    }
    merged.extend(explicit);
    let mut result: Vec<(SafeYaml, SafeYaml)> = Vec::new();
    for (key, value) in merged {
        if let Some((_, existing)) = result
            .iter_mut()
            .find(|(existing, _)| equivalent(existing, &key))
        {
            *existing = value;
        } else {
            result.push((key, value));
        }
    }
    Ok(SafeYaml::Mapping(result))
}
fn node(
    events: &[(Event, yaml_rust2::scanner::Marker)],
    position: &mut usize,
    anchors: &mut HashMap<usize, SafeYaml>,
    depth: usize,
) -> Result<SafeYaml> {
    if depth > 256 {
        return Err(invalid());
    }
    let event = events.get(*position).ok_or_else(invalid)?.0.clone();
    *position += 1;
    let (value, anchor) = match event {
        Event::Scalar(value, style, anchor, tag) => (scalar(value, style, tag)?, anchor),
        Event::Alias(anchor) => {
            return Ok(anchors
                .get(&anchor)
                .cloned()
                .unwrap_or(SafeYaml::RecursiveAlias(anchor)))
        }
        Event::SequenceStart(anchor, tag) => {
            let mut values = Vec::new();
            while !matches!(
                events.get(*position).map(|event| &event.0),
                Some(Event::SequenceEnd)
            ) {
                let value = node(events, position, anchors, depth + 1)?;
                if matches!(value, SafeYaml::Merge | SafeYaml::ValueMarker) {
                    return Err(invalid());
                }
                values.push(value);
            }
            *position += 1;
            let value = match tag_name(tag.as_ref()).as_deref() {
                None | Some("!" | "tag:yaml.org,2002:seq") => SafeYaml::Sequence(values),
                Some("tag:yaml.org,2002:omap" | "tag:yaml.org,2002:pairs") => {
                    let mut pairs = Vec::new();
                    for value in values {
                        if let SafeYaml::Mapping(mut values) = value {
                            if values.len() != 1 {
                                return Err(invalid());
                            }
                            pairs.push(values.remove(0));
                        } else {
                            return Err(invalid());
                        }
                    }
                    SafeYaml::Pairs(pairs)
                }
                _ => return Err(invalid()),
            };
            (value, anchor)
        }
        Event::MappingStart(anchor, tag) => {
            let mut entries = Vec::new();
            while !matches!(
                events.get(*position).map(|event| &event.0),
                Some(Event::MappingEnd)
            ) {
                let key = node(events, position, anchors, depth + 1)?;
                let value = node(events, position, anchors, depth + 1)?;
                entries.push((key, value));
            }
            *position += 1;
            let value = mapping(entries)?;
            let value = match tag_name(tag.as_ref()).as_deref() {
                None | Some("!" | "tag:yaml.org,2002:map") => value,
                Some("tag:yaml.org,2002:set") => SafeYaml::Set(
                    value
                        .as_mapping()
                        .unwrap()
                        .iter()
                        .map(|(key, _)| key.clone())
                        .collect(),
                ),
                _ => return Err(invalid()),
            };
            (value, anchor)
        }
        _ => return Err(invalid()),
    };
    if anchor != 0 {
        anchors.insert(anchor, value.clone());
    }
    Ok(value)
}

pub fn safe_load(source: &str) -> Result<SafeYaml> {
    let mut parser = Parser::new_from_str(source);
    let mut events = Vec::new();
    loop {
        let event = parser.next_token().map_err(|_| invalid())?;
        let done = event.0 == Event::StreamEnd;
        events.push(event);
        if done {
            break;
        }
    }
    let mut position = 0;
    while matches!(
        events.get(position).map(|event| &event.0),
        Some(Event::StreamStart | Event::Nothing)
    ) {
        position += 1;
    }
    if events
        .get(position)
        .is_some_and(|event| event.0 == Event::StreamEnd)
    {
        return Ok(SafeYaml::Null);
    }
    if !matches!(
        events.get(position).map(|event| &event.0),
        Some(Event::DocumentStart)
    ) {
        return Err(invalid());
    }
    position += 1;
    let result = node(&events, &mut position, &mut HashMap::new(), 0)?;
    if matches!(result, SafeYaml::Merge | SafeYaml::ValueMarker) {
        return Err(invalid());
    }
    if !matches!(
        events.get(position).map(|event| &event.0),
        Some(Event::DocumentEnd)
    ) {
        return Err(invalid());
    }
    position += 1;
    if !matches!(
        events.get(position).map(|event| &event.0),
        Some(Event::StreamEnd)
    ) {
        return Err(invalid());
    }
    Ok(result)
}
