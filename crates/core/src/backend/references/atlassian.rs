use serde::{Deserialize, Serialize};
use unicode_general_category::{get_general_category, GeneralCategory};
use unicode_normalization::UnicodeNormalization;
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct UrlLocator {
    pub kind: String,
    pub service: Option<String>,
    pub family: Option<String>,
    pub normalized_domain: Option<String>,
    pub canonical_base_url: Option<String>,
    pub safe_locator_url: Option<String>,
    pub item_identity_kind: Option<String>,
    pub item_identity: Option<String>,
    pub reference_kind: Option<String>,
    pub reference_identity: Option<String>,
    pub container_hint: Option<String>,
    pub reason: Option<String>,
}
#[derive(Clone)]
pub(super) struct Split {
    pub scheme: String,
    pub host: String,
    pub port: Option<u16>,
    pub userinfo: bool,
    pub path: String,
    pub query: String,
}
pub(super) fn split_url(value: &str) -> Option<Split> {
    let cleaned = value
        .trim_start_matches(|ch: char| ch <= '\u{20}')
        .replace(['\t', '\r', '\n'], "");
    let value = cleaned.as_str();
    let (scheme, rest) = value.split_once("://")?;
    let scheme = scheme.to_ascii_lowercase();
    if scheme.is_empty() {
        return None;
    }
    let end = rest.find(['/', '?', '#']).unwrap_or(rest.len());
    let authority = &rest[..end];
    let tail = &rest[end..];
    let userinfo = authority.contains('@');
    let authority = authority.rsplit('@').next()?;
    let (host, port) = if let Some(stripped) = authority.strip_prefix('[') {
        let (host, after) = stripped.split_once(']')?;
        if host.starts_with('v') {
            if !regex::Regex::new(r"^v[0-9A-Fa-f]+\..+$")
                .unwrap()
                .is_match(host)
            {
                return None;
            }
        } else {
            ipv6(host)?;
        }
        let port = if after.is_empty() {
            None
        } else {
            let port = after.strip_prefix(':')?;
            if port.is_empty() {
                None
            } else {
                Some(parse_port(port)?)
            }
        };
        (host.to_string(), port)
    } else {
        let mut parts = authority.split(':');
        let host = parts.next()?.to_string();
        let port = match parts.next() {
            None | Some("") => None,
            Some(value) => Some(parse_port(value)?),
        };
        if parts.next().is_some() {
            return None;
        }
        (host, port)
    };
    let tail = tail.split('#').next().unwrap_or("");
    let (path, query) = tail.split_once('?').unwrap_or((tail, ""));
    Some(Split {
        scheme,
        host,
        port,
        userinfo,
        path: path.into(),
        query: query.into(),
    })
}
fn parse_port(value: &str) -> Option<u16> {
    if value.is_empty() || !value.bytes().all(|ch| ch.is_ascii_digit()) {
        return None;
    }
    value.parse().ok()
}
fn ipv6(value: &str) -> Option<String> {
    let (address, scope) = match value.split_once('%') {
        Some((address, scope)) if !scope.is_empty() && !scope.contains('%') => {
            (address, Some(scope))
        }
        Some(_) => return None,
        None => (value, None),
    };
    let address = address.parse::<std::net::Ipv6Addr>().ok()?.to_string();
    Some(format!(
        "{address}{}",
        scope
            .map(|scope| format!("%{}", scope.to_ascii_lowercase()))
            .unwrap_or_default()
    ))
}

