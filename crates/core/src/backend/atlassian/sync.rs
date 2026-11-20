//! Source-neutral envelopes. Remote facts belong exclusively to the executor;
//! the model may return only the bounded maintenance summary.
use super::{
    access::{self, ToolDispatch},
    common::*,
};
use crate::backend::{db, BackendError, Config, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};

pub const EXTERNAL_SYNC_TASK: &str = "external_source_sync";
pub const MANIFEST_SCHEMA: &str = "localbrain.external-sync-manifest.v1";
pub const RESULT_SCHEMA_VERSION: &str = "localbrain.external-sync-result.v1";
pub const MODEL_RESULT_SCHEMA_VERSION: &str = "localbrain.external-sync-model-result.v1";
pub const MAX_TARGETS: usize = 500;
pub const MAX_CALL_BUDGET: i64 = 200;
const RUNNERS: &[&str] = &["claude", "codex"];
const SCOPE_KINDS: &[&str] = &["item", "space", "thread", "workstream", "all_known"];
const IDENTIFIER: &str = r"\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\z";
const SUCCESS: &[&str] = &["resolved", "unchanged", "changed"];
const OUTCOMES: &[&str] = &[
    "resolved",
    "unchanged",
    "changed",
    "unavailable",
    "not_found",
    "error",
];

