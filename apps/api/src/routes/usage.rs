use super::{bind, Params, EMPTY};
use crate::{
    state::{database, AppState},
    transport::RequestContext,
    usage_dashboard::UsageDashboardCache,
};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    preferences,
    usage::{self, UsageOptions},
    Result,
};
use serde_json::{json, Value};
fn dashboard(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    let setting = preferences::effective_preferences(&state.config)?;
    let options = UsageOptions {
        view: request
            .query
            .get("view")
            .cloned()
            .unwrap_or_else(|| "daily".into()),
        source: request
            .query
            .get("source")
            .cloned()
            .unwrap_or_else(|| "all".into()),
        metric: request
            .query
            .get("metric")
            .cloned()
            .unwrap_or_else(|| "cost".into()),
        breakdown: request
            .query
            .get("breakdown")
            .cloned()
            .unwrap_or_else(|| "source".into()),
        from_value: request.query.get("from").cloned(),
        to_value: request.query.get("to").cloned(),
        timezone_name: setting["timezone"]
            .as_str()
            .unwrap_or(&state.config.timezone_name)
            .into(),
        visible_only: true,
        ..Default::default()
    };
    let (usage, refresh, status) = if UsageDashboardCache::is_default(&options) {
        let refresh_request = request.path == "/sessions-dashboard/refresh"
            || request.header("x-requested-with") == "LocalBrain-Usage-Dashboard";
        let cached = if refresh_request
            || request
                .query
                .get("refresh")
                .is_some_and(|value| value == "1")
        {
            None
        } else {
            UsageDashboardCache::preview(&state.config, &options)?
        };
        if let Some((usage, needs_refresh)) = cached {
            (usage, needs_refresh, 200)
        } else {
            match state
                .services
                .usage_dashboard
                .refresh(&state.config, options)
            {
                Ok(usage) => (usage, false, 200),
                Err(error) if refresh_request => return Err(error),
                Err(error) => (Value::Null, false, error.status),
            }
        }
    } else {
        (
            database(&state.config, false, |conn| {
                usage::usage_dashboard_data(conn, &options)
            })?,
            false,
            200,
        )
    };
    state.render(
        request,
        "sessions_dashboard.html",
        json!({"active_page":"sessions-dashboard","usage":usage,"usage_refresh":refresh}),
        status,
    )
}
pub fn install(router: Router<AppState>) -> Router<AppState> {
    let router = bind(
        router,
        "/sessions-dashboard",
        MethodFilter::GET,
        dashboard,
        EMPTY,
    );
    bind(
        router,
        "/sessions-dashboard/refresh",
        MethodFilter::GET,
        dashboard,
        EMPTY,
    )
}
