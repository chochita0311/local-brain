use localbrain_core::backend::{
    auto_work::{self, PreviewOptions, PreviewSupervisor},
    db, BackendError, Config, Result,
};
use serde_json::Value;
use std::{
    fs,
    os::{
        fd::AsRawFd,
        unix::fs::{symlink, PermissionsExt},
    },
    sync::atomic::{AtomicUsize, Ordering},
};
struct Local {
    calls: AtomicUsize,
    fail_text: bool,
}
impl PreviewSupervisor for Local {
    fn supervise(&self, operation: &str, args: &Value) -> Result<Value> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if self.fail_text && operation == "text" {
            return Err(BackendError::invalid("WORKER_FAILED", "WORKER_FAILED"));
        }
        auto_work::run_preview_operation(operation, args)
    }
}
fn setup() -> (tempfile::TempDir, Config, chrono::DateTime<chrono::Utc>) {
    let root = tempfile::tempdir().unwrap();
    let canonical = fs::canonicalize(root.path()).unwrap();
    let config = Config::for_data_dir(canonical.join("data"));
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    connection.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Synthetic','/synthetic'); INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count) VALUES (1,1,'a','/synthetic/a','Alpha',1); INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,occurred_at,source_line) VALUES ('a',1,1,'message','user','Fix parser. Just an observation.','2026-11-01T09:00:00Z',1); INSERT INTO session_reference_scans(session_id,source_fingerprint,extractor_version,status,scanned_at,updated_at) VALUES (1,'0000000000000000000000000000000000000000000000000000000000000000','synthetic','ok','2026-11-01','2026-11-01');").unwrap();
    let at = chrono::DateTime::parse_from_rfc3339("2026-11-18T00:00:00Z")
        .unwrap()
        .with_timezone(&chrono::Utc);
    (root, config, at)
}
fn local() -> Local {
    Local {
        calls: AtomicUsize::new(0),
        fail_text: false,
    }
}
#[test]
fn invalid_duplicate_and_oversize_previews_are_preserved_before_any_worker() {
    let (_root, config, at) = setup();
    assert_eq!(
        auto_work::preview_page(&config, &PreviewOptions::default(), Some(at))["state"],
        "missing"
    );
    assert!(!config.cache_dir.exists());
    auto_work::prepare_preview_with_supervisor(&config, Some(at), &local()).unwrap();
    let target = config.cache_dir.join("auto-work-preview/current.json");
    for raw in [
        b"not JSON".to_vec(),
        b"{\"version\":1,\"version\":1}".to_vec(),
        vec![b' '; 10 * 1024 * 1024 + 1],
    ] {
        fs::write(&target, &raw).unwrap();
        let worker = local();
        assert_eq!(
            auto_work::preview_page(&config, &PreviewOptions::default(), Some(at))["state"],
            "error"
        );
        assert!(auto_work::prepare_preview_with_supervisor(&config, Some(at), &worker).is_err());
        assert_eq!(worker.calls.load(Ordering::SeqCst), 0);
        assert_eq!(fs::read(&target).unwrap(), raw);
    }
}
#[test]
fn failed_refresh_busy_lock_and_expiry_keep_authority_boundaries() {
    let (_root, config, at) = setup();
    auto_work::prepare_preview_with_supervisor(&config, Some(at), &local()).unwrap();
    let folder = config.cache_dir.join("auto-work-preview");
    let target = folder.join("current.json");
    let before = fs::read(&target).unwrap();
    let failed = Local {
        calls: AtomicUsize::new(0),
        fail_text: true,
    };
    assert!(auto_work::prepare_preview_with_supervisor(&config, Some(at), &failed).is_err());
    assert_eq!(before, fs::read(&target).unwrap());
    assert_eq!(fs::read_dir(&folder).unwrap().count(), 2);
    let lock = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .open(folder.join("preview.lock"))
        .unwrap();
    assert_eq!(
        unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) },
        0
    );
    let worker = local();
    assert_eq!(
        auto_work::prepare_preview_with_supervisor(&config, Some(at), &worker)
            .unwrap_err()
            .code,
        "PREVIEW_BUSY"
    );
    assert_eq!(worker.calls.load(Ordering::SeqCst), 0);
    let expired = at + chrono::Duration::days(8);
    assert_eq!(
        auto_work::preview_page(&config, &PreviewOptions::default(), Some(expired))["state"],
        "expired"
    );
    assert!(target.exists());
    drop(lock);
    fs::write(folder.join("unrelated"), "preserve").unwrap();
    assert_eq!(
        auto_work::preview_page(&config, &PreviewOptions::default(), Some(expired))["state"],
        "expired"
    );
    assert!(!target.exists());
    assert_eq!(
        fs::read_to_string(folder.join("unrelated")).unwrap(),
        "preserve"
    );
}
#[test]
fn source_edit_and_eligibility_revocation_withhold_old_wording() {
    let (_root, config, at) = setup();
    auto_work::prepare_preview_with_supervisor(&config, Some(at), &local()).unwrap();
    let ready = auto_work::preview_page(&config, &PreviewOptions::default(), Some(at));
    assert_eq!(ready["state"], "ready");
    assert_eq!(ready["evidence"][0]["wording"], "Fix parser.");
    let connection = db::connect(&config).unwrap();
    connection
        .execute(
            "UPDATE activity_events SET text='Fix parser! Just an observation.' WHERE id='a'",
            [],
        )
        .unwrap();
    let stale = auto_work::preview_page(&config, &PreviewOptions::default(), Some(at));
    assert_eq!(stale["state"], "stale");
    assert!(stale.get("evidence").is_none());
    connection
        .execute(
            "UPDATE sessions SET index_policy='metadata_only' WHERE id=1",
            [],
        )
        .unwrap();
    connection
        .execute(
            "UPDATE activity_events SET text=CAST(X'FF' AS TEXT) WHERE id='a'",
            [],
        )
        .unwrap();
    let payload: Value = serde_json::from_slice(
        &fs::read(config.cache_dir.join("auto-work-preview/current.json")).unwrap(),
    )
    .unwrap();
    assert_eq!(
        auto_work::reconstruction::load_snapshots(&config.database_path, &payload["manifest"])
            .unwrap_err()
            .code,
        "INELIGIBLE_SOURCE"
    );
}
#[test]
fn symlinks_hardlinks_permissions_and_legacy_owner_hooks_refuse_adoption() {
    let (_root, config, at) = setup();
    auto_work::prepare_preview_with_supervisor(&config, Some(at), &local()).unwrap();
    let folder = config.cache_dir.join("auto-work-preview");
    let target = folder.join("current.json");
    let owners = auto_work::cache::legacy_cache_owners();
    assert!(owners["auto-work-preview"](&folder).unwrap());
    fs::write(folder.join("unknown"), "preserve").unwrap();
    assert!(!owners["auto-work-preview"](&folder).unwrap());
    let result = auto_work::cache::maintain_cache(
        &config,
        &config.cache_dir,
        true,
        Some(at + chrono::Duration::days(8)),
    )
    .unwrap();
    assert_eq!(result["preserved_directories"], 1);
    assert!(target.exists());
    fs::remove_file(folder.join("unknown")).unwrap();
    fs::set_permissions(&target, fs::Permissions::from_mode(0o644)).unwrap();
    assert_eq!(
        auto_work::preview_page(&config, &PreviewOptions::default(), Some(at))["state"],
        "error"
    );
    fs::set_permissions(&target, fs::Permissions::from_mode(0o600)).unwrap();
    let linked = folder.join("linked");
    fs::hard_link(&target, &linked).unwrap();
    assert_eq!(
        auto_work::preview_page(&config, &PreviewOptions::default(), Some(at))["state"],
        "error"
    );
    fs::remove_file(linked).unwrap();
    let retained = folder.join("retained");
    fs::rename(&target, &retained).unwrap();
    symlink(&retained, &target).unwrap();
    assert_eq!(
        auto_work::preview_page(&config, &PreviewOptions::default(), Some(at))["state"],
        "error"
    );
    let worker = local();
    assert!(auto_work::prepare_preview_with_supervisor(&config, Some(at), &worker).is_err());
    assert_eq!(worker.calls.load(Ordering::SeqCst), 0);
    assert!(retained.exists());
}
