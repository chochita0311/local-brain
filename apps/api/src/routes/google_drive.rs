use super::{bind, json_response, Params, EMPTY, SETTINGS};
use crate::{
    state::AppState,
    transport::{self, RequestContext},
};
use axum::{http::Method, response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{google_drive::DriveService, BackendError, Result};
use serde_json::{json, Value};
use std::sync::Arc;
fn service(state: &AppState) -> Result<Arc<DriveService>> {
    state.services.google_drive.clone().ok_or_else(||BackendError::unavailable("Google Drive의 로컬 상태를 읽지 못했습니다. 기존 상태를 보존합니다. 앱 데이터 폴더를 확인해 주세요."))
}
fn action<T>(result: Result<T>) -> Result<T> {
    result.map_err(|error| {
        if error.status == 422 || error.code == "busy" {
            BackendError::new(
                if error.code == "busy" { 409 } else { 422 },
                error.code,
                error.message,
            )
        } else {
            error
        }
    })
}
fn payload(body: &[u8]) -> Result<Value> {
    transport::json_object(body, 422, "설정 요청 형식을 확인해 주세요.").map_err(|error| error.0)
}
fn exact(body: &Value, keys: &[&str]) -> bool {
    body.as_object().is_some_and(|map| {
        map.len() == keys.len() && map.keys().all(|key| keys.contains(&key.as_str()))
    })
}
fn handle(
    state: &AppState,
    request: &RequestContext,
    params: &Params,
    bytes: &[u8],
) -> Result<Response> {
    if request.method == Method::GET {
        return json_response(action(service(state)?.status())?);
    }
    if request.path == "/api/settings/google-drive/connections" {
        let values = payload(bytes)?;
        if !exact(&values, &["url", "target"])
            || !values["url"].is_string()
            || !values["target"].is_string()
        {
            return Err(BackendError::new(
                422,
                "request",
                "루트 폴더 URL과 내 대상 폴더명을 입력해 주세요.",
            ));
        }
        return json_response(action(service(state)?.add(
            values["url"].as_str().unwrap(),
            values["target"].as_str().unwrap(),
        ))?);
    }
    let id = &params["connection_id"];
    if request.path.ends_with("/connect") {
        let values = payload(bytes)?;
        if values
            .as_object()
            .unwrap()
            .keys()
            .any(|key| !["account", "login"].contains(&key.as_str()))
            || values
                .get("account")
                .is_some_and(|value| !value.is_string())
            || values.get("login").is_some_and(|value| !value.is_boolean())
        {
            return Err(BackendError::new(
                422,
                "request",
                "Google 계정과 로그인 요청을 확인해 주세요.",
            ));
        }
        let login = values["login"].as_bool().unwrap_or(false);
        action(
            service(state)?.authenticate(
                id,
                values["account"]
                    .as_str()
                    .filter(|account| !account.is_empty()),
                login,
            ),
        )?;
        return json_response(json!({"status":if login{"auth_pending"}else{"connected"}}));
    }
    if request.path.ends_with("/browse") {
        return json_response(json!({"publishers":action(service(state)?.browse(id))?}));
    }
    let job = &params["job"];
    if request.method == Method::PATCH {
        let values = payload(bytes)?;
        action(service(state)?.configure(id, job, &values))?;
        json_response(json!({"saved":true}))
    } else {
        action(service(state)?.run(id, job))?;
        json_response(json!({"started":true}))
    }
}
pub fn install(mut router: Router<AppState>) -> Router<AppState> {
    router = bind(
        router,
        "/api/settings/google-drive",
        MethodFilter::GET,
        handle,
        EMPTY,
    );
    for (path, method) in [
        ("/api/settings/google-drive/connections", MethodFilter::POST),
        (
            "/api/settings/google-drive/{connection_id}/connect",
            MethodFilter::POST,
        ),
        (
            "/api/settings/google-drive/{connection_id}/browse",
            MethodFilter::POST,
        ),
        (
            "/api/settings/google-drive/{connection_id}/jobs/{job}",
            MethodFilter::PATCH,
        ),
        (
            "/api/settings/google-drive/{connection_id}/jobs/{job}/run",
            MethodFilter::POST,
        ),
    ] {
        router = bind(router, path, method, handle, SETTINGS);
    }
    router
}
