//! Explicit persisted-only local Sync. Resolver overlays publish after each source commits.
mod queries;
mod report;
mod stream;
use super::{
    catalog,
    common::*,
    evidence::{self, RecognizedAtlassianItemUrl, SyncScopeSnapshot, MAX_SOURCE_EVIDENCE},
    structure_references,
};
use crate::backend::{
    db,
    ingest::{ParsedUrlEvidence, REFERENCE_VERSION, URL_EVIDENCE_VERSION},
    references::{self, UrlLocator},
    BackendError, Result,
};
use report::{inc, ActionReport, SourceResult};
pub use report::{CANDIDATE_SKIP_KEYS, SOURCE_REASON_CODES};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection, OptionalExtension};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::{Mutex, TryLockError},
};
pub use stream::{DocumentScan, DocumentStreamScanner, DocumentUrl, MAX_URL_CODE_POINTS};
pub const SOURCE_BATCH_SIZE: usize = 100;
pub const DOCUMENT_CHUNK_BYTES: usize = 64 * 1024;
static SYNC_LOCK: Mutex<()> = Mutex::new(());
struct Registry {
    scope: evidence::SiteScope,
    source_instances: BTreeMap<(i64, String), Option<i64>>,
    domain_sites: BTreeMap<String, Vec<i64>>,
}
impl From<SyncScopeSnapshot> for Registry {
    fn from(value: SyncScopeSnapshot) -> Self {
        Self {
            scope: value.scope,
            source_instances: value.choices,
            domain_sites: value.domain_sites,
        }
    }
}
impl Registry {
    fn publish(&mut self, result: &SourceResult) {
        for (key, site) in &result.site_scope_updates {
            self.scope.insert(key.clone(), vec![*site]);
        }
        for (domain, site) in &result.domain_site_updates {
            self.domain_sites.insert(domain.clone(), vec![*site]);
        }
    }
}
struct Candidate {
    locator: UrlLocator,
    item: Option<RecognizedAtlassianItemUrl>,
    site_id: Option<i64>,
}
fn unavailable(message: &str) -> BackendError {
    fail("context-unavailable", message)
}
fn resolve_site(
    db: &Connection,
    locator: &UrlLocator,
    registry: &Registry,
    result: &mut SourceResult,
) -> Result<Option<i64>> {
    let domain = locator.normalized_domain.as_ref().unwrap();
    let service = locator.service.as_ref().unwrap();
    let key = (domain.clone(), service.clone());
    let site = if let Some(site) = result.domain_site_updates.get(domain) {
        *site
    } else {
        let domain_sites = registry
            .domain_sites
            .get(domain)
            .cloned()
            .unwrap_or_default()
            .into_iter()
            .collect::<BTreeSet<_>>();
        let mut service_sites = registry
            .scope
            .get(&key)
            .cloned()
            .unwrap_or_default()
            .into_iter()
            .collect::<BTreeSet<_>>();
        if let Some(site) = result.site_scope_updates.get(&key) {
            service_sites = BTreeSet::from([*site]);
        }
        if service_sites.len() > 1 {
            result.skip("ambiguous_site");
            return Ok(None);
        }
        if let Some(site) = service_sites.first() {
            *site
        } else if domain_sites.len() == 1 {
            *domain_sites.first().unwrap()
        } else if domain_sites.len() > 1 {
            result.skip("ambiguous_site");
            return Ok(None);
        } else {
            let site = catalog::register_atlassian_site(
                db,
                &json!({"base_url":locator.canonical_base_url}),
            )?;
            let site = id(&site["id"])?;
            result.domain_site_updates.insert(domain.clone(), site);
            site
        }
    };
    result.site_scope_updates.insert(key, site);
    Ok(Some(site))
}
fn recognize(
    db: &Connection,
    result: &mut SourceResult,
    url: Option<&str>,
    registry: &Registry,
) -> Result<Option<Candidate>> {
    let Some(url) = url else {
        result.skip("unsafe_url");
        return Ok(None);
    };
    let locator = references::describe_atlassian_url(url);
    if ["unsafe", "unsupported"].contains(&locator.kind.as_str()) {
        result.skip(if locator.kind == "unsafe" {
            "unsafe_url"
        } else {
            "unsupported_locator"
        });
        return Ok(None);
    }
    result
        .admitted_urls
        .insert(locator.safe_locator_url.as_ref().unwrap().clone());
    if locator.kind == "site" {
        inc(&mut result.counts, "site_only", 1);
        return Ok(Some(Candidate {
            locator,
            item: None,
            site_id: None,
        }));
    }
    let Some(site) = resolve_site(db, &locator, registry, result)? else {
        return Ok(None);
    };
    if locator.kind == "structure" {
        return Ok(Some(Candidate {
            locator,
            item: None,
            site_id: Some(site),
        }));
    }
    let item = RecognizedAtlassianItemUrl {
        source_instance_id: None,
        site_id: site,
        service: locator.service.as_ref().unwrap().clone(),
        normalized: catalog::NormalizedAtlassianUrl {
            observed_url: trim(url).into(),
            normalized_url: locator.safe_locator_url.as_ref().unwrap().clone(),
            normalized_domain: locator.normalized_domain.as_ref().unwrap().clone(),
            canonical_base_url: locator.canonical_base_url.as_ref().unwrap().clone(),
        },
        observed_remote_id: if locator.item_identity_kind.as_deref() == Some("confluence_page") {
            locator.item_identity.clone()
        } else {
            None
        },
        observed_remote_key: if locator.item_identity_kind.as_deref() == Some("jira_issue") {
            locator.item_identity.clone()
        } else {
            None
        },
        container_structural_scope: None,
        container_label: None,
    };
    Ok(Some(Candidate {
        locator,
        item: Some(item),
        site_id: Some(site),
    }))
}
fn item_for_target(
    db: &Connection,
    item: &RecognizedAtlassianItemUrl,
    url: &str,
    observed: Option<&str>,
    registry: &Registry,
    refresh: bool,
) -> Result<(i64, bool)> {
    let existing=db::row(db,"SELECT id,external_resource_id FROM atlassian_item_urls WHERE site_id=? AND normalized_url=?",params![item.site_id,item.normalized.normalized_url])?;
    if let Some(existing) = existing {
        if refresh {
            db.execute(
                "UPDATE atlassian_item_urls SET observed_url=?,last_observed_at=? WHERE id=?",
                params![
                    url,
                    observed
                        .filter(|s| !s.is_empty())
                        .map(ToOwned::to_owned)
                        .unwrap_or_else(now),
                    id(&existing["id"])?
                ],
            )?;
        }
        return Ok((id(&existing["external_resource_id"])?, false));
    }
    let timestamp = observed
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
        .unwrap_or_else(now);
    let row = catalog::create_or_reuse_atlassian_stub(
        db,
        &json!({"source_instance_id":null,"service":item.service,"site_id":item.site_id,"url":item.normalized.normalized_url,"observed_at":timestamp}),
    )?;
    let resource = id(&row["external_resource_id"])?;
    if url != item.normalized.normalized_url {
        db.execute("UPDATE atlassian_item_urls SET observed_url=?,last_observed_at=? WHERE external_resource_id=? AND site_id=? AND normalized_url=?",params![url,timestamp,resource,item.site_id,item.normalized.normalized_url])?;
    }
    if let Some(source) = registry
        .source_instances
        .get(&(item.site_id, item.service.clone()))
        .copied()
        .flatten()
    {
        db.execute("UPDATE atlassian_items SET source_instance_id=? WHERE external_resource_id=? AND source_instance_id IS NULL",params![source,resource])?;
    }
    Ok((resource, true))
}
struct Location<'a> {
    session: Option<i64>,
    path: Option<&'a str>,
    event: Option<&'a str>,
    document: Option<i64>,
    line: i64,
    ordinal: i64,
    channel: &'a str,
    observed: Option<&'a str>,
}
fn insert_evidence(
    db: &Connection,
    result: &mut SourceResult,
    resource: i64,
    item: &RecognizedAtlassianItemUrl,
    url: &str,
    location: &Location<'_>,
    refresh: bool,
) -> Result<String> {
    let candidate = ParsedUrlEvidence {
        observed_url: url.into(),
        source_line: location.line,
        url_ordinal: location.ordinal,
        source_channel: location.channel.into(),
        source_event_id: location.event.map(Into::into),
        observed_at: location.observed.map(Into::into),
        observed_remote_id: item.observed_remote_id.clone(),
        observed_title: None,
    };
    let key = evidence::atlassian_evidence_key(
        resource,
        location.session,
        location.path,
        location.document,
        &candidate,
        &item.normalized.normalized_url,
        Some(URL_EVIDENCE_VERSION),
    )?;
    if location.session.is_some() {
        let fingerprint = canonical(&json!([
            resource,
            location.session,
            location.path,
            location.event,
            location.line,
            location.ordinal,
            item.normalized.normalized_url,
            location.channel
        ]))?;
        if !result.seen_session_locations.insert(fingerprint) {
            return Ok(key);
        }
    }
    if result.seen_evidence.contains(&key) {
        return Ok(key);
    }
    let existing = if let Some(session) = location.session {
        db::row(db,"SELECT evidence_key FROM atlassian_item_evidence WHERE external_resource_id=? AND session_id=? AND source_path=? AND source_event_id=? AND source_line=? AND url_ordinal=? AND normalized_url=? AND source_channel=? ORDER BY id LIMIT 1",params![resource,session,location.path,location.event,location.line,location.ordinal,item.normalized.normalized_url,location.channel])?
    } else {
        db::row(
            db,
            "SELECT evidence_key FROM atlassian_item_evidence WHERE evidence_key=?",
            [&key],
        )?
    };
    if let Some(existing) = existing {
        let existing = python_string(&existing["evidence_key"]);
        if refresh {
            let timestamp = now();
            db.execute("UPDATE atlassian_item_evidence SET observed_url=?,observed_remote_id=?,observed_at=?,extractor_version=?,last_observed_at=?,updated_at=? WHERE evidence_key=?",params![url,item.observed_remote_id,location.observed,URL_EVIDENCE_VERSION,timestamp,timestamp,existing])?;
        }
        result.seen_evidence.insert(key);
        result.seen_evidence.insert(existing.clone());
        inc(&mut result.counts, "reused_evidence", 1);
        return Ok(existing);
    }
    let timestamp = now();
    db.execute("INSERT INTO atlassian_item_evidence(external_resource_id,session_id,source_path,document_id,source_channel,source_event_id,source_line,url_ordinal,observed_url,normalized_url,observed_remote_id,observed_title,observed_at,extractor_version,evidence_key,first_observed_at,last_observed_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?,?,?,?)",params![resource,location.session,location.path,location.document,location.channel,location.event,location.line,location.ordinal,url,item.normalized.normalized_url,item.observed_remote_id,location.observed,URL_EVIDENCE_VERSION,key,timestamp,timestamp,timestamp])?;
    result.seen_evidence.insert(key.clone());
    inc(&mut result.counts, "new_evidence", 1);
    Ok(key)
}
fn structure_candidate(
    db: &Connection,
    result: &mut SourceResult,
    candidate: &Candidate,
    location: &Location<'_>,
    refresh: bool,
) -> Result<String> {
    let target = structure_references::ensure_structure_reference(
        db,
        candidate.site_id.unwrap(),
        &candidate.locator,
        location.observed,
    )?;
    let reference = id(&target["reference_id"])?;
    if target["created_reference"] == true {
        result.new_structure_reference_ids.insert(reference);
    } else {
        result.reused_structure_reference_ids.insert(reference);
    }
    let evidence = structure_references::insert_or_reuse_structure_reference_evidence(
        db,
        &json!({"reference_id":reference,"safe_locator_url":candidate.locator.safe_locator_url,"container_hint":candidate.locator.container_hint,"session_id":location.session,"source_path":location.path,"source_event_id":location.event,"document_id":location.document,"source_line":location.line,"url_ordinal":location.ordinal,"source_channel":location.channel,"observed_at":location.observed,"refresh_existing":refresh}),
    )?;
    let key = python_string(&evidence["evidence_key"]);
    if evidence["created"] == true {
        result.new_structure_evidence_keys.insert(key.clone());
    } else {
        result.reused_structure_evidence_keys.insert(key.clone());
    }
    result.affected_structure_reference_ids.insert(reference);
    Ok(key)
}
fn valid_location(row: &Value) -> bool {
    truth(&row["source_path"])
        && python_string(&row["source_path"]).chars().count() <= 8_000
        && truth(&row["source_event_id"])
        && python_string(&row["source_event_id"]).chars().count() <= 1_000
        && row["source_line"].as_i64().is_some_and(|n| n > 0)
        && row["evidence_ordinal"].as_i64().is_some_and(|n| n > 0)
}
fn process_session(db: &Connection, session: i64, registry: &Registry) -> Result<SourceResult> {
    atomic(db, "atlassian_local_evidence_source", || {
        let Some(row) = db::row(db, queries::SESSION, [session])? else {
            return Ok(SourceResult::unavailable(
                "session",
                session,
                "unavailable",
                "session-projection-missing",
            ));
        };
        if row["session_class"] != "work"
            || row["session_role"] != "primary"
            || row["index_policy"] != "full"
        {
            return Ok(SourceResult::unavailable(
                "session",
                session,
                "excluded",
                "ineligible-session",
            ));
        }
        let Some(scan) = db::row(db, queries::SESSION_SCAN, [session])? else {
            return Ok(SourceResult::unavailable(
                "session",
                session,
                "unavailable",
                "session-projection-missing",
            ));
        };
        if scan["extractor_version"] != REFERENCE_VERSION {
            return Ok(SourceResult::unavailable(
                "session",
                session,
                "unavailable",
                "session-projection-stale",
            ));
        }
        if scan["status"] == "error" {
            return Ok(SourceResult::unavailable(
                "session",
                session,
                "unavailable",
                "session-projection-error",
            ));
        }
        let partial = scan["status"] == "partial";
        let mut result = SourceResult::new(
            "session",
            session,
            if partial { "partial" } else { "complete" },
        );
        result.scope_limits["session_projection_sources"] = json!(1);
        if partial {
            result.reason("session-projection-partial");
            result.scope_limits["session_reference_overflow"] =
                json!(
                    (id(&scan["observed_target_count"])? - id(&scan["retained_target_count"])?)
                        .max(0)
                );
        }
        for row in db::rows(db, queries::SESSION_EVIDENCE, [session])? {
            if !valid_location(&row) {
                result.skip("invalid_location");
                continue;
            }
            let observed_url = if truth(&row["normalized_url"]) {
                python_string(&row["normalized_url"])
            } else {
                String::new()
            };
            let Some(candidate) = recognize(db, &mut result, Some(&observed_url), registry)? else {
                continue;
            };
            if candidate.locator.kind == "site" {
                continue;
            }
            let path = python_string(&row["source_path"]);
            let event = python_string(&row["source_event_id"]);
            let location = Location {
                session: Some(session),
                path: Some(&path),
                event: Some(&event),
                document: None,
                line: id(&row["source_line"])?,
                ordinal: id(&row["evidence_ordinal"])?,
                channel: if row["evidence_kind"] == "tool_result" {
                    "approved_tool_result"
                } else {
                    "visible_text"
                },
                observed: row["observed_at"].as_str(),
            };
            if candidate.locator.kind == "structure" {
                structure_candidate(db, &mut result, &candidate, &location, false)?;
                continue;
            }
            let item = candidate.item.unwrap();
            let (resource, created) =
                item_for_target(db, &item, &observed_url, location.observed, registry, false)?;
            if created {
                result.new_item_ids.insert(resource);
            } else {
                result.reused_item_ids.insert(resource);
            }
            insert_evidence(
                db,
                &mut result,
                resource,
                &item,
                &item.normalized.normalized_url,
                &location,
                false,
            )?;
        }
        for reference in &result.affected_structure_reference_ids {
            structure_references::project_structure_reference_search(db, *reference)?;
        }
        result.finish();
        Ok(result)
    })
}
fn current_document(db: &Connection, document: i64) -> Result<Option<Value>> {
    db::row(db, queries::CURRENT_DOCUMENT, [document])
}
fn current_scan(db: &Connection, document: i64, fingerprint: &str) -> Result<bool> {
    Ok(
        db::row(db, queries::DOCUMENT_CURRENT_SCAN, [document])?.is_some_and(|row| {
            row["status"] == "ok"
                && row["source_fingerprint"] == fingerprint
                && row["extractor_version"] == URL_EVIDENCE_VERSION
        }),
    )
}
fn read_document(db: &Connection, document: i64) -> Result<DocumentScan> {
    let mut scanner = DocumentStreamScanner::new();
    let mut offset = 1i64;
    let mut pending = vec![];
    loop {
        let chunk:Option<Option<Vec<u8>>>=db.query_row("SELECT substr(CAST(body AS BLOB),?,?) AS body_chunk FROM context_documents WHERE id=?",params![offset,DOCUMENT_CHUNK_BYTES as i64,document],|row|row.get(0)).optional()?;
        let chunk = chunk
            .ok_or_else(|| unavailable("Document disappeared during Sync"))?
            .unwrap_or_default();
        let length = chunk.len();
        offset += length as i64;
        pending.extend(chunk);
        match std::str::from_utf8(&pending) {
            Ok(text) => {
                scanner.feed(text);
                pending.clear();
            }
            Err(error) if error.error_len().is_none() => {
                let valid = error.valid_up_to();
                scanner.feed(std::str::from_utf8(&pending[..valid]).unwrap());
                pending.drain(..valid);
            }
            Err(error) => return Err(fail("source_unicode", error.to_string())),
        }
        if length < DOCUMENT_CHUNK_BYTES {
            break;
        }
    }
    if !pending.is_empty() {
        return Err(fail("source_unicode", "Incomplete UTF-8 in Document"));
    }
    Ok(scanner.finish())
}
fn delete_document_evidence(
    db: &Connection,
    document: i64,
    keys: &BTreeSet<String>,
) -> Result<i64> {
    let mut values = vec![SqlValue::Integer(document)];
    let extra = if keys.is_empty() {
        String::new()
    } else {
        values.extend(keys.iter().cloned().map(SqlValue::Text));
        format!(
            " AND evidence_key NOT IN ({})",
            vec!["?"; keys.len()].join(",")
        )
    };
    let predicate = format!("document_id=?{extra}");
    let count: i64 = db.query_row(
        &format!("SELECT COUNT(*) FROM atlassian_item_evidence WHERE {predicate}"),
        params_from_iter(values.iter()),
        |r| r.get(0),
    )?;
    if count > 0 {
        db.execute(
            &format!("DELETE FROM atlassian_item_evidence WHERE {predicate}"),
            params_from_iter(values.iter()),
        )?;
    }
    Ok(count)
}
fn process_document(
    db: &Connection,
    document: i64,
    registry: &Registry,
    site_fingerprint: &str,
) -> Result<SourceResult> {
    let result =
        atomic(db, "atlassian_local_evidence_source", || {
            let row = current_document(db, document)?
                .ok_or_else(|| unavailable("Document no longer exists"))?;
            if row["context_root_id"].is_null() {
                return Err(unavailable("Document root is unavailable"));
            }
            if !truth(&row["enabled"]) {
                return Ok(SourceResult::unavailable(
                    "document",
                    document,
                    "excluded",
                    "disabled-document",
                ));
            }
            if !truth(&row["readable"]) || row["status"] != "ready" {
                return Err(unavailable("Document root is unavailable"));
            }
            let hash = python_string(&row["content_hash"]);
            let fingerprint = evidence::document_evidence_source_fingerprint(&hash)?;
            let was_current = current_scan(db, document, &fingerprint)?;
            let scan = read_document(db, document)?;
            let current = current_document(db, document)?;
            if current.as_ref().is_none_or(|r| {
                r["context_root_id"].is_null()
                    || !truth(&r["enabled"])
                    || !truth(&r["readable"])
                    || r["status"] != "ready"
                    || python_string(&r["content_hash"]) != hash
            }) {
                return Err(unavailable("Document changed during Sync"));
            }
            let mut result = SourceResult::new(
                "document",
                document,
                if scan.url_overflow > 0 {
                    "partial"
                } else {
                    "complete"
                },
            );
            if scan.url_overflow > 0 {
                result.reason("document-url-limit");
                result.scope_limits["document_url_overflow"] = json!(scan.url_overflow);
            }
            result.candidate_skips["key_only"] = json!(scan.key_only_count);
            let mut retained = BTreeSet::new();
            let mut retained_structure = BTreeSet::new();
            let observed = now();
            for item in scan.candidates {
                let Some(candidate) =
                    recognize(db, &mut result, item.observed_url.as_deref(), registry)?
                else {
                    continue;
                };
                if candidate.locator.kind == "site" {
                    continue;
                }
                if candidate.locator.kind == "structure" {
                    retained_structure.insert(structure_candidate(
                        db,
                        &mut result,
                        &candidate,
                        &Location {
                            session: None,
                            path: None,
                            event: None,
                            document: Some(document),
                            line: item.source_line,
                            ordinal: item.url_ordinal,
                            channel: "visible_text",
                            observed: Some(&observed),
                        },
                        !was_current,
                    )?);
                    continue;
                }
                let recognized = candidate.item.unwrap();
                let url = item.observed_url.as_deref().unwrap();
                let (resource, created) = item_for_target(
                    db,
                    &recognized,
                    url,
                    Some(&observed),
                    registry,
                    !was_current,
                )?;
                if created {
                    result.new_item_ids.insert(resource);
                } else {
                    result.reused_item_ids.insert(resource);
                }
                retained.insert(insert_evidence(
                    db,
                    &mut result,
                    resource,
                    &recognized,
                    url,
                    &Location {
                        session: None,
                        path: None,
                        event: None,
                        document: Some(document),
                        line: item.source_line,
                        ordinal: item.url_ordinal,
                        channel: "visible_text",
                        observed: None,
                    },
                    !was_current,
                )?);
            }
            result.counts["removed_evidence"] =
                json!(delete_document_evidence(db, document, &retained)?);
            let removed = structure_references::remove_obsolete_document_structure_evidence(
                db,
                document,
                &retained_structure,
            )?;
            result
                .removed_structure_evidence_keys
                .extend(serde_json::from_value::<BTreeSet<String>>(
                    removed["evidence_keys"].clone(),
                )?);
            result.affected_structure_reference_ids.extend(
                serde_json::from_value::<BTreeSet<i64>>(removed["reference_ids"].clone())?,
            );
            for reference in &result.affected_structure_reference_ids {
                structure_references::project_structure_reference_search(db, *reference)?;
            }
            if !was_current {
                evidence::record_document_evidence_scan(
                    db,
                    document,
                    &fingerprint,
                    site_fingerprint,
                    Some(URL_EVIDENCE_VERSION),
                )?;
            }
            result.finish();
            Ok(result)
        });
    match result {
        Err(error) if error.code == "context-unavailable" => Ok(SourceResult::unavailable(
            "document",
            document,
            "unavailable",
            "context-unavailable",
        )),
        result => result,
    }
}
pub fn busy_atlassian_local_evidence_report() -> Value {
    report::empty_report("busy")
}
fn source_ids(db: &Connection, table: &str, maximum: i64) -> Result<Vec<i64>> {
    if maximum <= 0 {
        return Ok(vec![]);
    }
    let mut ids = vec![];
    db::scan(
        db,
        &format!("SELECT id FROM {table} WHERE id>0 AND id<=? ORDER BY id"),
        [maximum],
        |row| {
            ids.push(id(&row["id"])?);
            Ok(true)
        },
    )?;
    Ok(ids)
}
pub fn sync_atlassian_local_evidence(db: &Connection) -> Result<Value> {
    let _lease = match SYNC_LOCK.try_lock() {
        Ok(lease) => lease,
        Err(TryLockError::WouldBlock) => return Ok(busy_atlassian_local_evidence_report()),
        Err(TryLockError::Poisoned(error)) => error.into_inner(),
    };
    let mut action = ActionReport::new();
    let result = (|| -> Result<()> {
        let snapshot = evidence::configured_atlassian_sync_scope_snapshot(db)?;
        let site_fingerprint = snapshot.fingerprint.clone();
        let mut registry = Registry::from(snapshot);
        let (sessions, documents) = atomic(db, "atlassian_local_evidence_source", || {
            let max_session: i64 =
                db.query_row("SELECT COALESCE(MAX(id),0) FROM sessions", [], |r| r.get(0))?;
            let max_document: i64 = db.query_row(
                "SELECT COALESCE(MAX(id),0) FROM context_documents",
                [],
                |r| r.get(0),
            )?;
            Ok((
                source_ids(db, "sessions", max_session)?,
                source_ids(db, "context_documents", max_document)?,
            ))
        })?;
        for (kind, ids) in [("session", sessions), ("document", documents)] {
            for batch in ids.chunks(SOURCE_BATCH_SIZE) {
                for local_id in batch {
                    let processed = (|| -> Result<SourceResult> {
                        if db.is_autocommit() {
                            db.execute_batch("BEGIN DEFERRED")?;
                        }
                        if kind == "session" {
                            process_session(db, *local_id, &registry)
                        } else {
                            process_document(db, *local_id, &registry, &site_fingerprint)
                        }
                    })();
                    let mut source = processed.unwrap_or_else(|error| {
                        SourceResult::unavailable(
                            kind,
                            *local_id,
                            "failed",
                            if error.code == "structure-reference-identity-collision" {
                                "identity-collision"
                            } else {
                                "reconciliation-error"
                            },
                        )
                    });
                    if !db.is_autocommit() {
                        if db.execute_batch("COMMIT").is_err() {
                            let _ = db.execute_batch("ROLLBACK");
                            source = SourceResult::unavailable(
                                kind,
                                *local_id,
                                "failed",
                                "reconciliation-error",
                            );
                        } else {
                            registry.publish(&source);
                        }
                    } else {
                        registry.publish(&source);
                    }
                    action.add(source);
                }
            }
        }
        Ok(())
    })();
    if result.is_err() {
        if !db.is_autocommit() {
            let _ = db.execute_batch("ROLLBACK");
        }
        let mut report = action.finish();
        report["status"] = json!("failed");
        return Ok(report);
    }
    Ok(action.finish())
}
