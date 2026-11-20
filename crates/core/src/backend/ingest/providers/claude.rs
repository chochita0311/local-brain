use super::super::{
    common::*, evidence, skills, ApprovedResourceCall, ParsedSession, ParsedSkillObservation,
    ScanControl,
};
use super::usage;
use crate::backend::{BackendError, Result};
use serde_json::Value;
use std::{
    collections::{HashMap, HashSet},
    path::Path,
};

pub(super) fn parse(path: &Path, control: &ScanControl) -> Result<ParsedSession> {
    let stem = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("")
        .to_owned();
    let mut session = ParsedSession::empty(path, stem.clone());
    let sub = path
        .parent()
        .and_then(Path::file_name)
        .and_then(|s| s.to_str())
        == Some("subagents");
    if sub {
        session.session_role = "subsession".into();
        session.parent_external_id = path
            .parent()
            .and_then(Path::parent)
            .and_then(Path::file_name)
            .and_then(|s| s.to_str())
            .map(Into::into);
    }
    let mut explicit = None;
    let mut first_text = String::new();
    let mut timestamps = vec![];
    let mut assistant: HashMap<(String, i64), Vec<usize>> = HashMap::new();
    let mut reasons: HashMap<(String, i64), HashSet<String>> = HashMap::new();
    let mut usages = HashMap::new();
    let mut calls: HashMap<String, ApprovedResourceCall> = HashMap::new();
    let lines = JsonLines::new(path)?;
    let source_json = lines.source();
    let mut skills = skills::Collector::new("claude", source_json.clone());
    for line in lines {
        control.check()?;
        let (line, record) = line?;
        let Some(record) = record.filter(Value::is_object) else {
            session.skipped_lines += 1;
            continue;
        };
        skills.observe(&record, line);
        if !sub && truth(&record["sessionId"]) {
            session.external_id = source_json.python_string(&record["sessionId"]);
        }
        if truth(&record["cwd"]) {
            session.cwd_raw = Some(
                record["cwd"]
                    .as_str()
                    .ok_or_else(|| {
                        BackendError::invalid("source_path", "Native cwd must be a string")
                    })?
                    .into(),
            );
        }
        if let Some(branch) = nonempty(&record["gitBranch"]) {
            session.git_branch = Some(branch);
        }
        let timestamp = string(&record["timestamp"]);
        if let Some(t) = &timestamp {
            timestamps.push(t.clone());
        }
        let kind = record["type"].as_str().unwrap_or("");
        if kind == "ai-title" && record["aiTitle"].is_string() {
            explicit = Some(record["aiTitle"].as_str().unwrap().py_trim().to_owned());
            continue;
        }
        if kind == "last-prompt" && explicit.as_deref().is_none_or(str::is_empty) {
            if let Some(v) = nonempty(&record["lastPrompt"]) {
                explicit = Some(title(&v, &stem));
            }
            continue;
        }
        if !["user", "assistant"].contains(&kind) || truth(&record["isMeta"]) {
            continue;
        }
        let message_value = &record["message"];
        let content = if message_value.is_object() {
            &message_value["content"]
        } else {
            message_value
        };
        let items = content.as_array().map(Vec::as_slice).unwrap_or(&[]);
        let assistant_key = if kind == "assistant" && message_value.is_object() {
            let key = if let Some(id) = message_value["id"]
                .as_str()
                .filter(|s| !s.py_trim().is_empty())
            {
                (id.into(), 0)
            } else {
                (String::new(), line)
            };
            let set = reasons.entry(key.clone()).or_default();
            if !message_value["stop_reason"].is_null() {
                set.insert(
                    message_value["stop_reason"]
                        .as_str()
                        .unwrap_or("invalid")
                        .into(),
                );
            }
            if items
                .iter()
                .any(|item| matches!(item["type"].as_str(), Some("tool_use" | "server_tool_use")))
            {
                set.insert("tool_use".into());
            }
            if truth(&record["isApiErrorMessage"]) || truth(&record["error"]) {
                set.insert("error".into());
            }
            Some(key)
        } else {
            None
        };
        let is_result = truth(&record["sourceToolAssistantUUID"])
            || record.get("toolUseResult").is_some()
            || items.iter().any(|i| i["type"] == "tool_result");
        if kind == "user" && is_result {
            for (offset, item) in items.iter().enumerate() {
                if item["type"] != "tool_result" {
                    continue;
                }
                let Some(id) = item["tool_use_id"].as_str() else {
                    continue;
                };
                let Some(call) = calls.get(id) else {
                    continue;
                };
                let fallback = stable_id(&[
                    "claude",
                    &session.external_id,
                    &line.to_string(),
                    "approved-tool-result",
                    &(offset + 1).to_string(),
                ]);
                let id = native_event_id(&record, &fallback);
                let failed = evidence::failed(&source_json, &[item, &record["toolUseResult"]]);
                evidence::tool_result(
                    &source_json,
                    &mut session,
                    call,
                    &item["content"],
                    failed,
                    line,
                    &id,
                    timestamp.as_deref(),
                );
            }
            continue;
        }
        let text = text_from_content(content);
        if !text.is_empty() {
            if kind == "user" && first_text.is_empty() {
                first_text = text.clone();
            }
            let event = message(
                "claude",
                &session.external_id,
                line,
                kind,
                timestamp.clone(),
                text.clone(),
            );
            let id = event.event_id.clone();
            let native = native_event_id(&record, &id);
            if let Some(key) = assistant_key {
                assistant.entry(key).or_default().push(session.events.len());
            }
            session.events.push(event);
            evidence::visible(
                &mut session,
                &text,
                kind,
                line,
                &id,
                &native,
                timestamp.as_deref(),
            );
        }
        if kind == "assistant" {
            if let Some(record) = usage::claude(
                &source_json,
                &session.external_id,
                line,
                timestamp.clone(),
                &record,
            )? {
                let identity = record.source_record_id.clone();
                if let Some(index) = usages.get(&identity).copied() {
                    let old: &super::super::ParsedUsageRecord = &session.usage_records[index];
                    if old.capability_state == "malformed" || record.capability_state != "malformed"
                    {
                        session.usage_records[index] = record;
                    }
                } else {
                    usages.insert(identity, session.usage_records.len());
                    session.usage_records.push(record);
                }
            }
            for (offset, item) in items.iter().enumerate() {
                if item["type"] != "tool_use" {
                    continue;
                }
                let Some(name) = item["name"].as_str() else {
                    continue;
                };
                let native = item["id"].as_str();
                let input = &item["input"];
                if name == "Skill"
                    && native.is_some_and(|s| !s.py_trim().is_empty())
                    && input.is_object()
                {
                    if let Some(skill) = nonempty(&input["skill"]) {
                        session.skill_observations.push(ParsedSkillObservation {
                            native_event_id: native.unwrap().py_trim().into(),
                            skill_name: skill,
                            signal_kind: "claude_skill_tool".into(),
                            source_line: line,
                            occurred_at: timestamp.clone(),
                            skill_locator: None,
                            request_key: None,
                        });
                    }
                }
                if let Some(id) = native {
                    if let Some(call) = evidence::approved(&source_json, name, id, input) {
                        calls.insert(id.into(), call);
                    }
                }
                session.events.push(tool(
                    "claude",
                    &session.external_id,
                    line,
                    Some(offset as i64 + 1),
                    timestamp.clone(),
                    name.into(),
                ));
            }
        }
    }
    for (key, indexes) in assistant {
        let reasons = &reasons[&key];
        let phase = if reasons.len() == 1 {
            match reasons.iter().next().unwrap().as_str() {
                "end_turn" => Some("final_answer"),
                "tool_use" => Some("commentary"),
                _ => None,
            }
        } else {
            None
        };
        for index in indexes {
            session.events[index].message_phase = phase.map(Into::into);
        }
    }
    let fallback = session
        .cwd_raw
        .as_deref()
        .map(|cwd| {
            Path::new(cwd)
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_owned()
        })
        .unwrap_or_else(|| {
            let s = path
                .parent()
                .and_then(Path::file_name)
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .trim_matches('-');
            if s.is_empty() {
                stem.clone()
            } else {
                s.into()
            }
        });
    finish(
        &mut session,
        &timestamps,
        explicit
            .as_deref()
            .filter(|s| !s.is_empty())
            .unwrap_or(&first_text),
        &fallback,
    );
    session.skill_observations = skills.finish(session.skill_observations, &session.events);
    source_json.materialized(&session)?;
    Ok(session)
}
