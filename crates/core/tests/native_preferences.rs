//! Native settings checks use the frozen Python settings fixtures and serializer
//! output. Python is an evidence source, never a runtime/test subprocess.
use localbrain_core::{files, preferences, Context};
use serde_json::{json, Value};
use std::fs::{self, File, OpenOptions};
use std::os::fd::{AsFd, AsRawFd};
use std::os::unix::fs::{symlink, OpenOptionsExt, PermissionsExt};

struct Fixture {
    _temporary: tempfile::TempDir,
    context: Context,
}
impl Fixture {
    fn new() -> Self {
        let temporary = tempfile::Builder::new()
            .prefix("lb-native-preferences-")
            .tempdir()
            .unwrap();
        let root = fs::canonicalize(temporary.path()).unwrap();
        Self {
            _temporary: temporary,
            context: Context {
                data_dir: root.join("data"),
                cache_dir: root.join("cache"),
                home_dir: root,
            },
        }
    }
    fn call(&self, operation: &str, arguments: Value) -> preferences::Result<Value> {
        preferences::native_call(operation, &self.context, "UTC", arguments, None)
    }
    fn read(&self) -> Value {
        self.call("common.read", json!({})).unwrap()
    }
    fn write(&self, text: &str) -> Value {
        fs::create_dir_all(&self.context.data_dir).unwrap();
        fs::write(self.context.data_dir.join("settings.toml"), text).unwrap();
        self.read()
    }
    fn lease(&self) -> File {
        fs::create_dir_all(&self.context.data_dir).unwrap();
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .mode(0o600)
            .open(self.context.data_dir.join("operations.lock"))
            .unwrap();
        assert_eq!(
            unsafe { libc::flock(file.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) },
            0
        );
        file
    }
    fn save(&self, changes: Value, revision: Value) -> preferences::Result<Value> {
        let lease = self.lease();
        preferences::native_call(
            "common.save",
            &self.context,
            "UTC",
            json!({"changes":changes,"revision":revision}),
            Some(lease.as_fd()),
        )
    }
    fn bytes(&self) -> Vec<u8> {
        fs::read(self.context.data_dir.join("settings.toml")).unwrap()
    }
    fn no_temporary(&self) {
        assert!(!fs::read_dir(&self.context.data_dir)
            .unwrap()
            .any(|entry| entry
                .unwrap()
                .file_name()
                .to_string_lossy()
                .starts_with(".settings.toml-")));
    }
}

fn raw_child<'a>(raw: &'a Value, table: usize, key: &str) -> &'a Value {
    let entry = raw["nodes"][table]["value"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entry| entry[0] == key)
        .unwrap();
    &raw["nodes"][entry[1].as_u64().unwrap() as usize]
}

#[test]
fn defaults_reads_and_preflight_create_no_storage_or_cache() {
    let f = Fixture::new();
    let first = f.read();
    assert_eq!(first["revision"], files::digest(b""));
    assert_eq!(first["saved"], first["effective"]);
    assert_eq!(first["saved"]["timezone"], "UTC");
    assert_eq!(first["saved"]["session_sync_minutes"], 10);
    assert_eq!(first["saved"]["context_sync_minutes"], 30);
    assert_eq!(first["source"]["timezone"], "default");
    for changes in [Value::Null, json!([]), json!({"projects":{}})] {
        let error = f
            .call("common.preflight", json!({"changes":changes}))
            .unwrap_err();
        assert!(error.message.contains("지원하지 않는 설정"));
    }
    let invalid_zone =
        preferences::native_call("common.defaults", &f.context, "../UTC", json!({}), None).unwrap();
    assert_eq!(invalid_zone["timezone"], "UTC");
    let alias =
        preferences::native_call("common.defaults", &f.context, "US/Eastern", json!({}), None)
            .unwrap();
    assert_eq!(alias["timezone"], "US/Eastern");
    assert!(!f.context.data_dir.exists());
    assert!(!f.context.cache_dir.exists());
}

