//! One explicitly authorized child, nonblocking bounded pipes, and observed usage.
use super::{private_binary, update, InsightRuntime, Job};
use crate::backend::{
    clock, db,
    insights::{invalid, required, usage},
    json as codec, BackendError, Result,
};
use chrono::Utc;
use serde_json::{json, Value};
use std::{
    ffi::OsString,
    fs::File,
    io::{Read, Write},
    os::{fd::AsRawFd, unix::process::ExitStatusExt},
    path::Path,
    process::{Child, Command, Stdio},
    sync::atomic::Ordering,
    thread,
    time::{Duration, Instant},
};
const MAX_STREAM_BYTES: usize = 8_000_000;
const MAX_STDERR_BYTES: usize = 1_000_000;
const MAX_LINE_BYTES: usize = 1_000_000;
pub(super) struct Output {
    pub return_code: i32,
    pub final_event: Option<Value>,
    pub usage: Option<Value>,
    pub resolved_model: Option<String>,
}
struct ChildGuard(Child);
impl Drop for ChildGuard {
    fn drop(&mut self) {
        if self.0.try_wait().ok().flatten().is_some() {
            return;
        }
        let _ = signal(&self.0, libc::SIGTERM);
        let started = Instant::now();
        loop {
            match self.0.try_wait() {
                Ok(Some(_)) => break,
                Ok(None) if started.elapsed() < Duration::from_secs(5) => {
                    thread::sleep(Duration::from_millis(10))
                }
                _ => {
                    let _ = self.0.kill();
                    let _ = self.0.wait();
                    break;
                }
            }
        }
    }
}
fn signal(child: &Child, signal: i32) -> Result<()> {
    if unsafe { libc::kill(child.id() as i32, signal) } != 0 {
        let error = std::io::Error::last_os_error();
        if error.raw_os_error() != Some(libc::ESRCH) {
            return Err(error.into());
        }
    }
    Ok(())
}
fn nonblocking(stream: &impl AsRawFd) -> Result<()> {
    let fd = stream.as_raw_fd();
    let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
    if flags < 0 || unsafe { libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    Ok(())
}
fn available(stream: &impl AsRawFd) -> Result<usize> {
    let mut bytes: libc::c_int = 0;
    if unsafe { libc::ioctl(stream.as_raw_fd(), libc::FIONREAD, &mut bytes) } < 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    usize::try_from(bytes).map_err(|_| invalid("Invalid analysis pipe length"))
}
struct StreamState {
    file: File,
    written: usize,
    pending: Vec<u8>,
    line: usize,
    output: Output,
}
impl StreamState {
    fn bytes(&mut self, bytes: &[u8], runtime: &InsightRuntime, run: &Value) -> Result<()> {
        let retain = bytes.len().min(MAX_STREAM_BYTES - self.written);
        self.file.write_all(&bytes[..retain])?;
        self.written += retain;
        for byte in bytes {
            self.pending.push(*byte);
            if self.pending.len() > MAX_LINE_BYTES + usize::from(*byte == b'\n') {
                return Err(BackendError::new(
                    422,
                    "insight-stream-limit",
                    "Analysis stream line exceeds the supported limit",
                ));
            }
            if *byte == b'\n' {
                self.event(runtime, run)?;
            }
        }
        Ok(())
    }
    fn event(&mut self, runtime: &InsightRuntime, run: &Value) -> Result<()> {
        self.line += 1;
        let bytes = std::mem::take(&mut self.pending);
        let event = std::str::from_utf8(&bytes)
            .ok()
            .and_then(|s| codec::decode(s.strip_prefix('\u{feff}').unwrap_or(s)).ok());
        let Some(event) = event.filter(Value::is_object) else {
            return Ok(());
        };
        if let Some(model) = event["model"]
            .as_str()
            .or_else(|| event["message"]["model"].as_str())
        {
            self.output.resolved_model = Some(model.into());
        }
        if event["type"] == "result" {
            if event["usage"].is_object() {
                let mut usage = event["usage"].clone();
                if event["total_cost_usd"].is_number() || event["total_cost_usd"].is_boolean() {
                    usage["total_cost_usd"] = event["total_cost_usd"].clone();
                }
                self.output.usage = Some(usage);
            }
            self.output.final_event = Some(event);
        } else if event["type"] == "turn.completed" && event["usage"].is_object() {
            self.output.usage = Some(event["usage"].clone());
            self.file.flush()?;
            let connection = db::connect(runtime.config())?;
            connection.execute_batch("BEGIN IMMEDIATE")?;
            let mut observed_run = run.clone();
            observed_run["resolved_model"] = json!(self.output.resolved_model);
            let stored = usage::store_insight_usage(
                &connection,
                runtime.config(),
                &observed_run,
                &event["usage"],
                &clock::isoformat(Utc::now()),
                self.line as i64,
            );
            if stored.is_err() {
                connection.execute_batch("ROLLBACK")?;
            } else {
                connection.execute_batch("COMMIT")?;
            }
            stored?;
        }
        Ok(())
    }
}
fn stderr_bytes(
    file: &mut File,
    written: &mut usize,
    line_bytes: &mut usize,
    bytes: &[u8],
) -> Result<()> {
    for byte in bytes {
        if *byte == b'\n' {
            *line_bytes = 0;
        } else {
            *line_bytes += 1;
            if *line_bytes > MAX_LINE_BYTES {
                return Err(BackendError::new(
                    422,
                    "insight-stream-limit",
                    "Analysis stderr line exceeds the supported limit",
                ));
            }
        }
    }
    let retain = bytes.len().min(MAX_STDERR_BYTES - *written);
    file.write_all(&bytes[..retain])?;
    *written += retain;
    Ok(())
}
pub(super) fn execute(
    runtime: &InsightRuntime,
    job: &Job,
    run: &mut Value,
    args: Vec<OsString>,
    prompt: String,
    home: &Path,
) -> Result<Output> {
    if job.cancelled.load(Ordering::Acquire) || runtime.stopping.load(Ordering::Acquire) {
        return Err(BackendError::conflict("Run cancelled before launch"));
    }
    let mut stream = StreamState {
        file: private_binary(Path::new(required(run, "stream_path")?))?,
        written: 0,
        pending: vec![],
        line: 0,
        output: Output {
            return_code: 0,
            final_event: None,
            usage: None,
            resolved_model: None,
        },
    };
    let mut stderr_file = private_binary(Path::new(required(run, "stderr_path")?))?;
    let executable = args
        .first()
        .ok_or_else(|| invalid("Runner command is empty"))?;
    let mut child = ChildGuard(
        Command::new(executable)
            .args(&args[1..])
            .current_dir(super::run_root(runtime.config(), required(run, "id")?)?)
            .env("CODEX_HOME", home)
            .env("LOCALBRAIN_INSIGHT_RUN_ID", required(run, "id")?)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?,
    );
    let mut stdin = Some(child.0.stdin.take().expect("piped stdin"));
    let mut stdout = child.0.stdout.take().expect("piped stdout");
    let mut stderr = child.0.stderr.take().expect("piped stderr");
    nonblocking(stdin.as_ref().unwrap())?;
    nonblocking(&stdout)?;
    nonblocking(&stderr)?;
    let at = Utc::now();
    run["started_at"] = json!(clock::isoformat(at));
    let connection = db::connect(runtime.config())?;
    let changed = update(
        &connection,
        required(run, "id")?,
        &json!({"status":"running","started_at":run["started_at"],"pid":child.0.id()}),
        at,
        true,
    )?;
    drop(connection);
    if changed == 0 {
        return Err(BackendError::conflict("Run became terminal before launch"));
    }
    let prompt = prompt.as_bytes();
    let mut input = 0;
    let mut err_written = 0;
    let mut err_line_bytes = 0;
    let mut buffer = [0u8; 64 * 1024];
    let mut stdout_eof = false;
    let mut stderr_eof = false;
    let mut stopping_since = None;
    loop {
        if let Some(stdin_pipe) = stdin.as_mut() {
            if input < prompt.len() {
                match stdin_pipe.write(&prompt[input..]) {
                    Ok(0) => {
                        return Err(invalid(
                            "Analysis runner stdin closed before the prompt was supplied",
                        ))
                    }
                    Ok(written) => input += written,
                    Err(error)
                        if matches!(
                            error.kind(),
                            std::io::ErrorKind::WouldBlock | std::io::ErrorKind::Interrupted
                        ) => {}
                    Err(error) => return Err(error.into()),
                }
            }
            if input == prompt.len() {
                stdin = None;
            }
        }
        // Fair polling keeps cancellation and the other pipe responsive even
        // when one writer continuously fills its pipe.
        for _ in 0..16 {
            match stdout.read(&mut buffer) {
                Ok(0) => {
                    stdout_eof = true;
                    break;
                }
                Ok(length) => stream.bytes(&buffer[..length], runtime, run)?,
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => break,
                Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
                Err(error) => return Err(error.into()),
            }
        }
        for _ in 0..16 {
            match stderr.read(&mut buffer) {
                Ok(0) => {
                    stderr_eof = true;
                    break;
                }
                Ok(length) => {
                    stderr_bytes(
                        &mut stderr_file,
                        &mut err_written,
                        &mut err_line_bytes,
                        &buffer[..length],
                    )?;
                }
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => break,
                Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
                Err(error) => return Err(error.into()),
            }
        }
        if job.cancelled.load(Ordering::Acquire) || runtime.stopping.load(Ordering::Acquire) {
            if let Some(since) = stopping_since {
                if Instant::now().duration_since(since) >= Duration::from_secs(5) {
                    signal(&child.0, libc::SIGKILL)?;
                }
            } else {
                signal(&child.0, libc::SIGTERM)?;
                stopping_since = Some(Instant::now());
            }
        }
        if let Some(status) = child.0.try_wait()? {
            // Drain currently available bytes once more; an unrelated descendant
            // retaining a pipe cannot keep the owned child alive indefinitely.
            if !stdout_eof {
                let mut remaining = available(&stdout)?;
                while remaining > 0 {
                    let length = remaining.min(buffer.len());
                    match stdout.read(&mut buffer[..length]) {
                        Ok(0) => break,
                        Ok(length) => {
                            remaining -= length;
                            stream.bytes(&buffer[..length], runtime, run)?;
                        }
                        Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => break,
                        Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
                        Err(error) => return Err(error.into()),
                    }
                }
            }
            if !stderr_eof {
                let mut remaining = available(&stderr)?;
                while remaining > 0 {
                    let length = remaining.min(buffer.len());
                    match stderr.read(&mut buffer[..length]) {
                        Ok(0) => break,
                        Ok(length) => {
                            remaining -= length;
                            stderr_bytes(
                                &mut stderr_file,
                                &mut err_written,
                                &mut err_line_bytes,
                                &buffer[..length],
                            )?;
                        }
                        Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => break,
                        Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
                        Err(error) => return Err(error.into()),
                    }
                }
            }
            if !stream.pending.is_empty() {
                stream.event(runtime, run)?;
            }
            stream.file.flush()?;
            stderr_file.flush()?;
            if stopping_since.is_some() {
                return Err(BackendError::conflict("Analysis Run cancelled"));
            }
            stream.output.return_code = status
                .code()
                .unwrap_or_else(|| -status.signal().unwrap_or(1));
            return Ok(stream.output);
        }
        thread::sleep(Duration::from_millis(10));
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn line_limit_excludes_newline_like_python_streamreader() {
        let directory = tempfile::tempdir().unwrap();
        let runtime = InsightRuntime::new(crate::backend::Config::for_data_dir(
            directory.path().join("data"),
        ));
        let make = || StreamState {
            file: tempfile::tempfile().unwrap(),
            written: 0,
            pending: vec![],
            line: 0,
            output: Output {
                return_code: 0,
                final_event: None,
                usage: None,
                resolved_model: None,
            },
        };
        let mut state = make();
        let mut line = vec![b' '; MAX_LINE_BYTES - 4];
        line.extend_from_slice(b"null\n");
        state.bytes(&line, &runtime, &Value::Null).unwrap();
        assert_eq!(state.line, 1);
        let mut state = make();
        assert!(state
            .bytes(&vec![b' '; MAX_LINE_BYTES + 1], &runtime, &Value::Null)
            .is_err());
        let mut file = tempfile::tempfile().unwrap();
        let mut written = 0;
        let mut count = 0;
        stderr_bytes(
            &mut file,
            &mut written,
            &mut count,
            &vec![b'x'; MAX_LINE_BYTES],
        )
        .unwrap();
        stderr_bytes(&mut file, &mut written, &mut count, b"\n").unwrap();
        assert_eq!(count, 0);
        assert!(stderr_bytes(
            &mut file,
            &mut written,
            &mut count,
            &vec![b'x'; MAX_LINE_BYTES + 1]
        )
        .is_err());
    }
}
