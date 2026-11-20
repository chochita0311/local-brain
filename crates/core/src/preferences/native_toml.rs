//! TOML 1.0 with the frozen CPython 3.11 value semantics. This parser uses flat
//! values so dotted tables and nested values do not acquire a JSON depth limit.
//! Grammar and namespace behavior follow CPython's MIT-licensed tomllib parser
//! (Taneli Hukkinen, 2021); no Python runtime or foreign callback is used.
use super::native::{decimal_limit, float_hex, float_text, float_value, quote};
use super::{values::Arena, Fault, Result, READ_ERROR};
use regex::Regex;
use serde_json::json;
use std::collections::HashSet;
use std::sync::LazyLock;

static NUMBER: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?:0(?:x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*|b[01](?:_?[01])*|o[0-7](?:_?[0-7])*)|[+-]?(?:0|[1-9](?:_?[0-9])*)(?<float>(?:\.[0-9](?:_?[0-9])*)?(?:[eE][+-]?[0-9](?:_?[0-9])*)?))").unwrap()
});
static DATETIME: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(concat!(
        r"^(?<date>[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01]))",
        r"(?:[Tt ](?<time>(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9])",
        r"(?:\.(?<fraction>[0-9]+))?(?<offset>[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])?)?"
    ))
    .unwrap()
});
static TIME: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?<time>(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9])(?:\.(?<fraction>[0-9]+))?")
        .unwrap()
});

fn invalid() -> Fault {
    let mut fault = Fault::prefs(READ_ERROR);
    fault.commit = "not-published".into();
    fault
}
const WRITE_ERROR: &str = "기존 설정에 저장할 수 없는 값이 있습니다. 파일은 보존했습니다.";

#[derive(Default)]
struct Flags {
    explicit: HashSet<Vec<String>>,
    frozen: HashSet<Vec<String>>,
    pending: HashSet<Vec<String>>,
}
impl Flags {
    fn frozen(&self, key: &[String]) -> bool {
        (1..=key.len()).any(|length| self.frozen.contains(&key[..length]))
    }
    fn finish_section(&mut self) {
        self.explicit.extend(self.pending.drain());
    }
    fn reset_array(&mut self, key: &[String]) {
        self.explicit.retain(|entry| !entry.starts_with(key));
        self.frozen.retain(|entry| !entry.starts_with(key));
    }
}

