use super::common::*;
use crate::backend::{db, Result};
use localbrain_models::Cancellation;
use rusqlite::{Transaction, TransactionBehavior};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, path::Path, time::Duration};
pub const OWNER: &str = "localbrain.session-simulation.v1";
pub const EXTRACTION: &str = "all-message-character-windows-with-session-context.v1";
pub(super) fn status(row: &Value) -> &'static str {
    if row["registered_source_id"].is_null() {
        "excluded-missing-source"
    } else if row["session_class"] != "work" {
        "excluded-maintenance"
    } else if row["session_role"] != "primary" {
        "excluded-subsession"
    } else if row["index_policy"] != "full" {
        "excluded-metadata-only"
    } else {
        "eligible"
    }
}
pub(super) fn date(value: &Value) -> Option<String> {
    value
        .as_str()
        .and_then(|value| timestamp(value).ok())
        .map(|value| value.isoformat())
}
pub fn input_text(title: &str, role: &str, text: &str) -> String {
    format!("Session context: {title}\n{role}: {text}")
}
fn bump(counters: &mut BTreeMap<String, u64>, key: &str, n: u64) {
    *counters.get_mut(key).expect("known coverage counter") += n;
}
pub fn inventory(
    database: &Path,
    chunk_chars: usize,
    visit: impl FnMut(&str, &Value) -> Result<()>,
) -> Result<Value> {
    scan_inventory(database, chunk_chars, None, visit)
}
pub(super) fn scan_inventory(
    database: &Path,
    chunk_chars: usize,
    cancel: Option<&Cancellation>,
    mut visit: impl FnMut(&str, &Value) -> Result<()>,
) -> Result<Value> {
    let check = || cancel.map_or(Ok(()), check_cancel);
    check()?;
    require((128..=16000).contains(&chunk_chars), "INVALID_CHUNK_SIZE")?;
    let mut counters = [
        "total_sessions",
        "eligible_sessions",
        "excluded-maintenance_sessions",
        "excluded-subsession_sessions",
        "excluded-metadata-only_sessions",
        "excluded-missing-source_sessions",
        "excluded_nonmessage_events",
        "message_events",
        "empty_events",
        "unknown_date_events",
        "admitted_characters",
        "chunks",
        "sessions_with_text",
        "sessions_without_text",
    ]
    .into_iter()
    .map(|key| (key.to_owned(), 0u64))
    .collect::<BTreeMap<_, _>>();
    let mut fingerprint = Sha256::new();
    let mut emit = |kind: &str, value: &Value| -> Result<()> {
        check()?;
        fingerprint.update(digest(&json!([kind, value])).as_bytes());
        visit(kind, value)
    };
    let source = read_only_database_with_cancellation(database, Duration::from_secs(600), cancel);
    check()?;
    let source = source?;
    let scanned = db::scan(&source,"SELECT s.id,s.source_id,s.external_id,s.title,s.session_class,s.session_role,s.index_policy,p.id AS registered_source_id FROM sessions s LEFT JOIN sources p ON p.id=s.source_id ORDER BY p.id,s.external_id,s.id",[],|row|{
        let source_id=if row["registered_source_id"].is_null()||row["registered_source_id"]==0{json!(format!("missing-source-{}",row["source_id"]))}else{row["registered_source_id"].clone()};
        let skey=digest(&json!([source_id,row["external_id"]]));let status=status(&row);let title=row["title"].as_str().unwrap_or_default().chars().take(300).collect::<String>();let session=json!({"key":skey,"id":row["id"],"title":title,"status":status});
        bump(&mut counters,"total_sessions",1);bump(&mut counters,&format!("{status}_sessions"),1);emit("session",&session)?;if status!="eligible"{return Ok(true);}
        let mut chunks=0;
        db::scan(&source,"SELECT id,role,event_type,occurred_at,CASE WHEN event_type='message' AND role IN ('user','assistant') THEN length(text) END AS size,CASE WHEN event_type='message' AND role IN ('user','assistant') THEN substr(text,1,65536) END AS prefix FROM activity_events WHERE session_id=? ORDER BY sequence,id",[row["id"].as_i64().unwrap()],|mut event|{
            check()?;
            let mut cached=event.as_object_mut().unwrap().remove("prefix").and_then(|value|value.as_str().map(str::to_owned)).unwrap_or_default().chars().collect::<Vec<_>>();let mut cached_start=0usize;
            if event["event_type"]!="message"||!["user","assistant"].contains(&event["role"].as_str().unwrap_or_default()){bump(&mut counters,"excluded_nonmessage_events",1);return Ok(true);}
            bump(&mut counters,"message_events",1);emit("event",&event)?;let size=event["size"].as_u64().unwrap_or(0) as usize;if size==0{bump(&mut counters,"empty_events",1);return Ok(true);}
            let at=date(&event["occurred_at"]);if at.is_none(){bump(&mut counters,"unknown_date_events",1);}
            for start in (0..size).step_by(chunk_chars){let end=(start+chunk_chars).min(size);if end>cached_start+cached.len(){cached_start=start;let row=db::row(&source,"SELECT substr(text,?,65536) AS text FROM activity_events WHERE id=?",rusqlite::params![start+1,event["id"].as_str()])?;cached=row.as_ref().and_then(|row|row["text"].as_str()).unwrap_or_default().chars().collect();}
                let text=cached[start-cached_start..end-cached_start].iter().collect::<String>();let end=start+text.chars().count();
                let chunk=json!({"key":digest(&json!([skey,event["id"],start,end])),"session_key":skey,"event_id":event["id"],"start":start,"end":end,"content_hash":sha(&text),"input_hash":sha(&input_text(&title,event["role"].as_str().unwrap(),&text)),"role":event["role"],"at":at});emit("chunk",&chunk)?;bump(&mut counters,"admitted_characters",text.chars().count() as u64);chunks+=1;
            }Ok(true)
        })?;
        bump(&mut counters,"chunks",chunks);bump(&mut counters,if chunks>0{"sessions_with_text"}else{"sessions_without_text"},1);Ok(true)
    });
    check()?;
    scanned.map_err(|error| {
        if error.code == "database" {
            failure("DATABASE_UNAVAILABLE")
        } else {
            error
        }
    })?;
    Ok(
        json!({"digest":format!("{:x}",fingerprint.finalize()),"coverage":counters,"extraction":EXTRACTION,"chunk_chars":chunk_chars,"sampled":false}),
    )
}
pub fn inventory_collect(
    database: &Path,
    chunk_chars: usize,
) -> Result<(Value, Vec<Value>, Vec<Value>)> {
    let mut sessions = Vec::new();
    let mut chunks = Vec::new();
    let manifest = inventory(database, chunk_chars, |kind, value| {
        match kind {
            "session" => sessions.push(value.clone()),
            "chunk" => chunks.push(value.clone()),
            _ => {}
        }
        Ok(())
    })?;
    Ok((manifest, sessions, chunks))
}
pub fn source_texts(database: &Path, rows: &[Value]) -> Result<Vec<String>> {
    let source = read_only_database(database, Duration::from_secs(120))?;
    let mut result = Vec::new();
    for chunk in rows {
        let start = chunk["start"]
            .as_i64()
            .ok_or_else(|| failure("SOURCE_CHANGED"))?;
        let end = chunk["end"]
            .as_i64()
            .ok_or_else(|| failure("SOURCE_CHANGED"))?;
        let row=db::row(&source,"SELECT substr(e.text,?,?) AS text,e.role,s.title,s.session_class,s.session_role,s.index_policy,p.id AS registered_source_id,s.external_id FROM activity_events e JOIN sessions s ON s.id=e.session_id JOIN sources p ON p.id=s.source_id WHERE e.id=?",rusqlite::params![start+1,end-start,chunk["event_id"].as_str()])?.ok_or_else(||failure("SOURCE_CHANGED"))?;
        require(
            status(&row) == "eligible"
                && digest(&json!([row["registered_source_id"], row["external_id"]]))
                    == chunk["session_key"]
                && row["text"]
                    .as_str()
                    .is_some_and(|text| sha(text) == chunk["content_hash"]),
            "SOURCE_CHANGED",
        )?;
        let title = row["title"]
            .as_str()
            .unwrap_or_default()
            .chars()
            .take(300)
            .collect::<String>();
        let text = input_text(
            &title,
            row["role"].as_str().unwrap_or_default(),
            row["text"].as_str().unwrap(),
        );
        require(sha(&text) == chunk["input_hash"], "SOURCE_CHANGED")?;
        result.push(text);
    }
    Ok(result)
}
pub(super) fn sync_inventory(
    store: &rusqlite::Connection,
    database: &Path,
    chunk_chars: usize,
    cancel: &Cancellation,
) -> Result<Value> {
    check_cancel(cancel)?;
    let transaction = Transaction::new_unchecked(store, TransactionBehavior::Immediate)?;
    transaction.execute_batch("DELETE FROM chunks; DELETE FROM sessions")?;
    let manifest = scan_inventory(database, chunk_chars, Some(cancel), |kind, value| {
        let table = match kind {
            "session" => "sessions",
            "chunk" => "chunks",
            _ => return Ok(()),
        };
        let object = value.as_object().unwrap();
        let columns = object.keys().cloned().collect::<Vec<_>>().join(",");
        let placeholders = vec!["?"; object.len()].join(",");
        let parameters = object
            .values()
            .map(crate::backend::usage::sql_value)
            .collect::<Result<Vec<_>>>()?;
        transaction.execute(
            &format!("INSERT INTO {table}({columns}) VALUES({placeholders})"),
            rusqlite::params_from_iter(parameters),
        )?;
        Ok(())
    })?;
    transaction.execute(
        "INSERT OR REPLACE INTO meta VALUES ('manifest',?)",
        [serde_json::to_string(&manifest)?],
    )?;
    transaction.execute(
        "DELETE FROM embeddings WHERE input_hash NOT IN (SELECT input_hash FROM chunks)",
        [],
    )?;
    check_cancel(cancel)?;
    transaction.commit()?;
    Ok(manifest)
}
