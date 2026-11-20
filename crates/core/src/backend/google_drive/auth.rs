//! External Google SDK authentication; credentials stay in SDK facilities, tokens in RAM.
use super::{array, error, require, text};
use crate::backend::{storage::files, unicode, Config, Result};
use serde_json::{json, Value};
use std::os::unix::{fs::PermissionsExt, process::CommandExt};
use std::{
    collections::BTreeMap,
    ffi::OsString,
    io::Read,
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread::JoinHandle,
    time::{Duration, Instant},
};
pub const LOGIN_COMMAND: &str = "gcloud auth login --enable-gdrive-access --force";
pub fn gcloud_path(config: &Config) -> Result<PathBuf> {
    let candidates = if let Some(path) = &config.gcloud_path {
        vec![files::expand(path, config)]
    } else {
        let mut paths = std::env::split_paths(&std::env::var_os("PATH").unwrap_or_default())
            .map(|p| p.join("gcloud"))
            .filter(|p| p.is_file())
            .take(1)
            .collect::<Vec<_>>();
        paths.extend([
            config.home_dir.join("google-cloud-sdk/bin/gcloud"),
            PathBuf::from("/opt/homebrew/bin/gcloud"),
            PathBuf::from("/usr/local/bin/gcloud"),
            PathBuf::from("/opt/homebrew/share/google-cloud-sdk/bin/gcloud"),
            PathBuf::from("/usr/local/share/google-cloud-sdk/bin/gcloud"),
            config
                .home_dir
                .join(".local/share/google-cloud-sdk/bin/gcloud"),
        ]);
        paths
    };
    for path in candidates {
        if path.is_file()
            && path
                .metadata()
                .is_ok_and(|m| m.permissions().mode() & 0o111 != 0)
        {
            return files::lexical_absolute(&path);
        }
    }
    Err(error(
        "gcloud_missing",
        "Google Cloud CLI(gcloud)를 찾을 수 없습니다. 설치 후 다시 연결해 주세요.",
        false,
    ))
}
pub fn sdk_environment() -> BTreeMap<OsString, OsString> {
    let mut env = std::env::vars_os().collect::<BTreeMap<_, _>>();
    for key in [
        "PYTHONHOME",
        "PYTHONPATH",
        "_MEIPASS2",
        "_PYI_APPLICATION_HOME_DIR",
        "DYLD_LIBRARY_PATH",
        "DYLD_FALLBACK_LIBRARY_PATH",
        "LD_LIBRARY_PATH",
    ] {
        env.remove(&OsString::from(key));
    }
    let mut path = env
        .get(&OsString::from("PATH"))
        .cloned()
        .unwrap_or_default();
    path.push(":/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin");
    env.insert("PATH".into(), path);
    for (key, value) in [
        ("CLOUDSDK_CORE_DISABLE_USAGE_REPORTING", "true"),
        ("CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK", "true"),
        ("CLOUDSDK_CORE_DISABLE_FILE_LOGGING", "true"),
        ("CLOUDSDK_CORE_LOG_HTTP", "false"),
        ("CLOUDSDK_AUTH_ACCESS_TOKEN", ""),
        ("CLOUDSDK_AUTH_ACCESS_TOKEN_FILE", ""),
        ("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", ""),
        ("CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT", ""),
    ] {
        env.insert(key.into(), value.into());
    }
    env
}
pub fn account_name(value: &str) -> Result<&str> {
    require(
        !value.is_empty()
            && value.chars().count() <= 320
            && !value.starts_with('-')
            && !value
                .chars()
                .any(|c| unicode::python_space(c) || (c as u32) < 32),
        "account",
        "연결할 Google 계정을 확인해 주세요.",
    )?;
    Ok(value)
}
pub fn sdk_error(stderr: &str) -> crate::backend::BackendError {
    let lower = unicode::lowercase(stderr);
    if [
        "connection",
        "network",
        "timed out",
        "timeout",
        "sslerror",
        "transporterror",
        "name resolution",
    ]
    .iter()
    .any(|s| lower.contains(s))
    {
        error(
            "network",
            "Google 인증 서버에 연결하지 못했습니다. 연결 상태를 확인하고 다시 시도해 주세요.",
            true,
        )
    } else if [
        "invalid_grant",
        "reauthentication",
        "no valid credentials",
        "does not have valid credentials",
        "not have valid credentials",
        "no active account",
        "not have an active account",
        "login required",
    ]
    .iter()
    .any(|s| lower.contains(s))
    {
        error(
            "reauth",
            "Google 로그인이 필요합니다. Drive 접근을 포함해 다시 로그인해 주세요.",
            false,
        )
    } else if lower.contains("python")
        && ["not found", "could not", "unsupported", "requires"]
            .iter()
            .any(|s| lower.contains(s))
    {
        error("gcloud_runtime","gcloud 실행 환경을 확인하지 못했습니다. Google Cloud CLI 설치와 Python 설정을 확인해 주세요.",false)
    } else {
        error("gcloud_request","gcloud 인증 요청을 완료하지 못했습니다. Google 로그인 상태와 CLI 설치를 확인해 주세요.",false)
    }
}
pub struct CommandOutput {
    pub code: i32,
    pub stdout: String,
    pub stderr: String,
}
pub trait CommandRunner: Send + Sync {
    fn run(
        &self,
        argv: &[OsString],
        env: &BTreeMap<OsString, OsString>,
        timeout: Duration,
        stopped: &AtomicBool,
    ) -> Result<CommandOutput>;
    fn stop(&self) {}
}
#[derive(Default)]
pub struct NativeCommandRunner {
    processes: Mutex<BTreeMap<u32, Arc<Mutex<Child>>>>,
}
fn terminate(child: &mut Child) {
    if !matches!(child.try_wait(), Ok(None)) {
        return;
    }
    unsafe {
        libc::killpg(child.id() as i32, libc::SIGTERM);
    }
    let started = Instant::now();
    while matches!(child.try_wait(), Ok(None)) && started.elapsed() < Duration::from_secs(3) {
        std::thread::sleep(Duration::from_millis(10))
    }
    if matches!(child.try_wait(), Ok(None)) {
        unsafe {
            libc::killpg(child.id() as i32, libc::SIGKILL);
        }
        let _ = child.kill();
    }
    let _ = child.wait();
}
impl CommandRunner for NativeCommandRunner {
    fn run(
        &self,
        argv: &[OsString],
        env: &BTreeMap<OsString, OsString>,
        timeout: Duration,
        stopped: &AtomicBool,
    ) -> Result<CommandOutput> {
        let mut process = Command::new(&argv[0])
            .args(&argv[1..])
            .env_clear()
            .envs(env)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .process_group(0)
            .spawn()
            .map_err(|_| {
                error(
                    "gcloud_runtime",
                    "gcloud를 실행하지 못했습니다. 설치 경로와 실행 권한을 확인해 주세요.",
                    false,
                )
            })?;
        let id = process.id();
        let stdout = process.stdout.take().unwrap();
        let stderr = process.stderr.take().unwrap();
        let output = std::thread::spawn(move || {
            let mut bytes = Vec::new();
            stdout.take(262149).read_to_end(&mut bytes).map(|_| bytes)
        });
        let errors = std::thread::spawn(move || {
            let mut bytes = Vec::new();
            stderr
                .take(1024 * 1024)
                .read_to_end(&mut bytes)
                .map(|_| bytes)
        });
        let child = Arc::new(Mutex::new(process));
        self.processes.lock().unwrap().insert(id, child.clone());
        let started = Instant::now();
        let result = loop {
            if stopped.load(Ordering::Acquire) || started.elapsed() > timeout {
                terminate(&mut child.lock().unwrap());
                break Err(error(
                    if stopped.load(Ordering::Acquire) {
                        "cancelled"
                    } else if argv.get(1) == Some(&OsString::from("auth"))
                        && argv.get(2) == Some(&OsString::from("login"))
                    {
                        "auth_timeout"
                    } else {
                        "network"
                    },
                    "Google 인증 요청 시간이 끝났습니다. 연결 상태를 확인하고 다시 시도해 주세요.",
                    true,
                ));
            }
            match child.lock().unwrap().try_wait() {
                Ok(Some(status)) => break Ok(status.code().unwrap_or(-1)),
                Ok(None) => {}
                Err(e) => break Err(e.into()),
            }
            std::thread::sleep(Duration::from_millis(10));
        };
        self.processes.lock().unwrap().remove(&id);
        let stdout = output.join().ok().and_then(|r| r.ok()).unwrap_or_default();
        let stderr = errors.join().ok().and_then(|r| r.ok()).unwrap_or_default();
        Ok(CommandOutput {
            code: result?,
            stdout: String::from_utf8_lossy(&stdout).into_owned(),
            stderr: String::from_utf8_lossy(&stderr).into_owned(),
        })
    }
    fn stop(&self) {
        for process in self.processes.lock().unwrap().values() {
            terminate(&mut process.lock().unwrap());
        }
    }
}
type Bound = Arc<dyn Fn(&str) -> Result<Option<String>> + Send + Sync>;
type Connected = Arc<dyn Fn(&str, &str, &str) -> Result<()> + Send + Sync>;
type OnError = Arc<dyn Fn(&str, crate::backend::BackendError) + Send + Sync>;
pub struct GcloudAuth {
    config: Config,
    bound: Bound,
    connected: Connected,
    on_error: OnError,
    runner: Arc<dyn CommandRunner>,
    tokens: Mutex<BTreeMap<String, (String, Instant)>>,
    token_locks: Mutex<BTreeMap<String, Arc<Mutex<()>>>>,
    flows: Mutex<BTreeMap<String, JoinHandle<()>>>,
    pub stopped: AtomicBool,
}
impl GcloudAuth {
    pub fn new(
        config: Config,
        bound: Bound,
        connected: Connected,
        on_error: OnError,
        runner: Option<Arc<dyn CommandRunner>>,
    ) -> Arc<Self> {
        Arc::new(Self {
            config,
            bound,
            connected,
            on_error,
            runner: runner.unwrap_or_else(|| Arc::new(NativeCommandRunner::default())),
            tokens: Mutex::new(BTreeMap::new()),
            token_locks: Mutex::new(BTreeMap::new()),
            flows: Mutex::new(BTreeMap::new()),
            stopped: AtomicBool::new(false),
        })
    }
    pub fn status(&self) -> Value {
        match gcloud_path(&self.config) {
            Ok(_) => json!({"ready":true,"message":null}),
            Err(e) => json!({"ready":false,"message":e.message}),
        }
    }
    pub fn pending(&self, id: &str) -> bool {
        self.flows.lock().unwrap().contains_key(id)
    }
    pub fn command(&self, arguments: &[String], timeout: Duration) -> Result<String> {
        require(
            !self.stopped.load(Ordering::Acquire),
            "cancelled",
            "Google 연결을 중단했습니다.",
        )?;
        let mut argv = vec![gcloud_path(&self.config)?.into_os_string()];
        argv.extend(arguments.iter().map(OsString::from));
        argv.extend(["--quiet".into(), "--user-output-enabled".into()]);
        let result = self
            .runner
            .run(&argv, &sdk_environment(), timeout, &self.stopped)?;
        require(
            !self.stopped.load(Ordering::Acquire),
            "cancelled",
            "Google 연결을 중단했습니다.",
        )?;
        if result.code != 0 {
            return Err(sdk_error(&result.stderr));
        }
        require(
            result.stdout.chars().count() <= 65536,
            "gcloud_response",
            "gcloud 인증 응답을 확인하지 못했습니다.",
        )?;
        Ok(result.stdout)
    }
    pub fn accounts(&self) -> Result<Value> {
        let values = crate::backend::json::decode(&self.command(
            &["auth".into(), "list".into(), "--format=json".into()],
            Duration::from_secs(45),
        )?)
        .map_err(|_| {
            error(
                "gcloud_response",
                "gcloud 로그인 계정 목록을 확인하지 못했습니다.",
                false,
            )
        })?;
        require(
            values.is_array(),
            "gcloud_response",
            "gcloud 로그인 계정 목록을 확인하지 못했습니다.",
        )?;
        let mut accounts = Vec::new();
        for value in array(&values) {
            let account = account_name(text(value, "account")).map_err(|_| {
                error(
                    "gcloud_response",
                    "gcloud 로그인 계정 목록을 확인하지 못했습니다.",
                    false,
                )
            })?;
            accounts.push(json!({"account":account,"active":value["status"]=="ACTIVE"}))
        }
        Ok(json!(accounts))
    }
    pub fn resolve_account(
        &self,
        id: &str,
        requested: Option<&str>,
        allow_empty: bool,
    ) -> Result<Option<String>> {
        if let Some(requested) = requested.filter(|s| !s.is_empty()) {
            return Ok(Some(account_name(requested)?.into()));
        }
        if let Some(bound) = (self.bound)(id)?.filter(|s| !s.is_empty()) {
            return Ok(Some(account_name(&bound)?.into()));
        }
        let accounts = self.accounts()?;
        let values = array(&accounts);
        let active = values
            .iter()
            .filter(|v| v["active"] == true)
            .collect::<Vec<_>>();
        if active.len() == 1 {
            return Ok(Some(text(active[0], "account").into()));
        }
        if values.len() == 1 {
            return Ok(Some(text(&values[0], "account").into()));
        }
        if values.is_empty() {
            if allow_empty {
                return Ok(None);
            }
            return Err(error(
                "unauthenticated",
                "gcloud에 로그인한 Google 계정이 없습니다. Google 로그인을 진행해 주세요.",
                false,
            ));
        }
        Err(error(
            "account",
            "사용할 Google 계정을 입력해 주세요. 연결 뒤에는 이 계정을 고정해 사용합니다.",
            false,
        ))
    }
    pub fn token_for(&self, account: &str) -> Result<String> {
        account_name(account)?;
        let lock = self
            .token_locks
            .lock()
            .unwrap()
            .entry(account.into())
            .or_default()
            .clone();
        let _guard = lock.lock().unwrap();
        require(
            !self.stopped.load(Ordering::Acquire),
            "cancelled",
            "Google 연결을 중단했습니다.",
        )?;
        if let Some((token, _)) = self
            .tokens
            .lock()
            .unwrap()
            .get(account)
            .filter(|(_, at)| *at > Instant::now())
        {
            return Ok(token.clone());
        }
        let token = self.command(
            &[
                "auth".into(),
                "print-access-token".into(),
                format!("--account={account}"),
                "--format=value(token)".into(),
            ],
            Duration::from_secs(45),
        )?;
        let token = token.trim_matches(unicode::python_space);
        require(
            (12..=16384).contains(&token.len())
                && token
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b"._~+/-".contains(&b)),
            "gcloud_response",
            "gcloud 액세스 토큰을 확인하지 못했습니다.",
        )?;
        require(
            !self.stopped.load(Ordering::Acquire),
            "cancelled",
            "Google 연결을 중단했습니다.",
        )?;
        self.tokens.lock().unwrap().insert(
            account.into(),
            (token.into(), Instant::now() + Duration::from_secs(30)),
        );
        Ok(token.into())
    }
    pub fn access_token(&self, id: &str) -> Result<String> {
        let account = (self.bound)(id)?.filter(|s| !s.is_empty()).ok_or_else(|| {
            error(
                "unauthenticated",
                "Google 연결이 필요합니다. 사용할 gcloud 계정을 연결해 주세요.",
                false,
            )
        })?;
        self.token_for(&account)
    }
    pub fn invalidate(&self, id: &str) -> Result<()> {
        if let Some(account) = (self.bound)(id)? {
            self.tokens.lock().unwrap().remove(&account);
        }
        Ok(())
    }
    pub fn connect(&self, id: &str, requested: Option<&str>) -> Result<()> {
        let account = self.resolve_account(id, requested, false)?.unwrap();
        let token = self.token_for(&account)?;
        (self.connected)(id, &account, &token)
    }
    pub fn begin(self: &Arc<Self>, id: &str, requested: Option<&str>) -> Result<()> {
        require(
            self.flows.lock().unwrap().is_empty(),
            "auth_pending",
            "진행 중인 Google 로그인을 먼저 마쳐 주세요.",
        )?;
        let account = self.resolve_account(id, requested, true)?;
        let mut flows = self.flows.lock().unwrap();
        require(
            !self.stopped.load(Ordering::Acquire) && flows.is_empty(),
            "auth_pending",
            "Google 연결 상태를 다시 확인해 주세요.",
        )?;
        let auth = self.clone();
        let id = id.to_owned();
        let task_id = id.clone();
        let thread = crate::backend::worker_thread("drive-gcloud-login").spawn(move || {
            let result = (|| {
                let mut args = vec!["auth".into(), "login".into()];
                args.extend(account.iter().cloned());
                args.extend([
                    "--enable-gdrive-access".into(),
                    "--force".into(),
                    "--no-activate".into(),
                ]);
                auth.command(&args, Duration::from_secs(300))?;
                let selected = match account {
                    Some(s) => s,
                    None => auth.resolve_account(&task_id, None, false)?.unwrap(),
                };
                auth.tokens.lock().unwrap().remove(&selected);
                let token = auth.token_for(&selected)?;
                (auth.connected)(&task_id, &selected, &token)
            })();
            if let Err(e) = result {
                if e.code != "cancelled" {
                    (auth.on_error)(&task_id, e)
                }
            }
            auth.flows.lock().unwrap().remove(&task_id);
        })?;
        flows.insert(id, thread);
        Ok(())
    }
    pub fn stop(&self) {
        self.stopped.store(true, Ordering::Release);
        self.runner.stop();
        let threads = std::mem::take(&mut *self.flows.lock().unwrap());
        for (_, thread) in threads {
            let _ = thread.join();
        }
        self.tokens.lock().unwrap().clear();
    }
}
