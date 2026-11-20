use super::{bind, BodyLimit, Params, EMPTY};
use crate::{
    state::{database, immediate, AppState},
    transport::{self, ApiError, RequestContext},
};
use axum::{
    body::Body,
    extract::{Path, Request, State},
    response::{IntoResponse, Response},
    routing::{get, MethodFilter},
    Router,
};
use localbrain_core::backend::{
    db,
    insights::{
        presentation::{self, PageRequest},
        runs::{self, PrepareRequest},
    },
    unicode, BackendError, Result,
};
use tower::ServiceExt;
fn guard(request: &RequestContext) -> Result<()> {
    if request
        .header("sec-fetch-site")
        .eq_ignore_ascii_case("cross-site")
    {
        return Err(BackendError::new(400, "local", "Local access required"));
    }
    Ok(())
}
fn page_response(
    state: &AppState,
    request: &RequestContext,
    selection: PageRequest,
) -> Result<Response> {
    let choices = runs::runner_choices(&state.config)?;
    let context = database(&state.config, false, |conn| {
        presentation::page_data(conn, &state.config, &selection, &choices)
    })?;
    state.render(request, "session_insights.html", context, 200)
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    guard(request)?;
    page_response(
        state,
        request,
        PageRequest {
            selected_id: request.query.get("run").filter(|s| !s.is_empty()).cloned(),
            before: request.query.get("before").cloned(),
            ..Default::default()
        },
    )
}
fn redirect(id: &str) -> Response {
    transport::redirect(&format!(
        "/sessions-dashboard/insights?run={id}#session-insights-run-detail"
    ))
}
fn create(state: &AppState, request: &RequestContext, _: &Params, body: &[u8]) -> Result<Response> {
    guard(request)?;
    if !request.header("origin").is_empty() && request.header("origin") != request.origin {
        return Err(BackendError::new(
            400,
            "origin",
            "Same-origin submission required",
        ));
    }
    if request
        .header("content-type")
        .split(';')
        .next()
        .unwrap_or("")
        != "application/x-www-form-urlencoded"
    {
        return Err(BackendError::new(415, "form", "Form submission required"));
    }
    let text = std::str::from_utf8(body)
        .map_err(|_| BackendError::new(400, "form", "Invalid form encoding"))?;
    let mut fields = std::collections::BTreeMap::new();
    for (key, value) in url::form_urlencoded::parse(text.as_bytes()) {
        fields
            .entry(key.into_owned())
            .or_insert_with(|| value.into_owned());
    }
    let field = |key: &str| fields.get(key).map(String::as_str).unwrap_or("");
    let question = field("question")
        .trim_matches(unicode::python_space)
        .to_owned();
    let choices = runs::runner_choices(&state.config)?;
    let result = immediate(&state.config, |conn| {
        if db::row(
            conn,
            "SELECT id FROM personal_insight_runs WHERE status IN ('queued','running') LIMIT 1",
            [],
        )?
        .is_some()
        {
            return Err(BackendError::new(
                422,
                "active-run",
                "이미 분석이 실행 중입니다. 완료하거나 중지한 뒤 새로 시작해 주세요.",
            ));
        }
        runs::prepare_insight_run(
            conn,
            &state.config,
            &PrepareRequest {
                mode: field("mode").into(),
                question: if field("mode") == "ask" {
                    Some(question.clone())
                } else {
                    None
                },
                runner: field("runner").into(),
            },
            &choices,
            chrono::Utc::now(),
        )
    });
    match result {
        Ok(id) => {
            state
                .services
                .insights
                .as_ref()
                .ok_or_else(|| BackendError::unavailable("Insight runtime unavailable"))?
                .start(&id)?;
            Ok(redirect(&id))
        }
        Err(error) if error.status < 500 => page_response(
            state,
            request,
            PageRequest {
                error: Some(error.message),
                question,
                ..Default::default()
            },
        ),
        Err(error) => Err(error),
    }
}
fn cancel(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    guard(request)?;
    if !request.header("origin").is_empty() && request.header("origin") != request.origin {
        return Err(BackendError::new(
            400,
            "origin",
            "Same-origin submission required",
        ));
    }
    let id = &params["run_id"];
    let cancelled = database(&state.config, true, |conn| {
        state
            .services
            .insights
            .as_ref()
            .ok_or_else(|| BackendError::unavailable("Insight runtime unavailable"))?
            .cancel(conn, id)
    })?;
    if !cancelled {
        return Err(BackendError::conflict(
            "중지할 수 있는 분석 실행이 아닙니다.",
        ));
    }
    Ok(redirect(id))
}
fn status(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    guard(request)?;
    let run = database(&state.config, false, |conn| {
        runs::get_insight_run(conn, &params["run_id"])
    })?
    .ok_or_else(|| BackendError::not_found("Analysis Run not found"))?;
    super::json_response(presentation::run_status(&run))
}
async fn download(
    State(state): State<AppState>,
    Path(id): Path<String>,
    request: Request,
) -> Response {
    let context = match RequestContext::new(
        request.method().clone(),
        request.headers().clone(),
        request.uri().clone(),
    ) {
        Ok(context) => context,
        Err(error) => return ApiError(error).into_response(),
    };
    let lookup = id.clone();
    let path = match state
        .blocking(move |state| {
            guard(&context)?;
            let run = database(&state.config, false, |conn| {
                runs::get_insight_run(conn, &lookup)
            })?
            .ok_or_else(|| BackendError::not_found("Report not found"))?;
            presentation::download_report_path(&state.config, &run)
        })
        .await
    {
        Ok(path) => path,
        Err(error) => return error.into_response(),
    };
    let mut response = match tower_http::services::ServeFile::new(path)
        .oneshot(request)
        .await
    {
        Ok(response) => response.map(Body::new),
        Err(error) => match error {},
    };
    response.headers_mut().insert(
        "content-type",
        "text/markdown; charset=utf-8".parse().unwrap(),
    );
    response.headers_mut().insert(
        "content-disposition",
        format!("attachment; filename=\"localbrain-insight-{id}.md\"")
            .parse()
            .unwrap(),
    );
    response
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for (path, handler) in [
        ("/sessions-dashboard/insights", page as super::Handler),
        ("/api/insight-runs/{run_id}", status),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    router = bind(
        router,
        "/sessions-dashboard/insights/runs",
        MethodFilter::POST,
        create,
        BodyLimit {
            status: 413,
            bytes: 8192,
            message: "Form is too large",
        },
    );
    router = bind(
        router,
        "/sessions-dashboard/insights/runs/{run_id}/cancel",
        MethodFilter::POST,
        cancel,
        BodyLimit {
            status: 413,
            bytes: 8192,
            message: "Form is too large",
        },
    );
    router.route(
        "/sessions-dashboard/insights/runs/{run_id}/download",
        get(download),
    )
}