/// A typed contract failure retains the Python ExternalSyncError boundary;
/// unrelated executor failures receive a fixed privacy-safe public message.
#[derive(Debug)]
pub enum ExternalExecutionError {
    Contract(BackendError),
    Failed,
}
pub trait ExternalReadExecutor: Send + Sync {
    fn execute(
        &self,
        dispatch: &ToolDispatch,
    ) -> std::result::Result<Value, ExternalExecutionError>;
}
pub fn model_result_schema() -> Value {
    json!({"type":"object","additionalProperties":false,"properties":{"schema":{"type":"string","enum":[MODEL_RESULT_SCHEMA_VERSION]},"run_id":{"type":"string"},"summary":{"type":"string","maxLength":2000}},"required":["schema","run_id","summary"]})
}
fn manifest_text(
    value: &Value,
    label: &str,
    maximum: usize,
    pattern: Option<&str>,
) -> Result<String> {
    checked_text(value, label, maximum, pattern, "invalid-manifest")
}
fn checked_text(
    value: &Value,
    label: &str,
    maximum: usize,
    pattern: Option<&str>,
    code: &str,
) -> Result<String> {
    let value = text(value, label, maximum, code)?;
    if pattern.is_some_and(|pattern| !matches(pattern, &value)) {
        return Err(fail(code, format!("{label} has an invalid shape")));
    }
    Ok(value)
}
fn manifest_keys(value: &Value, required: &[&str], optional: &[&str], label: &str) -> Result<()> {
    exact_keys(value, required, optional, label, "invalid-manifest")
}
fn validate_locator(value: &Value) -> Result<Value> {
    manifest_keys(value, &["kind", "value"], &[], "target.locator")?;
    let kind = manifest_text(&value["kind"], "target.locator.kind", 32, None)?;
    if !["url", "remote_id", "source_root", "local_ref"].contains(&kind.as_str()) {
        return Err(fail("invalid-manifest", "unsupported target locator kind"));
    }
    let locator = manifest_text(&value["value"], "target.locator.value", 4000, None)?;
    if kind == "url" && !crate::backend::references::is_http_locator(&locator)? {
        return Err(fail(
            "invalid-manifest",
            "URL locators must use HTTP or HTTPS",
        ));
    }
    Ok(json!({"kind":kind,"value":locator}))
}
fn validate_known(value: &Value) -> Result<Value> {
    if value.is_null() {
        return Ok(json!({"remote_version":null,"remote_updated_at":null,"content_hash":null}));
    }
    manifest_keys(
        value,
        &[],
        &["remote_version", "remote_updated_at", "content_hash"],
        "target.known",
    )?;
    let hash = if value["content_hash"].is_null() {
        None
    } else {
        Some(manifest_text(
            &value["content_hash"],
            "target.known.content_hash",
            64,
            Some(access::HASH),
        )?)
    };
    Ok(
        json!({"remote_version":optional_text(&value["remote_version"],"target.known.remote_version",300,"invalid-manifest")?,"remote_updated_at":optional_text(&value["remote_updated_at"],"target.known.remote_updated_at",100,"invalid-manifest")?,"content_hash":hash}),
    )
}
fn validate_coverage(value: &Value) -> Result<Vec<Value>> {
    let values = value
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= 3)
        .ok_or_else(|| {
            fail(
                "invalid-manifest",
                "target.coverage must be a non-empty bounded list",
            )
        })?;
    let mut result = vec![];
    for value in values {
        if !value
            .as_str()
            .is_some_and(|s| ["metadata", "content", "hierarchy"].contains(&s))
        {
            return Err(fail("invalid-manifest", "unsupported target coverage"));
        }
        if !result.contains(value) {
            result.push(value.clone());
        }
    }
    Ok(result)
}
fn validate_fields(value: &Value) -> Result<Vec<String>> {
    if value.is_null() {
        return Ok(vec![]);
    }
    let values = value
        .as_array()
        .filter(|a| a.len() <= 100)
        .ok_or_else(|| fail("invalid-manifest", "field_allowlist must be a bounded list"))?;
    let mut result = vec![];
    for value in values {
        let value = manifest_text(value, "field_allowlist item", 120, None)?;
        if !result.contains(&value) {
            result.push(value);
        }
    }
    Ok(result)
}
pub fn build_external_sync_manifest(
    connection: &Connection,
    config: &Config,
    values: &Value,
) -> Result<(Value, BTreeMap<String, ToolDispatch>)> {
    let runner = values["runner"]
        .as_str()
        .filter(|s| RUNNERS.contains(s))
        .ok_or_else(|| fail("unsupported-runner", "runner must be claude or codex"))?;
    let source_kind = manifest_text(
        &values["source_kind"],
        "source_kind",
        64,
        Some(r"\A[a-z][a-z0-9_]{0,63}\z"),
    )?;
    let scope = values["scope_kind"]
        .as_str()
        .filter(|s| SCOPE_KINDS.contains(s))
        .ok_or_else(|| fail("invalid-manifest", "unsupported external sync scope"))?;
    let source = if values["source_instance_id"].is_null() {
        None
    } else {
        if !is_integer(&values["source_instance_id"]) {
            return Err(fail(
                "invalid-manifest",
                "source_instance_id must be an integer or null",
            ));
        }
        Some(id(&values["source_instance_id"])?)
    };
    let budget = if values["call_budget"].is_null() {
        config.mcp_call_budget.as_i64().unwrap_or(i64::MAX)
    } else {
        values["call_budget"]
            .as_i64()
            .filter(|_| is_integer(&values["call_budget"]))
            .unwrap_or(0)
    };
    if !(1..=MAX_CALL_BUDGET).contains(&budget) {
        return Err(fail(
            "invalid-manifest",
            format!("call_budget must be between 1 and {MAX_CALL_BUDGET}"),
        ));
    }
    let raw_targets = values["targets"]
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= MAX_TARGETS)
        .ok_or_else(|| {
            fail(
                "invalid-manifest",
                format!("targets must contain between 1 and {MAX_TARGETS}"),
            )
        })?;
    let mut targets = vec![];
    let mut dispatches = BTreeMap::new();
    let mut target_ids = BTreeSet::new();
    let mut states = BTreeMap::new();
    let mut selected_sources = BTreeSet::new();
    let mut selected_services = BTreeSet::new();
    let mut requests_count = 0;
    for target in raw_targets {
        manifest_keys(
            target,
            &["target_id", "locator", "coverage", "requests"],
            &["known", "field_allowlist", "source_instance_id"],
            "target",
        )?;
        let target_source = target
            .get("source_instance_id")
            .unwrap_or(&values["source_instance_id"]);
        if !is_integer(target_source) {
            return Err(fail(
                "invalid-manifest",
                "each target requires a Source Instance",
            ));
        }
        let target_source = id(target_source)?;
        if source.is_some_and(|source| source != target_source) {
            return Err(fail(
                "source-instance-mismatch",
                "single-source targets cannot change Source Instance",
            ));
        }
        if let std::collections::btree_map::Entry::Vacant(entry) = states.entry(target_source) {
            let state = access::capability_state(connection, target_source)?;
            if state["state"] != "current" {
                return Err(fail(
                    "capability-not-current",
                    format!(
                        "Source Instance capability state is {}",
                        state["state"].as_str().unwrap_or("error")
                    ),
                ));
            }
            if [json!("mcp_gateway"), json!("atlassian_cloud")].contains(&state["provider_kind"])
                && source_kind != "atlassian"
            {
                return Err(fail(
                    "source-kind-mismatch",
                    "the selected Source Instance requires source_kind atlassian",
                ));
            }
            entry.insert(state);
        }
        selected_sources.insert(target_source);
        selected_services.insert(
            states[&target_source]["service"]
                .as_str()
                .unwrap()
                .to_owned(),
        );
        let target_id = manifest_text(
            &target["target_id"],
            "target.target_id",
            128,
            Some(IDENTIFIER),
        )?;
        if !target_ids.insert(target_id.clone()) {
            return Err(fail("invalid-manifest", "target_id must be unique"));
        }
        let coverage = validate_coverage(&target["coverage"])?;
        let fields = validate_fields(&target["field_allowlist"])?;
        if coverage.contains(&json!("metadata")) && fields.is_empty() {
            return Err(fail(
                "invalid-manifest",
                "metadata coverage requires an explicit field_allowlist",
            ));
        }
        let raw_requests = target["requests"]
            .as_array()
            .filter(|a| !a.is_empty())
            .ok_or_else(|| {
                fail(
                    "invalid-manifest",
                    "target.requests must be a non-empty list",
                )
            })?;
        let mut requests = vec![];
        for request in raw_requests {
            manifest_keys(
                request,
                &["request_id", "logical_operation", "arguments"],
                &[],
                "target.request",
            )?;
            let request_id = manifest_text(
                &request["request_id"],
                "target.request.request_id",
                128,
                Some(IDENTIFIER),
            )?;
            if dispatches.contains_key(&request_id) {
                return Err(fail(
                    "invalid-manifest",
                    "request_id must be globally unique",
                ));
            }
            let operation = manifest_text(
                &request["logical_operation"],
                "target.request.logical_operation",
                160,
                None,
            )?;
            if operation.starts_with("capability.") {
                return Err(fail(
                    "operation-not-allowed",
                    "capability inspection is not an external sync request",
                ));
            }
            let arguments = &request["arguments"];
            if !arguments.is_object() {
                return Err(fail(
                    "invalid-manifest",
                    "target.request.arguments must be an object",
                ));
            }
            json_size(
                arguments,
                "target.request.arguments",
                32768,
                "invalid-manifest",
            )?;
            if operation == "jira.search_metadata" {
                let selected = arguments["fields"]
                    .as_array()
                    .filter(|a| !a.is_empty())
                    .ok_or_else(|| {
                        fail(
                            "invalid-manifest",
                            "Jira metadata requests require explicit selected fields",
                        )
                    })?;
                if selected.iter().any(|field| {
                    !field
                        .as_str()
                        .is_some_and(|field| fields.iter().any(|v| v == field))
                }) {
                    return Err(fail(
                        "invalid-manifest",
                        "Jira metadata request fields exceed the target allowlist",
                    ));
                }
            }
            dispatches.insert(
                request_id.clone(),
                access::authorize_external_read(connection, target_source, &operation, arguments)?,
            );
            requests.push(json!({"request_id":request_id,"logical_operation":operation,"arguments":arguments}));
            requests_count += 1;
        }
        let mut normalized = json!({"target_id":target_id,"locator":validate_locator(&target["locator"])?,"coverage":coverage,"field_allowlist":fields,"known":validate_known(&target["known"])?,"requests":requests});
        if source.is_none() {
            normalized["source_instance_id"] = target_source.into();
        }
        targets.push(normalized);
    }
    if requests_count > budget {
        return Err(fail(
            "call-budget-exceeded",
            "selected requests exceed the external sync call budget",
        ));
    }
    let run_id = manifest_text(&values["run_id"], "run_id", 128, Some(IDENTIFIER))?;
    Ok((
        json!({"schema":MANIFEST_SCHEMA,"run_id":run_id,"generated_at":now(),"runner":runner,"source":{"kind":source_kind,"instance_id":source,"service":if selected_services.len()==1{selected_services.into_iter().next().unwrap()}else{"mixed".into()}},"scope":{"kind":scope},"read_policy_version":access::READ_POLICY_VERSION,"call_budget":budget,"targets":targets}),
        dispatches,
    ))
}
pub fn external_sync_projection(manifest: &Value) -> Value {
    json!({"maintenance_run_id":manifest["run_id"],"source_instance_id":manifest["source"]["instance_id"],"source_kind":manifest["source"]["kind"],"service":manifest["source"]["service"],"requested_scope_kind":manifest["scope"]["kind"],"selected_target_count":manifest["targets"].as_array().map_or(0,Vec::len),"manifest_schema_version":manifest["schema"],"read_policy_version":manifest["read_policy_version"]})
}
pub fn build_external_sync_prompt(
    run: &str,
    manifest_path: &Path,
    evidence_path: &Path,
    inline: Option<(&Value, &Value)>,
) -> Result<String> {
    let inline = inline
        .map(|(manifest, evidence)| {
            let mut input = json!({"manifest":null,"evidence":null});
            input["manifest"] = manifest.clone();
            input["evidence"] = evidence.clone();
            canonical(&input).map(|s| format!("\n\nValidated input:\n{s}"))
        })
        .transpose()?
        .unwrap_or_default();
    Ok(format!("[LOCALBRAIN_RUN: {run}]\n[MODE: maintenance]\n\nYou are LocalBrain's external synchronization maintenance runner. This is not\nan ordinary work session.\n\nRules:\n- Read only the selected manifest and host-validated evidence files below.\n- Do not call MCP, Gateway, network, shell, Git, ticket, email, or chat tools.\n- Do not invent or rewrite remote identity, metadata, content, timestamps,\n  versions, hashes, outcomes, or provider errors.\n- Return only a short summary of the already validated target outcomes.\n\nManifest: {}\nEvidence: {}\n\nReturn the exact JSON schema supplied by LocalBrain. Use schema\n`{MODEL_RESULT_SCHEMA_VERSION}` and run_id `{run}`.\n{inline}\n",manifest_path.display(),evidence_path.display()))
}
pub fn prepare_external_sync_run(
    connection: &Connection,
    config: &Config,
    values: &Value,
    run_root: Option<&Path>,
) -> Result<String> {
    let run = format!("lb-{}", &uuid::Uuid::new_v4().simple().to_string()[..12]);
    let mut request = values.clone();
    request["run_id"] = json!(run);
    let (manifest, _) = build_external_sync_manifest(connection, config, &request)?;
    let projection = external_sync_projection(&manifest);
    let parent = run_root
        .map(PathBuf::from)
        .unwrap_or_else(|| config.data_dir.join("runs"));
    fs::create_dir_all(&parent)?;
    let root = parent.join(&run);
    fs::create_dir(&root)?;
    struct RootGuard {
        path: PathBuf,
        keep: bool,
    }
    impl Drop for RootGuard {
        fn drop(&mut self) {
            if !self.keep {
                let _ = fs::remove_dir_all(&self.path);
            }
        }
    }
    let mut guard = RootGuard {
        path: root.clone(),
        keep: false,
    };
    let manifest_path = root.join("manifest.json");
    let prompt_path = root.join("prompt.md");
    let stream_path = root.join("stream.jsonl");
    let result_path = root.join("result.md");
    let stderr_path = root.join("stderr.log");
    fs::write(&manifest_path, serde_json::to_string_pretty(&manifest)?)?;
    fs::write(
        &prompt_path,
        build_external_sync_prompt(&run, &manifest_path, &root.join("evidence.json"), None)?,
    )?;
    fs::write(
        root.join("model-result-schema.json"),
        canonical(&model_result_schema())?,
    )?;
    fs::write(root.join("empty-mcp.json"), "{\"mcpServers\":{}}\n")?;
    let workstream = if values["workstream_id"].is_null() {
        None
    } else {
        Some(id(&values["workstream_id"])?)
    };
    atomic(connection, "external_sync_prepare", || {
        connection.execute("INSERT INTO maintenance_runs(id,workstream_id,task_type,runner,cwd,status,source_snapshot_json,manifest_path,prompt_path,stream_path,result_path,stderr_path,refresh_suggestions,mcp_call_budget,updated_at) VALUES (?,?,?,?,?,'queued',?,?,?,?,?,?,0,?,?)",params![run,workstream,EXTERNAL_SYNC_TASK,manifest["runner"].as_str(),root.to_str(),serde_json::to_string(&manifest)?,manifest_path.to_str(),prompt_path.to_str(),stream_path.to_str(),result_path.to_str(),stderr_path.to_str(),manifest["call_budget"].as_i64(),now()])?;
        connection.execute("INSERT INTO external_sync_runs(maintenance_run_id,source_instance_id,source_kind,service,requested_scope_kind,selected_target_count,manifest_schema_version,read_policy_version) VALUES (?,?,?,?,?,?,?,?)",params![run,projection["source_instance_id"].as_i64(),projection["source_kind"].as_str(),projection["service"].as_str(),projection["requested_scope_kind"].as_str(),projection["selected_target_count"].as_i64(),MANIFEST_SCHEMA,access::READ_POLICY_VERSION])?;
        Ok(())
    })?;
    guard.keep = true;
    Ok(run)
}
pub fn load_external_sync_manifest(
    connection: &Connection,
    config: &Config,
    run: &Value,
) -> Result<(Value, BTreeMap<String, ToolDispatch>)> {
    if run["task_type"] != EXTERNAL_SYNC_TASK {
        return Err(fail(
            "not-external-sync",
            "Run is not an external synchronization",
        ));
    }
    let stored: Value = serde_json::from_str(
        run["source_snapshot_json"]
            .as_str()
            .filter(|s| !s.is_empty())
            .unwrap_or("{}"),
    )
    .map_err(|_| {
        fail(
            "invalid-manifest",
            "stored external sync manifest is invalid",
        )
    })?;
    let artifact = run["manifest_path"]
        .as_str()
        .and_then(|path| fs::read_to_string(path).ok())
        .and_then(|s| serde_json::from_str::<Value>(&s).ok())
        .ok_or_else(|| {
            fail(
                "invalid-manifest",
                "external sync manifest artifact is invalid",
            )
        })?;
    if artifact != stored {
        return Err(fail(
            "external-sync-manifest-mismatch",
            "stored external sync manifest does not match its artifact",
        ));
    }
    let values = json!({"run_id":stored["run_id"],"runner":stored["runner"],"source_instance_id":stored["source"]["instance_id"],"source_kind":stored["source"]["kind"],"scope_kind":stored["scope"]["kind"],"targets":stored["targets"],"call_budget":stored["call_budget"]});
    let (mut manifest, dispatches) = build_external_sync_manifest(connection, config, &values)?;
    manifest["generated_at"] = json!(manifest_text(
        &stored["generated_at"],
        "generated_at",
        100,
        None
    )?);
    if manifest != stored {
        return Err(fail(
            "external-sync-manifest-mismatch",
            "stored external sync manifest is not canonical for the current contract",
        ));
    }
    let projection = external_sync_projection(&manifest);
    let envelope = db::row(
        connection,
        "SELECT * FROM external_sync_runs WHERE maintenance_run_id = ?",
        [run["id"].as_str().unwrap_or("")],
    )?
    .ok_or_else(|| {
        fail(
            "external-sync-envelope-missing",
            "external synchronization has no query envelope",
        )
    })?;
    for (key, value) in projection.as_object().unwrap() {
        if envelope[key] != *value {
            return Err(fail(
                "external-sync-envelope-mismatch",
                "external synchronization query envelope does not match manifest",
            ));
        }
    }
    Ok((manifest, dispatches))
}

