//! Workstream-owned explicit Claude tasks. Successful model output creates only
//! pending Suggestions; acceptance remains a separate curated mutation.
use super::{
    get_workstream,
    retrieval::{build_candidate_bundle, spaced_json, write_candidate_evidence},
    runner_sql as sql,
};
use crate::backend::{
    db,
    maintenance::{self, ProcessSpec, TaskRuntime},
    now, storage, unicode, BackendError, Config, Result,
};
use rusqlite::{params, Connection};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::{
    ffi::OsString,
    fs,
    os::unix::fs::DirBuilderExt,
    path::{Path, PathBuf},
    sync::{Arc, LazyLock},
};
static DATA: LazyLock<Value> = LazyLock::new(|| {
    serde_json::from_str(include_str!("runner_data.json")).expect("built-in task definitions")
});
const CHECKPOINTS: &[(&str, &str)] = &[
    ("current_goal", "현재 목표"),
    ("confirmed_facts", "확정 사실"),
    ("recent_decisions", "최근 결정"),
    ("open_questions", "열린 질문"),
    ("next_actions", "다음 행동"),
    ("files_to_open", "다시 열 파일"),
];
fn text<'a>(row: &'a Value, key: &str) -> Option<&'a str> {
    row[key].as_str()
}
fn nonempty<'a>(row: &'a Value, key: &str) -> Option<&'a str> {
    text(row, key).filter(|s| !s.is_empty())
}
fn cleaned(value: Option<&str>) -> String {
    value
        .unwrap_or_default()
        .trim_matches(unicode::python_space)
        .into()
}
fn id(value: &Value) -> String {
    value
        .as_str()
        .map(str::to_owned)
        .unwrap_or_else(|| value.to_string())
}
fn object(row: &Value, fields: &[&str]) -> Value {
    Value::Object(
        fields
            .iter()
            .map(|key| ((*key).into(), row[*key].clone()))
            .collect(),
    )
}
fn integer(value: &Value) -> Option<i64> {
    value
        .as_i64()
        .or_else(|| value.as_bool().map(i64::from))
        .or_else(|| {
            value
                .as_f64()
                .filter(|v| v.fract() == 0.0 && *v >= i64::MIN as f64 && *v <= i64::MAX as f64)
                .map(|v| v as i64)
        })
}
pub fn task_choices() -> Vec<Value> {
    DATA["TASK_DEFINITIONS"]
        .as_object()
        .unwrap()
        .iter()
        .map(|(key, value)| {
            let mut value = value.clone();
            value["value"] = key.clone().into();
            value
        })
        .collect()
}
pub fn runner_command_args(executable: &Path) -> Vec<OsString> {
    vec![
        executable.as_os_str().to_owned(),
        "--print".into(),
        "--output-format".into(),
        "stream-json".into(),
        "--verbose".into(),
        "--permission-mode".into(),
        "plan".into(),
        "--json-schema".into(),
        serde_json::to_string(&DATA["RESULT_SCHEMA"])
            .unwrap()
            .into(),
    ]
}
fn shell_quote(value: &str) -> String {
    if !value.is_empty()
        && value
            .bytes()
            .all(|ch| ch.is_ascii_alphanumeric() || b"_/@%+=:,.-".contains(&ch))
    {
        value.into()
    } else {
        format!("'{}'", value.replace('\'', "'\"'\"'"))
    }
}
pub fn runner_command_preview() -> String {
    runner_command_args(Path::new("claude"))
        .iter()
        .map(|value| shell_quote(&value.to_string_lossy()))
        .collect::<Vec<_>>()
        .join(" ")
}
fn resource_manifest(connection: &Connection, link: &Value) -> Result<Option<Value>> {
    let kind = text(link, "entity_type").unwrap_or_default();
    let entity = if !link["resource_id"].is_null() && link["resource_id"] != 0 {
        id(&link["resource_id"])
    } else {
        id(&link["entity_id"])
    };
    let mut base = json!({"entity_type":kind,"entity_id":entity,"relation_type":link["relation_type"],"title":link["title"]});
    let selection = match kind {
        "session" => sql::RESOURCE_MANIFEST_0,
        "document" => sql::RESOURCE_MANIFEST_1,
        "project" => sql::RESOURCE_MANIFEST_2,
        "external" => sql::RESOURCE_MANIFEST_3,
        _ => sql::RESOURCE_MANIFEST_4,
    };
    let row = db::row(connection, selection, [entity])?;
    if kind == "session" && row.is_none() {
        return Ok(None);
    }
    if let Some(row) = row {
        base.as_object_mut()
            .unwrap()
            .extend(row.as_object().unwrap().clone());
    }
    Ok(Some(base))
}
fn resource_manifests(connection: &Connection, links: &Value) -> Result<Vec<Value>> {
    let mut result = Vec::new();
    for link in links.as_array().into_iter().flatten() {
        if let Some(resource) = resource_manifest(connection, link)? {
            result.push(resource);
        }
    }
    Ok(result)
}
fn pending(suggestion: &Value) -> Value {
    let mut value = object(
        suggestion,
        &[
            "id",
            "suggestion_type",
            "target_type",
            "target_id",
            "title",
            "description",
            "rationale",
            "origin_run_id",
        ],
    );
    value["payload"] = text(suggestion, "payload_json")
        .filter(|v| !v.is_empty())
        .and_then(|v| serde_json::from_str(v).ok())
        .unwrap_or_else(|| json!({}));
    value
}
fn previous_analysis(
    connection: &Connection,
    workstream: i64,
    task: &str,
    fingerprint: &str,
) -> Result<Option<Value>> {
    for row in db::rows(
        connection,
        sql::PREVIOUS_ANALYSIS_0,
        params![workstream, task],
    )? {
        let snapshot = text(&row, "source_snapshot_json")
            .filter(|v| !v.is_empty())
            .unwrap_or("{}");
        let result = text(&row, "structured_result_json")
            .filter(|v| !v.is_empty())
            .unwrap_or("{}");
        let (Ok(snapshot), Ok(result)) = (
            serde_json::from_str::<Value>(snapshot),
            serde_json::from_str::<Value>(result),
        ) else {
            continue;
        };
        if snapshot["retrieval"]["fingerprint"] == fingerprint {
            return Ok(Some(
                json!({"local_candidate_snapshot_unchanged":true,"run_id":row["id"],"completed_at":row["completed_at"],"structured_result":result}),
            ));
        }
    }
    Ok(None)
}
pub fn build_manifest(
    connection: &Connection,
    config: &Config,
    workstream: i64,
    run_id: &str,
    task: &str,
    candidate_bundle: Option<&Value>,
    refresh: bool,
) -> Result<Value> {
    let workstream_row = get_workstream(connection, workstream)?
        .ok_or_else(|| BackendError::not_found("Workstream not found"))?;
    let candidates = if let Some(bundle) = candidate_bundle {
        bundle.clone()
    } else {
        build_candidate_bundle(connection, &workstream_row)?
    };
    let mut workstream = object(
        &workstream_row,
        &["id", "name", "status", "summary", "checkpoint"],
    );
    workstream["resources"] = resource_manifests(connection, &workstream_row["links"])?.into();
    let threads = workstream_row["threads"]
        .as_array()
        .unwrap()
        .iter()
        .map(|thread| {
            let mut value = object(
                thread,
                &[
                    "id",
                    "title",
                    "status",
                    "summary",
                    "current_goal",
                    "next_action",
                ],
            );
            value["resources"] = resource_manifests(connection, &thread["links"])?.into();
            Ok(value)
        })
        .collect::<Result<Vec<_>>>()?;
    Ok(
        json!({"schema":"localbrain.maintenance-context.v2","run_id":run_id,"generated_at":now(),"execution_root":config.home_dir.to_string_lossy(),"workstream":workstream,"threads":threads,"retrieval":{"policy":candidates["policy"],"fingerprint":candidates["fingerprint"],"counts":candidates["counts"],"evidence_root":candidates["evidence_root"]},"candidate_resources":candidates["candidate_resources"],"thread_resource_matches":candidates["thread_resource_matches"],"pending_suggestions":workstream_row["suggestions"].as_array().unwrap().iter().map(pending).collect::<Vec<_>>(),"suggestion_refresh":{"enabled":refresh,"behavior":if refresh{"Replace pending Claude Run suggestions after this run succeeds. Rejected and accepted suggestions keep their status."}else{"Merge this run's output with pending suggestions."}},"previous_analysis":previous_analysis(connection,workstream_row["id"].as_i64().unwrap(),task,text(&candidates,"fingerprint").unwrap_or_default())?,"external_discovery":{"mode":"mcp-gap-fill-only","requested_sources":["jira","slack","wiki","git"],"mcp_call_budget":config.mcp_call_budget,"budget_scope":"this maintenance run","enforcement":"prompt-and-stream-audit","cache_rule":"Do not re-query connected resources, pending suggestions, or unchanged previous analysis unless freshness is material to the task."}}),
    )
}
pub fn build_prompt(
    config: &Config,
    run_id: &str,
    task: &str,
    manifest: &Path,
    extra: Option<&str>,
    refresh: bool,
) -> Result<String> {
    let definition = DATA["TASK_DEFINITIONS"]
        .get(task)
        .ok_or_else(|| BackendError::invalid("task", "Unsupported task type"))?;
    let extra = cleaned(extra);
    let extra = if extra.is_empty() {
        String::new()
    } else {
        format!("\n\n추가 요청:\n{extra}")
    };
    let refresh_instruction = if refresh {
        "- 이 실행은 제안 갱신 모드다. 기존 pending_suggestions를 참고하되 현재 근거로 다시 판단해 유지할 항목도 결과에 포함하라. 성공 후 결과에 없는 기존 Claude 제안은 교체된다."
    } else {
        "- 이 실행의 결과는 현재 pending_suggestions와 병합된다. 중복 후보를 만들지 마라."
    };
    let replacements = [
        ("run_id", run_id.to_owned()),
        ("manifest_path", manifest.to_string_lossy().into_owned()),
        (
            "task_instruction",
            text(definition, "instruction").unwrap().into(),
        ),
        ("extra_block", extra),
        ("mcp_call_budget", config.mcp_call_budget.to_string()),
        ("refresh_instruction", refresh_instruction.into()),
    ];
    // Replace only template tokens in the built-in text; braces supplied by a
    // user instruction are ordinary input and never interpreted a second time.
    let template = include_str!("prompt.txt");
    let mut result = String::new();
    let mut cursor = 0;
    while let Some(start) = template[cursor..].find('{') {
        let start = cursor + start;
        result.push_str(&template[cursor..start]);
        let Some(end) = template[start..].find('}') else {
            break;
        };
        let end = start + end;
        let name = &template[start + 1..end];
        if let Some((_, value)) = replacements.iter().find(|(key, _)| *key == name) {
            result.push_str(value);
        } else {
            result.push_str(&template[start..=end]);
        }
        cursor = end + 1;
    }
    result.push_str(&template[cursor..]);
    Ok(result)
}
pub fn prepare_run(
    connection: &Connection,
    config: &Config,
    workstream: i64,
    task: &str,
    extra: Option<&str>,
    run_root: Option<&Path>,
    refresh: bool,
) -> Result<String> {
    if DATA["TASK_DEFINITIONS"].get(task).is_none() {
        return Err(BackendError::invalid("task", "Unsupported task type"));
    }
    let workstream_row = get_workstream(connection, workstream)?
        .ok_or_else(|| BackendError::not_found("Workstream not found"))?;
    let run_id = format!("lb-{}", &uuid::Uuid::new_v4().simple().to_string()[..12]);
    let parent = run_root
        .map(Path::to_owned)
        .unwrap_or_else(|| config.data_dir.join("runs"));
    storage::files::private_directory(&parent, config)?;
    let root = parent.join(&run_id);
    fs::DirBuilder::new().mode(0o700).create(&root)?;
    let result = (|| {
        let candidates = write_candidate_evidence(
            &build_candidate_bundle(connection, &workstream_row)?,
            &root,
            config,
        )?;
        let manifest = build_manifest(
            connection,
            config,
            workstream,
            &run_id,
            task,
            Some(&candidates),
            refresh,
        )?;
        let manifest_path = root.join("manifest.json");
        let prompt_path = root.join("prompt.md");
        let stream_path = root.join("stream.jsonl");
        let result_path = root.join("result.md");
        let stderr_path = root.join("stderr.log");
        storage::files::atomic_write(
            &manifest_path,
            serde_json::to_string_pretty(&manifest)?.as_bytes(),
        )?;
        storage::files::atomic_write(
            &prompt_path,
            build_prompt(config, &run_id, task, &manifest_path, extra, refresh)?.as_bytes(),
        )?;
        connection.execute(
            sql::PREPARE_RUN_0,
            params![
                run_id,
                workstream,
                task,
                config.home_dir.to_string_lossy(),
                serde_json::to_string(&manifest)?,
                manifest_path.to_string_lossy(),
                prompt_path.to_string_lossy(),
                stream_path.to_string_lossy(),
                result_path.to_string_lossy(),
                stderr_path.to_string_lossy(),
                i32::from(refresh),
                config.mcp_call_budget.as_i64().ok_or_else(
                    || crate::backend::BackendError::new(
                        500,
                        "database",
                        "MCP call budget is outside SQLite's integer range"
                    )
                )?,
                now()
            ],
        )?;
        Ok(())
    })();
    if let Err(error) = result {
        let _ = fs::remove_dir_all(&root);
        return Err(error);
    }
    Ok(run_id)
}
pub fn list_runs(connection: &Connection, workstream: i64, limit: i64) -> Result<Vec<Value>> {
    db::rows(connection, sql::LIST_RUNS_0, params![workstream, limit])
}
pub fn render_structured_result(result: &Value) -> String {
    let mut lines = vec![
        "# 실행 결과".to_owned(),
        String::new(),
        nonempty(result, "summary")
            .unwrap_or("요약이 없습니다.")
            .to_owned(),
        String::new(),
        "## 자원 연결 제안".into(),
    ];
    let suggestions = result["resource_suggestions"]
        .as_array()
        .filter(|v| !v.is_empty());
    if let Some(suggestions) = suggestions {
        for item in suggestions {
            let target = if item["target_thread_id"].is_null() {
                "Workstream 공통".into()
            } else {
                format!("Thread #{}", id(&item["target_thread_id"]))
            };
            lines.extend([
                String::new(),
                format!(
                    "- **{}** · {} · {target}",
                    nonempty(item, "title")
                        .or_else(|| text(item, "locator"))
                        .unwrap_or("None"),
                    text(item, "resource_type").unwrap_or("None")
                ),
                format!("  - 위치: `{}`", nonempty(item, "locator").unwrap_or("-")),
                format!(
                    "  - 근거: {}",
                    nonempty(item, "evidence")
                        .or_else(|| nonempty(item, "rationale"))
                        .unwrap_or("-")
                ),
            ]);
        }
    } else {
        lines.extend([String::new(), "발견된 자원 연결 제안이 없습니다.".into()]);
    }
    lines.extend([String::new(), "## Checkpoint 초안".into()]);
    let mut populated = false;
    for (key, label) in CHECKPOINTS {
        let value = cleaned(text(&result["checkpoint_draft"], key));
        if !value.is_empty() {
            populated = true;
            lines.extend([String::new(), format!("### {label}"), value]);
        }
    }
    if !populated {
        lines.extend([String::new(), "Checkpoint 변경 제안이 없습니다.".into()]);
    }
    lines.extend([
        String::new(),
        "## 우선순위 검토".into(),
        String::new(),
        nonempty(result, "priority_review")
            .unwrap_or("검토 내용이 없습니다.")
            .into(),
    ]);
    format!("{}\n", lines.join("\n").trim_matches(unicode::python_space))
}
pub fn persist_structured_suggestions(
    connection: &Connection,
    config: &Config,
    run_id: &str,
    workstream: i64,
    result: &Value,
) -> Result<usize> {
    let valid = db::rows(
        connection,
        sql::PERSIST_STRUCTURED_SUGGESTIONS_0,
        [workstream],
    )?
    .into_iter()
    .filter_map(|row| integer(&row["id"]))
    .collect::<std::collections::BTreeSet<_>>();
    let mut created = 0;
    for item in result["resource_suggestions"]
        .as_array()
        .into_iter()
        .flatten()
    {
        let locator = cleaned(text(item, "locator"));
        let kind = cleaned(text(item, "resource_type"));
        if locator.is_empty()
            || ![
                "local_path",
                "session",
                "document",
                "project",
                "jira",
                "wiki",
                "slack",
                "git",
                "url",
            ]
            .contains(&kind.as_str())
        {
            continue;
        }
        let (target, owner) = if item["target_thread_id"].is_null() {
            ("workstream", workstream)
        } else if let Some(thread) =
            integer(&item["target_thread_id"]).filter(|thread| valid.contains(thread))
        {
            ("thread", thread)
        } else {
            continue;
        };
        let locator = if kind == "local_path" {
            storage::files::expand(Path::new(&locator), config)
                .to_string_lossy()
                .into_owned()
        } else {
            locator
        };
        let fingerprint = format!(
            "{:x}",
            Sha256::digest(
                format!(
                    "runner-resource:{target}:{owner}:{kind}:{}",
                    unicode::lowercase(&locator)
                )
                .as_bytes()
            )
        );
        let payload = json!({"resource_type":kind,"locator":locator,"title":cleaned(Some(nonempty(item,"title").unwrap_or(&locator))),"relation_type":cleaned(Some(nonempty(item,"relation_type").unwrap_or("related-to"))),"rationale":cleaned(text(item,"rationale")),"evidence":cleaned(text(item,"evidence"))});
        let confidence = item["confidence"]
            .as_f64()
            .or_else(|| text(item, "confidence").and_then(|v| v.parse::<f64>().ok()))
            .unwrap_or(0.0);
        let confidence = if confidence.is_nan() {
            1.0
        } else {
            confidence.clamp(0.0, 1.0)
        };
        let mut rationale = text(&payload, "rationale").unwrap().to_owned();
        let evidence = text(&payload, "evidence").unwrap();
        if !evidence.is_empty() && evidence != rationale {
            rationale = format!(
                "{} · 근거: {evidence}",
                if rationale.is_empty() {
                    "연결 근거"
                } else {
                    &rationale
                }
            );
        }
        connection.execute(
            sql::PERSIST_STRUCTURED_SUGGESTIONS_1,
            params![
                target,
                owner,
                payload["title"].as_str(),
                locator,
                rationale,
                serde_json::to_string(&payload)?,
                fingerprint,
                run_id,
                confidence
            ],
        )?;
        let current = db::row(
            connection,
            sql::PERSIST_STRUCTURED_SUGGESTIONS_2,
            [&fingerprint],
        )?;
        created += usize::from(
            current.is_some_and(|row| row["status"] == "pending" && row["origin_run_id"] == run_id),
        );
    }
    let checkpoint = Value::Object(
        CHECKPOINTS
            .iter()
            .map(|(key, _)| {
                (
                    (*key).into(),
                    cleaned(text(&result["checkpoint_draft"], key)).into(),
                )
            })
            .collect::<Map<_, _>>(),
    );
    if checkpoint
        .as_object()
        .unwrap()
        .values()
        .any(|value| value != "")
    {
        let fingerprint = format!(
            "{:x}",
            Sha256::digest(
                format!(
                    "runner-checkpoint:{workstream}:{}",
                    spaced_json(&checkpoint)
                )
                .as_bytes()
            )
        );
        connection.execute(
            sql::PERSIST_STRUCTURED_SUGGESTIONS_3,
            params![
                workstream,
                "Checkpoint 초안",
                checkpoint["current_goal"].as_str(),
                "Claude Task Runner가 연결 자원과 최근 상태를 바탕으로 작성했습니다.",
                serde_json::to_string(&checkpoint)?,
                fingerprint,
                run_id,
                0.7
            ],
        )?;
        let current = db::row(
            connection,
            sql::PERSIST_STRUCTURED_SUGGESTIONS_4,
            [&fingerprint],
        )?;
        created += usize::from(
            current.is_some_and(|row| row["status"] == "pending" && row["origin_run_id"] == run_id),
        );
    }
    Ok(created)
}
pub fn supersede_runner_suggestions(connection: &Connection, workstream: i64) -> Result<usize> {
    Ok(connection.execute(
        sql::SUPERSEDE_RUNNER_SUGGESTIONS_0,
        params![now(), workstream, workstream],
    )?)
}
pub fn start_run(runtime: &Arc<TaskRuntime>, run_id: &str) -> Result<()> {
    let run_id = run_id.to_owned();
    runtime.start(&run_id.clone(), move |runtime| {
        execute_run(&runtime, &run_id)
    })
}
fn execute_run(runtime: &Arc<TaskRuntime>, run_id: &str) -> Result<()> {
    let config = runtime.config();
    let Some(run) = maintenance::get_run(&db::connect(config)?, run_id)? else {
        return Ok(());
    };
    let Some(executable) = maintenance::runner_executable(config, "claude") else {
        runtime.finalize_failed(run_id, "Claude executable was not found.")?;
        return Ok(());
    };
    let path = |key: &str| -> Result<PathBuf> {
        text(&run, key)
            .map(PathBuf::from)
            .ok_or_else(|| BackendError::invalid("run", format!("Run has no {key}")))
    };
    let output = runtime.execute_process(
        run_id,
        ProcessSpec {
            arguments: runner_command_args(&executable),
            cwd: path("cwd")?,
            prompt: fs::read_to_string(path("prompt_path")?)?,
            stream_path: path("stream_path")?,
            result_path: Some(path("result_path")?),
            stderr_path: path("stderr_path")?,
            mcp_call_budget: Some(run["mcp_call_budget"].as_i64().unwrap_or(0)),
            timeout: None,
        },
    )?;
    let current = maintenance::get_run(&db::connect(config)?, run_id)?;
    if current.as_ref().is_some_and(|row| {
        ["cancelling", "cancelled"].contains(&text(row, "status").unwrap_or_default())
    }) {
        runtime.finalize(run_id, "cancelled", &json!({"pid":null}))?;
        return Ok(());
    }
    if output.return_code != 0 {
        let error = output.stderr.trim_matches(unicode::python_space);
        let error = if error.is_empty() {
            format!("Claude exited with code {}", output.return_code)
        } else {
            error.to_owned()
        };
        runtime.finalize_failed(run_id, &error)?;
        return Ok(());
    }
    let structured = output.structured_result()?;
    let text = if let Some(structured) = &structured {
        let text = render_structured_result(structured);
        storage::files::atomic_write(&path("result_path")?, text.as_bytes())?;
        text
    } else {
        output.output
    };
    let connection = db::connect(config)?;
    connection.execute_batch("BEGIN IMMEDIATE")?;
    let current = maintenance::get_run(&connection, run_id)?;
    if runtime.is_cancelled(run_id)
        || current.as_ref().is_some_and(|row| {
            ["cancelling", "cancelled"].contains(&row["status"].as_str().unwrap_or_default())
        })
    {
        maintenance::update_run_row(
            &connection,
            run_id,
            &json!({"status":"cancelled","pid":null,"completed_at":now()}),
        )?;
        connection.execute_batch("COMMIT")?;
        runtime.synchronize("claude");
        return Ok(());
    }
    let apply = (|| {
        let mut count = 0;
        if let Some(structured) = &structured {
            if run["refresh_suggestions"] == 1 {
                supersede_runner_suggestions(&connection, integer(&run["workstream_id"]).unwrap())?;
            }
            count = persist_structured_suggestions(
                &connection,
                config,
                run_id,
                integer(&run["workstream_id"]).unwrap(),
                structured,
            )?;
        }
        maintenance::update_run_row(
            &connection,
            run_id,
            &json!({"status":"completed","pid":null,"completed_at":now(),"summary":if text.is_empty(){None}else{Some(text.chars().take(2000).collect::<String>())},"structured_result_json":structured.as_ref().map(serde_json::to_string).transpose()?,"suggestions_created":count,"mcp_calls_used":output.mcp_calls.len(),"mcp_tool_calls_json":serde_json::to_string(&output.mcp_calls)?,"mcp_budget_exceeded":i32::from((output.mcp_calls.len() as i128)>i128::from(run["mcp_call_budget"].as_i64().unwrap_or(0)))}),
        )?;
        Ok(())
    })();
    if let Err(error) = apply {
        connection.execute_batch("ROLLBACK")?;
        return Err(error);
    }
    connection.execute_batch("COMMIT")?;
    runtime.synchronize("claude");
    Ok(())
}