#[test]
fn ordered_unknown_values_save_to_the_actual_python_serializer_bytes() {
    let f = Fixture::new();
    let original = f.write(concat!(
        "schema_version=1\nfuture=1267650600228229401496703205376\n",
        "overflow=1e999\nnegative=-0.0\ndate=2026-01-02\n",
        "instant=2026-01-02T03:04:05.123456789+09:00\nclock=03:04:05.123456789\n",
        "mixed=[1,\"한글\",true]\n[terminal]\nfuture=\"keep\"\n[[nested.rows]]\nx=17\n"
    ));
    assert_eq!(
        raw_child(&original["raw"], 0, "future")["value"],
        "1267650600228229401496703205376"
    );
    f.save(
        json!({"startup_screen":"context"}),
        original["revision"].clone(),
    )
    .unwrap();
    let expected = concat!(
        "\"schema_version\" = 1\n\"onboarding_completed\" = false\n",
        "\"future\" = 1267650600228229401496703205376\n\"overflow\" = inf\n\"negative\" = -0.0\n",
        "\"date\" = 2026-01-02\n\"instant\" = 2026-01-02T03:04:05.123456+09:00\n",
        "\"clock\" = 03:04:05.123456\n\"mixed\" = [1, \"한글\", true]\n",
        "\"startup_screen\" = \"context\"\n\"timezone\" = \"UTC\"\n",
        "\"session_sync_enabled\" = true\n\"session_sync_minutes\" = 10\n",
        "\"context_sync_enabled\" = true\n\"context_sync_minutes\" = 30\n",
        "\n[\"terminal\"]\n\"future\" = \"keep\"\n\n[\"nested\"]\n\n[[\"nested\".\"rows\"]]\n\"x\" = 17\n"
    );
    assert_eq!(f.bytes(), expected.as_bytes());
    let result = f.read();
    assert_eq!(result["revision"], files::digest(expected.as_bytes()));
    assert_eq!(result["saved"]["startup_screen"], "context");
    assert_eq!(
        raw_child(&result["raw"], 0, "negative")["value"],
        "-0x0.0p+0"
    );
    f.no_temporary();
}

#[test]
fn legacy_float_date_and_string_lexemes_remain_typed_and_exact() {
    let f = Fixture::new();
    let current = f.write(concat!(
        "schema_version=1\n",
        "floats=[-nan,+nan,-inf,+inf,1e999,-1e999,1e-999,-1e-999,1e-5,1e16,1.2345678901234567,5e-324]\n",
        "dates=[2024-02-29,2026-01-02t03:04:05.000000999z,2026-01-02 03:04:05.2-00:00,03:04:05.0000019]\n",
        "text=\"\"\"\nA\\\n   B \\\" \\u000B 한글\"\"\"\n",
        "literal='''\nline one\nline two'''\n"
    ));
    let floats = raw_child(&current["raw"], 0, "floats")["value"]
        .as_array()
        .unwrap();
    let nan = &current["raw"]["nodes"][floats[0].as_u64().unwrap() as usize];
    assert_eq!(nan["value"], "-nan");
    f.save(json!({}), current["revision"].clone()).unwrap();
    let text = String::from_utf8(f.bytes()).unwrap();
    assert!(text.contains("\"floats\" = [nan, nan, -inf, inf, inf, -inf, 0.0, -0.0, 1e-05, 1e+16, 1.2345678901234567, 5e-324]\n"), "{text}");
    assert!(text.contains("\"dates\" = [2024-02-29, 2026-01-02T03:04:05+00:00, 2026-01-02T03:04:05.200000+00:00, 03:04:05.000001]\n"));
    assert!(text.contains("\"text\" = \"AB \\\" \\u000b 한글\"\n"));
    assert!(text.contains("\"literal\" = \"line one\\nline two\"\n"));
}

#[test]
fn readable_mixed_arrays_and_large_hex_integers_refuse_write_before_publication() {
    let f = Fixture::new();
    for text in [
        "schema_version=1\nmixed=[1,{x=2}]\nterminal=\"repair later\"\n".into(),
        "schema_version=1\nmixed=[{x=2},1]\n".into(),
        "schema_version=1\nmixed=[[{x=2}]]\n".into(),
        format!("schema_version=1\nunknown=0x{}\n", "f".repeat(4000)),
    ] {
        let current = f.write(&text);
        let before = f.bytes();
        let error = f.save(json!({}), current["revision"].clone()).unwrap_err();
        if text.contains("0x") {
            assert_eq!(error.kind, "io");
            assert_eq!(error.code, "value");
            assert!(
                raw_child(&current["raw"], 0, "unknown")["value"]
                    .as_str()
                    .unwrap()
                    .len()
                    > 4300
            );
        } else {
            assert!(error.message.contains("기존 설정에 저장할 수 없는 값"));
        }
        assert_eq!(error.commit, "not-published");
        assert_eq!(f.bytes(), before);
        f.no_temporary();
    }
}

