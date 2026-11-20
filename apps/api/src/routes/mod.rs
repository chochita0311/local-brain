use crate::{
    boundary::{self, Boundary},
    state::AppState,
    transport::{self, ApiError, RequestContext},
};
use axum::{
    body::Body,
    extract::{Path, Request, State},
    http::{header, StatusCode, Uri},
    middleware,
    response::{IntoResponse, Response},
    routing::{get, on, MethodFilter},
    Json, Router,
};
use localbrain_core::backend::{BackendError, Result};
use serde_json::{json, Value};
use std::collections::BTreeMap;
use tower::ServiceExt;

mod api_reference;
pub(crate) mod atlassian;
mod auto_work;
mod context_search;
mod documents;
mod google_drive;
mod guides;
mod insights;
mod learning;
mod payload;
mod schema;
mod search;
mod sessions;
mod settings;
mod sources;
mod terminal;
mod usage;
mod workflow;
mod workstreams;
pub type Params = BTreeMap<String, String>;
pub type Handler = fn(&AppState, &RequestContext, &Params, &[u8]) -> Result<Response>;
#[derive(Clone, Copy)]
pub struct BodyLimit {
    pub status: u16,
    pub bytes: usize,
    pub message: &'static str,
}
pub const EMPTY: BodyLimit = BodyLimit {
    status: 413,
    bytes: 0,
    message: "Request body is not accepted",
};
pub const SETTINGS: BodyLimit = BodyLimit {
    status: 413,
    bytes: 65_536,
    message: "설정 요청이 너무 큽니다.",
};
pub const FORM: BodyLimit = BodyLimit {
    status: 413,
    bytes: 160 * 1024,
    message: "Form is too large",
};
pub const LEARNING_FORM: BodyLimit = BodyLimit {
    status: 413,
    bytes: 100_000,
    message: "Form is too large",
};
pub fn identifier(params: &Params, key: &str) -> Result<i64> {
    let invalid = || BackendError::new(422, "path", format!("Invalid path parameter: {key}"));
    let value = params.get(key).ok_or_else(invalid)?;
    let digits = value.strip_prefix('-').unwrap_or(value);
    value.parse().map_err(|_| {
        if !digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit()) {
            BackendError::new(500, "database", "Integer exceeds the database range")
        } else {
            invalid()
        }
    })
}
pub fn json_response(value: Value) -> Result<Response> {
    localbrain_core::backend::json::validate_http_json(&value)?;
    Ok(Json(value).into_response())
}
pub fn bind(
    router: Router<AppState>,
    path: &'static str,
    method: MethodFilter,
    handler: Handler,
    limit: BodyLimit,
) -> Router<AppState> {
    router.route(
        path,
        on(
            method,
            move |State(state): State<AppState>,
                  Path(mut params): Path<Params>,
                  request: Request| async move {
                if request.method() == axum::http::Method::HEAD
                    && method.or(MethodFilter::HEAD) != method
                {
                    let mut response =
                        ApiError(BackendError::new(405, "method", "Method Not Allowed"))
                            .into_response();
                    response
                        .headers_mut()
                        .insert("allow", "GET".parse().unwrap());
                    return response;
                }
                let mut context = match RequestContext::new(
                    request.method().clone(),
                    request.headers().clone(),
                    request.uri().clone(),
                ) {
                    Ok(value) => value,
                    Err(error) => return ApiError(error).into_response(),
                };
                let request_method = context.method.as_str().to_owned();
                if let Err(error) =
                    crate::parameters::validate(path, &request_method, &mut context, &mut params)
                {
                    return ApiError(error).into_response();
                }
                let bytes = match transport::bounded_body(request.into_body(), limit.bytes).await {
                    Ok(bytes) => bytes,
                    Err(_) => return transport::error(limit.status, limit.message).into_response(),
                };
                match state
                    .blocking(move |state| handler(&state, &context, &params, &bytes))
                    .await
                {
                    Ok(response) => response,
                    Err(error) => error.into_response(),
                }
            },
        ),
    )
}
async fn static_asset(State(state): State<AppState>, request: Request) -> Response {
    let suffix = transport::decode_path(request.uri().path())
        .strip_prefix("/static/")
        .unwrap_or("")
        .to_owned();
    let config = state.config.clone();
    let candidate = tokio::task::spawn_blocking(move || -> Result<_> {
        let root = std::fs::canonicalize(config.web_root.join("static"))?;
        let candidate = std::fs::canonicalize(root.join(suffix))
            .map_err(|_| BackendError::not_found("Not Found"))?;
        if !candidate.starts_with(root) || !candidate.is_file() {
            return Err(BackendError::not_found("Not Found"));
        }
        Ok(candidate)
    })
    .await;
    let path = match candidate {
        Ok(Ok(path)) => path,
        Ok(Err(error)) => return ApiError(error).into_response(),
        Err(_) => {
            return ApiError(BackendError::unavailable("Static asset read interrupted"))
                .into_response()
        }
    };
    match tower_http::services::ServeFile::new(path)
        .oneshot(request)
        .await
    {
        Ok(response) => response.map(Body::new),
        Err(error) => match error {},
    }
}
fn health(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    json_response(json!({"status":"ok","edition":if state.config.desktop{"desktop"}else{"web"}}))
}
fn desktop_shutdown(
    state: &AppState,
    _: &RequestContext,
    _: &Params,
    _: &[u8],
) -> Result<Response> {
    state.shutdown.request();
    json_response(json!({"ok":true}))
}

