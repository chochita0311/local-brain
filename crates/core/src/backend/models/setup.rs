use super::*;
use crate::backend::search::SearchService;
use serde::{Deserialize, Serialize};
use std::{
    collections::BTreeMap,
    io::{BufRead, BufReader, Read, Write},
    process::{Child, ChildStdin, Command, Stdio},
    sync::{Arc, Mutex},
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};
#[derive(Serialize, Deserialize)]
struct Job {
    data: PathBuf,
    cache: PathBuf,
    home: PathBuf,
    public_cache: PathBuf,
    installation: Option<PathBuf>,
    key: String,
    selected: Option<PathBuf>,
    revision: Option<String>,
}
struct Process {
    child: Mutex<Child>,
    stdin: Mutex<Option<ChildStdin>>,
}
struct State {
    phase: String,
    generation: BTreeMap<String, String>,
    active: String,
    canceled: bool,
    folder_busy: bool,
    process: Option<Arc<Process>>,
}
pub struct ModelSetupService {
    config: Config,
    search: Arc<SearchService>,
    state: Arc<Mutex<State>>,
    thread: Mutex<Option<JoinHandle<()>>>,
}
fn guard<T>(lock: &Mutex<T>) -> std::sync::MutexGuard<'_, T> {
    lock.lock().unwrap_or_else(|error| error.into_inner())
}
fn set_phase(state: &mut State, phase: &str) {
    if state.active == "embedding" {
        state.phase = phase.into();
    } else {
        state.generation.insert(state.active.clone(), phase.into());
    }
}
impl ModelSetupService {
    pub fn new(config: Config, search: Arc<SearchService>) -> Self {
        Self {
            config,
            search,
            state: Arc::new(Mutex::new(State {
                phase: "idle".into(),
                generation: BTreeMap::from([
                    ("4b".into(), "idle".into()),
                    ("8b".into(), "idle".into()),
                ]),
                active: "embedding".into(),
                canceled: false,
                folder_busy: false,
                process: None,
            })),
            thread: Mutex::new(None),
        }
    }
    pub fn status(&self) -> Result<Value> {
        let mut state = guard(&self.state);
        if state.phase == "preparing" {
            match self.search.status()?["state"].as_str() {
                Some("ready" | "no-data" | "partial") => state.phase = "ready".into(),
                Some("failed") => state.phase = "index-failed".into(),
                _ => {}
            }
        }
        let running = state
            .process
            .as_ref()
            .is_some_and(|process| guard(&process.child).try_wait().ok().flatten().is_none());
        let mut models = generation_models(&self.config)?;
        for model in models.as_array_mut().unwrap() {
            let key = model["key"].as_str().unwrap().to_string();
            model["phase"] = state
                .generation
                .get(&key)
                .cloned()
                .unwrap_or_else(|| "idle".into())
                .into();
            model["running"] = (running && state.active == key).into();
        }
        Ok(
            json!({"phase":state.phase,"running":running,"active_key":state.active,"installed":model_root(&self.config,ModelKey::Embedding)?.join("model.json").is_file(),"runtime_missing":[],"download_bytes_approx":1210000000_u64,"generation_runtime_missing":[],"generation_models":models,"folder":folder_status(&self.config)?,"folder_busy":state.folder_busy}),
        )
    }
    pub fn start(&self, key: &str, selected: Option<&Value>, revision: Option<&str>) -> Result<()> {
        if !["embedding", "4b", "8b"].contains(&key) {
            return Err(BackendError::conflict("지원하는 모델을 선택해 주세요."));
        }
        let selected = selected
            .map(|path| selected_folder(path, &self.config))
            .transpose()?;
        if selected.is_some() && (key != "embedding" || revision.is_none()) {
            return Err(BackendError::conflict(
                "모델 저장 위치를 다시 확인해 주세요.",
            ));
        }
        let mut thread = guard(&self.thread);
        let mut state = guard(&self.state);
        if state.folder_busy {
            return Err(BackendError::conflict(
                "모델 폴더 확인을 마친 뒤 다시 시도해 주세요.",
            ));
        }
        if thread.as_ref().is_some_and(|thread| !thread.is_finished()) {
            if selected.is_some() {
                return Err(BackendError::conflict(
                    "진행 중인 모델 작업을 마치거나 중단한 뒤 시도해 주세요.",
                ));
            }
            if key != state.active {
                return Err(BackendError::conflict(
                    "진행 중인 모델 설치를 마치거나 중단한 뒤 시도해 주세요.",
                ));
            }
            return Ok(());
        }
        if let Some(thread) = thread.take() {
            let _ = thread.join();
        }
        if selected.is_some()
            && revision
                != Some(
                    registration_revision(&model_root(&self.config, ModelKey::Embedding)?)?
                        .as_str(),
                )
        {
            return Err(BackendError::conflict(
                "모델 설정이 변경되었습니다. 폴더를 다시 확인해 주세요.",
            ));
        }
        let job = Job {
            data: self.config.data_dir.clone(),
            cache: self.config.cache_dir.clone(),
            home: self.config.home_dir.clone(),
            public_cache: self.config.hf_hub_cache.clone(),
            installation: self.config.installation_root.clone(),
            key: key.into(),
            selected,
            revision: revision.map(str::to_owned),
        };
        let mut encoded = serde_json::to_vec(&job)?;
        encoded.push(b'\n');
        let mut child = Command::new(std::env::current_exe()?)
            .arg("--install-search-model")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()?;
        let mut input = child
            .stdin
            .take()
            .ok_or_else(|| BackendError::unavailable("Model worker input is unavailable"))?;
        let output = child
            .stdout
            .take()
            .ok_or_else(|| BackendError::unavailable("Model worker output is unavailable"))?;
        if let Err(error) = input.write_all(&encoded).and_then(|_| input.flush()) {
            let _ = child.kill();
            let _ = child.wait();
            return Err(error.into());
        }
        let process = Arc::new(Process {
            child: Mutex::new(child),
            stdin: Mutex::new(Some(input)),
        });
        state.active = key.into();
        state.canceled = false;
        state.process = Some(process.clone());
        set_phase(&mut state, "downloading");
        drop(state);
        let shared = self.state.clone();
        let search = self.search.clone();
        let spawned = crate::backend::worker_thread("model-setup").spawn(move || {
            for line in BufReader::new(output).lines() {
                let Ok(line) = line else {
                    break;
                };
                let Some(phase) = serde_json::from_str::<Value>(&line)
                    .ok()
                    .and_then(|value| value["phase"].as_str().map(str::to_owned))
                else {
                    continue;
                };
                if ["downloading", "verifying", "installed", "failed"].contains(&phase.as_str()) {
                    set_phase(&mut guard(&shared), &phase);
                }
            }
            let success = guard(&process.child)
                .wait()
                .is_ok_and(|status| status.success());
            let embedding;
            {
                let mut state = guard(&shared);
                embedding = state.active == "embedding";
                let phase = if state.canceled {
                    "canceled"
                } else if success {
                    if embedding {
                        "preparing"
                    } else {
                        "installed"
                    }
                } else {
                    "failed"
                };
                set_phase(&mut state, phase);
            }
            if success && embedding && !guard(&shared).canceled {
                search.model_changed();
                if search.request_prepare().is_err() {
                    set_phase(&mut guard(&shared), "failed");
                }
            }
            guard(&process.stdin).take();
        });
        match spawned {
            Ok(worker) => *thread = Some(worker),
            Err(error) => {
                let mut state = guard(&self.state);
                if let Some(process) = &state.process {
                    let mut child = guard(&process.child);
                    let _ = child.kill();
                    let _ = child.wait();
                    guard(&process.stdin).take();
                }
                set_phase(&mut state, "failed");
                return Err(error.into());
            }
        }
        Ok(())
    }
    fn folder_operation(&self) -> Result<FolderGuard> {
        let state = self.state.clone();
        {
            let thread = guard(&self.thread);
            let mut current = guard(&state);
            if current.folder_busy || thread.as_ref().is_some_and(|thread| !thread.is_finished()) {
                return Err(BackendError::conflict(
                    "진행 중인 모델 작업을 마친 뒤 다시 시도해 주세요.",
                ));
            }
            current.folder_busy = true;
        }
        Ok(FolderGuard(state))
    }
    pub fn check_folder(&self, path: &Value) -> Result<Value> {
        let _guard = self.folder_operation()?;
        inspect_folder(path, &self.config)
    }
    pub fn use_folder(&self, path: &Value, revision: &str) -> Result<Value> {
        let candidate = selected_folder(path, &self.config)?;
        {
            let _guard = self.folder_operation()?;
            install_model(&self.config,ModelKey::Embedding,true,Some(&candidate),Some(revision.into()),&localbrain_models::cancellation(),|_|{}).map_err(|error|match error.code.as_str(){"MODEL_REGISTRATION_CHANGED"=>BackendError::conflict("모델 설정이 변경되었습니다. 폴더를 다시 확인해 주세요."),"MODEL_IDENTITY_CHANGED"=>BackendError::conflict("현재 모델의 버전이 달라 저장 위치를 바꿀 수 없습니다. 기존 모델을 보존했습니다."),"MODEL_IO"|"io"=>BackendError::conflict("모델 저장 위치를 연결하지 못했습니다. 접근 권한을 확인해 주세요."),_=>BackendError::conflict("모델 파일을 확인하지 못했습니다. 기존 저장 위치를 유지합니다. 폴더를 다시 확인해 주세요.")})?;
            self.search.model_changed();
        }
        self.status()
    }
    pub fn cancel(&self) -> Result<()> {
        let process;
        let embedding;
        {
            let mut state = guard(&self.state);
            state.canceled = true;
            process = state.process.clone();
            embedding = state.active == "embedding";
            set_phase(&mut state, "canceled");
        }
        if let Some(process) = &process {
            let mut child = guard(&process.child);
            if child.try_wait()?.is_none() {
                unsafe {
                    libc::kill(child.id() as i32, libc::SIGTERM);
                }
            }
        }
        if embedding {
            self.search.cancel();
        }
        if let Some(process) = process {
            let start = Instant::now();
            loop {
                if guard(&process.child).try_wait()?.is_some() {
                    break;
                }
                if start.elapsed() >= Duration::from_secs(10) {
                    let mut child = guard(&process.child);
                    child.kill()?;
                    child.wait()?;
                    break;
                }
                thread::sleep(Duration::from_millis(20));
            }
        }
        let mut handle = guard(&self.thread);
        if let Some(worker) = handle.take() {
            let start = Instant::now();
            while !worker.is_finished() && start.elapsed() < Duration::from_secs(10) {
                thread::sleep(Duration::from_millis(20));
            }
            if worker.is_finished() {
                let _ = worker.join();
            } else {
                *handle = Some(worker);
                return Err(BackendError::conflict("Model worker is still stopping"));
            }
        }
        Ok(())
    }
    pub fn stop(&self) -> Result<()> {
        let running = guard(&self.thread)
            .as_ref()
            .is_some_and(|thread| !thread.is_finished());
        let process = guard(&self.state).process.is_some();
        if process || running {
            self.cancel()?;
        }
        Ok(())
    }
}
impl Drop for ModelSetupService {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}
struct FolderGuard(Arc<Mutex<State>>);
impl Drop for FolderGuard {
    fn drop(&mut self) {
        guard(&self.0).folder_busy = false;
    }
}
/// A native installer subprocess. Its stdin remains a parent-lifetime lease.
pub fn download_worker() -> i32 {
    let mut line = String::new();
    if std::io::stdin()
        .lock()
        .take(64 * 1024)
        .read_line(&mut line)
        .is_err()
    {
        return 1;
    }
    let Ok(job) = serde_json::from_str::<Job>(&line) else {
        return 1;
    };
    let Ok(key) = ModelKey::parse(&job.key) else {
        return 1;
    };
    let mut config = Config::for_data_dir(job.data);
    config.cache_dir = job.cache;
    config.home_dir = job.home;
    config.hf_hub_cache = job.public_cache;
    config.installation_root = job.installation;
    let descriptor = unsafe { libc::dup(libc::STDIN_FILENO) };
    if descriptor < 0 {
        return 1;
    }
    thread::spawn(move || {
        use std::os::fd::FromRawFd;
        let mut input = unsafe { fs::File::from_raw_fd(descriptor) };
        let mut buffer = [0; 4096];
        loop {
            match input.read(&mut buffer) {
                Ok(0) | Err(_) => {
                    unsafe {
                        libc::kill(libc::getpid(), libc::SIGTERM);
                    }
                    break;
                }
                Ok(_) => {}
            }
        }
    });
    if key != ModelKey::Embedding {
        let available = assets::model_status(&config.data_dir, &config.hf_hub_cache)
            .iter()
            .any(|model| model.key == key && (model.registered || model.cached));
        let _ = writeln!(
            std::io::stdout(),
            "{}",
            json!({"phase":if available{"verifying"}else{"downloading"}})
        );
        let _ = std::io::stdout().flush();
    }
    let outcome = install_model(
        &config,
        key,
        false,
        job.selected.as_deref(),
        job.revision,
        &localbrain_models::cancellation(),
        |value| {
            let _ = writeln!(std::io::stdout(), "{}", json!({"phase":value.phase}));
            let _ = std::io::stdout().flush();
        },
    );
    let phase = if outcome.is_ok() {
        "installed"
    } else {
        "failed"
    };
    let _ = writeln!(std::io::stdout(), "{}", json!({"phase":phase}));
    if outcome.is_ok() {
        0
    } else {
        1
    }
}
