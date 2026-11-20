use crate::backend::{db, Result};
use rusqlite::{params, Connection};
use serde_json::Value;
pub fn recent_documents(connection: &Connection, limit: i64) -> Result<Vec<Value>> {
    db::rows(connection,"SELECT context_documents.id,context_documents.title,context_documents.relative_path,context_documents.path,context_documents.mtime_ns FROM context_documents LEFT JOIN context_roots ON context_roots.id=context_documents.context_root_id WHERE context_documents.context_root_id IS NULL OR context_roots.enabled=1 ORDER BY mtime_ns DESC LIMIT ?",[limit])
}
pub fn context_documents(
    connection: &Connection,
    root: Option<i64>,
    limit: i64,
) -> Result<Vec<Value>> {
    if let Some(root) = root {
        db::rows(connection,"SELECT context_documents.id,context_documents.title,context_documents.relative_path,context_documents.path,context_documents.size_bytes,context_documents.mtime_ns,context_roots.label AS root_label,context_roots.path AS root_path FROM context_documents JOIN context_roots ON context_roots.id=context_documents.context_root_id WHERE context_roots.enabled=1 AND context_roots.id=? ORDER BY context_documents.mtime_ns DESC LIMIT ?",params![root,limit])
    } else {
        db::rows(connection,"SELECT context_documents.id,context_documents.title,context_documents.relative_path,context_documents.path,context_documents.size_bytes,context_documents.mtime_ns,context_roots.label AS root_label,context_roots.path AS root_path FROM context_documents LEFT JOIN context_roots ON context_roots.id=context_documents.context_root_id WHERE context_documents.context_root_id IS NULL OR context_roots.enabled=1 ORDER BY context_documents.mtime_ns DESC LIMIT ?",[limit])
    }
}
pub fn document_detail(connection: &Connection, id: i64) -> Result<Option<Value>> {
    db::row(connection,"SELECT context_documents.*,sources.name AS source_name,workspaces.display_name AS workspace_name,context_roots.label AS context_root_label,context_roots.path AS context_root_path FROM context_documents JOIN sources ON sources.id=context_documents.source_id LEFT JOIN context_roots ON context_roots.id=context_documents.context_root_id LEFT JOIN workspaces ON workspaces.id=context_documents.workspace_id WHERE context_documents.id=?",[id])
}
