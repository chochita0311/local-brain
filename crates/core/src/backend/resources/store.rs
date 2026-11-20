use super::{bind_external_link, bind_local_path};
use crate::backend::{db, now, storage::files, unicode, BackendError, Config, Result};
use rusqlite::{params, Connection};
use serde_json::Value;
pub const RESOURCE_TYPES: &[&str] = &["jira", "wiki", "slack", "git", "document", "url"];
fn clean(value: Option<&str>) -> Option<&str> {
    value
        .map(|v| v.trim_matches(unicode::python_space))
        .filter(|v| !v.is_empty())
}
pub fn create_external_resource(
    conn: &Connection,
    resource_type: &str,
    title: &str,
    url: &str,
    summary: Option<&str>,
    source_role: Option<&str>,
) -> Result<i64> {
    if !RESOURCE_TYPES.contains(&resource_type) {
        return Err(BackendError::invalid(
            "resource",
            "Unsupported resource type",
        ));
    }
    let timestamp = now();
    let url = url.trim_matches(unicode::python_space);
    let title = title.trim_matches(unicode::python_space);
    let existing = db::row(
        conn,
        "SELECT id FROM external_resources WHERE url=? ORDER BY id LIMIT 1",
        [url],
    )?;
    let id = if let Some(existing) = existing {
        let id = existing["id"].as_i64().unwrap();
        conn.execute("UPDATE external_resources SET resource_type=?,title=?,summary=?,source_role=?,updated_at=? WHERE id=?",params![resource_type,title,clean(summary),clean(source_role),timestamp,id])?;
        id
    } else {
        conn.execute("INSERT INTO external_resources(resource_type,title,url,summary,source_role,updated_at) VALUES(?,?,?,?,?,?)",params![resource_type,title,url,clean(summary),clean(source_role),timestamp])?;
        conn.last_insert_rowid()
    };
    bind_external_link(conn, id)?;
    Ok(id)
}
pub fn create_local_resource(
    conn: &Connection,
    config: &Config,
    path: &str,
    title: Option<&str>,
    summary: Option<&str>,
    discovered_by: &str,
) -> Result<i64> {
    let candidate = files::expand(std::path::Path::new(path), config);
    let exists = candidate.exists();
    let canonical = if exists {
        files::resolve(&candidate)?
    } else {
        candidate.clone()
    };
    let resource_type = if candidate.is_dir() {
        if candidate.join(".git").exists() {
            "repository"
        } else {
            "directory"
        }
    } else if candidate.is_file() {
        "file"
    } else {
        "path"
    };
    let canonical = canonical
        .to_str()
        .ok_or_else(|| BackendError::invalid("unicode", "Resource path is not Unicode"))?;
    let title = clean(title)
        .or_else(|| candidate.file_name().and_then(|s| s.to_str()))
        .filter(|s| !s.is_empty())
        .unwrap_or(canonical);
    conn.execute("INSERT INTO local_resources(path,resource_type,title,summary,exists_now,discovered_by,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET resource_type=excluded.resource_type,title=excluded.title,summary=COALESCE(excluded.summary,local_resources.summary),exists_now=excluded.exists_now,discovered_by=excluded.discovered_by,updated_at=excluded.updated_at",params![canonical,resource_type,title,clean(summary),exists,discovered_by,now()])?;
    let id = conn.query_row(
        "SELECT id FROM local_resources WHERE path=?",
        [canonical],
        |row| row.get(0),
    )?;
    bind_local_path(conn, id, config)?;
    Ok(id)
}
pub fn local_resource_detail(conn: &Connection, id: i64) -> Result<Option<Value>> {
    db::row(conn, "SELECT * FROM local_resources WHERE id=?", [id])
}
