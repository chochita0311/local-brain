//! Literal source evidence only: logged commands are tokenized and never run.
use super::source_json::SourceJson;
use super::{common::*, ParsedEvent, ParsedSkillObservation};
use regex::Regex;
use serde_json::Value;
use std::{
    collections::{BTreeSet, HashMap, HashSet},
    sync::LazyLock,
};
fn normalize(path: &str) -> String {
    let absolute = path.starts_with('/');
    let double = path.starts_with("//") && !path.starts_with("///");
    let mut parts = vec![];
    for s in path.split('/') {
        match s {
            "" | "." => {}
            ".." if parts.last().is_some_and(|s| *s != "..") => {
                parts.pop();
            }
            ".." if !absolute => parts.push(s),
            ".." => {}
            _ => parts.push(s),
        }
    }
    let prefix = if double {
        "//"
    } else if absolute {
        "/"
    } else {
        ""
    };
    let result = format!("{prefix}{}", parts.join("/"));
    if result.is_empty() {
        ".".into()
    } else {
        result
    }
}
fn basename(path: &str) -> &str {
    path.rsplit('/').next().unwrap_or("")
}
fn dirname(path: &str) -> &str {
    path.rsplit_once('/')
        .map(|(a, _)| if a.is_empty() { "/" } else { a })
        .unwrap_or("")
}
fn joined(path: &str, cwd: Option<&str>) -> String {
    if path.starts_with(['/', '~']) {
        normalize(path)
    } else if let Some(cwd) = cwd {
        normalize(&format!("{cwd}/{path}"))
    } else {
        normalize(path)
    }
}
fn shell(command: &str) -> Option<Vec<String>> {
    let chars = command.chars().collect::<Vec<_>>();
    let mut i = 0;
    let mut words = vec![];
    let mut word = String::new();
    let mut active = false;
    while i < chars.len() {
        let c = chars[i];
        if " \t\r".contains(c) {
            if active {
                words.push(std::mem::take(&mut word));
                active = false;
            }
            i += 1;
            continue;
        }
        if c == '#' {
            if active {
                words.push(std::mem::take(&mut word));
                active = false;
            }
            while i < chars.len() && chars[i] != '\n' {
                i += 1;
            }
            continue;
        }
        if ";&|()<>\n".contains(c) {
            if active {
                words.push(std::mem::take(&mut word));
                active = false;
            }
            let mut punct = c.to_string();
            i += 1;
            if c != '\n' {
                while i < chars.len() && ";&|()<>".contains(chars[i]) {
                    punct.push(chars[i]);
                    i += 1;
                }
            }
            words.push(punct);
            continue;
        }
        if c == '\'' || c == '"' {
            active = true;
            let quote = c;
            i += 1;
            let mut closed = false;
            while i < chars.len() {
                let c = chars[i];
                i += 1;
                if c == quote {
                    closed = true;
                    break;
                }
                if c == '\\' && quote == '"' {
                    let next = *chars.get(i)?;
                    i += 1;
                    if next != '"' && next != '\\' {
                        word.push('\\');
                    }
                    word.push(next);
                } else {
                    word.push(c);
                }
            }
            if !closed {
                return None;
            }
            continue;
        }
        if c == '\\' {
            i += 1;
            word.push(*chars.get(i)?);
            active = true;
            i += 1;
            continue;
        }
        if SHELL_WORDS.contains(c) {
            word.push(c);
            active = true;
            i += 1;
        } else {
            if active {
                words.push(std::mem::take(&mut word));
                active = false;
            }
            words.push(c.to_string());
            i += 1;
        }
    }
    if active {
        words.push(word);
    }
    Some(words)
}
fn segments(command: &str) -> Vec<Vec<String>> {
    let Some(tokens) = shell(command) else {
        return vec![];
    };
    if tokens
        .iter()
        .any(|s| ["<<", "<<-", "<<<"].contains(&s.as_str()))
    {
        return vec![];
    }
    let mut result = vec![vec![]];
    for token in tokens {
        if ["\n", ";", "&&", "||", "|", "(", ")"].contains(&token.as_str()) {
            result.push(vec![]);
        } else {
            result.last_mut().unwrap().push(token);
        }
    }
    result
}
fn read_paths(command: &str, cwd: Option<&str>) -> Vec<String> {
    let mut paths = vec![];
    for s in segments(command) {
        let Some(program) = s.first().map(|s| basename(s)) else {
            continue;
        };
        if !["cat", "sed", "head", "tail", "nl"].contains(&program)
            || s.iter().any(|s| s.contains('>'))
            || program == "sed"
                && s.iter()
                    .skip(1)
                    .any(|s| s.starts_with("-i") || s.starts_with("--in-place"))
        {
            continue;
        }
        for path in s.iter().skip(1) {
            if basename(path) == "SKILL.md" && !path.contains(['$', '`', '*', '?', '[', ']']) {
                let path = joined(path, cwd);
                if !paths.contains(&path) {
                    paths.push(path);
                }
            }
        }
    }
    paths
}
fn execution_paths(value: &Value, cwd: Option<&str>) -> Vec<String> {
    let parts = if let Some(array) = value.as_array() {
        let Some(args) = array
            .iter()
            .map(|v| v.as_str().map(ToOwned::to_owned))
            .collect::<Option<Vec<_>>>()
        else {
            return vec![];
        };
        if args.len() == 3
            && ["sh", "bash", "zsh"].contains(&basename(&args[0]))
            && ["-c", "-lc", "-ilc"].contains(&args[1].as_str())
        {
            return execution_paths(&Value::String(args[2].clone()), cwd);
        }
        vec![args]
    } else if let Some(s) = value.as_str() {
        segments(s)
    } else {
        return vec![];
    };
    let mut paths = vec![];
    static ASSIGN: LazyLock<Regex> =
        LazyLock::new(|| python_regex(r"^[A-Za-z_][A-Za-z0-9_]*=").unwrap());
    static PYTHON: LazyLock<Regex> = LazyLock::new(|| python_regex(r"^python3\.\d+$").unwrap());
    for mut args in parts {
        if args.is_empty()
            || args
                .iter()
                .any(|s| ["<", ">", "<<", ">>", "<<<"].contains(&s.as_str()))
        {
            continue;
        }
        if basename(&args[0]) == "env" {
            args.remove(0);
        }
        while args.first().is_some_and(|s| ASSIGN.is_match(s)) {
            args.remove(0);
        }
        if args.is_empty() {
            continue;
        }
        let executable = args.remove(0);
        let program = basename(&executable);
        let path = if [
            "python", "python3", "node", "bash", "sh", "zsh", "ruby", "perl",
        ]
        .contains(&program)
            || PYTHON.is_match(program)
        {
            while args
                .first()
                .is_some_and(|s| ["-B", "-u", "-I", "-E", "-s", "-S"].contains(&s.as_str()))
            {
                args.remove(0);
            }
            args.first().map(String::as_str)
        } else {
            Some(executable.as_str())
        };
        let Some(path) = path.filter(|s| {
            !s.starts_with('-') && s.contains('/') && !s.contains(['$', '`', '*', '?', '[', ']'])
        }) else {
            continue;
        };
        if !path.starts_with(['/', '~']) && cwd.is_none() {
            continue;
        }
        let path = joined(path, cwd);
        if path.contains("/scripts/") && !paths.contains(&path) {
            paths.push(path);
        }
    }
    paths
}
#[derive(Clone)]
struct Token {
    kind: &'static str,
    value: Option<String>,
}
fn js_tokens(source: &str) -> Vec<Token> {
    let chars = source.chars().collect::<Vec<_>>();
    let mut i = 0;
    let mut result = vec![];
    while i < chars.len() {
        let c = chars[i];
        if crate::backend::unicode::python_space(c) {
            i += 1;
            continue;
        }
        if c == '/' && chars.get(i + 1) == Some(&'/') {
            while i < chars.len() && chars[i] != '\n' {
                i += 1;
            }
            continue;
        }
        if c == '/' && chars.get(i + 1) == Some(&'*') {
            i += 2;
            while i + 1 < chars.len() && chars[i..i + 2] != ['*', '/'] {
                i += 1;
            }
            i = (i + 2).min(chars.len());
            continue;
        }
        if ['\'', '"', '`'].contains(&c) {
            let quote = c;
            i += 1;
            let mut text = String::new();
            let mut valid = true;
            while i < chars.len() && chars[i] != quote {
                let c = chars[i];
                if quote == '`' && c == '$' && chars.get(i + 1) == Some(&'{') {
                    valid = false;
                }
                if c == '\\' {
                    i += 1;
                    let Some(c) = chars.get(i).copied() else {
                        valid = false;
                        break;
                    };
                    if c == 'u' || c == 'x' {
                        let width = if c == 'u' { 4 } else { 2 };
                        if i + width < chars.len() {
                            let s = chars[i + 1..i + 1 + width].iter().collect::<String>();
                            if let Ok(n) = u32::from_str_radix(&s, 16) {
                                if let Some(ch) = char::from_u32(n) {
                                    text.push(ch);
                                    i += width + 1;
                                    continue;
                                }
                            }
                        }
                        valid = false;
                    } else if c != '\n' {
                        text.push(match c {
                            'n' => '\n',
                            'r' => '\r',
                            't' => '\t',
                            'b' => '\u{8}',
                            'f' => '\u{c}',
                            _ => c,
                        });
                    }
                } else {
                    text.push(c);
                }
                i += 1;
            }
            if i >= chars.len() {
                valid = false;
            }
            i += 1;
            result.push(Token {
                kind: "string",
                value: valid.then_some(text),
            });
            continue;
        }
        if c.is_ascii_alphabetic() || ['_', '$'].contains(&c) {
            let start = i;
            i += 1;
            while i < chars.len()
                && (crate::backend::unicode::python_alnum(chars[i])
                    || ['_', '$'].contains(&chars[i]))
            {
                i += 1;
            }
            result.push(Token {
                kind: "word",
                value: Some(chars[start..i].iter().collect()),
            });
        } else {
            i += 1;
            result.push(Token {
                kind: "symbol",
                value: Some(c.to_string()),
            });
        }
    }
    result
}
fn script_commands(source: &str) -> Vec<(String, Option<String>)> {
    let tokens = js_tokens(source);
    let mut result = vec![];
    for i in 0..tokens.len().saturating_sub(5) {
        if tokens[i].kind != "word"
            || tokens[i..i + 5].iter().map(|t| t.value.as_deref()).ne([
                Some("tools"),
                Some("."),
                Some("exec_command"),
                Some("("),
                Some("{"),
            ])
        {
            continue;
        }
        let mut fields = HashMap::new();
        let mut depth = 1;
        let mut j = i + 5;
        while j < tokens.len() && depth > 0 {
            let t = &tokens[j];
            let value = t.value.as_deref();
            if t.kind == "symbol" && matches!(value, Some("{" | "[" | "(")) {
                depth += 1;
            } else if t.kind == "symbol" && matches!(value, Some("}" | "]" | ")")) {
                depth -= 1;
            } else if depth == 1
                && matches!(value, Some("cmd" | "workdir"))
                && j + 3 < tokens.len()
                && tokens[j + 1].value.as_deref() == Some(":")
                && tokens[j + 2].kind == "string"
                && matches!(tokens[j + 3].value.as_deref(), Some("," | "}"))
            {
                fields.insert(value.unwrap().to_owned(), tokens[j + 2].value.clone());
            }
            j += 1;
        }
        if let Some(Some(command)) = fields.remove("cmd") {
            result.push((command, fields.remove("workdir").flatten()));
        }
    }
    result
}
fn call_paths(source: &SourceJson, tool: &str, args: &Value) -> Vec<String> {
    let tool = tool.rsplit('.').next().unwrap_or(tool);
    if args.as_str().is_some_and(|s| !s.contains("SKILL.md")) {
        return vec![];
    }
    if tool == "exec" {
        if let Some(s) = args.as_str() {
            return script_commands(s)
                .into_iter()
                .flat_map(|(command, cwd)| read_paths(&command, cwd.as_deref()))
                .collect();
        }
    }
    let args = if let Some(s) = args.as_str() {
        source.parse(s).unwrap_or(Value::Null)
    } else {
        args.clone()
    };
    if !args.is_object() {
        return vec![];
    }
    match tool {
        "Read" | "read_file" => first(&[&args["file_path"], &args["path"]])
            .as_str()
            .filter(|s| basename(s) == "SKILL.md")
            .map(|s| vec![normalize(s)])
            .unwrap_or_default(),
        "exec_command" | "Bash" => first(&[&args["cmd"], &args["command"]])
            .as_str()
            .map(|s| read_paths(s, args["workdir"].as_str()))
            .unwrap_or_default(),
        _ => vec![],
    }
}
fn successful(
    source: &SourceJson,
    value: &Value,
    direct: bool,
    depth: usize,
    output: &mut Vec<String>,
) {
    if depth > 12 {
        return;
    }
    if let Some(s) = value.as_str() {
        static EXIT: LazyLock<Regex> =
            LazyLock::new(|| python_regex(r"Process exited with code (-?\d+)\b").unwrap());
        if EXIT.captures_iter(s).any(|c| &c[1] != "0") {
            return;
        }
        if let Ok(v) = source.parse(s) {
            if v.is_object() || v.is_array() {
                successful(source, &v, direct, depth + 1, output);
                return;
            }
        }
        if direct || EXIT.captures_iter(s).any(|c| &c[1] == "0") {
            output.push(s.into());
        }
        return;
    }
    if let Some(array) = value.as_array() {
        let complete = array.iter().any(|v| {
            v.is_object()
                && source
                    .python_string(v.get("text").unwrap_or(&Value::String(String::new())))
                    .starts_with("Script completed")
        });
        for child in array {
            successful(source, child, direct || complete, depth + 1, output);
        }
        return;
    }
    if !value.is_object() || truth(&value["is_error"]) || truth(&value["isError"]) {
        return;
    }
    if let Some(code) = value.get("exit_code") {
        if (code == 0 || code == false) && value["output"].is_string() {
            output.push(value["output"].as_str().unwrap().into());
        }
        return;
    }
    if value["success"] == false
        || value["status"]
            .as_str()
            .is_some_and(|s| ["failed", "failure", "error", "cancelled", "rejected"].contains(&s))
        || truth(&value["error"])
    {
        return;
    }
    for key in ["content", "text", "result", "value", "output"] {
        if let Some(v) = value.get(key) {
            successful(source, v, direct, depth + 1, output);
        }
    }
}
fn skill_names(text: &str) -> BTreeSet<String> {
    static LINE: LazyLock<Regex> =
        LazyLock::new(|| python_regex(r"(?m)^\s*\d+(?:→|\s+)\s?").unwrap());
    static DELIMITER: LazyLock<Regex> = LazyLock::new(|| python_regex(r"(?m)^---[ \t]*$").unwrap());
    let text = LINE.replace_all(text, "");
    let mut names = BTreeSet::new();
    let delimiters = DELIMITER.find_iter(&text).collect::<Vec<_>>();
    let mut index = 0;
    while index < delimiters.len() {
        let opening = delimiters[index];
        let mut closing = None;
        if text.as_bytes().get(opening.end()) == Some(&b'\n') {
            let start = opening.end() + 1;
            for (next, delimiter) in delimiters.iter().enumerate().skip(index + 1) {
                let count = text[start..delimiter.start()].chars().count();
                if count > 16000 {
                    break;
                }
                if count > 0 {
                    closing = Some((next, &text[start..delimiter.start()]));
                    break;
                }
            }
        }
        let Some((next, block)) = closing else {
            index += 1;
            continue;
        };
        index = next + 1;
        if let Ok(metadata) = crate::backend::yaml::safe_load(block) {
            if let Some(name) = metadata.get("name").and_then(|v| v.as_str()) {
                if !name.py_trim().is_empty()
                    && name.py_trim().chars().count() <= 160
                    && !name.chars().any(|c| (c as u32) < 32)
                {
                    names.insert(name.py_trim().into());
                }
            }
        }
    }
    names
}
#[derive(Clone)]
struct Pending {
    tool: String,
    paths: Vec<String>,
    scripts: Vec<String>,
    line: i64,
    time: Option<String>,
}
pub(super) struct Collector {
    source: SourceJson,
    provider: String,
    pending: HashMap<String, Pending>,
    reads: Vec<ParsedSkillObservation>,
    requests: Vec<(i64, String)>,
    event_requests: HashMap<String, String>,
    message_ids: HashMap<i64, String>,
    message_requests: HashMap<i64, String>,
    executions: Vec<(String, Vec<String>, i64, Option<String>)>,
    cwd: Option<String>,
}
impl Collector {
    pub fn new(provider: &str, source: SourceJson) -> Self {
        Self {
            source,
            provider: provider.into(),
            pending: HashMap::new(),
            reads: vec![],
            requests: vec![],
            event_requests: HashMap::new(),
            message_ids: HashMap::new(),
            message_requests: HashMap::new(),
            executions: vec![],
            cwd: None,
        }
    }
    fn call(&mut self, tool: &Value, id: &Value, args: &Value, line: i64, time: Option<String>) {
        let (Some(tool), Some(id)) = (
            tool.as_str(),
            id.as_str().filter(|s| !s.py_trim().is_empty()),
        ) else {
            return;
        };
        let paths = call_paths(&self.source, tool, args);
        let scripts = if self.provider == "claude" && tool == "Bash" && args.is_object() {
            execution_paths(
                &args["command"],
                args["workdir"].as_str().or(self.cwd.as_deref()),
            )
        } else {
            vec![]
        };
        if !paths.is_empty() || !scripts.is_empty() {
            self.pending.insert(
                id.into(),
                Pending {
                    tool: tool.into(),
                    paths,
                    scripts,
                    line,
                    time,
                },
            );
        }
    }
    fn result(&mut self, id: &Value, value: &Value) {
        let Some(id) = id.as_str() else {
            return;
        };
        let Some(call) = self.pending.get(id) else {
            return;
        };
        if !call.scripts.is_empty() {
            self.executions.push((
                id.into(),
                call.scripts.clone(),
                call.line,
                call.time.clone(),
            ));
        }
        let direct = ["Read", "read_file"].contains(&call.tool.rsplit('.').next().unwrap_or(""));
        let mut output = vec![];
        successful(&self.source, value, direct, 0, &mut output);
        let names = output
            .iter()
            .flat_map(|s| skill_names(s))
            .collect::<BTreeSet<_>>();
        for path in &call.paths {
            let parent = crate::backend::unicode::casefold(basename(dirname(path)));
            for name in &names {
                if parent
                    != crate::backend::unicode::casefold(name.rsplit(':').next().unwrap_or(name))
                {
                    continue;
                }
                self.reads.push(ParsedSkillObservation {
                    native_event_id: id.into(),
                    skill_name: name.clone(),
                    signal_kind: format!("{}_skill_read", self.provider),
                    source_line: call.line,
                    occurred_at: call.time.clone(),
                    skill_locator: Some(path.clone()),
                    request_key: None,
                });
            }
        }
    }
    pub fn observe(&mut self, record: &Value, line: i64) {
        let time = string(&record["timestamp"]);
        if self.provider == "codex" {
            let payload = &record["payload"];
            if !payload.is_object() {
                return;
            }
            if let Some(cwd) = payload["cwd"].as_str() {
                self.cwd = Some(cwd.into());
            }
            if record["type"] == "turn_context"
                || record["type"] == "event_msg" && payload["type"] == "task_started"
            {
                if let Some(turn) = payload["turn_id"].as_str().filter(|s| !s.is_empty()) {
                    self.requests
                        .push((line, stable_id(&["skill-request", "codex", turn])));
                }
            }
            if record["type"] == "event_msg" {
                if matches!(
                    payload["type"].as_str(),
                    Some("user_message" | "agent_message")
                ) {
                    self.message_ids.insert(line, native_event_id(payload, ""));
                }
                let item = &payload["item"];
                if payload["type"] == "item_completed"
                    && item["type"] == "CommandExecution"
                    && matches!(item["status"].as_str(), Some("completed" | "failed"))
                    && (item["exit_code"].is_i64()
                        || item["exit_code"].is_u64()
                        || item["exit_code"].is_boolean())
                {
                    if let Some(id) = item["id"].as_str().filter(|s| !s.is_empty()) {
                        let paths = execution_paths(
                            &item["command"],
                            item["cwd"].as_str().or(self.cwd.as_deref()),
                        );
                        if !paths.is_empty() {
                            self.executions.push((id.into(), paths, line, time.clone()));
                        }
                    }
                }
            }
            if record["type"] != "response_item" {
                return;
            }
            let id = first(&[&payload["call_id"], &payload["id"]]);
            let turn = payload["internal_chat_message_metadata_passthrough"]["turn_id"]
                .as_str()
                .filter(|s| !s.is_empty());
            if let (Some(id), Some(turn)) = (id.as_str(), turn) {
                self.event_requests
                    .insert(id.into(), stable_id(&["skill-request", "codex", turn]));
            }
            if payload["type"] == "message"
                && matches!(payload["role"].as_str(), Some("user" | "assistant"))
            {
                self.message_ids.insert(line, native_event_id(payload, ""));
                if let Some(turn) = turn {
                    self.message_requests
                        .insert(line, stable_id(&["skill-request", "codex", turn]));
                }
            }
            match payload["type"].as_str() {
                Some("function_call" | "custom_tool_call") => self.call(
                    &payload["name"],
                    id,
                    first(&[&payload["arguments"], &payload["input"]]),
                    line,
                    time,
                ),
                Some("function_call_output" | "custom_tool_call_output") => {
                    self.result(id, &payload["output"])
                }
                _ => {}
            }
        } else if !truth(&record["isMeta"]) {
            if let Some(cwd) = record["cwd"].as_str() {
                self.cwd = Some(cwd.into());
            }
            if matches!(record["type"].as_str(), Some("user" | "assistant")) {
                self.message_ids.insert(line, native_event_id(record, ""));
            }
            let content = &record["message"]["content"];
            let items = content.as_array().map(Vec::as_slice).unwrap_or(&[]);
            let is_result = truth(&record["sourceToolAssistantUUID"])
                || record.get("toolUseResult").is_some()
                || items.iter().any(|v| v["type"] == "tool_result");
            if record["type"] == "user" && !is_result {
                if let Some(id) = record["uuid"].as_str().filter(|s| !s.is_empty()) {
                    self.requests
                        .push((line, stable_id(&["skill-request", "claude", id])));
                }
            }
            for item in items {
                if record["type"] == "assistant" && item["type"] == "tool_use" {
                    self.call(
                        &item["name"],
                        &item["id"],
                        &item["input"],
                        line,
                        time.clone(),
                    );
                } else if record["type"] == "user"
                    && item["type"] == "tool_result"
                    && !truth(&item["is_error"])
                {
                    self.result(&item["tool_use_id"], &item["content"]);
                }
            }
        }
    }
    pub fn finish(
        self,
        explicit: Vec<ParsedSkillObservation>,
        events: &[ParsedEvent],
    ) -> Vec<ParsedSkillObservation> {
        let user_requests = events
            .iter()
            .filter(|e| e.event_type == "message" && e.role.as_deref() == Some("user"))
            .map(|e| {
                (
                    e.source_line,
                    stable_id(&["skill-request", &self.provider, &e.event_id]),
                )
            })
            .collect::<Vec<_>>();
        let mut requests = if self.provider == "claude" {
            let native = self.requests.iter().cloned().collect::<HashMap<_, _>>();
            user_requests
                .into_iter()
                .map(|(line, key)| (line, native.get(&line).cloned().unwrap_or(key)))
                .collect()
        } else if self.requests.is_empty() {
            user_requests
        } else {
            self.requests.clone()
        };
        requests.sort();
        let request = |line: i64| {
            requests
                .iter()
                .rev()
                .find(|(n, _)| *n <= line)
                .map(|(_, key)| key.clone())
        };
        let locators = explicit
            .iter()
            .filter_map(|s| {
                s.skill_locator
                    .as_deref()
                    .map(|p| (normalize(p), s.skill_name.clone()))
            })
            .collect::<HashMap<_, _>>();
        let mut output = explicit;
        output.extend(self.reads);
        output.sort_by_key(|s| s.source_line);
        for item in &mut output {
            item.request_key = self
                .event_requests
                .get(&item.native_event_id)
                .cloned()
                .or_else(|| request(item.source_line));
            if item.request_key.is_none()
                && !self.requests.is_empty()
                && item.signal_kind == "codex_skill_context"
            {
                item.request_key = requests.first().map(|(_, k)| k.clone());
            }
            if item.signal_kind.ends_with("_read") {
                if let Some(name) = item.skill_locator.as_ref().and_then(|p| locators.get(p)) {
                    item.skill_name = name.clone();
                }
            }
        }
        let mut known = HashMap::new();
        let mut known_order = Vec::new();
        for item in &output {
            if !known.contains_key(&item.skill_name) {
                known_order.push(item.skill_name.clone());
            }
            if item.skill_locator.is_some() || !known.contains_key(&item.skill_name) {
                known.insert(item.skill_name.clone(), item.skill_locator.clone());
            }
        }
        let mut aliases: HashMap<String, HashSet<String>> = HashMap::new();
        let mut canonical = HashMap::new();
        for name in &known_order {
            canonical
                .entry(crate::backend::unicode::casefold(name))
                .or_insert(name.clone());
        }
        for name in canonical.values() {
            aliases
                .entry(crate::backend::unicode::casefold(name))
                .or_default()
                .insert(name.clone());
            if let Some((_, tail)) = name.rsplit_once(':') {
                aliases
                    .entry(crate::backend::unicode::casefold(tail))
                    .or_default()
                    .insert(name.clone());
            }
        }
        let mut aliases = aliases
            .into_iter()
            .filter_map(|(alias, names)| {
                (names.len() == 1).then(|| (alias, names.into_iter().next().unwrap()))
            })
            .collect::<Vec<_>>();
        aliases.sort_by_key(|(alias, _)| std::cmp::Reverse(alias.chars().count()));
        let boundary = |c: char| c.is_ascii_alphanumeric() || "_:/-".contains(c);
        for event in events {
            if event.event_type != "message"
                || !matches!(event.role.as_deref(), Some("user" | "assistant"))
            {
                continue;
            }
            let Some(text) = event.text.as_deref().filter(|s| !s.is_empty()) else {
                continue;
            };
            if [
                "# AGENTS.md instructions for ",
                "<environment_context>",
                "<skills_instructions>",
            ]
            .iter()
            .any(|prefix| text.py_trim().starts_with(prefix))
            {
                continue;
            }
            let text = crate::backend::unicode::casefold(text);
            let mut names = BTreeSet::new();
            let mut index = 0;
            while index < text.len() {
                let mut found = None;
                if !text[..index].chars().next_back().is_some_and(boundary) {
                    let starts = if text[index..].starts_with('$') {
                        vec![index + 1, index]
                    } else {
                        vec![index]
                    };
                    for start in starts {
                        for (alias, name) in &aliases {
                            if text[start..].starts_with(alias) {
                                let end = start + alias.len();
                                if !text[end..].chars().next().is_some_and(boundary) {
                                    found = Some((end, name));
                                    break;
                                }
                            }
                        }
                        if found.is_some() {
                            break;
                        }
                    }
                }
                if let Some((end, name)) = found {
                    names.insert(name.clone());
                    index = end;
                } else {
                    index += text[index..].chars().next().unwrap().len_utf8();
                }
            }
            for name in names {
                output.push(ParsedSkillObservation {
                    native_event_id: format!(
                        "mention:{}",
                        self.message_ids
                            .get(&event.source_line)
                            .filter(|s| !s.is_empty())
                            .unwrap_or(&event.event_id)
                    ),
                    skill_name: name.clone(),
                    signal_kind: format!("{}_skill_mention", self.provider),
                    source_line: event.source_line,
                    occurred_at: event.occurred_at.clone(),
                    skill_locator: known[&name].clone(),
                    request_key: self
                        .message_requests
                        .get(&event.source_line)
                        .cloned()
                        .or_else(|| request(event.source_line)),
                });
            }
        }
        let roots = output
            .iter()
            .filter_map(|o| {
                o.skill_locator
                    .as_deref()
                    .filter(|p| basename(p) == "SKILL.md")
                    .map(|p| (dirname(p).to_owned(), o.skill_name.clone()))
            })
            .collect::<HashMap<_, _>>();
        for (id, paths, line, time) in self.executions {
            for (root, name) in &roots {
                if paths
                    .iter()
                    .any(|p| p.starts_with(&format!("{root}/scripts/")))
                {
                    output.push(ParsedSkillObservation {
                        native_event_id: format!("script:{id}"),
                        skill_name: name.clone(),
                        signal_kind: format!("{}_skill_script", self.provider),
                        source_line: line,
                        occurred_at: time.clone(),
                        skill_locator: known[name].clone(),
                        request_key: request(line),
                    });
                }
            }
        }
        output
            .sort_by(|a, b| (&a.source_line, &a.skill_name).cmp(&(&b.source_line, &b.skill_name)));
        output
    }
}

const SHELL_WORDS:&str="abcdfeghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ~-./*?=$`";
