//! Explicit preparation and lifecycle of private analysis-only runs.
mod process;
use super::{
    evidence::{self, EvidenceRequest, MANIFEST_VERSION},
    guidance, invalid, presentation, required, text, usage, values,
};
use crate::backend::{
    clock, db, json as codec, maintenance, storage, BackendError, Config, Result,
};
use chrono::{DateTime, Utc};
use rusqlite::{params, params_from_iter, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    ffi::OsString,
    fs::{self, OpenOptions},
    os::unix::fs::{DirBuilderExt, OpenOptionsExt},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread,
};
pub const RUNNER_POLICY_VERSION: &str = "personal-insight-cli-v3-bootstrap";
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerChoice {
    pub runner: String,
    pub label: String,
    pub model: String,
    pub codex_home: PathBuf,
    pub profile: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrepareRequest {
    pub mode: String,
    pub question: Option<String>,
    pub runner: String,
}
pub fn runner_choices(config: &Config) -> Result<Vec<RunnerChoice>> {
    let home = std::env::var_os("LOCALBRAIN_INSIGHT_CODEX_HOME")
        .filter(|s| !s.is_empty())
        .or_else(|| std::env::var_os("CODEX_HOME").filter(|s| !s.is_empty()))
        .map(PathBuf::from);
    let model = std::env::var("LOCALBRAIN_INSIGHT_CODEX_MODEL").ok();
    runner_choices_with(config, home.as_deref(), model.as_deref())
}
/// Explicit bindings avoid process-global environment changes in callers/tests.
pub fn runner_choices_with(
    config: &Config,
    configured_home: Option<&Path>,
    configured_model: Option<&str>,
) -> Result<Vec<RunnerChoice>> {
    let home = if let Some(home) = configured_home {
        storage::files::resolve(&storage::files::expand(home, config))?
    } else {
        let company = config.home_dir.join(".codex-company");
        if company.is_dir() {
            company
        } else {
            config.home_dir.join(".codex")
        }
    };
    if !home.is_dir() || maintenance::runner_executable(config, "codex").is_none() {
        return Ok(vec![]);
    }
    let profile = if home
        .file_name()
        .is_some_and(|name| name == ".codex-company")
    {
        "Codex Company"
    } else {
        "Codex"
    };
    Ok(vec![RunnerChoice {
        runner: "codex".into(),
        label: format!("Codex CLI · {profile}"),
        model: configured_model.unwrap_or("gpt-6-astra").into(),
        codex_home: home,
        profile: profile.into(),
    }])
}
pub fn valid_run_id(id: &str) -> bool {
    id.strip_prefix("ins-").is_some_and(|id| {
        id.len() == 16
            && id
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}
pub fn get_insight_run(connection: &Connection, id: &str) -> Result<Option<Value>> {
    if !valid_run_id(id) {
        return Ok(None);
    }
    db::row(
        connection,
        "SELECT * FROM personal_insight_runs WHERE id=?",
        [id],
    )
}
pub fn list_insight_runs(
    connection: &Connection,
    limit: usize,
    before: Option<&str>,
) -> Result<Vec<Value>> {
    let limit = i64::try_from(limit).map_err(|_| invalid("Run limit exceeds supported range"))?;
    if let Some(anchor) = before
        .filter(|id| valid_run_id(id))
        .map(|id| {
            db::row(
                connection,
                "SELECT created_at,id FROM personal_insight_runs WHERE id=?",
                [id],
            )
        })
        .transpose()?
        .flatten()
    {
        return db::rows(connection,"SELECT * FROM personal_insight_runs WHERE created_at<? OR (created_at=? AND id<?) ORDER BY created_at DESC,id DESC LIMIT ?",params![required(&anchor,"created_at")?,required(&anchor,"created_at")?,required(&anchor,"id")?,limit]);
    }
    db::rows(
        connection,
        "SELECT * FROM personal_insight_runs ORDER BY created_at DESC,id DESC LIMIT ?",
        [limit],
    )
}
pub fn run_root(config: &Config, id: &str) -> Result<PathBuf> {
    if !valid_run_id(id) {
        return Err(invalid("Invalid Run ID"));
    }
    let path = config.data_dir.join("personal-insight-runs").join(id);
    if path.to_str().is_none() {
        return Err(invalid("Run artifact path must be Unicode"));
    }
    Ok(path)
}
fn runner_settings(choice: &RunnerChoice) -> Result<Value> {
    let home = choice
        .codex_home
        .to_str()
        .ok_or_else(|| invalid("Codex profile path must be Unicode"))?;
    Ok(
        json!({"policy_version":RUNNER_POLICY_VERSION,"codex_home":home,"profile":choice.profile,"reasoning_effort":"high","service_tier":"standard","tools":"disabled","native_session_persistence":false,"network_tools":false,"filesystem_access":"run-artifacts-and-cli-read-only","structured_result":true}),
    )
}
fn private_write(path: &Path, content: &str) -> Result<()> {
    storage::files::atomic_write(path, content.as_bytes())
}
pub(super) fn private_binary(path: &Path) -> Result<fs::File> {
    Ok(OpenOptions::new()
        .create_new(true)
        .write(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?)
}
/// Creates only the requested queued Run and private artifacts. It never starts
/// an analyzer; the host commits its transaction before calling `start`.
pub fn prepare_insight_run(
    connection: &Connection,
    config: &Config,
    request: &PrepareRequest,
    choices: &[RunnerChoice],
    requested_at: DateTime<Utc>,
) -> Result<String> {
    let choice = choices
        .iter()
        .rev()
        .find(|c| c.runner == request.runner)
        .ok_or_else(|| invalid("선택한 분석 실행기를 사용할 수 없습니다."))?;
    let mut evidence_request = EvidenceRequest::new(&request.mode, requested_at);
    evidence_request.question = request.question.clone();
    evidence_request.timezone = config.timezone_name.clone();
    let manifest = evidence::build_insight_evidence_manifest(connection, &evidence_request)?;
    if manifest["coverage"]["selected_excerpts"] == 0 {
        return Err(invalid(
            "분석할 업무 세션 메시지가 없습니다. 먼저 Sessions에서 동기화해 주세요.",
        ));
    }
    let bundle = guidance::build_guide_bundle(&manifest)?;
    let mut options = runner_settings(choice)?;
    options["guide"] = guidance::guide_metadata(&bundle);
    options["sampling_description"] = json!(presentation::sampling_description(&manifest));
    options["usage_source_id"] =
        usage::insight_usage_source(connection, config, &options)?["id"].clone();
    let id = format!("ins-{}", &uuid::Uuid::new_v4().simple().to_string()[..16]);
    let root = run_root(config, &id)?;
    storage::files::private_directory(root.parent().unwrap(), config)?;
    fs::DirBuilder::new().mode(0o700).create(&root)?;
    let result = (|| -> Result<()> {
        let paths = [
            ("evidence_path", "evidence.json"),
            ("prompt_path", "prompt.md"),
            ("response_path", "response.json"),
            ("report_path", "report.md"),
            ("stream_path", "stream.jsonl"),
            ("stderr_path", "stderr.log"),
        ]
        .into_iter()
        .map(|(key, file)| (key, root.join(file)))
        .collect::<BTreeMap<_, _>>();
        private_write(
            &paths["evidence_path"],
            &serde_json::to_string_pretty(&manifest)?,
        )?;
        private_write(
            &paths["prompt_path"],
            &presentation::prompt(&manifest, &bundle)?,
        )?;
        let selected = values(&bundle["playbooks"])
            .iter()
            .map(|p| required(p, "id").map(str::to_owned))
            .collect::<Result<Vec<_>>>()?;
        private_write(
            &root.join("response-schema.json"),
            &codec::encode_http(&guidance::result_schema(
                &selected,
                guidance::report_version_for_guide(&bundle)?,
            )?)?,
        )?;
        let now = clock::isoformat(requested_at);
        connection.execute("INSERT INTO personal_insight_runs(id,mode,question,status,runner,model,settings_json,guide_version,evidence_version,evidence_path,prompt_path,response_path,report_path,stream_path,stderr_path,coverage_json,created_at,updated_at) VALUES (?,?,?,'queued',?,?,?,?,?,?,?,?,?,?,?,?,?,?)",params![id,request.mode,manifest["scope"]["question"].as_str(),request.runner,choice.model,codec::encode_http(&options)?,guidance::CORE_VERSION,MANIFEST_VERSION,paths["evidence_path"].to_string_lossy(),paths["prompt_path"].to_string_lossy(),paths["response_path"].to_string_lossy(),paths["report_path"].to_string_lossy(),paths["stream_path"].to_string_lossy(),paths["stderr_path"].to_string_lossy(),codec::encode_http(&manifest["coverage"])?,now,now])?;
        Ok(())
    })();
    if let Err(error) = result {
        fs::remove_dir_all(&root)?;
        return Err(error);
    }
    Ok(id)
}
pub fn runner_args(config: &Config, run: &Value, executable: &Path) -> Result<Vec<OsString>> {
    let executable = storage::files::resolve(&storage::files::expand(executable, config))?;
    let path = executable
        .to_str()
        .ok_or_else(|| invalid("Runner executable path must be Unicode"))?;
    let filesystem=format!("permissions.external-sync.filesystem={{\":minimal\"=\"read\",\":workspace_roots\"={{\".\"=\"read\"}},{path}=\"read\"}}",path=serde_json::to_string(path)?);
    let root = run_root(config, required(run, "id")?)?;
    let schema_path = root.join("response-schema.json");
    let options = codec::decode(required(run, "settings_json")?)?;
    let guide = &options["guide"];
    let selected = values(&guide["playbooks"])
        .iter()
        .map(|book| required(book, "id").map(str::to_owned))
        .collect::<Result<Vec<_>>>()?;
    let schema = guidance::result_schema(&selected, guidance::report_version_for_guide(guide)?)?;
    if schema_path.is_file() {
        if codec::decode(&fs::read_to_string(&schema_path)?)? != schema {
            return Err(invalid("분석 응답 규격이 실행 기록과 일치하지 않습니다."));
        }
    } else {
        private_write(&schema_path, &codec::encode_http(&schema)?)?;
    }
    Ok(vec![
        executable.into_os_string(),
        "exec".into(),
        "--json".into(),
        "--ephemeral".into(),
        "--ignore-user-config".into(),
        "--ignore-rules".into(),
        "--skip-git-repo-check".into(),
        "-C".into(),
        root.into_os_string(),
        "-m".into(),
        required(run, "model")?.into(),
        "-c".into(),
        "model_reasoning_effort=\"high\"".into(),
        "-c".into(),
        "service_tier=\"default\"".into(),
        "-c".into(),
        "default_permissions=\"external-sync\"".into(),
        "-c".into(),
        filesystem.into(),
        "-c".into(),
        "permissions.external-sync.network.enabled=false".into(),
        "-c".into(),
        "web_search=\"disabled\"".into(),
        "-c".into(),
        "shell_environment_policy.inherit=\"none\"".into(),
        "--output-schema".into(),
        schema_path.into_os_string(),
        "--output-last-message".into(),
        required(run, "response_path")?.into(),
        "-".into(),
    ])
}
pub fn validate_result(value: &Value, manifest: &Value, run: &Value) -> Result<Value> {
    let options = codec::decode(required(run, "settings_json")?)?;
    let guide = &options["guide"];
    if guide["core_version"] != run["guide_version"] {
        return Err(invalid("분석 가이드 버전이 실행 기록과 일치하지 않습니다."));
    }
    guidance::validate_guided_result(value,manifest,guide).map_err(|error|if error.code=="insight-supplied-message"{invalid("이미 전문이 제공된 메시지를 다시 요청해 보고서를 만들지 못했습니다. 실행 기록과 사용량은 보존되며 자동으로 다시 실행하지 않습니다.")}else{error})
}
pub(super) fn update(
    connection: &Connection,
    id: &str,
    packet: &Value,
    at: DateTime<Utc>,
    active_only: bool,
) -> Result<usize> {
    let fields = packet
        .as_object()
        .ok_or_else(|| invalid("Run update must be an object"))?;
    let mut fields = fields.clone();
    fields.insert("updated_at".into(), json!(clock::isoformat(at)));
    let allowed = [
        "status",
        "title",
        "resolved_model",
        "pid",
        "started_at",
        "completed_at",
        "usage_json",
        "error",
        "updated_at",
    ];
    let mut assignments = vec![];
    let mut params = vec![];
    for (key, value) in fields {
        if !allowed.contains(&key.as_str()) {
            return Err(invalid("unsupported insight Run update field"));
        }
        assignments.push(format!("{key}=?"));
        params.push(crate::backend::usage::sql_value(&value)?);
    }
    params.push(id.to_owned().into());
    Ok(connection.execute(
        &format!(
            "UPDATE personal_insight_runs SET {} WHERE id=?{}",
            assignments.join(","),
            if active_only {
                " AND status IN ('queued','running')"
            } else {
                ""
            }
        ),
        params_from_iter(params),
    )?)
}
struct Job {
    cancelled: AtomicBool,
    handle: Mutex<Option<thread::JoinHandle<()>>>,
}
/// Owns only explicitly started jobs. New/read/reconcile never launch a child.
pub struct InsightRuntime {
    config: Config,
    jobs: Mutex<BTreeMap<String, Arc<Job>>>,
    stopping: AtomicBool,
}
impl InsightRuntime {
    pub fn new(config: Config) -> Self {
        Self {
            config,
            jobs: Mutex::new(BTreeMap::new()),
            stopping: AtomicBool::new(false),
        }
    }
    pub fn config(&self) -> &Config {
        &self.config
    }
    pub fn start(self: &Arc<Self>, id: &str) -> Result<()> {
        if self.stopping.load(Ordering::Acquire) {
            return Err(BackendError::conflict("Insights runtime is shutting down"));
        }
        if !valid_run_id(id) {
            return Err(invalid("Invalid Run ID"));
        }
        let mut jobs = self.jobs.lock().unwrap();
        if jobs.contains_key(id) {
            return Err(BackendError::conflict("Analysis Run already started"));
        }
        let job = Arc::new(Job {
            cancelled: AtomicBool::new(false),
            handle: Mutex::new(None),
        });
        jobs.insert(id.into(), job.clone());
        let runtime = self.clone();
        let id = id.to_owned();
        let worker_job = job.clone();
        let worker_id = id.clone();
        let handle = crate::backend::worker_thread("insight-analysis").spawn(move || {
            runtime.execute(&worker_id, &worker_job);
            runtime.jobs.lock().unwrap().remove(&worker_id);
        });
        match handle {
            Ok(handle) => {
                *job.handle.lock().unwrap() = Some(handle);
                Ok(())
            }
            Err(error) => {
                jobs.remove(&id);
                Err(error.into())
            }
        }
    }
    pub fn cancel(&self, connection: &Connection, id: &str) -> Result<bool> {
        let Some(run) = get_insight_run(connection, id)? else {
            return Ok(false);
        };
        if !["queued", "running"].contains(&text(&run["status"], "")) {
            return Ok(false);
        }
        if let Some(job) = self.jobs.lock().unwrap().get(id) {
            job.cancelled.store(true, Ordering::Release);
        }
        Ok(update(
            connection,
            id,
            &json!({"status":"cancelled","pid":null,"completed_at":clock::isoformat(Utc::now())}),
            Utc::now(),
            true,
        )? > 0)
    }
    pub fn reconcile(&self, connection: &Connection) -> Result<usize> {
        self.stopping.store(false, Ordering::Release);
        let now = clock::isoformat(Utc::now());
        let changed=connection.execute("UPDATE personal_insight_runs SET status='interrupted',pid=NULL,completed_at=?,updated_at=?,error='LocalBrain이 실행 중 재시작되었습니다.' WHERE status IN ('queued','running')",params![now,now])?;
        usage::recover_insight_usage(connection, &self.config)?;
        Ok(changed)
    }
    pub fn shutdown(&self) -> Result<()> {
        self.stopping.store(true, Ordering::Release);
        let jobs = self
            .jobs
            .lock()
            .unwrap()
            .values()
            .cloned()
            .collect::<Vec<_>>();
        for job in &jobs {
            job.cancelled.store(true, Ordering::Release);
        }
        for job in jobs {
            if let Some(handle) = job.handle.lock().unwrap().take() {
                handle.join().map_err(|_| {
                    BackendError::new(500, "insight-worker", "Analysis worker panicked")
                })?;
            }
        }
        Ok(())
    }
    fn execute(&self, id: &str, job: &Job) {
        let result = self.execute_inner(id, job);
        if let Err(error) = result {
            if let Ok(connection) = db::connect(&self.config) {
                let cancelled =
                    job.cancelled.load(Ordering::Acquire) || self.stopping.load(Ordering::Acquire);
                let status = if cancelled {
                    if self.stopping.load(Ordering::Acquire) {
                        "interrupted"
                    } else {
                        "cancelled"
                    }
                } else {
                    "failed"
                };
                let mut packet =
                    json!({"status":status,"pid":null,"completed_at":clock::isoformat(Utc::now())});
                if !cancelled {
                    packet["error"] = json!(error.message.chars().take(1000).collect::<String>());
                }
                let _ = update(&connection, id, &packet, Utc::now(), true);
            }
        }
    }
    fn execute_inner(&self, id: &str, job: &Job) -> Result<()> {
        let connection = db::connect(&self.config)?;
        let Some(mut run) = get_insight_run(&connection, id)? else {
            return Ok(());
        };
        if run["status"] != "queued" {
            return Ok(());
        }
        if job.cancelled.load(Ordering::Acquire) {
            return Err(BackendError::conflict("Run cancelled before launch"));
        }
        let executable = maintenance::runner_executable(&self.config, required(&run, "runner")?)
            .ok_or_else(|| invalid("선택한 분석 실행기를 찾을 수 없습니다."))?;
        let options = codec::decode(required(&run, "settings_json")?)?;
        let home = Path::new(required(&options, "codex_home")?);
        if !home.is_dir() {
            return Err(invalid("선택한 Codex 프로필을 찾을 수 없습니다."));
        }
        usage::insight_usage_source(&connection, &self.config, &options)?;
        let args = runner_args(&self.config, &run, &executable)?;
        let prompt = fs::read_to_string(required(&run, "prompt_path")?)?;
        drop(connection);
        let output = process::execute(self, job, &mut run, args, prompt, home)?;
        let connection = db::connect(&self.config)?;
        let current = get_insight_run(&connection, id)?;
        if current
            .as_ref()
            .is_none_or(|run| !["queued", "running"].contains(&text(&run["status"], "")))
        {
            return Ok(());
        }
        if output.return_code != 0 {
            return Err(invalid(&format!(
                "{} 실행이 종료 코드 {}로 끝났습니다. 실행 기록은 보존됩니다.",
                required(&run, "runner")?,
                output.return_code
            )));
        }
        let manifest = codec::decode(&fs::read_to_string(required(&run, "evidence_path")?)?)?;
        let value = fs::read_to_string(required(&run, "response_path")?)
            .ok()
            .and_then(|value| codec::decode(&value).ok())
            .filter(Value::is_object)
            .unwrap_or(Value::Null);
        let result = validate_result(&value, &manifest, &run)?;
        let resolved = output.resolved_model.or_else(|| {
            output
                .final_event
                .as_ref()
                .and_then(|event| event["modelUsage"].as_object())
                .filter(|models| models.len() == 1)
                .and_then(|models| models.keys().next().cloned())
        });
        run["resolved_model"] = json!(resolved);
        private_write(
            &run_root(&self.config, id)?.join("validated-result.json"),
            &serde_json::to_string_pretty(&result)?,
        )?;
        private_write(
            Path::new(required(&run, "report_path")?),
            &presentation::render_report(&run, &manifest, &result)?,
        )?;
        update(
            &connection,
            id,
            &json!({"status":if result["outcome"]=="findings"{"completed"}else{"no_finding"},"title":text(&result["title"],"").chars().take(160).collect::<String>(),"resolved_model":resolved,"pid":null,"completed_at":clock::isoformat(Utc::now()),"error":null}),
            Utc::now(),
            true,
        )?;
        Ok(())
    }
}