fn forbidden(ch: char) -> bool {
    matches!(
        get_general_category(ch),
        GeneralCategory::Control
            | GeneralCategory::Format
            | GeneralCategory::PrivateUse
            | GeneralCategory::Surrogate
            | GeneralCategory::Unassigned
    )
}
fn unquote(value: &str, plus: bool) -> Option<String> {
    let bytes = value.as_bytes();
    let mut out = Vec::new();
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] == b'%' {
            let raw = bytes.get(index + 1..index + 3)?;
            let digit = |ch: u8| match ch {
                b'0'..=b'9' => Some(ch - b'0'),
                b'a'..=b'f' => Some(ch - b'a' + 10),
                b'A'..=b'F' => Some(ch - b'A' + 10),
                _ => None,
            };
            out.push(digit(raw[0])? * 16 + digit(raw[1])?);
            index += 3;
        } else {
            out.push(if plus && bytes[index] == b'+' {
                b' '
            } else {
                bytes[index]
            });
            index += 1;
        }
    }
    String::from_utf8(out).ok()
}
fn encoded(value: &str) -> String {
    let mut out = String::new();
    for byte in value.bytes() {
        if byte.is_ascii_alphanumeric() || b"_.-~".contains(&byte) {
            out.push(byte as char);
        } else {
            out.push_str(&format!("%{byte:02X}"));
        }
    }
    out
}
#[derive(Clone)]
struct Normalized {
    domain: String,
    base: String,
    segments: Vec<String>,
    pairs: Vec<(String, String)>,
    overflow: bool,
}
fn normalize(value: &str) -> Option<Normalized> {
    let value = value.trim_matches(crate::backend::unicode::python_space);
    if value.is_empty() || value.chars().count() > 8000 || value.chars().any(forbidden) {
        return None;
    }
    let raw = split_url(value)?;
    if !["http", "https"].contains(&raw.scheme.as_str())
        || raw.userinfo
        || raw.host.is_empty()
        || raw.host.ends_with("..")
    {
        return None;
    }
    let host = raw.host.strip_suffix('.').unwrap_or(&raw.host);
    let host = if host.contains(':') {
        ipv6(host)?
    } else {
        if host.chars().all(|ch| ch.is_ascii_digit() || ch == '.') {
            host.parse::<std::net::Ipv4Addr>().ok()?;
        }
        let host = super::idna::ascii(host)?;
        if host.len() > 253
            || host.split('.').any(|label| {
                label.is_empty()
                    || label.len() > 63
                    || !label.as_bytes()[0].is_ascii_alphanumeric()
                    || !label.as_bytes()[label.len() - 1].is_ascii_alphanumeric()
                    || label
                        .bytes()
                        .any(|ch| !ch.is_ascii_alphanumeric() && ch != b'-')
            })
        {
            return None;
        }
        host
    };
    let rendered = if host.contains(':') {
        format!("[{host}]")
    } else {
        host.clone()
    };
    let port = raw
        .port
        .filter(|port| {
            !((raw.scheme == "http" && *port == 80) || (raw.scheme == "https" && *port == 443))
        })
        .map(|port| format!(":{port}"))
        .unwrap_or_default();
    let base = format!("{}://{rendered}{port}", raw.scheme);
    if base.chars().count() > 8000 {
        return None;
    }
    let path = if raw.path.is_empty() { "/" } else { &raw.path };
    if path.chars().any(forbidden) {
        return None;
    }
    let path = if path == "/" {
        "/"
    } else {
        let trimmed = path.trim_end_matches('/');
        if trimmed.is_empty() {
            "/"
        } else {
            trimmed
        }
    };
    let mut segments = path
        .trim_start_matches('/')
        .split('/')
        .map(str::to_owned)
        .collect::<Vec<_>>();
    if segments == [""] {
        segments.clear();
    }
    let parts = if raw.query.is_empty() {
        vec![]
    } else {
        raw.query.splitn(65, '&').collect::<Vec<_>>()
    };
    let overflow = parts.len() > 64;
    let pairs = parts
        .into_iter()
        .take(64)
        .filter_map(|part| {
            let (key, value) = part.split_once('=').unwrap_or((part, ""));
            Some((unquote(key, true)?.to_ascii_lowercase(), value.into()))
        })
        .collect();
    Some(Normalized {
        domain: format!("{host}{port}"),
        base,
        segments,
        pairs,
        overflow,
    })
}
#[derive(Clone)]
struct Classification {
    result: UrlLocator,
    item_container: Option<String>,
    title: Option<String>,
}
fn terminal(kind: &str, reason: &str) -> Classification {
    Classification {
        result: UrlLocator {
            kind: kind.into(),
            reason: Some(reason.into()),
            ..Default::default()
        },
        item_container: None,
        title: None,
    }
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn recognized(
    n: &Normalized,
    kind: &str,
    service: &str,
    family: &str,
    path: &str,
    query: &str,
    identity: Option<&str>,
    container: Option<&str>,
) -> Classification {
    let safe = format!(
        "{}{path}{}",
        n.base,
        if query.is_empty() {
            String::new()
        } else {
            format!("?{query}")
        }
    );
    if safe.chars().count() > 8000 {
        return terminal("unsafe", "unsafe-url");
    }
    let mut result = UrlLocator {
        kind: kind.into(),
        service: Some(service.into()),
        family: Some(family.into()),
        normalized_domain: Some(n.domain.clone()),
        canonical_base_url: Some(n.base.clone()),
        safe_locator_url: Some(safe),
        container_hint: container.map(str::to_owned),
        ..Default::default()
    };
    if kind == "item" {
        result.item_identity_kind = Some(family.into());
        result.item_identity = identity.map(str::to_owned);
    } else if kind == "structure" {
        result.reference_kind = Some(family.into());
        result.reference_identity = identity.map(str::to_owned);
    }
    Classification {
        result,
        item_container: None,
        title: None,
    }
}
fn item(
    n: &Normalized,
    service: &str,
    family: &str,
    identity: &str,
    container: Option<&str>,
    title: Option<String>,
    context: &str,
) -> Classification {
    let (path, query) = if service == "jira" {
        (format!("/browse/{identity}"), String::new())
    } else if let Some(container) = container {
        (
            format!("{context}/spaces/{}/pages/{identity}", encoded(container)),
            String::new(),
        )
    } else {
        (
            format!("{context}/pages/viewpage.action"),
            format!("pageId={identity}"),
        )
    };
    let mut result = recognized(
        n,
        "item",
        service,
        family,
        &path,
        &query,
        Some(identity),
        None,
    );
    result.item_container = container.map(str::to_owned);
    result.title = title;
    result
}
fn structure(
    n: &Normalized,
    service: &str,
    family: &str,
    identity: &str,
    path: &str,
    query: &str,
    container: Option<&str>,
) -> Classification {
    recognized(
        n,
        "structure",
        service,
        family,
        path,
        query,
        Some(identity),
        container,
    )
}
fn site(n: &Normalized, service: &str, family: &str, path: &str) -> Classification {
    recognized(n, "site", service, family, path, "", None, None)
}
fn project(value: &str) -> std::result::Result<Option<String>, ()> {
    let value = unquote(value, false).ok_or(())?.to_ascii_uppercase();
    let valid = valid_project(&value);
    Ok(valid.then_some(value))
}
fn valid_project(value: &str) -> bool {
    !value.is_empty()
        && value.chars().count() <= 300
        && value.as_bytes()[0].is_ascii_uppercase()
        && value
            .bytes()
            .all(|ch| ch.is_ascii_uppercase() || ch.is_ascii_digit() || ch == b'_')
}
fn issue(value: &str) -> std::result::Result<Option<String>, ()> {
    let value = unquote(value, false).ok_or(())?.to_ascii_uppercase();
    if value.chars().count() > 300 {
        return Ok(None);
    }
    let valid = value.rsplit_once('-').is_some_and(|(key, id)| {
        valid_project(key)
            && !id.is_empty()
            && id.as_bytes()[0] != b'0'
            && id.bytes().all(|ch| ch.is_ascii_digit())
    });
    Ok(valid.then_some(value))
}
fn decimal(value: &str) -> Option<String> {
    if value.is_empty()
        || value.chars().count() > 300
        || !value.bytes().all(|ch| ch.is_ascii_digit())
        || value.bytes().all(|ch| ch == b'0')
    {
        None
    } else {
        Some(value.trim_start_matches('0').into())
    }
}
fn decimal_segment(value: &str) -> std::result::Result<Option<String>, ()> {
    Ok(decimal(&unquote(value, false).ok_or(())?))
}
fn text_identity(value: &str) -> std::result::Result<Option<String>, ()> {
    let value = unquote(value, false).ok_or(())?.nfkc().collect::<String>();
    let valid = !value.is_empty()
        && value.chars().count() <= 300
        && !value.trim().is_empty()
        && !['/', '\\'].iter().any(|ch| value.contains(*ch))
        && value != "."
        && value != ".."
        && !value.chars().any(forbidden);
    Ok(valid.then_some(value))
}
fn query(n: &Normalized, names: &[&str]) -> std::result::Result<Vec<String>, ()> {
    if n.overflow {
        return Ok(vec![]);
    }
    n.pairs
        .iter()
        .filter(|(key, _)| names.iter().any(|name| key.eq_ignore_ascii_case(name)))
        .map(|(_, value)| unquote(value, true).ok_or(()))
        .collect()
}
fn one_decimal(n: &Normalized, names: &[&str]) -> std::result::Result<Option<String>, ()> {
    let values = query(n, names)?;
    Ok(if values.len() == 1 {
        decimal(&values[0])
    } else {
        None
    })
}
fn one_issue(n: &Normalized) -> std::result::Result<Option<String>, ()> {
    let values = query(n, &["selectedissue"])?;
    if values.len() != 1 {
        return Ok(None);
    }
    let value = values[0].to_ascii_uppercase();
    let valid = value.chars().count() <= 300
        && value.rsplit_once('-').is_some_and(|(key, id)| {
            valid_project(key)
                && !id.is_empty()
                && id.as_bytes()[0] != b'0'
                && id.bytes().all(|ch| ch.is_ascii_digit())
        });
    Ok(valid.then_some(value))
}
fn one_project(n: &Normalized) -> std::result::Result<Option<String>, ()> {
    let values = query(n, &["projectkey"])?;
    if values.len() != 1 {
        return Ok(None);
    }
    let value = values[0].to_ascii_uppercase();
    let valid = !value.is_empty()
        && value.chars().count() <= 300
        && value.as_bytes()[0].is_ascii_uppercase()
        && value
            .bytes()
            .all(|ch| ch.is_ascii_uppercase() || ch.is_ascii_digit() || ch == b'_');
    Ok(valid.then_some(value))
}
fn context(segments: &[String]) -> (String, &[String]) {
    if segments
        .first()
        .is_some_and(|value| ["wiki", "confluence"].contains(&value.to_ascii_lowercase().as_str()))
    {
        (
            format!("/{}", segments[0].to_ascii_lowercase()),
            &segments[1..],
        )
    } else {
        (String::new(), segments)
    }
}
fn path_item(n: &Normalized) -> std::result::Result<Option<Classification>, ()> {
    let s = &n.segments;
    let lower = s.iter().map(|v| v.to_ascii_lowercase()).collect::<Vec<_>>();
    for (prefix, length, project_index) in [
        (vec!["browse"], 2, None),
        (vec!["issues"], 2, None),
        (vec!["jira", "core", "projects"], 6, Some(3)),
        (vec!["jira", "software", "projects"], 6, Some(3)),
        (vec!["jira", "software", "c", "projects"], 7, Some(4)),
        (vec!["jira", "servicedesk", "projects"], 6, Some(3)),
    ] {
        if !lower.starts_with(&prefix.iter().map(|v| v.to_string()).collect::<Vec<_>>())
            || s.len() != length
        {
            continue;
        }
        if let Some(index) = project_index {
            if project(&s[index])?.is_none() || lower[index + 1] != "issues" {
                continue;
            }
        }
        if let Some(issue) = issue(&s[length - 1])? {
            return Ok(Some(item(
                n,
                "jira",
                "jira_issue",
                &issue,
                issue.rsplit_once('-').map(|(project, _)| project),
                None,
                "",
            )));
        }
    }
    if lower.starts_with(&["servicedesk".into(), "customer".into(), "portal".into()])
        && s.len() == 5
    {
        let portal = decimal_segment(&s[3])?;
        let issue = issue(&s[4])?;
        if portal.is_some() {
            if let Some(issue) = issue {
                return Ok(Some(item(
                    n,
                    "jira",
                    "jira_issue",
                    &issue,
                    issue.rsplit_once('-').map(|(project, _)| project),
                    None,
                    "",
                )));
            }
        }
    }
    let (context, segments) = context(s);
    let lower = segments
        .iter()
        .map(|v| v.to_ascii_lowercase())
        .collect::<Vec<_>>();
    let mut page = None;
    let mut space = None;
    let mut title = None;
    if [4, 5].contains(&segments.len()) && lower[0] == "spaces" && lower[2] == "pages" {
        page = Some(&segments[3]);
        space = text_identity(&segments[1])?;
        if segments.len() == 5 {
            title = unquote(&segments[4], false)
                .filter(|v| !v.is_empty())
                .map(|v| v.nfkc().collect());
        }
    } else if [2, 3].contains(&segments.len()) && lower[0] == "pages" {
        page = Some(&segments[1]);
        if segments.len() == 3 {
            title = unquote(&segments[2], false)
                .filter(|v| !v.is_empty())
                .map(|v| v.nfkc().collect());
        }
    }
    if let Some(page) = page {
        if let Some(page) = decimal_segment(page)? {
            return Ok(Some(item(
                n,
                "confluence",
                "confluence_page",
                &page,
                space.as_deref(),
                title,
                &context,
            )));
        }
    }
    Ok(None)
}
fn structure_or_site(n: &Normalized) -> std::result::Result<Option<Classification>, ()> {
    let s = &n.segments;
    let lower = s.iter().map(|v| v.to_ascii_lowercase()).collect::<Vec<_>>();
    let eq = |parts: &[&str]| lower.iter().map(String::as_str).eq(parts.iter().copied());
    if eq(&["secure", "rapidboard.jspa"]) {
        let Some(id) = one_decimal(n, &["rapidview"])? else {
            return Ok(Some(site(
                n,
                "jira",
                "jira_board",
                "/secure/RapidBoard.jspa",
            )));
        };
        let hint = one_project(n)?;
        let query = format!(
            "rapidView={id}{}",
            hint.as_ref()
                .map(|hint| format!("&projectKey={hint}"))
                .unwrap_or_default()
        );
        return Ok(Some(structure(
            n,
            "jira",
            "jira_board",
            &id,
            "/secure/RapidBoard.jspa",
            &query,
            hint.as_deref(),
        )));
    }
    if eq(&["issues"])
        || eq(&["secure", "issuenavigator.jspa"])
        || eq(&["secure", "managefilters.jspa"])
    {
        return Ok(Some(
            match one_decimal(n, &["filter", "requestid", "filterid"])? {
                Some(id) => structure(
                    n,
                    "jira",
                    "jira_filter",
                    &id,
                    "/issues",
                    &format!("filter={id}"),
                    None,
                ),
                None => site(n, "jira", "jira_filter", "/issues"),
            },
        ));
    }
    if eq(&["secure", "dashboard.jspa"]) {
        return Ok(Some(match one_decimal(n, &["selectpageid"])? {
            Some(id) => structure(
                n,
                "jira",
                "jira_dashboard",
                &id,
                "/secure/Dashboard.jspa",
                &format!("selectPageId={id}"),
                None,
            ),
            None => site(n, "jira", "jira_dashboard", "/secure/Dashboard.jspa"),
        }));
    }
    if lower.starts_with(&["servicedesk".into(), "customer".into(), "portal".into()]) {
        let id = if s.len() < 4 {
            None
        } else {
            decimal_segment(&s[3])?
        };
        return Ok(Some(match id {
            Some(id) => structure(
                n,
                "jira",
                "jira_service_portal",
                &id,
                &format!("/servicedesk/customer/portal/{id}"),
                "",
                None,
            ),
            None => site(
                n,
                "jira",
                "jira_service_portal",
                "/servicedesk/customer/portal",
            ),
        }));
    }
    if lower.starts_with(&["jira".into(), "servicedesk".into(), "projects".into()]) {
        if s.len() < 4 {
            return Ok(None);
        }
        let Some(project) = project(&s[3])? else {
            return Ok(None);
        };
        return Ok(Some(structure(
            n,
            "jira",
            "jira_service_project",
            &project,
            &format!("/jira/servicedesk/projects/{project}"),
            "",
            Some(&project),
        )));
    }
    for prefix in [
        vec!["projects"],
        vec!["jira", "core", "projects"],
        vec!["jira", "software", "projects"],
        vec!["jira", "software", "c", "projects"],
        vec!["plugins", "servlet", "project-config"],
    ] {
        if !lower.starts_with(&prefix.iter().map(|v| v.to_string()).collect::<Vec<_>>()) {
            continue;
        }
        let index = prefix.len();
        if s.len() <= index {
            return Ok(None);
        }
        let project = project(&s[index])?;
        let board_index = index + 1;
        let modern = prefix == ["jira", "software", "projects"]
            || prefix == ["jira", "software", "c", "projects"];
        if modern && s.len() > board_index && lower[board_index] == "boards" {
            let Some(project) = project else {
                return Ok(None);
            };
            let id = if s.len() <= board_index + 1 {
                None
            } else {
                decimal_segment(&s[board_index + 1])?
            };
            let path = format!("/jira/software/projects/{project}/boards");
            return Ok(Some(match id {
                Some(id) => structure(
                    n,
                    "jira",
                    "jira_board",
                    &id,
                    &format!("{path}/{id}"),
                    "",
                    Some(&project),
                ),
                None => site(n, "jira", "jira_board", &path),
            }));
        }
        let Some(project) = project else {
            return Ok(None);
        };
        return Ok(Some(structure(
            n,
            "jira",
            "jira_project",
            &project,
            &format!("/projects/{project}"),
            "",
            Some(&project),
        )));
    }
    let (context, segments) = context(s);
    let lower = segments
        .iter()
        .map(|v| v.to_ascii_lowercase())
        .collect::<Vec<_>>();
    if lower == ["viewpage.action"]
        || lower == ["pages", "viewpage.action"]
        || lower.first().is_some_and(|v| v == "pages")
        || (lower.len() >= 3 && lower[0] == "spaces" && lower[2] == "pages")
    {
        return Ok(None);
    }
    if lower
        .first()
        .is_some_and(|v| ["spaces", "display"].contains(&v.as_str()))
    {
        if segments.len() < 2 {
            return Ok(None);
        }
        if lower[2..].iter().any(|v| {
            [
                "attachment",
                "attachments",
                "blog",
                "blogs",
                "database",
                "databases",
                "embed",
                "embeds",
                "whiteboard",
                "whiteboards",
            ]
            .contains(&v.as_str())
        }) {
            return Ok(None);
        }
        let Some(space) = text_identity(&segments[1])? else {
            return Ok(None);
        };
        return Ok(Some(structure(
            n,
            "confluence",
            "confluence_space",
            &space,
            &format!("{context}/spaces/{}", encoded(&space)),
            "",
            Some(&space),
        )));
    }
    Ok(None)
}
fn query_item(
    n: &Normalized,
    structure: Option<&Classification>,
) -> std::result::Result<Option<Classification>, ()> {
    let lower = n
        .segments
        .iter()
        .map(|v| v.to_ascii_lowercase())
        .collect::<Vec<_>>();
    let jira = lower == ["browse"]
        || structure.is_some_and(|v| {
            ["structure", "site"].contains(&v.result.kind.as_str())
                && v.result.service.as_deref() == Some("jira")
        });
    if jira {
        if let Some(issue) = one_issue(n)? {
            return Ok(Some(item(
                n,
                "jira",
                "jira_issue",
                &issue,
                issue.rsplit_once('-').map(|(project, _)| project),
                None,
                "",
            )));
        }
    }
    let (context, segments) = context(&n.segments);
    let lower = segments
        .iter()
        .map(|v| v.to_ascii_lowercase())
        .collect::<Vec<_>>();
    if lower == ["viewpage.action"] || lower == ["pages", "viewpage.action"] {
        if let Some(page) = one_decimal(n, &["pageid"])? {
            return Ok(Some(item(
                n,
                "confluence",
                "confluence_page",
                &page,
                None,
                None,
                &context,
            )));
        }
    }
    Ok(None)
}
fn unsafe_query(n: &Normalized) -> bool {
    let mut path_only = n.clone();
    path_only.pairs.clear();
    path_only.overflow = false;
    let lower = n
        .segments
        .iter()
        .map(|v| v.to_ascii_lowercase())
        .collect::<Vec<_>>();
    let path = path_item(&path_only).ok().flatten();
    let family = structure_or_site(&path_only).ok().flatten();
    let mut allowed = Vec::new();
    if lower == ["browse"]
        || path
            .as_ref()
            .is_some_and(|v| v.result.kind == "item" && v.result.service.as_deref() == Some("jira"))
        || family.as_ref().is_some_and(|v| {
            ["structure", "site"].contains(&v.result.kind.as_str())
                && v.result.service.as_deref() == Some("jira")
        })
    {
        allowed.push("selectedissue");
    }
    if lower == ["secure", "rapidboard.jspa"] {
        allowed.extend(["rapidview", "projectkey"]);
    }
    if lower == ["issues"]
        || lower == ["secure", "issuenavigator.jspa"]
        || lower == ["secure", "managefilters.jspa"]
    {
        allowed.extend(["filter", "requestid", "filterid"]);
    }
    if lower == ["secure", "dashboard.jspa"] {
        allowed.push("selectpageid");
    }
    let (_, segments) = context(&n.segments);
    let lower = segments
        .iter()
        .map(|v| v.to_ascii_lowercase())
        .collect::<Vec<_>>();
    if lower == ["viewpage.action"] || lower == ["pages", "viewpage.action"] {
        allowed.push("pageid");
    }
    n.pairs
        .iter()
        .any(|(name, value)| allowed.contains(&name.as_str()) && unquote(value, true).is_none())
}
fn classify(value: &str) -> Classification {
    let Some(n) = normalize(value) else {
        return terminal("unsafe", "unsafe-url");
    };
    if n.segments.iter().any(|v| v.eq_ignore_ascii_case("rest")) {
        return terminal("unsupported", "unsupported-url");
    }
    if unsafe_query(&n) {
        return terminal("unsafe", "unsafe-url");
    }
    let result = (|| -> std::result::Result<Classification, ()> {
        if let Some(value) = path_item(&n)? {
            return Ok(value);
        }
        let structure = structure_or_site(&n)?;
        if let Some(value) = query_item(&n, structure.as_ref())? {
            return Ok(value);
        }
        Ok(structure.unwrap_or_else(|| terminal("unsupported", "unsupported-url")))
    })();
    result.unwrap_or_else(|_| terminal("unsafe", "unsafe-url"))
}
pub fn describe_atlassian_url(value: &str) -> UrlLocator {
    classify(value).result
}
pub fn atlassian_item_container_hint(value: &str) -> Option<String> {
    let result = classify(value);
    (result.result.kind == "item")
        .then_some(result.item_container)
        .flatten()
}
pub fn atlassian_page_title_hint(value: &str) -> Option<String> {
    let result = classify(value);
    if result.result.kind != "item" || result.result.service.as_deref() != Some("confluence") {
        return None;
    }
    result
        .title
        .filter(|value| !value.is_empty() && !value.chars().any(forbidden))
        .map(|value| value.chars().take(500).collect())
}
pub fn atlassian_locator_identity(locator: &UrlLocator) -> Option<Vec<String>> {
    let mut result = vec![
        "localbrain.atlassian-locator.v1".into(),
        locator.normalized_domain.clone()?,
        locator.service.clone()?,
        locator.kind.clone(),
    ];
    match locator.kind.as_str() {
        "item" => {
            result.push(locator.item_identity_kind.clone()?);
            result.push(locator.item_identity.clone()?);
        }
        "structure" => {
            result.push(locator.reference_kind.clone()?);
            result.push(locator.reference_identity.clone()?);
        }
        "site" => result.push(locator.family.clone()?),
        _ => return None,
    }
    Some(result)
}
