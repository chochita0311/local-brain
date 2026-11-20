//! Feature-neutral Run tracking. Features own preparation and terminal apply.
mod process;
use crate::backend::{db, now, storage, BackendError, Config, Result};
pub use process::{extract_text, extract_tool_uses, is_mcp_tool, ProcessOutput, ProcessSpec};
use rusqlite::{params_from_iter, Connection};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    path::PathBuf,
    process::Child,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex, RwLock,
    },
    thread,
    time::{Duration, Instant},
};

pub fn get_run(connection: &Connection, run_id: &str) -> Result<Option<Value>> {
    db::row(connection,"SELECT maintenance_runs.*,workstreams.name AS workstream_name FROM maintenance_runs LEFT JOIN workstreams ON workstreams.id=maintenance_runs.workstream_id WHERE maintenance_runs.id=?",[run_id])
}
pub fn read_run_output(run: &Value) -> Result<String> {
    for key in ["result_path", "stderr_path"] {
        if let Some(path) = run[key].as_str() {
            let path = std::path::Path::new(path);
            if path.is_file() {
                return Ok(String::from_utf8_lossy(&fs::read(path)?).into_owned());
            }
        }
    }
    Ok(String::new())
}
pub fn run_output_placeholder(status: &str) -> &'static str {
    match status {
        "prepared" => "아직 실행하지 않았습니다.",
        "queued" => "Claude 실행을 준비하고 있습니다.",
        "running" | "cancelling" => "아직 표시할 실행 출력이 없습니다.",
        _ => "표시할 실행 출력이 없습니다.",
    }
}
/// Participates in the feature's existing transaction, including atomic result
/// application. Column identifiers are internal schema names, never SQL text.
pub fn update_run_row(connection: &Connection, run_id: &str, values: &Value) -> Result<()> {
    let Some(values) = values.as_object() else {
        return Err(BackendError::invalid(
            "run",
            "Run updates must be an object",
        ));
    };
    if values.is_empty() {
        return Ok(());
    }
    let columns = db::rows(connection, "PRAGMA table_info(maintenance_runs)", [])?
        .into_iter()
        .filter_map(|row| row["name"].as_str().map(str::to_owned))
        .collect::<std::collections::BTreeSet<_>>();
    let mut updates = values.clone();
    updates.insert("updated_at".into(), now().into());
    let mut assignments = Vec::new();
    let mut parameters = Vec::new();
    for (column, value) in updates {
        if column == "id" || !columns.contains(&column) {
            return Err(BackendError::invalid(
                "run",
                format!("Unknown Run field: {column}"),
            ));
        }
        assignments.push(format!("\"{column}\"=?"));
        parameters.push(crate::backend::usage::sql_value(&value)?);
    }
    parameters.push(run_id.to_owned().into());
    connection.execute(
        &format!(
            "UPDATE maintenance_runs SET {} WHERE id=?",
            assignments.join(",")
        ),
        params_from_iter(parameters),
    )?;
    Ok(())
}
pub fn structured_result(event: Option<&Value>) -> Option<Value> {
    scoped_structured_result(event, None).ok().flatten()
}
/// Keep parser scope until the selected result is materialized; ignored event
/// metadata may contain Python-admitted exceptional scalars.
fn scoped_structured_result(
    event: Option<&Value>,
    scope: Option<&crate::backend::json::Scope>,
) -> Result<Option<Value>> {
    let Some(event) = event else { return Ok(None) };
    let value = &event["structured_output"];
    if value.is_object() {
        if let Some(scope) = scope {
            scope.materialized(value)?;
        }
        return Ok(Some(value.clone()));
    }
    let raw = if let Some(raw) = value.as_str() {
        Some(raw)
    } else {
        event["result"].as_str()
    };
    let Some(raw) = raw else { return Ok(None) };
    let selected_scope = crate::backend::json::Scope::for_document(raw);
    let selected_scope = scope.unwrap_or(&selected_scope);
    let parsed = match selected_scope.parse(raw) {
        Ok(value) => value,
        Err(error) if error.is_io() => {
            return Err(BackendError::invalid("json_scalar", error.to_string()))
        }
        Err(_) => return Ok(None),
    };
    if !parsed.is_object() {
        return Ok(None);
    }
    selected_scope.materialized(&parsed)?;
    Ok(Some(parsed))
}
pub fn runner_executable(config: &Config, runner: &str) -> Option<PathBuf> {
    let configured = match runner {
        "claude" => &config.claude_bin,
        "codex" => &config.codex_bin,
        _ => return None,
    };
    if let Some(path) = configured {
        let path = storage::files::expand(path, config);
        return path.is_file().then_some(path);
    }
    use std::os::unix::fs::PermissionsExt;
    std::env::split_paths(&std::env::var_os("PATH")?)
        .map(|path| path.join(runner))
        .find(|path| {
            fs::metadata(path)
                .is_ok_and(|info| info.is_file() && info.permissions().mode() & 0o111 != 0)
        })
}
#[derive(Default)]
struct Job {
    cancelled: AtomicBool,
    finished: AtomicBool,
}
type Scanner = Arc<dyn Fn(&Config, &str) -> Result<()> + Send + Sync>;
pub struct TaskRuntime {
    config: Config,
    jobs: Mutex<BTreeMap<String, Arc<Job>>>,
    pub(super) processes: Mutex<BTreeMap<String, Arc<Mutex<Child>>>>,
    scanner: RwLock<Option<Scanner>>,
    stopping: AtomicBool,
}
impl TaskRuntime {
    pub fn new(config: Config) -> Self {
        Self {
            config,
            jobs: Mutex::new(BTreeMap::new()),
            processes: Mutex::new(BTreeMap::new()),
            scanner: RwLock::new(None),
            stopping: AtomicBool::new(false),
        }
    }
    pub fn config(&self) -> &Config {
        &self.config
    }
    pub fn set_scanner(
        &self,
        scanner: impl Fn(&Config, &str) -> Result<()> + Send + Sync + 'static,
    ) {
        *self.scanner.write().unwrap() = Some(Arc::new(scanner));
    }
    pub fn synchronize(&self, runner: &str) -> bool {
        self.scanner
            .read()
            .unwrap()
            .as_ref()
            .is_none_or(|scanner| scanner(&self.config, runner).is_ok())
    }
    pub fn update(&self, run_id: &str, values: &Value) -> Result<()> {
        let connection = db::connect(&self.config)?;
        update_run_row(&connection, run_id, values)
    }
    pub fn finalize(&self, run_id: &str, status: &str, values: &Value) -> Result<()> {
        let connection = db::connect(&self.config)?;
        let run = get_run(&connection, run_id)?
            .ok_or_else(|| BackendError::not_found("Run not found"))?;
        let mut values = values.as_object().cloned().unwrap_or_default();
        values.insert("status".into(), status.into());
        values.insert("completed_at".into(), now().into());
        connection.execute_batch("BEGIN IMMEDIATE")?;
        let result = update_run_row(&connection, run_id, &Value::Object(values));
        if result.is_ok() {
            connection.execute_batch("COMMIT")?;
        } else {
            connection.execute_batch("ROLLBACK")?;
            result?;
        }
        self.synchronize(run["runner"].as_str().unwrap_or("claude"));
        Ok(())
    }
    pub fn finalize_failed(&self, run_id: &str, error: &str) -> Result<()> {
        let error = tail(error, 4000);
        if let Err(failure) = self.finalize(run_id, "failed", &json!({"pid":null,"error":error})) {
            self.update(run_id,&json!({"status":"failed","pid":null,"completed_at":now(),"error":tail(&format!("{error} · Run finalization failed: {failure}"),4000)}))?;
        }
        Ok(())
    }
    pub fn reconcile_interrupted_runs(&self) -> Result<usize> {
        let connection = db::connect(&self.config)?;
        connection.execute_batch("BEGIN IMMEDIATE")?;
        let rows=db::rows(&connection,"SELECT id,runner FROM maintenance_runs WHERE status IN ('queued','running','cancelling') AND task_type IS NOT NULL AND stream_path IS NOT NULL",[])?;
        for row in &rows {
            update_run_row(
                &connection,
                row["id"].as_str().unwrap(),
                &json!({"status":"interrupted","pid":null,"completed_at":now(),"error":"LocalBrain restarted while the run was active."}),
            )?;
        }
        connection.execute_batch("COMMIT")?;
        let runners = rows
            .iter()
            .filter_map(|row| row["runner"].as_str())
            .collect::<std::collections::BTreeSet<_>>();
        for runner in runners {
            self.synchronize(runner);
        }
        Ok(rows.len())
    }
    pub fn start(
        self: &Arc<Self>,
        run_id: &str,
        execution: impl FnOnce(Arc<Self>) -> Result<()> + Send + 'static,
    ) -> Result<()> {
        if self.stopping.load(Ordering::Acquire) {
            return Err(BackendError::conflict("Task Runner is stopping"));
        }
        let mut jobs = self.jobs.lock().unwrap();
        if jobs.contains_key(run_id) {
            return Err(BackendError::conflict("Run is already active"));
        }
        let job = Arc::new(Job::default());
        jobs.insert(run_id.into(), job.clone());
        let runtime = self.clone();
        let id = run_id.to_owned();
        let spawn =
            crate::backend::worker_thread(format!("localbrain-run-{run_id}")).spawn(move || {
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    execution(runtime.clone())
                }));
                match result {
                    Ok(Ok(())) => {}
                    Ok(Err(error)) => {
                        let _ = if job.cancelled.load(Ordering::Acquire) {
                            runtime.finalize(&id, "cancelled", &json!({"pid":null}))
                        } else {
                            runtime.finalize_failed(&id, &error.to_string())
                        };
                    }
                    Err(_) => {
                        let _ = runtime.finalize_failed(&id, "Task Runner worker failed.");
                    }
                }
                job.finished.store(true, Ordering::Release);
                runtime.jobs.lock().unwrap().remove(&id);
            });
        if let Err(error) = spawn {
            jobs.remove(run_id);
            return Err(error.into());
        }
        Ok(())
    }
    pub fn is_cancelled(&self, run_id: &str) -> bool {
        self.stopping.load(Ordering::Acquire)
            || self
                .jobs
                .lock()
                .unwrap()
                .get(run_id)
                .is_some_and(|job| job.cancelled.load(Ordering::Acquire))
    }
    pub fn cancel(&self, run_id: &str) -> Result<bool> {
        let connection = db::connect(&self.config)?;
        let Some(run) = get_run(&connection, run_id)? else {
            return Ok(false);
        };
        if !["queued", "running", "cancelling"]
            .contains(&run["status"].as_str().unwrap_or_default())
        {
            return Ok(false);
        }
        let changed=connection.execute("UPDATE maintenance_runs SET status='cancelling',updated_at=? WHERE id=? AND status IN ('queued','running','cancelling')",rusqlite::params![now(),run_id])?;
        if changed == 0 {
            return Ok(false);
        }
        let job = self.jobs.lock().unwrap().get(run_id).cloned();
        if let Some(job) = &job {
            job.cancelled.store(true, Ordering::Release);
        }
        let process = self.processes.lock().unwrap().get(run_id).cloned();
        if let Some(process) = process {
            signal(&process, libc::SIGTERM)?;
            return Ok(true);
        }
        if job.is_none() {
            self.finalize(run_id, "cancelled", &json!({"pid":null}))?;
        }
        Ok(true)
    }
    pub fn shutdown(&self) -> Result<()> {
        self.stopping.store(true, Ordering::Release);
        let active = self
            .processes
            .lock()
            .unwrap()
            .iter()
            .map(|(id, child)| (id.clone(), child.clone()))
            .collect::<Vec<_>>();
        for job in self.jobs.lock().unwrap().values() {
            job.cancelled.store(true, Ordering::Release);
        }
        for (_, child) in &active {
            signal(child, libc::SIGTERM)?;
        }
        let started = Instant::now();
        while !self.jobs.lock().unwrap().is_empty() || !self.processes.lock().unwrap().is_empty() {
            if started.elapsed() > Duration::from_secs(11) {
                for (_, child) in &active {
                    signal(child, libc::SIGKILL)?;
                }
            }
            if started.elapsed() > Duration::from_secs(15) {
                return Err(BackendError::conflict(
                    "Task Runner did not stop within its shutdown deadline",
                ));
            }
            thread::sleep(Duration::from_millis(20));
        }
        let connection = db::connect(&self.config)?;
        connection.execute_batch("BEGIN IMMEDIATE")?;
        let mut runners = std::collections::BTreeSet::new();
        for (id, _) in &active {
            if let Some(run) = get_run(&connection, id)? {
                runners.insert(run["runner"].as_str().unwrap_or("claude").to_owned());
            }
            update_run_row(
                &connection,
                id,
                &json!({"status":"interrupted","pid":null,"completed_at":now(),"error":"LocalBrain stopped during the run."}),
            )?;
        }
        connection.execute_batch("COMMIT")?;
        for runner in runners {
            self.synchronize(&runner);
        }
        Ok(())
    }
}
fn tail(value: &str, limit: usize) -> String {
    let count = value.chars().count();
    value.chars().skip(count.saturating_sub(limit)).collect()
}
fn signal(process: &Arc<Mutex<Child>>, signal: i32) -> Result<()> {
    // Keep the Child handle locked through try_wait and signal. An unreaped
    // child retains its PID, so a stored or reused unrelated PID is never used.
    let mut process = process.lock().unwrap();
    if process.try_wait()?.is_none() {
        let result = unsafe { libc::kill(process.id() as libc::pid_t, signal) };
        if result != 0 {
            let error = std::io::Error::last_os_error();
            if error.raw_os_error() != Some(libc::ESRCH) {
                return Err(error.into());
            }
        }
    }
    Ok(())
}
