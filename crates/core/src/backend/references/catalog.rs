//! Manual Atlassian catalog URLs retain sorted query parameters. This existing
//! registration policy is separate from privacy-safe extracted URL identities.
use super::{atlassian, idna};
use crate::backend::{search::urlencode, unicode::python_space, BackendError, Result};
use serde::{Deserialize, Serialize};
use unicode_normalization::UnicodeNormalization;
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizedAtlassianUrl {
    pub observed_url: String,
    pub normalized_url: String,
    pub normalized_domain: String,
    pub canonical_base_url: String,
}
pub fn normalize_atlassian_catalog_url(value: &str) -> Result<NormalizedAtlassianUrl> {
    let observed = value.trim_matches(python_space);
    if observed.is_empty() {
        return Err(BackendError::invalid(
            "invalid-input",
            "url must be a non-empty string",
        ));
    }
    if observed.chars().count() > 8000 {
        return Err(BackendError::invalid(
            "invalid-input",
            "url exceeds 8000 characters",
        ));
    }
    let invalid = || BackendError::invalid("invalid-url", "URL is invalid");
    let network = || BackendError::invalid("invalid-url", "Atlassian URLs must use HTTP or HTTPS");
    let scheme = observed
        .split_once(':')
        .map(|(scheme, _)| scheme.to_ascii_lowercase())
        .unwrap_or_default();
    if !["http", "https"].contains(&scheme.as_str()) {
        return Err(network());
    }
    let clean = observed
        .trim_start_matches(|ch: char| ch <= '\u{20}')
        .replace(['\t', '\r', '\n'], "");
    let Some((_, tail)) = clean.split_once("://") else {
        return Err(network());
    };
    let authority = tail.split(['/', '?', '#']).next().unwrap_or_default();
    // urllib.parse rejects authority characters whose NFKC expansion creates
    // delimiters before IDNA is attempted.
    let check = authority.replace(['@', ':', '#', '?'], "");
    let normalized = check.nfkc().collect::<String>();
    if normalized != check && normalized.contains(['/', '?', '#', '@', ':']) {
        return Err(invalid());
    }
    let raw = atlassian::split_url(&clean).ok_or_else(invalid)?;
    if raw.host.is_empty() {
        return Err(network());
    }
    if raw.userinfo {
        return Err(BackendError::invalid(
            "invalid-url",
            "Atlassian URLs cannot contain credentials",
        ));
    }
    let raw_host = raw.host.trim_end_matches('.');
    if raw_host.is_empty() {
        return Err(BackendError::invalid(
            "invalid-url",
            "Atlassian URL domain is empty",
        ));
    }
    let host = idna::ascii(raw_host)
        .ok_or_else(|| BackendError::invalid("invalid-url", "Atlassian URL domain is invalid"))?;
    if host.is_empty() {
        return Err(BackendError::invalid(
            "invalid-url",
            "Atlassian URL domain is empty",
        ));
    }
    let port = raw.port.filter(|port| {
        !((raw.scheme == "http" && *port == 80) || (raw.scheme == "https" && *port == 443))
    });
    let domain = port.map_or(host.clone(), |port| format!("{host}:{port}"));
    let base = format!("{}://{domain}", raw.scheme);
    let path = if raw.path.is_empty() {
        "/"
    } else {
        raw.path.trim_end_matches('/')
    };
    let path = if path.is_empty() { "/" } else { path };
    let mut pairs = url::form_urlencoded::parse(raw.query.as_bytes())
        .map(|(key, value)| (key.into_owned(), value.into_owned()))
        .collect::<Vec<_>>();
    pairs.sort();
    let query = urlencode(
        &pairs
            .iter()
            .map(|(key, value)| (key.as_str(), value.clone()))
            .collect::<Vec<_>>(),
    );
    let normalized_url = format!(
        "{base}{path}{}",
        if query.is_empty() {
            String::new()
        } else {
            format!("?{query}")
        }
    );
    Ok(NormalizedAtlassianUrl {
        observed_url: observed.into(),
        normalized_url,
        normalized_domain: domain,
        canonical_base_url: base,
    })
}
/// Admission for an already authorized opaque external-sync locator. This is
/// precisely urlsplit's scheme/netloc check, which intentionally does not read
/// a hostname or port and therefore does not impose resource-identity policy.
pub fn is_http_locator(value: &str) -> Result<bool> {
    let cleaned = value
        .trim_start_matches(|ch: char| ch <= '\u{20}')
        .replace(['\t', '\r', '\n'], "");
    let (scheme, rest) = cleaned
        .split_once(':')
        .filter(|(scheme, _)| {
            scheme
                .as_bytes()
                .first()
                .is_some_and(u8::is_ascii_alphabetic)
                && scheme
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || b"+-.".contains(&byte))
        })
        .unwrap_or(("", cleaned.as_str()));
    let Some(rest) = rest.strip_prefix("//") else {
        return Ok(false);
    };
    let authority = rest.split(['/', '?', '#']).next().unwrap_or_default();
    let invalid = || BackendError::invalid("invalid-url", "URL is invalid");
    if authority.contains('[') != authority.contains(']') {
        return Err(invalid());
    }
    if authority.contains('[') && authority.contains(']') {
        let host = authority.rsplit('@').next().unwrap_or_default();
        let hostname = if let Some((before, bracketed)) = host.split_once('[') {
            if !before.is_empty() {
                return Err(invalid());
            }
            let (hostname, port) = bracketed.split_once(']').ok_or_else(invalid)?;
            if !port.is_empty() && !port.starts_with(':') {
                return Err(invalid());
            }
            hostname
        } else {
            host.split(':').next().unwrap_or_default()
        };
        if hostname.starts_with('v') {
            let valid = hostname
                .strip_prefix('v')
                .and_then(|rest| rest.split_once('.'))
                .is_some_and(|(version, tail)| {
                    !version.is_empty()
                        && version.bytes().all(|byte| byte.is_ascii_hexdigit())
                        && !tail.is_empty()
                });
            if !valid {
                return Err(invalid());
            }
        } else {
            let (address, scope) = hostname
                .split_once('%')
                .map_or((hostname, None), |(address, scope)| (address, Some(scope)));
            if scope.is_some_and(|scope| scope.is_empty() || scope.contains('%'))
                || address.parse::<std::net::Ipv6Addr>().is_err()
            {
                return Err(invalid());
            }
        }
    }
    if !authority.is_ascii() {
        let check = authority.replace(['@', ':', '#', '?'], "");
        let normalized = check.nfkc().collect::<String>();
        if check != normalized && normalized.contains(['/', '?', '#', '@', ':']) {
            return Err(invalid());
        }
    }
    Ok(["http", "https"].contains(&scheme.to_ascii_lowercase().as_str()) && !authority.is_empty())
}
