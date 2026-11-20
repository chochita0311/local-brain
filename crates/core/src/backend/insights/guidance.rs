//! Frozen guide resources, structured-result schema, and cited finding admission.
use super::{evidence::MANIFEST_VERSION, invalid, required, text, values};
use crate::backend::{json as codec, unicode, BackendError, Result};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
pub const CORE_VERSION: &str = "personal-improvement-core-v8";
pub const REPORT_VERSION: &str = "personal-improvement-report-v3";
pub const LEGACY_REPORT_VERSION: &str = "personal-improvement-report-v2";
pub const PLAYBOOK_IDS: &[&str] = &[
    "task_framing",
    "request_feedback",
    "context_recovery",
    "repeatable_procedure",
    "learning_explanation",
    "verification_rework",
    "information_access",
    "decision_memory",
    "task_fit_effort",
    "personal_value",
    "assistant_configuration",
];
pub const HANDOFF_FIELDS: &[&str] = &[
    "goal",
    "proposed_change",
    "scope",
    "constraints",
    "first_steps",
    "success_check",
];
pub const FINDING_FIELDS: &[&str] = &[
    "title",
    "type_id",
    "owner_goal",
    "pattern_scope",
    "observation",
    "evidence_ids",
    "counterevidence_ids",
    "counterexample_status",
    "counterexample_check",
    "alternative",
    "coverage_limit",
    "action",
    "benefit_hypothesis",
    "effort_or_tradeoff",
    "follow_up",
    "handoff",
    "outcome_state",
];
pub const RESULT_FIELDS: &[&str] = &[
    "result_version",
    "title",
    "summary",
    "outcome",
    "findings",
    "no_finding_reason",
    "additional_evidence",
    "limits",
];
pub const REQUEST_FIELDS: &[&str] = &["kind", "question", "evidence_ids"];
pub const OUTCOMES: &[&str] = &["findings", "no_actionable_finding", "needs_evidence"];
pub const REQUEST_KINDS: &[&str] = &[
    "none",
    "conversation_neighbors",
    "independent_session",
    "owner_goal",
    "outcome",
];
pub const PATTERN_SCOPES: &[&str] = &["single_observation", "recurring_pattern"];
pub const COUNTEREXAMPLE_STATES: &[&str] = &["observed", "not_observed", "not_available"];
const CORE: &str = include_str!("resources/core-v8.md");
/// Historical resources remain packaged; selecting a new guide never rewrites
/// a retained Run's prompt or substitutes its frozen version/digests.
pub fn guide_resource(path: &str) -> Option<&'static str> {
    Some(match path {
        "personal_insight_guide.md" => include_str!("resources/personal_insight_guide.md"),
        "core-v2.md" => include_str!("resources/core-v2.md"),
        "core-v3.md" => include_str!("resources/core-v3.md"),
        "core-v4.md" => include_str!("resources/core-v4.md"),
        "core-v5.md" => include_str!("resources/core-v5.md"),
        "core-v6.md" => include_str!("resources/core-v6.md"),
        "core-v7.md" => include_str!("resources/core-v7.md"),
        "core-v8.md" => CORE,
        "playbooks/request_feedback-v1.md" => {
            include_str!("resources/playbooks/request_feedback-v1.md")
        }
        "playbooks/request_feedback-v2.md" => {
            include_str!("resources/playbooks/request_feedback-v2.md")
        }
        "playbooks/request_feedback-v3.md" => {
            include_str!("resources/playbooks/request_feedback-v3.md")
        }
        _ => {
            let path = path.strip_prefix("playbooks/")?;
            let (index, _) = PLAYBOOK_IDS.iter().enumerate().find(|(_, id)| {
                path == format!(
                    "{id}-{}.md",
                    if **id == "request_feedback" {
                        "v4"
                    } else {
                        "v1"
                    }
                )
            })?;
            PLAYBOOK_CONTENTS[index]
        }
    })
}
const PLAYBOOK_CONTENTS: &[&str] = &[
    include_str!("resources/playbooks/task_framing-v1.md"),
    include_str!("resources/playbooks/request_feedback-v4.md"),
    include_str!("resources/playbooks/context_recovery-v1.md"),
    include_str!("resources/playbooks/repeatable_procedure-v1.md"),
    include_str!("resources/playbooks/learning_explanation-v1.md"),
    include_str!("resources/playbooks/verification_rework-v1.md"),
    include_str!("resources/playbooks/information_access-v1.md"),
    include_str!("resources/playbooks/decision_memory-v1.md"),
    include_str!("resources/playbooks/task_fit_effort-v1.md"),
    include_str!("resources/playbooks/personal_value-v1.md"),
    include_str!("resources/playbooks/assistant_configuration-v1.md"),
];
fn digest(text: &str) -> String {
    format!("{:x}", Sha256::digest(text.as_bytes()))
}
fn trim(value: &str) -> &str {
    value.trim_matches(unicode::python_space)
}
pub fn select_playbooks(manifest: &Value) -> Result<(Vec<String>, String)> {
    let scope = &manifest["scope"];
    if manifest["version"] != MANIFEST_VERSION || !scope.is_object() {
        return Err(invalid(
            "unsupported evidence manifest for improvement guidance",
        ));
    }
    if !["ask", "discover"].contains(&text(&scope["mode"], "")) {
        return Err(invalid("unsupported improvement analysis mode"));
    }
    if scope["mode"] == "ask"
        && scope["question"]
            .as_str()
            .is_none_or(|s| trim(s).is_empty())
    {
        return Err(invalid("ask guidance requires a question"));
    }
    if scope["mode"] == "discover" && !scope["question"].is_null() {
        return Err(invalid("discover guidance does not accept a question"));
    }
    Ok((
        PLAYBOOK_IDS.iter().map(|s| (*s).into()).collect(),
        "owner_goal_and_observed_friction".into(),
    ))
}
pub fn build_guide_bundle(manifest: &Value) -> Result<Value> {
    let (selected, reason) = select_playbooks(manifest)?;
    let books=selected.iter().zip(PLAYBOOK_CONTENTS).map(|(id,content)|json!({"id":id,"version":if id=="request_feedback"{"v4"}else{"v1"},"sha256":digest(content),"content":content})).collect::<Vec<_>>();
    Ok(
        json!({"core_version":CORE_VERSION,"report_version":REPORT_VERSION,"core_sha256":digest(CORE),"core":CORE,"playbooks":books,"route_reason":reason}),
    )
}
pub fn guide_text(bundle: &Value) -> Result<String> {
    let mut sections = vec![trim(required(bundle, "core")?).to_owned()];
    for book in values(&bundle["playbooks"]) {
        sections.push(trim(required(book, "content")?).into());
    }
    Ok(sections.join("\n\n") + "\n")
}
pub fn report_version_for_guide(bundle: &Value) -> Result<&'static str> {
    let version = match text(&bundle["core_version"], "") {
        "personal-improvement-core-v2" | "personal-improvement-core-v3" => LEGACY_REPORT_VERSION,
        "personal-improvement-core-v4"
        | "personal-improvement-core-v5"
        | "personal-improvement-core-v6"
        | "personal-improvement-core-v7"
        | CORE_VERSION => REPORT_VERSION,
        _ => {
            return Err(invalid(
                "unsupported or mismatched personal improvement guide/report version",
            ))
        }
    };
    if bundle.get("report_version").is_some_and(|v| v != version) {
        return Err(invalid(
            "unsupported or mismatched personal improvement guide/report version",
        ));
    }
    Ok(version)
}
fn extended(
    fields: &'static [&'static str],
    extra: &[&'static str],
    current: bool,
) -> Vec<&'static str> {
    fields
        .iter()
        .copied()
        .chain(extra.iter().copied().filter(|_| current))
        .collect()
}
fn string_properties(fields: &[&str]) -> Value {
    Value::Object(
        fields
            .iter()
            .map(|name| ((*name).to_owned(), json!({"type":"string"})))
            .collect(),
    )
}
pub fn result_schema(selected_ids: &[String], report_version: &str) -> Result<Value> {
    if selected_ids.is_empty()
        || selected_ids
            .iter()
            .any(|id| !PLAYBOOK_IDS.contains(&id.as_str()))
    {
        return Err(invalid("result schema requires selected playbooks"));
    }
    if ![REPORT_VERSION, LEGACY_REPORT_VERSION].contains(&report_version) {
        return Err(invalid("unsupported personal improvement report schema"));
    }
    let current = report_version == REPORT_VERSION;
    let finding_fields = extended(FINDING_FIELDS, &["type_reason"], current);
    let result_fields = extended(
        RESULT_FIELDS,
        &["selection_reason", "selection_evidence_ids"],
        current,
    );
    let request_fields = extended(REQUEST_FIELDS, &["message_requests"], current);
    let mut finding = string_properties(&finding_fields);
    finding["type_id"] = json!({"type":"string","enum":selected_ids});
    finding["pattern_scope"] = json!({"type":"string","enum":PATTERN_SCOPES});
    for key in ["evidence_ids", "counterevidence_ids"] {
        finding[key] = json!({"type":"array","items":{"type":"string"}});
    }
    finding["counterexample_status"] = json!({"type":"string","enum":COUNTEREXAMPLE_STATES});
    finding["handoff"] = json!({"type":"object","additionalProperties":false,"properties":string_properties(HANDOFF_FIELDS),"required":HANDOFF_FIELDS});
    finding["outcome_state"] = json!({"type":"string","enum":["not_confirmed"]});
    let mut properties = string_properties(&result_fields);
    properties["result_version"] = json!({"type":"string","enum":[report_version]});
    properties["outcome"] = json!({"type":"string","enum":OUTCOMES});
    properties["findings"] = json!({"type":"array","items":{"type":"object","additionalProperties":false,"properties":finding,"required":finding_fields}});
    properties["additional_evidence"] = json!({"type":"object","additionalProperties":false,"properties":{"kind":{"type":"string","enum":REQUEST_KINDS},"question":{"type":"string"},"evidence_ids":{"type":"array","items":{"type":"string"}}},"required":request_fields});
    if current {
        properties["selection_evidence_ids"] = json!({"type":"array","items":{"type":"string"}});
        properties["additional_evidence"]["properties"]["message_requests"] = json!({"type":"array","items":{"type":"object","additionalProperties":false,"properties":{"anchor_evidence_id":{"type":"string"},"message_index":{"type":"integer"}},"required":["anchor_evidence_id","message_index"]}});
    }
    Ok(
        json!({"type":"object","additionalProperties":false,"properties":properties,"required":result_fields}),
    )
}
fn exact(value: &Value, fields: &[&str]) -> bool {
    value.as_object().is_some_and(|map| {
        map.len() == fields.len() && fields.iter().all(|field| map.contains_key(*field))
    })
}
fn required_text<'a>(value: &'a Value, maximum: usize, field: &str) -> Result<&'a str> {
    value
        .as_str()
        .filter(|s| !trim(s).is_empty() && s.chars().count() <= maximum)
        .ok_or_else(|| invalid(&format!("{field} must be nonempty bounded text")))
}
fn references<'a>(
    value: &'a Value,
    lookup: &BTreeMap<String, Value>,
    maximum: usize,
    field: &str,
) -> Result<Vec<&'a str>> {
    let error = || invalid(&format!("{field} must cite unique selected evidence IDs"));
    let array = value
        .as_array()
        .filter(|v| v.len() <= maximum)
        .ok_or_else(error)?;
    let mut seen = BTreeSet::new();
    let mut result = vec![];
    for value in array {
        let id = value
            .as_str()
            .filter(|id| lookup.contains_key(*id))
            .ok_or_else(error)?;
        if !seen.insert(id) {
            return Err(error());
        }
        result.push(id);
    }
    Ok(result)
}
fn validate_message_requests(request: &Value, manifest: &Value) -> Result<()> {
    let targets = request["message_requests"]
        .as_array()
        .filter(|v| v.len() <= 5)
        .ok_or_else(|| invalid("message requests must be a bounded list"))?;
    if request["kind"] != "conversation_neighbors" {
        if !targets.is_empty() {
            return Err(invalid("only conversation requests may target messages"));
        }
        return Ok(());
    }
    if targets.is_empty() {
        return Err(invalid(
            "conversation requests must identify missing messages",
        ));
    }
    let anchors = values(&manifest["sessions"])
        .iter()
        .flat_map(|session| {
            values(&session["events"])
                .iter()
                .map(move |event| (text(&event["event_id"], ""), (session, event)))
        })
        .collect::<BTreeMap<_, _>>();
    let mut seen = BTreeSet::new();
    for target in targets {
        if !exact(target, &["anchor_evidence_id", "message_index"]) {
            return Err(invalid("invalid conversation message target"));
        }
        let reference = target["anchor_evidence_id"]
            .as_str()
            .filter(|id| values(&request["evidence_ids"]).iter().any(|v| v == id))
            .ok_or_else(|| invalid("message target must use an admitted request anchor"))?;
        let (session, anchor) = anchors
            .get(reference)
            .ok_or_else(|| invalid("message target must use an admitted request anchor"))?;
        let (Some(count), Some(index), Some(anchor_index)) = (
            session["message_count"].as_i64(),
            target["message_index"].as_i64(),
            anchor["message_index"].as_i64(),
        ) else {
            return Err(invalid(
                "message target must fall within the frozen positioned scope",
            ));
        };
        if index < 0 || index >= count || anchor_index < 0 || anchor_index >= count {
            return Err(invalid(
                "message target must fall within the frozen positioned scope",
            ));
        }
        if !seen.insert((session["session_id"].to_string(), index)) {
            return Err(invalid("duplicate conversation message target"));
        }
        for event in values(&session["events"]) {
            if event["message_index"].as_i64() == Some(index)
                && event["excerpt_start"] == 0
                && event["text_length"].as_u64()
                    == event["excerpt"].as_str().map(|s| s.chars().count() as u64)
            {
                return Err(BackendError::new(
                    422,
                    "insight-supplied-message",
                    "requested message was already supplied in full",
                ));
            }
        }
    }
    Ok(())
}
pub fn guide_metadata(bundle: &Value) -> Value {
    json!({"core_version":bundle["core_version"],"report_version":bundle["report_version"],"core_sha256":bundle["core_sha256"],"route_reason":bundle["route_reason"],"playbooks":values(&bundle["playbooks"]).iter().map(|book|json!({"id":book["id"],"version":book["version"],"sha256":book["sha256"]})).collect::<Vec<_>>()})
}
pub fn validate_guided_result(value: &Value, manifest: &Value, bundle: &Value) -> Result<Value> {
    let version = report_version_for_guide(bundle)?;
    let current = version == REPORT_VERSION;
    let finding_fields = extended(FINDING_FIELDS, &["type_reason"], current);
    let result_fields = extended(
        RESULT_FIELDS,
        &["selection_reason", "selection_evidence_ids"],
        current,
    );
    let request_fields = extended(REQUEST_FIELDS, &["message_requests"], current);
    if !exact(value, &result_fields) {
        return Err(invalid("invalid personal improvement result fields"));
    }
    if value["result_version"] != version {
        return Err(invalid("unsupported personal improvement result version"));
    }
    for field in ["title", "summary", "limits"] {
        required_text(&value[field], 8000, field)?;
    }
    if value["no_finding_reason"]
        .as_str()
        .is_none_or(|v| v.chars().count() > 8000)
    {
        return Err(invalid("invalid no-finding reason"));
    }
    let outcome = text(&value["outcome"], "");
    if !OUTCOMES.contains(&outcome) {
        return Err(invalid("invalid improvement outcome"));
    }
    let findings = value["findings"]
        .as_array()
        .filter(|v| v.len() <= 3)
        .ok_or_else(|| invalid("invalid improvement finding count"))?;
    if (outcome == "findings") == findings.is_empty() {
        return Err(invalid("finding count does not match improvement outcome"));
    }
    if outcome == "no_actionable_finding" || (current && outcome == "needs_evidence") {
        required_text(&value["no_finding_reason"], 8000, "no_finding_reason")?;
    }
    let lookup = values(&manifest["sessions"])
        .iter()
        .flat_map(|session| {
            values(&session["events"]).iter().map(move |event| {
                (
                    text(&event["event_id"], "").to_owned(),
                    session["session_id"].clone(),
                )
            })
        })
        .collect::<BTreeMap<_, _>>();
    let selected = values(&bundle["playbooks"])
        .iter()
        .map(|v| text(&v["id"], ""))
        .collect::<BTreeSet<_>>();
    if current {
        required_text(&value["selection_reason"], 2000, "selection_reason")?;
        let refs = references(
            &value["selection_evidence_ids"],
            &lookup,
            5,
            "selection_evidence_ids",
        )?;
        if ["findings", "needs_evidence"].contains(&outcome) && refs.is_empty() {
            return Err(invalid("a selected candidate must cite its evidence"));
        }
    }
    let request = &value["additional_evidence"];
    if !exact(request, &request_fields) {
        return Err(invalid("invalid additional evidence request"));
    }
    if !REQUEST_KINDS.contains(&text(&request["kind"], "")) {
        return Err(invalid("invalid additional evidence kind"));
    }
    if request["question"]
        .as_str()
        .is_none_or(|v| v.chars().count() > 1000)
    {
        return Err(invalid("invalid additional evidence question"));
    }
    references(&request["evidence_ids"], &lookup, 5, "additional_evidence")?;
    if outcome == "needs_evidence" {
        if request["kind"] == "none" || trim(text(&request["question"], "")).is_empty() {
            return Err(invalid("an evidence request needs a bounded question"));
        }
    } else {
        let mut empty = json!({"kind":"none","question":"","evidence_ids":[]});
        if current {
            empty["message_requests"] = json!([]);
        }
        if *request != empty {
            return Err(invalid(
                "only a needs-evidence outcome may request more evidence",
            ));
        }
    }
    if current {
        validate_message_requests(request, manifest)?;
    }
    let mut identified = vec![];
    for (index, finding) in findings.iter().enumerate() {
        if !exact(finding, &finding_fields) {
            return Err(invalid("invalid improvement finding fields"));
        }
        if !selected.contains(text(&finding["type_id"], "")) {
            return Err(invalid("finding type was not selected for this Run"));
        }
        if !PATTERN_SCOPES.contains(&text(&finding["pattern_scope"], "")) {
            return Err(invalid("invalid finding scope"));
        }
        if finding["outcome_state"] != "not_confirmed" {
            return Err(invalid("owner outcome was not confirmed by this Run"));
        }
        for field in &finding_fields {
            if [
                "type_id",
                "pattern_scope",
                "evidence_ids",
                "counterevidence_ids",
                "counterexample_status",
                "handoff",
                "outcome_state",
            ]
            .contains(field)
            {
                continue;
            }
            required_text(
                &finding[*field],
                if *field == "title" { 160 } else { 4000 },
                field,
            )?;
        }
        if current {
            required_text(&finding["type_reason"], 1000, "type_reason")?;
        }
        let evidence = references(&finding["evidence_ids"], &lookup, 12, "evidence_ids")?;
        if evidence.is_empty() {
            return Err(invalid("finding must cite selected evidence"));
        }
        let counter = references(
            &finding["counterevidence_ids"],
            &lookup,
            12,
            "counterevidence_ids",
        )?;
        if evidence.iter().any(|id| counter.contains(id)) {
            return Err(invalid(
                "supporting and counterevidence IDs must be distinct",
            ));
        }
        let status = text(&finding["counterexample_status"], "");
        if !COUNTEREXAMPLE_STATES.contains(&status) {
            return Err(invalid("invalid counterexample status"));
        }
        if (status == "observed") == counter.is_empty() {
            return Err(invalid("counterexample status does not match citations"));
        }
        if finding["pattern_scope"] == "recurring_pattern"
            && evidence
                .iter()
                .map(|id| lookup[*id].to_string())
                .collect::<BTreeSet<_>>()
                .len()
                < 2
        {
            return Err(invalid("recurrence needs distinct Sessions"));
        }
        let handoff = &finding["handoff"];
        if !exact(handoff, HANDOFF_FIELDS) {
            return Err(invalid("invalid work-session handoff"));
        }
        for field in HANDOFF_FIELDS {
            required_text(&handoff[*field], 1000, &format!("handoff.{field}"))?;
        }
        let fingerprint = codec::canonical(finding)?;
        let id = digest(&format!("{}:{fingerprint}", index + 1));
        let mut finding = finding.clone();
        finding["finding_id"] = json!(&id[..16]);
        identified.push(finding);
    }
    let mut output = value.clone();
    output["findings"] = json!(identified);
    let metadata = guide_metadata(bundle);
    let guide: Map<String, Value> = ["core_version", "core_sha256", "playbooks"]
        .iter()
        .map(|key| ((*key).into(), metadata[*key].clone()))
        .collect();
    output["guide"] = Value::Object(guide);
    Ok(output)
}
