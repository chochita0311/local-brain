use localbrain_core::backend::{
    db,
    search::{
        self, index,
        model::Encoder,
        molecules::{self, Profile, SearchTokenizer},
        retrieval::Retriever,
        source::Source,
        SearchService,
    },
    sources::registry,
    Config, Result,
};
use localbrain_models::Cancellation;
use serde_json::{json, Value};
use std::{
    fs,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};
struct CharacterTokenizer;
impl SearchTokenizer for CharacterTokenizer {
    fn count(&self, text: &str, special: bool) -> Result<usize> {
        Ok(text.chars().count() + usize::from(special))
    }
    fn spans(&self, text: &str) -> Result<Vec<(usize, usize)>> {
        Ok(text
            .chars()
            .enumerate()
            .map(|(index, _)| (index, index + 1))
            .collect())
    }
}
struct SyntheticEncoder {
    calls: AtomicUsize,
    interrupt_query: Option<Cancellation>,
}
impl SyntheticEncoder {
    fn new() -> Self {
        Self {
            calls: AtomicUsize::new(0),
            interrupt_query: None,
        }
    }
}
impl Encoder for SyntheticEncoder {
    fn contract(&self) -> Value {
        json!({"synthetic":"one-molecule-one-vector"})
    }
    fn batch_size(&self) -> usize {
        2
    }
    fn tokenizer(&self, _: &Cancellation) -> Result<Arc<dyn SearchTokenizer>> {
        Ok(Arc::new(CharacterTokenizer))
    }
    fn encode(
        &self,
        texts: &[String],
        query: bool,
        cancel: &Cancellation,
    ) -> Result<Vec<Vec<f32>>> {
        if let Some(interrupt) = self.interrupt_query.as_ref().filter(|_| query) {
            interrupt.store(true, Ordering::Release);
        }
        if cancel.load(Ordering::Acquire) {
            return Err(search::failure("SEARCH_INTERRUPTED"));
        }
        self.calls.fetch_add(texts.len(), Ordering::AcqRel);
        Ok(texts
            .iter()
            .map(|text| {
                let mut vector = vec![0.0; 512];
                let index = if text.contains("Rust") || text.contains("앱") || text.contains("app")
                {
                    0
                } else {
                    1
                };
                vector[index] = 1.0;
                vector
            })
            .collect())
    }
}
fn fixture() -> (tempfile::TempDir, Config) {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    db::initialize(&config).unwrap();
    let sessions = root.path().join("sessions");
    let context = root.path().join("context");
    fs::create_dir(&sessions).unwrap();
    fs::create_dir(&context).unwrap();
    let entries = vec![
        json!({"source_id":1,"provider_kind":"codex","display_label":"Synthetic","root":sessions,"color":"green"}),
    ];
    localbrain_core::backend::storage::files::atomic_write(
        &registry::session_sources_path(&config),
        registry::session_sources_text(&entries).unwrap().as_bytes(),
    )
    .unwrap();
    let connection = db::connect(&config).unwrap();
    registry::load_and_reconcile_session_sources(&connection, &config).unwrap();
    connection
        .execute(
            "INSERT INTO sources(id,provider_kind,name,root_path) VALUES (2,'context','Context',?)",
            [context.to_string_lossy().as_ref()],
        )
        .unwrap();
    connection
        .execute(
            "INSERT INTO context_roots(id,path,label) VALUES (1,?,'Context')",
            [context.to_string_lossy().as_ref()],
        )
        .unwrap();
    connection.execute("INSERT INTO context_documents(id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash) VALUES (1,2,1,?,'guide.md','Migration guide','Database migration guide',24,1700000000000000000,'old')",[context.join("guide.md").to_string_lossy().as_ref()]).unwrap();
    connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title,last_event_at) VALUES (1,1,'one',?,'Build app','2026-11-18T10:00:00+00:00')",[sessions.join("one.jsonl").to_string_lossy().as_ref()]).unwrap();
    connection.execute_batch("INSERT INTO sessions(id,source_id,external_id,source_path,title,session_class) VALUES (2,1,'maintenance','/synthetic/maintenance','Excluded','maintenance');INSERT INTO sessions(id,source_id,external_id,source_path,title,session_role) VALUES (3,1,'child','/synthetic/child','Excluded','subsession'); INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,source_line) VALUES ('event-one',1,0,'message','user','Rust 앱을 만든다. exact/path',1)").unwrap();
    drop(connection);
    (root, config)
}
fn prepare(config: &Config, encoder: &dyn Encoder) -> Value {
    index::prepare(
        config,
        encoder,
        Profile::default(),
        &localbrain_models::cancellation(),
        false,
        &mut |_| {},
    )
    .unwrap()
}
#[test]
fn source_policy_snapshot_and_private_cache_exclusions_are_preserved() {
    let (_root, config) = fixture();
    let (values, coverage) = search::source::read_sources(&config, None).unwrap();
    assert_eq!(
        values
            .iter()
            .map(|value| value.key.as_str())
            .collect::<Vec<_>>(),
        ["session:1", "document:1"]
    );
    assert_eq!(coverage["excluded_sessions"], 2);
    let connection = db::connect(&config).unwrap();
    connection
        .execute(
            "UPDATE context_documents SET mtime_ns=1700000000000001408",
            [],
        )
        .unwrap();
    let timestamp = search::source::read_sources(&config, None)
        .unwrap()
        .0
        .into_iter()
        .find(|source| source.kind == "document")
        .unwrap()
        .timestamp;
    assert_eq!(timestamp, "2023-11-14T22:13:20.000001+00:00");
    connection
        .execute(
            "UPDATE context_documents SET path=?",
            [config
                .cache_dir
                .join("derived.md")
                .to_string_lossy()
                .as_ref()],
        )
        .unwrap();
    let (_, coverage) = search::source::read_sources(&config, None).unwrap();
    assert_eq!(coverage["excluded_runtime_documents"], 1);
    connection
        .execute("UPDATE context_roots SET readable=0", [])
        .unwrap();
    assert_eq!(
        search::source::read_sources(&config, None).unwrap().1["unreadable_context_roots"],
        1
    );
}
#[test]
fn exhaustive_unicode_spans_and_bounded_context_keep_every_body_character() {
    let text = format!(
        "{}끝의 고유 근거",
        "첫 요청.\n\n조건 유지와 👨‍💻 취소하지 않는다.\n".repeat(120)
    );
    let spans = molecules::split_spans(&text, &CharacterTokenizer, Profile::default()).unwrap();
    let body = spans
        .iter()
        .map(|(start, end)| molecules::slice(&text, *start, *end))
        .collect::<String>();
    assert_eq!(body, text);
    assert!(spans.iter().all(|(start, end)| end - start <= 768));
    let mut source = Source {
        key: "session:1".into(),
        kind: "session".into(),
        entity_id: 1,
        title: "제목".repeat(200),
        path: "/synthetic".into(),
        source_kind: "codex".into(),
        timestamp: "fixed".into(),
        blocks: vec![
            json!({"id":"request","role":"user","text":"요청".repeat(2000),"sequence":0,"source_line":1}),
            json!({"id":"answer","role":"assistant","text":text,"sequence":1,"source_line":2}),
        ],
        source_id: Some(1),
    };
    let values = molecules::molecularize(&source, &CharacterTokenizer, Profile::default()).unwrap();
    assert!(values
        .iter()
        .all(|value| value["input"].as_str().unwrap().chars().count() < 1024));
    let answer = values
        .iter()
        .filter(|value| value["locator"]["block_id"] == "answer")
        .collect::<Vec<_>>();
    assert!(answer
        .iter()
        .all(|value| value["locator"]["context_event"] == "request"
            && value["locator"]["context_limited"] == true));
    let reconstructed = answer
        .iter()
        .map(|value| value["text"].as_str().unwrap())
        .collect::<String>();
    assert_eq!(reconstructed, source.blocks[1]["text"].as_str().unwrap());
    source.blocks.clear();
    assert!(
        molecules::molecularize(&source, &CharacterTokenizer, Profile::default())
            .unwrap()
            .is_empty()
    );
}
#[test]
fn foreground_query_cancellation_reaches_the_encoder_and_preserves_the_index() {
    let (_root, config) = fixture();
    let cancel = localbrain_models::cancellation();
    let encoder = Arc::new(SyntheticEncoder {
        interrupt_query: Some(cancel.clone()),
        ..SyntheticEncoder::new()
    });
    prepare(&config, encoder.as_ref());
    let path = index::folder(&config).join("index.sqlite3");
    let before = fs::read(&path).unwrap();
    let calls = encoder.calls.load(Ordering::Acquire);
    let reader = Retriever::new(config, Profile::default(), encoder.clone());
    assert_eq!(
        reader
            .search_with_cancellation("Rust", "dense", Some(0.0), 1, 20, &cancel)
            .unwrap_err()
            .code,
        "SEARCH_INTERRUPTED"
    );
    assert_eq!(encoder.calls.load(Ordering::Acquire), calls);
    assert_eq!(fs::read(&path).unwrap(), before);
    assert!(reader.search("Rust", "dense", Some(0.0), 1, 20).is_ok());
}
#[test]
fn binary_index_reuses_unchanged_generation_and_filters_stale_evidence() {
    let (_root, config) = fixture();
    let encoder = Arc::new(SyntheticEncoder::new());
    let first = prepare(&config, encoder.as_ref());
    assert_eq!(first["parents"], 2);
    assert_eq!(first["encoded"], 2);
    let reader = Retriever::new(config.clone(), Profile::default(), encoder.clone());
    let result = reader
        .search("앱 관련 세션 보여줘", "hybrid", None, 1, 20)
        .unwrap();
    assert_eq!(result["total"], 1);
    assert_eq!(result["results"][0]["key"], "session:1");
    assert!(result["results"][0]["href"]
        .as_str()
        .unwrap()
        .contains("#event-event-one"));
    assert_eq!(result["partial"], false);
    let generation = result["results"][0]["evidence"][0]["generation"]
        .as_str()
        .unwrap()
        .to_string();
    let second = prepare(&config, encoder.as_ref());
    assert_eq!(second["encoded"], 0);
    assert_eq!(second["unchanged"], true);
    let index = index::open_index(&index::folder(&config).join("index.sqlite3")).unwrap();
    assert_eq!(
        index
            .query_row("SELECT length(value) FROM vectors LIMIT 1", [], |row| row
                .get::<_, i64>(
                0
            ))
            .unwrap(),
        2048
    );
    drop(index);
    let connection = db::connect(&config).unwrap();
    connection
        .execute(
            "UPDATE activity_events SET text='Changed source' WHERE id='event-one'",
            [],
        )
        .unwrap();
    drop(connection);
    assert!(reader.evidence(1, &generation).is_err());
    let current = reader.search("Rust", "dense", Some(0.0), 1, 20).unwrap();
    assert_eq!(current["partial"], true);
    assert!(current["results"]
        .as_array()
        .unwrap()
        .iter()
        .all(|item| item["key"] != "session:1"));
    let third = prepare(&config, encoder.as_ref());
    assert_eq!(third["encoded"], 1);
    assert!(third["reused"].as_u64().unwrap() >= 1);
}
#[test]
fn interrupted_build_keeps_committed_vectors_and_resumes_without_truncation() {
    let (_root, config) = fixture();
    let encoder = SyntheticEncoder::new();
    let cancel = localbrain_models::cancellation();
    let signal = cancel.clone();
    let failure = index::prepare(
        &config,
        &encoder,
        Profile::default(),
        &cancel,
        false,
        &mut |stats| {
            if stats["encoded"].as_u64().unwrap_or(0) > 0 {
                signal.store(true, Ordering::Release);
            }
        },
    )
    .unwrap_err();
    assert_eq!(failure.code, "SEARCH_INTERRUPTED");
    assert!(!index::folder(&config).join("index.sqlite3").exists());
    assert!(index::folder(&config).join("building.sqlite3").exists());
    cancel.store(false, Ordering::Release);
    let result = index::prepare(
        &config,
        &encoder,
        Profile::default(),
        &cancel,
        false,
        &mut |_| {},
    )
    .unwrap();
    assert_eq!(result["parents"], 2);
    assert!(result["reused"].as_u64().unwrap() > 0);
    assert_eq!(result["encoded"], 1);
}

