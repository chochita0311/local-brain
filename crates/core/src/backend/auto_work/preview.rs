//! The retained bounded sample is separate from the full-history affinity map.
use super::{
    common::*,
    reconstruction,
    worker::{self, NativePreviewSupervisor, PreviewSupervisor},
};
use crate::backend::{
    clock, db, search::urlencode, sources::profiles::decimal_integer, storage, unicode, Config,
    Result,
};
use chrono::{DateTime, Duration, Utc};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, File, OpenOptions},
    io::Read,
    os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt},
    path::{Path, PathBuf},
    time::Duration as WallDuration,
};
pub const PREVIEW_OWNER: &str = "localbrain.auto-work-preview.v1";
const DIRECTORY: &str = "auto-work-preview";
const FILENAME: &str = "current.json";
fn changes(key: &str) -> Option<&'static str> {
    match key {
        "reduce" => Some("줄이기"),
        "increase" => Some("늘리기"),
        "improve" => Some("개선"),
        "fix" => Some("수정"),
        "add" => Some("추가"),
        "remove" => Some("제거"),
        "replace" => Some("교체"),
        "enable" => Some("활성화"),
        "disable" => Some("비활성화"),
        _ => None,
    }
}
fn reason(key: &str) -> Option<&'static str> {
    match key {
        "unsupported-goal" => Some("작업 목표를 식별하지 못함"),
        "unsupported-negation" => Some("부정 표현의 의미를 판단하지 못함"),
        "unsupported-subject" => Some("작업 대상을 식별하지 못함"),
        "ambiguous-completion" => Some("완료 조건이 서로 달라 소속을 판단하지 못함"),
        "ineligible-session" => Some("분석 대상이 아닌 세션"),
        _ => None,
    }
}
fn state(name: &str) -> Value {
    let(title,explanation)=match name{"missing"=>("아직 분석 결과가 없습니다","현재 저장된 데이터로 표본 분석을 시작할 수 있습니다."),"expired"=>("분석 결과의 보관 기간이 끝났습니다","현재 데이터로 다시 분석하면 새 결과를 볼 수 있습니다."),"stale"=>("분석 근거가 달라졌습니다","원문이나 접근 범위가 바뀌어 이전 결과를 표시하지 않습니다. 다시 분석해 주세요."),_=>("분석 결과를 불러오지 못했습니다","결과 파일이나 로컬 저장 경로를 확인한 뒤 갱신해 주세요. 알 수 없거나 손상된 파일은 덮어쓰지 않습니다. 원본과 기존 작업 구성은 변경되지 않았습니다.")};
    json!({"state":name,"title":title,"explanation":explanation})
}
fn text<'a>(row: &'a Value, key: &str) -> &'a str {
    row[key].as_str().unwrap_or_default()
}
fn directory(config: &Config, create: bool) -> Result<PathBuf> {
    let base = &config.cache_dir;
    require(
        base.is_absolute()
            && (!base.exists() || base.is_dir())
            && *base == storage::files::resolve(base)?,
        "INVALID_OUTPUT",
    )?;
    if let Some(root) = &config.installation_root {
        require(!base.starts_with(root), "INVALID_OUTPUT")?;
    }
    let folder = base.join(DIRECTORY);
    require(!folder.is_symlink(), "INVALID_OUTPUT")?;
    if create {
        storage::files::private_directory(base, config)?;
        match fs::DirBuilder::new().mode(0o700).create(&folder) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(error) => return Err(error.into()),
        }
    }
    if folder.exists() {
        let info = fs::metadata(&folder)?;
        require(
            info.is_dir() && info.uid() == unsafe { libc::getuid() } && info.mode() & 0o077 == 0,
            "INVALID_OUTPUT",
        )?;
    }
    Ok(folder)
}
fn preview_lock(folder: &Path) -> Result<File> {
    let file = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(folder.join("preview.lock"))?;
    let info = file.metadata()?;
    require(
        info.is_file() && info.uid() == unsafe { libc::getuid() } && info.mode() & 0o077 == 0,
        "INVALID_OUTPUT",
    )?;
    lock(&file, libc::LOCK_EX).map_err(|_| failure("PREVIEW_BUSY"))?;
    Ok(file)
}
pub(super) fn read_preview(path: &Path) -> Result<Value> {
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?;
    let info = file.metadata()?;
    require(
        info.is_file()
            && info.uid() == unsafe { libc::getuid() }
            && info.mode() & 0o077 == 0
            && info.nlink() == 1,
        "INVALID_OUTPUT",
    )?;
    let mut bytes = Vec::new();
    file.take(worker::MAX_PREVIEW_BYTES as u64 + 1)
        .read_to_end(&mut bytes)?;
    let payload = worker::decode_bounded(&bytes)?;
    let expected = [
        "version",
        "owner",
        "created_at",
        "expires_at",
        "manifest",
        "snapshot_digest",
        "preparation",
        "output",
    ]
    .into_iter()
    .collect::<BTreeSet<_>>();
    require(
        payload.as_object().is_some_and(|object| {
            object.keys().map(String::as_str).collect::<BTreeSet<_>>() == expected
        }) && (payload["version"] == 1 || payload["version"] == true)
            && payload["owner"] == PREVIEW_OWNER,
        "INVALID_INPUT",
    )?;
    let retention = utc(text(&payload, "expires_at"))? - utc(text(&payload, "created_at"))?;
    require(
        retention > Duration::zero() && retention <= Duration::days(7),
        "INVALID_INPUT",
    )?;
    reconstruction::validate_manifest(&payload["manifest"])?;
    let manifest = &payload["manifest"];
    require(
        manifest["owner"] == PREVIEW_OWNER
            && manifest["end"] == payload["created_at"]
            && manifest["expires_at"] == payload["expires_at"]
            && manifest["snapshots"]
                .as_array()
                .is_some_and(|values| values.len() == 1)
            && payload["snapshot_digest"]
                .as_str()
                .is_some_and(|value| value.chars().count() == 64),
        "INVALID_INPUT",
    )?;
    let prep = &payload["preparation"];
    require(prep.is_object(), "INVALID_INPUT")?;
    for key in [
        "eligible_sessions",
        "selected_sessions",
        "outside_sample_sessions",
        "omitted_or_truncated_records",
    ] {
        require(prep[key].as_i64().is_some_and(|n| n >= 0), "INVALID_INPUT")?;
    }
    require(
        prep["selected_sessions"].as_i64().unwrap() <= 60
            && prep["selected_sessions"]
                .as_i64()
                .unwrap()
                .checked_add(prep["outside_sample_sessions"].as_i64().unwrap())
                == prep["eligible_sessions"].as_i64()
            && prep["selected_sessions"].as_u64()
                == Some(
                    manifest["snapshots"][0]["session_ids"]
                        .as_array()
                        .unwrap()
                        .len() as u64,
                )
            && payload["output"].is_object()
            && payload["output"]["version"] == reconstruction::VERSION,
        "INVALID_INPUT",
    )?;
    Ok(payload)
}
pub fn prepare_preview(config: &Config, at: Option<DateTime<Utc>>) -> Result<()> {
    prepare_preview_with_supervisor(config, at, &NativePreviewSupervisor::new()?)
}
pub fn prepare_preview_with_supervisor(
    config: &Config,
    at: Option<DateTime<Utc>>,
    supervisor: &dyn PreviewSupervisor,
) -> Result<()> {
    let at = at.unwrap_or_else(Utc::now);
    let through = clock::isoformat(at);
    let expiry = clock::isoformat(at + Duration::days(7));
    let folder = directory(config, true)?;
    let target = folder.join(FILENAME);
    let _lock = preview_lock(&folder)?;
    if target.symlink_metadata().is_ok() {
        read_preview(&target)?;
    }
    let prepared = supervisor.supervise(
        "prepare",
        &json!([
            config.database_path.to_string_lossy(),
            through,
            PREVIEW_OWNER,
            expiry
        ]),
    )?;
    let snapshot = prepared["snapshots"]
        .as_array()
        .and_then(|snapshots| snapshots.last())
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    let output = supervisor.supervise("text", &json!([snapshot, [], false]))?;
    let mut manifest = prepared["manifest"].clone();
    manifest["snapshots"] = json!([prepared["manifest"]["snapshots"]
        .as_array()
        .and_then(|scopes| scopes.last())
        .ok_or_else(|| failure("INVALID_INPUT"))?]);
    let value = json!({"version":1,"owner":PREVIEW_OWNER,"created_at":through,"expires_at":expiry,"manifest":manifest,"snapshot_digest":digest(snapshot),"preparation":prepared["preparation"],"output":output});
    let bytes = worker::encode_bounded(&value)?;
    let mut stage = tempfile::Builder::new()
        .prefix(".staged-")
        .tempfile_in(&folder)?;
    use std::io::Write;
    stage.write_all(&bytes)?;
    stage.flush()?;
    stage.as_file().sync_all()?;
    read_preview(stage.path())?;
    stage.persist(target).map_err(|error| error.error)?;
    Ok(())
}
fn bound_output(output: &Value, data: &Value) -> Result<BTreeMap<String, Value>> {
    let records = data["records"]
        .as_array()
        .ok_or_else(|| failure("INVALID_INPUT"))?
        .iter()
        .filter(|record| record["kind"] != "organization")
        .map(|record| (text(record, "key").to_owned(), record.clone()))
        .collect::<BTreeMap<_, _>>();
    require(
        output["corrections"] == json!([])
            && (output["routine_confirmations"] == 0 || output["routine_confirmations"] == false)
            && output["coverage"] == data["coverage"],
        "INVALID_INPUT",
    )?;
    let flows = output["flows"]
        .as_array()
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    let unknown = output["unassigned"]
        .as_array()
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    let mut seen = BTreeSet::new();
    for flow in flows {
        let id = flow["flow_id"]
            .as_str()
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        require(
            seen.insert(id)
                && flow["authority"] == "inferred"
                && flow["lifecycle"] == "unknown"
                && changes(text(flow, "change")).is_some()
                && flow["subject"]
                    .as_str()
                    .is_some_and(|value| !value.is_empty() && value.chars().count() <= 300)
                && (flow["completion"].is_null() || flow["completion"].is_string()),
            "INVALID_INPUT",
        )?;
        let members = flow["members"]
            .as_array()
            .filter(|members| !members.is_empty())
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        for member in members {
            let (record, wording) = span(member, &records)?;
            require(
                member["wording"] == wording
                    && member["session_id"] == record["session_id"]
                    && member["role"] == record["role"]
                    && member["source_kind"] == record["kind"]
                    && member["observed_at"] == record["at"]
                    && member["authority"] == "inferred"
                    && member["subject"] == flow["subject"]
                    && member["change"] == flow["change"],
                "INVALID_INPUT",
            )?;
        }
    }
    for item in unknown {
        require(
            item.is_object() && reason(text(item, "reason")).is_some(),
            "INVALID_INPUT",
        )?;
        span(item, &records)?;
    }
    Ok(records)
}
fn span<'a>(item: &Value, records: &'a BTreeMap<String, Value>) -> Result<(&'a Value, String)> {
    let record = records
        .get(text(item, "record_key"))
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    let start = item["start"]
        .as_i64()
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    let end = item["end"]
        .as_i64()
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    let offset = record["offset"]
        .as_i64()
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    let text = text(record, "text");
    require(
        offset <= start && start < end && end <= offset + text.chars().count() as i64,
        "INVALID_INPUT",
    )?;
    Ok((
        record,
        text.chars()
            .skip((start - offset) as usize)
            .take((end - start) as usize)
            .collect(),
    ))
}
fn destinations(
    config: &Config,
    manifest: &Value,
    records: &BTreeMap<String, Value>,
) -> Result<BTreeMap<String, Value>> {
    let source = read_only_database(&config.database_path, WallDuration::from_secs(5))?;
    let scope = &manifest["snapshots"][0];
    let mut sessions = BTreeMap::new();
    let mut result = BTreeMap::new();
    for sid in scope["session_ids"].as_array().unwrap() {
        let row = db::row(
            &source,
            "SELECT substr(title,1,500) AS title FROM sessions WHERE id=?",
            [sid.as_i64().unwrap()],
        )?
        .ok_or_else(|| failure("SOURCE_CHANGED"))?;
        let title = row["title"]
            .as_str()
            .filter(|title| !title.is_empty())
            .unwrap_or("제목 없는 세션");
        sessions.insert(
            sid.as_i64().unwrap(),
            json!({"title":title,"href":format!("/sessions/{sid}"),"kind":"세션"}),
        );
    }
    for (key, record) in records {
        if record["kind"] == "session" {
            result.insert(
                key.clone(),
                sessions[&record["session_id"].as_i64().unwrap()].clone(),
            );
        }
    }
    for (field, kind, table, route, label) in [
        (
            "documents",
            "document",
            "context_documents",
            "/documents/",
            "문서",
        ),
        (
            "items",
            "item",
            "external_resources",
            "/atlassian/items/",
            "링크/문서",
        ),
    ] {
        for choice in scope[field].as_array().unwrap() {
            let row = db::row(
                &source,
                &format!("SELECT substr(title,1,500) AS title FROM {table} WHERE id=?"),
                [crate::backend::usage::sql_value(&choice["id"])?],
            )?
            .ok_or_else(|| failure("INVALID_INPUT"))?;
            let id = choice["id"]
                .as_str()
                .map(str::to_owned)
                .unwrap_or_else(|| choice["id"].to_string());
            let key = format!("record:{}", digest(&json!([kind, id])));
            result.insert(key,json!({"title":row["title"].as_str().filter(|title|!title.is_empty()).unwrap_or("제목 없음"),"href":format!("{route}{id}"),"kind":label}));
        }
    }
    Ok(result)
}
fn pages(number: &str, total: usize, size: usize) -> (usize, usize) {
    let parsed = (|| {
        if number.chars().count() > 9 {
            return None;
        }
        let value = number.trim_matches(unicode::python_space);
        let (sign, value) = if let Some(value) = value.strip_prefix('-') {
            (-1, value)
        } else {
            (1, value.strip_prefix('+').unwrap_or(value))
        };
        let chars = value.chars().collect::<Vec<_>>();
        if chars.iter().enumerate().any(|(i, ch)| {
            *ch == '_'
                && (i == 0 || i + 1 == chars.len() || chars[i - 1] == '_' || chars[i + 1] == '_')
        }) {
            return None;
        }
        decimal_integer(&value.replace('_', "")).map(|n| n * sign)
    })();
    let pages = total.div_ceil(size).max(1);
    ((parsed.unwrap_or(1).max(1) as usize).min(pages), pages)
}
fn url(values: &[(&str, Option<String>)]) -> String {
    let mut pairs = vec![("mode", "sample".into())];
    pairs.extend(
        values
            .iter()
            .filter_map(|(key, value)| value.as_ref().map(|value| (*key, value.clone()))),
    );
    format!("/auto-work?{}", urlencode(&pairs))
}
fn evidence(
    item: &Value,
    records: &BTreeMap<String, Value>,
    destinations: &BTreeMap<String, Value>,
) -> Result<Value> {
    let (record, wording) = span(item, records)?;
    let mut result = destinations
        .get(text(record, "key"))
        .cloned()
        .ok_or_else(|| failure("INVALID_INPUT"))?;
    result.as_object_mut().unwrap().extend(json!({"wording":wording,"at":record["at"],"role":match text(record,"role"){"user"=>"사용자","assistant"=>"어시스턴트의 발언","document"=>"문서",_=>"원문"},"start":item["start"],"end":item["end"],"reason":reason(text(item,"reason")),"session_id":record["session_id"]}).as_object().unwrap().clone());
    Ok(result)
}
#[derive(Debug, Clone)]
pub struct PreviewOptions {
    pub page: String,
    pub flow: Option<String>,
    pub view: String,
    pub evidence_page: String,
}
impl Default for PreviewOptions {
    fn default() -> Self {
        Self {
            page: "1".into(),
            flow: None,
            view: "flows".into(),
            evidence_page: "1".into(),
        }
    }
}
pub fn preview_page(config: &Config, options: &PreviewOptions, at: Option<DateTime<Utc>>) -> Value {
    let at = at.unwrap_or_else(Utc::now);
    let mut current_state = "error";
    let result = (|| -> Result<Value> {
        let folder = directory(config, false)?;
        let target = folder.join(FILENAME);
        if !target.exists() && !target.is_symlink() {
            current_state = "missing";
            return Err(failure("PREVIEW_MISSING"));
        }
        let payload = read_preview(&target)?;
        if utc(text(&payload, "expires_at"))? <= at {
            current_state = "expired";
            let _ = (|| -> Result<()> {
                let _lock = preview_lock(&folder)?;
                if utc(text(&read_preview(&target)?, "expires_at"))? <= at {
                    fs::remove_file(&target)?;
                }
                Ok(())
            })();
            return Err(failure("PREVIEW_EXPIRED"));
        }
        current_state = "stale";
        let data = reconstruction::load_snapshots(&config.database_path, &payload["manifest"])?;
        let data = data.first().ok_or_else(|| failure("INVALID_INPUT"))?;
        require(digest(data) == payload["snapshot_digest"], "SOURCE_CHANGED")?;
        current_state = "error";
        let records = bound_output(&payload["output"], data)?;
        let destinations = destinations(config, &payload["manifest"], &records)?;
        view(&payload, &records, &destinations, options)
    })();
    result.unwrap_or_else(|_| state(current_state))
}
fn view(
    payload: &Value,
    records: &BTreeMap<String, Value>,
    destinations: &BTreeMap<String, Value>,
    options: &PreviewOptions,
) -> Result<Value> {
    let output = &payload["output"];
    let mut flows = output["flows"]
        .as_array()
        .unwrap()
        .iter()
        .collect::<Vec<_>>();
    flows.sort_by(|a, b| {
        (text(a, "subject"), text(a, "change"), text(a, "flow_id")).cmp(&(
            text(b, "subject"),
            text(b, "change"),
            text(b, "flow_id"),
        ))
    });
    let (page, pages) = pages(&options.page, flows.len(), 12);
    let visible = &flows[((page - 1) * 12).min(flows.len())..(page * 12).min(flows.len())];
    let mode = if options.view == "unassigned" {
        "unassigned"
    } else {
        "flows"
    };
    let flow = options.flow.as_deref().filter(|flow| !flow.is_empty());
    let selected = if let Some(flow) = flow {
        flows.iter().copied().find(|item| item["flow_id"] == flow)
    } else {
        visible.first().copied()
    };
    let summary = |item: &Value| json!({"id":item["flow_id"],"title":format!("{} · {}",text(item,"subject"),changes(text(item,"change")).unwrap()),"completion":item["completion"],"members":item["members"].as_array().unwrap().len(),"sessions":item["members"].as_array().unwrap().iter().filter_map(|member|member["session_id"].as_i64()).collect::<BTreeSet<_>>().len(),"href":url(&[("page",Some(page.to_string())),("flow",Some(text(item,"flow_id").into()))])});
    let mut rows = if mode == "unassigned" {
        output["unassigned"]
            .as_array()
            .unwrap()
            .iter()
            .collect::<Vec<_>>()
    } else {
        selected
            .map(|flow| flow["members"].as_array().unwrap().iter().collect())
            .unwrap_or_default()
    };
    rows.sort_by(|a, b| {
        let ar = &records[text(a, "record_key")];
        let br = &records[text(b, "record_key")];
        (text(ar, "at"), text(a, "record_key"), a["start"].as_i64()).cmp(&(
            text(br, "at"),
            text(b, "record_key"),
            b["start"].as_i64(),
        ))
    });
    let (ep, eps) = self::pages(&options.evidence_page, rows.len(), 20);
    let current = if mode == "flows" {
        selected.map(|item| text(item, "flow_id").to_owned())
    } else {
        None
    };
    let assigned = flows
        .iter()
        .flat_map(|flow| flow["members"].as_array().unwrap())
        .map(|member| text(member, "record_key"))
        .collect::<BTreeSet<_>>();
    let evidence = rows[((ep - 1) * 20).min(rows.len())..(ep * 20).min(rows.len())]
        .iter()
        .map(|item| evidence(item, records, destinations))
        .collect::<Result<Vec<_>>>()?;
    Ok(
        json!({"state":"ready","created_at":payload["created_at"],"expires_at":payload["expires_at"],"start":payload["manifest"]["start"],"preparation":payload["preparation"],"coverage":output["coverage"],"group_count":flows.len(),"unassigned_count":output["unassigned"].as_array().unwrap().len(),"record_count":records.len(),"assigned_record_count":assigned.len(),"mode":mode,"groups":visible.iter().map(|item|summary(item)).collect::<Vec<_>>(),"selected":if mode=="flows"{selected.map(summary)}else{None},"selection_missing":flow.is_some()&&selected.is_none(),"page":page,"pages":pages,"previous":if page>1{Some(url(&[("page",Some((page-1).to_string()))]))}else{None},"next":if page<pages{Some(url(&[("page",Some((page+1).to_string()))]))}else{None},"flows_url":url(&[("page",Some(page.to_string())),("flow",options.flow.clone())]),"unassigned_url":url(&[("page",Some(page.to_string())),("view",Some("unassigned".into()))]),"evidence":evidence,"evidence_total":rows.len(),"evidence_page":ep,"evidence_pages":eps,"evidence_previous":if ep>1{Some(url(&[("page",Some(page.to_string())),("flow",current.clone()),("view",Some(mode.into())),("evidence_page",Some((ep-1).to_string()))]))}else{None},"evidence_next":if ep<eps{Some(url(&[("page",Some(page.to_string())),("flow",current),("view",Some(mode.into())),("evidence_page",Some((ep+1).to_string()))]))}else{None}}),
    )
}
