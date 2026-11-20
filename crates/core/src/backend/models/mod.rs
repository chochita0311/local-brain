//! Explicit pinned model setup. Discovery is read-only and never opens weights.
mod setup;
use crate::backend::{
    sources::registry::{readable_directory, PythonText},
    storage::files,
    BackendError, Config, Result,
};
use localbrain_models::{assets, catalog::ModelKey, Cancellation};
use serde_json::{json, Value};
pub use setup::{download_worker, ModelSetupService};
use std::{
    fs,
    path::{Path, PathBuf},
};
pub fn failure(error: localbrain_models::ModelError) -> BackendError {
    BackendError::new(503, &error.code, &error.code)
        .with_details(json!({"code":error.code,"message":error.detail}))
}
pub fn hub_cache_root(config: &Config) -> Result<PathBuf> {
    files::resolve(&files::expand(&config.hf_hub_cache, config))
}
pub fn model_root(config: &Config, key: ModelKey) -> Result<PathBuf> {
    Ok(assets::model_root(
        key,
        &files::resolve(&files::expand(&config.data_dir, config))?,
    ))
}
pub fn registration_revision(root: &Path) -> Result<String> {
    match fs::read(root.join("model.json")) {
        Ok(bytes) => Ok(assets::sha256(&bytes)),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(assets::sha256(b"")),
        Err(error) => Err(error.into()),
    }
}
pub fn embedding_cache_root(config: &Config) -> Result<PathBuf> {
    let path = model_root(config, ModelKey::Embedding)?.join("model.json");
    if !path.exists() {
        return hub_cache_root(config);
    }
    let value: Value = serde_json::from_slice(&fs::read(&path)?)?;
    if !value.is_object() {
        return Err(BackendError::invalid(
            "INVALID_MODEL",
            "Invalid model registration",
        ));
    }
    if value["schema"] == "foundry.semantic-model/v1" {
        let relative = value["snapshot"]
            .as_str()
            .filter(|value| !value.is_empty())
            .ok_or_else(|| BackendError::invalid("INVALID_MODEL", "Invalid model registration"))?;
        let root = path
            .parent()
            .and_then(Path::parent)
            .and_then(Path::parent)
            .ok_or_else(|| BackendError::invalid("INVALID_MODEL", "Invalid model registration"))?;
        let snapshot = files::resolve(&root.join(relative))?;
        return snapshot
            .parent()
            .map(Path::to_owned)
            .ok_or_else(|| BackendError::invalid("INVALID_MODEL", "Invalid model registration"));
    }
    match value.get("cache_root") {
        None | Some(Value::Null) => hub_cache_root(config),
        Some(value) => {
            let root = value
                .as_str()
                .filter(|root| {
                    !root.is_empty()
                        && Path::new(root).is_absolute()
                        && !root.chars().any(|ch| (ch as u32) < 32)
                })
                .ok_or_else(|| BackendError::invalid("INVALID_MODEL", "INVALID_MODEL"))?;
            files::resolve(Path::new(root))
        }
    }
}
fn display(path: &Path, config: &Config) -> String {
    match path.strip_prefix(&config.home_dir) {
        Ok(path) if path.as_os_str().is_empty() => "~".into(),
        Ok(path) => format!("~/{}", path.display()),
        Err(_) => path.to_string_lossy().into_owned(),
    }
}
pub fn folder_status(config: &Config) -> Result<Value> {
    let recommended = hub_cache_root(config)?;
    let result = (|| {
        let path = embedding_cache_root(config)?;
        let revision = registration_revision(&model_root(config, ModelKey::Embedding)?)?;
        Ok::<_, BackendError>(
            json!({"path":path,"display_path":display(&path,config),"recommended_path":display(&recommended,config),"revision":revision,"error":null}),
        )
    })();
    Ok(result.unwrap_or_else(|_|json!({"path":null,"display_path":"","recommended_path":display(&recommended,config),"revision":null,"error":"모델 저장 위치를 확인하지 못했습니다. 앱을 다시 열어 확인해 주세요."})))
}
pub fn selected_folder(value: &Value, config: &Config) -> Result<PathBuf> {
    let value = value
        .as_str()
        .filter(|value| {
            !value.py_trim().is_empty()
                && value.chars().count() <= 4096
                && !value.chars().any(|ch| (ch as u32) < 32)
        })
        .ok_or_else(|| BackendError::conflict("모델 파일을 보관할 폴더 경로를 입력해 주세요."))?;
    let candidate = files::expand(Path::new(value.py_trim()), config);
    if !candidate.is_absolute() {
        return Err(BackendError::conflict(
            "폴더 경로와 접근 권한을 확인해 주세요.",
        ));
    }
    let candidate = files::resolve(&candidate)
        .map_err(|_| BackendError::conflict("폴더 경로와 접근 권한을 확인해 주세요."))?;
    let in_installation = if let Some(root) = &config.installation_root {
        candidate.starts_with(files::resolve(root)?)
    } else {
        false
    };
    if in_installation
        || candidate
            .ancestors()
            .any(|parent| parent.join(".git").exists())
    {
        return Err(BackendError::conflict(
            "앱 설치 폴더와 소스 코드 저장소 밖의 모델 전용 폴더를 선택해 주세요.",
        ));
    }
    for root in [&config.data_dir, &config.cache_dir] {
        if files::overlap(&candidate, &files::resolve(root)?) {
            return Err(BackendError::conflict(
                "앱 데이터·검색 캐시와 겹치지 않는 모델 전용 폴더를 선택해 주세요.",
            ));
        }
    }
    let parent = candidate
        .ancestors()
        .find(|parent| parent.exists())
        .ok_or_else(|| BackendError::conflict("폴더 경로와 접근 권한을 확인해 주세요."))?;
    if !readable_directory(parent) {
        return Err(BackendError::conflict(
            "폴더 경로와 접근 권한을 확인해 주세요.",
        ));
    }
    Ok(candidate)
}
pub fn inspect_folder(value: &Value, config: &Config) -> Result<Value> {
    let candidate = selected_folder(value, config)?;
    let revision = registration_revision(&model_root(config, ModelKey::Embedding)?)?;
    let spec = ModelKey::Embedding.spec();
    let snapshot = candidate.join(spec.snapshot_relative());
    let complete = spec
        .assets()
        .iter()
        .all(|name| snapshot.join(name).is_file());
    let state = if !complete {
        "missing"
    } else {
        match assets::verify_cached(
            ModelKey::Embedding,
            &candidate,
            &localbrain_models::cancellation(),
        ) {
            Ok(_) => "valid",
            Err(error) if error.code == "MODEL_IO" => "unreadable",
            Err(_) => "invalid",
        }
    };
    Ok(json!({"path":candidate,"state":state,"revision":revision}))
}
pub fn generation_models(config: &Config) -> Result<Value> {
    Ok(json!(assets::model_status(&config.data_dir,&config.hf_hub_cache).into_iter().filter(|model|model.key!=ModelKey::Embedding).map(|model|json!({"key":model.key,"name":model.model_id.split('/').next_back().unwrap_or(""),"registered":model.registered,"cached":model.cached,"available":model.registered||model.cached})).collect::<Vec<_>>()))
}
pub fn model_status(config: &Config) -> Result<Value> {
    Ok(
        json!({"runtime":"READY","missing_modules":[],"models":assets::model_status(&config.data_dir,&config.hf_hub_cache).iter().map(|model|json!({"key":model.key,"model_id":model.model_id,"purpose":model.purpose,"state":model.state})).collect::<Vec<_>>()}),
    )
}
pub fn verify_model(
    config: &Config,
    key: ModelKey,
    cancel: &Cancellation,
) -> Result<assets::VerifiedModel> {
    assets::verify_model(
        &model_root(config, key)?,
        &hub_cache_root(config)?,
        key,
        cancel,
    )
    .map_err(failure)
}
pub fn install_model(
    config: &Config,
    key: ModelKey,
    offline: bool,
    cache: Option<&Path>,
    revision: Option<String>,
    cancel: &Cancellation,
    progress: impl FnMut(assets::InstallProgress),
) -> Result<assets::VerifiedModel> {
    let selected = cache
        .map(|cache| selected_folder(&json!(cache), config))
        .transpose()?;
    let default_cache = hub_cache_root(config)?;
    files::private_directory(&config.data_dir, config)?;
    let root = model_root(config, key)?;
    files::private_directory(root.parent().unwrap(), config)?;
    assets::install(
        &assets::InstallOptions {
            model: key,
            registration_root: root,
            cache_root: selected.as_deref().unwrap_or(&default_cache).to_owned(),
            offline,
            replace_cache: cache.is_some(),
            expected_registration_revision: revision,
        },
        cancel,
        progress,
    )
    .map_err(failure)
}
