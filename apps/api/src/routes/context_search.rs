use super::{bind, json_response, Params, EMPTY, SETTINGS};
use crate::{
    state::AppState,
    transport::{self, RequestContext},
};
use axum::{
    body::Body,
    extract::{Request, State},
    response::{IntoResponse, Response},
    routing::{post, MethodFilter},
    Router,
};
use localbrain_core::backend::{
    context_search::{ContextSearchJob, ContextSearchService},
    rendering::{render_markdown, MarkdownOptions},
    BackendError, Result,
};
use serde_json::json;
use std::{
    sync::{atomic::Ordering, Arc},
    time::Duration,
};
fn service(state: &AppState) -> Result<Arc<ContextSearchService>> {
    state
        .services
        .context_search
        .clone()
        .ok_or_else(|| BackendError::unavailable("Context Search is unavailable"))
}
fn unavailable(error: BackendError) -> BackendError {
    if ["io", "database"].contains(&error.code.as_str()) {
        BackendError::unavailable("자료 목록을 읽지 못했습니다. 연결 상태를 확인해 주세요.")
    } else {
        error
    }
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    state.render(
        request,
        "context-search.html",
        json!({"active_page":"context-search"}),
        200,
    )
}
fn status(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    json_response(service(state)?.status().map_err(unavailable)?)
}
fn unload(state: &AppState, _: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    service(state)?.unload_idle();
    json_response(json!({"ok":true}))
}
struct ResponseJob {
    service: Arc<ContextSearchService>,
    job: Arc<ContextSearchJob>,
}
impl Drop for ResponseJob {
    fn drop(&mut self) {
        if !self.job.completed() {
            self.job.canceled.store(true, Ordering::Release);
        }
        let service = self.service.clone();
        let job = self.job.clone();
        if let Ok(runtime) = tokio::runtime::Handle::try_current() {
            runtime.spawn_blocking(move || service.release(&job));
        } else {
            let owned_service = service.clone();
            let owned_job = job.clone();
            if localbrain_core::backend::worker_thread("context-release")
                .spawn(move || owned_service.release(&owned_job))
                .is_err()
            {
                service.release(&job);
            }
        }
    }
}
async fn answer(State(state): State<AppState>, request: Request) -> Response {
    if request
        .headers()
        .get("content-type")
        .and_then(|value| value.to_str().ok())
        .unwrap_or("")
        .split(';')
        .next()
        != Some("application/json")
    {
        return transport::error(415, "질문 요청 형식을 확인해 주세요.").into_response();
    }
    let bytes = match transport::bounded_body(request.into_body(), 120_000).await {
        Ok(bytes) => bytes,
        Err(_) => {
            return transport::error(413, "질문과 대화를 줄여 다시 시도해 주세요.").into_response()
        }
    };
    let value = match transport::json_object(&bytes, 422, "모델과 질문을 확인해 주세요.")
    {
        Ok(value) => value,
        Err(error) => return error.into_response(),
    };
    let started = state
        .blocking(move |state| {
            let service = service(&state)?;
            let job = service.begin(&value).map_err(unavailable)?;
            Ok(ResponseJob { service, job })
        })
        .await;
    let job = match started {
        Ok(job) => job,
        Err(error) => return error.into_response(),
    };
    let shutdown = state.shutdown.clone();
    let stream = futures_util::stream::try_unfold(
        (job, false, shutdown),
        |(owner, finished, shutdown)| async move {
            if finished {
                return Ok::<_, std::io::Error>(None);
            }
            loop {
                if owner.job.canceled.load(Ordering::Acquire) || shutdown.is_requested() {
                    return Ok(None);
                }
                let job = owner.job.clone();
                let event = tokio::task::spawn_blocking(move || -> std::io::Result<_> {
                    let Some(mut event) = job.next_event(Duration::from_millis(250)) else {
                        return Ok(None);
                    };
                    if event["type"] == "answer" {
                        event["html"] = json!(
                            render_markdown(
                                event["text"].as_str().unwrap_or(""),
                                &MarkdownOptions::default()
                            )
                            .html
                        );
                    }
                    let finished = event["type"]
                        .as_str()
                        .is_some_and(|kind| ["answer", "error"].contains(&kind));
                    let mut line = localbrain_core::backend::json::encode_http(&event)
                        .map_err(|_| std::io::Error::other("Invalid context stream event"))?;
                    line.push('\n');
                    Ok(Some((line, finished)))
                })
                .await
                .map_err(|_| std::io::Error::other("Context stream interrupted"))??;
                if let Some((line, finished)) = event {
                    return Ok(Some((line, (owner, finished, shutdown))));
                }
                if owner.job.completed() {
                    return Ok(None);
                }
            }
        },
    );
    let mut response = Body::from_stream(stream).into_response();
    response
        .headers_mut()
        .insert("content-type", "application/x-ndjson".parse().unwrap());
    response
        .headers_mut()
        .insert("cache-control", "no-store, private".parse().unwrap());
    response
        .headers_mut()
        .insert("x-accel-buffering", "no".parse().unwrap());
    response
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for (path, handler) in [
        ("/context-search", page as super::Handler),
        ("/api/context-search/status", status),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    router = bind(
        router,
        "/api/context-search/unload",
        MethodFilter::POST,
        unload,
        SETTINGS,
    );
    router.route("/api/context-search/answer", post(answer))
}
