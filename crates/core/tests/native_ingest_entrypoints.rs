use localbrain_core::backend::{
    contexts, db,
    ingest::{
        self, IngestionObserver, NoObservers, ParsedUrlEvidence, ScanControl, SessionObservation,
    },
    sources::registry,
    Config,
};
use rusqlite::Connection;
use serde_json::{json, Value};
use std::{
    fs,
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
};

struct Fixture {
    _temp: tempfile::TempDir,
    config: Config,
    db: Connection,
    claude: PathBuf,
    codex: PathBuf,
}
impl Fixture {
    fn new() -> Self {
        let temp = tempfile::Builder::new()
            .prefix("lb-native-scan-entrypoints-")
            .tempdir()
            .unwrap();
        let base = fs::canonicalize(temp.path()).unwrap();
        let config = Config::for_data_dir(base.join("data"));
        for path in [
            &config.home_dir,
            &config.claude_root,
            &config.codex_root,
            &config.context_root,
            &config.data_dir,
        ] {
            fs::create_dir_all(path).unwrap();
        }
        fs::write(registry::session_sources_path(&config),registry::session_sources_text(&[
            json!({"source_id":1001,"provider_kind":"claude","display_label":"Synthetic Claude","root":config.claude_root}),
            json!({"source_id":1002,"provider_kind":"codex","display_label":"Synthetic Codex","root":config.codex_root}),
        ]).unwrap()).unwrap();
        db::initialize(&config).unwrap();
        let db = db::connect(&config).unwrap();
        contexts::add_context_root(&db, &config, config.context_root.to_str().unwrap()).unwrap();
        let claude = config.claude_root.join("synthetic.jsonl");
        let codex = config.codex_root.join("synthetic.jsonl");
        Self {
            _temp: temp,
            config,
            db,
            claude,
            codex,
        }
    }
    fn write_claude(&self) {
        fs::write(&self.claude,json!({"type":"user","sessionId":"synthetic-claude-entrypoint","message":{"content":"Synthetic Claude work"}}).to_string()).unwrap();
    }
    fn write_codex(&self) {
        fs::write(&self.codex,[json!({"type":"session_meta","payload":{"id":"synthetic-codex-entrypoint"}}),json!({"type":"event_msg","payload":{"type":"user_message","message":"Synthetic Codex work"}})].iter().map(Value::to_string).collect::<Vec<_>>().join("\n")).unwrap();
    }
    fn codex_snapshot(&self) -> Value {
        json!({"source":db::row(&self.db,"SELECT * FROM sources WHERE id=1002",[]).unwrap(),"files":db::rows(&self.db,"SELECT * FROM source_files WHERE source_id=1002 ORDER BY id",[]).unwrap(),"sessions":db::rows(&self.db,"SELECT * FROM sessions WHERE source_id=1002 ORDER BY id",[]).unwrap()})
    }
}

#[test]
fn selected_provider_returns_legacy_counts_without_touching_other_presence_or_health() {
    let f = Fixture::new();
    f.write_codex();
    let imported =
        ingest::scan_codex_sessions(&f.config, false, &ScanControl::default(), &NoObservers)
            .unwrap();
    assert_eq!(imported, json!({"imported":1,"skipped":0,"failed":0}));
    let before = f.codex_snapshot();
    assert_eq!(before["files"][0]["presence_state"], "PRESENT");
    fs::remove_file(&f.codex).unwrap();
    f.write_claude();
    assert_eq!(
        ingest::scan_claude_sessions(&f.config, false, &ScanControl::default(), &NoObservers)
            .unwrap(),
        json!({"imported":1,"skipped":0,"failed":0})
    );
    assert_eq!(f.codex_snapshot(), before);
    assert_eq!(
        ingest::scan_codex_sessions(&f.config, false, &ScanControl::default(), &NoObservers)
            .unwrap(),
        json!({"imported":0,"skipped":0,"failed":0})
    );
    let after = f.codex_snapshot();
    assert_eq!(after["sessions"], before["sessions"]);
    assert_eq!(after["files"][0]["id"], before["files"][0]["id"]);
    assert_eq!(after["files"][0]["presence_state"], "MISSING");
}

#[test]
fn all_entrypoint_aggregates_both_providers_and_registered_context() {
    let f = Fixture::new();
    f.write_claude();
    f.write_codex();
    fs::write(
        f.config.context_root.join("synthetic.md"),
        "# Synthetic Context\n\nKeep this document.",
    )
    .unwrap();
    let report = ingest::scan_all(&f.config, false, &ScanControl::default(), &NoObservers).unwrap();
    assert_eq!(report["outcome"], "complete");
    assert_eq!(report["summary"]["source_count"], 3);
    assert_eq!(report["summary"]["imported"], 3);
    let providers = report["sources"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v["provider_kind"].as_str().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(providers, vec!["claude", "codex", "context"]);
    let sessions: i64 =
        f.db.query_row("SELECT count(*) FROM sessions", [], |r| r.get(0))
            .unwrap();
    let documents: i64 =
        f.db.query_row("SELECT count(*) FROM context_documents", [], |r| r.get(0))
            .unwrap();
    assert_eq!((sessions, documents), (2, 1));
}

#[test]
fn cancellation_rolls_back_the_active_source_and_keeps_completed_sources() {
    struct CancelOnCodex(Arc<AtomicBool>);
    impl IngestionObserver for CancelOnCodex {
        fn session_indexed(
            &self,
            _: &Connection,
            source: &SessionObservation<'_>,
            _: &[ParsedUrlEvidence],
        ) -> localbrain_core::backend::Result<()> {
            if source.source_id == 1002 {
                self.0.store(true, Ordering::Release);
            }
            Ok(())
        }
    }

    let f = Fixture::new();
    f.write_claude();
    f.write_codex();
    let cancelled = Arc::new(AtomicBool::new(false));
    let observer = CancelOnCodex(cancelled.clone());
    let control = ScanControl {
        cancelled: Some(Arc::new(move || cancelled.load(Ordering::Acquire))),
        progress: None,
    };
    let error = ingest::scan_all(&f.config, false, &control, &observer).unwrap_err();
    assert_eq!(error.code, "interrupted");
    assert_eq!(f.codex_snapshot()["sessions"], json!([]));
    assert_eq!(f.codex_snapshot()["files"], json!([]));
    let prior = db::rows(&f.db, "SELECT id,source_id FROM sessions ORDER BY id", []).unwrap();
    assert_eq!(prior.len(), 1);
    assert_eq!(prior[0]["source_id"], 1001);

    let report = ingest::scan_all(&f.config, false, &ScanControl::default(), &NoObservers).unwrap();
    assert_eq!(report["outcome"], "complete");
    let sessions = db::rows(&f.db, "SELECT id,source_id FROM sessions ORDER BY id", []).unwrap();
    assert_eq!(sessions.len(), 2);
    assert_eq!(sessions[0], prior[0]);
    assert_eq!(sessions[1]["source_id"], 1002);
}
