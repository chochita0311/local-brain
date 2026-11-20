//! Passive affinity navigation. Every displayed quote is rechecked against its
//! current source span; browsing never prepares a simulation or creates files.
use super::{
    affinity_index::{self, Indexed, Loaded},
    common::*,
    inventory,
};
use crate::backend::{
    clock, db, search::urlencode, sources::profiles::decimal_integer, unicode, Config, Result,
};
use chrono::{DateTime, Datelike, Duration, Utc};
use serde_json::{json, Map, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
    time::Duration as WallDuration,
};
const VERSION: &str = "localbrain.session-affinity.v2";
fn string<'a>(row: &'a Value, key: &str) -> &'a str {
    row[key].as_str().unwrap_or_default()
}
fn rows(row: &Value, key: &str) -> Vec<Value> {
    row[key].as_array().cloned().unwrap_or_default()
}
fn public(group: &Value) -> Value {
    let mut result = group.clone();
    if let Some(object) = result.as_object_mut() {
        for key in ["chunks", "members", "session_keys"] {
            object.remove(key);
        }
    }
    result
}
fn url(base: &Map<String, Value>, updates: &[(&str, Option<Value>)]) -> String {
    let mut values = base.clone();
    for (key, value) in updates {
        values.insert((*key).into(), value.clone().unwrap_or(Value::Null));
    }
    let pairs = values
        .iter()
        .filter(|(_, value)| !value.is_null() && **value != "")
        .map(|(key, value)| {
            (
                key.as_str(),
                value
                    .as_str()
                    .map(str::to_owned)
                    .unwrap_or_else(|| value.to_string()),
            )
        })
        .collect::<Vec<_>>();
    format!("/auto-work?{}", urlencode(&pairs))
}
fn paginate<'a>(
    items: &'a [Value],
    number: &str,
    size: usize,
) -> Result<(&'a [Value], usize, usize)> {
    let pages = items.len().div_ceil(size).max(1);
    let page = if !number.is_empty()
        && number.chars().all(unicode::python_digit)
        && number.chars().count() <= 6
    {
        decimal_integer(number)
            .ok_or_else(|| failure("INVALID_INPUT"))?
            .max(1) as usize
    } else {
        1
    };
    let page = page.min(pages);
    let start = (page - 1) * size;
    Ok((
        &items[start.min(items.len())..(start + size).min(items.len())],
        page,
        pages,
    ))
}
fn timeline(candidates: &[Value]) -> Result<Value> {
    let mut first: Option<clock::ParsedTimestamp> = None;
    let mut last: Option<DateTime<Utc>> = None;
    let mut unknown = 0;
    let mut known = 0;
    for group in candidates {
        for chunk in rows(group, "chunks") {
            if chunk["at"].is_null() {
                unknown += 1;
                continue;
            }
            let at = timestamp(string(&chunk, "at"))?;
            let utc = at.utc().unwrap();
            if first.is_none_or(|first| utc < first.utc().unwrap()) {
                first = Some(at);
            }
            last = Some(last.map_or(utc, |last| last.max(utc)));
            known += 1;
        }
    }
    let Some(first) = first else {
        return Ok(
            json!({"start":null,"end":null,"period_days":1,"periods":0,"dated_occurrences":0,"unknown_occurrences":unknown}),
        );
    };
    let start = clock::ParsedTimestamp {
        local: first.local.date().and_hms_opt(0, 0, 0).unwrap(),
        offset_micros: first.offset_micros,
    };
    let days = (last.unwrap() - start.utc().unwrap()).num_days() + 1;
    let period_days = days.div_euclid(64) + i64::from(days % 64 != 0);
    let period_days = period_days.max(1);
    let periods = days.div_euclid(period_days) + i64::from(days % period_days != 0);
    let end = clock::ParsedTimestamp {
        local: start.local + Duration::days(periods * period_days),
        ..start
    };
    require((1..=9999).contains(&end.local.year()), "INVALID_TIME")?;
    Ok(
        json!({"start":start.isoformat(),"end":end.isoformat(),"period_days":period_days,"periods":periods,"dated_occurrences":known,"unknown_occurrences":unknown}),
    )
}
fn period(chunk: &Value, timeline: &Value) -> Result<String> {
    if chunk["at"].is_null() {
        return Ok("unknown".into());
    }
    Ok(
        ((utc(string(chunk, "at"))? - utc(string(timeline, "start"))?).num_days()
            / timeline["period_days"]
                .as_i64()
                .ok_or_else(|| failure("INVALID_INPUT"))?)
        .to_string(),
    )
}
fn activity(group: &Value, timeline: &Value) -> Result<Vec<Value>> {
    let mut periods: BTreeMap<String, Vec<Value>> = BTreeMap::new();
    for chunk in rows(group, "chunks") {
        periods
            .entry(period(&chunk, timeline)?)
            .or_default()
            .push(chunk);
    }
    let mut periods = periods.into_iter().collect::<Vec<_>>();
    periods.sort_by_key(|(period, _)| {
        if period == "unknown" {
            65
        } else {
            period.parse().unwrap_or(65)
        }
    });
    periods.into_iter().map(|(period,chunks)|{let mut dates=chunks.iter().filter_map(|chunk|chunk["at"].as_str()).collect::<Vec<_>>();dates.sort();let average=if dates.is_empty(){None}else{Some(dates.iter().map(|date|{let at=utc(date)?;Ok((at.timestamp() as f64+f64::from(at.timestamp_subsec_micros())/1_000_000.0)*1000.0)}).collect::<Result<Vec<_>>>()?.iter().sum::<f64>()/dates.len() as f64)};Ok(json!({"period":period,"first":dates.first(),"last":dates.last(),"at":average,"occurrences":chunks.len(),"sessions":chunks.iter().map(|chunk|string(chunk,"session_key")).collect::<BTreeSet<_>>().len()}))}).collect()
}
fn activity_links(
    group: &Value,
    timeline: &Value,
    base: &Map<String, Value>,
) -> Result<Vec<Value>> {
    activity(group, timeline)?
        .into_iter()
        .map(|mut item| {
            item["href"] = url(
                base,
                &[
                    ("pick", Some(group["id"].clone())),
                    ("period", Some(item["period"].clone())),
                ],
            )
            .into();
            Ok(item)
        })
        .collect()
}
fn node(group: &Value, timeline: &Value, base: &Map<String, Value>, pick: &str) -> Result<Value> {
    let mut result = public(group);
    result["href"] = url(base, &[("pick", Some(group["id"].clone()))]).into();
    result["selected"] = (group["id"] == pick).into();
    result["activity"] = activity_links(group, timeline, base)?.into();
    Ok(result)
}
#[derive(Clone)]
struct Edge {
    weight: f64,
    unknown: bool,
    left_key: String,
    right_key: String,
    left_at: Value,
    right_at: Value,
}
fn add_edge(
    weights: &mut BTreeMap<(String, String), Edge>,
    left: &str,
    right: &str,
    weight: f64,
    a: &Value,
    b: &Value,
) {
    if left == right {
        return;
    }
    let (left, right, a, b) = if left > right {
        (right, left, b, a)
    } else {
        (left, right, a, b)
    };
    let candidate = Edge {
        weight,
        unknown: a["at"].is_null() || b["at"].is_null(),
        left_key: string(a, "key").into(),
        right_key: string(b, "key").into(),
        left_at: a["at"].clone(),
        right_at: b["at"].clone(),
    };
    let key = (left.into(), right.into());
    let replace = weights.get(&key).is_none_or(|old| {
        weight > old.weight
            || (weight == old.weight
                && (candidate.unknown, &candidate.left_key, &candidate.right_key)
                    < (old.unknown, &old.left_key, &old.right_key))
    });
    if replace {
        weights.insert(key, candidate);
    }
}
fn edges(indexed: &Indexed, visible: &[Value]) -> Vec<Value> {
    let mut owners: BTreeMap<String, Map<String, Value>> = BTreeMap::new();
    for item in visible {
        let mut chunks = rows(item, "chunks");
        chunks.sort_by(|a, b| {
            a["at"]
                .is_null()
                .cmp(&b["at"].is_null())
                .then_with(|| string(a, "at").cmp(string(b, "at")))
                .then_with(|| string(a, "key").cmp(string(b, "key")))
        });
        for chunk in chunks {
            owners
                .entry(string(&chunk, "input_hash").into())
                .or_default()
                .entry(string(item, "id"))
                .or_insert(chunk);
        }
    }
    let mut weights = BTreeMap::new();
    for keys in owners.values() {
        for (a, ac) in keys {
            for (b, bc) in keys {
                add_edge(&mut weights, a, b, 1.0, ac, bc);
            }
        }
    }
    for edge in rows(&indexed.report["grouping"], "edges") {
        if let (Some(left), Some(right)) = (
            owners.get(string(&edge, "left")),
            owners.get(string(&edge, "right")),
        ) {
            for (a, ac) in left {
                for (b, bc) in right {
                    add_edge(
                        &mut weights,
                        a,
                        b,
                        edge["similarity"].as_f64().unwrap(),
                        ac,
                        bc,
                    );
                }
            }
        }
    }
    weights.into_iter().map(|((left,right),edge)|json!({"left":left,"right":right,"similarity":edge.weight,"left_at":edge.left_at,"right_at":edge.right_at})).collect()
}
fn evidence(database: &Path, rows: &[Value], sessions: &Map<String, Value>) -> Result<Vec<Value>> {
    let source = read_only_database(database, WallDuration::from_secs(120))?;
    let mut result = Vec::new();
    for chunk in rows {
        let session = &sessions[string(chunk, "session_key")];
        let mut item = chunk.clone();
        item["title"] = session["title"].clone();
        item["available"] = false.into();
        let row=db::row(&source,"SELECT s.id,s.source_id,s.external_id,s.title,s.session_class,s.session_role,s.index_policy,p.id AS registered_source_id,e.role,e.event_type,e.occurred_at,substr(e.text,?,?) AS wording FROM activity_events e JOIN sessions s ON s.id=e.session_id LEFT JOIN sources p ON p.id=s.source_id WHERE e.id=? AND s.id=?",rusqlite::params![chunk["start"].as_u64().unwrap()+1,chunk["end"].as_u64().unwrap()-chunk["start"].as_u64().unwrap(),chunk["event_id"].as_str(),session["id"].as_i64()])?;
        if let Some(row) = row {
            let wording = string(&row, "wording");
            let title = string(&row, "title").chars().take(300).collect::<String>();
            let valid = inventory::status(&row) == "eligible"
                && digest(&json!([row["registered_source_id"], row["external_id"]]))
                    == chunk["session_key"]
                && row["event_type"] == "message"
                && row["role"] == chunk["role"]
                && inventory::date(&row["occurred_at"]) == chunk["at"].as_str().map(str::to_owned)
                && wording.chars().count() as u64
                    == chunk["end"].as_u64().unwrap() - chunk["start"].as_u64().unwrap()
                && sha(wording) == chunk["content_hash"]
                && sha(&inventory::input_text(
                    &title,
                    string(&row, "role"),
                    wording,
                )) == chunk["input_hash"];
            if valid {
                item["available"] = true.into();
                item["wording"] = wording.into();
                item["href"] = format!("/sessions/{}", row["id"]).into();
                item["focus_href"] = format!("/sessions/{}/workflow", row["id"]).into();
            }
        }
        result.push(item);
    }
    Ok(result)
}
fn selected_stale(base: &Map<String, Value>) -> Value {
    let mut state = affinity_index::state("selection-stale");
    state["overview_url"] = url(base, &[("pick", None)]).into();
    state
}
pub fn affinity_page(
    config: &Config,
    params: &BTreeMap<String, String>,
    at: Option<DateTime<Utc>>,
) -> Value {
    affinity_page_at(&config.database_path, &config.cache_dir, params, at)
}
pub fn affinity_page_at(
    database: &Path,
    data_dir: &Path,
    params: &BTreeMap<String, String>,
    at: Option<DateTime<Utc>>,
) -> Value {
    match project(database, data_dir, params, at.unwrap_or_else(Utc::now)) {
        Ok(value) => value,
        Err(error) => affinity_index::state(
            if ["io", "database", "DATABASE_UNAVAILABLE", "INVALID_DATABASE"]
                .contains(&error.code.as_str())
            {
                "unavailable"
            } else {
                "invalid"
            },
        ),
    }
}
fn project(
    database: &Path,
    data_dir: &Path,
    params: &BTreeMap<String, String>,
    at: DateTime<Utc>,
) -> Result<Value> {
    let indexed = match affinity_index::load(database, &data_dir.join("session-simulation"), at)? {
        Loaded::State(value) => return Ok(value),
        Loaded::Current(indexed) => indexed,
    };
    let report = &indexed.report;
    let snapshot = &indexed.snapshot;
    let get = |key: &str| params.get(key).map(String::as_str).unwrap_or_default();
    let (group, subgroup, pick) = (get("group"), get("subgroup"), get("pick"));
    let mut base = Map::new();
    base.insert("snapshot".into(), snapshot.clone().into());
    if (!get("snapshot").is_empty() && get("snapshot") != snapshot)
        || (!group.is_empty() || !subgroup.is_empty() || !pick.is_empty())
            && get("snapshot") != snapshot
    {
        return Ok(selected_stale(&base));
    }
    if !group.is_empty() && !indexed.groups.contains_key(group)
        || !subgroup.is_empty()
            && (group.is_empty()
                || !indexed
                    .children
                    .get(group)
                    .is_some_and(|children| children.contains_key(subgroup)))
    {
        return Ok(selected_stale(&base));
    }
    let mut level = "groups";
    let mut candidates = indexed.groups.values().cloned().collect::<Vec<_>>();
    let mut crumbs = vec![json!({"title":"전체 묶음","href":url(&base,&[])})];
    if !group.is_empty() {
        base.insert("group".into(), group.into());
        candidates = indexed.children[group].values().cloned().collect();
        level = "subgroups";
        crumbs.push(json!({"title":"세부 묶음","href":url(&base,&[])}));
    }
    if !subgroup.is_empty() {
        base.insert("subgroup".into(), subgroup.into());
        level = "sessions";
        let parent = &indexed.children[group][subgroup];
        candidates = Vec::new();
        for key in rows(parent, "session_keys") {
            let key = key.as_str().unwrap();
            let chunks = rows(parent, "chunks")
                .into_iter()
                .filter(|chunk| chunk["session_key"] == key)
                .collect::<Vec<_>>();
            let dates = chunks
                .iter()
                .filter_map(|chunk| chunk["at"].as_str())
                .collect::<BTreeSet<_>>();
            candidates.push(json!({"id":key,"kind":"session","title":indexed.sessions[key]["title"],"chunks":chunks,"members":chunks.iter().map(|chunk|string(chunk,"input_hash")).collect::<BTreeSet<_>>(),"sessions":1,"occurrences":chunks.len(),"first":dates.first(),"last":dates.last()}));
        }
        crumbs.push(json!({"title":"세션","href":url(&base,&[])}));
    }
    if get("inventory") == "all" {
        base = Map::new();
        base.insert("snapshot".into(), snapshot.clone().into());
        base.insert("inventory".into(), "all".into());
        candidates=indexed.sessions.values().map(|session|json!({"id":session["key"],"kind":"inventory","title":session["title"],"status":session["status"],"members":[],"chunks":[],"sessions":1,"occurrences":0,"has_text":indexed.membership.get(string(session,"key")).copied().unwrap_or(0)>0,"membership_count":indexed.membership.get(string(session,"key")).copied().unwrap_or(0)})).collect();
        level = "inventory";
        crumbs = vec![
            crumbs[0].clone(),
            json!({"title":"전체 기록 범위","href":url(&base,&[])}),
        ];
    }
    let q = get("q")
        .chars()
        .take(120)
        .collect::<String>()
        .trim_matches(unicode::python_space)
        .to_owned();
    base.insert("q".into(), q.clone().into());
    candidates.sort_by(|a, b| {
        b["occurrences"]
            .as_u64()
            .cmp(&a["occurrences"].as_u64())
            .then_with(|| string(a, "id").cmp(string(b, "id")))
    });
    let timeline = timeline(&candidates)?;
    let selected = candidates
        .iter()
        .find(|candidate| candidate["id"] == pick)
        .cloned();
    if !pick.is_empty() && selected.is_none() {
        return Ok(selected_stale(&base));
    }
    let folded = unicode::casefold(&q);
    let filtered = candidates
        .iter()
        .filter(|candidate| {
            q.is_empty()
                || unicode::casefold(string(candidate, "title")).contains(&folded)
                || rows(candidate, "session_keys").iter().any(|key| {
                    unicode::casefold(string(&indexed.sessions[key.as_str().unwrap()], "title"))
                        .contains(&folded)
                })
        })
        .cloned()
        .collect::<Vec<_>>();
    let (visible, page, pages) = paginate(
        &filtered,
        params.get("page").map(String::as_str).unwrap_or("1"),
        24,
    )?;
    base.insert("page".into(), page.into());
    let map_nodes = if level != "inventory" {
        filtered
            .iter()
            .map(|group| node(group, &timeline, &base, pick))
            .collect::<Result<Vec<_>>>()?
    } else {
        Vec::new()
    };
    let nodes = visible
        .iter()
        .map(|group| {
            map_nodes
                .iter()
                .find(|node| node["id"] == group["id"])
                .cloned()
                .map(Ok)
                .unwrap_or_else(|| node(group, &timeline, &base, pick))
        })
        .collect::<Result<Vec<_>>>()?;
    let period_selected = get("period");
    let selected_activity = selected
        .as_ref()
        .map(|group| activity_links(group, &timeline, &base))
        .transpose()?
        .unwrap_or_default();
    if !period_selected.is_empty()
        && (selected.is_none()
            || !selected_activity
                .iter()
                .any(|item| item["period"] == period_selected))
    {
        return Ok(selected_stale(&base));
    }
    let mut selection = selected.as_ref().map(public).unwrap_or(Value::Null);
    if !selection.is_null() {
        selection["activity"] = selected_activity.into();
        selection["whole_href"] = url(&base, &[("pick", Some(pick.into()))]).into();
        if ["groups", "subgroups"].contains(&level) {
            selection["expand_href"] = url(
                &base,
                &[
                    (
                        "group",
                        Some(if level == "groups" {
                            selection["id"].clone()
                        } else {
                            group.into()
                        }),
                    ),
                    (
                        "subgroup",
                        if level == "subgroups" {
                            Some(selection["id"].clone())
                        } else {
                            None
                        },
                    ),
                    ("pick", None),
                    ("page", None),
                    ("q", None),
                ],
            )
            .into();
        }
    }
    let evidence_rows = selected
        .as_ref()
        .map(|group| {
            rows(group, "chunks")
                .into_iter()
                .map(|chunk| {
                    let retain =
                        period_selected.is_empty() || period(&chunk, &timeline)? == period_selected;
                    Ok((chunk, retain))
                })
                .collect::<Result<Vec<_>>>()
        })
        .transpose()?
        .unwrap_or_default()
        .into_iter()
        .filter_map(|(chunk, retain)| retain.then_some(chunk))
        .collect::<Vec<_>>();
    let (selected_evidence, ep, eps) = paginate(
        &evidence_rows,
        params
            .get("evidence_page")
            .map(String::as_str)
            .unwrap_or("1"),
        8,
    )?;
    let pair = |key: &str, value: Value| (key.to_owned(), value);
    let base_public = base
        .iter()
        .filter(|(key, _)| key.as_str() != "q")
        .map(|(key, value)| pair(key, value.clone()))
        .collect::<Map<_, _>>();
    Ok(
        json!({"version":VERSION,"state":if indexed.groups.is_empty(){"empty"}else{"current"},"snapshot":snapshot,"created_at":report["created_at"],"coverage":report["manifest"]["coverage"],"counts":indexed.counts,"model":report["model"],"parameters":report["parameters"],"configuration":report["configuration"],"level":level,"nodes":nodes,"map_nodes":map_nodes,"map_scope":[VERSION,snapshot,level,group,subgroup,q],"edges":if level!="inventory"&&!filtered.is_empty(){edges(&indexed,&filtered)}else{Vec::new()},"selection":selection,"timeline":timeline,"period":period_selected,"scope_title":if level=="inventory"{Value::Null}else if !subgroup.is_empty(){indexed.children[group][subgroup]["title"].clone()}else if !group.is_empty(){indexed.groups[group]["title"].clone()}else{Value::Null},"crumbs":crumbs,"q":q,"base":base_public,"total":candidates.len(),"matched":filtered.len(),"page":page,"pages":pages,"previous":if page>1{Some(url(&base,&[("page",Some((page-1).into())),("pick",Some(pick.into())),("period",Some(period_selected.into()))]))}else{None},"next":if page<pages{Some(url(&base,&[("page",Some((page+1).into())),("pick",Some(pick.into())),("period",Some(period_selected.into()))]))}else{None},"evidence":evidence(database,selected_evidence,&indexed.sessions)?,"evidence_page":ep,"evidence_pages":eps,"evidence_total":evidence_rows.len(),"evidence_previous":if ep>1{Some(url(&base,&[("pick",Some(pick.into())),("period",Some(period_selected.into())),("evidence_page",Some((ep-1).into()))]))}else{None},"evidence_next":if ep<eps{Some(url(&base,&[("pick",Some(pick.into())),("period",Some(period_selected.into())),("evidence_page",Some((ep+1).into()))]))}else{None},"clear_url":url(&base,&[]),"overview_url":format!("/auto-work?{}",urlencode(&[("snapshot",snapshot.clone())])),"inventory_url":format!("/auto-work?{}",urlencode(&[("snapshot",snapshot.clone()),("inventory","all".into())]))}),
    )
}
