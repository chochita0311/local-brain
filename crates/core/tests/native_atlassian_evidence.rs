//! Frozen recognizer/evidence/structure calls plus native failure and observer probes.
use localbrain_core::backend::{
    atlassian::{catalog, evidence as e, ingestion::AtlassianIngestion, structure_references as s},
    db,
    ingest::{IngestionObserver, SessionObservation},
    Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::collections::BTreeSet;
#[path = "native_atlassian_support/mod.rs"]
mod support;
fn call(db: &Connection, operation: &str, v: &Value) -> Result<Value> {
    let session = v["session_id"].as_i64();
    let document = v["document_id"].as_i64();
    let path = v["source_path"].as_str();
    let fp = v["source_fingerprint"].as_str().unwrap_or("");
    let reference = v["reference_id"].as_i64().unwrap_or(0);
    match operation {
        "document_evidence_source_fingerprint" => Ok(json!(
            e::document_evidence_source_fingerprint(v["content_hash"].as_str().unwrap())?
        )),
        "reconcile_document_evidence" => Ok(json!(e::reconcile_document_evidence(
            db,
            document.unwrap(),
            fp,
            v["body"].as_str().unwrap()
        )?)),
        "evidence_scan_is_current" => Ok(json!(e::evidence_scan_is_current(
            db, fp, session, path, document
        )?)),
        "clear_context_root_evidence" => {
            e::clear_context_root_evidence(db, v["context_root_id"].as_i64().unwrap())?;
            Ok(Value::Null)
        }
        "recognize_strict_atlassian_item_url" => Ok(serde_json::to_value(
            e::recognize_strict_atlassian_item_url(v["url"].as_str().unwrap()),
        )?),
        "reconcile_session_evidence" => Ok(json!(e::reconcile_session_evidence(
            db,
            session.unwrap(),
            path.unwrap(),
            fp,
            &serde_json::from_value::<Vec<_>>(v["candidates"].clone())?
        )?)),
        "recognize_configured_atlassian_item_url" => Ok(serde_json::to_value(
            e::recognize_configured_atlassian_item_url(db, v["url"].as_str().unwrap())?,
        )?),
        "configured_atlassian_site_fingerprint" => {
            Ok(json!(e::configured_atlassian_site_fingerprint(db)?))
        }
        "atlassian_url_container_hint" => {
            Ok(json!(e::atlassian_url_container_hint(v["url"].as_str())))
        }
        "normalize_atlassian_structural_scope" => {
            Ok(json!(e::normalize_atlassian_structural_scope(&v["value"])))
        }
        "ensure_structure_reference" => s::ensure_structure_reference(
            db,
            v["site_id"].as_i64().unwrap(),
            &serde_json::from_value(v["locator"].clone())?,
            v["observed_at"].as_str(),
        ),
        "insert_or_reuse_structure_reference_evidence" => {
            s::insert_or_reuse_structure_reference_evidence(db, v)
        }
        "project_structure_reference_search" => {
            Ok(json!(s::project_structure_reference_search(db, reference)?))
        }
        "structure_reference_preview" => Ok(json!(s::structure_reference_preview(db, reference)?)),
        "remove_obsolete_document_structure_evidence" => {
            s::remove_obsolete_document_structure_evidence(
                db,
                document.unwrap(),
                &serde_json::from_value(v["retained_keys"].clone())?,
            )
        }
        "structural_scope_service" => Ok(json!(e::structural_scope_service(v["value"].as_str()))),
        other => panic!("unknown captured call {other}"),
    }
}
#[test]
fn complete_recognizer_reconciliation_and_structure_contracts_match_frozen_calls() {
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/evidence.json")).unwrap();
    assert_eq!(cases.len(), 128);
    support::replay(&cases, call);
}
fn database() -> Connection {
    let db = Connection::open_in_memory().unwrap();
    db.execute_batch("PRAGMA foreign_keys=ON").unwrap();
    db.execute_batch(db::SCHEMA).unwrap();
    db
}
#[test]
fn failed_evidence_reconciliation_keeps_prior_facts_and_records_bounded_diagnostic() {
    let db = database();
    db.execute("INSERT INTO external_source_instances(instance_key,provider_kind,service,display_name) VALUES ('synthetic-jira','mcp_gateway','jira','Synthetic')",[]).unwrap();
    let access = db.last_insert_rowid();
    catalog::register_atlassian_site(
        &db,
        &json!({"source_instance_id":access,"base_url":"https://jira.failure.test"}),
    )
    .unwrap();
    db.execute("INSERT INTO sources(provider_kind,name,root_path) VALUES ('codex','Synthetic','/synthetic')",[]).unwrap();
    let source = db.last_insert_rowid();
    db.execute("INSERT INTO sessions(source_id,external_id,source_path,title,session_class,session_role,index_policy) VALUES (?,'synthetic','/synthetic/one.jsonl','Synthetic','work','primary','full')",[source]).unwrap();
    let session = db.last_insert_rowid();
    let candidates = localbrain_core::backend::ingest::visible_url_evidence(
        "https://jira.failure.test/browse/SYN-1",
        1,
        Some("event-1"),
        None,
    );
    assert_eq!(
        e::reconcile_session_evidence(
            &db,
            session,
            "/synthetic/one.jsonl",
            &"a".repeat(64),
            &candidates
        )
        .unwrap(),
        1
    );
    let before = db::rows(&db, "SELECT * FROM atlassian_item_evidence", []).unwrap();
    db.execute_batch(&format!("CREATE TRIGGER synthetic_evidence_failure BEFORE INSERT ON atlassian_item_evidence WHEN NEW.source_line=2 BEGIN SELECT RAISE(ABORT,'{}');END;","실패".repeat(400))).unwrap();
    let mut changed = candidates.clone();
    changed.extend(localbrain_core::backend::ingest::visible_url_evidence(
        "https://jira.failure.test/browse/SYN-2",
        2,
        Some("event-2"),
        None,
    ));
    assert_eq!(
        e::reconcile_session_evidence(
            &db,
            session,
            "/synthetic/one.jsonl",
            &"b".repeat(64),
            &changed
        )
        .unwrap(),
        0
    );
    assert_eq!(
        db::rows(&db, "SELECT * FROM atlassian_item_evidence", []).unwrap(),
        before
    );
    assert_eq!(
        db.query_row::<i64, _, _>("SELECT count(*) FROM atlassian_items", [], |r| r.get(0))
            .unwrap(),
        1
    );
    let scan = db::row(
        &db,
        "SELECT * FROM atlassian_evidence_scans WHERE session_id=?",
        [session],
    )
    .unwrap()
    .unwrap();
    assert_eq!(scan["status"], "error");
    assert_eq!(scan["source_fingerprint"], "b".repeat(64));
    assert_eq!(scan["error_code"], "evidence-reconciliation-error");
    assert_eq!(scan["error_message"].as_str().unwrap().chars().count(), 500);
    assert!(!e::evidence_scan_is_current(
        &db,
        &"b".repeat(64),
        Some(session),
        Some("/synthetic/one.jsonl"),
        None
    )
    .unwrap());
}
#[test]
fn real_observer_tracks_currentness_and_cascade_reprojects_archived_structure() {
    let db = database();
    let observer = AtlassianIngestion::new();
    db.execute("INSERT INTO external_source_instances(instance_key,provider_kind,service,display_name) VALUES ('synthetic-jira','mcp_gateway','jira','Synthetic')",[]).unwrap();
    let access = db.last_insert_rowid();
    let site = catalog::register_atlassian_site(
        &db,
        &json!({"source_instance_id":access,"base_url":"https://jira.observer.test"}),
    )
    .unwrap();
    db.execute("INSERT INTO sources(provider_kind,name,root_path) VALUES ('codex','Synthetic','/synthetic')",[]).unwrap();
    let source = db.last_insert_rowid();
    db.execute("INSERT INTO sessions(source_id,external_id,source_path,title,session_class,session_role,index_policy) VALUES (?,'synthetic','/synthetic/one.jsonl','Synthetic','work','primary','full')",[source]).unwrap();
    let session = db.last_insert_rowid();
    let input = SessionObservation {
        source_id: source,
        session_id: session,
        source_path: "/synthetic/one.jsonl",
        size_bytes: 42,
        mtime_ns: 1,
    };
    assert!(!observer.session_is_current(&db, &input).unwrap());
    let candidates = localbrain_core::backend::ingest::visible_url_evidence(
        "https://jira.observer.test/browse/SYN-1",
        1,
        Some("event-1"),
        None,
    );
    observer.session_indexed(&db, &input, &candidates).unwrap();
    assert!(observer.session_is_current(&db, &input).unwrap());
    let locator = localbrain_core::backend::references::describe_atlassian_url(
        "https://jira.observer.test/projects/SYN",
    );
    let target =
        s::ensure_structure_reference(&db, site["id"].as_i64().unwrap(), &locator, None).unwrap();
    let reference = target["reference_id"].as_i64().unwrap();
    s::insert_or_reuse_structure_reference_evidence(&db,&json!({"reference_id":reference,"safe_locator_url":locator.safe_locator_url,"container_hint":"SYN","session_id":session,"source_path":input.source_path,"source_event_id":"event-2","source_line":2,"url_ordinal":1,"source_channel":"visible_text"})).unwrap();
    assert!(s::project_structure_reference_search(&db, reference).unwrap());
    let snapshot = observer
        .before_owner_deleted(&db, Some(session), None)
        .unwrap();
    assert_eq!(snapshot, json!([reference]));
    db.execute("DELETE FROM sessions WHERE id=?", [session])
        .unwrap();
    observer.after_owner_deleted(&db, snapshot).unwrap();
    assert_eq!(
        s::structure_reference_preview(&db, reference)
            .unwrap()
            .unwrap()["lifecycle"],
        "archived"
    );
    assert_eq!(
        db.query_row::<i64, _, _>(
            "SELECT count(*) FROM search_index WHERE entity_type='atlassian_structure_reference'",
            [],
            |r| r.get(0)
        )
        .unwrap(),
        0
    );
    // Retained Site and structure identity are local memory, not source ownership.
    assert_eq!(
        db.query_row::<i64, _, _>(
            "SELECT count(*) FROM atlassian_structure_references",
            [],
            |r| r.get(0)
        )
        .unwrap(),
        1
    );
    observer
        .session_sources_pruned(&db, source, &BTreeSet::new())
        .unwrap();
}
