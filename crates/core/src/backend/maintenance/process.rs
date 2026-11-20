use super::{get_run, signal, TaskRuntime};
use crate::backend::{db, now, storage, unicode, BackendError, Result};
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    ffi::OsString,
    fs::{File, OpenOptions},
    io::{BufRead, BufReader, Read, Write},
    os::{
        fd::AsRawFd,
        unix::{fs::OpenOptionsExt, process::ExitStatusExt},
    },
    path::{Path, PathBuf},
    process::{Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread,
    time::{Duration, Instant},
};
type StdoutCapture = (
    Option<Value>,
    Option<crate::backend::json::Scope>,
    String,
    Vec<Value>,
);
#[derive(Debug, Clone)]
pub struct ProcessSpec {
    /// First argument is the executable. No shell is introduced by the host.
    pub arguments: Vec<OsString>,
    pub cwd: PathBuf,
    pub prompt: String,
    pub stream_path: PathBuf,
    pub result_path: Option<PathBuf>,
    pub stderr_path: PathBuf,
    pub mcp_call_budget: Option<i64>,
    /// Legacy features leave this unset. Explicit owners may bound their job.
    pub timeout: Option<Duration>,
}
#[derive(Clone)]
pub struct ProcessOutput {
    pub return_code: i32,
    pub final_event: Option<Value>,
    pub output: String,
    pub stderr: String,
    pub mcp_calls: Vec<Value>,
    final_event_scope: Option<crate::backend::json::Scope>,
}
impl std::fmt::Debug for ProcessOutput {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ProcessOutput")
            .field("return_code", &self.return_code)
            .field("final_event", &self.final_event)
            .field("output", &self.output)
            .field("stderr", &self.stderr)
            .field("mcp_calls", &self.mcp_calls)
            .finish()
    }
}
impl ProcessOutput {
    pub fn structured_result(&self) -> Result<Option<Value>> {
        super::scoped_structured_result(self.final_event.as_ref(), self.final_event_scope.as_ref())
    }
}

