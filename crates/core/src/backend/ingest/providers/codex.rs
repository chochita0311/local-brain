use super::super::source_json::SourceJson;
use super::super::{
    common::*, evidence, skills, ApprovedResourceCall, ParsedSession, ParsedSkillObservation,
    ScanControl,
};
use super::usage;
use crate::backend::{BackendError, Result};
use serde_json::Value;
use std::{
    collections::{HashMap, HashSet},
    fs,
    io::Read,
    path::Path,
};

fn unique_json(source: &SourceJson, text: &str) -> Option<Value> {
    source.parse_unique(text).ok()
}
fn generated(source: &SourceJson, text: &str) -> bool {
    let v = text.py_trim();
    if let Some(body) = v
        .strip_prefix("<external_codex_apps_open_page>")
        .and_then(|s| s.strip_suffix("</external_codex_apps_open_page>"))
    {
        return unique_json(source, body) == Some(serde_json::json!({"page_id":null}));
    }
    let header = v.split('\n').next().unwrap_or("").py_trim_end();
    v.starts_with(
        "<recommended_plugins>\nHere is a list of plugins that are available but not installed.",
    ) && v.ends_with("</recommended_plugins>")
        || v.starts_with("<codex_internal_context source=\"daemon_recovery\">\n")
            && v.ends_with("</codex_internal_context>")
        || v.starts_with("<turn_aborted>\nThe user interrupted the previous turn")
            && v.ends_with("</turn_aborted>")
        || v.starts_with("<skill>\n<name>") && v.contains("\n<path>") && v.ends_with("\n</skill>")
        || (header == "# AGENTS.md instructions"
            || header.starts_with("# AGENTS.md instructions for "))
            && v.contains("\n<INSTRUCTIONS>")
            && v.contains("\n</INSTRUCTIONS>")
        || v.starts_with("<environment_context>") && v.ends_with("</environment_context>")
}
fn user_text(source: &SourceJson, text: &str) -> String {
    if generated(source, text) {
        return String::new();
    }
    let v = text.py_trim();
    let Some(body) = v
        .strip_prefix("<send_user_message_question_reply>")
        .and_then(|s| s.strip_suffix("</send_user_message_question_reply>"))
    else {
        return v.into();
    };
    let Some(replies) =
        unique_json(source, body).filter(|v| v.as_array().is_some_and(|v| !v.is_empty()))
    else {
        return v.into();
    };
    let mut parts = vec![];
    for reply in replies.as_array().unwrap() {
        let Some(map) = reply.as_object().filter(|map| {
            map.keys()
                .all(|s| ["answer", "question", "questionItemId"].contains(&s.as_str()))
        }) else {
            return v.into();
        };
        let Some(answer) = nonempty(&reply["answer"]) else {
            return v.into();
        };
        let question = match map.get("question") {
            None => "",
            Some(question_value) => match question_value.as_str() {
                Some(s) => s,
                None => return v.into(),
            },
        };
        if !question.py_trim().is_empty() {
            parts.push(
                crate::backend::unicode::splitlines(question.py_trim())
                    .into_iter()
                    .map(|s| format!("> {s}"))
                    .collect::<Vec<_>>()
                    .join("\n"),
            );
        }
        parts.push(answer);
    }
    parts.join("\n\n")
}
fn user_content(source: &SourceJson, value: &Value) -> String {
    if let Some(s) = value.as_str() {
        return user_text(source, s);
    }
    value
        .as_array()
        .map(|items| {
            items
                .iter()
                .map(|item| text_from_content(&Value::Array(vec![item.clone()])))
                .filter(|s| !s.is_empty())
                .map(|s| user_text(source, &s))
                .filter(|s| !s.is_empty())
                .collect::<Vec<_>>()
                .join("\n\n")
        })
        .unwrap_or_default()
}
fn loaded_skill(text: &str) -> Option<(String, String)> {
    let v = text.py_trim();
    if !v.starts_with("<skill>\n<name>") || !v.ends_with("\n</skill>") {
        return None;
    }
    let lines = crate::backend::unicode::splitlines(v);
    if lines.len() < 4 {
        return None;
    }
    let name = lines[1]
        .strip_prefix("<name>")?
        .strip_suffix("</name>")?
        .py_trim();
    let path = lines[2]
        .strip_prefix("<path>")?
        .strip_suffix("</path>")?
        .py_trim();
    (!name.is_empty()
        && !path.is_empty()
        && name.chars().count() <= 160
        && path.chars().count() <= 4096)
        .then_some((name.into(), path.into()))
}
fn phase(value: &Value, role: &str) -> Option<String> {
    (role == "assistant")
        .then(|| {
            value["phase"]
                .as_str()
                .filter(|s| ["commentary", "final_answer"].contains(s))
                .map(Into::into)
        })
        .flatten()
}
fn append(
    session: &mut ParsedSession,
    line: i64,
    time: Option<String>,
    payload: &Value,
    role: &str,
    text: &str,
) -> Option<usize> {
    let text = text.py_trim();
    if text.is_empty() {
        return None;
    }
    let mut event = message(
        "codex",
        &session.external_id,
        line,
        role,
        time.clone(),
        text.into(),
    );
    event.message_phase = phase(payload, role);
    let id = native_event_id(payload, &event.event_id);
    evidence::visible(session, text, role, line, &id, &id, time.as_deref());
    let index = session.events.len();
    session.events.push(event);
    Some(index)
}
fn tier(path: &Path) -> Result<(String, String)> {
    let root = path
        .ancestors()
        .skip(1)
        .find(|p| {
            p.file_name()
                .and_then(|s| s.to_str())
                .is_some_and(|s| ["sessions", "archived_sessions"].contains(&s))
        })
        .and_then(Path::parent)
        .or_else(|| path.parent())
        .unwrap_or(Path::new("."));
    let bytes = match fs::read(root.join("config.toml")) {
        Ok(v) => v,
        Err(_) => return Ok(("standard".into(), "unmarked_default_assumption".into())),
    };
    let text = std::str::from_utf8(&bytes).map_err(|_| {
        BackendError::invalid("source_unicode", "Codex configuration is not valid UTF-8")
    })?;
    let raw = match crate::preferences::decode_toml_exchange(text) {
        Ok(v) => v,
        Err(_) => return Ok(("standard".into(), "unmarked_default_assumption".into())),
    };
    let value = raw["nodes"][0]["value"]
        .as_array()
        .and_then(|entries| entries.iter().find(|e| e[0] == "service_tier"))
        .and_then(|e| e[1].as_u64())
        .map(|id| &raw["nodes"][id as usize])
        .filter(|n| n["kind"] == "string")
        .and_then(|n| n["value"].as_str());
    Ok(match value {
        Some("priority" | "fast") => ("fast".into(), "config_fallback".into()),
        Some("default" | "standard") => ("standard".into(), "config_fallback".into()),
        _ => ("standard".into(), "unmarked_default_assumption".into()),
    })
}
fn replay_second(path: &Path) -> Result<Option<String>> {
    let mut header = vec![];
    match open_jsonl(path) {
        Ok(reader) => {
            reader.take(16 * 1024).read_to_end(&mut header)?;
        }
        Err(_) => return Ok(None),
    };
    if !header
        .windows(b"thread_spawn".len())
        .any(|w| w == b"thread_spawn")
        && !header
            .windows(b"forked_from_id".len())
            .any(|w| w == b"forked_from_id")
    {
        return Ok(None);
    }
    let mut first = None;
    for line in JsonLines::new(path)? {
        let (_, record) = line?;
        let Some(record) = record else {
            continue;
        };
        let payload = &record["payload"];
        let info = &payload["info"];
        if record["type"] != "event_msg"
            || payload["type"] != "token_count"
            || !info.is_object()
            || !(info["last_token_usage"].is_object() || info["total_token_usage"].is_object())
        {
            continue;
        }
        let Some(t) = record["timestamp"]
            .as_str()
            .filter(|s| s.chars().count() >= 19)
        else {
            continue;
        };
        let second = t.chars().take(19).collect::<String>();
        if let Some(first) = first {
            return Ok((first == second).then_some(first));
        }
        first = Some(second);
    }
    Ok(None)
}
struct Response {
    line: i64,
    time: Option<String>,
    payload: Value,
    role: String,
    text: String,
    turn: Option<String>,
}
pub(super) fn parse(path: &Path, control: &ScanControl) -> Result<ParsedSession> {
    let file = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
    let stem = if let Some(s) = file.strip_suffix(".jsonl.zst") {
        s.to_owned()
    } else {
        path.file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .into()
    };
    let mut session = ParsedSession::empty(path, stem.clone());
    let mut times = vec![];
    let mut seen_meta = false;
    let mut guardian = false;
    let mut primary_start = None;
    let mut turn = None;
    let mut model = None;
    let mut previous = HashMap::new();
    let mut responses = vec![];
    let mut event_turns = HashSet::new();
    let mut legacy: HashMap<(Option<String>, String), Vec<usize>> = HashMap::new();
    let mut hints: HashMap<usize, HashSet<String>> = HashMap::new();
    let mut texts: HashMap<(String, String), HashSet<Option<String>>> = HashMap::new();
    let replay = replay_second(path)?;
    let mut skip_replay = replay.is_some();
    let (fallback_tier, fallback_source) = tier(path)?;
    let mut current_tier = fallback_tier.clone();
    let mut tier_source = fallback_source.clone();
    let mut usages = HashMap::new();
    let mut calls: HashMap<String, ApprovedResourceCall> = HashMap::new();
    let lines = JsonLines::new(path)?;
    let source_json = lines.source();
    let mut skills = skills::Collector::new("codex", source_json.clone());
    for line in lines {
        control.check()?;
        let (line, record) = line?;
        let Some(record) = record.filter(Value::is_object) else {
            session.skipped_lines += 1;
            continue;
        };
        skills.observe(&record, line);
        let time = string(&record["timestamp"]);
        if let Some(t) = &time {
            times.push(t.clone());
        }
        let kind = record["type"].as_str().unwrap_or("");
        let payload = &record["payload"];
        if !payload.is_object() {
            continue;
        }
        if kind == "session_meta" {
            if !seen_meta {
                let external = first(&[&payload["id"], &payload["session_id"]]);
                if truth(external) {
                    session.external_id = source_json.python_string(external);
                }
                if truth(&payload["cwd"]) {
                    session.cwd_raw = Some(
                        payload["cwd"]
                            .as_str()
                            .ok_or_else(|| {
                                BackendError::invalid("source_path", "Native cwd must be a string")
                            })?
                            .into(),
                    );
                }
                session.git_branch = nonempty(&payload["git"]["branch"]);
                let source = &payload["source"];
                let sub = &source["subagent"];
                guardian = sub["other"]
                    .as_str()
                    .is_some_and(|s| s.py_trim().eq_ignore_ascii_case("guardian"));
                let mut parent = first(&[&payload["parent_thread_id"], &payload["forked_from_id"]]);
                if !truth(parent) && sub.is_object() {
                    parent = first(&[
                        &sub["parent_thread_id"],
                        &sub["parent_id"],
                        &sub["thread_id"],
                    ]);
                }
                if !parent.is_null() {
                    let s = source_json.python_string(parent).py_trim().to_owned();
                    session.parent_external_id = (!s.is_empty()).then_some(s);
                }
                let marked = !sub.is_null() && sub != false && sub != ""
                    || source
                        .as_str()
                        .is_some_and(|s| s.eq_ignore_ascii_case("subagent"));
                if marked || session.parent_external_id.is_some() {
                    session.session_role = "subsession".into();
                }
                primary_start = time.clone();
                seen_meta = true;
            }
            continue;
        }
        if kind == "thread_settings_applied"
            || kind == "event_msg" && payload["type"] == "thread_settings_applied"
        {
            let settings = &payload["thread_settings"];
            if let Some(value) = nonempty(&settings["model"]) {
                model = Some(value);
            }
            match settings["service_tier"].as_str() {
                Some("priority" | "fast") => {
                    current_tier = "fast".into();
                    tier_source = "thread_settings_applied".into();
                }
                Some("default" | "standard") => {
                    current_tier = "standard".into();
                    tier_source = "thread_settings_applied".into();
                }
                _ => {
                    current_tier = fallback_tier.clone();
                    tier_source = "config_after_unmarked_setting".into();
                }
            }
            continue;
        }
        if kind == "turn_context" {
            if session.cwd_raw.is_none() && truth(&payload["cwd"]) {
                session.cwd_raw = Some(
                    payload["cwd"]
                        .as_str()
                        .ok_or_else(|| {
                            BackendError::invalid("source_path", "Native cwd must be a string")
                        })?
                        .into(),
                );
            }
            turn =
                truth(&payload["turn_id"]).then(|| source_json.python_string(&payload["turn_id"]));
            model = nonempty(&payload["model"]);
            continue;
        }
        if kind == "event_msg" {
            let payload_kind = payload["type"].as_str().unwrap_or("");
            if payload_kind == "token_count" {
                if skip_replay {
                    let second = time
                        .as_ref()
                        .map(|s| s.chars().take(19).collect::<String>());
                    if second == replay {
                        usage::update_previous(&mut previous, payload);
                        continue;
                    }
                    skip_replay = false;
                }
                if let Some(value) =
                    usage::model(payload).or_else(|| usage::model(&payload["info"]))
                {
                    model = Some(value);
                }
                if let Some(record) = usage::codex(
                    &session.external_id,
                    line,
                    time.clone(),
                    payload,
                    turn.as_deref(),
                    model.clone(),
                    &previous,
                    &current_tier,
                    &tier_source,
                )? {
                    let key = record.source_record_id.clone();
                    if let Some(index) = usages.get(&key).copied() {
                        session.usage_records[index] = record;
                    } else {
                        usages.insert(key, session.usage_records.len());
                        session.usage_records.push(record);
                    }
                }
                usage::update_previous(&mut previous, payload);
                continue;
            }
            let role = match payload_kind {
                "user_message" => "user",
                "agent_message" => "assistant",
                _ => continue,
            };
            if let Some(text) = payload["message"]
                .as_str()
                .filter(|s| !s.py_trim().is_empty())
            {
                let text = if role == "user" {
                    user_text(&source_json, text)
                } else {
                    text.into()
                };
                if text.is_empty() {
                    continue;
                }
                event_turns.insert((role.to_owned(), turn.clone()));
                texts
                    .entry((role.into(), text.py_trim().into()))
                    .or_default()
                    .insert(turn.clone());
                if let Some(index) = append(&mut session, line, time.clone(), payload, role, &text)
                {
                    if role == "assistant" {
                        legacy
                            .entry((turn.clone(), text.py_trim().into()))
                            .or_default()
                            .push(index);
                    }
                }
            }
            continue;
        }
        if kind != "response_item" {
            continue;
        }
        match payload["type"].as_str() {
            Some("message") => {
                let Some(role) = payload["role"]
                    .as_str()
                    .filter(|s| ["user", "assistant"].contains(s))
                else {
                    continue;
                };
                let text = text_from_content(&payload["content"]);
                if text.is_empty() {
                    continue;
                }
                if role == "user" {
                    if let (Some((name, path)), Some(id)) =
                        (loaded_skill(&text), nonempty(&payload["id"]))
                    {
                        session.skill_observations.push(ParsedSkillObservation {
                            native_event_id: id,
                            skill_name: name,
                            signal_kind: "codex_skill_context".into(),
                            source_line: line,
                            occurred_at: time.clone(),
                            skill_locator: Some(path),
                            request_key: None,
                        });
                    }
                }
                let text = if role == "user" {
                    user_content(&source_json, &payload["content"])
                } else {
                    text
                };
                if text.is_empty() {
                    continue;
                }
                let value = &payload["internal_chat_message_metadata_passthrough"]["turn_id"];
                let response_turn = if truth(value) {
                    Some(source_json.python_string(value))
                } else {
                    turn.clone()
                };
                responses.push(Response {
                    line,
                    time,
                    payload: payload.clone(),
                    role: role.into(),
                    text,
                    turn: response_turn,
                });
            }
            Some("function_call_output" | "custom_tool_call_output") => {
                let id = first(&[&payload["call_id"], &payload["id"]]);
                if let Some(call) = id.as_str().and_then(|id| calls.get(id)) {
                    let fallback = stable_id(&[
                        "codex",
                        &session.external_id,
                        &line.to_string(),
                        "approved-tool-result",
                    ]);
                    let event = native_event_id(payload, &fallback);
                    evidence::tool_result(
                        &source_json,
                        &mut session,
                        call,
                        &payload["output"],
                        evidence::failed(&source_json, &[payload, &payload["output"]]),
                        line,
                        &event,
                        time.as_deref(),
                    );
                }
            }
            Some("function_call" | "custom_tool_call") => {
                if let Some(name) = payload["name"].as_str() {
                    let id = first(&[&payload["call_id"], &payload["id"]]);
                    if let Some(id) = id.as_str() {
                        if let Some(call) = evidence::approved(
                            &source_json,
                            name,
                            id,
                            first(&[&payload["arguments"], &payload["input"]]),
                        ) {
                            calls.insert(id.into(), call);
                        }
                    }
                    session.events.push(tool(
                        "codex",
                        &session.external_id,
                        line,
                        None,
                        time,
                        name.into(),
                    ));
                }
            }
            _ => {}
        }
    }
    for response in responses {
        let key = (response.role.clone(), response.text.py_trim().to_owned());
        let legacy_turns = texts.get(&key);
        let duplicate = response.role == "assistant"
            && response.turn.is_some()
            && event_turns.contains(&(response.role.clone(), response.turn.clone()))
            || legacy_turns.is_some_and(|turns| {
                !turns.is_empty()
                    && (response.turn.is_none()
                        || turns.contains(&None)
                        || turns.contains(&response.turn))
            });
        if duplicate {
            if let Some(phase) = phase(&response.payload, &response.role) {
                let text = response.text.py_trim();
                let matches = if response.turn.is_some() {
                    let matches = legacy.get(&(response.turn.clone(), text.into()));
                    matches
                        .filter(|v| !v.is_empty())
                        .or_else(|| legacy.get(&(None, text.into())))
                        .cloned()
                        .unwrap_or_default()
                } else {
                    legacy
                        .iter()
                        .filter(|((_, s), _)| s == text)
                        .flat_map(|(_, v)| v.iter().copied())
                        .collect()
                };
                if matches.len() == 1 {
                    hints.entry(matches[0]).or_default().insert(phase);
                }
            }
            continue;
        }
        append(
            &mut session,
            response.line,
            response.time,
            &response.payload,
            &response.role,
            &response.text,
        );
    }
    for (index, phases) in hints {
        if session.events[index].message_phase.is_none() && phases.len() == 1 {
            session.events[index].message_phase = phases.into_iter().next();
        }
    }
    session.events.sort_by(|a, b| {
        (&a.sequence, &a.source_line, &a.event_id).cmp(&(&b.sequence, &b.source_line, &b.event_id))
    });
    let first = session
        .events
        .iter()
        .find(|e| {
            e.event_type == "message"
                && e.role.as_deref() == Some("user")
                && e.text.as_deref().is_some_and(|s| !s.is_empty())
        })
        .and_then(|e| e.text.clone())
        .unwrap_or_default();
    finish(&mut session, &times, &first, &stem);
    session.started_at = primary_start.or(session.started_at);
    if guardian {
        session.session_class = "maintenance".into();
        session.index_policy = "metadata_only".into();
        session.maintenance_run_id = None;
        session.title = "Codex guardian".into();
    }
    session.skill_observations = skills.finish(session.skill_observations, &session.events);
    source_json.materialized(&session)?;
    Ok(session)
}
