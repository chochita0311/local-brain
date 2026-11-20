//! Exhaustive FTS and structured candidate discovery, without model calls.
use super::retrieval_sql as sql;
use crate::backend::{db, storage, unicode, Config, Result};
use rusqlite::Connection;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet, HashMap},
    path::Path,
    sync::LazyLock,
};
const GROUPS: &[(&str, &str)] = &[
    ("session", "sessions"),
    ("document", "documents"),
    ("project", "projects"),
    ("local", "local_paths"),
    ("external", "external_references"),
];
fn group(kind: &str) -> Option<&'static str> {
    GROUPS
        .iter()
        .find_map(|(key, value)| (*key == kind).then_some(*value))
}
fn text<'a>(row: &'a Value, key: &str) -> Option<&'a str> {
    row[key].as_str()
}
fn nonempty<'a>(row: &'a Value, key: &str) -> Option<&'a str> {
    text(row, key).filter(|v| !v.is_empty())
}
fn id(value: &Value) -> String {
    value
        .as_str()
        .map(str::to_owned)
        .unwrap_or_else(|| value.to_string())
}
fn integer(row: &Value, key: &str) -> i64 {
    row[key].as_i64().expect("integer identity from schema")
}
fn joined(row: &Value, fields: &[&str]) -> String {
    fields
        .iter()
        .filter_map(|key| nonempty(row, key))
        .collect::<Vec<_>>()
        .join(" ")
}
fn tokens(value: &str) -> BTreeSet<String> {
    static PATTERN: LazyLock<regex::Regex> =
        LazyLock::new(|| regex::Regex::new(r"[A-Za-z0-9가-힣_.-]{2,}").unwrap());
    const STOP: &[&str] = &[
        "about",
        "and",
        "context",
        "for",
        "from",
        "local",
        "project",
        "the",
        "this",
        "with",
        "개발",
        "관련",
        "관리",
        "대한",
        "문서",
        "범위",
        "사용",
        "상태",
        "작업",
        "정보",
        "프로젝트",
        "필요",
        "확인",
    ];
    PATTERN
        .find_iter(value)
        .map(|part| {
            unicode::lowercase(part.as_str())
                .trim_matches(['.', '_', '-'])
                .to_owned()
        })
        .filter(|part| !STOP.contains(&part.as_str()))
        .collect()
}
fn excerpt(value: &str, matched: &BTreeSet<String>) -> String {
    let compact = value
        .split(unicode::python_space)
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    let chars = compact.chars().collect::<Vec<_>>();
    if chars.len() <= 560 {
        return compact;
    }
    let lower = unicode::lowercase(&compact);
    let center = matched
        .iter()
        .filter_map(|token| {
            lower
                .find(token)
                .map(|index| lower[..index].chars().count())
        })
        .min()
        .unwrap_or(0);
    let start = center.saturating_sub(280);
    let end = chars.len().min(center + 280);
    format!(
        "{}{}{}",
        if start > 0 { "..." } else { "" },
        chars[start..end].iter().collect::<String>(),
        if end < chars.len() { "..." } else { "" }
    )
}
fn query(
    workstream: &Value,
    thread: &Value,
) -> (BTreeSet<String>, BTreeSet<String>, BTreeSet<String>) {
    let thread_tokens = tokens(&joined(
        thread,
        &["title", "summary", "current_goal", "next_action"],
    ));
    let work = tokens(&joined(workstream, &["name", "summary"]));
    let title = tokens(text(thread, "title").unwrap_or_default());
    let query = if thread_tokens.is_empty() {
        work.clone()
    } else {
        thread_tokens
    };
    let candidates = if title.is_empty() {
        query.clone()
    } else {
        title
    };
    (query, work, candidates)
}
fn matching(connection: &Connection, tokens: &BTreeSet<String>) -> Result<Vec<Value>> {
    let expression = tokens
        .iter()
        .map(|token| format!("\"{}\"", token.replace('"', "\"\"")))
        .collect::<Vec<_>>()
        .join(" AND ");
    if expression.is_empty() {
        return Ok(Vec::new());
    }
    db::rows(connection, sql::MATCHING_SEARCH_ROWS_0, [expression])
}
fn relation_key(thread: i64, kind: &str, entity: &str) -> String {
    format!("{thread}:{kind}:{entity}")
}
struct States {
    confirmed: Vec<(i64, String, String, String)>,
    lookup: HashMap<String, String>,
    shared: BTreeSet<(String, String)>,
    suggestions: HashMap<String, String>,
}
impl States {
    fn load(connection: &Connection, workstream: i64) -> Result<Self> {
        let mut confirmed = Vec::new();
        let mut lookup = HashMap::new();
        for row in db::rows(connection, sql::THREAD_LINK_MAPS_0, [workstream])? {
            let thread = integer(&row, "thread_id");
            let kind = text(&row, "entity_type").unwrap().to_owned();
            let entity = id(&row["entity_id"]);
            let relation = text(&row, "relation_type").unwrap().to_owned();
            lookup.insert(relation_key(thread, &kind, &entity), relation.clone());
            confirmed.push((thread, kind, entity, relation));
        }
        let shared = db::rows(connection, sql::THREAD_LINK_MAPS_1, [workstream])?
            .into_iter()
            .map(|row| {
                (
                    text(&row, "entity_type").unwrap().to_owned(),
                    id(&row["entity_id"]),
                )
            })
            .collect();
        let mut suggestions = HashMap::new();
        for row in db::rows(connection, sql::SUGGESTION_STATES_0, [workstream])? {
            let Some(payload) = text(&row, "payload_json")
                .and_then(|value| serde_json::from_str::<Value>(value).ok())
            else {
                continue;
            };
            let direct = nonempty(&payload, "entity_type")
                .filter(|_| !payload["entity_id"].is_null())
                .map(|kind| (kind, id(&payload["entity_id"])));
            let mapped = nonempty(&payload, "resource_type")
                .filter(|kind| ["session", "document", "project"].contains(kind))
                .filter(|_| !payload["locator"].is_null())
                .map(|kind| (kind, id(&payload["locator"])));
            if let Some((kind, entity)) = direct.or(mapped) {
                suggestions.insert(
                    relation_key(integer(&row, "target_id"), kind, &entity),
                    text(&row, "status").unwrap().to_owned(),
                );
            }
        }
        Ok(Self {
            confirmed,
            lookup,
            shared,
            suggestions,
        })
    }
    fn relation(&self, thread: i64, kind: &str, entity: &str) -> (String, Option<String>) {
        let key = relation_key(thread, kind, entity);
        if let Some(value) = self.lookup.get(&key) {
            ("confirmed".into(), Some(value.clone()))
        } else {
            (
                self.suggestions
                    .get(&key)
                    .cloned()
                    .unwrap_or_else(|| "candidate".into()),
                None,
            )
        }
    }
    fn shared(&self, kind: &str, entity: &str) -> bool {
        self.shared.contains(&(kind.into(), entity.into()))
    }
}
fn summary(resource: &mut Value, relation: &Value) {
    if resource.get("thread_relation_summary").is_none() {
        resource["thread_relation_summary"] =
            json!({"confirmed":[],"candidate":[],"pending":[],"rejected":[]});
    }
    let state = text(relation, "state").unwrap();
    if let Some(items) = resource["thread_relation_summary"]
        .get_mut(state)
        .and_then(Value::as_array_mut)
    {
        if !items.contains(&relation["thread_id"]) {
            items.push(relation["thread_id"].clone());
        }
    }
}
fn round3(value: f64) -> f64 {
    format!("{value:.3}").parse().expect("finite score")
}
fn score(metadata: usize, evidence: usize, count: usize) -> f64 {
    round3((0.35 + (metadata * 3 + evidence + count.min(10)) as f64 * 0.035).min(0.99))
}
fn relation(
    states: &States,
    thread: i64,
    kind: &str,
    entity: i64,
    score: f64,
    matched: &BTreeSet<String>,
    evidence: &[Value],
) -> Value {
    let (state, relation_type) = states.relation(thread, kind, &entity.to_string());
    json!({"thread_id":thread,"resource_type":kind,"resource_id":entity,"state":state,"relation_type":relation_type,"shared_confirmed":states.shared(kind,&entity.to_string()),"score":score,"matched_tokens":matched,"evidence_ids":evidence})
}
/// Python json.dumps(sort_keys=True) uses spaces in these persisted legacy
/// fingerprints. Compact identity digests elsewhere deliberately remain compact.
pub(super) fn spaced_json(value: &Value) -> String {
    match value {
        Value::Object(items) => {
            let mut keys = items.keys().collect::<Vec<_>>();
            keys.sort();
            format!(
                "{{{}}}",
                keys.into_iter()
                    .map(|key| format!(
                        "{}: {}",
                        serde_json::to_string(key).unwrap(),
                        spaced_json(&items[key])
                    ))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        }
        Value::Array(items) => format!(
            "[{}]",
            items.iter().map(spaced_json).collect::<Vec<_>>().join(", ")
        ),
        other => serde_json::to_string(other).expect("JSON scalar"),
    }
}
fn sort_key(value: &Value) -> (String, String) {
    (
        nonempty(value, "last_event_at")
            .map(str::to_owned)
            .or_else(|| {
                value["mtime_ns"]
                    .as_i64()
                    .filter(|n| *n != 0)
                    .map(|n| n.to_string())
            })
            .or_else(|| nonempty(value, "updated_at").map(str::to_owned))
            .unwrap_or_default(),
        id(&value["id"]),
    )
}
fn version(value: &Value) -> Value {
    json!({"id":value["id"],"last_event_at":value["last_event_at"],"event_count":value["event_count"],"content_hash":value["content_hash"],"updated_at":value["updated_at"]})
}
pub fn build_candidate_bundle(connection: &Connection, workstream: &Value) -> Result<Value> {
    let states = States::load(connection, integer(workstream, "id"))?;
    let mut resources = json!({"sessions":{},"documents":{},"projects":{},"local_paths":{},"external_references":{}});
    let mut evidence: Map<String, Value> = Map::new();
    let mut relations: Map<String, Value> = Map::new();
    let mut events: BTreeMap<i64, Vec<Value>> = BTreeMap::new();
    let mut bodies: BTreeMap<i64, String> = BTreeMap::new();
    for thread in workstream["threads"]
        .as_array()
        .into_iter()
        .flatten()
        .filter(|thread| thread["status"] != "done")
    {
        let tid = integer(thread, "id");
        let (query, work, candidate) = query(workstream, thread);
        for row in matching(connection, &candidate)? {
            let kind = text(&row, "entity_type").unwrap();
            let eid = id(&row["entity_id"]).parse::<i64>().map_err(|_| {
                crate::backend::BackendError::invalid("candidate", "Invalid indexed identity")
            })?;
            let eid_string = eid.to_string();
            let resource_group = group(kind).unwrap();
            let metadata = query
                .intersection(&tokens(&joined(&row, &["title", "path"])))
                .cloned()
                .collect::<BTreeSet<_>>();
            if resources[resource_group].get(&eid_string).is_none() {
                let selection = if kind == "session" {
                    sql::SESSION_RESOURCE_0
                } else {
                    sql::DOCUMENT_RESOURCE_0
                };
                let Some(resource) = db::row(connection, selection, [eid])? else {
                    continue;
                };
                resources[resource_group][&eid_string] = resource;
                resources[resource_group][&eid_string]["thread_relation_summary"] =
                    json!({"confirmed":[],"candidate":[],"pending":[],"rejected":[]});
            }
            let resource_key = format!("{kind}:{eid}");
            let resource_evidence = evidence
                .entry(resource_key)
                .or_insert_with(|| json!({}))
                .as_object_mut()
                .unwrap();
            let mut evidence_ids = Vec::new();
            let mut evidence_tokens = BTreeSet::new();
            if kind == "session" {
                if let std::collections::btree_map::Entry::Vacant(entry) = events.entry(eid) {
                    entry.insert(db::rows(connection, sql::BUILD_CANDIDATE_BUNDLE_0, [eid])?);
                    let tools = events[&eid]
                        .iter()
                        .filter_map(|event| nonempty(event, "tool_name"))
                        .collect::<BTreeSet<_>>();
                    resources[resource_group][&eid_string]["tools"] = json!(tools);
                }
                for event in &events[&eid] {
                    let Some(value) = nonempty(event, "text") else {
                        continue;
                    };
                    let event_tokens = tokens(value);
                    if candidate.is_disjoint(&event_tokens) {
                        continue;
                    }
                    let matched = query
                        .intersection(&event_tokens)
                        .cloned()
                        .collect::<BTreeSet<_>>();
                    evidence_tokens.extend(matched.iter().cloned());
                    evidence_ids.push(event["id"].clone());
                    resource_evidence.entry(id(&event["id"])).or_insert_with(||json!({"id":event["id"],"sequence":event["sequence"],"occurred_at":event["occurred_at"],"event_type":event["event_type"],"role":event["role"],"text":excerpt(value,&matched)}));
                }
            } else {
                if let std::collections::btree_map::Entry::Vacant(entry) = bodies.entry(eid) {
                    let body = db::row(connection, sql::BUILD_CANDIDATE_BUNDLE_1, [eid])?;
                    entry.insert(
                        body.as_ref()
                            .and_then(|row| text(row, "body"))
                            .unwrap_or_default()
                            .to_owned(),
                    );
                }
                for (line_number, line) in
                    unicode::splitlines(&bodies[&eid]).into_iter().enumerate()
                {
                    let line_tokens = tokens(line);
                    if candidate.is_disjoint(&line_tokens) {
                        continue;
                    }
                    let matched = query
                        .intersection(&line_tokens)
                        .cloned()
                        .collect::<BTreeSet<_>>();
                    evidence_tokens.extend(matched.iter().cloned());
                    let evidence_id = format!("document:{eid}:line:{}", line_number + 1);
                    evidence_ids.push(evidence_id.clone().into());
                    resource_evidence.entry(evidence_id.clone()).or_insert_with(||json!({"id":evidence_id,"line":line_number+1,"text":excerpt(line,&matched)}));
                }
            }
            let matched = metadata
                .union(&evidence_tokens)
                .cloned()
                .collect::<BTreeSet<_>>();
            let mut relation = relation(
                &states,
                tid,
                kind,
                eid,
                score(metadata.len(), evidence_tokens.len(), evidence_ids.len()),
                &matched,
                &evidence_ids,
            );
            relation["workstream_tokens"] = json!(work.intersection(&matched).collect::<Vec<_>>());
            summary(&mut resources[resource_group][&eid_string], &relation);
            relations.insert(relation_key(tid, kind, &eid_string), relation);
        }
    }
    derived(
        connection,
        integer(workstream, "id"),
        &states,
        &mut resources,
        &mut relations,
    )?;
    for (thread, kind, eid, relation_type) in &states.confirmed {
        let Some(group) = group(kind) else { continue };
        let Some(resource) = resources[group].get_mut(eid) else {
            continue;
        };
        let key = relation_key(*thread, kind, eid);
        let relation=relations.entry(key).or_insert_with(||json!({"thread_id":thread,"resource_type":kind,"resource_id":eid.parse::<i64>().unwrap_or_default(),"state":"confirmed","relation_type":relation_type,"shared_confirmed":states.shared(kind,eid),"score":1.0,"matched_tokens":[],"evidence_ids":[]}));
        relation["state"] = "confirmed".into();
        relation["relation_type"] = relation_type.clone().into();
        summary(resource, relation);
    }
    let mut candidate_resources = Map::new();
    for (_, group) in GROUPS {
        let mut values = resources[group]
            .as_object()
            .unwrap()
            .values()
            .cloned()
            .collect::<Vec<_>>();
        values.sort_by_key(|value| std::cmp::Reverse(sort_key(value)));
        candidate_resources.insert((*group).into(), values.into());
    }
    let mut relations = relations.into_values().collect::<Vec<_>>();
    relations.sort_by(|a, b| {
        integer(a, "thread_id")
            .cmp(&integer(b, "thread_id"))
            .then_with(|| {
                b["score"]
                    .as_f64()
                    .unwrap()
                    .total_cmp(&a["score"].as_f64().unwrap())
            })
            .then_with(|| text(a, "resource_type").cmp(&text(b, "resource_type")))
            .then_with(|| id(&a["resource_id"]).cmp(&id(&b["resource_id"])))
    });
    let versions = candidate_resources
        .iter()
        .map(|(key, values)| {
            (
                key.clone(),
                Value::Array(values.as_array().unwrap().iter().map(version).collect()),
            )
        })
        .collect::<Map<_, _>>();
    let projected=relations.iter().map(|relation|json!({"thread_id":relation["thread_id"],"resource_type":relation["resource_type"],"resource_id":relation["resource_id"],"score":relation["score"],"matched_tokens":relation["matched_tokens"],"evidence_ids":relation["evidence_ids"]})).collect::<Vec<_>>();
    let fingerprint = format!(
        "{:x}",
        Sha256::digest(
            spaced_json(&json!({"resources":versions,"relations":projected})).as_bytes()
        )
    );
    let evidence_count = evidence
        .values()
        .map(|items| items.as_object().unwrap().len())
        .sum::<usize>();
    let evidence = evidence
        .into_iter()
        .map(|(key, items)| {
            (
                key,
                Value::Array(items.as_object().unwrap().values().cloned().collect()),
            )
        })
        .collect::<Map<_, _>>();
    let mut counts = candidate_resources
        .iter()
        .map(|(key, values)| (key.clone(), json!(values.as_array().unwrap().len())))
        .collect::<Map<_, _>>();
    counts.insert("thread_resource_matches".into(), relations.len().into());
    counts.insert("evidence_items".into(), evidence_count.into());
    Ok(
        json!({"policy":{"retriever":"sqlite-fts5-and-structured-signals","ai_used":false,"candidate_count_limit":null,"evidence_count_limit_per_resource":null,"deduplication":"resource and evidence IDs","session_candidates":{"session_class":"work","session_role":"primary","excluded":["maintenance","subsession"]}},"fingerprint":fingerprint,"counts":counts,"candidate_resources":candidate_resources,"thread_resource_matches":relations,"_evidence":evidence}),
    )
}
fn derived(
    connection: &Connection,
    workstream: i64,
    states: &States,
    resources: &mut Value,
    relations: &mut Map<String, Value>,
) -> Result<()> {
    let sources = resources["sessions"]
        .as_object()
        .unwrap()
        .values()
        .chain(resources["documents"].as_object().unwrap().values())
        .cloned()
        .collect::<Vec<_>>();
    for source in sources {
        let Some(workspace) = source["workspace_id"].as_i64().filter(|id| *id != 0) else {
            continue;
        };
        let Some(project) = db::row(connection, sql::ADD_DERIVED_RESOURCES_0, [workspace])? else {
            continue;
        };
        let wid = workspace.to_string();
        if resources["projects"].get(&wid).is_none() {
            resources["projects"][&wid] = project;
        }
        if resources["projects"][&wid]
            .get("thread_relation_summary")
            .is_none()
        {
            resources["projects"][&wid]["thread_relation_summary"] =
                json!({"confirmed":[],"candidate":[],"pending":[],"rejected":[]});
        }
        let source_type = if nonempty(&source, "source_path").is_some() {
            "session"
        } else {
            "document"
        };
        let source_id = id(&source["id"]);
        let related = relations
            .values()
            .filter(|relation| {
                relation["resource_type"] == source_type
                    && id(&relation["resource_id"]) == source_id
            })
            .cloned()
            .collect::<Vec<_>>();
        for source_relation in related {
            let thread = integer(&source_relation, "thread_id");
            let key = relation_key(thread, "project", &wid);
            let score = round3(source_relation["score"].as_f64().unwrap() - 0.05).max(0.35);
            let derived = json!({"resource_type":source_type,"resource_id":source["id"]});
            if let Some(existing) = relations.get_mut(&key) {
                let ids = existing["evidence_ids"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .chain(source_relation["evidence_ids"].as_array().unwrap())
                    .map(id)
                    .collect::<BTreeSet<_>>();
                existing["evidence_ids"] = json!(ids);
                if existing.get("derived_from").is_none() {
                    existing["derived_from"] = json!([]);
                }
                existing["derived_from"]
                    .as_array_mut()
                    .unwrap()
                    .push(derived);
                existing["score"] = existing["score"].as_f64().unwrap().max(score).into();
            } else {
                let (state, relation_type) = states.relation(thread, "project", &wid);
                relations.insert(key.clone(),json!({"thread_id":thread,"resource_type":"project","resource_id":workspace,"state":state,"relation_type":relation_type,"shared_confirmed":states.shared("project",&wid),"score":score,"matched_tokens":source_relation["matched_tokens"],"evidence_ids":source_relation["evidence_ids"],"derived_from":[derived]}));
            }
            summary(&mut resources["projects"][&wid], &relations[&key]);
        }
    }
    let thread_queries = db::rows(connection, sql::ADD_DERIVED_RESOURCES_1, [workstream])?
        .into_iter()
        .map(|thread| {
            let title = tokens(text(&thread, "title").unwrap_or_default());
            (
                integer(&thread, "id"),
                if title.is_empty() {
                    tokens(&joined(&thread, &["summary", "current_goal"]))
                } else {
                    title
                },
            )
        })
        .collect::<Vec<_>>();
    for (resource_group, kind, selection, fields) in [
        (
            "projects",
            "project",
            sql::ADD_DERIVED_RESOURCES_2,
            &["title", "canonical_path", "git_root"][..],
        ),
        (
            "local_paths",
            "local",
            sql::ADD_DERIVED_RESOURCES_3,
            &["title", "path", "summary"][..],
        ),
        (
            "external_references",
            "external",
            sql::ADD_DERIVED_RESOURCES_4,
            &["title", "url", "summary"][..],
        ),
    ] {
        for item in db::rows(connection, selection, [])? {
            let item_tokens = tokens(&joined(&item, fields));
            let eid = id(&item["id"]);
            for (thread, query) in &thread_queries {
                let matched = query
                    .intersection(&item_tokens)
                    .cloned()
                    .collect::<BTreeSet<_>>();
                if matched.is_empty() {
                    continue;
                }
                if resources[resource_group].get(&eid).is_none() {
                    resources[resource_group][&eid] = item.clone();
                }
                let key = relation_key(*thread, kind, &eid);
                let mut value = relation(
                    states,
                    *thread,
                    kind,
                    integer(&item, "id"),
                    score(matched.len(), 0, 0),
                    &matched,
                    &[],
                );
                if let Some(existing) = relations.get_mut(&key) {
                    existing["score"] = existing["score"]
                        .as_f64()
                        .unwrap()
                        .max(value["score"].as_f64().unwrap())
                        .into();
                    let matched = existing["matched_tokens"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .filter_map(Value::as_str)
                        .map(str::to_owned)
                        .chain(matched)
                        .collect::<BTreeSet<_>>();
                    existing["matched_tokens"] = json!(matched);
                    value = existing.clone();
                } else {
                    relations.insert(key, value.clone());
                }
                summary(&mut resources[resource_group][&eid], &value);
            }
        }
    }
    Ok(())
}
pub fn write_candidate_evidence(bundle: &Value, run_root: &Path, config: &Config) -> Result<Value> {
    let mut output = bundle.clone();
    let evidence = output
        .as_object_mut()
        .unwrap()
        .remove("_evidence")
        .unwrap_or_else(|| json!({}));
    let root = run_root.join("evidence");
    for (key, items) in evidence.as_object().into_iter().flatten() {
        let Some((kind, eid)) = key.split_once(':') else {
            continue;
        };
        let directory = root.join(format!("{kind}s"));
        storage::files::private_directory(&directory, config)?;
        let path = directory.join(format!("{eid}.json"));
        storage::files::atomic_write(&path,serde_json::to_string_pretty(&json!({"schema":"localbrain.resource-evidence.v1","resource_type":kind,"resource_id":eid.parse::<i64>().unwrap(),"evidence":items}))?.as_bytes())?;
        let group = if kind == "session" {
            "sessions"
        } else {
            "documents"
        };
        for resource in output["candidate_resources"][group].as_array_mut().unwrap() {
            if id(&resource["id"]) == eid {
                resource["evidence_path"] = path.to_string_lossy().into_owned().into();
                resource["evidence_count"] = items.as_array().unwrap().len().into();
                break;
            }
        }
    }
    output["evidence_root"] = root.to_string_lossy().into_owned().into();
    Ok(output)
}
