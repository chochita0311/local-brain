use localbrain_core::backend::{
    db,
    maintenance::{self, ProcessSpec, TaskRuntime},
    Config,
};
use serde_json::{json, Value};
use std::{
    ffi::OsString,
    fs,
    path::PathBuf,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};
fn setup() -> (tempfile::TempDir, Config, Arc<TaskRuntime>) {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    db::initialize(&config).unwrap();
    let runtime = Arc::new(TaskRuntime::new(config.clone()));
    (root, config, runtime)
}
fn run(config: &Config, id: &str) {
    db::connect(config).unwrap().execute("INSERT INTO maintenance_runs(id,task_type,runner,cwd,status,stream_path,result_path,stderr_path) VALUES (?,'synthetic','claude',?,'queued',?,?,?)",rusqlite::params![id,config.home_dir.to_str().unwrap(),config.data_dir.join("runs").join(id).join("stream.jsonl").to_str().unwrap(),config.data_dir.join("runs").join(id).join("result.md").to_str().unwrap(),config.data_dir.join("runs").join(id).join("stderr.log").to_str().unwrap()]).unwrap();
}
fn spec(config: &Config, id: &str, script: &str) -> ProcessSpec {
    let directory = config.data_dir.join("runs").join(id);
    ProcessSpec {
        arguments: vec![
            OsString::from("/bin/sh"),
            OsString::from("-c"),
            OsString::from(script),
        ],
        cwd: config.data_dir.clone(),
        prompt: "synthetic prompt\n".into(),
        stream_path: directory.join("stream.jsonl"),
        result_path: Some(directory.join("result.md")),
        stderr_path: directory.join("stderr.log"),
        mcp_call_budget: Some(0),
        timeout: Some(Duration::from_secs(5)),
    }
}
fn status(config: &Config, id: &str) -> Value {
    maintenance::get_run(&db::connect(config).unwrap(), id)
        .unwrap()
        .unwrap()
}
fn until(mut predicate: impl FnMut() -> bool) {
    let start = Instant::now();
    while !predicate() {
        assert!(
            start.elapsed() < Duration::from_secs(6),
            "synthetic job deadline"
        );
        std::thread::sleep(Duration::from_millis(10));
    }
}
#[test]
fn stream_persists_deduplicated_mcp_advisory_and_structured_result() {
    let (_root, config, runtime) = setup();
    run(&config, "lb-test");
    let script="cat >/dev/null; printf '%s\\n' '{\"type\":\"assistant\",\"message\":{\"content\":[{\"type\":\"text\",\"text\":\" partial \"},{\"type\":\"tool_use\",\"id\":\"m1\",\"name\":\"mcp__synthetic\"}]}}' '{\"type\":\"assistant\",\"message\":{\"content\":[{\"type\":\"tool_use\",\"id\":\"m1\",\"name\":\"mcp__synthetic\"}]}}' '{\"type\":\"result\",\"result\":\" final \",\"structured_output\":{\"summary\":\"Synthetic\"}}'; printf '%s' 'synthetic stderr' >&2";
    let output = runtime
        .execute_process("lb-test", spec(&config, "lb-test", script))
        .unwrap();
    assert_eq!(output.return_code, 0);
    assert_eq!(output.output, "final");
    assert_eq!(output.stderr, "synthetic stderr");
    assert_eq!(
        output.mcp_calls,
        json!([{"id":"m1","name":"mcp__synthetic"}])
            .as_array()
            .unwrap()
            .clone()
    );
    assert_eq!(
        maintenance::structured_result(output.final_event.as_ref()),
        Some(json!({"summary":"Synthetic"}))
    );
    assert_eq!(status(&config, "lb-test")["mcp_budget_exceeded"], 1);
    assert_eq!(status(&config, "lb-test")["mcp_calls_used"], 1);
    assert_eq!(
        maintenance::read_run_output(&status(&config, "lb-test")).unwrap(),
        "final"
    );
    assert_eq!(
        fs::read_to_string(config.data_dir.join("runs/lb-test/stream.jsonl"))
            .unwrap()
            .lines()
            .count(),
        3
    );
    runtime
        .finalize(
            "lb-test",
            "completed",
            &json!({"pid":null,"summary":"Synthetic"}),
        )
        .unwrap();
    assert_eq!(status(&config, "lb-test")["status"], "completed");
    assert!(!runtime.cancel("lb-test").unwrap());
}
#[test]
fn cancellation_tracks_owned_child_and_keeps_terminal_state() {
    let (_root, config, runtime) = setup();
    run(&config, "lb-cancel");
    let selected = spec(&config, "lb-cancel", "cat >/dev/null; while :; do :; done");
    runtime
        .start("lb-cancel", move |runtime| {
            let _ = runtime.execute_process("lb-cancel", selected)?;
            runtime.finalize("lb-cancel", "cancelled", &json!({"pid":null}))
        })
        .unwrap();
    until(|| status(&config, "lb-cancel")["status"] == "running");
    assert!(runtime.cancel("lb-cancel").unwrap());
    until(|| status(&config, "lb-cancel")["status"] == "cancelled");
    assert!(status(&config, "lb-cancel")["pid"].is_null());
    runtime.shutdown().unwrap();
}
#[test]
fn recovery_changes_only_owned_active_task_shapes_and_scans_runners() {
    let (_root, config, runtime) = setup();
    run(&config, "lb-recover");
    db::connect(&config).unwrap().execute_batch("INSERT INTO maintenance_runs(id,status,pid) VALUES ('unowned','running',999999),('prepared','prepared',999999),('terminal','completed',999999);").unwrap();
    let calls = Arc::new(AtomicUsize::new(0));
    let copied = calls.clone();
    runtime.set_scanner(move |_, runner| {
        assert_eq!(runner, "claude");
        copied.fetch_add(1, Ordering::SeqCst);
        Ok(())
    });
    assert_eq!(runtime.reconcile_interrupted_runs().unwrap(), 1);
    assert_eq!(status(&config, "lb-recover")["status"], "interrupted");
    assert!(status(&config, "lb-recover")["pid"].is_null());
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    for (id, state) in [
        ("unowned", "running"),
        ("prepared", "prepared"),
        ("terminal", "completed"),
    ] {
        assert_eq!(status(&config, id)["status"], state);
        assert_eq!(status(&config, id)["pid"], 999999);
    }
    assert_eq!(runtime.reconcile_interrupted_runs().unwrap(), 0);
}
#[test]
fn explicit_runner_path_and_atomic_terminal_transaction_are_preserved() {
    let (_root, mut config, runtime) = setup();
    run(&config, "lb-transaction");
    config.claude_bin = Some(PathBuf::from("/synthetic/missing"));
    assert!(maintenance::runner_executable(&config, "claude").is_none());
    assert!(maintenance::runner_executable(&config, "invalid").is_none());
    let connection = db::connect(&config).unwrap();
    connection.execute_batch("BEGIN IMMEDIATE").unwrap();
    maintenance::update_run_row(
        &connection,
        "lb-transaction",
        &json!({"status":"completed","structured_result_json":"{}"}),
    )
    .unwrap();
    connection.execute_batch("ROLLBACK").unwrap();
    assert_eq!(status(&config, "lb-transaction")["status"], "queued");
    assert!(maintenance::update_run_row(
        &connection,
        "lb-transaction",
        &json!({"status = 'completed' --":"x"})
    )
    .is_err());
    assert!(runtime.cancel("lb-transaction").unwrap());
    assert_eq!(status(&config, "lb-transaction")["status"], "cancelled");
    for (input, expected) in [
        ("prepared", "아직 실행하지 않았습니다."),
        ("completed", "표시할 실행 출력이 없습니다."),
        ("running", "아직 표시할 실행 출력이 없습니다."),
    ] {
        assert_eq!(maintenance::run_output_placeholder(input), expected);
    }
}
#[test]
fn process_timeout_and_artifact_symlink_refusal_leave_no_active_child() {
    use std::os::unix::fs::symlink;
    let (_root, config, runtime) = setup();
    run(&config, "lb-timeout");
    let mut selected = spec(&config, "lb-timeout", "cat >/dev/null; while :; do :; done");
    selected.timeout = Some(Duration::from_millis(50));
    assert_eq!(
        runtime
            .execute_process("lb-timeout", selected)
            .unwrap_err()
            .code,
        "runner-timeout"
    );
    runtime
        .finalize_failed("lb-timeout", "Synthetic timeout")
        .unwrap();
    run(&config, "lb-link");
    let selected = spec(&config, "lb-link", "exit 0");
    fs::create_dir_all(selected.stream_path.parent().unwrap()).unwrap();
    let keep = config.data_dir.join("keep");
    fs::write(&keep, "keep").unwrap();
    symlink(&keep, &selected.stream_path).unwrap();
    assert!(runtime.execute_process("lb-link", selected).is_err());
    assert_eq!(fs::read_to_string(keep).unwrap(), "keep");
    runtime.shutdown().unwrap();
}
#[test]
fn stderr_remains_visible_when_a_runner_emits_no_result() {
    let (_root, config, runtime) = setup();
    run(&config, "lb-stderr");
    let output = runtime
        .execute_process(
            "lb-stderr",
            spec(
                &config,
                "lb-stderr",
                "cat >/dev/null; printf '%s' 'synthetic error' >&2; exit 2",
            ),
        )
        .unwrap();
    assert_eq!(output.return_code, 2);
    assert!(output.output.is_empty());
    assert_eq!(
        maintenance::read_run_output(&status(&config, "lb-stderr")).unwrap(),
        "synthetic error"
    );
    assert!(!config.data_dir.join("runs/lb-stderr/result.md").exists());
}
fn scripted_lines(lines: &[String]) -> String {
    format!(
        "cat >/dev/null; printf '%s\\n' {}",
        lines
            .iter()
            .map(|line| format!("'{}'", line.replace('\'', "'\\''")))
            .collect::<Vec<_>>()
            .join(" ")
    )
}
#[test]
fn scoped_protocol_preserves_ignored_exceptional_scalars_and_current_tool_accounting() {
    let (_root, config, runtime) = setup();
    run(&config, "lb-scalars");
    let script=scripted_lines(&[r#"{"type":"assistant","message":{"content":[{"type":"tool_use","id":"one","name":"mcp__synthetic","input":{"ignored":NaN,"unicode":"\ud800"}},{"type":"text","text":"partial"}]},"ignored":Infinity}"#.into(),r#"{"type":"assistant","message":{"content":[{"type":"tool_use","id":"one","name":"mcp__synthetic"}]},"ignored":-Infinity}"#.into(),r#"{"type":"result","result":"final","structured_output":{"summary":"Synthetic"},"ignored_nan":NaN,"ignored_unicode":"\ud800"}"#.into()]);
    let output = runtime
        .execute_process("lb-scalars", spec(&config, "lb-scalars", &script))
        .unwrap();
    assert_eq!(output.output, "final");
    assert_eq!(
        output.mcp_calls,
        vec![json!({"id":"one","name":"mcp__synthetic"})]
    );
    assert_eq!(
        output.structured_result().unwrap(),
        Some(json!({"summary":"Synthetic"}))
    );
    assert_eq!(status(&config, "lb-scalars")["mcp_calls_used"], 1);
    assert_eq!(status(&config, "lb-scalars")["mcp_budget_exceeded"], 1);
    assert!(
        fs::read_to_string(config.data_dir.join("runs/lb-scalars/stream.jsonl"))
            .unwrap()
            .contains("ignored_nan")
    );
}
#[test]
fn scoped_protocol_refuses_selected_unicode_without_publishing_success() {
    let (_root, config, runtime) = setup();
    for (index, event) in [
        r#"{"type":"result","result":"\ud800","structured_output":{"summary":"safe"}}"#.to_owned(),
        r#"{"type":"result","result":"valid","structured_output":{"summary":"\ud800"}}"#.to_owned(),
        json!({"type":"result","result":"valid","structured_output":r#"{"summary":"\ud800"}"#})
            .to_string(),
    ]
    .into_iter()
    .enumerate()
    {
        let id = format!("lb-unicode-{index}");
        run(&config, &id);
        let command = spec(&config, &id, &scripted_lines(&[event]));
        let run_id = id.clone();
        runtime
            .start(&id, move |runtime| {
                let output = runtime.execute_process(&run_id, command)?;
                output.structured_result()?;
                Ok(())
            })
            .unwrap();
        until(|| status(&config, &id)["status"] == "failed");
        let row = status(&config, &id);
        assert_eq!(row["status"], "failed");
        assert!(row["error"].as_str().unwrap().contains("surrogate"));
        assert!(row["pid"].is_null());
    }
    runtime.shutdown().unwrap();
}
#[test]
fn protocol_admits_deep_legacy_json_and_fails_above_the_shared_recursion_bound() {
    backend_worker(|| {
        let (_root, config, runtime) = setup();
        run(&config, "lb-depth");
        let deep = format!("{}0{}", "[".repeat(900), "]".repeat(900));
        let event = format!(
            r#"{{"type":"result","result":"valid","structured_output":{{"summary":"Deep"}},"ignored":{deep}}}"#
        );
        let output = runtime
            .execute_process(
                "lb-depth",
                spec(&config, "lb-depth", &scripted_lines(&[event])),
            )
            .unwrap();
        assert_eq!(
            output.structured_result().unwrap(),
            Some(json!({"summary":"Deep"}))
        );
        drop(output);
        run(&config, "lb-too-deep");
        let deep = format!("{}0{}", "[".repeat(1001), "]".repeat(1001));
        let event = format!(
            r#"{{"type":"result","result":"valid","structured_output":{{"summary":"Deep"}},"ignored":{deep}}}"#
        );
        let caught = runtime
            .execute_process(
                "lb-too-deep",
                spec(&config, "lb-too-deep", &scripted_lines(&[event])),
            )
            .unwrap_err();
        assert_eq!(caught.code, "json_scalar");
        assert!(caught.message.contains("recursion limit"));
    });
}
fn backend_worker(operation: impl FnOnce() + Send + 'static) {
    localbrain_core::backend::worker_thread("maintenance-depth-proof")
        .spawn(operation)
        .unwrap()
        .join()
        .unwrap();
}
