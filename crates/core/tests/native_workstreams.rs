use localbrain_core::backend::{
    db,
    maintenance::{self, TaskRuntime},
    workstreams, Config,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::{
    fs,
    os::unix::fs::{MetadataExt, PermissionsExt},
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};
fn setup() -> (tempfile::TempDir, Config, Connection) {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    connection.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Synthetic','/synthetic'); INSERT INTO sessions(id,source_id,external_id,source_path,title,session_class,session_role,last_event_at) VALUES (1,1,'a','/synthetic/a','Alpha delivery','work','primary','2026-11-15'),(2,1,'b','/synthetic/b','Alpha maintenance','maintenance','primary','2026-11-15'),(3,1,'c','/synthetic/c','Alpha child','work','subsession','2026-11-15');").unwrap();
    (root, config, connection)
}
#[test]
fn queued_run_preserves_large_sqlite_budget_and_refuses_overflow_without_a_partial_row() {
    let (_root, mut config, connection) = setup();
    let workstream =
        workstreams::create_workstream(&connection, "Synthetic large budget", None).unwrap();
    for value in [4_294_967_296_u64, i64::MAX as u64] {
        config.mcp_call_budget = value.into();
        let run = workstreams::prepare_run(
            &connection,
            &config,
            workstream,
            "organize_resources",
            None,
            None,
            false,
        )
        .unwrap();
        let row = maintenance::get_run(&connection, &run).unwrap().unwrap();
        assert_eq!(row["mcp_call_budget"], value);
        let snapshot: Value =
            serde_json::from_str(row["source_snapshot_json"].as_str().unwrap()).unwrap();
        assert_eq!(snapshot["external_discovery"]["mcp_call_budget"], value);
    }
    config.mcp_call_budget = serde_json::Number::from_string_unchecked(
        "9999999999999999999999999999999999999999999999".into(),
    );
    let before: i64 = connection
        .query_row("SELECT COUNT(*) FROM maintenance_runs", [], |row| {
            row.get(0)
        })
        .unwrap();
    assert!(workstreams::prepare_run(
        &connection,
        &config,
        workstream,
        "organize_resources",
        None,
        None,
        false
    )
    .is_err());
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM maintenance_runs", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        before
    );
}
#[test]
fn curated_links_checkpoint_versions_and_parent_ids_survive_mutations() {
    let (_root, config, connection) = setup();
    let workstream =
        workstreams::create_workstream(&connection, " Alpha ", Some(" summary ")).unwrap();
    let thread = workstreams::create_thread(
        &connection,
        workstream,
        &json!({"title":" Delivery ","current_goal":" Alpha "}),
    )
    .unwrap();
    assert!(workstreams::add_link(
        &connection,
        &config,
        "thread",
        thread,
        "session",
        "2",
        "related-to",
        "user",
        None
    )
    .is_err());
    assert!(workstreams::add_link(
        &connection,
        &config,
        "thread",
        thread,
        "session",
        "3",
        "related-to",
        "user",
        None
    )
    .is_err());
    let first = workstreams::add_link(
        &connection,
        &config,
        "thread",
        thread,
        "session",
        "1",
        " implements ",
        "user",
        None,
    )
    .unwrap();
    let second = workstreams::add_link(
        &connection,
        &config,
        "thread",
        thread,
        "session",
        "1",
        "evidence",
        "user",
        Some(0.9),
    )
    .unwrap();
    assert_eq!(first, second);
    let checkpoint = workstreams::create_checkpoint(
        &connection,
        workstream,
        &json!({"current_goal":" Confirmed "}),
    )
    .unwrap();
    let initial = workstreams::get_workstream(&connection, workstream)
        .unwrap()
        .unwrap();
    assert_eq!(initial["checkpoint"]["resource_count"], 1);
    assert_eq!(initial["checkpoint"]["version"], 1);
    workstreams::remove_link(&connection, "thread", thread, first).unwrap();
    assert_eq!(
        db::row(
            &connection,
            "SELECT relation_type FROM checkpoint_resource_refs WHERE checkpoint_id=?",
            [checkpoint]
        )
        .unwrap()
        .unwrap()["relation_type"],
        "evidence"
    );
    let next = workstreams::create_checkpoint(&connection, workstream, &json!({})).unwrap();
    assert_ne!(checkpoint, next);
    let result = workstreams::get_workstream(&connection, workstream)
        .unwrap()
        .unwrap();
    assert_eq!(result["checkpoint"]["version"], 2);
    assert_eq!(result["checkpoint"]["resource_count"], 0);
    assert_eq!(result["name"], "Alpha");
    assert!(
        workstreams::update_workstream(&connection, workstream, "Alpha", "invalid", None).is_err()
    );
    assert!(workstreams::update_thread(&connection, thread, &json!({"status":"invalid"})).is_err());
    assert_eq!(
        db::row(&connection, "SELECT COUNT(*) AS n FROM sessions", [])
            .unwrap()
            .unwrap()["n"],
        3
    );
}
#[test]
fn suggestions_require_explicit_acceptance_and_reject_restore_are_reversible() {
    let (_root, config, connection) = setup();
    let workstream = workstreams::create_workstream(&connection, "Alpha", None).unwrap();
    let thread =
        workstreams::create_thread(&connection, workstream, &json!({"title":"Alpha"})).unwrap();
    assert_eq!(
        workstreams::generate_suggestions(&connection, workstream).unwrap(),
        1
    );
    assert_eq!(
        workstreams::generate_suggestions(&connection, workstream).unwrap(),
        0
    );
    let suggestion = db::row(&connection, "SELECT id FROM suggestions", [])
        .unwrap()
        .unwrap()["id"]
        .as_i64()
        .unwrap();
    assert_eq!(
        workstreams::entity_memberships(&connection, "session", 1)
            .unwrap()
            .len(),
        0
    );
    workstreams::resolve_suggestion(&connection, &config, suggestion, "reject").unwrap();
    assert!(workstreams::resolve_suggestion(&connection, &config, suggestion, "accept").is_err());
    workstreams::resolve_suggestion(&connection, &config, suggestion, "restore").unwrap();
    workstreams::resolve_suggestion(&connection, &config, suggestion, "accept").unwrap();
    let result = workstreams::get_workstream(&connection, workstream)
        .unwrap()
        .unwrap();
    assert_eq!(result["threads"][0]["links"][0]["resource_id"], "1");
    assert_eq!(result["threads"][0]["id"], thread);
    assert_eq!(result["threads"][0]["links"][0]["linked_by"], "suggestion");
    assert_eq!(
        workstreams::generate_suggestions(&connection, workstream).unwrap(),
        0
    );
}
fn structured(thread: i64) -> Value {
    json!({"summary":"Synthetic","resource_suggestions":[{"target_thread_id":thread,"resource_type":"session","locator":"1","title":"Alpha","relation_type":"related-to","rationale":"Synthetic rationale","evidence":"e-1","confidence":0.9}],"checkpoint_draft":{"current_goal":"Alpha"},"priority_review":"Review"})
}
#[test]
fn runner_refresh_preserves_decisions_and_preparation_does_not_launch() {
    let (_root, config, connection) = setup();
    let workstream = workstreams::create_workstream(&connection, "Alpha", None).unwrap();
    let thread =
        workstreams::create_thread(&connection, workstream, &json!({"title":"Alpha"})).unwrap();
    let run = workstreams::prepare_run(
        &connection,
        &config,
        workstream,
        "organize_resources",
        Some("additional {run_id}"),
        None,
        true,
    )
    .unwrap();
    let record = maintenance::get_run(&connection, &run).unwrap().unwrap();
    assert_eq!(record["status"], "queued");
    assert!(record["pid"].is_null());
    let prompt = fs::read_to_string(record["prompt_path"].as_str().unwrap()).unwrap();
    assert!(prompt.contains(&format!("[LOCALBRAIN_RUN: {run}]")));
    assert!(prompt.contains("additional {run_id}"));
    assert_eq!(
        fs::metadata(record["prompt_path"].as_str().unwrap())
            .unwrap()
            .mode()
            & 0o777,
        0o600
    );
    assert!(workstreams::runner_command_preview().contains("--permission-mode plan"));
    assert!(!workstreams::runner_command_preview().contains("--no-session-persistence"));
    assert_eq!(
        workstreams::persist_structured_suggestions(
            &connection,
            &config,
            &run,
            workstream,
            &structured(thread)
        )
        .unwrap(),
        2
    );
    let link = db::row(
        &connection,
        "SELECT id FROM suggestions WHERE suggestion_type='resource_link'",
        [],
    )
    .unwrap()
    .unwrap()["id"]
        .as_i64()
        .unwrap();
    workstreams::resolve_suggestion(&connection, &config, link, "reject").unwrap();
    let second = workstreams::prepare_run(
        &connection,
        &config,
        workstream,
        "organize_resources",
        None,
        None,
        true,
    )
    .unwrap();
    assert_eq!(
        workstreams::supersede_runner_suggestions(&connection, workstream).unwrap(),
        1
    );
    assert_eq!(
        workstreams::persist_structured_suggestions(
            &connection,
            &config,
            &second,
            workstream,
            &structured(thread)
        )
        .unwrap(),
        1
    );
    assert_eq!(
        db::row(
            &connection,
            "SELECT status FROM suggestions WHERE id=?",
            [link]
        )
        .unwrap()
        .unwrap()["status"],
        "rejected"
    );
    assert_eq!(
        workstreams::entity_memberships(&connection, "session", 1)
            .unwrap()
            .len(),
        0
    );
    connection.execute("UPDATE maintenance_runs SET status='completed',completed_at='2026-11-18',structured_result_json=? WHERE id=?",rusqlite::params![serde_json::to_string(&structured(thread)).unwrap(),second]).unwrap();
    let manifest = workstreams::build_manifest(
        &connection,
        &config,
        workstream,
        "lb-next",
        "organize_resources",
        None,
        false,
    )
    .unwrap();
    assert_eq!(
        manifest["previous_analysis"]["local_candidate_snapshot_unchanged"],
        true
    );
    assert_eq!(manifest["previous_analysis"]["run_id"], second);
}
#[test]
fn explicit_synthetic_runner_completes_and_only_publishes_pending_suggestions() {
    let (root, mut config, connection) = setup();
    fs::create_dir_all(&config.home_dir).unwrap();
    let executable = root.path().join("synthetic-runner");
    let workstream = workstreams::create_workstream(&connection, "Alpha", None).unwrap();
    let thread =
        workstreams::create_thread(&connection, workstream, &json!({"title":"Alpha"})).unwrap();
    let event =
        json!({"type":"result","result":"Synthetic","structured_output":structured(thread)})
            .to_string();
    fs::write(
        &executable,
        format!(
            "#!/bin/sh\ncat >/dev/null\nprintf '%s\\n' '{}'\n",
            event.replace('\'', "'\"'\"'")
        ),
    )
    .unwrap();
    fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
    config.claude_bin = Some(executable);
    let run = workstreams::prepare_run(
        &connection,
        &config,
        workstream,
        "organize_resources",
        None,
        None,
        true,
    )
    .unwrap();
    let runtime = Arc::new(TaskRuntime::new(config.clone()));
    let syncs = Arc::new(AtomicUsize::new(0));
    let cloned = syncs.clone();
    runtime.set_scanner(move |_, _| {
        cloned.fetch_add(1, Ordering::SeqCst);
        Ok(())
    });
    workstreams::start_run(&runtime, &run).unwrap();
    let started = Instant::now();
    loop {
        let current = maintenance::get_run(&connection, &run).unwrap().unwrap();
        if current["status"] == "completed" {
            assert_eq!(current["suggestions_created"], 2);
            break;
        }
        assert_ne!(current["status"], "failed", "{current}");
        assert!(started.elapsed() < Duration::from_secs(6));
        std::thread::sleep(Duration::from_millis(10));
    }
    assert_eq!(
        workstreams::entity_memberships(&connection, "session", 1)
            .unwrap()
            .len(),
        0
    );
    assert_eq!(
        db::row(
            &connection,
            "SELECT COUNT(*) AS n FROM suggestions WHERE status='pending'",
            []
        )
        .unwrap()
        .unwrap()["n"],
        2
    );
    runtime.shutdown().unwrap();
    assert_eq!(syncs.load(Ordering::SeqCst), 1);
}
#[test]
fn excluded_session_content_does_not_change_candidate_fingerprint() {
    let (_root, _config, connection) = setup();
    let workstream = workstreams::create_workstream(&connection, "Alpha", None).unwrap();
    workstreams::create_thread(&connection, workstream, &json!({"title":"Alpha"})).unwrap();
    connection.execute("INSERT INTO search_index(entity_type,entity_id,title,path,body) SELECT 'session',CAST(id AS TEXT),title,source_path,'Alpha' FROM sessions",[]).unwrap();
    let first = workstreams::build_candidate_bundle(
        &connection,
        &workstreams::get_workstream(&connection, workstream)
            .unwrap()
            .unwrap(),
    )
    .unwrap();
    connection.execute("UPDATE sessions SET title='Alpha changed excluded source',last_event_at='2999-01-01',event_count=999 WHERE id IN (2,3)",[]).unwrap();
    let second = workstreams::build_candidate_bundle(
        &connection,
        &workstreams::get_workstream(&connection, workstream)
            .unwrap()
            .unwrap(),
    )
    .unwrap();
    assert_eq!(first["fingerprint"], second["fingerprint"]);
    assert_eq!(first["counts"]["sessions"], 1);
}
#[test]
fn failed_runner_refresh_preserves_the_existing_review_queue() {
    let (root, mut config, connection) = setup();
    fs::create_dir_all(&config.home_dir).unwrap();
    let executable = root.path().join("synthetic-failure");
    fs::write(
        &executable,
        "#!/bin/sh\ncat >/dev/null\nprintf '%s' 'synthetic failure' >&2\nexit 2\n",
    )
    .unwrap();
    fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
    config.claude_bin = Some(executable);
    let workstream = workstreams::create_workstream(&connection, "Alpha", None).unwrap();
    let thread =
        workstreams::create_thread(&connection, workstream, &json!({"title":"Alpha"})).unwrap();
    let old = workstreams::prepare_run(
        &connection,
        &config,
        workstream,
        "organize_resources",
        None,
        None,
        false,
    )
    .unwrap();
    workstreams::persist_structured_suggestions(
        &connection,
        &config,
        &old,
        workstream,
        &structured(thread),
    )
    .unwrap();
    let before = db::rows(&connection, "SELECT * FROM suggestions ORDER BY id", []).unwrap();
    let run = workstreams::prepare_run(
        &connection,
        &config,
        workstream,
        "organize_resources",
        None,
        None,
        true,
    )
    .unwrap();
    let runtime = Arc::new(TaskRuntime::new(config));
    workstreams::start_run(&runtime, &run).unwrap();
    let started = Instant::now();
    while maintenance::get_run(&connection, &run).unwrap().unwrap()["status"] != "failed" {
        assert!(started.elapsed() < Duration::from_secs(6));
        std::thread::sleep(Duration::from_millis(10));
    }
    assert_eq!(
        before,
        db::rows(&connection, "SELECT * FROM suggestions ORDER BY id", []).unwrap()
    );
    runtime.shutdown().unwrap();
}
