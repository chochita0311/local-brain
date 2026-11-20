use localbrain_core::backend::{
    auto_work::{self, SimulationEncoder, SimulationOptions},
    db, models, Config, Result,
};
use localbrain_models::{Cancellation, ModelError};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    os::unix::fs::{symlink, PermissionsExt},
    sync::{
        atomic::{AtomicUsize, Ordering},
        Mutex,
    },
    time::{Duration, Instant},
};
struct Encoder {
    calls: AtomicUsize,
    fail_after: Option<usize>,
    mutate: Mutex<Option<Box<dyn FnOnce() + Send>>>,
}
impl Default for Encoder {
    fn default() -> Self {
        Self {
            calls: AtomicUsize::new(0),
            fail_after: None,
            mutate: Mutex::new(None),
        }
    }
}
impl SimulationEncoder for Encoder {
    fn contract(&self) -> Value {
        json!({"model_id":"synthetic-only","dimension":3,"version":1})
    }
    fn encode(&self, texts: &[String], cancel: &Cancellation) -> Result<Vec<Vec<f64>>> {
        let call = self.calls.fetch_add(1, Ordering::SeqCst);
        if self.fail_after.is_some_and(|limit| call >= limit) {
            cancel.store(true, Ordering::Release);
            return Err(models::failure(ModelError::new(
                "MODEL_INFERENCE_FAILED",
                "synthetic error while cancellation is pending",
            )));
        }
        if let Some(mutate) = self.mutate.lock().unwrap().take() {
            mutate();
        }
        Ok(texts
            .iter()
            .map(|text| vec![1.0, text.len() as f64 / 100.0, 0.2])
            .collect())
    }
}
fn setup() -> (tempfile::TempDir, Config, std::path::PathBuf) {
    let root = tempfile::tempdir().unwrap();
    let canonical = fs::canonicalize(root.path()).unwrap();
    let config = Config::for_data_dir(canonical.join("data"));
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    connection.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Synthetic','/synthetic'); INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (1,1,'a','/synthetic/a','Alpha'),(2,1,'b','/synthetic/b','Beta'),(3,1,'c','/synthetic/c','Gamma'); INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,occurred_at,source_line) VALUES ('a',1,1,'message','user','Alpha body','2026-11-01T09:00:00Z',1),('b',2,1,'message','assistant','Beta body',NULL,1),('c',3,1,'message','user','Gamma body','2026-11-03T09:00:00Z',1);").unwrap();
    drop(connection);
    fs::create_dir(&config.cache_dir).unwrap();
    fs::set_permissions(&config.cache_dir, fs::Permissions::from_mode(0o700)).unwrap();
    let output = config.cache_dir.join("session-simulation");
    (root, config, output)
}
#[test]
fn simulation_replay_corrupt_cache_and_parameter_change_preserve_sources() {
    let (_root, config, output) = setup();
    let before = fs::read(&config.database_path).unwrap();
    let first = auto_work::simulate(
        &config,
        &output,
        &Encoder::default(),
        &SimulationOptions::default(),
    )
    .unwrap();
    assert_eq!(first["cache"], json!({"reused":0,"encoded":3,"total":3}));
    assert_eq!(
        first["grouping"]["engine"]["implementation"],
        "localbrain-rust"
    );
    let replay = Encoder::default();
    let second =
        auto_work::simulate(&config, &output, &replay, &SimulationOptions::default()).unwrap();
    assert_eq!(replay.calls.load(Ordering::SeqCst), 0);
    assert_eq!(second["cache"]["reused"], 3);
    assert_eq!(second["comparison"]["same_grouping"], true);
    assert_eq!(before, fs::read(&config.database_path).unwrap());
    let cache = rusqlite::Connection::open(output.join("state.sqlite3")).unwrap();
    cache.execute("UPDATE embeddings SET vector=zeroblob(12) WHERE input_hash=(SELECT input_hash FROM embeddings LIMIT 1)",[]).unwrap();
    drop(cache);
    let recovered = auto_work::simulate(
        &config,
        &output,
        &Encoder::default(),
        &SimulationOptions::default(),
    )
    .unwrap();
    assert_eq!(recovered["cache"]["encoded"], 1);
    let mut changed = SimulationOptions::default();
    changed.parameters["area_resolution"] = json!(1.2);
    let change = Encoder::default();
    let report = auto_work::simulate(&config, &output, &change, &changed).unwrap();
    assert_eq!(change.calls.load(Ordering::SeqCst), 0);
    assert_eq!(report["comparison"]["same_configuration"], false);
    assert_eq!(report["comparison"]["same_input"], true);
    assert_eq!(report["quality"], "unassessed");
    assert_eq!(report["lineage_status"], "not_inferred");
    let view = auto_work::affinity_page(&config, &BTreeMap::new(), None);
    assert_eq!(view["state"], "current", "{view}");
}
#[test]
fn interrupted_batches_resume_and_source_change_keeps_previous_report() {
    let (_root, config, output) = setup();
    let mut options = SimulationOptions {
        batch_size: 1,
        ..SimulationOptions::default()
    };
    let interrupted = Encoder {
        fail_after: Some(1),
        ..Encoder::default()
    };
    assert_eq!(
        auto_work::simulate(&config, &output, &interrupted, &options)
            .unwrap_err()
            .code,
        "SIMULATION_INTERRUPTED"
    );
    let progress_path = output.join("progress.json");
    let mut progress: Value = serde_json::from_slice(&fs::read(&progress_path).unwrap()).unwrap();
    assert_eq!(progress["state"], "interrupted");
    assert_eq!(progress["error_code"], "SIMULATION_INTERRUPTED");
    progress["state"] = "failed".into();
    progress["error_code"] = "MODEL_CANCELLED".into();
    let legacy_progress = serde_json::to_vec(&progress).unwrap();
    fs::write(&progress_path, &legacy_progress).unwrap();
    let status = auto_work::simulation_status(&config, &output, None).unwrap();
    assert_eq!(status["state"], "interrupted");
    assert_eq!(status["error_code"], "SIMULATION_INTERRUPTED");
    assert_eq!(fs::read(&progress_path).unwrap(), legacy_progress);
    options.cancel.store(false, Ordering::Release);
    let report = auto_work::simulate(&config, &output, &Encoder::default(), &options).unwrap();
    assert_eq!(report["cache"], json!({"reused":1,"encoded":2,"total":3}));
    let previous = fs::read(output.join("report.json")).unwrap();
    let database = config.database_path.clone();
    let encoder = Encoder {
        mutate: Mutex::new(Some(Box::new(move || {
            rusqlite::Connection::open(database)
                .unwrap()
                .execute(
                    "UPDATE activity_events SET text='AlphA body' WHERE id='a'",
                    [],
                )
                .unwrap();
        }))),
        ..Encoder::default()
    };
    options.force = true;
    assert_eq!(
        auto_work::simulate(&config, &output, &encoder, &options)
            .unwrap_err()
            .code,
        "SOURCE_CHANGED"
    );
    assert_eq!(previous, fs::read(output.join("report.json")).unwrap());
    let view = auto_work::affinity_page(&config, &BTreeMap::new(), None);
    assert_eq!(view["state"], "stale");
    assert_eq!(view["delta"]["changed"], 1);
    assert!(view.get("nodes").is_none());
}
#[test]
fn owned_inventory_purge_expiry_and_unknown_files_follow_the_existing_owner() {
    let (_root, config, output) = setup();
    let cancel = localbrain_models::cancellation();
    let prepared = auto_work::prepare_inventory(&config, &output, 1800, None, &cancel).unwrap();
    assert_eq!(prepared["state"], "prepared");
    assert_eq!(
        auto_work::simulation_status(&config, &output, None).unwrap()["state"],
        "prepared"
    );
    fs::write(output.join("unknown"), "preserve").unwrap();
    assert!(auto_work::purge(&config, &output, None).is_err());
    assert_eq!(
        fs::read_to_string(output.join("unknown")).unwrap(),
        "preserve"
    );
    fs::remove_file(output.join("unknown")).unwrap();
    let mut marker: Value =
        serde_json::from_slice(&fs::read(output.join("owner.json")).unwrap()).unwrap();
    marker["expires_at"] = "2000-01-01T00:00:00+00:00".into();
    fs::write(output.join("owner.json"), marker.to_string()).unwrap();
    let before = fs::read(output.join("owner.json")).unwrap();
    assert_eq!(
        auto_work::affinity_page(&config, &BTreeMap::new(), None)["state"],
        "expired"
    );
    assert_eq!(before, fs::read(output.join("owner.json")).unwrap());
    auto_work::purge(&config, &output, None).unwrap();
    let names = fs::read_dir(&output)
        .unwrap()
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(
        names,
        ["owner.json".to_owned(), "writer.lock".to_owned()]
            .into_iter()
            .collect()
    );
}
#[test]
fn cancelled_inventory_rolls_back_and_keeps_the_previous_report() {
    let (_root, config, output) = setup();
    let report = auto_work::simulate(
        &config,
        &output,
        &Encoder::default(),
        &SimulationOptions::default(),
    )
    .unwrap();
    let report_path = output.join("report.json");
    let previous_bytes = fs::read(&report_path).unwrap();
    let snapshot_path = output.join("state.sqlite3");
    let cached_manifest = || {
        rusqlite::Connection::open(&snapshot_path)
            .unwrap()
            .query_row("SELECT value FROM meta WHERE key='manifest'", [], |row| {
                row.get::<_, String>(0)
            })
            .unwrap()
    };
    let previous_manifest = cached_manifest();

    // Keep the source reader behind a real SQLite lock while the inventory
    // transaction has begun. This also covers cancellation with no new rows read.
    let lock = rusqlite::Connection::open(&config.database_path).unwrap();
    lock.execute_batch("PRAGMA journal_mode=DELETE; BEGIN EXCLUSIVE")
        .unwrap();
    let progress_path = output.join("progress.json");
    let cancel = localbrain_models::cancellation();
    std::thread::scope(|scope| {
        let job =
            scope.spawn(|| auto_work::prepare_inventory(&config, &output, 128, None, &cancel));
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            let progress: Value =
                serde_json::from_slice(&fs::read(&progress_path).unwrap()).unwrap();
            if progress["state"] == "inventory" {
                break;
            }
            assert!(!job.is_finished() && Instant::now() < deadline);
            std::thread::sleep(Duration::from_millis(2));
        }
        cancel.store(true, Ordering::Release);
        lock.execute_batch("ROLLBACK").unwrap();
        assert_eq!(
            job.join().unwrap().unwrap_err().code,
            "SIMULATION_INTERRUPTED"
        );
    });
    let status = auto_work::simulation_status(&config, &output, None).unwrap();
    assert_eq!(status["state"], "interrupted");
    assert_eq!(status["error_code"], "SIMULATION_INTERRUPTED");
    assert_eq!(cached_manifest(), previous_manifest);
    assert_eq!(fs::read(&report_path).unwrap(), previous_bytes);
    cancel.store(false, Ordering::Release);
    let retry = auto_work::prepare_inventory(&config, &output, 1800, None, &cancel).unwrap();
    assert_eq!(retry["state"], "prepared");
    assert_eq!(retry["manifest"], report["manifest"]);
}

