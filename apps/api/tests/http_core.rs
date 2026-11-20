use axum::{
    body::{to_bytes, Body},
    http::{Request, StatusCode},
    response::Response,
    Router,
};
use localbrain_api::{
    routes,
    state::{AppState, FeatureBindings},
};
use localbrain_core::backend::Config;
use serde_json::{json, Value};
use tower::ServiceExt;

struct Host {
    root: tempfile::TempDir,
    state: AppState,
    router: Router,
}
impl Host {
    fn new(desktop: bool) -> Self {
        Self::features(desktop, &[])
    }
    fn features(desktop: bool, features: &[&str]) -> Self {
        let root = tempfile::Builder::new()
            .prefix("lb-http-")
            .tempdir_in("/private/tmp")
            .unwrap();
        let mut config = Config::for_data_dir(root.path().join("data"));
        config.desktop = desktop;
        config.claude_bin = Some(root.path().join("missing-claude"));
        config.codex_bin = Some(root.path().join("missing-codex"));
        let config = config
            .with_features(features.iter().map(|feature| (*feature).into()))
            .unwrap();
        std::fs::create_dir(&config.home_dir).unwrap();
        std::fs::create_dir(&config.data_dir).unwrap();
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&config.data_dir, std::fs::Permissions::from_mode(0o700)).unwrap();
        localbrain_core::backend::storage::files::atomic_write(&config.data_dir.join("settings.toml"),b"schema_version = 1\nonboarding_completed = false\nsession_sync_enabled = false\ncontext_sync_enabled = false\n").unwrap();
        let bindings = FeatureBindings::for_config(&config).unwrap();
        let state =
            AppState::initialize(config, "synthetic-launch-token".into(), bindings).unwrap();
        let router = routes::router(state.clone());
        Self {
            root,
            state,
            router,
        }
    }
    async fn request(&self, method: &str, path: &str, body: Value) -> Response {
        self.router
            .clone()
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri(path)
                    .header("host", "127.0.0.1:8123")
                    .header("origin", "http://127.0.0.1:8123")
                    .header("content-type", "application/json")
                    .body(if matches!(method, "GET" | "HEAD") {
                        Body::empty()
                    } else {
                        Body::from(body.to_string())
                    })
                    .unwrap(),
            )
            .await
            .unwrap()
    }
    async fn form(&self, method: &str, path: &str, body: &str) -> Response {
        self.router
            .clone()
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri(path)
                    .header("host", "127.0.0.1:8123")
                    .header("origin", "http://127.0.0.1:8123")
                    .header("content-type", "application/x-www-form-urlencoded")
                    .body(Body::from(body.to_owned()))
                    .unwrap(),
            )
            .await
            .unwrap()
    }
}
impl Drop for Host {
    fn drop(&mut self) {
        self.state.services.stop().unwrap();
    }
}
async fn bytes(response: Response) -> Vec<u8> {
    to_bytes(response.into_body(), 8 * 1024 * 1024)
        .await
        .unwrap()
        .to_vec()
}
async fn document(response: Response) -> Value {
    serde_json::from_slice(&bytes(response).await).unwrap()
}

#[tokio::test]
async fn default_dashboard_serves_the_last_complete_summary_before_refreshing() {
    use localbrain_core::backend::{db, preferences};
    let host = Host::new(false);
    let host_ref = &host;
    let get = |path: &'static str| async move {
        let response = host_ref.request("GET", path, Value::Null).await;
        assert_eq!(response.status(), 200, "{path}");
        String::from_utf8(bytes(response).await).unwrap()
    };
    let config = &host.state.config;
    let connection = db::connect(config).unwrap();
    connection.execute_batch("INSERT INTO sources(id,provider_kind,name,root_path) VALUES(31,'codex','Synthetic dashboard source','/synthetic'); INSERT INTO sessions(id,source_id,external_id,source_path,title) VALUES(31,31,'dashboard','/synthetic/usage.jsonl','Synthetic session'); INSERT INTO usage_price_snapshots(id,label,source_ref,calculator_version,created_at) VALUES('synthetic-dashboard','Synthetic','synthetic','synthetic','2026-11-20');").unwrap();
    connection.execute("INSERT INTO usage_records(id,source_id,session_id,source_record_id,source_line,occurred_at,model_name,total_tokens,total_semantics,capability_state,capability_json,calculation_state,estimated_cost_usd,price_snapshot_id,calculator_version,calculated_at,attributed_at) VALUES('dash',31,31,'dash',1,?,'synthetic-dashboard-model',27000,'normalized','complete','{}','priced','41.23','synthetic-dashboard','synthetic','2026-11-20','2026-11-20')",[chrono::Utc::now().to_rfc3339()]).unwrap();
    drop(connection);
    let first = get("/sessions-dashboard").await;
    assert!(first.contains("<strong>$41.23</strong>"));
    assert!(first.contains("class=\"usage-history-chart\""));
    assert!(!first.contains("data-usage-refresh="));
    let current = get("/sessions-dashboard").await;
    assert!(current.contains("<strong>$41.23</strong>"));
    assert!(!current.contains("data-usage-refresh="));

    let connection = db::connect(config).unwrap();
    connection
        .execute(
            "UPDATE usage_records SET estimated_cost_usd='73.50' WHERE id='dash'",
            [],
        )
        .unwrap();
    drop(connection);
    let stale = get("/sessions-dashboard").await;
    assert!(stale.contains("<strong>$41.23</strong>"));
    assert!(stale.contains("data-usage-refresh=\"/sessions-dashboard/refresh\""));
    let filtered = get("/sessions-dashboard?metric=tokens").await;
    assert!(filtered.contains("<strong>$73.50</strong>"));
    assert!(!filtered.contains("data-usage-refresh="));
    let updated = get("/sessions-dashboard?refresh=1").await;
    assert!(updated.contains("<strong>$73.50</strong>"));
    assert!(get("/sessions-dashboard")
        .await
        .contains("<strong>$73.50</strong>"));

    let settings = preferences::read_preferences(config).unwrap();
    preferences::save_preferences(
        config,
        &json!({"timezone":"America/Los_Angeles"}),
        &settings["revision"],
    )
    .unwrap();
    db::connect(config)
        .unwrap()
        .execute(
            "UPDATE usage_records SET estimated_cost_usd='92.15' WHERE id='dash'",
            [],
        )
        .unwrap();
    let new_zone = get("/sessions-dashboard").await;
    assert!(new_zone.contains("<strong>$92.15</strong>"));
    assert!(!new_zone.contains("data-usage-refresh="));
}

