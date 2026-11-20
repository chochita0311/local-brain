use crate::{
    templates::Templates,
    transport::{ApiError, ApiResult, RequestContext},
    usage_dashboard::UsageDashboardCache,
};
use axum::{
    http::StatusCode,
    response::{Html, IntoResponse, Response},
};
use localbrain_core::backend::{
    db,
    ingest::{self, ContextSyncService, IngestionObserver, ScanControl, SessionSyncService},
    integrations::ApplicationIngestion,
    maintenance::TaskRuntime,
    models::ModelSetupService,
    preferences,
    search::SearchService,
    sources, storage, BackendError, Config, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};

pub fn database<T>(
    config: &Config,
    write: bool,
    perform: impl FnOnce(&Connection) -> Result<T>,
) -> Result<T> {
    database_with_begin(config, write.then_some("BEGIN"), perform)
}
pub fn immediate<T>(config: &Config, perform: impl FnOnce(&Connection) -> Result<T>) -> Result<T> {
    database_with_begin(config, Some("BEGIN IMMEDIATE"), perform)
}
fn database_with_begin<T>(
    config: &Config,
    begin: Option<&str>,
    perform: impl FnOnce(&Connection) -> Result<T>,
) -> Result<T> {
    let connection = db::connect(config)?;
    if let Some(begin) = begin {
        connection.execute_batch(begin)?;
    }
    match perform(&connection) {
        Ok(value) => {
            if begin.is_some() {
                connection.execute_batch("COMMIT")?;
            }
            Ok(value)
        }
        Err(error) => {
            if begin.is_some() {
                connection.execute_batch("ROLLBACK")?;
            }
            Err(error)
        }
    }
}
pub type MembershipReader = fn(&Connection, &str, i64) -> Result<Vec<Value>>;
pub type WorkflowEligibility = fn(&Connection, i64) -> Result<bool>;
pub fn maintain_included_caches(config: &Config) -> Result<Value> {
    let mut result = if config.feature("auto_work") {
        localbrain_core::backend::auto_work::cache::maintain_cache(
            config,
            &config.cache_dir,
            true,
            None,
        )?
    } else {
        json!({"removed_bytes":0})
    };
    if config.feature("terminal") {
        let terminal = localbrain_core::backend::terminal::maintain_cache(config);
        result["removed_bytes"] = json!(
            result["removed_bytes"].as_u64().unwrap_or(0)
                + terminal["removed_bytes"].as_u64().unwrap_or(0)
        );
        result["protected"] = terminal["protected"].clone();
    }
    Ok(result)
}
#[derive(Default)]
pub struct FeatureBindings {
    pub atlassian: Option<Arc<dyn IngestionObserver>>,
    pub memberships: Option<MembershipReader>,
    pub workflow_eligible: Option<WorkflowEligibility>,
    pub external_executor:
        Option<Arc<dyn localbrain_core::backend::atlassian::sync::ExternalReadExecutor>>,
}
impl FeatureBindings {
    pub fn for_config(config: &Config) -> Result<Self> {
        let bindings = Self {
            atlassian: config.feature("atlassian").then(|| {
                Arc::new(localbrain_core::backend::atlassian::ingestion::AtlassianIngestion::new())
                    as Arc<dyn IngestionObserver>
            }),
            memberships: config.feature("workstreams").then_some(
                localbrain_core::backend::workstreams::entity_memberships as MembershipReader,
            ),
            workflow_eligible: config.feature("workflow").then_some(
                localbrain_core::backend::workflow::focus::workflow_session_is_eligible
                    as WorkflowEligibility,
            ),
            ..Self::default()
        };
        bindings.validate(config)?;
        Ok(bindings)
    }
    fn validate(&self, config: &Config) -> Result<()> {
        for (feature, present) in [
            ("atlassian", self.atlassian.is_some()),
            ("workstreams", self.memberships.is_some()),
            ("workflow", self.workflow_eligible.is_some()),
        ] {
            if config.feature(feature) && !present {
                return Err(BackendError::unavailable(format!(
                    "Required feature integration is missing: {feature}"
                )));
            }
        }
        Ok(())
    }
}
pub struct Services {
    pub search: Arc<SearchService>,
    pub session_sync: SessionSyncService,
    pub context_sync: ContextSyncService,
    pub(crate) usage_dashboard: Arc<UsageDashboardCache>,
    pub models: ModelSetupService,
    pub observer: Arc<dyn IngestionObserver>,
    pub features: FeatureBindings,
    pub tasks: Option<Arc<TaskRuntime>>,
    pub insights: Option<Arc<localbrain_core::backend::insights::runs::InsightRuntime>>,
    pub context_search: Option<Arc<localbrain_core::backend::context_search::ContextSearchService>>,
    pub google_drive: Option<Arc<localbrain_core::backend::google_drive::DriveService>>,
    _storage: storage::BackendStorageLease,
    stopped: AtomicBool,
}
impl Services {
    pub fn start(config: &Config, features: FeatureBindings) -> Result<Self> {
        features.validate(config)?;
        let lease = storage::backend_storage_lease(config)?;
        db::initialize(config)?;
        sources::settings::recover_source_reconnect(config)?;
        sources::settings::migrate_source_settings(config)?;
        if config.feature("auto_work") || config.feature("terminal") {
            maintain_included_caches(config)?;
        }
        let registry = database(config, true, |db| {
            sources::registry::load_and_reconcile_session_sources(db, config)
        })?;
        if !config.data_dir.join("settings.toml").exists() {
            let has_context = database(config, false, |connection| {
                Ok(db::row(
                    connection,
                    "SELECT 1 FROM context_roots WHERE enabled=1 LIMIT 1",
                    [],
                )?
                .is_some())
            })?;
            match preferences::read_preferences(config) {
                Ok(saved) => {
                    let result = preferences::save_preferences(
                        config,
                        &json!({"onboarding_completed":!registry.settings.entries.is_empty()||has_context}),
                        &saved["revision"],
                    );
                    if let Err(error) = result {
                        if error.status != 409 {
                            return Err(error);
                        }
                    }
                }
                Err(error) if error.status == 409 => {}
                Err(error) => return Err(error),
            }
        }
        let observer: Arc<dyn IngestionObserver> = Arc::new(ApplicationIngestion::new(
            config.clone(),
            features.atlassian.iter().cloned().collect(),
        ));
        let tasks =
            if !config.desktop && (config.feature("atlassian") || config.feature("workstreams")) {
                let runtime = Arc::new(TaskRuntime::new(config.clone()));
                let observers = observer.clone();
                runtime.set_scanner(move |config, runner| {
                    let control = ScanControl::default();
                    if runner == "codex" {
                        ingest::scan_codex_sessions(config, false, &control, observers.as_ref())?;
                    } else {
                        ingest::scan_claude_sessions(config, false, &control, observers.as_ref())?;
                    }
                    Ok(())
                });
                runtime.reconcile_interrupted_runs()?;
                Some(runtime)
            } else {
                None
            };
        let insights = if config.desktop {
            None
        } else {
            let runtime = Arc::new(
                localbrain_core::backend::insights::runs::InsightRuntime::new(config.clone()),
            );
            database(config, true, |conn| runtime.reconcile(conn))?;
            Some(runtime)
        };
        let search = Arc::new(SearchService::new(config.clone()));
        let models = ModelSetupService::new(config.clone(), search.clone());
        let google_drive = if config.feature("google_drive") {
            localbrain_core::backend::google_drive::start_service(config.clone())
        } else {
            None
        };
        let catalog = google_drive.as_ref().map(|service| {
            service.store.clone()
                as Arc<dyn localbrain_core::backend::context_search::tools::DriveCatalog>
        });
        let context_search = if config.feature("context_search") {
            match localbrain_core::backend::context_search::ContextSearchService::new(
                config.clone(),
                catalog,
            ) {
                Ok(service) => Some(service),
                Err(error) => {
                    if let Some(drive) = &google_drive {
                        drive.stop();
                    }
                    return Err(error);
                }
            }
        } else {
            None
        };
        let usage_dashboard = Arc::new(UsageDashboardCache::default());
        let session_sync = {
            let config = config.clone();
            let observer = observer.clone();
            let usage_dashboard = usage_dashboard.clone();
            SessionSyncService::with_scanner(
                config.clone(),
                Arc::new(move |control| {
                    let report =
                        ingest::scan_session_sources(&config, false, control, observer.as_ref())?;
                    if matches!(report["outcome"].as_str(), Some("complete" | "partial"))
                        && control.check().is_ok()
                    {
                        let _ = usage_dashboard.refresh_after_sync(&config);
                    }
                    Ok(report)
                }),
            )
        };
        let services = Self {
            search,
            session_sync,
            context_sync: ContextSyncService::new(config.clone(), observer.clone()),
            usage_dashboard,
            models,
            observer,
            features,
            tasks,
            insights,
            context_search,
            google_drive,
            _storage: lease,
            stopped: AtomicBool::new(false),
        };
        services.search.start()?;
        services.session_sync.start();
        services.context_sync.start();
        Ok(services)
    }
    pub fn stop(&self) -> Result<()> {
        if self.stopped.swap(true, Ordering::AcqRel) {
            return Ok(());
        }
        let mut errors = Vec::new();
        if let Some(context) = &self.context_search {
            context.stop();
        }
        if let Some(drive) = &self.google_drive {
            drive.stop();
        }
        if let Err(error) = self.models.stop() {
            errors.push(error);
        }
        self.context_sync.stop();
        self.session_sync.stop();
        if let Err(error) = self.search.stop() {
            errors.push(error);
        }
        if let Some(tasks) = &self.tasks {
            if let Err(error) = tasks.shutdown() {
                errors.push(error);
            }
        }
        if let Some(insights) = &self.insights {
            if let Err(error) = insights.shutdown() {
                errors.push(error);
            }
        }
        if errors.is_empty() {
            Ok(())
        } else {
            Err(
                BackendError::unavailable("Background services did not stop cleanly").with_details(
                    json!(errors
                        .iter()
                        .map(|error| json!({"code":error.code,"message":error.message}))
                        .collect::<Vec<_>>()),
                ),
            )
        }
    }
}
impl Drop for Services {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}

