use super::{ParsedEvent, ParsedSession};
use crate::backend::{BackendError, Result};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    collections::VecDeque,
    fs::File,
    io::{BufRead, BufReader, Read},
    path::Path,
    sync::LazyLock,
};

pub(crate) trait PythonText {
    fn py_trim(&self) -> &str;
    fn py_trim_end(&self) -> &str;
}
impl PythonText for str {
    fn py_trim(&self) -> &str {
        self.trim_matches(crate::backend::unicode::python_space)
    }
    fn py_trim_end(&self) -> &str {
        self.trim_end_matches(crate::backend::unicode::python_space)
    }
}

pub fn stable_id(parts: &[&str]) -> String {
    format!("{:x}", Sha256::digest(parts.join("\u{1f}").as_bytes()))
}
pub(crate) fn path_text(path: &Path) -> Result<String> {
    path.to_str()
        .map(ToOwned::to_owned)
        .ok_or_else(|| BackendError::invalid("source_unicode", "Source path is not valid Unicode"))
}
pub(crate) fn python_string(value: &Value) -> String {
    crate::backend::json::python_string(value)
}

pub(crate) fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(v) => v.as_f64().is_none_or(|n| n != 0.0),
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
pub(crate) fn string(value: &Value) -> Option<String> {
    value.as_str().map(ToOwned::to_owned)
}
pub(crate) fn nonempty(value: &Value) -> Option<String> {
    value
        .as_str()
        .map(|s| s.py_trim())
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
}
pub(crate) fn first<'a>(values: &[&'a Value]) -> &'a Value {
    values
        .iter()
        .copied()
        .find(|v| truth(v))
        .or_else(|| values.last().copied())
        .unwrap_or(&Value::Null)
}
pub(crate) fn text_from_content(content: &Value) -> String {
    if let Some(text) = content.as_str() {
        return text.py_trim().into();
    }
    content
        .as_array()
        .map(|items| {
            items
                .iter()
                .filter(|item| {
                    matches!(
                        item["type"].as_str(),
                        Some("text" | "input_text" | "output_text")
                    )
                })
                .filter_map(|item| nonempty(&item["text"]))
                .collect::<Vec<_>>()
                .join("\n\n")
        })
        .unwrap_or_default()
}
pub(crate) fn native_event_id(record: &Value, fallback: &str) -> String {
    ["uuid", "id", "event_id", "eventId"]
        .iter()
        .find_map(|key| nonempty(&record[key]))
        .unwrap_or_else(|| fallback.into())
}
pub(crate) fn title(text: &str, fallback: &str) -> String {
    let text = text
        .split(crate::backend::unicode::python_space)
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    if text.is_empty() {
        return fallback.into();
    }
    if text.chars().count() <= 96 {
        text
    } else {
        format!(
            "{}...",
            text.chars().take(95).collect::<String>().py_trim_end()
        )
    }
}
pub(crate) fn finish(
    session: &mut ParsedSession,
    timestamps: &[String],
    first_text: &str,
    fallback: &str,
) {
    session.title = title(first_text, fallback);
    session.started_at = timestamps.iter().min().cloned();
    session.ended_at = timestamps.iter().max().cloned();
    session.last_event_at = session.ended_at.clone();
    static MAINTENANCE: LazyLock<regex::Regex> = LazyLock::new(|| {
        python_regex(r"(?i)^\s*\[\s*LOCALBRAIN_RUN\s*:\s*(lb-[0-9a-f]{12})\s*\]\s*\n\s*\[\s*MODE\s*:\s*maintenance\s*\]").unwrap()
    });
    for event in &session.events {
        if event.event_type != "message" || event.role.as_deref() != Some("user") {
            continue;
        }
        if let Some(captures) = event
            .text
            .as_deref()
            .and_then(|text| MAINTENANCE.captures(text))
        {
            let run = captures[1].to_lowercase();
            session.session_class = "maintenance".into();
            session.index_policy = "metadata_only".into();
            session.maintenance_run_id = Some(run.clone());
            session.title = format!("LocalBrain maintenance · {run}");
            break;
        }
    }
}
pub(crate) fn message(
    provider: &str,
    external: &str,
    line: i64,
    role: &str,
    timestamp: Option<String>,
    text: String,
) -> ParsedEvent {
    ParsedEvent {
        event_id: stable_id(&[provider, external, &line.to_string(), role]),
        sequence: line * 10,
        source_line: line,
        event_type: "message".into(),
        occurred_at: timestamp,
        role: Some(role.into()),
        text: Some(text),
        tool_name: None,
        message_phase: None,
    }
}
pub(crate) fn tool(
    provider: &str,
    external: &str,
    line: i64,
    offset: Option<i64>,
    timestamp: Option<String>,
    name: String,
) -> ParsedEvent {
    let mut parts = vec![
        provider.to_owned(),
        external.into(),
        line.to_string(),
        "tool".into(),
    ];
    if let Some(offset) = offset {
        parts.push(offset.to_string());
    }
    ParsedEvent {
        event_id: stable_id(&parts.iter().map(String::as_str).collect::<Vec<_>>()),
        sequence: line * 10 + offset.unwrap_or(0),
        source_line: line,
        event_type: "tool_call".into(),
        occurred_at: timestamp,
        role: Some("assistant".into()),
        text: None,
        tool_name: Some(name),
        message_phase: None,
    }
}
pub(crate) fn open_jsonl(path: &Path) -> Result<Box<dyn Read>> {
    let file = File::open(path)?;
    if path
        .file_name()
        .and_then(|s| s.to_str())
        .is_some_and(|s| s.ends_with(".jsonl.zst"))
    {
        Ok(Box::new(zstd::stream::read::Decoder::new(file)?))
    } else {
        Ok(Box::new(file))
    }
}
pub(crate) struct JsonLines {
    reader: BufReader<Box<dyn Read>>,
    pending: VecDeque<String>,
    line: i64,
    source: super::source_json::SourceJson,
}
impl JsonLines {
    pub fn new(path: &Path) -> Result<Self> {
        Ok(Self {
            reader: BufReader::new(open_jsonl(path)?),
            pending: VecDeque::new(),
            line: 0,
            source: super::source_json::for_file(path),
        })
    }
    pub fn source(&self) -> super::source_json::SourceJson {
        self.source.clone()
    }
}
impl Iterator for JsonLines {
    type Item = Result<(i64, Option<Value>)>;
    fn next(&mut self) -> Option<Self::Item> {
        if self.pending.is_empty() {
            let mut buffer = vec![];
            match self.reader.read_until(b'\n', &mut buffer) {
                Ok(0) => return None,
                Err(error) => return Some(Err(error.into())),
                _ => {}
            }
            let text = String::from_utf8_lossy(&buffer)
                .replace("\r\n", "\n")
                .replace('\r', "\n");
            self.pending
                .extend(text.split_terminator('\n').map(ToOwned::to_owned));
        }
        let text = self.pending.pop_front()?;
        self.line += 1;
        match self.source.parse(&text) {
            Ok(value) => Some(Ok((self.line, Some(value)))),
            Err(error)
                if error.is_io()
                    || error.to_string().contains("surrogate")
                    || error.to_string().contains("number out of range") =>
            {
                Some(Err(BackendError::invalid(
                    "source_scalar",
                    format!(
                        "Native source scalar cannot be represented at line {}",
                        self.line
                    ),
                )))
            }
            Err(_) => Some(Ok((self.line, None))),
        }
    }
}

pub(crate) fn python_regex(pattern: &str) -> std::result::Result<regex::Regex, regex::Error> {
    regex::Regex::new(
        &pattern
            .replace(r"\s", r"[\s\x1c-\x1f]")
            .replace(r"\S", r"[^\s\x1c-\x1f]"),
    )
}
