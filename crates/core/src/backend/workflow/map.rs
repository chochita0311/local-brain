//! Bounded template/client view of one immutable Workflow Focus projection.
use super::{
    correction_view::{
        authority_label, enrich_workflow_corrections, episode_title, text, truth, values,
        workflow_relation_id,
    },
    focus::WorkflowFocusProjection,
    projection::invalid,
};
use crate::backend::{unicode, value_registry::visible_value_label, Result};
use serde_json::{json, Value};
use std::collections::BTreeMap;

pub const WORKFLOW_ROUTE_VERSION: &str = "localbrain.workflow-map.v2";
fn reason_label(kind: &str) -> String {
    match kind {
        "direct-source-relation" => "원본의 직접 관계",
        "shared-reference" => "같은 자료 참조",
        "thread-membership" => "같은 Thread",
        "workstream-membership" => "같은 Workstream",
        "user-assertion" => "사용자 확인",
        "same-workspace" => "같은 workspace",
        "same-git-root" => "같은 Git root",
        "same-git-branch" => "같은 Git branch",
        "lexical-overlap" => "문구 겹침",
        "temporal-proximity" => "시간 인접",
        _ => return kind.replace('-', " "),
    }
    .into()
}
fn family_label(family: &str) -> String {
    match family {
        "atlassian" => "Atlassian",
        "external" => "외부 링크",
        "git" => "Git",
        "local-context" => "Local Context",
        "local-resource" => "로컬 자료",
        "organization" => "연결된 작업",
        "session" => "Subsessions",
        "slack" => "Slack",
        "unknown" => "분류되지 않은 자료",
        _ => return unicode::titlecase(&family.replace('-', " ")),
    }
    .into()
}
fn label(value: &Value, known: fn(&str) -> Option<&'static str>) -> String {
    let value = text(value, "unknown");
    known(value)
        .map(str::to_owned)
        .unwrap_or_else(|| value.replace('-', " "))
}
fn kind_label(kind: &str) -> Option<&'static str> {
    Some(match kind {
        "organization-link" => "정리 연결",
        "structure-reference" => "구조 참조",
        "subsession" => "Subsession",
        "thread-membership" => "Thread 연결",
        "workstream-membership" => "Workstream 연결",
        _ => return None,
    })
}
fn availability_label(kind: &str) -> Option<&'static str> {
    Some(match kind {
        "available" => "사용 가능",
        "stale" => "마지막 관측",
        "unavailable" => "열 수 없음",
        "missing" => "경로 없음",
        "archived" => "보관됨",
        "unknown" => "상태 미확인",
        _ => return None,
    })
}
fn count(value: &Value) -> i64 {
    value.as_i64().unwrap_or(0)
}
fn reason_view(reason: &Value) -> Value {
    let kind = text(&reason["kind"], "unknown");
    json!({"kind":kind,"label":reason_label(kind),"identity":text(&reason["identity"],"근거 식별자 없음"),"observed_at":reason["observed_at"]})
}
fn evidence_group_view(group: &Value) -> Value {
    let family = text(&group["source_family"], "unknown");
    let family_label = family_label(family);
    let items = values(&group["items"])
        .iter()
        .filter(|v| v.is_object())
        .map(|item| {
            let mut item = item.clone();
            let kind = label(&item["evidence_kind"], kind_label);
            let availability = label(&item["availability"], availability_label);
            let authority = label(
                &json!(text(&item["authority"], "observed")),
                authority_label,
            );
            let admissions = values(&item["admission_reasons"])
                .iter()
                .map(|v| reason_label(text(v, "unknown")))
                .collect::<Vec<_>>();
            item["source_family"] = json!(family);
            item["source_label"] = json!(family_label);
            item["kind_label"] = json!(kind);
            item["availability_label"] = json!(availability);
            item["authority_label"] = json!(authority);
            item["admission_labels"] = json!(admissions);
            item
        })
        .collect::<Vec<_>>();
    let retained = count(&group["retained_total"]).max(items.len() as i64);
    let observed = count(&group["observed_total"]).max(retained);
    json!({"source_family":family,"label":family_label,"items":items,"retained_total":retained,"observed_total":observed,"partial":truth(&group["partial"]),"stale":truth(&group["stale"])})
}
fn relation_label(kind: &str) -> Option<&'static str> {
    Some(match kind {
        "continues" => "continues",
        "branches-from" => "branches from",
        "merged-into" => "merged into",
        _ => return None,
    })
}
pub fn workflow_map_view(
    projection: &WorkflowFocusProjection,
    requested_session_id: i64,
) -> Result<Value> {
    if requested_session_id <= 0 {
        return Err(invalid("requested_session_id must be positive"));
    }
    let payload = serde_json::to_value(projection)?;
    let status = text(&payload["status"], "");
    if !["ready", "missing", "ineligible"].contains(&status) {
        return Err(invalid("unsupported workflow route state"));
    }
    if status != "ready" {
        return workflow_map_state_view(status, requested_session_id);
    }
    let raw = values(&payload["episodes"]);
    let selected = payload["selected_episode_key"]
        .as_str()
        .ok_or_else(|| invalid("ready workflow projection requires a selected Episode"))?;
    if raw.is_empty() {
        return Err(invalid(
            "ready workflow projection requires a selected Episode",
        ));
    }
    let mut by_key = BTreeMap::new();
    for item in raw {
        if !item.is_object() || !item["episode"].is_object() {
            return Err(invalid("workflow Episode view is malformed"));
        }
        let episode = &item["episode"];
        let key = text(&episode["episode_key"], "");
        if key.is_empty() || by_key.insert(key.to_owned(), episode.clone()).is_some() {
            return Err(invalid("workflow Episode key is absent or duplicated"));
        }
    }
    if !by_key.contains_key(selected) {
        return Err(invalid("selected workflow Episode is absent"));
    }
    let mut relations = vec![];
    for raw in values(&payload["relations"]) {
        let source = text(&raw["source_episode_key"], "");
        let target = text(&raw["target_episode_key"], "");
        let source_episode = by_key
            .get(source)
            .ok_or_else(|| invalid("workflow relation references an absent Episode"))?;
        let target_episode = by_key
            .get(target)
            .ok_or_else(|| invalid("workflow relation references an absent Episode"))?;
        let relation_label = relation_label(text(&raw["kind"], ""))
            .ok_or_else(|| invalid("workflow relation kind is not presentable"))?;
        let mut relation = raw.clone();
        relation["relation_id"] = json!(workflow_relation_id(source, target)?);
        relation["label"] = json!(relation_label);
        relation["authority_label"] =
            json!(label(&json!(text(&raw["authority"], "")), authority_label));
        relation["source_title"] = json!(episode_title(source_episode));
        relation["target_title"] = json!(episode_title(target_episode));
        relation["reasons"] = json!(values(&raw["reasons"])
            .iter()
            .filter(|v| v.is_object())
            .map(reason_view)
            .collect::<Vec<_>>());
        relations.push(relation);
    }
    let mut episodes = vec![];
    let mut evidence_partial = false;
    for item in raw {
        let mut episode = item["episode"].clone();
        let key = text(&episode["episode_key"], "").to_owned();
        let groups = values(&item["evidence_groups"])
            .iter()
            .filter(|v| v.is_object())
            .map(evidence_group_view)
            .collect::<Vec<_>>();
        let partial = truth(&item["evidence_partial"])
            || groups
                .iter()
                .any(|g| truth(&g["partial"]) || truth(&g["stale"]));
        evidence_partial |= partial;
        let authority = label(&episode["authority"], authority_label);
        let activity = text(&episode["activity_state"], "unknown").replace('-', " ");
        let lifecycle = visible_value_label(
            "workflow-assertion.meaning",
            &json!(format!(
                "lifecycle:{}",
                text(&episode["lifecycle_state"], "unknown")
            )),
            None,
        )?;
        episode["title"] = json!(episode_title(&episode));
        episode["authority_label"] = json!(authority);
        episode["activity_label"] = json!(activity);
        episode["lifecycle_label"] = json!(lifecycle);
        episode["evidence_groups"] = json!(groups);
        episode["evidence_retained_total"] = json!(count(&item["evidence_retained_total"]));
        episode["evidence_observed_total"] = json!(count(&item["evidence_observed_total"]));
        episode["evidence_partial"] = json!(partial);
        episode["relations"] = json!(relations
            .iter()
            .filter(|v| v["source_episode_key"] == key || v["target_episode_key"] == key)
            .cloned()
            .collect::<Vec<_>>());
        episode["selected"] = json!(key == selected);
        episode["workflow_destination"] = json!(format!(
            "/sessions/{}/workflow",
            count(&episode["session_id"])
        ));
        episodes.push(episode);
    }
    let correction =
        enrich_workflow_corrections(&payload, episodes, relations, &by_key, reason_view)?;
    let episodes = values(&correction["episodes"]);
    let relations = values(&correction["relations"]);
    let selected_episode = episodes
        .iter()
        .find(|v| truth(&v["selected"]))
        .ok_or_else(|| invalid("selected workflow Episode is absent"))?;
    let episode_partial =
        count(&payload["episode_observed_total"]) > count(&payload["episode_retained_total"]);
    let branch_partial = count(&payload["branch_root_observed_total"])
        > count(&payload["branch_root_retained_total"]);
    let candidate_partial =
        count(&payload["candidate_observed_total"]) > count(&payload["candidate_retained_total"]);
    let client_episodes=episodes.iter().map(|v|json!({"episode_key":v["episode_key"],"session_id":v["session_id"],"workflow_destination":v["workflow_destination"],"observed_start_at":v["observed_start_at"],"last_observed_at":v["last_observed_at"],"title":v["title"],"lifecycle_state":v["lifecycle_state"],"authority":v["authority"],"active_assertion_id":v["active_lifecycle_assertion"]["id"]})).collect::<Vec<_>>();
    let client_relations=relations.iter().map(|v|json!({"relation_id":v["relation_id"],"boundary_key":v["boundary_key"],"source_episode_key":v["source_episode_key"],"target_episode_key":v["target_episode_key"],"kind":v["kind"],"label":v["label"],"authority":v["authority"],"authority_label":v["authority_label"],"active_assertion_id":v["active_assertion"]["id"]})).collect::<Vec<_>>();
    Ok(
        json!({"status":"ready","requested_session_id":requested_session_id,"correction_destination":format!("/sessions/{requested_session_id}/workflow/corrections"),"assertion_revision":correction["revision"],"session_destination":selected_episode["destination"],"selected_episode":selected_episode,"episodes":episodes,"relations":relations,"assertions":correction["assertions"],"assertion_count":values(&correction["assertions"]).len(),"diagnostics":payload["diagnostics"],"unconnected":relations.is_empty(),"partial":episode_partial||branch_partial||candidate_partial||evidence_partial,"candidate_observed_total":count(&payload["candidate_observed_total"]),"candidate_retained_total":count(&payload["candidate_retained_total"]),"episode_observed_total":if count(&payload["episode_observed_total"])==0{episodes.len() as i64}else{count(&payload["episode_observed_total"])},"episode_retained_total":if count(&payload["episode_retained_total"])==0{episodes.len() as i64}else{count(&payload["episode_retained_total"])},"branch_root_observed_total":count(&payload["branch_root_observed_total"]),"branch_root_retained_total":count(&payload["branch_root_retained_total"]),"client_projection":{"status":"ready","selected_episode_key":selected,"assertion_revision":correction["revision"],"episodes":client_episodes,"relations":client_relations,"projection_version":payload["projection_version"],"route_version":WORKFLOW_ROUTE_VERSION}}),
    )
}
pub fn workflow_map_state_view(status: &str, requested_session_id: i64) -> Result<Value> {
    let (title, message, destination, destination_label) = match status {
        "missing" => (
            "Session을 찾을 수 없습니다",
            "이 주소에 해당하는 작업 Session이 현재 로컬 인덱스에 없습니다.",
            "/sessions".to_owned(),
            "Sessions 목록",
        ),
        "ineligible" => (
            "작업 흐름을 만들 수 없는 Session입니다",
            "기본 작업 Session의 관측된 활동만 작업 흐름 Episode가 됩니다.",
            format!("/sessions/{requested_session_id}"),
            "Session 상세",
        ),
        "unexpected-error" => (
            "작업 흐름을 표시할 수 없습니다",
            "Session 원문은 그대로이며, 흐름 투영만 불러오지 못했습니다.",
            format!("/sessions/{requested_session_id}"),
            "Session 상세로 돌아가기",
        ),
        _ => return Err(invalid("unsupported workflow state")),
    };
    Ok(
        json!({"status":status,"requested_session_id":requested_session_id,"title":title,"message":message,"destination":destination,"destination_label":destination_label}),
    )
}
