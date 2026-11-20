//! Pure provider URL grammar and stable identity; no settings or filesystem reads.
mod atlassian;
mod catalog;
mod idna;
mod nameprep_tables;
pub use atlassian::{
    atlassian_item_container_hint, atlassian_locator_identity, atlassian_page_title_hint,
    describe_atlassian_url, UrlLocator,
};
pub use catalog::{is_http_locator, normalize_atlassian_catalog_url, NormalizedAtlassianUrl};
use serde::{Deserialize, Serialize};
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedUrl {
    pub normalized_url: String,
    pub target_key: String,
    pub observed_identity: String,
    pub locator: Option<UrlLocator>,
}
pub fn trim_url_token(value: &str) -> String {
    let candidate = value.trim_end_matches(['.', ',', ';', ':', '!', '?']);
    let mut stack = Vec::new();
    for (index, ch) in candidate.char_indices() {
        if ['(', '[', '{'].contains(&ch) {
            stack.push(ch);
            continue;
        }
        let expected = match ch {
            ')' => Some('('),
            ']' => Some('['),
            '}' => Some('{'),
            _ => None,
        };
        if let Some(expected) = expected {
            if stack.last() == Some(&expected) {
                stack.pop();
            } else {
                return candidate[..index]
                    .trim_end_matches(['.', ',', ';', ':', '!', '?'])
                    .into();
            }
        }
    }
    candidate.into()
}
pub fn safe_generic_url(value: &str) -> Option<String> {
    let value = trim_url_token(value.trim_matches(crate::backend::unicode::python_space));
    let parsed = atlassian::split_url(&value)?;
    if !["http", "https"].contains(&parsed.scheme.as_str())
        || parsed.userinfo
        || parsed.host.is_empty()
    {
        return None;
    }
    let host = parsed.host.to_lowercase().trim_end_matches('.').to_string();
    if host.is_empty() || host.chars().any(|c| (c as u32) < 32) {
        return None;
    }
    let rendered = if host.contains(':') && !host.starts_with('[') {
        format!("[{host}]")
    } else {
        host
    };
    let port = parsed
        .port
        .filter(|port| {
            !((parsed.scheme == "http" && *port == 80)
                || (parsed.scheme == "https" && *port == 443))
        })
        .map(|port| format!(":{port}"))
        .unwrap_or_default();
    let path = if parsed.path.is_empty() {
        "/"
    } else {
        &parsed.path
    };
    if path.chars().any(|c| (c as u32) < 32) {
        return None;
    }
    let result = format!("{}://{}{port}{path}", parsed.scheme, rendered);
    (result.chars().count() <= 8000).then_some(result)
}
pub fn safe_url_identity(value: &str) -> String {
    atlassian::split_url(value)
        .map(|url| {
            format!(
                "{}{}{}",
                if url.host.contains(':') {
                    format!("[{}]", url.host)
                } else {
                    url.host
                },
                url.port.map(|port| format!(":{port}")).unwrap_or_default(),
                if url.path.is_empty() {
                    "/".into()
                } else {
                    url.path
                }
            )
        })
        .unwrap_or_default()
        .chars()
        .take(500)
        .collect()
}
/// A retained observed URL is displayed verbatim after the existing URL grammar
/// admits its scheme/authority. Rendering never follows the link.
pub fn external_href(value: &str) -> Option<String> {
    let value = trim_url_token(value.trim_matches(crate::backend::unicode::python_space));
    let parsed = atlassian::split_url(&value)?;
    (["http", "https"].contains(&parsed.scheme.as_str())
        && !parsed.userinfo
        && !parsed.host.is_empty())
    .then_some(value)
}
pub fn external_detail(value: &str) -> Option<String> {
    let safe = external_href(value)?;
    let parsed = atlassian::split_url(&safe)?;
    let host = if let Some(port) = parsed.port {
        format!("{}:{port}", parsed.host)
    } else {
        parsed.host
    };
    Some(
        format!(
            "{host}{}",
            if parsed.path.is_empty() {
                "/"
            } else {
                &parsed.path
            }
        )
        .chars()
        .take(500)
        .collect(),
    )
}
pub fn hash_payload(value: &serde_json::Value) -> String {
    localbrain_models::assets::value_digest(value).expect("serializable URL identity")
}
pub fn parse_url(value: &str) -> Option<ParsedUrl> {
    let locator = describe_atlassian_url(value);
    if ["item", "structure", "site"].contains(&locator.kind.as_str()) {
        let identity = atlassian_locator_identity(&locator)?;
        let normalized_url = locator.safe_locator_url.clone()?;
        let key = locator
            .item_identity
            .as_ref()
            .or(locator.reference_identity.as_ref());
        let observed_identity = format!(
            "{} · {}{}",
            locator.normalized_domain.as_deref().unwrap_or(""),
            locator.family.as_deref().unwrap_or(""),
            key.map(|key| format!(":{key}")).unwrap_or_default()
        )
        .chars()
        .take(500)
        .collect();
        Some(ParsedUrl {
            normalized_url,
            target_key: format!("url:{}", hash_payload(&serde_json::json!(identity))),
            observed_identity,
            locator: Some(locator),
        })
    } else if locator.kind == "unsafe" {
        None
    } else {
        let normalized_url = safe_generic_url(value)?;
        Some(ParsedUrl {
            target_key: format!("url:{}", hash_payload(&serde_json::json!(normalized_url))),
            observed_identity: safe_url_identity(&normalized_url),
            normalized_url,
            locator: None,
        })
    }
}
