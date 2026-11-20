use localbrain_core::backend::{
    clock, db,
    ingest::ParsedReferenceCandidate,
    sessions::{self, references},
    terminal_workspaces, Config,
};
use rusqlite::{params, Connection};
use serde_json::json;

fn setup() -> Connection {
    let conn = Connection::open_in_memory().unwrap();
    conn.execute_batch(db::SCHEMA).unwrap();
    conn.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES(1,'codex','Synthetic','/synthetic')",[]).unwrap();
    conn
}
fn session(conn: &Connection, id: i64) {
    conn.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title,cwd_raw,started_at) VALUES(?,1,?,?,?,'/synthetic/project','2026-11-18T09:00:00Z')",params![id,format!("native-{id:08}"),format!("/synthetic/{id}.jsonl"),format!("Source {id}")]).unwrap();
}
fn candidate(
    value: &str,
    kind: &str,
    outcome: Option<&str>,
    line: i64,
) -> ParsedReferenceCandidate {
    ParsedReferenceCandidate {
        reference_kind: "url".into(),
        reference: value.into(),
        evidence_kind: kind.into(),
        source_line: line,
        evidence_ordinal: 1,
        source_event_id: Some(format!("event-{line}")),
        observed_at: Some(format!("2026-11-18T09:{:02}:00Z", line % 60)),
        tool_name: ["tool_result", "resource_read"]
            .contains(&kind)
            .then(|| "read".into()),
        tool_call_id: ["tool_result", "resource_read"]
            .contains(&kind)
            .then(|| format!("call-{line}")),
        read_outcome: outcome.map(Into::into),
    }
}
#[test]
fn inventory_keeps_primary_scope_children_presence_and_complete_chart() {
    let conn = setup();
    for id in 1..=18 {
        session(&conn, id);
    }
    conn.execute(
        "UPDATE sessions SET session_role='subsession',parent_session_id=1 WHERE id=17",
        [],
    )
    .unwrap();
    conn.execute(
        "UPDATE sessions SET session_class='maintenance',index_policy='metadata_only' WHERE id=18",
        [],
    )
    .unwrap();
    conn.execute("INSERT INTO source_files(source_id,session_id,path,size_bytes,mtime_ns,last_scanned_at,presence_state) VALUES(1,1,'/synthetic/a',1,1,'fixed','MISSING'),(1,1,'/synthetic/b',1,1,'fixed','PRESENT')",[]).unwrap();
    let first = sessions::session_inventory_page(&conn, None, None, 0).unwrap();
    assert_eq!(first["page"], 1);
    assert_eq!(first["total"], 16);
    assert_eq!(first["items"].as_array().unwrap().len(), 15);
    let last = sessions::session_inventory_page(&conn, None, None, 999).unwrap();
    assert_eq!(last["page"], 2);
    assert_eq!(last["items"][0]["id"], 1);
    assert_eq!(last["items"][0]["source_presence_state"], "PRESENT");
    assert_eq!(last["items"][0]["subsessions"][0]["id"], 17);
    assert_eq!(
        sessions::session_inventory_page(&conn, Some("missing"), None, 1).unwrap()["total"],
        0
    );
    assert_eq!(
        sessions::session_inventory_page(&conn, None, Some(0), 1).unwrap()["total"],
        0
    );
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    assert_eq!(
        sessions::session_chart_inventory(&conn, &config, None, None)
            .unwrap()
            .len(),
        16
    );
    assert!(sessions::session_detail(&conn, 18).unwrap().is_none());
    assert!(sessions::session_parent(&conn, 17).unwrap().is_some());
}
#[test]
fn user_title_and_pins_preserve_imported_ownership_and_reject_ineligible_mutation() {
    let conn = setup();
    session(&conn, 1);
    session(&conn, 2);
    conn.execute(
        "UPDATE sessions SET session_class='maintenance',index_policy='metadata_only' WHERE id=2",
        [],
    )
    .unwrap();
    assert_eq!(
        sessions::set_display_title(&conn, 1, &json!("  My title  ")).unwrap()["effective_title"],
        "My title"
    );
    assert_eq!(
        sessions::pin_session(&conn, 1, Some("first")).unwrap()["pinned_at"],
        "first"
    );
    assert_eq!(
        sessions::pin_session(&conn, 1, Some("second")).unwrap()["pinned_at"],
        "first"
    );
    let pinned = sessions::list_pinned_sessions(&conn, 8).unwrap();
    assert_eq!(pinned[0]["title"], "Source 1");
    assert_eq!(pinned[0]["display_title"], "My title");
    for value in [
        json!("bad\nline"),
        json!("bad\u{85}line"),
        json!(false),
        json!("x".repeat(501)),
    ] {
        assert!(sessions::set_display_title(&conn, 1, &value).is_err());
    }
    assert_eq!(
        sessions::session_detail(&conn, 1).unwrap().unwrap()["display_title"],
        "My title"
    );
    assert!(sessions::set_display_title(&conn, 2, &json!("hidden")).is_err());
    assert!(sessions::pin_session(&conn, 2, None).is_err());
    assert_eq!(
        sessions::set_display_title(&conn, 1, &json!(" ")).unwrap()["effective_title"],
        "Source 1"
    );
    assert!(sessions::unpin_session(&conn, 1).unwrap());
    assert!(!sessions::unpin_session(&conn, 1).unwrap());
    assert_eq!(
        sessions::pin_session(&conn, 1, Some("third")).unwrap()["pinned_at"],
        "third"
    );
    conn.execute("DELETE FROM sessions WHERE id=1", []).unwrap();
    assert!(!sessions::is_session_pinned(&conn, 1).unwrap());
}
#[test]
fn chart_visibility_distinguishes_absent_empty_scope_and_caller_rollback() {
    let conn = setup();
    assert_eq!(
        sessions::get_project_visibility(&conn, "all", None).unwrap(),
        None
    );
    conn.execute_batch("BEGIN").unwrap();
    sessions::set_project_visibility(&conn, "all", None, &json!([]), false).unwrap();
    assert_eq!(
        sessions::get_project_visibility(&conn, "all", None).unwrap(),
        Some(vec![])
    );
    conn.execute_batch("ROLLBACK").unwrap();
    assert!(sessions::get_project_visibility(&conn, "all", None)
        .unwrap()
        .is_none());
    sessions::set_project_visibility(&conn, "all", None, &json!([]), false).unwrap();
    sessions::set_project_visibility(&conn, "all", None, &json!(["old"]), true).unwrap();
    assert_eq!(
        sessions::get_project_visibility(&conn, "all", None).unwrap(),
        Some(vec![])
    );
    assert_eq!(
        sessions::set_project_visibility(
            &conn,
            "all",
            Some(0),
            &json!(["", "/synthetic//A", "/synthetic/A", "/synthetic/A"]),
            false
        )
        .unwrap(),
        vec!["", "/synthetic//A", "/synthetic/A"]
    );
    for bad in [
        json!(false),
        json!([null]),
        json!(["x".repeat(4097)]),
        json!((0..16)
            .map(|index| format!("{index:03}{}", "x".repeat(4093)))
            .collect::<Vec<_>>()),
    ] {
        assert!(sessions::validate_hidden_projects(&bad).is_err());
    }
}
#[test]
fn activity_preserves_occurrences_metadata_priority_and_gap_union() {
    let conn = setup();
    session(&conn, 1);
    session(&conn, 2);
    conn.execute("UPDATE sessions SET started_at='invalid' WHERE id=2", [])
        .unwrap();
    for (sequence, (id, session, at)) in [
        ("a", 1, "2026-11-18T00:00:00Z"),
        ("b", 1, "2026-11-18T00:30:00Z"),
        ("c", 1, "2026-11-18T01:00:01Z"),
        ("d", 1, "bad"),
        ("e", 2, "20261118T013000"),
        ("f", 2, "2026-11-18T01:45:00Z"),
    ]
    .into_iter()
    .enumerate()
    {
        conn.execute("INSERT INTO activity_events(id,session_id,sequence,source_line,event_type,occurred_at) VALUES(?,?,?,1,'message',?)",params![id,session,sequence as i64,at]).unwrap();
    }
    let activity = sessions::session_chart_activity(&conn, 1).unwrap().unwrap();
    assert_eq!(activity["timestamps"].as_array().unwrap().len(), 3);
    assert_eq!(activity["undated_events"], 1);
    assert_eq!(activity["total_events"], 4);
    let config = Config::for_data_dir("/synthetic/data");
    let chart = sessions::session_chart_inventory(&conn, &config, None, None).unwrap();
    assert_eq!(chart[0]["time_source"], "metadata");
    assert_eq!(chart[1]["time_source"], "event");
    let summary = sessions::activity::activity_summary(&conn, None, None, None).unwrap();
    assert_eq!(summary["estimated_active_seconds"], 2700);
    assert_eq!(summary["activity_segment_count"], 3);
    let (start, end) = clock::calendar_day_bounds(
        chrono::NaiveDate::from_ymd_opt(2026, 3, 8).unwrap(),
        "America/New_York",
    )
    .unwrap();
    assert_eq!((end - start).num_hours(), 23);
}
#[test]
fn references_reconcile_resources_deduplicate_reads_and_preserve_evidence_on_failure() {
    let conn = setup();
    session(&conn, 1);
    let config = Config::for_data_dir("/synthetic/data");
    let url = "https://example.com/docs?q=one";
    let failed = candidate(url, "resource_read", Some("failure"), 1);
    let success = candidate(url, "resource_read", Some("success"), 2);
    let mention = candidate(url, "user_mention", None, 3);
    let candidates = vec![
        failed,
        success.clone(),
        success,
        mention,
        candidate("javascript:alert(1)", "user_mention", None, 4),
    ];
    references::reconcile_session_references(
        &conn,
        &config,
        1,
        "/synthetic/1.jsonl",
        10,
        20,
        &candidates,
        true,
        None,
    )
    .unwrap();
    let projection = references::session_reference_projection(&conn, 1).unwrap();
    assert_eq!(projection["retained_total"], 1);
    assert_eq!(
        projection["items"][0]["evidence"],
        json!([{"kind":"resource_read","outcome":"success","count":1},{"kind":"user_mention","outcome":null,"count":1}])
    );
    let first: String = conn
        .query_row(
            "SELECT MIN(first_observed_at) FROM session_reference_evidence",
            [],
            |row| row.get(0),
        )
        .unwrap();
    references::reconcile_session_references(
        &conn,
        &config,
        1,
        "/synthetic/1.jsonl",
        10,
        20,
        &candidates,
        true,
        None,
    )
    .unwrap();
    assert_eq!(
        conn.query_row(
            "SELECT MIN(first_observed_at) FROM session_reference_evidence",
            [],
            |row| row.get::<_, String>(0)
        )
        .unwrap(),
        first
    );
    conn.execute_batch("CREATE TRIGGER reject_reference BEFORE INSERT ON session_reference_evidence BEGIN SELECT RAISE(ABORT,'synthetic failure'); END;").unwrap();
    assert!(references::reconcile_session_references(
        &conn,
        &config,
        1,
        "/synthetic/1.jsonl",
        11,
        21,
        &[candidate(
            "https://example.com/new",
            "user_mention",
            None,
            5
        )],
        true,
        None
    )
    .is_err());
    let failed = references::session_reference_projection(&conn, 1).unwrap();
    assert_eq!(failed["stale"], true);
    assert_eq!(failed["items"], projection["items"]);
}
#[test]
fn reference_bounds_prefer_completed_reads_without_guessing_unindexed_documents() {
    let conn = setup();
    session(&conn, 1);
    let config = Config::for_data_dir("/synthetic/data");
    let mut candidates = Vec::new();
    for index in 0..105 {
        candidates.push(candidate(
            &format!("https://example.com/{index}"),
            "assistant_mention",
            None,
            index + 1,
        ));
    }
    candidates.push(candidate(
        "https://example.com/winner",
        "resource_read",
        Some("success"),
        200,
    ));
    let mut missing = candidate("unindexed.md", "resource_read", Some("success"), 201);
    missing.reference_kind = "markdown".into();
    candidates.push(missing);
    references::reconcile_session_references(
        &conn,
        &config,
        1,
        "/synthetic/1.jsonl",
        10,
        20,
        &candidates,
        true,
        None,
    )
    .unwrap();
    let projection = references::session_reference_projection(&conn, 1).unwrap();
    assert_eq!(projection["partial"], true);
    assert_eq!(projection["observed_total"], 106);
    assert_eq!(projection["retained_total"], 100);
    assert!(projection["items"]
        .as_array()
        .unwrap()
        .iter()
        .any(|item| item["destination"] == "https://example.com/winner"));
}
#[test]
fn empty_terminal_workspace_removal_returns_removed_identity_and_keeps_private_store() {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    let state = json!({"generation":"0123456789abcdef0123456789abcdef","tabs":[],"terminals":[]});
    let created = terminal_workspaces::change_workspaces(
        &config,
        || Ok(state.clone()),
        "create",
        &json!({"name":" Draft ","cwd":""}),
    )
    .unwrap();
    let id = created["id"].clone();
    assert_eq!(created["items"][0]["name"], "Draft");
    let removed = terminal_workspaces::change_workspaces(
        &config,
        || Ok(state.clone()),
        "remove",
        &json!({"id":id}),
    )
    .unwrap();
    assert_eq!(removed["id"], id);
    assert_eq!(removed["items"], json!([]));
    assert_eq!(
        terminal_workspaces::read_workspaces(&config, &state)["items"],
        json!([])
    );
}
