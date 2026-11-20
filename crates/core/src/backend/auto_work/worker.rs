//! A task-owned native child preserves the preview's process/resource boundary.
use super::{common::*, reconstruction};
use crate::backend::Result;
use serde_json::{json, Value};
use std::{
    io::{Read, Write},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc, Arc,
    },
    thread,
    time::{Duration, Instant},
};
pub const MAX_PREVIEW_BYTES: usize = 10 * 1024 * 1024;
const MEMORY_BYTES: u64 = 512 * 1024 * 1024;
const WALL_SECONDS: u64 = 120;
pub trait PreviewSupervisor {
    fn supervise(&self, operation: &str, args: &Value) -> Result<Value>;
}
pub struct NativePreviewSupervisor {
    executable: PathBuf,
}
impl NativePreviewSupervisor {
    pub fn new() -> Result<Self> {
        Ok(Self {
            executable: std::env::current_exe()?,
        })
    }
}
pub(super) fn decode_bounded(raw: &[u8]) -> Result<Value> {
    require(raw.len() <= MAX_PREVIEW_BYTES, "INPUT_LIMIT")?;
    crate::backend::json::decode_unique(raw).map_err(|_| failure("INVALID_JSON"))
}
pub(super) fn encode_bounded(value: &Value) -> Result<Vec<u8>> {
    struct Bounded(Vec<u8>);
    impl Write for Bounded {
        fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
            if self.0.len() + bytes.len() > MAX_PREVIEW_BYTES {
                return Err(std::io::Error::other("OUTPUT_LIMIT"));
            }
            self.0.extend_from_slice(bytes);
            Ok(bytes.len())
        }
        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }
    let mut output = Bounded(Vec::new());
    serde_json::to_writer(&mut output, value).map_err(|_| failure("OUTPUT_LIMIT"))?;
    Ok(output.0)
}
pub fn run_preview_operation(operation: &str, args: &Value) -> Result<Value> {
    let args = args.as_array().ok_or_else(|| failure("INVALID_INPUT"))?;
    let value = |index: usize| args.get(index).ok_or_else(|| failure("INVALID_INPUT"));
    let string = |index: usize| -> Result<&str> {
        value(index)?
            .as_str()
            .ok_or_else(|| failure("INVALID_INPUT"))
    };
    match operation {
        "prepare" => reconstruction::prepare_current(
            Path::new(string(0)?),
            string(1)?,
            string(2)?,
            string(3)?,
        ),
        "load" => Ok(reconstruction::load_snapshots(Path::new(string(0)?), value(1)?)?.into()),
        "text" => reconstruction::reconstruct(
            value(0)?,
            value(1)?
                .as_array()
                .ok_or_else(|| failure("INVALID_INPUT"))?,
            value(2)?
                .as_bool()
                .ok_or_else(|| failure("INVALID_INPUT"))?,
        ),
        _ => Err(failure("INVALID_INPUT")),
    }
}
fn memory_usage() -> Result<u64> {
    let mut usage = std::mem::MaybeUninit::<libc::rusage>::uninit();
    require(
        unsafe { libc::getrusage(libc::RUSAGE_SELF, usage.as_mut_ptr()) } == 0,
        "MONITOR_UNAVAILABLE",
    )?;
    let usage = unsafe { usage.assume_init() };
    let value = usage.ru_maxrss as u64;
    Ok(if cfg!(target_os = "macos") {
        value
    } else {
        value * 1024
    })
}
/// Internal binary entry point. It is dispatched before Config, DB initialization,
/// model creation, or application startup. Failure envelopes never carry input.
pub fn preview_worker() -> i32 {
    let result = (|| -> Result<(Value, u64)> {
        require(
            cfg!(any(target_os = "macos", target_os = "linux")),
            "MONITOR_UNAVAILABLE",
        )?;
        require(unsafe { libc::setsid() } >= 0, "MONITOR_UNAVAILABLE")?;
        let limit = libc::rlimit {
            rlim_cur: WALL_SECONDS as libc::rlim_t,
            rlim_max: WALL_SECONDS as libc::rlim_t,
        };
        require(
            unsafe { libc::setrlimit(libc::RLIMIT_CPU, &limit) } == 0,
            "MONITOR_UNAVAILABLE",
        )?;
        let mut raw = Vec::new();
        std::io::stdin()
            .take(MAX_PREVIEW_BYTES as u64 + 1)
            .read_to_end(&mut raw)?;
        let job = decode_bounded(&raw)?;
        let memory = job["memory_bytes"]
            .as_u64()
            .filter(|memory| *memory > 0 && *memory <= MEMORY_BYTES)
            .ok_or_else(|| failure("INVALID_INPUT"))?;
        let used = memory_usage()?;
        require(used > 0 && used <= memory, "MEMORY_LIMIT")?;
        let stopped = Arc::new(AtomicBool::new(false));
        let monitor_stopped = stopped.clone();
        let monitor = thread::spawn(move || {
            while !monitor_stopped.load(Ordering::Acquire) {
                match memory_usage() {
                    Ok(used) if used > 0 && used <= memory => {}
                    Ok(_) => unsafe { libc::_exit(71) },
                    Err(_) => unsafe { libc::_exit(72) },
                }
                thread::sleep(Duration::from_millis(10));
            }
        });
        let value = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            run_preview_operation(
                job["operation"]
                    .as_str()
                    .ok_or_else(|| failure("INVALID_INPUT"))?,
                &job["args"],
            )
        }));
        stopped.store(true, Ordering::Release);
        let _ = monitor.join();
        let value = value.map_err(|_| failure("WORKER_FAILED"))??;
        let peak = memory_usage()?;
        require(peak <= memory, "MEMORY_LIMIT")?;
        Ok((value, peak))
    })();
    let mut stdout = std::io::stdout().lock();
    match result {
        Ok((value, peak)) => match encode_bounded(&json!({"ok":true,"value":value})) {
            Ok(bytes) => {
                if stdout
                    .write_all(&bytes)
                    .and_then(|_| stdout.write_all(b"\n"))
                    .and_then(|_| writeln!(stdout, "{}", json!({"peak_bytes":peak})))
                    .and_then(|_| stdout.flush())
                    .is_ok()
                {
                    0
                } else {
                    2
                }
            }
            Err(_) => {
                let _ = stdout.write_all(b"{\"ok\":false}\n");
                2
            }
        },
        Err(_) => {
            let _ = stdout.write_all(b"{\"ok\":false}\n");
            2
        }
    }
}
struct ChildLease(Child);
impl Drop for ChildLease {
    fn drop(&mut self) {
        if self.0.try_wait().ok().flatten().is_none() {
            let pid = self.0.id() as libc::pid_t;
            unsafe {
                if libc::getpgid(pid) == pid {
                    libc::killpg(pid, libc::SIGKILL);
                } else {
                    let _ = self.0.kill();
                }
            }
        }
        let _ = self.0.wait();
    }
}
impl PreviewSupervisor for NativePreviewSupervisor {
    fn supervise(&self, operation: &str, args: &Value) -> Result<Value> {
        require(
            ["prepare", "load", "text"].contains(&operation),
            "INVALID_INPUT",
        )?;
        let request = encode_bounded(
            &json!({"operation":operation,"args":args,"memory_bytes":MEMORY_BYTES}),
        )?;
        let child = Command::new(&self.executable)
            .arg("--auto-work-worker")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| failure("WORKER_FAILED"))?;
        let mut child = ChildLease(child);
        let mut input = child.0.stdin.take().unwrap();
        let mut output = child.0.stdout.take().unwrap();
        let writer = thread::spawn(move || input.write_all(&request));
        let (sender, receiver) = mpsc::sync_channel(1);
        let reader = thread::spawn(move || {
            let mut bytes = Vec::new();
            let result = Read::by_ref(&mut output)
                .take(MAX_PREVIEW_BYTES as u64 + 2048)
                .read_to_end(&mut bytes)
                .map(|_| bytes);
            let _ = sender.send(result);
        });
        let started = Instant::now();
        let mut bytes = None;
        let mut status = None;
        loop {
            if started.elapsed() > Duration::from_secs(WALL_SECONDS) {
                return Err(failure("TIME_LIMIT"));
            }
            if bytes.is_none() {
                match receiver.try_recv() {
                    Ok(Ok(value)) => {
                        require(value.len() <= MAX_PREVIEW_BYTES + 1001, "WORKER_FAILED")?;
                        bytes = Some(value);
                    }
                    Ok(Err(_)) => return Err(failure("WORKER_FAILED")),
                    Err(mpsc::TryRecvError::Disconnected) => return Err(failure("WORKER_FAILED")),
                    Err(mpsc::TryRecvError::Empty) => {}
                }
            }
            if status.is_none() {
                status = child.0.try_wait().map_err(|_| failure("WORKER_FAILED"))?;
            }
            if status.is_some() && bytes.is_some() {
                break;
            }
            thread::sleep(Duration::from_millis(10));
        }
        writer
            .join()
            .map_err(|_| failure("WORKER_FAILED"))?
            .map_err(|_| failure("WORKER_FAILED"))?;
        reader.join().map_err(|_| failure("WORKER_FAILED"))?;
        require(status.unwrap().success(), "WORKER_FAILED")?;
        let bytes = bytes.unwrap();
        let mut lines = bytes.split(|byte| *byte == b'\n');
        let message = decode_bounded(lines.next().ok_or_else(|| failure("WORKER_FAILED"))?)?;
        let metrics = decode_bounded(lines.next().ok_or_else(|| failure("WORKER_FAILED"))?)?;
        require(
            message["ok"] == true
                && metrics["peak_bytes"]
                    .as_u64()
                    .is_some_and(|peak| peak <= MEMORY_BYTES)
                && started.elapsed() <= Duration::from_secs(WALL_SECONDS),
            "RESOURCE_LIMIT",
        )?;
        Ok(message["value"].clone())
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn strict_preview_codec_rejects_duplicates_nonfinite_and_byte_overflow() {
        for raw in [
            br#"{"x":1,"x":2}"#.as_slice(),
            br#"{"outer":{"a":1,"\u0061":2}}"#,
            br#"{"n":NaN}"#,
            br#"{"n":1e99999}"#,
        ] {
            assert!(decode_bounded(raw).is_err());
        }
        assert!(decode_bounded(&vec![b' '; MAX_PREVIEW_BYTES + 1]).is_err());
        let value = decode_bounded(br#"{"n":9007199254740993}"#).unwrap();
        assert_eq!(value["n"].to_string(), "9007199254740993");
        assert_eq!(
            encode_bounded(&json!("x".repeat(MAX_PREVIEW_BYTES)))
                .unwrap_err()
                .code,
            "OUTPUT_LIMIT"
        );
        assert_eq!(
            run_preview_operation("unknown", &json!([]))
                .unwrap_err()
                .code,
            "INVALID_INPUT"
        );
    }
}
