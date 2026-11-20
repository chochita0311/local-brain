use localbrain_core::backend::{models, search::SearchService, Config};
use localbrain_models::catalog::ModelKey;
use serde_json::json;
use std::{fs, sync::Arc};
#[test]
fn status_and_inspection_never_create_private_or_public_model_state() {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    let search = Arc::new(SearchService::new(config.clone()));
    let service = models::ModelSetupService::new(config.clone(), search);
    let status = service.status().unwrap();
    assert_eq!(status["phase"], "idle");
    assert_eq!(status["installed"], false);
    assert_eq!(status["runtime_missing"], json!([]));
    assert!(!config.data_dir.exists());
    let candidate = root.path().join("public-models");
    let inspected = service.check_folder(&json!(candidate)).unwrap();
    assert_eq!(inspected["state"], "missing");
    assert!(!candidate.exists());
    assert!(!config.data_dir.exists());
}
#[test]
fn folder_paths_reject_private_overlap_git_and_installation_trees() {
    let root = tempfile::tempdir().unwrap();
    let mut config = Config::for_data_dir(root.path().join("data"));
    for path in [&config.data_dir, &config.cache_dir, root.path()] {
        assert!(models::selected_folder(&json!(path), &config).is_err());
    }
    let checkout = root.path().join("checkout");
    fs::create_dir_all(checkout.join(".git")).unwrap();
    assert!(models::selected_folder(&json!(checkout.join("models")), &config).is_err());
    let installed = root.path().join("installed");
    fs::create_dir(&installed).unwrap();
    config.installation_root = Some(installed.clone());
    assert!(models::selected_folder(&json!(installed.join("models")), &config).is_err());
    assert!(models::selected_folder(&json!("relative/path"), &config).is_err());
}
#[test]
fn legacy_and_selected_cache_roots_preserve_registration_semantics() {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    let legacy = config.data_dir.join("qwen3-embedding-0-6b");
    fs::create_dir_all(&legacy).unwrap();
    let selected = root.path().join("selected");
    fs::write(
        legacy.join("model.json"),
        serde_json::to_vec(&json!({"schema":"localbrain.semantic-model/v1","cache_root":selected}))
            .unwrap(),
    )
    .unwrap();
    assert_eq!(
        models::model_root(&config, ModelKey::Embedding).unwrap(),
        localbrain_core::backend::storage::files::resolve(&legacy).unwrap()
    );
    assert_eq!(
        models::embedding_cache_root(&config).unwrap(),
        localbrain_core::backend::storage::files::resolve(&selected).unwrap()
    );
    let canonical = config.data_dir.join("models/qwen3-embedding-0-6b");
    fs::create_dir_all(&canonical).unwrap();
    assert_eq!(
        models::model_root(&config, ModelKey::Embedding).unwrap(),
        localbrain_core::backend::storage::files::resolve(&canonical).unwrap()
    );
    assert_eq!(
        models::embedding_cache_root(&config).unwrap(),
        localbrain_core::backend::storage::files::resolve(&config.hf_hub_cache).unwrap()
    );
    fs::write(canonical.join("model.json"), b"not-json").unwrap();
    assert_eq!(
        models::folder_status(&config).unwrap()["path"],
        serde_json::Value::Null
    );
}
#[test]
fn offline_connect_missing_assets_preserves_existing_registration() {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    let search = Arc::new(SearchService::new(config.clone()));
    let service = models::ModelSetupService::new(config.clone(), search);
    let root = models::model_root(&config, ModelKey::Embedding).unwrap();
    fs::create_dir_all(&root).unwrap();
    use std::os::unix::fs::PermissionsExt;
    fs::set_permissions(&root, fs::Permissions::from_mode(0o700)).unwrap();
    let spec = ModelKey::Embedding.spec();
    fs::write(root.join("owner.json"),serde_json::to_vec(&json!({"owner":"localbrain.semantic-model/v1","model":spec.id,"revision":spec.revision})).unwrap()).unwrap();
    let registration=serde_json::to_vec(&json!({"schema":"localbrain.semantic-model/v1","model_id":spec.id,"resolved_revision":spec.revision,"fingerprint":localbrain_models::catalog::EMBEDDING_FINGERPRINT,"snapshot":spec.snapshot_relative(),"files":[]})).unwrap();
    fs::write(root.join("model.json"), &registration).unwrap();
    fs::set_permissions(root.join("owner.json"), fs::Permissions::from_mode(0o600)).unwrap();
    fs::set_permissions(root.join("model.json"), fs::Permissions::from_mode(0o600)).unwrap();
    let revision = models::registration_revision(&root).unwrap();
    let target = config.data_dir.parent().unwrap().join("public-models");
    assert!(service.use_folder(&json!(target), &revision).is_err());
    assert_eq!(fs::read(root.join("model.json")).unwrap(), registration);
    assert_eq!(service.status().unwrap()["folder_busy"], false);
}
