use localbrain_models::{
    assets::{install, model_status, InstallOptions},
    cancellation,
    catalog::ModelKey,
};
use std::sync::atomic::Ordering;

#[test]
fn discovery_does_not_parse_fake_metadata_or_weight_files() {
    let directory = tempfile::tempdir().unwrap();
    let data = directory.path().join("data");
    let cache = directory.path().join("cache");
    let spec = ModelKey::Embedding.spec();
    let registration = data.join("models").join(spec.slug);
    std::fs::create_dir_all(&registration).unwrap();
    std::fs::write(registration.join("model.json"), b"unparseable metadata").unwrap();
    let snapshot = cache.join(spec.snapshot_relative());
    for name in spec.assets() {
        let path = snapshot.join(name);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, b"synthetic invalid assets").unwrap();
    }
    let status = model_status(&data, &cache);
    assert_eq!(status[0].state, "PRESENT_UNVERIFIED");
    assert!(status[0].registered && status[0].cached);
    assert!(status[1..].iter().all(|model| model.experiment_suspended));
}

#[test]
fn offline_missing_assets_refuse_without_a_download() {
    let directory = tempfile::tempdir().unwrap();
    let options = InstallOptions {
        model: ModelKey::Embedding,
        registration_root: directory.path().join("registration"),
        cache_root: directory.path().join("cache"),
        offline: true,
        replace_cache: false,
        expected_registration_revision: None,
    };
    let mut phases = Vec::new();
    let error = install(&options, &cancellation(), |event| phases.push(event.phase)).unwrap_err();
    assert_eq!(error.code, "MODEL_NOT_CACHED");
    assert!(phases.is_empty());
    assert!(!options.registration_root.join("model.json").exists());
}

#[test]
fn already_cancelled_install_does_not_create_directories() {
    let directory = tempfile::tempdir().unwrap();
    let options = InstallOptions {
        model: ModelKey::Generation4b,
        registration_root: directory.path().join("registration"),
        cache_root: directory.path().join("cache"),
        offline: false,
        replace_cache: false,
        expected_registration_revision: None,
    };
    let cancel = cancellation();
    cancel.store(true, Ordering::Release);
    assert_eq!(
        install(&options, &cancel, |_| panic!(
            "no progress after cancellation"
        ))
        .unwrap_err()
        .code,
        "MODEL_CANCELLED"
    );
    assert!(!options.registration_root.exists());
    assert!(!options.cache_root.exists());
}

#[test]
fn catalog_rejects_unpinned_repository_revision_and_urls() {
    assert!(ModelKey::parse("Qwen/Qwen3-0.6B").is_err());
    assert!(ModelKey::parse("https://example.invalid/model").is_err());
    assert!(ModelKey::parse("embedding@main").is_err());
    assert_eq!(
        ModelKey::parse("Qwen/Qwen3-8B").unwrap(),
        ModelKey::Generation8b
    );
}

#[test]
fn cached_verification_never_creates_or_registers_missing_assets() {
    let directory = tempfile::tempdir().unwrap();
    let cache = directory.path().join("missing-cache");
    let error =
        localbrain_models::assets::verify_cached(ModelKey::Embedding, &cache, &cancellation())
            .unwrap_err();
    assert_eq!(error.code, "MODEL_NOT_CACHED");
    assert!(!cache.exists());
    assert!(std::fs::read_dir(directory.path())
        .unwrap()
        .next()
        .is_none());
}
