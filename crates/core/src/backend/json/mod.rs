//! Python-compatible JSON scalar admission with explicit source scope and
//! separate strict output/protocol validation. No filesystem or environment I/O.
use crate::backend::{unicode::python_space, BackendError, Result};
mod python;
mod selected_strings;
use serde::{
    de::{self, DeserializeSeed, MapAccess, SeqAccess, Visitor as DeVisitor},
    Deserialize, Serialize,
};
use serde_json::{Map, Number, Value};
use std::{
    collections::HashSet,
    fmt,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, OnceLock,
    },
};

/// Marker discovery is lazy. File adapters supply their own inventory callback;
/// an in-memory scope declares the original document and its decoded descendants.
#[derive(Clone)]
pub struct Scope(Arc<State>);
struct State {
    marker: OnceLock<Result<char>>,
    inventory: Box<dyn Fn() -> Result<char> + Send + Sync>,
    unicode_check: AtomicBool,
}
impl Scope {
    pub fn for_document(text: &str) -> Self {
        let text: Arc<str> = text.into();
        Self::with_marker_factory(move || {
            let mut inventory = MarkerInventory::default();
            inventory.add_text(&text);
            inventory.finish()
        })
    }
    pub(crate) fn with_marker_factory(
        factory: impl Fn() -> Result<char> + Send + Sync + 'static,
    ) -> Self {
        Self(Arc::new(State {
            marker: OnceLock::new(),
            inventory: Box::new(factory),
            unicode_check: AtomicBool::new(false),
        }))
    }
    pub fn parse(&self, text: &str) -> std::result::Result<Value, serde_json::Error> {
        self.parse_mode(text, false)
    }
    pub fn parse_unique(&self, text: &str) -> std::result::Result<Value, serde_json::Error> {
        self.parse_mode(text, true)
    }
    fn parse_mode(
        &self,
        text: &str,
        unique: bool,
    ) -> std::result::Result<Value, serde_json::Error> {
        match strict_value_mode(text, unique) {
            Ok(value) => Ok(value),
            Err(error) => {
                if error.is_io() {
                    return Err(error);
                }
                let marked = self.0.marker.get().is_some_and(|marker| {
                    marker.as_ref().is_ok_and(|marker| text.contains(*marker))
                });
                if !marked
                    && !text.contains("NaN")
                    && !text.contains("Infinity")
                    && !text.contains("\\ud")
                    && !text.contains("\\uD")
                {
                    return Err(error);
                }
                let marker = self
                    .0
                    .marker
                    .get_or_init(|| (self.0.inventory)())
                    .as_ref()
                    .map_err(|error| {
                        serde_json::Error::io(std::io::Error::other(error.to_string()))
                    })?;
                // The source budget excludes the temporary numeric marker
                // object introduced for a nonfinite leaf by the lexer.
                admit_depth(text, MAX_JSON_DEPTH)?;
                let (value, unicode) = parse_exceptional(text, *marker, |rewritten| {
                    strict_value_limit(rewritten, unique, MAX_JSON_DEPTH + 1)
                })?;
                if unicode {
                    self.0.unicode_check.store(true, Ordering::Relaxed);
                }
                Ok(value)
            }
        }
    }
    /// Validate only values actually selected for a Rust DTO/string or write.
    /// Ignored exceptional strings need not become representable UTF-8 strings.
    pub fn materialized(&self, value: &(impl Serialize + Sync)) -> Result<()> {
        if let Some(Err(error)) = self.0.marker.get() {
            return Err(error.clone());
        }
        if !self.0.unicode_check.load(Ordering::Relaxed) {
            return Ok(());
        }
        if let Some(Ok(marker)) = self.0.marker.get() {
            // This branch exists only after an exceptional Unicode scalar was
            // observed. Serializing a selected DTO can itself recurse, so keep
            // that rare validation on the same bounded stack as deep decoding.
            on_json_stack(|| materialized(value, *marker))
                .map_err(|error| BackendError::invalid("source_unicode", error.to_string()))??;
        }
        Ok(())
    }
    /// Python str(value), retaining surrogate escapes inside containers. A
    /// selected primitive string still requires materialized() validation.
    pub fn python_string(&self, value: &Value) -> String {
        python::string(value, self.unicode_marker())
    }
    /// Iterate the original Python characters, including distinct unpaired
    /// UTF-16 units. Only this scope can interpret its opaque transport tokens.
    pub fn characters<'a>(&self, text: &'a str) -> SourceCharacters<'a> {
        SourceCharacters::new(text, self.unicode_marker())
    }
    fn unicode_marker(&self) -> Option<char> {
        self.0
            .unicode_check
            .load(Ordering::Relaxed)
            .then(|| {
                self.0
                    .marker
                    .get()
                    .and_then(|value| value.as_ref().ok())
                    .copied()
            })
            .flatten()
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SourceCharacter {
    Scalar(char),
    Surrogate(u16),
}
pub struct SourceCharacters<'a> {
    characters: std::str::Chars<'a>,
    marker: Option<char>,
}
impl<'a> SourceCharacters<'a> {
    fn new(text: &'a str, marker: Option<char>) -> Self {
        Self {
            characters: text.chars(),
            marker,
        }
    }
}
impl Iterator for SourceCharacters<'_> {
    type Item = SourceCharacter;
    fn next(&mut self) -> Option<Self::Item> {
        let ch = self.characters.next()?;
        if Some(ch) == self.marker {
            let mut candidate = self.characters.clone();
            let digits = candidate.by_ref().take(4).collect::<String>();
            if candidate.next() == Some(ch) {
                if let Ok(point) = u16::from_str_radix(&digits, 16) {
                    if (0xd800..=0xdfff).contains(&point) {
                        self.characters = candidate;
                        return Some(SourceCharacter::Surrogate(point));
                    }
                }
            }
        }
        Some(SourceCharacter::Scalar(ch))
    }
}
/// Python str/repr for values that do not carry a source scope. Never infer
/// opaque surrogate units without the scope that created them.
pub fn python_string(value: &Value) -> String {
    python::string(value, None)
}

