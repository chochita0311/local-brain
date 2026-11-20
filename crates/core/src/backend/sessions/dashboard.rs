use super::dashboard_sql as sql;
use crate::backend::{db, Result};
use rusqlite::{params, params_from_iter, Connection};
use serde_json::{Map, Value};

pub fn dashboard_stats(conn: &Connection, source: Option<&str>) -> Result<Value> {
    let source = source.filter(|s| !s.is_empty());
    let condition = if source.is_some() {
        " AND sessions.source_id = ?"
    } else {
        ""
    };
    let mut output = Map::new();
    for (key, query, scoped) in [
        ("sessions", sql::DASHBOARD_STATS_0, true),
        ("events", sql::DASHBOARD_STATS_1, true),
        ("documents", sql::DASHBOARD_STATS_2, false),
        ("workspaces", sql::DASHBOARD_STATS_3, false),
        ("missing_workspaces", sql::DASHBOARD_STATS_4, true),
        ("recent_sessions", sql::DASHBOARD_STATS_5, true),
        ("active_workspaces", sql::DASHBOARD_STATS_6, true),
        ("context_switches", sql::DASHBOARD_STATS_7, true),
    ] {
        let query = query.replace("{source_condition}", condition);
        let args = source.filter(|_| scoped);
        let row = db::row(conn, &query, params_from_iter(args))?.unwrap();
        output.insert(key.into(), row["count"].clone());
    }
    Ok(Value::Object(output))
}
pub fn source_inventory(conn: &Connection) -> Result<Vec<Value>> {
    db::rows(conn, sql::SOURCE_INVENTORY, [])
}
pub fn daily_activity(conn: &Connection, days: i64) -> Result<Vec<Value>> {
    db::rows(
        conn,
        sql::DAILY_ACTIVITY,
        params![format!("-{} days", days - 1), days],
    )
}
pub fn source_activity(conn: &Connection) -> Result<Vec<Value>> {
    db::rows(conn, sql::SOURCE_ACTIVITY, [])
}
pub fn top_tools(conn: &Connection, limit: i64) -> Result<Vec<Value>> {
    db::rows(conn, sql::TOP_TOOLS, [limit])
}
pub fn top_workspace_activity(conn: &Connection, limit: i64) -> Result<Vec<Value>> {
    db::rows(conn, sql::TOP_WORKSPACE_ACTIVITY, [limit])
}