#[tokio::test]
async fn first_dashboard_calculation_failure_offers_a_retry_in_the_page() {
    let host = Host::new(false);
    let connection = localbrain_core::backend::db::connect(&host.state.config).unwrap();
    connection
        .execute_batch("DROP TABLE usage_records;")
        .unwrap();
    drop(connection);

    let response = host
        .request("GET", "/sessions-dashboard", Value::Null)
        .await;
    assert_eq!(response.status(), 500);
    let body = String::from_utf8(bytes(response).await).unwrap();
    assert!(body.contains("사용량을 불러오지 못했습니다."));
    assert!(body.contains("href=\"/sessions-dashboard?refresh=1\""));
    assert!(!body.contains("No usage indexed"));
    assert!(!body.contains("data-usage-refresh="));
}

#[tokio::test]
async fn web_bookmarks_redirect_locally_with_the_original_query() {
    let host = Host::new(false);
    for path in [
        "/sessions",
        "/projects",
        "/sessions/123",
        "/sessions-dashboard",
        "/context",
        "/documents/123",
        "/natural-search",
    ] {
        let query = "source=all&label=%ED%95%9C";
        let response = host
            .request("GET", &format!("{path}/?{query}"), Value::Null)
            .await;
        assert_eq!(response.status(), StatusCode::TEMPORARY_REDIRECT);
        assert_eq!(response.headers()["location"], format!("{path}?{query}"));
    }
    let response = host.request("GET", "/missing/", Value::Null).await;
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
    let desktop = Host::new(true);
    let response = desktop
        .request("GET", "/sessions-dashboard/", Value::Null)
        .await;
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
    for path in ["/context", "/natural-search"] {
        let uri = format!("{path}/?saved=1");
        let response = desktop.request("GET", &uri, Value::Null).await;
        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        let response = desktop
            .router
            .clone()
            .oneshot(
                Request::builder()
                    .uri(uri)
                    .header("host", "127.0.0.1:8123")
                    .header("authorization", "Bearer synthetic-launch-token")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::TEMPORARY_REDIRECT);
        assert_eq!(response.headers()["location"], format!("{path}?saved=1"));
    }
}

#[tokio::test]
async fn checkpoint_saves_unicode_at_its_field_limits() {
    let host = Host::features(false, &["workstreams"]);
    let created = host
        .request(
            "POST",
            "/api/workstreams",
            json!({"name":"Synthetic checkpoint"}),
        )
        .await;
    assert_eq!(created.status(), 200);
    let id = document(created).await["id"].as_i64().unwrap();
    let path = format!("/api/workstreams/{id}/checkpoints");
    let notes = "한".repeat(12_000);
    let mut fields = json!({"current_goal":"한".repeat(4_000),"confirmed_facts":notes,
        "recent_decisions":notes,"open_questions":notes,"next_actions":notes,"files_to_open":notes});
    let saved = host.request("POST", &path, fields.clone()).await;
    assert_eq!(saved.status(), 200);

    fields["confirmed_facts"] = json!("한".repeat(12_001));
    assert_eq!(host.request("POST", &path, fields).await.status(), 422);
    let conn = localbrain_core::backend::db::connect(&host.state.config).unwrap();
    let lengths: (i64, i64, i64) = conn.query_row(
        "SELECT COUNT(*),length(current_goal),length(confirmed_facts) FROM checkpoints WHERE workstream_id=?",
        [id],
        |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?)),
    ).unwrap();
    assert_eq!(lengths, (1, 4_000, 12_000));
}