fn artifact(path: &Path, config: &crate::backend::Config) -> Result<File> {
    storage::files::private_directory(
        path.parent()
            .ok_or_else(|| BackendError::invalid("run", "Run artifact needs a parent directory"))?,
        config,
    )?;
    if path.symlink_metadata().is_ok() {
        storage::files::owned_file(path)?;
    }
    Ok(OpenOptions::new()
        .create(true)
        .append(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?)
}
fn nonblocking(stream: &impl AsRawFd) -> Result<()> {
    let fd = stream.as_raw_fd();
    let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
    if flags < 0 || unsafe { libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    Ok(())
}
/// Pipes are nonblocking so a detached descendant retaining stdout cannot keep
/// shutdown waiting forever after the owned child exits. Bytes already present
/// are drained before the final partial line is consumed.
fn lines(
    stream: impl Read,
    ended: &AtomicBool,
    mut visit: impl FnMut(&[u8]) -> Result<()>,
) -> Result<()> {
    let mut reader = BufReader::new(stream);
    let mut pending = Vec::new();
    loop {
        match reader.read_until(b'\n', &mut pending) {
            Ok(0) => {
                if !pending.is_empty() {
                    visit(&pending)?;
                }
                return Ok(());
            }
            Ok(_) => {
                visit(&pending)?;
                pending.clear();
            }
            Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                if ended.load(Ordering::Acquire) {
                    if !pending.is_empty() {
                        visit(&pending)?;
                    }
                    return Ok(());
                }
                thread::sleep(Duration::from_millis(10));
            }
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {}
            Err(error) => return Err(error.into()),
        }
    }
}
pub fn extract_text(event: &Value) -> Option<String> {
    if event["type"] == "assistant" {
        let chunks = event["message"]["content"]
            .as_array()?
            .iter()
            .filter(|item| item["type"] == "text")
            .filter_map(|item| item["text"].as_str())
            .map(|text| text.trim_matches(unicode::python_space))
            .filter(|text| !text.is_empty())
            .collect::<Vec<_>>();
        if !chunks.is_empty() {
            return Some(chunks.join("\n\n"));
        }
    }
    if event["type"] == "result" {
        return event["result"]
            .as_str()
            .map(|text| text.trim_matches(unicode::python_space))
            .filter(|text| !text.is_empty())
            .map(str::to_owned);
    }
    None
}
pub fn extract_tool_uses(event: &Value) -> Vec<Value> {
    if event["type"] != "assistant" {
        return Vec::new();
    }
    event["message"]["content"]
        .as_array()
        .into_iter()
        .flatten()
        .filter(|item| item["type"] == "tool_use" && item["name"].is_string())
        .map(|item| json!({"id":item["id"],"name":item["name"]}))
        .collect()
}
pub fn is_mcp_tool(name: &str) -> bool {
    let name = unicode::lowercase(name);
    name.starts_with("mcp__") || name.starts_with("mcp_")
}
impl TaskRuntime {
    pub fn execute_process(
        self: &Arc<Self>,
        run_id: &str,
        spec: ProcessSpec,
    ) -> Result<ProcessOutput> {
        if self.is_cancelled(run_id) {
            return Err(BackendError::conflict("Run was cancelled before launch"));
        }
        let executable = spec
            .arguments
            .first()
            .ok_or_else(|| BackendError::invalid("run", "Runner command is empty"))?;
        let run = get_run(&db::connect(self.config())?, run_id)?
            .ok_or_else(|| BackendError::not_found("Run not found"))?;
        if !["prepared", "queued", "running"].contains(&run["status"].as_str().unwrap_or_default())
        {
            return Err(BackendError::conflict("Run is not launchable"));
        }
        // Open all output artifacts before launching, so path refusal cannot
        // leave an untracked child behind.
        let mut raw = artifact(&spec.stream_path, self.config())?;
        let mut stderr_file = artifact(&spec.stderr_path, self.config())?;
        if let Some(path) = &spec.result_path {
            storage::files::private_directory(
                path.parent().ok_or_else(|| {
                    BackendError::invalid("run", "Run artifact needs a parent directory")
                })?,
                self.config(),
            )?;
            if path.symlink_metadata().is_ok() {
                storage::files::owned_file(path)?;
            }
        }
        let mut child = Command::new(executable)
            .args(&spec.arguments[1..])
            .current_dir(&spec.cwd)
            .env("LOCALBRAIN_RUN_ID", run_id)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        let mut stdin = child.stdin.take().expect("piped stdin");
        let stdout = child.stdout.take().expect("piped stdout");
        let stderr = child.stderr.take().expect("piped stderr");
        if let Err(error) = nonblocking(&stdout).and_then(|_| nonblocking(&stderr)) {
            let _ = child.kill();
            let _ = child.wait();
            return Err(error);
        }
        let process = Arc::new(Mutex::new(child));
        {
            let mut processes = self.processes.lock().unwrap();
            if processes.contains_key(run_id) {
                let mut child = process.lock().unwrap();
                let _ = child.kill();
                let _ = child.wait();
                return Err(BackendError::conflict("Run already has a process"));
            }
            processes.insert(run_id.into(), process.clone());
        }
        struct Lease<'a> {
            runtime: &'a TaskRuntime,
            id: &'a str,
            child: Arc<Mutex<std::process::Child>>,
            ended: Arc<AtomicBool>,
        }
        impl Drop for Lease<'_> {
            fn drop(&mut self) {
                self.ended.store(true, Ordering::Release);
                {
                    let mut child = self.child.lock().unwrap();
                    if child.try_wait().ok().flatten().is_none() {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                }
                self.runtime.processes.lock().unwrap().remove(self.id);
            }
        }
        let ended = Arc::new(AtomicBool::new(false));
        let _lease = Lease {
            runtime: self,
            id: run_id,
            child: process.clone(),
            ended: ended.clone(),
        };
        let connection = db::connect(self.config())?;
        let started_at = now();
        let changed=connection.execute("UPDATE maintenance_runs SET status=CASE WHEN status='cancelling' THEN status ELSE 'running' END,pid=?,started_at=?,error=NULL,updated_at=? WHERE id=? AND status IN ('prepared','queued','running','cancelling')",rusqlite::params![process.lock().unwrap().id(),started_at,started_at,run_id])?;
        if changed == 0 {
            return Err(BackendError::conflict(
                "Run became terminal before process launch",
            ));
        }
        let prompt = spec.prompt.into_bytes();
        let input = thread::spawn(move || stdin.write_all(&prompt));
        let runtime = self.clone();
        let id = run_id.to_owned();
        let stdout_ended = ended.clone();
        let stdout_failed = Arc::new(AtomicBool::new(false));
        let reader_failed = stdout_failed.clone();
        let output = crate::backend::worker_thread("task-output").spawn(move || -> Result<StdoutCapture> {
            let result = (|| {
                let mut chunks = Vec::new();
                let mut final_event = None;
                let mut final_event_scope=None;
                let mut calls = Vec::new();
                let mut seen = BTreeSet::new();
                lines(stdout, &stdout_ended, |line| {
                    let decoded = String::from_utf8_lossy(line);
                    let decoded = decoded.trim_end_matches('\n');
                    writeln!(raw, "{decoded}")?;
                    raw.flush()?;
                    let scope=crate::backend::json::Scope::for_document(decoded);
                    let event=match scope.parse(decoded){Ok(value)=>value,Err(error)if error.is_io()=>return Err(BackendError::invalid("json_scalar",error.to_string())),Err(_)=>return Ok(())};
                    if let Some(budget) = spec.mcp_call_budget {
                        for tool in extract_tool_uses(&event) {
                            scope.materialized(&tool)?;
                            let identity = if !tool["id"].is_null() && tool["id"] != "" {
                                tool["id"].to_string()
                            } else {
                                format!(
                                    "{}:{}",
                                    tool["name"].as_str().unwrap_or_default(),
                                    seen.len()
                                )
                            };
                            if !seen.insert(identity) {
                                continue;
                            }
                            if is_mcp_tool(tool["name"].as_str().unwrap_or_default()) {
                                calls.push(tool);
                                runtime.update(&id,&json!({"mcp_calls_used":calls.len(),"mcp_tool_calls_json":serde_json::to_string(&calls)?,"mcp_budget_exceeded":i32::from((calls.len() as i128)>i128::from(budget))}))?;
                            }
                        }
                    }
                    let text = extract_text(&event);
                    scope.materialized(&text)?;
                    if event["type"] == "result" {
                        final_event = Some(event);
                        final_event_scope=Some(scope);
                        if let Some(text) = text {
                            chunks = vec![text];
                        }
                    } else if let Some(text) = text {
                        if !chunks.contains(&text) {
                            chunks.push(text);
                        }
                    }
                    if !chunks.is_empty() {
                        if let Some(path) = &spec.result_path {
                            storage::files::atomic_write(path, chunks.join("\n\n").as_bytes())?;
                        }
                    }
                    Ok(())
                })?;
                Ok((final_event,final_event_scope, chunks.join("\n\n"), calls))
            })();
            if result.is_err() {
                reader_failed.store(true, Ordering::Release);
            }
            result
        })?;
        let stderr_ended = ended.clone();
        let errors = thread::spawn(move || -> Result<String> {
            let mut result = String::new();
            lines(stderr, &stderr_ended, |line| {
                let decoded = String::from_utf8_lossy(line);
                stderr_file.write_all(decoded.as_bytes())?;
                stderr_file.flush()?;
                result.push_str(&decoded);
                Ok(())
            })?;
            Ok(result)
        });
        let started = Instant::now();
        let mut stop_since = None;
        let mut timed_out = false;
        let status = loop {
            if let Some(status) = process.lock().unwrap().try_wait()? {
                break status;
            }
            if self.is_cancelled(run_id)
                || stdout_failed.load(Ordering::Acquire)
                || spec
                    .timeout
                    .is_some_and(|timeout| started.elapsed() >= timeout)
            {
                if stop_since.is_none() {
                    timed_out = spec
                        .timeout
                        .is_some_and(|timeout| started.elapsed() >= timeout);
                    signal(&process, libc::SIGTERM)?;
                    stop_since = Some(Instant::now());
                } else if stop_since.is_some_and(|since| since.elapsed() >= Duration::from_secs(10))
                {
                    signal(&process, libc::SIGKILL)?;
                }
            }
            thread::sleep(Duration::from_millis(20));
        };
        ended.store(true, Ordering::Release);
        let input_result = input
            .join()
            .map_err(|_| BackendError::new(500, "runner", "Runner stdin worker failed"))?;
        let (final_event, final_event_scope, text, calls) = output
            .join()
            .map_err(|_| BackendError::new(500, "runner", "Runner stdout worker failed"))??;
        let stderr = errors
            .join()
            .map_err(|_| BackendError::new(500, "runner", "Runner stderr worker failed"))??;
        input_result?;
        if timed_out {
            return Err(BackendError::new(
                504,
                "runner-timeout",
                "Task Runner process exceeded its timeout",
            ));
        }
        Ok(ProcessOutput {
            return_code: status
                .code()
                .unwrap_or_else(|| -status.signal().unwrap_or(1)),
            final_event,
            final_event_scope,
            output: text,
            stderr,
            mcp_calls: calls,
        })
    }
}
