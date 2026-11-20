use super::{profiles::*, registry::*};
use crate::backend::{
    db,
    storage::{files, migrations::identity, operation_lock},
    BackendError, Config, Result,
};
use base64::{engine::general_purpose::STANDARD, Engine};
use rusqlite::Connection;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
};
fn error(message: &str) -> BackendError {
    BackendError::conflict(message)
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn configuration(config: &Config) -> Result<(String, String, SettingsResult)> {
    let parsed = load_session_source_settings(config)?;
    if parsed.file_error {
        return Err(error(
            "세션 소스 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요.",
        ));
    }
    let bytes = fs::read(&parsed.settings_path)?;
    let revision = digest(&bytes);
    let text = String::from_utf8(bytes)
        .map_err(|_| error("세션 소스 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요."))?;
    Ok((text, revision, parsed))
}
fn valid(registry: &RegistryResult, message: &str) -> Result<()> {
    if registry
        .diagnostics
        .iter()
        .any(|item| item.code != "config_missing")
    {
        Err(error(message))
    } else {
        Ok(())
    }
}
fn rollback_file(path: &Path, before: &[u8], attempted: Option<&[u8]>) -> Result<()> {
    let actual = fs::read(path)?;
    if actual == before {
        return Ok(());
    }
    if attempted.is_none_or(|attempted| attempted != actual) {
        return Err(error(
            "저장 중 설정 파일이 변경되었습니다. 현재 파일을 보존했습니다.",
        ));
    }
    files::atomic_write(path, before)
}
pub fn migrate_source_settings(config: &Config) -> Result<()> {
    let path = session_sources_path(config);
    let Ok(text) = fs::read_to_string(&path) else {
        return Ok(());
    };
    let Ok(raw) = decode(&text) else {
        return Ok(());
    };
    if raw["schema_version"].as_i64() != Some(1) {
        return Ok(());
    }
    let _lock = operation_lock(config, "source-migration")?;
    let connection = db::connect(config)?;
    connection.execute_batch("BEGIN")?;
    let mut recovery = None;
    let outcome = (|| {
        recovery = identity::upgrade_config(&connection, config)?;
        let registry = load_and_reconcile_session_sources(&connection, config)?;
        valid(
            &registry,
            "기존 프로필 설정을 확인해 주세요. 파일은 보존했습니다.",
        )?;
        connection.execute_batch("COMMIT")?;
        Ok(())
    })();
    if outcome.is_err() {
        let _ = connection.execute_batch("ROLLBACK");
        if let Some(recovery) = recovery {
            identity::restore(&recovery)?;
        }
    }
    outcome
}
pub fn source_inventory(config: &Config) -> Result<Value> {
    migrate_source_settings(config)?;
    let (mut text, mut revision, mut parsed) = configuration(config)?;
    if parsed.schema_version != 2 && parsed.diagnostics.is_empty() {
        return Err(error(
            "기존 프로필 ID·도구·세션 경로가 일치하는지 확인해 주세요. 설정 파일은 보존했습니다.",
        ));
    }
    let connection = db::connect(config)?;
    let query="SELECT * FROM sources WHERE provider_kind IN ('claude','codex') ORDER BY profile_position,id";
    let mut rows = db::rows(&connection, query, [])?;
    let configured: BTreeSet<i64> = parsed.entries.iter().map(|entry| entry.source_id).collect();
    let changed = parsed.schema_version == 2
        && parsed.diagnostics.is_empty()
        && (parsed.entries.iter().enumerate().any(|(position, entry)| {
            rows.iter()
                .find(|row| row["id"].as_i64() == Some(entry.source_id))
                .is_none_or(|row| {
                    row["name"] != entry.display_label
                        || row["provider_kind"] != entry.provider_kind
                        || row["root_path"] != entry.root.to_string_lossy().as_ref()
                        || row["profile_color"]
                            != entry
                                .color
                                .as_deref()
                                .unwrap_or_else(|| default_color(&entry.provider_kind))
                        || row["profile_position"].as_u64() != Some(position as u64)
                })
        }) || rows.iter().any(|row| {
            !configured.contains(&row["id"].as_i64().unwrap())
                && row["profile_position"].as_i64() != Some(2147483647)
        }));
    if changed {
        let _lock = operation_lock(config, "source-settings")?;
        connection.execute_batch("BEGIN")?;
        let outcome: Result<()> = (|| {
            (text, revision, parsed) = configuration(config)?;
            let registry = load_and_reconcile_session_sources(&connection, config)?;
            valid(
                &registry,
                "프로필 설정을 적용하지 못했습니다. ID·도구·세션 경로를 확인해 주세요.",
            )?;
            rows = db::rows(&connection, query, [])?;
            connection.execute_batch("COMMIT")?;
            Ok(())
        })();
        if outcome.is_err() {
            let _ = connection.execute_batch("ROLLBACK");
        }
        outcome?;
    }
    let raw = decode_for_validation(&text)
        .map_err(|_| error("세션 소스 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요."))?;
    let entries = raw["session_sources"]
        .as_array()
        .ok_or_else(|| error("세션 소스 설정을 읽지 못했습니다. 기존 파일을 확인해 주세요."))?;
    for row in &mut rows {
        let id = row["id"].as_i64().unwrap();
        let entry = entries
            .iter()
            .find(|entry| entry["source_id"].as_i64() == Some(id));
        let status = parsed
            .entries
            .iter()
            .find(|entry| entry.source_id == id)
            .map(|entry| entry.availability.as_str())
            .unwrap_or("config_missing");
        let color = row["profile_color"]
            .as_str()
            .unwrap_or_else(|| default_color(row["provider_kind"].as_str().unwrap_or("")))
            .to_string();
        let object = row.as_object_mut().unwrap();
        object.insert("configured".into(), entry.is_some().into());
        object.insert(
            "registered".into(),
            entry
                .is_some_and(|entry| {
                    entry
                        .get("enabled")
                        .and_then(Value::as_bool)
                        .unwrap_or(true)
                })
                .into(),
        );
        object.insert(
            "agent_home".into(),
            entry
                .and_then(|entry| entry.get("agent_home"))
                .cloned()
                .unwrap_or("".into()),
        );
        object.insert("availability".into(), status.into());
        object.insert("color".into(), color.into());
        object.remove("profile_color");
        object.remove("profile_position");
    }
    Ok(
        json!({"revision":revision,"sources":rows,"palette":palette()?,"diagnostics":parsed.diagnostics.iter().map(|item|json!({"code":item.code,"message":item.message,"source_id":item.source_id})).collect::<Vec<_>>()}),
    )
}
pub fn candidates(config: &Config) -> Result<Value> {
    Ok(json!([("codex","Codex",".codex","sessions"),("claude","Claude Code",".claude","projects")].into_iter().filter_map(|(provider,label,folder,suffix)|{let home=config.home_dir.join(folder);home.is_dir().then(||json!({"provider_kind":provider,"display_label":label,"agent_home":home,"root":home.join(suffix)}))}).collect::<Vec<_>>()))
}
fn configured_root(entry: &Value, config: &Config) -> Result<std::path::PathBuf> {
    normalized_root(
        &session_sources_path(config),
        entry["root"].as_str().unwrap_or(""),
        config,
    )
}
pub fn update_source(config: &Config, payload: &Value) -> Result<Value> {
    let _lock = operation_lock(config, "source-settings")?;
    migrate_source_settings(config)?;
    let (text, revision, parsed) = configuration(config)?;
    if payload["revision"] != revision {
        return Err(error(
            "소스 설정이 변경되었습니다. 목록을 다시 불러온 뒤 저장해 주세요.",
        ));
    }
    let invalid_profiles =
        || error("기존 소스 설정의 오류를 먼저 해결해 주세요. 파일은 보존했습니다.");
    if !parsed.diagnostics.is_empty() || parsed.schema_version != 2 {
        return Err(invalid_profiles());
    }
    let raw = decode(&text).map_err(|_| invalid_profiles())?;
    let mut entries = raw["session_sources"]
        .as_array()
        .cloned()
        .ok_or_else(invalid_profiles)?;
    let mut source_id = payload["source_id"].as_i64();
    if payload.get("source_key").is_some() {
        return Err(error(
            "프로필 ID 형식이 변경되었습니다. 설정을 다시 열어 주세요.",
        ));
    }
    if payload
        .get("source_id")
        .is_some_and(|value| !value.is_null() && !valid_source_id(value))
    {
        return Err(error("프로필 ID를 확인해 주세요."));
    }
    let mut current = entries
        .iter()
        .find(|entry| entry["source_id"].as_i64() == source_id)
        .cloned();
    if let Some(current) = &mut current {
        current["root"] = configured_root(current, config)?
            .to_string_lossy()
            .into_owned()
            .into();
    }
    let action = payload
        .get("action")
        .and_then(Value::as_str)
        .unwrap_or("save");
    if payload
        .get("action")
        .is_some_and(|value| !value.is_string())
        || !["save", "remove", "reconnect", "color", "reorder"].contains(&action)
    {
        return Err(error("지원하지 않는 소스 작업입니다."));
    }
    let connection = db::connect(config)?;
    if source_id.is_some() && current.is_none() {
        let retained = db::row(
            &connection,
            "SELECT * FROM sources WHERE id=?",
            [source_id.unwrap()],
        )?;
        let retained = retained
            .filter(|row| [Some("codex"), Some("claude")].contains(&row["provider_kind"].as_str()))
            .ok_or_else(|| error("등록된 소스를 찾지 못했습니다."))?;
        if !["save", "reconnect"].contains(&action) {
            return Err(error("프로필을 다시 등록한 뒤 변경해 주세요."));
        }
        let restored = json!({"source_id":source_id,"display_label":retained["name"],"provider_kind":retained["provider_kind"],"root":retained["root_path"],"color":retained["profile_color"].as_str().unwrap_or_else(||default_color(retained["provider_kind"].as_str().unwrap_or(""))),"enabled":false});
        entries.push(restored.clone());
        current = Some(restored);
    }
    let mut replacement = None;
    match action {
        "reorder" => {
            let order = payload["source_ids"].as_array().ok_or_else(|| {
                error("프로필 순서가 현재 목록과 다릅니다. 목록을 다시 불러와 주세요.")
            })?;
            let expected = entries
                .iter()
                .filter_map(|entry| entry["source_id"].as_i64())
                .collect::<BTreeSet<_>>();
            let actual = order
                .iter()
                .filter_map(Value::as_i64)
                .collect::<BTreeSet<_>>();
            if order.iter().any(|id| !valid_source_id(id))
                || order.len() != entries.len()
                || actual.len() != order.len()
                || actual != expected
            {
                return Err(error(
                    "프로필 순서가 현재 목록과 다릅니다. 목록을 다시 불러와 주세요.",
                ));
            }
            let by_id = entries
                .into_iter()
                .map(|entry| (entry["source_id"].as_i64().unwrap(), entry))
                .collect::<BTreeMap<_, _>>();
            entries = order
                .iter()
                .map(|id| by_id[&id.as_i64().unwrap()].clone())
                .collect();
        }
        "remove" => {
            let mut value = current
                .clone()
                .ok_or_else(|| error("해제할 소스를 선택해 주세요."))?;
            value["enabled"] = false.into();
            replacement = Some(value);
        }
        "color" => {
            let color = payload["color"]
                .as_str()
                .filter(|value| valid_color(value))
                .ok_or_else(|| error("프로필과 색상을 확인해 주세요."))?;
            let mut value = current
                .clone()
                .ok_or_else(|| error("프로필과 색상을 확인해 주세요."))?;
            value["color"] = color.into();
            replacement = Some(value);
        }
        _ => {
            let provider = payload["provider_kind"]
                .as_str()
                .filter(|value| ["codex", "claude"].contains(value))
                .ok_or_else(|| {
                    error("소스 도구 종류를 확인해 주세요. 기존 소스의 종류는 바꿀 수 없습니다.")
                })?;
            if current
                .as_ref()
                .is_some_and(|entry| entry["provider_kind"] != provider)
            {
                return Err(error(
                    "소스 도구 종류를 확인해 주세요. 기존 소스의 종류는 바꿀 수 없습니다.",
                ));
            }
            let label = payload["display_label"]
                .as_str()
                .filter(|value| {
                    !value.py_trim().is_empty() && value.py_trim().chars().count() <= 160
                })
                .ok_or_else(|| error("표시 이름은 1~160자로 입력해 주세요."))?;
            let home = match payload.get("agent_home") {
                None => "",
                Some(value) => value
                    .as_str()
                    .ok_or_else(|| error("Home 경로를 확인해 주세요."))?,
            };
            if home.chars().count() > 4096 {
                return Err(error("Home 경로를 확인해 주세요."));
            }
            let root = payload["root"]
                .as_str()
                .filter(|value| !value.py_trim().is_empty() && value.chars().count() <= 4096)
                .ok_or_else(|| error("실제로 읽을 세션 경로를 입력해 주세요."))?;
            let root = files::expand(Path::new(root.py_trim()), config);
            if !root.is_absolute() {
                return Err(error("세션 위치는 절대 경로로 입력해 주세요."));
            }
            let root = files::resolve(&root)?;
            if current.is_none() && !readable_directory(&root) {
                return Err(error("읽을 수 있는 세션 폴더를 선택해 주세요."));
            }
            for entry in &entries {
                if current
                    .as_ref()
                    .is_some_and(|current| entry["source_id"] == current["source_id"])
                {
                    continue;
                }
                let other = files::resolve(&configured_root(entry, config)?)?;
                if entry.get("enabled").and_then(Value::as_bool) == Some(false) {
                    if root == other {
                        return Err(error("등록을 해제한 같은 경로가 있습니다. 해당 소스의 ‘다시 등록’을 사용해 주세요."));
                    }
                    continue;
                }
                if files::overlap(&root, &other) {
                    return Err(error(
                        "다른 세션 소스와 경로가 겹칩니다. 하나의 소스로 등록해 주세요.",
                    ));
                }
            }
            let default = current
                .as_ref()
                .and_then(|entry| entry["color"].as_str())
                .unwrap_or_else(|| default_color(provider));
            let color = payload
                .get("color")
                .map_or(Some(default), Value::as_str)
                .filter(|value| valid_color(value))
                .ok_or_else(|| error("지원하는 프로필 색상을 선택해 주세요."))?;
            let stored = if let Some(current) = &current {
                if root == files::resolve(&configured_root(current, config)?)? {
                    current["root"].as_str().unwrap_or("").to_string()
                } else {
                    root.to_string_lossy().into_owned()
                }
            } else {
                root.to_string_lossy().into_owned()
            };
            let mut value = json!({"source_id":source_id,"display_label":label.py_trim(),"provider_kind":provider,"root":stored,"enabled":true,"color":color});
            if !home.py_trim().is_empty() {
                let home = files::expand(Path::new(home.py_trim()), config);
                if !home.is_absolute() {
                    return Err(error("Home은 절대 경로로 입력해 주세요."));
                }
                value["agent_home"] = files::resolve(&home)?.to_string_lossy().into_owned().into();
            }
            replacement = Some(value);
        }
    }
    let path = session_sources_path(config);
    let original = fs::read(&path)?;
    let mut attempted: Option<Vec<u8>> = None;
    let journal = config.data_dir.join("source-reconnect.json");
    let changed_root = if let (Some(current), Some(replacement)) = (&current, &replacement) {
        files::resolve(&configured_root(current, config)?)?
            != files::resolve(&configured_root(replacement, config)?)?
    } else {
        false
    };
    connection.execute_batch("BEGIN")?;
    let outcome = (|| {
        let registry = load_and_reconcile_session_sources(&connection, config)?;
        valid(
            &registry,
            "기존 프로필 설정을 확인해 주세요. 파일은 보존했습니다.",
        )?;
        if let Some(replacement) = &mut replacement {
            match &current {
                None => {
                    let id: i64 = connection.query_row(
                        "SELECT COALESCE(MAX(id),0)+1 FROM sources",
                        [],
                        |row| row.get(0),
                    )?;
                    if !valid_source_id(&json!(id)) {
                        return Err(error(
                            "새 프로필 ID를 만들지 못했습니다. 기존 등록은 보존했습니다.",
                        ));
                    }
                    source_id = Some(id);
                    connection.execute(
                        "INSERT INTO sources(id,provider_kind,name,root_path) VALUES (?,?,?,?)",
                        rusqlite::params![
                            id,
                            replacement["provider_kind"].as_str(),
                            replacement["display_label"].as_str(),
                            replacement["root"].as_str()
                        ],
                    )?;
                    replacement["source_id"] = id.into();
                    entries.push(replacement.clone());
                }
                Some(current) => {
                    for entry in &mut entries {
                        if entry["source_id"] == current["source_id"] {
                            *entry = replacement.clone();
                        }
                    }
                }
            }
        }
        let updated = session_sources_text(&entries)?.into_bytes();
        if changed_root {
            if action != "reconnect" || payload["confirm_same_source"] != true {
                return Err(error("경로 변경은 ‘같은 소스 재연결’로 확인해 주세요."));
            }
            files::atomic_write(
                &journal,
                &serde_json::to_vec(
                    &json!({"source_id":source_id,"old_root":current.as_ref().unwrap()["root"],"new_root":replacement.as_ref().unwrap()["root"],"before":STANDARD.encode(&original),"after_sha256":digest(&updated)}),
                )?,
            )?;
            reconnect(
                &connection,
                current.as_ref().unwrap(),
                replacement.as_ref().unwrap(),
                config,
            )?;
        }
        if fs::read(&path)? != original {
            return Err(error(
                "저장 중 설정이 변경되었습니다. 현재 파일을 보존했습니다.",
            ));
        }
        attempted = Some(updated);
        files::atomic_write(&path, attempted.as_ref().unwrap())?;
        let registry = load_and_reconcile_session_sources(&connection, config)?;
        valid(
            &registry,
            "소스 설정을 적용하지 못했습니다. 기존 등록을 보존했습니다.",
        )?;
        connection.execute_batch("COMMIT")?;
        Ok(())
    })();
    if let Err(failure) = outcome {
        let _ = connection.execute_batch("ROLLBACK");
        rollback_file(&path, &original, attempted.as_deref())?;
        if journal.exists() {
            fs::remove_file(&journal)?;
        }
        return Err(failure);
    }
    if journal.exists() {
        fs::remove_file(journal)?;
    }
    source_inventory(config)
}
fn reconnect(
    connection: &Connection,
    before: &Value,
    after: &Value,
    config: &Config,
) -> Result<()> {
    let old = files::resolve(&configured_root(before, config)?)?;
    let new = configured_root(after, config)?;
    if !readable_directory(&new) {
        return Err(error("재연결할 폴더를 읽을 수 없습니다."));
    }
    let source_id = before["source_id"]
        .as_i64()
        .ok_or_else(|| error("프로필 ID를 확인해 주세요."))?;
    if db::row(connection, "SELECT id FROM sources WHERE id=?", [source_id])?.is_none() {
        return Ok(());
    }
    let provider = before["provider_kind"].as_str().unwrap_or("");
    let revision = if provider == "codex" {
        crate::backend::ingest::CODEX_SESSION_REVISION
    } else {
        crate::backend::ingest::CLAUDE_SESSION_REVISION
    };
    for row in db::rows(connection,"SELECT DISTINCT session_contract_version,typeof(session_contract_version) AS storage_type FROM source_files WHERE source_id=? AND session_contract_version IS NOT NULL",[source_id])?{let stored=row["session_contract_version"].as_i64().filter(|value|*value>0).ok_or_else(||error("This source has an unsupported Session revision."))?;if row["storage_type"]!="integer"{return Err(error("This source has an unsupported Session revision."));}
if stored>revision{return Err(error(&format!("This source was processed by a newer Session parser ({stored} > {revision}). Update LocalBrain before synchronizing it.")));}}
    let mut rewrites = Vec::new();
    for row in db::rows(
        connection,
        "SELECT id,source_path,external_id FROM sessions WHERE source_id=?",
        [source_id],
    )? {
        let path = Path::new(row["source_path"].as_str().unwrap_or(""));
        let relative = path
            .strip_prefix(&old)
            .map_err(|_| error("기존 세션 경로가 등록된 폴더와 일치하지 않습니다."))?;
        let target = new.join(relative);
        if !target.is_file() {
            return Err(error(
                "기존 세션 파일이 새 위치에 모두 있는지 확인해 주세요. 기존 기록은 유지됩니다.",
            ));
        }
        let parsed = crate::backend::ingest::parse_session(provider, &target)
            .map_err(|_| {
                error("새 위치의 세션 동일성을 확인하지 못했습니다. 기존 등록을 보존했습니다.")
            })?
            .ok_or_else(|| {
                error("새 위치의 세션 동일성을 확인하지 못했습니다. 기존 등록을 보존했습니다.")
            })?;
        if parsed.external_id != row["external_id"].as_str().unwrap_or("") {
            return Err(error("새 위치의 세션 ID가 기존 소스와 다릅니다."));
        }
        rewrites.push((target, row["id"].as_i64().unwrap()));
    }
    for (target, id) in rewrites {
        connection.execute(
            "UPDATE sessions SET source_path=? WHERE id=?",
            rusqlite::params![target.to_string_lossy(), id],
        )?;
    }
    for row in db::rows(
        connection,
        "SELECT id,path FROM source_files WHERE source_id=?",
        [source_id],
    )? {
        if let Ok(relative) = Path::new(row["path"].as_str().unwrap_or("")).strip_prefix(&old) {
            connection.execute(
                "UPDATE source_files SET path=?,session_contract_version=NULL WHERE id=?",
                rusqlite::params![new.join(relative).to_string_lossy(), row["id"].as_i64()],
            )?;
        }
    }
    connection.execute(
        "UPDATE sources SET root_path=? WHERE id=?",
        rusqlite::params![new.to_string_lossy(), source_id],
    )?;
    Ok(())
}
pub fn recover_source_reconnect(config: &Config) -> Result<()> {
    let journal = config.data_dir.join("source-reconnect.json");
    if !journal.exists() {
        return Ok(());
    }
    let _lock = operation_lock(config, "source-recovery")?;
    let value: Value = serde_json::from_slice(&fs::read(&journal)?)?;
    let path = session_sources_path(config);
    let current = fs::read(&path)?;
    let original = STANDARD
        .decode(value["before"].as_str().unwrap_or(""))
        .map_err(|_| error("Invalid source reconnect journal"))?;
    if current != original && digest(&current) != value["after_sha256"].as_str().unwrap_or("") {
        return Err(error("중단된 소스 재연결 후 설정이 변경되었습니다. 기존 파일과 source-reconnect.json을 보존했습니다."));
    }
    let connection = db::connect(config)?;
    let row = db::row(
        &connection,
        "SELECT root_path FROM sources WHERE id=?",
        [value["source_id"].as_i64()],
    )?;
    if row.is_none_or(|row| row["root_path"] != value["new_root"]) {
        files::atomic_write(&path, &original)?;
    }
    fs::remove_file(journal)?;
    Ok(())
}