#[tokio::test]
async fn actual_routes_preserve_aggregated_parameter_errors_and_numeric_coercions() {
    let host = Host::features(false, &["terminal", "workflow"]);
    for method in ["GET", "POST"] {
        let path = if method == "GET" {
            "/sessions/invalid?workspace=bad"
        } else {
            "/sessions/invalid/workflow/corrections"
        };
        let response = host.request(method, path, json!({})).await;
        assert_eq!(response.status(), 422);
        let value = document(response).await;
        assert_eq!(
            value["detail"][0],
            json!({"type":"int_parsing","loc":["path","session_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"invalid"})
        );
        assert_eq!(
            value["detail"].as_array().unwrap().len(),
            if method == "GET" { 2 } else { 1 }
        );
        if method == "GET" {
            assert_eq!(value["detail"][1]["loc"], json!(["query", "workspace"]));
        }
    }
    let response = host
        .request("GET", "/natural-search?page=0&mode=invalid", Value::Null)
        .await;
    assert_eq!(response.status(), 422);
    let value = document(response).await;
    assert_eq!(value["detail"][0]["type"], "greater_than_equal");
    assert_eq!(value["detail"][0]["loc"], json!(["query", "page"]));
    assert_eq!(value["detail"][1]["type"], "string_pattern_mismatch");
    let response = host
        .request("GET", "/api/terminal/settings?launch=bad", Value::Null)
        .await;
    assert_eq!(response.status(), 422);
    assert_eq!(
        document(response).await["detail"][0]["type"],
        "bool_parsing"
    );
    assert_eq!(
        host.request("GET", "/api/terminal/settings?launch=TRUE", Value::Null)
            .await
            .status(),
        200
    );
    assert_eq!(
        host.request("GET", "/sessions/910.0?workspace=1_0.0", Value::Null)
            .await
            .status(),
        404
    );
    assert_eq!(
        host.request("GET", "/sessions/9223372036854775808", Value::Null)
            .await
            .status(),
        500
    );
    assert_eq!(
        host.request("GET", "/sessions/-", Value::Null)
            .await
            .status(),
        422
    );
}

#[tokio::test]
async fn http_methods_match_api_routes_reference_pages_and_websocket_only_paths() {
    let host = Host::features(false, &["terminal"]);
    for path in ["/api/settings", "/sessions/1", "/help"] {
        let response = host.request("HEAD", path, Value::Null).await;
        assert_eq!(response.status(), 405, "{path}");
        assert_eq!(response.headers()["allow"], "GET");
    }
    for path in [
        "/docs",
        "/redoc",
        "/docs/oauth2-redirect",
        "/openapi.json",
        "/static/styles.css",
    ] {
        assert_eq!(
            host.request("HEAD", path, Value::Null).await.status(),
            200,
            "{path}"
        );
    }
    for method in ["GET", "HEAD", "POST"] {
        assert_eq!(
            host.request(method, "/api/terminal/terminals/absent/stream", json!({}))
                .await
                .status(),
            404
        );
    }
}

#[tokio::test]
async fn native_settings_save_readback_conflict_and_headers() {
    let host = Host::new(false);
    let response = host.request("GET", "/api/settings", Value::Null).await;
    assert_eq!(response.status(), 200);
    assert_eq!(response.headers()["cache-control"], "no-store, private");
    let initial = document(response).await;
    assert!(initial["preferences"].is_object());
    assert!(initial["preferences"].get("raw").is_none());
    assert!(initial["preferences"]["effective"]["onboarding_completed"].is_boolean());
    let revision = initial["preferences"]["revision"].clone();
    let response = host
        .request(
            "PATCH",
            "/api/settings/preferences",
            json!({"revision":revision,"changes":{"onboarding_completed":true}}),
        )
        .await;
    assert_eq!(response.status(), 200);
    let saved = document(response).await;
    assert_eq!(saved["effective"]["onboarding_completed"], true);
    assert_ne!(saved["revision"], revision);
    assert_eq!(
        host.request(
            "PATCH",
            "/api/settings/preferences",
            json!({"revision":revision,"changes":{"onboarding_completed":false}})
        )
        .await
        .status(),
        StatusCode::CONFLICT
    );
    assert_eq!(
        document(host.request("GET", "/api/settings", Value::Null).await).await["preferences"]
            ["effective"]["onboarding_completed"],
        true
    );
    let response = host.request("GET", "/settings", Value::Null).await;
    assert_eq!(response.status(), 200);
    let html = String::from_utf8(bytes(response).await).unwrap();
    assert!(html.contains("data-settings"));
    assert!(!html.contains("$serde_json::private::Number"));
}
#[tokio::test]
async fn native_context_registration_reader_order_and_removal() {
    let host = Host::new(false);
    let folder = host.root.path().join("notes");
    std::fs::create_dir(&folder).unwrap();
    std::fs::write(
        folder.join("guide.md"),
        "# Synthetic guide\n\nSafe **content**, <script>never()</script>.\n",
    )
    .unwrap();
    let response = host
        .request("POST", "/api/context-roots", json!({"path":folder}))
        .await;
    assert_eq!(response.status(), 200);
    let result = document(response).await;
    assert_eq!(result["report"]["imported"], 1);
    let id = result["id"].as_i64().unwrap();
    let response = host
        .request("GET", &format!("/context?root={id}"), Value::Null)
        .await;
    assert_eq!(response.status(), 200);
    let html = String::from_utf8(bytes(response).await).unwrap();
    assert!(html.contains("guide.md"));
    assert!(!html.contains("<script>never()</script>"));
    let connection = localbrain_core::backend::db::connect(&host.state.config).unwrap();
    let doc: i64 = connection
        .query_row(
            "SELECT id FROM context_documents WHERE context_root_id=?",
            [id],
            |row| row.get(0),
        )
        .unwrap();
    drop(connection);
    let response = host
        .request(
            "GET",
            &format!("/context?root={id}&document={doc}"),
            Value::Null,
        )
        .await;
    assert_eq!(response.status(), 200);
    let html = String::from_utf8(bytes(response).await).unwrap();
    assert!(html.contains("<strong>content</strong>"));
    assert!(html.contains("&lt;script&gt;never()&lt;/script&gt;"));
    assert!(!html.contains("<script>never()</script>"));
    let response = host
        .request("GET", &format!("/documents/{doc}"), Value::Null)
        .await;
    assert_eq!(response.status(), 200);
    let html = String::from_utf8(bytes(response).await).unwrap();
    assert!(html.contains("<strong>content</strong>"));
    assert!(!html.contains("$serde_json::private::Number"));
    assert_eq!(
        host.request(
            "POST",
            "/api/context-sources/order",
            json!({"source_ids":[id],"expected_source_ids":[id]})
        )
        .await
        .status(),
        200
    );
    assert_eq!(
        host.request(
            "POST",
            "/api/context-sources/order",
            json!({"source_ids":[],"expected_source_ids":[]})
        )
        .await
        .status(),
        409
    );
    assert_eq!(
        host.request("DELETE", &format!("/api/context-roots/{id}"), json!({}))
            .await
            .status(),
        200
    );
    let settings = document(host.request("GET", "/api/settings", Value::Null).await).await;
    assert_eq!(settings["context_sources"], json!([]));

    let file = host.root.path().join("standalone.md");
    std::fs::write(
        &file,
        "# Synthetic file\n\nSafe **content**, <script>never()</script>.\n",
    )
    .unwrap();
    let response = host
        .request("POST", "/api/context-files", json!({"path":file}))
        .await;
    assert_eq!(response.status(), 200);
    let result = document(response).await;
    assert_eq!(result["report"]["imported"], 1);
    let file_source = result["id"].as_i64().unwrap();
    let connection = localbrain_core::backend::db::connect(&host.state.config).unwrap();
    let file_doc: i64 = connection
        .query_row(
            "SELECT id FROM context_documents WHERE context_root_id=?",
            [file_source],
            |row| row.get(0),
        )
        .unwrap();
    drop(connection);
    for path in [
        format!("/context?root={file_source}"),
        format!("/context?root={file_source}&document={file_doc}"),
    ] {
        let response = host.request("GET", &path, Value::Null).await;
        assert_eq!(response.status(), 200);
        let html = String::from_utf8(bytes(response).await).unwrap();
        assert!(html.contains("<strong>content</strong>"), "{path}");
        assert!(
            html.contains("&lt;script&gt;never()&lt;/script&gt;"),
            "{path}"
        );
        assert!(!html.contains("<script>never()</script>"), "{path}");
    }
}
#[tokio::test]
async fn existing_guides_static_bundle_and_empty_learning_render_natively() {
    let host = Host::new(false);
    for path in [
        "/",
        "/learning",
        "/help",
        "/help/settings?lang=en",
        "/settings",
    ] {
        let response = host.request("GET", path, Value::Null).await;
        assert_eq!(
            response.status(),
            200,
            "{path}: {}",
            String::from_utf8_lossy(&bytes(response).await)
        );
    }
    let terminal_host = Host::features(false, &["terminal"]);
    for lang in ["ko", "en"] {
        for slug in [
            "",
            "settings",
            "sessions-dashboard",
            "sessions",
            "local-contexts",
            "search",
            "terminal",
        ] {
            let path = if slug.is_empty() {
                format!("/help?lang={lang}")
            } else {
                format!("/help/{slug}?lang={lang}")
            };
            let response = terminal_host.request("GET", &path, Value::Null).await;
            assert_eq!(response.status(), 200, "{path}");
            let html = String::from_utf8(bytes(response).await).unwrap();
            assert!(html.contains("data-markdown-body"), "{path}");
            assert!(html.contains("id=\"heading-"), "{path}");
            assert!(!html.contains("markdown-render-fallback"), "{path}");
            assert!(!html.contains("LOCALBRAINMARKER"), "{path}");
        }
    }
    let response = host.request("GET", "/static/styles.css", Value::Null).await;
    assert_eq!(response.status(), 200);
    assert!(response.headers()["content-type"]
        .to_str()
        .unwrap()
        .contains("text/css"));
    assert!(!bytes(response).await.is_empty());
    assert_eq!(
        host.request("GET", "/help/missing", Value::Null)
            .await
            .status(),
        404
    );
    assert_eq!(
        host.request("POST", "/learning", json!({})).await.status(),
        405
    );
}
#[tokio::test]
async fn loopback_origin_and_settings_body_boundaries_are_enforced() {
    let host = Host::new(false);
    for (method, origin, hostname, status) in [
        ("GET", "http://outside.invalid", "outside.invalid", 403),
        ("PATCH", "http://outside.invalid", "127.0.0.1:8123", 403),
    ] {
        let response = host
            .router
            .clone()
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri("/api/settings")
                    .header("host", hostname)
                    .header("origin", origin)
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), status);
    }
    let response = host
        .router
        .clone()
        .oneshot(
            Request::builder()
                .method("PATCH")
                .uri("/api/settings/preferences")
                .header("host", "127.0.0.1:8123")
                .body(Body::from("x".repeat(65_537)))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), 413);
    assert_eq!(
        document(response).await["detail"],
        "설정 요청이 너무 큽니다."
    );
    assert_eq!(
        host.request("PATCH", "/api/settings/preferences", json!([]))
            .await
            .status(),
        422
    );
    assert_eq!(
        host.request(
            "POST",
            "/api/settings/choose-path",
            json!({"directory":"yes"})
        )
        .await
        .status(),
        422
    );
    for hostname in [
        "127.1:8123",
        "2130706433:8123",
        "0177.0.0.1:8123",
        "[0:0:0:0:0:0:0:1]:8123",
        "ｌｏｃａｌｈｏｓｔ:8123",
    ] {
        let response = host
            .router
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/api/health")
                    .header("host", hostname)
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), 403, "{hostname}");
    }
}
#[tokio::test]
async fn desktop_launch_token_cookie_precedence_and_feature_boundary() {
    let host = Host::new(true);
    assert_eq!(
        host.request("GET", "/api/health", Value::Null)
            .await
            .status(),
        401
    );
    let response = host
        .request(
            "GET",
            "/desktop/start?token=synthetic-launch-token",
            Value::Null,
        )
        .await;
    assert_eq!(response.status(), 303);
    assert_eq!(response.headers()["location"], "/onboarding");
    let cookie = response.headers()["set-cookie"].to_str().unwrap();
    assert!(cookie.contains("HttpOnly"));
    assert!(cookie.contains("SameSite=Lax"));
    assert_eq!(response.headers()["referrer-policy"], "no-referrer");
    let response = host
        .router
        .clone()
        .oneshot(
            Request::builder()
                .uri("/api/health")
                .header("host", "127.0.0.1:8123")
                .header("cookie", "localbrain-desktop=synthetic-launch-token")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), 200);
    assert_eq!(document(response).await["edition"], "desktop");
    let response = host
        .router
        .clone()
        .oneshot(
            Request::builder()
                .uri("/api/health")
                .header("host", "127.0.0.1:8123")
                .header("cookie", "localbrain-desktop=synthetic-launch-token")
                .header("authorization", "Bearer bad")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), 401);
    for path in [
        "/learning",
        "/sessions/1/workflow",
        "/sessions-dashboard/insights",
        "/runs/a",
    ] {
        assert_eq!(
            host.request("GET", path, Value::Null).await.status(),
            404,
            "{path}"
        );
    }
    let response = host
        .router
        .clone()
        .oneshot(
            Request::builder()
                .uri("/api/health")
                .header("host", "localhost:8123")
                .header("authorization", "Bearer synthetic-launch-token")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), 403);
}
#[tokio::test]
async fn inventory_dashboard_keyword_and_native_session_mutations_render_together() {
    let host = Host::features(false, &["workflow"]);
    let conn = localbrain_core::backend::db::connect(&host.state.config).unwrap();
    conn.execute("INSERT INTO sources(id,provider_kind,name,root_path) VALUES(99,'codex','Synthetic','/synthetic')",[]).unwrap();
    conn.execute("INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count,started_at,ended_at) VALUES(91,99,'synthetic-session-91','/synthetic/91.jsonl','Synthetic session',1,'2026-11-18T00:00:00Z','2026-11-18T00:01:00Z')",[]).unwrap();
    conn.execute("INSERT INTO activity_events(id,session_id,sequence,source_line,event_type,role,text,occurred_at) VALUES('synthetic-message-91',91,0,1,'message','assistant','Synthetic **conversation** <script>no()</script>','2026-11-18T00:00:30Z')",[]).unwrap();
    drop(conn);
    for path in [
        "/sessions",
        "/sessions?display=chart",
        "/projects",
        "/sessions-dashboard",
        "/sessions/91",
        "/natural-search?q=Synthetic",
        "/schema",
        "/schema?area=missing",
    ] {
        let response = host.request("GET", path, Value::Null).await;
        let status = response.status();
        let text = String::from_utf8(bytes(response).await).unwrap();
        assert_eq!(status, 200, "{path}: {text}");
        assert!(!text.contains("$serde_json::private::Number"), "{path}");
    }
    let response = host.request("GET", "/sessions/91", Value::Null).await;
    let html = String::from_utf8(bytes(response).await).unwrap();
    assert!(html.contains("<strong>conversation</strong>"));
    assert!(!html.contains("<script>no()</script>"));
    assert!(html.contains("/sessions/91/workflow"));
    let response = host
        .form(
            "POST",
            "/sessions/91/title",
            "display_title=Personal+title&return_to=%2Fsessions",
        )
        .await;
    assert_eq!(response.status(), 303);
    assert_eq!(response.headers()["location"], "/sessions#session-title-91");
    assert_eq!(
        host.form("POST", "/sessions/91/pin", "return_to=%2Fsessions")
            .await
            .status(),
        303
    );
    let response = host.request("GET", "/sessions", Value::Null).await;
    assert!(String::from_utf8(bytes(response).await)
        .unwrap()
        .contains("Personal title"));
    let visibility = host
        .request(
            "PUT",
            "/sessions/chart/project-visibility",
            json!({"hidden_projects":[]}),
        )
        .await;
    assert_eq!(visibility.status(), 200);
    assert_eq!(document(visibility).await["hidden_projects"], json!([]));
    assert_eq!(
        host.request("GET", "/sessions/91/chart-activity", Value::Null)
            .await
            .status(),
        200
    );
    let response = host.request("GET", "/sessions?page=bad", Value::Null).await;
    assert_eq!(response.status(), 303);
    assert_eq!(response.headers()["location"], "/sessions?page=1");
}
#[tokio::test]
async fn workstream_memberships_reversible_suggestions_and_runner_refusal_are_native() {
    let host = Host::features(false, &["workstreams"]);
    let created = host
        .request(
            "POST",
            "/api/workstreams",
            json!({"name":"Synthetic work","summary":"A bounded fixture"}),
        )
        .await;
    assert_eq!(created.status(), 200);
    let id = document(created).await["id"].as_i64().unwrap();
    assert_eq!(
        host.request("POST", "/api/workstreams", json!({"name":"Synthetic work"}))
            .await
            .status(),
        409
    );
    let thread = host
        .request(
            "POST",
            &format!("/api/workstreams/{id}/threads"),
            json!({"title":"First thread","next_action":"Review"}),
        )
        .await;
    assert_eq!(thread.status(), 200);
    let thread = document(thread).await["id"].as_i64().unwrap();
    assert_eq!(
        host.request(
            "PUT",
            &format!("/api/threads/{thread}"),
            json!({"title":"Updated thread","status":"active"})
        )
        .await
        .status(),
        200
    );
    assert_eq!(
        host.request(
            "POST",
            &format!("/api/workstreams/{id}/checkpoints"),
            json!({"current_goal":"Keep provenance","next_actions":"Review sources"})
        )
        .await
        .status(),
        200
    );
    let resource=host.request("POST","/api/local-resources",json!({"path":"/synthetic/notes","title":"Synthetic resource","scope_type":"workstream","scope_id":id})).await;
    assert_eq!(resource.status(), 200);
    let resource = document(resource).await["id"].as_i64().unwrap();
    for path in [
        "/workstreams".to_owned(),
        format!("/workstreams/{id}"),
        format!("/local-resources/{resource}"),
    ] {
        let response = host.request("GET", &path, Value::Null).await;
        let status = response.status();
        let text = String::from_utf8(bytes(response).await).unwrap();
        assert_eq!(status, 200, "{path}: {text}");
        assert!(text.contains("Synthetic"));
    }
    let response = host
        .request(
            "POST",
            &format!("/api/workstreams/{id}/suggestions"),
            json!({}),
        )
        .await;
    assert_eq!(response.status(), 200);
    assert!(document(response).await["created"].is_number());
    assert_eq!(
        host.request("POST", &format!("/api/workstreams/{id}/runs"), json!({}))
            .await
            .status(),
        503
    );
    assert_eq!(
        host.request("POST", "/api/runs/missing/cancel", json!({}))
            .await
            .status(),
        409
    );
}
#[tokio::test]
async fn terminal_passive_state_settings_and_explicit_origin_boundary() {
    let host = Host::features(false, &["terminal"]);
    let response = host.request("GET", "/api/terminal", Value::Null).await;
    assert_eq!(response.status(), 200);
    let value = document(response).await;
    assert_eq!(value["running"], false);
    assert_eq!(value["tabs"], json!([]));
    assert_eq!(value["workspaces"]["items"], json!([]));
    let saved = document(
        host.request("GET", "/api/terminal/settings", Value::Null)
            .await,
    )
    .await;
    let changed=host.request("POST","/api/terminal/settings",json!({"revision":saved["revision"],"cwd":host.state.config.home_dir,"shell":"/bin/zsh"})).await;
    assert_eq!(changed.status(), 200);
    assert_eq!(
        document(changed).await["cwd"],
        json!(host.state.config.home_dir)
    );
    let response = host
        .router
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/terminal/install")
                .header("host", "127.0.0.1:8123")
                .header("content-type", "application/json")
                .body(Body::from("{}"))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), 403);
    assert_eq!(
        host.request(
            "POST",
            "/api/terminal/stop",
            json!({"expected":{"generation":null,"terminals":[]},"force":"yes"})
        )
        .await
        .status(),
        400
    );
}
#[tokio::test]
async fn passive_auto_work_and_refresh_admission_preserve_feature_gate() {
    let excluded = Host::new(false);
    assert_eq!(
        excluded
            .request("GET", "/auto-work", Value::Null)
            .await
            .status(),
        404
    );
    let host = Host::features(false, &["auto_work"]);
    for path in [
        "/auto-work",
        "/auto-work?mode=sample",
        "/auto-work?mode=sample&page=bad",
    ] {
        let response = host.request("GET", path, Value::Null).await;
        let status = response.status();
        assert_eq!(
            status,
            200,
            "{path}: {}",
            String::from_utf8_lossy(&bytes(response).await)
        );
    }
    assert_eq!(
        host.request("POST", "/auto-work/refresh", json!({}))
            .await
            .status(),
        400
    );
}
#[tokio::test]
async fn suspended_optional_routes_require_explicit_composition_and_reject_before_auth_or_models() {
    let excluded = Host::new(false);
    for path in [
        "/context-search",
        "/api/context-search/status",
        "/api/settings/google-drive",
    ] {
        assert_eq!(
            excluded.request("GET", path, Value::Null).await.status(),
            404
        );
    }
    let host = Host::features(false, &["context_search", "google_drive"]);
    for path in [
        "/context-search",
        "/api/context-search/status",
        "/api/settings/google-drive",
    ] {
        let response = host.request("GET", path, Value::Null).await;
        let status = response.status();
        assert_eq!(
            status,
            200,
            "{path}: {}",
            String::from_utf8_lossy(&bytes(response).await)
        );
    }
    assert_eq!(
        host.request(
            "POST",
            "/api/context-search/answer",
            json!({"model":"invalid","question":"Synthetic only"})
        )
        .await
        .status(),
        422
    );
    assert_eq!(
        host.request("POST", "/api/context-search/unload", json!({}))
            .await
            .status(),
        200
    );
    assert_eq!(
        host.request(
            "POST",
            "/api/settings/google-drive/connections",
            json!({"url":true,"target":"Synthetic"})
        )
        .await
        .status(),
        422
    );
    assert_eq!(
        host.request(
            "POST",
            "/api/settings/google-drive/missing/connect",
            json!({"login":"yes"})
        )
        .await
        .status(),
        422
    );
    assert_eq!(
        host.request(
            "PATCH",
            "/api/settings/google-drive/missing/jobs/receive",
            json!({"unexpected":true})
        )
        .await
        .status(),
        422
    );
}