struct Parser {
    text: String,
    pos: usize,
    arena: Arena,
}
impl Parser {
    fn rest(&self) -> &str {
        &self.text[self.pos..]
    }
    fn byte(&self) -> Option<u8> {
        self.text.as_bytes().get(self.pos).copied()
    }
    fn take(&mut self, text: &str) -> bool {
        if self.rest().starts_with(text) {
            self.pos += text.len();
            true
        } else {
            false
        }
    }
    fn expect(&mut self, text: &str) -> Result<()> {
        if self.take(text) {
            Ok(())
        } else {
            Err(invalid())
        }
    }
    fn whitespace(&mut self, multiline: bool) {
        while self
            .byte()
            .is_some_and(|c| c == b' ' || c == b'\t' || (multiline && c == b'\n'))
        {
            self.pos += 1;
        }
    }
    fn comment(&mut self) -> Result<()> {
        if self.take("#") {
            while let Some(c) = self.byte() {
                if c == b'\n' {
                    break;
                }
                if (c < 0x20 && c != b'\t') || c == 0x7f {
                    return Err(invalid());
                }
                self.pos += 1;
            }
        }
        Ok(())
    }
    fn array_whitespace(&mut self) -> Result<()> {
        loop {
            self.whitespace(true);
            if self.byte() != Some(b'#') {
                return Ok(());
            }
            self.comment()?;
        }
    }
    fn key(&mut self) -> Result<Vec<String>> {
        let mut key = vec![];
        loop {
            let item = match self.byte() {
                Some(b'\'' | b'"') => self.string(false)?,
                Some(c) if bare(c) => {
                    let start = self.pos;
                    while self.byte().is_some_and(bare) {
                        self.pos += 1;
                    }
                    self.text[start..self.pos].into()
                }
                _ => return Err(invalid()),
            };
            key.push(item);
            self.whitespace(false);
            if !self.take(".") {
                break;
            }
            self.whitespace(false);
        }
        Ok(key)
    }
    fn string(&mut self, allow_multiline: bool) -> Result<String> {
        let delimiter = self.byte().ok_or_else(invalid)?;
        let multiline = allow_multiline
            && self
                .rest()
                .as_bytes()
                .get(..3)
                .is_some_and(|v| v == [delimiter; 3]);
        self.pos += if multiline { 3 } else { 1 };
        if multiline {
            self.take("\n");
        }
        let mut result = String::new();
        loop {
            let c = self.byte().ok_or_else(invalid)?;
            if c == delimiter {
                if !multiline {
                    self.pos += 1;
                    return Ok(result);
                }
                if self
                    .rest()
                    .as_bytes()
                    .get(..3)
                    .is_some_and(|v| v == [delimiter; 3])
                {
                    self.pos += 3;
                    for _ in 0..2 {
                        if self.byte() == Some(delimiter) {
                            result.push(delimiter as char);
                            self.pos += 1;
                        } else {
                            break;
                        }
                    }
                    return Ok(result);
                }
            }
            if c == b'\\' && delimiter == b'"' {
                self.pos += 1;
                let escaped = self.byte().ok_or_else(invalid)?;
                self.pos += 1;
                match escaped {
                    b'b' => result.push('\u{8}'),
                    b't' => result.push('\t'),
                    b'n' => result.push('\n'),
                    b'f' => result.push('\u{c}'),
                    b'r' => result.push('\r'),
                    b'"' => result.push('"'),
                    b'\\' => result.push('\\'),
                    b'u' | b'U' => {
                        let count = if escaped == b'u' { 4 } else { 8 };
                        let text = self.rest().get(..count).ok_or_else(invalid)?;
                        if !text.bytes().all(|c| c.is_ascii_hexdigit()) {
                            return Err(invalid());
                        }
                        let point = u32::from_str_radix(text, 16).map_err(|_| invalid())?;
                        result.push(char::from_u32(point).ok_or_else(invalid)?);
                        self.pos += count;
                    }
                    b' ' | b'\t' | b'\n' if multiline => {
                        if escaped != b'\n' {
                            self.whitespace(false);
                            // tomllib accepts whitespace to EOF here but the
                            // enclosing unterminated string still refuses it.
                            self.expect("\n")?;
                        }
                        self.whitespace(true);
                    }
                    _ => return Err(invalid()),
                }
            } else {
                if (c < 0x20 && c != b'\t' && !(multiline && c == b'\n')) || c == 0x7f {
                    return Err(invalid());
                }
                let ch = self.rest().chars().next().ok_or_else(invalid)?;
                result.push(ch);
                self.pos += ch.len_utf8();
            }
        }
    }
    fn nest(&mut self, root: usize, key: &[String], access_arrays: bool) -> Result<usize> {
        let mut current = root;
        for part in key {
            let mut child = if let Some(id) = self.arena.get(current, part) {
                id
            } else {
                let child = self.arena.add("table", json!([]));
                self.arena.set(current, part, child)?;
                child
            };
            if access_arrays && self.arena.kind(child) == "array" {
                child = *self.arena.children(child)?.last().ok_or_else(invalid)?;
            }
            if self.arena.kind(child) != "table" {
                return Err(invalid());
            }
            current = child;
        }
        Ok(current)
    }
    fn insert(&mut self, table: usize, key: &str, value: usize) -> Result<()> {
        if self.arena.get(table, key).is_some() {
            return Err(invalid());
        }
        self.arena.set(table, key, value)
    }