fn fact_object(value: &Value, label: &str) -> Result<Value> {
    if value.is_null() {
        return Ok(json!({}));
    }
    if !value.is_object() {
        return Err(fail(
            "invalid-provider-result",
            format!("{label} must be an object"),
        ));
    }
    json_size(value, label, 2_000_000, "invalid-provider-result")?;
    Ok(value.clone())
}
pub fn validate_provider_result(
    value: &Value,
    request: &Value,
    coverage: &Value,
    field_allowlist: &Value,
) -> Result<Value> {
    const CODE: &str = "invalid-provider-result";
    exact_keys(
        value,
        &["outcome"],
        &[
            "identity",
            "metadata",
            "content",
            "remote_version",
            "remote_updated_at",
            "error",
        ],
        "provider result",
        CODE,
    )?;
    let outcome = value["outcome"]
        .as_str()
        .filter(|s| OUTCOMES.contains(s))
        .ok_or_else(|| fail(CODE, "unsupported provider outcome"))?;
    let identity = fact_object(&value["identity"], "identity")?;
    let metadata = fact_object(&value["metadata"], "metadata")?;
    let covered = |name: &str| {
        coverage
            .as_array()
            .is_some_and(|v| v.contains(&json!(name)))
    };
    if metadata.as_object().is_some_and(|v| !v.is_empty()) && !covered("metadata") {
        return Err(fail(
            CODE,
            "provider metadata was returned for a target without metadata coverage",
        ));
    }
    if metadata.as_object().unwrap().keys().any(|key| {
        !field_allowlist
            .as_array()
            .is_some_and(|v| v.contains(&json!(key)))
    }) {
        return Err(fail(
            CODE,
            "provider metadata contains a field outside the manifest allowlist",
        ));
    }
    let content = &value["content"];
    if !content.is_null() && !covered("content") {
        return Err(fail(
            CODE,
            "provider content was returned for a target without content coverage",
        ));
    }
    if !content.is_null()
        && !request["logical_operation"]
            .as_str()
            .is_some_and(|s| ["jira.read_description", "confluence.read_page"].contains(&s))
    {
        return Err(fail(
            CODE,
            "provider content was returned by a non-content operation",
        ));
    }
    let content_json = json_size(content, "content", 2_000_000, CODE)?;
    let error = if value["error"].is_null() {
        Value::Null
    } else {
        exact_keys(
            &value["error"],
            &["code"],
            &["message"],
            "provider result error",
            CODE,
        )?;
        let code = checked_text(
            &value["error"]["code"],
            "provider result error code",
            80,
            Some(access::ERROR_CODE),
            CODE,
        )?;
        json!({"code":code,"message":match outcome{"unavailable"=>"External source is unavailable.","not_found"=>"Selected external resource was not found.",_=>"Approved external read failed."}})
    };
    if SUCCESS.contains(&outcome) && !error.is_null() {
        return Err(fail(
            CODE,
            "successful provider outcomes cannot include an error",
        ));
    }
    if !SUCCESS.contains(&outcome) && error.is_null() {
        return Err(fail(
            CODE,
            "unsuccessful provider outcomes require a bounded error",
        ));
    }
    // These provider facts are already Values. Serializing them into another
    // Value would reinterpret literal private-number keys and reject NaN.
    let mut result = json!({"request_id":null,"logical_operation":null,"outcome":outcome,"identity":null,"metadata":null,"content":null,"remote_version":optional_text(&value["remote_version"],"remote_version",300,CODE)?,"remote_updated_at":optional_text(&value["remote_updated_at"],"remote_updated_at",100,CODE)?,"content_hash":(!content.is_null()).then(||format!("{:x}",Sha256::digest(content_json.as_bytes()))),"error":error});
    result["request_id"] = request["request_id"].clone();
    result["logical_operation"] = request["logical_operation"].clone();
    result["identity"] = identity;
    result["metadata"] = metadata;
    result["content"] = content.clone();
    Ok(result)
}
pub fn aggregate_target_outcome(requests: &[Value]) -> &'static str {
    let all = |value: &str| requests.iter().all(|r| r["outcome"] == value);
    let any = |value: &str| requests.iter().any(|r| r["outcome"] == value);
    if any("error") {
        "error"
    } else if any("unavailable") {
        if all("unavailable") {
            "unavailable"
        } else {
            "error"
        }
    } else if any("not_found") {
        if all("not_found") {
            "not_found"
        } else {
            "error"
        }
    } else if any("changed") {
        "changed"
    } else if any("resolved") {
        "resolved"
    } else if !requests.is_empty() && all("unchanged") {
        "unchanged"
    } else {
        "error"
    }
}
pub fn derive_run_status(targets: &[Value]) -> &'static str {
    let successes = targets
        .iter()
        .filter(|t| t["outcome"].as_str().is_some_and(|s| SUCCESS.contains(&s)))
        .count();
    if successes == targets.len() && !targets.is_empty() {
        "completed"
    } else if successes > 0 {
        "partial"
    } else {
        "failed"
    }
}
pub type CallObserver<'a> = dyn FnMut(&[Value]) -> Result<()> + 'a;

