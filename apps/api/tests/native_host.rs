//! Real native child/lifeline checks use only synthetic private roots.
use serde_json::Value;
use std::{
    io::{BufRead, BufReader, Read, Write},
    net::TcpStream,
    path::Path,
    process::{Child, Command, Stdio},
    sync::mpsc,
    time::{Duration, Instant},
};
struct Process(Child);
impl Drop for Process {
    fn drop(&mut self) {
        if self.0.try_wait().ok().flatten().is_none() {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }
}
fn command(root: &Path) -> Command {
    std::fs::create_dir_all(root.join("home")).unwrap();
    let mut command = Command::new(env!("CARGO_BIN_EXE_localbrain-backend"));
    command
        .env_clear()
        .env("PATH", "/usr/bin:/bin")
        .env("HOME", root.join("home"))
        .env("SHELL", "/bin/zsh")
        .env("LOCALBRAIN_DATA_DIR", root.join("data"))
        .env("LOCALBRAIN_CACHE_DIR", root.join("cache"))
        .env("LOCALBRAIN_DEVELOPMENT_DIR", root.join("development"))
        .env("LOCALBRAIN_CONTEXT_ROOT", root.join("context"))
        .env("LOCALBRAIN_CLAUDE_ROOT", root.join("claude"))
        .env("LOCALBRAIN_CODEX_ROOT", root.join("codex"))
        .env("HF_HOME", root.join("models"))
        .env("HF_HUB_CACHE", root.join("models/hub"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    command
}
fn request(port: u16, method: &str, path: &str, body: &str, token: bool) -> (u16, String) {
    let mut stream = TcpStream::connect(("127.0.0.1", port)).unwrap();
    stream
        .set_read_timeout(Some(Duration::from_secs(20)))
        .unwrap();
    stream
        .set_write_timeout(Some(Duration::from_secs(10)))
        .unwrap();
    write!(stream,"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nOrigin: http://127.0.0.1:{port}\r\n{}Content-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",if token{"Authorization: Bearer synthetic-native-token\r\n"}else{""},body.len()).unwrap();
    let mut bytes = vec![];
    stream.read_to_end(&mut bytes).unwrap();
    let response = String::from_utf8(bytes).unwrap();
    let (header, body) = response.split_once("\r\n\r\n").unwrap();
    let code = header.split_whitespace().nth(1).unwrap().parse().unwrap();
    (code, body.into())
}
#[test]
#[ignore = "requires loopback access; run explicitly with synthetic native child"]
fn native_desktop_ready_auth_deep_json_and_parent_lifetime() {
    let root = tempfile::Builder::new()
        .prefix("lb-native-")
        .tempdir_in("/private/tmp")
        .unwrap();
    let mut process = Process(
        command(root.path())
            .env("LOCALBRAIN_DESKTOP_TOKEN", "synthetic-native-token")
            .spawn()
            .unwrap(),
    );
    let output = process.0.stdout.take().unwrap();
    let (tx, rx) = mpsc::channel();
    let reader = std::thread::spawn(move || {
        let mut line = String::new();
        let result = BufReader::new(output).read_line(&mut line).map(|_| line);
        let _ = tx.send(result);
    });
    let line = rx
        .recv_timeout(Duration::from_secs(25))
        .expect("native readiness timeout")
        .unwrap();
    reader.join().unwrap();
    let ready: Value = serde_json::from_str(&line).unwrap();
    assert_eq!(ready["ready"], true);
    let port = ready["port"].as_u64().unwrap() as u16;
    assert_eq!(request(port, "GET", "/api/health", "", false).0, 401);
    let (code, health) = request(port, "GET", "/api/health", "", true);
    assert_eq!(code, 200);
    assert_eq!(
        serde_json::from_str::<Value>(&health).unwrap()["edition"],
        "desktop"
    );
    assert_eq!(
        request(port, "GET", "/sessions/1/workflow", "", true).0,
        404
    );
    let (code, settings) = request(port, "GET", "/api/settings", "", true);
    assert_eq!(code, 200);
    let settings: Value = serde_json::from_str(&settings).unwrap();
    for depth in [190, 900, 995, 996, 1000, 1001, 10_000] {
        let deep = format!("{}0{}", "[".repeat(depth), "]".repeat(depth));
        let body = format!(
            "{{\"revision\":{},\"changes\":{{\"unknown\":{deep}}}}}",
            settings["preferences"]["revision"]
        );
        let (code, _) = request(port, "PATCH", "/api/settings/preferences", &body, true);
        assert!([400, 409, 422].contains(&code), "depth {depth}: {code}");
        assert_eq!(
            request(port, "GET", "/api/health", "", true).0,
            200,
            "depth {depth}"
        );
    }
    let (code, html) = request(port, "GET", "/sessions-dashboard", "", true);
    assert_eq!(code, 200);
    assert!(html.contains("LocalBrain"));
    drop(process.0.stdin.take());
    let deadline = Instant::now() + Duration::from_secs(12);
    loop {
        if let Some(status) = process.0.try_wait().unwrap() {
            assert!(status.success());
            break;
        }
        assert!(Instant::now() < deadline, "native child ignored parent EOF");
        std::thread::sleep(Duration::from_millis(25));
    }
    assert!(TcpStream::connect(("127.0.0.1", port)).is_err());
}
#[test]
fn desktop_without_launch_credential_refuses_before_database_creation() {
    let root = tempfile::Builder::new()
        .prefix("lb-no-token-")
        .tempdir_in("/private/tmp")
        .unwrap();
    let output = command(root.path()).output().unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert!(!root.path().join("data/localbrain.db").exists());
    assert!(String::from_utf8(output.stderr)
        .unwrap()
        .contains("must be launched by LocalBrain.app"));
}
