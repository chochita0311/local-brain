use super::{home_relative_path, source_presence_columns, sql};
use crate::backend::{db, now, unicode, BackendError, Config, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};

fn pin_error(code: &str, message: &str) -> BackendError {
    BackendError::new(400, code, message)
}
pub fn pin_session(conn: &Connection, id: i64, pinned_at: Option<&str>) -> Result<Value> {
    let row = db::row(conn, sql::ELIGIBLE_SESSION, [id])?
        .ok_or_else(|| pin_error("session-not-found", "Session not found."))?;
    if row["session_class"] != "work" {
        return Err(pin_error(
            "maintenance-session-ineligible",
            "Maintenance Sessions cannot be pinned.",
        ));
    }
    if row["session_role"] != "primary" {
        return Err(pin_error(
            "subsession-ineligible",
            "Subsessions cannot be pinned.",
        ));
    }
    let current = now();
    let timestamp = pinned_at
        .filter(|v| !v.is_empty())
        .unwrap_or(&current)
        .trim_matches(unicode::python_space);
    if timestamp.is_empty() {
        return Err(pin_error("invalid-pinned-at", "Pin time is required."));
    }
    conn.execute(sql::PIN_SESSION_0, params![id, timestamp])?;
    Ok(db::row(conn, sql::PIN_SESSION_1, [id])?.unwrap())
}
pub fn unpin_session(conn: &Connection, id: i64) -> Result<bool> {
    Ok(conn.execute(sql::UNPIN_SESSION, [id])? > 0)
}
pub fn is_session_pinned(conn: &Connection, id: i64) -> Result<bool> {
    Ok(db::row(conn, sql::IS_SESSION_PINNED, [id])?.is_some())
}
pub fn list_pinned_sessions(conn: &Connection, limit: i64) -> Result<Vec<Value>> {
    if !(1..=100).contains(&limit) {
        return Err(pin_error(
            "invalid-limit",
            "Pinned Session limit must be between 1 and 100.",
        ));
    }
    db::rows(
        conn,
        &format!(
            "{}\nLIMIT ?",
            sql::PINNED_SESSION_SELECT
                .replace("{source_presence}", &source_presence_columns("sessions"))
        ),
        [limit],
    )
}
pub fn list_all_pinned_sessions(conn: &Connection) -> Result<Vec<Value>> {
    db::rows(
        conn,
        &sql::PINNED_SESSION_SELECT
            .replace("{source_presence}", &source_presence_columns("sessions")),
        [],
    )
}
pub fn group_pinned_sessions(rows: &[Value], config: &Config) -> Vec<Value> {
    let mut groups: Vec<Value> = Vec::new();
    for row in rows {
        let identity = if let Some(id) = row["workspace_id"].as_i64() {
            format!("workspace:{id:020}")
        } else if let Some(cwd) = row["cwd_raw"].as_str().filter(|s| !s.is_empty()) {
            format!("cwd:{cwd}")
        } else {
            "unassigned".into()
        };
        let index = if let Some(index) = groups.iter().position(|v| v["identity"] == identity) {
            index
        } else {
            let path = row["workspace_path"]
                .as_str()
                .filter(|s| !s.is_empty())
                .or(row["cwd_raw"].as_str().filter(|s| !s.is_empty()));
            let name = row["workspace_name"]
                .as_str()
                .filter(|s| !s.is_empty())
                .or(path)
                .unwrap_or("작업 경로 없음");
            groups.push(json!({"identity":identity,"workspace_name":name,"workspace_path":path,"is_git":row["workspace_git_root"].as_str().is_some_and(|s|!s.is_empty()),"sessions":[]}));
            groups.len() - 1
        };
        groups[index]["sessions"]
            .as_array_mut()
            .unwrap()
            .push(row.clone());
    }
    groups.sort_by_key(|group| {
        (
            !group["is_git"].as_bool().unwrap(),
            unicode::casefold(
                &group["workspace_path"]
                    .as_str()
                    .filter(|s| !s.is_empty())
                    .map(|s| home_relative_path(s, config))
                    .unwrap_or_else(|| group["workspace_name"].as_str().unwrap().into()),
            ),
            group["identity"].as_str().unwrap().to_owned(),
        )
    });
    groups
}
pub fn set_display_title(conn: &Connection, id: i64, value: &Value) -> Result<Value> {
    let invalid = || BackendError::invalid("invalid-title", "invalid-title");
    let value = value
        .as_str()
        .ok_or_else(invalid)?
        .trim_matches(unicode::python_space);
    if value.chars().count() > 500
        || value
            .chars()
            .any(|ch| (ch as u32) < 32 || ['\u{85}', '\u{2028}', '\u{2029}'].contains(&ch))
    {
        return Err(invalid());
    }
    let row = db::row(
        conn,
        "SELECT id, title, session_class, session_role FROM sessions WHERE id = ?",
        [id],
    )?
    .ok_or_else(|| BackendError::invalid("session-not-found", "session-not-found"))?;
    if row["session_class"] != "work" || row["session_role"] != "primary" {
        return Err(BackendError::invalid(
            "ineligible-session",
            "ineligible-session",
        ));
    }
    let title = (!value.is_empty()).then_some(value);
    conn.execute(
        "UPDATE sessions SET display_title = ? WHERE id = ?",
        params![title, id],
    )?;
    Ok(
        json!({"id":row["id"],"title":row["title"],"display_title":title,"effective_title":title.map(|v|json!(v)).unwrap_or_else(||row["title"].clone())}),
    )
}
pub fn validate_hidden_projects(value: &Value) -> Result<Vec<String>> {
    let items = value
        .as_array()
        .filter(|v| v.len() <= 2000)
        .ok_or_else(|| {
            BackendError::invalid(
                "project-visibility",
                "Hidden projects must be a bounded list",
            )
        })?;
    let mut result = items
        .iter()
        .map(|v| {
            v.as_str()
                .filter(|v| v.chars().count() <= 4096)
                .map(ToOwned::to_owned)
                .ok_or_else(|| {
                    BackendError::invalid("project-visibility", "Invalid Project identity")
                })
        })
        .collect::<Result<Vec<_>>>()?;
    result.sort();
    result.dedup();
    if serde_json::to_vec(&result)?.len() > 60_000 {
        return Err(BackendError::invalid(
            "project-visibility",
            "Project preferences are too large",
        ));
    }
    Ok(result)
}
pub fn get_project_visibility(
    conn: &Connection,
    source: &str,
    workspace: Option<i64>,
) -> Result<Option<Vec<String>>> {
    let row=db::row(conn,"SELECT hidden_projects_json FROM session_chart_preferences WHERE source_scope = ? AND workspace_scope = ?",params![source,workspace.map(|v|v.to_string()).unwrap_or_default()])?;
    row.map(|row| {
        validate_hidden_projects(&serde_json::from_str::<Value>(
            row["hidden_projects_json"].as_str().unwrap(),
        )?)
    })
    .transpose()
}
pub fn set_project_visibility(
    conn: &Connection,
    source: &str,
    workspace: Option<i64>,
    hidden: &Value,
    only_if_missing: bool,
) -> Result<Vec<String>> {
    let keys = validate_hidden_projects(hidden)?;
    let conflict = if only_if_missing {
        "DO NOTHING"
    } else {
        "DO UPDATE SET hidden_projects_json = excluded.hidden_projects_json, updated_at = excluded.updated_at"
    };
    conn.execute(&format!("INSERT INTO session_chart_preferences (source_scope, workspace_scope, hidden_projects_json, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(source_scope, workspace_scope) {conflict}"),params![source,workspace.map(|v|v.to_string()).unwrap_or_default(),serde_json::to_string(&keys)?,now()])?;
    Ok(get_project_visibility(conn, source, workspace)?.unwrap())
}
