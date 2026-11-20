//! Preserve the explicit research installer entrypoint using native assets.
use super::{arguments::Arguments, CancellationGuard, CommandResult};
use localbrain_core::backend::{storage::files, Config};
use localbrain_models::{assets, catalog::ModelKey, ModelError, Result};
use serde_json::{json, Value};
use std::{
    fs,
    io::Write,
    os::unix::fs::{MetadataExt, OpenOptionsExt},
    path::{Path, PathBuf},
};

fn failure(code: &str) -> ModelError {
    ModelError::new(code, code)
}
fn require(ok: bool, code: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(failure(code))
    }
}
fn safe_root(config: &Config, root: &Path) -> Result<()> {
    require(
        root.is_absolute() && root.parent().is_some_and(Path::is_dir),
        "INVALID_MODEL_ROOT",
    )?;
    let resolved = files::resolve(root).map_err(|_| failure("INVALID_MODEL_ROOT"))?;
    require(root == resolved, "INVALID_MODEL_ROOT")?;
    if let Some(package) = &config.installation_root {
        require(
            !root.starts_with(package) && !package.starts_with(root),
            "INVALID_MODEL_ROOT",
        )?;
    }
    files::validate_runtime_directory(root, config).map_err(|_| failure("INVALID_MODEL_ROOT"))?;
    Ok(())
}
fn key(model: &str) -> Result<ModelKey> {
    match model {
        "Qwen/Qwen3-4B" => Ok(ModelKey::Generation4b),
        "Qwen/Qwen3-8B" => Ok(ModelKey::Generation8b),
        _ => Err(failure("INVALID_ARGUMENTS")),
    }
}
fn owned_json(path: &Path) -> Result<Value> {
    let info = files::owned_file(path).map_err(|_| failure("UNOWNED_OUTPUT"))?;
    require(info.mode() & 0o077 == 0, "UNOWNED_OUTPUT")?;
    let text = fs::read_to_string(path)?;
    localbrain_core::backend::json::decode(&text).map_err(|_| failure("MODEL_INSTALL_FAILED"))
}
fn check_registration(root: &Path, selected: Option<ModelKey>) -> Result<ModelKey> {
    let info = fs::metadata(root)?;
    require(
        info.is_dir()
            && !root.is_symlink()
            && info.uid() == unsafe { libc::geteuid() }
            && info.mode() & 0o077 == 0,
        "UNOWNED_MODEL",
    )?;
    let marker = owned_json(&root.join("owner.json"))?;
    let owned =
        key(marker["model"].as_str().unwrap_or("")).map_err(|_| failure("UNOWNED_MODEL"))?;
    require(
        marker
            == json!({"owner":"localbrain.work-context-model.v1","model":owned.spec().id,"revision":owned.spec().revision}),
        "UNOWNED_MODEL",
    )?;
    require(
        selected.is_none_or(|selected| selected == owned),
        "MODEL_MISMATCH",
    )?;
    for entry in fs::read_dir(root)? {
        require(
            matches!(
                entry?.file_name().to_str(),
                Some("owner.json" | "install.lock" | "cache" | "model.json" | "model.json.pending")
            ),
            "UNOWNED_MODEL",
        )?;
    }
    Ok(owned)
}
fn admit_transfer(config: &Config, path: Option<&Path>) -> Result<()> {
    let Some(path) = path else { return Ok(()) };
    safe_root(config, path)?;
    let info = fs::metadata(path)?;
    require(
        info.is_dir()
            && info.uid() == unsafe { libc::geteuid() }
            && info.mode() & 0o077 == 0
            && fs::read_dir(path)?.next().is_none(),
        "UNOWNED_TRANSFER_CACHE",
    )?;
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path.join("owner.json"))?;
    file.write_all(b"{\n  \"owner\": \"localbrain.work-context-transfer.v1\"\n}\n")?;
    file.sync_all()?;
    Ok(())
}
fn arguments(raw: &[String]) -> localbrain_core::backend::Result<Arguments> {
    // argparse accepted unambiguous long-option prefixes. Preserve them for
    // this compatibility entrypoint without widening other native commands.
    let mut normalized = Vec::new();
    let mut positional = false;
    for item in raw {
        let value = if !positional && item.starts_with("--") && item != "--" {
            let (name, value) = item
                .split_once('=')
                .map(|(name, value)| (name, Some(value)))
                .unwrap_or((item, None));
            let choices = ["--root", "--verify", "--model", "--xet-cache"]
                .into_iter()
                .filter(|choice| choice.starts_with(name))
                .collect::<Vec<_>>();
            if choices.len() == 1 {
                format!(
                    "{}{}",
                    choices[0],
                    value.map(|value| format!("={value}")).unwrap_or_default()
                )
            } else {
                item.clone()
            }
        } else {
            item.clone()
        };
        positional |= item == "--";
        normalized.push(value);
    }
    for (index, item) in normalized.iter().enumerate() {
        if ["--root", "--model", "--xet-cache"].contains(&item.as_str())
            && normalized.get(index + 1).is_some_and(|value| {
                value.starts_with('-') && !super::arguments::negative_number(value)
            })
        {
            return Err(super::arguments::invalid("a flag value is required"));
        }
    }
    let args = Arguments::parse(
        &normalized,
        &["--verify"],
        &["--root", "--model", "--xet-cache"],
    )?;
    args.count(0, 0)?;
    if args.value("--root").is_none()
        || args
            .value("--model")
            .is_some_and(|value| key(value).is_err())
    {
        return Err(super::arguments::invalid("invalid registration arguments"));
    }
    Ok(args)
}
pub(super) fn run(config: &Config, raw: &[String]) -> CommandResult {
    let args = match arguments(raw) {
        Ok(args) => args,
        Err(_) => {
            println!("INVALID_ARGUMENTS");
            return Ok(2);
        }
    };
    let verify = args.flag("--verify");
    let cancel = CancellationGuard::new()?;
    println!(
        "{}",
        if verify {
            "MODEL_VERIFYING"
        } else {
            "MODEL_INSTALLING"
        }
    );
    let result = (|| -> Result<()> {
        let root = PathBuf::from(args.value("--root").unwrap());
        safe_root(config, &root)?;
        let selected = args.value("--model").map(key).transpose()?;
        let cache =
            files::resolve(&config.hf_hub_cache).map_err(|_| failure("INVALID_MODEL_ROOT"))?;
        if verify {
            let selected = check_registration(&root, selected)?;
            owned_json(&root.join("model.json"))?;
            assets::verify_manifest(&root.join("model.json"), &cache, selected, &cancel.token)?;
        } else {
            let selected = selected.unwrap_or(ModelKey::Generation4b);
            if root.exists() {
                check_registration(&root, Some(selected))?;
            }
            let transfer = args.value("--xet-cache").map(PathBuf::from);
            assets::install_with_transfer_admission(
                &assets::InstallOptions {
                    model: selected,
                    registration_root: root,
                    cache_root: cache,
                    offline: false,
                    replace_cache: false,
                    expected_registration_revision: None,
                },
                &cancel.token,
                |_| {},
                || admit_transfer(config, transfer.as_deref()),
            )?;
        }
        Ok(())
    })();
    if cancel.interrupted() {
        println!("MODEL_INTERRUPTED");
        return Ok(130);
    }
    match result {
        Ok(()) => {
            println!(
                "{}",
                if verify {
                    "MODEL_VERIFIED"
                } else {
                    "MODEL_INSTALLED"
                }
            );
            Ok(0)
        }
        Err(error) => {
            let code = if matches!(
                error.code.as_str(),
                "INVALID_ARGUMENTS"
                    | "INVALID_MODEL_ROOT"
                    | "UNOWNED_MODEL"
                    | "UNOWNED_OUTPUT"
                    | "MODEL_MISMATCH"
                    | "INVALID_MODEL"
                    | "MODEL_ASSETS_CHANGED"
                    | "MODEL_BUSY"
                    | "UNOWNED_TRANSFER_CACHE"
            ) {
                error.code.as_str()
            } else {
                "MODEL_INSTALL_FAILED"
            };
            println!("{code}");
            Ok(2)
        }
    }
}
