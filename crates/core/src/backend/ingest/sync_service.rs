//! Independent completion clocks and one coalesced request per source domain.
use super::{IngestionObserver, ScanControl};
use crate::backend::{db, preferences, sources::registry, storage, BackendError, Config, Result};
use serde_json::{json, Value};
use std::{
    fs,
    sync::{Arc, Condvar, Mutex},
    thread::JoinHandle,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
const STORAGE_UNAVAILABLE: &str =
    "동기화 저장소를 열지 못했습니다. 상태를 확인한 뒤 다시 시도해 주세요.";
#[derive(Debug, Clone, Copy)]
pub enum SyncKind {
    Session,
    Context,
}
impl SyncKind {
    fn key(self) -> &'static str {
        match self {
            Self::Session => "session",
            Self::Context => "context",
        }
    }
    fn label(self) -> &'static str {
        match self {
            Self::Session => "세션",
            Self::Context => "문서",
        }
    }
    fn source_label(self) -> &'static str {
        match self {
            Self::Session => "세션 소스",
            Self::Context => "Local Context",
        }
    }
}
pub type SyncScanner = Arc<dyn Fn(&ScanControl) -> Result<Value> + Send + Sync>;
pub type SourcePredicate = Arc<dyn Fn() -> Result<bool> + Send + Sync>;
#[derive(Default)]
struct State {
    stop: bool,
    wake: bool,
    queued: bool,
    requested_at: Option<f64>,
    alive: bool,
    progress: Option<Value>,
    error: Option<String>,
    handle: Option<JoinHandle<()>>,
}
struct Inner {
    config: Config,
    kind: SyncKind,
    scanner: SyncScanner,
    has_sources: SourcePredicate,
    state: Mutex<State>,
    wake: Condvar,
}
#[derive(Clone)]
pub struct SourceSyncService {
    inner: Arc<Inner>,
}
fn seconds() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
}
impl SourceSyncService {
    pub fn new(config: Config, kind: SyncKind, scanner: SyncScanner) -> Self {
        let input = config.clone();
        let has_sources: SourcePredicate = Arc::new(move || match kind {
            SyncKind::Session => {
                let sources = registry::load_session_source_settings(&input)?;
                if sources.file_error {
                    return Err(BackendError::conflict(
                        "세션 소스 설정을 읽지 못했습니다. 설정에서 확인해 주세요.",
                    ));
                }
                Ok(sources.entries.iter().any(|e| e.enabled))
            }
            SyncKind::Context => {
                let connection = db::connect(&input)?;
                Ok(connection.query_row(
                    "SELECT EXISTS(SELECT 1 FROM context_roots WHERE enabled=1)",
                    [],
                    |r| r.get(0),
                )?)
            }
        });
        Self::with_source_predicate(config, kind, scanner, has_sources)
    }
    pub fn with_source_predicate(
        config: Config,
        kind: SyncKind,
        scanner: SyncScanner,
        has_sources: SourcePredicate,
    ) -> Self {
        Self {
            inner: Arc::new(Inner {
                config,
                kind,
                scanner,
                has_sources,
                state: Mutex::new(State::default()),
                wake: Condvar::new(),
            }),
        }
    }
    pub fn for_kind(config: Config, kind: SyncKind, observer: Arc<dyn IngestionObserver>) -> Self {
        let input = config.clone();
        let scanner: SyncScanner = Arc::new(move |control| match kind {
            SyncKind::Session => {
                super::scan_session_sources(&input, false, control, observer.as_ref())
            }
            SyncKind::Context => {
                super::scan_context_sources(&input, false, control, observer.as_ref())
            }
        });
        Self::new(config, kind, scanner)
    }
    pub fn start(&self) {
        let mut state = self.inner.state.lock().unwrap();
        if state.alive || state.stop {
            return;
        }
        state.alive = true;
        let inner = self.inner.clone();
        state.handle = Some(
            crate::backend::worker_thread(format!("{}-sync", self.inner.kind.key()))
                .spawn(move || {
                    let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| inner.run()));
                    inner.state.lock().unwrap().alive = false;
                })
                .expect("source synchronization thread"),
        );
    }
    pub fn stop(&self) {
        let handle = {
            let mut state = self.inner.state.lock().unwrap();
            state.stop = true;
            state.wake = true;
            self.inner.wake.notify_all();
            state.handle.take()
        };
        if let Some(handle) = handle {
            let _ = handle.join();
        }
    }
    pub fn changed(&self) {
        let mut state = self.inner.state.lock().unwrap();
        state.wake = true;
        self.inner.wake.notify_all();
    }
    pub fn request(&self) -> Result<Value> {
        if self.status()?["running"] != true {
            storage::operation_active(&self.inner.config)
                .map_err(|_| BackendError::unavailable(STORAGE_UNAVAILABLE))?;
            {
                let mut state = self.inner.state.lock().unwrap();
                state.requested_at = Some(seconds());
                state.queued = true;
            }
            self.start();
            self.changed();
        }
        self.status()
    }
    pub fn request_sync(&self) -> Result<Value> {
        self.request()
    }
    pub fn status(&self) -> Result<Value> {
        self.inner.status()
    }
    pub fn alive(&self) -> bool {
        self.inner.state.lock().unwrap().alive
    }
}
impl Inner {
    fn read(&self) -> Result<Value> {
        let path = self
            .config
            .data_dir
            .join(format!("{}-sync-state.json", self.kind.key()));
        match fs::read(&path) {
            Ok(bytes) => Ok(serde_json::from_slice::<Value>(&bytes)
                .ok()
                .filter(Value::is_object)
                .unwrap_or_else(|| json!({}))),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(json!({})),
            Err(e) => Err(e.into()),
        }
    }
    fn write(&self, state: &Value) -> Result<()> {
        storage::files::atomic_write(
            &self
                .config
                .data_dir
                .join(format!("{}-sync-state.json", self.kind.key())),
            &serde_json::to_vec(state)?,
        )
    }
    fn prefs(&self) -> Result<Value> {
        preferences::effective_preferences(&self.config)
    }
    fn enabled(&self, prefs: &Value) -> bool {
        prefs[format!("{}_sync_enabled", self.kind.key())]
            .as_bool()
            .unwrap_or(false)
    }
    fn minutes(&self, prefs: &Value) -> f64 {
        prefs[format!("{}_sync_minutes", self.kind.key())]
            .as_f64()
            .unwrap_or(10.0)
    }
    fn status(&self) -> Result<Value> {
        let mut saved = self.read()?;
        let (queued, progress, mut error) = {
            let state = self.state.lock().unwrap();
            (state.queued, state.progress.clone(), state.error.clone())
        };
        let prefs = match self.prefs() {
            Ok(prefs) => prefs,
            Err(e) if e.status == 409 => {
                error = Some(e.to_string());
                json!({format!("{}_sync_enabled",self.kind.key()):false,format!("{}_sync_minutes",self.kind.key()):10})
            }
            Err(e) => return Err(e),
        };
        let running = if saved["running"] == true {
            match storage::operation_active(&self.config) {
                Ok(active) => active,
                Err(_) => {
                    error = Some(STORAGE_UNAVAILABLE.into());
                    false
                }
            }
        } else {
            false
        };
        let completed = saved["completed_at"].as_f64().unwrap_or(0.0);
        let has = match (self.has_sources)() {
            Ok(has) => has,
            Err(_) => {
                if error.is_none() {
                    error = Some(format!(
                        "{} 설정을 확인해 주세요.",
                        self.kind.source_label()
                    ));
                }
                false
            }
        };
        let enabled = self.enabled(&prefs);
        let next = if enabled && has && !running {
            Some((completed + self.minutes(&prefs) * 60.0).max(seconds()))
        } else {
            None
        };
        saved["running"] = json!(running);
        saved["queued"] = json!(queued);
        saved["enabled"] = json!(enabled);
        saved["minutes"] = prefs[format!("{}_sync_minutes", self.kind.key())].clone();
        saved["next_at"] = json!(next);
        saved["progress"] = json!(progress);
        if let Some(error) = error {
            saved["error"] = json!(error);
        } else if saved.get("error").is_none() {
            saved["error"] = Value::Null;
        }
        Ok(saved)
    }
    fn run(self: &Arc<Self>) {
        loop {
            if self.state.lock().unwrap().stop {
                return;
            }
            let result = (|| -> Result<()> {
                let prefs = self.prefs()?;
                let saved = self.read()?;
                let explicit = self.state.lock().unwrap().queued;
                let due = seconds()
                    >= saved["completed_at"].as_f64().unwrap_or(0.0) + self.minutes(&prefs) * 60.0;
                if explicit || (self.enabled(&prefs) && due) {
                    if (self.has_sources)()? {
                        self.collect(explicit)?;
                    } else {
                        self.state.lock().unwrap().queued = false;
                    }
                }
                Ok(())
            })();
            {
                let mut state = self.state.lock().unwrap();
                match result {
                    Ok(()) => state.error = None,
                    Err(e) if e.code == storage::OPERATION_BUSY => {}
                    Err(e) => {
                        state.error = Some(if e.status == 409 || e.status == 503 {
                            e.to_string()
                        } else {
                            "동기화 상태를 확인하지 못했습니다.".into()
                        });
                        state.queued = false;
                    }
                }
                if state.stop {
                    return;
                }
                let (mut state, _) = self
                    .wake
                    .wait_timeout_while(state, Duration::from_secs(5), |state| {
                        !state.wake && !state.stop
                    })
                    .unwrap();
                state.wake = false;
            }
        }
    }
    fn collect(self: &Arc<Self>, explicit: bool) -> Result<()> {
        let _lease = storage::operation_lock(&self.config, &format!("{}-sync", self.kind.key()))?;
        let previous = self.read()?;
        let prefs = self.prefs()?;
        let requested = self.state.lock().unwrap().requested_at;
        if explicit
            && requested.is_some_and(|t| previous["completed_at"].as_f64().unwrap_or(0.0) >= t)
        {
            self.state.lock().unwrap().queued = false;
            return Ok(());
        }
        if !explicit
            && (!self.enabled(&prefs)
                || seconds()
                    < previous["completed_at"].as_f64().unwrap_or(0.0)
                        + self.minutes(&prefs) * 60.0)
        {
            return Ok(());
        }
        let mut state = previous.clone();
        state["running"] = json!(true);
        state["started_at"] = json!(seconds());
        state["error"] = Value::Null;
        self.write(&state)?;
        self.state.lock().unwrap().queued = false;
        let progress = self.clone();
        let cancelled = self.clone();
        let control = ScanControl {
            cancelled: Some(Arc::new(move || cancelled.state.lock().unwrap().stop)),
            progress: Some(Arc::new(move |event| {
                progress.state.lock().unwrap().progress = Some(event)
            })),
        };
        match (self.scanner)(&control) {
            Ok(report) => {
                let outcome = report["outcome"].as_str().unwrap_or("failed").to_owned();
                state["report"] = report;
                state["outcome"] = json!(outcome);
                if outcome == "complete" {
                    state["last_success_at"] = json!(seconds());
                } else {
                    state["error"] = json!(format!(
                        "일부 소스를 가져오지 못했습니다. {}의 상태를 확인해 주세요.",
                        self.kind.source_label()
                    ));
                }
                state["generation"] = json!(previous["generation"].as_i64().unwrap_or(0) + 1);
            }
            Err(_) => {
                state["outcome"] = json!("failed");
                state["error"] = json!(format!(
                    "{}을 가져오지 못했습니다. 기존 기록은 보존했습니다.",
                    self.kind.label()
                ));
            }
        }
        self.state.lock().unwrap().progress = None;
        state["running"] = json!(false);
        state["completed_at"] = json!(seconds());
        self.write(&state)
    }
}

#[derive(Clone)]
pub struct SessionSyncService(SourceSyncService);
impl SessionSyncService {
    pub fn new(config: Config, observer: Arc<dyn IngestionObserver>) -> Self {
        Self(SourceSyncService::for_kind(
            config,
            SyncKind::Session,
            observer,
        ))
    }

    pub fn with_scanner(config: Config, scanner: SyncScanner) -> Self {
        Self(SourceSyncService::new(config, SyncKind::Session, scanner))
    }
}
impl std::ops::Deref for SessionSyncService {
    type Target = SourceSyncService;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
#[derive(Clone)]
pub struct ContextSyncService(SourceSyncService);
impl ContextSyncService {
    pub fn new(config: Config, observer: Arc<dyn IngestionObserver>) -> Self {
        Self(SourceSyncService::for_kind(
            config,
            SyncKind::Context,
            observer,
        ))
    }
}
impl std::ops::Deref for ContextSyncService {
    type Target = SourceSyncService;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
