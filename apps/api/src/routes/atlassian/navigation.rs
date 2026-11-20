use localbrain_core::backend::{search, unicode, BackendError, Result};
use serde_json::{json, Map, Value};
pub const ADVANCED_FIELDS: &[&str] = &[
    "coverage",
    "freshness",
    "attention",
    "topic_id",
    "tag_id",
    "workstream_id",
];
pub const BROWSE_FIELDS: &[&str] = &[
    "q",
    "source_instance_id",
    "item_type",
    "site_id",
    "space_id",
    "structural_scope",
    "coverage",
    "freshness",
    "attention",
    "topic_id",
    "tag_id",
    "workstream_id",
];
pub const EXPLORER_FIELDS: &[&str] = &[
    "q",
    "source_instance_id",
    "item_type",
    "site_id",
    "space_id",
    "structural_scope",
    "coverage",
    "freshness",
    "attention",
    "topic_id",
    "tag_id",
    "workstream_id",
    "item",
    "reference",
];
pub fn normalize_view(value: &str) -> String {
    let normalized = unicode::lowercase(value.trim_matches(unicode::python_space));
    match normalized.as_str() {
        "confluence" | "wiki" => "wiki",
        "jira" => "jira",
        _ => "all",
    }
    .into()
}
pub fn view_for_service(value: &str) -> &'static str {
    if value == "confluence" {
        "wiki"
    } else {
        "jira"
    }
}
pub fn service(view: &str) -> Value {
    match view {
        "jira" => json!("jira"),
        "wiki" => json!("confluence"),
        _ => Value::Null,
    }
}
pub fn connections_view(value: &str) -> &'static str {
    if ["wiki", "confluence"]
        .contains(&unicode::lowercase(value.trim_matches(unicode::python_space)).as_str())
    {
        "wiki"
    } else {
        "jira"
    }
}
pub fn scalar(value: &Value) -> String {
    match value {
        Value::String(value) => value.clone(),
        Value::Bool(value) => if *value { "True" } else { "False" }.into(),
        Value::Null => "None".into(),
        _ => localbrain_core::backend::json::canonical(value).unwrap_or_else(|_| value.to_string()),
    }
}
pub fn browse_url(view: &str, filters: &Value, overrides: &[(&str, Value)]) -> String {
    let mut state: Map<String, Value> = EXPLORER_FIELDS
        .iter()
        .map(|key| ((*key).into(), filters[key].clone()))
        .collect();
    for (key, value) in overrides {
        state.insert((*key).into(), value.clone());
    }
    let mut pairs = vec![("view", normalize_view(view))];
    for (key, value) in &state {
        if !value.is_null() && value != "" {
            pairs.push((key.as_str(), scalar(value)));
        }
    }
    format!("/atlassian?{}", search::urlencode(&pairs))
}
pub fn repeated_state(query: &str) -> bool {
    let mut seen = std::collections::BTreeSet::new();
    url::form_urlencoded::parse(query.as_bytes()).any(|(key, _)| {
        (key == "view" || EXPLORER_FIELDS.contains(&key.as_ref())) && !seen.insert(key.into_owned())
    })
}
pub fn selection(value: Option<&str>, reference: bool) -> Result<Option<i64>> {
    let Some(raw) = value.filter(|value| !value.is_empty()) else {
        return Ok(None);
    };
    let raw = raw.trim_matches(unicode::python_space);
    let id = (!raw.is_empty()
        && raw.is_ascii()
        && raw.len() <= 19
        && raw.bytes().all(|ch| ch.is_ascii_digit()))
    .then(|| raw.parse::<i64>().ok())
    .flatten()
    .filter(|id| *id >= 1);
    id.map(Some).ok_or_else(|| {
        BackendError::invalid(
            "invalid-selection",
            if reference {
                "선택한 Atlassian 구조 참조가 올바르지 않습니다."
            } else {
                "선택한 Atlassian 링크/문서가 올바르지 않습니다."
            },
        )
    })
}
pub fn relative_parts(value: &str) -> Option<(String, String)> {
    let cleaned = value
        .trim_start_matches(|ch: char| ch <= '\u{20}')
        .replace(['\t', '\r', '\n'], "");
    let clean = cleaned.split('#').next().unwrap_or("");
    if clean.starts_with("//") {
        return None;
    }
    let (path, query) = clean.split_once('?').unwrap_or((clean, ""));
    if path.split_once(':').is_some_and(|(scheme, _)| {
        scheme
            .as_bytes()
            .first()
            .is_some_and(u8::is_ascii_alphabetic)
            && scheme
                .bytes()
                .all(|ch| ch.is_ascii_alphanumeric() || b"+-.".contains(&ch))
    }) {
        return None;
    }
    Some((path.into(), query.into()))
}
pub fn notice(value: Option<&str>) -> Option<&'static str> {
    let value = value.unwrap_or("").chars().take(80).collect::<String>();
    match value.as_str() {
        "connection-created" => Some("Site에 원격 접근 경로를 연결했습니다."),
        "connection-updated" => Some("원격 접근 경로 설정을 저장했습니다."),
        "item-created" => Some("Atlassian 링크/문서를 로컬에 등록했습니다."),
        "item-reused" => Some("이미 등록된 Atlassian 링크/문서를 열었습니다."),
        "space-created" => Some("Space를 로컬에 등록했습니다."),
        "space-reused" => Some("이미 등록된 Space를 열었습니다."),
        "catalog-started" => Some("Space 후보 조회 maintenance Run을 시작했습니다."),
        _ => None,
    }
}
pub fn connections_url(
    view: &str,
    selected_notice: Option<&str>,
    catalog: Option<&str>,
    fragment: Option<&str>,
) -> String {
    let mut pairs = vec![("view", connections_view(view).into())];
    if let Some(value) = selected_notice.filter(|value| notice(Some(value)).is_some()) {
        pairs.push(("notice", value.into()));
    }
    if let Some(value) = catalog.filter(|value| !value.is_empty() && value.chars().count() <= 300) {
        pairs.push(("catalog_run", value.into()));
    }
    let mut result = format!("/atlassian/connections?{}", search::urlencode(&pairs));
    if let Some(fragment) = fragment.filter(|value| !value.is_empty()) {
        result.push('#');
        result.push_str(&search::quote(fragment));
    }
    result
}
pub fn receipt_url(return_to: &str, token: &str) -> String {
    let (path, query) =
        relative_parts(return_to).unwrap_or_else(|| ("/atlassian".into(), String::new()));
    let mut pairs = url::form_urlencoded::parse(query.as_bytes())
        .filter(|(key, _)| key != "sync_receipt")
        .map(|(key, value)| (key.into_owned(), value.into_owned()))
        .collect::<Vec<_>>();
    pairs.push(("sync_receipt".into(), token.into()));
    let query = search::urlencode(
        &pairs
            .iter()
            .map(|(key, value)| (key.as_str(), value.clone()))
            .collect::<Vec<_>>(),
    );
    format!("{path}?{query}#atlassian-sync-result")
}
pub fn explorer_urls(browse: &mut Value, view: &str) -> Value {
    let filters = browse["filters"].clone();
    let reset = [
        ("site_id", Value::Null),
        ("space_id", Value::Null),
        ("structural_scope", Value::Null),
    ];
    let services = ["all", "jira", "wiki"]
        .into_iter()
        .map(|view| (view, browse_url(view, &filters, &reset)))
        .collect::<std::collections::BTreeMap<_, _>>();
    if let Some(sites) = browse["hierarchy"]["sites"].as_array_mut() {
        for site in sites {
            let id = site["id"].clone();
            site["href"] = json!(browse_url(
                view,
                &filters,
                &[
                    ("site_id", id.clone()),
                    ("space_id", Value::Null),
                    ("structural_scope", Value::Null)
                ]
            ));
            site["active"] = json!(
                filters["site_id"] == id
                    && filters["space_id"].is_null()
                    && filters["structural_scope"].is_null()
            );
            if let Some(containers) = site["containers"].as_array_mut() {
                for container in containers {
                    let space = container["kind"] == "space";
                    let structural = container["structural_scope"].clone();
                    container["href"] = json!(browse_url(
                        view,
                        &filters,
                        &[
                            ("site_id", id.clone()),
                            (
                                "space_id",
                                if space {
                                    container["id"].clone()
                                } else {
                                    Value::Null
                                }
                            ),
                            ("structural_scope", structural.clone())
                        ]
                    ));
                    container["active"] = json!(
                        filters["site_id"] == id
                            && if space {
                                filters["space_id"] == container["id"]
                            } else {
                                filters["structural_scope"] == structural
                            }
                    );
                }
            }
        }
    }
    json!({"services":services,"root":browse_url(view,&filters,&reset),"clear_filters":browse_url(view,&filters,&ADVANCED_FIELDS.iter().map(|field|(*field,Value::Null)).collect::<Vec<_>>()),"reset":"/atlassian"})
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn explorer_navigation_and_selection_match_complete_frozen_python_outputs() {
        let cases: Vec<Value> = serde_json::from_str(include_str!(
            "../../../tests/fixtures/native-atlassian-navigation.json"
        ))
        .unwrap();
        for case in cases {
            let a = &case["args"];
            let result: Result<Value> = match case["op"].as_str().unwrap() {
                "view" => Ok(json!([
                    normalize_view(a[0].as_str().unwrap()),
                    connections_view(a[0].as_str().unwrap())
                ])),
                "selection" => {
                    selection(a[0].as_str(), a[1].as_bool().unwrap()).map(|value| json!(value))
                }
                "repeated" => Ok(json!(repeated_state(a[0].as_str().unwrap()))),
                "browse" => {
                    let pairs = a[2]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|pair| (pair[0].as_str().unwrap(), pair[1].clone()))
                        .collect::<Vec<_>>();
                    Ok(json!(browse_url(a[0].as_str().unwrap(), &a[1], &pairs)))
                }
                "connections" => Ok(json!(connections_url(
                    a[0].as_str().unwrap(),
                    a[1].as_str(),
                    a[2].as_str(),
                    a[3].as_str()
                ))),
                "receipt" => Ok(json!(receipt_url(
                    a[0].as_str().unwrap(),
                    a[1].as_str().unwrap()
                ))),
                "explorer" => {
                    let mut browse = a[0].clone();
                    let urls = explorer_urls(&mut browse, a[1].as_str().unwrap());
                    Ok(json!({"urls":urls,"browse":browse}))
                }
                _ => panic!("unknown fixture op"),
            };
            if let Some(error) = case.get("error") {
                let actual = result.unwrap_err();
                assert_eq!(actual.code, error["code"], "{case}");
                assert_eq!(actual.message, error["message"], "{case}");
            } else {
                assert_eq!(result.unwrap(), case["value"], "{case}");
            }
        }
    }
}
