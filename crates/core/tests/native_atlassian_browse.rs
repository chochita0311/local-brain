use localbrain_core::backend::{
    atlassian::{browse, catalog},
    db,
};
use rusqlite::{
    hooks::{AuthAction, AuthContext, Authorization},
    Connection,
};
use serde_json::{json, Value};
#[allow(dead_code)]
#[path = "native_atlassian_support/mod.rs"]
mod support;
fn connection() -> Connection {
    let db = Connection::open_in_memory().unwrap();
    db.execute_batch(db::SCHEMA).unwrap();
    db
}
fn stub(db: &Connection, key: &str) -> i64 {
    catalog::create_or_reuse_atlassian_stub(db,&json!({"service":"jira","url":format!("https://jira.synthetic.test/browse/{key}"),"title":key,"coverage":"indexed","observed_at":"2026-08-01T00:00:00Z"})).unwrap()["external_resource_id"].as_i64().unwrap()
}
#[test]
fn selected_detail_does_not_read_other_items_and_ineligible_preview_never_loads_detail_groups() {
    let db = connection();
    let first = stub(&db, "ONE-1");
    let other = stub(&db, "TWO-2");
    assert_eq!(
        db.execute(
            "INSERT INTO atlassian_item_remote_state(external_resource_id,metadata_json) VALUES(?,CAST(x'FF' AS TEXT))",
            [other],
        )
        .unwrap(),
        1
    );
    assert_eq!(
        browse::atlassian_item_detail(&db, first).unwrap().unwrap()["id"],
        first
    );
    let changes = db.total_changes();
    db.execute_batch("PRAGMA query_only=ON").unwrap();
    db.authorizer(Some(|ctx: AuthContext<'_>| match ctx.action {
        AuthAction::Read { table_name, .. }
            if [
                "external_resource_content",
                "external_resource_notes",
                "atlassian_classifications",
                "atlassian_item_classifications",
                "atlassian_item_evidence",
                "maintenance_runs",
                "external_sync_runs",
                "workstream_links",
                "thread_links",
                "activity_events",
                "source_files",
                "search_index",
                "external_source_capabilities",
            ]
            .contains(&table_name) =>
        {
            Authorization::Deny
        }
        _ => Authorization::Allow,
    }));
    let result = browse::atlassian_item_preview(&db, first, &json!({"service":"confluence"}))
        .unwrap()
        .unwrap();
    assert_eq!(result["eligible"], false);
    for key in [
        "content_excerpt",
        "evidence",
        "organization",
        "recent_refresh_run",
    ] {
        assert!(result.get(key).is_none());
    }
    assert!(browse::atlassian_item_preview(&db, 999999, &json!({}))
        .unwrap()
        .is_none());
    assert_eq!(db.total_changes(), changes);
}
#[test]
fn classification_sql_failure_rolls_back_notes_axes_and_existing_memberships() {
    let db = connection();
    let item = stub(&db, "LOCAL-1");
    let changed = "2026-08-02T12:00:00Z";
    browse::update_atlassian_local_state(
        &db,
        item,
        &json!({"note":"original","attention":"pinned","tags":"one","changed_at":changed}),
    )
    .unwrap();
    let before = db::rows(&db, "SELECT * FROM external_resource_notes", []).unwrap();
    let classes = db::rows(&db, "SELECT * FROM atlassian_classifications", []).unwrap();
    let links = db::rows(&db, "SELECT * FROM atlassian_item_classifications", []).unwrap();
    let fts = db::rows(&db, "SELECT * FROM search_index", []).unwrap();
    let caught=browse::update_atlassian_local_state(&db,item,&json!({"note":"new","attention":"archived","tags":"a b,a  b","changed_at":"2026-08-03T00:00:00Z"})).unwrap_err();
    assert!(caught.message.contains("UNIQUE constraint failed"));
    assert_eq!(
        db::rows(&db, "SELECT * FROM external_resource_notes", []).unwrap(),
        before
    );
    assert_eq!(
        db::rows(&db, "SELECT * FROM atlassian_classifications", []).unwrap(),
        classes
    );
    assert_eq!(
        db::rows(&db, "SELECT * FROM atlassian_item_classifications", []).unwrap(),
        links
    );
    assert_eq!(
        db::rows(&db, "SELECT * FROM search_index", []).unwrap(),
        fts
    );
    assert_eq!(
        browse::atlassian_item_detail(&db, item).unwrap().unwrap()["attention"],
        "pinned"
    );
}
#[test]
fn unicode_fourteen_exact_tokens_and_query_refusals_preserve_local_scope() {
    let db = connection();
    let item = stub(&db, "UNICODE-1");
    db.execute(
        "UPDATE external_resources SET title=? WHERE id=?",
        rusqlite::params!["Straße Ａlpha ²Beta combining e\u{301}mark", item],
    )
    .unwrap();
    assert_eq!(
        browse::browse_inventory(&db, &json!({"q":"STRASSE alpha"})).unwrap()["matching_count"],
        1
    );
    assert_eq!(
        browse::browse_inventory(&db, &json!({"q":"²Beta"})).unwrap()["matching_count"],
        1
    );
    assert_eq!(
        browse::browse_inventory(&db, &json!({"q":"e mark"})).unwrap()["matching_count"],
        1
    );
    for query in ["!!!", "a b c d e f g h i j k l m"] {
        assert_eq!(
            browse::browse_inventory(&db, &json!({"q":query}))
                .unwrap_err()
                .code,
            "invalid-query"
        );
    }
    assert_eq!(
        browse::normalize_browse_filters(&json!({"site_id":"＋３"}))
            .unwrap_err()
            .code,
        "invalid-filter"
    );
    assert_eq!(
        browse::normalize_browse_filters(&json!({"site_id":"３_４"})).unwrap()["site_id"],
        34
    );
    assert_eq!(
        browse::normalize_browse_filters(&json!({"site_id":3.9})).unwrap()["site_id"],
        3
    );
    assert!(browse::normalize_browse_filters(&json!({"site_id":true})).is_err());
    let _ = Value::Null;
}

