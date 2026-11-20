use crate::backend::{
    ingest::{parse_session, ParsedSession},
    Result,
};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
pub fn subagent_root(source: &str) -> PathBuf {
    let path = Path::new(source);
    path.parent()
        .unwrap_or(Path::new("."))
        .join(path.file_stem().unwrap_or_default())
        .join("subagents")
}
pub fn list_subagents(source: &str, parent: Option<&str>) -> Result<Vec<Value>> {
    let root = subagent_root(source);
    if !root.is_dir() {
        return Ok(vec![]);
    }
    let mut paths = std::fs::read_dir(&root)?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| {
            path.extension()
                .is_some_and(|extension| extension == "jsonl")
        })
        .map(|path| {
            std::fs::metadata(&path)
                .and_then(|info| info.modified())
                .map(|mtime| (mtime, path))
        })
        .collect::<std::io::Result<Vec<_>>>()?;
    paths.sort_by(|a, b| b.0.cmp(&a.0));
    let mut items = Vec::new();
    for (_, path) in paths {
        let Ok(Some(parsed)) = parse_session("claude", &path) else {
            continue;
        };
        if parent.is_some() && parsed.parent_external_id.as_deref() != parent {
            continue;
        }
        let stem = path.file_stem().unwrap_or_default().to_string_lossy();
        items.push(json!({"file_name":path.file_name().unwrap_or_default().to_string_lossy(),"source_path":parsed.source_path,"external_id":parsed.external_id,"parent_external_id":parsed.parent_external_id,"agent_id":stem.strip_prefix("agent-").unwrap_or(&stem),"title":parsed.title,"last_event_at":parsed.last_event_at,"user_message_count":parsed.events.iter().filter(|event|event.event_type=="message"&&event.role.as_deref()==Some("user")).count(),"event_count":parsed.events.len()}));
    }
    Ok(items)
}
pub fn load_subagent(source: &str, name: &str) -> Result<Option<ParsedSession>> {
    if Path::new(name).file_name().is_none_or(|base| base != name) || !name.ends_with(".jsonl") {
        return Ok(None);
    }
    let root = subagent_root(source);
    let candidate = root.join(name);
    if !candidate.is_file() || candidate.parent() != Some(root.as_path()) {
        return Ok(None);
    }
    parse_session("claude", &candidate)
}