#[test]
fn frozen_decimal_limit_applies_at_the_original_read_and_encode_stages() {
    let f = Fixture::new();
    let decimal = "9".repeat(4300);
    let current = f.write(&format!("schema_version=1\nunknown={decimal}\n"));
    f.save(json!({}), current["revision"].clone()).unwrap();
    assert_eq!(raw_child(&f.read()["raw"], 0, "unknown")["value"], decimal);
    let rejected = format!("schema_version=1\nunknown={}\n", "9".repeat(4301));
    fs::write(f.context.data_dir.join("settings.toml"), &rejected).unwrap();
    let error = f.call("common.read", json!({})).unwrap_err();
    assert_eq!(error.kind, "preferences");
    assert!(error.message.contains("로컬 설정을 읽지 못"));
    assert_eq!(f.bytes(), rejected.as_bytes());
    f.no_temporary();
}

#[test]
fn current_file_validation_precedes_revision_and_changed_values() {
    let f = Fixture::new();
    for content in [
        b"bad [".as_slice(),
        b"\xff",
        b"schema_version=true",
        b"schema_version=1\nsession_sync_minutes=false",
    ] {
        fs::create_dir_all(&f.context.data_dir).unwrap();
        fs::write(f.context.data_dir.join("settings.toml"), content).unwrap();
        let error = f
            .save(json!({"timezone":"bad-zone"}), Value::Null)
            .unwrap_err();
        assert_eq!(error.kind, "preferences");
        assert!(!error.message.contains("다른 창"));
        assert_eq!(f.bytes(), content);
    }
    let current = f.write("schema_version=1\n");
    assert!(f
        .save(json!({"timezone":"bad-zone"}), Value::Null)
        .unwrap_err()
        .message
        .contains("다른 창"));
    assert!(f
        .save(json!({"timezone":"bad-zone"}), current["revision"].clone())
        .unwrap_err()
        .message
        .contains("올바른 시간대"));
    assert!(f
        .save(
            json!({"session_sync_minutes":10.0}),
            current["revision"].clone()
        )
        .unwrap_err()
        .message
        .contains("정수로 입력"));
    let lease = f.lease();
    let invalid_surrogate = json!({"root":0,"nodes":[
        {"kind":"table","value":[["changes",1],["revision",3]]},
        {"kind":"table","value":[["timezone",2]]},
        {"kind":"surrogate-string","value":[55296]},
        {"kind":"string","value":current["revision"]}
    ]});
    let error = preferences::native_call_tagged(
        "common.save",
        &f.context,
        "UTC",
        invalid_surrogate,
        Some(lease.as_fd()),
        &preferences::NativeOptions::default(),
    )
    .unwrap_err();
    assert!(error.message.contains("올바른 시간대"));
    f.no_temporary();
}

#[test]
fn toml_10_grammar_duplicate_namespaces_and_inline_immutability_are_preserved() {
    for text in [
        "x={a=1,}",
        "x={\na=1}",
        "x={a=1 #comment\n}",
        "x=\"\\e\"",
        "x=\"\\x41\"",
        "x=03:04",
        "x=2026-01-02T03:04Z",
        "x=2023-02-29",
        "x=0001-01-01T24:00:00",
        "x=0x_1",
        "x=+0xff",
        "x=1__2",
        "x=01",
        "x=1.",
        "x=TRUE",
        "x=1\r",
        "x=\"\\uD800\"",
        "x=1 #\u{7f}",
        "x=1\nx=2",
        "[a]\n[a]",
        "a.b=1\n[a]",
        "a={x=1}\na.y=2",
        "a=[]\n[[a]]",
        "a={b={x=1},b.y=2}",
        "[a.b]\n[a]\nb.x=2",
        "[[a]]\n[a]",
        "a=1\n[a.b]",
    ] {
        assert!(
            preferences::decode_toml_document(text).is_err(),
            "unexpectedly read {text:?}"
        );
    }
    let text = "[a.b]\nx=1\n[a]\ny=2\n[[rows]]\nx=1\n[rows.detail]\na=3\n[[rows]]\nx=2\n[rows.detail]\na=4\n";
    let document = preferences::decode_toml_document(text).unwrap();
    assert_eq!(
        document,
        json!({"a":{"b":{"x":1},"y":2},"rows":[{"x":1,"detail":{"a":3}},{"x":2,"detail":{"a":4}}]})
    );
    assert_eq!(preferences::decode_toml_document("").unwrap(), json!({}));
    let json = json!({"schema_version":1,"session_sources":[{"id":"source-a","enabled":true,"root":"/synthetic/한글"}]});
    assert_eq!(
        preferences::decode_toml_document(
            &preferences::encode_toml_document(json.clone()).unwrap()
        )
        .unwrap(),
        json
    );
}

