use super::{
    digest, failure,
    model::{Encoder, ExecutionOptions},
    molecules::{for_each_molecule, Profile},
    source::{read_sources, Source},
};
use crate::backend::{
    db,
    storage::{files, operation_lock},
    Config, Result,
};
use localbrain_models::{
    embedding::{DevicePreference, MAX_BATCH_SIZE, NATIVE_EMBEDDING_RUNTIME},
    Cancellation,
};
use rusqlite::{params, Connection, OpenFlags, OptionalExtension};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, File, OpenOptions},
    io::Write,
    os::unix::fs::{MetadataExt, OpenOptionsExt},
    path::{Path, PathBuf},
    sync::atomic::Ordering,
    time::{Instant, SystemTime, UNIX_EPOCH},
};
use unicode_normalization::UnicodeNormalization;
pub const OWNER: &str = "localbrain.natural-search.v1";
pub const SCHEMA:&str="CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS parents(key TEXT PRIMARY KEY,revision TEXT NOT NULL,metadata TEXT NOT NULL); CREATE TABLE IF NOT EXISTS vectors(input_hash TEXT PRIMARY KEY,value BLOB NOT NULL); CREATE TABLE IF NOT EXISTS fragments(id INTEGER PRIMARY KEY,parent_key TEXT NOT NULL,ordinal INTEGER NOT NULL,input_hash TEXT NOT NULL,body_hash TEXT NOT NULL,text TEXT NOT NULL,context TEXT NOT NULL,locator TEXT NOT NULL,UNIQUE(parent_key,ordinal)); CREATE INDEX IF NOT EXISTS fragments_parent ON fragments(parent_key); CREATE VIRTUAL TABLE IF NOT EXISTS terms USING fts5(tokens,tokenize='unicode61');";
pub fn folder(config: &Config) -> PathBuf {
    config.cache_dir.join("natural-search")
}
pub(super) type FileStamp = (u64, u64, i64, i64);

pub(super) fn file_stamp(path: &Path) -> Option<FileStamp> {
    fs::metadata(path)
        .ok()
        .map(|info| (info.ino(), info.len(), info.mtime(), info.mtime_nsec()))
}

pub(super) fn published_stamp(config: &Config) -> Option<FileStamp> {
    file_stamp(&folder(config).join("index.sqlite3"))
}

/// A publication between encoder selection and opening the reader can look
/// incompatible. Retry against the new file without blocking the writer.
pub fn read_published<T>(config: &Config, mut read: impl FnMut() -> Result<T>) -> Result<T> {
    let mut stamp = published_stamp(config);
    for _ in 0..2 {
        let result = read();
        if !result.as_ref().is_err_and(|error| {
            ["SEARCH_INDEX_INCOMPATIBLE", "INVALID_SEARCH_VECTORS"].contains(&error.code.as_str())
        }) {
            return result;
        }
        let current = published_stamp(config);
        if stamp == current {
            return result;
        }
        stamp = current;
    }
    Err(failure("SEARCH_BUSY"))
}