#[tokio::test]
async fn workflow_correction_http_roundtrip_preserves_optimistic_revision_and_undo() {
    use localbrain_core::backend::{db, search, workflow::focus};
    let host = Host::features(false, &["workflow"]);
    let fixtures: Value = serde_json::from_str(include_str!(
        "../../../crates/core/src/backend/workflow/fixtures/focus-golden.json"
    ))
    .unwrap();
    let conn = db::connect(&host.state.config).unwrap();
    conn.execute_batch("PRAGMA foreign_keys=OFF").unwrap();
    conn.execute_batch(fixtures["cases"][1]["setup_sql"].as_str().unwrap())
        .unwrap();
    conn.execute_batch("PRAGMA foreign_keys=ON").unwrap();
    let initial = focus::workflow_focus_projection(&conn, 11).unwrap();
    let key = initial
        .episodes
        .iter()
        .find(|view| view.episode.session_id == 12)
        .unwrap()
        .episode
        .episode_key
        .clone();
    let revision = initial.assertion_revision.unwrap();
    let form = search::urlencode(&[
        ("action", "close".into()),
        ("source_episode_key", key),
        ("close_reason", "completed".into()),
        ("note", "Synthetic private correction note".into()),
        ("expected_revision", revision),
    ]);
    let response = host
        .form("POST", "/sessions/11/workflow/corrections", &form)
        .await;
    assert_eq!(
        response.status(),
        303,
        "{}",
        String::from_utf8_lossy(&bytes(response).await)
    );
    let response = host
        .router
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/sessions/11/workflow/corrections")
                .header("host", "127.0.0.1:8123")
                .header("origin", "http://127.0.0.1:8123")
                .header("content-type", "application/x-www-form-urlencoded")
                .header("X-LocalBrain-Partial", "workflow-correction")
                .body(Body::from(form))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), 409);
    assert!(response.headers()["vary"]
        .to_str()
        .unwrap()
        .contains("X-LocalBrain-Partial"));
    assert_eq!(
        document(response).await["reload_url"],
        "/sessions/11/workflow"
    );
    let updated = focus::workflow_focus_projection(&conn, 11).unwrap();
    let assertion: i64 = conn
        .query_row(
            "SELECT id FROM workflow_assertions WHERE assertion_kind='close'",
            [],
            |row| row.get(0),
        )
        .unwrap();
    let undo = search::urlencode(&[
        ("action", "undo".into()),
        ("assertion_id", assertion.to_string()),
        ("expected_revision", updated.assertion_revision.unwrap()),
    ]);
    assert_eq!(
        host.form("POST", "/sessions/11/workflow/corrections", &undo)
            .await
            .status(),
        303
    );
    assert_eq!(
        conn.query_row("SELECT COUNT(*) FROM workflow_assertions", [], |row| row
            .get::<_, i64>(0))
            .unwrap(),
        2
    );
    let response = host
        .request("GET", "/sessions/11/workflow", Value::Null)
        .await;
    assert_eq!(response.status(), 200);
    assert!(!String::from_utf8(bytes(response).await)
        .unwrap()
        .contains("Synthetic private correction note"));
    assert_eq!(
        host.form(
            "POST",
            "/sessions/11/workflow/corrections",
            "action=close&action=undo"
        )
        .await
        .status(),
        422
    );
    assert_eq!(
        conn.query_row("SELECT COUNT(*) FROM workflow_assertions", [], |row| row
            .get::<_, i64>(0))
            .unwrap(),
        2
    );
}

