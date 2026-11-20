//! Local evidence recognizes registered Site scope and never resolves remote data.
use super::{
    catalog::{self, NormalizedAtlassianUrl},
    common::*,
};
use crate::backend::{
    db,
    ingest::{self, ParsedUrlEvidence},
    references, unicode, Result,
};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use unicode_general_category::{get_general_category, GeneralCategory};
use unicode_normalization::UnicodeNormalization;
pub const MAX_SOURCE_EVIDENCE: usize = 500;
pub const MAX_CONTAINER_HINT_CODE_POINTS: usize = 300;
pub const MAX_STRUCTURAL_SCOPE_CODE_POINTS: usize = 320;
pub const JIRA_CONTAINER_PREFIX: &str = "url:jira:";
pub const CONFLUENCE_CONTAINER_PREFIX: &str = "url:confluence:";
pub type SiteScope = BTreeMap<(String, String), Vec<i64>>;
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecognizedAtlassianItemUrl {
    pub source_instance_id: Option<i64>,
    pub site_id: i64,
    pub service: String,
    pub normalized: NormalizedAtlassianUrl,
    pub observed_remote_id: Option<String>,
    pub observed_remote_key: Option<String>,
    pub container_structural_scope: Option<String>,
    pub container_label: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrictAtlassianItemUrl {
    pub service: String,
    pub normalized: NormalizedAtlassianUrl,
    pub observed_remote_id: Option<String>,
    pub observed_remote_key: Option<String>,
    pub container_structural_scope: Option<String>,
    pub container_label: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrictAtlassianItemUrlResult {
    pub recognized: Option<StrictAtlassianItemUrl>,
    pub reason_code: Option<String>,
    pub normalized_url: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScopedAtlassianItemUrl {
    pub recognized: Option<RecognizedAtlassianItemUrl>,
    pub reason_code: Option<String>,
    pub normalized_url: Option<String>,
}
#[derive(Debug, Clone)]
pub struct SyncScopeSnapshot {
    pub scope: SiteScope,
    pub choices: BTreeMap<(i64, String), Option<i64>>,
    pub fingerprint: String,
    pub domain_sites: BTreeMap<String, Vec<i64>>,
}
fn hash_payload(value: &Value) -> Result<String> {
    Ok(format!(
        "{:x}",
        Sha256::digest(canonical(value)?.as_bytes())
    ))
}
pub fn session_evidence_source_fingerprint(
    source_id: i64,
    source_path: &str,
    size_bytes: i64,
    mtime_ns: i64,
) -> Result<String> {
    hash_payload(
        &json!({"kind":"session","source_id":source_id,"source_path":source_path,"size_bytes":size_bytes,"mtime_ns":mtime_ns}),
    )
}
pub fn document_evidence_source_fingerprint(content_hash: &str) -> Result<String> {
    hash_payload(&json!({"kind":"document","content_hash":content_hash}))
}
const SCOPE_SQL:&str="SELECT atlassian_sites.id AS site_id,scoped_sites.service,atlassian_sites.normalized_domain FROM atlassian_sites JOIN (SELECT atlassian_site_bindings.site_id,external_source_instances.service FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE external_source_instances.enabled=1 UNION SELECT site_id,service FROM atlassian_items UNION SELECT site_id,service FROM atlassian_spaces) AS scoped_sites ON scoped_sites.site_id=atlassian_sites.id ORDER BY atlassian_sites.id,scoped_sites.service";
pub fn configured_atlassian_site_scope_snapshot(db: &Connection) -> Result<(SiteScope, String)> {
    let rows = db::rows(db, SCOPE_SQL, [])?;
    let mut scope = SiteScope::new();
    for row in &rows {
        let ids = scope
            .entry((
                row["normalized_domain"].as_str().unwrap().into(),
                row["service"].as_str().unwrap().into(),
            ))
            .or_default();
        let site = id(&row["site_id"])?;
        if !ids.contains(&site) {
            ids.push(site);
        }
    }
    Ok((scope, hash_payload(&json!(rows))?))
}
pub fn configured_atlassian_site_fingerprint(db: &Connection) -> Result<String> {
    Ok(configured_atlassian_site_scope_snapshot(db)?.1)
}
pub fn configured_atlassian_sync_scope_snapshot(db: &Connection) -> Result<SyncScopeSnapshot> {
    let (scope, fingerprint, rows, sites) = atomic(db, "atlassian_sync_scope_snapshot", || {
        let (scope, fingerprint) = configured_atlassian_site_scope_snapshot(db)?;
        let rows=db::rows(db,"SELECT atlassian_site_bindings.site_id,external_source_instances.service,external_source_instances.id AS source_instance_id FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE external_source_instances.enabled=1 ORDER BY atlassian_site_bindings.site_id,external_source_instances.service,external_source_instances.id",[])?;
        let sites = db::rows(
            db,
            "SELECT id,normalized_domain FROM atlassian_sites ORDER BY normalized_domain,id",
            [],
        )?;
        Ok((scope, fingerprint, rows, sites))
    })?;
    let mut candidates: BTreeMap<(i64, String), Vec<i64>> = BTreeMap::new();
    for row in rows {
        candidates
            .entry((
                id(&row["site_id"])?,
                row["service"].as_str().unwrap().into(),
            ))
            .or_default()
            .push(id(&row["source_instance_id"])?);
    }
    let mut choices = BTreeMap::new();
    for ((_, service), sites) in &scope {
        for site in sites {
            let key = (*site, service.clone());
            let values = candidates.get(&key);
            choices.insert(key, values.filter(|v| v.len() == 1).map(|v| v[0]));
        }
    }
    let mut domain_sites: BTreeMap<String, Vec<i64>> = BTreeMap::new();
    for row in sites {
        domain_sites
            .entry(row["normalized_domain"].as_str().unwrap().into())
            .or_default()
            .push(id(&row["id"])?);
    }
    Ok(SyncScopeSnapshot {
        scope,
        choices,
        fingerprint,
        domain_sites,
    })
}
fn category_c(ch: char) -> bool {
    matches!(
        get_general_category(ch),
        GeneralCategory::Control
            | GeneralCategory::Format
            | GeneralCategory::PrivateUse
            | GeneralCategory::Surrogate
            | GeneralCategory::Unassigned
    )
}
pub fn normalize_atlassian_structural_scope(value: &Value) -> Option<String> {
    if value.is_null() || value == "" {
        return None;
    }
    let normalized = python_string(value);
    if normalized.chars().count() > MAX_STRUCTURAL_SCOPE_CODE_POINTS {
        return None;
    }
    if normalized == "unclassified" {
        return Some(normalized);
    }
    if let Some(key) = normalized.strip_prefix(JIRA_CONTAINER_PREFIX) {
        let key = unicode::uppercase(key);
        if key.chars().count() <= MAX_CONTAINER_HINT_CODE_POINTS
            && matches(r"\A[A-Z][A-Z0-9_]*\z", &key)
        {
            return Some(format!("{JIRA_CONTAINER_PREFIX}{key}"));
        }
        return None;
    }
    if let Some(segment) = normalized.strip_prefix(CONFLUENCE_CONTAINER_PREFIX) {
        let segment = segment.nfkc().collect::<String>();
        if !trim(&segment).is_empty()
            && segment != "."
            && segment != ".."
            && segment.chars().count() <= MAX_CONTAINER_HINT_CODE_POINTS
            && !segment.contains(['/', '\\'])
            && !segment.chars().any(category_c)
        {
            return Some(format!("{CONFLUENCE_CONTAINER_PREFIX}{segment}"));
        }
    }
    None
}
pub fn structural_scope_service(value: Option<&str>) -> Option<&'static str> {
    let value = value?;
    if value.starts_with(JIRA_CONTAINER_PREFIX) {
        Some("jira")
    } else if value.starts_with(CONFLUENCE_CONTAINER_PREFIX) {
        Some("confluence")
    } else {
        None
    }
}
pub fn recognize_strict_atlassian_item_url(url: &str) -> StrictAtlassianItemUrlResult {
    let locator = references::describe_atlassian_url(url);
    if locator.kind == "unsafe" {
        return StrictAtlassianItemUrlResult {
            recognized: None,
            reason_code: Some("unsafe-url".into()),
            normalized_url: None,
        };
    }
    if locator.kind != "item" {
        return StrictAtlassianItemUrlResult {
            recognized: None,
            reason_code: Some("unsupported-locator".into()),
            normalized_url: locator.safe_locator_url,
        };
    }
    let service = locator.service.unwrap();
    let normalized_url = locator.safe_locator_url.unwrap();
    let container_label = references::atlassian_item_container_hint(url);
    let container_structural_scope = container_label.as_ref().map(|s| {
        format!(
            "{}{s}",
            if service == "jira" {
                JIRA_CONTAINER_PREFIX
            } else {
                CONFLUENCE_CONTAINER_PREFIX
            }
        )
    });
    let observed_remote_id = (locator.item_identity_kind.as_deref() == Some("confluence_page"))
        .then(|| locator.item_identity.clone())
        .flatten();
    let observed_remote_key = (locator.item_identity_kind.as_deref() == Some("jira_issue"))
        .then(|| locator.item_identity.clone())
        .flatten();
    StrictAtlassianItemUrlResult {
        recognized: Some(StrictAtlassianItemUrl {
            service,
            normalized: NormalizedAtlassianUrl {
                observed_url: trim(url).into(),
                normalized_url: normalized_url.clone(),
                normalized_domain: locator.normalized_domain.unwrap(),
                canonical_base_url: locator.canonical_base_url.unwrap(),
            },
            observed_remote_id,
            observed_remote_key,
            container_structural_scope,
            container_label,
        }),
        reason_code: None,
        normalized_url: Some(normalized_url),
    }
}
fn scoped(
    locator: StrictAtlassianItemUrl,
    site_id: i64,
    source_instance_id: Option<i64>,
) -> RecognizedAtlassianItemUrl {
    RecognizedAtlassianItemUrl {
        site_id,
        source_instance_id,
        service: locator.service,
        normalized: locator.normalized,
        observed_remote_id: locator.observed_remote_id,
        observed_remote_key: locator.observed_remote_key,
        container_structural_scope: locator.container_structural_scope,
        container_label: locator.container_label,
    }
}
pub fn atlassian_url_container_hint(url: Option<&str>) -> Option<Value> {
    let result = recognize_strict_atlassian_item_url(url.filter(|s| !s.is_empty())?);
    let locator = result.recognized?;
    Some(
        json!({"structural_scope":locator.container_structural_scope?,"label":locator.container_label,"service":locator.service}),
    )
}
pub fn recognize_atlassian_item_url_in_scope(
    url: &str,
    scope: &SiteScope,
) -> ScopedAtlassianItemUrl {
    let strict = recognize_strict_atlassian_item_url(url);
    let Some(locator) = strict.recognized else {
        return ScopedAtlassianItemUrl {
            recognized: None,
            reason_code: strict.reason_code,
            normalized_url: strict.normalized_url,
        };
    };
    let sites = scope
        .get(&(
            locator.normalized.normalized_domain.clone(),
            locator.service.clone(),
        ))
        .map(|v| v.iter().copied().collect::<BTreeSet<_>>())
        .unwrap_or_default();
    let reason = if sites.is_empty() {
        Some("unconfigured-domain")
    } else if sites.len() != 1 {
        Some("ambiguous-site")
    } else {
        None
    };
    ScopedAtlassianItemUrl {
        recognized: if reason.is_none() {
            Some(scoped(locator, *sites.first().unwrap(), None))
        } else {
            None
        },
        reason_code: reason.map(Into::into),
        normalized_url: strict.normalized_url,
    }
}
pub fn recognize_configured_atlassian_item_url(
    db: &Connection,
    url: &str,
) -> Result<Option<RecognizedAtlassianItemUrl>> {
    let Some(locator) = recognize_strict_atlassian_item_url(url).recognized else {
        return Ok(None);
    };
    let sites = db::rows(db,"SELECT DISTINCT atlassian_sites.id AS site_id FROM atlassian_sites JOIN (SELECT atlassian_site_bindings.site_id,external_source_instances.service FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE external_source_instances.enabled=1 UNION SELECT site_id,service FROM atlassian_items UNION SELECT site_id,service FROM atlassian_spaces) AS scoped_sites ON scoped_sites.site_id=atlassian_sites.id WHERE atlassian_sites.normalized_domain=? AND scoped_sites.service=? ORDER BY atlassian_sites.id",params![locator.normalized.normalized_domain,locator.service])?;
    if sites.len() != 1 {
        return Ok(None);
    }
    let site = id(&sites[0]["site_id"])?;
    let access=db::rows(db,"SELECT external_source_instances.id FROM atlassian_site_bindings JOIN external_source_instances ON external_source_instances.id=atlassian_site_bindings.source_instance_id WHERE atlassian_site_bindings.site_id=? AND external_source_instances.service=? AND external_source_instances.enabled=1 ORDER BY external_source_instances.id",params![site,locator.service])?;
    let source = if access.len() == 1 {
        Some(id(&access[0]["id"])?)
    } else {
        None
    };
    Ok(Some(scoped(locator, site, source)))
}
pub fn document_url_evidence(body: &str) -> Vec<ParsedUrlEvidence> {
    let mut result = vec![];
    for (index, line) in unicode::splitlines(body).iter().enumerate() {
        result.extend(ingest::visible_url_evidence(
            line,
            index as i64 + 1,
            None,
            None,
        ));
        if result.len() >= MAX_SOURCE_EVIDENCE {
            result.truncate(MAX_SOURCE_EVIDENCE);
            break;
        }
    }
    result
}
fn predicate(
    session: Option<i64>,
    path: Option<&str>,
    document: Option<i64>,
    scan: bool,
) -> Result<(&'static str, Vec<SqlValue>)> {
    if session.is_some() == document.is_some() {
        return Err(fail(
            "invalid-input",
            if scan {
                "Evidence scan requires exactly one source"
            } else {
                "Evidence requires exactly one source"
            },
        ));
    }
    if let Some(session) = session {
        let path = path.filter(|s| !s.is_empty()).ok_or_else(|| {
            fail(
                "invalid-input",
                if scan {
                    "Session evidence scan requires source_path"
                } else {
                    "Session evidence requires source_path"
                },
            )
        })?;
        Ok((
            "session_id=? AND source_path=?",
            vec![session.into(), path.to_owned().into()],
        ))
    } else {
        Ok(("document_id=?", vec![document.unwrap().into()]))
    }
}
fn scan_row(
    db: &Connection,
    session: Option<i64>,
    path: Option<&str>,
    document: Option<i64>,
) -> Result<Option<Value>> {
    let (predicate, values) = predicate(session, path, document, true)?;
    db::row(
        db,
        &format!("SELECT * FROM atlassian_evidence_scans WHERE {predicate}"),
        params_from_iter(values),
    )
}
pub fn evidence_scan_is_current(
    db: &Connection,
    fingerprint: &str,
    session: Option<i64>,
    path: Option<&str>,
    document: Option<i64>,
) -> Result<bool> {
    let Some(row) = scan_row(db, session, path, document)? else {
        return Ok(false);
    };
    Ok(row["status"] == "ok"
        && row["source_fingerprint"] == fingerprint
        && row["site_fingerprint"] == configured_atlassian_site_fingerprint(db)?
        && row["extractor_version"] == ingest::URL_EVIDENCE_VERSION)
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn record_scan(
    db: &Connection,
    fingerprint: &str,
    site_fingerprint: &str,
    status: &str,
    session: Option<i64>,
    path: Option<&str>,
    document: Option<i64>,
    error: Option<(&str, &str)>,
    version: &str,
) -> Result<()> {
    let existing = scan_row(db, session, path, document)?;
    let now = now();
    let message = error.map(|(_, message)| message.chars().take(500).collect::<String>());
    if let Some(row) = existing {
        db.execute("UPDATE atlassian_evidence_scans SET source_fingerprint=?,site_fingerprint=?,extractor_version=?,status=?,error_code=?,error_message=?,scanned_at=?,updated_at=? WHERE id=?",params![fingerprint,site_fingerprint,version,status,error.map(|(code,_)|code),message,now,now,id(&row["id"]) ?])?;
    } else {
        db.execute("INSERT INTO atlassian_evidence_scans(session_id,source_path,document_id,source_fingerprint,site_fingerprint,extractor_version,status,error_code,error_message,scanned_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",params![session,path,document,fingerprint,site_fingerprint,version,status,error.map(|(code,_)|code),message,now,now])?;
    }
    Ok(())
}
pub fn record_document_evidence_scan(
    db: &Connection,
    document: i64,
    fingerprint: &str,
    site_fingerprint: &str,
    version: Option<&str>,
) -> Result<()> {
    record_scan(
        db,
        fingerprint,
        site_fingerprint,
        "ok",
        None,
        None,
        Some(document),
        None,
        version.unwrap_or(ingest::URL_EVIDENCE_VERSION),
    )
}
pub fn atlassian_evidence_key(
    resource: i64,
    session: Option<i64>,
    path: Option<&str>,
    document: Option<i64>,
    candidate: &ParsedUrlEvidence,
    normalized_url: &str,
    version: Option<&str>,
) -> Result<String> {
    hash_payload(
        &json!({"external_resource_id":resource,"session_id":session,"source_path":path,"document_id":document,"source_channel":candidate.source_channel,"source_event_id":candidate.source_event_id,"source_line":candidate.source_line,"url_ordinal":candidate.url_ordinal,"normalized_url":normalized_url,"extractor_version":version.unwrap_or(ingest::URL_EVIDENCE_VERSION)}),
    )
}
fn reconcile(
    db: &Connection,
    fingerprint: &str,
    candidates: &[ParsedUrlEvidence],
    session: Option<i64>,
    path: Option<&str>,
    document: Option<i64>,
) -> Result<usize> {
    let (where_sql, values) = predicate(session, path, document, false)?;
    let site_fingerprint = configured_atlassian_site_fingerprint(db)?;
    let now = now();
    let result = atomic(db, "atlassian_evidence_reconciliation", || {
        let mut keys = vec![];
        for candidate in candidates.iter().take(MAX_SOURCE_EVIDENCE) {
            let Some(recognized) =
                recognize_configured_atlassian_item_url(db, &candidate.observed_url)?
            else {
                continue;
            };
            let observed = candidate
                .observed_at
                .as_deref()
                .filter(|s| !s.is_empty())
                .unwrap_or(&now);
            let item = catalog::create_or_reuse_atlassian_stub(
                db,
                &json!({"source_instance_id":recognized.source_instance_id,"service":recognized.service,"site_id":recognized.site_id,"url":recognized.normalized.normalized_url,"observed_at":observed}),
            )?;
            let resource = id(&item["external_resource_id"])?;
            if document.is_some() && candidate.observed_url != recognized.normalized.normalized_url
            {
                db.execute("UPDATE atlassian_item_urls SET observed_url=?,last_observed_at=? WHERE external_resource_id=? AND site_id=? AND normalized_url=?",params![candidate.observed_url,observed,resource,recognized.site_id,recognized.normalized.normalized_url])?;
            }
            let key = atlassian_evidence_key(
                resource,
                session,
                path,
                document,
                candidate,
                &recognized.normalized.normalized_url,
                None,
            )?;
            keys.push(key.clone());
            db.execute("INSERT INTO atlassian_item_evidence(external_resource_id,session_id,source_path,document_id,source_channel,source_event_id,source_line,url_ordinal,observed_url,normalized_url,observed_remote_id,observed_title,observed_at,extractor_version,evidence_key,first_observed_at,last_observed_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(evidence_key) DO UPDATE SET observed_url=excluded.observed_url,observed_remote_id=excluded.observed_remote_id,observed_title=excluded.observed_title,observed_at=excluded.observed_at,last_observed_at=excluded.last_observed_at,updated_at=excluded.updated_at",params![resource,session,path,document,candidate.source_channel,candidate.source_event_id,candidate.source_line,candidate.url_ordinal,if document.is_some(){&candidate.observed_url}else{&recognized.normalized.normalized_url},recognized.normalized.normalized_url,candidate.observed_remote_id.as_deref().filter(|s|!s.is_empty()).or(recognized.observed_remote_id.as_deref()),candidate.observed_title,candidate.observed_at,ingest::URL_EVIDENCE_VERSION,key,now,now,now])?;
        }
        let mut values = values.clone();
        let extra = if keys.is_empty() {
            String::new()
        } else {
            values.extend(keys.iter().cloned().map(SqlValue::Text));
            format!(
                " AND evidence_key NOT IN ({})",
                vec!["?"; keys.len()].join(",")
            )
        };
        db.execute(
            &format!("DELETE FROM atlassian_item_evidence WHERE {where_sql}{extra}"),
            params_from_iter(values),
        )?;
        record_scan(
            db,
            fingerprint,
            &site_fingerprint,
            "ok",
            session,
            path,
            document,
            None,
            ingest::URL_EVIDENCE_VERSION,
        )?;
        Ok(keys.len())
    });
    match result {
        Ok(count) => Ok(count),
        Err(error) => {
            // Frozen Python's missing exception-class import broke this intended
            // diagnostic branch. The approved native repair retains rollback and
            // records the bounded failed scan while keeping prior evidence intact.
            let code = if error.code == "database" {
                "evidence-reconciliation-error"
            } else {
                &error.code
            };
            record_scan(
                db,
                fingerprint,
                &site_fingerprint,
                "error",
                session,
                path,
                document,
                Some((code, &error.message)),
                ingest::URL_EVIDENCE_VERSION,
            )?;
            Ok(0)
        }
    }
}
pub fn reconcile_session_evidence(
    db: &Connection,
    session: i64,
    path: &str,
    fingerprint: &str,
    candidates: &[ParsedUrlEvidence],
) -> Result<usize> {
    let row = required_row(
        db,
        "SELECT session_class,session_role,index_policy FROM sessions WHERE id=?",
        [session],
        "not_found",
        "Session not found",
    )?;
    if row["session_class"] != "work"
        || row["session_role"] != "primary"
        || row["index_policy"] != "full"
    {
        db.execute(
            "DELETE FROM atlassian_item_evidence WHERE session_id=? AND source_path=?",
            params![session, path],
        )?;
        db.execute(
            "DELETE FROM atlassian_evidence_scans WHERE session_id=? AND source_path=?",
            params![session, path],
        )?;
        record_scan(
            db,
            fingerprint,
            &configured_atlassian_site_fingerprint(db)?,
            "ok",
            Some(session),
            Some(path),
            None,
            None,
            ingest::URL_EVIDENCE_VERSION,
        )?;
        return Ok(0);
    }
    reconcile(db, fingerprint, candidates, Some(session), Some(path), None)
}
pub fn reconcile_document_evidence(
    db: &Connection,
    document: i64,
    fingerprint: &str,
    body: &str,
) -> Result<usize> {
    if db::row(db,"SELECT context_documents.id FROM context_documents JOIN context_roots ON context_roots.id=context_documents.context_root_id WHERE context_documents.id=? AND context_roots.enabled=1",[document])?.is_none(){clear_document_evidence(db,document)?;return Ok(0);}
    reconcile(
        db,
        fingerprint,
        &document_url_evidence(body),
        None,
        None,
        Some(document),
    )
}
pub fn clear_document_evidence(db: &Connection, document: i64) -> Result<()> {
    db.execute(
        "DELETE FROM atlassian_item_evidence WHERE document_id=?",
        [document],
    )?;
    db.execute(
        "DELETE FROM atlassian_evidence_scans WHERE document_id=?",
        [document],
    )?;
    Ok(())
}
pub fn clear_context_root_evidence(db: &Connection, root: i64) -> Result<()> {
    for row in db::rows(
        db,
        "SELECT id FROM context_documents WHERE context_root_id=?",
        [root],
    )? {
        clear_document_evidence(db, id(&row["id"])?)?;
    }
    Ok(())
}