/// Inventory every character that can appear after repeated escape decoding.
/// Reductions run in layer/position order. Newly decoded backslashes must not
/// consume a sibling escape before that sibling's original layer is decoded.
#[derive(Default)]
pub(crate) struct MarkerInventory {
    used: HashSet<char>,
}
impl MarkerInventory {
    pub(crate) fn add_text(&mut self, text: &str) {
        use std::collections::BTreeSet;
        const END: usize = usize::MAX;
        struct Node {
            point: u32,
            previous: usize,
            next: usize,
            layer: usize,
            removed: bool,
        }
        fn candidate(nodes: &[Node], start: usize) -> Option<(u32, usize, usize)> {
            if start == END || nodes[start].removed {
                return None;
            }
            let node = &nodes[start];
            let second = node.next;
            if second == END {
                return None;
            }
            let other = &nodes[second];
            let mut layer = node.layer.max(other.layer);
            if (0xd800..=0xdbff).contains(&node.point) && (0xdc00..=0xdfff).contains(&other.point) {
                return Some((
                    0x10000 + ((node.point - 0xd800) << 10) + (other.point - 0xdc00),
                    second,
                    layer,
                ));
            }
            if node.point != 92 {
                return None;
            }
            if let Some(point) = match other.point {
                34 => Some(34),
                47 => Some(47),
                92 => Some(92),
                98 => Some(8),
                102 => Some(12),
                110 => Some(10),
                114 => Some(13),
                116 => Some(9),
                _ => None,
            } {
                return Some((point, second, layer));
            }
            let digits = match other.point {
                117 => 4,
                85 => 8,
                120 => 2,
                _ => return None,
            };
            let mut current = second;
            let mut value = 0;
            for _ in 0..digits {
                current = nodes[current].next;
                if current == END {
                    return None;
                }
                layer = layer.max(nodes[current].layer);
                value = (value << 4) | char::from_u32(nodes[current].point)?.to_digit(16)?;
            }
            Some((value, current, layer))
        }
        let mut nodes: Vec<Node> = text
            .chars()
            .enumerate()
            .map(|(index, ch)| {
                self.used.insert(ch);
                Node {
                    point: ch as u32,
                    previous: if index == 0 { END } else { index - 1 },
                    next: index + 1,
                    layer: 0,
                    removed: false,
                }
            })
            .collect();
        if let Some(last) = nodes.last_mut() {
            last.next = END;
        }
        let mut pending = BTreeSet::new();
        for index in 0..nodes.len() {
            if let Some((_, _, layer)) = candidate(&nodes, index) {
                pending.insert((layer, index));
            }
        }
        while let Some((expected, start)) = pending.pop_first() {
            let Some((point, end, layer)) = candidate(&nodes, start) else {
                continue;
            };
            if layer != expected {
                pending.insert((layer, start));
                continue;
            }
            let next = nodes[end].next;
            let mut current = nodes[start].next;
            while current != next {
                nodes[current].removed = true;
                current = nodes[current].next;
            }
            nodes[start].point = point;
            nodes[start].layer = layer + 1;
            nodes[start].next = next;
            if next != END {
                nodes[next].previous = start;
            }
            if let Some(ch) = char::from_u32(point) {
                self.used.insert(ch);
            }
            // The longest escape is a backslash, U and eight hex digits.
            // Only those predecessor positions can gain a new token here.
            let mut position = start;
            for _ in 0..10 {
                if let Some((_, _, layer)) = candidate(&nodes, position) {
                    pending.insert((layer, position));
                }
                position = nodes[position].previous;
                if position == END {
                    break;
                }
            }
        }
    }
    pub(crate) fn finish(self) -> Result<char> {
        // Prefer non-word control/noncharacter sentinels. The final fallback
        // retains the previous finite scalar inventory rather than imposing a
        // smaller arbitrary pool on large source documents.
        let preferred = (0..=0x1f).chain(0x7f..=0x9f).chain([0xfffe, 0xffff]);
        for point in preferred.chain(0..=0x10ffff) {
            let Some(ch) = char::from_u32(point) else {
                continue;
            };
            if !python_space(ch)
                && !self.used.contains(&ch)
                // Printable ASCII is introduced by Python container repr
                // syntax even when absent from the original document.
                && (!ch.is_ascii() || ch.is_ascii_control())
                && ch.to_lowercase().eq(std::iter::once(ch))
            {
                return Ok(ch);
            }
        }
        Err(BackendError::invalid(
            "source_unicode",
            "No lossless exceptional-scalar marker is available",
        ))
    }
}

