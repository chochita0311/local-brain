//! Native observations bind only admitted shared resources, never guessed files.
use super::{queries::posix_normpath, reference_sql as sql};
use crate::backend::{
    db,
    ingest::{ParsedReferenceCandidate, REFERENCE_VERSION},
    now,
    references::{hash_payload, parse_url},
    resources, unicode, BackendError, Config, Result,
};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet, HashMap},
    path::Path,
};

pub const MAX_REFERENCE_TARGETS: usize = 100;
pub const MAX_EVIDENCE_PER_TARGET: usize = 50;
pub const MAX_REFERENCE_CANDIDATES: usize = 5_000;

#[derive(Debug, Clone)]
pub struct SessionReferenceLookup {
    by_normalized_path: HashMap<String, Vec<Value>>,
    by_workspace_name: HashMap<(i64, String), Vec<Value>>,
}
fn absolute(path: &str) -> Result<String> {
    Ok(posix_normpath(&if Path::new(path).is_absolute() {
        path.to_owned()
    } else {
        format!(
            "{}/{}",
            std::env::current_dir()?
                .to_str()
                .ok_or_else(|| BackendError::invalid("unicode", "Current path is not Unicode"))?,
            path
        )
    }))
}
pub fn build_session_reference_lookup(conn: &Connection) -> Result<SessionReferenceLookup> {
    let rows = db::rows(
        conn,
        &format!(
            "{} ORDER BY context_documents.id",
            sql::ELIGIBLE_DOCUMENT_ROWS
        ),
        [],
    )?;
    let mut by_normalized_path: HashMap<String, Vec<Value>> = HashMap::new();
    let mut by_workspace_name: HashMap<(i64, String), Vec<Value>> = HashMap::new();
    for row in rows {
        let path = row["path"].as_str().unwrap();
        by_normalized_path
            .entry(absolute(path)?)
            .or_default()
            .push(row.clone());
        if let Some(workspace) = row["workspace_id"].as_i64() {
            by_workspace_name
                .entry((
                    workspace,
                    Path::new(path)
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .into_owned(),
                ))
                .or_default()
                .push(row);
        }
    }
    Ok(SessionReferenceLookup {
        by_normalized_path,
        by_workspace_name,
    })
}
fn resolve_markdown(
    conn: &Connection,
    config: &Config,
    candidate: &ParsedReferenceCandidate,
    session: &Value,
    source_path: &str,
    lookup: &SessionReferenceLookup,
) -> Result<Option<Value>> {
    let reference = candidate.reference.trim_matches(unicode::python_space);
    if !unicode::lowercase(reference).ends_with(".md") {
        return Ok(None);
    }
    let path = Path::new(reference);
    let normalized = if path.is_absolute() {
        Some(absolute(reference)?)
    } else if reference.contains('/') || reference.starts_with('.') {
        let Some(cwd) = session["cwd_raw"].as_str().filter(|s| !s.is_empty()) else {
            return Ok(None);
        };
        Some(absolute(&format!("{cwd}/{reference}"))?)
    } else {
        None
    };
    let rows = if let Some(normalized) = &normalized {
        lookup.by_normalized_path.get(normalized)
    } else {
        session["workspace_id"]
            .as_i64()
            .and_then(|workspace| lookup.by_workspace_name.get(&(workspace, reference.into())))
    };
    let rows = rows.map(Vec::as_slice).unwrap_or(&[]);
    if rows.len() > 1 {
        return Ok(None);
    }
    let identity = if path.is_absolute() {
        path.file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .into_owned()
    } else {
        reference.into()
    }
    .chars()
    .take(500)
    .collect::<String>();
    let resource = if let Some(row) = rows.first() {
        resources::bind_document(conn, row["id"].as_i64().unwrap(), config)?
    } else {
        let prior = db::rows(
            conn,
            sql::RESOLVE_MARKDOWN_0,
            params![
                session["id"].as_i64(),
                source_path,
                candidate.source_event_id,
                candidate.source_line,
                candidate.evidence_ordinal,
                identity
            ],
        )?;
        let prior = prior
            .iter()
            .filter(|row| {
                if let Some(normalized) = &normalized {
                    row["locator"] == *normalized
                } else {
                    Path::new(row["locator"].as_str().unwrap())
                        .file_name()
                        .is_some_and(|name| name == reference)
                }
            })
            .collect::<Vec<_>>();
        if prior.len() != 1 {
            return Ok(None);
        }
        prior[0]["id"].as_i64().unwrap()
    };
    let key: String = conn.query_row(sql::RESOLVE_MARKDOWN_1, [resource], |row| row.get(0))?;
    Ok(Some(resolved(
        candidate,
        source_path,
        resource,
        &key,
        &identity,
        None,
    )))
}
fn resolved(
    candidate: &ParsedReferenceCandidate,
    path: &str,
    resource: i64,
    key: &str,
    identity: &str,
    url: Option<&str>,
) -> Value {
    json!({"source_path":path,"source_event_id":candidate.source_event_id,"source_line":candidate.source_line,"evidence_ordinal":candidate.evidence_ordinal,"resource_id":resource,"target_key":key,"evidence_kind":candidate.evidence_kind,"read_outcome":candidate.read_outcome,"observed_identity":identity,"normalized_url":url,"tool_name":candidate.tool_name,"tool_call_id":candidate.tool_call_id,"observed_at":candidate.observed_at})
}
fn resolve_candidate(
    conn: &Connection,
    config: &Config,
    candidate: &ParsedReferenceCandidate,
    session: &Value,
    path: &str,
    lookup: &SessionReferenceLookup,
) -> Result<Option<Value>> {
    if candidate.reference_kind == "markdown" {
        return resolve_markdown(conn, config, candidate, session, path, lookup);
    }
    if candidate.reference_kind == "url" {
        let Some(parsed) = parse_url(&candidate.reference) else {
            return Ok(None);
        };
        let id = resources::parsed_url_resource(conn, &parsed)?;
        return Ok(Some(resolved(
            candidate,
            path,
            id,
            &parsed.target_key,
            &parsed.observed_identity,
            Some(&parsed.normalized_url),
        )));
    }
    let Some(resource) =
        resources::resource_by_hint(conn, &candidate.reference_kind, &candidate.reference)?
    else {
        return Ok(None);
    };
    Ok(Some(resolved(
        candidate,
        path,
        resource["id"].as_i64().unwrap(),
        resource["identity_key"].as_str().unwrap(),
        &candidate.reference.chars().take(500).collect::<String>(),
        resource["locator"].as_str(),
    )))
}
pub fn evidence_rank(kind: &str, outcome: Option<&str>) -> u8 {
    match (kind, outcome) {
        ("resource_read", Some("success")) => 0,
        ("resource_read", Some("failure")) => 1,
        ("tool_result", _) => 2,
        ("user_mention", _) => 3,
        _ => 4,
    }
}
fn native_location(item: &Value) -> String {
    if item["evidence_kind"] == "resource_read"
        && item["tool_call_id"].as_str().is_some_and(|s| !s.is_empty())
    {
        format!("call:{}", item["tool_call_id"].as_str().unwrap())
    } else if let Some(event) = item["source_event_id"].as_str().filter(|s| !s.is_empty()) {
        format!("event:{event}")
    } else {
        format!(
            "line:{}:{}",
            item["source_path"].as_str().unwrap(),
            item["source_line"]
        )
    }
}
fn evidence_key(session: i64, item: &Value) -> String {
    hash_payload(
        &json!({"session_id":session,"location":format!("path:{}|{}",item["source_path"].as_str().unwrap(),native_location(item)),"target_key":item["target_key"],"evidence_kind":item["evidence_kind"],"read_outcome":item["read_outcome"],"extractor_version":REFERENCE_VERSION}),
    )
}
fn source_set_fingerprint(
    conn: &Connection,
    session: i64,
    path: &str,
    size: i64,
    mtime: i64,
) -> Result<String> {
    let mut rows = db::rows(conn, sql::SOURCE_SET_FINGERPRINT, params![session, path])?;
    rows.push(json!({"path":path,"size_bytes":size,"mtime_ns":mtime}));
    rows.sort_by(|a, b| a["path"].as_str().cmp(&b["path"].as_str()));
    Ok(hash_payload(&json!(rows)))
}
fn recorded_fingerprint(conn: &Connection, session: i64) -> Result<String> {
    Ok(hash_payload(&json!(db::rows(
        conn,
        sql::RECORDED_SOURCE_SET_FINGERPRINT,
        params![session, REFERENCE_VERSION]
    )?)))
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn record_scan(
    conn: &Connection,
    session: i64,
    fingerprint: &str,
    status: &str,
    observed: i64,
    retained: i64,
    error_code: Option<&str>,
    error: Option<&str>,
) -> Result<()> {
    let now = now();
    conn.execute(
        sql::RECORD_SCAN,
        params![
            session,
            fingerprint,
            REFERENCE_VERSION,
            status,
            observed,
            retained,
            error_code,
            error
                .filter(|s| !s.is_empty())
                .map(|s| s.chars().take(500).collect::<String>()),
            now,
            now
        ],
    )?;
    Ok(())
}
fn atomic<T>(conn: &Connection, name: &str, perform: impl FnOnce() -> Result<T>) -> Result<T> {
    conn.execute_batch(&format!("SAVEPOINT {name}"))?;
    match perform() {
        Ok(result) => {
            conn.execute_batch(&format!("RELEASE {name}"))?;
            Ok(result)
        }
        Err(error) => {
            conn.execute_batch(&format!("ROLLBACK TO {name}; RELEASE {name}"))?;
            Err(error)
        }
    }
}
pub fn session_reference_scan_is_current(conn: &Connection, session: i64) -> Result<bool> {
    let Some(scan) = db::row(conn, sql::SESSION_REFERENCE_SCAN_IS_CURRENT_0, [session])? else {
        return Ok(false);
    };
    if !matches!(scan["status"].as_str(), Some("ok" | "partial"))
        || scan["extractor_version"] != REFERENCE_VERSION
    {
        return Ok(false);
    }
    if db::row(
        conn,
        sql::SESSION_REFERENCE_SCAN_IS_CURRENT_1,
        params![session, REFERENCE_VERSION],
    )?
    .is_none()
    {
        return Ok(false);
    }
    Ok(scan["source_fingerprint"] == recorded_fingerprint(conn, session)?)
}
fn record_error(
    conn: &Connection,
    session: i64,
    fingerprint: &str,
    code: &str,
    error: &str,
) -> Result<()> {
    let prior = db::row(conn, sql::MARK_SESSION_REFERENCE_ERROR, [session])?.unwrap_or(Value::Null);
    record_scan(
        conn,
        session,
        fingerprint,
        "error",
        prior["observed_target_count"].as_i64().unwrap_or(0),
        prior["retained_target_count"].as_i64().unwrap_or(0),
        Some(code),
        Some(error),
    )
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
pub fn reconcile_session_references(
    conn: &Connection,
    config: &Config,
    session: i64,
    path: &str,
    size: i64,
    mtime: i64,
    candidates: &[ParsedReferenceCandidate],
    finalize: bool,
    lookup: Option<&SessionReferenceLookup>,
) -> Result<usize> {
    let row = db::row(conn, sql::RECONCILE_SESSION_REFERENCES_0, [session])?
        .ok_or_else(|| BackendError::invalid("session-reference", "Session not found"))?;
    let fingerprint = source_set_fingerprint(conn, session, path, size, mtime)?;
    if row["session_class"] != "work"
        || row["session_role"] != "primary"
        || row["index_policy"] != "full"
    {
        conn.execute(sql::RECONCILE_SESSION_REFERENCES_1, [session])?;
        conn.execute(sql::RECONCILE_SESSION_REFERENCES_2, [session])?;
        return Ok(0);
    }
    let result = atomic(conn, "session_reference_reconciliation", || {
        let own_lookup = if lookup.is_none() {
            Some(build_session_reference_lookup(conn)?)
        } else {
            None
        };
        let lookup = lookup.or(own_lookup.as_ref()).unwrap();
        for candidate in candidates
            .iter()
            .take(MAX_REFERENCE_CANDIDATES)
            .filter(|v| v.reference_kind == "url")
        {
            if let Some(url) = parse_url(&candidate.reference) {
                resources::parsed_url_resource(conn, &url)?;
            }
        }
        let mut resolved = Vec::new();
        let mut seen = BTreeSet::new();
        for candidate in candidates.iter().take(MAX_REFERENCE_CANDIDATES) {
            if let Some(item) = resolve_candidate(conn, config, candidate, &row, path, lookup)? {
                let key = evidence_key(session, &item);
                if seen.insert(key.clone()) {
                    resolved.push((key, item));
                }
            }
        }
        let prior = db::rows(
            conn,
            sql::RECONCILE_SESSION_REFERENCES_3,
            params![session, path],
        )?
        .into_iter()
        .map(|v| {
            (
                v["evidence_key"].as_str().unwrap().to_owned(),
                v["first_observed_at"].clone(),
            )
        })
        .collect::<HashMap<_, _>>();
        conn.execute(sql::RECONCILE_SESSION_REFERENCES_4, params![session, path])?;
        let timestamp = now();
        for (key, item) in &resolved {
            conn.execute(
                sql::RECONCILE_SESSION_REFERENCES_5,
                params![
                    session,
                    path,
                    item["source_event_id"].as_str(),
                    item["source_line"].as_i64(),
                    item["evidence_ordinal"].as_i64(),
                    item["resource_id"].as_i64(),
                    item["target_key"].as_str(),
                    item["evidence_kind"].as_str(),
                    item["read_outcome"].as_str(),
                    item["observed_identity"].as_str(),
                    item["normalized_url"].as_str(),
                    item["tool_name"].as_str(),
                    item["tool_call_id"].as_str(),
                    item["observed_at"].as_str(),
                    REFERENCE_VERSION,
                    key,
                    prior.get(key).and_then(Value::as_str).unwrap_or(&timestamp),
                    timestamp,
                    timestamp
                ],
            )?;
        }
        Ok(resolved.len())
    });
    let result = result.and_then(|count| {
        if finalize {
            finalize_session_references(conn, session, Some(&fingerprint))
        } else {
            Ok(count)
        }
    });
    match result {
        Ok(count) => Ok(count),
        Err(error) => {
            record_error(
                conn,
                session,
                &fingerprint,
                "reference-reconciliation-error",
                &error.to_string(),
            )?;
            Err(error)
        }
    }
}
pub fn finalize_session_references(
    conn: &Connection,
    session: i64,
    fingerprint: Option<&str>,
) -> Result<usize> {
    let fingerprint = match fingerprint.filter(|s| !s.is_empty()) {
        Some(value) => value.to_owned(),
        None => recorded_fingerprint(conn, session)?,
    };
    let result = atomic(conn, "session_reference_finalization", || {
        let rows = db::rows(conn, sql::FINALIZE_SESSION_REFERENCES_0, [session])?;
        let mut ranks: BTreeMap<String, u8> = BTreeMap::new();
        for row in &rows {
            let rank = evidence_rank(
                row["evidence_kind"].as_str().unwrap(),
                row["read_outcome"].as_str(),
            );
            ranks
                .entry(row["target_key"].as_str().unwrap().into())
                .and_modify(|old| *old = rank.min(*old))
                .or_insert(rank);
        }
        let mut ordered = ranks.into_iter().collect::<Vec<_>>();
        ordered.sort_by(|a, b| (a.1, &a.0).cmp(&(b.1, &b.0)));
        let observed = ordered.len();
        let retained = ordered
            .into_iter()
            .take(MAX_REFERENCE_TARGETS)
            .map(|v| v.0)
            .collect::<BTreeSet<_>>();
        if retained.is_empty() {
            conn.execute(sql::FINALIZE_SESSION_REFERENCES_2, [session])?;
        } else {
            let query = sql::FINALIZE_SESSION_REFERENCES_1
                .replace("{}", &vec!["?"; retained.len()].join(","));
            let args = std::iter::once(SqlValue::Integer(session))
                .chain(retained.iter().cloned().map(SqlValue::Text));
            conn.execute(&query, params_from_iter(args))?;
        }
        let mut by_target: BTreeMap<&str, Vec<&Value>> = BTreeMap::new();
        for row in &rows {
            if retained.contains(row["target_key"].as_str().unwrap()) {
                by_target
                    .entry(row["target_key"].as_str().unwrap())
                    .or_default()
                    .push(row);
            }
        }
        let mut excess = Vec::new();
        for mut group in by_target.into_values() {
            group.sort_by_key(|row| {
                (
                    evidence_rank(
                        row["evidence_kind"].as_str().unwrap(),
                        row["read_outcome"].as_str(),
                    ),
                    row["source_path"].as_str().unwrap(),
                    row["source_event_id"].as_str().unwrap_or(""),
                    row["source_line"].as_i64().unwrap(),
                    row["evidence_ordinal"].as_i64().unwrap(),
                    row["tool_call_id"].as_str().unwrap_or(""),
                    row["id"].as_i64().unwrap(),
                )
            });
            excess.extend(
                group
                    .into_iter()
                    .skip(MAX_EVIDENCE_PER_TARGET)
                    .map(|row| row["id"].as_i64().unwrap()),
            );
        }
        if !excess.is_empty() {
            conn.execute(
                &sql::FINALIZE_SESSION_REFERENCES_3
                    .replace("{}", &vec!["?"; excess.len()].join(",")),
                params_from_iter(excess),
            )?;
        }
        let retained: i64 =
            conn.query_row(sql::FINALIZE_SESSION_REFERENCES_4, [session], |row| {
                row.get(0)
            })?;
        record_scan(
            conn,
            session,
            &fingerprint,
            if observed > MAX_REFERENCE_TARGETS {
                "partial"
            } else {
                "ok"
            },
            observed as i64,
            retained,
            None,
            None,
        )?;
        Ok(retained as usize)
    });
    if let Err(error) = &result {
        record_error(
            conn,
            session,
            &fingerprint,
            "reference-finalization-error",
            &error.to_string(),
        )?;
    }
    result
}
pub fn clear_session_reference_source(conn: &Connection, session: i64, path: &str) -> Result<()> {
    conn.execute(
        sql::CLEAR_SESSION_REFERENCE_SOURCE_0,
        params![session, path],
    )?;
    conn.execute(sql::CLEAR_SESSION_REFERENCE_SOURCE_1, [session])?;
    Ok(())
}
pub fn mark_session_reference_error(conn: &Connection, session: i64, error: &str) -> Result<()> {
    record_error(
        conn,
        session,
        &recorded_fingerprint(conn, session)?,
        "reference-source-error",
        error,
    )
}
fn location_count(rows: impl IntoIterator<Item = Value>) -> usize {
    rows.into_iter()
        .map(|row| native_location(&row))
        .collect::<BTreeSet<_>>()
        .len()
}
fn occurrence_key(row: &Value) -> (u8, String, String, i64, i64, String) {
    let at = row["observed_at"].as_str().unwrap_or("");
    (
        u8::from(at.is_empty()),
        at.into(),
        row["source_path"].as_str().unwrap().into(),
        row["source_line"].as_i64().unwrap(),
        row["evidence_ordinal"].as_i64().unwrap(),
        row["target_key"].as_str().unwrap().into(),
    )
}
pub fn session_reference_projection(conn: &Connection, session: i64) -> Result<Value> {
    let scan = db::row(conn, sql::SESSION_REFERENCE_PROJECTION_0, [session])?;
    let mut grouped: BTreeMap<String, Vec<Value>> = BTreeMap::new();
    for row in db::rows(conn, sql::SESSION_REFERENCE_PROJECTION_1, [session])? {
        grouped
            .entry(row["target_key"].as_str().unwrap().into())
            .or_default()
            .push(row);
    }
    let mut items = Vec::new();
    for mut rows in grouped.into_values() {
        let first = rows
            .iter()
            .min_by_key(|row| occurrence_key(row))
            .unwrap()
            .clone();
        rows.sort_by_key(|row| {
            (
                evidence_rank(
                    row["evidence_kind"].as_str().unwrap(),
                    row["read_outcome"].as_str(),
                ),
                row["source_path"].as_str().unwrap().to_owned(),
                row["source_line"].as_i64().unwrap(),
                row["evidence_ordinal"].as_i64().unwrap(),
            )
        });
        let strongest = &rows[0];
        let mut evidence = Vec::new();
        let successful = rows
            .iter()
            .filter(|row| {
                row["evidence_kind"] == "resource_read" && row["read_outcome"] == "success"
            })
            .cloned()
            .collect::<Vec<_>>();
        let failed = rows
            .iter()
            .filter(|row| {
                row["evidence_kind"] == "resource_read" && row["read_outcome"] == "failure"
            })
            .cloned()
            .collect::<Vec<_>>();
        if !successful.is_empty() {
            evidence.push(json!({"kind":"resource_read","outcome":"success","count":location_count(successful)}));
        } else if !failed.is_empty() {
            evidence.push(
                json!({"kind":"resource_read","outcome":"failure","count":location_count(failed)}),
            );
        }
        for kind in ["tool_result", "user_mention", "assistant_mention"] {
            let matching = rows
                .iter()
                .filter(|row| row["evidence_kind"] == kind)
                .cloned()
                .collect::<Vec<_>>();
            if !matching.is_empty() {
                evidence.push(json!({"kind":kind,"outcome":null,"count":location_count(matching)}));
            }
        }
        let is_url = strongest["resource_kind"] == "url";
        let available = !strongest["context_document_id"].is_null()
            && strongest["document_enabled"] == 1
            && strongest["document_readable"] == 1
            && strongest["document_status"] == "ready";
        let destination = if is_url {
            strongest["normalized_url"]
                .as_str()
                .filter(|s| !s.is_empty())
                .map(|s| json!(s))
                .unwrap_or_else(|| strongest["locator"].clone())
        } else if available {
            json!(format!("/documents/{}", strongest["context_document_id"]))
        } else {
            Value::Null
        };
        let rank = evidence.first().map_or(5, |v| {
            evidence_rank(v["kind"].as_str().unwrap(), v["outcome"].as_str())
        });
        let item = json!({"target_key":strongest["target_key"],"target_kind":if is_url{"url"}else{"context_document"},"resource_id":strongest["resource_id"],"product":strongest["product"],"locator":strongest["locator"],"relative_path":strongest["relative_path"],"context_document_id":strongest["context_document_id"],"identity":strongest["observed_identity"],"destination":destination,"observed_at":first["observed_at"],"evidence":evidence,"rank":rank});
        items.push((occurrence_key(&first), item));
    }
    items.sort_by(|a, b| a.0.cmp(&b.0));
    let items = items.into_iter().map(|(_, item)| item).collect::<Vec<_>>();
    let count = items.len();
    let scan = scan.unwrap_or(Value::Null);
    Ok(
        json!({"state":scan["status"].as_str().unwrap_or("ok"),"observed_total":scan["observed_target_count"].as_u64().unwrap_or(count as u64),"retained_total":count,"partial":scan["status"]=="partial","stale":scan["status"]=="error","items":items}),
    )
}