#[tokio::test]
async fn insights_native_report_read_download_and_admission_need_no_cli() {
    use localbrain_core::backend::{
        db,
        insights::{
            evidence::{build_insight_evidence_manifest, EvidenceRequest},
            runs,
        },
    };
    let host = Host::new(false);
    let response = host
        .request("GET", "/sessions-dashboard/insights", Value::Null)
        .await;
    assert_eq!(
        response.status(),
        200,
        "{}",
        String::from_utf8_lossy(&bytes(response).await)
    );
    assert_eq!(
        host.request("POST", "/sessions-dashboard/insights/runs", json!({}))
            .await
            .status(),
        415
    );
    let response = host
        .form(
            "POST",
            "/sessions-dashboard/insights/runs",
            "mode=discover&runner=codex",
        )
        .await;
    assert_eq!(response.status(), 200);
    assert!(String::from_utf8(bytes(response).await)
        .unwrap()
        .contains("insight"));
    let conn = db::connect(&host.state.config).unwrap();
    assert_eq!(
        conn.query_row("SELECT COUNT(*) FROM personal_insight_runs", [], |row| row
            .get::<_, i64>(
            0
        ))
        .unwrap(),
        0
    );
    let id = "ins-0123456789abcdef";
    let root = runs::run_root(&host.state.config, id).unwrap();
    std::fs::create_dir_all(&root).unwrap();
    let report = "# Synthetic report\n\nVerified **local** content. <script>no()</script>\n";
    std::fs::write(root.join("report.md"), report).unwrap();
    let manifest = build_insight_evidence_manifest(
        &conn,
        &EvidenceRequest::new("discover", chrono::Utc::now()),
    )
    .unwrap();
    std::fs::write(root.join("evidence.json"), manifest.to_string()).unwrap();
    std::fs::write(root.join("response.json"), "{\"findings\":[]}").unwrap();
    conn.execute("INSERT INTO personal_insight_runs(id,mode,status,runner,model,settings_json,guide_version,evidence_version,evidence_path,prompt_path,response_path,report_path,stream_path,stderr_path,coverage_json,title,created_at,updated_at) VALUES(?,'discover','completed','codex','synthetic','{}','synthetic','synthetic',?,?,?,?,?,?,'{}','Synthetic insight','2026-11-18T00:00:00Z','2026-11-18T00:00:00Z')",rusqlite::params![id,root.join("evidence.json").to_str(),root.join("prompt.txt").to_str(),root.join("response.json").to_str(),root.join("report.md").to_str(),root.join("stream.jsonl").to_str(),root.join("stderr.txt").to_str()]).unwrap();
    conn.execute(
        "UPDATE personal_insight_runs SET coverage_json=? WHERE id=?",
        rusqlite::params![manifest["coverage"].to_string(), id],
    )
    .unwrap();
    let response = host
        .request(
            "GET",
            &format!("/sessions-dashboard/insights?run={id}"),
            Value::Null,
        )
        .await;
    let status = response.status();
    let html = String::from_utf8(bytes(response).await).unwrap();
    assert_eq!(status, 200, "{html}");
    assert!(html.contains("<strong>local</strong>"));
    assert!(!html.contains("<script>no()</script>"));
    let response = host
        .request(
            "GET",
            &format!("/sessions-dashboard/insights/runs/{id}/download"),
            Value::Null,
        )
        .await;
    assert_eq!(response.status(), 200);
    assert!(response.headers()["content-disposition"]
        .to_str()
        .unwrap()
        .contains(id));
    assert_eq!(bytes(response).await, report.as_bytes());
    assert_eq!(
        document(
            host.request("GET", &format!("/api/insight-runs/{id}"), Value::Null)
                .await
        )
        .await["status"],
        "completed"
    );
    assert_eq!(
        host.form(
            "POST",
            &format!("/sessions-dashboard/insights/runs/{id}/cancel"),
            ""
        )
        .await
        .status(),
        409
    );
    assert_eq!(
        host.request("GET", "/api/insight-runs/missing", Value::Null)
            .await
            .status(),
        404
    );
}

