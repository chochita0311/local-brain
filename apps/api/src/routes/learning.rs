use super::{bind, identifier, Params, EMPTY, LEARNING_FORM};
use crate::{
    state::{database, immediate, AppState},
    transport::{self, RequestContext},
};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{learning, BackendError, Result};
use serde_json::{json, Value};
use std::collections::BTreeSet;

fn local(request: &RequestContext) -> Result<()> {
    if !["localhost", "127.0.0.1", "::1"].contains(&request.hostname.as_str())
        || request
            .header("sec-fetch-site")
            .eq_ignore_ascii_case("cross-site")
    {
        Err(BackendError::invalid("local", "Local access required"))
    } else {
        Ok(())
    }
}
fn form(request: &RequestContext, body: &[u8], keys: &[&str]) -> Result<Value> {
    local(request)?;
    if !request.same_origin() {
        return Err(BackendError::new(
            403,
            "origin",
            "Same-origin submission required",
        ));
    }
    if request.content_type() != "application/x-www-form-urlencoded" {
        return Err(BackendError::new(
            415,
            "encoding",
            "URL-encoded form required",
        ));
    }
    transport::form(
        body,
        12,
        &BTreeSet::new(),
        Some(&keys.iter().copied().collect()),
        false,
        true,
    )
    .map_err(|error| error.0)
}
fn render(
    state: &AppState,
    request: &RequestContext,
    template: &str,
    mut data: Value,
    status: u16,
) -> Result<Response> {
    data["active_page"] = json!("dashboard");
    let mut response = state.render(request, template, data, status)?;
    response
        .headers_mut()
        .insert("referrer-policy", "no-referrer".parse().unwrap());
    Ok(response)
}
pub(super) fn home(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    _: &[u8],
) -> Result<Response> {
    local(request)?;
    let mut data = database(&state.config, false, |db| {
        learning::daily_selection(db, &state.config.timezone_name)
    })?;
    for lesson in data["selected_lessons"].as_array_mut().unwrap() {
        *lesson = learning::presentation::present_note(
            lesson,
            &uuid::Uuid::new_v4().simple().to_string(),
        )?;
    }
    data["note_return"] = json!("home");
    render(state, request, "dashboard.html", data, 200)
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn render_reader(
    state: &AppState,
    request: &RequestContext,
    id: i64,
    attempt: Option<i64>,
    question: Option<&str>,
    error: Option<&str>,
    values: Option<&Value>,
    status: u16,
) -> Result<Response> {
    let selected = values
        .and_then(|value| value["question_id"].as_str())
        .or(question);
    let mut data = match database(&state.config, false, |db| {
        learning::reader(db, id, &state.config.timezone_name, attempt, selected)
    }) {
        Ok(data) => data,
        Err(error) if error.code == "learning" => {
            return render(
                state,
                request,
                "learning-reader.html",
                json!({"missing":error.message}),
                404,
            )
        }
        Err(error) => return Err(error),
    };
    let note = values
        .and_then(|value| value["from_note"].as_str())
        .unwrap_or_else(|| request.parameter("from_note"))
        == "1";
    data["error"] = json!(error);
    data["values"] = values.cloned().unwrap_or_else(|| json!({}));
    data["submission_key"] = json!(uuid::Uuid::new_v4().simple().to_string());
    data["read_key"] = json!(uuid::Uuid::new_v4().simple().to_string());
    data["note_practice"] = json!(note);
    data["hint_used"] = json!(note || request.parameter("hint") == "1");
    if let Some(values) = values {
        if let Some(question) = data["lesson"]["questions"]
            .as_array()
            .and_then(|questions| {
                questions
                    .iter()
                    .find(|question| question["id"] == values["question_id"])
            })
        {
            data["question"] = question.clone();
        }
        if values["submission_key"]
            .as_str()
            .is_some_and(|s| !s.is_empty())
        {
            data["submission_key"] = values["submission_key"].clone();
        }
        data["hint_used"] = json!(note || values["hint_used"] == "1");
    }
    render(state, request, "learning-reader.html", data, status)
}
fn render_library(
    state: &AppState,
    request: &RequestContext,
    error: Option<&str>,
    status: u16,
) -> Result<Response> {
    let lessons = database(&state.config, false, |db| {
        learning::library(db, &state.config.timezone_name)
    })?;
    render(
        state,
        request,
        "learning-library.html",
        json!({"lessons":lessons,"error":error,"notice":(request.parameter("updated")=="1").then_some("목록 표시를 변경했습니다.")}),
        status,
    )
}
fn library(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    local(request)?;
    render_library(state, request, None, 200)
}
fn reader(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    local(request)?;
    let attempt = if request.query.contains_key("attempt") {
        Some(request.integer("attempt", 0)?)
    } else {
        None
    };
    render_reader(
        state,
        request,
        identifier(params, "lesson_id")?,
        attempt,
        request.query.get("question").map(String::as_str),
        None,
        None,
        200,
    )
}
fn note(state: &AppState, request: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    local(request)?;
    let id = identifier(params, "lesson_id")?;
    let mut data = match database(&state.config, false, |db| {
        learning::reader(db, id, &state.config.timezone_name, None, None)
    }) {
        Ok(data) => data,
        Err(error) if error.code == "learning" => {
            return render(
                state,
                request,
                "learning-reader.html",
                json!({"missing":error.message}),
                404,
            )
        }
        Err(error) => return Err(error),
    };
    let question = data["question"].clone();
    let pending = if data["attempt"]["outcome"] == "pending" {
        data["attempt"]["id"].clone()
    } else {
        Value::Null
    };
    let today = learning::today(&state.config.timezone_name)?;
    let mut done = false;
    for item in data["history"].as_array().into_iter().flatten() {
        if let Some(at) = item["assessed_at"].as_str().filter(|s| !s.is_empty()) {
            if learning::local_day(at, &state.config.timezone_name)? == today {
                done = true;
                break;
            }
        }
    }
    data["lesson"]["question"] = question;
    data["lesson"]["pending"] = pending;
    data["lesson"]["done_today"] = json!(done);
    data["lesson"] = learning::presentation::present_note(
        &data["lesson"],
        &uuid::Uuid::new_v4().simple().to_string(),
    )?;
    data["note_return"] = json!("note");
    render(state, request, "learning-note.html", data, 200)
}
fn submit(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    let id = identifier(params, "lesson_id")?;
    let mut fields = form(
        request,
        body,
        &[
            "question_id",
            "submission_key",
            "action",
            "answer",
            "confidence",
            "hint_used",
            "from_note",
            "return_to",
        ],
    )?;
    if fields["from_note"] == "1" {
        fields["hint_used"] = json!("1");
    }
    let attempt = match immediate(&state.config, |db| {
        learning::submit_attempt(db, id, &fields)
    }) {
        Ok(value) => value,
        Err(error) if error.code == "learning" => {
            return render_reader(
                state,
                request,
                id,
                None,
                None,
                Some(&error.message),
                Some(&fields),
                422,
            )
        }
        Err(error) if error.code == "database" => {
            return render_reader(
                state,
                request,
                id,
                None,
                None,
                Some("저장하지 못했습니다. 입력한 답변을 확인하고 다시 제출해 주세요."),
                Some(&fields),
                503,
            )
        }
        Err(error) => return Err(error),
    };
    Ok(transport::redirect(
        &if fields["action"] == "read" && fields["return_to"] == "home" {
            "/#today-title".into()
        } else if fields["action"] == "read" && fields["return_to"] == "note" {
            format!("/learning/{id}/note#article-finish")
        } else {
            format!("/learning/{id}?attempt={attempt}#feedback")
        },
    ))
}
fn assess(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    let id = identifier(params, "lesson_id")?;
    let fields = form(request, body, &["attempt_id", "outcome"])?;
    let attempt = fields["attempt_id"]
        .as_str()
        .and_then(|value| value.parse::<i64>().ok())
        .filter(|value| *value > 0)
        .ok_or_else(|| BackendError::invalid("attempt", "Invalid attempt"))?;
    match immediate(&state.config, |db| {
        learning::assess_attempt(db, id, attempt, fields["outcome"].as_str().unwrap_or(""))
    }) {
        Ok(()) => Ok(transport::redirect(&format!(
            "/learning/{id}?attempt={attempt}#feedback"
        ))),
        Err(error) if error.code == "learning" => render_reader(
            state,
            request,
            id,
            Some(attempt),
            None,
            Some(&error.message),
            None,
            422,
        ),
        Err(error) if error.code == "database" => render_reader(
            state,
            request,
            id,
            Some(attempt),
            None,
            Some("자기 평가를 저장하지 못했습니다. 선택한 평가를 다시 제출해 주세요."),
            None,
            503,
        ),
        Err(error) => Err(error),
    }
}
fn visibility(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    body: &[u8],
) -> Result<Response> {
    let id = identifier(params, "lesson_id")?;
    let fields = form(request, body, &["action"])?;
    match database(&state.config, true, |db| {
        learning::set_visibility(
            db,
            id,
            fields["action"].as_str().unwrap_or(""),
            &state.config.timezone_name,
        )
    }) {
        Ok(()) => Ok(transport::redirect("/learning?updated=1")),
        Err(error) if error.code == "learning" => {
            render_library(state, request, Some(&error.message), 422)
        }
        Err(error) if error.code == "database" => render_library(
            state,
            request,
            Some("표시 설정을 저장하지 못했습니다. 다시 시도해 주세요."),
            503,
        ),
        Err(error) => Err(error),
    }
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for (path, handler) in [
        ("/learning", library as super::Handler),
        ("/learning/{lesson_id}", reader),
        ("/learning/{lesson_id}/note", note),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    for (path, handler) in [
        ("/learning/{lesson_id}/attempts", submit as super::Handler),
        ("/learning/{lesson_id}/assess", assess),
        ("/learning/{lesson_id}/visibility", visibility),
    ] {
        router = bind(router, path, MethodFilter::POST, handler, LEARNING_FORM);
    }
    router
}
