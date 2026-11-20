//! Explicit approved executor plus owned CLI process. There is no live default adapter.
use super::{
    common::*,
    refresh,
    sync::{self, ExternalReadExecutor},
};
use crate::backend::{
    db, json as codec,
    maintenance::{self, ProcessSpec, TaskRuntime},
    storage, BackendError, Result,
};
use serde_json::{json, Value};
use std::{
    ffi::OsString,
    fs,
    path::{Path, PathBuf},
    sync::Arc,
};
pub fn external_runner_command_args(
    runner: &str,
    executable: &Path,
    root: &Path,
) -> Result<Vec<OsString>> {
    let mut args = vec![executable.as_os_str().to_owned()];
    match runner {
        "claude" => {
            for arg in [
                "--print",
                "--output-format",
                "stream-json",
                "--verbose",
                "--permission-mode",
                "plan",
                "--tools",
                "",
                "--strict-mcp-config",
                "--mcp-config",
            ] {
                args.push(arg.into());
            }
            args.push(root.join("empty-mcp.json").into_os_string());
            args.push("--json-schema".into());
            args.push(serde_json::to_string(&sync::model_result_schema())?.into());
        }
        "codex" => {
            for arg in ["exec","--json","--ignore-user-config","--ignore-rules","-c","default_permissions=\"external-sync\"","-c","permissions.external-sync.filesystem={\":minimal\"=\"read\",\":workspace_roots\"={\".\"=\"read\"}}","-c","permissions.external-sync.network.enabled=false","-c","web_search=\"disabled\"","-c","shell_environment_policy.inherit=\"none\"","--skip-git-repo-check","-C"]{args.push(arg.into());}
            args.push(root.as_os_str().to_owned());
            args.push("--output-schema".into());
            args.push(root.join("model-result-schema.json").into_os_string());
            args.push("--output-last-message".into());
            args.push(root.join("model-result.json").into_os_string());
            args.push("-".into());
        }
        _ => return Err(fail("invalid-runner", "Unsupported external sync runner")),
    }
    Ok(args)
}
pub fn render_external_sync_result(result: &Value) -> String {
    let mut lines = vec![
        "# External synchronization result".into(),
        String::new(),
        if truth(&result["summary"]) {
            python_string(&result["summary"])
        } else {
            "No runner summary was provided.".into()
        },
        String::new(),
        "## Targets".into(),
    ];
    if let Some(targets) = result["targets"].as_array() {
        for target in targets {
            lines.push(format!(
                "- `{}`: `{}`",
                python_string(&target["target_id"]),
                python_string(&target["outcome"])
            ));
        }
    }
    format!("{}\n", trim(&lines.join("\n")))
}
fn run_path(run: &Value, key: &str) -> Result<PathBuf> {
    run[key]
        .as_str()
        .map(PathBuf::from)
        .ok_or_else(|| fail("invalid-run", format!("Run {key} is missing")))
}
fn model_document(raw: &str) -> Result<(Option<Value>, Option<codec::Scope>)> {
    let scope = codec::Scope::for_document(raw);
    let value = match scope.parse(raw) {
        Ok(value) => value,
        Err(error) if error.is_io() => {
            return Err(BackendError::new(500, "json_scalar", error.to_string()))
        }
        Err(_) => return Ok((None, None)),
    };
    if !value.is_object() {
        return Ok((None, None));
    }
    Ok((Some(value), Some(scope)))
}
fn model_result(
    run: &Value,
    output: &maintenance::ProcessOutput,
) -> Result<(Option<Value>, Option<codec::Scope>)> {
    if run["runner"] == "claude" {
        return Ok((output.structured_result()?, None));
    }
    let root = run_path(run, "manifest_path")?
        .parent()
        .ok_or_else(|| fail("invalid-run", "Run manifest needs a parent"))?
        .to_owned();
    let path = root.join("model-result.json");
    if !path.is_file() {
        return Ok((None, None));
    }
    storage::files::owned_file(&path)?;
    let raw = match fs::read_to_string(path) {
        Ok(raw) => raw,
        Err(error) if error.kind() == std::io::ErrorKind::InvalidData => return Err(error.into()),
        Err(_) => return Ok((None, None)),
    };
    model_document(&raw)
}
fn write_artifact(runtime: &TaskRuntime, path: &Path, content: &str) -> Result<()> {
    storage::files::private_directory(
        path.parent()
            .ok_or_else(|| fail("invalid-run", "Run artifact needs a parent"))?,
        runtime.config(),
    )?;
    storage::files::atomic_write(path, content.as_bytes())
}
fn call_counts(log: &[Value], run: &Value) -> Value {
    json!({"mcp_calls_used":log.len(),"mcp_tool_calls_json":serde_json::to_string(log).expect("call log has only bounded strings"),"mcp_budget_exceeded":i64::from(log.len() as i64>run["mcp_call_budget"].as_i64().unwrap_or(0))})
}
fn execute(
    runtime: &Arc<TaskRuntime>,
    run_id: &str,
    executor: Option<Arc<dyn ExternalReadExecutor>>,
) -> Result<()> {
    let connection = db::connect(runtime.config())?;
    let Some(run) = maintenance::get_run(&connection, run_id)? else {
        return Ok(());
    };
    drop(connection);
    let Some(executor) = executor else {
        return runtime.finalize_failed(
            run_id,
            "External synchronization requires an approved read executor.",
        );
    };
    if runtime.is_cancelled(run_id) {
        return runtime.finalize(run_id, "cancelled", &json!({"pid":null}));
    }
    let (manifest, dispatches) =
        sync::load_external_sync_manifest(&db::connect(runtime.config())?, runtime.config(), &run)?;
    let manifest_path = run_path(&run, "manifest_path")?;
    let root = manifest_path
        .parent()
        .ok_or_else(|| fail("invalid-run", "Run manifest needs a parent"))?;
    let evidence_path = root.join("evidence.json");
    let runner = run["runner"].as_str().unwrap_or("claude");
    runtime.update(
        run_id,
        &json!({"status":"running","pid":null,"started_at":now(),"error":null}),
    )?;
    let mut on_call = |log: &[Value]| {
        if runtime.is_cancelled(run_id) {
            return Err(BackendError::conflict("Run was cancelled"));
        }
        runtime.update(run_id, &call_counts(log, &run))
    };
    let (targets, call_log) = sync::collect_external_sync_evidence(
        &manifest,
        &dispatches,
        executor.as_ref(),
        Some(&mut on_call),
    )?;
    if runtime.is_cancelled(run_id) {
        return runtime.finalize(run_id, "cancelled", &json!({"pid":null}));
    }
    let mut evidence =
        json!({"schema":"localbrain.external-sync-evidence.v1","run_id":run_id,"targets":[]});
    evidence["targets"] = Value::Array(targets.clone());
    write_artifact(runtime, &evidence_path, &codec::pretty(&evidence)?)?;
    let Some(executable) = maintenance::runner_executable(runtime.config(), runner) else {
        return runtime.finalize_failed(
            run_id,
            &format!(
                "{} executable was not found.",
                if runner == "codex" { "Codex" } else { "Claude" }
            ),
        );
    };
    let prompt = sync::build_external_sync_prompt(
        run_id,
        &manifest_path,
        &evidence_path,
        Some((&manifest, &evidence)),
    )?;
    write_artifact(runtime, &run_path(&run, "prompt_path")?, &prompt)?;
    let output = runtime.execute_process(
        run_id,
        ProcessSpec {
            arguments: external_runner_command_args(runner, &executable, root)?,
            cwd: root.to_owned(),
            prompt,
            stream_path: run_path(&run, "stream_path")?,
            result_path: None,
            stderr_path: run_path(&run, "stderr_path")?,
            mcp_call_budget: None,
            timeout: None,
        },
    )?;
    let current = maintenance::get_run(&db::connect(runtime.config())?, run_id)?;
    if runtime.is_cancelled(run_id)
        || current
            .as_ref()
            .is_some_and(|r| matches!(r["status"].as_str(), Some("cancelling" | "cancelled")))
    {
        return runtime.finalize(run_id, "cancelled", &json!({"pid":null}));
    }
    if output.return_code != 0 {
        return runtime.finalize_failed(run_id,&format!("{} external synchronization process failed with exit code {}. See the private stderr artifact.",if runner=="codex"{"Codex"}else{"Claude"},output.return_code));
    }
    let (model, scope) = model_result(&run, &output)?;
    let model = model.ok_or_else(|| {
        fail(
            "invalid-model-result",
            "External synchronization runner returned no structured result.",
        )
    })?;
    let result = sync::assemble_external_sync_result(&manifest, &targets, &model)?;
    if let Some(scope) = scope {
        scope.materialized(&result)?;
    }
    let rendered = render_external_sync_result(&result);
    write_artifact(runtime, &run_path(&run, "result_path")?, &rendered)?;
    let connection = db::connect(runtime.config())?;
    connection.execute_batch("BEGIN IMMEDIATE")?;
    let terminal_state = maintenance::get_run(&connection, run_id)?;
    if runtime.is_cancelled(run_id)
        || terminal_state
            .as_ref()
            .is_some_and(|r| matches!(r["status"].as_str(), Some("cancelling" | "cancelled")))
    {
        connection.execute_batch("ROLLBACK")?;
        return runtime.finalize(run_id, "cancelled", &json!({"pid":null}));
    }
    let terminal = (|| -> Result<()> {
        if refresh::is_atlassian_refresh_manifest(&manifest) {
            refresh::apply_atlassian_refresh_result(&connection, &manifest, &result, None)?;
        }
        let mut values = call_counts(&call_log, &run);
        values["status"] = result["status"].clone();
        values["pid"] = Value::Null;
        values["completed_at"] = json!(now());
        let summary = if truth(&result["summary"]) {
            python_string(&result["summary"])
        } else {
            rendered
        };
        values["summary"] = json!(summary.chars().take(2000).collect::<String>());
        values["structured_result_json"] = json!(serde_json::to_string(&result)?);
        maintenance::update_run_row(&connection, run_id, &values)
    })(); // The facts and terminal status have one commit boundary.
    match terminal {
        Ok(()) => {
            if let Err(error) = connection.execute_batch("COMMIT") {
                let _ = connection.execute_batch("ROLLBACK");
                return Err(error.into());
            }
        }
        Err(error) => {
            let _ = connection.execute_batch("ROLLBACK");
            return Err(error);
        }
    }
    runtime.synchronize(runner);
    Ok(())
}
pub fn start_run(
    runtime: &Arc<TaskRuntime>,
    run_id: &str,
    executor: Option<Arc<dyn ExternalReadExecutor>>,
) -> Result<()> {
    let id = run_id.to_owned();
    runtime.start(run_id, move |runtime| execute(&runtime, &id, executor))
}
