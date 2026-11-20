//! Actual owned synthetic CLIs prove missing-adapter, authority and atomic terminal behavior.
use localbrain_core::backend::{
    atlassian::{
        access, catalog, refresh, runner,
        sync::{ExternalExecutionError, ExternalReadExecutor},
    },
    db,
    maintenance::{self, TaskRuntime},
    Config,
};
use serde_json::{json, Value};
use std::{
    fs,
    path::Path,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};
#[test]
fn command_arguments_and_result_rendering_match_frozen_python_bytes() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/runner.json")).unwrap();
    assert_eq!(cases.len(), 6);
    for case in cases {
        if case["operation"] == "external_runner_command_args" {
            let actual = runner::external_runner_command_args(
                case["runner"].as_str().unwrap(),
                Path::new(case["executable"].as_str().unwrap()),
                Path::new(case["root"].as_str().unwrap()),
            );
            if let Some(error) = case.get("error") {
                assert_eq!(actual.unwrap_err().message, error.as_str().unwrap());
            } else {
                assert_eq!(
                    json!(actual
                        .unwrap()
                        .iter()
                        .map(|s| s.to_str().unwrap())
                        .collect::<Vec<_>>()),
                    case["expected"]
                );
            }
        } else {
            assert_eq!(
                runner::render_external_sync_result(&case["value"]),
                case["expected"].as_str().unwrap()
            );
        }
    }
}
const AGENT: &str = r#"#!/bin/sh
printf x > "$(dirname "$0")/agent-launched"
lb_model_output_path=
while [ "$#" -gt 0 ]; do
  if [ "$1" = '--output-last-message' ]; then shift; lb_model_output_path=$1; fi
  shift
done
cat >/dev/null
if [ -n "$lb_model_output_path" ]; then
  printf '%s%s%s\n' '{"schema":"localbrain.external-sync-model-result.v1","run_id":"' "$LOCALBRAIN_RUN_ID" '","summary":"Synthetic model summary"}' > "$lb_model_output_path"
  printf '%s\n' '{"type":"result","result":"Codex finished"}'
else
  printf '%s%s%s\n' '{"type":"result","ignored":{"count":NaN,"surrogate":"\ud800"},"structured_output":{"schema":"localbrain.external-sync-model-result.v1","run_id":"' "$LOCALBRAIN_RUN_ID" '","summary":"Synthetic model summary"}}'
