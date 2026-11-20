use localbrain_core::backend::{
    db,
    insights::{
        guidance::{CORE_VERSION, REPORT_VERSION},
        runs::*,
        usage::insight_usage_cost,
    },
    Config,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{
    fs,
    os::unix::fs::{symlink, PermissionsExt},
    path::Path,
    sync::Arc,
    thread,
    time::{Duration, Instant},
};
struct Fixture {
    _directory: tempfile::TempDir,
    config: Config,
    connection: Connection,
    choice: RunnerChoice,
}
struct RuntimeGuard(Arc<InsightRuntime>);
impl std::ops::Deref for RuntimeGuard {
    type Target = Arc<InsightRuntime>;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
impl Drop for RuntimeGuard {
    fn drop(&mut self) {
        let _ = self.0.shutdown();
    }
}
fn new_runtime(config: &Config) -> RuntimeGuard {
    RuntimeGuard(Arc::new(InsightRuntime::new(config.clone())))
}
impl Fixture {
    fn new(script: &str) -> Self {
        let directory = tempfile::tempdir().unwrap();
        let mut config = Config::for_data_dir(directory.path().join("data"));
        config.timezone_name = "UTC".into();
        fs::create_dir_all(&config.home_dir).unwrap();
        let binary = directory.path().join("synthetic-codex");
        fs::write(&binary, script).unwrap();
        fs::set_permissions(&binary, fs::Permissions::from_mode(0o700)).unwrap();
        config.codex_bin = Some(binary);
        let connection = db::connect(&config).unwrap();
        connection.execute_batch(db::SCHEMA).unwrap();
        connection.execute("INSERT INTO sources(id,provider_kind,name,root_path)VALUES(1,'codex','Synthetic',?)",[config.home_dir.join("sessions").to_string_lossy()]).unwrap();
        for id in 1..=2 {
            connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title)VALUES(?,1,?,?,'Synthetic work')",params![id,format!("work-{id}"),format!("/synthetic/work-{id}.jsonl")]).unwrap();
            connection.execute("INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,source_line)VALUES(?,?,1,'2026-09-27T12:00:00Z','message','user','Synthetic learning question',1)",params![format!("event-{id}"),id]).unwrap();
        }
        let choice = RunnerChoice {
            runner: "codex".into(),
            label: "Synthetic CLI".into(),
            model: "selected-unverified-model".into(),
            codex_home: config.home_dir.clone(),
            profile: "Synthetic".into(),
        };
        Self {
            _directory: directory,
            config,
            connection,
            choice,
        }
    }
    fn prepare(&self) -> String {
        prepare_insight_run(
            &self.connection,
            &self.config,
            &PrepareRequest {
                mode: "discover".into(),
                question: None,
                runner: "codex".into(),
            },
            std::slice::from_ref(&self.choice),
            "2026-09-30T00:00:00Z".parse().unwrap(),
        )
        .unwrap()
    }
    fn row(&self, id: &str) -> Value {
        get_insight_run(&self.connection, id).unwrap().unwrap()
    }
    fn wait(&self, id: &str, condition: impl Fn(&Value) -> bool) -> Value {
        let start = Instant::now();
        loop {
            let row = self.row(id);
            if condition(&row) {
                return row;
            }
            assert!(
                start.elapsed() < Duration::from_secs(8),
                "timed out waiting for {id}: {row}"
            );
            thread::sleep(Duration::from_millis(10));
        }
    }
}
fn no_finding() -> Value {
    json!({"result_version":REPORT_VERSION,"title":"Synthetic analysis","summary":"A bounded synthetic observation.","selection_reason":"The selected excerpts do not establish an improvement.","selection_evidence_ids":["event-1"],"outcome":"no_actionable_finding","findings":[],"no_finding_reason":"No supported actionable finding.","additional_evidence":{"kind":"none","question":"","evidence_ids":[],"message_requests":[]},"limits":"Synthetic fixture only."})
}
fn finding() -> Value {
    let all: Value = serde_json::from_str(include_str!(
        "../src/backend/insights/fixtures/guidance-golden.json"
    ))
    .unwrap();
    all["cases"]
        .as_array()
        .unwrap()
        .iter()
        .find(|case| {
            case.get("expected").is_some()
                && case["value"]["outcome"] == "findings"
                && case["value"]["result_version"] == REPORT_VERSION
        })
        .unwrap()["value"]
        .clone()
}
fn script(response: Option<&Value>, blocked: bool, exit: i32) -> String {
    let mut script="#!/bin/sh\noutput=\nwhile [ \"$#\" -gt 0 ]; do\n if [ \"$1\" = '--output-last-message' ]; then shift; output=$1; fi\n shift\ndone\ncat >/dev/null\nprintf x >> launched\nprintf '%s\\n' '{\"type\":\"turn.completed\",\"model\":\"gpt-6-astra\",\"usage\":{\"input_tokens\":1000,\"cached_input_tokens\":800,\"output_tokens\":100,\"reasoning_output_tokens\":40}}'\nprintf '%s\\n' 'synthetic diagnostic' >&2\n".to_owned();
    if let Some(response) = response {
        script.push_str("cat >\"$output\" <<'NATIVE_SYNTHETIC_RESPONSE'\n");
        script.push_str(&serde_json::to_string(response).unwrap());
        script.push_str("\nNATIVE_SYNTHETIC_RESPONSE\n");
    }
    if blocked {
        script.push_str("trap 'exit 0' TERM\nwhile :; do :; done\n");
    } else {
        script.push_str(&format!("exit {exit}\n"));
    }
    script
}
#[test]
fn preparation_freezes_private_evidence_guides_prompt_schema_without_starting() {
    let f = Fixture::new(&script(None, false, 0));
    let runtime = InsightRuntime::new(f.config.clone());
    let id = f.prepare();
    let run = f.row(&id);
    assert!(valid_run_id(&id));
    assert_eq!(run["status"], "queued");
    assert!(run["pid"].is_null());
    assert_eq!(run["guide_version"], CORE_VERSION);
    let root = run_root(&f.config, &id).unwrap();
    assert!(!root.join("launched").exists());
    assert_eq!(
        fs::metadata(&root).unwrap().permissions().mode() & 0o777,
        0o700
    );
    for name in ["evidence.json", "prompt.md", "response-schema.json"] {
        assert_eq!(
            fs::metadata(root.join(name)).unwrap().permissions().mode() & 0o777,
            0o600
        );
    }
    let options: Value = serde_json::from_str(run["settings_json"].as_str().unwrap()).unwrap();
    assert_eq!(options["usage_source_id"], 1);
    assert_eq!(options["service_tier"], "standard");
    assert_eq!(options["guide"]["playbooks"].as_array().unwrap().len(), 11);
    assert_eq!(options["native_session_persistence"], false);
    let prompt = fs::read_to_string(root.join("prompt.md")).unwrap();
    assert!(prompt.contains("answer the person's actual question first"));
    assert!(prompt.contains("\"message_count\":1"));
    assert!(prompt.contains("\"message_index\":0"));
    assert_eq!(list_insight_runs(&f.connection, 25, None).unwrap().len(), 1);
    assert!(get_insight_run(&f.connection, "../invalid")
        .unwrap()
        .is_none());
    assert_eq!(runtime.reconcile(&f.connection).unwrap(), 1);
    assert_eq!(f.row(&id)["status"], "interrupted");
    assert!(!root.join("launched").exists());
    assert_eq!(runtime.reconcile(&f.connection).unwrap(), 0);
}
#[test]
fn source_binding_and_sql_failure_refuse_preparation_and_cleanup_only_owned_run() {
    let f = Fixture::new(&script(None, false, 0));
    f.connection
        .execute(
            "UPDATE sources SET root_path='/synthetic/wrong' WHERE id=1",
            [],
        )
        .unwrap();
    assert!(prepare_insight_run(
        &f.connection,
        &f.config,
        &PrepareRequest {
            mode: "discover".into(),
            question: None,
            runner: "codex".into()
        },
        std::slice::from_ref(&f.choice),
        "2026-09-30T00:00:00Z".parse().unwrap()
    )
    .is_err());
    assert!(!f.config.data_dir.join("personal-insight-runs").exists());
    f.connection
        .execute(
            "UPDATE sources SET root_path=? WHERE id=1",
            [f.config.home_dir.join("sessions").to_string_lossy()],
        )
        .unwrap();
    f.connection.execute_batch("CREATE TRIGGER refuse_insight BEFORE INSERT ON personal_insight_runs BEGIN SELECT RAISE(ABORT,'synthetic failure');END;").unwrap();
    assert!(prepare_insight_run(
        &f.connection,
        &f.config,
        &PrepareRequest {
            mode: "discover".into(),
            question: None,
            runner: "codex".into()
        },
        std::slice::from_ref(&f.choice),
        "2026-09-30T00:00:00Z".parse().unwrap()
    )
    .is_err());
    assert_eq!(
        fs::read_dir(f.config.data_dir.join("personal-insight-runs"))
            .unwrap()
            .count(),
        0
    );
}
#[test]
fn runner_uses_resolved_executable_exact_frozen_schema_and_restricted_cli_arguments() {
    let f = Fixture::new(&script(None, false, 0));
    let id = f.prepare();
    let mut run = f.row(&id);
    let root = run_root(&f.config, &id).unwrap();
    let quoted = f.config.data_dir.join("runtime \"quoted\" 한글");
    fs::write(&quoted, "placeholder").unwrap();
    let launcher = f.config.data_dir.join("launcher");
    symlink(&quoted, &launcher).unwrap();
    let args = runner_args(&f.config, &run, &launcher)
        .unwrap()
        .into_iter()
        .map(|s| s.into_string().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(Path::new(&args[0]), fs::canonicalize(&quoted).unwrap());
    for arg in [
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "permissions.external-sync.network.enabled=false",
        "web_search=\"disabled\"",
        "shell_environment_policy.inherit=\"none\"",
        "service_tier=\"default\"",
    ] {
        assert!(args.iter().any(|a| a == arg), "{arg}");
    }
    assert!(!args.iter().any(|a| a.contains("bypass")));
    let filesystem = args
        .iter()
        .find(|arg| arg.starts_with("permissions.external-sync.filesystem="))
        .unwrap();
    assert!(filesystem.contains("\":minimal\"=\"read\""));
    assert!(filesystem.contains("\":workspace_roots\"={\".\"=\"read\"}"));
    assert!(filesystem.contains("runtime \\\"quoted\\\" 한글"));
    fs::write(root.join("response-schema.json"), "{}").unwrap();
    assert!(runner_args(&f.config, &run, &quoted).is_err());
    fs::remove_file(root.join("response-schema.json")).unwrap();
    let mut options: Value = serde_json::from_str(run["settings_json"].as_str().unwrap()).unwrap();
    options["guide"]["core_version"] = json!("personal-improvement-core-v3");
    options["guide"]
        .as_object_mut()
        .unwrap()
        .remove("report_version");
    run["settings_json"] = json!(options.to_string());
    runner_args(&f.config, &run, &quoted).unwrap();
    let schema: Value =
        serde_json::from_str(&fs::read_to_string(root.join("response-schema.json")).unwrap())
            .unwrap();
    assert_eq!(
        schema["properties"]["result_version"]["enum"],
        json!(["personal-improvement-report-v2"])
    );
    assert!(
        runner_choices_with(&f.config, Some(&f.config.home_dir), Some("synthetic"))
            .unwrap()
            .iter()
            .all(|c| c.model == "synthetic")
    );
    assert!(
        runner_choices_with(&f.config, Some(&root.join("absent")), None)
            .unwrap()
            .is_empty()
    );
}
#[test]
fn explicit_synthetic_runs_complete_and_keep_observed_usage_without_retry() {
    for response in [no_finding(), finding()] {
        let f = Fixture::new(&script(Some(&response), false, 0));
        let id = f.prepare();
        let root = run_root(&f.config, &id).unwrap();
        let runtime = new_runtime(&f.config);
        runtime.start(&id).unwrap();
        let run = f.wait(&id, |run| {
            !["queued", "running"].contains(&run["status"].as_str().unwrap())
        });
        assert_eq!(
            run["status"],
            if response["outcome"] == "findings" {
                "completed"
            } else {
                "no_finding"
            }
        );
        assert!(run["pid"].is_null());
        assert_eq!(run["model"], "selected-unverified-model");
        assert_eq!(run["resolved_model"], "gpt-6-astra");
        assert!(root.join("validated-result.json").is_file());
        assert!(root.join("report.md").is_file());
        assert_eq!(
            insight_usage_cost(&f.connection, &id).unwrap().unwrap()["estimated_cost_usd"],
            "0.007800000000"
        );
        runtime.shutdown().unwrap();
        assert_eq!(fs::read(root.join("launched")).unwrap(), b"x");
        assert!(!runtime.cancel(&f.connection, &id).unwrap());
    }
}
#[test]
fn failed_results_and_nonzero_exit_retain_observed_usage_without_another_launch() {
    for script in [script(Some(&json!({})), false, 0), script(None, false, 7)] {
        let f = Fixture::new(&script);
        let id = f.prepare();
        let runtime = new_runtime(&f.config);
        runtime.start(&id).unwrap();
        let run = f.wait(&id, |run| run["status"] == "failed");
        assert!(!run["error"].as_str().unwrap().is_empty());
        assert_eq!(
            insight_usage_cost(&f.connection, &id).unwrap().unwrap()["estimated_cost_usd"],
            "0.007800000000"
        );
        assert!(run["usage_json"].is_string());
        runtime.shutdown().unwrap();
        assert_eq!(
            fs::read(run_root(&f.config, &id).unwrap().join("launched")).unwrap(),
            b"x"
        );
    }
}
#[test]
fn cancellation_and_shutdown_stop_only_owned_child_and_preserve_usage() {
    for shutdown in [false, true] {
        let f = Fixture::new(&script(None, true, 0));
        let id = f.prepare();
        let runtime = new_runtime(&f.config);
        runtime.start(&id).unwrap();
        let run = f.wait(&id, |run| run["usage_json"].is_string());
        let pid = run["pid"].as_i64().unwrap();
        if shutdown {
            runtime.shutdown().unwrap();
        } else {
            assert!(runtime.cancel(&f.connection, &id).unwrap());
            runtime.shutdown().unwrap();
        }
        let run = f.row(&id);
        assert_eq!(
            run["status"],
            if shutdown { "interrupted" } else { "cancelled" }
        );
        assert!(run["pid"].is_null());
        assert_eq!(
            insight_usage_cost(&f.connection, &id).unwrap().unwrap()["estimated_cost_usd"],
            "0.007800000000"
        );
        assert_eq!(unsafe { libc::kill(pid as i32, 0) }, -1);
        assert_eq!(
            std::io::Error::last_os_error().raw_os_error(),
            Some(libc::ESRCH)
        );
    }
    let f = Fixture::new(&script(None, true, 0));
    let id = f.prepare();
    let runtime = new_runtime(&f.config);
    assert!(runtime.cancel(&f.connection, &id).unwrap());
    runtime.start(&id).unwrap();
    runtime.shutdown().unwrap();
    assert_eq!(f.row(&id)["status"], "cancelled");
    assert!(!run_root(&f.config, &id).unwrap().join("launched").exists());
}
#[test]
fn capped_artifacts_keep_parsing_later_usage_and_continuous_output_cannot_starve_cancel() {
    let block = "x".repeat(60_000);
    let later = json!({"type":"turn.completed","model":"gpt-6-astra","usage":{"input_tokens":2000,"cached_input_tokens":1600,"output_tokens":200,"reasoning_output_tokens":80}});
    let burst=format!("synthetic_block='{block}'\nsynthetic_i=0\nwhile [ \"$synthetic_i\" -lt 140 ]; do printf '%s\\n' \"$synthetic_block\"; synthetic_i=$((synthetic_i+1)); done\nsynthetic_i=0\nwhile [ \"$synthetic_i\" -lt 20 ]; do printf '%s\\n' \"$synthetic_block\" >&2; synthetic_i=$((synthetic_i+1)); done\ncat <<'NATIVE_LATE_USAGE'\n{later}\nNATIVE_LATE_USAGE\nexit 0\n");
    let f = Fixture::new(&script(Some(&no_finding()), false, 0).replace("exit 0\n", &burst));
    let id = f.prepare();
    let runtime = new_runtime(&f.config);
    runtime.start(&id).unwrap();
    let run = f.wait(&id, |run| {
        !["queued", "running"].contains(&run["status"].as_str().unwrap())
    });
    assert_eq!(run["status"], "no_finding");
    assert_eq!(
        fs::metadata(run["stream_path"].as_str().unwrap())
            .unwrap()
            .len(),
        8_000_000
    );
    assert_eq!(
        fs::metadata(run["stderr_path"].as_str().unwrap())
            .unwrap()
            .len(),
        1_000_000
    );
    assert_eq!(
        insight_usage_cost(&f.connection, &id).unwrap().unwrap()["estimated_cost_usd"],
        "0.015600000000"
    );
    assert_eq!(
        f.connection
            .query_row("SELECT COUNT(*) FROM usage_records", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
    runtime.shutdown().unwrap();
    let flood = script(None, true, 0).replace(
        "while :; do :; done",
        "while :; do printf '%s\\n' 'not-json'; done",
    );
    let f = Fixture::new(&flood);
    let id = f.prepare();
    let runtime = new_runtime(&f.config);
    runtime.start(&id).unwrap();
    f.wait(&id, |run| run["usage_json"].is_string());
    assert!(runtime.cancel(&f.connection, &id).unwrap());
    runtime.shutdown().unwrap();
    assert_eq!(f.row(&id)["status"], "cancelled");
}
#[test]
fn structured_stdout_never_substitutes_for_the_frozen_response_artifact() {
    let result = json!({"type":"result","structured_output":no_finding()});
    let source = script(None, false, 0).replace(
        "exit 0\n",
        &format!("cat <<'NATIVE_STREAM_RESULT'\n{result}\nNATIVE_STREAM_RESULT\nexit 0\n"),
    );
    let f = Fixture::new(&source);
    let id = f.prepare();
    let runtime = new_runtime(&f.config);
    runtime.start(&id).unwrap();
    let run = f.wait(&id, |run| run["status"] == "failed");
    assert!(!Path::new(run["response_path"].as_str().unwrap()).exists());
    assert!(insight_usage_cost(&f.connection, &id).unwrap().is_some());
    runtime.shutdown().unwrap();
}