const NUMBER_TOKEN: &str = "$serde_json::private::Number";
struct Key {
    value: String,
    number: bool,
}
impl<'de> Deserialize<'de> for Key {
    fn deserialize<D: de::Deserializer<'de>>(decoder: D) -> std::result::Result<Self, D::Error> {
        struct K;
        impl<'de> DeVisitor<'de> for K {
            type Value = Key;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("JSON object key")
            }
            fn visit_newtype_struct<D: de::Deserializer<'de>>(
                self,
                decoder: D,
            ) -> std::result::Result<Key, D::Error> {
                Ok(Key {
                    value: String::deserialize(decoder)?,
                    number: false,
                })
            }
            fn visit_str<E: de::Error>(self, value: &str) -> std::result::Result<Key, E> {
                Ok(Key {
                    value: value.into(),
                    number: value == NUMBER_TOKEN,
                })
            }
            fn visit_borrowed_str<E: de::Error>(
                self,
                value: &'de str,
            ) -> std::result::Result<Key, E> {
                self.visit_str(value)
            }
        }
        // serde_json1.0.154's real MapKey preserves a newtype boundary. Its
        // arbitrary-precision NumberFieldDeserializer is a scalar, so this
        // distinguishes genuine JSON keys from the internal number envelope.
        // Literal/escaped reserved keys therefore retain ordinary map identity.
        decoder.deserialize_newtype_struct("LocalBrainJsonKey", K)
    }
}
struct ValueSeed {
    unique: bool,
}
impl<'de> DeserializeSeed<'de> for ValueSeed {
    type Value = Value;
    fn deserialize<D: de::Deserializer<'de>>(
        self,
        decoder: D,
    ) -> std::result::Result<Value, D::Error> {
        struct V {
            unique: bool,
        }
        impl<'de> DeVisitor<'de> for V {
            type Value = Value;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("JSON value")
            }
            fn visit_unit<E: de::Error>(self) -> std::result::Result<Value, E> {
                Ok(Value::Null)
            }
            fn visit_none<E: de::Error>(self) -> std::result::Result<Value, E> {
                Ok(Value::Null)
            }
            fn visit_bool<E: de::Error>(self, value: bool) -> std::result::Result<Value, E> {
                Ok(value.into())
            }
            fn visit_i64<E: de::Error>(self, value: i64) -> std::result::Result<Value, E> {
                Ok(value.into())
            }
            fn visit_u64<E: de::Error>(self, value: u64) -> std::result::Result<Value, E> {
                Ok(value.into())
            }
            fn visit_f64<E: de::Error>(self, value: f64) -> std::result::Result<Value, E> {
                Number::from_f64(value)
                    .map(Value::Number)
                    .ok_or_else(|| E::custom("Nonfinite number in strict JSON"))
            }
            fn visit_str<E: de::Error>(self, value: &str) -> std::result::Result<Value, E> {
                Ok(Value::String(value.into()))
            }
            fn visit_borrowed_str<E: de::Error>(
                self,
                value: &'de str,
            ) -> std::result::Result<Value, E> {
                self.visit_str(value)
            }
            fn visit_string<E: de::Error>(self, value: String) -> std::result::Result<Value, E> {
                Ok(Value::String(value))
            }
            fn visit_seq<A: SeqAccess<'de>>(
                self,
                mut values: A,
            ) -> std::result::Result<Value, A::Error> {
                let mut result = vec![];
                while let Some(value) = values.next_element_seed(ValueSeed {
                    unique: self.unique,
                })? {
                    result.push(value);
                }
                Ok(Value::Array(result))
            }
            fn visit_map<A: MapAccess<'de>>(
                self,
                mut values: A,
            ) -> std::result::Result<Value, A::Error> {
                let Some(key) = values.next_key::<Key>()? else {
                    return Ok(Value::Object(Map::new()));
                };
                if key.number {
                    let raw = values.next_value::<String>()?;
                    if integer_raw(&raw) && raw.trim_start_matches('-').len() > 4300 {
                        return Err(de::Error::custom(
                            "Source integer exceeds Python decimal conversion limit",
                        ));
                    }
                    return Ok(Value::Number(Number::from_string_unchecked(raw)));
                }
                let mut result = Map::new();
                result.insert(
                    key.value,
                    values.next_value_seed(ValueSeed {
                        unique: self.unique,
                    })?,
                );
                while let Some(key) = values.next_key::<String>()? {
                    if self.unique && result.contains_key(&key) {
                        return Err(de::Error::custom("Duplicate JSON field"));
                    }
                    result.insert(
                        key,
                        values.next_value_seed(ValueSeed {
                            unique: self.unique,
                        })?,
                    );
                }
                Ok(Value::Object(result))
            }
        }
        decoder.deserialize_any(V {
            unique: self.unique,
        })
    }
}
fn integer_raw(raw: &str) -> bool {
    let raw = raw.strip_prefix('-').unwrap_or(raw);
    !raw.is_empty() && raw.bytes().all(|ch| ch.is_ascii_digit())
}
pub(crate) fn strict_value(text: &str) -> std::result::Result<Value, serde_json::Error> {
    strict_value_mode(text, false)
}
fn strict_value_mode(text: &str, unique: bool) -> std::result::Result<Value, serde_json::Error> {
    strict_value_limit(text, unique, MAX_JSON_DEPTH)
}
fn strict_value_limit(
    text: &str,
    unique: bool,
    maximum: usize,
) -> std::result::Result<Value, serde_json::Error> {
    match read_value(text, unique, false) {
        Err(error) if error.to_string().starts_with("recursion limit exceeded") => {
            admit_depth(text, maximum)?;
            on_json_stack(|| read_value(text, unique, true))?
        }
        result => result,
    }
}

