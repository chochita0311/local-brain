use super::{resources::json_value, support::*};
use crate::backend::{
    db,
    sources::registry::{
        decode, normalized_root, session_sources_path, session_sources_text, PythonText,
    },
    storage::{files, operation_lock},
    Config, Result,
};
use base64::{engine::general_purpose::STANDARD, Engine};
use rusqlite::Connection;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};
#[derive(Clone)]
pub struct FileRecovery {
    pub path: PathBuf,
    pub before: Vec<u8>,
    pub after: Vec<u8>,
}
pub fn restore(recovery: &FileRecovery) -> Result<()> {
    let actual = fs::read(&recovery.path)?;
    if actual == recovery.before {
        return Ok(());
    }
    if actual != recovery.after {
        return Err(fail(
            "이전 중 설정이 별도로 변경되었습니다. 현재 파일을 보존했습니다.",
        ));
    }
    files::atomic_write(&recovery.path, &recovery.before)
}
fn publish(
    path: PathBuf,
    before: Vec<u8>,
    after: Vec<u8>,
    recoveries: &mut Vec<FileRecovery>,
) -> Result<()> {
    if fs::read(&path)? != before {
        return Err(fail(
            "이전 중 설정 파일이 변경되었습니다. 현재 파일을 보존했습니다.",
        ));
    }
    let recovery = FileRecovery {
        path,
        before,
        after,
    };
    recoveries.push(recovery.clone());
    files::atomic_write(&recovery.path, &recovery.after)
}
pub fn upgrade_config(connection: &Connection, config: &Config) -> Result<Option<FileRecovery>> {
    let path = session_sources_path(config);
    if !path.exists() {
        return Ok(None);
    }
    let before = fs::read(&path)?;
    let raw = match std::str::from_utf8(&before)
        .ok()
        .and_then(|text| decode(text).ok())
    {
        Some(value) => value,
        None => return Ok(None),
    };
    if raw["schema_version"].as_i64() != Some(1) {
        return Ok(None);
    }
    let Some(array) = raw["session_sources"].as_array() else {
        return Err(fail(
            "기존 세션 소스 설정 형식을 확인해 주세요. 파일은 보존했습니다.",
        ));
    };
    if raw.as_object().is_none_or(|object| object.len() != 2) {
        return Err(fail(
            "기존 세션 소스 설정 형식을 확인해 주세요. 파일은 보존했습니다.",
        ));
    }
    let has_alias = has(connection, "sources", "kind")?;
    let rows = db::rows(connection, "SELECT * FROM sources ORDER BY id", [])?;
    let mut entries = Vec::new();
    let mut seen = BTreeSet::new();
    let mut roots: Vec<PathBuf> = Vec::new();
    for old in array {
        let Some(object) = old.as_object() else {
            return Err(fail(
                "기존 프로필 항목을 확인해 주세요. 파일은 보존했습니다.",
            ));
        };
        if ["source_key", "provider_kind", "display_label", "root"]
            .iter()
            .any(|key| !object.contains_key(*key))
            || object.keys().any(|key| {
                ![
                    "source_key",
                    "provider_kind",
                    "display_label",
                    "root",
                    "agent_home",
                    "enabled",
                ]
                .contains(&key.as_str())
            })
        {
            return Err(fail(
                "기존 프로필 항목을 확인해 주세요. 파일은 보존했습니다.",
            ));
        }
        let key = old["source_key"].as_str().unwrap_or("");
        let provider = old["provider_kind"].as_str().unwrap_or("");
        let label = old["display_label"].as_str().unwrap_or("");
        let root_value = old["root"].as_str().unwrap_or("");
        let valid_key = !key.is_empty()
            && key.len() <= 64
            && key.split('-').all(|part| {
                !part.is_empty()
                    && part
                        .bytes()
                        .all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit())
            });
        if !valid_key
            || !seen.insert(key.to_string())
            || !["codex", "claude"].contains(&provider)
            || label.py_trim().is_empty()
            || label.py_trim().chars().count() > 160
            || root_value.py_trim().is_empty()
            || root_value.py_trim().chars().count() > 4096
            || old.get("enabled").is_some_and(|value| !value.is_boolean())
            || old.get("agent_home").is_some_and(|value| {
                value
                    .as_str()
                    .is_none_or(|value| value.py_trim().is_empty() || value.chars().count() > 4096)
            })
        {
            return Err(fail(
                "기존 프로필 ID·도구·이름·경로를 확인해 주세요. 파일은 보존했습니다.",
            ));
        }
        let root = files::resolve(&normalized_root(&path, root_value, config)?)?;
        if old.get("enabled").and_then(Value::as_bool).unwrap_or(true) {
            if roots.iter().any(|other| files::overlap(&root, other)) {
                return Err(fail("기존 세션 소스 경로가 겹칩니다. 파일은 보존했습니다."));
            }
            roots.push(root.clone());
        }
        let matches = if has_alias {
            rows.iter()
                .filter(|row| row["kind"] == key)
                .collect::<Vec<_>>()
        } else {
            let mut matches = Vec::new();
            for row in &rows {
                if row["provider_kind"] == provider
                    && files::resolve(&files::expand(
                        Path::new(row["root_path"].as_str().unwrap_or("")),
                        config,
                    ))? == root
                {
                    matches.push(row);
                }
            }
            matches
        };
        if matches.len() > 1 {
            return Err(fail("기존 경로의 프로필을 하나로 확인할 수 없습니다."));
        }
        let (id, color) = if let Some(row) = matches.first() {
            if row.get("provider_kind").unwrap_or(&row["kind"]) != provider
                || files::resolve(&files::expand(
                    Path::new(row["root_path"].as_str().unwrap_or("")),
                    config,
                ))? != root
            {
                return Err(fail(
                    "기존 프로필의 도구·경로가 일치하지 않습니다. 파일은 보존했습니다.",
                ));
            }
            (
                row["id"].as_i64().unwrap(),
                row["profile_color"].as_str().map(str::to_owned),
            )
        } else {
            if has_alias {
                connection.execute(
                    "INSERT INTO sources(kind,provider_kind,name,root_path) VALUES (?,?,?,?)",
                    rusqlite::params![key, provider, label.py_trim(), root.to_string_lossy()],
                )?;
            } else {
                connection.execute(
                    "INSERT INTO sources(provider_kind,name,root_path) VALUES (?,?,?)",
                    rusqlite::params![provider, label.py_trim(), root.to_string_lossy()],
                )?;
            }
            (connection.last_insert_rowid(), None)
        };
        let mut entry = old.clone();
        entry.as_object_mut().unwrap().remove("source_key");
        entry["source_id"] = id.into();
        entry["color"] = color
            .unwrap_or_else(|| {
                if key == "codex-company" {
                    "blue"
                } else if provider == "claude" {
                    "orange"
                } else {
                    "green"
                }
                .into()
            })
            .into();
        entries.push(entry);
    }
    entries.sort_by_key(|entry| entry["source_id"].as_i64());
    let after = session_sources_text(&entries)?.into_bytes();
    if fs::read(&path)? != before {
        return Err(fail(
            "이전 중 설정 파일이 변경되었습니다. 현재 파일을 보존했습니다.",
        ));
    }
    let recovery = FileRecovery {
        path,
        before,
        after,
    };
    if let Err(error) = files::atomic_write(&recovery.path, &recovery.after) {
        restore(&recovery)?;
        return Err(error);
    }
    Ok(Some(recovery))
}
fn replace(connection: &Connection, table: &str, rows: &[Value]) -> Result<()> {
    let temporary = format!("{table}__pk_upgrade");
    if !columns(connection, &temporary)?.is_empty() {
        return Err(fail(
            "An unfinished source identity upgrade table already exists",
        ));
    }
    triggers_absent(
        connection,
        table,
        "Source identity upgrade found an unexpected trigger",
    )?;
    let indexes = objects(connection, "index", table)?;
    connection.execute_batch(&ddl(table)?.replacen(table, &temporary, 1))?;
    let target = column_set(connection, &temporary)?;
    let removed: BTreeSet<String> = match table {
        "sources" => BTreeSet::from(["kind".into(), "enabled".into()]),
        "skill_observations" => BTreeSet::from(["source_key".into()]),
        _ => BTreeSet::new(),
    };
    if column_set(connection, table)?
        .difference(&target)
        .any(|column| !removed.contains(column))
    {
        return Err(fail(
            "Source identity upgrade found unexpected columns; database preserved",
        ));
    }
    for row in rows {
        let retained = row
            .as_object()
            .ok_or_else(|| fail("Invalid row during source identity upgrade"))?
            .iter()
            .filter(|(key, _)| target.contains(*key))
            .collect::<Vec<_>>();
        let statement = format!(
            "INSERT INTO {} ({}) VALUES ({})",
            quote(&temporary),
            retained
                .iter()
                .map(|(key, _)| quote(key))
                .collect::<Vec<_>>()
                .join(","),
            vec!["?"; retained.len()].join(",")
        );
        connection.execute(
            &statement,
            rusqlite::params_from_iter(
                retained
                    .iter()
                    .map(|(_, value)| json_value(value))
                    .collect::<Result<Vec<_>>>()?,
            ),
        )?;
    }
    connection.execute_batch(&format!(
        "DROP TABLE {}; ALTER TABLE {} RENAME TO {}",
        quote(table),
        quote(&temporary),
        quote(table)
    ))?;
    for statement in indexes {
        connection.execute_batch(&if table == "skill_observations" {
            statement.replace("source_key", "source_id")
        } else {
            statement
        })?;
    }
    Ok(())
}
fn digest(parts: &[&str]) -> String {
    let mut hash = Sha256::new();
    for part in parts {
        hash.update((part.len() as u64).to_be_bytes());
        hash.update(part.as_bytes());
    }
    format!("{:x}", hash.finalize())
}
fn episode(source: &str, external: &str) -> String {
    format!("session:{}", digest(&[source, external]))
}
fn recover_reconnect(connection: &Connection, config: &Config) -> Result<()> {
    let journal = config.data_dir.join("source-reconnect.json");
    if !journal.exists() {
        return Ok(());
    }
    let value: Value = serde_json::from_slice(&fs::read(&journal)?)?;
    let path = session_sources_path(config);
    let current = fs::read(&path)?;
    let original = STANDARD
        .decode(value["before"].as_str().unwrap_or(""))
        .map_err(|_| fail("Invalid source reconnect journal"))?;
    if current != original
        && format!("{:x}", Sha256::digest(&current)) != value["after_sha256"].as_str().unwrap_or("")
    {
        return Err(fail(
            "중단된 소스 재연결 후 설정이 변경되었습니다. 파일과 복구 기록을 보존했습니다.",
        ));
    }
    let row = if let Some(id) = value["source_id"].as_i64() {
        db::row(connection, "SELECT root_path FROM sources WHERE id=?", [id])?
    } else {
        db::row(
            connection,
            "SELECT root_path FROM sources WHERE kind=?",
            [value["source_key"].as_str().unwrap_or("")],
        )?
    };
    if row.is_none_or(|row| row["root_path"] != value["new_root"]) {
        files::atomic_write(&path, &original)?;
    }
    fs::remove_file(journal)?;
    Ok(())
}
fn sync_health(
    config: &Config,
    aliases: &BTreeMap<String, i64>,
    recoveries: &mut Vec<FileRecovery>,
) -> Result<()> {
    for domain in ["session", "context"] {
        let path = config.data_dir.join(format!("{domain}-sync-state.json"));
        if !path.exists() {
            continue;
        }
        let before = fs::read(&path)?;
        let Ok(mut value) = serde_json::from_slice::<Value>(&before) else {
            continue;
        };
        let Some(rows) = value
            .get_mut("report")
            .and_then(|value| value.get_mut("sources"))
            .and_then(Value::as_array_mut)
        else {
            continue;
        };
        let mut changed = false;
        for row in rows {
            if let Some(object) = row.as_object_mut() {
                if let Some(key) = object.remove("source_key") {
                    let id = key.as_str().and_then(|key| aliases.get(key)).copied();
                    object.insert("source_id".into(), json!(id));
                    changed = true;
                }
            }
        }
        if changed {
            let after = serde_json::to_vec(&value)?;
            publish(path, before, after, recoveries)?;
        }
    }
    Ok(())
}
pub fn migrate(connection: &Connection, config: &Config) -> Result<bool> {
    if !has(connection, "sources", "kind")? {
        return Ok(false);
    }
    let file: String = connection.query_row(
        "SELECT file FROM pragma_database_list WHERE name='main'",
        [],
        |row| row.get(0),
    )?;
    let owns = !file.is_empty()
        && files::resolve(Path::new(&file))? == files::resolve(&config.database_path)?;
    let _lease = if owns {
        Some(operation_lock(config, "source-primary-key-upgrade")?)
    } else {
        None
    };
    if !has(connection, "sources", "kind")? {
        return Ok(false);
    }
    if !connection.is_autocommit() {
        connection.execute_batch("COMMIT")?;
    }
    if owns {
        recover_reconnect(connection, config)?;
    }
    let foreign: i64 = connection.query_row("PRAGMA foreign_keys", [], |row| row.get(0))?;
    connection.execute_batch("PRAGMA foreign_keys=OFF; BEGIN IMMEDIATE")?;
    let mut recoveries = Vec::new();
    let outcome = (|| {
        if !has(connection, "sources", "provider_kind")? {
            connection.execute_batch("ALTER TABLE sources ADD COLUMN provider_kind TEXT NOT NULL DEFAULT 'unknown'; UPDATE sources SET provider_kind=kind")?;
        }
        if owns {
            if let Some(recovery) = upgrade_config(connection, config)? {
                recoveries.push(recovery);
            }
        }
        let mut sources = db::rows(connection, "SELECT * FROM sources ORDER BY id", [])?;
        let aliases = sources
            .iter()
            .map(|row| {
                (
                    row["kind"].as_str().unwrap_or("").into(),
                    row["id"].as_i64().unwrap(),
                )
            })
            .collect::<BTreeMap<String, i64>>();
        if owns {
            sync_health(config, &aliases, &mut recoveries)?;
        }
        if has(connection, "skill_observations", "source_key")? {
            let mut skills = db::rows(connection, "SELECT * FROM skill_observations", [])?;
            for row in &mut skills {
                let key = row.as_object_mut().unwrap().remove("source_key").unwrap();
                row["source_id"] = (*aliases
                    .get(key.as_str().unwrap_or(""))
                    .ok_or_else(|| fail("Skill evidence refers to an unknown source"))?)
                .into();
            }
            replace(connection, "skill_observations", &skills)?;
        }
        if exists(connection, "session_chart_preferences")? {
            let mut preferences =
                db::rows(connection, "SELECT * FROM session_chart_preferences", [])?;
            for row in &mut preferences {
                let scope = row["source_scope"].as_str().unwrap_or("").to_string();
                if let Some(id) = aliases.get(&scope) {
                    if let Some(numeric) =
                        crate::backend::sources::profiles::decimal_integer(&scope)
                    {
                        if aliases.values().any(|id| *id == numeric) && *id != numeric {
                            return Err(fail("An old chart alias conflicts with a numeric source ID; preferences preserved"));
                        }
                    }
                    row["source_scope"] = id.to_string().into();
                }
            }
            replace(connection, "session_chart_preferences", &preferences)?;
        }
        if exists(connection, "workflow_assertions")? {
            let episodes=db::rows(connection,"SELECT sessions.source_id,sessions.external_id,sources.kind FROM sessions JOIN sources ON sources.id=sessions.source_id",[])?.iter().map(|row|(episode(row["kind"].as_str().unwrap_or(""),row["external_id"].as_str().unwrap_or("")),episode(&row["source_id"].to_string(),row["external_id"].as_str().unwrap_or("")))).collect::<BTreeMap<_,_>>();
            let mut assertions = db::rows(connection, "SELECT * FROM workflow_assertions", [])?;
            for row in &mut assertions {
                for key in ["source_episode_key", "target_episode_key"] {
                    if let Some(new) = row[key].as_str().and_then(|key| episodes.get(key)) {
                        row[key] = new.clone().into();
                    }
                }
                let mut parts = vec![
                    row["boundary_kind"].as_str().unwrap_or(""),
                    row["source_episode_key"].as_str().unwrap_or(""),
                ];
                if row["boundary_kind"] == "relation" {
                    parts.push(row["target_episode_key"].as_str().unwrap_or(""));
                }
                row["boundary_key"] = digest(&parts).into();
            }
            replace(connection, "workflow_assertions", &assertions)?;
        }
        if exists(connection, "personal_insight_runs")? {
            for row in db::rows(
                connection,
                "SELECT id,settings_json FROM personal_insight_runs",
                [],
            )? {
                let mut settings: Value =
                    serde_json::from_str(row["settings_json"].as_str().unwrap_or(""))?;
                if let Some(key) = settings
                    .as_object_mut()
                    .and_then(|object| object.remove("usage_source_key"))
                {
                    settings["usage_source_id"] = (*aliases
                        .get(key.as_str().unwrap_or(""))
                        .ok_or_else(|| fail("Analysis usage refers to an unknown source"))?)
                    .into();
                    connection.execute(
                        "UPDATE personal_insight_runs SET settings_json=? WHERE id=?",
                        rusqlite::params![serde_json::to_string(&settings)?, row["id"].as_str()],
                    )?;
                }
            }
        }
        if exists(connection, "search_index")? {
            for (entity, table) in [("session", "sessions"), ("document", "context_documents")] {
                connection.execute(&format!("UPDATE search_index SET source_kind=COALESCE((SELECT sources.provider_kind FROM {table} AS entity JOIN sources ON sources.id=entity.source_id WHERE CAST(entity.id AS TEXT)=search_index.entity_id),source_kind) WHERE entity_type=?"),[entity])?;
            }
        }
        for row in &mut sources {
            row.as_object_mut().unwrap().remove("kind");
        }
        replace(connection, "sources", &sources)?;
        foreign_check(connection, None)?;
        connection.execute_batch("COMMIT")?;
        Ok(())
    })();
    if outcome.is_err() {
        let _ = connection.execute_batch("ROLLBACK");
        let mut restoration = None;
        for recovery in recoveries.iter().rev() {
            if let Err(error) = restore(recovery) {
                restoration = Some(error);
            }
        }
        connection.execute_batch(&format!(
            "PRAGMA foreign_keys={}",
            if foreign != 0 { "ON" } else { "OFF" }
        ))?;
        if let Some(error) = restoration {
            return Err(error);
        }
        outcome?;
    }
    connection.execute_batch(&format!(
        "PRAGMA foreign_keys={}",
        if foreign != 0 { "ON" } else { "OFF" }
    ))?;
    Ok(true)
}