#[test]
fn passive_missing_refusal_paths_and_vector_checks_never_create_or_adopt() {
    let (_root, config, output) = setup();
    assert_eq!(
        auto_work::affinity_page(&config, &BTreeMap::new(), None)["state"],
        "missing"
    );
    assert!(!output.exists());
    assert!(auto_work::vector_bytes(&[0.0, 0.0, 0.0], 3).is_err());
    assert!(auto_work::vector_bytes(&[f64::NAN, 1.0, 2.0], 3).is_err());
    assert!(auto_work::load_vector(&[0; 11], 3).is_err());
    fs::create_dir(&output).unwrap();
    fs::set_permissions(&output, fs::Permissions::from_mode(0o700)).unwrap();
    assert_eq!(
        auto_work::affinity_page(&config, &BTreeMap::new(), None)["state"],
        "invalid"
    );
    let cancel = localbrain_models::cancellation();
    assert!(auto_work::prepare_inventory(&config, &output, 1800, None, &cancel).is_err());
    fs::remove_dir(&output).unwrap();
    let alias = config.cache_dir.join("alias");
    fs::create_dir(&alias).unwrap();
    symlink(&alias, &output).unwrap();
    assert!(auto_work::prepare_inventory(&config, &output, 1800, None, &cancel).is_err());
    assert!(fs::read_dir(alias).unwrap().next().is_none());
}
