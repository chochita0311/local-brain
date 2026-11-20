use localbrain_core::backend::{
    db,
    workflow::{assertions::*, focus::*},
};
use rusqlite::Connection;
use serde_json::{json, Value};

fn database() -> Connection {
    let all: Value = serde_json::from_str(include_str!(
        "../src/backend/workflow/fixtures/focus-golden.json"
    ))
    .unwrap();
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection.execute_batch("PRAGMA foreign_keys=OFF").unwrap();
    connection
        .execute_batch(all["cases"][1]["setup_sql"].as_str().unwrap())
        .unwrap();
    connection.execute_batch("PRAGMA foreign_keys=ON").unwrap();
    connection
}
fn key(projection: &WorkflowFocusProjection, id: i64) -> String {
    projection
        .episodes
        .iter()
        .find(|view| view.episode.session_id == id)
        .unwrap()
        .episode
        .episode_key
        .clone()
}
fn request(
    projection: &WorkflowFocusProjection,
    action: &str,
    source: i64,
    target: Option<i64>,
) -> Value {
    json!({"assertion_kind":action,"source_episode_key":key(projection,source),"target_episode_key":target.map(|id|key(projection,id)),"expected_revision":projection.assertion_revision,"created_at":"2026-09-15T01:00:00Z"})
}
fn count(connection: &Connection) -> i64 {
    connection
        .query_row("SELECT COUNT(*) FROM workflow_assertions", [], |row| {
            row.get(0)
        })
        .unwrap()
}
#[test]
fn split_same_flow_undo_chain_is_append_only_and_keeps_base_provenance() {
    let connection = database();
    let projection = workflow_focus_projection(&connection, 11).unwrap();
    let split = apply_workflow_assertion(
        &connection,
        &projection,
        &request(&projection, "split-here", 10, Some(11)),
    )
    .unwrap();
    assert_eq!(split.assertion["boundary_version"], 1);
    assert_eq!(split.assertion["before_meaning"], "relation:continues");
    assert_eq!(split.assertion["after_meaning"], "relation:branches-from");
    assert_eq!(split.projection.base_relations, projection.relations);
    let source = key(&projection, 10);
    let target = key(&projection, 11);
    let relation = split
        .projection
        .relations
        .iter()
        .find(|r| r.source_episode_key == source && r.target_episode_key == target)
        .unwrap();
    assert_eq!(relation.kind, "branches-from");
    assert_eq!(relation.authority, "user-confirmed");
    assert_eq!(relation.reasons[0].identity, "assertion:1");
    let undone=undo_workflow_assertion(&connection,&split.projection,&json!({"assertion_id":1,"expected_revision":split.projection.assertion_revision,"created_at":"2026-09-15T02:00:00Z"})).unwrap();
    assert_eq!(undone.assertion["is_undo"], 1);
    assert_eq!(undone.projection.relations, projection.relations);
    assert_eq!(count(&connection), 2);
    let redone=undo_workflow_assertion(&connection,&undone.projection,&json!({"assertion_id":2,"expected_revision":undone.projection.assertion_revision,"created_at":"2026-09-15T03:00:00Z"})).unwrap();
    assert_eq!(count(&connection), 3);
    assert_eq!(redone.projection.assertions[0]["restored_assertion_id"], 1);
    assert_eq!(redone.projection.assertions[0]["is_undo"], true);
    let relation = redone
        .projection
        .relations
        .iter()
        .find(|r| r.source_episode_key == source && r.target_episode_key == target)
        .unwrap();
    assert_eq!(relation.kind, "branches-from");
    assert_eq!(relation.authority, "user-confirmed");
    assert_eq!(relation.reasons[0].identity, "assertion:3");
    let history = workflow_assertion_history(
        &connection,
        split.assertion["boundary_key"].as_str().unwrap(),
        2,
    )
    .unwrap();
    assert_eq!(history["observed_total"], 3);
    assert_eq!(history["retained_total"], 2);
    assert_eq!(history["partial"], true);
    assert_eq!(history["active_assertion_id"], 3);
}
#[test]
fn supersession_requires_both_current_projection_and_exact_active_record() {
    let connection = database();
    let projection = workflow_focus_projection(&connection, 11).unwrap();
    let first = apply_workflow_assertion(
        &connection,
        &projection,
        &request(&projection, "split-here", 10, Some(11)),
    )
    .unwrap();
    assert_eq!(
        apply_workflow_assertion(
            &connection,
            &projection,
            &request(&projection, "same-flow", 10, Some(11))
        )
        .unwrap_err()
        .code,
        "conflict"
    );
    let mut args = request(&first.projection, "same-flow", 10, Some(11));
    assert_eq!(
        apply_workflow_assertion(&connection, &first.projection, &args)
            .unwrap_err()
            .code,
        "conflict"
    );
    args["expected_active_assertion_id"] = json!(1);
    let second = apply_workflow_assertion(&connection, &first.projection, &args).unwrap();
    assert_eq!(second.assertion["supersedes_assertion_id"], 1);
    assert_eq!(second.assertion["boundary_version"], 2);
    let mut duplicate = request(&second.projection, "same-flow", 10, Some(11));
    duplicate["expected_active_assertion_id"] = json!(2);
    let error = apply_workflow_assertion(&connection, &second.projection, &duplicate).unwrap_err();
    assert_eq!(error.code, "duplicate-active");
    assert_eq!(error.status, 409);
    assert_eq!(
        undo_workflow_assertion(
            &connection,
            &second.projection,
            &json!({"assertion_id":1,"expected_revision":second.projection.assertion_revision})
        )
        .unwrap_err()
        .code,
        "assertion-not-active"
    );
    assert_eq!(count(&connection), 2);
}
#[test]
fn close_reason_correction_and_reopen_preserve_every_revision() {
    let connection = database();
    let projection = workflow_focus_projection(&connection, 12).unwrap();
    let mut args = request(&projection, "close", 12, None);
    args["close_reason"] = json!("completed");
    args["note"] = json!("  Synthetic closure  ");
    let closed = apply_workflow_assertion(&connection, &projection, &args).unwrap();
    assert_eq!(closed.assertion["note"], "Synthetic closure");
    assert_eq!(
        closed
            .projection
            .episodes
            .iter()
            .find(|v| v.episode.session_id == 12)
            .unwrap()
            .episode
            .lifecycle_state,
        "closed"
    );
    let mut args = request(&closed.projection, "close", 12, None);
    args["close_reason"] = json!("abandoned");
    args["expected_active_assertion_id"] = json!(1);
    let corrected = apply_workflow_assertion(&connection, &closed.projection, &args).unwrap();
    assert_eq!(corrected.assertion["before_closure_reason"], "completed");
    assert_eq!(corrected.assertion["after_closure_reason"], "abandoned");
    let mut args = request(&corrected.projection, "reopen", 12, None);
    args["expected_active_assertion_id"] = json!(2);
    let reopened = apply_workflow_assertion(&connection, &corrected.projection, &args).unwrap();
    let episode = &reopened
        .projection
        .episodes
        .iter()
        .find(|v| v.episode.session_id == 12)
        .unwrap()
        .episode;
    assert_eq!(episode.lifecycle_state, "open");
    assert_eq!(episode.closure_reason, None);
    assert_eq!(episode.authority, "user-confirmed");
    assert_eq!(count(&connection), 3);
}
#[test]
fn invalid_consequences_and_notes_never_append_history() {
    let connection = database();
    let projection = workflow_focus_projection(&connection, 11).unwrap();
    for (action, source, target, reason, code) in [
        ("close", 10, None, Some("completed"), "not-tip"),
        ("close", 12, None, None, "invalid-close-reason"),
        ("reopen", 12, None, None, "requires-active-closure"),
        ("same-flow", 10, Some(10), None, "self-relation"),
        ("same-flow", 12, Some(10), None, "non-forward-time"),
        ("merge-into", 12, Some(10), None, "merge-before-source"),
        ("same-flow", 10, Some(12), None, "contradictory-boundary"),
        ("invented", 10, None, None, "invalid-action"),
    ] {
        let mut args = request(&projection, action, source, target);
        if let Some(reason) = reason {
            args["close_reason"] = json!(reason);
        }
        let error = apply_workflow_assertion(&connection, &projection, &args).unwrap_err();
        assert_eq!(error.code, code);
        assert_eq!(count(&connection), 0);
    }
    for value in [json!(true), json!("N".repeat(1001))] {
        let mut args = request(&projection, "same-flow", 10, Some(11));
        args["note"] = value;
        assert_eq!(
            apply_workflow_assertion(&connection, &projection, &args)
                .unwrap_err()
                .code,
            "invalid-note"
        );
        assert_eq!(count(&connection), 0);
    }
}
#[test]
fn savepoint_failure_rolls_back_and_never_commits_callers_transaction() {
    let connection = database();
    connection.execute_batch("BEGIN").unwrap();
    let projection = workflow_focus_projection(&connection, 11).unwrap();
    let result = apply_workflow_assertion(
        &connection,
        &projection,
        &request(&projection, "split-here", 10, Some(11)),
    )
    .unwrap();
    assert_eq!(count(&connection), 1);
    assert!(!connection.is_autocommit());
    connection.execute_batch("ROLLBACK").unwrap();
    assert_eq!(count(&connection), 0);
    connection.execute_batch("CREATE TRIGGER synthetic_assertion_failure BEFORE INSERT ON workflow_assertions BEGIN SELECT RAISE(ABORT,'synthetic insert failure'); END;").unwrap();
    let projection = workflow_focus_projection(&connection, 11).unwrap();
    assert!(apply_workflow_assertion(
        &connection,
        &projection,
        &request(&projection, "split-here", 10, Some(11))
    )
    .is_err());
    assert_eq!(count(&connection), 0);
    assert!(connection.is_autocommit());
    assert_ne!(
        result.projection.assertion_revision,
        projection.assertion_revision
    );
}
#[test]
fn deleted_source_keeps_unresolved_record_and_restored_native_identity_resolves() {
    let connection = database();
    let projection = workflow_focus_projection(&connection, 11).unwrap();
    let asserted = apply_workflow_assertion(
        &connection,
        &projection,
        &request(&projection, "split-here", 10, Some(11)),
    )
    .unwrap();
    let stable = key(&projection, 10);
    connection
        .execute("DELETE FROM sessions WHERE id=10", [])
        .unwrap();
    let absent = workflow_focus_projection(&connection, 11).unwrap();
    assert_eq!(absent.assertions[0]["resolution"], "unresolved");
    assert_eq!(
        absent.assertions[0]["resolution_reason"],
        "missing-endpoint"
    );
    assert_eq!(count(&connection), 1);
    connection.execute("INSERT INTO sessions(id,source_id,workspace_id,external_id,source_path,title,started_at,last_event_at,event_count,session_class,session_role,index_policy) VALUES(110,1,1,'native-10','/synthetic/restored.jsonl','Restored','2026-09-14T01:00:00Z','2026-09-14T01:00:00Z',1,'work','primary','full')",[]).unwrap();
    connection.execute("INSERT INTO thread_links(thread_id,entity_type,entity_id,linked_by) VALUES(1,'session','110','user')",[]).unwrap();
    let restored = workflow_focus_projection(&connection, 11).unwrap();
    assert_eq!(key(&restored, 110), stable);
    assert_eq!(restored.assertions[0]["resolution"], "applied");
    assert_eq!(restored.assertions[0]["id"], asserted.assertion["id"]);
    assert!(connection
        .query_row(
            "SELECT source_session_id IS NULL FROM workflow_assertions WHERE id=1",
            [],
            |r| r.get::<_, bool>(0)
        )
        .unwrap());
}
