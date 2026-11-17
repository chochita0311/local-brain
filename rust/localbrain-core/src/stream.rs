use crate::{fields, service::Service, string, Error, Request, Result, MAX_REQUEST};
use serde_json::{json, Value};
use std::fs::File;
use std::io::Read;
use std::net::Shutdown;
use std::os::fd::{AsRawFd, FromRawFd};
use std::os::unix::net::UnixStream;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    mpsc, Arc, Condvar, Mutex,
};
use std::time::{Duration, Instant};

pub struct Lines {
    file: File,
    buffer: Vec<u8>,
}
impl Lines {
    pub fn stdin() -> Result<Self> {
        let fd = unsafe { libc::dup(0) };
        if fd < 0 {
            return Err(Error::unavailable());
        }
        unsafe {
            libc::fcntl(fd, libc::F_SETFD, libc::FD_CLOEXEC);
        }
        Ok(Self {
            file: unsafe { File::from_raw_fd(fd) },
            buffer: Vec::new(),
        })
    }
    pub fn next(&mut self, stop: &AtomicBool) -> Result<Option<Vec<u8>>> {
        loop {
            if stop.load(Ordering::Acquire) {
                return Ok(None);
            }
            if let Some(index) = self.buffer.iter().position(|b| *b == b'\n') {
                if index > MAX_REQUEST {
                    return Err(Error::invalid());
                }
                let line: Vec<_> = self.buffer.drain(..=index).collect();
                return Ok(Some(line[..index].to_vec()));
            }
            if self.buffer.len() > MAX_REQUEST {
                return Err(Error::invalid());
            }
            let mut poll = libc::pollfd {
                fd: self.file.as_raw_fd(),
                events: libc::POLLIN,
                revents: 0,
            };
            let result = unsafe { libc::poll(&mut poll, 1, 100) };
            if result < 0 {
                if std::io::Error::last_os_error().kind() == std::io::ErrorKind::Interrupted {
                    continue;
                }
                return Err(Error::unavailable());
            }
            if result == 0 {
                continue;
            }
            let mut bytes = [0u8; 8192];
            let count = self
                .file
                .read(&mut bytes)
                .map_err(|_| Error::unavailable())?;
            if count == 0 {
                return if self.buffer.is_empty() {
                    Ok(None)
                } else {
                    Err(Error::invalid())
                };
            }
            self.buffer.extend_from_slice(&bytes[..count]);
        }
    }
}
fn write_frame(value: &Value) -> Result<()> {
    let mut bytes = serde_json::to_vec(value).map_err(|_| Error::invalid())?;
    if bytes.len() > crate::service::MAX_FRAME {
        return Err(Error::invalid());
    }
    bytes.push(b'\n');
    let deadline = Instant::now() + Duration::from_secs(15);
    let mut offset = 0;
    while offset < bytes.len() {
        let count =
            unsafe { libc::write(1, bytes[offset..].as_ptr().cast(), bytes.len() - offset) };
        if count > 0 {
            offset += count as usize;
            continue;
        }
        let error = std::io::Error::last_os_error();
        if error.kind() == std::io::ErrorKind::Interrupted {
            continue;
        }
        if error.kind() != std::io::ErrorKind::WouldBlock || Instant::now() >= deadline {
            return Err(Error::unavailable());
        }
        let mut poll = libc::pollfd {
            fd: 1,
            events: libc::POLLOUT,
            revents: 0,
        };
        unsafe {
            libc::poll(&mut poll, 1, 100);
        }
    }
    Ok(())
}
fn send(sender: &mpsc::SyncSender<(Value, bool)>, value: Value, final_error: bool) -> Result<()> {
    sender
        .try_send((value, final_error))
        .map_err(|_| Error::unavailable())
}
#[derive(Default)]
struct FailureSignal {
    frame: Mutex<Option<Value>>,
    input_failed: AtomicBool,
}
impl FailureSignal {
    fn report(&self, error: &Error) {
        let input = matches!(error.code.as_str(), "input_busy" | "input_failed");
        if input {
            self.input_failed.store(true, Ordering::Release);
        }
        if let Ok(mut frame) = self.frame.lock() {
            if frame.is_none() || input {
                *frame = Some(json!({"type":"error","code":error.code,"message":error.message}));
            }
        }
    }
    fn take(&self) -> Option<Value> {
        self.frame.lock().ok()?.take()
    }
    fn pending(&self) -> bool {
        self.frame.lock().is_ok_and(|frame| frame.is_some())
    }
}
fn publish_control(
    token: &Mutex<Option<String>>,
    sender: &mpsc::SyncSender<(Value, bool)>,
    lease: Option<String>,
    writable: Value,
) -> Result<()> {
    let mut current = token.lock().map_err(|_| Error::unavailable())?;
    *current = lease;
    // Token mutation and publication share this lock with output publication.
    send(sender, json!({"type":"control","writable":writable}), false)
}
fn publish_output(
    token: &Mutex<Option<String>>,
    sender: &mpsc::SyncSender<(Value, bool)>,
    captured: &Option<String>,
    mut frame: Value,
) -> Result<()> {
    let current = token.lock().map_err(|_| Error::unavailable())?;
    if captured != &*current {
        frame
            .as_object_mut()
            .ok_or_else(Error::invalid)?
            .remove("writable");
    }
    send(sender, frame, false)
}
#[derive(Default)]
struct Ack {
    seq: Option<u64>,
    acked: bool,
}