pub(super) fn database_binding(config: &Config) -> Result<String> {
    digest(&json!(
        files::resolve(&config.database_path)?.to_string_lossy()
    ))
}
fn sorted(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut keys = object.keys().collect::<Vec<_>>();
            keys.sort();
            Value::Object(
                keys.into_iter()
                    .map(|key| (key.clone(), sorted(&object[key])))
                    .collect(),
            )
        }
        Value::Array(array) => Value::Array(array.iter().map(sorted).collect()),
        _ => value.clone(),
    }
}
pub fn read_json(path: &Path) -> Result<Value> {
    let info = files::owned_file(path)?;
    if info.mode() & 0o077 != 0 {
        return Err(failure("UNOWNED_OUTPUT"));
    }
    Ok(serde_json::from_slice(&fs::read(path)?)?)
}
pub fn atomic_json(path: &Path, value: &Value) -> Result<()> {
    let pending = PathBuf::from(format!("{}.pending", path.display()));
    if fs::symlink_metadata(&pending).is_ok() {
        return Err(failure("UNOWNED_OUTPUT"));
    }
    if fs::symlink_metadata(path).is_ok() {
        let info = files::owned_file(path)?;
        if info.mode() & 0o077 != 0 {
            return Err(failure("UNOWNED_OUTPUT"));
        }
    }
    let mut stream = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(&pending)?;
    let initial = stream.metadata()?;
    let outcome = (|| {
        let compact = serde_json::to_string(&sorted(value))?;
        let mut spaced = String::new();
        let (mut string, mut escape) = (false, false);
        for ch in compact.chars() {
            spaced.push(ch);
            if string {
                if escape {
                    escape = false
                } else if ch == '\\' {
                    escape = true
                } else if ch == '"' {
                    string = false
                }
            } else if ch == '"' {
                string = true
            } else if [',', ':'].contains(&ch) {
                spaced.push(' ');
            }
        }
        stream.write_all(spaced.as_bytes())?;
        stream.sync_all()?;
        let current = fs::symlink_metadata(&pending)?;
        if current.dev() != initial.dev()
            || current.ino() != initial.ino()
            || !current.is_file()
            || current.nlink() != 1
        {
            return Err(failure("UNOWNED_OUTPUT"));
        }
        fs::rename(&pending, path)?;
        Ok(())
    })();
    drop(stream);
    if let Ok(info) = fs::symlink_metadata(&pending) {
        if info.dev() == initial.dev()
            && info.ino() == initial.ino()
            && !info.file_type().is_symlink()
        {
            let _ = fs::remove_file(pending);
        }
    }
    outcome
}
pub fn read_settings(config: &Config) -> Result<(Value, Profile)> {
    let path = config.data_dir.join("natural-search.json");
    if !path.exists() {
        let profile = Profile::default();
        return Ok((
            json!({"version":1,"enabled":false,"profile":profile}),
            profile,
        ));
    }
    let value = read_json(&path)?;
    if value["version"].as_i64() != Some(1) || !value["enabled"].is_boolean() {
        return Err(failure("INVALID_SEARCH_SETTINGS"));
    }
    let profile = serde_json::from_value::<Profile>(value["profile"].clone())
        .map_err(|_| failure("INVALID_SEARCH_SETTINGS"))?;
    profile
        .validate()
        .map_err(|_| failure("INVALID_SEARCH_SETTINGS"))?;
    Ok((value, profile))
}
pub fn search_settings(config: &Config) -> Result<Value> {
    let (value, profile) = read_settings(config)?;
    Ok(
        json!({"cutoff":profile.cutoff,"default_cutoff":Profile::default().cutoff,"revision":digest(&value)?,"error":null}),
    )
}
pub fn update_cutoff(config: &Config, cutoff: &Value, revision: &Value) -> Result<Value> {
    let cutoff = cutoff
        .as_f64()
        .filter(|value| value.is_finite() && (0.0..=1.0).contains(value))
        .ok_or_else(|| failure("INVALID_SEARCH_CUTOFF"))?;
    let _lock = operation_lock(config, "search-settings")?;
    let (mut value, _) = read_settings(config)?;
    if revision.as_str() != Some(digest(&value)?.as_str()) {
        return Err(failure("SEARCH_SETTINGS_CHANGED"));
    }
    value["profile"]["cutoff"] = cutoff.into();
    atomic_json(&config.data_dir.join("natural-search.json"), &value)?;
    search_settings(config)
}
pub fn save_settings(config: &Config, profile: Profile, enabled: bool) -> Result<()> {
    profile.validate()?;
    let _lock = operation_lock(config, "search-settings")?;
    files::private_directory(&config.data_dir, config)?;
    atomic_json(
        &config.data_dir.join("natural-search.json"),
        &json!({"version":1,"enabled":enabled,"profile":profile}),
    )
}
pub fn lexical_tokens(text: &str) -> Vec<String> {
    let normalized = crate::backend::unicode::lowercase(&text.nfkc().collect::<String>());
    let words = regex::Regex::new(r"[가-힣]+|[a-z0-9_./:+-]+").unwrap();
    let split = regex::Regex::new(r"[_./:+-]+").unwrap();
    let mut output = Vec::new();
    for found in words.find_iter(&normalized) {
        let word = found.as_str();
        if word.chars().all(|ch| ('가'..='힣').contains(&ch)) {
            let chars = word.chars().collect::<Vec<_>>();
            for index in 0..chars.len().saturating_sub(1).max(1) {
                output.push(chars[index..(index + 2).min(chars.len())].iter().collect());
            }
            if chars.len() > 2 {
                output.push(word.into());
            }
        } else {
            output.push(word.into());
            output.extend(
                split
                    .split(word)
                    .filter(|part| !part.is_empty() && *part != word)
                    .map(str::to_owned),
            );
        }
    }
    output
}
pub fn meta(connection: &Connection) -> Result<Value> {
    let mut result = serde_json::Map::new();
    for row in db::rows(connection, "SELECT key,value FROM meta", [])? {
        result.insert(
            row["key"]
                .as_str()
                .ok_or_else(|| failure("INVALID_SEARCH_INDEX"))?
                .into(),
            serde_json::from_str(
                row["value"]
                    .as_str()
                    .ok_or_else(|| failure("INVALID_SEARCH_INDEX"))?,
            )?,
        );
    }
    Ok(result.into())
}
fn set_meta(connection: &Connection, value: &Value) -> Result<()> {
    for (key, value) in value.as_object().unwrap() {
        connection.execute(
            "INSERT OR REPLACE INTO meta VALUES (?,?)",
            [
                key.as_str(),
                serde_json::to_string(&sorted(value))?.as_str(),
            ],
        )?;
    }
    Ok(())
}
pub fn open_index(path: &Path) -> Result<Connection> {
    if !path.is_file() || path.is_symlink() {
        return Err(failure("SEARCH_INDEX_UNAVAILABLE"));
    }
    let connection =
        Connection::open_with_flags(files::resolve(path)?, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
    connection.busy_timeout(std::time::Duration::from_secs(10))?;
    Ok(connection)
}

/// A published native generation records the batch and actual device that
/// produced its vectors. Retrieval still validates the full model contract.
pub(super) fn published_execution(config: &Config) -> Option<ExecutionOptions> {
    let connection = open_index(&folder(config).join("index.sqlite3")).ok()?;
    let metadata = meta(&connection).ok()?;
    let contract = &metadata["contract"];
    if metadata["owner"] != OWNER
        || metadata["complete"] != true
        || metadata["binding"] != database_binding(config).ok()?
        || contract["native_runtime"] != NATIVE_EMBEDDING_RUNTIME
        || metadata["identity"] != digest(contract).ok()?
    {
        return None;
    }
    let device = match contract["runtime"]["device"].as_str()? {
        "cpu" => DevicePreference::Cpu,
        "mps" => DevicePreference::Mps,
        "cuda" => DevicePreference::Cuda,
        _ => return None,
    };
    let batch_size = usize::try_from(contract["batch_size"].as_u64()?).ok()?;
    (1..=MAX_BATCH_SIZE)
        .contains(&batch_size)
        .then_some(ExecutionOptions { device, batch_size })
}
pub struct Writer {
    _file: File,
    pub root: PathBuf,
}
pub fn writer(config: &Config) -> Result<Writer> {
    let root = files::private_directory(&folder(config), config)?;
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(root.join("writer.lock"))?;
    let info = file.metadata()?;
    if info.nlink() != 1 || info.uid() != unsafe { libc::getuid() } {
        return Err(failure("UNOWNED_SEARCH_LOCK"));
    }
    files::lock(&file, libc::LOCK_EX | libc::LOCK_NB).map_err(|_| failure("SEARCH_BUSY"))?;
    Ok(Writer { _file: file, root })
}
pub fn writer_active(config: &Config) -> Result<bool> {
    let file = match OpenOptions::new()
        .read(true)
        .write(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(folder(config).join("writer.lock"))
    {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(false),
        Err(error) => return Err(error.into()),
    };
    let info = file.metadata()?;
    if info.nlink() != 1 || info.uid() != unsafe { libc::getuid() } {
        return Err(failure("UNOWNED_SEARCH_LOCK"));
    }
    Ok(files::lock(&file, libc::LOCK_EX | libc::LOCK_NB).is_err())
}
struct Builder<'a> {
    config: &'a Config,
    encoder: &'a dyn Encoder,
    profile: Profile,
    cancel: &'a Cancellation,
    stats: Value,
    started: Instant,
    connection: Option<Connection>,
    prior: Option<Connection>,
    known: BTreeSet<String>,
    pending: BTreeMap<String, String>,
    last_flush: u64,
    progress: &'a mut dyn FnMut(&Value),
}
impl Builder<'_> {
    fn report(&mut self) -> Result<()> {
        self.stats["elapsed_seconds"] =
            ((self.started.elapsed().as_secs_f64() * 1000.0).round() / 1000.0).into();
        let disk = fs::read_dir(folder(self.config))?
            .map(|entry| {
                entry.and_then(|entry| entry.metadata()).map(|info| {
                    if info.is_file() {
                        info.len()
                    } else {
                        0
                    }
                })
            })
            .collect::<std::io::Result<Vec<_>>>()?
            .into_iter()
            .sum::<u64>();
        self.stats["disk_bytes"] = disk.into();
        self.stats["peak_disk_bytes"] = self.stats["peak_disk_bytes"]
            .as_u64()
            .unwrap_or(0)
            .max(disk)
            .into();
        atomic_json(&folder(self.config).join("status.json"), &self.stats)?;
        (self.progress)(&self.stats);
        Ok(())
    }
    fn connection(&self) -> &Connection {
        self.connection.as_ref().unwrap()
    }
    fn begin(&self) -> Result<()> {
        if self.connection().is_autocommit() {
            self.connection().execute_batch("BEGIN")?;
        }
        Ok(())
    }
    fn flush(&mut self) -> Result<()> {
        if self.cancel.load(Ordering::Acquire) {
            return Err(failure("SEARCH_INTERRUPTED"));
        }
        if !self.pending.is_empty() {
            let keys = self.pending.keys().cloned().collect::<Vec<_>>();
            let vectors = self.encoder.encode(
                &keys
                    .iter()
                    .map(|key| self.pending[key].clone())
                    .collect::<Vec<_>>(),
                false,
                self.cancel,
            )?;
            if vectors.len() != keys.len() {
                return Err(failure("INVALID_SEARCH_VECTORS"));
            }
            self.begin()?;
            for (key, vector) in keys.iter().zip(vectors) {
                if vector.len() != self.profile.dimension
                    || vector.iter().any(|value| !value.is_finite())
                {
                    return Err(failure("INVALID_SEARCH_VECTORS"));
                }
                let norm = vector.iter().map(|value| value * value).sum::<f32>().sqrt();
                if norm <= 0.0 || !norm.is_finite() {
                    return Err(failure("INVALID_SEARCH_VECTORS"));
                }
                let bytes = vector
                    .iter()
                    .flat_map(|value| (value / norm).to_le_bytes())
                    .collect::<Vec<_>>();
                self.connection().execute(
                    "INSERT OR IGNORE INTO vectors VALUES (?,?)",
                    params![key, bytes],
                )?;
            }
            inc(&mut self.stats, "encoded", keys.len() as u64);
            self.known.extend(keys);
            self.pending.clear();
        }
        if !self.connection().is_autocommit() {
            self.connection().execute_batch("COMMIT")?;
        }
        self.last_flush = self.stats["fragments"].as_u64().unwrap_or(0);
        self.report()
    }
    fn molecule(
        &mut self,
        source: &Source,
        value: Value,
        previous: Option<&Connection>,
    ) -> Result<()> {
        self.begin()?;
        let key = value["input_hash"]
            .as_str()
            .ok_or_else(|| failure("INVALID_SEARCH_MOLECULE"))?
            .to_string();
        if self.known.contains(&key) || self.pending.contains_key(&key) {
            inc(&mut self.stats, "reused", 1);
        } else {
            let prior = if let Some(prior) = previous {
                prior
                    .query_row(
                        "SELECT value FROM vectors WHERE input_hash=?",
                        [&key],
                        |row| row.get::<_, Vec<u8>>(0),
                    )
                    .optional()?
            } else {
                None
            };
            if let Some(bytes) = prior {
                self.connection()
                    .execute("INSERT INTO vectors VALUES (?,?)", params![key, bytes])?;
                self.known.insert(key.clone());
                inc(&mut self.stats, "reused", 1);
            } else {
                self.pending
                    .insert(key.clone(), value["input"].as_str().unwrap().into());
            }
        }
        self.connection().execute("INSERT INTO fragments(parent_key,ordinal,input_hash,body_hash,text,context,locator) VALUES (?,?,?,?,?,?,?)",params![source.key,value["ordinal"].as_i64(),key,value["body_hash"].as_str(),value["text"].as_str(),value["context"].as_str(),serde_json::to_string(&value["locator"])?])?;
        let rowid = self.connection().last_insert_rowid();
        let words = lexical_tokens(&format!(
            "{}\n{}",
            source.title,
            value["text"].as_str().unwrap()
        ));
        self.connection().execute(
            "INSERT INTO terms(rowid,tokens) VALUES (?,?)",
            params![rowid, words.join(" ")],
        )?;
        inc(&mut self.stats, "fragments", 1);
        inc(
            &mut self.stats,
            "context_limited",
            u64::from(
                value["locator"]["context_limited"]
                    .as_bool()
                    .unwrap_or(false),
            ),
        );
        if self.stats["fragments"].as_u64().unwrap() - self.last_flush
            >= self.encoder.batch_size() as u64
        {
            self.flush()?;
        }
        Ok(())
    }
}
fn inc(value: &mut Value, key: &str, amount: u64) {
    value[key] = (value[key].as_u64().unwrap_or(0) + amount).into();
}
pub fn prepare(
    config: &Config,
    encoder: &dyn Encoder,
    profile: Profile,
    cancel: &Cancellation,
    force: bool,
    progress: &mut dyn FnMut(&Value),
) -> Result<Value> {
    profile.validate()?;
    let writer = writer(config)?;
    prepare_locked(config, encoder, profile, cancel, force, progress, &writer)
}

