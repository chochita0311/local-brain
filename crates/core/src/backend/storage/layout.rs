use super::{accounting::increment, files};
use crate::backend::{Config, Result};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    os::unix::fs::{MetadataExt, PermissionsExt},
    path::{Path, PathBuf},
};
pub type CacheOwners = BTreeMap<String, Box<dyn Fn(&Path) -> Result<bool>>>;
type MigrationCandidate<'a> = (PathBuf, PathBuf, Box<dyn Fn(&Path) -> Result<bool> + 'a>);
fn names(path: &Path) -> Result<Vec<String>> {
    Ok(fs::read_dir(path)?
        .map(|entry| entry.map(|entry| entry.file_name().to_string_lossy().into_owned()))
        .collect::<std::io::Result<_>>()?)
}
fn model_owner(path: &Path, key: &str) -> Result<bool> {
    let marker = files::read_owned_json(&path.join("owner.json"), 8192)?;
    let manifest = files::read_owned_json(&path.join("model.json"), 8 * 1024 * 1024)?;
    if names(path)?
        .iter()
        .any(|name| !["owner.json", "model.json", "install.lock"].contains(&name.as_str()))
    {
        return Ok(false);
    }
    if key == "embedding" {
        let model = "Qwen/Qwen3-Embedding-0.6B";
        let revision = "b22da495047858cce924d27d76261e96be6febc0";
        let owner = "localbrain.semantic-model/v1";
        return Ok(
            marker == json!({"owner":owner,"model":model,"revision":revision})
                && manifest["schema"] == owner
                && manifest["model_id"] == model
                && manifest["resolved_revision"] == revision,
        );
    }
    let (model, revision) = if key == "8b" {
        ("Qwen/Qwen3-8B", "b968826d9c46dd6066d109eabc6255188de91218")
    } else {
        ("Qwen/Qwen3-4B", "1cfa9a7208912126459214e8b04321603b3df60c")
    };
    Ok(marker
        == json!({"owner":"localbrain.work-context-model.v1","model":model,"revision":revision})
        && manifest["owner"] == "localbrain.work-context-model.v2"
        && manifest["model_id"] == model
        && manifest["revision"] == revision)
}
fn development_owner(path: &Path) -> Result<bool> {
    if path
        .file_name()
        .is_some_and(|name| name == "personal-insight-evaluations")
    {
        return Ok(true);
    }
    Ok(
        files::read_owned_json(&path.join("owner.json"), 8192)?["owner"]
            == "localbrain.work-context-evaluation.v1"
            && names(path)?.iter().all(|name| {
                ["owner.json", "writer.lock", "progress.json", "report.json"]
                    .contains(&name.as_str())
            }),
    )
}
pub fn migrate_storage(
    config: &Config,
    apply: bool,
    include_development: bool,
    cache_owners: Option<&CacheOwners>,
) -> Result<Value> {
    let data = files::validate_runtime_directory(&config.data_dir, config)?;
    let cache = files::validate_runtime_directory(&config.cache_dir, config)?;
    let development = files::validate_runtime_directory(&config.development_dir, config)?;
    if files::overlap(&data, &cache)
        || files::overlap(&data, &development)
        || files::overlap(&cache, &development)
    {
        return Err(files::failure("STORAGE_ROOTS_OVERLAP"));
    }
    let mut result = json!({"eligible_directories":0,"eligible_bytes":0,"moved_directories":0,"moved_bytes":0,"preserved_directories":0});
    if !data.exists() {
        return Ok(result);
    }
    let mut candidates: Vec<MigrationCandidate<'_>> = Vec::new();
    if let Some(owners) = cache_owners {
        for (name, owner) in owners {
            candidates.push((
                data.join(name),
                cache.join(name),
                Box::new(move |path| owner(path)),
            ));
        }
    }
    for (key, slug) in [
        ("embedding", "qwen3-embedding-0-6b"),
        ("4b", "qwen3-4b"),
        ("8b", "qwen3-8b"),
    ] {
        candidates.push((
            data.join(slug),
            data.join("models").join(slug),
            Box::new(move |path| model_owner(path, key)),
        ));
    }
    if include_development {
        let mut entries = fs::read_dir(&data)?
            .map(|entry| entry.map(|entry| entry.path()))
            .collect::<std::io::Result<Vec<_>>>()?;
        entries.sort();
        for path in entries {
            let name = path.file_name().unwrap_or_default().to_string_lossy();
            if name == "personal-insight-evaluations"
                || ["work-context-", "work-role-", "source-claim-"]
                    .iter()
                    .any(|prefix| name.starts_with(prefix))
            {
                candidates.push((
                    path.clone(),
                    development.join(path.file_name().unwrap()),
                    Box::new(development_owner),
                ));
            }
        }
    }
    let mut moves = Vec::new();
    for (source, target, owner) in candidates {
        if fs::symlink_metadata(&source).is_err() {
            continue;
        }
        let stamps = match files::owned_tree(&source).and_then(|stamps| {
            if source.is_dir() && owner(&source)? {
                Ok(stamps)
            } else {
                Err(files::failure("UNOWNED_STORAGE"))
            }
        }) {
            Ok(stamps) => stamps,
            Err(_) => {
                increment(&mut result, "preserved_directories", 1);
                continue;
            }
        };
        files::validate_runtime_directory(&target, config)?;
        if fs::symlink_metadata(&target).is_ok() {
            return Err(files::failure("STORAGE_DESTINATION_EXISTS"));
        }
        let ancestor = target
            .ancestors()
            .skip(1)
            .find(|parent| parent.exists())
            .ok_or_else(|| files::failure("STORAGE_MOVE_CROSS_DEVICE"))?;
        if fs::metadata(&source)?.dev() != fs::metadata(ancestor)?.dev() {
            return Err(files::failure("STORAGE_MOVE_CROSS_DEVICE"));
        }
        let size = stamps
            .iter()
            .filter(|stamp| stamp.info.is_file())
            .map(|stamp| stamp.info.len())
            .sum::<u64>();
        increment(&mut result, "eligible_directories", 1);
        increment(&mut result, "eligible_bytes", size);
        moves.push((source, target, stamps, size));
    }
    if apply {
        if moves
            .iter()
            .any(|(_, _, stamps, _)| !files::tree_is_inactive(stamps))
        {
            return Err(files::failure("STORAGE_BUSY_OR_UNAVAILABLE"));
        }
        for (_, _, stamps, _) in &moves {
            files::ensure_unchanged(stamps)?;
        }
        for (source, target, stamps, size) in moves {
            files::private_directory(target.parent().unwrap(), config)?;
            files::ensure_unchanged(&stamps)?;
            if fs::symlink_metadata(&target).is_ok() {
                return Err(files::failure("STORAGE_DESTINATION_EXISTS"));
            }
            fs::rename(&source, &target)?;
            for stamp in stamps {
                let moved = target.join(
                    stamp
                        .path
                        .strip_prefix(&source)
                        .map_err(|_| files::failure("STORAGE_CHANGED"))?,
                );
                fs::set_permissions(
                    moved,
                    fs::Permissions::from_mode(if stamp.info.is_dir() { 0o700 } else { 0o600 }),
                )?;
            }
            increment(&mut result, "moved_directories", 1);
            increment(&mut result, "moved_bytes", size);
        }
    }
    Ok(result)
}
