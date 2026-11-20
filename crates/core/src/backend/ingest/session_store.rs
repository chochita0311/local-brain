use super::{
    common::{path_text, stable_id},
    storage, IngestionObserver, ParsedSession,
};
use crate::backend::{db, now, usage, Config, Result};
use rusqlite::{params, Connection};
use std::{
    collections::{BTreeSet, HashMap, HashSet},
    path::Path,
};
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
pub(super) fn store(
    db: &Connection,
    config: &Config,
    source: i64,
    provider: &str,
    parsed: &ParsedSession,
    usage_version: &str,
    include_usage: bool,
    preserve: bool,
) -> Result<i64> {
    let workspace = storage::workspace(
        db,
        config,
        parsed.cwd_raw.as_deref(),
        parsed.last_event_at.as_deref(),
    )?;
    let maintenance = parsed.maintenance_run_id.as_deref().filter(|id| {
        db.query_row(
            "SELECT EXISTS(SELECT 1 FROM maintenance_runs WHERE id=?)",
            [*id],
            |r| r.get::<_, bool>(0),
        )
        .unwrap_or(false)
    });
    let full = parsed.index_policy == "full";
    let users = parsed
        .events
        .iter()
        .filter(|e| e.event_type == "message" && e.role.as_deref() == Some("user"))
        .count() as i64;
    let assistants = parsed
        .events
        .iter()
        .filter(|e| e.event_type == "message" && e.role.as_deref() == Some("assistant"))
        .count() as i64;
    db.execute("INSERT INTO sessions(source_id,workspace_id,external_id,source_path,cwd_raw,git_branch,title,started_at,ended_at,last_event_at,event_count,user_message_count,assistant_message_count,session_class,session_role,parent_external_id,parent_session_id,index_policy,maintenance_run_id,imported_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?) ON CONFLICT(source_id,external_id) DO UPDATE SET workspace_id=excluded.workspace_id,source_path=excluded.source_path,cwd_raw=excluded.cwd_raw,git_branch=excluded.git_branch,title=excluded.title,started_at=excluded.started_at,ended_at=excluded.ended_at,last_event_at=excluded.last_event_at,event_count=excluded.event_count,user_message_count=excluded.user_message_count,assistant_message_count=excluded.assistant_message_count,session_class=excluded.session_class,session_role=excluded.session_role,parent_external_id=excluded.parent_external_id,parent_session_id=NULL,index_policy=excluded.index_policy,maintenance_run_id=excluded.maintenance_run_id,imported_at=excluded.imported_at",params![source,workspace,parsed.external_id,parsed.source_path,parsed.cwd_raw,parsed.git_branch,parsed.title,parsed.started_at,parsed.ended_at,parsed.last_event_at,if full{parsed.events.len()as i64}else{0},if full{users}else{0},if full{assistants}else{0},parsed.session_class,parsed.session_role,parsed.parent_external_id,parsed.index_policy,maintenance,now()])?;
    let id: i64 = db.query_row(
        "SELECT id FROM sessions WHERE source_id=? AND external_id=?",
        params![source, parsed.external_id],
        |r| r.get(0),
    )?;
    if include_usage {
        usage::store_usage_records(
            db,
            source,
            id,
            &parsed.usage_records,
            workspace,
            usage_version,
        )?;
    }
    let mut old = HashMap::new();
    for row in db::rows(
        db,
        "SELECT id,sequence,event_type,source_line FROM activity_events WHERE session_id=?",
        [id],
    )? {
        old.insert(
            (
                row["sequence"].as_i64().unwrap(),
                row["event_type"].as_str().unwrap().to_owned(),
                row["source_line"].as_i64().unwrap(),
            ),
            row["id"].as_str().unwrap().to_owned(),
        );
    }
    let preserve = preserve && full;
    if !preserve {
        db.execute("DELETE FROM activity_events WHERE session_id=?", [id])?;
    }
    db.execute(
        "DELETE FROM search_index WHERE entity_type='session' AND entity_id=?",
        [id.to_string()],
    )?;
    if full {
        for event in &parsed.events {
            let event_id = old
                .get(&(event.sequence, event.event_type.clone(), event.source_line))
                .cloned()
                .unwrap_or_else(|| {
                    stable_id(&["source-event", &source.to_string(), &event.event_id])
                });
            let sql=format!("INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,tool_name,source_line,message_phase) VALUES(?,?,?,?,?,?,?,?,?,?){}",if preserve{" ON CONFLICT DO NOTHING"}else{""});
            db.execute(
                &sql,
                params![
                    event_id,
                    id,
                    event.sequence,
                    event.occurred_at,
                    event.event_type,
                    event.role,
                    event.text,
                    event.tool_name,
                    event.source_line,
                    event.message_phase
                ],
            )?;
        }
        let body = if preserve {
            db.execute("UPDATE sessions SET event_count=(SELECT count(*) FROM activity_events WHERE session_id=?),user_message_count=(SELECT count(*) FROM activity_events WHERE session_id=? AND event_type='message' AND role='user'),assistant_message_count=(SELECT count(*) FROM activity_events WHERE session_id=? AND event_type='message' AND role='assistant') WHERE id=?",params![id,id,id,id])?;
            db::rows(
                db,
                "SELECT text FROM activity_events WHERE session_id=? ORDER BY sequence,id",
                [id],
            )?
            .iter()
            .filter_map(|r| r["text"].as_str().filter(|s| !s.is_empty()).map(Into::into))
            .collect::<Vec<String>>()
            .join("\n")
        } else {
            parsed
                .events
                .iter()
                .filter_map(|e| e.text.as_deref().filter(|s| !s.is_empty()))
                .collect::<Vec<_>>()
                .join("\n")
        };
        if parsed.session_role == "primary" {
            storage::replace_search(
                db,
                "session",
                &id.to_string(),
                provider,
                &parsed.title,
                &body,
                parsed
                    .cwd_raw
                    .as_deref()
                    .filter(|s| !s.is_empty())
                    .unwrap_or(&parsed.source_path),
            )?;
        }
    }
    Ok(id)
}
pub(super) fn prune(
    db: &Connection,
    source: i64,
    valid: &BTreeSet<String>,
    observer: &dyn IngestionObserver,
) -> Result<()> {
    let rows = db::rows(
        db,
        "SELECT session_id,path FROM source_files WHERE source_id=? AND session_id IS NOT NULL",
        [source],
    )?;
    let mut linked: HashMap<i64, Vec<String>> = HashMap::new();
    for row in &rows {
        let path = row["path"].as_str().unwrap();
        if valid.contains(path) {
            linked
                .entry(row["session_id"].as_i64().unwrap())
                .or_default()
                .push(path.into());
        }
    }
    for row in db::rows(db,"SELECT id,source_path FROM sessions WHERE source_id=? AND NOT(session_class='maintenance' AND index_policy='metadata_only' AND external_id IN(SELECT 'localbrain-insight:'||id FROM personal_insight_runs))",[source])?{let path=row["source_path"].as_str().unwrap();let id=row["id"].as_i64().unwrap();if valid.contains(path){continue;}
if let Some(paths)=linked.get_mut(&id){paths.sort();db.execute("UPDATE sessions SET source_path=? WHERE id=?",params![paths[0],id])?;}else{db.execute("DELETE FROM search_index WHERE entity_type='session' AND entity_id=?",[id.to_string()])?;storage::delete_owner(db,Some(id),None,observer)?;}}
    observer.session_sources_pruned(db, source, valid)?;
    for row in db::rows(
        db,
        "SELECT id,path FROM source_files WHERE source_id=?",
        [source],
    )? {
        if !valid.contains(row["path"].as_str().unwrap()) {
            db.execute("DELETE FROM source_files WHERE id=?", [row["id"].as_i64()])?;
        }
    }
    for row in rows {
        let path = row["path"].as_str().unwrap();
        let id = row["session_id"].as_i64().unwrap();
        if !valid.contains(path)
            && db.query_row(
                "SELECT EXISTS(SELECT 1 FROM sessions WHERE id=?)",
                [id],
                |r| r.get::<_, bool>(0),
            )?
        {
            observer.clear_reference_source(db, id, path)?;
        }
    }
    Ok(())
}
pub(super) fn eligibility_repair(db: &Connection, source: i64) -> Result<bool> {
    Ok(db.query_row("SELECT EXISTS(SELECT 1 FROM sessions WHERE source_id=? AND index_policy='full' AND event_count=0 AND NOT EXISTS(SELECT 1 FROM activity_events WHERE session_id=sessions.id) AND NOT EXISTS(SELECT 1 FROM usage_records WHERE session_id=sessions.id) AND NOT EXISTS(SELECT 1 FROM skill_observations WHERE source_id=sessions.source_id AND external_session_id=sessions.external_id AND state='observed'))",[source],|r|r.get(0))?)
}
pub(super) fn remove_empty(
    db: &Connection,
    source: i64,
    candidates: &[(String, ParsedSession)],
    observer: &dyn IngestionObserver,
) -> Result<()> {
    let empty = candidates
        .iter()
        .map(|(p, _)| p.clone())
        .collect::<HashSet<_>>();
    for (path, parsed) in candidates {
        if let Some(row) = db::row(
            db,
            "SELECT session_id FROM source_files WHERE source_id=? AND path=?",
            params![source, path],
        )? {
            if let Some(id) = row["session_id"].as_i64() {
                observer.clear_reference_source(db, id, path)?;
            }
        }
        observer.empty_session_source(db, source, path)?;
        for row in db::rows(db,"SELECT id,source_path FROM sessions WHERE source_id=? AND index_policy='full' AND(external_id=? OR source_path=?)",params![source,parsed.external_id,path])?{let id=row["id"].as_i64().unwrap();let paths=db::rows(db,"SELECT path FROM source_files WHERE session_id=?",[id])?;if !empty.contains(row["source_path"].as_str().unwrap())||paths.iter().any(|r|!empty.contains(r["path"].as_str().unwrap())){continue;}db.execute("DELETE FROM activity_events WHERE session_id=?",[id])?;db.execute("DELETE FROM search_index WHERE entity_type='session' AND entity_id=?",[id.to_string()])?;db.execute("UPDATE sessions SET event_count=0,user_message_count=0,assistant_message_count=0 WHERE id=?",[id])?;let meaningful:bool=db.query_row("SELECT EXISTS(SELECT 1 FROM usage_records WHERE session_id=?)",[id],|r|r.get(0))?;if !meaningful{storage::delete_owner(db,Some(id),None,observer)?;}}
        db.execute(
            "DELETE FROM source_files WHERE source_id=? AND path=?",
            params![source, path],
        )?;
    }
    Ok(())
}
pub(super) fn parents(db: &Connection, source: i64, provider: &str) -> Result<()> {
    let rows=db::rows(db,"SELECT id,external_id,source_path,session_class,session_role,parent_external_id FROM sessions WHERE source_id=?",[source])?;
    let mut candidates = HashMap::new();
    let by_external = rows
        .iter()
        .map(|r| (r["external_id"].as_str().unwrap(), r))
        .collect::<HashMap<_, _>>();
    let by_path = rows
        .iter()
        .map(|r| (r["source_path"].as_str().unwrap(), r))
        .collect::<HashMap<_, _>>();
    let by_id = rows
        .iter()
        .map(|r| (r["id"].as_i64().unwrap(), r))
        .collect::<HashMap<_, _>>();
    for row in &rows {
        let id = row["id"].as_i64().unwrap();
        if row["session_role"] != "subsession" {
            db.execute(
                "UPDATE sessions SET parent_external_id=NULL,parent_session_id=NULL WHERE id=?",
                [id],
            )?;
            continue;
        }
        let mut parent = row["parent_external_id"]
            .as_str()
            .and_then(|s| by_external.get(s).copied());
        if parent.is_none() && provider == "claude" {
            let path = Path::new(row["source_path"].as_str().unwrap());
            if path
                .parent()
                .and_then(Path::file_name)
                .and_then(|s| s.to_str())
                == Some("subagents")
            {
                if let Some(base) = path.parent().and_then(Path::parent) {
                    let p = base.with_extension("jsonl");
                    parent = by_path.get(path_text(&p)?.as_str()).copied();
                }
            }
        }
        if let Some(parent) = parent.filter(|p| p["id"].as_i64() != Some(id)) {
            candidates.insert(id, parent["id"].as_i64().unwrap());
        }
    }
    for row in &rows {
        if row["session_role"] != "subsession" {
            continue;
        }
        let id = row["id"].as_i64().unwrap();
        let mut seen = HashSet::from([id]);
        let mut current = candidates.get(&id).copied();
        let mut safe = true;
        while let Some(parent) = current {
            if !seen.insert(parent) {
                safe = false;
                break;
            }
            current = candidates.get(&parent).copied();
        }
        let Some(parent) = candidates.get(&id).copied().filter(|_| safe) else {
            db.execute(
                "UPDATE sessions SET parent_session_id=NULL WHERE id=?",
                [id],
            )?;
            continue;
        };
        db.execute(
            "UPDATE sessions SET parent_external_id=?,parent_session_id=? WHERE id=?",
            params![by_id[&parent]["external_id"].as_str(), parent, id],
        )?;
        if by_id[&parent]["session_class"] == "maintenance" {
            db.execute("UPDATE sessions SET session_class='maintenance',index_policy='metadata_only',maintenance_run_id=NULL,event_count=0,user_message_count=0,assistant_message_count=0 WHERE id=?",[id])?;
            db.execute("DELETE FROM activity_events WHERE session_id=?", [id])?;
            db.execute(
                "DELETE FROM search_index WHERE entity_type='session' AND entity_id=?",
                [id.to_string()],
            )?;
        }
    }
    Ok(())
}
