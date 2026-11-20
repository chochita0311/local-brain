use super::super::common::*;
use crate::backend::{search::pattern, unicode, Result};
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};
use unicode_normalization::UnicodeNormalization;
pub const VERSION: &str = "localbrain.work-reconstruction.v1";
pub(super) fn keys(value: &Value, allowed: &[&str]) -> Result<()> {
    require(
        value
            .as_object()
            .is_some_and(|object| object.keys().all(|key| allowed.contains(&key.as_str()))),
        "INVALID_INPUT",
    )
}
pub(super) fn array(value: &Value, limit: usize) -> Result<&Vec<Value>> {
    let value = value.as_array().ok_or_else(|| failure("INPUT_LIMIT"))?;
    require(value.len() <= limit, "INPUT_LIMIT")?;
    Ok(value)
}
pub(super) fn identifier(value: &Value) -> Result<&str> {
    let value = value.as_str().ok_or_else(|| failure("INVALID_INPUT"))?;
    require(
        !value.is_empty() && value.chars().count() <= 500,
        "INVALID_INPUT",
    )?;
    Ok(value)
}
pub(super) fn string(value: &Value) -> Result<&str> {
    value.as_str().ok_or_else(|| failure("INVALID_INPUT"))
}
pub(super) fn eligible(row: &Value) -> bool {
    row["session_class"] == "work"
        && row["session_role"] == "primary"
        && row["index_policy"] == "full"
}
pub(super) fn int(value: &Value) -> Option<i64> {
    value.as_i64()
}
fn one(value: &Value) -> bool {
    value == 1 || value == true || value.as_f64() == Some(1.0)
}
pub fn validate_snapshot(data: &Value) -> Result<()> {
    keys(
        data,
        &[
            "version",
            "name",
            "sessions",
            "records",
            "artifacts",
            "references",
            "coverage",
            "organization_links",
        ],
    )?;
    require(one(&data["version"]), "INVALID_INPUT")?;
    identifier(&data["name"])?;
    let mut sessions = BTreeSet::new();
    let mut sources = BTreeSet::new();
    for session in array(&data["sessions"], 60)? {
        keys(
            session,
            &[
                "id",
                "source_id",
                "external_id",
                "session_class",
                "session_role",
                "index_policy",
                "event_count",
                "title",
                "workspace_id",
                "ended_at",
                "has_activity_events",
                "has_usage_records",
            ],
        )?;
        let id = int(&session["id"])
            .filter(|id| *id > 0)
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        require(sessions.insert(id), "INVALID_INPUT")?;
        let source = int(&session["source_id"])
            .filter(|id| *id > 0)
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        sources.insert(source);
        identifier(&session["external_id"])?;
        require(
            int(&session["event_count"]).is_some_and(|n| n >= 0)
                && (session["title"].is_null()
                    || session["title"]
                        .as_str()
                        .is_some_and(|title| title.chars().count() <= 500)),
            "INVALID_INPUT",
        )?;
    }
    require(sources.len() <= 8, "INPUT_LIMIT")?;
    let mut seen = BTreeSet::new();
    let mut totals: BTreeMap<i64, usize> = BTreeMap::new();
    let mut counts: BTreeMap<i64, usize> = BTreeMap::new();
    let mut kinds: BTreeMap<&str, usize> = BTreeMap::new();
    let mut total = 0;
    for record in array(&data["records"], 12060)? {
        keys(
            record,
            &["key", "kind", "session_id", "role", "offset", "at", "text"],
        )?;
        let key = identifier(&record["key"])?;
        require(seen.insert(key), "INVALID_INPUT")?;
        let kind = string(&record["kind"])?;
        require(
            ["session", "document", "item", "organization"].contains(&kind),
            "INVALID_INPUT",
        )?;
        let role = string(&record["role"])?;
        require(
            if kind == "session" {
                ["user", "assistant"].contains(&role)
            } else {
                ["document", "owner"].contains(&role)
            },
            "INVALID_INPUT",
        )?;
        require(
            int(&record["offset"]).is_some_and(|offset| offset >= 0),
            "INVALID_INPUT",
        )?;
        let length = string(&record["text"])?.chars().count();
        require(
            length
                <= match kind {
                    "session" => 4000,
                    "organization" => 2000,
                    _ => 8000,
                },
            "INPUT_LIMIT",
        )?;
        if !record["at"].is_null() {
            timestamp(string(&record["at"])?)?;
        }
        if kind == "session" {
            let session = int(&record["session_id"])
                .filter(|id| sessions.contains(id))
                .ok_or_else(|| failure("INVALID_INPUT"))?;
            *totals.entry(session).or_default() += length;
            *counts.entry(session).or_default() += 1;
        } else {
            require(record["session_id"].is_null(), "INVALID_INPUT")?;
        }
        *kinds.entry(kind).or_default() += 1;
        total += length;
    }
    require(
        totals.values().all(|n| *n <= 32000)
            && counts.values().all(|n| *n <= 200)
            && ["document", "item", "organization"]
                .iter()
                .all(|key| kinds.get(key).copied().unwrap_or(0) <= 20)
            && total <= 2_500_000,
        "INPUT_LIMIT",
    )?;
    for artifact in array(&data["artifacts"], 2000)? {
        keys(
            artifact,
            &[
                "kind",
                "source_scope",
                "source_identity",
                "title",
                "identity_state",
                "enabled",
                "is_container",
                "availability",
                "freshness",
            ],
        )?;
    }
    for reference in array(&data["references"], 12000)? {
        keys(
            reference,
            &[
                "episode_key",
                "artifact_key",
                "reference_identity",
                "evidence_kind",
                "read_outcome",
                "observed_at",
            ],
        )?;
    }
    array(&data["organization_links"], 200)?;
    require(
        data["coverage"].is_object()
            && data["coverage"]["complete"].is_boolean()
            && int(&data["coverage"]["unexamined"]).is_some_and(|n| n >= 0)
            && (!data["coverage"]["complete"].as_bool().unwrap()
                || data["coverage"]["unexamined"] == 0),
        "INVALID_INPUT",
    )
}
fn normalized(value: &str) -> String {
    unicode::casefold(&value.nfkc().collect::<String>())
        .split(unicode::python_space)
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join(" ")
        .trim_matches([' ', '.', '!', '?', '。'])
        .into()
}
fn key(prefix: &str, values: Value) -> String {
    format!("{prefix}:{}", digest(&values))
}
/// Python IGNORECASE includes the four historical ASCII equivalences that
/// Rust's Unicode simple-fold tables do not all admit. Expand only literals,
/// retaining regex escapes and named capture identifiers verbatim.
fn insensitive(value: &str) -> String {
    let mut output = String::from("(?i)");
    let chars = value.chars().collect::<Vec<_>>();
    let mut i = 0;
    while i < chars.len() {
        if chars[i] == '\\' {
            output.push(chars[i]);
            i += 1;
            if i < chars.len() {
                output.push(chars[i]);
                i += 1;
            }
            continue;
        }
        if chars[i..].starts_with(&['(', '?', 'P', '<']) {
            while i < chars.len() {
                let ch = chars[i];
                output.push(ch);
                i += 1;
                if ch == '>' {
                    break;
                }
            }
            continue;
        }
        output.push_str(match chars[i] {
            'i' | 'I' => "[iİı]",
            's' | 'S' => "[sſ]",
            'k' | 'K' => "[kK]",
            _ => {
                output.push(chars[i]);
                i += 1;
                continue;
            }
        });
        i += 1;
    }
    output
}
fn statement_spans(record: &Value) -> Result<Vec<(String, usize, usize)>> {
    let chars = string(&record["text"])?.chars().collect::<Vec<_>>();
    let offset = int(&record["offset"]).unwrap() as usize;
    let mut ends = Vec::new();
    for (index, ch) in chars.iter().enumerate() {
        if matches!(ch, '\n' | '!' | '?' | '。')
            || *ch == '.' && (index + 1 == chars.len() || unicode::python_space(chars[index + 1]))
        {
            ends.push(index + 1);
        }
    }
    if ends.last().copied() != Some(chars.len()) {
        ends.push(chars.len());
    }
    let mut result = Vec::new();
    let mut cursor = 0;
    for finish in ends {
        let segment = &chars[cursor..finish];
        let leading = segment
            .iter()
            .take_while(|ch| unicode::python_space(**ch))
            .count();
        let trailing = segment
            .iter()
            .rev()
            .take_while(|ch| unicode::python_space(**ch))
            .count();
        if leading + trailing < segment.len() {
            result.push((
                segment[leading..segment.len() - trailing].iter().collect(),
                offset + cursor + leading,
                offset + finish - trailing,
            ));
        }
        cursor = finish;
    }
    Ok(result)
}
fn extract(record: &Value) -> Result<(Vec<Value>, Vec<Value>)> {
    let mut found = Vec::new();
    let mut missing = Vec::new();
    let verbs = [
        ("reduce", "reduce"),
        ("lower", "reduce"),
        ("decrease", "reduce"),
        ("increase", "increase"),
        ("raise", "increase"),
        ("expand", "increase"),
        ("improve", "improve"),
        ("optimize", "improve"),
        ("optimise", "improve"),
        ("fix", "fix"),
        ("repair", "fix"),
        ("resolve", "fix"),
        ("add", "add"),
        ("introduce", "add"),
        ("remove", "remove"),
        ("delete", "remove"),
        ("retire", "remove"),
        ("replace", "replace"),
        ("enable", "enable"),
        ("disable", "disable"),
    ];
    let english = pattern(&insensitive(&format!(
        r"(?:^|\bto\s+)(?:please\s+)?(?P<verb>{})\s+(?P<subject>.+)",
        verbs
            .iter()
            .map(|(key, _)| *key)
            .collect::<Vec<_>>()
            .join("|")
    )));
    let korean = pattern(
        r"(?P<subject>.+?)(?:을|를)\s*(?P<verb>줄이|늘리|개선하|최적화하|수정하|고치|추가하|제거하|삭제하|교체하|활성화하|비활성화하)",
    );
    for (raw, start, end) in statement_spans(record)? {
        let location = json!({"record_key":record["key"],"start":start,"end":end});
        let statement_key = key("statement", json!([record["key"], start, end, raw]));
        let mut text = pattern(r"^(?:[-*+]\s+|\d+[.)]\s+|#{1,6}\s+)")
            .replace(raw.trim_matches([' ', '.', '!', '?', '。']), "")
            .into_owned();
        let unknown = |reason: &str| {
            let mut value = location.clone();
            value["reason"] = reason.into();
            value
        };
        if pattern(&insensitive(
            r"\b(?:do not|don't|not to|never)\b|하지\s*말|않",
        ))
        .is_match(&text)
        .map_err(|_| failure("INVALID_INPUT"))?
        {
            missing.push(unknown("unsupported-negation"));
            continue;
        }
        let completion = if let Some(complete) = pattern(&insensitive(
            r"\s+(?:until|so that|완료\s*조건\s*:)\s+(.+)$",
        ))
        .captures(&text)
        .map_err(|_| failure("INVALID_INPUT"))?
        {
            let completion = normalized(complete.get(1).unwrap().as_str());
            text = text[..complete.get(0).unwrap().start()].to_owned();
            Some(completion)
        } else {
            None
        };
        let outcome = pattern(&insensitive(r"^(?:completed|done|완료)\s*:"))
            .is_match(&text)
            .map_err(|_| failure("INVALID_INPUT"))?
            .then(|| raw.clone());
        text = pattern(&insensitive(r"^(?:completed|done|완료)\s*:\s*"))
            .replace(&text, "")
            .into_owned();
        text=pattern(&insensitive(r"^(?:(?:our|the)\s+(?:goal|objective|aim)\s+is\s+(?:to\s+)?|(?:we|i)\s+(?:need|want|aim)\s+to\s+|goal\s*:\s*|please\s+)")).replace(&text,"").into_owned();
        let en = english
            .captures(&text)
            .map_err(|_| failure("INVALID_INPUT"))?;
        let ko = korean
            .captures(&text)
            .map_err(|_| failure("INVALID_INPUT"))?;
        let (change, subject) = if let Some(capture) = en {
            let verb = unicode::lowercase(capture.name("verb").unwrap().as_str());
            let change = verbs
                .iter()
                .find(|(key, _)| *key == verb)
                .map(|(_, value)| *value)
                .ok_or_else(|| failure("INVALID_INPUT"))?;
            (
                change,
                normalized(capture.name("subject").unwrap().as_str()),
            )
        } else if let Some(capture) = ko {
            let change = match capture.name("verb").unwrap().as_str() {
                "줄이" => "reduce",
                "늘리" => "increase",
                "개선하" | "최적화하" => "improve",
                "수정하" | "고치" => "fix",
                "추가하" => "add",
                "제거하" | "삭제하" => "remove",
                "교체하" => "replace",
                "활성화하" => "enable",
                _ => "disable",
            };
            (
                change,
                normalized(capture.name("subject").unwrap().as_str()),
            )
        } else {
            missing.push(unknown("unsupported-goal"));
            continue;
        };
        if subject.is_empty()
            || subject.chars().count() > 300
            || pattern(r"https?://|[{}]")
                .is_match(&subject)
                .map_err(|_| failure("INVALID_INPUT"))?
        {
            missing.push(unknown("unsupported-subject"));
            continue;
        }
        let phase = if pattern(&insensitive(r"investigat|diagnos|조사|분석"))
            .is_match(&raw)
            .map_err(|_| failure("INVALID_INPUT"))?
        {
            "investigation"
        } else if pattern(&insensitive(r"implement|build|구현"))
            .is_match(&raw)
            .map_err(|_| failure("INVALID_INPUT"))?
        {
            "implementation"
        } else if pattern(&insensitive(r"verif|test|검증|테스트"))
            .is_match(&raw)
            .map_err(|_| failure("INVALID_INPUT"))?
        {
            "verification"
        } else {
            "activity"
        };
        let mut field_evidence = Map::new();
        for field in ["subject", "change", "phase", "completion", "outcome"] {
            if field == "completion" && completion.is_none()
                || field == "outcome" && outcome.is_none()
            {
                continue;
            }
            let mut value = location.clone();
            value["authority"] = "observed".into();
            field_evidence.insert(field.into(), value);
        }
        found.push(json!({"statement_key":statement_key,"record_key":record["key"],"start":start,"end":end,"session_id":record["session_id"],"source_kind":record["kind"],"role":record["role"],"observed_at":record["at"],"subject":subject,"change":change,"completion":completion,"outcome":outcome,"phase":phase,"wording":raw,"wording_authority":"observed","authority":"inferred","field_evidence":field_evidence}));
    }
    Ok((found, missing))
}
pub fn reconstruct(
    data: &Value,
    corrections: &[Value],
    include_organization: bool,
) -> Result<Value> {
    validate_snapshot(data)?;
    let accepted = array(&data["sessions"], 60)?
        .iter()
        .filter(|session| eligible(session))
        .map(|session| session["id"].clone())
        .collect::<Vec<_>>();
    let mut coverage = data["coverage"].clone();
    let mut records = array(&data["records"], 12060)?.iter().collect::<Vec<_>>();
    records.sort_by(|a, b| string(&a["key"]).unwrap().cmp(string(&b["key"]).unwrap()));
    let mut goals: BTreeMap<(String, String), Vec<Value>> = BTreeMap::new();
    let mut missing = Vec::new();
    for record in records {
        if record["kind"] == "organization" && !include_organization {
            continue;
        }
        if record["kind"] == "session" && !accepted.contains(&record["session_id"]) {
            coverage["complete"] = false.into();
            coverage["unexamined"] = (coverage["unexamined"].as_i64().unwrap() + 1).into();
            missing.push(json!({"record_key":record["key"],"reason":"ineligible-session"}));
            continue;
        }
        let (claims, unknown) = extract(record)?;
        missing.extend(unknown);
        for claim in claims {
            goals
                .entry((
                    string(&claim["subject"])?.into(),
                    string(&claim["change"])?.into(),
                ))
                .or_default()
                .push(claim);
        }
    }
    let mut buckets: BTreeMap<String, Vec<Value>> = BTreeMap::new();
    for ((subject, action), values) in goals {
        let completions = values
            .iter()
            .filter_map(|value| value["completion"].as_str().filter(|v| !v.is_empty()))
            .collect::<BTreeSet<_>>();
        for claim in &values {
            let completion = claim["completion"].as_str().filter(|v| !v.is_empty());
            if completion.is_none() && completions.len() > 1 {
                missing.push(json!({"record_key":claim["record_key"],"start":claim["start"],"end":claim["end"],"reason":"ambiguous-completion"}));
                continue;
            }
            let completion = completion.or_else(|| completions.first().copied());
            buckets
                .entry(key("flow", json!([subject, action, completion])))
                .or_default()
                .push(claim.clone());
        }
    }
    require(corrections.len() <= 100, "INVALID_INPUT")?;
    let lookup = buckets
        .values()
        .flatten()
        .map(|claim| {
            (
                claim["statement_key"].as_str().unwrap().to_owned(),
                claim.clone(),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut labels = BTreeMap::new();
    let mut used = BTreeSet::new();
    let mut correction_ids = BTreeSet::new();
    let mut correction_rows = Vec::new();
    for correction in corrections {
        keys(correction, &["id", "statement_keys", "label"])?;
        let cid = identifier(&correction["id"])?;
        require(correction_ids.insert(cid), "INVALID_INPUT")?;
        let targets = array(&correction["statement_keys"], 12060)?
            .iter()
            .map(|value| Ok(string(value)?.to_owned()))
            .collect::<Result<BTreeSet<_>>>()?;
        require(
            targets.len() == correction["statement_keys"].as_array().unwrap().len()
                && used.is_disjoint(&targets),
            "INVALID_INPUT",
        )?;
        used.extend(targets.clone());
        let label = &correction["label"];
        require(
            label.is_null()
                || label
                    .as_str()
                    .is_some_and(|value| !value.is_empty() && value.chars().count() <= 500),
            "INVALID_INPUT",
        )?;
        let active = targets
            .iter()
            .filter_map(|target| lookup.get(target))
            .cloned()
            .map(|mut claim| {
                claim["authority"] = "user-corrected".into();
                claim
            })
            .collect::<Vec<_>>();
        for values in buckets.values_mut() {
            values.retain(|claim| !targets.contains(claim["statement_key"].as_str().unwrap()));
        }
        let identity = key("correction-flow", json!([cid]));
        labels.insert(identity.clone(), label.clone());
        correction_rows.push(
            json!({"id":cid,"statement_keys":targets,"label":label,"active_count":active.len()}),
        );
        buckets.insert(identity, active);
    }
    let mut flows = Vec::new();
    for (identity, mut members) in buckets {
        if members.is_empty() {
            continue;
        }
        members.sort_by(|a, b| {
            string(&a["statement_key"])
                .unwrap()
                .cmp(string(&b["statement_key"]).unwrap())
        });
        let first = &members[0];
        let completion = members
            .iter()
            .filter_map(|claim| claim["completion"].as_str().filter(|v| !v.is_empty()))
            .next();
        let mut flow = json!({"flow_id":identity,"subject":first["subject"],"change":first["change"],"completion":completion,"label":format!("{} {}",string(&first["change"])?,string(&first["subject"])?),"user_label":labels.get(&identity),"authority":"inferred","lifecycle":"unknown","members":members});
        flow["revision"] = digest(&flow).into();
        flows.push(flow);
    }
    missing.sort_by(|a, b| {
        string(&a["record_key"])
            .unwrap()
            .cmp(string(&b["record_key"]).unwrap())
            .then_with(|| {
                a["start"]
                    .as_i64()
                    .unwrap_or(0)
                    .cmp(&b["start"].as_i64().unwrap_or(0))
            })
    });
    correction_rows.sort_by(|a, b| string(&a["id"]).unwrap().cmp(string(&b["id"]).unwrap()));
    Ok(
        json!({"version":VERSION,"flows":flows,"unassigned":missing,"coverage":coverage,"corrections":correction_rows,"routine_confirmations":0}),
    )
}
