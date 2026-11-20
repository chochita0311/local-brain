use super::digest;
use crate::backend::{clock, db, models, sources, storage::files, Config, Result};
use rusqlite::{Connection, OpenFlags};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::Path};
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Source {
    pub key: String,
    pub kind: String,
    pub entity_id: i64,
    pub title: String,
    pub path: String,
    pub source_kind: String,
    pub timestamp: String,
    pub blocks: Vec<Value>,
    pub source_id: Option<i64>,
}
impl Source {
    pub fn revision(&self) -> Result<String> {
        digest(&serde_json::to_value(self)?)
    }
    pub fn metadata(&self) -> Result<Value> {
        let mut result = serde_json::to_value(self)?;
        result.as_object_mut().unwrap().remove("blocks");
        Ok(result)
    }
}
pub fn private_derived(path: &str, config: &Config, model_cache: Option<&Path>) -> Result<bool> {
    let candidate = files::resolve(&files::expand(Path::new(path), config))?;
    for root in [
        &config.data_dir,
        &config.cache_dir,
        &config.development_dir,
        &config.hf_hub_cache,
    ]
    .into_iter()
    .map(|path| path.as_path())
    .chain(model_cache)
    {
        if candidate.starts_with(files::resolve(root)?) {
            return Ok(true);
        }
    }
    Ok(false)
}
pub fn read_sources(
    config: &Config,
    keys: Option<&BTreeSet<String>>,
) -> Result<(Vec<Source>, Value)> {
    let model_cache = models::embedding_cache_root(config)?;
    let registered = sources::registered_session_roots(config)?;
    let connection = Connection::open_with_flags(
        files::resolve(&config.database_path)?,
        OpenFlags::SQLITE_OPEN_READ_ONLY,
    )?;
    connection.busy_timeout(std::time::Duration::from_secs(30))?;
    connection.execute_batch("PRAGMA query_only=ON; BEGIN")?;
    let mut result = Vec::new();
    let (mut empty_sessions, mut empty_documents, mut excluded_runtime_documents) = (0, 0, 0);
    let sessions = db::rows(
        &connection,
        "SELECT s.*,o.provider_kind AS source_kind,o.root_path AS registered_root
         FROM sessions s JOIN sources o ON o.id=s.source_id
         WHERE s.session_class='work' AND s.session_role='primary' AND s.index_policy='full'
         ORDER BY s.id",
        [],
    )?;
    for row in sessions {
        let id = row["id"].as_i64().unwrap();
        let source_id = row["source_id"].as_i64().unwrap();
        if registered.get(&source_id).map(String::as_str) != row["registered_root"].as_str() {
            continue;
        }
        let key = format!("session:{id}");
        if keys.is_some_and(|keys| !keys.contains(&key)) {
            continue;
        }
        let blocks = db::rows(
            &connection,
            "SELECT id,role,text,sequence,source_line FROM activity_events
             WHERE session_id=? AND event_type='message' AND role IN ('user','assistant')
               AND length(text)>0 ORDER BY sequence,source_line,id",
            [id],
        )?;
        if blocks.is_empty() {
            empty_sessions += 1;
            continue;
        }
        let first = |keys: &[&str]| {
            keys.iter()
                .filter_map(|key| row[*key].as_str())
                .find(|value| !value.is_empty())
                .unwrap_or("")
                .to_string()
        };
        result.push(Source {
            key,
            kind: "session".into(),
            entity_id: id,
            title: row["title"].as_str().unwrap().into(),
            path: first(&["cwd_raw", "source_path"]),
            source_kind: row["source_kind"].as_str().unwrap().into(),
            timestamp: first(&["last_event_at", "ended_at", "started_at"]),
            blocks,
            source_id: Some(source_id),
        });
    }
    let documents = db::rows(
        &connection,
        "SELECT d.*,o.provider_kind AS source_kind FROM context_documents d
         JOIN context_roots r ON r.id=d.context_root_id JOIN sources o ON o.id=d.source_id
         WHERE r.enabled=1 AND r.readable=1 ORDER BY d.id",
        [],
    )?;
    for row in documents {
        let id = row["id"].as_i64().unwrap();
        let key = format!("document:{id}");
        if keys.is_some_and(|keys| !keys.contains(&key)) {
            continue;
        }
        let path = row["path"].as_str().unwrap();
        if private_derived(path, config, Some(&model_cache))? {
            excluded_runtime_documents += 1;
            continue;
        }
        let body = row["body"].as_str().unwrap();
        if body.is_empty() {
            empty_documents += 1;
            continue;
        }
        // Python datetime.fromtimestamp rounds the fractional second separately.
        // Multiplying the whole epoch float changes some microsecond boundaries.
        let seconds = row["mtime_ns"].as_i64().unwrap() as f64 / 1e9;
        let micros = seconds.trunc() as i64 * 1_000_000
            + ((seconds - seconds.trunc()) * 1e6).round_ties_even() as i64;
        let stamp = chrono::DateTime::from_timestamp_micros(micros)
            .ok_or_else(|| super::failure("INVALID_SOURCE_TIMESTAMP"))?;
        result.push(Source {
            key,kind:"document".into(),entity_id:id,title:row["title"].as_str().unwrap().into(),
            path:path.into(),source_kind:row["source_kind"].as_str().unwrap().into(),
            timestamp:clock::isoformat(stamp),source_id:row["source_id"].as_i64(),
            blocks:vec![json!({"id":id.to_string(),"role":"document","text":body,"sequence":0,"source_line":1})],
        });
    }
    let unreadable: i64 = connection.query_row(
        "SELECT count(*) FROM context_roots WHERE enabled=1 AND readable=0",
        [],
        |row| row.get(0),
    )?;
    let excluded:i64=connection.query_row("SELECT count(*) FROM sessions WHERE session_class!='work' OR session_role!='primary' OR index_policy!='full'",[],|row|row.get(0))?;
    let coverage = json!({"eligible_parents":result.len(),"excluded_sessions":excluded,"unreadable_context_roots":unreadable,"empty_sessions":empty_sessions,"empty_documents":empty_documents,"excluded_runtime_documents":excluded_runtime_documents});
    Ok((result, coverage))
}
