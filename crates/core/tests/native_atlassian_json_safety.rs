use localbrain_core::backend::{json, WORKER_STACK_BYTES};
use std::process::Command;

#[test]
fn deep_json_does_not_abort_small_threads_or_native_host_workers() {
    for stack in [2 * 1024 * 1024, WORKER_STACK_BYTES] {
        for kind in ["array", "object", "malformed", "nonfinite", "surrogate"] {
            for depth in [190, 900, 995, 996, 1000, 1001, 1100, 10_000, 100_000] {
                let output = Command::new(std::env::current_exe().unwrap())
                    .args([
                        "--exact",
                        "json_depth_child",
                        "--ignored",
                        "--nocapture",
                        "--test-threads=1",
                    ])
                    .env("LOCALBRAIN_NATIVE_JSON_PROBE_DEPTH", depth.to_string())
                    .env("LOCALBRAIN_NATIVE_JSON_PROBE_KIND", kind)
                    .env("LOCALBRAIN_NATIVE_JSON_PROBE_STACK", stack.to_string())
                    .output()
                    .unwrap();
                assert!(
                    output.status.success(),
                    "kind={kind} depth={depth} stack={stack} status={}\n{}\n{}",
                    output.status,
                    String::from_utf8_lossy(&output.stdout),
                    String::from_utf8_lossy(&output.stderr)
                );
                eprintln!("child passed kind={kind} depth={depth} stack={stack}");
            }
        }
    }
}

#[test]
#[ignore = "invoked only by isolated child-process regression"]
fn json_depth_child() {
    let Ok(depth) = std::env::var("LOCALBRAIN_NATIVE_JSON_PROBE_DEPTH") else {
        return;
    };
    let depth: usize = depth.parse().unwrap();
    let kind = std::env::var("LOCALBRAIN_NATIVE_JSON_PROBE_KIND").unwrap();
    let stack: usize = std::env::var("LOCALBRAIN_NATIVE_JSON_PROBE_STACK")
        .unwrap()
        .parse()
        .unwrap();
    std::thread::Builder::new()
        .name("synthetic-json-host".into())
        .stack_size(stack)
        .spawn(move || {
            let (opening, closing) = if kind == "object" {
                (r#"{"x":"#, "}")
            } else {
                ("[", "]")
            };
            let leaf = match kind.as_str() {
                "nonfinite" => "NaN",
                "surrogate" => r#""\ud800""#,
                // These are quoted brackets and escaped quotes, not nesting.
                _ => r#""[{\"\\\"}]""#,
            };
            let raw = format!("{}{leaf}{}", opening.repeat(depth), closing.repeat(depth));
            if kind == "malformed" {
                let invalid = format!("{}!{}", opening.repeat(depth), closing.repeat(depth));
                assert!(json::decode(&invalid).is_err());
                // A complete deep value followed by bad input must safely drop
                // its tree when the end-of-document check fails.
                assert!(json::decode(&format!("{raw} trailing")).is_err());
                return;
            }
            if kind == "surrogate" {
                let scope = json::Scope::for_document(&raw);
                let parsed = scope.parse(&raw);
                if depth > 1000 {
                    assert!(parsed.is_err());
                } else {
                    let value = parsed.unwrap();
                    assert!(scope.materialized(&value).is_err());
                    drop(value);
                }
                assert!(json::decode(&raw).is_err());
                return;
            }
            let result = json::decode(&raw);
            if depth > 1000 {
                assert!(result.is_err());
                assert!(json::decode_unique(raw.as_bytes()).is_err());
                return;
            }
            let value = result.unwrap();
            // Value's derived clone/serde serializer are recursive. Application
            // host and sync workers use the shared 32MiB stack boundary.
            if stack >= WORKER_STACK_BYTES {
                let cloned = value.clone();
                let serialized = serde_json::to_string(&cloned).unwrap();
                assert_eq!(serialized, raw);
                drop(cloned);
            }
            if kind == "nonfinite" {
                assert_eq!(json::canonical(&value).unwrap(), raw);
                assert!(json::encode_http(&value).is_err());
                assert!(json::decode_unique(raw.as_bytes()).is_err());
            } else {
                assert_eq!(json::encode_http(&value).unwrap(), raw);
                let protocol_value = json::decode_unique(raw.as_bytes()).unwrap();
                drop(protocol_value);
            }
            // Even a library caller with a 2MiB thread can discard a parsed
            // maximum-depth value without a recursive parser/serializer.
            drop(value);
        })
        .unwrap()
        .join()
        .unwrap();
}
