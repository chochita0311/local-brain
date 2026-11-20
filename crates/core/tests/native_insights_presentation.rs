use localbrain_core::backend::{
    db,
    insights::{guidance::*, presentation::*},
    Config,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs;
#[test]
fn complete_frozen_reports_prompt_and_all_historical_resources_match() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../src/backend/insights/fixtures/presentation-golden.json"
    ))
    .unwrap();
    for (index, case) in fixture["reports"].as_array().unwrap().iter().enumerate() {
        assert_eq!(
            render_report(&case["run"], &case["manifest"], &case["result"]).unwrap(),
            case["expected"],
            "report {index}"
        );
    }
    let bundle = build_guide_bundle(&fixture["prompt_manifest"]).unwrap();
    assert_eq!(
        prompt(&fixture["prompt_manifest"], &bundle).unwrap(),
        fixture["prompt"]
    );
    for (path, digest) in fixture["resource_digests"].as_object().unwrap() {
        let content = guide_resource(path).unwrap();
        assert_eq!(
            format!("{:x}", Sha256::digest(content.as_bytes())),
            digest.as_str().unwrap(),
            "{path}"
        );
    }
    assert!(guide_resource("../core-v8.md").is_none());
    assert_eq!(
        plain(" \n`*_{}[]<>#|$\\\nline "),
        "\\`\\*\\_\\{\\}\\[\\]\\<\\>\\#\\|\\$\\\\  \nline"
    );
}
#[test]
fn retained_report_review_is_read_only_and_only_manifest_session_routes_are_trusted() {
    let directory = tempfile::tempdir().unwrap();
    let config = Config::for_data_dir(directory.path().join("data"));
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES(1,'codex','Synthetic','/synthetic/sessions')",[]).unwrap();
    connection.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title)VALUES(1,1,'one','/synthetic/one','Synthetic')",[]).unwrap();
    connection.execute("INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,source_line)VALUES('event-one',1,1,'message','user','Synthetic question',1)",[]).unwrap();
    let id = "ins-0123456789abcdef";
    let root = config.data_dir.join("personal-insight-runs").join(id);
    fs::create_dir_all(&root).unwrap();
    let manifest = json!({"sessions":[{"session_id":1,"events":[{"source_id":1,"provider_kind":"codex","session_id":1,"event_id":"event-one","sequence":1,"role":"user","occurred_at":null,"text_revision":format!("{:x}",Sha256::digest(b"Synthetic question"))}]}]});
    let evidence = root.join("evidence.json");
    let response = root.join("response.json");
    let report = root.join("report.md");
    fs::write(&evidence, serde_json::to_vec(&manifest).unwrap()).unwrap();
    fs::write(&response,br#"{"findings":[{"evidence_ids":["event-one"],"counterevidence_ids":[]}],"selection_evidence_ids":["event-one"]}"#).unwrap();
    fs::write(
        &report,
        "# Synthetic report\n\n[Allowed](/sessions/1) [Absent](/sessions/9999)\n",
    )
    .unwrap();
    connection.execute("INSERT INTO personal_insight_runs(id,mode,status,runner,model,settings_json,guide_version,evidence_version,evidence_path,prompt_path,response_path,report_path,stream_path,stderr_path,coverage_json,created_at,updated_at)VALUES(?,'discover','completed','codex','synthetic','{}','synthetic','synthetic',?,?,?,?,?,?,'{}','2026-09-30','2026-09-30')",params![id,evidence.to_string_lossy(),root.join("prompt.md").to_string_lossy(),response.to_string_lossy(),report.to_string_lossy(),root.join("stream.jsonl").to_string_lossy(),root.join("stderr.log").to_string_lossy()]).unwrap();
    let request = PageRequest {
        selected_id: Some(id.into()),
        ..Default::default()
    };
    let before = connection.total_changes();
    let original = fs::read(&evidence).unwrap();
    let view = page_data(&connection, &config, &request, &[]).unwrap();
    assert_eq!(
        view["reference_states"],
        json!({"current":1,"stale":0,"unavailable":0})
    );
    let html = view["report_html"].as_str().unwrap();
    assert!(html.contains("href=\"/sessions/1\""));
    assert!(!html.contains("/sessions/9999"));
    assert_eq!(connection.total_changes(), before);
    assert_eq!(fs::read(&evidence).unwrap(), original);
    assert!(download_report_path(&config, &view["selected_run"]).is_ok());
    connection
        .execute(
            "UPDATE activity_events SET text='Changed source' WHERE id='event-one'",
            [],
        )
        .unwrap();
    assert_eq!(
        page_data(&connection, &config, &request, &[]).unwrap()["reference_states"]["stale"],
        1
    );
    fs::write(&response, br#"{"findings":null}"#).unwrap();
    assert!(page_data(&connection, &config, &request, &[]).unwrap()["reference_states"].is_null());
    fs::remove_file(&response).unwrap();
    let missing = page_data(&connection, &config, &request, &[]).unwrap();
    assert!(missing["reference_states"].is_null());
    assert!(missing["report_html"]
        .as_str()
        .unwrap()
        .contains("href=\"/sessions/1\""));
    assert!(page_data(
        &connection,
        &config,
        &PageRequest {
            selected_id: Some("ins-ffffffffffffffff".into()),
            ..Default::default()
        },
        &[]
    )
    .is_err());
    let mut other = view["selected_run"].clone();
    other["report_path"] = json!(directory.path().join("other.md"));
    assert!(download_report_path(&config, &other).is_err());
}