#[test]
fn deep_dotted_tables_and_large_common_files_have_no_json_or_terminal_read_cap() {
    let f = Fixture::new();
    let current = f.write(&format!(
        "schema_version=1\n{}leaf=\"end\"\n",
        "deep.".repeat(1500)
    ));
    assert_eq!(current["raw"]["nodes"].as_array().unwrap().len(), 1503);
    assert!(!f.context.cache_dir.exists());
    let content = format!(
        "schema_version=1\nunknown=\"{}\"\n",
        "x".repeat(8 * 1024 * 1024 + 1)
    );
    let current = f.write(&content);
    assert_eq!(current["revision"], files::digest(content.as_bytes()));
    assert_eq!(
        f.call("terminal.read", json!({})).unwrap_err().code,
        "identity"
    );
    assert!(!f.context.cache_dir.exists());
}

#[test]
fn borrowed_lock_is_required_and_remains_held_after_publication() {
    let f = Fixture::new();
    let current = f.read();
    let args = json!({"changes":{},"revision":current["revision"]});
    assert_eq!(
        f.call("common.save", args.clone()).unwrap_err().kind,
        "transport"
    );
    assert!(!f.context.data_dir.exists());
    let wrong = File::open("/dev/null").unwrap();
    assert!(preferences::native_call(
        "common.save",
        &f.context,
        "UTC",
        args.clone(),
        Some(wrong.as_fd())
    )
    .is_err());
    let lease = f.lease();
    preferences::native_call("common.save", &f.context, "UTC", args, Some(lease.as_fd())).unwrap();
    let competitor = OpenOptions::new()
        .read(true)
        .write(true)
        .open(f.context.data_dir.join("operations.lock"))
        .unwrap();
    assert_ne!(
        unsafe { libc::flock(competitor.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) },
        0
    );
    drop(lease);
    assert_eq!(
        unsafe { libc::flock(competitor.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) },
        0
    );
    assert_eq!(
        fs::metadata(f.context.data_dir.join("settings.toml"))
            .unwrap()
            .permissions()
            .mode()
            & 0o777,
        0o600
    );
    f.no_temporary();
}

#[test]
fn absent_empty_directory_and_dangling_settings_link_remain_distinct() {
    let f = Fixture::new();
    let absent = f.read();
    assert_eq!(f.write(""), absent);
    let path = f.context.data_dir.join("settings.toml");
    fs::remove_file(&path).unwrap();
    fs::create_dir(&path).unwrap();
    assert!(f
        .call("common.read", json!({}))
        .unwrap_err()
        .message
        .contains("로컬 설정을 읽지 못"));
    fs::remove_dir(&path).unwrap();
    symlink(f.context.home_dir.join("absent"), &path).unwrap();
    assert_eq!(f.read(), absent);
    assert!(f
        .save(json!({}), absent["revision"].clone())
        .unwrap_err()
        .message
        .contains("심볼릭 링크"));
    assert!(path.is_symlink());
    f.no_temporary();
}

#[test]
fn terminal_save_keeps_unknown_values_and_reads_back_under_the_borrowed_lock() {
    let f = Fixture::new();
    let original = f.write(
        "schema_version=1\nunknown=0x10000000000000000000000000\n[terminal]\nfuture=\"keep\"\n",
    );
    let lease = f.lease();
    let result = preferences::native_call(
        "terminal.save",
        &f.context,
        "UTC",
        json!({"cwd":f.context.home_dir,"shell":"/bin/sh","revision":original["revision"]}),
        Some(lease.as_fd()),
    )
    .unwrap();
    assert_eq!(result["shell"], "/bin/sh");
    assert_eq!(result["cwd"], json!(f.context.home_dir));
    assert_eq!(result["preferences"]["revision"], files::digest(&f.bytes()));
    let text = String::from_utf8(f.bytes()).unwrap();
    assert!(text.contains("\"future\" = \"keep\""));
    assert!(text.contains("\"unknown\" = 1267650600228229401496703205376"));
    assert!(text.contains("\"onboarding_completed\" = false"));
    assert!(!f.context.cache_dir.exists());
    f.no_temporary();
}