#[test]
fn cancellation_after_final_flush_preserves_the_published_generation() {
    let (_root, config) = fixture();
    let encoder = SyntheticEncoder::new();
    let first = prepare(&config, &encoder);
    let published = index::folder(&config).join("index.sqlite3");
    let before = fs::read(&published).unwrap();
    let cancel = localbrain_models::cancellation();
    let mut all_parents_reported = false;
    let error = index::prepare(
        &config,
        &encoder,
        Profile::default(),
        &cancel,
        true,
        &mut |state| {
            if state["state"] == "preparing" && state["parents"] == first["parents"] {
                if all_parents_reported {
                    cancel.store(true, Ordering::Release);
                }
                all_parents_reported = true;
            }
        },
    )
    .unwrap_err();
    assert_eq!(error.code, "SEARCH_INTERRUPTED");
    assert_eq!(fs::read(&published).unwrap(), before);
    assert_eq!(prepare(&config, &encoder)["unchanged"], true);
}
#[test]
fn writer_lock_and_unknown_owner_preserve_active_cache() {
    let (_root, config) = fixture();
    let writer = index::writer(&config).unwrap();
    assert!(index::writer_active(&config).unwrap());
    assert!(index::writer(&config).is_err());
    drop(writer);
    assert!(!index::writer_active(&config).unwrap());
    let encoder = SyntheticEncoder::new();
    prepare(&config, &encoder);
    let path = index::folder(&config).join("index.sqlite3");
    let connection = rusqlite::Connection::open(&path).unwrap();
    connection
        .execute(
            "UPDATE meta SET value='\"unknown-owner\"' WHERE key='owner'",
            [],
        )
        .unwrap();
    drop(connection);
    let before = fs::read(&path).unwrap();
    assert!(index::prepare(
        &config,
        &encoder,
        Profile::default(),
        &localbrain_models::cancellation(),
        true,
        &mut |_| {}
    )
    .is_err());
    assert_eq!(fs::read(path).unwrap(), before);
}
#[test]
fn exact_identifier_bridge_does_not_inflate_semantic_ranking() {
    let (_root, config) = fixture();
    let encoder = Arc::new(SyntheticEncoder::new());
    prepare(&config, encoder.as_ref());
    let reader = Retriever::new(config, Profile::default(), encoder);
    let response = reader.search("exact/path", "hybrid", None, 1, 20).unwrap();
    let items = response["results"].as_array().unwrap();
    let exact = items
        .iter()
        .find(|value| value["key"] == "session:1")
        .unwrap();
    assert_eq!(exact["match_reason"], "exact");
    assert_eq!(exact["score"], 0.0);
    assert_eq!(items[0]["key"], "document:1");
}
#[test]
fn natural_search_settings_revision_and_status_are_read_only_until_explicit_prepare() {
    let root = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(root.path().join("data"));
    let service = SearchService::new(config.clone());
    assert_eq!(service.status().unwrap()["state"], "disabled");
    assert!(!config.data_dir.exists());
    assert!(!config.cache_dir.exists());
    db::initialize(&config).unwrap();
    index::save_settings(&config, Profile::default(), true).unwrap();
    assert_eq!(service.status().unwrap()["state"], "model-missing");
    let state = index::search_settings(&config).unwrap();
    let updated = index::update_cutoff(&config, &json!(0.2), &state["revision"]).unwrap();
    assert_eq!(updated["cutoff"], 0.2);
    assert!(index::update_cutoff(&config, &json!(0.9), &state["revision"]).is_err());
    assert!(index::update_cutoff(&config, &json!(true), &updated["revision"]).is_err());
    assert!(!index::folder(&config).exists());
}
#[test]
fn service_coalesces_refresh_and_cancel_without_weight_loading() {
    let (_root, config) = fixture();
    let encoder = Arc::new(SyntheticEncoder::new());
    let factory_encoder = encoder.clone();
    let service = SearchService::with_encoder_factory(
        config.clone(),
        Arc::new(move |_, _| Ok(factory_encoder.clone())),
    );
    service.request_prepare().unwrap();
    let start = Instant::now();
    while service.status().unwrap()["state"] != "ready" {
        assert!(start.elapsed() < Duration::from_secs(5));
        std::thread::sleep(Duration::from_millis(10));
    }
    assert_eq!(service.search("앱", 1).unwrap()["total"], 1);
    service.request_prepare().unwrap();
    service.cancel();
    service.stop().unwrap();
    assert!(!index::writer_active(&config).unwrap());
}

