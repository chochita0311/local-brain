use super::{bind, json_response, BodyLimit, Params, EMPTY};
use crate::{
    state::{database, AppState},
    transport::{self, RequestContext},
};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{search, BackendError, Result};
use serde_json::{json, Value};
use std::collections::BTreeSet;
fn local(request: &RequestContext) -> Result<()> {
    if request
        .header("sec-fetch-site")
        .eq_ignore_ascii_case("cross-site")
    {
        Err(BackendError::invalid("local", "Local access required"))
    } else {
        Ok(())
    }
}
fn status_value(state: &AppState) -> Value {
    search::presentation::state_copy(
        &state
            .services
            .search
            .status()
            .unwrap_or_else(|_| json!({"state":"failed"})),
    )
}
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    local(request)?;
    let query = request.query.get("q").cloned().unwrap_or_default();
    let page = request.integer("page", 1)?;
    let mode = request
        .query
        .get("mode")
        .map(String::as_str)
        .unwrap_or("auto");
    if query.chars().count() > 300
        || !(1..=1_000_000).contains(&page)
        || !["auto", "keyword", "ai"].contains(&mode)
    {
        return Err(BackendError::new(422, "query", "Invalid search query"));
    }
    let mut status = status_value(state);
    if matches!(status["state"].as_str(), Some("disabled" | "model-missing")) {
        let results = if query
            .trim_matches(localbrain_core::backend::unicode::python_space)
            .is_empty()
        {
            vec![]
        } else {
            database(&state.config, false, |conn| {
                search::keyword::keyword_search(conn, &query, "all", 80, &state.config)
            })?
        };
        return state.render(request,"keyword-search.html",json!({"active_page":"natural-search","natural_query":query,"results":results,"search_status":status}),200);
    }
    let mut result = Value::Null;
    let mut error = None;
    if !query
        .trim_matches(localbrain_core::backend::unicode::python_space)
        .is_empty()
        && !matches!(
            status["state"].as_str(),
            Some("disabled" | "model-missing" | "no-data")
        )
    {
        match state.services.search.search(&query, page as usize) {
            Ok(value) => {
                if value["partial"] == true {
                    status["state"] = json!("partial");
                    status = search::presentation::state_copy(&status);
                }
                result = value;
            }
            Err(failure) => {
                error=match failure.code.as_str(){"SEARCH_INPUT_TOO_LONG"=>Some("검색어를 더 짧게 입력해 주세요. 이 표현은 검색 모델의 입력 한도를 넘었습니다."),"SEARCH_INDEX_UNAVAILABLE" if status["state"]=="ready"=>Some("검색할 자료를 불러오지 못했습니다. 잠시 후 다시 검색해 주세요."),"SEARCH_INDEX_UNAVAILABLE"=>None,_=>Some("검색을 완료하지 못했습니다. 잠시 후 다시 검색해 주세요.")};
            }
        }
    }
    state.render(request,"natural-search.html",json!({"active_page":"natural-search","natural_query":query,"search_status":status,"search_response":result,"query_error":error,"previous_url":format!("/natural-search?{}",search::urlencode(&[("q",query.clone()),("page",(page-1).max(1).to_string())])),"next_url":format!("/natural-search?{}",search::urlencode(&[("q",query),("page",(page+1).to_string())]))}),200)
}
fn status(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    local(request)?;
    json_response(status_value(state))
}
fn action(state: &AppState, request: &RequestContext, _: &Params, body: &[u8]) -> Result<Response> {
    local(request)?;
    let invalid = || BackendError::new(422, "form", "검색어 또는 요청 형식을 확인해 주세요.");
    if !request
        .content_type()
        .eq_ignore_ascii_case("application/x-www-form-urlencoded")
        || body.len() > 160 * 1024
    {
        return Err(invalid());
    }
    let form =
        transport::form(body, 128, &BTreeSet::new(), None, true, false).map_err(|_| invalid())?;
    let query = form["q"].as_str().unwrap_or("");
    if query.chars().count() > 300 {
        return Err(invalid());
    }
    if request.path.ends_with("/cancel") {
        state.services.search.cancel();
    } else {
        state
            .services
            .search
            .request_prepare()
            .map_err(|_| BackendError::unavailable("검색 설정을 저장하지 못했습니다."))?;
    }
    Ok(transport::redirect(&format!(
        "/natural-search?{}",
        search::urlencode(&[("q", query.into())])
    )))
}
fn evidence(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    _: &[u8],
) -> Result<Response> {
    local(request)?;
    let generation = request.parameter("generation");
    let back = request
        .query
        .get("return_to")
        .map(String::as_str)
        .unwrap_or("/natural-search");
    if generation.chars().count() > 64 || back.chars().count() > 4000 {
        return Err(BackendError::new(422, "query", "Invalid evidence query"));
    }
    let row = state
        .services
        .search
        .evidence(super::identifier(params, "rowid")?, generation)
        .ok();
    let status = if row.is_some() { 200 } else { 409 };
    state.render(request,"natural-search-evidence.html",json!({"active_page":"natural-search","evidence":row,"return_to":search::presentation::safe_return(back)}),status)
}
fn legacy(_: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let query = request.parameter("q");
    if query.chars().count() > 300 {
        return Err(BackendError::new(422, "query", "Invalid search query"));
    }
    Ok(transport::redirect(&format!(
        "/natural-search?{}",
        search::urlencode(&[("q", query.into())])
    )))
}
fn legacy_page(
    state: &AppState,
    request: &RequestContext,
    _: &Params,
    _: &[u8],
) -> Result<Response> {
    let values = super::atlassian::search_filters(request)?;
    let query = request.parameter("q");
    let scope = request.parameter("source");
    let scope = if ["sessions", "documents", "atlassian"].contains(&scope) {
        scope
    } else {
        "all"
    };
    let (filters, results, options) = database(&state.config, false, |conn| {
        let filters =
            localbrain_core::backend::atlassian::browse::normalize_browse_filters(&values)?;
        let results = if query
            .trim_matches(localbrain_core::backend::unicode::python_space)
            .is_empty()
        {
            vec![]
        } else {
            search::keyword::legacy_search(conn, query, scope, &filters, 80)?
        };
        let options =
            localbrain_core::backend::atlassian::browse::browse_inventory(conn, &json!({}))?
                ["options"]
                .clone();
        Ok((filters, results, options))
    })?;
    state.render(request,"search.html",json!({"active_page":"search","query":query,"results":results,"selected_source":scope,"filters":filters,"search_options":options}),200)
}
pub fn install_legacy(router: Router<AppState>) -> Router<AppState> {
    bind(router, "/search", MethodFilter::GET, legacy_page, EMPTY)
}
pub fn install(mut router: Router<AppState>, desktop: bool) -> Router<AppState> {
    for (path, handler) in [
        ("/natural-search", page as super::Handler),
        ("/api/natural-search/status", status),
        ("/natural-search/evidence/{rowid}", evidence),
    ] {
        router = bind(router, path, MethodFilter::GET, handler, EMPTY);
    }
    for path in ["/natural-search/prepare", "/natural-search/cancel"] {
        router = bind(
            router,
            path,
            MethodFilter::POST,
            action,
            BodyLimit {
                status: 422,
                bytes: 160 * 1024,
                message: "검색어 또는 요청 형식을 확인해 주세요.",
            },
        );
    }
    if desktop {
        router = bind(router, "/search", MethodFilter::GET, legacy, EMPTY);
    }
    router
}
