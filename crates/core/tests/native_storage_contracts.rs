use localbrain_core::backend::{db, Config};
use rusqlite::Connection;
use serde_json::json;
fn setup() -> (tempfile::TempDir, Config) {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    (root, config)
}
fn replace_table(schema: &str, table: &str, modify: impl FnOnce(&str) -> String) -> String {
    let start = schema
        .find(&format!("CREATE TABLE IF NOT EXISTS {table} ("))
        .unwrap();
    let end = start + schema[start..].find("\n);").unwrap() + 3;
    format!(
        "{}{}{}",
        &schema[..start],
        modify(&schema[start..end]),
        &schema[end..]
    )
}
fn seed(config: &Config, schema: &str) -> Connection {
    let connection = db::connect(config).unwrap();
    connection.execute_batch(schema).unwrap();
    connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Keep','/synthetic')",[]).unwrap();
    connection
}
#[test]
fn maintenance_workstream_fk_rebuild_preserves_run_and_session_relationships() {
    let (_root, config) = setup();
    let legacy = replace_table(db::SCHEMA, "maintenance_runs", |ddl| {
        ddl.replace(
            "workstream_id INTEGER REFERENCES workstreams(id) ON DELETE SET NULL",
            "workstream_id INTEGER",
        )
    });
    let connection = seed(&config, &legacy);
    connection.execute_batch("INSERT INTO workstreams(id,name) VALUES (5,'Keep work'); INSERT INTO maintenance_runs(id,workstream_id,status,summary) VALUES ('run',5,'completed','Keep result'); INSERT INTO sessions(id,source_id,external_id,source_path,title,session_class,index_policy,maintenance_run_id) VALUES (7,1,'session','/synthetic','Keep session','maintenance','metadata_only','run'); INSERT INTO session_pins(session_id,pinned_at) VALUES (7,'fixed')").unwrap();
    let before = db::rows(&connection, "SELECT * FROM maintenance_runs", []).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::rows(&connection, "SELECT * FROM maintenance_runs", []).unwrap(),
        before
    );
    assert_eq!(
        db::row(
            &connection,
            "SELECT maintenance_run_id FROM sessions WHERE id=7",
            []
        )
        .unwrap()
        .unwrap()["maintenance_run_id"],
        "run"
    );
    connection
        .execute("DELETE FROM workstreams WHERE id=5", [])
        .unwrap();
    assert_eq!(
        db::row(
            &connection,
            "SELECT workstream_id,summary FROM maintenance_runs",
            []
        )
        .unwrap()
        .unwrap(),
        json!({"workstream_id":null,"summary":"Keep result"})
    );
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM session_pins", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
}
#[test]
fn legacy_session_run_constraint_upgrade_retains_children_and_rejects_invalid_links() {
    let (_root, config) = setup();
    let legacy = replace_table(db::SCHEMA, "sessions", |ddl| {
        ddl.replace("CHECK(session_class IN ('work', 'maintenance'))","").replace("CHECK(index_policy IN ('full', 'metadata_only'))","").replace("maintenance_run_id TEXT UNIQUE\n        REFERENCES maintenance_runs(id) ON DELETE SET NULL,","maintenance_run_id TEXT,").replace("    CHECK(\n        maintenance_run_id IS NULL\n        OR (\n            session_class = 'maintenance'\n            AND session_role = 'primary'\n            AND index_policy = 'metadata_only'\n        )\n    ),\n","")
    });
    let connection = seed(&config, &legacy);
    connection.execute_batch("INSERT INTO maintenance_runs(id) VALUES ('run'); INSERT INTO sessions(id,source_id,external_id,source_path,title,session_class,index_policy,maintenance_run_id) VALUES (7,1,'session','/synthetic','Keep','maintenance','metadata_only','run'); INSERT INTO session_pins(session_id,pinned_at) VALUES (7,'fixed')").unwrap();
    let before = db::rows(&connection, "SELECT * FROM sessions", []).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::rows(&connection, "SELECT * FROM sessions", []).unwrap(),
        before
    );
    assert!(connection
        .execute("UPDATE sessions SET session_class='work' WHERE id=7", [])
        .is_err());
    connection
        .execute("DELETE FROM maintenance_runs WHERE id='run'", [])
        .unwrap();
    assert_eq!(
        db::row(&connection, "SELECT maintenance_run_id FROM sessions", [])
            .unwrap()
            .unwrap()["maintenance_run_id"],
        serde_json::Value::Null
    );
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM session_pins", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
}
#[test]
fn external_url_uniqueness_is_removed_without_merging_curated_metadata() {
    let (_root, config) = setup();
    let legacy = replace_table(db::SCHEMA, "external_resources", |ddl| {
        ddl.replace("url TEXT NOT NULL,", "url TEXT NOT NULL UNIQUE,")
    });
    let connection = seed(&config, &legacy);
    connection.execute("INSERT INTO external_resources(id,resource_type,title,url,summary) VALUES (40,'url','First','https://example.test/path','Keep note')",[]).unwrap();
    let before = db::rows(&connection, "SELECT * FROM external_resources", []).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::rows(&connection, "SELECT * FROM external_resources", []).unwrap(),
        before
    );
    connection.execute("INSERT INTO external_resources(id,resource_type,title,url,summary) VALUES (41,'url','Second','https://example.test/path','Separate note')",[]).unwrap();
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM external_resources", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        2
    );
}
#[test]
fn optional_atlassian_access_rebuild_keeps_site_identity_custom_index_and_bindings() {
    let (_root, config) = setup();
    let legacy = replace_table(db::SCHEMA, "atlassian_sites", |ddl| {
        ddl.replace("source_instance_id INTEGER\n        REFERENCES external_source_instances(id) ON DELETE SET NULL,","source_instance_id INTEGER NOT NULL\n        REFERENCES external_source_instances(id) ON DELETE RESTRICT,")
    });
    let connection = seed(&config, &legacy);
    connection.execute_batch("INSERT INTO external_source_instances(id,instance_key,provider_kind,service,display_name) VALUES (2,'synthetic','mcp_gateway','jira','Keep source'); INSERT INTO atlassian_sites(id,source_instance_id,normalized_domain,display_name,canonical_base_url) VALUES (9,2,'example.test','Keep site','https://example.test'); CREATE INDEX synthetic_site_name ON atlassian_sites(display_name)").unwrap();
    let before = db::rows(&connection, "SELECT * FROM atlassian_sites", []).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::rows(&connection, "SELECT * FROM atlassian_sites", []).unwrap(),
        before
    );
    assert!(db::row(
        &connection,
        "SELECT 1 FROM sqlite_master WHERE name='synthetic_site_name'",
        []
    )
    .unwrap()
    .is_some());
    assert_eq!(
        db::row(
            &connection,
            "SELECT site_id,source_instance_id FROM atlassian_site_bindings",
            []
        )
        .unwrap()
        .unwrap(),
        json!({"site_id":9,"source_instance_id":2})
    );
    connection
        .execute("DELETE FROM external_source_instances WHERE id=2", [])
        .unwrap();
    assert_eq!(
        db::row(
            &connection,
            "SELECT id,source_instance_id,display_name FROM atlassian_sites",
            []
        )
        .unwrap()
        .unwrap(),
        json!({"id":9,"source_instance_id":null,"display_name":"Keep site"})
    );
}
#[test]
fn skill_observation_extension_preserves_existing_ledger_and_explicit_indexes() {
    let (_root, config) = setup();
    let legacy = replace_table(db::SCHEMA, "skill_observations", |ddl| {
        let ddl=ddl.replace("    request_key TEXT CHECK(request_key IS NULL OR length(request_key) BETWEEN 1 AND 160),\n","");
        regex::Regex::new(r"(?s)signal_kind IN \(.*?\)")
            .unwrap()
            .replace(
                &ddl,
                "signal_kind IN ('claude_skill_tool','codex_skill_context')",
            )
            .into_owned()
    });
    let connection = seed(&config, &legacy);
    connection.execute_batch("INSERT INTO skill_observations(id,source_id,provider_kind,external_session_id,native_event_id,skill_name,skill_group_key,signal_kind,source_line) VALUES ('keep',1,'codex','session','event','Review','review','codex_skill_context',1); CREATE INDEX synthetic_skill_name ON skill_observations(skill_name)").unwrap();
    let before = db::rows(&connection, "SELECT * FROM skill_observations", []).unwrap()[0].clone();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    let after = db::row(&connection, "SELECT * FROM skill_observations", [])
        .unwrap()
        .unwrap();
    for (key, value) in before.as_object().unwrap() {
        assert_eq!(&after[key], value);
    }
    assert_eq!(after["request_key"], serde_json::Value::Null);
    assert!(db::row(
        &connection,
        "SELECT 1 FROM sqlite_master WHERE name='synthetic_skill_name'",
        []
    )
    .unwrap()
    .is_some());
    connection.execute("UPDATE skill_observations SET signal_kind='codex_skill_script',request_key='request' WHERE id='keep'",[]).unwrap();
}
