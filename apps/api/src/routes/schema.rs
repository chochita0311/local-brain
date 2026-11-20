use super::{bind, Params, EMPTY};
use crate::{state::AppState, transport::RequestContext};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{schema, Result};
use serde_json::json;
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    state.render(request,"schema.html",json!({"active_page":"schema","schema_view":schema::schema_explorer_page_data(request.query.get("area").map(String::as_str),request.query.get("table").map(String::as_str))}),200)
}
pub fn install(router: Router<AppState>) -> Router<AppState> {
    bind(router, "/schema", MethodFilter::GET, page, EMPTY)
}
