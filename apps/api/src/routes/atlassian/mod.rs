mod explorer;
mod local;
mod navigation;
mod receipts;
mod refresh;
mod registration;
pub(crate) use receipts::SyncReceipts;

use crate::{
    routes::Params,
    state::AppState,
    transport::{self, ApiError, RequestContext},
};
use axum::{
    extract::{Path, Request, State},
    response::{IntoResponse, Response},
    routing::{on, MethodFilter},
    Router,
};
use localbrain_core::backend::{unicode, BackendError, Result};
use serde_json::Value;
type FormHandler = fn(&AppState, &RequestContext, &Params, Result<Value>) -> Result<Response>;
fn form_route(
    router: Router<AppState>,
    path: &'static str,
    handler: FormHandler,
) -> Router<AppState> {
    router.route(path,on(MethodFilter::POST,move|State(state):State<AppState>,Path(params):Path<Params>,request:Request|async move{
        let context=match RequestContext::new(request.method().clone(),request.headers().clone(),request.uri().clone()){Ok(value)=>value,Err(error)=>return ApiError(error).into_response()};
        let form=if !context.content_type().eq_ignore_ascii_case("application/x-www-form-urlencoded"){Err(invalid("Form encoding is unsupported"))}else{match transport::bounded_body(request.into_body(),160*1024).await{Err(_)=>Err(invalid("Form is too large")),Ok(bytes)=>transport::form(&bytes,128,&["item_id","topic_id"].into(),None,true,false).map_err(|_|invalid("Form data is invalid"))}};
        match state.blocking(move|state|handler(&state,&context,&params,form)).await{Ok(response)=>response,Err(error)=>error.into_response()}
    }))
}
fn invalid(message: impl Into<String>) -> BackendError {
    BackendError::new(422, "invalid-form", message)
}
fn text<'a>(form: &'a Value, key: &str) -> &'a str {
    form[key].as_str().unwrap_or("")
}
fn optional<'a>(form: &'a Value, key: &str) -> Option<&'a str> {
    form.get(key).and_then(Value::as_str)
}
fn integer(value: Option<&str>, field: &str) -> Result<Option<i64>> {
    let Some(raw) = value.filter(|value| !value.is_empty()) else {
        return Ok(None);
    };
    let parsed = unicode::integer_literal(raw).and_then(|raw| raw.parse::<i64>().ok());
    parsed
        .filter(|id| *id >= 1)
        .map(Some)
        .ok_or_else(|| invalid(format!("{field} is invalid")))
}
pub(super) fn search_filters(request: &RequestContext) -> Result<Value> {
    let mut values = explorer::fields(request)?;
    let object = values.as_object_mut().unwrap();
    object.remove("q");
    object.remove("structural_scope");
    values["service"] = request
        .query
        .get("service")
        .map(|value| serde_json::json!(value))
        .unwrap_or(Value::Null);
    Ok(values)
}
pub fn install(router: Router<AppState>, workstreams: bool) -> Router<AppState> {
    let router = registration::install(explorer::install(router));
    refresh::install(local::install(router, workstreams))
}
