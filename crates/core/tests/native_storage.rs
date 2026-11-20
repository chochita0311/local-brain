use localbrain_core::backend::{db, references, sources, storage, Config};
use rusqlite::{params, Connection};
use serde_json::json;
use std::{
    fs,
    os::{
        fd::AsFd,
        unix::{fs::symlink, fs::MetadataExt},
    },
    path::PathBuf,
};
fn setup() -> (tempfile::TempDir, Config) {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    (root, config)
}
fn seed(config: &Config, schema: &str) -> Connection {
    let connection = db::connect(config).unwrap();
    connection.execute_batch(schema).unwrap();
    connection
}
const REVISION:&str="CHECK(session_contract_version IS NULL OR (typeof(session_contract_version) = 'integer' AND session_contract_version > 0))";
fn legacy_revisions() -> String {
    db::SCHEMA.replace(
        &format!("session_contract_version INTEGER {REVISION}"),
        "session_contract_version TEXT",
    )
}
fn seed_source(connection: &Connection) {
    connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,'codex','Synthetic','/synthetic')",[]).unwrap();
}
fn seed_file(connection: &Connection, revision: &str) {
    connection.execute("INSERT INTO source_files(id,source_id,path,size_bytes,mtime_ns,last_scanned_at,status,error,session_contract_version,usage_contract_version,reference_contract_version) VALUES (7,1,'/synthetic/a.jsonl',123,456,'fixed','error','keep',?,'usage','refs')",[revision]).unwrap();
}
fn schema(connection: &Connection, table: &str) -> String {
    connection
        .query_row(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            [table],
            |row| row.get(0),
        )
        .unwrap()
}
#[test]
fn fresh_database_is_private_and_idempotent() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        connection
            .query_row("PRAGMA foreign_keys", [], |row| row.get::<_, i64>(0))
            .unwrap(),
        1
    );
    assert_eq!(
        connection
            .query_row("PRAGMA journal_mode", [], |row| row.get::<_, String>(0))
            .unwrap(),
        "wal"
    );
    let info = fs::metadata(&config.database_path).unwrap();
    assert_eq!(info.mode() & 0o777, 0o600);
    assert_eq!(
        fs::metadata(&config.data_dir).unwrap().mode() & 0o777,
        0o700
    );
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM sources", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        0
    );
    connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (9,'codex','Keep','/synthetic')",[]).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    assert_eq!(
        db::row(
            &db::connect(&config).unwrap(),
            "SELECT name FROM sources WHERE id=9",
            []
        )
        .unwrap()
        .unwrap()["name"],
        "Keep"
    );
    assert!(!fs::read_dir(&config.data_dir).unwrap().any(|entry| entry
        .unwrap()
        .file_name()
        .to_string_lossy()
        .ends_with(".bak")));
}
#[test]
fn rows_preserve_types_column_order_duplicate_names_and_invalid_utf8_refusal() {
    let connection = Connection::open_in_memory().unwrap();
    let row = db::row(
        &connection,
        "SELECT 7 AS z,2.5 AS a,NULL AS n,X'0102' AS b,'first' AS same,'last' AS same",
        [],
    )
    .unwrap()
    .unwrap();
    assert_eq!(
        row,
        json!({"z":7,"a":2.5,"n":null,"b":[1,2],"same":"first"})
    );
    assert_eq!(
        row.as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<Vec<_>>(),
        ["z", "a", "n", "b", "same"]
    );
    assert!(db::row(&connection, "SELECT CAST(X'FF' AS TEXT)", []).is_err());
    assert_eq!(
        db::row(&connection, "SELECT 1 AS a,2 AS A", [])
            .unwrap()
            .unwrap(),
        json!({"a":1,"A":1})
    );
    assert_eq!(
        db::row(
            &connection,
            "SELECT 'first' AS value UNION ALL SELECT CAST(X'FF' AS TEXT)",
            []
        )
        .unwrap()
        .unwrap()["value"],
        "first"
    );
}
#[test]
fn numeric_revision_migration_preserves_other_lanes_and_original_backup() {
    let (_root, config) = setup();
    let connection = seed(&config, &legacy_revisions());
    seed_source(&connection);
    seed_file(&connection, "codex-session-v12-empty-page-controls");
    connection
        .execute(
            "CREATE INDEX idx_source_files_synthetic ON source_files(status,path)",
            [],
        )
        .unwrap();
    let before = db::row(&connection, "SELECT * FROM source_files", [])
        .unwrap()
        .unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    let mut expected = before;
    expected["session_contract_version"] = 12.into();
    assert_eq!(
        db::row(&connection, "SELECT * FROM source_files", [])
            .unwrap()
            .unwrap(),
        expected
    );
    assert!(schema(&connection, "source_files").contains(REVISION));
    assert!(db::row(
        &connection,
        "SELECT 1 FROM sqlite_master WHERE name='idx_source_files_synthetic'",
        []
    )
    .unwrap()
    .is_some());
    let backup = PathBuf::from(format!(
        "{}-pre-session-revision-v1.bak",
        config.database_path.display()
    ));
    let saved = fs::read(&backup).unwrap();
    assert_eq!(
        db::row(
            &Connection::open(&backup).unwrap(),
            "SELECT session_contract_version FROM source_files",
            []
        )
        .unwrap()
        .unwrap()["session_contract_version"],
        "codex-session-v12-empty-page-controls"
    );
    drop(connection);
    db::initialize(&config).unwrap();
    assert_eq!(fs::read(backup).unwrap(), saved);
}
#[test]
fn unknown_and_mismatched_session_revisions_stop_before_changes() {
    for (provider, revision) in [
        ("codex", "unknown-future"),
        ("claude", "codex-session-v12-empty-page-controls"),
    ] {
        let (_root, config) = setup();
        let connection = seed(&config, &legacy_revisions());
        connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES (1,?,'Synthetic','/synthetic')",[provider]).unwrap();
        seed_file(&connection, revision);
        let before = schema(&connection, "source_files");
        drop(connection);
        assert!(db::initialize(&config).is_err());
        let connection = db::connect(&config).unwrap();
        assert_eq!(schema(&connection, "source_files"), before);
        assert_eq!(
            db::row(
                &connection,
                "SELECT session_contract_version FROM source_files",
                []
            )
            .unwrap()
            .unwrap()["session_contract_version"],
            revision
        );
    }
}
#[test]
fn revision_unknown_constraints_triggers_and_incoming_children_are_preserved() {
    for suffix in ["CHECK(size_bytes >= 0)", "UNIQUE(path) ON CONFLICT IGNORE"] {
        let (_root, config) = setup();
        let legacy = legacy_revisions().replacen(
            "UNIQUE(source_id, path)",
            &format!("UNIQUE(source_id, path), {suffix}"),
            1,
        );
        let connection = seed(&config, &legacy);
        seed_source(&connection);
        seed_file(&connection, "codex-session-v12-empty-page-controls");
        let before = schema(&connection, "source_files");
        drop(connection);
        assert!(db::initialize(&config).is_err());
        let connection = db::connect(&config).unwrap();
        assert_eq!(schema(&connection, "source_files"), before);
        assert_eq!(
            connection
                .query_row("SELECT COUNT(*) FROM source_files", [], |row| row
                    .get::<_, i64>(0))
                .unwrap(),
            1
        );
    }
    for extra in ["CREATE TRIGGER synthetic_source_rule AFTER INSERT ON source_files BEGIN SELECT 1; END;","CREATE TABLE synthetic_child(id INTEGER PRIMARY KEY,file_id INTEGER REFERENCES source_files(id) ON DELETE CASCADE); INSERT INTO synthetic_child(file_id) VALUES (7);"]{let (_root,config)=setup();let connection=seed(&config,&legacy_revisions());seed_source(&connection);seed_file(&connection,"codex-session-v12-empty-page-controls");connection.execute_batch(extra).unwrap();drop(connection);assert!(db::initialize(&config).is_err());let connection=db::connect(&config).unwrap();assert_eq!(connection.query_row("SELECT COUNT(*) FROM source_files",[],|row|row.get::<_,i64>(0)).unwrap(),1);if extra.contains("synthetic_child"){assert_eq!(connection.query_row("SELECT COUNT(*) FROM synthetic_child",[],|row|row.get::<_,i64>(0)).unwrap(),1);}}
}
#[test]
fn title_upgrade_retains_titles_children_and_positions_display_title() {
    let (_root, config) = setup();
    let legacy = db::SCHEMA.replacen("    display_title TEXT,\n", "", 1);
    assert_ne!(legacy, db::SCHEMA);
    let connection = seed(&config, &legacy);
    seed_source(&connection);
    connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (17,1,'one','/synthetic/one','Imported title')",[]).unwrap();
    connection
        .execute(
            "INSERT INTO session_pins(session_id,pinned_at) VALUES (17,'fixed')",
            [],
        )
        .unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    let columns = db::rows(&connection, "PRAGMA table_info(sessions)", []).unwrap();
    let title = columns
        .iter()
        .position(|column| column["name"] == "title")
        .unwrap();
    assert_eq!(columns[title + 1]["name"], "display_title");
    assert_eq!(
        db::row(
            &connection,
            "SELECT title,display_title FROM sessions WHERE id=17",
            []
        )
        .unwrap()
        .unwrap(),
        json!({"title":"Imported title","display_title":null})
    );
    assert_eq!(
        connection
            .query_row("SELECT session_id FROM session_pins", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        17
    );
}
#[test]
fn title_upgrade_refuses_unknown_session_constraint_without_dropping_it() {
    let (_root, config) = setup();
    let legacy = db::SCHEMA
        .replacen("    display_title TEXT,\n", "", 1)
        .replacen(
            "    title TEXT NOT NULL,",
            "    title TEXT NOT NULL CHECK(length(title) < 200),",
            1,
        );
    let connection = seed(&config, &legacy);
    let before = schema(&connection, "sessions");
    drop(connection);
    assert!(db::initialize(&config).is_err());
    assert_eq!(schema(&db::connect(&config).unwrap(), "sessions"), before);
}
#[test]
fn legacy_usage_name_and_attribution_are_repaired_preserving_rows() {
    let (_root, config) = setup();
    let legacy = db::SCHEMA.replace("usage_records", "usage_facts").replace(
        "CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned'))",
        "",
    );
    let connection = seed(&config, &legacy);
    assert!(schema(&connection, "usage_facts").contains("attribution_basis"));
    seed_source(&connection);
    connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (11,1,'usage-session','/synthetic/usage','Keep')",[]).unwrap();
    connection.execute("INSERT INTO usage_price_snapshots(id,label,source_ref,calculator_version,created_at) VALUES ('synthetic-frozen','Keep','local','synthetic','fixed')",[]).unwrap();
    connection.execute("INSERT INTO usage_facts(id,source_id,session_id,source_record_id,source_line,input_tokens,total_semantics,capability_state,capability_json,calculation_state,estimated_cost_usd,price_snapshot_id,calculator_version,calculated_at,attribution_basis,attributed_at,project_name_snapshot) VALUES ('keep',1,11,'record',42,17,'source','complete','{}','priced','0.123','synthetic-frozen','synthetic','fixed','git_root','fixed','Keep project')",[]).unwrap();
    let retained = db::rows(&connection, "SELECT * FROM usage_facts", []).unwrap();
    let before = db::rows(&connection, "PRAGMA table_info(usage_facts)", []).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::rows(&connection, "PRAGMA table_info(usage_records)", []).unwrap(),
        before
    );
    assert!(db::row(
        &connection,
        "SELECT 1 FROM sqlite_master WHERE name='usage_facts'",
        []
    )
    .unwrap()
    .is_none());
    assert!(schema(&connection, "usage_records")
        .contains("CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned'))"));
    assert_eq!(
        db::rows(
            &connection,
            "SELECT * FROM usage_records WHERE id='keep'",
            []
        )
        .unwrap(),
        retained
    );
}
#[test]
fn source_alias_upgrade_preserves_primary_keys_file_order_and_unknown_files() {
    let (root, config) = setup();
    let legacy=db::SCHEMA.replacen("    provider_kind TEXT NOT NULL DEFAULT 'unknown'\n        CHECK(length(trim(provider_kind)) BETWEEN 1 AND 64),\n","    kind TEXT NOT NULL UNIQUE,\n",1);
    let connection = seed(&config, &legacy);
    let source_root = root.path().join("codex");
    fs::create_dir(&source_root).unwrap();
    connection
        .execute(
            "INSERT INTO sources(id,kind,name,root_path) VALUES (13,'codex','Known',?)",
            [source_root.to_string_lossy().as_ref()],
        )
        .unwrap();
    connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES (21,13,'one','/synthetic','Keep')",[]).unwrap();
    let text=format!("schema_version = 1\n[[session_sources]]\nsource_key = 'codex'\nprovider_kind = 'codex'\ndisplay_label = 'Known'\nroot = {:?}\n",source_root.to_string_lossy());
    fs::write(config.data_dir.join("session-sources.toml"), text).unwrap();
    drop(connection);
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    assert!(!schema(&connection, "sources").contains("kind TEXT NOT NULL UNIQUE"));
    assert_eq!(
        db::row(&connection, "SELECT id,source_id,title FROM sessions", [])
            .unwrap()
            .unwrap(),
        json!({"id":21,"source_id":13,"title":"Keep"})
    );
    let parsed = sources::load_session_source_settings(&config).unwrap();
    assert!(!parsed.file_error);
    assert_eq!(parsed.entries[0].source_id, 13);
    assert_eq!(parsed.entries[0].root, source_root);
}
#[test]
fn source_settings_support_stable_identity_rename_disable_reorder_and_revision_conflicts() {
    let (root, config) = setup();
    db::initialize(&config).unwrap();
    let state = sources::source_inventory(&config).unwrap();
    assert_eq!(state["sources"], json!([]));
    let first = root.path().join("first");
    let second = root.path().join("second");
    fs::create_dir(&first).unwrap();
    fs::create_dir(&second).unwrap();
    let state=sources::update_source(&config,&json!({"revision":state["revision"],"provider_kind":"codex","display_label":"First","root":first})).unwrap();
    let id = state["sources"][0]["id"].as_i64().unwrap();
    let old_revision = state["revision"].clone();
    let state=sources::update_source(&config,&json!({"revision":state["revision"],"source_id":id,"provider_kind":"codex","display_label":"Renamed","root":first})).unwrap();
    assert_eq!(state["sources"][0]["id"], id);
    assert_eq!(state["sources"][0]["name"], "Renamed");
    assert!(sources::update_source(
        &config,
        &json!({"revision":old_revision,"source_id":id,"action":"remove"})
    )
    .is_err());
    assert!(sources::update_source(&config,&json!({"revision":state["revision"],"provider_kind":"claude","display_label":"Overlap","root":first})).is_err());
    let state=sources::update_source(&config,&json!({"revision":state["revision"],"provider_kind":"claude","display_label":"Second","root":second})).unwrap();
    let id2 = state["sources"][1]["id"].as_i64().unwrap();
    let state = sources::update_source(
        &config,
        &json!({"revision":state["revision"],"action":"reorder","source_ids":[id2,id]}),
    )
    .unwrap();
    assert_eq!(state["sources"][0]["id"], id2);
    let state = sources::update_source(
        &config,
        &json!({"revision":state["revision"],"source_id":id,"action":"remove"}),
    )
    .unwrap();
    assert!(!state["sources"]
        .as_array()
        .unwrap()
        .iter()
        .find(|source| source["id"] == id)
        .unwrap()["registered"]
        .as_bool()
        .unwrap());
    assert_eq!(sources::registered_session_roots(&config).unwrap().len(), 1);
}
#[test]
fn malformed_sources_and_omitted_retained_sources_never_remove_data() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    seed_source(&connection);
    drop(connection);
    let state = sources::source_inventory(&config).unwrap();
    assert_eq!(state["sources"][0]["id"], 1);
    let path = config.data_dir.join("session-sources.toml");
    fs::write(&path, "schema_version = 2\nsession_sources = []\n").unwrap();
    let state = sources::source_inventory(&config).unwrap();
    assert_eq!(state["sources"][0]["availability"], "config_missing");
    assert_eq!(state["sources"][0]["registered"], false);
    fs::write(&path, "schema_version = 99\nsession_sources = []\n").unwrap();
    let parsed = sources::load_session_source_settings(&config).unwrap();
    assert!(parsed.file_error);
    assert_eq!(parsed.diagnostics[0].code, "unsupported_schema_version");
    assert!(fs::read_to_string(path).unwrap().contains("99"));
    assert_eq!(
        db::connect(&config)
            .unwrap()
            .query_row("SELECT COUNT(*) FROM sources", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
}
#[test]
fn malformed_toml_values_are_isolated_to_their_source_profiles() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    let good = config.home_dir.join("good-source");
    fs::create_dir_all(&good).unwrap();
    let connection = db::connect(&config).unwrap();
    connection
        .execute(
            "INSERT INTO sources(id,provider_kind,name,root_path) VALUES (7,'codex','Synthetic',?)",
            [good.to_str().unwrap()],
        )
        .unwrap();
    drop(connection);
    let path = config.data_dir.join("session-sources.toml");
    let original = format!(concat!(
        "schema_version=2\n[[session_sources]]\nsource_id=7\nprovider_kind='codex'\ndisplay_label='Synthetic'\nroot={}\n",
        "[[session_sources]]\nsource_id=8\nprovider_kind='codex'\ndisplay_label='Bad Enabled'\nroot='/synthetic-bad-bool'\nenabled=inf\n",
        "[[session_sources]]\nsource_id=9\nprovider_kind='codex'\ndisplay_label='Bad Color'\nroot='/synthetic-bad-color'\ncolor=2026-11-01\n",
        "[[session_sources]]\nsource_id=1267650600228229401496703205376\nprovider_kind='codex'\ndisplay_label='Bad ID'\nroot='/synthetic-bad-id'\n"
    ), json!(good));
    storage::files::atomic_write(&path, original.as_bytes()).unwrap();
    let parsed = sources::load_session_source_settings(&config).unwrap();
    assert!(!parsed.file_error);
    assert_eq!(
        parsed
            .entries
            .iter()
            .map(|entry| entry.source_id)
            .collect::<Vec<_>>(),
        [7]
    );
    assert_eq!(
        parsed
            .diagnostics
            .iter()
            .map(|issue| issue.code.as_str())
            .collect::<Vec<_>>(),
        ["invalid_enabled", "invalid_color", "invalid_source_id"]
    );
    assert_eq!(
        sources::registered_session_roots(&config)
            .unwrap()
            .keys()
            .copied()
            .collect::<Vec<_>>(),
        [7]
    );
    let settings = sources::source_inventory(&config).unwrap();
    assert_eq!(settings["sources"][0]["registered"], true);
    assert_eq!(settings["diagnostics"][0]["code"], "invalid_enabled");
    let invalid = sources::update_source(
        &config,
        &json!({"revision":settings["revision"],"source_id":7,"action":"remove"}),
    )
    .unwrap_err();
    assert_eq!(invalid.status, 409);
    assert_eq!(invalid.code, "conflict");
    assert!(invalid.message.contains("기존 소스 설정의 오류"));
    let stale = sources::update_source(
        &config,
        &json!({"revision":"stale","source_id":7,"action":"remove"}),
    )
    .unwrap_err();
    assert_eq!(stale.status, 409);
    assert!(stale.message.contains("목록을 다시 불러온 뒤"));
    assert_eq!(fs::read_to_string(path).unwrap(), original);
    assert_eq!(sources::source_inventory(&config).unwrap(), settings);
}
#[test]
fn redundant_separators_in_home_relative_source_keep_registered_identity() {
    let (_root, config) = setup();
    let source_root = config.home_dir.join("retained");
    fs::create_dir_all(&source_root).unwrap();
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    let settings_path = config.data_dir.join("session-sources.toml");
    let settings = |root: &str| {
        sources::registry::session_sources_text(&[json!({
            "source_id":7, "provider_kind":"codex", "display_label":"Synthetic",
            "root":root, "enabled":true
        })])
        .unwrap()
    };
    fs::write(&settings_path, settings("~/retained")).unwrap();
    let inventory = sources::source_inventory(&config).unwrap();
    let id = inventory["sources"][0]["id"].as_i64().unwrap();
    connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES(1,?,'synthetic','sample.jsonl','Retained')",[id]).unwrap();
    fs::write(settings_path, settings("~//retained")).unwrap();

    let inventory = sources::source_inventory(&config).unwrap();
    assert_eq!(inventory["sources"][0]["id"], id);
    assert_eq!(inventory["sources"][0]["registered"], true);
    assert_eq!(
        db::row(&connection, "SELECT source_id FROM sessions WHERE id=1", [])
            .unwrap()
            .unwrap()["source_id"],
        id
    );
}
#[test]
fn operation_leases_are_reentrant_and_exclude_other_threads_even_after_outer_drop() {
    let (_root, config) = setup();
    let outer = storage::operation_lock(&config, "one").unwrap();
    let inner = storage::operation_lock(&config, "two").unwrap();
    let _fd = inner.as_fd();
    drop(outer);
    let other = config.clone();
    assert!(
        std::thread::spawn(move || storage::operation_lock(&other, "other").is_err())
            .join()
            .unwrap()
    );
    drop(inner);
    assert!(storage::operation_lock(&config, "released").is_ok());
}
#[test]
fn runtime_symlink_git_and_hardlinked_database_are_refused() {
    let (root, config) = setup();
    fs::create_dir(&config.data_dir).unwrap();
    let linked = root.path().join("linked");
    symlink(&config.data_dir, &linked).unwrap();
    assert!(db::connect(&Config::for_data_dir(linked)).is_err());
    let git = root.path().join("checkout");
    fs::create_dir_all(git.join(".git")).unwrap();
    assert!(db::connect(&Config::for_data_dir(git.join("runtime"))).is_err());
    fs::write(&config.database_path, []).unwrap();
    fs::hard_link(&config.database_path, root.path().join("hardlink")).unwrap();
    assert!(db::connect(&config).is_err());
}
#[test]
fn accounting_deduplicates_hardlinks_skips_nested_symlinks_and_reports_future_volume() {
    let (root, config) = setup();
    fs::create_dir(&config.data_dir).unwrap();
    fs::write(config.data_dir.join("a"), b"12345").unwrap();
    fs::hard_link(config.data_dir.join("a"), config.data_dir.join("b")).unwrap();
    let external = root.path().join("external");
    fs::create_dir(&external).unwrap();
    fs::write(external.join("large"), b"do not count").unwrap();
    symlink(&external, config.data_dir.join("nested-link")).unwrap();
    assert_eq!(
        storage::accounting::directory_size(&config.data_dir),
        json!({"bytes":5,"state":"complete"})
    );
    let status = storage::storage_status(&config).unwrap();
    assert_eq!(status["data_bytes"], 5);
    assert_eq!(status["cache_bytes"], 0);
    assert_eq!(status["locations"]["cache"]["state"], "missing");
    assert!(status["locations"]["cache"]["volume"]["free_bytes"]
        .as_u64()
        .is_some());
}
#[test]
fn same_installation_backup_restore_is_consistent_and_backend_lease_prevents_early_restore() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    seed_source(&connection);
    drop(connection);
    let settings = b"schema_version = 1\ncustom_date = 2026-11-01\ncustom_number = inf\ncustom_integer = 1267650600228229401496703205376\n";
    let settings_path = config.data_dir.join("settings.toml");
    storage::files::atomic_write(&settings_path, settings).unwrap();
    let backup = storage::create_backup(&config).unwrap();
    let validated = tempfile::tempdir().unwrap();
    let hashes = storage::validate_backup(&backup.archive, validated.path(), &config).unwrap();
    assert!(hashes.contains_key("localbrain.db"));
    assert!(!hashes.contains_key("installation-id"));
    assert_eq!(
        fs::read(validated.path().join("settings.toml")).unwrap(),
        settings
    );
    let lease = storage::backend_storage_lease(&config).unwrap();
    let connection = db::connect(&config).unwrap();
    connection
        .execute("UPDATE sources SET name='Changed' WHERE id=1", [])
        .unwrap();
    drop(connection);
    storage::files::atomic_write(&settings_path, b"schema_version = 1\n").unwrap();
    storage::recovery::stage_restore(&config, &backup.archive).unwrap();
    assert!(storage::backend_storage_lease(&config).is_err());
    drop(lease);
    let restored = storage::backend_storage_lease(&config).unwrap();
    assert_eq!(fs::read(&settings_path).unwrap(), settings);
    assert_eq!(
        db::row(
            &db::connect(&config).unwrap(),
            "SELECT name FROM sources WHERE id=1",
            []
        )
        .unwrap()
        .unwrap()["name"],
        "Synthetic"
    );
    assert!(config
        .data_dir
        .join("recovery/before/localbrain.db")
        .is_file());
    assert!(!config.data_dir.join("restore-pending.zip").exists());
    drop(restored);
}
#[test]
fn archive_paths_and_foreign_installations_are_refused_before_publication() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    let backup = storage::create_backup(&config).unwrap();
    let (_other_root, other) = setup();
    db::initialize(&other).unwrap();
    let target = tempfile::tempdir().unwrap();
    assert!(storage::validate_backup(&backup.archive, target.path(), &other).is_err());
    let path = config.data_dir.join("malicious.zip");
    let file = fs::File::create(&path).unwrap();
    let mut zip = zip::ZipWriter::new(file);
    zip.start_file("../escape", zip::write::SimpleFileOptions::default())
        .unwrap();
    use std::io::Write;
    zip.write_all(b"private").unwrap();
    zip.finish().unwrap();
    let staged = config.data_dir.join("must-stay-missing");
    assert!(storage::validate_backup(&path, &staged, &config).is_err());
    assert!(!staged.exists());
}
#[test]
fn restore_refuses_invalid_toml_and_noninteger_schema_versions() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    for settings in [
        "schema_version = 1\ninvalid = [\n",
        "schema_version = \"1\"\n",
    ] {
        storage::files::atomic_write(&config.data_dir.join("settings.toml"), settings.as_bytes())
            .unwrap();
        let backup = storage::create_backup(&config).unwrap();
        assert!(storage::recovery::stage_restore(&config, &backup.archive).is_err());
        assert!(!config.data_dir.join("restore-pending.zip").exists());
    }
}
#[test]
fn reference_url_identity_preserves_provider_grammar_and_unicode14_bounds() {
    assert_eq!(unicode_general_category::UNICODE_VERSION, (14, 0, 0));
    assert_eq!(
        unicode_general_category::get_general_category('\u{1fae8}'),
        unicode_general_category::GeneralCategory::Unassigned
    );
    let issue =
        references::parse_url("HTTPS://jira.example.test/browse/proj-12?tracking=private").unwrap();
    assert_eq!(
        issue.normalized_url,
        "https://jira.example.test/browse/PROJ-12"
    );
    assert_eq!(
        issue.target_key,
        references::parse_url("https://jira.example.test/issues/PROJ-12")
            .unwrap()
            .target_key
    );
    assert!(references::parse_url(&format!(
        "https://{}:{}@{}/path",
        "user", "password", "example.test"
    ))
    .is_none());
    assert!(references::parse_url("https://example.test/wiki/spaces/\u{1fae8}").is_none());
    assert_eq!(
        references::parse_url("https://example.test/path?private=true#fragment")
            .unwrap()
            .normalized_url,
        "https://example.test/path"
    );
    let page =
        references::parse_url("https://example.test/wiki/spaces/ＴＥＳＴ/pages/000123/Title")
            .unwrap();
    assert_eq!(
        page.normalized_url,
        "https://example.test/wiki/spaces/TEST/pages/123"
    );
    assert_eq!(
        page.target_key,
        references::parse_url("https://example.test/wiki/pages/viewpage.action?pageId=123")
            .unwrap()
            .target_key
    );
    assert!(
        references::parse_url("https://example.test/browse/PROJ-12?selectedIssue=%GG").is_none()
    );
}

