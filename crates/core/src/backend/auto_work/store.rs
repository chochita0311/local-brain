use super::{
    common::*,
    inventory::{self, OWNER},
};
use crate::backend::{clock, storage, BackendError, Config, Result};
use chrono::{DateTime, Duration, Utc};
use localbrain_models::Cancellation;
use rusqlite::Connection;
use serde_json::{json, Value};
use std::{
    fs::{self, File, OpenOptions},
    os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt},
    path::{Path, PathBuf},
};
pub(super) const FILES: &[&str] = &[
    "owner.json",
    "writer.lock",
    "state.sqlite3",
    "state.sqlite3-journal",
    "report.json",
    "previous-report.json",
    "progress.json",
];
const SCHEMA:&str="CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS sessions(key TEXT PRIMARY KEY,id INTEGER NOT NULL,title TEXT NOT NULL,status TEXT NOT NULL); CREATE TABLE IF NOT EXISTS chunks(key TEXT PRIMARY KEY,session_key TEXT NOT NULL,event_id TEXT NOT NULL,start INTEGER NOT NULL,end INTEGER NOT NULL,content_hash TEXT NOT NULL,input_hash TEXT NOT NULL,role TEXT NOT NULL,at TEXT); CREATE INDEX IF NOT EXISTS chunks_input ON chunks(input_hash); CREATE TABLE IF NOT EXISTS embeddings(namespace TEXT NOT NULL,input_hash TEXT NOT NULL,vector BLOB NOT NULL,PRIMARY KEY(namespace,input_hash));";
pub(super) fn binding(database: &Path) -> Result<String> {
    require(
        database.is_absolute() && database.is_file() && !database.is_symlink(),
        "INVALID_DATABASE",
    )?;
    let info = fs::metadata(database)?;
    Ok(digest(&json!([
        fs::canonicalize(database)?.to_string_lossy(),
        info.dev(),
        info.ino()
    ])))
}
pub(super) struct Store {
    pub connection: Option<Connection>,
    pub folder: PathBuf,
    _lock: File,
}
impl Store {
    pub(super) fn open(
        config: &Config,
        folder: &Path,
        database: &Path,
        purge: bool,
        at: DateTime<Utc>,
    ) -> Result<Self> {
        let binding = binding(database)?;
        let resolved = storage::files::resolve(folder)?;
        require(
            folder.is_absolute()
                && folder == resolved
                && folder != database.parent().unwrap_or(Path::new("/"))
                && folder.parent().is_some_and(Path::is_dir),
            "INVALID_OUTPUT",
        )?;
        if let Some(root) = &config.installation_root {
            require(!folder.starts_with(root), "INVALID_OUTPUT")?;
        }
        storage::files::validate_runtime_directory(folder, config)
            .map_err(|_| failure("INVALID_OUTPUT"))?;
        let created = folder.symlink_metadata().is_err();
        if created {
            require(!purge, "NO_SIMULATION")?;
            fs::DirBuilder::new().mode(0o700).create(folder)?;
        }
        let info = fs::symlink_metadata(folder)?;
        require(
            info.is_dir() && info.uid() == unsafe { libc::getuid() } && info.mode() & 0o077 == 0,
            "UNOWNED_OUTPUT",
        )?;
        if !created {
            let marker = read_json(&folder.join("owner.json"), 65536)?;
            require(
                marker["owner"] == OWNER && marker["database"] == binding,
                "UNOWNED_OUTPUT",
            )?;
        }
        let lock_path = folder.join("writer.lock");
        let lock_file = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .mode(0o600)
            .custom_flags(libc::O_NOFOLLOW)
            .open(&lock_path)?;
        safe_file(&lock_path)?;
        lock(&lock_file, libc::LOCK_EX)?;
        if created {
            atomic_json(
                &folder.join("owner.json"),
                &json!({"owner":OWNER,"database":binding,"expires_at":clock::isoformat(at+Duration::days(30))}),
            )?;
        }
        for entry in fs::read_dir(folder)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().into_owned();
            if let Some(base) = name
                .strip_suffix(".pending")
                .filter(|name| FILES.contains(name))
            {
                let _ = base;
                safe_file(&entry.path())?;
                fs::remove_file(entry.path())?;
            } else {
                require(FILES.contains(&name.as_str()), "UNOWNED_OUTPUT")?;
                safe_file(&entry.path())?;
            }
        }
        let marker = read_json(&folder.join("owner.json"), 65536)?;
        let expires = marker["expires_at"]
            .as_str()
            .ok_or_else(|| failure("UNOWNED_OUTPUT"))?;
        let expired = utc(expires)? <= at;
        if purge || expired {
            for name in FILES
                .iter()
                .filter(|name| !matches!(**name, "owner.json" | "writer.lock"))
            {
                let path = folder.join(name);
                if path.symlink_metadata().is_ok() {
                    safe_file(&path)?;
                    fs::remove_file(path)?;
                }
            }
            if purge {
                return Ok(Self {
                    connection: None,
                    folder: folder.into(),
                    _lock: lock_file,
                });
            }
        }
        atomic_json(
            &folder.join("owner.json"),
            &json!({"owner":OWNER,"database":binding,"expires_at":clock::isoformat(at+Duration::days(30))}),
        )?;
        let path = folder.join("state.sqlite3");
        if path.symlink_metadata().is_err() {
            drop(
                OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .mode(0o600)
                    .custom_flags(libc::O_NOFOLLOW)
                    .open(&path)?,
            );
        }
        safe_file(&path)?;
        let connection = Connection::open(path)?;
        connection.execute_batch("PRAGMA secure_delete=ON")?;
        connection.execute_batch(SCHEMA)?;
        Ok(Self {
            connection: Some(connection),
            folder: folder.into(),
            _lock: lock_file,
        })
    }
}
pub fn prepare_inventory(
    config: &Config,
    folder: &Path,
    chunk_chars: usize,
    at: Option<DateTime<Utc>>,
    cancel: &Cancellation,
) -> Result<Value> {
    check_cancel(cancel)?;
    let at = at.unwrap_or_else(Utc::now);
    let store = Store::open(config, folder, &config.database_path, false, at)?;
    let mut progress = json!({"owner":OWNER,"state":"inventory","started_at":clock::isoformat(at),"quality":"unassessed"});
    atomic_json(&folder.join("progress.json"), &progress)?;
    let manifest = match inventory::sync_inventory(
        store.connection.as_ref().unwrap(),
        &config.database_path,
        chunk_chars,
        cancel,
    )
    .map_err(|error| check_cancel(cancel).err().unwrap_or(error))
    {
        Ok(manifest) => manifest,
        Err(error) => {
            record_failure(folder, &mut progress, &error)?;
            return Err(error);
        }
    };
    let progress = json!({"owner":OWNER,"state":"prepared","manifest":manifest,"updated_at":clock::isoformat(at),"quality":"unassessed"});
    atomic_json(&folder.join("progress.json"), &progress)?;
    Ok(progress)
}
pub(super) fn record_failure(
    folder: &Path,
    progress: &mut Value,
    error: &BackendError,
) -> Result<()> {
    progress["state"] = if error.code == "SIMULATION_INTERRUPTED" {
        "interrupted"
    } else {
        "failed"
    }
    .into();
    progress["error_code"] = if error
        .code
        .chars()
        .all(|ch| ch.is_ascii_uppercase() || ch == '_')
    {
        error.code.as_str()
    } else {
        "SIMULATION_FAILED"
    }
    .into();
    atomic_json(&folder.join("progress.json"), progress)
}
pub fn purge(config: &Config, folder: &Path, at: Option<DateTime<Utc>>) -> Result<()> {
    drop(Store::open(
        config,
        folder,
        &config.database_path,
        true,
        at.unwrap_or_else(Utc::now),
    )?);
    Ok(())
}
pub fn simulation_status(
    config: &Config,
    folder: &Path,
    at: Option<DateTime<Utc>>,
) -> Result<Value> {
    let marker = read_json(&folder.join("owner.json"), 65536)?;
    require(
        marker["owner"] == OWNER && marker["database"] == binding(&config.database_path)?,
        "UNOWNED_OUTPUT",
    )?;
    require(
        utc(marker["expires_at"]
            .as_str()
            .ok_or_else(|| failure("UNOWNED_OUTPUT"))?)?
            > at.unwrap_or_else(Utc::now),
        "SIMULATION_EXPIRED",
    )?;
    let mut progress = read_json(&folder.join("progress.json"), 128 * 1024 * 1024)?;
    let state = progress["state"].as_str().unwrap_or_default();
    require(
        progress["owner"] == OWNER
            && [
                "prepared",
                "inventory",
                "embedding",
                "grouping",
                "complete",
                "interrupted",
                "failed",
            ]
            .contains(&state),
        "INVALID_INPUT",
    )?;
    if ["inventory", "embedding", "grouping"].contains(&state) {
        let path = folder.join("writer.lock");
        let file = OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_NOFOLLOW)
            .open(&path)?;
        safe_file(&path)?;
        if lock(&file, libc::LOCK_EX).is_ok() {
            progress["state"] = "interrupted".into();
        }
    } else if state == "failed" && progress["error_code"] == "MODEL_CANCELLED" {
        progress["state"] = "interrupted".into();
        progress["error_code"] = "SIMULATION_INTERRUPTED".into();
    }
    if progress["state"] == "complete" {
        let manifest = &progress["manifest"];
        let chunk_chars = manifest["chunk_chars"]
            .as_u64()
            .ok_or_else(|| failure("INVALID_CHUNK_SIZE"))? as usize;
        require(
            inventory::inventory(&config.database_path, chunk_chars, |_, _| Ok(()))? == *manifest,
            "SOURCE_CHANGED",
        )?;
    }
    Ok(progress)
}
