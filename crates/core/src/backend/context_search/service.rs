//! Owns a single reusable native worker and one transient request at a time.
use super::{
    dumps,
    engine::validate_request,
    error,
    tools::{public_sources, source_catalog, DriveCatalog},
};
use crate::backend::{models, Config, Result};
use serde_json::{json, Value};
use std::{
    io::{BufRead, BufReader, Read, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc::{self, Receiver, SyncSender, TrySendError},
        Arc, Mutex,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};
fn send(sender: &SyncSender<Value>, mut value: Value, cancel: &AtomicBool) -> bool {
    loop {
        if cancel.load(Ordering::Acquire) {
            return false;
        }
        match sender.try_send(value) {
            Ok(()) => return true,
            Err(TrySendError::Disconnected(_)) => return false,
            Err(TrySendError::Full(v)) => {
                value = v;
                thread::sleep(Duration::from_millis(10))
            }
        }
    }
}
pub struct ContextSearchJob {
    events: Mutex<Receiver<Value>>,
    sender: SyncSender<Value>,
    pub canceled: Arc<AtomicBool>,
    completed: AtomicBool,
    thread: Mutex<Option<JoinHandle<()>>>,
}
impl ContextSearchJob {
    pub fn next_event(&self, timeout: Duration) -> Option<Value> {
        self.events.lock().unwrap().recv_timeout(timeout).ok()
    }
    pub fn completed(&self) -> bool {
        self.completed.load(Ordering::Acquire)
    }
}
struct Worker {
    child: Mutex<Child>,
    input: Mutex<Option<ChildStdin>>,
    responses: Mutex<Receiver<Value>>,
    stopped: Arc<AtomicBool>,
    reader: Mutex<Option<JoinHandle<()>>>,
    key: String,
}
impl Worker {
    fn stop(&self) {
        self.stopped.store(true, Ordering::Release);
        self.input.lock().unwrap().take();
        let mut child = self.child.lock().unwrap();
        if matches!(child.try_wait(), Ok(None)) {
            unsafe {
                libc::kill(child.id() as i32, libc::SIGTERM);
            }
            let started = Instant::now();
            while matches!(child.try_wait(), Ok(None)) && started.elapsed() < Duration::from_secs(2)
            {
                thread::sleep(Duration::from_millis(10));
            }
            if matches!(child.try_wait(), Ok(None)) {
                let _ = child.kill();
            }
            let _ = child.wait();
        }
        drop(child);
        if let Some(reader) = self.reader.lock().unwrap().take() {
            let _ = reader.join();
        }
    }
    fn alive(&self) -> bool {
        matches!(self.child.lock().unwrap().try_wait(), Ok(None))
    }
}
impl Drop for Worker {
    fn drop(&mut self) {
        self.stop();
    }
}
struct State {
    closed: bool,
    job: Option<Arc<ContextSearchJob>>,
}
pub struct ContextSearchService {
    config: Config,
    drive: Option<Arc<dyn DriveCatalog>>,
    executable: PathBuf,
    state: Mutex<State>,
    worker: Mutex<Option<Arc<Worker>>>,
}
impl ContextSearchService {
    pub fn new(config: Config, drive: Option<Arc<dyn DriveCatalog>>) -> Result<Arc<Self>> {
        Self::with_executable(config, drive, std::env::current_exe()?)
    }
    /// Explicit executable injection is for a native host or a synthetic protocol fixture.
    pub fn with_executable(
        config: Config,
        drive: Option<Arc<dyn DriveCatalog>>,
        executable: PathBuf,
    ) -> Result<Arc<Self>> {
        Ok(Arc::new(Self {
            config,
            drive,
            executable,
            state: Mutex::new(State {
                closed: false,
                job: None,
            }),
            worker: Mutex::new(None),
        }))
    }
    pub fn status(&self) -> Result<Value> {
        let sources = source_catalog(&self.config, self.drive.as_deref())?;
        Ok(
            json!({"models":models::generation_models(&self.config)?,"runtime_missing":[],"sources":public_sources(&sources),"busy":self.state.lock().unwrap().job.is_some()}),
        )
    }
    pub fn begin(self: &Arc<Self>, value: &Value) -> Result<Arc<ContextSearchJob>> {
        let (key, messages) = validate_request(value)?;
        if !models::generation_models(&self.config)?
            .as_array()
            .unwrap()
            .iter()
            .any(|m| m["key"] == key && m["available"] == true)
        {
            return Err(error(
                "MODEL_MISSING",
                "설정 → 검색 모델에서 선택한 모델을 설치해 주세요.",
            )
            .with_status(409));
        }
        let sources = source_catalog(&self.config, self.drive.as_deref())?;
        if sources.is_empty() {
            return Err(error(
                "SOURCES_MISSING",
                "Local Context를 연결하거나 Google Drive 폴더를 먼저 받아 주세요.",
            )
            .with_status(409));
        }
        if sources.len() > 100 {
            return Err(error(
                "SOURCES_LIMIT",
                "검색 대상이100개를 넘습니다. Local Context 연결 범위를 줄여 주세요.",
            )
            .with_status(409));
        }
        let payload = json!({"model":key,"messages":messages,"sources":sources});
        if dumps(&payload)?.len() > 250000 {
            return Err(error("INPUT", "질문이나 연결된 자료 범위를 줄여 주세요."));
        }
        let mut state = self.state.lock().unwrap();
        if state.closed || state.job.is_some() {
            return Err(error(
                "BUSY",
                "다른 질문을 처리 중입니다. 완료하거나 중단한 뒤 시도해 주세요.",
            )
            .with_status(409));
        }
        let (sender, receiver) = mpsc::sync_channel(64);
        let job = Arc::new(ContextSearchJob {
            events: Mutex::new(receiver),
            sender,
            canceled: Arc::new(AtomicBool::new(false)),
            completed: AtomicBool::new(false),
            thread: Mutex::new(None),
        });
        state.job = Some(job.clone());
        let service = self.clone();
        let run_job = job.clone();
        *job.thread.lock().unwrap() = Some(
            crate::backend::worker_thread("context-search-turn")
                .spawn(move || service.run(&run_job, &key, payload))?,
        );
        Ok(job)
    }
    fn spawn(&self, key: &str) -> Result<Arc<Worker>> {
        self.terminate();
        let mut child = Command::new(&self.executable)
            .arg("--context-search-worker")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()?;
        let input = child.stdin.take();
        let stdout = child.stdout.take().unwrap();
        let (sender, receiver) = mpsc::sync_channel(64);
        let stopped = Arc::new(AtomicBool::new(false));
        let reader_stopped = stopped.clone();
        let reader = crate::backend::worker_thread("context-search-output").spawn(move || {
            let mut reader = BufReader::new(stdout);
            loop {
                let mut raw = Vec::new();
                let read = Read::by_ref(&mut reader)
                    .take(524293)
                    .read_until(b'\n', &mut raw);
                if !matches!(read,Ok(n)if n>0) {
                    break;
                }
                let Ok(line) = std::str::from_utf8(&raw) else {
                    break;
                };
                if line.chars().count() > 131072 || !line.ends_with('\n') {
                    break;
                }
                let Ok(value) = crate::backend::json::decode(line) else {
                    break;
                };
                if value.is_object() && !send(&sender, value, &reader_stopped) {
                    break;
                }
            }
            let _ = send(
                &sender,
                json!({"type":"error","code":"MODEL_FAILED"}),
                &reader_stopped,
            );
        })?;
        let worker = Arc::new(Worker {
            child: Mutex::new(child),
            input: Mutex::new(input),
            responses: Mutex::new(receiver),
            stopped,
            reader: Mutex::new(Some(reader)),
            key: key.into(),
        });
        *self.worker.lock().unwrap() = Some(worker.clone());
        {
            let mut input = worker.input.lock().unwrap();
            let input = input.as_mut().unwrap();
            writeln!(
                input,
                "{}",
                crate::backend::json::encode_http(
                    &json!({"type":"configure","model":key,"config":{"data_dir":self.config.data_dir,"home_dir":self.config.home_dir,"hf_hub_cache":self.config.hf_hub_cache}})
                )?
            )?;
            input.flush()?;
        }
        Ok(worker)
    }
    fn run(&self, job: &ContextSearchJob, key: &str, mut payload: Value) {
        let result = (|| -> Result<()> {
            let cached = self.worker.lock().unwrap().clone();
            let worker = match cached.filter(|w| w.key == key && w.alive()) {
                Some(w) => w,
                None => self.spawn(key)?,
            };
            if job.canceled.load(Ordering::Acquire) {
                self.terminate();
                return Ok(());
            }
            {
                let mut input = worker.input.lock().unwrap();
                let input = input.as_mut().ok_or_else(|| {
                    error(
                        "MODEL_FAILED",
                        "모델 실행이 중단되었습니다. 다시 시도해 주세요.",
                    )
                })?;
                writeln!(input, "{}", crate::backend::json::encode_http(&payload)?)?;
                input.flush()?;
            }
            payload = Value::Null;
            let started = Instant::now();
            while !job.canceled.load(Ordering::Acquire) {
                if started.elapsed() > Duration::from_secs(360) {
                    return Err(error(
                        "TIMEOUT",
                        "모델 응답 시간이 길어 중단했습니다. 질문 범위를 줄여 다시 시도해 주세요.",
                    ));
                }
                let Some(value) = worker
                    .responses
                    .lock()
                    .unwrap()
                    .recv_timeout(Duration::from_millis(250))
                    .ok()
                else {
                    continue;
                };
                if value["type"] == "error" {
                    return Err(error(
                        value["code"].as_str().unwrap_or("MODEL_FAILED"),
                        friendly(value["code"].as_str().unwrap_or("")),
                    ));
                }
                if matches!(value["type"].as_str(), Some("status" | "answer")) {
                    let answer = value["type"] == "answer";
                    if !send(&job.sender, value, &job.canceled) {
                        break;
                    }
                    if answer {
                        job.completed.store(true, Ordering::Release);
                        return Ok(());
                    }
                }
            }
            Ok(())
        })();
        if let Err(caught) = result {
            if !job.canceled.load(Ordering::Acquire) {
                send(
                    &job.sender,
                    json!({"type":"error","message":if caught.status==422 {caught.message.as_str()}else{"모델 실행이 중단되었습니다. 다시 시도해 주세요."}}),
                    &job.canceled,
                );
            }
            self.terminate();
        }
    }
    fn terminate(&self) {
        if let Some(worker) = self.worker.lock().unwrap().take() {
            worker.stop();
        }
    }
    pub fn release(&self, job: &Arc<ContextSearchJob>) {
        if !job.completed() {
            job.canceled.store(true, Ordering::Release);
            self.terminate()
        }
        if let Some(thread) = job.thread.lock().unwrap().take() {
            let _ = thread.join();
        }
        let mut state = self.state.lock().unwrap();
        if state
            .job
            .as_ref()
            .is_some_and(|current| Arc::ptr_eq(current, job))
        {
            state.job = None
        }
        drop(state);
        while job.events.lock().unwrap().try_recv().is_ok() {}
    }
    pub fn stop(&self) {
        let job = {
            let mut state = self.state.lock().unwrap();
            state.closed = true;
            state.job.clone()
        };
        if let Some(job) = job {
            self.release(&job)
        }
        self.terminate()
    }
    pub fn unload_idle(&self) {
        let state = self.state.lock().unwrap();
        if state.job.is_none() {
            self.terminate()
        }
    }
}
trait Status {
    fn with_status(self, status: u16) -> Self;
}
impl Status for crate::backend::BackendError {
    fn with_status(mut self, status: u16) -> Self {
        self.status = status;
        self
    }
}
fn friendly(code: &str) -> &'static str {
    match code {"CONTEXT_TOO_LARGE"=>"대화나 읽은 자료가 모델 입력 한도를 넘었습니다. 새 질문에서 폴더·파일·키워드를 좁혀 주세요.","OUTPUT_TRUNCATED"=>"모델이 답변을 끝내지 못했습니다. 질문 범위를 줄여 다시 시도해 주세요.","MODEL_ASSETS_CHANGED"=>"모델 파일 검증에 실패했습니다. 설정 → 검색 모델에서 설치를 확인해 주세요.","INVALID_MODEL"=>"모델 설치를 확인해 주세요. 설정 → 검색 모델에서 다시 연결할 수 있습니다.","MODEL_NOT_CACHED"=>"모델 원본이 없습니다. 설정 → 검색 모델에서 설치해 주세요.","MODEL_BUSY"=>"모델 설치나 검증이 진행 중입니다. 완료한 뒤 다시 질문해 주세요.","PROTOCOL"=>"모델의 도구 요청을 읽지 못했습니다. 질문을 구체화해 다시 시도해 주세요.","BUDGET"=>"이번 질문의 탐색 한도에 도달했습니다. 폴더·파일·키워드를 좁혀 주세요.",_=>"로컬 모델 실행에 실패했습니다. 설치와 사용 가능한 메모리를 확인해 주세요."}
}
