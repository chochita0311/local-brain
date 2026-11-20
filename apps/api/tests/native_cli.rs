use localbrain_core::backend::{auto_work, db, Config};
use serde_json::{json, Value};
use std::{
    io::Write,
    process::{Command, Output, Stdio},
};
struct Host {
    root: tempfile::TempDir,
    config: Config,
}
impl Host {
    fn new() -> Self {
        let root = tempfile::Builder::new()
            .prefix("lb-cli-")
            .tempdir_in("/private/tmp")
            .unwrap();
        let config = Config::for_data_dir(root.path().join("data"));
        std::fs::create_dir(&config.home_dir).unwrap();
        Self { root, config }
    }
    fn command(&self, binary: &str) -> Command {
        let mut command = Command::new(binary);
        command
            .env_clear()
            .env("PATH", "/usr/bin:/bin")
            .env("HOME", &self.config.home_dir)
            .env("SHELL", "/bin/zsh")
            .env("LOCALBRAIN_DATA_DIR", &self.config.data_dir)
            .env("LOCALBRAIN_CACHE_DIR", &self.config.cache_dir)
            .env("LOCALBRAIN_DEVELOPMENT_DIR", &self.config.development_dir)
            .env("LOCALBRAIN_CONTEXT_ROOT", &self.config.context_root)
            .env("LOCALBRAIN_CLAUDE_ROOT", &self.config.claude_root)
            .env("LOCALBRAIN_CODEX_ROOT", &self.config.codex_root)
            .env(
                "LOCALBRAIN_CLAUDE_BIN",
                self.root.path().join("missing-claude"),
            )
            .env(
                "LOCALBRAIN_CODEX_BIN",
                self.root.path().join("missing-codex"),
            )
            .env("HF_HOME", &self.config.hf_home)
            .env("HF_HUB_CACHE", &self.config.hf_hub_cache)
            .stdin(Stdio::null());
        command
    }
    fn run(&self, args: &[&str]) -> Output {
        self.command(env!("CARGO_BIN_EXE_localbrain"))
            .args(args)
            .output()
            .unwrap()
    }
}
fn success(output: Output) -> String {
    assert!(
        output.status.success(),
        "stdout={} stderr={}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    String::from_utf8(output.stdout).unwrap()
}
#[test]
fn native_cli_entrypoints_doctor_and_passive_status_need_no_python_or_database() {
    let host = Host::new();
    assert_eq!(success(host.run(&["--version"])).trim(), "LocalBrain 0.0.1");
    assert!(success(host.run(&["--help"])).contains("serve"));
    let doctor: Value = serde_json::from_str(&success(host.run(&["doctor"]))).unwrap();
    assert_eq!(doctor["backend"], "rust");
    assert!(doctor.get("python").is_none());
    assert!(!host.config.database_path.exists());
    let status: Value = serde_json::from_str(&success(host.run(&["search", "status"]))).unwrap();
    assert!(status["state"].is_string());
    assert!(!host.config.database_path.exists());
    let output = host
        .command(env!("CARGO_BIN_EXE_lb"))
        .args(["terminal", "list", "--json"])
        .output()
        .unwrap();
    let status: Value = serde_json::from_str(&success(output)).unwrap();
    assert_eq!(status["running"], false);
    assert!(!host.config.database_path.exists());
    assert_eq!(
        host.run(&["serve", "--host", "outside.invalid"])
            .status
            .code(),
        Some(2)
    );
    assert!(!host.config.database_path.exists());
}
#[test]
fn native_init_and_reviewed_packet_refusal_keep_preflight_before_mutation() {
    let host = Host::new();
    let path = host.root.path().join("invalid.json");
    std::fs::write(&path, "{}").unwrap();
    let output = host.run(&["learning", "import", path.to_str().unwrap(), "--reviewed"]);
    assert_eq!(output.status.code(), Some(2));
    assert!(!host.config.database_path.exists());
    assert_eq!(
        success(host.run(&["init"])).trim(),
        "LocalBrain database initialized"
    );
    let conn = db::connect(&host.config).unwrap();
    let count: i64 = conn
        .query_row(
            "SELECT count(*) FROM sqlite_master WHERE type='table'",
            [],
            |row| row.get(0),
        )
        .unwrap();
    assert!(count > 40);
    drop(conn);
    assert!(success(host.run(&["storage", "status"])).contains("locations"));
}
#[test]
fn native_cli_keeps_literal_queries_and_offline_install_failure_codes() {
    let host = Host::new();
    for args in [
        vec!["search", "query", "--", "--help"],
        vec!["search", "query", "-1"],
        vec!["search", "query", "-.1"],
        vec!["search", "query", "-١"],
    ] {
        let output = host.run(&args);
        assert_eq!(output.status.code(), Some(2), "{args:?}");
        assert_eq!(
            String::from_utf8(output.stdout).unwrap().trim(),
            "SEARCH_DISABLED",
            "{args:?}"
        );
        assert!(!host.config.database_path.exists());
    }
    let output = host.run(&["models", "install", "embedding", "--offline"]);
    assert_eq!(output.status.code(), Some(2));
    assert_eq!(
        String::from_utf8(output.stdout).unwrap().trim(),
        "MODEL_NOT_CACHED"
    );
    assert!(!host.config.database_path.exists());
    let output = host
        .command(env!("CARGO_BIN_EXE_localbrain"))
        .env(
            "LOCALBRAIN_DATA_DIR",
            "~localbrain-missing-synthetic-account/data",
        )
        .arg("doctor")
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(!host.config.database_path.exists());
}
#[test]
fn inventory_only_displays_the_same_counts_as_status() {
    let host = Host::new();
    success(host.run(&["init"]));
    let prepared = success(host.run(&["simulate", "--inventory-only", "--show-counts"]));
    let mut lines = prepared.lines();
    assert_eq!(lines.next(), Some("SIMULATION_PREPARED"));
    let coverage: Value = serde_json::from_str(lines.next().unwrap()).unwrap();
    assert!(coverage.is_object());

    let status = success(host.run(&["simulate", "--status", "--show-counts"]));
    let mut lines = status.lines();
    assert_eq!(lines.next(), Some("SIMULATION_PREPARED"));
    let counts: Value = serde_json::from_str(lines.next().unwrap()).unwrap();
    assert_eq!(counts["coverage"], coverage);
}
#[test]
fn real_native_preview_worker_protocol_matches_in_process_synthetic_preparation() {
    let host = Host::new();
    db::initialize(&host.config).unwrap();
    let at = "2026-11-18T00:00:00+00:00";
    let expires = "2026-11-25T00:00:00+00:00";
    let conn = db::connect(&host.config).unwrap();
    conn.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES(1,'codex','Synthetic','/synthetic');INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count) VALUES(1,1,'a','/synthetic/a','Synthetic fixture',1);INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,occurred_at,source_line) VALUES('a',1,1,'message','user','Fix the synthetic parser. Keep provenance.','2026-11-01T09:00:00Z',1);").unwrap();
    drop(conn);
    let args = json!([
        host.config.database_path,
        at,
        "localbrain.auto-work-preview.v1",
        expires
    ]);
    let expected = auto_work::run_preview_operation("prepare", &args).unwrap();
    let mut child = host
        .command(env!("CARGO_BIN_EXE_localbrain"))
        .arg("--auto-work-worker")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let job = json!({"operation":"prepare","args":args,"memory_bytes":512*1024*1024});
    child
        .stdin
        .take()
        .unwrap()
        .write_all(job.to_string().as_bytes())
        .unwrap();
    let output = child.wait_with_output().unwrap();
    let output = success(output);
    let lines = output.lines().collect::<Vec<_>>();
    assert_eq!(lines.len(), 2, "{output}");
    let envelope: Value = serde_json::from_str(lines[0]).unwrap();
    assert_eq!(envelope["ok"], true);
    assert_eq!(envelope["value"], expected);
    let usage: Value = serde_json::from_str(lines[1]).unwrap();
    assert!(usage["peak_bytes"]
        .as_u64()
        .is_some_and(|peak| peak > 0 && peak <= 512 * 1024 * 1024));
}
