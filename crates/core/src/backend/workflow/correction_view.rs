//! Pure assertion summaries and reviewable correction controls.
use super::{
    assertions::{action_after_meaning, workflow_boundary_key},
    projection::{invalid, CLOSURE_REASONS},
};
use crate::backend::{unicode, value_registry::visible_value_label, Result};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub fn workflow_relation_id(source: &str, target: &str) -> Result<String> {
    Ok(format!(
        "workflow-relation-{}",
        workflow_boundary_key("relation", source, Some(target))?
    ))
}
pub(super) fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(v) => v.as_f64().is_none_or(|v| v != 0.0),
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
pub(super) fn text<'a>(value: &'a Value, fallback: &'a str) -> &'a str {
    value.as_str().filter(|s| !s.is_empty()).unwrap_or(fallback)
}
pub(super) fn values(value: &Value) -> &[Value] {
    value.as_array().map(Vec::as_slice).unwrap_or(&[])
}
pub(super) fn authority_label(value: &str) -> Option<&'static str> {
    Some(match value {
        "observed" => "관측",
        "deterministic-candidate" => "규칙 기반 후보",
        "explicit-organization" => "직접 정리",
        "user-confirmed" => "사용자 확인",
        _ => return None,
    })
}
fn strict_authority(value: &str) -> Result<&'static str> {
    authority_label(value).ok_or_else(|| invalid("workflow authority is not presentable"))
}
fn value_label(family: &str, value: &Value) -> Result<String> {
    visible_value_label(family, value, None)
}
fn meaning(value: &Value) -> Result<String> {
    value_label("workflow-assertion.meaning", value)
}
fn closure(value: &Value) -> Result<String> {
    visible_value_label("workflow-assertion.closure-reason", value, Some("null"))
}
pub(super) fn episode_title(episode: &Value) -> String {
    episode["display_title"]
        .as_str()
        .filter(|s| !s.trim_matches(unicode::python_space).is_empty())
        .unwrap_or("제목 없는 Session")
        .into()
}
fn title(episodes: &BTreeMap<String, Value>, key: Option<&str>) -> Option<String> {
    key.map(|key| {
        episodes
            .get(key)
            .map(episode_title)
            .unwrap_or_else(|| "현재 범위 밖 Episode".into())
    })
}
fn identity(value: &Value, field: &str) -> Result<Option<i64>> {
    if value.is_null() {
        return Ok(None);
    }
    value
        .as_i64()
        .filter(|v| *v > 0)
        .map(Some)
        .ok_or_else(|| invalid(&format!("{field} is malformed")))
}
fn resolution_reason(value: &str) -> Option<&'static str> {
    Some(match value {
        "missing-source-episode" => "출발 Episode가 현재 범위에 없습니다",
        "missing-endpoint" => "한쪽 Episode가 현재 범위에 없습니다",
        "endpoint-time-order" => "관측 시간 순서를 확인할 수 없습니다",
        "cycle" => "순환 경로를 만들 수 있어 적용하지 않았습니다",
        "contradictory-incoming-boundary" => "도착 Episode에 다른 진입 경계가 있습니다",
        _ => return None,
    })
}
fn assertion_view(raw: &Value, episodes: &BTreeMap<String, Value>) -> Result<Value> {
    for field in [
        "boundary_key",
        "boundary_kind",
        "assertion_kind",
        "source_episode_key",
        "before_meaning",
        "after_meaning",
        "authority",
        "resolution",
        "created_at",
    ] {
        if !raw[field].is_string() {
            return Err(invalid("workflow assertion summary is malformed"));
        }
    }
    let id = identity(&raw["id"], "assertion id")?;
    let supersedes = identity(&raw["supersedes_assertion_id"], "superseded assertion id")?;
    let restored = identity(&raw["restored_assertion_id"], "restored assertion id")?;
    let kind = raw["boundary_kind"].as_str().unwrap();
    let source = raw["source_episode_key"].as_str().unwrap();
    // A malformed non-string target cannot form a valid stable Episode key.
    let target = if raw["target_episode_key"].is_null() {
        None
    } else {
        Some(
            raw["target_episode_key"]
                .as_str()
                .ok_or_else(|| invalid("workflow assertion target is malformed"))?,
        )
    };
    if kind == "relation" && target.is_none() {
        return Err(invalid("workflow relation assertion has no target"));
    }
    if kind == "lifecycle" && target.is_some() {
        return Err(invalid("workflow lifecycle assertion has a target"));
    }
    if !["relation", "lifecycle"].contains(&kind) {
        return Err(invalid("workflow assertion boundary is not presentable"));
    }
    let boundary = workflow_boundary_key(kind, source, target)?;
    if raw["boundary_key"] != boundary {
        return Err(invalid(
            "workflow assertion boundary identity is inconsistent",
        ));
    }
    let resolution = raw["resolution"].as_str().unwrap();
    let resolution_label = match resolution {
        "applied" => "현재 적용됨",
        "unresolved" => "현재 범위에서 적용 대기",
        _ => return Err(invalid("workflow assertion resolution is not presentable")),
    };
    let reason_label = if raw["resolution_reason"].is_null() {
        None
    } else {
        Some(
            raw["resolution_reason"]
                .as_str()
                .and_then(resolution_reason)
                .ok_or_else(|| invalid("workflow assertion diagnostic is not presentable"))?,
        )
    };
    Ok(
        json!({"id":id,"boundary_key":boundary,"boundary_kind":kind,"assertion_kind":raw["assertion_kind"],"assertion_kind_label":value_label("workflow-assertion.kind",&raw["assertion_kind"])? ,"is_undo":truth(&raw["is_undo"]),"source_episode_key":source,"target_episode_key":target,"source_title":title(episodes,Some(source)),"target_title":title(episodes,target),"before_meaning":raw["before_meaning"],"after_meaning":raw["after_meaning"],"before_meaning_label":meaning(&raw["before_meaning"])? ,"after_meaning_label":meaning(&raw["after_meaning"])? ,"before_closure_reason":raw["before_closure_reason"],"after_closure_reason":raw["after_closure_reason"],"before_closure_reason_label":closure(&raw["before_closure_reason"])? ,"after_closure_reason_label":closure(&raw["after_closure_reason"])? ,"note_present":truth(&raw["note"]),"authority":raw["authority"],"authority_label":value_label("workflow-assertion.authority",&raw["authority"])? ,"supersedes_assertion_id":supersedes,"restored_assertion_id":restored,"created_at":raw["created_at"],"resolution":resolution,"resolution_label":resolution_label,"resolution_reason":raw["resolution_reason"],"resolution_reason_label":reason_label,"endpoints_resolved":episodes.contains_key(source)&&target.is_none_or(|key|episodes.contains_key(key))}),
    )
}
struct Action<'a> {
    action: &'a str,
    source: &'a str,
    target: Option<&'a str>,
    source_title: &'a str,
    target_title: Option<&'a str>,
    before: &'a str,
    after: &'a str,
    before_authority: &'a str,
    after_authority: &'a str,
    revision: &'a str,
    active: Option<&'a Value>,
    assertion_id: Option<i64>,
    current_reason: Option<&'a str>,
    display: Option<&'a str>,
}
fn action_view(a: Action<'_>) -> Result<Value> {
    let boundary_kind = if a.target.is_some() {
        "relation"
    } else {
        "lifecycle"
    };
    let boundary = workflow_boundary_key(boundary_kind, a.source, a.target)?;
    let active_id = a
        .active
        .map(|v| identity(&v["id"], "assertion id"))
        .transpose()?
        .flatten();
    let selected = if a.action == "close"
        && a.current_reason
            .is_some_and(|v| CLOSURE_REASONS.contains(&v))
    {
        CLOSURE_REASONS
            .iter()
            .copied()
            .find(|v| Some(*v) != a.current_reason)
            .unwrap()
    } else {
        "completed"
    };
    let options=CLOSURE_REASONS.iter().map(|reason|Ok(json!({"value":reason,"label":closure(&json!(reason))?,"selected":*reason==selected,"current":Some(*reason)==a.current_reason}))).collect::<Result<Vec<_>>>()?;
    Ok(
        json!({"action_id":format!("workflow-correction-{boundary}-{}",a.action),"action":a.action,"action_label":if a.action=="undo" {"되돌리기".into()} else {value_label("workflow-assertion.kind",&json!(a.action))?},"display_label":a.display,"boundary_kind":boundary_kind,"boundary_key":boundary,"source_episode_key":a.source,"target_episode_key":a.target,"source_title":a.source_title,"target_title":a.target_title,"before_meaning":a.before,"after_meaning":a.after,"before_meaning_label":meaning(&json!(a.before))?,"after_meaning_label":meaning(&json!(a.after))?,"before_authority_label":strict_authority(a.before_authority)?,"after_authority_label":strict_authority(a.after_authority)?,"expected_revision":a.revision,"expected_active_assertion_id":active_id,"assertion_id":a.assertion_id,"supersedes_assertion_id":active_id,"is_close":a.action=="close","is_undo":a.action=="undo","current_close_reason":a.current_reason,"selected_close_reason_label":closure(&json!(selected))?,"close_reason_options":options}),
    )
}
fn undo_action(assertion: &Value, before: &str, after: &str, revision: &str) -> Result<Value> {
    action_view(Action {
        action: "undo",
        source: text(&assertion["source_episode_key"], ""),
        target: assertion["target_episode_key"].as_str(),
        source_title: text(&assertion["source_title"], ""),
        target_title: assertion["target_title"].as_str(),
        before: text(&assertion["after_meaning"], ""),
        after: text(&assertion["before_meaning"], ""),
        before_authority: before,
        after_authority: after,
        revision,
        active: Some(assertion),
        assertion_id: identity(&assertion["id"], "assertion id")?,
        current_reason: None,
        display: None,
    })
}
fn pair(value: &Value) -> (String, String) {
    (
        text(&value["source_episode_key"], "").into(),
        text(&value["target_episode_key"], "").into(),
    )
}
fn restored_relation_authority<'a>(base: Option<&'a Value>, active: &Value) -> &'a str {
    if active["supersedes_assertion_id"].is_null() {
        base.map(|v| text(&v["authority"], "deterministic-candidate"))
            .unwrap_or("user-confirmed")
    } else {
        "user-confirmed"
    }
}
/// This adapter reads only the supplied immutable projection. It never queries
/// or modifies a ledger and never serializes correction notes into the view.
pub fn enrich_workflow_corrections(
    payload: &Value,
    episodes: Vec<Value>,
    relations: Vec<Value>,
    episodes_by_key: &BTreeMap<String, Value>,
    reason_view: fn(&Value) -> Value,
) -> Result<Value> {
    let revision = payload["assertion_revision"]
        .as_str()
        .ok_or_else(|| invalid("ready workflow projection requires an assertion revision"))?;
    let mut assertions = vec![];
    let mut relation_assertions = vec![];
    let mut lifecycle_assertions = BTreeMap::new();
    let mut relation_pairs = BTreeSet::new();
    for raw in values(&payload["assertions"]) {
        if !raw.is_object() {
            return Err(invalid("workflow assertion summary is malformed"));
        }
        let assertion = assertion_view(raw, episodes_by_key)?;
        if assertion["boundary_kind"] == "relation" {
            let pair = pair(&assertion);
            if !relation_pairs.insert(pair.clone()) {
                return Err(invalid("workflow relation assertion is duplicated"));
            }
            relation_assertions.push((pair, assertion.clone()));
        } else if lifecycle_assertions
            .insert(
                text(&assertion["source_episode_key"], "").to_owned(),
                assertion.clone(),
            )
            .is_some()
        {
            return Err(invalid("workflow lifecycle assertion is duplicated"));
        }
        assertions.push(assertion);
    }
    let mut base_relations = BTreeMap::new();
    for raw in values(&payload["base_relations"]) {
        if !raw.is_object() {
            return Err(invalid("base workflow relation is malformed"));
        }
        let pair = pair(raw);
        if !episodes_by_key.contains_key(&pair.0) || !episodes_by_key.contains_key(&pair.1) {
            return Err(invalid(
                "base workflow relation references an absent Episode",
            ));
        }
        base_relations.insert(pair, raw);
    }
    let mut base_lifecycle = BTreeMap::new();
    for raw in values(&payload["base_episode_lifecycle"]) {
        if !raw.is_object()
            || !raw["episode_key"]
                .as_str()
                .is_some_and(|key| episodes_by_key.contains_key(key))
        {
            return Err(invalid("base workflow lifecycle is malformed"));
        }
        base_lifecycle.insert(text(&raw["episode_key"], ""), raw);
    }
    let mut effective = BTreeSet::new();
    let mut outgoing = BTreeSet::new();
    let mut enriched_relations = vec![];
    for mut relation in relations {
        let pair = pair(&relation);
        effective.insert(pair.clone());
        outgoing.insert(pair.0.clone());
        let active = relation_assertions
            .iter()
            .find(|(key, _)| key == &pair)
            .map(|(_, v)| v);
        let base = base_relations.get(&pair).copied();
        let authority = text(&relation["authority"], "");
        let actions: &[&str] = match text(&relation["kind"], "") {
            "continues" => &["split-here", "merge-into"],
            "branches-from" => &["same-flow", "merge-into"],
            "merged-into" => &["same-flow"],
            _ => return Err(invalid("workflow relation kind is not presentable")),
        };
        let mut controls = vec![];
        for action in actions {
            controls.push(action_view(Action {
                action,
                source: &pair.0,
                target: Some(&pair.1),
                source_title: text(&relation["source_title"], ""),
                target_title: relation["target_title"].as_str(),
                before: &format!("relation:{}", text(&relation["kind"], "")),
                after: action_after_meaning(action).unwrap(),
                before_authority: authority,
                after_authority: "user-confirmed",
                revision,
                active,
                assertion_id: None,
                current_reason: None,
                display: None,
            })?);
        }
        if let Some(active) = active.filter(|a| truth(&a["endpoints_resolved"])) {
            controls.push(undo_action(
                active,
                authority,
                restored_relation_authority(base, active),
                revision,
            )?);
        }
        let base_reasons = base
            .map(|b| {
                values(&b["reasons"])
                    .iter()
                    .filter(|v| v.is_object())
                    .map(reason_view)
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();
        let confirmed = authority == "user-confirmed";
        relation["boundary_key"] =
            json!(workflow_boundary_key("relation", &pair.0, Some(&pair.1))?);
        relation["user_confirmed"] = json!(confirmed);
        relation["active_assertion"] = json!(active);
        relation["base_relation"] = json!(base);
        relation["base_reasons"] = json!(base_reasons);
        relation["correction_actions"] = json!(controls);
        enriched_relations.push(relation);
    }
    let mut detached: BTreeMap<String, Vec<Value>> = episodes_by_key
        .keys()
        .map(|key| (key.clone(), vec![]))
        .collect();
    for (pair, assertion) in &relation_assertions {
        if effective.contains(pair) {
            continue;
        }
        let owner = if episodes_by_key.contains_key(&pair.0) {
            &pair.0
        } else {
            &pair.1
        };
        let Some(items) = detached.get_mut(owner) else {
            continue;
        };
        let mut item = assertion.clone();
        item["undo_action"] = Value::Null;
        if truth(&assertion["endpoints_resolved"]) {
            item["undo_action"] = undo_action(
                assertion,
                "user-confirmed",
                restored_relation_authority(base_relations.get(pair).copied(), assertion),
                revision,
            )?;
        }
        items.push(item);
    }
    let mut enriched_episodes = vec![];
    for mut episode in episodes {
        let key = text(&episode["episode_key"], "").to_owned();
        let authority = text(&episode["authority"], "");
        let lifecycle = lifecycle_assertions.get(&key);
        let base = base_lifecycle
            .get(key.as_str())
            .copied()
            .unwrap_or(&episode);
        let state = text(&episode["lifecycle_state"], "unknown");
        let is_tip = !outgoing.contains(&key);
        let mut actions = vec![];
        let change_reason = is_tip
            && state == "closed"
            && lifecycle.is_some_and(|v| v["after_meaning"] == "lifecycle:closed");
        if (is_tip && ["open", "unknown"].contains(&state)) || change_reason {
            actions.push(action_view(Action {
                action: "close",
                source: &key,
                target: None,
                source_title: text(&episode["title"], ""),
                target_title: None,
                before: &format!("lifecycle:{state}"),
                after: "lifecycle:closed",
                before_authority: authority,
                after_authority: "user-confirmed",
                revision,
                active: lifecycle,
                assertion_id: None,
                current_reason: if change_reason {
                    episode["closure_reason"].as_str()
                } else {
                    None
                },
                display: change_reason.then_some("종료 사유 고치기"),
            })?);
        }
        if lifecycle.is_some_and(|v| v["after_meaning"] == "lifecycle:closed") {
            actions.push(action_view(Action {
                action: "reopen",
                source: &key,
                target: None,
                source_title: text(&episode["title"], ""),
                target_title: None,
                before: "lifecycle:closed",
                after: "lifecycle:open",
                before_authority: authority,
                after_authority: "user-confirmed",
                revision,
                active: lifecycle,
                assertion_id: None,
                current_reason: None,
                display: None,
            })?);
        }
        if let Some(lifecycle) = lifecycle.filter(|v| truth(&v["endpoints_resolved"])) {
            let restored = if lifecycle["supersedes_assertion_id"].is_null() {
                text(&base["authority"], "observed")
            } else {
                "user-confirmed"
            };
            actions.push(undo_action(lifecycle, authority, restored, revision)?);
        }
        let confirmed = authority == "user-confirmed";
        let closure_label = closure(&episode["closure_reason"])?;
        episode["user_confirmed"] = json!(confirmed);
        episode["active_lifecycle_assertion"] = json!(lifecycle);
        episode["detached_relation_assertions"] = json!(detached[&key]);
        episode["correction_actions"] = json!(actions);
        episode["closure_reason_label"] = json!(closure_label);
        episode["relations"] = json!(enriched_relations
            .iter()
            .filter(|v| v["source_episode_key"] == key || v["target_episode_key"] == key)
            .cloned()
            .collect::<Vec<_>>());
        enriched_episodes.push(episode);
    }
    Ok(
        json!({"revision":revision,"assertions":assertions,"episodes":enriched_episodes,"relations":enriched_relations}),
    )
}