pub(super) fn prepare_locked(
    config: &Config,
    encoder: &dyn Encoder,
    profile: Profile,
    cancel: &Cancellation,
    force: bool,
    progress: &mut dyn FnMut(&Value),
    writer: &Writer,
) -> Result<Value> {
    let stage = writer.root.join("building.sqlite3");
    let active = writer.root.join("index.sqlite3");
    let mut contract = encoder.contract();
    for (key, value) in profile.index_contract().as_object().unwrap() {
        contract[key] = value.clone();
    }
    let identity = digest(&contract)?;
    let binding = database_binding(config)?;
    let started = Instant::now();
    let stats = json!({"state":"preparing","parents":0,"fragments":0,"encoded":0,"reused":0,"context_limited":0,"pid":std::process::id(),"started_at":SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64()});
    let mut builder = Builder {
        config,
        encoder,
        profile,
        cancel,
        stats,
        started,
        connection: None,
        prior: None,
        known: BTreeSet::new(),
        pending: BTreeMap::new(),
        last_flush: 0,
        progress,
    };
    let outcome = (|| {
        builder.report()?;
        if stage.exists() {
            let old = meta(&open_index(&stage)?)?;
            if old["owner"] != OWNER || old["binding"] != binding {
                return Err(failure("UNOWNED_SEARCH_INDEX"));
            }
            if force || old["identity"] != identity {
                fs::remove_file(&stage)?;
            }
        }
        files::private_database(&stage, config)?;
        let connection = Connection::open(&stage)?;
        connection.busy_timeout(std::time::Duration::from_secs(30))?;
        connection.execute_batch(SCHEMA)?;
        set_meta(
            &connection,
            &json!({"owner":OWNER,"binding":binding,"identity":identity,"contract":contract,"complete":false}),
        )?;
        connection
            .execute_batch("DELETE FROM parents; DELETE FROM fragments; DELETE FROM terms")?;
        builder.connection = Some(connection);
        let mut old = Value::Null;
        if active.exists() {
            let prior = open_index(&active)?;
            old = meta(&prior)?;
            if old["owner"] != OWNER || old["binding"] != binding {
                return Err(failure("UNOWNED_SEARCH_INDEX"));
            }
            if !force && old["identity"] == identity {
                builder.prior = Some(prior);
            }
        }
        let (sources, coverage) = read_sources(config, None)?;
        for (key, value) in coverage.as_object().unwrap() {
            builder.stats[key] = value.clone();
        }
        let revisions = sources
            .iter()
            .map(|source| Ok((source.key.clone(), source.revision()?)))
            .collect::<Result<BTreeMap<_, _>>>()?;
        let prior_revisions = if let Some(prior) = &builder.prior {
            db::rows(prior, "SELECT key,revision FROM parents", [])?
                .into_iter()
                .map(|row| {
                    (
                        row["key"].as_str().unwrap().into(),
                        row["revision"].as_str().unwrap().into(),
                    )
                })
                .collect::<BTreeMap<String, String>>()
        } else {
            BTreeMap::new()
        };
        if builder.prior.is_some() && old["complete"] == true && revisions == prior_revisions {
            builder.stats["parents"] = sources.len().into();
            builder.stats["fragments"] = old["fragments"].clone();
            builder.stats["reused"] = old["fragments"].clone();
            builder.stats["state"] = if sources.is_empty() {
                "no-data"
            } else {
                "ready"
            }
            .into();
            builder.stats["unchanged"] = true.into();
            builder.stats["context_limited"]=builder.prior.as_ref().unwrap().query_row("SELECT coalesce(sum(json_extract(locator,'$.context_limited')),0) FROM fragments",[],|row|row.get::<_,i64>(0))?.into();
            builder.connection.take();
            fs::remove_file(&stage)?;
            builder.report()?;
            return Ok(builder.stats.clone());
        }
        builder.known = db::rows(builder.connection(), "SELECT input_hash FROM vectors", [])?
            .iter()
            .filter_map(|row| row["input_hash"].as_str().map(str::to_owned))
            .collect();
        let tokenizer = if sources.is_empty() {
            None
        } else {
            Some(encoder.tokenizer(cancel)?)
        };
        for source in &sources {
            if cancel.load(Ordering::Acquire) {
                return Err(failure("SEARCH_INTERRUPTED"));
            }
            builder.begin()?;
            builder.connection().execute(
                "INSERT INTO parents VALUES (?,?,?)",
                [
                    source.key.as_str(),
                    revisions[&source.key].as_str(),
                    serde_json::to_string(&source.metadata()?)?.as_str(),
                ],
            )?;
            let prior = builder.prior.take();
            if prior_revisions.get(&source.key) == revisions.get(&source.key) {
                let connection = prior.as_ref().unwrap();
                let mut statement=connection.prepare("SELECT ordinal,input_hash,body_hash,text,context,locator FROM fragments WHERE parent_key=? ORDER BY ordinal")?;
                let mut cursor = statement.query([&source.key])?;
                while let Some(row) = cursor.next()? {
                    let text: String = row.get(3)?;
                    let context: String = row.get(4)?;
                    let value = json!({"ordinal":row.get::<_,i64>(0)?,"input_hash":row.get::<_,String>(1)?,"body_hash":row.get::<_,String>(2)?,"input":format!("{context}\n\n{text}"),"text":text,"context":context,"locator":serde_json::from_str::<Value>(&row.get::<_,String>(5)?)?});
                    builder.molecule(source, value, prior.as_ref())?;
                }
            } else {
                for_each_molecule(
                    source,
                    tokenizer.as_ref().unwrap().as_ref(),
                    profile,
                    |value| builder.molecule(source, value, prior.as_ref()),
                )?;
            }
            builder.prior = prior;
            inc(&mut builder.stats, "parents", 1);
            builder.flush()?;
        }
        builder.flush()?;
        builder.begin()?;
        builder.connection().execute(
            "DELETE FROM vectors WHERE input_hash NOT IN (SELECT input_hash FROM fragments)",
            [],
        )?;
        set_meta(
            builder.connection(),
            &json!({"complete":true,"coverage":coverage,"completed_at":SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64(),"fragments":builder.stats["fragments"],"generation":digest(&json!([identity,SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_nanos()]))?}),
        )?;
        builder.connection().execute_batch("COMMIT; VACUUM")?;
        builder.connection.take();
        builder.prior.take();
        if cancel.load(Ordering::Acquire) {
            return Err(failure("SEARCH_INTERRUPTED"));
        }
        fs::rename(&stage, &active)?;
        builder.stats["state"] = if sources.is_empty() {
            "no-data"
        } else {
            "ready"
        }
        .into();
        builder.report()?;
        Ok(builder.stats.clone())
    })();
    if let Err(error) = &outcome {
        if let Some(connection) = &builder.connection {
            if !connection.is_autocommit() {
                let _ = connection.execute_batch("ROLLBACK");
            }
        }
        builder.stats["state"] = "failed".into();
        builder.stats["error"] =
            if error.code == "SEARCH_INTERRUPTED" || cancel.load(Ordering::Acquire) {
                "SEARCH_INTERRUPTED"
            } else {
                "SEARCH_PREPARATION_FAILED"
            }
            .into();
        builder.report()?;
    }
    outcome
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_query_retries_only_if_an_incompatible_generation_was_replaced() {
        let root = tempfile::tempdir().unwrap();
        let config = Config::for_data_dir(root.path().join("data"));
        let folder = folder(&config);
        fs::create_dir_all(&folder).unwrap();
        let active = folder.join("index.sqlite3");
        let stage = folder.join("building.sqlite3");
        fs::write(&active, b"generation A").unwrap();
        let mut attempts = 0;
        let result = read_published(&config, || {
            attempts += 1;
            if attempts == 1 {
                fs::write(&stage, b"generation B").unwrap();
                fs::rename(&stage, &active).unwrap();
                Err(failure("SEARCH_INDEX_INCOMPATIBLE"))
            } else {
                Ok(fs::read(&active)?)
            }
        })
        .unwrap();
        assert_eq!(result, b"generation B");
        assert_eq!(attempts, 2);

        let mut attempts = 0;
        let error = read_published(&config, || {
            attempts += 1;
            Err::<(), _>(failure("SEARCH_INDEX_INCOMPATIBLE"))
        })
        .unwrap_err();
        assert_eq!(error.code, "SEARCH_INDEX_INCOMPATIBLE");
        assert_eq!(attempts, 1);
    }
}
