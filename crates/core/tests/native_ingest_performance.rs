//! Explicit synthetic timing probe; no user corpus or service is involved.
use localbrain_core::backend::ingest::parse_session;
use serde_json::json;
use std::{fs, time::Instant};

#[test]
#[ignore = "manual 10,000-message compatibility performance evidence"]
fn ordinary_ten_thousand_message_parse_timings() {
    let temp = tempfile::Builder::new()
        .prefix("lb-native-ingest-timing-")
        .tempdir()
        .unwrap();
    for provider in ["claude", "codex"] {
        let mut text = String::new();
        if provider == "codex" {
            text.push_str(
                "{\"type\":\"session_meta\",\"payload\":{\"id\":\"synthetic-timing\"}}\n",
            );
        }
        for index in 0..10_000 {
            let message = format!(
                "Synthetic ordinary message {index}: retain the original parser event and title."
            );
            let record = if provider == "claude" {
                json!({"type":"user","sessionId":"synthetic-timing","message":{"content":message}})
            } else {
                json!({"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":message}]}})
            };
            text.push_str(&record.to_string());
            text.push('\n');
        }
        for compressed in [false, true] {
            let filename = if compressed {
                "ordinary.jsonl.zst"
            } else {
                "ordinary.jsonl"
            };
            let path = temp.path().join(filename);
            let bytes = if compressed {
                zstd::stream::encode_all(text.as_bytes(), 1).unwrap()
            } else {
                text.as_bytes().to_vec()
            };
            fs::write(&path, &bytes).unwrap();
            let mut elapsed_ms = Vec::new();
            for _ in 0..3 {
                let start = Instant::now();
                let parsed = parse_session(provider, &path).unwrap().unwrap();
                elapsed_ms.push(start.elapsed().as_secs_f64() * 1000.0);
                assert_eq!(parsed.events.len(), 10_000);
                assert_eq!(parsed.skipped_lines, 0);
                assert_eq!(parsed.external_id, "synthetic-timing");
            }
            println!(
                "{}",
                json!({"provider":provider,"compressed":compressed,"messages":10000,"input_bytes":bytes.len(),"uncompressed_bytes":text.len(),"elapsed_ms":elapsed_ms})
            );
        }
    }
}