pub fn collect_external_sync_evidence(
    manifest: &Value,
    dispatches: &BTreeMap<String, ToolDispatch>,
    executor: &dyn ExternalReadExecutor,
    mut on_call: Option<&mut CallObserver<'_>>,
) -> Result<(Vec<Value>, Vec<Value>)> {
    let mut targets = vec![];
    let mut log = vec![];
    for target in manifest["targets"]
        .as_array()
        .ok_or_else(|| fail("invalid-manifest", "targets must be a list"))?
    {
        let mut requests = vec![];
        for request in target["requests"]
            .as_array()
            .ok_or_else(|| fail("invalid-manifest", "target.requests must be a list"))?
        {
            let key = request["request_id"]
                .as_str()
                .ok_or_else(|| fail("invalid-manifest", "request_id must be a string"))?;
            let dispatch = dispatches.get(key).ok_or_else(|| {
                fail("invalid-manifest", "request has no pre-authorized dispatch")
            })?;
            log.push(json!({"request_id":key,"target_id":target["target_id"],"logical_operation":dispatch.logical_operation,"tool_name":dispatch.tool_name,"outcome":"running"}));
            if let Some(callback) = on_call.as_mut() {
                callback(&log)?;
            }
            let index = log.len() - 1;
            let executed = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                executor.execute(dispatch)
            }))
            .unwrap_or(Err(ExternalExecutionError::Failed));
            let raw = match executed {
                Ok(value) => value,
                Err(error) => {
                    log[index]["outcome"] =
                        json!(if matches!(error, ExternalExecutionError::Contract(_)) {
                            "invalid"
                        } else {
                            "error"
                        });
                    if let Some(callback) = on_call.as_mut() {
                        callback(&log)?;
                    }
                    return Err(match error {
                        ExternalExecutionError::Contract(error) => error,
                        ExternalExecutionError::Failed => fail(
                            "provider-execution-failed",
                            "Approved external read executor failed.",
                        ),
                    });
                }
            };
            let validated = match validate_provider_result(
                &raw,
                request,
                &target["coverage"],
                &target["field_allowlist"],
            ) {
                Ok(value) => value,
                Err(error) => {
                    log[index]["outcome"] = json!("invalid");
                    if let Some(callback) = on_call.as_mut() {
                        callback(&log)?;
                    }
                    return Err(error);
                }
            };
            log[index]["outcome"] = validated["outcome"].clone();
            if let Some(callback) = on_call.as_mut() {
                callback(&log)?;
            }
            requests.push(validated);
        }
        let mut result = json!({"target_id":target["target_id"],"locator":target["locator"],"outcome":aggregate_target_outcome(&requests),"requests":[]});
        result["requests"] = Value::Array(requests);
        targets.push(result);
    }
    Ok((targets, log))
}
pub fn validate_model_result(value: &Value, run: &str) -> Result<Value> {
    const CODE: &str = "invalid-model-result";
    exact_keys(
        value,
        &["schema", "run_id", "summary"],
        &[],
        "model result",
        CODE,
    )?;
    if value["schema"] != MODEL_RESULT_SCHEMA_VERSION {
        return Err(fail(CODE, "model result schema is unsupported"));
    }
    if value["run_id"] != run {
        return Err(fail(CODE, "model result Run ID does not match"));
    }
    let summary = value["summary"]
        .as_str()
        .filter(|s| s.chars().count() <= 2000)
        .ok_or_else(|| fail(CODE, "model summary is invalid"))?;
    Ok(json!({"schema":MODEL_RESULT_SCHEMA_VERSION,"run_id":run,"summary":trim(summary)}))
}
pub fn assemble_external_sync_result(
    manifest: &Value,
    targets: &[Value],
    model: &Value,
) -> Result<Value> {
    let model = validate_model_result(model, manifest["run_id"].as_str().unwrap_or(""))?;
    let mut result = json!({"schema":RESULT_SCHEMA_VERSION,"run_id":manifest["run_id"],"source":manifest["source"],"scope":manifest["scope"],"read_policy_version":manifest["read_policy_version"],"status":derive_run_status(targets),"targets":[],"summary":model["summary"]});
    result["targets"] = Value::Array(targets.to_vec());
    Ok(result)
}