#[test]
fn empty_corpus_avoids_tokenizer_and_inference() {
    struct Empty;
    impl Encoder for Empty {
        fn contract(&self) -> Value {
            json!({"synthetic":"one-molecule-one-vector"})
        }
        fn batch_size(&self) -> usize {
            panic!("empty corpus must not enter batches")
        }
        fn tokenizer(&self, _: &Cancellation) -> Result<Arc<dyn SearchTokenizer>> {
            panic!("empty corpus must not load tokenizer")
        }
        fn encode(&self, _: &[String], _: bool, _: &Cancellation) -> Result<Vec<Vec<f32>>> {
            panic!("empty corpus must not infer")
        }
    }
    let (_root, config) = fixture();
    let connection = db::connect(&config).unwrap();
    connection
        .execute_batch(
            "UPDATE sessions SET index_policy='metadata_only'; UPDATE context_roots SET enabled=0",
        )
        .unwrap();
    drop(connection);
    let stats = prepare(&config, &Empty);
    assert_eq!(stats["state"], "no-data");
    assert_eq!(stats["parents"], 0);
    let reader = Retriever::new(config, Profile::default(), Arc::new(Empty));
    assert_eq!(
        reader.search("앱", "hybrid", None, 1, 20).unwrap()["total"],
        0
    );
}
#[test]
fn malformed_vector_storage_is_refused_and_forced_rebuild_repairs_owned_cache() {
    let (_root, config) = fixture();
    let encoder = Arc::new(SyntheticEncoder::new());
    prepare(&config, encoder.as_ref());
    let path = index::folder(&config).join("index.sqlite3");
    for bytes in [
        vec![0; 3],
        vec![0; 512 * 4],
        std::iter::repeat_n(f32::NAN.to_le_bytes(), 512)
            .flatten()
            .collect(),
    ] {
        let connection = rusqlite::Connection::open(&path).unwrap();
        connection
            .execute("UPDATE vectors SET value=?", [bytes])
            .unwrap();
        drop(connection);
        let reader = Retriever::new(config.clone(), Profile::default(), encoder.clone());
        assert_eq!(
            reader.search("앱", "dense", None, 1, 20).unwrap_err().code,
            "INVALID_SEARCH_VECTORS"
        );
    }
    let stats = index::prepare(
        &config,
        encoder.as_ref(),
        Profile::default(),
        &localbrain_models::cancellation(),
        true,
        &mut |_| {},
    )
    .unwrap();
    assert!(stats["encoded"].as_u64().unwrap() > 0);
    assert_eq!(
        Retriever::new(config, Profile::default(), encoder)
            .search("앱", "dense", None, 1, 20)
            .unwrap()["total"],
        1
    );
}
#[test]
fn lexical_scope_precedes_candidate_cap_and_evidence_deduplicates_repeated_bodies() {
    let (_root, config) = fixture();
    let connection = db::connect(&config).unwrap();
    connection
        .execute(
            "UPDATE activity_events SET text=? WHERE session_id=1",
            ["needle  ".repeat(64 * 501)],
        )
        .unwrap();
    connection
        .execute(
            "UPDATE context_documents SET body='needle matching document'",
            [],
        )
        .unwrap();
    drop(connection);
    let encoder = Arc::new(SyntheticEncoder::new());
    let stats = prepare(&config, encoder.as_ref());
    assert!(stats["fragments"].as_u64().unwrap() > 500);
    let reader = Retriever::new(config, Profile::default(), encoder);
    let scoped = reader
        .search("needle 문서만", "lexical", None, 1, 20)
        .unwrap();
    assert_eq!(scoped["total"], 1);
    assert_eq!(scoped["results"][0]["key"], "document:1");
    let all = reader.search("needle", "lexical", None, 1, 20).unwrap();
    let session = all["results"]
        .as_array()
        .unwrap()
        .iter()
        .find(|item| item["key"] == "session:1")
        .unwrap();
    assert_eq!(session["evidence"].as_array().unwrap().len(), 1);
}
#[test]
fn keyword_search_uses_same_current_source_admission_and_preserves_unknown_model_status() {
    let (_root, config) = fixture();
    let connection = db::connect(&config).unwrap();
    connection.execute("INSERT INTO search_index VALUES ('session','1','codex','Build app','Rust exact/path','/synthetic')",[]).unwrap();
    connection.execute("INSERT INTO search_index VALUES ('session','2','codex','Excluded','Rust','/synthetic')",[]).unwrap();
    connection
        .execute(
            "INSERT INTO search_index VALUES ('document','1','context','Guide','Rust document',?)",
            [config
                .context_root
                .join("guide.md")
                .to_string_lossy()
                .as_ref()],
        )
        .unwrap();
    let model = localbrain_core::backend::models::model_root(
        &config,
        localbrain_models::catalog::ModelKey::Embedding,
    )
    .unwrap();
    fs::create_dir_all(&model).unwrap();
    fs::write(model.join("model.json"), b"not-json").unwrap();
    let hits = search::keyword::keyword_search(&connection, "Rust", "all", 80, &config).unwrap();
    assert_eq!(hits.len(), 2);
    assert!(hits.iter().all(|hit| hit["entity_id"] != "2"));
    connection
        .execute(
            "UPDATE sources SET root_path='/changed-root' WHERE id=1",
            [],
        )
        .unwrap();
    let hits =
        search::keyword::keyword_search(&connection, "Rust", "sessions", 80, &config).unwrap();
    assert!(hits.is_empty());
}
