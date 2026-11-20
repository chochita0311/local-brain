//! Strict bounded form contract, independent of HTTP host types and transactions.
use super::projection::CLOSURE_REASONS;
use crate::backend::{unicode, BackendError, Result};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeMap;
pub const WORKFLOW_CORRECTION_PARTIAL: &str = "workflow-correction";
pub const MAX_WORKFLOW_CORRECTION_FORM_BYTES: usize = 16 * 1024;
pub const MAX_WORKFLOW_CORRECTION_FIELDS: usize = 8;
pub const MAX_SQLITE_INTEGER: u64 = 9_223_372_036_854_775_807;
pub const WORKFLOW_CORRECTION_ACTIONS: &[&str] = &[
    "same-flow",
    "split-here",
    "merge-into",
    "close",
    "reopen",
    "undo",
];
pub const WORKFLOW_CORRECTION_FIELDS: &[&str] = &[
    "action",
    "source_episode_key",
    "target_episode_key",
    "close_reason",
    "note",
    "assertion_id",
    "expected_active_assertion_id",
    "expected_revision",
];
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkflowCorrectionRequest {
    pub action: String,
    pub expected_revision: String,
    pub source_episode_key: Option<String>,
    pub target_episode_key: Option<String>,
    pub close_reason: Option<String>,
    pub note: Option<String>,
    pub assertion_id: Option<i64>,
    pub expected_active_assertion_id: Option<i64>,
}
impl WorkflowCorrectionRequest {
    fn new(action: &str, revision: &str) -> Self {
        Self {
            action: action.into(),
            expected_revision: revision.into(),
            source_episode_key: None,
            target_episode_key: None,
            close_reason: None,
            note: None,
            assertion_id: None,
            expected_active_assertion_id: None,
        }
    }
    /// Domain keyword packet. Transport-only `action` never enters persistence.
    pub fn domain_request(&self) -> Value {
        if self.action == "undo" {
            json!({"assertion_id":self.assertion_id,"expected_revision":self.expected_revision})
        } else {
            json!({"assertion_kind":self.action,"source_episode_key":self.source_episode_key,"target_episode_key":self.target_episode_key,"close_reason":self.close_reason,"note":self.note,"expected_active_assertion_id":self.expected_active_assertion_id,"expected_revision":self.expected_revision})
        }
    }
}
fn reject(code: &str, message: &str) -> BackendError {
    BackendError::new(422, code, message)
}
fn invalid_form(message: &str) -> BackendError {
    BackendError::new(400, "invalid-form", message)
}
pub fn reject_cross_site_workflow_correction(fetch_site: Option<&str>) -> Result<()> {
    if fetch_site.is_some_and(|value| {
        unicode::lowercase(value.trim_matches(unicode::python_space)) == "cross-site"
    }) {
        Err(BackendError::new(
            400,
            "cross-site-request",
            "Cross-site workflow corrections are not accepted.",
        ))
    } else {
        Ok(())
    }
}
fn positive(value: &str, field: &str) -> Result<i64> {
    if !value
        .as_bytes()
        .first()
        .is_some_and(|b| (b'1'..=b'9').contains(b))
        || !value.bytes().all(|b| b.is_ascii_digit())
    {
        return Err(reject(
            "invalid-request",
            &format!("{field} must be a positive integer."),
        ));
    }
    value
        .parse::<u64>()
        .ok()
        .filter(|value| *value <= MAX_SQLITE_INTEGER)
        .map(|value| value as i64)
        .ok_or_else(|| {
            reject(
                "invalid-request",
                &format!("{field} is outside the supported range."),
            )
        })
}
fn opaque(value: &str, prefix: &str) -> bool {
    value.strip_prefix(prefix).is_some_and(|hex| {
        hex.len() == 64
            && hex
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}
fn episode(value: Option<&String>, field: &str) -> Result<String> {
    value
        .filter(|value| opaque(value, "session:"))
        .cloned()
        .ok_or_else(|| {
            reject(
                "invalid-request",
                &format!("{field} must be a stable Episode key."),
            )
        })
}
fn exact(values: &BTreeMap<String, String>, required: &[&str], optional: &[&str]) -> Result<()> {
    if required.iter().any(|key| !values.contains_key(*key))
        || values
            .keys()
            .any(|key| !required.contains(&key.as_str()) && !optional.contains(&key.as_str()))
    {
        Err(reject(
            "invalid-request",
            "The correction fields do not match the action.",
        ))
    } else {
        Ok(())
    }
}
fn hex(b: u8) -> Option<u8> {
    match b {
        b'0'..=b'9' => Some(b - b'0'),
        b'a'..=b'f' => Some(b - b'a' + 10),
        b'A'..=b'F' => Some(b - b'A' + 10),
        _ => None,
    }
}
fn decode(value: &[u8]) -> Result<String> {
    let mut decoded = Vec::with_capacity(value.len());
    let mut index = 0;
    while index < value.len() {
        match value[index] {
            b'+' => decoded.push(b' '),
            b'%' => {
                decoded.push(hex(value[index + 1]).unwrap() * 16 + hex(value[index + 2]).unwrap());
                index += 2;
            }
            byte => decoded.push(byte),
        }
        index += 1;
    }
    String::from_utf8(decoded).map_err(|_| invalid_form("Form data is invalid."))
}
pub fn parse_workflow_correction_form(
    content_type: Option<&str>,
    body: &[u8],
) -> Result<WorkflowCorrectionRequest> {
    let media = content_type.unwrap_or("").split(';').next().unwrap_or("");
    if unicode::lowercase(media.trim_matches(unicode::python_space))
        != "application/x-www-form-urlencoded"
    {
        return Err(invalid_form("Form encoding is unsupported."));
    }
    if body.len() > MAX_WORKFLOW_CORRECTION_FORM_BYTES {
        return Err(invalid_form("Form is too large."));
    }
    if body.is_empty() {
        return Err(invalid_form("Form data is invalid."));
    }
    let mut index = 0;
    while index < body.len() {
        if body[index] == b'%' {
            if index + 2 >= body.len()
                || hex(body[index + 1]).is_none()
                || hex(body[index + 2]).is_none()
            {
                return Err(invalid_form("Form data is invalid."));
            }
            index += 2;
        }
        index += 1;
    }
    if !body.is_ascii()
        || body.iter().filter(|byte| **byte == b'&').count() + 1 > MAX_WORKFLOW_CORRECTION_FIELDS
    {
        return Err(invalid_form("Form data is invalid."));
    }
    let mut pairs = vec![];
    for pair in body.split(|byte| *byte == b'&') {
        let Some(equal) = pair.iter().position(|byte| *byte == b'=') else {
            return Err(invalid_form("Form data is invalid."));
        };
        pairs.push((decode(&pair[..equal])?, decode(&pair[equal + 1..])?));
    }
    let mut values = BTreeMap::new();
    for (key, value) in pairs {
        if !WORKFLOW_CORRECTION_FIELDS.contains(&key.as_str()) {
            return Err(reject(
                "invalid-request",
                "The form contains an unknown field.",
            ));
        }
        if values.contains_key(&key) {
            return Err(reject(
                "invalid-request",
                "The form contains a repeated field.",
            ));
        }
        if value.is_empty() && key != "note" {
            return Err(reject(
                "invalid-request",
                "Correction fields cannot be blank.",
            ));
        }
        values.insert(key, value);
    }
    let action = values
        .get("action")
        .filter(|value| WORKFLOW_CORRECTION_ACTIONS.contains(&value.as_str()))
        .ok_or_else(|| {
            reject(
                "invalid-action",
                "The workflow correction action is unsupported.",
            )
        })?;
    let revision = values
        .get("expected_revision")
        .filter(|value| opaque(value, "workflow-revision:"))
        .ok_or_else(|| reject("invalid-request", "A stable workflow revision is required."))?;
    let mut request = WorkflowCorrectionRequest::new(action, revision);
    if action == "undo" {
        exact(
            &values,
            &["action", "assertion_id", "expected_revision"],
            &[],
        )?;
        request.assertion_id = Some(positive(&values["assertion_id"], "assertion_id")?);
        return Ok(request);
    }
    request.source_episode_key = Some(episode(
        values.get("source_episode_key"),
        "source_episode_key",
    )?);
    request.expected_active_assertion_id = values
        .get("expected_active_assertion_id")
        .map(|value| positive(value, "expected_active_assertion_id"))
        .transpose()?;
    if ["same-flow", "split-here", "merge-into"].contains(&action.as_str()) {
        exact(
            &values,
            &[
                "action",
                "source_episode_key",
                "expected_revision",
                "target_episode_key",
            ],
            &["expected_active_assertion_id"],
        )?;
        request.target_episode_key = Some(episode(
            values.get("target_episode_key"),
            "target_episode_key",
        )?);
        return Ok(request);
    }
    if action == "close" {
        exact(
            &values,
            &[
                "action",
                "source_episode_key",
                "expected_revision",
                "close_reason",
            ],
            &["expected_active_assertion_id", "note"],
        )?;
        let reason = &values["close_reason"];
        if !CLOSURE_REASONS.contains(&reason.as_str()) {
            return Err(reject(
                "invalid-close-reason",
                "The close reason is unsupported.",
            ));
        }
        request.close_reason = Some(reason.clone());
        request.note = values
            .get("note")
            .filter(|value| !value.is_empty())
            .cloned();
        if request
            .note
            .as_ref()
            .is_some_and(|note| note.chars().count() > 1000)
        {
            return Err(reject("invalid-note", "The correction note is too long."));
        }
        return Ok(request);
    }
    exact(
        &values,
        &[
            "action",
            "source_episode_key",
            "expected_revision",
            "expected_active_assertion_id",
        ],
        &[],
    )?;
    Ok(request)
}
