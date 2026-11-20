use super::super::{catalog, common::*};
use crate::backend::{references, unicode, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegistrationLocator {
    pub service: String,
    pub kind: String,
    pub normalized_url: String,
    pub normalized_domain: String,
    pub remote_id: Option<String>,
    pub remote_key: Option<String>,
    pub space_key: Option<String>,
    pub title_hint: Option<String>,
}
pub fn recognize_registration_url(
    url: &str,
    expected_service: Option<&str>,
) -> Result<RegistrationLocator> {
    let described = references::describe_atlassian_url(url);
    if described.kind == "unsafe" {
        return Err(fail("invalid-url", "Atlassian URL is invalid"));
    }
    let owner = catalog::normalize_atlassian_url(url)?;
    let locator = if described.kind == "item" {
        RegistrationLocator {
            service: described.service.unwrap(),
            kind: "item".into(),
            normalized_url: owner.normalized_url,
            normalized_domain: described.normalized_domain.unwrap(),
            remote_id: if described.item_identity_kind.as_deref() == Some("confluence_page") {
                described.item_identity.clone()
            } else {
                None
            },
            remote_key: if described.item_identity_kind.as_deref() == Some("jira_issue") {
                described.item_identity
            } else {
                None
            },
            space_key: references::atlassian_item_container_hint(url),
            title_hint: references::atlassian_page_title_hint(url),
        }
    } else if described.kind == "structure"
        && matches!(
            described.reference_kind.as_deref(),
            Some("jira_project" | "confluence_space")
        )
    {
        RegistrationLocator {
            service: described.service.unwrap(),
            kind: "space".into(),
            normalized_url: owner.normalized_url,
            normalized_domain: described.normalized_domain.unwrap(),
            remote_id: None,
            remote_key: None,
            space_key: described.reference_identity,
            title_hint: None,
        }
    } else {
        return Err(fail(
            "unsupported-url",
            "Use a Jira issue/project URL or Confluence Page/Space URL",
        ));
    };
    if expected_service
        .filter(|s| !s.is_empty())
        .is_some_and(|s| s != locator.service)
    {
        return Err(fail(
            "service-mismatch",
            "The URL does not belong to the selected Atlassian service",
        ));
    }
    Ok(locator)
}
pub(super) fn bounded(
    value: &Value,
    field: &str,
    maximum: usize,
    optional: bool,
) -> Result<Option<String>> {
    if optional && (value.is_null() || value.as_str().is_some_and(|s| trim(s).is_empty())) {
        return Ok(None);
    }
    let cleaned = value
        .as_str()
        .map(trim)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| fail("invalid-input", format!("{field} is required")))?;
    if cleaned.chars().count() > maximum {
        return Err(fail("invalid-input", format!("{field} is too long")));
    }
    Ok(Some(cleaned.into()))
}
fn unquote(value: &str) -> String {
    let mut out = vec![];
    let bytes = value.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            if let (Some(a), Some(b)) = (
                (bytes[i + 1] as char).to_digit(16),
                (bytes[i + 2] as char).to_digit(16),
            ) {
                out.push((a * 16 + b) as u8);
                i += 3;
                continue;
            }
        }
        out.push(bytes[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}
fn title_text(value: &str) -> String {
    trim(&regex::Regex::new("[-_]+").unwrap().replace_all(value, " ")).into()
}
pub(super) fn bootstrap_title(locator: &RegistrationLocator) -> String {
    if let Some(key) = locator.remote_key.as_deref().filter(|s| !s.is_empty()) {
        return key.into();
    }
    if locator.kind == "space" {
        if let Some(key) = locator.space_key.as_deref().filter(|s| !s.is_empty()) {
            return key.into();
        }
    }
    if locator.service == "confluence" {
        if let Some(remote) = locator.remote_id.as_deref().filter(|s| !s.is_empty()) {
            if let Some(hint) = locator.title_hint.as_deref().filter(|s| !s.is_empty()) {
                let candidate = title_text(hint);
                if !candidate.is_empty() {
                    return candidate;
                }
            }
            let tail = locator
                .normalized_url
                .split_once("://")
                .map(|(_, rest)| rest)
                .unwrap_or("");
            let path = &tail[tail.find(['/', '?', '#']).unwrap_or(tail.len())..];
            let path = path.split(['?', '#']).next().unwrap_or("");
            let parts = path
                .split('/')
                .filter(|s| !trim(s).is_empty())
                .map(|s| trim(&unquote(s)).to_owned())
                .collect::<Vec<_>>();
            if let Some(index) = parts.iter().position(|s| s == remote) {
                if let Some(next) = parts.get(index + 1) {
                    let candidate = title_text(next);
                    if !candidate.is_empty() {
                        return candidate;
                    }
                }
            }
            return remote.into();
        }
    }
    locator
        .space_key
        .as_deref()
        .filter(|s| !s.is_empty())
        .or(locator.remote_id.as_deref().filter(|s| !s.is_empty()))
        .unwrap_or(&locator.normalized_domain)
        .into()
}
pub(super) fn instance_key_base(provider: &str, service: &str, domain: &str) -> String {
    let value = unicode::lowercase(&format!(
        "{}-{service}-{domain}",
        provider.replace('_', "-")
    ));
    let value = regex::Regex::new("[^a-z0-9._-]+")
        .unwrap()
        .replace_all(&value, "-");
    let value = regex::Regex::new("-+")
        .unwrap()
        .replace_all(&value, "-")
        .into_owned();
    value
        .trim_matches(['.', '_', '-'])
        .chars()
        .take(128)
        .collect()
}