async fn bookmark_redirect(uri: Uri) -> impl IntoResponse {
    let mut target = uri.path().trim_end_matches('/').to_owned();
    if let Some(query) = uri.query() {
        target.push('?');
        target.push_str(query);
    }
    (StatusCode::TEMPORARY_REDIRECT, [(header::LOCATION, target)])
}

pub fn router(state: AppState) -> Router {
    let mut router = Router::new().route("/static/{*path}", axum::routing::get(static_asset));
    router = bind(router, "/api/health", MethodFilter::GET, health, EMPTY);
    if state.config.desktop {
        router = bind(
            router,
            "/desktop/shutdown",
            MethodFilter::POST,
            desktop_shutdown,
            SETTINGS,
        );
    }
    router = settings::install(router);
    router = documents::install(router);
    router = guides::install(router);
    router = sessions::install(router);
    router = search::install(router, state.config.desktop);
    router = usage::install(router);
    router = sources::install(router, state.config.desktop);
    if state.config.feature("terminal") {
        router = terminal::install(router);
    }
    if !state.config.desktop {
        router = workstreams::install(
            router,
            state.config.feature("workstreams"),
            state.config.feature("workstreams") || state.config.feature("atlassian"),
        );
    }
    if !state.config.desktop {
        router = schema::install(router);
    }
    if state.config.feature("auto_work") {
        router = auto_work::install(router);
    }
    if state.config.feature("context_search") {
        router = context_search::install(router);
    }
    if state.config.feature("google_drive") {
        router = google_drive::install(router);
    }
    if state.config.feature("workflow") {
        router = workflow::install(router);
    }
    if state.config.feature("atlassian") {
        router = atlassian::install(router, state.config.feature("workstreams"));
        if !state.config.desktop {
            router = search::install_legacy(router);
        }
    }
    for path in ["/context/", "/natural-search/"] {
        router = router.route(path, get(bookmark_redirect));
    }
    if !state.config.desktop {
        router = learning::install(router);
        router = insights::install(router);
        router = api_reference::install(router);
        for path in [
            "/sessions/",
            "/projects/",
            "/sessions/{session_id}/",
            "/sessions-dashboard/",
            "/documents/{document_id}/",
        ] {
            router = router.route(path, get(bookmark_redirect));
        }
    }
    router
        .fallback(|| async {
            ApiError(BackendError::new(404, "route", "Not Found")).into_response()
        })
        .method_not_allowed_fallback(|| async {
            (
                StatusCode::METHOD_NOT_ALLOWED,
                Json(json!({"detail":"Method Not Allowed"})),
            )
        })
        .with_state(state.clone())
        .layer(middleware::from_fn_with_state(
            Boundary {
                config: state.config.clone(),
                token: state.token.clone(),
            },
            boundary::middleware,
        ))
}
