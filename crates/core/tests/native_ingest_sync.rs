use localbrain_core::backend::{
    db,
    ingest::{ScanControl, SourceSyncService, SyncKind},
    preferences, storage, Config, Result,
};
use serde_json::{json, Value};
use std::{
    fs,
    ops::Deref,
    sync::{
        atomic::{AtomicUsize, Ordering},
        mpsc, Arc, Condvar, Mutex,
    },
    thread,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};
type TestScanner = Arc<dyn Fn(&ScanControl) -> Result<Value> + Send + Sync>;
struct Fixture {
    _temp: tempfile::TempDir,
    config: Config,
}
impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().unwrap();
        let base = fs::canonicalize(temp.path()).unwrap();
        let config = Config::for_data_dir(base.join("data"));
        fs::create_dir_all(&config.home_dir).unwrap();
        db::initialize(&config).unwrap();
        let current = preferences::read_preferences(&config).unwrap();
        preferences::save_preferences(
            &config,
            &json!({"session_sync_enabled":false,"context_sync_enabled":false}),
            &current["revision"],
        )
        .unwrap();
        Self {
            _temp: temp,
            config,
        }
    }
    fn service(&self, scanner: TestScanner) -> Stopping {
        Stopping(SourceSyncService::with_source_predicate(
            self.config.clone(),
            SyncKind::Session,
            scanner,
            Arc::new(|| Ok(true)),
        ))
    }
}
struct Stopping(SourceSyncService);
impl Deref for Stopping {
    type Target = SourceSyncService;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
impl Drop for Stopping {
    fn drop(&mut self) {
        self.0.stop();
    }
}
fn wait(mut check: impl FnMut() -> bool) {
    let until = Instant::now() + Duration::from_secs(5);
    while !check() {
        assert!(Instant::now() < until, "synthetic sync deadline");
        thread::sleep(Duration::from_millis(5));
    }
}
#[test]
fn manual_sync_runs_while_disabled_and_persists_completion_clock() {
    let f = Fixture::new();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    let s = f.service(Arc::new(move |control| {
        control.emit(json!({"type":"synthetic_progress"}));
        n.fetch_add(1, Ordering::SeqCst);
        Ok(json!({"outcome":"complete","sources":[]}))
    }));
    s.start();
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    s.request_sync().unwrap();
    wait(|| {
        s.status()
            .ok()
            .is_some_and(|v| v["generation"] == 1 && v["running"] == false)
    });
    let status = s.status().unwrap();
    assert_eq!(status["enabled"], false);
    assert_eq!(status["queued"], false);
    assert!(status["completed_at"].as_f64().unwrap() > 0.0);
    assert!(status["last_success_at"].as_f64().unwrap() > 0.0);
    assert_eq!(status["progress"], Value::Null);
    assert_eq!(calls.load(Ordering::SeqCst), 1);
}
#[test]
fn busy_writer_retains_one_request_until_lease_can_be_claimed() {
    let f = Fixture::new();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    let s = f.service(Arc::new(move |_| {
        n.fetch_add(1, Ordering::SeqCst);
        Ok(json!({"outcome":"complete"}))
    }));
    let lease = storage::operation_lock(&f.config, "synthetic-busy").unwrap();
    s.request_sync().unwrap();
    thread::sleep(Duration::from_millis(30));
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_eq!(s.status().unwrap()["queued"], true);
    drop(lease);
    s.changed();
    wait(|| calls.load(Ordering::SeqCst) == 1);
    wait(|| s.status().unwrap()["running"] == false);
    assert_eq!(s.status().unwrap()["queued"], false);
}

#[test]
fn invalid_lock_reports_failure_and_allows_a_retry_after_recovery() {
    let f = Fixture::new();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    let s = f.service(Arc::new(move |_| {
        n.fetch_add(1, Ordering::SeqCst);
        Ok(json!({"outcome":"complete"}))
    }));
    let lock = f.config.data_dir.join("operations.lock");
    fs::remove_file(&lock).unwrap();
    fs::create_dir(&lock).unwrap();
    fs::write(
        f.config.data_dir.join("session-sync-state.json"),
        r#"{"running":true,"generation":4,"last_success_at":100}"#,
    )
    .unwrap();

    let status = s.status().unwrap();
    assert_eq!(status["running"], false);
    assert_eq!(status["queued"], false);
    assert_eq!(status["last_success_at"], 100);
    let error = s.request_sync().unwrap_err();
    assert_eq!(error.status, 503);
    assert_eq!(status["error"], error.message);
    assert_eq!(calls.load(Ordering::SeqCst), 0);

    fs::remove_dir(&lock).unwrap();
    s.request_sync().unwrap();
    // Checking status while the crash marker still says running probes the
    // operation lock. Observe the scanner first to avoid creating contention.
    let retry_deadline = Instant::now() + Duration::from_secs(7);
    while calls.load(Ordering::SeqCst) == 0 {
        assert!(Instant::now() < retry_deadline, "sync retry did not start");
        thread::sleep(Duration::from_millis(5));
    }
    wait(|| {
        s.status().is_ok_and(|state| {
            state["generation"] == 5 && state["running"] == false && state["error"].is_null()
        })
    });
    assert_eq!(calls.load(Ordering::SeqCst), 1);
}
#[test]
fn a_later_other_backend_completion_satisfies_queued_manual_request() {
    let f = Fixture::new();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    let s = f.service(Arc::new(move |_| {
        n.fetch_add(1, Ordering::SeqCst);
        Ok(json!({"outcome":"complete"}))
    }));
    let lease = storage::operation_lock(&f.config, "synthetic-other-backend").unwrap();
    s.request_sync().unwrap();
    let future = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64()
        + 1.0;
    fs::write(
        f.config.data_dir.join("session-sync-state.json"),
        serde_json::to_vec(&json!({"completed_at":future,"running":false,"generation":9})).unwrap(),
    )
    .unwrap();
    drop(lease);
    s.changed();
    wait(|| s.status().unwrap()["queued"] == false);
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_eq!(s.status().unwrap()["generation"], 9);
}
#[test]
fn preference_outage_keeps_worker_alive_and_changed_resumes_collection() {
    let f = Fixture::new();
    let path = f.config.data_dir.join("settings.toml");
    let valid = fs::read(&path).unwrap();
    fs::write(&path, b"schema_version=999\n").unwrap();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    let s = f.service(Arc::new(move |_| {
        n.fetch_add(1, Ordering::SeqCst);
        Ok(json!({"outcome":"complete"}))
    }));
    s.start();
    thread::sleep(Duration::from_millis(30));
    assert!(s.alive());
    assert!(s.status().unwrap()["error"]
        .as_str()
        .unwrap()
        .contains("설정 버전"));
    fs::write(path, valid).unwrap();
    s.changed();
    s.request_sync().unwrap();
    wait(|| calls.load(Ordering::SeqCst) == 1);
}
#[test]
fn changed_does_not_interrupt_active_work_and_stop_joins_before_returning() {
    let f = Fixture::new();
    let gate = Arc::new((Mutex::new(false), Condvar::new()));
    let worker = gate.clone();
    let (entered_tx, entered_rx) = mpsc::channel();
    let s = f.service(Arc::new(move |control| {
        entered_tx.send(()).unwrap();
        let (released, wake) = (&worker.0, &worker.1);
        let mut released = released.lock().unwrap();
        while !*released {
            released = wake.wait(released).unwrap();
        }
        control.check()?;
        Ok(json!({"outcome":"complete"}))
    }));
    s.request_sync().unwrap();
    entered_rx.recv_timeout(Duration::from_secs(5)).unwrap();
    s.changed();
    assert_eq!(s.status().unwrap()["running"], true);
    assert_eq!(s.request_sync().unwrap()["queued"], false);
    let clone = s.0.clone();
    let (stopped_tx, stopped_rx) = mpsc::channel();
    let stopping = thread::spawn(move || {
        clone.stop();
        stopped_tx.send(()).unwrap();
    });
    assert!(stopped_rx.recv_timeout(Duration::from_millis(30)).is_err());
    {
        let mut released = gate.0.lock().unwrap();
        *released = true;
        gate.1.notify_all();
    }
    stopped_rx.recv_timeout(Duration::from_secs(5)).unwrap();
    stopping.join().unwrap();
    assert!(!s.alive());
    assert_eq!(s.status().unwrap()["running"], false);
}
