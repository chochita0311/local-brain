use localbrain_core::backend::{
    db,
    workflow::{assertions::overlay_workflow_assertions, focus::*},
};
use rusqlite::{
    hooks::{AuthAction, AuthContext, Authorization},
    Connection,
};
use serde_json::Value;

fn fixtures() -> Value {
    serde_json::from_str(include_str!(
        "../src/backend/workflow/fixtures/focus-golden.json"
    ))
    .unwrap()
}
fn database(case: &Value) -> Connection {
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection.execute_batch("PRAGMA foreign_keys=OFF").unwrap();
    connection
        .execute_batch(case["setup_sql"].as_str().unwrap())
        .unwrap();
    connection.execute_batch("PRAGMA foreign_keys=ON").unwrap();
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM pragma_foreign_key_check", [], |r| r
                .get::<_, i64>(
                0
            ))
            .unwrap(),
        0
    );
    connection
}
#[test]
fn complete_focus_and_user_overlay_match_frozen_python() {
    for case in fixtures()["cases"].as_array().unwrap() {
        let connection = database(case);
        let result =
            workflow_focus_projection(&connection, case["selected_session_id"].as_i64().unwrap())
                .unwrap();
        assert_eq!(
            serde_json::to_value(result).unwrap(),
            case["expected"],
            "{}",
            case["name"]
        );
    }
}
#[test]
fn focus_is_read_only_repeatable_and_does_not_select_message_or_document_bodies() {
    for case in fixtures()["cases"].as_array().unwrap() {
        let connection = database(case);
        connection.execute_batch("PRAGMA query_only=ON").unwrap();
        let before = connection.total_changes();
        connection.authorizer(Some(|context: AuthContext<'_>| match context.action {
            AuthAction::Read {
                table_name: "activity_events",
                column_name: "text",
            }
            | AuthAction::Read {
                table_name: "context_documents",
                column_name: "body",
            } => Authorization::Deny,
            _ => Authorization::Allow,
        }));
        let id = case["selected_session_id"].as_i64().unwrap();
        assert!(workflow_session_is_eligible(&connection, id).unwrap());
        let first = workflow_focus_projection(&connection, id).unwrap();
        let second = workflow_focus_projection(&connection, id).unwrap();
        assert_eq!(first, second);
        assert_eq!(
            overlay_workflow_assertions(&connection, first.clone()).unwrap(),
            first
        );
        assert_eq!(connection.total_changes(), before);
        let payload = serde_json::to_string(&first).unwrap();
        for private in [
            "/private/repo-secret",
            "/private/source-",
            "private body",
            "native-",
        ] {
            assert!(
                !payload.contains(private),
                "{} leaked {private}",
                case["name"]
            );
        }
    }
}
#[test]
fn missing_ineligible_and_meaningful_eligibility_are_distinct() {
    let fixture = fixtures();
    let connection = database(&fixture["cases"][0]);
    assert_eq!(
        workflow_focus_projection(&connection, 999).unwrap().status,
        "missing"
    );
    assert!(!workflow_session_is_eligible(&connection, 999).unwrap());
    assert!(workflow_focus_projection(&connection, 0).is_err());
    connection
        .execute("UPDATE sessions SET event_count=0 WHERE id=7", [])
        .unwrap();
    assert!(!workflow_session_is_eligible(&connection, 7).unwrap());
    assert_eq!(
        workflow_focus_projection(&connection, 7).unwrap().status,
        "ineligible"
    );
    connection.execute("INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,source_line) VALUES('synthetic-meaningful',7,1,'message','user','',1)",[]).unwrap();
    assert!(workflow_session_is_eligible(&connection, 7).unwrap());
    connection
        .execute(
            "UPDATE sessions SET session_class='maintenance' WHERE id=7",
            [],
        )
        .unwrap();
    assert!(!workflow_session_is_eligible(&connection, 7).unwrap());
    assert_eq!(
        workflow_focus_projection(&connection, 7).unwrap().status,
        "ineligible"
    );
}
#[test]
fn workspace_branch_and_proximity_never_establish_a_relation_alone() {
    let fixture = fixtures();
    let connection = database(&fixture["cases"][1]);
    connection.execute("DELETE FROM thread_links", []).unwrap();
    let result = workflow_focus_projection(&connection, 11).unwrap();
    assert_eq!(result.episodes.len(), 1);
    assert!(result.relations.is_empty());
    assert_eq!(result.candidate_observed_total, 0);
}
#[test]
fn candidate_episode_and_branch_counts_remain_honest_at_caps() {
    let fixture = fixtures();
    let connection = database(&fixture["cases"][1]);
    connection.execute("DELETE FROM thread_links", []).unwrap();
    connection.execute("DELETE FROM sessions", []).unwrap();
    for offset in 0..206 {
        let id = 1000 + offset;
        let day = 1 + offset / 20;
        let hour = offset % 20;
        let stamp = format!("2026-09-{day:02}T{hour:02}:00:00Z");
        connection.execute("INSERT INTO sessions(id,source_id,workspace_id,external_id,source_path,title,started_at,last_event_at,event_count,session_class,session_role,index_policy) VALUES(?,1,1,?,?,'Synthetic bounded episode',?,?,1,'work','primary','full')",rusqlite::params![id,format!("native-{id}"),format!("/synthetic/{id}.jsonl"),stamp,stamp]).unwrap();
        connection.execute("INSERT INTO thread_links(thread_id,entity_type,entity_id,linked_by) VALUES(1,'session',?,'user')",[id.to_string()]).unwrap();
    }
    let result = workflow_focus_projection(&connection, 1000).unwrap();
    assert_eq!(result.candidate_observed_total, 205);
    assert_eq!(result.candidate_retained_total, 200);
    assert_eq!(result.episode_retained_total, 24);
    assert_eq!(result.episode_observed_total, 201);
    assert_eq!(result.branch_root_retained_total, 0);
}