    /// Containers are parsed with an explicit stack. Scalar parsing and strings
    /// have no recursive JSON conversion, including for deeply dotted settings.
    fn value(&mut self) -> Result<usize> {
        enum Container {
            Array {
                id: usize,
                after: bool,
            },
            Table {
                id: usize,
                key: Vec<String>,
                frozen: HashSet<Vec<String>>,
                after: bool,
                initial: bool,
            },
        }
        let mut stack: Vec<Container> = vec![];
        let mut ready = None;
        let mut need_value = true;
        loop {
            if let Some(value) = ready.take() {
                let Some(parent) = stack.last_mut() else {
                    return Ok(value);
                };
                match parent {
                    Container::Array { id, after } => {
                        self.arena.append(*id, value)?;
                        *after = true;
                    }
                    Container::Table {
                        id,
                        key,
                        frozen,
                        after,
                        ..
                    } => {
                        if (1..=key.len()).any(|length| frozen.contains(&key[..length])) {
                            return Err(invalid());
                        }
                        let table = self.nest(*id, &key[..key.len() - 1], false)?;
                        self.insert(table, key.last().unwrap(), value)?;
                        if ["table", "array"].contains(&self.arena.kind(value)) {
                            frozen.insert(key.clone());
                        }
                        *after = true;
                    }
                }
                need_value = false;
            }
            if !need_value {
                let parent = stack.last_mut().ok_or_else(invalid)?;
                match parent {
                    Container::Array { id, after } => {
                        self.array_whitespace()?;
                        if self.take("]") {
                            ready = Some(*id);
                            stack.pop();
                            continue;
                        }
                        if *after {
                            self.expect(",")?;
                            self.array_whitespace()?;
                            *after = false;
                            if self.take("]") {
                                ready = Some(*id);
                                stack.pop();
                                continue;
                            }
                        }
                        need_value = true;
                    }
                    Container::Table {
                        id,
                        key,
                        after,
                        initial,
                        ..
                    } => {
                        self.whitespace(false);
                        if (*initial || *after) && self.take("}") {
                            ready = Some(*id);
                            stack.pop();
                            continue;
                        }
                        if *after {
                            self.expect(",")?;
                            self.whitespace(false);
                        }
                        *initial = false;
                        *after = false;
                        *key = self.key()?;
                        self.expect("=")?;
                        self.whitespace(false);
                        need_value = true;
                    }
                }
            }
            if need_value {
                match self.byte() {
                    Some(b'[') => {
                        self.pos += 1;
                        let id = self.arena.add("array", json!([]));
                        stack.push(Container::Array { id, after: false });
                        need_value = false;
                    }
                    Some(b'{') => {
                        self.pos += 1;
                        let id = self.arena.add("table", json!([]));
                        stack.push(Container::Table {
                            id,
                            key: vec![],
                            frozen: HashSet::new(),
                            after: false,
                            initial: true,
                        });
                        need_value = false;
                    }
                    _ => {
                        ready = Some(self.scalar()?);
                    }
                }
            }
        }
    }
    fn scalar(&mut self) -> Result<usize> {
        if matches!(self.byte(), Some(b'"' | b'\'')) {
            let value = self.string(true)?;
            return Ok(self.arena.add("string", json!(value)));
        }
        for (text, value) in [("true", true), ("false", false)] {
            if self.take(text) {
                return Ok(self.arena.add("boolean", json!(value)));
            }
        }
        if let Some(captures) = DATETIME.captures(self.rest()) {
            let date = captures.name("date").unwrap().as_str();
            let year: i32 = date[..4].parse().unwrap();
            let month: u32 = date[5..7].parse().unwrap();
            let day: u32 = date[8..].parse().unwrap();
            if year == 0 || chrono::NaiveDate::from_ymd_opt(year, month, day).is_none() {
                return Err(invalid());
            }
            let (kind, value) = if let Some(time) = captures.name("time") {
                let mut value = format!(
                    "{date}T{}{}",
                    time.as_str(),
                    fraction(captures.name("fraction").map(|m| m.as_str()))
                );
                if let Some(offset) = captures.name("offset") {
                    let offset = offset.as_str();
                    value.push_str(if ["Z", "z", "-00:00"].contains(&offset) {
                        "+00:00"
                    } else {
                        offset
                    });
                }
                ("datetime", value)
            } else {
                ("date", date.into())
            };
            self.pos += captures.get(0).unwrap().end();
            return Ok(self.arena.add(kind, json!(value)));
        }
        if let Some(captures) = TIME.captures(self.rest()) {
            let value = format!(
                "{}{}",
                captures.name("time").unwrap().as_str(),
                fraction(captures.name("fraction").map(|m| m.as_str()))
            );
            self.pos += captures.get(0).unwrap().end();
            return Ok(self.arena.add("time", json!(value)));
        }
        if let Some(captures) = NUMBER.captures(self.rest()) {
            let text = captures.get(0).unwrap().as_str();
            let value = if captures
                .name("float")
                .is_some_and(|m| !m.as_str().is_empty())
            {
                let value = text
                    .replace('_', "")
                    .parse::<f64>()
                    .map_err(|_| invalid())?;
                ("float", float_hex(value))
            } else {
                ("integer", integer(text)?)
            };
            self.pos += text.len();
            return Ok(self.arena.add(value.0, json!(value.1)));
        }
        for text in ["inf", "nan", "-inf", "+inf", "-nan", "+nan"] {
            if self.take(text) {
                return Ok(self.arena.add("float", json!(text.trim_start_matches('+'))));
            }
        }
        Err(invalid())
    }
}

