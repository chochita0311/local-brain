//! Native in-process HTTP assertions for the existing Explorer contract; no server/network/CLI.
use axum::{
    body::{to_bytes, Body},
    http::Request,
    response::Response,
    Router,
};
use localbrain_api::{
    routes,
    state::{AppState, FeatureBindings},
};
use localbrain_core::backend::{
    self,
    atlassian::{catalog, ingestion::AtlassianIngestion, structure_references},
    Config,
};
use serde_json::{json, Value};
use std::sync::Arc;
use tower::ServiceExt;
struct Host {
    _root: tempfile::TempDir,
    state: AppState,
    router: Router,
    jira: i64,
    wiki: i64,
    reference: i64,
    site: i64,
    document: i64,
}
impl Host {
    fn new() -> Self {
        let root = tempfile::tempdir_in("/private/tmp").unwrap();
        let mut config = Config::for_data_dir(root.path().join("data"));
        config.claude_bin = Some(root.path().join("missing-claude"));
        config.codex_bin = Some(root.path().join("missing-codex"));
        let config = config.with_features(["atlassian".into()]).unwrap();
        std::fs::create_dir_all(&config.home_dir).unwrap();
        let bindings = FeatureBindings {
            atlassian: Some(Arc::new(AtlassianIngestion::new())),
            ..FeatureBindings::default()
        };
        let state = AppState::initialize(config, "synthetic-token".into(), bindings).unwrap();
        let db = backend::db::connect(&state.config).unwrap();
        let jira=catalog::create_or_reuse_atlassian_stub(&db,&json!({"service":"jira","url":"https://jira.synthetic.test/browse/DEMO-1","title":"Synthetic Jira title","coverage":"reference"})).unwrap();
        let wiki=catalog::create_or_reuse_atlassian_stub(&db,&json!({"service":"confluence","url":"https://wiki.synthetic.test/spaces/TEAM/pages/77/Guide","title":"Synthetic Wiki guide","coverage":"reference"})).unwrap();
        let site = jira["site_id"].as_i64().unwrap();
        let board =
            "https://jira.synthetic.test/secure/RapidBoard.jspa?rapidView=37746&projectKey=JPDI";
        let locator = backend::references::describe_atlassian_url(board);
        let target = structure_references::ensure_structure_reference(
            &db,
            site,
            &locator,
            Some("2026-09-01T00:00:00Z"),
        )
        .unwrap();
        let reference = target["reference_id"].as_i64().unwrap();
        db.execute("INSERT INTO sources(provider_kind,name,root_path)VALUES('context','Synthetic structure','/synthetic/structure')",[]).unwrap();
        let source = db.last_insert_rowid();
        db.execute("INSERT INTO context_roots(path,label)VALUES('/synthetic/structure','Synthetic structure')",[]).unwrap();
        let root_id = db.last_insert_rowid();
        db.execute("INSERT INTO context_documents(source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)VALUES(?,?,'/synthetic/structure/reference.md','reference.md','Synthetic structure',?,?,1,?)",rusqlite::params![source,root_id,board,board.len(),"a".repeat(64)]).unwrap();
        let document = db.last_insert_rowid();
        structure_references::insert_or_reuse_structure_reference_evidence(&db,&json!({"reference_id":reference,"safe_locator_url":locator.safe_locator_url,"container_hint":locator.container_hint,"document_id":document,"source_line":1,"url_ordinal":1,"source_channel":"visible_text","observed_at":"2026-09-01T00:00:00Z"})).unwrap();
        structure_references::project_structure_reference_search(&db, reference).unwrap();
        drop(db);
        let router = routes::router(state.clone());
        Self {
            _root: root,
            state,
            router,
            jira: jira["external_resource_id"].as_i64().unwrap(),
            wiki: wiki["external_resource_id"].as_i64().unwrap(),
            reference,
            site,
            document,
        }
    }
    async fn request(
        &self,
        method: &str,
        path: &str,
        body: Vec<u8>,
        partial: Option<&str>,
        content_type: &str,
    ) -> Response {
        let mut request = Request::builder()
            .method(method)
            .uri(path)
            .header("host", "127.0.0.1:8123")
            .header("origin", "http://127.0.0.1:8123")
            .header("content-type", content_type);
        if let Some(partial) = partial {
            request = request.header("X-LocalBrain-Partial", partial);
        }
        self.router
            .clone()
            .oneshot(request.body(Body::from(body)).unwrap())
            .await
            .unwrap()
    }
    async fn get(&self, path: &str, partial: Option<&str>) -> Response {
        self.request(
            "GET",
            path,
            vec![],
            partial,
            "application/x-www-form-urlencoded",
        )
        .await
    }
}
impl Drop for Host {
    fn drop(&mut self) {
        self.state.services.stop().unwrap();
    }
}
async fn text(response: Response) -> String {
    String::from_utf8(
        to_bytes(response.into_body(), 8 * 1024 * 1024)
            .await
            .unwrap()
            .to_vec(),
    )
    .unwrap()
}
async fn json_body(response: Response) -> Value {
    serde_json::from_str(&text(response).await).unwrap()
}
#[tokio::test]
async fn retained_nonfinite_metadata_survives_explorer_ssr_and_strict_json_still_refuses() {
    let cases = backend::json::decode(include_str!(
        "../../../crates/core/tests/native_atlassian_fixtures/browse-nonfinite.json"
    ))
    .unwrap();
    let host = Host::new();
    for case in cases.as_array().unwrap() {
        let db = backend::db::connect(&host.state.config).unwrap();
        db.execute(
            "INSERT INTO atlassian_item_remote_state(external_resource_id,metadata_json) VALUES(?,?) ON CONFLICT(external_resource_id) DO UPDATE SET metadata_json=excluded.metadata_json",
            rusqlite::params![host.jira, case["metadata_raw"].as_str().unwrap()],
        )
        .unwrap();
        let detail = backend::atlassian::browse::atlassian_item_detail(&db, host.jira)
            .unwrap()
            .unwrap();
        let error = routes::json_response(detail).unwrap_err();
        assert_eq!(error.status, 500);
        assert_eq!(error.code, "json_nonfinite");
        drop(db);
        let selected = format!("/atlassian?view=jira&item={}", host.jira);
        for partial in [None, Some("atlassian-selection-preview")] {
            let response = host.get(&selected, partial).await;
            assert_eq!(response.status(), 200);
            let html = text(response).await;
            assert!(html.contains("not a number"));
            assert!(html.contains("Infinity"));
        }
        let response = host
            .get(&format!("/atlassian/items/{}", host.jira), None)
            .await;
        assert_eq!(response.status(), 200);
        let html = text(response).await;
        assert!(html.contains(case["html_metadata"].as_str().unwrap()), "metadata JSON must match frozen Jinja, including nonfinite numbers, large integers and HTML escaping");
    }
}
#[tokio::test]
async fn default_inventory_owns_query_and_scope_and_legacy_setup_redirects() {
    let host = Host::new();
    let response = host.get("/atlassian", None).await;
    assert_eq!(response.status(), 200);
    assert_eq!(response.headers()["vary"], "X-LocalBrain-Partial");
    let html = text(response).await;
    assert!(html.contains("Synthetic Jira title"));
    assert!(html.contains("Synthetic Wiki guide"));
    assert_eq!(html.matches("type=\"search\"").count(), 1);
    assert!(!html.contains("id=\"global-query\""));
    assert!(html.contains("global-search-reserve"));
    for field in [
        "coverage",
        "freshness",
        "attention",
        "topic_id",
        "tag_id",
        "workstream_id",
    ] {
        assert!(html.contains(&format!("select name=\"{field}\"")));
    }
    let wiki = text(host.get("/atlassian?view=wiki", None).await).await;
    assert!(wiki.contains("Synthetic Wiki guide"));
    assert!(!wiki.contains("Synthetic Jira title"));
    let unknown = text(host.get("/atlassian?view=unknown", None).await).await;
    assert!(unknown.contains("Synthetic Jira title"));
    let response = host
        .get("/atlassian?mode=setup&method=connected&view=wiki", None)
        .await;
    assert_eq!(response.status(), 303);
    assert_eq!(
        response.headers()["location"],
        "/atlassian/connections?view=wiki"
    );
    let response = host
        .get("/atlassian?mode=setup&view=jira&q=DEMO-1", None)
        .await;
    assert_eq!(response.status(), 303);
    assert!(response.headers()["location"]
        .to_str()
        .unwrap()
        .starts_with("/atlassian/add?return_to="));
}
#[tokio::test]
async fn full_and_partial_selection_share_current_evidence_and_partial_avoids_other_rows() {
    let host = Host::new();
    let path = format!("/atlassian?view=jira&item={}", host.jira);
    let full = host.get(&path, None).await;
    assert_eq!(full.status(), 200);
    let html = text(full).await;
    assert!(html.contains("data-preview-state=\"selected\""));
    assert!(html.contains("REMOTE FACTS · LAST KNOWN"));
    assert!(html.contains("LOCAL ONLY"));
    assert!(html.contains("FOUND IN · LOCAL EVIDENCE"));
    assert!(!html.contains("name=\"note\""));
    let db = backend::db::connect(&host.state.config).unwrap();
    assert_eq!(
        db.execute(
            "INSERT INTO atlassian_item_remote_state(external_resource_id,metadata_json) VALUES(?,CAST(x'FF' AS TEXT))",
            [host.wiki],
        )
        .unwrap(),
        1
    );
    drop(db);
    let response = host.get(&path, Some("atlassian-selection-preview")).await;
    assert_eq!(response.status(), 200);
    let html = text(response).await;
    assert!(html.contains("data-preview-state=\"selected\""));
    assert!(!html.contains("atlassian-explorer-layout"));
    let html = text(
        host.get(
            &format!("/atlassian?view=wiki&item={}", host.jira),
            Some("atlassian-item-preview"),
        )
        .await,
    )
    .await;
    assert!(html.contains("data-preview-state=\"out_of_scope\""));
    let html = text(
        host.get(
            "/atlassian?item=9223372036854775807",
            Some("atlassian-item-preview"),
        )
        .await,
    )
    .await;
    assert!(html.contains("data-preview-state=\"missing\""));
}
#[tokio::test]
async fn reference_read_reload_history_and_invalid_state_preserve_local_boundary() {
    let host = Host::new();
    let target = format!(
        "/atlassian?site_id={}&structural_scope=url%3Ajira%3AJPDI&reference={}",
        host.site, host.reference
    );
    let response = host.get(&target, None).await;
    assert_eq!(response.status(), 200);
    let html = text(response).await;
    assert!(html.contains("data-selection-kind=\"reference\""));
    assert!(html.contains(&format!(
        "data-selected-key=\"reference:{}\"",
        host.reference
    )));
    assert!(html.contains("Jira 보드 참조"));
    let html = text(
        host.get(
            &format!("/atlassian?reference={}&coverage=indexed", host.reference),
            None,
        )
        .await,
    )
    .await;
    assert!(html.contains("data-preview-state=\"out_of_scope\""));
    let response = host
        .get(&format!("/atlassian/references/{}", host.reference), None)
        .await;
    assert_eq!(response.status(), 200);
    assert!(text(response).await.contains("LOCAL STRUCTURE ONLY"));
    let db = backend::db::connect(&host.state.config).unwrap();
    db.execute(
        "DELETE FROM atlassian_structure_reference_evidence WHERE document_id=?",
        [host.document],
    )
    .unwrap();
    structure_references::project_structure_reference_search(&db, host.reference).unwrap();
    drop(db);
    let html = text(
        host.get(&format!("/atlassian?reference={}", host.reference), None)
            .await,
    )
    .await;
    assert!(html.contains("data-preview-state=\"archived\""));
    let response = host
        .get(
            "/atlassian/references/999999?return_to=https%3A%2F%2Foutside.invalid%2Fatlassian",
            None,
        )
        .await;
    assert_eq!(response.status(), 404);
    let html = text(response).await;
    assert!(html.contains("이 구조 참조를 찾을 수 없습니다"));
    assert!(!html.contains("outside.invalid"));
    for target in [
        format!("/atlassian?item={}&reference={}", host.jira, host.reference),
        "/atlassian?item=1&item=2".into(),
        "/atlassian?reference=1&reference=2".into(),
        "/atlassian?item=0".into(),
        "/atlassian?reference=９".into(),
    ] {
        assert_eq!(host.get(&target, None).await.status(), 400, "{target}");
    }
}
#[tokio::test]
async fn direct_detail_safe_return_and_explicit_zero_space_stay_navigable() {
    let host = Host::new();
    let db = backend::db::connect(&host.state.config).unwrap();
    let space=catalog::register_atlassian_space(&db,&json!({"site_id":host.site,"service":"jira","name":"Selected Empty Project","space_key":"EMPTY","canonical_url":"https://jira.synthetic.test/projects/EMPTY","observed_at":"2026-09-01T00:00:00Z"})).unwrap();
    drop(db);
    let path = format!(
        "/atlassian?view=jira&site_id={}&space_id={}",
        host.site, space["id"]
    );
    let response = host.get(&path, None).await;
    assert_eq!(response.status(), 200);
    let html = text(response).await;
    assert!(html.contains("data-atlassian-selected-zero-space"));
    assert!(html.contains("remote 링크를 자동으로 발견하거나 동기화하지 않습니다"));
    let response = host
        .get(
            &format!(
                "/atlassian/items/{}?return_to=https%3A%2F%2Foutside.invalid%2Fatlassian",
                host.jira
            ),
            None,
        )
        .await;
    assert_eq!(response.status(), 200);
    let html = text(response).await;
    assert!(html.contains("name=\"note\""));
    assert!(!html.contains("outside.invalid"));
    assert_eq!(
        host.get("/atlassian/items/999999", None).await.status(),
        404
    );
}
#[tokio::test]
async fn explicit_sync_has_strict_bounded_form_enhancement_and_query_bound_receipt() {
    let host = Host::new();
    for (body, ctype, message) in [
        (
            b"{}".to_vec(),
            "application/json",
            "Form encoding is unsupported",
        ),
        (
            b"return_to=%FF".to_vec(),
            "application/x-www-form-urlencoded",
            "Form data is invalid",
        ),
        (
            b"return_to=a&return_to=b".to_vec(),
            "application/x-www-form-urlencoded",
            "Sync requires exactly one return_to field",
        ),
        (
            b"a=1&b=2&c=3".to_vec(),
            "application/x-www-form-urlencoded",
            "Form data is invalid",
        ),
        (
            vec![b'x'; 8193],
            "application/x-www-form-urlencoded",
            "Form is too large",
        ),
        (
            format!("return_to={}", "x".repeat(4001)).into_bytes(),
            "application/x-www-form-urlencoded",
            "return_to is too large",
        ),
    ] {
        let response = host
            .request(
                "POST",
                "/atlassian/sync",
                body,
                Some("atlassian-local-evidence-sync"),
                ctype,
            )
            .await;
        assert_eq!(response.status(), 422);
        assert_eq!(response.headers()["vary"], "X-LocalBrain-Partial");
        let value = json_body(response).await;
        assert_eq!(value["detail"]["code"], "invalid-form");
        assert_eq!(value["detail"]["message"], message);
    }
    let response = host
        .request(
            "POST",
            "/atlassian/sync",
            b"return_to=%2Fatlassian%3Fview%3Dall".to_vec(),
            Some("atlassian-local-evidence-sync"),
            "application/x-www-form-urlencoded",
        )
        .await;
    assert_eq!(response.status(), 200);
    let value = json_body(response).await;
    assert!(value["report"].is_object());
    assert_eq!(value["return_to"], "/atlassian?view=all");
    let response = host
        .request(
            "POST",
            "/atlassian/sync",
            b"return_to=%2Fatlassian".to_vec(),
            None,
            "application/x-www-form-urlencoded",
        )
        .await;
    assert_eq!(response.status(), 303);
    let location = response.headers()["location"].to_str().unwrap().to_owned();
    assert!(location.starts_with("/atlassian?view=all&sync_receipt="));
    assert!(location.ends_with("#atlassian-sync-result"));
    let response = host.get(location.split('#').next().unwrap(), None).await;
    assert_eq!(response.status(), 200);
    assert!(text(response).await.contains("atlassian-sync-result"));
}
#[tokio::test]
async fn typed_http_integer_admission_stays_distinct_from_domain_and_selection_ids() {
    let host = Host::new();
    let response = host
        .get(&format!("/atlassian?site_id={}.0", host.site), None)
        .await;
    assert_eq!(response.status(), 200);
    for target in [
        "/atlassian?site_id=%EF%BC%93",
        "/atlassian?site_id=%2B0",
        "/atlassian?site_id=-1",
        "/atlassian?site_id=1__0",
        "/atlassian?topic_id=3.1",
    ] {
        assert_eq!(host.get(target, None).await.status(), 422, "{target}");
    }
    assert_eq!(
        host.get("/atlassian?site_id=9223372036854775808", None)
            .await
            .status(),
        400
    );
    assert_eq!(
        host.get("/atlassian/items/9223372036854775808", None)
            .await
            .status(),
        404
    );
    assert_eq!(
        host.get(&format!("/atlassian/items/{}.0", host.jira), None)
            .await
            .status(),
        200
    );
}