#[derive(Clone)]
pub struct Shutdown {
    signal: tokio::sync::watch::Sender<bool>,
}
impl Shutdown {
    fn new() -> Self {
        let (signal, _) = tokio::sync::watch::channel(false);
        Self { signal }
    }
    pub fn request(&self) {
        self.signal.send_replace(true);
    }
    pub fn is_requested(&self) -> bool {
        *self.signal.borrow()
    }
    pub async fn wait(&self) {
        let mut receiver = self.signal.subscribe();
        if *receiver.borrow() {
            return;
        }
        let _ = receiver.changed().await;
    }
}
#[derive(Clone)]
pub struct AppState {
    pub config: Arc<Config>,
    pub templates: Arc<Templates>,
    pub services: Arc<Services>,
    pub shutdown: Shutdown,
    pub token: String,
    pub(crate) atlassian_sync_receipts: Option<Arc<crate::routes::atlassian::SyncReceipts>>,
}
impl AppState {
    pub fn initialize(config: Config, token: String, features: FeatureBindings) -> Result<Self> {
        let config = Arc::new(config);
        let templates = Arc::new(Templates::load(config.clone())?);
        let services = Arc::new(Services::start(&config, features)?);
        let atlassian_sync_receipts = config
            .feature("atlassian")
            .then(|| Arc::new(crate::routes::atlassian::SyncReceipts::default()));
        Ok(Self {
            config,
            templates,
            services,
            shutdown: Shutdown::new(),
            token,
            atlassian_sync_receipts,
        })
    }
    pub async fn blocking<T, F>(&self, perform: F) -> ApiResult<T>
    where
        T: Send + 'static,
        F: FnOnce(Self) -> Result<T> + Send + 'static,
    {
        let state = self.clone();
        tokio::task::spawn_blocking(move || perform(state))
            .await
            .map_err(|_| ApiError(BackendError::unavailable("Local operation interrupted")))?
            .map_err(ApiError)
    }
    pub fn scan_control(&self) -> ScanControl {
        let shutdown = self.shutdown.clone();
        ScanControl {
            cancelled: Some(Arc::new(move || shutdown.is_requested())),
            progress: None,
        }
    }
    pub fn render(
        &self,
        request: &RequestContext,
        template: &str,
        data: Value,
        status: u16,
    ) -> Result<Response> {
        let html = self.templates.render(
            template,
            &request.origin,
            &request.path,
            request.uri.query().unwrap_or(""),
            data,
        )?;
        Ok((
            StatusCode::from_u16(status)
                .map_err(|_| BackendError::invalid("status", "Invalid response status"))?,
            Html(html),
        )
            .into_response())
    }
}
