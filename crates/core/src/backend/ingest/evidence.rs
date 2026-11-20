use super::common::python_regex;
use super::common::truth;
use super::common::PythonText;
use super::source_json::SourceJson;
use super::{ApprovedResourceCall, ParsedReferenceCandidate, ParsedSession, ParsedUrlEvidence};
use crate::backend::references::trim_url_token;
use regex::Regex;
use serde_json::Value;
use std::{collections::HashSet, sync::LazyLock};
pub const REFERENCE_VERSION: &str = "localbrain.session-reference.v4";
pub const URL_EVIDENCE_VERSION: &str = "localbrain.atlassian-evidence.v4";
static URL: LazyLock<Regex> =
    LazyLock::new(|| python_regex(r#"(?i)https?://[^\s<>'"`]+"#).unwrap());
static LINK: LazyLock<Regex> =
    LazyLock::new(|| python_regex(r"(?i)\[[^\]]*\]\((?<target>[^)\s]+\.md(?:#[^)]*)?)\)").unwrap());
static PATH: LazyLock<Regex> = LazyLock::new(|| {
    python_regex(r#"(?i)(?<target>(?:/|\.{1,2}/|[A-Za-z0-9_~.-]+/)*[A-Za-z0-9_~.-]+\.md(?:#[^\s)\]}>,'"`]*)?)"#).unwrap()
});
fn chars(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}
fn normalized(source: &SourceJson, s: &str) -> String {
    // The source regex discards non-ASCII characters, including surrogate
    // units. Opaque token payload digits must not become part of a field name.
    source
        .characters(s)
        .filter_map(|point| match point {
            crate::backend::json::SourceCharacter::Scalar(ch) => Some(ch),
            crate::backend::json::SourceCharacter::Surrogate(_) => None,
        })
        .flat_map(char::to_lowercase)
        .filter(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
        .collect()
}
const CONTAINERS: &[&str] = &[
    "content", "data", "issue", "issues", "page", "pages", "result", "results", "text", "value",
    "values",
];
const URL_FIELDS: &[&str] = &[
    "browserurl",
    "canonicalurl",
    "link",
    "self",
    "url",
    "weburl",
];
const ID_FIELDS: &[&str] = &["id", "issueid", "pageid", "remoteid"];
const TITLE_FIELDS: &[&str] = &["name", "summary", "title"];
const TARGETS: &[&str] = &[
    "jira__searchIssuesByJql",
    "jira__getProjectDetails",
    "wiki__searchWiki",
    "wiki__getPageById",
    "wiki__getChildPages",
];
const DIRECT: &[&str] = &[
    "atlassian.getAccessibleAtlassianResources",
    "atlassian.searchJiraIssuesUsingJql",
    "atlassian.searchConfluenceUsingCql",
    "atlassian.getConfluencePage",
];
const GATEWAY: &[&str] = &[
    "mcp_gateway.gateway_dispatch",
    "gateway_dispatch",
    "mcp__mcp_gateway__gateway_dispatch",
];
fn container(source: &SourceJson, value: &Value) -> Option<Value> {
    if let Some(s) = value.as_str() {
        if s.len() > 1_000_000 || !matches!(s.py_trim().as_bytes().first(), Some(b'[' | b'{')) {
            return None;
        }
        source.parse(s.py_trim()).ok()
    } else {
        Some(value.clone())
    }
}
fn mapping(source: &SourceJson, value: &Value, fields: &[&str]) -> Option<String> {
    value.as_object()?.iter().find_map(|(key, value)| {
        if !fields.contains(&normalized(source, key).as_str())
            || !(value.is_string() || count_is_integer(value))
        {
            return None;
        }
        let s = source.python_string(value).py_trim().to_owned();
        (!s.is_empty()).then_some(s)
    })
}
fn reference(
    kind: &str,
    value: String,
    evidence: &str,
    line: i64,
    ordinal: i64,
    event: Option<&str>,
    time: Option<&str>,
) -> ParsedReferenceCandidate {
    ParsedReferenceCandidate {
        reference_kind: kind.into(),
        reference: value,
        evidence_kind: evidence.into(),
        source_line: line,
        evidence_ordinal: ordinal,
        source_event_id: event.map(Into::into),
        observed_at: time.map(Into::into),
        tool_name: None,
        tool_call_id: None,
        read_outcome: None,
    }
}
pub fn visible_url_evidence(
    text: &str,
    line: i64,
    event: Option<&str>,
    observed_at: Option<&str>,
) -> Vec<ParsedUrlEvidence> {
    URL.find_iter(text)
        .enumerate()
        .filter_map(|(index, found)| {
            let url = trim_url_token(found.as_str());
            (!url.is_empty()).then(|| ParsedUrlEvidence {
                observed_url: url,
                source_line: line,
                url_ordinal: index as i64 + 1,
                source_channel: "visible_text".into(),
                source_event_id: event.map(Into::into),
                observed_at: observed_at.map(Into::into),
                observed_remote_id: None,
                observed_title: None,
            })
        })
        .collect()
}
pub(super) fn visible(
    session: &mut ParsedSession,
    text: &str,
    role: &str,
    line: i64,
    url_event: &str,
    reference_event: &str,
    time: Option<&str>,
) {
    let mut seen = HashSet::new();
    let mut occupied = vec![];
    let kind = if role == "user" {
        "user_mention"
    } else {
        "assistant_mention"
    };
    let mut ordinal = 0;
    for (i, m) in URL.find_iter(text).enumerate() {
        let url = trim_url_token(m.as_str());
        if url.is_empty() {
            continue;
        }
        session.url_evidence.push(ParsedUrlEvidence {
            observed_url: url.clone(),
            source_line: line,
            url_ordinal: i as i64 + 1,
            source_channel: "visible_text".into(),
            source_event_id: Some(url_event.into()),
            observed_at: time.map(Into::into),
            observed_remote_id: None,
            observed_title: None,
        });
        if url.chars().count() <= 8000 && seen.insert(("url", url.clone())) {
            ordinal += 1;
            occupied.push((m.start(), m.end()));
            session.reference_candidates.push(reference(
                "url",
                url,
                kind,
                line,
                ordinal,
                Some(reference_event),
                time,
            ));
        }
    }
    let mut matches = LINK
        .captures_iter(text)
        .filter_map(|c| c.name("target"))
        .collect::<Vec<_>>();
    matches.extend(
        PATH.captures_iter(text)
            .filter_map(|c| c.name("target"))
            .filter(|m| {
                let prior = text[..m.start()].chars().next_back();
                !prior.is_some_and(|c| c.is_ascii_alphanumeric() || ":/".contains(c))
            }),
    );
    for m in matches {
        if occupied.iter().any(|(s, e)| m.start() < *e && m.end() > *s) {
            continue;
        }
        let value = m.as_str().py_trim().split('#').next().unwrap_or("");
        if !value.is_empty()
            && value.chars().count() <= 8000
            && seen.insert(("markdown", value.into()))
        {
            ordinal += 1;
            session.reference_candidates.push(reference(
                "markdown",
                value.into(),
                kind,
                line,
                ordinal,
                Some(reference_event),
                time,
            ));
        }
    }
}
pub(super) fn approved(
    source: &SourceJson,
    name: &str,
    id: &str,
    args: &Value,
) -> Option<ApprovedResourceCall> {
    if id.py_trim().is_empty() {
        return None;
    }
    let name = name.py_trim();
    let parsed = container(source, args).unwrap_or(Value::Null);
    let target = ["capability", "capability_name", "name", "target", "tool"]
        .iter()
        .find_map(|key| parsed[key].as_str().filter(|v| TARGETS.contains(v)));
    if !(DIRECT.contains(&name)
        || TARGETS.iter().any(|t| {
            name == *t || name.ends_with(&format!(".{t}")) || name.ends_with(&format!("__{t}"))
        })
        || GATEWAY.contains(&name) && target.is_some())
    {
        return None;
    }
    let operation = if GATEWAY.contains(&name) {
        target.unwrap_or(name)
    } else {
        name
    }
    .to_lowercase();
    let mut hints = vec![];
    let mut seen = HashSet::new();
    let mut nodes = 0usize;
    enum Task {
        Node(Value, usize),
        Field(String, Value, usize),
    }
    let mut stack = vec![Task::Node(parsed, 0)];
    static ISSUE: LazyLock<Regex> =
        LazyLock::new(|| python_regex(r"(?i)^[A-Z][A-Z0-9_]*-\d+$").unwrap());
    static JQL: LazyLock<Regex> = LazyLock::new(|| {
        python_regex(r#"(?i)^\s*key\s*=\s*(?:"([^"]+)"|'([^']+)'|([A-Z][A-Z0-9_]*-\d+))\s*$"#)
            .unwrap()
    });
    while let Some(task) = stack.pop() {
        let (key, child, depth) = match task {
            Task::Node(value, depth) => {
                if depth > 4 || nodes >= 200 || hints.len() >= 20 {
                    continue;
                }
                nodes += 1;
                let value = container(source, &value).unwrap_or(Value::Null);
                if let Some(array) = value.as_array() {
                    stack.extend(
                        array
                            .iter()
                            .take(50)
                            .rev()
                            .map(|v| Task::Node(v.clone(), depth + 1)),
                    );
                } else if let Some(map) = value.as_object() {
                    stack.extend(
                        map.iter()
                            .rev()
                            .map(|(k, v)| Task::Field(k.clone(), v.clone(), depth)),
                    );
                }
                continue;
            }
            Task::Field(key, value, depth) => (key, value, depth),
        };
        let field = normalized(source, &key);
        let mut additions = vec![];
        if URL_FIELDS.contains(&field.as_str())
            || ["issueurl", "pageurl", "baseurl"].contains(&field.as_str())
        {
            if let Some(s) = child.as_str() {
                additions.extend(
                    URL.find_iter(s)
                        .map(|m| ("url", trim_url_token(m.as_str()))),
                );
            }
        } else if operation.contains("jira") && ["issuekey", "key"].contains(&field.as_str()) {
            if let Some(s) = child.as_str().filter(|s| ISSUE.is_match(s.py_trim())) {
                additions.push(("jira_key", s.py_trim().to_uppercase()));
            }
        } else if operation.contains("jira") && field == "jql" {
            if let Some(c) = child.as_str().and_then(|s| JQL.captures(s)) {
                if let Some(s) = (1..=3)
                    .find_map(|i| c.get(i).map(|m| m.as_str()))
                    .filter(|s| ISSUE.is_match(s))
                {
                    additions.push(("jira_key", s.to_uppercase()));
                }
            }
        } else if (operation.contains("confluence") || operation.contains("wiki"))
            && ["pageid", "contentid"].contains(&field.as_str())
        {
            let s = source.python_string(&child);
            if s.py_trim()
                .chars()
                .all(crate::backend::unicode::python_digit)
                && !s.py_trim().is_empty()
            {
                additions.push(("confluence_page_id", s.py_trim().into()));
            }
        } else if [
            "arguments",
            "args",
            "input",
            "params",
            "parameters",
            "payload",
            "request",
        ]
        .contains(&field.as_str())
        {
            stack.push(Task::Node(child.clone(), depth + 1));
        }
        for (kind, s) in additions {
            if !s.is_empty() && s.chars().count() <= 8000 && seen.insert((kind, s.clone())) {
                hints.push((kind.into(), s));
            }
        }
    }
    Some(ApprovedResourceCall {
        tool_name: name.into(),
        tool_call_id: id.py_trim().into(),
        target_hints: hints,
    })
}
pub(super) fn failed(source: &SourceJson, values: &[&Value]) -> bool {
    values.iter().any(|value| {
        let Some(v) = container(source, value) else {
            return false;
        };
        v.is_object()
            && (v["is_error"] == true
                || v["isError"] == true
                || v["success"] == false
                || v["status"].as_str().is_some_and(|s| {
                    ["cancelled", "error", "failed", "failure"]
                        .contains(&s.py_trim().to_lowercase().as_str())
                })
                || truth(&v["error"]))
    })
}
pub(super) fn completed(source: &SourceJson, value: &Value) -> bool {
    let Some(value) = container(source, value) else {
        return false;
    };
    if let Some(array) = value.as_array() {
        return array.iter().any(|v| completed(source, v));
    }
    let Some(map) = value.as_object() else {
        return false;
    };
    if map.is_empty() {
        return false;
    }
    if value["success"] == true
        || value["status"].as_str().is_some_and(|s| {
            ["complete", "completed", "ok", "success", "succeeded"]
                .contains(&s.py_trim().to_lowercase().as_str())
        })
    {
        return true;
    }
    map.iter().any(|(key, child)| {
        let field = normalized(source, key);
        if CONTAINERS.contains(&field.as_str()) {
            completed(source, child)
        } else if URL_FIELDS.contains(&field.as_str())
            || ID_FIELDS.contains(&field.as_str())
            || TITLE_FIELDS.contains(&field.as_str())
            || ["issuekey", "key", "pageid", "contentid"].contains(&field.as_str())
        {
            (child.is_string() || count_is_integer(child))
                && !source.python_string(child).py_trim().is_empty()
        } else {
            false
        }
    })
}
fn count_is_integer(v: &Value) -> bool {
    v.as_number().is_some_and(|number| {
        let text = number.to_string();
        let digits = text.trim_start_matches('-');
        !digits.is_empty() && digits.bytes().all(|b| b.is_ascii_digit())
    })
}
fn result_urls(
    source: &SourceJson,
    value: &Value,
    line: i64,
    event: &str,
    time: Option<&str>,
) -> Vec<ParsedUrlEvidence> {
    let Some(root) = container(source, value) else {
        return vec![];
    };
    let mut nodes = 0;
    let mut output = vec![];
    let mut stack = vec![(root, 0usize)];
    while let Some((node, depth)) = stack.pop() {
        if depth > 8 || nodes >= 2000 || output.len() >= 100 {
            continue;
        }
        nodes += 1;
        if node.is_string() {
            if let Some(parsed) = container(source, &node) {
                stack.push((parsed, depth + 1));
            }
            continue;
        }
        if let Some(array) = node.as_array() {
            stack.extend(
                array
                    .iter()
                    .take(2000)
                    .rev()
                    .map(|v| (v.clone(), depth + 1)),
            );
            continue;
        }
        let Some(map) = node.as_object() else {
            continue;
        };
        let id = mapping(source, &node, ID_FIELDS);
        let title = mapping(source, &node, TITLE_FIELDS);
        for (key, value) in map {
            if !URL_FIELDS.contains(&normalized(source, key).as_str()) {
                continue;
            }
            if let Some(s) = value.as_str() {
                for m in URL.find_iter(s) {
                    let s = trim_url_token(m.as_str());
                    if !s.is_empty() && output.len() < 100 {
                        output.push(ParsedUrlEvidence {
                            observed_url: s,
                            source_line: line,
                            url_ordinal: output.len() as i64 + 1,
                            source_channel: "approved_tool_result".into(),
                            source_event_id: Some(event.into()),
                            observed_at: time.map(Into::into),
                            observed_remote_id: id.as_deref().map(|s| chars(s, 300)),
                            observed_title: title.as_deref().map(|s| chars(s, 500)),
                        });
                    }
                }
            }
        }
        stack.extend(
            map.iter()
                .filter(|(key, _)| CONTAINERS.contains(&normalized(source, key).as_str()))
                .rev()
                .map(|(_, child)| (child.clone(), depth + 1)),
        );
    }
    output
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
pub(super) fn tool_result(
    source: &SourceJson,
    session: &mut ParsedSession,
    call: &ApprovedResourceCall,
    value: &Value,
    is_failed: bool,
    line: i64,
    event: &str,
    time: Option<&str>,
) {
    if !is_failed && !completed(source, value) {
        return;
    }
    let urls = if is_failed {
        vec![]
    } else {
        result_urls(source, value, line, event, time)
    };
    session.url_evidence.extend(urls.iter().cloned());
    let mut candidates = vec![];
    for url in &urls {
        let mut item = reference(
            "url",
            url.observed_url.clone(),
            "tool_result",
            line,
            candidates.len() as i64 + 1,
            Some(event),
            time,
        );
        item.tool_name = Some(call.tool_name.clone());
        item.tool_call_id = Some(call.tool_call_id.clone());
        candidates.push(item);
    }
    let mut targets = call.target_hints.clone();
    targets.extend(urls.into_iter().map(|v| ("url".into(), v.observed_url)));
    let mut seen = HashSet::new();
    for (kind, value) in targets {
        if !seen.insert((kind.clone(), value.clone())) {
            continue;
        }
        let mut item = reference(
            &kind,
            value,
            "resource_read",
            line,
            candidates.len() as i64 + 1,
            Some(event),
            time,
        );
        item.tool_name = Some(call.tool_name.clone());
        item.tool_call_id = Some(call.tool_call_id.clone());
        item.read_outcome = Some(if is_failed { "failure" } else { "success" }.into());
        candidates.push(item);
    }
    session.reference_candidates.extend(candidates);
}