// CPython3.11's default recursion limit is 1000; its actual JSON refusal point
// also includes the caller's Python frames. Native code keeps the full1000
// container budget instead of inventing a smaller caller-dependent boundary.
// The ordinary serde guard stays enabled; only rare deep inputs get a lexical
// admission pass and a larger parser stack. This also bounds partial-tree Drop
// after a syntax error. A 2MiB child-process test covers returned Value Drop.
const MAX_JSON_DEPTH: usize = 1000;
fn admit_depth(text: &str, maximum: usize) -> std::result::Result<(), serde_json::Error> {
    let mut depth = 0usize;
    let mut quoted = false;
    let mut escaped = false;
    for byte in text.bytes() {
        if quoted {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                quoted = false;
            }
        } else {
            match byte {
                b'"' => quoted = true,
                b'[' | b'{' => {
                    depth += 1;
                    if depth > maximum {
                        return Err(serde_json::Error::io(std::io::Error::new(
                            std::io::ErrorKind::InvalidData,
                            "JSON input exceeds the Python recursion limit of 1000",
                        )));
                    }
                }
                b']' | b'}' => depth = depth.saturating_sub(1),
                _ => {}
            }
        }
    }
    Ok(())
}
fn on_json_stack<T: Send>(
    operation: impl FnOnce() -> T + Send,
) -> std::result::Result<T, serde_json::Error> {
    std::thread::scope(|scope| {
        crate::backend::worker_thread("localbrain-json-depth")
            .spawn_scoped(scope, operation)
            .map_err(serde_json::Error::io)?
            .join()
            .map_err(|_| serde_json::Error::io(std::io::Error::other("JSON decoder worker failed")))
    })
}
fn read_value(
    text: &str,
    unique: bool,
    deep: bool,
) -> std::result::Result<Value, serde_json::Error> {
    let mut decoder = serde_json::Deserializer::from_str(text);
    if deep {
        decoder.disable_recursion_limit();
    }
    let value = ValueSeed { unique }
        .deserialize(&mut decoder)
        .map_err(|error| {
            if error
                .to_string()
                .contains("Python decimal conversion limit")
            {
                serde_json::Error::io(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    "Source integer exceeds Python decimal conversion limit",
                ))
            } else {
                error
            }
        })?;
    decoder.end()?;
    Ok(value)
}
fn decode_error(error: serde_json::Error) -> BackendError {
    BackendError::invalid(
        if error.is_io() { "json_scalar" } else { "json" },
        error.to_string(),
    )
}
/// Decode stored/input JSON. NaN and infinities remain numbers. Any unpaired
/// surrogate selected by this whole-document convenience API fails explicitly.
pub fn decode(text: &str) -> Result<Value> {
    match strict_value(text) {
        Ok(value) => Ok(value),
        Err(error) if error.is_io() => Err(decode_error(error)),
        Err(_) => {
            let scope = Scope::for_document(text);
            let value = scope.parse(text).map_err(decode_error)?;
            scope.materialized(&value)?;
            Ok(value)
        }
    }
}
/// Worker/protocol admission: decoded duplicate names and nonfinite floats fail;
/// integer lexical values retain arbitrary precision through the frozen limit.
pub fn decode_unique(raw: &[u8]) -> Result<Value> {
    let text =
        std::str::from_utf8(raw).map_err(|e| BackendError::invalid("json", e.to_string()))?;
    let value = strict_value_mode(text, true).map_err(decode_error)?;
    validate_http_json(&value).map_err(|error| BackendError::invalid(error.code, error.message))?;
    Ok(value)
}
fn number_text(number: &Number) -> Result<String> {
    let raw = number.to_string();
    if integer_raw(&raw) {
        if raw.trim_start_matches('-').len() > 4300 {
            return Err(BackendError::invalid(
                "json_scalar",
                "Integer exceeds Python decimal conversion limit",
            ));
        }
        return Ok(if raw == "-0" { "0".into() } else { raw });
    }
    let value = match raw.as_str() {
        "NaN" => f64::NAN,
        "Infinity" => f64::INFINITY,
        "-Infinity" => f64::NEG_INFINITY,
        _ => raw
            .parse::<f64>()
            .map_err(|_| BackendError::invalid("json", "Invalid JSON number"))?,
    };
    if value.is_nan() {
        return Ok("NaN".into());
    }
    if value.is_infinite() {
        return Ok(if value.is_sign_negative() {
            "-Infinity"
        } else {
            "Infinity"
        }
        .into());
    }
    let raw = format!("{value:?}");
    Ok(if let Some((mantissa, exponent)) = raw.split_once('e') {
        format!("{mantissa}e{:+03}", exponent.parse::<i32>().unwrap())
    } else {
        raw
    })
}
pub fn validate_http_json(value: &Value) -> Result<()> {
    let mut pending = vec![value];
    while let Some(value) = pending.pop() {
        match value {
            Value::Array(values) => pending.extend(values),
            Value::Object(values) => pending.extend(values.values()),
            Value::Number(number) => {
                let raw = number_text(number).map_err(|mut error| {
                    error.status = 500;
                    error
                })?;
                if ["NaN", "Infinity", "-Infinity"].contains(&raw.as_str()) {
                    return Err(BackendError::new(
                        500,
                        "json_nonfinite",
                        "Out of range float values are not JSON compliant",
                    ));
                }
            }
            _ => {}
        }
    }
    Ok(())
}
pub fn strict_output(value: &Value) -> Result<()> {
    validate_http_json(value)
}
fn encode(value: &Value, sorted: bool, finite: bool, pretty: bool) -> Result<String> {
    enum Part<'a> {
        Value(&'a Value, usize),
        Key(&'a str),
        Literal(&'static str),
        Indent(usize),
    }
    let mut pending = vec![Part::Value(value, 0)];
    let mut out = String::new();
    while let Some(part) = pending.pop() {
        match part {
            Part::Key(value) => out.push_str(&serde_json::to_string(value)?),
            Part::Literal(value) => out.push_str(value),
            Part::Indent(depth) => {
                out.push('\n');
                out.extend(std::iter::repeat_n(' ', depth * 2));
            }
            Part::Value(Value::String(value), _) => out.push_str(&serde_json::to_string(value)?),
            Part::Value(Value::Number(value), _) => {
                let value = number_text(value).map_err(|mut error| {
                    if finite {
                        error.status = 500;
                    }
                    error
                })?;
                if finite && ["NaN", "Infinity", "-Infinity"].contains(&value.as_str()) {
                    return Err(BackendError::new(
                        500,
                        "json_nonfinite",
                        "Out of range float values are not JSON compliant",
                    ));
                }
                out.push_str(&value);
            }
            Part::Value(Value::Null, _) => out.push_str("null"),
            Part::Value(Value::Bool(value), _) => {
                out.push_str(if *value { "true" } else { "false" })
            }
            Part::Value(Value::Array(values), depth) => {
                out.push('[');
                pending.push(Part::Literal("]"));
                if pretty && !values.is_empty() {
                    pending.push(Part::Indent(depth));
                }
                for (index, value) in values.iter().enumerate().rev() {
                    if index + 1 < values.len() {
                        pending.push(Part::Literal(","));
                    }
                    pending.push(Part::Value(value, depth + 1));
                    if pretty {
                        pending.push(Part::Indent(depth + 1));
                    }
                }
            }
            Part::Value(Value::Object(values), depth) => {
                out.push('{');
                pending.push(Part::Literal("}"));
                if pretty && !values.is_empty() {
                    pending.push(Part::Indent(depth));
                }
                let mut keys = values.keys().collect::<Vec<_>>();
                if sorted {
                    keys.sort();
                }
                for (index, key) in keys.iter().enumerate().rev() {
                    if index + 1 < keys.len() {
                        pending.push(Part::Literal(","));
                    }
                    pending.push(Part::Value(&values[*key], depth + 1));
                    pending.push(Part::Literal(if pretty { ": " } else { ":" }));
                    pending.push(Part::Key(key));
                    if pretty {
                        pending.push(Part::Indent(depth + 1));
                    }
                }
            }
        }
    }
    Ok(out)
}
/// Python's compact, sorted, ensure_ascii=False JSON used for stored hashes.
pub fn canonical(value: &Value) -> Result<String> {
    encode(value, true, false, false)
}
/// Python's insertion-ordered, ensure_ascii=False, indent=2 private artifacts.
pub fn pretty(value: &Value) -> Result<String> {
    encode(value, false, false, true)
}
/// JSONResponse's finite-float policy, with no partial output on refusal.
pub fn encode_http(value: &Value) -> Result<String> {
    encode(value, false, true, false)
}

fn hex(bytes: &[u8]) -> Option<u32> {
    if bytes.len() != 4 || !bytes.iter().all(u8::is_ascii_hexdigit) {
        return None;
    }
    u32::from_str_radix(std::str::from_utf8(bytes).ok()?, 16).ok()
}
fn parse_exceptional(
    text: &str,
    marker: char,
    decode: impl Fn(&str) -> std::result::Result<Value, serde_json::Error>,
) -> std::result::Result<(Value, bool), serde_json::Error> {
    let bytes = text.as_bytes();
    let mut out = String::with_capacity(text.len());
    let mut i = 0;
    let mut quoted = false;
    let mut unicode_check = false;
    while i < bytes.len() {
        let b = bytes[i];
        if b == b'"' {
            quoted = !quoted;
            out.push('"');
            i += 1;
            continue;
        }
        if quoted && b == b'\\' {
            if bytes.get(i + 1) == Some(&b'u') {
                if let Some(value) = bytes.get(i + 2..i + 6).and_then(hex) {
                    if (0xd800..=0xdbff).contains(&value) {
                        let pair = bytes.get(i + 6..i + 8) == Some(b"\\u")
                            && bytes
                                .get(i + 8..i + 12)
                                .and_then(hex)
                                .is_some_and(|v| (0xdc00..=0xdfff).contains(&v));
                        if pair {
                            out.push_str(&text[i..i + 12]);
                            i += 12;
                            continue;
                        }
                        unicode_check = true;
                        let encoded = format!("{marker}{value:04x}{marker}");
                        let escaped = serde_json::to_string(&encoded).unwrap();
                        out.push_str(&escaped[1..escaped.len() - 1]);
                        i += 6;
                        continue;
                    }
                    if (0xdc00..=0xdfff).contains(&value) {
                        unicode_check = true;
                        let encoded = format!("{marker}{value:04x}{marker}");
                        let escaped = serde_json::to_string(&encoded).unwrap();
                        out.push_str(&escaped[1..escaped.len() - 1]);
                        i += 6;
                        continue;
                    }
                }
            }
            if let Some(ch) = text[i + 1..].chars().next() {
                out.push('\\');
                out.push(ch);
                i += 1 + ch.len_utf8();
                continue;
            }
        }
        if !quoted {
            let mut special = None;
            for (token, value) in [("-Infinity", "-inf"), ("Infinity", "inf"), ("NaN", "nan")] {
                if text[i..].starts_with(token) {
                    special = Some((token, value));
                    break;
                }
            }
            if let Some((token, value)) = special {
                out.push_str(&format!(
                    "{{{}:{}}}",
                    serde_json::to_string(&marker.to_string()).unwrap(),
                    serde_json::to_string(value).unwrap()
                ));
                i += token.len();
                continue;
            }
        }
        let ch = text[i..].chars().next().unwrap();
        if quoted && ch == marker {
            let escaped = serde_json::to_string(&marker.to_string()).unwrap();
            out.push_str(&escaped[1..escaped.len() - 1]);
            unicode_check = true;
        } else {
            out.push(ch);
        }
        i += ch.len_utf8();
    }
    let mut value = decode(&out)?;
    let key = marker.to_string();
    let mut pending = vec![&mut value];
    while let Some(value) = pending.pop() {
        if let Some(kind) = value
            .as_object()
            .filter(|m| m.len() == 1)
            .and_then(|m| m.get(&key))
            .and_then(Value::as_str)
            .filter(|s| ["nan", "inf", "-inf"].contains(s))
        {
            let raw = match kind {
                "nan" => "NaN",
                "inf" => "Infinity",
                _ => "-Infinity",
            };
            *value = Value::Number(Number::from_string_unchecked(raw.into()));
            continue;
        }
        match value {
            Value::Array(values) => pending.extend(values),
            Value::Object(values) => pending.extend(values.values_mut()),
            _ => {}
        }
    }
    Ok((value, unicode_check))
}
fn materialized(value: &impl Serialize, marker: char) -> Result<()> {
    selected_strings::validate(value, marker)
}