fn bare(c: u8) -> bool {
    c.is_ascii_alphanumeric() || c == b'-' || c == b'_'
}
fn fraction(value: Option<&str>) -> String {
    let Some(value) = value else {
        return String::new();
    };
    let mut micros = value[..value.len().min(6)].to_owned();
    while micros.len() < 6 {
        micros.push('0');
    }
    if micros == "000000" {
        String::new()
    } else {
        format!(".{micros}")
    }
}

fn integer(text: &str) -> Result<String> {
    let text = text.replace('_', "");
    let base = if text.starts_with("0x") {
        16
    } else if text.starts_with("0o") {
        8
    } else if text.starts_with("0b") {
        2
    } else {
        10
    };
    if base == 10 {
        let text = text.trim_start_matches('+');
        // Decimal TOML input has the same conversion limit as the baseline.
        decimal_limit(text).map_err(|_| invalid())?;
        return Ok(if text == "-0" { "0" } else { text }.into());
    }
    // Base 10^9 limbs avoid any i64 narrowing and preserve unbounded hex input.
    let mut limbs = vec![0u64];
    for digit in text[2..].bytes() {
        let mut carry = (digit as char).to_digit(base).ok_or_else(invalid)? as u64;
        for limb in &mut limbs {
            let value = *limb * base as u64 + carry;
            *limb = value % 1_000_000_000;
            carry = value / 1_000_000_000;
        }
        if carry != 0 {
            limbs.push(carry);
        }
    }
    let mut value = limbs.pop().unwrap().to_string();
    while let Some(limb) = limbs.pop() {
        value.push_str(&format!("{limb:09}"));
    }
    Ok(value)
}

pub(super) fn decode(text: &str) -> Result<Arena> {
    let mut parser = Parser {
        text: text.replace("\r\n", "\n"),
        pos: 0,
        arena: Arena::table(),
    };
    let mut flags = Flags::default();
    let mut header: Vec<String> = vec![];
    while parser.pos < parser.text.len() {
        parser.whitespace(false);
        if parser.take("\n") {
            continue;
        }
        match parser.byte() {
            None => break,
            Some(b'[') => {
                parser.pos += 1;
                let array = parser.take("[");
                flags.finish_section();
                parser.whitespace(false);
                let key = parser.key()?;
                if flags.frozen(&key) || (!array && flags.explicit.contains(&key)) {
                    return Err(invalid());
                }
                if array {
                    flags.reset_array(&key);
                    let table = parser.nest(0, &key[..key.len() - 1], true)?;
                    let name = key.last().unwrap();
                    let array = if let Some(id) = parser.arena.get(table, name) {
                        if parser.arena.kind(id) != "array" {
                            return Err(invalid());
                        }
                        id
                    } else {
                        let id = parser.arena.add("array", json!([]));
                        parser.arena.set(table, name, id)?;
                        id
                    };
                    let child = parser.arena.add("table", json!([]));
                    parser.arena.append(array, child)?;
                } else {
                    parser.nest(0, &key, true)?;
                }
                flags.explicit.insert(key.clone());
                parser.expect(if array { "]]" } else { "]" })?;
                header = key;
                parser.whitespace(false);
            }
            Some(b'#') => {}
            _ => {
                let key = parser.key()?;
                parser.expect("=")?;
                parser.whitespace(false);
                let value = parser.value()?;
                for length in 1..key.len() {
                    let mut path = header.clone();
                    path.extend_from_slice(&key[..length]);
                    if flags.explicit.contains(&path) {
                        return Err(invalid());
                    }
                    flags.pending.insert(path);
                }
                let mut parent = header.clone();
                parent.extend_from_slice(&key[..key.len() - 1]);
                if flags.frozen(&parent) {
                    return Err(invalid());
                }
                let table = parser.nest(0, &parent, true)?;
                parser.insert(table, key.last().unwrap(), value)?;
                if ["array", "table"].contains(&parser.arena.kind(value)) {
                    parent.push(key.last().unwrap().clone());
                    flags.frozen.insert(parent);
                }
                parser.whitespace(false);
            }
        }
        parser.comment()?;
        if parser.pos < parser.text.len() {
            parser.expect("\n")?;
        }
    }
    parser.arena.subtree(0)
}

