use super::{bind, json_response, Params, EMPTY, SETTINGS};
use crate::{
    state::{database, AppState},
    transport::{self, RequestContext},
};
use axum::{
    body::Body,
    extract::State,
    response::{IntoResponse, Response},
    routing::{post, MethodFilter},
    Router,
};
use localbrain_core::backend::{ingest, search, sessions::dashboard, BackendError, Result};
use serde_json::json;
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let sources = database(&state.config, false, dashboard::source_inventory)?;
    let outcome = request.parameter("sync");
    state.render(request,"sources.html",json!({"active_page":"sources","sources":sources,"database_path":state.config.database_path,"sync_outcome":(["complete","partial","failed"].contains(&outcome).then_some(outcome))}),200)
}
fn all(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let report = ingest::scan_all(
        &state.config,
        false,
        &state.scan_control(),
        state.services.observer.as_ref(),
    )?;
    if request.path == "/sources/scan" {
        let outcome = report["outcome"]
            .as_str()
            .filter(|outcome| ["complete", "partial", "failed"].contains(outcome))
            .unwrap_or("failed");
        Ok(transport::redirect(&format!(
            "/sources?{}",
            search::urlencode(&[("sync", outcome.into())])
        )))
    } else {
        json_response(json!({"ok":true,"report":report}))
    }
}
fn request_sync(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    json_response(json!({"ok":true,"state":state.services.session_sync.request_sync()?}))
}
fn status(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    json_response(state.services.session_sync.status()?)
}
fn sync_page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let page = request.integer("page", 1)?;
    if page < 1 {
        return Err(BackendError::new(422, "query", "Invalid page"));
    }
    let workspace = request
        .query
        .get("workspace")
        .map(|_| request.integer("workspace", 0))
        .transpose()?;
    state.services.session_sync.request_sync()?;
    let mut pairs = vec![
        (
            "source",
            request
                .query
                .get("source")
                .cloned()
                .unwrap_or_else(|| "all".into()),
        ),
        (
            "display",
            request
                .query
                .get("display")
                .cloned()
                .unwrap_or_else(|| "list".into()),
        ),
        ("page", page.to_string()),
    ];
    if let Some(workspace) = workspace {
        pairs.push(("workspace", workspace.to_string()));
    }
    Ok(transport::redirect(&format!(
        "{}?{}",
        if request.parameter("view") == "projects" {
            "/projects"
        } else {
            "/sessions"
        },
        search::urlencode(&pairs)
    )))
}
async fn stream(State(state): State<AppState>) -> Response {
    let sync = state.services.session_sync.clone();
    let start = state.blocking(move |_| sync.request_sync()).await;
    if let Err(error) = start {
        return error.into_response();
    }
    let service = state.services.session_sync.clone();
    let shutdown = state.shutdown.clone();
    let stream = futures_util::stream::try_unfold(
        Some((service, shutdown, false)),
        |next| async move {
            let Some((service, shutdown, wait)) = next else {
                return Ok::<_, std::io::Error>(None);
            };
            let mut wait = wait;
            loop {
                if shutdown.is_requested() {
                    return Ok(None);
                }
                if wait {
                    tokio::select! {_=shutdown.wait()=>return Ok(None),_=tokio::time::sleep(std::time::Duration::from_secs(1))=>{}}
                }
                wait = true;
                let snapshot = service.clone();
                let value = tokio::task::spawn_blocking(move || snapshot.status())
                    .await
                    .map_err(std::io::Error::other)?
                    .map_err(std::io::Error::other)?;
                if value["running"] != true && value["queued"] != true {
                    let output = json!({"type":"result","ok":value["error"].is_null()||value["error"]=="","report":value.get("report").cloned().unwrap_or_else(||json!({})),"state":value});
                    let output =
                        serde_json::to_string(&output).map_err(std::io::Error::other)? + "\n";
                    return Ok(Some((output, None)));
                }
                if value["progress"].is_object() {
                    let output = serde_json::to_string(&value["progress"])
                        .map_err(std::io::Error::other)?
                        + "\n";
                    return Ok(Some((output, Some((service, shutdown, true)))));
                }
            }
        },
    );
    let mut response = Body::from_stream(stream).into_response();
    response
        .headers_mut()
        .insert("content-type", "application/x-ndjson".parse().unwrap());
    response
}
pub fn install(mut router: Router<AppState>, desktop: bool) -> Router<AppState> {
    router = bind(
        router,
        "/sessions/sync",
        MethodFilter::POST,
        sync_page,
        SETTINGS,
    );
    router = bind(
        router,
        "/api/sessions/sync",
        MethodFilter::POST,
        request_sync,
        SETTINGS,
    );
    router = bind(
        router,
        "/api/sessions/sync/status",
        MethodFilter::GET,
        status,
        EMPTY,
    );
    router = router.route("/api/sessions/sync/stream", post(stream));
    if !desktop {
        router = bind(router, "/sources", MethodFilter::GET, page, EMPTY);
        for path in ["/sources/scan", "/api/scan"] {
            router = bind(router, path, MethodFilter::POST, all, SETTINGS);
        }
    }
    router
}
