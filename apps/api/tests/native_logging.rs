//! Console logging checks run real native children with synthetic local roots.
use serde_json::Value;
use std::{
    io::{BufRead, BufReader, Read, Write},
    net::{SocketAddr, TcpListener, TcpStream},
    path::Path,
    process::{Child, Command, Stdio},
    sync::mpsc::{self, Receiver},
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

const MISSING_PATH: &str = "/synthetic-missing-endpoint";
const STATIC_PATH: &str = "/static/synthetic%20missing.css";
const QUERY_MARKER: &str = "SYNTHETIC_PRIVATE_QUERY";
const HEADER_MARKER: &str = "SYNTHETIC_PRIVATE_HEADER";
const COOKIE_MARKER: &str = "SYNTHETIC_PRIVATE_COOKIE";
const AUTH_MARKER: &str = "SYNTHETIC_PRIVATE_AUTH";
const BODY_MARKER: &str = "SYNTHETIC_PRIVATE_BODY";

fn command(root: &Path, binary: &str) -> Command {
    std::fs::create_dir(root.join("home")).unwrap();
    let mut command = Command::new(binary);
    command
        .env_clear()
        .env("PATH", "/usr/bin:/bin")
        .env("HOME", root.join("home"))
        .env("SHELL", "/bin/sh")
        .env("LOCALBRAIN_DATA_DIR", root.join("data"))
        .env("LOCALBRAIN_CACHE_DIR", root.join("cache"))
        .env("LOCALBRAIN_DEVELOPMENT_DIR", root.join("development"))
        .env("LOCALBRAIN_CONTEXT_ROOT", root.join("context"))
        .env("LOCALBRAIN_CLAUDE_ROOT", root.join("claude"))
        .env("LOCALBRAIN_CODEX_ROOT", root.join("codex"))
        .env("LOCALBRAIN_CLAUDE_BIN", root.join("missing-claude"))
        .env("LOCALBRAIN_CODEX_BIN", root.join("missing-codex"))
        .env("HF_HOME", root.join("models"))
        .env("HF_HUB_CACHE", root.join("models/hub"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    command
}

fn capture(reader: impl Read + Send + 'static) -> (Receiver<String>, JoinHandle<String>) {
    let (sender, receiver) = mpsc::channel();
    let worker = thread::spawn(move || {
        let mut output = String::new();
        for line in BufReader::new(reader).lines() {
            let line = line.unwrap();
            output.push_str(&line);
            output.push('\n');
            let _ = sender.send(line);
        }
        output
    });
    (receiver, worker)
}

struct Process {
    child: Child,
    stdout: Receiver<String>,
    stderr: Receiver<String>,
    stdout_reader: Option<JoinHandle<String>>,
    stderr_reader: Option<JoinHandle<String>>,
}
impl Process {
    fn spawn(mut command: Command) -> Self {
        let mut child = command.spawn().unwrap();
        let (stdout, stdout_reader) = capture(child.stdout.take().unwrap());
        let (stderr, stderr_reader) = capture(child.stderr.take().unwrap());
        Self {
            child,
            stdout,
            stderr,
            stdout_reader: Some(stdout_reader),
            stderr_reader: Some(stderr_reader),
        }
    }

    fn finish(mut self, parent_eof: bool) -> (String, String) {
        if parent_eof {
            drop(self.child.stdin.take());
        } else {
            assert_eq!(
                unsafe { libc::kill(self.child.id() as i32, libc::SIGTERM) },
                0
            );
        }
        let deadline = Instant::now() + Duration::from_secs(15);
        loop {
            if let Some(status) = self.child.try_wait().unwrap() {
                assert!(status.success(), "native server exited with {status}");
                break;
            }
            assert!(Instant::now() < deadline, "native server did not stop");
            thread::sleep(Duration::from_millis(25));
        }
        let stdout = self.stdout_reader.take().unwrap().join().unwrap();
        let stderr = self.stderr_reader.take().unwrap().join().unwrap();
        (stdout, stderr)
    }
}
impl Drop for Process {
    fn drop(&mut self) {
        if self.child.try_wait().ok().flatten().is_none() {
            let _ = self.child.kill();
            let _ = self.child.wait();
        }
        for reader in [&mut self.stdout_reader, &mut self.stderr_reader] {
            if let Some(reader) = reader.take() {
                let _ = reader.join();
            }
        }
    }
}

fn web(root: &Path, flags: &[&str], access_log: bool) -> (Process, u16) {
    let listener = TcpListener::bind(("127.0.0.1", 0)).unwrap();
    let port = listener.local_addr().unwrap().port();
    let mut command = command(root, env!("CARGO_BIN_EXE_lb"));
    command.args(["serve", "--port", &port.to_string()]);
    command.args(flags);
    drop(listener);
    let process = Process::spawn(command);
    let banner = process
        .stderr
        .recv_timeout(Duration::from_secs(25))
        .expect("web readiness banner");
    assert_eq!(
        banner,
        format!(
            "LocalBrain ready: http://127.0.0.1:{port} (access log: {})",
            if access_log { "on" } else { "off" }
        )
    );
    (process, port)
}

fn request(port: u16, method: &str, path: &str, body: &str) -> (u16, String, SocketAddr) {
    let mut stream = TcpStream::connect(("127.0.0.1", port)).unwrap();
    let peer = stream.local_addr().unwrap();
    stream
        .set_read_timeout(Some(Duration::from_secs(20)))
        .unwrap();
    stream
        .set_write_timeout(Some(Duration::from_secs(10)))
        .unwrap();
    write!(stream,"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nOrigin: http://127.0.0.1:{port}\r\nAuthorization: Bearer {AUTH_MARKER}\r\nCookie: synthetic={COOKIE_MARKER}\r\nX-Synthetic: {HEADER_MARKER}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",body.len()).unwrap();
    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .unwrap_or_else(|error| panic!("{method} {path}: {error}"));
    let (headers, body) = response.split_once("\r\n\r\n").unwrap();
    let status = headers.split_whitespace().nth(1).unwrap().parse().unwrap();
    (status, body.into(), peer)
}

#[test]
fn native_web_banner_and_explicit_request_silence() {
    let root = tempfile::tempdir().unwrap();
    // A quiet flag also overrides the legacy flag in an existing shell alias.
    let (process, port) = web(root.path(), &["--access-log", "--no-access-log"], false);
    assert_eq!(request(port, "GET", "/api/health", "").0, 200);
    assert_eq!(request(port, "GET", MISSING_PATH, "").0, 404);
    let (stdout, stderr) = process.finish(false);
    assert!(stdout.is_empty(), "{stdout}");
    assert_eq!(
        stderr,
        format!("LocalBrain ready: http://127.0.0.1:{port} (access log: off)\n")
    );
}

#[test]
fn native_web_default_access_log_shows_requested_paths_without_query_data() {
    let root = tempfile::tempdir().unwrap();
    let (process, port) = web(root.path(), &[], true);
    let connection = rusqlite::Connection::open(root.path().join("data/localbrain.db")).unwrap();
    connection.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES(1,'codex','Synthetic','/synthetic');INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count) VALUES(123456789,1,'synthetic-session','/synthetic/session.jsonl','Synthetic fixture',0);").unwrap();
    drop(connection);
    let query = format!("?token={QUERY_MARKER}");
    let (status, health, health_peer) = request(port, "GET", &format!("/api/health{query}"), "");
    assert_eq!(status, 200);
    assert_eq!(
        serde_json::from_str::<Value>(&health).unwrap()["edition"],
        "web"
    );
    let session_path = "/sessions/123456789";
    let (status, session, session_peer) = request(port, "GET", session_path, "");
    assert_eq!(status, 200, "{session}");
    let (status, _, missing_peer) = request(port, "GET", &format!("{MISSING_PATH}{query}"), "");
    assert_eq!(status, 404);
    let (status, _, static_peer) = request(port, "GET", &format!("{STATIC_PATH}{query}"), "");
    assert_eq!(status, 404);
    let (status, _, method_peer) = request(port, "POST", &format!("/api/health{query}"), "");
    assert_eq!(status, 405);
    let (status, _, body_peer) = request(port, "PATCH", "/api/settings/preferences", BODY_MARKER);
    assert_eq!(status, 422);
    let (stdout, stderr) = process.finish(false);
    assert!(stdout.is_empty(), "{stdout}");
    let records: Vec<_> = stderr.lines().skip(1).collect();
    let expected = [
        (health_peer, "GET", "/api/health", "200 OK"),
        (session_peer, "GET", session_path, "200 OK"),
        (missing_peer, "GET", MISSING_PATH, "404 Not Found"),
        (static_peer, "GET", STATIC_PATH, "404 Not Found"),
        (method_peer, "POST", "/api/health", "405 Method Not Allowed"),
        (
            body_peer,
            "PATCH",
            "/api/settings/preferences",
            "422 Unprocessable Entity",
        ),
    ];
    assert_eq!(records.len(), expected.len(), "{stderr}");
    for (record, (peer, method, path, status)) in records.iter().zip(expected) {
        let prefix = format!("INFO:     {peer} - \"{method} {path} HTTP/1.1\" {status} ");
        let elapsed: f64 = record
            .strip_prefix(&prefix)
            .unwrap_or_else(|| panic!("unexpected access log: {record}"))
            .strip_suffix("ms")
            .unwrap()
            .parse()
            .unwrap();
        assert!(elapsed.is_finite() && elapsed >= 0.0, "{record}");
    }
    for marker in [
        QUERY_MARKER,
        HEADER_MARKER,
        COOKIE_MARKER,
        AUTH_MARKER,
        BODY_MARKER,
    ] {
        assert!(!stderr.contains(marker), "logged private marker: {marker}");
    }
}

#[test]
fn native_desktop_keeps_stdout_ready_protocol_and_stdin_lifeline_without_logs() {
    let root = tempfile::tempdir().unwrap();
    let mut command = command(root.path(), env!("CARGO_BIN_EXE_localbrain-backend"));
    command.env("LOCALBRAIN_DESKTOP_TOKEN", AUTH_MARKER);
    let process = Process::spawn(command);
    let line = process
        .stdout
        .recv_timeout(Duration::from_secs(25))
        .expect("desktop readiness JSON");
    let ready: Value = serde_json::from_str(&line).unwrap();
    assert_eq!(ready.as_object().unwrap().len(), 2);
    assert_eq!(ready["ready"], true);
    let port = u16::try_from(ready["port"].as_u64().unwrap()).unwrap();
    let (status, health, _) = request(port, "GET", "/api/health", "");
    assert_eq!(status, 200);
    assert_eq!(
        serde_json::from_str::<Value>(&health).unwrap()["edition"],
        "desktop"
    );
    let (stdout, stderr) = process.finish(true);
    assert_eq!(stdout, format!("{line}\n"));
    assert!(stderr.is_empty(), "{stderr}");
    assert!(TcpStream::connect(("127.0.0.1", port)).is_err());
}
