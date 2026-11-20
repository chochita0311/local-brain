//! URL structure references preserve local evidence authority and archived IDs.
use super::{common::*, evidence::normalize_atlassian_structural_scope};
use crate::backend::{
    db,
    ingest::{REFERENCE_VERSION, URL_EVIDENCE_VERSION},
    references::UrlLocator,
    unicode, Result,
};
use rusqlite::{params, params_from_iter, types::Value as SqlValue, Connection};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use unicode_normalization::UnicodeNormalization;
pub const REFERENCE_AUTHORITY_COPY:&str="Session/Local Context에서 URL 구조만 확인했습니다. Jira 링크/Wiki 문서·등록된 Project/Space·원격 조회 결과가 아닙니다.";
pub const MAX_REFERENCE_EVIDENCE_PREVIEW: i64 = 5;
const PREVIEW_FIELDS: &[&str] = &[
    "id",
    "site_id",
    "service",
    "reference_kind",
    "reference_identity",
    "normalized_domain",
    "entity_kind",
    "entity_id",
    "stable_key",
    "family_label",
    "display_title",
    "canonical_url",
    "canonical_safe_locator",
    "alias_total",
    "evidence_total",
    "lifecycle",
    "availability",
    "provenance",
    "container_kind",
    "container_label",
    "container_service",
    "container_cue",
    "container_structural_scope",
];
pub fn structure_reference_family_label(kind: &str) -> Result<&'static str> {
    match kind {
        "jira_project" => Ok("Jira Project 참조"),
        "jira_board" => Ok("Jira 보드 참조"),
        "jira_filter" => Ok("Jira 필터 참조"),
        "jira_dashboard" => Ok("Jira 대시보드 참조"),
        "jira_service_portal" => Ok("Jira 서비스 포털 참조"),
        "jira_service_project" => Ok("Jira 서비스 Project 참조"),
        "confluence_space" => Ok("Wiki Space 참조"),
        _ => Err(fail(
            "invalid-input",
            "Unsupported Atlassian structure reference kind",
        )),
    }
}
pub fn ensure_structure_reference(
    db: &Connection,
    site: i64,
    locator: &UrlLocator,
    observed_at: Option<&str>,
) -> Result<Value> {
    let valid = locator.kind == "structure"
        && locator.service.is_some()
        && locator.reference_kind.is_some()
        && locator.reference_identity.is_some()
        && locator.safe_locator_url.is_some()
        && locator.normalized_domain.is_some();
    if !valid {
        return Err(fail(
            "invalid-input",
            "A complete structure locator is required",
        ));
    }
    let domain = db::row(
        db,
        "SELECT normalized_domain FROM atlassian_sites WHERE id=?",
        [site],
    )?;
    if domain
        .as_ref()
        .is_none_or(|v| v["normalized_domain"] != *locator.normalized_domain.as_ref().unwrap())
    {
        return Err(fail(
            "invalid-input",
            "Structure locator Site does not match its domain",
        ));
    }
    let reference=db::row(db,"SELECT id FROM atlassian_structure_references WHERE site_id=? AND service=? AND reference_kind=? AND reference_identity=?",params![site,locator.service,locator.reference_kind,locator.reference_identity])?;
    let timestamp = observed_at
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
        .unwrap_or_else(now);
    let created_reference = reference.is_none();
    let reference = if let Some(row) = reference {
        id(&row["id"])?
    } else {
        db.execute("INSERT INTO atlassian_structure_references(site_id,service,reference_kind,reference_identity,created_at,updated_at) VALUES (?,?,?,?,?,?)",params![site,locator.service,locator.reference_kind,locator.reference_identity,timestamp,timestamp])?;
        db.last_insert_rowid()
    };
    let url=db::row(db,"SELECT id,reference_id,url_role FROM atlassian_structure_reference_urls WHERE site_id=? AND safe_locator_url=?",params![site,locator.safe_locator_url])?;
    if url.as_ref().is_some_and(|v| v["reference_id"] != reference) {
        return Err(fail(
            "structure-reference-identity-collision",
            "Safe locator belongs to a different structure reference",
        ));
    }
    let created_url = url.is_none();
    let (url_id, url_role) = if let Some(url) = url {
        (
            id(&url["id"])?,
            url["url_role"].as_str().unwrap().to_owned(),
        )
    } else {
        let canonical=db::row(db,"SELECT 1 FROM atlassian_structure_reference_urls WHERE reference_id=? AND url_role='canonical'",[reference])?.is_some();
        let role = if canonical { "alias" } else { "canonical" };
        db.execute("INSERT INTO atlassian_structure_reference_urls(reference_id,site_id,url_role,safe_locator_url,first_observed_at,last_observed_at) VALUES (?,?,?,?,?,?)",params![reference,site,role,locator.safe_locator_url,timestamp,timestamp])?;
        let url = db.last_insert_rowid();
        if !created_reference {
            touch_structure_reference(db, reference, Some(&timestamp))?;
        }
        (url, role.into())
    };
    Ok(
        json!({"reference_id":reference,"url_id":url_id,"url_role":url_role,"created_reference":created_reference,"created_url":created_url}),
    )
}
pub fn touch_structure_reference_url(
    db: &Connection,
    reference: i64,
    url: &str,
    observed: Option<&str>,
) -> Result<()> {
    let timestamp = observed
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
        .unwrap_or_else(now);
    db.execute("UPDATE atlassian_structure_reference_urls SET last_observed_at=? WHERE reference_id=? AND safe_locator_url=? AND last_observed_at!=?",params![timestamp,reference,url,timestamp])?;
    Ok(())
}
pub fn touch_structure_reference(
    db: &Connection,
    reference: i64,
    changed: Option<&str>,
) -> Result<()> {
    let timestamp = changed
        .filter(|s| !s.is_empty())
        .map(ToOwned::to_owned)
        .unwrap_or_else(now);
    db.execute(
        "UPDATE atlassian_structure_references SET updated_at=? WHERE id=? AND updated_at!=?",
        params![timestamp, reference, timestamp],
    )?;
    Ok(())
}
pub fn structure_reference_evidence_key(v: &Value) -> Result<String> {
    let payload = json!([
        "atlassian-structure-reference-evidence",
        v["reference_id"],
        if !v["session_id"].is_null() {
            "session"
        } else {
            "document"
        },
        v["session_id"],
        v["source_path"],
        v["source_event_id"],
        v["document_id"],
        v["source_channel"],
        v["source_line"],
        v["url_ordinal"],
        v["safe_locator_url"],
        v["container_hint"],
        v["extractor_version"]
            .as_str()
            .unwrap_or(URL_EVIDENCE_VERSION)
    ]);
    Ok(format!(
        "{:x}",
        Sha256::digest(canonical(&payload)?.as_bytes())
    ))
}
pub fn insert_or_reuse_structure_reference_evidence(db: &Connection, v: &Value) -> Result<Value> {
    let reference = id(&v["reference_id"])?;
    let url = v["safe_locator_url"]
        .as_str()
        .ok_or_else(|| fail("invalid-input", "safe_locator_url must be a string"))?;
    let key = structure_reference_evidence_key(v)?;
    let existing = db::row(
        db,
        "SELECT id FROM atlassian_structure_reference_evidence WHERE evidence_key=?",
        [&key],
    )?;
    let timestamp = now();
    if let Some(row) = existing {
        if truth(&v["refresh_existing"]) {
            db.execute("UPDATE atlassian_structure_reference_evidence SET observed_at=?,extractor_version=?,last_observed_at=?,updated_at=? WHERE id=?",params![v["observed_at"].as_str(),URL_EVIDENCE_VERSION,timestamp,timestamp,id(&row["id"]) ?])?;
            touch_structure_reference_url(db, reference, url, Some(&timestamp))?;
            touch_structure_reference(db, reference, Some(&timestamp))?;
        }
        return Ok(json!({"evidence_key":key,"created":false}));
    }
    db.execute("INSERT INTO atlassian_structure_reference_evidence(reference_id,session_id,source_path,document_id,source_channel,source_event_id,source_line,url_ordinal,safe_locator_url,container_hint,observed_at,extractor_version,evidence_key,first_observed_at,last_observed_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",params![reference,v["session_id"].as_i64(),v["source_path"].as_str(),v["document_id"].as_i64(),v["source_channel"].as_str(),v["source_event_id"].as_str(),v["source_line"].as_i64(),v["url_ordinal"].as_i64(),url,v["container_hint"].as_str(),v["observed_at"].as_str(),URL_EVIDENCE_VERSION,key,timestamp,timestamp,timestamp])?;
    touch_structure_reference_url(db, reference, url, Some(&timestamp))?;
    touch_structure_reference(db, reference, Some(&timestamp))?;
    Ok(json!({"evidence_key":key,"created":true}))
}
pub fn remove_obsolete_document_structure_evidence(
    db: &Connection,
    document: i64,
    keys: &BTreeSet<String>,
) -> Result<Value> {
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
    let rows=db::rows(db,&format!("SELECT evidence_key,reference_id FROM atlassian_structure_reference_evidence WHERE {predicate} ORDER BY id"),params_from_iter(values.iter()))?;
    let ids = rows
        .iter()
        .map(|r| id(&r["reference_id"]))
        .collect::<Result<BTreeSet<_>>>()?;
    if !rows.is_empty() {
        db.execute(
            &format!("DELETE FROM atlassian_structure_reference_evidence WHERE {predicate}"),
            params_from_iter(values.iter()),
        )?;
        let timestamp = now();
        for reference in &ids {
            touch_structure_reference(db, *reference, Some(&timestamp))?;
        }
    }
    Ok(
        json!({"evidence_keys":rows.iter().map(|r|r["evidence_key"].as_str().unwrap()).collect::<BTreeSet<_>>(),"reference_ids":ids}),
    )
}
fn available_evidence(db: &Connection, reference: Option<i64>) -> Result<BTreeMap<i64, i64>> {
    let rows=db::rows(db,"SELECT evidence.id,evidence.reference_id FROM atlassian_structure_reference_evidence AS evidence JOIN sessions ON sessions.id=evidence.session_id JOIN session_reference_scans ON session_reference_scans.session_id=sessions.id WHERE evidence.session_id IS NOT NULL AND sessions.session_class='work' AND sessions.session_role='primary' AND sessions.index_policy='full' AND session_reference_scans.extractor_version=? AND session_reference_scans.status IN ('ok','partial') AND (? IS NULL OR evidence.reference_id=?) AND EXISTS (SELECT 1 FROM session_reference_evidence AS projected WHERE projected.session_id=evidence.session_id AND projected.source_path=evidence.source_path AND projected.source_event_id=evidence.source_event_id AND projected.source_line=evidence.source_line AND projected.evidence_ordinal=evidence.url_ordinal AND projected.normalized_url=evidence.safe_locator_url AND projected.extractor_version=? AND ((evidence.source_channel='approved_tool_result' AND projected.evidence_kind='tool_result') OR (evidence.source_channel='visible_text' AND projected.evidence_kind IN ('user_mention','assistant_mention')))) UNION SELECT evidence.id,evidence.reference_id FROM atlassian_structure_reference_evidence AS evidence JOIN context_documents ON context_documents.id=evidence.document_id JOIN context_roots ON context_roots.id=context_documents.context_root_id WHERE evidence.document_id IS NOT NULL AND context_roots.enabled=1 AND context_roots.readable=1 AND context_roots.status='ready' AND (? IS NULL OR evidence.reference_id=?)",params![REFERENCE_VERSION,reference,reference,REFERENCE_VERSION,reference,reference])?;
    rows.into_iter()
        .map(|row| Ok((id(&row["id"])?, id(&row["reference_id"])?)))
        .collect()
}
fn container_projection(service: &str, hint: Option<&str>) -> Value {
    if let Some(hint) = hint {
        if let Some(scope) =
            normalize_atlassian_structural_scope(&json!(format!("url:{service}:{hint}")))
        {
            return json!({"container_kind":"url","container_label":hint,"container_service":service,"container_cue":format!("{} · URL 기준",if service=="jira"{"Jira"}else{"Wiki"}),"container_structural_scope":scope});
        }
    }
    json!({"container_kind":"unclassified","container_label":"소속 미확인","container_service":null,"container_cue":null,"container_structural_scope":"unclassified"})
}
pub fn structure_reference_rows(
    db: &Connection,
    include_archived: bool,
    reference: Option<i64>,
) -> Result<Vec<Value>> {
    let available = available_evidence(db, reference)?
        .into_values()
        .collect::<BTreeSet<_>>();
    let rows=db::rows(db,"SELECT structure_refs.id,structure_refs.site_id,structure_refs.service,structure_refs.reference_kind,structure_refs.reference_identity,structure_refs.created_at,structure_refs.updated_at,sites.normalized_domain,sites.display_name AS site_name,(SELECT safe_locator_url FROM atlassian_structure_reference_urls WHERE reference_id=structure_refs.id AND url_role='canonical' ORDER BY id LIMIT 1) AS canonical_url,(SELECT COUNT(*) FROM atlassian_structure_reference_evidence WHERE reference_id=structure_refs.id) AS evidence_total,(SELECT COUNT(DISTINCT container_hint) FROM atlassian_structure_reference_evidence WHERE reference_id=structure_refs.id) AS hint_count,(SELECT MIN(container_hint) FROM atlassian_structure_reference_evidence WHERE reference_id=structure_refs.id) AS consensus_hint,(SELECT COUNT(*) FROM atlassian_structure_reference_urls WHERE reference_id=structure_refs.id) AS url_total FROM atlassian_structure_references AS structure_refs JOIN atlassian_sites AS sites ON sites.id=structure_refs.site_id WHERE (? IS NULL OR structure_refs.id=?) ORDER BY structure_refs.id",params![reference,reference])?;
    let mut values = vec![];
    for mut row in rows {
        let total = id(&row["evidence_total"])?;
        let lifecycle = if total == 0 { "archived" } else { "active" };
        if lifecycle == "archived" && !include_archived {
            continue;
        }
        let reference = id(&row["id"])?;
        let availability = if lifecycle == "archived" {
            "archived"
        } else if available.contains(&reference) {
            "available"
        } else {
            "unavailable"
        };
        let hint = (row["hint_count"] == 1)
            .then(|| row["consensus_hint"].as_str())
            .flatten();
        let container = container_projection(row["service"].as_str().unwrap(), hint);
        let extra = json!({"entity_kind":"reference","entity_id":reference,"stable_key":format!("reference:{reference}"),"family_label":structure_reference_family_label(row["reference_kind"].as_str().unwrap())?,"display_title":row["reference_identity"],"canonical_safe_locator":row["canonical_url"],"alias_total":(id(&row["url_total"])?-1).max(0),"evidence_total":total,"lifecycle":lifecycle,"availability":availability,"provenance":"URL 기준 · Local evidence"});
        row.as_object_mut()
            .unwrap()
            .extend(extra.as_object().unwrap().clone());
        row.as_object_mut()
            .unwrap()
            .extend(container.as_object().unwrap().clone());
        values.push(row);
    }
    Ok(values)
}
fn evidence_rows(db: &Connection, reference: i64) -> Result<(Vec<Value>, i64)> {
    let total: i64 = db.query_row(
        "SELECT COUNT(*) FROM atlassian_structure_reference_evidence WHERE reference_id=?",
        [reference],
        |r| r.get(0),
    )?;
    let available = available_evidence(db, Some(reference))?;
    let rows=db::rows(db,"SELECT id,CASE WHEN session_id IS NOT NULL THEN 'session' ELSE 'document' END AS source_kind,COALESCE(session_id,document_id) AS local_id,source_channel,source_line,url_ordinal,safe_locator_url,container_hint,substr(observed_at,1,80) AS observed_at,substr(last_observed_at,1,80) AS last_observed_at FROM atlassian_structure_reference_evidence WHERE reference_id=? ORDER BY COALESCE(observed_at,last_observed_at) DESC,id DESC LIMIT ?",params![reference,MAX_REFERENCE_EVIDENCE_PREVIEW])?;
    let mut items = vec![];
    for mut row in rows {
        let key = id(&row["id"])?;
        row.as_object_mut().unwrap().remove("id");
        row["source_available"] = json!(available.contains_key(&key));
        items.push(row);
    }
    Ok((items, total))
}
pub fn structure_reference_preview(db: &Connection, reference: i64) -> Result<Option<Value>> {
    let Some(row) = structure_reference_rows(db, true, Some(reference))?
        .into_iter()
        .find(|row| row["id"] == reference)
    else {
        return Ok(None);
    };
    let (items, total) = evidence_rows(db, reference)?;
    let mut result = json!({});
    for key in PREVIEW_FIELDS {
        result[*key] = row[*key].clone();
    }
    result["authority_copy"] = json!(REFERENCE_AUTHORITY_COPY);
    result["evidence"] = json!({"total":total,"truncated":total>items.len() as i64,"items":items});
    Ok(Some(result))
}
pub fn structure_reference_detail(db: &Connection, reference: i64) -> Result<Option<Value>> {
    structure_reference_preview(db, reference)
}
pub fn project_structure_reference_search(db: &Connection, reference: i64) -> Result<bool> {
    let row = structure_reference_preview(db, reference)?;
    let current=db::rows(db,"SELECT entity_type,entity_id,source_kind,title,body,path FROM search_index WHERE entity_type='atlassian_structure_reference' AND entity_id=? ORDER BY source_kind,title,body,path",[reference.to_string()])?;
    let mut desired = vec![];
    if let Some(row) = row.filter(|v| v["lifecycle"] != "archived") {
        let urls=db::rows(db,"SELECT safe_locator_url FROM atlassian_structure_reference_urls WHERE reference_id=? ORDER BY CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END,id",[reference])?;
        let mut parts = vec![python_string(&row["reference_identity"])];
        parts.extend(urls.iter().map(|v| python_string(&v["safe_locator_url"])));
        desired.push(json!({"entity_type":"atlassian_structure_reference","entity_id":reference.to_string(),"source_kind":format!("atlassian:{}",python_string(&row["service"])),"title":row["family_label"],"body":parts.join("\n"),"path":python_string(&row["canonical_url"])}));
    }
    if current == desired {
        return Ok(false);
    }
    db.execute("DELETE FROM search_index WHERE entity_type='atlassian_structure_reference' AND entity_id=?",[reference.to_string()])?;
    for value in desired {
        db.execute("INSERT INTO search_index(entity_type,entity_id,source_kind,title,body,path) VALUES (?,?,?,?,?,?)",params![value["entity_type"].as_str(),value["entity_id"].as_str(),value["source_kind"].as_str(),value["title"].as_str(),value["body"].as_str(),value["path"].as_str()])?;
    }
    Ok(true)
}
pub fn rebuild_structure_reference_search_index(db: &Connection) -> Result<i64> {
    let rows = db::rows(
        db,
        "SELECT id FROM atlassian_structure_references ORDER BY id",
        [],
    )?;
    db.execute(
        "DELETE FROM search_index WHERE entity_type='atlassian_structure_reference'",
        [],
    )?;
    let mut count = 0;
    for row in rows {
        count += i64::from(project_structure_reference_search(db, id(&row["id"])?)?);
    }
    Ok(count)
}
pub fn normalized_reference_search_value(value: &Value) -> String {
    unicode::casefold(
        &if truth(value) {
            python_string(value)
        } else {
            String::new()
        }
        .nfkc()
        .collect::<String>(),
    )
}
