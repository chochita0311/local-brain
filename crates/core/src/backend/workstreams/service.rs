use super::sql;
use crate::backend::{db, now, resources, unicode, BackendError, Config, Result};
use rusqlite::{params, params_from_iter, Connection};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, sync::LazyLock};
pub const ENTITY_TYPES: &[&str] = &["session", "document", "project", "external", "local"];
pub const WORKSTREAM_STATUSES: &[&str] = &["active", "paused", "done", "archived"];
pub const THREAD_STATUSES: &[&str] = &["active", "blocked", "paused", "done"];
fn text<'a>(value: &'a Value, field: &str) -> Option<&'a str> {
    value[field].as_str()
}
fn truth<'a>(value: &'a Value, field: &str) -> Option<&'a str> {
    text(value, field).filter(|v| !v.is_empty())
}
fn clean(value: Option<&str>) -> Option<&str> {
    value
        .map(|value| value.trim_matches(unicode::python_space))
        .filter(|v| !v.is_empty())
}
fn id(value: &Value) -> String {
    value
        .as_str()
        .map(str::to_owned)
        .unwrap_or_else(|| value.to_string())
}
fn need(row: Option<Value>, message: &str) -> Result<Value> {
    row.ok_or_else(|| BackendError::not_found(message))
}
fn integer(value: &Value, field: &str) -> Result<i64> {
    value[field]
        .as_i64()
        .ok_or_else(|| BackendError::invalid("workstream", format!("Invalid {field}")))
}
fn label(kind: &str) -> Option<&'static str> {
    match kind {
        "document" => Some("Local Context"),
        "project" => Some("Project"),
        "local_path" => Some("Local Path"),
        "jira" => Some("Jira"),
        "wiki" => Some("Wiki"),
        "slack" => Some("Slack"),
        "git" => Some("Git"),
        "url" => Some("URL"),
        _ => None,
    }
}
fn local_label(kind: &str) -> &'static str {
    match kind {
        "repository" => "Local Repository",
        "directory" => "Local Directory",
        "file" => "Local File",
        _ => "Local Path",
    }
}
fn session_label(kind: &str) -> &'static str {
    match unicode::lowercase(kind).as_str() {
        "claude" => "Claude Session",
        "codex" => "Codex Session",
        _ => "Session",
    }
}
fn title(value: &str) -> String {
    value
        .replace('_', " ")
        .split_inclusive(char::is_whitespace)
        .map(|word| {
            let mut chars = word.chars();
            let first = chars
                .next()
                .map(|ch| ch.to_uppercase().collect::<String>())
                .unwrap_or_default();
            format!("{first}{}", unicode::lowercase(chars.as_str()))
        })
        .collect()
}
fn parsed_payload(row: &Value) -> Value {
    text(row, "payload_json")
        .filter(|v| !v.is_empty())
        .and_then(|v| serde_json::from_str(v).ok())
        .unwrap_or_else(|| json!({}))
}
pub(super) fn latest_activity(connection: &Connection, workstream: i64) -> Result<Option<String>> {
    Ok(db::row(
        connection,
        sql::LATEST_ACTIVITY_0,
        params_from_iter([workstream; 10]),
    )?
    .and_then(|row| row["activity_at"].as_str().map(str::to_owned)))
}
fn latest_checkpoint(connection: &Connection, workstream: i64) -> Result<Option<Value>> {
    let Some(mut checkpoint) = db::row(connection, sql::LATEST_CHECKPOINT_0, [workstream])? else {
        return Ok(None);
    };
    let references = db::rows(
        connection,
        sql::LATEST_CHECKPOINT_1,
        [integer(&checkpoint, "id")?],
    )?;
    let references = resolve_links(connection, &references)?;
    checkpoint["resource_count"] = references.len().into();
    checkpoint["resources"] = references.into();
    Ok(Some(checkpoint))
}
fn workstream_summary(connection: &Connection, mut row: Value) -> Result<Value> {
    let workstream = integer(&row, "id")?;
    row["threads"] = db::rows(connection, sql::WORKSTREAM_SUMMARY_0, [workstream])?.into();
    row["checkpoint"] = latest_checkpoint(connection, workstream)?.unwrap_or(Value::Null);
    let linked = latest_activity(connection, workstream)?;
    row["latest_activity_at"] = linked
        .as_ref()
        .map(|v| Value::String(v.clone()))
        .unwrap_or_else(|| row["last_activity_at"].clone());
    let checkpoint = &row["checkpoint"];
    let checkpoint_time = truth(checkpoint, "confirmed_at")
        .or_else(|| truth(checkpoint, "updated_at"))
        .or_else(|| truth(checkpoint, "created_at"));
    row["needs_review"] = (checkpoint.is_null()
        || linked
            .as_deref()
            .zip(checkpoint_time)
            .is_some_and(|(activity, checkpoint)| activity > checkpoint))
    .into();
    Ok(row)
}
pub fn list_workstreams(connection: &Connection, include_archived: bool) -> Result<Vec<Value>> {
    let selection = sql::LIST_WORKSTREAMS_0.replace(
        "{where}",
        if include_archived {
            ""
        } else {
            "WHERE status != 'archived'"
        },
    );
    db::rows(connection, &selection, [])?
        .into_iter()
        .map(|row| workstream_summary(connection, row))
        .collect()
}
pub fn get_workstream(connection: &Connection, workstream: i64) -> Result<Option<Value>> {
    let Some(row) = db::row(connection, sql::GET_WORKSTREAM_0, [workstream])? else {
        return Ok(None);
    };
    let mut item = workstream_summary(connection, row)?;
    item["links"] = resolve_links(
        connection,
        &db::rows(connection, sql::GET_WORKSTREAM_1, [workstream])?,
    )?
    .into();
    for thread in item["threads"].as_array_mut().unwrap() {
        thread["links"] = resolve_links(
            connection,
            &db::rows(connection, sql::GET_WORKSTREAM_2, [integer(thread, "id")?])?,
        )?
        .into();
    }
    item["suggestions"] = workstream_suggestions(connection, workstream, "pending")?.into();
    item["excluded_suggestions"] =
        workstream_suggestions(connection, workstream, "rejected")?.into();
    Ok(Some(item))
}
fn suggestion_label(connection: &Connection, kind: &str, payload: &Value) -> Result<String> {
    if kind == "checkpoint_draft" {
        return Ok("Checkpoint".into());
    }
    let entity = text(payload, "entity_type");
    let resource = text(payload, "resource_type");
    if entity == Some("session") || resource == Some("session") {
        let lookup = if entity == Some("session") {
            id(&payload["entity_id"])
        } else {
            id(&payload["locator"])
        };
        let row = db::row(connection, sql::SUGGESTION_RESOURCE_LABEL_0, [lookup])?;
        return Ok(session_label(
            row.as_ref()
                .and_then(|row| text(row, "provider_kind"))
                .unwrap_or_default(),
        )
        .into());
    }
    if entity == Some("external") {
        let row = db::row(
            connection,
            sql::SUGGESTION_RESOURCE_LABEL_1,
            [id(&payload["entity_id"])],
        )?;
        return Ok(row
            .as_ref()
            .and_then(|row| text(row, "resource_type"))
            .and_then(label)
            .unwrap_or("External")
            .into());
    }
    if entity == Some("local") {
        let row = db::row(
            connection,
            sql::SUGGESTION_RESOURCE_LABEL_2,
            [id(&payload["entity_id"])],
        )?;
        return Ok(local_label(
            row.as_ref()
                .and_then(|row| text(row, "resource_type"))
                .unwrap_or_default(),
        )
        .into());
    }
    let kind = entity
        .filter(|v| !v.is_empty())
        .or(resource)
        .filter(|v| !v.is_empty())
        .unwrap_or("Resource");
    Ok(label(kind)
        .map(str::to_owned)
        .unwrap_or_else(|| title(kind)))
}
fn workstream_suggestions(
    connection: &Connection,
    workstream: i64,
    status: &str,
) -> Result<Vec<Value>> {
    db::rows(
        connection,
        sql::WORKSTREAM_SUGGESTIONS_0,
        params![status, workstream, workstream],
    )?
    .into_iter()
    .map(|mut row| {
        let payload = parsed_payload(&row);
        row["resource_label"] = suggestion_label(
            connection,
            text(&row, "suggestion_type").unwrap_or_default(),
            &payload,
        )?
        .into();
        row["origin_label"] = if truth(&row, "origin_run_id").is_some() {
            "Claude Run"
        } else {
            "Quick match"
        }
        .into();
        row["payload"] = payload;
        Ok(row)
    })
    .collect()
}
pub fn create_workstream(
    connection: &Connection,
    name: &str,
    summary: Option<&str>,
) -> Result<i64> {
    connection.execute(
        sql::CREATE_WORKSTREAM_0,
        params![
            name.trim_matches(unicode::python_space),
            clean(summary),
            now()
        ],
    )?;
    Ok(connection.last_insert_rowid())
}
pub fn update_workstream(
    connection: &Connection,
    workstream: i64,
    name: &str,
    status: &str,
    summary: Option<&str>,
) -> Result<()> {
    if !WORKSTREAM_STATUSES.contains(&status) {
        return Err(BackendError::invalid(
            "workstream",
            "Unsupported workstream status",
        ));
    }
    if connection.execute(
        sql::UPDATE_WORKSTREAM_0,
        params![
            name.trim_matches(unicode::python_space),
            status,
            clean(summary),
            now(),
            workstream
        ],
    )? == 0
    {
        return Err(BackendError::not_found("Workstream not found"));
    }
    Ok(())
}
pub fn create_thread(connection: &Connection, workstream: i64, payload: &Value) -> Result<i64> {
    let position = db::row(connection, sql::CREATE_THREAD_0, [workstream])?.unwrap()["position"]
        .as_i64()
        .unwrap();
    connection.execute(
        sql::CREATE_THREAD_1,
        params![
            workstream,
            text(payload, "title")
                .unwrap_or_default()
                .trim_matches(unicode::python_space),
            clean(text(payload, "summary")),
            clean(text(payload, "current_goal")),
            clean(text(payload, "next_action")),
            position,
            now()
        ],
    )?;
    let id = connection.last_insert_rowid();
    touch_workstream(connection, workstream)?;
    Ok(id)
}
pub fn update_thread(connection: &Connection, thread: i64, payload: &Value) -> Result<()> {
    let status = text(payload, "status").unwrap_or("active");
    if !THREAD_STATUSES.contains(&status) {
        return Err(BackendError::invalid("thread", "Unsupported thread status"));
    }
    let row = need(
        db::row(connection, sql::UPDATE_THREAD_0, [thread])?,
        "Thread not found",
    )?;
    connection.execute(
        sql::UPDATE_THREAD_1,
        params![
            text(payload, "title")
                .unwrap_or_default()
                .trim_matches(unicode::python_space),
            status,
            clean(text(payload, "summary")),
            clean(text(payload, "current_goal")),
            clean(text(payload, "next_action")),
            now(),
            thread
        ],
    )?;
    touch_workstream(connection, integer(&row, "workstream_id")?)
}
pub fn create_checkpoint(connection: &Connection, workstream: i64, payload: &Value) -> Result<i64> {
    let version = db::row(connection, sql::CREATE_CHECKPOINT_0, [workstream])?.unwrap()["version"]
        .as_i64()
        .unwrap();
    let timestamp = now();
    connection.execute(
        sql::CREATE_CHECKPOINT_1,
        params![
            workstream,
            clean(text(payload, "current_goal")),
            clean(text(payload, "confirmed_facts")),
            clean(text(payload, "recent_decisions")),
            clean(text(payload, "open_questions")),
            clean(text(payload, "next_actions")),
            clean(text(payload, "files_to_open")),
            timestamp,
            latest_activity(connection, workstream)?,
            version,
            timestamp
        ],
    )?;
    let checkpoint = connection.last_insert_rowid();
    connection.execute(
        sql::SNAPSHOT_CHECKPOINT_RESOURCES_0,
        params![checkpoint, workstream],
    )?;
    connection.execute(
        sql::SNAPSHOT_CHECKPOINT_RESOURCES_1,
        params![checkpoint, workstream],
    )?;
    touch_workstream(connection, workstream)?;
    Ok(checkpoint)
}
fn link_scope(
    connection: &Connection,
    scope: &str,
    owner: i64,
) -> Result<(&'static str, &'static str, i64)> {
    match scope {
        "workstream" => Ok(("workstream_links", "workstream_id", owner)),
        "thread" => {
            let row = need(
                db::row(connection, sql::ADD_LINK_0, [owner])?,
                "Thread not found",
            )?;
            Ok(("thread_links", "thread_id", integer(&row, "workstream_id")?))
        }
        _ => Err(BackendError::invalid("link", "Unsupported link scope")),
    }
}
fn validate_entity(connection: &Connection, kind: &str, entity: &str) -> Result<()> {
    let table = match kind {
        "session" => "sessions",
        "document" => "context_documents",
        "project" => "workspaces",
        "external" => "external_resources",
        "local" => "local_resources",
        _ => return Err(BackendError::invalid("link", "Unsupported entity type")),
    };
    let selection = sql::VALIDATE_ENTITY_0.replacen("{}", table, 1).replacen(
        "{}",
        if kind == "session" {
            " AND session_class = 'work' AND session_role = 'primary'"
        } else {
            ""
        },
        1,
    );
    if db::row(connection, &selection, [entity])?.is_none() {
        return Err(BackendError::not_found("Linked resource not found"));
    }
    Ok(())
}
#[allow(clippy::too_many_arguments)]
pub fn add_link(
    connection: &Connection,
    config: &Config,
    scope: &str,
    owner: i64,
    kind: &str,
    entity: &str,
    relation: &str,
    linked_by: &str,
    confidence: Option<f64>,
) -> Result<i64> {
    validate_entity(connection, kind, entity)?;
    let (table, column, workstream) = link_scope(connection, scope, owner)?;
    let resource = resources::bind_entity(connection, kind, entity, config)?;
    connection.execute(
        &sql::ADD_LINK_1
            .replace("{table}", table)
            .replace("{owner_column}", column),
        params![
            owner,
            kind,
            entity,
            resource,
            relation.trim_matches(unicode::python_space),
            confidence,
            linked_by
        ],
    )?;
    touch_workstream(connection, workstream)?;
    Ok(db::row(
        connection,
        &sql::ADD_LINK_2
            .replace("{table}", table)
            .replace("{owner_column}", column),
        params![owner, kind, entity],
    )?
    .unwrap()["id"]
        .as_i64()
        .unwrap())
}
pub fn remove_link(connection: &Connection, scope: &str, owner: i64, link: i64) -> Result<()> {
    match scope {
        "workstream" => {
            connection.execute(sql::REMOVE_LINK_0, params![link, owner])?;
            touch_workstream(connection, owner)?;
        }
        "thread" => {
            let row = db::row(connection, sql::REMOVE_LINK_1, [owner])?;
            connection.execute(sql::REMOVE_LINK_2, params![link, owner])?;
            if let Some(row) = row {
                touch_workstream(connection, integer(&row, "workstream_id")?)?;
            }
        }
        _ => return Err(BackendError::invalid("link", "Unsupported link scope")),
    }
    Ok(())
}
pub fn picker_resources(connection: &Connection) -> Result<Value> {
    Ok(
        json!({"sessions":db::rows(connection,sql::PICKER_RESOURCES_0,[])?,"documents":db::rows(connection,sql::PICKER_RESOURCES_1,[])?,"projects":db::rows(connection,sql::PICKER_RESOURCES_2,[])?,"external":db::rows(connection,sql::PICKER_RESOURCES_3,[])?,"local":db::rows(connection,sql::PICKER_RESOURCES_4,[])?}),
    )
}
pub fn resolve_links(connection: &Connection, links: &[Value]) -> Result<Vec<Value>> {
    let mut resolved = Vec::new();
    for link in links {
        let mut item = link.clone();
        item["link_id"] = item["id"].clone();
        let kind = text(link, "entity_type").unwrap_or_default();
        let entity = id(&link["entity_id"]);
        item["resource_id"] = link["entity_id"].clone();
        let (selection, href) = match kind {
            "session" => (sql::RESOLVE_LINKS_0, format!("/sessions/{entity}")),
            "document" => (sql::RESOLVE_LINKS_1, format!("/documents/{entity}")),
            "project" => (
                sql::RESOLVE_LINKS_2,
                format!("/sessions?workspace={entity}"),
            ),
            "external" => (sql::RESOLVE_LINKS_3, String::new()),
            _ => (sql::RESOLVE_LINKS_4, format!("/local-resources/{entity}")),
        };
        let Some(row) = db::row(connection, selection, [entity])? else {
            continue;
        };
        item["href"] = if kind == "external" {
            row["detail"].clone()
        } else {
            href.into()
        };
        if kind == "external" {
            item["external"] = true.into();
        }
        item.as_object_mut()
            .unwrap()
            .extend(row.as_object().unwrap().clone());
        item["resource_label"] = match kind {
            "session" => session_label(text(&item, "source_kind").unwrap_or_default()),
            "document" => "Local Context",
            "project" => "Project",
            "external" => {
                label(text(&item, "resource_type").unwrap_or_default()).unwrap_or("External")
            }
            _ => local_label(text(&item, "resource_type").unwrap_or_default()),
        }
        .into();
        resolved.push(item);
    }
    Ok(resolved)
}
pub fn entity_memberships(connection: &Connection, kind: &str, entity: i64) -> Result<Vec<Value>> {
    db::rows(
        connection,
        sql::ENTITY_MEMBERSHIPS_0,
        params![kind, entity.to_string(), kind, entity.to_string()],
    )
}
pub fn dashboard_overview(connection: &Connection) -> Result<Value> {
    let workstreams = list_workstreams(connection, false)?
        .into_iter()
        .filter(|item| ["active", "paused"].contains(&text(item, "status").unwrap_or_default()))
        .collect::<Vec<_>>();
    let sessions = db::rows(connection, sql::DASHBOARD_OVERVIEW_0, [])?;
    Ok(
        json!({"metrics":{"active_workstreams":workstreams.iter().filter(|item|item["status"]=="active").count(),"active_threads":workstreams.iter().flat_map(|item|item["threads"].as_array().into_iter().flatten()).filter(|thread|["active","blocked"].contains(&text(thread,"status").unwrap_or_default())).count(),"needs_review":workstreams.iter().filter(|item|item["needs_review"]==true).count(),"unlinked_sessions":sessions.len(),"unlinked_documents":db::row(connection,sql::DASHBOARD_OVERVIEW_1,[])?.unwrap()["count"],"pending_suggestions":db::row(connection,sql::DASHBOARD_OVERVIEW_2,[])?.unwrap()["count"]},"workstreams":workstreams,"unlinked_sessions":sessions[..sessions.len().min(8)]}),
    )
}
pub(super) fn touch_workstream(connection: &Connection, workstream: i64) -> Result<()> {
    let timestamp = now();
    connection.execute(
        sql::TOUCH_WORKSTREAM_0,
        params![timestamp, timestamp, workstream],
    )?;
    Ok(())
}
fn tokens(value: &str) -> BTreeSet<String> {
    static PATTERN: LazyLock<regex::Regex> =
        LazyLock::new(|| regex::Regex::new(r"[A-Za-z0-9가-힣_.-]{2,}").unwrap());
    const STOP: &[&str] = &[
        "about",
        "and",
        "context",
        "for",
        "from",
        "local",
        "project",
        "the",
        "this",
        "with",
        "개발",
        "관련",
        "대한",
        "작업",
        "정보",
        "프로젝트",
        "확인",
    ];
    PATTERN
        .find_iter(value)
        .map(|item| unicode::lowercase(item.as_str()))
        .filter(|item| !STOP.contains(&item.as_str()))
        .collect()
}
fn target_has_link(
    connection: &Connection,
    target: &str,
    owner: i64,
    kind: &str,
    entity: &str,
) -> Result<bool> {
    let (table, column) = if target == "thread" {
        ("thread_links", "thread_id")
    } else {
        ("workstream_links", "workstream_id")
    };
    let selection = sql::TARGET_HAS_LINK_0
        .replacen("{}", table, 1)
        .replacen("{}", column, 1);
    Ok(db::row(connection, &selection, params![owner, kind, entity])?.is_some())
}
pub fn generate_suggestions(connection: &Connection, workstream: i64) -> Result<usize> {
    let workstream_row = need(
        get_workstream(connection, workstream)?,
        "Workstream not found",
    )?;
    let mut targets = Vec::new();
    let workstream_name = text(&workstream_row, "name").unwrap_or_default();
    let summary = truth(&workstream_row, "summary");
    for thread in workstream_row["threads"].as_array().unwrap() {
        if !["active", "blocked"].contains(&text(thread, "status").unwrap_or_default()) {
            continue;
        }
        let query = [
            Some(workstream_name),
            summary,
            truth(thread, "title"),
            truth(thread, "summary"),
            truth(thread, "current_goal"),
        ]
        .into_iter()
        .flatten()
        .collect::<Vec<_>>()
        .join(" ");
        targets.push(("thread", integer(thread, "id")?, query));
    }
    if targets.is_empty() {
        targets.push((
            "workstream",
            workstream,
            [Some(workstream_name), summary]
                .into_iter()
                .flatten()
                .collect::<Vec<_>>()
                .join(" "),
        ));
    }
    let mut candidates = db::rows(connection, sql::GENERATE_SUGGESTIONS_0, [])?;
    candidates.extend(db::rows(connection, sql::GENERATE_SUGGESTIONS_1, [])?);
    let mut created = 0;
    for (target, owner, query) in targets {
        let target_tokens = tokens(&query);
        let mut scored = Vec::new();
        for candidate in &candidates {
            let kind = text(candidate, "entity_type").unwrap_or_default();
            let entity = id(&candidate["id"]);
            if target_has_link(connection, target, owner, kind, &entity)? {
                continue;
            }
            let candidate_tokens = tokens(&format!(
                "{} {}",
                text(candidate, "title").unwrap_or_default(),
                truth(candidate, "detail").unwrap_or_default()
            ));
            let overlap = target_tokens
                .intersection(&candidate_tokens)
                .cloned()
                .collect::<Vec<_>>();
            if overlap.is_empty() {
                continue;
            }
            let score = (0.48 + overlap.len() as f64 * 0.12).min(0.94);
            scored.push((score, overlap, candidate));
        }
        scored.sort_by(|a, b| b.0.total_cmp(&a.0));
        for (score, overlap, candidate) in scored.into_iter().take(3) {
            let kind = text(candidate, "entity_type").unwrap_or_default();
            let entity = id(&candidate["id"]);
            let fingerprint = format!(
                "{:x}",
                Sha256::digest(format!("{target}:{owner}:{kind}:{entity}").as_bytes())
            );
            created += connection.execute(
                sql::GENERATE_SUGGESTIONS_2,
                params![
                    target,
                    owner,
                    candidate["title"].as_str(),
                    candidate["detail"].as_str(),
                    format!("공통 키워드: {}", overlap.join(", ")),
                    serde_json::to_string(
                        &json!({"entity_type":kind,"entity_id":entity,"relation_type":"related-to"})
                    )?,
                    fingerprint,
                    score
                ],
            )?;
        }
    }
    Ok(created)
}
fn materialize(
    connection: &Connection,
    config: &Config,
    payload: &Value,
) -> Result<(String, String)> {
    if let Some(kind) = truth(payload, "entity_type") {
        if !payload["entity_id"].is_null()
            && payload["entity_id"] != ""
            && payload["entity_id"] != 0
        {
            return Ok((kind.into(), id(&payload["entity_id"])));
        }
    }
    let kind = truth(payload, "resource_type").ok_or_else(|| {
        BackendError::invalid(
            "suggestion",
            "Suggestion does not contain a usable resource",
        )
    })?;
    let locator = truth(payload, "locator").ok_or_else(|| {
        BackendError::invalid(
            "suggestion",
            "Suggestion does not contain a usable resource",
        )
    })?;
    let summary = truth(payload, "summary")
        .or_else(|| truth(payload, "evidence"))
        .or_else(|| truth(payload, "rationale"));
    if kind == "local_path" {
        let id = resources::store::create_local_resource(
            connection,
            config,
            locator,
            text(payload, "title"),
            summary,
            "task_runner",
        )?;
        return Ok(("local".into(), id.to_string()));
    }
    if ["session", "document", "project"].contains(&kind) {
        return Ok((kind.into(), locator.into()));
    }
    let kind = if ["jira", "wiki", "slack", "git", "document", "url"].contains(&kind) {
        kind
    } else {
        "url"
    };
    let id = resources::store::create_external_resource(
        connection,
        kind,
        truth(payload, "title").unwrap_or(locator),
        locator,
        summary,
        text(payload, "source_role"),
    )?;
    Ok(("external".into(), id.to_string()))
}
pub fn resolve_suggestion(
    connection: &Connection,
    config: &Config,
    suggestion: i64,
    action: &str,
) -> Result<()> {
    let row = need(
        db::row(connection, sql::RESOLVE_SUGGESTION_0, [suggestion])?,
        "Suggestion not found",
    )?;
    if action == "restore" {
        if row["status"] != "rejected" {
            return Err(BackendError::invalid(
                "suggestion",
                "Only rejected suggestions can be restored",
            ));
        }
        connection.execute(sql::RESOLVE_SUGGESTION_1, [suggestion])?;
        return Ok(());
    }
    if row["status"] != "pending" {
        return Err(BackendError::invalid(
            "suggestion",
            "Only pending suggestions can be resolved",
        ));
    }
    let status = match action {
        "accept" => {
            let payload: Value = serde_json::from_str(
                text(&row, "payload_json")
                    .filter(|v| !v.is_empty())
                    .unwrap_or("{}"),
            )?;
            let target = text(&row, "target_type").unwrap_or_default();
            let owner = integer(&row, "target_id")?;
            if row["suggestion_type"] == "checkpoint_draft" {
                if target != "workstream" {
                    return Err(BackendError::invalid(
                        "suggestion",
                        "Checkpoint draft must target a Workstream",
                    ));
                }
                create_checkpoint(connection, owner, &payload)?;
            } else {
                let (kind, entity) = materialize(connection, config, &payload)?;
                add_link(
                    connection,
                    config,
                    target,
                    owner,
                    &kind,
                    &entity,
                    text(&payload, "relation_type").unwrap_or("related-to"),
                    "suggestion",
                    row["confidence"].as_f64(),
                )?;
            }
            "accepted"
        }
        "reject" => "rejected",
        _ => {
            return Err(BackendError::invalid(
                "suggestion",
                "Unsupported suggestion action",
            ))
        }
    };
    connection.execute(
        sql::RESOLVE_SUGGESTION_2,
        params![status, now(), suggestion],
    )?;
    Ok(())
}
