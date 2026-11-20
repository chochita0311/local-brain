//! Only recognized, inactive, expired derived files may be retired. Markers,
//! locks, unknown shapes and active producers survive cleanup.
use super::{
    common::{failure, require},
    inventory::OWNER,
    preview::{read_preview, PREVIEW_OWNER},
    store::FILES,
};
use crate::backend::{
    clock,
    storage::{files, layout::CacheOwners},
    Config, Result,
};
use chrono::{DateTime, Utc};
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    fs::{self, OpenOptions},
    os::unix::fs::OpenOptionsExt,
    path::Path,
};
fn names(folder: &Path) -> Result<BTreeSet<String>> {
    Ok(fs::read_dir(folder)?
        .map(|entry| entry.map(|entry| entry.file_name().to_string_lossy().into_owned()))
        .collect::<std::io::Result<_>>()?)
}
fn simulation_owned(folder: &Path) -> Result<bool> {
    let marker = files::read_owned_json(&folder.join("owner.json"), 8192)?;
    Ok(marker["owner"] == OWNER
        && names(folder)?
            .iter()
            .all(|name| FILES.contains(&name.as_str())))
}
fn preview_owned(folder: &Path) -> Result<bool> {
    let names = names(folder)?;
    let mut owned = names
        .iter()
        .all(|name| ["current.json", "preview.lock"].contains(&name.as_str()));
    if names.contains("current.json") {
        owned &= files::read_owned_json(&folder.join("current.json"), 8 * 1024 * 1024)?["owner"]
            == PREVIEW_OWNER;
    } else {
        owned &= names == BTreeSet::from(["preview.lock".to_owned()])
            && fs::metadata(folder.join("preview.lock"))?.len() == 0;
    }
    Ok(owned)
}
pub fn legacy_cache_owners() -> CacheOwners {
    let mut owners = CacheOwners::new();
    owners.insert("session-simulation".into(), Box::new(simulation_owned));
    owners.insert("auto-work-preview".into(), Box::new(preview_owned));
    owners
}
pub fn maintain_cache(
    config: &Config,
    cache_root: &Path,
    apply: bool,
    at: Option<DateTime<Utc>>,
) -> Result<Value> {
    let root = files::validate_runtime_directory(cache_root, config)?;
    let at = at.unwrap_or_else(Utc::now);
    let mut eligible_files = 0u64;
    let mut eligible_bytes = 0u64;
    let mut removed_files = 0u64;
    let mut removed_bytes = 0u64;
    let mut preserved = 0u64;
    for name in ["session-simulation", "auto-work-preview"] {
        let folder = root.join(name);
        if folder.symlink_metadata().is_err() {
            continue;
        }
        let result = (|| -> Result<()> {
            let stamps = files::owned_tree(&folder)?;
            let simulation = name == "session-simulation";
            let (lock_name, marker_name, owner) = if simulation {
                ("writer.lock", "owner.json", OWNER)
            } else {
                ("preview.lock", "current.json", PREVIEW_OWNER)
            };
            let known = if simulation {
                FILES
            } else {
                &["preview.lock", "current.json"][..]
            };
            require(
                names(&folder)?
                    .iter()
                    .all(|name| known.contains(&name.as_str()))
                    && files::tree_is_inactive(&stamps),
                "STORAGE_BUSY_OR_UNAVAILABLE",
            )?;
            let file = OpenOptions::new()
                .read(true)
                .write(true)
                .custom_flags(libc::O_NOFOLLOW)
                .open(folder.join(lock_name))?;
            files::lock(&file, libc::LOCK_EX | libc::LOCK_NB)?;
            files::ensure_unchanged(&stamps)?;
            let marker = if simulation {
                let value = files::read_owned_json(&folder.join(marker_name), 8192)?;
                let keys = value
                    .as_object()
                    .unwrap()
                    .keys()
                    .map(String::as_str)
                    .collect::<BTreeSet<_>>();
                let binding = value["database"].as_str().unwrap_or_default();
                require(
                    keys == BTreeSet::from(["owner", "database", "expires_at"])
                        && binding.len() == 64
                        && binding
                            .bytes()
                            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)),
                    "UNOWNED_STORAGE",
                )?;
                value
            } else {
                read_preview(&folder.join(marker_name))?
            };
            let expires = marker["expires_at"]
                .as_str()
                .and_then(clock::parse_iso_datetime)
                .filter(|value| value.offset_micros.is_some())
                .and_then(|value| value.utc())
                .ok_or_else(|| failure("UNOWNED_STORAGE"))?;
            require(marker["owner"] == owner, "UNOWNED_STORAGE")?;
            if expires > at {
                return Ok(());
            }
            let retired = stamps
                .iter()
                .filter(|stamp| {
                    stamp.path != folder
                        && stamp.path.file_name().is_some_and(|name| {
                            name != lock_name && (!simulation || name != marker_name)
                        })
                })
                .collect::<Vec<_>>();
            require(
                retired.iter().all(|stamp| stamp.info.is_file()),
                "UNOWNED_STORAGE",
            )?;
            let size = retired.iter().map(|stamp| stamp.info.len()).sum::<u64>();
            eligible_files += retired.len() as u64;
            eligible_bytes += size;
            if apply {
                files::ensure_unchanged(&stamps)?;
                for stamp in &retired {
                    fs::remove_file(&stamp.path)?;
                }
                removed_files += retired.len() as u64;
                removed_bytes += size;
            }
            Ok(())
        })();
        if result.is_err() {
            preserved += 1;
        }
    }
    Ok(
        json!({"eligible_files":eligible_files,"eligible_bytes":eligible_bytes,"removed_files":removed_files,"removed_bytes":removed_bytes,"preserved_directories":preserved}),
    )
}
