use localbrain_core::backend::{
    db,
    ingest::{self, IngestionObserver, ParsedSession, ScanControl, SessionObservation},
    sessions::{references, skills},
    BackendError, Config, Result,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{fs, path::PathBuf};
struct Fixture {
    _temp: tempfile::TempDir,
    config: Config,
    db: Connection,
    root: PathBuf,
    source: i64,
}
impl Fixture {
    fn new() -> Self {
        let temp = tempfile::Builder::new()
            .prefix("lb-native-session-")
            .tempdir()
            .unwrap();
        let base = fs::canonicalize(temp.path()).unwrap();
        let config = Config::for_data_dir(base.join("data"));
        fs::create_dir_all(&config.home_dir).unwrap();
        fs::create_dir_all(&config.codex_root).unwrap();
        db::initialize(&config).unwrap();
        let db = db::connect(&config).unwrap();
        db.execute(
            "INSERT INTO sources(provider_kind,name,root_path) VALUES('codex','Synthetic Codex',?)",
            [config.codex_root.to_str().unwrap()],
        )
        .unwrap();
        let source = db.last_insert_rowid();
        let root = config.codex_root.clone();
        Self {
            _temp: temp,
            config,
            db,
            root,
            source,
        }
    }
    fn path(&self, name: &str) -> PathBuf {
        self.root.join(name)
    }
    fn write(&self, name: &str, id: &str, text: &str) {
        let records = [
            json!({"type":"session_meta","timestamp":"2026-11-01T00:00:00Z","payload":{"id":id,"cwd":self.config.home_dir,"git":{"branch":"main"}}}),
            json!({"type":"turn_context","payload":{"turn_id":"turn","model":"gpt-5.4"}}),
            json!({"type":"event_msg","timestamp":"2026-11-01T00:00:01Z","payload":{"type":"user_message","message":text}}),
            json!({"type":"event_msg","timestamp":"2026-11-01T00:00:02Z","payload":{"type":"token_count","info":{"last_token_usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":1,"total_tokens":13}}}}),
        ];
        fs::write(
            self.path(name),
            records
                .iter()
                .map(Value::to_string)
                .collect::<Vec<_>>()
                .join("\n")
                + "\n",
        )
        .unwrap();
    }
    fn scan_with(&self, force: bool, observer: &dyn IngestionObserver) -> Result<(i64, i64, i64)> {
        self.db.execute_batch("BEGIN IMMEDIATE")?;
        let value = ingest::sessions::scan_source(
            &self.db,
            &self.config,
            self.source,
            "codex",
            "Synthetic Codex",
            &self.root,
            force,
            &ScanControl::default(),
            observer,
        );
        match value {
            Ok(v) => {
                self.db.execute_batch("COMMIT")?;
                Ok(v)
            }
            Err(e) => {
                self.db.execute_batch("ROLLBACK")?;
                Err(e)
            }
        }
    }
    fn scan(&self, force: bool) -> (i64, i64, i64) {
        let observer = CoreObserver {
            config: self.config.clone(),
            lookup: references::build_session_reference_lookup(&self.db).unwrap(),
        };
        self.scan_with(force, &observer).unwrap()
    }
    fn one(&self, table: &str) -> Value {
        db::row(
            &self.db,
            &format!("SELECT * FROM {table} ORDER BY rowid LIMIT 1"),
            [],
        )
        .unwrap()
        .unwrap()
    }
}
struct CoreObserver {
    config: Config,
    lookup: references::SessionReferenceLookup,
}
impl IngestionObserver for CoreObserver {
    fn reference_is_current(&self, db: &Connection, id: i64) -> Result<bool> {
        references::session_reference_scan_is_current(db, id)
    }
    fn reconcile_references(
        &self,
        db: &Connection,
        s: &SessionObservation<'_>,
        parsed: &ParsedSession,
    ) -> Result<()> {
        references::reconcile_session_references(
            db,
            &self.config,
            s.session_id,
            s.source_path,
            s.size_bytes,
            s.mtime_ns,
            &parsed.reference_candidates,
            false,
            Some(&self.lookup),
        )?;
        Ok(())
    }
    fn finalize_references(&self, db: &Connection, id: i64) -> Result<()> {
        references::finalize_session_references(db, id, None)?;
        Ok(())
    }
    fn clear_reference_source(&self, db: &Connection, id: i64, path: &str) -> Result<()> {
        references::clear_session_reference_source(db, id, path)
    }
    fn reference_error(&self, db: &Connection, id: i64, error: &str) -> Result<()> {
        references::mark_session_reference_error(db, id, error)
    }
    fn store_skills(
        &self,
        db: &Connection,
        source: i64,
        provider: &str,
        parsed: &ParsedSession,
    ) -> Result<()> {
        skills::store_skill_observations(db, source, provider, parsed)?;
        Ok(())
    }
}
#[test]
fn session_sync_preserves_pk_usage_user_metadata_and_unchanged_second_scan() {
    let f = Fixture::new();
    f.write(
        "one.jsonl",
        "native",
        "A human question https://example.test/guide",
    );
    assert_eq!(f.scan(false), (1, 0, 0));
    let session = f.one("sessions");
    let id = session["id"].as_i64().unwrap();
    let event = f.one("activity_events");
    let usage = f.one("usage_records");
    assert_eq!(usage["input_tokens"], 8);
    assert_eq!(usage["aggregation_scope"], "direct");
    assert_eq!(
        f.db.query_row("SELECT count(*) FROM session_reference_evidence", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        1
    );
    f.db.execute(
        "UPDATE sessions SET display_title='My retained title' WHERE id=?",
        [id],
    )
    .unwrap();
    assert_eq!(f.scan(false), (0, 1, 0));
    assert_eq!(f.one("activity_events"), event);
    assert_eq!(f.one("usage_records"), usage);
    assert_eq!(f.scan(true), (1, 0, 0));
    assert_eq!(f.one("activity_events")["id"], event["id"]);
    assert_eq!(f.one("usage_records")["id"], usage["id"]);
    assert_eq!(f.one("sessions")["display_title"], "My retained title");
}
#[test]
fn missing_native_inputs_retain_history_and_reappearance_uses_same_ids() {
    let f = Fixture::new();
    f.write("one.jsonl", "native", "Retained");
    f.scan(false);
    let before = f.one("sessions");
    let event = f.one("activity_events");
    let usage = f.one("usage_records");
    fs::remove_file(f.path("one.jsonl")).unwrap();
    assert_eq!(f.scan(true), (0, 0, 0));
    assert_eq!(f.one("source_files")["presence_state"], "MISSING");
    assert_eq!(f.one("sessions")["id"], before["id"]);
    assert_eq!(f.one("activity_events"), event);
    assert_eq!(f.one("usage_records"), usage);
    f.write("one.jsonl", "native", "Retained");
    f.scan(false);
    assert_eq!(f.one("source_files")["presence_state"], "PRESENT");
    assert_eq!(f.one("sessions")["id"], before["id"]);
    assert_eq!(f.one("activity_events")["id"], event["id"]);
}
#[test]
fn future_numeric_revision_refuses_before_lifecycle_or_workspace_writes() {
    let f = Fixture::new();
    f.write("one.jsonl", "native", "Future");
    f.scan(false);
    f.db.execute(
        "UPDATE source_files SET session_contract_version=? WHERE source_id=?",
        params![ingest::CODEX_SESSION_REVISION + 1, f.source],
    )
    .unwrap();
    let before = db::rows(&f.db, "SELECT * FROM source_files", []).unwrap();
    let workspaces = db::rows(&f.db, "SELECT * FROM workspaces", []).unwrap();
    fs::remove_file(f.path("one.jsonl")).unwrap();
    let observer = CoreObserver {
        config: f.config.clone(),
        lookup: references::build_session_reference_lookup(&f.db).unwrap(),
    };
    let error = f.scan_with(true, &observer).unwrap_err();
    assert!(error.message.contains("newer Session parser"));
    assert_eq!(
        db::rows(&f.db, "SELECT * FROM source_files", []).unwrap(),
        before
    );
    assert_eq!(
        db::rows(&f.db, "SELECT * FROM workspaces", []).unwrap(),
        workspaces
    );
}
#[test]
fn plain_zstd_precedence_replacement_and_identity_failure_keep_prior_owner() {
    let f = Fixture::new();
    f.write("one.jsonl", "native", "Original");
    let bytes = fs::read(f.path("one.jsonl")).unwrap();
    fs::write(
        f.path("one.jsonl.zst"),
        zstd::stream::encode_all(bytes.as_slice(), 3).unwrap(),
    )
    .unwrap();
    assert_eq!(
        ingest::sessions::session_paths(&f.root, "codex", &ScanControl::default()).unwrap(),
        vec![f.path("one.jsonl")]
    );
    f.scan(false);
    let id = f.one("sessions")["id"].clone();
    fs::remove_file(f.path("one.jsonl")).unwrap();
    assert_eq!(f.scan(false), (1, 0, 0));
    assert_eq!(f.one("sessions")["id"], id);
    assert_eq!(
        f.one("source_files")["path"],
        json!(f.path("one.jsonl.zst"))
    );
    assert_eq!(
        f.db.query_row("SELECT count(*) FROM source_files", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        1
    );
    f.write("one.jsonl", "different-native", "Wrong replacement");
    assert_eq!(f.scan(false), (0, 0, 1));
    assert_eq!(f.one("sessions")["external_id"], "native");
    assert_eq!(f.one("sessions")["id"], id);
}
struct BrokenReference;
impl IngestionObserver for BrokenReference {
    fn reconcile_references(
        &self,
        _: &Connection,
        _: &SessionObservation<'_>,
        _: &ParsedSession,
    ) -> Result<()> {
        Err(BackendError::invalid(
            "synthetic_reference",
            "Synthetic reference failure",
        ))
    }
}
#[test]
fn failed_contract_repair_rolls_back_projection_and_keeps_prior_versions() {
    let f = Fixture::new();
    f.write("one.jsonl", "native", "Prior content");
    f.scan(false);
    f.db.execute("UPDATE source_files SET session_contract_version=1,usage_contract_version='old' WHERE source_id=?",[f.source]).unwrap();
    let prior = f.one("sessions");
    let usage = f.one("usage_records");
    f.write("one.jsonl", "native", "Changed content");
    assert_eq!(f.scan_with(false, &BrokenReference).unwrap(), (0, 0, 1));
    assert_eq!(f.one("sessions"), prior);
    assert_eq!(f.one("usage_records"), usage);
    let tracked = f.one("source_files");
    assert_eq!(tracked["session_contract_version"], 1);
    assert_eq!(tracked["usage_contract_version"], "old");
    assert_eq!(tracked["status"], "error");
}
#[test]
fn metadata_stub_has_no_freshness_row_and_later_meaningful_file_is_imported() {
    let f = Fixture::new();
    fs::write(
        f.path("stub.jsonl"),
        "{\"type\":\"session_meta\",\"payload\":{\"id\":\"stub\"}}\n",
    )
    .unwrap();
    assert_eq!(f.scan(false), (0, 0, 0));
    assert_eq!(
        f.db.query_row("SELECT count(*) FROM sessions", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        0
    );
    assert_eq!(
        f.db.query_row("SELECT count(*) FROM source_files", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
    f.write("stub.jsonl", "stub", "Now meaningful");
    assert_eq!(f.scan(false), (1, 0, 0));
}
