use super::{bind, identifier, Params, EMPTY};
use crate::{
    state::{database, AppState},
    transport::{self, ApiError, RequestContext},
};
use axum::{
    extract::{Path, Request, State},
    response::{IntoResponse, Response},
    routing::{post, MethodFilter},
    Router,
};
use localbrain_core::backend::{
    workflow::{
        assertions,
        correction::{self, MAX_WORKFLOW_CORRECTION_FORM_BYTES, WORKFLOW_CORRECTION_PARTIAL},
        correction_view, focus, map,
    },
    Result,
};
use serde_json::{json, Value};
use std::sync::OnceLock;
const CONFLICTS: &[&str] = &[
    "conflict",
    "duplicate-active",
    "assertion-not-active",
    "assertion-not-found",
    "requires-active-closure",
    "not-tip",
    "missing-endpoint",
    "cycle",
    "contradictory-boundary",
];
fn messages() -> &'static Value {
    static MESSAGES: OnceLock<Value> = OnceLock::new();
    MESSAGES.get_or_init(|| {
        serde_json::from_str(include_str!("../../resources/workflow-messages.json"))
            .expect("compiled workflow feedback")
    })
}
fn vary(mut response: Response) -> Response {
    let current = response
        .headers()
        .get("vary")
        .and_then(|value| value.to_str().ok())
        .unwrap_or("");
    let mut values = current
        .split(',')
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_owned)
        .collect::<Vec<_>>();
    if !values.iter().any(|value| value == "X-LocalBrain-Partial") {
        values.push("X-LocalBrain-Partial".into());
    }
    if let Ok(value) = values.join(", ").parse() {
        response.headers_mut().insert("vary", value);
    }
    response
}
fn page_response(
    state: &AppState,
    request: &RequestContext,
    id: i64,
    feedback: Value,
    preferred: Option<u16>,
) -> Result<Response> {
    let result = database(&state.config, false, |conn| {
        map::workflow_map_view(&focus::workflow_focus_projection(conn, id)?, id)
    });
    let (workflow, status) = match result {
        Ok(workflow) => {
            let status = match workflow["status"].as_str() {
                Some("ready") => preferred.unwrap_or(200),
                Some("missing") => 404,
                Some("ineligible") => 422,
                _ => 500,
            };
            (workflow, status)
        }
        Err(_) => (map::workflow_map_state_view("unexpected-error", id)?, 500),
    };
    state.render(request,"session-workflow.html",json!({"active_page":"sessions","workflow":workflow,"workflow_correction_feedback":feedback}),status)
}
fn page(state: &AppState, request: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let feedback = match request.parameter("workflow_result") {
        "corrected" => {
            json!({"kind":"success","code":"workflow-corrected","message":"작업 흐름 경계를 사용자 확인으로 반영했습니다."})
        }
        "undone" => {
            json!({"kind":"success","code":"workflow-undone","message":"이전 경계를 되돌려 작업 흐름을 다시 투영했습니다."})
        }
        _ => Value::Null,
    };
    page_response(
        state,
        request,
        identifier(params, "session_id")?,
        feedback,
        None,
    )
}
fn failure(
    state: &AppState,
    request: &RequestContext,
    id: i64,
    code: &str,
    status: u16,
    enhanced: bool,
) -> Result<Response> {
    let code = if messages().get(code).is_some() {
        code
    } else {
        "correction-failed"
    };
    let message = &messages()[code];
    let response = if enhanced {
        let mut payload = json!({"status":"error","code":code,"message":message});
        if status == 409 {
            payload["reload_url"] = json!(format!("/sessions/{id}/workflow"));
        }
        let mut response = super::json_response(payload)?;
        *response.status_mut() = axum::http::StatusCode::from_u16(status).unwrap();
        response
    } else {
        page_response(
            state,
            request,
            id,
            json!({"kind":if status==409{"conflict"}else{"error"},"code":code,"message":message,"reload":status==409}),
            Some(status),
        )?
    };
    Ok(vary(response))
}
fn apply(
    state: &AppState,
    request: &RequestContext,
    id: i64,
    body: &[u8],
    enhanced: bool,
) -> Result<Response> {
    let correction = match correction::parse_workflow_correction_form(
        Some(request.header("content-type")),
        body,
    ) {
        Ok(value) => value,
        Err(error) => return failure(state, request, id, &error.code, error.status, enhanced),
    };
    let result = database(&state.config, true, |conn| {
        let projection = focus::workflow_focus_projection(conn, id)?;
        if correction.action == "undo" {
            assertions::undo_workflow_assertion(conn, &projection, &correction.domain_request())
        } else {
            assertions::apply_workflow_assertion(conn, &projection, &correction.domain_request())
        }
    });
    let result = match result {
        Ok(result) => result,
        Err(error) => {
            let known = messages().get(&error.code).is_some() && error.code != "correction-failed";
            return failure(
                state,
                request,
                id,
                if known {
                    &error.code
                } else {
                    "correction-failed"
                },
                if known {
                    if CONFLICTS.contains(&error.code.as_str()) {
                        409
                    } else {
                        422
                    }
                } else {
                    500
                },
                enhanced,
            );
        }
    };
    let undo = correction.action == "undo";
    let response = if enhanced {
        let assertion = result.assertion;
        let mut boundary = json!({"kind":assertion["boundary_kind"],"source_episode_key":assertion["source_episode_key"],"target_episode_key":assertion["target_episode_key"]});
        if boundary["kind"] == "relation" {
            boundary["relation_id"] = json!(correction_view::workflow_relation_id(
                boundary["source_episode_key"].as_str().unwrap_or(""),
                boundary["target_episode_key"].as_str().unwrap_or("")
            )?);
        }
        super::json_response(
            json!({"status":"ok","code":if undo{"workflow-undone"}else{"workflow-corrected"},"message":if undo{"이전 경계를 되돌려 작업 흐름을 다시 투영했습니다."}else{"작업 흐름 경계를 사용자 확인으로 반영했습니다."},"reload_url":format!("/sessions/{id}/workflow"),"boundary":boundary}),
        )?
    } else {
        transport::redirect(&format!(
            "/sessions/{id}/workflow?workflow_result={}#workflow-correction-feedback",
            if undo { "undone" } else { "corrected" }
        ))
    };
    Ok(vary(response))
}
async fn correct(
    State(state): State<AppState>,
    Path(mut params): Path<Params>,
    request: Request,
) -> Response {
    let mut context = match RequestContext::new(
        request.method().clone(),
        request.headers().clone(),
        request.uri().clone(),
    ) {
        Ok(value) => value,
        Err(error) => return ApiError(error).into_response(),
    };
    if let Err(error) = crate::parameters::validate(
        "/sessions/{session_id}/workflow/corrections",
        "POST",
        &mut context,
        &mut params,
    ) {
        return ApiError(error).into_response();
    }
    let id = match identifier(&params, "session_id") {
        Ok(id) => id,
        Err(error) => return ApiError(error).into_response(),
    };
    let enhanced = context.header("x-localbrain-partial") == WORKFLOW_CORRECTION_PARTIAL;
    let declared = context
        .headers
        .get("content-length")
        .and_then(|value| value.to_str().ok())
        .map(|value| {
            value
                .trim()
                .parse::<u64>()
                .ok()
                .is_some_and(|size| size <= MAX_WORKFLOW_CORRECTION_FORM_BYTES as u64)
        });
    let admission = correction::reject_cross_site_workflow_correction(
        context
            .headers
            .get("sec-fetch-site")
            .and_then(|value| value.to_str().ok()),
    );
    let rejection = match admission {
        Err(error) => Some((error.code, error.status)),
        Ok(()) if declared == Some(false) => Some(("invalid-form".into(), 400)),
        _ => None,
    };
    let result = if let Some((code, status)) = rejection {
        state
            .blocking(move |state| failure(&state, &context, id, &code, status, enhanced))
            .await
    } else {
        match transport::bounded_body(request.into_body(), MAX_WORKFLOW_CORRECTION_FORM_BYTES).await
        {
            Ok(body) => {
                state
                    .blocking(move |state| apply(&state, &context, id, &body, enhanced))
                    .await
            }
            Err(_) => {
                state
                    .blocking(move |state| {
                        failure(&state, &context, id, "invalid-form", 400, enhanced)
                    })
                    .await
            }
        }
    };
    match result {
        Ok(response) => response,
        Err(error) => error.into_response(),
    }
}
pub fn install(router: Router<AppState>) -> Router<AppState> {
    let router = bind(
        router,
        "/sessions/{session_id}/workflow",
        MethodFilter::GET,
        page,
        EMPTY,
    );
    router.route("/sessions/{session_id}/workflow/corrections", post(correct))
}