fi
"#;
struct Setup {
    _root: tempfile::TempDir,
    config: Config,
    runtime: Arc<TaskRuntime>,
    item: i64,
    run: String,
    scans: Arc<AtomicUsize>,
}
fn setup(kind: &str, agent: &str) -> Setup {
    use std::os::unix::fs::PermissionsExt;
    let root = tempfile::Builder::new()
        .prefix("lb-atlassian-runner-")
        .tempdir()
        .unwrap();
    let mut config = Config::for_data_dir(root.path().join("data"));
    let executable = root.path().join("synthetic-agent");
    fs::write(&executable, agent).unwrap();
    fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
    if kind == "codex" {
        config.codex_bin = Some(executable);
    } else {
        config.claude_bin = Some(executable);
    }
    db::initialize(&config).unwrap();
    let conn = db::connect(&config).unwrap();
    let source=access::register_source_instance(&conn,&json!({"instance_key":"synthetic-jira","provider_kind":"mcp_gateway","service":"jira","display_name":"Synthetic","config_ref":"synthetic-jira"})).unwrap();
    let source = source["id"].as_i64().unwrap();
    access::record_capability_observation(&conn,source,&json!({"availability":"available","operations":["jira.search_metadata"],"schema_fingerprint":"a".repeat(64)})).unwrap();
    let item=catalog::create_or_reuse_atlassian_stub(&conn,&json!({"source_instance_id":source,"url":"https://jira.runner.test/browse/SYN-1","title":"User local title","coverage":"metadata"})).unwrap();
    let item = item["external_resource_id"].as_i64().unwrap();
    let run = refresh::prepare_atlassian_refresh_run(
        &conn,
        &config,
        &json!({"scope_kind":"item","scope_id":item,"selected_item_ids":[item],"runner":kind}),
        None,
    )
    .unwrap();
    let runtime = Arc::new(TaskRuntime::new(config.clone()));
    let scans = Arc::new(AtomicUsize::new(0));
    let calls = scans.clone();
    runtime.set_scanner(move |_, _| {
        calls.fetch_add(1, Ordering::SeqCst);
        Ok(())
    });
    Setup {
        _root: root,
        config,
        runtime,
        item,
        run,
        scans,
    }
}
fn get(s: &Setup) -> Value {
    maintenance::get_run(&db::connect(&s.config).unwrap(), &s.run)
        .unwrap()
        .unwrap()
}
fn until_terminal(s: &Setup) -> Value {
    let start = Instant::now();
    loop {
        let row = get(s);
        if !matches!(
            row["status"].as_str(),
            Some("queued" | "running" | "cancelling")
        ) {
            s.runtime.shutdown().unwrap();
            return row;
        }
        assert!(
            start.elapsed() < Duration::from_secs(8),
            "synthetic Run deadline: {row}"
        );
        std::thread::sleep(Duration::from_millis(10));
    }
}
struct Executor {
    calls: AtomicUsize,
}
impl ExternalReadExecutor for Executor {
    fn execute(
        &self,
        dispatch: &access::ToolDispatch,
    ) -> std::result::Result<Value, ExternalExecutionError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        assert_eq!(dispatch.logical_operation, "jira.search_metadata");
        Ok(
            json!({"outcome":"changed","identity":{"remote_id":"issue-1"},"metadata":{"key":"SYN-1","summary":"Source fact"}}),
        )
    }
}
fn executor() -> Arc<Executor> {
    Arc::new(Executor {
        calls: AtomicUsize::new(0),
    })
}
#[test]
fn selected_nonfinite_and_literal_private_number_objects_survive_the_actual_run_pipeline() {
    use localbrain_core::backend::json as codec;
    struct Scalars;
    impl ExternalReadExecutor for Scalars {
        fn execute(
            &self,
            _: &access::ToolDispatch,
        ) -> std::result::Result<Value, ExternalExecutionError> {
            Ok(codec::decode(r#"{"outcome":"changed","identity":{"remote_id":"issue-1"},"metadata":{"key":"SYN-1","summary":{"n":NaN,"positive":Infinity,"negative":-Infinity,"literal_nan":{"$serde_json::private::Number":"NaN"},"literal_one":{"$serde_json::private::Number":"1"}}}}"#).unwrap())
        }
    }
    let s = setup("claude", AGENT);
    runner::start_run(&s.runtime, &s.run, Some(Arc::new(Scalars))).unwrap();
    let row = until_terminal(&s);
    assert_eq!(row["status"], "completed", "{row}");
    let result = codec::decode(row["structured_result_json"].as_str().unwrap()).unwrap();
    let facts = &result["targets"][0]["requests"][0]["metadata"]["summary"];
    assert_eq!(
        codec::canonical(facts).unwrap(),
        r#"{"literal_nan":{"$serde_json::private::Number":"NaN"},"literal_one":{"$serde_json::private::Number":"1"},"n":NaN,"negative":-Infinity,"positive":Infinity}"#
    );
    let conn = db::connect(&s.config).unwrap();
    let stored: String = conn
        .query_row(
            "SELECT metadata_json FROM atlassian_item_remote_state WHERE external_resource_id=?",
            [s.item],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(
        codec::canonical(&codec::decode(&stored).unwrap()["summary"]).unwrap(),
        codec::canonical(facts).unwrap()
    );
    let evidence = Path::new(row["manifest_path"].as_str().unwrap())
        .parent()
        .unwrap()
        .join("evidence.json");
    let evidence = codec::decode(&fs::read_to_string(evidence).unwrap()).unwrap();
    assert_eq!(
        codec::canonical(&evidence["targets"][0]["requests"][0]["metadata"]["summary"]).unwrap(),
        codec::canonical(facts).unwrap()
    );
    assert_eq!(codec::strict_output(&result).unwrap_err().status, 500);
    assert_eq!(
        codec::strict_output(&result).unwrap_err().code,
        "json_nonfinite"
    );
}
fn no_remote_fact(s: &Setup) {
    let conn = db::connect(&s.config).unwrap();
    let item = db::row(
        &conn,
        "SELECT * FROM atlassian_items WHERE external_resource_id=?",
        [s.item],
    )
    .unwrap()
    .unwrap();
    assert!(item["remote_id"].is_null());
    assert_eq!(
        conn.query_row::<i64, _, _>(
            "SELECT count(*) FROM atlassian_item_remote_state WHERE external_resource_id=?",
            [s.item],
            |r| r.get(0)
        )
        .unwrap(),
        0
    );
}
#[test]
fn default_none_executor_refuses_before_any_manifest_or_process_access() {
    let s = setup("claude", AGENT);
    let row = get(&s);
    let path = row["manifest_path"].as_str().unwrap();
    fs::remove_file(path).unwrap();
    runner::start_run(&s.runtime, &s.run, None).unwrap();
    let row = until_terminal(&s);
    assert_eq!(row["status"], "failed");
    assert_eq!(
        row["error"],
        "External synchronization requires an approved read executor."
    );
    assert!(!s._root.path().join("agent-launched").exists());
    assert!(!Path::new(path)
        .parent()
        .unwrap()
        .join("evidence.json")
        .exists());
    assert_eq!(s.scans.load(Ordering::SeqCst), 1);
    no_remote_fact(&s);
}
#[test]
fn both_owned_synthetic_clis_apply_only_executor_facts_and_preserve_local_title() {
    for kind in ["claude", "codex"] {
        let s = setup(kind, AGENT);
        let exec = executor();
        runner::start_run(&s.runtime, &s.run, Some(exec.clone())).unwrap();
        let row = until_terminal(&s);
        assert_eq!(row["status"], "completed", "{row}");
        assert_eq!(row["mcp_calls_used"], 1);
        assert_eq!(exec.calls.load(Ordering::SeqCst), 1);
        assert_eq!(s.scans.load(Ordering::SeqCst), 1);
        let result: Value =
            serde_json::from_str(row["structured_result_json"].as_str().unwrap()).unwrap();
        assert_eq!(result["summary"], "Synthetic model summary");
        assert_eq!(
            result["targets"][0]["requests"][0]["metadata"]["summary"],
            "Source fact"
        );
        let conn = db::connect(&s.config).unwrap();
        let remote = db::row(
            &conn,
            "SELECT * FROM atlassian_item_remote_state WHERE external_resource_id=?",
            [s.item],
        )
        .unwrap()
        .unwrap();
        let metadata: Value =
            serde_json::from_str(remote["metadata_json"].as_str().unwrap()).unwrap();
        assert_eq!(metadata["summary"], "Source fact");
        assert_eq!(
            conn.query_row::<String, _, _>(
                "SELECT title FROM external_resources WHERE id=?",
                [s.item],
                |r| r.get(0)
            )
            .unwrap(),
            "User local title"
        );
        assert_eq!(
            fs::read_to_string(row["result_path"].as_str().unwrap()).unwrap(),
            runner::render_external_sync_result(&result)
        );
    }
}
#[test]
fn terminal_update_failure_rolls_back_refresh_facts_before_failed_finalization() {
    let s = setup("claude", AGENT);
    db::connect(&s.config).unwrap().execute_batch("CREATE TRIGGER synthetic_terminal_failure BEFORE UPDATE ON maintenance_runs WHEN NEW.status='completed' BEGIN SELECT RAISE(ABORT,'synthetic terminal failure');END").unwrap();
    runner::start_run(&s.runtime, &s.run, Some(executor())).unwrap();
    let row = until_terminal(&s);
    assert_eq!(row["status"], "failed");
    assert!(row["error"]
        .as_str()
        .unwrap()
        .contains("synthetic terminal failure"));
    assert_eq!(s.scans.load(Ordering::SeqCst), 1);
    no_remote_fact(&s);
}
#[test]
fn model_cannot_author_source_facts_or_expand_its_closed_summary_schema() {
    let bad = AGENT.replace(
        "\"summary\":\"Synthetic model summary\"}}'",
        "\"summary\":\"Synthetic model summary\",\"metadata\":{\"summary\":\"fabricated\"}}}'",
    );
    assert_ne!(bad, AGENT);
    let s = setup("claude", &bad);
    runner::start_run(&s.runtime, &s.run, Some(executor())).unwrap();
    let row = until_terminal(&s);
    assert_eq!(row["status"], "failed");
    assert_eq!(row["error"], "model result has unsupported fields");
    no_remote_fact(&s);
}
#[test]
fn cancellation_after_an_inflight_callback_stops_before_model_launch_and_apply() {
    use std::sync::{mpsc, Mutex};
    struct Blocking {
        entered: mpsc::Sender<()>,
        release: Mutex<mpsc::Receiver<()>>,
    }
    impl ExternalReadExecutor for Blocking {
        fn execute(
            &self,
            _: &access::ToolDispatch,
        ) -> std::result::Result<Value, ExternalExecutionError> {
            self.entered.send(()).unwrap();
            self.release
                .lock()
                .unwrap()
                .recv_timeout(Duration::from_secs(5))
                .unwrap();
            Ok(
                json!({"outcome":"changed","identity":{"remote_id":"issue-1"},"metadata":{"key":"SYN-1","summary":"Source fact"}}),
            )
        }
    }
    let s = setup("claude", AGENT);
    let (entered_tx, entered_rx) = mpsc::channel();
    let (release_tx, release_rx) = mpsc::channel();
    runner::start_run(
        &s.runtime,
        &s.run,
        Some(Arc::new(Blocking {
            entered: entered_tx,
            release: Mutex::new(release_rx),
        })),
    )
    .unwrap();
    entered_rx.recv_timeout(Duration::from_secs(5)).unwrap();
    assert!(s.runtime.cancel(&s.run).unwrap());
    release_tx.send(()).unwrap();
    assert_eq!(until_terminal(&s)["status"], "cancelled");
    assert!(!s._root.path().join("agent-launched").exists());
    no_remote_fact(&s);
}
