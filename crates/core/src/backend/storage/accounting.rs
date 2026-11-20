use super::{files, migrations};
use crate::backend::{Config, Result};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    os::unix::{ffi::OsStrExt, fs::MetadataExt},
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};
pub const MIGRATION_BACKUP_SUFFIXES: [&str; 11] = [
    "-pre-session-display-title-v1.bak",
    "-pre-shared-resources-v1.bak",
    "-pre-session-revision-v1.bak",
    "-pre-usage-attribution-check-v1.bak",
    "-pre-usage-record-rename-v1.bak",
    "-pre-maintenance-session-contract-v1.bak",
    "-pre-maintenance-workstream-fk-v1.bak",
    "-pre-external-resource-url-scope-v1.bak",
    "-pre-atlassian-site-access-v1.bak",
    "-pre-source-provider-identity-v1.bak",
    "-pre-source-primary-key-v1.bak",
];
pub fn directory_size(root: &Path) -> Value {
    let info = match fs::metadata(root) {
        Ok(info) => info,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return json!({"bytes":0,"state":"missing"})
        }
        Err(_) => return json!({"bytes":null,"state":"unavailable"}),
    };
    if !info.is_dir() {
        return json!({"bytes":null,"state":"unavailable"});
    }
    let mut total = 0_u64;
    let mut seen = BTreeSet::new();
    let mut partial = false;
    for entry in walkdir::WalkDir::new(root)
        .follow_root_links(true)
        .follow_links(false)
    {
        let entry = match entry {
            Ok(entry) => entry,
            Err(_) => {
                partial = true;
                continue;
            }
        };
        let info = match fs::symlink_metadata(entry.path()) {
            Ok(info) => info,
            Err(_) => {
                partial = true;
                continue;
            }
        };
        if info.is_file() && seen.insert((info.dev(), info.ino())) {
            total += info.len();
        }
    }
    json!({"bytes":total,"state":if partial{"partial"}else{"complete"}})
}
pub fn volume_status(root: &Path) -> Value {
    let mut candidate = root;
    loop {
        match fs::metadata(candidate) {
            Ok(info) => {
                if let Ok(path) = std::ffi::CString::new(candidate.as_os_str().as_bytes()) {
                    let mut usage = std::mem::MaybeUninit::<libc::statvfs>::uninit();
                    if unsafe { libc::statvfs(path.as_ptr(), usage.as_mut_ptr()) } == 0 {
                        let usage = unsafe { usage.assume_init() };
                        return json!({"id":info.dev().to_string(),"free_bytes":usage.f_bavail as u64*usage.f_frsize,"state":"complete"});
                    }
                }
                break;
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                let Some(parent) = candidate.parent() else {
                    break;
                };
                if parent == candidate {
                    break;
                }
                candidate = parent;
            }
            Err(_) => break,
        }
    }
    json!({"id":null,"free_bytes":null,"state":"unavailable"})
}
pub fn location_status(root: &Path) -> Value {
    let mut result = directory_size(root);
    result["volume"] = volume_status(root);
    result
}
pub fn storage_status(config: &Config) -> Result<Value> {
    let mut paths = BTreeMap::from([
        ("data", config.data_dir.clone()),
        ("cache", config.cache_dir.clone()),
        ("models", crate::backend::models::hub_cache_root(config)?),
    ]);
    let registration = crate::backend::models::model_root(
        config,
        localbrain_models::catalog::ModelKey::Embedding,
    )?
    .join("model.json");
    if registration.is_file() {
        if let Some(selected) = crate::backend::models::folder_status(config)?["path"].as_str() {
            let selected = PathBuf::from(selected);
            let model = paths["models"].clone();
            if model.starts_with(&selected) {
                paths.insert("models", selected);
            } else if !selected.starts_with(&model) {
                paths.insert("embedding_models", selected);
            }
        }
    }
    let mut result = serde_json::Map::new();
    let mut locations = serde_json::Map::new();
    let mut display = serde_json::Map::new();
    for (key, path) in paths {
        let status = location_status(&path);
        result.insert(key.into(), json!(path));
        result.insert(format!("{key}_bytes"), status["bytes"].clone());
        locations.insert(key.into(), status);
        display.insert(
            key.into(),
            json!(if let Ok(relative) = path.strip_prefix(&config.home_dir) {
                if relative.as_os_str().is_empty() {
                    "~".into()
                } else {
                    format!("~/{}", relative.display())
                }
            } else {
                path.to_string_lossy().into_owned()
            }),
        );
    }
    result.insert(
        "free_bytes".into(),
        locations["data"]["volume"]["free_bytes"].clone(),
    );
    result.insert("locations".into(), locations.into());
    result.insert("display_paths".into(), display.into());
    result.insert(
        "restore_pending".into(),
        config.data_dir.join("restore-pending.zip").is_file().into(),
    );
    result.insert("recovery".into(), json!(config.data_dir.join("recovery")));
    Ok(result.into())
}
fn backups(database: &Path) -> Vec<(i64, i64, Vec<PathBuf>)> {
    let mut result = Vec::new();
    for suffix in MIGRATION_BACKUP_SUFFIXES {
        let path = PathBuf::from(format!("{}{suffix}", database.display()));
        let Ok(info) = files::owned_file(&path) else {
            continue;
        };
        let mut group = vec![path.clone()];
        for suffix in ["-wal", "-shm"] {
            let sidecar = PathBuf::from(format!("{}{suffix}", path.display()));
            if fs::symlink_metadata(&sidecar).is_ok() {
                group.push(sidecar);
            }
        }
        if group.iter().any(|path| files::owned_file(path).is_err())
            || group.iter().any(|path| {
                path.as_os_str().to_string_lossy().ends_with("-wal")
                    && fs::metadata(path).is_ok_and(|info| info.len() != 0)
            })
        {
            continue;
        }
        result.push((info.mtime(), info.mtime_nsec(), group));
    }
    result.sort_by(|left, right| (right.0, right.1).cmp(&(left.0, left.1)));
    result
}
pub fn maintain_migration_backups(
    database: &Path,
    connection: &Connection,
    apply: bool,
    current_time: Option<f64>,
) -> Result<Value> {
    let backups = backups(database);
    let mut result = json!({"eligible_files":0,"eligible_bytes":0,"removed_files":0,"removed_bytes":0,"preserved_backups":0});
    if backups.is_empty() {
        return Ok(result);
    }
    if !migrations::migration_contracts_current(connection)? {
        result["preserved_backups"] = backups.len().into();
        return Ok(result);
    }
    migrations::support::quick_check(connection)?;
    let cutoff = current_time.unwrap_or_else(|| {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64()
    }) - 7.0 * 86400.0;
    for (index, (modified, nanos, group)) in backups.into_iter().enumerate() {
        if (index == 0 && (modified as f64 + nanos as f64 / 1e9) >= cutoff)
            || !files::inactive_files(&group)
        {
            increment(&mut result, "preserved_backups", 1);
            continue;
        }
        let stamps = group
            .iter()
            .map(|path| {
                Ok(files::Stamp {
                    path: path.clone(),
                    info: fs::metadata(path)?,
                })
            })
            .collect::<Result<Vec<_>>>()?;
        let size = stamps.iter().map(|stamp| stamp.info.len()).sum();
        increment(&mut result, "eligible_files", group.len() as u64);
        increment(&mut result, "eligible_bytes", size);
        if apply {
            files::ensure_unchanged(&stamps).map_err(|_| files::failure("BACKUP_CHANGED"))?;
            for stamp in stamps.iter().rev() {
                fs::remove_file(&stamp.path)?;
            }
            increment(&mut result, "removed_files", group.len() as u64);
            increment(&mut result, "removed_bytes", size);
        }
    }
    Ok(result)
}
pub fn increment(value: &mut Value, key: &str, amount: u64) {
    value[key] = (value[key].as_u64().unwrap_or(0) + amount).into();
}
pub fn aggregate_status(config: &Config) -> Result<Value> {
    let mut categories = BTreeMap::from([
        ("database", 0_u64),
        ("migration_backups", 0),
        ("simulation", 0),
        ("saved_runs", 0),
        ("development_evidence", 0),
        ("model_metadata", 0),
        ("other", 0),
        ("preview", 0),
        ("natural_search", 0),
    ]);
    let mut roots = vec![(&config.data_dir, "")];
    if config.cache_dir != config.data_dir {
        roots.push((&config.cache_dir, "cache"));
    }
    if config.development_dir != config.data_dir {
        roots.push((&config.development_dir, "development"));
    }
    let backups = MIGRATION_BACKUP_SUFFIXES
        .iter()
        .map(|suffix| format!("localbrain.db{suffix}"))
        .collect::<Vec<_>>();
    let mut seen = BTreeSet::new();
    for (root, kind) in roots {
        for entry in walkdir::WalkDir::new(root)
            .follow_links(false)
            .into_iter()
            .filter_map(std::result::Result::ok)
        {
            let info = fs::symlink_metadata(entry.path())?;
            if !info.is_file() || !seen.insert((info.dev(), info.ino())) {
                continue;
            }
            let relative = entry.path().strip_prefix(root).unwrap_or(entry.path());
            let top = relative
                .components()
                .next()
                .map(|component| component.as_os_str().to_string_lossy())
                .unwrap_or_default();
            let category = if kind == "development" {
                "development_evidence"
            } else if kind.is_empty()
                && ["localbrain.db", "localbrain.db-wal", "localbrain.db-shm"]
                    .contains(&top.as_ref())
            {
                "database"
            } else if kind.is_empty()
                && backups.iter().any(|name| {
                    top == name.as_str()
                        || top == format!("{name}-wal")
                        || top == format!("{name}-shm")
                })
            {
                "migration_backups"
            } else if top == "session-simulation" {
                "simulation"
            } else if top == "auto-work-preview" {
                "preview"
            } else if top == "natural-search" {
                "natural_search"
            } else if kind.is_empty() && ["runs", "personal-insight-runs"].contains(&top.as_ref()) {
                "saved_runs"
            } else if top == "personal-insight-evaluations"
                || ["work-context-", "work-role-", "source-claim-"]
                    .iter()
                    .any(|prefix| top.starts_with(prefix))
            {
                "development_evidence"
            } else if ["models", "qwen3-4b", "qwen3-8b", "qwen3-embedding-0-6b"]
                .contains(&top.as_ref())
            {
                "model_metadata"
            } else {
                "other"
            };
            *categories.get_mut(category).unwrap() += info.len();
        }
    }
    Ok(json!({"total_bytes":categories.values().sum::<u64>(),"bytes":categories}))
}
