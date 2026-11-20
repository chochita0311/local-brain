use localbrain_core::backend::{
    context_search::{
        engine::{self, ContextGenerator},
        tools::FileTools,
    },
    google_drive::policy,
    BackendError, Result,
};
use serde_json::{json, Value};
use std::{
    collections::VecDeque,
    fs,
    time::{Duration, SystemTime},
};
const OWNER:&str="../../docs/evidence/stages/stage-20261118-python-free-backend-evidence/workers/native-storage/";
fn load(name: &str) -> Value {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join(OWNER)
        .join(name);
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn outcome(value: Result<Value>, tool: bool) -> Value {
    match value {
        Ok(value) => json!({"ok":value}),
        Err(e) => {
            json!({"error":e.message,"code":if tool{Value::Null}else{json!(e.code)},"retryable":null})
        }
    }
}
struct Generator {
    outputs: VecDeque<String>,
    seen: Vec<Value>,
    cleared: bool,
}
impl ContextGenerator for Generator {
    fn generate(
        &mut self,
        messages: &[Value],
        _: &[Value],
        _: &localbrain_models::Cancellation,
    ) -> Result<String> {
        self.seen.push(json!(messages));
        Ok(self
            .outputs
            .pop_front()
            .expect("oracle generation exhausted"))
    }
    fn clear_turn(&mut self) {
        self.cleared = true
    }
}
#[test]
fn context_tools_and_five_complete_bounded_tool_loops_match_frozen_python() {
    use base64::Engine;
    let golden = load("context-search-python-golden.json");
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().canonicalize().unwrap();
    for (name, body) in golden["files"].as_object().unwrap() {
        let bytes = if ["binary", "utf16"].contains(&name.as_str()) {
            base64::engine::general_purpose::STANDARD
                .decode(body.as_str().unwrap())
                .unwrap()
        } else {
            body.as_str().unwrap().as_bytes().to_vec()
        };
        let path = root.join(name);
        fs::write(&path, bytes).unwrap();
        let at = SystemTime::UNIX_EPOCH + Duration::from_nanos(1700000000123456789);
        fs::OpenOptions::new()
            .write(true)
            .open(&path)
            .unwrap()
            .set_times(fs::FileTimes::new().set_modified(at).set_accessed(at))
            .unwrap();
    }
    let sources =
        [json!({"id":"own","name":"Demo vault","kind":"local","mode":"files","root":root})];
    let mut tools = FileTools::new(&sources).unwrap();
    for case in golden["cases"].as_array().unwrap() {
        assert_eq!(
            outcome(
                tools.call(case["name"].as_str().unwrap(), &case["arguments"]),
                true
            ),
            case["result"],
            "{} {}",
            case["name"],
            case["arguments"]
        );
    }
    for case in golden["loops"].as_array().unwrap() {
        let mut generator = Generator {
            outputs: case["outputs"]
                .as_array()
                .unwrap()
                .iter()
                .map(|s| s.as_str().unwrap().into())
                .collect(),
            seen: vec![],
            cleared: false,
        };
        let mut events = vec![];
        let answer = outcome(
            engine::answer(
                &mut generator,
                &sources,
                &[json!({"role":"user","content":"Who runs Airflow?"})],
                |v| {
                    events.push(v);
                    Ok(())
                },
                &localbrain_models::cancellation(),
            ),
            false,
        );
        assert_eq!(answer, case["result"]);
        assert_eq!(json!(events), case["events"]);
        assert_eq!(json!(generator.seen), case["seen"]);
        assert!(generator.cleared);
    }
}
#[test]
fn drive_urls_unicode_names_and_sixty_three_dst_calendar_slots_match_frozen_python() {
    let golden = load("drive-policy-python-golden.json");
    fn result(value: Result<Value>) -> Value {
        match value {
            Ok(v) => json!({"ok":v}),
            Err(e) => {
                json!({"error":e.message,"code":e.code,"retryable":e.details.as_ref().and_then(|v|v.get("retryable")).cloned().unwrap_or(Value::Null)})
            }
        }
    }
    for case in golden["urls"].as_array().unwrap() {
        let value = policy::root_url(case["input"].as_str().unwrap()).map(|v| json!([v.0, v.1]));
        assert_eq!(result(value), case["result"], "{}", case["input"]);
    }
    for case in golden["names"].as_array().unwrap() {
        let input = case["input"].as_str().unwrap();
        let value = (|| -> std::result::Result<Value, BackendError> {
            Ok(json!({"safe":policy::safe_name(input)?,"key":policy::name_key(input)?}))
        })();
        assert_eq!(result(value), case["result"], "{}", case["input"]);
    }
    for case in golden["slots"].as_array().unwrap() {
        let now = chrono::DateTime::parse_from_rfc3339(case["at"].as_str().unwrap())
            .unwrap()
            .to_utc();
        assert_eq!(
            localbrain_core::backend::clock::isoformat(
                policy::next_slot(
                    now,
                    case["minutes"].as_i64().unwrap(),
                    case["zone"].as_str().unwrap()
                )
                .unwrap()
            ),
            case["result"]
        );
    }
}