#[test]
fn failed_source_publication_restores_toml_and_database_without_consuming_ids() {
    let (root, config) = setup();
    db::initialize(&config).unwrap();
    let path = root.path().join("source");
    fs::create_dir(&path).unwrap();
    let state = sources::source_inventory(&config).unwrap();
    let state=sources::update_source(&config,&json!({"revision":state["revision"],"provider_kind":"codex","display_label":"Before","root":path})).unwrap();
    let id = state["sources"][0]["id"].as_i64().unwrap();
    let settings = config.data_dir.join("session-sources.toml");
    let before = fs::read(&settings).unwrap();
    let connection = db::connect(&config).unwrap();
    connection.execute_batch("CREATE TRIGGER synthetic_refusal BEFORE UPDATE ON sources WHEN NEW.name='Refused' BEGIN SELECT RAISE(ABORT,'synthetic failure after file publication'); END").unwrap();
    drop(connection);
    assert!(sources::update_source(&config,&json!({"revision":state["revision"],"source_id":id,"provider_kind":"codex","display_label":"Refused","root":path})).is_err());
    assert_eq!(fs::read(settings).unwrap(), before);
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::row(&connection, "SELECT name FROM sources WHERE id=?", [id])
            .unwrap()
            .unwrap()["name"],
        "Before"
    );
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM sources", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
}
#[test]
fn reconnect_refuses_newer_parser_revision_without_erasing_it_or_settings() {
    let (root, config) = setup();
    db::initialize(&config).unwrap();
    let old = root.path().join("old");
    let new = root.path().join("new");
    fs::create_dir(&old).unwrap();
    fs::create_dir(&new).unwrap();
    let state = sources::source_inventory(&config).unwrap();
    let state=sources::update_source(&config,&json!({"revision":state["revision"],"provider_kind":"codex","display_label":"Keep","root":old})).unwrap();
    let id = state["sources"][0]["id"].as_i64().unwrap();
    let connection = db::connect(&config).unwrap();
    connection.execute("INSERT INTO source_files(source_id,path,size_bytes,mtime_ns,last_scanned_at,session_contract_version) VALUES (?,?,0,0,'fixed',999)",params![id,old.join("a.jsonl").to_string_lossy()]).unwrap();
    drop(connection);
    let path = config.data_dir.join("session-sources.toml");
    let before = fs::read(&path).unwrap();
    let failure=sources::update_source(&config,&json!({"revision":state["revision"],"source_id":id,"provider_kind":"codex","display_label":"Keep","root":new,"action":"reconnect","confirm_same_source":true})).unwrap_err();
    assert!(failure.message.contains("newer Session parser"));
    assert_eq!(fs::read(path).unwrap(), before);
    assert!(!config.data_dir.join("source-reconnect.json").exists());
    assert_eq!(
        db::row(
            &db::connect(&config).unwrap(),
            "SELECT session_contract_version FROM source_files",
            []
        )
        .unwrap()
        .unwrap()["session_contract_version"],
        999
    );
}
#[test]
fn unknown_source_shape_rolls_back_published_upgrade_files_and_health() {
    let (root, config) = setup();
    let legacy=db::SCHEMA.replacen("    provider_kind TEXT NOT NULL DEFAULT 'unknown'\n        CHECK(length(trim(provider_kind)) BETWEEN 1 AND 64),\n","    kind TEXT NOT NULL UNIQUE,\n",1);
    let connection = seed(&config, &legacy);
    let folder = root.path().join("source");
    fs::create_dir(&folder).unwrap();
    connection
        .execute(
            "INSERT INTO sources(id,kind,name,root_path) VALUES (4,'codex','Keep',?)",
            [folder.to_string_lossy().as_ref()],
        )
        .unwrap();
    connection.execute_batch("ALTER TABLE sources ADD COLUMN future_state TEXT; UPDATE sources SET future_state='retained'").unwrap();
    let path = config.data_dir.join("session-sources.toml");
    let before=format!("schema_version=1\n[[session_sources]]\nsource_key='codex'\nprovider_kind='codex'\ndisplay_label='Keep'\nroot={:?}\n",folder.to_string_lossy()).into_bytes();
    fs::write(&path, &before).unwrap();
    let health = config.data_dir.join("session-sync-state.json");
    let health_before =
        br#"{"completed_at":100,"report":{"sources":[{"source_key":"codex","imported":7}]}}"#;
    fs::write(&health, health_before).unwrap();
    drop(connection);
    let failure = db::initialize(&config).unwrap_err();
    assert!(failure.message.contains("unexpected columns"));
    assert_eq!(fs::read(path).unwrap(), before);
    assert_eq!(fs::read(health).unwrap(), health_before);
    let connection = db::connect(&config).unwrap();
    assert_eq!(
        db::row(
            &connection,
            "SELECT kind,future_state FROM sources WHERE id=4",
            []
        )
        .unwrap()
        .unwrap(),
        json!({"kind":"codex","future_state":"retained"})
    );
    assert!(!schema(&connection, "sources").contains("provider_kind"));
}
#[test]
fn malformed_workspace_metadata_is_rejected_from_backup_and_never_published() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    let path = config.data_dir.join("terminal-workspaces.json");
    let before=br#"{"schema":1,"generation":null,"items":[{"id":"invalid","name":"Keep","cwd":"","tabs":[]}]}"#;
    fs::write(&path, before).unwrap();
    let backup = storage::create_backup(&config).unwrap();
    let target = tempfile::tempdir().unwrap();
    assert!(storage::validate_backup(&backup.archive, target.path(), &config).is_err());
    assert_eq!(fs::read(path).unwrap(), before);
    assert!(!config.data_dir.join("restore-pending.zip").exists());
}
#[test]
fn storage_migration_ignores_unregistered_feature_caches_and_refuses_collisions() {
    let (_root, config) = setup();
    db::initialize(&config).unwrap();
    let unowned = config.data_dir.join("session-simulation");
    fs::create_dir(&unowned).unwrap();
    fs::write(unowned.join("private-unknown"), b"preserved").unwrap();
    let preview = storage::migrate_storage(&config, false, false, None).unwrap();
    assert_eq!(preview["eligible_directories"], 0);
    assert_eq!(preview["preserved_directories"], 0);
    assert!(unowned.join("private-unknown").is_file());
    let model = config.data_dir.join("qwen3-4b");
    fs::create_dir(&model).unwrap();
    fs::write(model.join("owner.json"),br#"{"owner":"localbrain.work-context-model.v1","model":"Qwen/Qwen3-4B","revision":"1cfa9a7208912126459214e8b04321603b3df60c"}"#).unwrap();
    fs::write(model.join("model.json"),br#"{"owner":"localbrain.work-context-model.v2","model_id":"Qwen/Qwen3-4B","revision":"1cfa9a7208912126459214e8b04321603b3df60c"}"#).unwrap();
    let preview = storage::migrate_storage(&config, false, false, None).unwrap();
    assert_eq!(preview["eligible_directories"], 1);
    assert!(model.is_dir());
    fs::create_dir_all(config.data_dir.join("models/qwen3-4b")).unwrap();
    assert!(storage::migrate_storage(&config, true, false, None).is_err());
    assert!(model.join("owner.json").is_file());
}
#[test]
fn idna2003_and_semantic_provider_hashes_match_frozen_identity_rules() {
    let parsed = references::parse_url("https://faß.example/browse/DEMO-1").unwrap();
    assert_eq!(parsed.normalized_url, "https://fass.example/browse/DEMO-1");
    let parsed = references::parse_url("https://例え.テスト/browse/DEMO-1").unwrap();
    assert_eq!(
        parsed.normalized_url,
        "https://xn--r8jz45g.xn--zckzah/browse/DEMO-1"
    );
    let board = references::parse_url(
        "https://jira.example.test/secure/RapidBoard.jspa?rapidView=17&projectKey=PAY",
    )
    .unwrap();
    assert_eq!(
        board.target_key,
        "url:214198462a821b2b3517ebeb9b668e22b14764fa330b05113bb58af2a41efacc"
    );
    assert_eq!(
        references::describe_atlassian_url("https://jira.example.test/browse/%2550AY-1").kind,
        "unsupported"
    );
    assert!(references::parse_url("https://%65xample.test/browse/DEMO-1").is_none());
}
