//! Opt-in synthetic browser fixture. Never linked into a delivered executable.
use axum::{extract::Request, middleware, response::Response, routing::get, Json};
use localbrain_api::{
    routes,
    state::{database, AppState, FeatureBindings},
};
use localbrain_core::backend::{
    atlassian, contexts,
    ingest::{self, ScanControl},
    sessions,
    terminal::TerminalService,
    Config,
};
use serde_json::json;
use std::{fs, os::unix::fs::DirBuilderExt, path::PathBuf, time::Duration};
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
fn synthetic(root: PathBuf, desktop: bool, mode: &str) -> Result<AppState> {
    if !root.is_absolute() || root.exists() {
        return Err("A new absolute task-owned fixture root is required".into());
    }
    let repository = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .canonicalize()?;
    if root
        .parent()
        .ok_or("Fixture parent missing")?
        .canonicalize()?
        .starts_with(&repository)
    {
        return Err("Fixture must be outside the repository".into());
    }
    fs::DirBuilder::new().mode(0o700).create(&root)?;
    let mut config = Config::for_data_dir(root.join("data"));
    config.desktop = desktop;
    config.home_dir = root.join("home");
    config.cache_dir = root.join("cache");
    config.development_dir = root.join("development");
    config.context_root = root.join("context");
    config.codex_root = root.join("codex/sessions");
    config.claude_root = root.join("claude");
    config.hf_home = root.join("hub");
    config.hf_hub_cache = root.join("hub/cache");
    config.session_sources_path = Some(config.data_dir.join("session-sources.toml"));
    config.claude_bin = Some(root.join("missing-claude"));
    config.codex_bin = Some(root.join("missing-codex"));
    config.gcloud_path = Some(root.join("missing-gcloud"));
    config.web_root = repository.join("apps/web");
    config.installation_root = Some(repository);
    let features = if desktop {
        vec!["terminal"]
    } else {
        vec![
            "atlassian",
            "workstreams",
            "workflow",
            "auto_work",
            "terminal",
        ]
    };
    config = config.with_features(features.into_iter().map(str::to_owned))?;
    for path in [&config.data_dir, &config.home_dir, &config.codex_root] {
        fs::create_dir_all(path)?;
    }
    let terminal = mode == "terminal";
    let navigation = mode == "navigation";
    let terminal_settings = if terminal {
        fs::create_dir(root.join("demo-a"))?;
        fs::create_dir(root.join("demo-b"))?;
        fs::write(
            config.home_dir.join(".profile"),
            "PS1='demo> '\nexport PS1\n",
        )?;
        fs::write(
            config.home_dir.join(".zshrc"),
            "PROMPT='demo> '\nRPROMPT=''\n",
        )?;
        format!(
            "\n[terminal]\ncwd = {}\nshell = \"/bin/sh\"\n",
            json!(root.join("demo-a"))
        )
    } else {
        String::new()
    };
    fs::write(config.data_dir.join("settings.toml"),format!("schema_version = 1\nonboarding_completed = true\nstartup_screen = \"context\"\ntimezone = \"Europe/Paris\"\nsession_sync_enabled = false\nsession_sync_minutes = 40\ncontext_sync_enabled = false\ncontext_sync_minutes = 90\n{terminal_settings}"))?;
    fs::write(config.data_dir.join("session-sources.toml"),format!("schema_version = 2\n[[session_sources]]\nsource_id = 1\nprovider_kind = \"codex\"\ndisplay_label = \"Synthetic QA\"\nroot = {}\nagent_home = {}\ncolor = \"green\"\n",json!(config.codex_root),json!(root.join("codex"))))?;
    let state = AppState::initialize(
        config.clone(),
        "synthetic-qa-token".into(),
        FeatureBindings::for_config(&config)?,
    )?;
    let workspace = root
        .join("workspaces")
        .join("long-synthetic-path-".repeat(9));
    fs::create_dir_all(&workspace)?;
    let path = config.codex_root.join("qa.jsonl");
    fs::write(&path, "{}\n")?;
    database(&config, true, |conn| {
        conn.execute("INSERT INTO workspaces(id,canonical_path,display_name,exists_now) VALUES (1,?,'Synthetic QA',1)",[workspace.to_str()])?;
        conn.execute("INSERT INTO sessions(id,source_id,workspace_id,external_id,source_path,title,cwd_raw,started_at,last_event_at) VALUES (1,1,1,'synthetic-ui-qa',?,'Synthetic QA Session',?,'2026-11-01T00:00:00Z','2026-11-01T00:00:00Z')",rusqlite::params![path.to_str(),workspace.to_str()])?;
        if navigation {
            conn.execute("INSERT INTO usage_price_snapshots(id,label,source_ref,calculator_version,created_at) VALUES('synthetic-dashboard','Synthetic','fixture','fixture','2026-11-20')", [])?;
            let now = chrono::Utc::now();
            for (id, age) in [("dashboard-early", 28), ("dashboard-now", 0)] {
                let at = (now - chrono::Duration::days(age)).to_rfc3339();
                conn.execute("INSERT INTO usage_records(id,source_id,session_id,source_record_id,source_line,occurred_at,model_name,total_tokens,total_semantics,capability_state,capability_json,calculation_state,estimated_cost_usd,price_snapshot_id,calculator_version,calculated_at,attributed_at) VALUES(?,1,1,?,1,?,'synthetic',1000,'normalized','complete','{}','priced','1.25','synthetic-dashboard','fixture',?,?)", rusqlite::params![id,id,at,at,at])?;
            }
        }
        sessions::pin_session(conn, 1, None)?;
        conn.execute(
            "INSERT INTO workstreams(id,name) VALUES (1,'Synthetic QA')",
            [],
        )?;
        for status in ["queued", "completed", "failed"] {
            conn.execute("INSERT INTO maintenance_runs(id,workstream_id,task_type,status,started_at,result_path) VALUES (?,1,'organize_resources',?,'2026-11-01T00:00:00Z',?)",rusqlite::params![format!("qa-{status}"),status,root.join("missing-result").to_str()])?;
        }
        Ok(())
    })?;
    if desktop || navigation {
        fs::create_dir(&config.context_root)?;
        fs::write(
            config.context_root.join("example.md"),
            "# Synthetic linked document\nTrial reader evidence.",
        )?;
        let context = database(&config, true, |conn| {
            let id =
                contexts::add_context_root(conn, &config, config.context_root.to_str().unwrap())?;
            ingest::scan_context_root(
                conn,
                &config,
                id,
                true,
                &ScanControl::default(),
                state.services.observer.as_ref(),
            )?;
            let document: i64 =
                conn.query_row("SELECT id FROM context_documents", [], |row| row.get(0))?;
            conn.execute("INSERT INTO workstream_links(workstream_id,entity_type,entity_id) VALUES (1,'document',?)",[document.to_string()])?;
            Ok(id)
        })?;
        if navigation {
            for name in ["example.md", "second.md", "third.md"] {
                let paragraphs=(0..120).map(|i|format!("Paragraph {i}: synthetic navigation evidence with enough text to scroll.")).collect::<Vec<_>>().join("\n\n");
                fs::write(
                    config.context_root.join(name),
                    format!("# Synthetic {name}\n\n{paragraphs}"),
                )?;
            }
            database(&config, true, |conn| {
                ingest::scan_context_root(
                    conn,
                    &config,
                    context,
                    true,
                    &ScanControl::default(),
                    state.services.observer.as_ref(),
                )
            })?;
            let mut records = vec![
                json!({"type":"session_meta","timestamp":"2026-11-01T00:00:00Z","payload":{"id":"synthetic-ui-qa","cwd":workspace}}),
            ];
            records.extend((0..45).map(|i|json!({"type":"event_msg","timestamp":"2026-11-01T00:01:00Z","payload":{"type":"user_message","message":format!("Synthetic message {i}: {}","navigation evidence ".repeat(20))}})));
            fs::write(
                &path,
                records
                    .iter()
                    .map(|record| record.to_string() + "\n")
                    .collect::<String>(),
            )?;
            ingest::scan_codex_sessions(
                &config,
                true,
                &ScanControl::default(),
                state.services.observer.as_ref(),
            )?;
            let other = root.join("second-project");
            fs::create_dir(&other)?;
            database(&config, true, |conn| {
                for id in 2..36 {
                    conn.execute("INSERT INTO sessions(id,source_id,workspace_id,external_id,source_path,title,cwd_raw,started_at,last_event_at) VALUES (?,1,1,?,?,?,?,'2026-11-01T00:00:00Z','2026-11-01T00:00:00Z')",rusqlite::params![id,format!("synthetic-navigation-{id}"),config.codex_root.join(format!("retained-{id}.jsonl")).to_str(),format!("Synthetic navigation Session {id}"),workspace.to_str()])?;
                }
                conn.execute("INSERT INTO workspaces(canonical_path,display_name,exists_now) VALUES (?,'Second synthetic Project',1)",[other.to_str()])?;
                let other_id = conn.last_insert_rowid();
                conn.execute(
                    "UPDATE sessions SET workspace_id=?,cwd_raw=? WHERE id=35",
                    rusqlite::params![other_id, other.to_str()],
                )?;
                if !desktop {
                    let source = atlassian::access::register_source_instance(
                        conn,
                        &json!({"instance_key":"toolbar-qa-jira","provider_kind":"mcp_gateway","service":"jira","display_name":"Synthetic Jira"}),
                    )?;
                    atlassian::catalog::create_or_reuse_atlassian_stub(
                        conn,
                        &json!({"source_instance_id":source["id"],"url":"https://jira.example.test/browse/QA-1","title":"Synthetic toolbar issue","coverage":"indexed","observed_at":"2026-11-01T00:00:00Z"}),
                    )?;
                }
                Ok(())
            })?;
        }
    }
    Ok(state)
}
fn main() {
    let outcome = localbrain_core::backend::worker_thread("synthetic-browser-fixture")
        .spawn(run)
        .unwrap()
        .join()
        .unwrap();
    if let Err(error) = outcome {
        eprintln!("Synthetic fixture failed: {error}");
        std::process::exit(1);
    }
}
fn run() -> std::result::Result<(), String> {
    run_fixture().map_err(|error| error.to_string())
}
fn run_fixture() -> Result<()> {
    let args = std::env::args().skip(1).collect::<Vec<_>>();
    let root = PathBuf::from(args.first().ok_or("Fixture root required")?);
    let mode = args.get(2).map(String::as_str).unwrap_or("");
    // This process is an explicit test program. Its environment is isolated by
    // the launcher before any worker starts, including OS/terminal discovery.
    let state = synthetic(
        root.clone(),
        args.get(1).is_some_and(|value| value == "desktop"),
        mode,
    )?;
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .thread_stack_size(localbrain_core::backend::WORKER_STACK_BYTES)
        .build()?;
    runtime.block_on(async{
        let held=root.clone();let app=routes::router(state.clone()).route("/__qa__/fixture",get(||async{Json(json!({"fixture":"synthetic-ui-states-v1","backend":"rust"}))})).layer(middleware::from_fn(move|request:Request,next:middleware::Next|{let held=held.clone();async move{if request.uri().path()=="/help"&&request.uri().query().is_some_and(|query|query.split('&').any(|pair|pair=="navigation_delay=1")){while held.join("hold-navigation").exists(){tokio::time::sleep(Duration::from_millis(30)).await;}}let response:Response=next.run(request).await;response}}));
        let listener=tokio::net::TcpListener::bind(("127.0.0.1",0)).await?;fs::write(root.join("port.json"),json!({"port":listener.local_addr()?.port()}).to_string())?;
        let shutdown=state.shutdown.clone();tokio::spawn(async move{let mut term=tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()).unwrap();tokio::select!{_=tokio::signal::ctrl_c()=>{},_=term.recv()=>{}}shutdown.request();});
        let shutdown=state.shutdown.clone();axum::serve(listener,app).with_graceful_shutdown(async move{shutdown.wait().await;}).await?;
        if mode=="terminal"{let service=TerminalService::new(&state.config)?;let current=service.list()?;if current["running"]==true{let terminals=current["terminals"].as_array().ok_or("Invalid owned terminal state")?.iter().map(|terminal|terminal["id"].clone()).collect::<Vec<_>>();service.call("service.stop",json!({"force":true,"expected":{"generation":current["generation"],"terminals":terminals}}))?;}}
        state.services.stop()?;Ok::<_,Box<dyn std::error::Error>>(())
    })
}
