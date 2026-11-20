use localbrain_core::backend::{
    db,
    insights::{evidence::*, runs::get_insight_run, skills::skill_insights_data, usage::*},
    json as codec, sessions, usage as accounting, Config,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::{fs, path::Path};
const NOW: &str = "2026-09-28T12:00:00+00:00";
fn usage() -> Value {
    json!({"input_tokens":1000,"cached_input_tokens":800,"output_tokens":100,"reasoning_output_tokens":40})
}
fn setup(root: &Path) -> (Config, Connection) {
    let mut config = Config::for_data_dir(root.join("data"));
    config.timezone_name = "UTC".into();
    fs::create_dir_all(&config.home_dir).unwrap();
    let connection = Connection::open_in_memory().unwrap();
    connection.execute_batch(db::SCHEMA).unwrap();
    connection
        .execute(
            "INSERT INTO sources(id,provider_kind,name,root_path)VALUES(1,'codex','Company',?)",
            [config.home_dir.join("sessions").to_string_lossy()],
        )
        .unwrap();
    connection
        .execute(
            "INSERT INTO sources(id,provider_kind,name,root_path)VALUES(2,'codex','Personal',?)",
            [root.join("personal/sessions").to_string_lossy()],
        )
        .unwrap();
    (config, connection)
}
fn run(
    connection: &Connection,
    config: &Config,
    index: u64,
    status: &str,
    model: &str,
    legacy: bool,
) -> Value {
    let id = format!("ins-{index:016x}");
    let root = config.data_dir.join("personal-insight-runs").join(&id);
    fs::create_dir_all(&root).unwrap();
    let mut options = json!({"codex_home":config.home_dir});
    if !legacy {
        options["service_tier"] = json!("standard");
        options["usage_source_id"] = json!(1);
    }
    connection.execute("INSERT INTO personal_insight_runs(id,mode,status,runner,model,settings_json,guide_version,evidence_version,evidence_path,prompt_path,response_path,report_path,stream_path,stderr_path,coverage_json,created_at,updated_at,started_at,completed_at)VALUES(?,'discover',?,'codex',?,?,'synthetic','synthetic',?,?,?,?,?,?,'{}',?,?,?,?)",params![id,status,model,serde_json::to_string(&options).unwrap(),root.join("evidence.json").to_string_lossy(),root.join("prompt.md").to_string_lossy(),root.join("response.json").to_string_lossy(),root.join("report.md").to_string_lossy(),root.join("stream.jsonl").to_string_lossy(),root.join("stderr.log").to_string_lossy(),NOW,NOW,NOW,if status=="queued"{None}else{Some(NOW)}]).unwrap();
    get_insight_run(connection, &id).unwrap().unwrap()
}
#[test]
fn all_frozen_normalizer_precision_missing_and_malformed_observations_match() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../src/backend/insights/fixtures/usage-golden.json"
    ))
    .unwrap();
    for case in fixture["cases"].as_array().unwrap() {
        let observed = codec::decode(case["usage_json"].as_str().unwrap()).unwrap();
        let record = usage_record(
            &case["run"],
            &observed,
            &case["options"],
            case["at"].as_str().unwrap(),
            case["line"].as_i64().unwrap(),
        )
        .unwrap();
        assert_eq!(
            serde_json::to_value(record).unwrap(),
            case["expected"],
            "{}",
            case["name"]
        );
    }
}
#[test]
fn one_charge_survives_replay_and_stays_out_of_work_evidence_and_project_composition() {
    let directory = tempfile::tempdir().unwrap();
    let (config, connection) = setup(directory.path());
    let run = run(&connection, &config, 1, "completed", "gpt-6-astra", false);
    store_insight_usage(&connection, &config, &run, &usage(), NOW, 1).unwrap();
    let first = db::row(&connection, "SELECT * FROM usage_records", [])
        .unwrap()
        .unwrap();
    assert_eq!(
        (
            first["input_tokens"].as_i64(),
            first["cache_read_tokens"].as_i64(),
            first["output_tokens"].as_i64(),
            first["total_tokens"].as_i64()
        ),
        (Some(200), Some(800), Some(100), Some(1100))
    );
    assert_eq!(first["estimated_cost_usd"], "0.007800000000");
    store_insight_usage(
        &connection,
        &config,
        &run,
        &usage(),
        "2026-10-01T12:00:00Z",
        0,
    )
    .unwrap();
    let second = db::row(&connection, "SELECT * FROM usage_records", [])
        .unwrap()
        .unwrap();
    for field in [
        "id",
        "occurred_at",
        "price_snapshot_id",
        "calculated_at",
        "attributed_at",
    ] {
        assert_eq!(first[field], second[field], "{field}");
    }
    accounting::reconcile_usage_record_contract(&connection, 1, &[]).unwrap();
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM usage_records", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
    assert_eq!(
        sessions::session_inventory_page(&connection, None, None, 1).unwrap()["total"],
        0
    );
    for table in [
        "activity_events",
        "search_index",
        "workspaces",
        "source_files",
    ] {
        assert_eq!(
            connection
                .query_row(&format!("SELECT COUNT(*) FROM {table}"), [], |r| r
                    .get::<_, i64>(0))
                .unwrap(),
            0
        );
    }
    let manifest = build_insight_evidence_manifest(
        &connection,
        &EvidenceRequest::new("discover", "2026-09-28T13:00:00Z".parse().unwrap()),
    )
    .unwrap();
    assert_eq!(manifest["coverage"]["eligible_sessions"], 0);
    let options = accounting::UsageOptions {
        today: Some("2026-09-28".parse().unwrap()),
        now: Some("2026-09-28T13:00:00Z".parse().unwrap()),
        ..Default::default()
    };
    let all = accounting::usage_dashboard_data(&connection, &options).unwrap();
    assert_eq!(all["aggregate"]["estimated_cost"].as_f64(), Some(0.0078));
    assert_eq!(all["aggregate"]["session_count"], 0);
    let projects = accounting::usage_dashboard_data(
        &connection,
        &accounting::UsageOptions {
            breakdown: "project".into(),
            ..options
        },
    )
    .unwrap();
    assert!(projects["breakdown"]["rows"].as_array().unwrap().is_empty());
    assert_eq!(
        insight_usage_cost(&connection, run["id"].as_str().unwrap())
            .unwrap()
            .unwrap()["cost_label"],
        "$0.0078"
    );
}
#[test]
fn absent_malformed_unknown_and_aggregate_context_are_never_priced_as_zero() {
    let directory = tempfile::tempdir().unwrap();
    let (config, connection) = setup(directory.path());
    let mut cases = vec![
        (
            json!({"input_tokens":1000,"output_tokens":100}),
            "gpt-6-astra",
            "partial",
        ),
        (usage(), "synthetic-unknown-model", "unpriced"),
    ];
    for (field, value, state) in [
        ("input_tokens", json!(true), "failed"),
        ("cached_input_tokens", json!(1001), "failed"),
        ("reasoning_output_tokens", json!(101), "failed"),
        ("input_tokens", json!(300_000), "partial"),
    ] {
        let mut observed = usage();
        observed[field] = value;
        cases.push((observed, "gpt-6-astra", state));
    }
    for (index, (observed, model, state)) in cases.into_iter().enumerate() {
        let run = run(
            &connection,
            &config,
            index as u64 + 1,
            "failed",
            model,
            false,
        );
        store_insight_usage(&connection, &config, &run, &observed, NOW, 0).unwrap();
        let row = insight_usage_cost(&connection, run["id"].as_str().unwrap())
            .unwrap()
            .unwrap();
        assert_eq!(row["calculation_state"], state);
        assert!(row["estimated_cost_usd"].is_null());
        assert!(row["cost_label"].is_null());
    }
    let zero = run(&connection, &config, 30, "completed", "gpt-6-astra", false);
    store_insight_usage(&connection,&config,&zero,&json!({"input_tokens":0,"cached_input_tokens":0,"output_tokens":0,"reasoning_output_tokens":0}),NOW,0).unwrap();
    assert_eq!(
        insight_usage_cost(&connection, zero["id"].as_str().unwrap())
            .unwrap()
            .unwrap()["cost_label"],
        "$0.0000"
    );
    let small = run(&connection, &config, 31, "completed", "gpt-6-astra", false);
    store_insight_usage(&connection,&config,&small,&json!({"input_tokens":1,"cached_input_tokens":0,"output_tokens":0,"reasoning_output_tokens":0}),NOW,0).unwrap();
    assert_eq!(
        insight_usage_cost(&connection, small["id"].as_str().unwrap())
            .unwrap()
            .unwrap()["cost_label"],
        "<$0.0001"
    );
    assert!(insight_usage_cost(&connection, "ins-ffffffffffffffff")
        .unwrap()
        .is_none());
}
#[test]
fn exact_home_source_binding_resolves_aliases_and_refuses_ambiguity_or_drift() {
    use std::os::unix::fs::symlink;
    let directory = tempfile::tempdir().unwrap();
    let (config, connection) = setup(directory.path());
    let root = directory.path().join("retained");
    fs::create_dir(&root).unwrap();
    symlink(&root, config.home_dir.join("sessions")).unwrap();
    let options = json!({"codex_home":config.home_dir});
    assert_eq!(
        insight_usage_source(&connection, &config, &options).unwrap()["id"],
        1
    );
    connection
        .execute(
            "INSERT INTO sources(id,provider_kind,name,root_path)VALUES(3,'codex','Duplicate',?)",
            [root.to_string_lossy()],
        )
        .unwrap();
    assert!(insight_usage_source(&connection, &config, &options).is_err());
    let mut frozen = options.clone();
    frozen["usage_source_id"] = json!(1);
    assert_eq!(
        insight_usage_source(&connection, &config, &frozen).unwrap()["id"],
        1
    );
    frozen["usage_source_id"] = json!(2);
    assert!(insight_usage_source(&connection, &config, &frozen).is_err());
    frozen["usage_source_id"] = json!("1");
    assert!(insight_usage_source(&connection, &config, &frozen).is_err());
}
#[test]
fn terminal_recovery_keeps_emitted_usage_is_idempotent_and_does_not_invent_observations() {
    let directory = tempfile::tempdir().unwrap();
    let (config, connection) = setup(directory.path());
    for (index, status) in ["completed", "failed", "cancelled", "interrupted"]
        .iter()
        .enumerate()
    {
        let run = run(
            &connection,
            &config,
            index as u64 + 1,
            status,
            "gpt-6-astra",
            true,
        );
        if *status == "completed" {
            connection
                .execute(
                    "UPDATE personal_insight_runs SET usage_json=? WHERE id=?",
                    params![usage().to_string(), run["id"].as_str()],
                )
                .unwrap();
        } else {
            fs::write(
                run["stream_path"].as_str().unwrap(),
                format!(
                    "malformed\n[]\n{}\n",
                    json!({"type":"turn.completed","usage":usage()})
                ),
            )
            .unwrap();
        }
    }
    run(&connection, &config, 9, "failed", "gpt-6-astra", false);
    run(&connection, &config, 10, "running", "gpt-6-astra", false);
    assert_eq!(recover_insight_usage(&connection, &config).unwrap(), 4);
    assert_eq!(recover_insight_usage(&connection, &config).unwrap(), 0);
    assert_eq!(
        connection
            .query_row("SELECT COUNT(*) FROM usage_records", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        4
    );
    let record = db::row(
        &connection,
        "SELECT capability_json FROM usage_records LIMIT 1",
        [],
    )
    .unwrap()
    .unwrap();
    let cap: Value = serde_json::from_str(record["capability_json"].as_str().unwrap()).unwrap();
    assert_eq!(cap["service_tier_source"], "unmarked_default_assumption");
}
#[test]
fn skill_ranking_counts_source_native_session_once_and_reports_current_file_coverage() {
    let directory = tempfile::tempdir().unwrap();
    let (config, connection) = setup(directory.path());
    assert_eq!(
        skill_insights_data(&connection).unwrap()["coverage"]["state"],
        "not_scanned"
    );
    for (id, source, external, event, name, key, state, time) in [
        (
            "1",
            1,
            "same-native",
            "a",
            "alpha",
            "alpha",
            "observed",
            "2026-09-27T12:00:00Z",
        ),
        (
            "2",
            1,
            "same-native",
            "b",
            "alpha",
            "alpha",
            "observed",
            "2026-09-28T12:00:00Z",
        ),
        (
            "3",
            2,
            "same-native",
            "c",
            "alpha",
            "alpha",
            "observed",
            "2026-09-29T12:00:00Z",
        ),
        ("4", 1, "other", "d", "beta", "beta", "observed", "invalid"),
        (
            "5",
            1,
            "third",
            "e",
            "beta",
            "beta",
            "corrected",
            "2026-09-30T00:00:00Z",
        ),
    ] {
        connection.execute("INSERT INTO skill_observations(id,source_id,provider_kind,external_session_id,native_event_id,skill_name,skill_group_key,signal_kind,source_line,state,occurred_at)VALUES(?,?,'codex',?,?,?,?,'codex_skill_read',1,?,?)",params![id,source,external,event,name,key,state,time]).unwrap();
    }
    let result = skill_insights_data(&connection).unwrap();
    assert_eq!(
        result["ranking"],
        json!([{"rank":1,"name":"alpha","use_count":2,"last_used_at":"2026-09-29T12:00:00Z"},{"rank":2,"name":"beta","use_count":1,"last_used_at":null}])
    );
    connection.execute("INSERT INTO source_files(source_id,path,size_bytes,mtime_ns,last_scanned_at,presence_state,session_contract_version)VALUES(1,?,0,0,'fixed','PRESENT',?)",params![config.home_dir.join("one.jsonl").to_string_lossy(),localbrain_core::backend::ingest::CODEX_SESSION_REVISION]).unwrap();
    assert_eq!(
        skill_insights_data(&connection).unwrap()["coverage"]["state"],
        "current"
    );
    connection
        .execute("UPDATE source_files SET presence_state='MISSING'", [])
        .unwrap();
    let before = connection.total_changes();
    let result = skill_insights_data(&connection).unwrap();
    assert_eq!(result["coverage"]["state"], "partial");
    assert_eq!(result["top"]["use_count"], 2);
    assert_eq!(connection.total_changes(), before);
}
