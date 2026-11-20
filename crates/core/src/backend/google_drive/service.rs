//! Backend-lifetime scheduler and cached Settings state. Construction/status never authenticate.
use super::{
    api::{Remote, API},
    array,
    auth::GcloudAuth,
    engine::Engine,
    error,
    policy::*,
    require,
    store::Store,
    text,
};
use crate::backend::{clock, db, preferences, Config, Result};
use chrono::{DateTime, Utc};
use rusqlite::{Connection, OpenFlags};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet, VecDeque},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Condvar, Mutex,
    },
    thread::JoinHandle,
    time::{Duration, Instant},
};
pub type Cancel = Arc<dyn Fn() -> bool + Send + Sync>;
pub type ApiFactory = Arc<dyn Fn(&Value, Cancel) -> Result<Arc<dyn Remote>> + Send + Sync>;
pub type SourceLoader = Arc<dyn Fn() -> Result<Vec<Value>> + Send + Sync>;
#[derive(Default)]
struct State {
    active: Option<(String, String)>,
    progress: Option<Value>,
    slots: BTreeMap<(String, String), (DateTime<Utc>, i64, String)>,
    queue: VecDeque<(String, String)>,
}
pub struct DriveService {
    pub config: Config,
    pub store: Arc<Store>,
    pub engine: Engine,
    pub auth: Arc<GcloudAuth>,
    factory: Option<ApiFactory>,
    sources: SourceLoader,
    state: Mutex<State>,
    stop_event: Arc<AtomicBool>,
    cancel: Arc<AtomicBool>,
    wake: Condvar,
    scheduler: Mutex<Option<JoinHandle<()>>>,
    worker: Mutex<Option<JoinHandle<()>>>,
}
struct Lease(Arc<dyn Remote>);
impl Drop for Lease {
    fn drop(&mut self) {
        self.0.close()
    }
}
impl DriveService {
    pub fn new(
        config: Config,
        factory: Option<ApiFactory>,
        sources: Option<SourceLoader>,
        auth: Option<Arc<GcloudAuth>>,
    ) -> Result<Arc<Self>> {
        let store = Arc::new(Store::new(&config.data_dir)?);
        let engine = Engine::new(store.clone(), config.data_dir.clone())?;
        let loader_config = config.clone();
        let sources=sources.unwrap_or_else(||Arc::new(move||{let db=Connection::open_with_flags(&loader_config.database_path,OpenFlags::SQLITE_OPEN_READ_ONLY)?;db::rows(&db,"SELECT id,label,path,source_type FROM context_roots WHERE enabled=1 AND source_type IN ('folder','file') ORDER BY id",[])}));
        let service = Arc::new_cyclic(|weak: &std::sync::Weak<Self>| {
            let bound_store = store.clone();
            let connected = weak.clone();
            let failed = weak.clone();
            let auth = auth.unwrap_or_else(|| {
                GcloudAuth::new(
                    config.clone(),
                    Arc::new(move |id| {
                        let connection = bound_store.connection(id)?;
                        Ok(connection["gcloud_account"]
                            .as_str()
                            .filter(|s| !s.is_empty())
                            .or_else(|| connection["account"]["emailAddress"].as_str())
                            .map(str::to_owned))
                    }),
                    Arc::new(move |id, account, token| {
                        connected
                            .upgrade()
                            .ok_or_else(|| {
                                error("cancelled", "Google 연결을 중단했습니다.", false)
                            })?
                            .connected(id, account, token)
                    }),
                    Arc::new(move |id, error| {
                        if let Some(service) = failed.upgrade() {
                            let _ = service.health(id, "auth", Some(&error));
                        }
                    }),
                    None,
                )
            });
            Self {
                config,
                store,
                engine,
                auth,
                factory,
                sources,
                state: Mutex::new(State::default()),
                stop_event: Arc::new(AtomicBool::new(false)),
                cancel: Arc::new(AtomicBool::new(false)),
                wake: Condvar::new(),
                scheduler: Mutex::new(None),
                worker: Mutex::new(None),
            }
        });
        for connection in array(&service.store.connections()?) {
            let id = text(connection, "id");
            let mut jobs = service.store.jobs(id)?;
            if let Some(jobs) = jobs.as_object_mut() {
                for job in jobs.values_mut() {
                    if job["status"] == "running" {
                        job["status"] = json!("interrupted");
                        job["message"] = json!(
                            "이전 동기화가 중단되었습니다. 다음 정시 또는 수동 실행을 기다립니다."
                        );
                    }
                }
            }
            service.store.save_jobs(id, &jobs)?;
        }
        Ok(service)
    }
    pub fn start(self: &Arc<Self>) -> Result<()> {
        let mut scheduler = self.scheduler.lock().unwrap();
        if scheduler.as_ref().is_some_and(|t| !t.is_finished()) {
            return Ok(());
        }
        let service = self.clone();
        *scheduler = Some(
            crate::backend::worker_thread("drive-scheduler").spawn(move || service.schedule())?,
        );
        Ok(())
    }
    pub fn stop(&self) {
        self.stop_event.store(true, Ordering::Release);
        self.cancel.store(true, Ordering::Release);
        self.wake.notify_all();
        if let Some(thread) = self.scheduler.lock().unwrap().take() {
            let _ = thread.join();
        }
        self.auth.stop();
        if let Some(worker) = self.worker.lock().unwrap().take() {
            let _ = worker.join();
        }
    }
    pub fn wait_idle(&self) {
        if let Some(worker) = self.worker.lock().unwrap().take() {
            let _ = worker.join();
        }
    }
    pub fn zone(&self) -> Result<String> {
        Ok(
            preferences::effective_preferences(&self.config)?["timezone"]
                .as_str()
                .unwrap_or(&self.config.timezone_name)
                .into(),
        )
    }
    pub fn api(&self, connection: &Value, cancel: Cancel) -> Result<Arc<dyn Remote>> {
        if let Some(factory) = &self.factory {
            return factory(connection, cancel);
        }
        let id = text(connection, "id").to_owned();
        let token_auth = self.auth.clone();
        let token_id = id.clone();
        let refresh_auth = self.auth.clone();
        Ok(Arc::new(API::new(
            Arc::new(move || token_auth.access_token(&token_id)),
            BTreeMap::from([(
                text(connection, "root_id").into(),
                text(connection, "resource_key").into(),
            )]),
            cancel,
            Some(Arc::new(move || refresh_auth.invalidate(&id))),
            None,
        )?))
    }
    pub fn connected(&self, id: &str, account: &str, token: &str) -> Result<()> {
        require(
            !self.stop_event.load(Ordering::Acquire),
            "cancelled",
            "Google 연결을 중단했습니다.",
        )?;
        let connection = self.store.connection(id)?;
        let api = if let Some(factory) = &self.factory {
            factory(&connection, Arc::new(|| false))?
        } else {
            let token = token.to_owned();
            Arc::new(API::new(
                Arc::new(move || Ok(token.clone())),
                BTreeMap::new(),
                Arc::new(|| false),
                None,
                None,
            )?) as Arc<dyn Remote>
        };
        let api = Lease(api);
        let user = api.0.about()?;
        require(
            !text(&user, "permissionId").is_empty(),
            "account",
            "Google 계정 식별 정보를 확인하지 못했습니다.",
        )?;
        require(
            text(&user, "emailAddress").is_empty()
                || crate::backend::unicode::casefold(text(&user, "emailAddress"))
                    == crate::backend::unicode::casefold(account),
            "account_changed",
            "gcloud 계정과 Google 응답 계정이 다릅니다. 사용할 계정을 확인해 주세요.",
        )?;
        let _lock = self.state.lock().unwrap();
        require(
            !self.stop_event.load(Ordering::Acquire),
            "cancelled",
            "Google 연결을 중단했습니다.",
        )?;
        let mut connection = self.store.connection(id)?;
        if connection["account"].is_object() {
            require(
                connection["account"]["permissionId"] == user["permissionId"],
                "account_changed",
                "이 연결에 사용했던 Google 계정으로 연결해 주세요. 기존 사본과 설정을 보존합니다.",
            )?;
        }
        connection["gcloud_account"] = json!(account);
        connection["account"] = json!({"permissionId":user.get("permissionId"),"displayName":user.get("displayName"),"emailAddress":user.get("emailAddress")});
        self.store.update_connection(&connection)?;
        self.health(id, "auth", None)
    }
    pub fn health(
        &self,
        id: &str,
        area: &str,
        caught: Option<&crate::backend::BackendError>,
    ) -> Result<()> {
        let mut value = self.store.get(&format!("health:{id}"), json!({}))?;
        let at = clock::isoformat(Utc::now());
        let last = if caught.is_some() {
            value[area]
                .get("last_success")
                .cloned()
                .unwrap_or(Value::Null)
        } else {
            json!(at)
        };
        value[area] = json!({"observed_at":at,"status":if caught.is_some(){"error"}else{"ok"},"code":caught.map(|e|&e.code),"message":caught.map(|e|e.message.as_str()).unwrap_or("확인했습니다."),"last_success":last});
        self.store.put(&format!("health:{id}"), &value)
    }
    pub fn status(&self) -> Result<Value> {
        let state = self.state.lock().unwrap();
        let readiness = self.auth.status();
        let zone = self.zone()?;
        let now = Utc::now();
        let mut connections = Vec::new();
        for mut connection in array(&self.store.connections()?).to_vec() {
            let id = text(&connection, "id").to_owned();
            let mut jobs = self.store.jobs(&id)?;
            if let Some(jobs) = jobs.as_object_mut() {
                for (key, job) in jobs {
                    job["next_slot"] = if job["selected"] == true && job["auto"] == true {
                        json!(clock::isoformat(
                            match state.slots.get(&(id.clone(), key.clone())) {
                                Some(slot) => slot.0,
                                None => next_slot(now, interval(&job["interval"])?, &zone)?,
                            }
                        ))
                    } else {
                        Value::Null
                    };
                }
            }
            connection["jobs"] = jobs;
            connection["publishers"] = self.store.get(&format!("publishers:{id}"), json!([]))?;
            connection["health"] = self.store.get(&format!("health:{id}"), json!({}))?;
            connection["auth_pending"] = json!(self.auth.pending(&id));
            connections.push(connection);
        }
        Ok(
            json!({"connections":connections,"sources":(self.sources)()?.iter().map(|v|json!({"id":v.get("id"),"label":v.get("label"),"path":v.get("path"),"source_type":v.get("source_type")})).collect::<Vec<_>>(),"intervals":INTERVALS,"max_file_bytes":MAX_FILE_BYTES,"timezone":zone,"auth_mode":"gcloud","auth_scope":SCOPE,"gcloud_ready":readiness["ready"],"gcloud_message":readiness["message"],"active":state.active.as_ref().map(|(cid,job)|json!({"connection_id":cid,"job":job,"progress":state.progress}))}),
        )
    }
    pub fn add(&self, url: &str, target: &str) -> Result<Value> {
        let _lock = self.state.lock().unwrap();
        let connection = self.store.add(url, target)?;
        self.wake.notify_all();
        Ok(connection)
    }
    pub fn authenticate(&self, id: &str, account: Option<&str>, login: bool) -> Result<()> {
        {
            let state = self.state.lock().unwrap();
            self.store.connection(id)?;
            require(
                state.active.as_ref().is_none_or(|(active, _)| active != id),
                "busy",
                "현재 동기화가 끝난 뒤 연결해 주세요.",
            )?;
        }
        let result = if login {
            self.auth.begin(id, account)
        } else {
            self.auth.connect(id, account)
        };
        if let Err(caught) = &result {
            self.health(id, "auth", Some(caught))?
        }
        result
    }
    pub fn browse(&self, id: &str) -> Result<Value> {
        let connection = {
            let _lock = self.state.lock().unwrap();
            self.store.connection(id)?
        };
        let result = (|| -> Result<Value> {
            let api = Lease(self.api(&connection, Arc::new(|| false))?);
            let root = api.0.get(text(&connection, "root_id"))?;
            require(
                root["trashed"] != true && root["mimeType"] == FOLDER,
                "root",
                "사용 가능한 Google Drive 폴더 URL을 확인해 주세요.",
            )?;
            let publishers=api.0.children(text(&root,"id"))?.iter().filter(|c|c["mimeType"]==FOLDER&&c["id"]!=connection["target_id"]&&c["name"]!=connection["target"]).map(|c|json!({"id":c["id"],"name":c["name"],"resource_key":c.get("resourceKey").cloned().unwrap_or(json!(""))})).collect::<Vec<_>>();
            let _lock = self.state.lock().unwrap();
            self.store
                .put(&format!("publishers:{id}"), &json!(publishers))?;
            self.store.put(&format!("root_name:{id}"), &root["name"])?;
            self.health(id, "api", None)?;
            self.health(id, "root", None)?;
            self.health(id, "auth", None)?;
            Ok(json!(publishers))
        })();
        if let Err(e) = &result {
            self.health(id, "root", Some(e))?;
            self.health(
                id,
                if ["reauth", "unauthenticated", "scope"].contains(&e.code.as_str()) {
                    "auth"
                } else {
                    "api"
                },
                Some(e),
            )?
        }
        result
    }
    pub fn configure(&self, id: &str, key: &str, changes: &Value) -> Result<()> {
        let allowed = if key == "upload" {
            vec!["auto", "interval", "sources"]
        } else {
            vec!["selected", "auto", "interval"]
        };
        let changes = changes
            .as_object()
            .filter(|v| !v.is_empty() && v.keys().all(|k| allowed.contains(&k.as_str())))
            .ok_or_else(|| {
                error(
                    "invalid_settings",
                    "지원하지 않는 동기화 설정입니다.",
                    false,
                )
            })?;
        for name in ["selected", "auto"] {
            if let Some(value) = changes.get(name) {
                require(
                    value.is_boolean(),
                    "invalid_settings",
                    "선택·자동 실행 상태를 확인해 주세요.",
                )?;
            }
        }
        if let Some(value) = changes.get("interval") {
            interval(value)?;
        }
        let mut state = self.state.lock().unwrap();
        self.store.connection(id)?;
        let mut jobs = self.store.jobs(id)?;
        if key != "upload" {
            let choices = self.store.get(&format!("publishers:{id}"), json!([]))?;
            require(
                jobs.get(key).is_some()
                    || array(&choices)
                        .iter()
                        .any(|p| key == format!("receive:{}", text(p, "id"))),
                "publisher",
                "루트에서 조회한 폴더를 선택해 주세요.",
            )?;
        } else if let Some(values) = changes.get("sources") {
            let ids = (self.sources)()?
                .iter()
                .filter_map(|v| v["id"].as_i64())
                .collect::<BTreeSet<_>>();
            let values = values.as_array().filter(|v| {
                v.iter()
                    .all(|n| n.as_i64().is_some_and(|n| ids.contains(&n)))
                    && v.iter()
                        .filter_map(Value::as_i64)
                        .collect::<BTreeSet<_>>()
                        .len()
                        == v.len()
            });
            require(
                values.is_some(),
                "source",
                "등록된 Local Context 파일·폴더를 선택해 주세요.",
            )?;
        }
        let mut current = jobs
            .get(key)
            .cloned()
            .unwrap_or(json!({"selected":false,"auto":false,"interval":1440}));
        for (k, v) in changes {
            current[k] = v.clone();
        }
        if key == "upload" {
            current["selected"] = json!(!array(&current["sources"]).is_empty());
        }
        jobs[key] = current;
        self.store.save_jobs(id, &jobs)?;
        let pair = (id.into(), key.into());
        if state.active.as_ref() == Some(&pair) {
            self.cancel.store(true, Ordering::Release);
        }
        state.slots.remove(&pair);
        state.queue.retain(|v| v != &pair);
        self.wake.notify_all();
        Ok(())
    }
    pub fn run(self: &Arc<Self>, id: &str, key: &str) -> Result<()> {
        let (mut connection, selected) = {
            let mut state = self.state.lock().unwrap();
            require(
                state.active.is_none(),
                "busy",
                "진행 중인 동기화가 끝난 뒤 실행해 주세요.",
            )?;
            let connection = self.store.connection(id)?;
            let mut jobs = self.store.jobs(id)?;
            let job = jobs
                .get_mut(key)
                .ok_or_else(|| error("selection", "동기화할 항목을 먼저 선택해 주세요.", false))?;
            require(
                job["selected"] == true,
                "selection",
                "동기화할 항목을 먼저 선택해 주세요.",
            )?;
            require(
                key == "upload" || key.starts_with("receive:"),
                "job",
                "지원하지 않는 동기화 대상입니다.",
            )?;
            state.active = Some((id.into(), key.into()));
            state.progress = if key == "upload" {
                Some(
                    json!({"stage":"preparing","processed":0,"total":null,"current":"","transferred":0,"changed":0,"excluded":0,"last_activity_at":clock::isoformat(Utc::now())}),
                )
            } else {
                None
            };
            self.cancel.store(false, Ordering::Release);
            job["status"] = json!("running");
            job["started_at"] = json!(clock::isoformat(Utc::now()));
            job["message"] = json!("동기화 중입니다.");
            let ids = array(&job["sources"]).to_vec();
            let selected = (self.sources)()?
                .into_iter()
                .filter(|s| ids.contains(&s["id"]))
                .collect::<Vec<_>>();
            self.store.save_jobs(id, &jobs)?;
            (connection, selected)
        };
        let service = self.clone();
        let (id, key) = (id.to_owned(), key.to_owned());
        let worker = crate::backend::worker_thread("drive-sync").spawn(move || {
            let result = (|| -> Result<Value> {
                let cancel_service = service.clone();
                let api = Lease(service.api(
                    &connection,
                    Arc::new(move || {
                        cancel_service.stop_event.load(Ordering::Acquire)
                            || cancel_service.cancel.load(Ordering::Acquire)
                    }),
                )?);
                let root = api.0.get(text(&connection, "root_id"))?;
                require(
                    root["trashed"] != true && root["mimeType"] == FOLDER,
                    "root",
                    "설정한 공유 루트를 확인할 수 없습니다.",
                )?;
                service.health(&id, "api", None)?;
                service.health(&id, "root", None)?;
                service.health(&id, "auth", None)?;
                let report = if key == "upload" {
                    let jobs = service.store.jobs(&id)?;
                    require(
                        selected.len()
                            == array(&jobs[&key]["sources"])
                                .iter()
                                .filter_map(Value::as_i64)
                                .collect::<BTreeSet<_>>()
                                .len(),
                        "source",
                        "선택한 Local Context 등록을 확인해 주세요. 기존 사본은 보존합니다.",
                    )?;
                    service.engine.publish(
                        &mut connection,
                        &selected,
                        api.0.as_ref(),
                        &|values| {
                            let mut state = service.state.lock().unwrap();
                            if let Some(progress) = state.progress.as_mut() {
                                if let Some(values) = values.as_object() {
                                    for (k, v) in values {
                                        progress[k] = v.clone();
                                    }
                                    progress["last_activity_at"] =
                                        json!(clock::isoformat(Utc::now()));
                                }
                            }
                        },
                    )?
                } else {
                    for publisher in
                        array(&service.store.get(&format!("publishers:{id}"), json!([]))?)
                    {
                        if publisher["id"] == key[8..]
                            && !text(publisher, "resource_key").is_empty()
                        {
                            api.0
                                .set_key(text(publisher, "id"), text(publisher, "resource_key"));
                        }
                    }
                    service
                        .engine
                        .receive(&connection, &key[8..], api.0.as_ref())?
                };
                api.0.check()?;
                Ok(report)
            })();
            let (report, status, message, caught) = match result {
                Ok(report) => {
                    let partial = !array(&report["errors"]).is_empty();
                    (
                        report,
                        if partial { "partial" } else { "complete" },
                        if partial {
                            "일부 항목을 갱신하지 못했습니다. 항목별 이유를 확인해 주세요."
                                .to_owned()
                        } else {
                            "동기화가 완료되었습니다.".to_owned()
                        },
                        None,
                    )
                }
                Err(e) => {
                    let status = if e.code == "cancelled" {
                        "stopped"
                    } else {
                        "error"
                    };
                    (json!({}), status, e.message.clone(), Some(e))
                }
            };
            let mut state = service.state.lock().unwrap();
            let stored = (|| -> Result<()> {
                let mut jobs = service.store.jobs(&id)?;
                let current = &mut jobs[&key];
                current["status"] = json!(status);
                current["message"] = json!(message);
                current["observed_at"] = json!(clock::isoformat(Utc::now()));
                current["report"] = report;
                if status == "complete" {
                    current["last_success"] = current["observed_at"].clone();
                }
                service.store.save_jobs(&id, &jobs)?;
                if let Some(e) = caught
                    .as_ref()
                    .filter(|e| ["reauth", "unauthenticated", "scope"].contains(&e.code.as_str()))
                {
                    service.health(&id, "auth", Some(e))?;
                }
                Ok(())
            })();
            let _ = stored;
            state.active = None;
            state.progress = None;
            service.wake.notify_all();
        })?;
        *self.worker.lock().unwrap() = Some(worker);
        Ok(())
    }
    pub fn schedule_once(
        self: &Arc<Self>,
        now: DateTime<Utc>,
        zone: &str,
        reset: bool,
    ) -> Result<()> {
        let next = {
            let mut state = self.state.lock().unwrap();
            if reset {
                state.slots.clear();
                state.queue.clear();
            }
            let mut active = BTreeSet::new();
            for connection in array(&self.store.connections()?) {
                let cid = text(connection, "id");
                let jobs = self.store.jobs(cid)?;
                for (key, job) in jobs.as_object().into_iter().flatten() {
                    if job["selected"] != true || job["auto"] != true {
                        continue;
                    }
                    let pair = (cid.to_owned(), key.clone());
                    active.insert(pair.clone());
                    let minutes = interval(&job["interval"])?;
                    let previous = state.slots.get(&pair).cloned();
                    if !previous
                        .as_ref()
                        .is_some_and(|(_, m, z)| *m == minutes && z == zone)
                    {
                        state
                            .slots
                            .insert(pair, (next_slot(now, minutes, zone)?, minutes, zone.into()));
                        continue;
                    }
                    let due = previous.unwrap().0;
                    if due <= now {
                        let slot_key = format!("slot:{cid}:{key}");
                        let last = self.store.get(&slot_key, Value::Null)?;
                        let due_text = clock::isoformat(due);
                        if (now - due).num_milliseconds() < 60000
                            && (last.is_null()
                                || last.as_str().is_some_and(|last| due_text.as_str() > last))
                            && state.active.as_ref() != Some(&pair)
                            && !state.queue.contains(&pair)
                        {
                            state.queue.push_back(pair.clone());
                            self.store.put(&slot_key, &json!(due_text))?;
                        }
                        state
                            .slots
                            .insert(pair, (next_slot(now, minutes, zone)?, minutes, zone.into()));
                    }
                }
            }
            state.slots.retain(|k, _| active.contains(k));
            if state.active.is_none() {
                state.queue.pop_front()
            } else {
                None
            }
        };
        if let Some((cid, key)) = next {
            self.run(&cid, &key)?;
        }
        Ok(())
    }
    fn schedule(self: &Arc<Self>) {
        let (mut last_wall, mut last_mono, mut last_zone) = (Utc::now(), Instant::now(), None);
        while !self.stop_event.load(Ordering::Acquire) {
            let now = Utc::now();
            let mono = Instant::now();
            if let Ok(zone) = self.zone() {
                let elapsed = mono.duration_since(last_mono).as_secs_f64();
                let wall = (now - last_wall).num_milliseconds() as f64 / 1000.0;
                let slept = elapsed > 90.0 || (wall - elapsed).abs() > 5.0;
                let _ = self.schedule_once(now, &zone, slept || last_zone.as_ref() != Some(&zone));
                last_zone = Some(zone);
                last_wall = now;
                last_mono = mono;
            }
            let state = self.state.lock().unwrap();
            let _ = self.wake.wait_timeout(state, Duration::from_millis(500));
        }
    }
}
/// Optional composition boundary: an unreadable Drive store leaves local sources usable.
/// Calling this function explicitly opts into the existing scheduler; defaults stay suspended.
pub fn start_service(config: Config) -> Option<Arc<DriveService>> {
    let service = DriveService::new(config, None, None, None).ok()?;
    service.start().ok()?;
    Some(service)
}
