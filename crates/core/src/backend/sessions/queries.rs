use super::{source_presence_columns, sql};
use crate::backend::{clock, db, Config, Result};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection};
use serde_json::{json, Value};
use std::collections::HashMap;

pub const SESSION_PAGE_SIZE: i64 = 15;
fn scope(
    source: Option<&str>,
    workspace: Option<i64>,
    truthy_workspace: bool,
) -> (String, Vec<SqlValue>) {
    let mut conditions = vec![
        "sessions.session_class = 'work'",
        "sessions.session_role = 'primary'",
    ];
    let mut args = Vec::new();
    if let Some(source) = source.filter(|s| !s.is_empty()) {
        conditions.push("sources.id = ?");
        args.push(source.to_owned().into());
    }
    if let Some(workspace) = workspace.filter(|v| !truthy_workspace || *v != 0) {
        conditions.push("sessions.workspace_id = ?");
        args.push(workspace.into());
    }
    (conditions.join(" AND "), args)
}
pub fn pagination_items(page: i64, total: i64) -> Vec<Option<i64>> {
    if total <= 7 {
        return (1..=total).map(Some).collect();
    }
    let mut first = 2.max(page - 1);
    let mut last = (total - 1).min(page + 1);
    if page <= 3 {
        last = 4;
    } else if page >= total - 2 {
        first = total - 3;
    }
    let mut result = vec![Some(1)];
    if first > 2 {
        result.push(None);
    }
    result.extend((first..=last).map(Some));
    if last < total - 1 {
        result.push(None);
    }
    result.push(Some(total));
    result
}
pub fn compact_pagination_items(page: i64, total: i64) -> Vec<Option<i64>> {
    if total <= 5 {
        (1..=total).map(Some).collect()
    } else if page <= 2 {
        vec![Some(1), Some(2), Some(3), None, Some(total)]
    } else if page >= total - 1 {
        vec![Some(1), None, Some(total - 2), Some(total - 1), Some(total)]
    } else {
        vec![Some(1), None, Some(page), None, Some(total)]
    }
}
pub fn recent_sessions(
    conn: &Connection,
    source: Option<&str>,
    workspace: Option<i64>,
    limit: i64,
) -> Result<Vec<Value>> {
    let (conditions, mut args) = scope(source, workspace, true);
    args.push(limit.into());
    db::rows(
        conn,
        &sql::RECENT_SESSIONS.replace("{where}", &format!("WHERE {conditions}")),
        params_from_iter(args),
    )
}
pub fn session_inventory_page(
    conn: &Connection,
    source: Option<&str>,
    workspace: Option<i64>,
    page: i64,
) -> Result<Value> {
    let (conditions, args) = scope(source, workspace, false);
    let total = db::row(
        conn,
        &sql::SESSION_INVENTORY_PAGE_0.replace("{where}", &conditions),
        params_from_iter(args.iter()),
    )?
    .unwrap()["count"]
        .as_i64()
        .unwrap();
    let total_pages = 1.max((total + SESSION_PAGE_SIZE - 1) / SESSION_PAGE_SIZE);
    let page = page.clamp(1, total_pages);
    let mut page_args = args;
    page_args.extend([
        SESSION_PAGE_SIZE.into(),
        ((page - 1) * SESSION_PAGE_SIZE).into(),
    ]);
    let mut items = db::rows(
        conn,
        &sql::SESSION_INVENTORY_PAGE_1
            .replace("{where}", &conditions)
            .replace("{source_presence}", &source_presence_columns("sessions")),
        params_from_iter(page_args),
    )?;
    let ids = items
        .iter()
        .filter_map(|v| v["id"].as_i64())
        .collect::<Vec<_>>();
    let mut children: HashMap<i64, Vec<Value>> = HashMap::new();
    if !ids.is_empty() {
        let query = sql::SESSION_INVENTORY_PAGE_2
            .replace("{placeholders}", &vec!["?"; ids.len()].join(", "))
            .replace("{source_presence}", &source_presence_columns("children"));
        for row in db::rows(conn, &query, params_from_iter(ids))? {
            children
                .entry(row["parent_session_id"].as_i64().unwrap())
                .or_default()
                .push(row);
        }
    }
    for item in &mut items {
        item["subsessions"] = json!(children
            .remove(&item["id"].as_i64().unwrap())
            .unwrap_or_default());
    }
    Ok(
        json!({"items":items,"total":total,"page":page,"page_size":SESSION_PAGE_SIZE,"total_pages":total_pages,"page_items":pagination_items(page,total_pages),"compact_page_items":compact_pagination_items(page,total_pages),"previous_page":(page>1).then_some(page-1),"next_page":(page<total_pages).then_some(page+1)}),
    )
}
pub fn home_relative_path(path: &str, config: &Config) -> String {
    let home = config.home_dir.to_string_lossy();
    if path == home {
        "~".into()
    } else if path
        .strip_prefix(home.as_ref())
        .is_some_and(|rest| rest.starts_with('/'))
    {
        format!("~{}", &path[home.len()..])
    } else {
        path.into()
    }
}
pub(crate) fn posix_normpath(path: &str) -> String {
    let absolute = path.starts_with('/');
    let double = path.starts_with("//") && !path.starts_with("///");
    let mut parts = Vec::new();
    for part in path.split('/') {
        match part {
            "" | "." => {}
            ".." if parts.last().is_some_and(|s| *s != "..") => {
                parts.pop();
            }
            ".." if absolute => {}
            _ => parts.push(part),
        }
    }
    let prefix = if double {
        "//"
    } else if absolute {
        "/"
    } else {
        ""
    };
    let normalized = format!("{prefix}{}", parts.join("/"));
    if normalized.is_empty() {
        ".".into()
    } else {
        normalized
    }
}
pub fn session_chart_inventory(
    conn: &Connection,
    config: &Config,
    source: Option<&str>,
    workspace: Option<i64>,
) -> Result<Vec<Value>> {
    let (conditions, args) = scope(source, workspace, false);
    let mut items = db::rows(
        conn,
        &sql::SESSION_CHART_INVENTORY.replace("{where}", &conditions),
        params_from_iter(args),
    )?;
    let home = config.home_dir.to_string_lossy();
    let mut undated = Vec::new();
    for item in &mut items {
        let cwd = item["cwd_raw"].as_str().unwrap_or("");
        let cwd = if cwd == "~" || cwd.starts_with("~/") {
            format!("{home}{}", &cwd[1..])
        } else {
            cwd.into()
        };
        let folder = if cwd.is_empty() {
            String::new()
        } else {
            posix_normpath(&cwd)
        };
        let project_name = if folder == home {
            "~".into()
        } else {
            folder
                .rsplit('/')
                .next()
                .filter(|s| !s.is_empty())
                .unwrap_or(if folder.is_empty() {
                    "실행 폴더 없음"
                } else {
                    &folder
                })
                .to_owned()
        };
        item["project_key"] = json!(folder);
        item["project_name"] = json!(project_name);
        item["project_path"] = json!(home_relative_path(&folder, config));
        let mut times = ["last_event_at", "started_at"]
            .iter()
            .filter_map(|key| item[*key].as_str().and_then(clock::parse_timestamp))
            .collect::<Vec<_>>();
        times.sort();
        item["first_observed_at"] = json!(times.first().copied().map(clock::isoformat));
        item["observed_at"] = json!(times.last().copied().map(clock::isoformat));
        item["time_source"] = if times.is_empty() {
            Value::Null
        } else {
            json!("metadata")
        };
        if times.is_empty() {
            undated.push(item["id"].as_i64().unwrap());
        }
    }
    let mut bounds = HashMap::new();
    for ids in undated.chunks(500) {
        let query = format!(
            "SELECT session_id, occurred_at FROM activity_events WHERE session_id IN ({})",
            vec!["?"; ids.len()].join(",")
        );
        for event in db::rows(conn, &query, params_from_iter(ids))? {
            if let Some(at) = event["occurred_at"]
                .as_str()
                .and_then(clock::parse_timestamp)
            {
                let bound = bounds
                    .entry(event["session_id"].as_i64().unwrap())
                    .or_insert((at, at));
                bound.0 = bound.0.min(at);
                bound.1 = bound.1.max(at);
            }
        }
    }
    for item in &mut items {
        if let Some((first, last)) = bounds.get(&item["id"].as_i64().unwrap()) {
            item["first_observed_at"] = json!(clock::isoformat(*first));
            item["observed_at"] = json!(clock::isoformat(*last));
            item["time_source"] = json!("event");
        }
    }
    Ok(items)
}
pub fn session_chart_activity(conn: &Connection, id: i64) -> Result<Option<Value>> {
    let Some(session) = db::row(conn, sql::SESSION_CHART_ACTIVITY_0, [id])? else {
        return Ok(None);
    };
    let mut times = Vec::new();
    let mut undated = 0;
    for row in db::rows(conn, sql::SESSION_CHART_ACTIVITY_1, [id])? {
        if let Some(at) = row["occurred_at"].as_str().and_then(clock::parse_timestamp) {
            times.push(at)
        } else {
            undated += 1;
        }
    }
    times.sort();
    let metadata = ["started_at", "last_event_at"]
        .iter()
        .filter_map(|key| {
            session[*key]
                .as_str()
                .and_then(clock::parse_timestamp)
                .map(|at| json!({"field":key,"at":clock::isoformat(at)}))
        })
        .collect::<Vec<_>>();
    Ok(Some(
        json!({"session_id":id,"timestamps":times.iter().copied().map(clock::isoformat).collect::<Vec<_>>(),"total_events":times.len()+undated,"undated_events":undated,"metadata_times":metadata}),
    ))
}
pub fn project_activity(conn: &Connection, source: Option<&str>) -> Result<Vec<Value>> {
    let args = source
        .filter(|s| !s.is_empty())
        .into_iter()
        .collect::<Vec<_>>();
    db::rows(
        conn,
        &sql::PROJECT_ACTIVITY.replace(
            "{source_condition}",
            if args.is_empty() {
                ""
            } else {
                "AND sources.id = ?"
            },
        ),
        params_from_iter(args),
    )
}
pub fn session_source_scopes(conn: &Connection) -> Result<Vec<Value>> {
    db::rows(conn, sql::SESSION_SOURCE_SCOPES, [])
}
pub fn session_id_prefix(conn: &Connection, external: &str) -> Result<String> {
    let chars = external.chars().collect::<Vec<_>>();
    let mut length = 8.min(chars.len());
    let prefix = chars[..length].iter().collect::<String>();
    let candidates = db::rows(
        conn,
        sql::SESSION_ID_PREFIX,
        params![length as i64, prefix, external],
    )?;
    while length < chars.len()
        && candidates.iter().any(|v| {
            v["external_id"]
                .as_str()
                .is_some_and(|v| v.starts_with(&chars[..length].iter().collect::<String>()))
        })
    {
        length += 1;
    }
    Ok(chars[..length].iter().collect())
}
pub fn session_detail(conn: &Connection, id: i64) -> Result<Option<Value>> {
    db::row(
        conn,
        &sql::SESSION_DETAIL.replace("{source_presence}", &source_presence_columns("sessions")),
        [id],
    )
}
pub fn session_events(conn: &Connection, id: i64, limit: i64) -> Result<Vec<Value>> {
    db::rows(conn, sql::SESSION_EVENTS, params![id, limit])
}
pub fn session_conversation_events(conn: &Connection, id: i64) -> Result<Vec<Value>> {
    db::rows(conn, sql::SESSION_CONVERSATION_EVENTS, [id])
}
pub fn session_parent(conn: &Connection, id: i64) -> Result<Option<Value>> {
    db::row(conn, sql::SESSION_PARENT, [id])
}
pub fn session_subsessions(conn: &Connection, id: i64) -> Result<Vec<Value>> {
    db::rows(
        conn,
        &sql::SESSION_SUBSESSIONS
            .replace("{source_presence}", &source_presence_columns("children")),
        [id],
    )
}