fn scalar(arena: &Arena, root: usize) -> Result<String> {
    enum Task {
        Value(usize),
        Text(&'static str),
    }
    let mut tasks = vec![Task::Value(root)];
    let mut output = String::new();
    while let Some(task) = tasks.pop() {
        let id = match task {
            Task::Value(id) => id,
            Task::Text(text) => {
                output.push_str(text);
                continue;
            }
        };
        let text = arena.value(id).as_str();
        match arena.kind(id) {
            "string" => output.push_str(&quote(text.unwrap())?),
            "boolean" => output.push_str(if arena.value(id) == true {
                "true"
            } else {
                "false"
            }),
            "integer" => {
                let text = text.ok_or_else(Fault::protocol)?;
                decimal_limit(text)?;
                output.push_str(text);
            }
            "float" => {
                output.push_str(&float_text(float_value(text.ok_or_else(Fault::protocol)?)?))
            }
            "date" | "time" | "datetime" => output.push_str(text.ok_or_else(Fault::protocol)?),
            "array" => {
                let children = arena.children(id)?;
                if children.iter().any(|child| arena.kind(*child) == "table") {
                    return Err(Fault::prefs(WRITE_ERROR));
                }
                output.push('[');
                tasks.push(Task::Text("]"));
                for (index, child) in children.into_iter().enumerate().rev() {
                    tasks.push(Task::Value(child));
                    if index != 0 {
                        tasks.push(Task::Text(", "));
                    }
                }
            }
            _ => return Err(Fault::prefs(WRITE_ERROR)),
        }
    }
    Ok(output)
}

pub(super) fn encode(arena: &Arena) -> Result<String> {
    enum Task {
        Table(usize, String),
        Header(String),
    }
    if arena.kind(0) != "table" {
        return Err(Fault::prefs(WRITE_ERROR));
    }
    let mut lines = vec![];
    let mut tasks = vec![Task::Table(0, String::new())];
    while let Some(task) = tasks.pop() {
        let (id, prefix) = match task {
            Task::Header(line) => {
                lines.push(String::new());
                lines.push(line);
                continue;
            }
            Task::Table(id, prefix) => (id, prefix),
        };
        let entries = arena.entries(id)?;
        let mut containers = vec![];
        for (key, child) in entries {
            let children = if arena.kind(child) == "array" {
                arena.children(child)?
            } else {
                vec![]
            };
            let table_array = children
                .first()
                .is_some_and(|id| arena.kind(*id) == "table");
            if arena.kind(child) != "table" && !table_array {
                lines.push(format!("{} = {}", quote(&key)?, scalar(arena, child)?));
            } else {
                let name = format!(
                    "{}{}{}",
                    prefix,
                    if prefix.is_empty() { "" } else { "." },
                    quote(&key)?
                );
                if table_array {
                    for entry in children {
                        if arena.kind(entry) != "table" {
                            return Err(Fault::prefs(WRITE_ERROR));
                        }
                        containers.push((entry, name.clone(), true));
                    }
                } else {
                    containers.push((child, name, false));
                }
            }
        }
        for (child, name, array) in containers.into_iter().rev() {
            let header = if array {
                format!("[[{name}]]")
            } else {
                format!("[{name}]")
            };
            tasks.push(Task::Table(child, name));
            tasks.push(Task::Header(header));
        }
    }
    Ok(lines.join("\n") + "\n")
}
