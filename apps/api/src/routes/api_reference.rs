//! Retained public API contract, filtered by the same explicit feature assembly.
use super::{bind, json_response, Params, EMPTY};
use crate::{state::AppState, transport::RequestContext};
use axum::{
    response::{Html, IntoResponse, Response},
    routing::MethodFilter,
    Router,
};
use localbrain_core::backend::Result;

fn reference(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    Ok(match request.path.as_str() {
        "/openapi.json" => return json_response(crate::api_contract::configured(&state.config)),
        "/redoc" => Html(include_str!("../../resources/redoc.html")).into_response(),
        "/docs/oauth2-redirect" => {
            Html(include_str!("../../resources/oauth2-redirect.html")).into_response()
        }
        _ => Html(include_str!("../../resources/swagger.html")).into_response(),
    })
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    for path in ["/docs", "/redoc", "/docs/oauth2-redirect", "/openapi.json"] {
        router = bind(
            router,
            path,
            MethodFilter::GET.or(MethodFilter::HEAD),
            reference,
            EMPTY,
        );
    }
    router
}