#[test]
fn native_host_boundaries_are_explicit_and_do_not_depend_on_environment_mutation() {
    let f = Fixture::new();
    let options = preferences::NativeOptions {
        package_root: Some(f.context.home_dir.clone()),
        ..Default::default()
    };
    assert_eq!(
        preferences::native_call_with_options(
            "terminal.read",
            &f.context,
            "UTC",
            json!({}),
            None,
            &options
        )
        .unwrap_err()
        .code,
        "identity"
    );
    assert!(!f.context.data_dir.exists());
    let actual = f.context.home_dir.join("actual");
    fs::create_dir(&actual).unwrap();
    symlink(&actual, &f.context.data_dir).unwrap();
    assert_eq!(
        f.call("terminal.read", json!({})).unwrap_err().code,
        "identity"
    );
    assert!(!f.context.cache_dir.exists());
}

#[test]
fn terminal_legacy_json_measurement_preserves_size_and_nonfinite_error_order() {
    let f = Fixture::new();
    let current = f.read();
    let lease = f.lease();
    let args = json!({"root":0,"nodes":[
        {"kind":"table","value":[["cwd",1],["shell",2],["revision",3]]},
        {"kind":"float","value":"-nan"},
        {"kind":"string","value":"/bin/sh"},
        {"kind":"string","value":current["revision"]}
    ]});
    let options = preferences::NativeOptions::default();
    let error = preferences::native_call_tagged(
        "terminal.save",
        &f.context,
        "UTC",
        args.clone(),
        Some(lease.as_fd()),
        &options,
    )
    .unwrap_err();
    assert_eq!(error.code, "protocol");
    let mut huge = args;
    huge["nodes"][2]["value"] = json!("x".repeat(128 * 1024));
    let error = preferences::native_call_tagged(
        "terminal.save",
        &f.context,
        "UTC",
        huge,
        Some(lease.as_fd()),
        &options,
    )
    .unwrap_err();
    assert!(error.message.contains("요청이 너무 큽니다"));
    let surrogate = json!({"root":0,"nodes":[
        {"kind":"table","value":[["cwdOverride",1]]},
        {"kind":"surrogate-string","value":[55296]}
    ]});
    let error = preferences::native_call_tagged(
        "terminal.launch",
        &f.context,
        "UTC",
        surrogate,
        None,
        &options,
    )
    .unwrap_err();
    assert_eq!(error.kind, "io");
    assert_eq!(error.code, "unicode");
    // The old JSON encoder visits cwd before shell. Keep that failure order
    // when two malformed application values fail in different categories.
    let errors_in_order = json!({"root":0,"nodes":[
        {"kind":"table","value":[["cwd",1],["shell",2],["revision",3]]},
        {"kind":"unsupported","value":null},
        {"kind":"surrogate-string","value":[55296]},
        {"kind":"string","value":current["revision"]}
    ]});
    let error = preferences::native_call_tagged(
        "terminal.save",
        &f.context,
        "UTC",
        errors_in_order,
        Some(lease.as_fd()),
        &options,
    )
    .unwrap_err();
    assert_eq!(error.kind, "io");
    assert_eq!(error.code, "type");
    let encode_after_serialization = json!({"root":0,"nodes":[
        {"kind":"table","value":[["cwd",1],["shell",2],["revision",3]]},
        {"kind":"surrogate-string","value":[55296]},
        {"kind":"unsupported","value":null},
        {"kind":"string","value":current["revision"]}
    ]});
    let error = preferences::native_call_tagged(
        "terminal.save",
        &f.context,
        "UTC",
        encode_after_serialization,
        Some(lease.as_fd()),
        &options,
    )
    .unwrap_err();
    assert_eq!(error.code, "type");
    assert!(!f.context.data_dir.join("settings.toml").exists());
    f.no_temporary();
}
