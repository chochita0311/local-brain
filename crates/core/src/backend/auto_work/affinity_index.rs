use super::{
    common::*,
    graph,
    inventory::{self, EXTRACTION, OWNER},
    store,
};
use crate::backend::Result;
use chrono::{DateTime, Utc};
use serde_json::{json, Map, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    os::unix::fs::{MetadataExt, OpenOptionsExt},
    path::{Path, PathBuf},
    sync::{Arc, LazyLock, Mutex},
};
pub(super) struct Indexed {
    pub report: Value,
    pub sessions: Map<String, Value>,
    pub groups: Map<String, Value>,
    pub children: BTreeMap<String, Map<String, Value>>,
    pub membership: BTreeMap<String, usize>,
    pub snapshot: String,
    pub counts: Value,
}
#[derive(Clone)]
pub(super) enum Loaded {
    State(Value),
    Current(Arc<Indexed>),
}
#[derive(PartialEq, Eq)]
struct CacheKey {
    path: PathBuf,
    report: Option<Signature>,
    database: Option<Signature>,
    wal: Option<Signature>,
}
type Signature = (u64, u64, u64, i64, i64, i64, i64);
static CACHE: LazyLock<Mutex<Option<(CacheKey, Loaded)>>> = LazyLock::new(|| Mutex::new(None));
pub(super) fn state(name: &str) -> Value {
    let (title,explanation)=match name{
        "missing"=>("전체 이력 계산이 아직 없습니다","기존 로컬 시뮬레이션 명령으로 결과를 준비한 뒤 다시 열어 주세요. 화면을 여는 것만으로 계산하지 않습니다."),
        "busy"=>("결과를 준비하고 있습니다","완료된 결과가 게시된 뒤 다시 열어 주세요. 이 화면에서 새 계산을 시작하지는 않습니다."),
        "expired"=>("보관 기한이 지난 결과입니다","30일 비활성 보관 기한이 지났습니다. 명시적으로 다시 계산해 주세요. 원본 기록은 그대로 있습니다."),
        "invalid"=>("결과를 안전하게 읽을 수 없습니다","결과의 형식·크기·소유권·설정이 맞지 않습니다. 기존 시뮬레이션 저장소를 확인해 주세요. 화면에서 덮어쓰지 않습니다."),
        "unavailable"=>("원본 저장소를 읽을 수 없습니다","로컬 원본의 이용 가능 여부를 확인한 뒤 다시 열어 주세요."),
        "stale"=>("계산 이후 원본이 달라졌습니다","변경된 근거를 현재 결과처럼 보여주지 않습니다. 기존 명령으로 누락·변경 입력만 재계산해 주세요."),
        "selection-stale"=>("이 선택은 현재 결과에 없습니다","이전 계산의 링크이거나 존재하지 않는 선택입니다. 다른 묶음으로 자동 연결하지 않았습니다."),_=>("","")};
    json!({"version":"localbrain.session-affinity.v2","state":name,"title":title,"explanation":explanation})
}
fn string(value: &Value) -> Result<&str> {
    value.as_str().ok_or_else(|| failure("INVALID_INPUT"))
}
fn array(value: &Value) -> Result<&Vec<Value>> {
    value.as_array().ok_or_else(|| failure("INVALID_INPUT"))
}
fn hash(value: &Value) -> bool {
    value.as_str().is_some_and(|value| {
        value.len() == 64
            && value
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    })
}
fn count(value: &Value) -> Option<usize> {
    value
        .as_u64()
        .and_then(|value| value.try_into().ok())
        .or_else(|| {
            value
                .as_f64()
                .filter(|value| {
                    value.is_finite()
                        && *value >= 0.0
                        && value.fract() == 0.0
                        && *value <= usize::MAX as f64
                })
                .map(|value| value as usize)
        })
        .or_else(|| value.as_bool().map(usize::from))
}
fn members(value: &Value) -> Result<BTreeSet<String>> {
    array(value)?
        .iter()
        .map(|value| Ok(string(value)?.to_owned()))
        .collect()
}
fn describe(
    group: &Value,
    kind: &str,
    inputs: &BTreeMap<String, Vec<Value>>,
    sessions: &Map<String, Value>,
) -> Result<Value> {
    let raw_members = array(&group["members"])?;
    let members = members(&group["members"])?;
    require(
        !members.is_empty()
            && members.len() == raw_members.len()
            && members.iter().all(|key| inputs.contains_key(key)),
        "INVALID_INPUT",
    )?;
    require(
        group["id"] == digest(&json!([kind, members])),
        "INVALID_INPUT",
    )?;
    let mut chunks = raw_members
        .iter()
        .flat_map(|node| inputs[node.as_str().unwrap()].iter().cloned())
        .collect::<Vec<_>>();
    chunks.sort_by(|a, b| {
        a["at"]
            .as_str()
            .unwrap_or_default()
            .cmp(b["at"].as_str().unwrap_or_default())
            .then_with(|| a["key"].as_str().cmp(&b["key"].as_str()))
    });
    let keys = chunks
        .iter()
        .map(|chunk| chunk["session_key"].as_str().unwrap())
        .collect::<BTreeSet<_>>();
    let dates = chunks
        .iter()
        .filter_map(|chunk| chunk["at"].as_str())
        .collect::<BTreeSet<_>>();
    Ok(
        json!({"id":group["id"],"kind":if kind=="area"{"group"}else{"subgroup"},"title":sessions[chunks[0]["session_key"].as_str().unwrap()]["title"],"members":members,"chunks":chunks,"session_keys":keys,"sessions":keys.len(),"occurrences":chunks.len(),"vectors":raw_members.len(),"first":dates.first(),"last":dates.last()}),
    )
}
pub(super) fn index(report: Value) -> Result<Indexed> {
    require(
        report["owner"] == OWNER
            && report["processing_complete"] == true
            && report["quality"] == "unassessed"
            && report["lineage_status"] == "not_inferred",
        "INVALID_INPUT",
    )?;
    let manifest = &report["manifest"];
    let grouping = &report["grouping"];
    require(
        manifest["sampled"] == false
            && manifest["extraction"] == EXTRACTION
            && manifest["chunk_chars"]
                .as_u64()
                .is_some_and(|n| (128..=16000).contains(&n))
            && hash(&manifest["digest"]),
        "INVALID_INPUT",
    )?;
    timestamp(string(&report["created_at"])?)?;
    graph::validate_parameters(&report["parameters"])?;
    require(
        report["namespace"]
            == digest(&json!([
                report["model"],
                EXTRACTION,
                manifest["chunk_chars"]
            ]))
            && report["configuration"]
                == digest(&json!([
                    report["namespace"],
                    report["parameters"],
                    grouping["engine"]
                ]))
            && grouping["authority"] == "inferred-affinity-only"
            && grouping["engine"]["method"] == graph::GROUPING_METHOD,
        "INVALID_INPUT",
    )?;
    let mut sessions = Map::new();
    let statuses = [
        "eligible",
        "excluded-maintenance",
        "excluded-subsession",
        "excluded-metadata-only",
        "excluded-missing-source",
    ];
    for session in array(&report["sessions"])? {
        let key = string(&session["key"])?;
        require(
            hash(&session["key"])
                && !sessions.contains_key(key)
                && statuses.contains(&string(&session["status"])?)
                && session["id"].as_i64().is_some_and(|n| n > 0)
                && session["title"]
                    .as_str()
                    .is_some_and(|title| title.chars().count() <= 300),
            "INVALID_INPUT",
        )?;
        sessions.insert(key.into(), session.clone());
    }
    let mut inputs: BTreeMap<String, Vec<Value>> = BTreeMap::new();
    let mut seen = BTreeSet::new();
    let mut characters = 0usize;
    let mut with_text = BTreeSet::new();
    for chunk in array(&report["chunks"])? {
        let skey = string(&chunk["session_key"])?;
        require(
            sessions
                .get(skey)
                .is_some_and(|session| session["status"] == "eligible"),
            "INVALID_INPUT",
        )?;
        let start = chunk["start"]
            .as_u64()
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        let end = chunk["end"]
            .as_u64()
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        require(
            start < end && end - start <= manifest["chunk_chars"].as_u64().unwrap(),
            "INVALID_INPUT",
        )?;
        require(
            chunk["event_id"]
                .as_str()
                .is_some_and(|value| value.chars().count() <= 1000)
                && ["user", "assistant"].contains(&string(&chunk["role"])?)
                && hash(&chunk["input_hash"])
                && hash(&chunk["content_hash"]),
            "INVALID_INPUT",
        )?;
        let key = string(&chunk["key"])?;
        require(
            key == digest(&json!([skey, chunk["event_id"], start, end]))
                && seen.insert(key.to_owned()),
            "INVALID_INPUT",
        )?;
        if !chunk["at"].is_null() {
            timestamp(string(&chunk["at"])?)?;
        }
        characters = characters
            .checked_add((end - start) as usize)
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        with_text.insert(skey.to_owned());
        inputs
            .entry(string(&chunk["input_hash"])?.into())
            .or_default()
            .push(chunk.clone());
    }
    let coverage = &manifest["coverage"];
    require(
        count(&coverage["total_sessions"]) == Some(sessions.len())
            && count(&coverage["chunks"]) == Some(seen.len())
            && count(&coverage["admitted_characters"]) == Some(characters)
            && count(&coverage["sessions_with_text"]) == Some(with_text.len())
            && count(&coverage["sessions_without_text"])
                == count(&coverage["eligible_sessions"])
                    .and_then(|n| n.checked_sub(with_text.len())),
        "INVALID_INPUT",
    )?;
    for status in statuses {
        require(
            count(&coverage[format!("{status}_sessions")])
                == Some(
                    sessions
                        .values()
                        .filter(|session| session["status"] == status)
                        .count(),
                ),
            "INVALID_INPUT",
        )?;
    }
    require(
        count(&report["cache"]["total"]) == Some(inputs.len())
            && count(&grouping["node_count"]) == Some(inputs.len()),
        "INVALID_INPUT",
    )?;
    let mut groups = Map::new();
    let mut children = BTreeMap::new();
    let mut assigned = BTreeSet::new();
    let mut membership = BTreeMap::new();
    for area in array(&grouping["areas"])? {
        let description = describe(area, "area", &inputs, &sessions)?;
        let aid = string(&description["id"])?.to_owned();
        let area_members = members(&description["members"])?;
        require(
            !groups.contains_key(&aid) && assigned.is_disjoint(&area_members),
            "INVALID_INPUT",
        )?;
        assigned.extend(area_members.clone());
        let mut parts = Map::new();
        let mut used = BTreeSet::new();
        for work in array(&area["work_groups"])? {
            let sub = describe(work, "work", &inputs, &sessions)?;
            let sid = string(&sub["id"])?.to_owned();
            let sub_members = members(&sub["members"])?;
            require(
                !parts.contains_key(&sid) && used.is_disjoint(&sub_members),
                "INVALID_INPUT",
            )?;
            used.extend(sub_members);
            parts.insert(sid, sub);
        }
        require(used == area_members, "INVALID_INPUT")?;
        for session in array(&description["session_keys"])? {
            *membership.entry(string(session)?.to_owned()).or_default() += 1usize;
        }
        groups.insert(aid.clone(), description);
        children.insert(aid, parts);
    }
    require(
        assigned == inputs.keys().cloned().collect(),
        "INVALID_INPUT",
    )?;
    let mut edge_keys = BTreeSet::new();
    for edge in array(&grouping["edges"])? {
        let a = string(&edge["left"])?;
        let b = string(&edge["right"])?;
        require(
            inputs.contains_key(a)
                && inputs.contains_key(b)
                && a < b
                && edge_keys.insert((a.to_owned(), b.to_owned()))
                && edge["similarity"]
                    .as_f64()
                    .is_some_and(|weight| weight.is_finite() && (0.0..=1.0).contains(&weight)),
            "INVALID_INPUT",
        )?;
    }
    require(
        count(&grouping["edge_count"]) == Some(edge_keys.len()),
        "INVALID_INPUT",
    )?;
    let counts = json!({"groups":groups.len(),"cross_session":groups.values().filter(|group|group["sessions"].as_u64().unwrap()>1).count(),"single_session":groups.values().filter(|group|group["sessions"]==1).count(),"overlap_sessions":membership.values().filter(|count|**count>1).count(),"vectors":inputs.len()});
    let snapshot = digest(&json!([manifest["digest"], report["configuration"]]));
    Ok(Indexed {
        report,
        sessions,
        groups,
        children,
        membership,
        snapshot,
        counts,
    })
}
pub(super) fn load(database: &Path, folder: &Path, at: DateTime<Utc>) -> Result<Loaded> {
    if !folder.exists() {
        return Ok(Loaded::State(state("missing")));
    }
    require(
        !folder.is_symlink() && folder == fs::canonicalize(folder)?,
        "INVALID_INPUT",
    )?;
    let info = fs::metadata(folder)?;
    require(
        info.is_dir() && info.uid() == unsafe { libc::getuid() } && info.mode() & 0o077 == 0,
        "INVALID_INPUT",
    )?;
    if !database.is_file() || database.is_symlink() {
        return Ok(Loaded::State(state("unavailable")));
    }
    let path = folder.join("writer.lock");
    safe_file(&path)?;
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?;
    if lock(&file, libc::LOCK_SH).is_err() {
        return Ok(Loaded::State(state("busy")));
    }
    let marker = read_json(&folder.join("owner.json"), 65536)?;
    require(
        marker["owner"] == OWNER && marker["database"] == store::binding(database)?,
        "INVALID_INPUT",
    )?;
    if utc(string(&marker["expires_at"])?)? <= at {
        *CACHE.lock().unwrap() = None;
        return Ok(Loaded::State(state("expired")));
    }
    let target = folder.join("report.json");
    if !target.exists() {
        return Ok(Loaded::State(state("missing")));
    }
    safe_file(&target)?;
    let wal = database.with_file_name(format!(
        "{}-wal",
        database.file_name().unwrap().to_string_lossy()
    ));
    let source = (signature(database), signature(&wal));
    let key = CacheKey {
        path: target.clone(),
        report: signature(&target),
        database: source.0,
        wal: source.1,
    };
    let mut cache = CACHE.lock().unwrap();
    if let Some((previous, value)) = cache.as_ref() {
        if *previous == key {
            return Ok(value.clone());
        }
    }
    let indexed = index(read_json(&target, 128 * 1024 * 1024)?)?;
    let mut current = BTreeMap::new();
    let manifest = inventory::inventory(
        database,
        indexed.report["manifest"]["chunk_chars"].as_u64().unwrap() as usize,
        |kind, value| {
            if kind == "chunk" {
                current.insert(
                    value["key"].as_str().unwrap().to_owned(),
                    value["input_hash"].as_str().unwrap().to_owned(),
                );
            }
            Ok(())
        },
    )?;
    if (signature(database), signature(&wal)) != source {
        return Ok(Loaded::State(state("busy")));
    }
    let loaded = if manifest != indexed.report["manifest"] {
        let old = indexed.report["chunks"]
            .as_array()
            .unwrap()
            .iter()
            .map(|chunk| {
                (
                    chunk["key"].as_str().unwrap().to_owned(),
                    chunk["input_hash"].as_str().unwrap().to_owned(),
                )
            })
            .collect::<BTreeMap<_, _>>();
        let mut value = state("stale");
        value["coverage"] = indexed.report["manifest"]["coverage"].clone();
        value["current_coverage"] = manifest["coverage"].clone();
        value["created_at"] = indexed.report["created_at"].clone();
        value["delta"] = json!({"added":current.keys().filter(|key|!old.contains_key(*key)).count(),"removed":old.keys().filter(|key|!current.contains_key(*key)).count(),"changed":old.iter().filter(|(key,value)|current.get(*key).is_some_and(|current|current!=*value)).count()});
        Loaded::State(value)
    } else {
        Loaded::Current(Arc::new(indexed))
    };
    *cache = Some((key, loaded.clone()));
    Ok(loaded)
}
