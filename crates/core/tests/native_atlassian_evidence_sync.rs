//! Complete persisted-only action reports/DB effects and native concurrency/failure probes.
use localbrain_core::backend::{atlassian::evidence_sync as sync, Result};
use rusqlite::Connection;
use serde_json::Value;
#[path = "native_atlassian_support/mod.rs"]
mod support;
#[test]
fn persisted_only_evidence_sync_matches_complete_frozen_action_reports_and_database_effects() {
    let _serial = TESTS.lock().unwrap();
    let cases: Vec<Value> =
        serde_json::from_str(include_str!("native_atlassian_fixtures/evidence_sync.json")).unwrap();
    assert!(!cases.is_empty());
    support::replay(&cases, |db, name, _| -> Result<Value> {
        assert_eq!(name, "sync_atlassian_local_evidence");
        sync::sync_atlassian_local_evidence(db)
    });
}
static TESTS: std::sync::Mutex<()> = std::sync::Mutex::new(());
fn injected() -> Vec<Value> {
    serde_json::from_str(include_str!(
        "native_atlassian_fixtures/evidence_sync_injected.json"
    ))
    .unwrap()
}
fn sql_literal(value: &Value) -> String {
    match value {
        Value::Null => "NULL".into(),
        Value::String(s) => format!("'{}'", s.replace('\'', "''")),
        Value::Number(n) => n.to_string(),
        _ => panic!("not a synthetic SQL scalar"),
    }
}
#[test]
fn real_sqlite_faults_and_triggered_source_mutation_match_frozen_injected_contracts() {
    let _serial = TESTS.lock().unwrap();
    let cases = injected()
        .into_iter()
        .filter(|c| {
            c["injected"].as_array().unwrap().iter().any(|v| {
                matches!(
                    v.as_str(),
                    Some("_read_document_scan" | "register_atlassian_site" | "_process_document")
                )
            })
        })
        .collect::<Vec<_>>();
    assert_eq!(cases.len(), 4);
    for case in cases {
        support::replay(std::slice::from_ref(&case), |db, _, _| {
            let injection = case["injected"].as_array().unwrap();
            if injection.iter().any(|v| v == "register_atlassian_site") {
                let failed = case["expected"]["source_outcomes"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .find(|r| r["outcome"] == "failed")
                    .unwrap()["local_id"]
                    .as_i64()
                    .unwrap();
                db.execute_batch(&format!("CREATE TRIGGER synthetic_source_failure BEFORE INSERT ON atlassian_item_evidence WHEN NEW.document_id={failed} BEGIN SELECT RAISE(ABORT,'synthetic source rollback');END"))?;
            } else if injection.iter().any(|v| v == "_read_document_scan") {
                let failed = case["expected"]["source_outcomes"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .filter(|r| r["outcome"] == "failed")
                    .map(|r| r["local_id"].as_i64().unwrap())
                    .collect::<std::collections::BTreeSet<_>>();
                let bodies = case["before"]["context_documents"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .filter(|r| failed.contains(&r["id"].as_i64().unwrap()))
                    .map(|r| r["body"].as_str().unwrap().as_bytes().to_vec())
                    .collect::<std::collections::BTreeSet<_>>();
                assert_eq!(bodies.len(), failed.len());
                db.create_scalar_function(
                    "substr",
                    3,
                    rusqlite::functions::FunctionFlags::SQLITE_UTF8,
                    move |context| -> rusqlite::Result<Vec<u8>> {
                        let raw = context.get::<Vec<u8>>(0)?;
                        if bodies.contains(&raw) {
                            return Err(rusqlite::Error::UserFunctionError(Box::new(
                                std::io::Error::other("synthetic body read failure"),
                            )));
                        }
                        let start = context.get::<i64>(1)?.saturating_sub(1).max(0) as usize;
                        let length = context.get::<i64>(2)?.max(0) as usize;
                        Ok(raw
                            .get(start..start.saturating_add(length).min(raw.len()))
                            .unwrap_or(&[])
                            .to_vec())
                    },
                )?;
            } else {
                let before = case["before"]["context_documents"].as_array().unwrap();
                let after = case["after"]["context_documents"].as_array().unwrap();
                let inserted = after
                    .iter()
                    .find(|r| !before.iter().any(|old| old["id"] == r["id"]))
                    .unwrap()
                    .as_object()
                    .unwrap();
                let deleted = before
                    .iter()
                    .find(|r| !after.iter().any(|new| new["id"] == r["id"]))
                    .unwrap()["id"]
                    .as_i64()
                    .unwrap();
                let columns = inserted
                    .keys()
                    .map(|k| format!("\"{k}\""))
                    .collect::<Vec<_>>()
                    .join(",");
                let values = inserted
                    .values()
                    .map(sql_literal)
                    .collect::<Vec<_>>()
                    .join(",");
                db.execute_batch(&format!("CREATE TRIGGER synthetic_snapshot_mutation AFTER INSERT ON atlassian_evidence_scans WHEN NEW.document_id={} BEGIN INSERT INTO context_documents({columns}) VALUES ({values}); DELETE FROM context_documents WHERE id={deleted};END",deleted-1))?;
            }
            sync::sync_atlassian_local_evidence(db)
        });
    }
}
fn database() -> Connection {
    let db = Connection::open_in_memory().unwrap();
    db.execute_batch(localbrain_core::backend::db::SCHEMA)
        .unwrap();
    db
}
#[test]
fn nonblocking_single_flight_is_real_and_never_writes_the_busy_connection() {
    let _serial = TESTS.lock().unwrap();
    let db = database();
    let (entered_tx, entered_rx) = std::sync::mpsc::channel();
    let (release_tx, release_rx) = std::sync::mpsc::channel();
    let mut entered = false;
    db.progress_handler(
        1,
        Some(move || {
            if !entered {
                entered = true;
                entered_tx.send(()).unwrap();
                release_rx
                    .recv_timeout(std::time::Duration::from_secs(10))
                    .unwrap();
            }
            false
        }),
    );
    let handle = localbrain_core::backend::worker_thread("synthetic-local-sync")
        .spawn(move || sync::sync_atlassian_local_evidence(&db))
        .unwrap();
    entered_rx
        .recv_timeout(std::time::Duration::from_secs(10))
        .unwrap();
    let other = database();
    let before = other.total_changes();
    let busy = sync::sync_atlassian_local_evidence(&other).unwrap();
    assert_eq!(busy, sync::busy_atlassian_local_evidence_report());
    assert_eq!(other.total_changes(), before);
    release_tx.send(()).unwrap();
    assert_eq!(handle.join().unwrap().unwrap()["status"], "complete");
}
#[test]
fn binding_choice_is_frozen_before_a_real_peer_disables_the_source() {
    use rusqlite::hooks::{AuthAction, AuthContext, Authorization};
    let _serial = TESTS.lock().unwrap();
    let case = injected()
        .into_iter()
        .find(|c| {
            c["case"]
                .as_str()
                .unwrap()
                .ends_with("test_frozen_binding_choice_attaches_only_one_compatible_source")
        })
        .unwrap();
    let temp = tempfile::Builder::new()
        .prefix("lb-atlassian-frozen-binding-")
        .tempdir()
        .unwrap();
    let path = temp.path().join("synthetic.db");
    let db = Connection::open(&path).unwrap();
    db.execute_batch(localbrain_core::backend::db::SCHEMA)
        .unwrap();
    support::restore(&db, &case["before"]);
    let (entered_tx, entered_rx) = std::sync::mpsc::channel();
    let (finished_tx, finished_rx) = std::sync::mpsc::channel();
    let peer = std::thread::spawn(move || {
        let peer = Connection::open(path).unwrap();
        peer.busy_timeout(std::time::Duration::from_millis(500))
            .unwrap();
        entered_rx
            .recv_timeout(std::time::Duration::from_secs(10))
            .unwrap();
        finished_tx.send(peer.execute("UPDATE external_source_instances SET enabled=0 WHERE instance_key='synthetic-jira'",[]).map_err(|e|e.to_string())).unwrap();
    });
    let mut changed = false;
    db.authorizer(Some(move |context: AuthContext<'_>| {
        if !changed
            && matches!(
                context.action,
                AuthAction::Read {
                    table_name: "context_documents",
                    column_name: "content_hash"
                }
            )
        {
            changed = true;
            if entered_tx.send(()).is_err() {
                return Authorization::Deny;
            }
            if !matches!(
                finished_rx.recv_timeout(std::time::Duration::from_secs(10)),
                Ok(Ok(1))
            ) {
                return Authorization::Deny;
            }
        }
        Authorization::Allow
    }));
    let actual = sync::sync_atlassian_local_evidence(&db).unwrap();
    peer.join().unwrap();
    assert_eq!(actual, case["expected"]);
    let rows=localbrain_core::backend::db::rows(&db,"SELECT normalized_url,source_instance_id FROM atlassian_item_urls JOIN atlassian_items ON atlassian_items.external_resource_id=atlassian_item_urls.external_resource_id WHERE url_role='canonical' ORDER BY normalized_url",[]).unwrap();
    let expected = case["after"]["atlassian_items"].as_array().unwrap();
    for row in rows {
        let url = case["after"]["atlassian_item_urls"]
            .as_array()
            .unwrap()
            .iter()
            .find(|v| v["normalized_url"] == row["normalized_url"])
            .unwrap();
        let item = expected
            .iter()
            .find(|v| v["external_resource_id"] == url["external_resource_id"])
            .unwrap();
        assert_eq!(row["source_instance_id"], item["source_instance_id"]);
    }
}
