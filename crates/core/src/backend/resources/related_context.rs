//! Direct Session evidence is enriched without optional registrations or curation.
use crate::backend::{
    references::{external_detail, external_href},
    sessions::references::session_reference_projection,
    unicode, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::collections::BTreeMap;
pub const RELATED_CONTEXT_LIMIT: usize = 100;
fn label(kind: &str, outcome: Option<&str>) -> Option<&'static str> {
    match (kind, outcome) {
        ("resource_read", Some("success")) => Some("MCP 조회"),
        ("resource_read", Some("failure")) => Some("MCP 조회 실패"),
        ("user_mention", None) => Some("사용자 메시지에서 언급"),
        ("assistant_mention", None) => Some("Agent 응답에서 언급"),
        ("tool_result", None) => Some("도구 결과에서 확인"),
        _ => None,
    }
}
fn nonempty<'a>(value: &'a Value, key: &str) -> Option<&'a str> {
    value[key].as_str().filter(|s| !s.is_empty())
}
fn direct_item(item: &Value) -> Value {
    let url = item["target_kind"] == "url";
    let href = if url {
        nonempty(item, "destination").and_then(external_href)
    } else {
        item["destination"].as_str().map(ToOwned::to_owned)
    };
    let mut detail = if url {
        href.as_deref().and_then(external_detail)
    } else {
        nonempty(item, "relative_path")
            .or_else(|| item["locator"].as_str())
            .map(ToOwned::to_owned)
    };
    let identity = if url && nonempty(item, "product").is_none() {
        href.as_deref()
            .and_then(external_detail)
            .map(|s| json!(s))
            .unwrap_or_else(|| item["identity"].clone())
    } else {
        item["identity"].clone()
    };
    if detail.as_deref().is_some_and(|detail| {
        unicode::casefold(detail) == unicode::casefold(identity.as_str().unwrap_or(""))
    }) {
        detail = None;
    }
    let evidence = item["evidence"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|summary| {
            label(
                summary["kind"].as_str().unwrap_or(""),
                summary["outcome"].as_str(),
            )
            .map(|label| {
                let mut value = summary.clone();
                value["label"] = json!(label);
                value
            })
        })
        .collect::<Vec<_>>();
    let kind = if url {
        match item["product"].as_str() {
            Some("jira") => "Jira",
            Some("confluence") => "Confluence",
            _ => "URL",
        }
    } else {
        "Markdown"
    };
    json!({"resource_id":item["resource_id"],"entity_type":if url{"external"}else{"document"},"entity_id":item["context_document_id"],"kind_label":kind,"availability":if href.is_some(){"available"}else{"unavailable"},"availability_label":href.is_none().then_some("열 수 없음"),"href":href,"external":url&&href.is_some(),"target_key":item["target_key"],"identity":identity,"detail":detail,"evidence":evidence,"observed_at":item["observed_at"]})
}
fn sections(items: &[Value]) -> Vec<Value> {
    let mut sections: BTreeMap<String, Vec<Value>> = BTreeMap::new();
    for item in items {
        let label = item["kind_label"]
            .as_str()
            .filter(|s| !s.is_empty())
            .unwrap_or("기타")
            .trim_matches(unicode::python_space)
            .to_uppercase();
        sections.entry(label).or_default().push(item.clone());
    }
    let mut sections = sections.into_iter().collect::<Vec<_>>();
    sections.sort_by_key(|(label, _)| unicode::casefold(label));
    sections
        .into_iter()
        .map(|(label, rows)| json!({"label":label,"rows":rows}))
        .collect()
}
pub fn session_related_context_error() -> Value {
    json!({"state":"error","groups":[],"item_count":0})
}
pub fn session_related_context(conn: &Connection, id: i64) -> Result<Value> {
    let projection = session_reference_projection(conn, id)?;
    let direct = projection["items"]
        .as_array()
        .into_iter()
        .flatten()
        .map(direct_item)
        .collect::<Vec<_>>();
    let count = direct.len();
    let mut notices = Vec::new();
    if projection["partial"] == true {
        notices.push(format!(
            "총 {}개 중 {}개까지 확인했습니다.",
            projection["observed_total"], projection["retained_total"]
        ));
    }
    if projection["stale"] == true {
        notices.push("참조 동기화가 완료되지 않아 이전 결과일 수 있습니다.".into());
    }
    let ordered = sections(&direct)
        .into_iter()
        .flat_map(|section| section["rows"].as_array().unwrap().clone())
        .collect::<Vec<_>>();
    let split = ordered.len().min(RELATED_CONTEXT_LIMIT);
    let initial = ordered[..split].to_vec();
    let additional = ordered[split..].to_vec();
    let first_sections = sections(&initial);
    let mut more_sections = sections(&additional);
    if first_sections
        .last()
        .zip(more_sections.first())
        .is_some_and(|(first, more)| first["label"] == more["label"])
    {
        more_sections[0]["continuation"] = json!(true);
    }
    let state = if count == 0 && notices.is_empty() {
        "empty"
    } else if projection["partial"] == true || projection["stale"] == true {
        "partial"
    } else {
        "ready"
    };
    Ok(
        json!({"state":state,"item_count":count,"groups":[{"key":"direct","label":"이 세션의 참조","total":projection["observed_total"],"items":ordered,"initial_items":initial,"additional_items":additional,"initial_sections":first_sections,"additional_sections":more_sections,"overflow_count":ordered.len()-split,"partial":projection["partial"],"stale":projection["stale"],"notices":notices}]}),
    )
}