#[test]
fn retained_nonfinite_metadata_and_literal_number_maps_match_complete_frozen_reads() {
    let cases = localbrain_core::backend::json::decode(include_str!(
        "native_atlassian_fixtures/browse-nonfinite.json"
    ))
    .unwrap();
    for case in cases.as_array().unwrap() {
        let db = connection();
        support::restore(&db, &case["before"]);
        let resource = case["resource"].as_i64().unwrap();
        let changes = db.total_changes();
        let detail = browse::atlassian_item_detail(&db, resource)
            .unwrap()
            .unwrap();
        let inventory = browse::browse_inventory(&db, &json!({})).unwrap();
        let preview = browse::atlassian_item_preview(&db, resource, &json!({}))
            .unwrap()
            .unwrap();
        for (name, value) in [
            ("detail", &detail),
            ("inventory", &inventory),
            ("preview", &preview),
        ] {
            assert_eq!(*value, case["expected"][name], "complete frozen {name}");
        }
        assert_eq!(db.total_changes(), changes);
        assert_eq!(
            detail["metadata"]["literal"]["$serde_json::private::Number"],
            "not a number"
        );
        for value in [&detail, &inventory] {
            let error = localbrain_core::backend::json::strict_output(value).unwrap_err();
            assert_eq!(error.status, 500);
            assert_eq!(error.code, "json_nonfinite");
        }
        if preview["display_title"].is_number() {
            assert_eq!(
                localbrain_core::backend::json::strict_output(&preview)
                    .unwrap_err()
                    .code,
                "json_nonfinite"
            );
        } else {
            localbrain_core::backend::json::strict_output(&preview).unwrap();
        }
        localbrain_core::backend::json::strict_output(&detail["metadata"]["literal"]).unwrap();
    }
}
