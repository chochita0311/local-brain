use localbrain_core::backend::{
    self,
    context_search::{
        engine::{self, ContextGenerator},
        tools::{self, FileTools},
        ContextSearchService,
    },
    Config, Result,
};
use serde_json::{json, Value};
use std::{fs, path::Path, time::Duration};
struct Generator {
    outputs: std::collections::VecDeque<String>,
    seen: Vec<Vec<Value>>,
    cleared: bool,
}
impl ContextGenerator for Generator {
    fn generate(
        &mut self,
        messages: &[Value],
        _: &[Value],
        _: &localbrain_models::Cancellation,
    ) -> Result<String> {
        self.seen.push(messages.to_vec());
        Ok(self.outputs.pop_front().unwrap())
    }
    fn clear_turn(&mut self) {
        self.cleared = true
    }
}
fn generator(outputs: Vec<String>) -> Generator {
    Generator {
        outputs: outputs.into(),
        seen: vec![],
        cleared: false,
    }
}
fn call(name: &str, args: Value) -> String {
    format!(
        "<tool_call>{}</tool_call>",
        json!({"name":name,"arguments":args})
    )
}
fn source(root: &Path) -> Value {
    json!({"id":"own","name":"Demo vault","kind":"local","mode":"files","root":root})
}
#[test]
fn actual_read_only_tools_evidence_bounds_and_source_changes() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().canonicalize().unwrap();
    fs::write(
        root.join("guide.md"),
        "Airflow controls jobs.\nOwner: Demo operator.\n",
    )
    .unwrap();
    fs::write(root.join("hidden.txt"), "Other").unwrap();
    let mut tool = FileTools::new(&[source(&root)]).unwrap();
    let result = tool
        .call("search_text", &json!({"query":"AIRFLOW"}))
        .unwrap();
    assert_eq!(result["scanned"], 2);
    assert_eq!(result["matches"][0]["path"], "guide.md");
    let read = tool
        .call(
            "read_file",
            &json!({"source":"own","path":"guide.md","start_line":2,"end_line":2}),
        )
        .unwrap();
    assert_eq!(read["ref"], "S2");
    assert!(read["text"].as_str().unwrap().contains("operator"));
    assert_eq!(tool.evidence.len(), 2);
    for (name, args) in [
        ("delete_file", json!({})),
        ("list_files", json!({"source":[]})),
        ("read_file", json!({"source":"own","path":"../outside"})),
        (
            "read_file",
            json!({"source":"own","path":"guide.md","start_line":true}),
        ),
    ] {
        assert!(tool.call(name, &args).is_err())
    }
    fs::write(root.join(".localbrain-drive-part"), "incomplete").unwrap();
    fs::write(root.join("binary"), b"\0bad").unwrap();
    std::os::unix::fs::symlink(root.join("guide.md"), root.join("link")).unwrap();
    assert!(tool
        .call("read_file", &json!({"source":"own","path":"link"}))
        .is_err());
    assert!(tool
        .call(
            "read_file",
            &json!({"source":"own","path":".localbrain-drive-part"})
        )
        .is_err());
    let result = tool
        .call("search_text", &json!({"query":"incomplete"}))
        .unwrap();
    assert_eq!(result["matches"], json!([]));
    assert_eq!(result["unreadable"], 1);
    fs::write(root.join("long"), "x".repeat(2_100_000)).unwrap();
    let read = tool
        .call("read_file", &json!({"source":"own","path":"long"}))
        .unwrap();
    assert_eq!(read["limited"], true);
    assert_eq!(read["text"].as_str().unwrap().len(), 10000);
    assert!(
        !serde_json::to_string(&tools::public_sources(&[source(&root)]))
            .unwrap()
            .contains(root.to_str().unwrap())
    );
    let selected = root.join("selected");
    fs::write(&selected, "one").unwrap();
    let mut tool =
        FileTools::new(&[json!({"id":"file","mode":"files","root":selected,"single_file":true})])
            .unwrap();
    fs::remove_file(&selected).unwrap();
    fs::create_dir(&selected).unwrap();
    assert!(tool.call("list_files", &json!({"source":"file"})).is_err());
}
#[test]
fn tool_loop_reads_before_answer_validates_current_citations_and_clears_turn() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().canonicalize().unwrap();
    fs::write(
        root.join("guide.md"),
        "Airflow owner is Demo operator.\nSchedule daily06.\n",
    )
    .unwrap();
    let sources = [source(&root)];
    let history = [json!({"role":"user","content":"Who runs Airflow?"})];
    let mut gen = generator(vec![
        call("search_text", json!({"query":"Airflow"})),
        "Claim [S99]".into(),
        "Demo operator [S1]".into(),
    ]);
    let mut events = vec![];
    let result = engine::answer(
        &mut gen,
        &sources,
        &history,
        |v| {
            events.push(v);
            Ok(())
        },
        &localbrain_models::cancellation(),
    )
    .unwrap();
    assert_eq!(result["text"], "Demo operator [S1]");
    assert!(result["evidence"][0]["text"]
        .as_str()
        .unwrap()
        .contains("daily06"));
    assert_eq!(gen.seen.len(), 3);
    assert!(gen.cleared);
    assert!(!gen.seen[0][0]["content"]
        .as_str()
        .unwrap()
        .contains(root.to_str().unwrap()));
    let mut gen = generator(vec!["Invented [S1]".into(); 2]);
    let answer = engine::answer(
        &mut gen,
        &sources,
        &history,
        |_| Ok(()),
        &localbrain_models::cancellation(),
    )
    .unwrap();
    assert_eq!(answer["evidence"], json!([]));
    assert_eq!(answer["limited"], true);
    let mut gen = generator(vec![call("list_sources", json!({})); 8]);
    assert_eq!(
        engine::answer(
            &mut gen,
            &sources,
            &history,
            |_| Ok(()),
            &localbrain_models::cancellation()
        )
        .unwrap_err()
        .code,
        "BUDGET"
    );
    assert!(gen.cleared);
}
#[test]
fn protocol_validation_keeps_unicode_and_default_json_semantics() {
    for output in [
        "<tool_call>{bad}</tool_call>",
        "<tool_call>{",
        "<tool_call>[]</tool_call>",
        "<tool_call>{}</tool_call></tool_call>",
    ] {
        assert_eq!(engine::parse_calls(output).unwrap_err().code, "PROTOCOL")
    }
    let calls = engine::parse_calls(
        r#"<tool_call>{"name":"a","name":"list_sources","arguments":{}}</tool_call>"#,
    )
    .unwrap();
    assert_eq!(calls[0]["name"], "list_sources");
    let value = json!({"model":"4b","messages":[{"role":"user","content":"🦀".repeat(4000)}]});
    assert!(engine::validate_request(&value).is_ok());
    for bad in [
        json!({"model":"remote","messages":[]}),
        json!({"model":"4b","messages":[{"role":"system","content":"x"}]}),
        json!({"model":"4b","messages":[{"role":"user","content":"\u{1c}"}]}),
        json!({"model":"4b","messages":[{"role":"user","content":"x"}],"root":"/outside"}),
    ] {
        assert!(engine::validate_request(&bad).is_err())
    }
    let result =
        engine::compact_result(json!({"matches":vec![json!({"text":"x".repeat(1600)});40]}))
            .unwrap();
    assert_eq!(result["limited"], true);
    assert!(result["matches"].as_array().unwrap().len() < 4);
}
#[test]
fn catalog_does_not_bootstrap_or_expand_runtime_and_notes_revocation_is_checked() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().canonicalize().unwrap();
    let config = Config::for_data_dir(root.join("data"));
    assert!(tools::source_catalog(&config, None).is_err());
    assert!(!config.data_dir.exists());
    fs::create_dir_all(&config.data_dir).unwrap();
    let db = rusqlite::Connection::open(&config.database_path).unwrap();
    db.execute_batch("CREATE TABLE context_roots(id INTEGER,path TEXT,label TEXT,source_type TEXT,enabled INTEGER,readable INTEGER);CREATE TABLE context_documents(id INTEGER,context_root_id INTEGER,title TEXT,body TEXT,mtime_ns INTEGER);").unwrap();
    let vault = root.join("vault");
    fs::create_dir(&vault).unwrap();
    db.execute(
        "INSERT INTO context_roots VALUES(1,?,'Vault','folder',1,1)",
        [vault.to_str()],
    )
    .unwrap();
    db.execute(
        "INSERT INTO context_roots VALUES(2,?,'App','folder',1,1)",
        [config.data_dir.to_str()],
    )
    .unwrap();
    db.execute_batch("INSERT INTO context_roots VALUES(3,'notes','Notes','apple_notes',1,1);INSERT INTO context_documents VALUES(1,3,'Demo','Airflow note',1);").unwrap();
    let sources = tools::source_catalog(&config, None).unwrap();
    assert_eq!(sources.len(), 2);
    let mut tools = FileTools::new(&sources).unwrap();
    assert_eq!(
        tools
            .call(
                "read_file",
                &json!({"source":"context-3","path":"document-1"})
            )
            .unwrap()["text"],
        "Airflow note"
    );
    db.execute("UPDATE context_roots SET enabled=0 WHERE id=3", [])
        .unwrap();
    assert!(tools
        .call(
            "read_file",
            &json!({"source":"context-3","path":"document-1"})
        )
        .is_err());
    let service = ContextSearchService::new(config, None).unwrap();
    assert_eq!(service.status().unwrap()["busy"], false);
    assert_eq!(
        service
            .begin(&json!({"model":"4b","messages":[{"role":"user","content":"x"}]}))
            .err()
            .unwrap()
            .code,
        "MODEL_MISSING"
    );
    service.unload_idle();
    service.stop();
    let _ = Duration::from_millis(1);
    let _ = backend::unicode::casefold("A");
}
#[test]
fn native_service_reuses_workers_switches_model_and_cancels_disconnected_job() {
    use std::{os::unix::fs::PermissionsExt, sync::Arc, time::Instant};
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().canonicalize().unwrap();
    let config = Config::for_data_dir(root.join("data"));
    fs::create_dir_all(&config.data_dir).unwrap();
    let vault = root.join("vault");
    fs::create_dir(&vault).unwrap();
    let db = rusqlite::Connection::open(&config.database_path).unwrap();
    db.execute_batch("CREATE TABLE context_roots(id INTEGER,path TEXT,label TEXT,source_type TEXT,enabled INTEGER,readable INTEGER);").unwrap();
    db.execute(
        "INSERT INTO context_roots VALUES(1,?,'Demo','folder',1,1)",
        [vault.to_str()],
    )
    .unwrap();
    for key in [
        localbrain_models::catalog::ModelKey::Generation4b,
        localbrain_models::catalog::ModelKey::Generation8b,
    ] {
        let path = backend::models::model_root(&config, key).unwrap();
        fs::create_dir_all(&path).unwrap();
        fs::write(path.join("model.json"), "{}").unwrap();
    }
    let starts = root.join("starts");
    let fixture = root.join("fixture");
    fs::write(&fixture,format!("#!/bin/sh\nprintf x >> '{}'\nwhile IFS= read -r line; do case \"$line\" in *'\"type\":\"configure\"'*) continue;; esac; printf '%s\\n' '{{\"type\":\"answer\",\"text\":\"Synthetic\",\"evidence\":[]}}'; done\n",starts.display())).unwrap();
    fs::set_permissions(&fixture, fs::Permissions::from_mode(0o700)).unwrap();
    let service = ContextSearchService::with_executable(config.clone(), None, fixture).unwrap();
    let begin = |key: &str| {
        service
            .begin(
                &json!({"model":key,"messages":[{"role":"user","content":"Synthetic question"}]}),
            )
            .unwrap()
    };
    for key in ["4b", "4b", "8b"] {
        let job = begin(key);
        assert_eq!(
            job.next_event(Duration::from_secs(3)).unwrap()["type"],
            "answer"
        );
        assert!(job.completed());
        service.release(&job);
    }
    assert_eq!(fs::read_to_string(&starts).unwrap(), "xx");
    service.unload_idle();
    let job = begin("8b");
    assert_eq!(
        job.next_event(Duration::from_secs(3)).unwrap()["type"],
        "answer"
    );
    service.release(&job);
    assert_eq!(fs::read_to_string(&starts).unwrap(), "xxx");
    service.stop();
    let fixture = root.join("hang");
    fs::write(&fixture, "#!/bin/sh\nwhile IFS= read -r line; do :; done\n").unwrap();
    fs::set_permissions(&fixture, fs::Permissions::from_mode(0o700)).unwrap();
    let service = ContextSearchService::with_executable(config, None, fixture).unwrap();
    let job = service
        .begin(&json!({"model":"4b","messages":[{"role":"user","content":"Demo"}]}))
        .unwrap();
    assert_eq!(
        service
            .begin(&json!({"model":"4b","messages":[{"role":"user","content":"Another"}]}))
            .err()
            .unwrap()
            .code,
        "BUSY"
    );
    service.unload_idle();
    let started = Instant::now();
    service.release(&job);
    assert!(started.elapsed() < Duration::from_secs(3));
    assert!(job.canceled.load(std::sync::atomic::Ordering::Acquire));
    assert_eq!(service.status().unwrap()["busy"], false);
    service.stop();
    let _ = Arc::strong_count(&service);
}
