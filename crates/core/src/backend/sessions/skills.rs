use crate::backend::{
    db,
    ingest::{common::stable_id, ParsedSession},
    unicode, Result,
};
use rusqlite::{params, Connection};

pub fn normalized_skill_name(value: &str) -> String {
    unicode::casefold(value.trim_matches(unicode::python_space))
}
pub fn store_skill_observations(
    conn: &Connection,
    source_id: i64,
    provider: &str,
    parsed: &ParsedSession,
) -> Result<usize> {
    if parsed.session_class != "work" {
        conn.execute("UPDATE skill_observations SET state = 'corrected' WHERE source_id = ? AND external_session_id = ? AND state = 'observed'",params![source_id,parsed.external_id])?;
        return Ok(0);
    }
    let mut inserted = 0;
    for item in &parsed.skill_observations {
        let name = item.skill_name.trim_matches(unicode::python_space);
        let native = item.native_event_id.trim_matches(unicode::python_space);
        if name.is_empty()
            || name.chars().count() > 160
            || name.chars().any(|c| (c as u32) < 32)
            || native.is_empty()
            || item.source_line <= 0
        {
            continue;
        }
        let group = normalized_skill_name(name);
        let locator = item
            .skill_locator
            .as_deref()
            .map(|s| s.trim_matches(unicode::python_space))
            .filter(|s| !s.is_empty() && s.chars().count() <= 4096);
        let multiple = ["_read", "_declaration", "_mention", "_script"]
            .iter()
            .any(|s| item.signal_kind.ends_with(s));
        let legacy = if item.signal_kind.ends_with("_mention") && native.starts_with("mention:") {
            format!("declaration:{}", &native[8..])
        } else {
            native.into()
        };
        let existing=db::row(conn,"SELECT id, request_key FROM skill_observations WHERE source_id = ? AND external_session_id = ? AND native_event_id IN (?, ?) AND (? = 0 OR skill_group_key = ?) LIMIT 1",params![source_id,parsed.external_id,native,legacy,multiple,group])?;
        let request = item
            .request_key
            .as_deref()
            .filter(|s| !s.is_empty() && s.chars().count() <= 160);
        if let Some(existing) = existing {
            if existing["request_key"].is_null() && request.is_some() {
                conn.execute(
                    "UPDATE skill_observations SET request_key = ? WHERE id = ?",
                    params![request, existing["id"].as_str()],
                )?;
            }
            continue;
        }
        let version = if item.signal_kind.ends_with("_declaration") {
            "skill-observation-declaration-v1"
        } else if item.signal_kind.ends_with("_mention") || item.signal_kind.ends_with("_script") {
            "skill-observation-reference-v1"
        } else if multiple {
            "skill-observation-read-v1"
        } else {
            "skill-observation-v2"
        };
        let source = source_id.to_string();
        let mut parts = vec![
            version,
            source.as_str(),
            parsed.external_id.as_str(),
            native,
        ];
        if multiple {
            parts.push(&group);
        }
        inserted+=conn.execute("INSERT OR IGNORE INTO skill_observations(id,source_id,provider_kind,external_session_id,native_event_id,skill_name,skill_group_key,skill_locator,signal_kind,source_line,occurred_at,request_key) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",params![stable_id(&parts),source_id,provider,parsed.external_id,native,name,group,locator,item.signal_kind,item.source_line,item.occurred_at,request])?;
    }
    Ok(inserted)
}
pub fn correct_skill_observation(
    conn: &Connection,
    source: i64,
    external: &str,
    native: &str,
) -> Result<usize> {
    Ok(conn.execute("UPDATE skill_observations SET state = 'corrected' WHERE source_id = ? AND external_session_id = ? AND native_event_id = ? AND state = 'observed'",params![source,external,native])?)
}