pub fn run(request: Request, mut lines: Lines) -> Result<i32> {
    if request.operation != "terminal.stream" {
        return Err(Error::invalid());
    }
    fields(
        &request.arguments,
        &["id", "unicodeVersion", "checkpointVersion"],
    )?;
    let id = string(&request.arguments, "id")?.to_owned();
    let version_error = || {
        Error::terminal(
            "client_update_required",
            "터미널 화면을 새로고침한 뒤 다시 연결해 주세요.",
        )
    };
    let unicode = request
        .arguments
        .get("unicodeVersion")
        .and_then(Value::as_str)
        .filter(|v| *v == "11")
        .ok_or_else(version_error)?
        .to_owned();
    let checkpoint = request
        .arguments
        .get("checkpointVersion")
        .and_then(Value::as_str)
        .filter(|v| *v == "xterm6-v3")
        .ok_or_else(version_error)?
        .to_owned();
    let service = Service::new(request.context)?;
    let _lease = service.use_payload()?;
    let status = service.status()?;
    if status["state"] != "running" {
        return Err(Error::unavailable());
    }
    let generation = status["generation"]
        .as_str()
        .ok_or_else(Error::identity)?
        .to_owned();
    let initial = service.rpc(
        "claim",
        &json!({"id":id,"takeover":false,"unicodeVersion":unicode,"checkpointVersion":checkpoint}),
        Some(&generation),
        Duration::from_secs(8),
    );
    let initial = match initial {
        Ok(v) => v,
        Err(e) if e.code == "exited" => json!({"lease":null,"writable":false}),
        Err(e) => return Err(e),
    };
    let token = Arc::new(Mutex::new(initial["lease"].as_str().map(str::to_owned)));
    let stop = Arc::new(AtomicBool::new(false));
    let active = Arc::new(Mutex::new(None::<UnixStream>));
    let ack = Arc::new((Mutex::new(Ack::default()), Condvar::new()));
    let (sender, receiver) = mpsc::sync_channel::<(Value, bool)>(2);
    let flags = unsafe { libc::fcntl(1, libc::F_GETFL) };
    if flags < 0 || unsafe { libc::fcntl(1, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0 {
        return Err(Error::unavailable());
    }
    send(
        &sender,
        json!({"type":"control","writable":initial["writable"]}),
        false,
    )?;
    let failures = Arc::new(FailureSignal::default());
    let writer_stop = stop.clone();
    let writer_failures = failures.clone();
    let writer = std::thread::spawn(move || loop {
        if let Some(error) = writer_failures.take() {
            let _ = write_frame(&error);
            break;
        }
        match receiver.recv_timeout(Duration::from_millis(100)) {
            Ok((value, saved_error)) => {
                if writer_stop.load(Ordering::Acquire) && !saved_error {
                    continue;
                }
                // Complete an already-started NDJSON frame before a final warning.
                // A stalled pipe remains bounded by write_frame's 15-second deadline.
                if write_frame(&value).is_err() {
                    writer_stop.store(true, Ordering::Release);
                    break;
                }
            }
            Err(mpsc::RecvTimeoutError::Timeout) if !writer_stop.load(Ordering::Acquire) => {
                continue
            }
            _ => {
                if writer_failures.pending() {
                    continue;
                }
                break;
            }
        }
    });
    let output_service = service.clone();
    let output_stop = stop.clone();
    let output_token = token.clone();
    let output_ack = ack.clone();
    let output_active = active.clone();
    let output_sender = sender.clone();
    let output_failures = failures.clone();
    let output_id = id.clone();
    let output_generation = generation.clone();
    let output_checkpoint = checkpoint.clone();
    let output = std::thread::spawn(move || {
        let result = (|| -> Result<()> {
            let mut after: Value = json!(-1);
            while !output_stop.load(Ordering::Acquire) {
                let lease = output_token
                    .lock()
                    .map_err(|_| Error::unavailable())?
                    .clone();
                let mut connection = output_service.connect(Duration::from_secs(1))?;
                connection
                    .set_read_timeout(Some(Duration::from_secs(12)))
                    .map_err(|_| Error::unavailable())?;
                {
                    let mut active = output_active.lock().map_err(|_| Error::unavailable())?;
                    if output_stop.load(Ordering::Acquire) {
                        break;
                    }
                    *active = Some(connection.try_clone().map_err(|_| Error::unavailable())?);
                }
                let frame=output_service.exchange(&mut connection,"read",&json!({"id":output_id,"after":after,"lease":lease,"checkpointVersion":output_checkpoint}),Some(&output_generation));
                *output_active.lock().map_err(|_| Error::unavailable())? = None;
                if output_stop.load(Ordering::Acquire) {
                    break;
                }
                let mut frame = frame?;
                let seq = frame["seq"].as_u64().ok_or_else(Error::invalid)?;
                {
                    let mut state = output_ack.0.lock().map_err(|_| Error::unavailable())?;
                    state.seq = Some(seq);
                    state.acked = false;
                }
                frame["type"] = json!("output");
                let running = frame["terminal"]["state"] == "running";
                publish_output(&output_token, &output_sender, &lease, frame)?;
                let deadline = Instant::now() + Duration::from_secs(15);
                let mut state = output_ack.0.lock().map_err(|_| Error::unavailable())?;
                while !state.acked && !output_stop.load(Ordering::Acquire) {
                    if Instant::now() >= deadline {
                        return Err(Error::unavailable());
                    }
                    state = output_ack
                        .1
                        .wait_timeout(state, Duration::from_millis(100))
                        .map_err(|_| Error::unavailable())?
                        .0;
                }
                if !running {
                    break;
                }
                after = json!(seq);
            }
            Ok(())
        })();
        if let Err(error) = result {
            if !output_stop.load(Ordering::Acquire) {
                output_failures.report(&error);
            }
        }
        output_stop.store(true, Ordering::Release);
        output_ack.1.notify_all();
    });
    let result = (|| -> Result<()> {
        while let Some(raw) = lines.next(&stop)? {
            let message: Value = serde_json::from_slice(&raw).map_err(|_| Error::invalid())?;
            if !message.is_object() {
                return Err(Error::invalid());
            }
            let kind = string(&message, "type")?;
            if kind == "ack" {
                let mut state = ack.0.lock().map_err(|_| Error::unavailable())?;
                if message
                    .get("seq")
                    .and_then(Value::as_u64)
                    .is_some_and(|seq| state.seq == Some(seq))
                {
                    state.acked = true;
                    ack.1.notify_all();
                }
                continue;
            }
            if kind == "claim" {
                let claimed=service.rpc("claim",&json!({"id":id,"takeover":true,"unicodeVersion":unicode,"checkpointVersion":checkpoint}),Some(&generation),Duration::from_secs(8))?;
                publish_control(
                    &token,
                    &sender,
                    claimed["lease"].as_str().map(str::to_owned),
                    claimed["writable"].clone(),
                )?;
                continue;
            }
            if !["input", "binary", "resize"].contains(&kind) {
                return Err(Error::invalid());
            }
            let lease = token.lock().map_err(|_| Error::unavailable())?.clone();
            let mut params = json!({"id":id,"lease":lease});
            if kind == "resize" {
                params["cols"] = message["cols"].clone();
                params["rows"] = message["rows"].clone();
            } else {
                params["data"] = message["data"].clone();
            }
            if let Err(error) =
                service.rpc(kind, &params, Some(&generation), Duration::from_secs(8))
            {
                if error.code == "not_owner" {
                    publish_control(&token, &sender, None, json!(false))?;
                } else {
                    if matches!(error.code.as_str(), "input_busy" | "input_failed") {
                        failures.report(&error);
                        return Ok(());
                    }
                    send(
                        &sender,
                        json!({"type":"error","code":error.code,"message":error.message}),
                        true,
                    )?;
                }
            }
        }
        Ok(())
    })();
    if let Err(error) = &result {
        failures.report(error);
    }
    stop.store(true, Ordering::Release);
    ack.1.notify_all();
    if let Some(socket) = active.lock().map_err(|_| Error::unavailable())?.take() {
        let _ = socket.shutdown(Shutdown::Both);
    }
    let _ = output.join();
    drop(sender);
    if let Some(lease) = token.lock().map_err(|_| Error::unavailable())?.take() {
        let _ = service.rpc(
            "release",
            &json!({"id":id,"lease":lease}),
            Some(&generation),
            Duration::from_secs(8),
        );
    }
    let _ = writer.join();
    // Exit 75 preserves partial-input close semantics even if a blocked pipe
    // prevented delivery of the mandatory warning. The host supplies its fallback.
    Ok(if failures.input_failed.load(Ordering::Acquire) {
        75
    } else {
        0
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn mandatory_input_warning_has_capacity_when_regular_queue_is_full() {
        let (sender, _receiver) = mpsc::sync_channel(2);
        send(&sender, json!({"type":"control"}), false).unwrap();
        send(&sender, json!({"type":"control"}), false).unwrap();
        assert!(send(&sender, json!({"type":"control"}), false).is_err());
        let failure = FailureSignal::default();
        failure.report(&Error::terminal("input_busy", "partial input"));
        assert!(failure.input_failed.load(Ordering::Acquire));
        assert_eq!(failure.take().unwrap()["code"], "input_busy");
    }
    #[test]
    fn stale_reads_neither_revoke_new_control_nor_restore_lost_control() {
        for writable in [true, false] {
            let token = Mutex::new(Some("old".into()));
            let (sender, receiver) = mpsc::sync_channel(4);
            publish_control(
                &token,
                &sender,
                if writable { Some("new".into()) } else { None },
                json!(writable),
            )
            .unwrap();
            publish_output(
                &token,
                &sender,
                &Some("old".into()),
                json!({"type":"output","writable":!writable}),
            )
            .unwrap();
            assert_eq!(receiver.recv().unwrap().0["writable"], json!(writable));
            assert!(receiver.recv().unwrap().0.get("writable").is_none());
        }
        let token = Mutex::new(Some("old".into()));
        let (sender, receiver) = mpsc::sync_channel(4);
        publish_output(
            &token,
            &sender,
            &Some("old".into()),
            json!({"type":"output","writable":true}),
        )
        .unwrap();
        publish_control(&token, &sender, Some("new".into()), json!(true)).unwrap();
        assert_eq!(receiver.recv().unwrap().0["type"], "output");
        assert_eq!(receiver.recv().unwrap().0["type"], "control");
    }
}
