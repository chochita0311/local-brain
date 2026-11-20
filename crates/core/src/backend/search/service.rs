use super::{
    failure,
    index::{self, folder},
    model::{Encoder, ExecutionOptions, NativeEncoder},
    molecules::Profile,
    retrieval::{database_stamp, DatabaseStamp, Retriever},
};
use crate::backend::{models, storage::operation_lock, Config, Result};
use localbrain_models::{catalog::ModelKey, Cancellation};
use serde_json::{json, Value};
use std::{
    sync::{atomic::Ordering, Arc, Condvar, Mutex},
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};
type Factory = Arc<dyn Fn(&Config, Profile) -> Result<Arc<dyn Encoder>> + Send + Sync>;
#[derive(Default)]
struct State {
    running: bool,
    requested: bool,
    error: Option<String>,
    had_index: bool,
    force_at: Option<index::FileStamp>,
    last_stamp: Option<(DatabaseStamp, String)>,
}
#[derive(Default)]
struct Engine {
    encoder: Option<Arc<dyn Encoder>>,
    retriever: Option<Arc<Retriever>>,
    contract: Option<(Value, Option<ExecutionOptions>)>,
    published_stamp: Option<index::FileStamp>,
    published_execution: Option<ExecutionOptions>,
}
struct Inner {
    config: Config,
    factory: Option<Factory>,
    engine: Mutex<Engine>,
    state: Mutex<State>,
    wake: Condvar,
    stop: Cancellation,
    cancel: Cancellation,
}
pub struct SearchService {
    inner: Arc<Inner>,
    thread: Mutex<Option<JoinHandle<()>>>,
}
fn lock<T>(mutex: &Mutex<T>) -> std::sync::MutexGuard<'_, T> {
    mutex.lock().unwrap_or_else(|error| error.into_inner())
}
impl Inner {
    fn assets_present(&self) -> bool {
        models::model_root(&self.config, ModelKey::Embedding)
            .is_ok_and(|root| root.join("model.json").is_file())
    }
    fn engine(&self, cancel: &Cancellation) -> Result<(Arc<dyn Encoder>, Arc<Retriever>, Profile)> {
        let (settings, profile) = index::read_settings(&self.config)?;
        if settings["enabled"] != true {
            return Err(failure("SEARCH_DISABLED"));
        }
        let mut engine = lock(&self.engine);
        if self.factory.is_none() {
            let stamp = index::published_stamp(&self.config);
            if stamp != engine.published_stamp {
                engine.published_execution =
                    stamp.and_then(|_| index::published_execution(&self.config));
                engine.published_stamp = stamp;
            }
        }
        let contract = (profile.index_contract(), engine.published_execution);
        if engine.contract.as_ref() != Some(&contract) {
            let encoder = match &self.factory {
                Some(factory) => factory(&self.config, profile)?,
                None => {
                    if !self.assets_present() {
                        return Err(failure("SEARCH_MODEL_MISSING"));
                    }
                    Arc::new(NativeEncoder::from_execution(
                        &self.config,
                        profile,
                        engine.published_execution,
                        cancel,
                    )?)
                }
            };
            if let Some(retriever) = &engine.retriever {
                retriever.close();
            }
            let retriever = Arc::new(Retriever::new(
                self.config.clone(),
                profile,
                encoder.clone(),
            ));
            engine.encoder = Some(encoder);
            engine.retriever = Some(retriever);
            engine.contract = Some(contract);
        }
        let encoder = engine.encoder.as_ref().unwrap().clone();
        let retriever = engine.retriever.as_ref().unwrap().clone();
        retriever.set_profile(profile);
        Ok((encoder, retriever, profile))
    }
}
impl SearchService {
    pub fn new(config: Config) -> Self {
        Self::make(config, None)
    }
    pub fn with_encoder_factory(config: Config, factory: Factory) -> Self {
        Self::make(config, Some(factory))
    }
    fn make(config: Config, factory: Option<Factory>) -> Self {
        Self {
            inner: Arc::new(Inner {
                config,
                factory,
                engine: Mutex::new(Engine::default()),
                state: Mutex::new(State::default()),
                wake: Condvar::new(),
                stop: localbrain_models::cancellation(),
                cancel: localbrain_models::cancellation(),
            }),
            thread: Mutex::new(None),
        }
    }
    pub fn start(&self) -> Result<()> {
        let mut handle = lock(&self.thread);
        if handle.as_ref().is_some_and(|thread| !thread.is_finished()) {
            return Ok(());
        }
        if let Some(thread) = handle.take() {
            let _ = thread.join();
        }
        self.inner.stop.store(false, Ordering::Release);
        let inner = self.inner.clone();
        *handle = Some(
            crate::backend::worker_thread("natural-search-refresh").spawn(move || watch(inner))?,
        );
        Ok(())
    }
    pub fn stop(&self) -> Result<()> {
        self.inner.stop.store(true, Ordering::Release);
        self.inner.cancel.store(true, Ordering::Release);
        self.inner.wake.notify_all();
        let mut handle = lock(&self.thread);
        if let Some(thread) = handle.take() {
            let start = Instant::now();
            while !thread.is_finished() && start.elapsed() < Duration::from_secs(30) {
                thread::sleep(Duration::from_millis(20));
            }
            if thread.is_finished() {
                let _ = thread.join();
            } else {
                *handle = Some(thread);
                return Err(failure("SEARCH_BUSY"));
            }
        }
        if !lock(&self.inner.state).running {
            if let Some(retriever) = &lock(&self.inner.engine).retriever {
                retriever.close();
            }
        }
        Ok(())
    }
    pub fn request_prepare(&self) -> Result<()> {
        {
            let _lease = operation_lock(&self.inner.config, "search-settings")?;
            let (value, profile) = index::read_settings(&self.inner.config)?;
            if value["enabled"] != true {
                index::save_settings(&self.inner.config, profile, true)?;
            }
        }
        {
            let mut state = lock(&self.inner.state);
            if !state.running {
                state.requested = true;
                state.error = None;
            }
        }
        self.start()?;
        self.inner.wake.notify_all();
        Ok(())
    }
    pub fn cancel(&self) {
        lock(&self.inner.state).requested = false;
        self.inner.cancel.store(true, Ordering::Release);
        self.inner.wake.notify_all();
    }
    pub fn model_changed(&self) {
        lock(&self.inner.engine).contract = None;
        lock(&self.inner.state).last_stamp = None;
        self.inner.wake.notify_all();
    }
    pub fn status(&self) -> Result<Value> {
        let (value, _) = index::read_settings(&self.inner.config)?;
        let enabled = value["enabled"] == true;
        let mut result = json!({"state":"disabled","parents":0,"eligible_parents":0,"fragments":0});
        let path = folder(&self.inner.config).join("status.json");
        if enabled && path.is_file() {
            match index::read_json(&path) {
                Ok(stored) if stored.is_object() => {
                    for key in [
                        "parents",
                        "eligible_parents",
                        "fragments",
                        "encoded",
                        "reused",
                        "elapsed_seconds",
                        "disk_bytes",
                        "peak_disk_bytes",
                        "excluded_sessions",
                        "unreadable_context_roots",
                        "empty_sessions",
                        "empty_documents",
                        "excluded_runtime_documents",
                        "error",
                    ] {
                        if let Some(value) = stored.get(key) {
                            result[key] = value.clone();
                        }
                    }
                    result["state"] = stored.get("state").cloned().unwrap_or("failed".into());
                }
                _ => result["state"] = "failed".into(),
            }
        }
        if !enabled {
            return Ok(result);
        }
        let (running, requested, error) = {
            let state = lock(&self.inner.state);
            (state.running, state.requested, state.error.clone())
        };
        if self.inner.factory.is_none() && !self.inner.assets_present() {
            result["state"] = "model-missing".into();
        } else if running || requested || index::writer_active(&self.inner.config)? {
            result["state"] = "preparing".into();
        } else if error.as_deref().is_some_and(|error| error != "SEARCH_BUSY") {
            result["state"] = "failed".into();
            result["error"] = json!(error);
        } else if !folder(&self.inner.config).join("index.sqlite3").is_file() {
            result["state"] = if lock(&self.thread)
                .as_ref()
                .is_some_and(|thread| !thread.is_finished())
            {
                "preparing"
            } else {
                "partial"
            }
            .into();
        } else if result["state"] == "preparing" {
            result["state"] = "partial".into();
        } else if result["state"] == "disabled" {
            result["state"] = "ready".into();
        }
        result["can_cancel"] = (running && error.as_deref() != Some("SEARCH_BUSY")).into();
        Ok(result)
    }
    pub fn search(&self, query: &str, page: usize) -> Result<Value> {
        let mut stamp = None;
        let cancel = localbrain_models::cancellation();
        let result = index::read_published(&self.inner.config, || {
            stamp = index::published_stamp(&self.inner.config);
            let (_, retriever, _) = self.inner.engine(&cancel)?;
            retriever.search(query, "hybrid", None, page, 20)
        });
        match &result {
            Err(error)
                if ["SEARCH_INDEX_INCOMPATIBLE", "INVALID_SEARCH_VECTORS"]
                    .contains(&error.code.as_str()) =>
            {
                let mut state = lock(&self.inner.state);
                if stamp == index::published_stamp(&self.inner.config) {
                    state.force_at = stamp;
                }
                state.requested = true;
                self.inner.wake.notify_all();
            }
            Ok(value) if value["partial"] == true => {
                lock(&self.inner.state).requested = true;
                self.inner.wake.notify_all();
            }
            _ => {}
        }
        result
    }
    pub fn evidence(&self, rowid: i64, generation: &str) -> Result<Value> {
        let cancel = localbrain_models::cancellation();
        index::read_published(&self.inner.config, || {
            self.inner.engine(&cancel)?.1.evidence(rowid, generation)
        })
    }
    pub fn refresh_after_scan(config: &Config, cancel: &Cancellation) -> Result<Option<Value>> {
        let (settings, profile) = index::read_settings(config)?;
        if settings["enabled"] != true {
            return Ok(None);
        }
        let writer = index::writer(config)?;
        let encoder = NativeEncoder::for_index(config, profile, cancel)?;
        Ok(Some(index::prepare_locked(
            config,
            &encoder,
            profile,
            cancel,
            false,
            &mut |_| {},
            &writer,
        )?))
    }
}
impl Drop for SearchService {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}
fn watch(inner: Arc<Inner>) {
    while !inner.stop.load(Ordering::Acquire) {
        let attempt = (|| {
            let (settings, profile) = index::read_settings(&inner.config)?;
            let stamp = (
                database_stamp(&inner.config.database_path),
                serde_json::to_string(&profile.index_contract())?,
            );
            let exists = folder(&inner.config).join("index.sqlite3").is_file();
            let prepare = {
                let mut state = lock(&inner.state);
                let lost = state.had_index && !exists;
                let prepare = settings["enabled"] == true
                    && (state.requested || state.last_stamp.as_ref() != Some(&stamp) || lost);
                if prepare {
                    state.requested = false;
                    state.last_stamp = Some(stamp);
                    state.running = true;
                }
                prepare
            };
            if prepare {
                inner.cancel.store(false, Ordering::Release);
                // Serialize resolution of the active generation with its
                // replacement, including explicit CLI preparation.
                let writer = index::writer(&inner.config)?;
                let (encoder, _, profile) = inner.engine(&inner.cancel)?;
                let force = lock(&inner.state)
                    .force_at
                    .is_some_and(|stamp| Some(stamp) == index::published_stamp(&inner.config));
                let prepared = index::prepare_locked(
                    &inner.config,
                    encoder.as_ref(),
                    profile,
                    &inner.cancel,
                    force,
                    &mut |_| {},
                    &writer,
                )?;
                drop(writer);
                if prepared["parents"].as_u64().unwrap_or(0) > 0
                    && !inner.cancel.load(Ordering::Acquire)
                {
                    encoder.tokenizer(&inner.cancel)?;
                }
                let mut state = lock(&inner.state);
                state.force_at = None;
                state.error = None;
            }
            lock(&inner.state).had_index = folder(&inner.config).join("index.sqlite3").is_file();
            Ok::<_, crate::backend::BackendError>(())
        })();
        {
            let mut state = lock(&inner.state);
            if let Err(error) = attempt {
                state.error = Some(
                    if ["SEARCH_MODEL_MISSING", "SEARCH_BUSY", "SEARCH_INTERRUPTED"]
                        .contains(&error.code.as_str())
                    {
                        error.code.clone()
                    } else {
                        "SEARCH_PREPARATION_FAILED".into()
                    },
                );
                if error.code == "SEARCH_BUSY" {
                    state.last_stamp = None;
                }
            }
            state.running = false;
            if inner.stop.load(Ordering::Acquire) {
                break;
            }
            let _ = inner
                .wake
                .wait_timeout(state, Duration::from_secs(5))
                .unwrap_or_else(|error| error.into_inner());
        }
    }
}