#[tokio::test]
async fn atlassian_local_registration_connections_organization_and_refresh_are_native() {
    use localbrain_core::backend::db;
    let host = Host::features(false, &["atlassian", "workstreams"]);
    for path in [
        "/atlassian",
        "/atlassian/add",
        "/atlassian/connections?view=jira",
        "/atlassian/refresh",
        "/search?q=Synthetic",
    ] {
        let response = host.request("GET", path, Value::Null).await;
        let status = response.status();
        assert_eq!(
            status,
            200,
            "{path}: {}",
            String::from_utf8_lossy(&bytes(response).await)
        );
    }
    let response = host
        .form(
            "POST",
            "/atlassian/register",
            "url=https%3A%2F%2Fsynthetic.atlassian.net%2Fbrowse%2FDEV-42&return_to=%2Fatlassian",
        )
        .await;
    assert_eq!(
        response.status(),
        303,
        "{}",
        String::from_utf8_lossy(&bytes(response).await)
    );
    let conn = db::connect(&host.state.config).unwrap();
    let id: i64 = conn
        .query_row(
            "SELECT external_resource_id FROM atlassian_items",
            [],
            |row| row.get(0),
        )
        .unwrap();
    let site: i64 = conn
        .query_row("SELECT id FROM atlassian_sites", [], |row| row.get(0))
        .unwrap();
    let response=host.form("POST",&format!("/atlassian/items/{id}/local"),"note=Synthetic+local+note+%3Cscript%3Eno()%3C%2Fscript%3E&attention=pinned&tags=native%2Creview").await;
    assert_eq!(
        response.status(),
        303,
        "{}",
        String::from_utf8_lossy(&bytes(response).await)
    );
    let response = host
        .request("GET", &format!("/atlassian/items/{id}"), Value::Null)
        .await;
    assert_eq!(response.status(), 200);
    let html = String::from_utf8(bytes(response).await).unwrap();
    assert!(html.contains("Synthetic local note"));
    assert!(!html.contains("<script>no()</script>"));
    let work = document(
        host.request(
            "POST",
            "/api/workstreams",
            json!({"name":"Synthetic Atlassian work"}),
        )
        .await,
    )
    .await["id"]
        .as_i64()
        .unwrap();
    assert_eq!(
        host.form(
            "POST",
            &format!("/atlassian/items/{id}/links"),
            &format!("target=workstream%3A{work}")
        )
        .await
        .status(),
        303
    );
    let link: i64 = conn
        .query_row(
            "SELECT id FROM workstream_links WHERE workstream_id=?",
            [work],
            |row| row.get(0),
        )
        .unwrap();
    assert_eq!(
        host.form(
            "POST",
            &format!("/atlassian/items/{id}/links/workstream/{work}/{link}"),
            ""
        )
        .await
        .status(),
        303
    );
    assert_eq!(
        conn.query_row("SELECT COUNT(*) FROM workstream_links", [], |row| row
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
    let response=host.form("POST","/atlassian/access",&format!("site_id={site}&service=jira&provider_kind=mcp_gateway&config_ref=synthetic-reference")).await;
    assert_eq!(
        response.status(),
        303,
        "{}",
        String::from_utf8_lossy(&bytes(response).await)
    );
    let (binding, source): (i64, i64) = conn
        .query_row(
            "SELECT id,source_instance_id FROM atlassian_site_bindings",
            [],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .unwrap();
    assert_eq!(
        host.form(
            "POST",
            &format!("/atlassian/connections/{source}/sites/{site}"),
            "enabled=1&config_ref=synthetic-reference"
        )
        .await
        .status(),
        303
    );
    let response = host
        .form(
            "POST",
            "/atlassian/spaces/discover",
            &format!("site_id={site}&binding_id={binding}&runner=claude"),
        )
        .await;
    assert_eq!(response.status(), 422);
    assert!(String::from_utf8(bytes(response).await)
        .unwrap()
        .contains("Approved host-side read executor is not connected"));
    let response = host
        .form(
            "POST",
            "/atlassian/refresh",
            &format!("scope=item&scope_id={id}&item_id={id}&runner=claude"),
        )
        .await;
    assert_eq!(response.status(), 422);
    assert_eq!(
        conn.query_row("SELECT COUNT(*) FROM maintenance_runs", [], |row| row
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
    let response=host.request("GET","/api/atlassian/registration-preview?url=https%3A%2F%2Fsynthetic.atlassian.net%2Fbrowse%2FDEV-42",Value::Null).await;
    assert_eq!(response.status(), 200);
    assert_eq!(document(response).await["service"], "jira");
    let response = host
        .request("GET", "/search?q=DEV-42&source=atlassian", Value::Null)
        .await;
    assert_eq!(response.status(), 200);
    assert!(String::from_utf8(bytes(response).await)
        .unwrap()
        .contains("DEV-42"));
}

#[tokio::test]
async fn frozen_api_reference_and_every_conditional_path_match_native_router_admission() {
    let placeholder = regex::Regex::new(r"\{[^}]+\}").unwrap();
    let admission: Value =
        serde_json::from_str(include_str!("../resources/openapi-features.json")).unwrap();
    let all = [
        "atlassian",
        "workstreams",
        "workflow",
        "auto_work",
        "terminal",
        "context_search",
        "google_drive",
    ];
    for selected in [&[][..], &all[..], &all[..5]] {
        let host = Host::features(false, selected);
        let response = host.request("GET", "/openapi.json", Value::Null).await;
        assert_eq!(response.status(), 200);
        let contract = document(response).await;
        assert_eq!(contract["info"]["title"], "LocalBrain");
        assert_eq!(contract["info"]["version"], "0.0.1");
        for (operation, alternatives) in admission.as_object().unwrap() {
            let (method, path) = operation.split_once(' ').unwrap();
            let expected = alternatives.as_array().unwrap().iter().any(|required| {
                required
                    .as_array()
                    .unwrap()
                    .iter()
                    .all(|feature| selected.contains(&feature.as_str().unwrap()))
            });
            assert_eq!(
                contract["paths"][path]
                    .get(method.to_ascii_lowercase())
                    .is_some(),
                expected,
                "{operation} for {selected:?}"
            );
            let path = placeholder.replace_all(path, "1");
            let response = host.request("OPTIONS", &path, Value::Null).await;
            let status = response.status();
            assert_eq!(
                status,
                if expected { 405 } else { 404 },
                "{operation} for {selected:?}: {}",
                String::from_utf8_lossy(&bytes(response).await)
            );
        }
        for path in ["/docs", "/redoc", "/docs/oauth2-redirect"] {
            let response = host.request("GET", path, Value::Null).await;
            assert_eq!(response.status(), 200);
            assert!(response.headers()["content-type"]
                .to_str()
                .unwrap()
                .starts_with("text/html"));
        }
    }
}
