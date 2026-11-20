use super::{explorer, form_route, integer, optional, text};
use crate::{
    routes::{bind, Params, EMPTY},
    state::{database, AppState},
    transport::{self, RequestContext},
};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    atlassian::{refresh, runner},
    maintenance, search, BackendError, Result,
};
use rusqlite::Connection;
use serde_json::{json, Value};
fn retry_ids(value: Option<&str>) -> Result<Option<Vec<i64>>> {
    let Some(value) = value.filter(|value| !value.is_empty()) else {
        return Ok(None);
    };
    let mut result = Vec::new();
    for value in value.split(',').take(20) {
        let id = integer(Some(value), "Retry")
            .ok()
            .flatten()
            .ok_or_else(|| {
                BackendError::invalid("invalid-retry", "Retry 링크/문서 선택이 올바르지 않습니다")
            })?;
        if !result.contains(&id) {
            result.push(id);
        }
    }
    Ok((!result.is_empty()).then_some(result))
}
fn runner_ready(state: &AppState) -> Value {
    json!({"claude":maintenance::runner_executable(&state.config,"claude").is_some(),"codex":maintenance::runner_executable(&state.config,"codex").is_some()})
}
pub(super) fn start(state: &AppState, run: &str) -> Result<()> {
    runner::start_run(
        state
            .services
            .tasks
            .as_ref()
            .ok_or_else(|| BackendError::unavailable("Task runtime unavailable"))?,
        run,
        state.services.features.external_executor.clone(),
    )
}
#[expect(
    clippy::too_many_arguments,
    reason = "Preserves the explicit service boundary and existing caller contract."
)]
fn context(
    state: &AppState,
    conn: &Connection,
    scope: &str,
    id: Option<i64>,
    page: i64,
    selected: Option<&[i64]>,
    run: Option<&str>,
    error: Option<&str>,
    return_to: Option<&str>,
) -> Result<Value> {
    let preview = refresh::refresh_preview(
        conn,
        &json!({"scope_kind":scope,"scope_id":id,"page":page,"selected_ids":selected}),
    )?;
    let return_to = if let Some(value) = return_to {
        explorer::inventory_return_path(conn, Some(value), false)?
    } else {
        preview["scope"]["return_to"]
            .as_str()
            .unwrap_or("/atlassian")
            .into()
    };
    Ok(
        json!({"active_page":"atlassian","preview":preview,"scope_kind":scope,"scope_id":id,"page":page,"run_result":run.filter(|run|!run.is_empty()).map(|run|refresh::refresh_run_result(conn,run)).transpose()?.flatten(),"form_error":error,"return_to":return_to,"return_to_encoded":search::quote(&return_to),"external_executor_ready":state.services.features.external_executor.is_some(),"runner_ready":runner_ready(state)}),
    )
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let scope = request
        .query
        .get("scope")
        .map(String::as_str)
        .unwrap_or("all_known");
    let id = request
        .query
        .get("id")
        .map(|raw| {
            raw.parse::<i64>()
                .map_err(|_| BackendError::new(422, "query", "Invalid scope ID"))
        })
        .transpose()?;
    let page = request.integer("page", 1)?;
    if page < 1 {
        return Err(BackendError::new(422, "query", "Page must be positive"));
    }
    let result = retry_ids(request.query.get("retry").map(String::as_str)).and_then(|selected| {
        database(&state.config, false, |conn| {
            context(
                state,
                conn,
                scope,
                id,
                page,
                selected.as_deref(),
                request.query.get("run").map(String::as_str),
                None,
                request.query.get("return_to").map(String::as_str),
            )
        })
    });
    match result {
        Ok(context) => state.render(request, "atlassian-refresh.html", context, 200),
        Err(mut error) if error.status < 500 => {
            error.status = 404;
            Err(error)
        }
        Err(error) => Err(error),
    }
}
fn submit(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    form: Result<Value>,
) -> Result<Response> {
    let mut scope = "all_known".to_owned();
    let mut id = None;
    let mut page = 1;
    let mut selected = Vec::new();
    let mut return_to = None;
    let mut safe_return_to = "/atlassian".into();
    let result = (|| {
        let form = form?;
        return_to = optional(&form, "return_to").map(str::to_owned);
        scope = optional(&form, "scope").unwrap_or("all_known").into();
        id = integer(optional(&form, "scope_id"), "Refresh scope")?;
        page = integer(optional(&form, "page"), "Page")?.unwrap_or(1);
        for value in form["item_id"].as_array().map(Vec::as_slice).unwrap_or(&[]) {
            if let Some(value) = integer(value.as_str(), "Atlassian 링크/문서")? {
                selected.push(value);
            }
        }
        let chosen = optional(&form, "runner").unwrap_or("claude");
        if !["claude", "codex"].contains(&chosen) {
            return Err(BackendError::invalid(
                "invalid-runner",
                "Maintenance runner is invalid",
            ));
        }
        if state.services.features.external_executor.is_none() {
            return Err(BackendError::invalid(
                "executor-unavailable",
                "Approved host-side read executor is not connected",
            ));
        }
        if maintenance::runner_executable(&state.config, chosen).is_none() {
            return Err(BackendError::invalid(
                "runner-unavailable",
                format!(
                    "{} runner is unavailable",
                    if chosen == "claude" {
                        "Claude"
                    } else {
                        "Codex"
                    }
                ),
            ));
        }
        let run = database(&state.config, true, |conn| {
            if return_to.is_some() {
                safe_return_to =
                    explorer::inventory_return_path(conn, return_to.as_deref(), false)?;
            }
            refresh::prepare_atlassian_refresh_run(
                conn,
                &state.config,
                &json!({"scope_kind":scope,"scope_id":id,"selected_item_ids":selected,"include_catalog":text(&form,"include_catalog")=="true","page":page,"runner":chosen}),
                None,
            )
        })?;
        start(state, &run)?;
        Ok(run)
    })();
    match result {
        Ok(run) => {
            let mut pairs = vec![("scope", scope), ("page", page.to_string()), ("run", run)];
            if let Some(id) = id {
                pairs.push(("id", id.to_string()));
            }
            if return_to.is_some() {
                pairs.push(("return_to", safe_return_to));
            }
            Ok(transport::redirect(&format!(
                "/atlassian/refresh?{}",
                search::urlencode(&pairs)
            )))
        }
        Err(error) if error.status < 500 => {
            let context = database(&state.config, false, |conn| {
                context(
                    state,
                    conn,
                    &scope,
                    id,
                    page,
                    Some(&selected),
                    None,
                    Some(&error.message),
                    return_to.as_deref(),
                )
            })
            .map_err(|mut error| {
                if error.status < 500 {
                    error.status = 422;
                }
                error
            })?;
            state.render(request, "atlassian-refresh.html", context, 422)
        }
        Err(error) => Err(error),
    }
}
pub fn install(router: Router<AppState>) -> Router<AppState> {
    let router = bind(router, "/atlassian/refresh", MethodFilter::GET, page, EMPTY);
    form_route(router, "/atlassian/refresh", submit)
}
