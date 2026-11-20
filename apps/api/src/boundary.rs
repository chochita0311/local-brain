use crate::transport::{self, ApiError, RequestContext};
use axum::{
    extract::{Request, State},
    middleware::Next,
    response::{IntoResponse, Response},
};
use localbrain_core::backend::{preferences, Config};
use regex::Regex;
use std::sync::{Arc, LazyLock};
use subtle::ConstantTimeEq;

#[derive(Clone)]
pub struct Boundary {
    pub config: Arc<Config>,
    pub token: String,
}
fn failure(status: u16, message: &str) -> Response {
    let mut response = transport::error(status, message).into_response();
    response.headers_mut().insert(
        "content-type",
        "application/json; charset=utf-8".parse().unwrap(),
    );
    response
        .headers_mut()
        .insert("cache-control", "no-store, private".parse().unwrap());
    response
        .headers_mut()
        .insert("x-content-type-options", "nosniff".parse().unwrap());
    response
}
pub fn authorized(request: &RequestContext, token: &str, start: bool) -> bool {
    let mut supplied = String::new();
    for cookie in request.header("cookie").split(';') {
        if let Some((name, value)) = cookie.trim().split_once('=') {
            if name == "localbrain-desktop" {
                supplied = value.trim_matches('"').into();
            }
        }
    }
    if let Some(value) = request.header("authorization").strip_prefix("Bearer ") {
        supplied = value.into();
    }
    if start {
        supplied = request.parameter("token").into();
    }
    !token.is_empty() && bool::from(token.as_bytes().ct_eq(supplied.as_bytes()))
}
fn desktop_path(path: &str) -> bool {
    static ALLOWED: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(concat!(r"^/(?:$|static/.*|desktop/(?:start|shutdown)|settings|onboarding|",
        r"help(?:/(?:settings|sessions-dashboard|sessions|local-contexts|search|terminal))?|terminal|",
        r"sessions-dashboard(?:/refresh)?|projects|sessions(?:/\d+(?:/(?:pin|unpin|title|chart-activity)|/(?:subsessions|subagents)/[^/]+)?|/chart/project-visibility|/sync)?|",
        r"context(?:/.*)?|context-search|documents/\d+|natural-search(?:/.*)?|search|",
        r"api/(?:health|terminal(?:/.*)?|settings(?:/.*)?|sessions(?:/.*)?|session-chart(?:/.*)?|",
        r"context-(?:roots|files|sources)(?:/.*)?|context-search/(?:status|answer|unload)|natural-search/status))$"
    )).unwrap()
    });
    ALLOWED.is_match(path)
        && !path
            .split('/')
            .any(|part| ["workflow", "insights", "runs"].contains(&part))
}
pub async fn middleware(
    State(boundary): State<Boundary>,
    request: Request,
    next: Next,
) -> Response {
    let context = match RequestContext::new(
        request.method().clone(),
        request.headers().clone(),
        request.uri().clone(),
    ) {
        Ok(context) => context,
        Err(error) => return failure(error.status, &error.message),
    };
    if !["localhost", "127.0.0.1", "::1"].contains(&context.hostname.as_str()) {
        return failure(403, "Local access required");
    }
    if !matches!(context.method.as_str(), "GET" | "HEAD" | "OPTIONS") {
        let origin = context.header("origin");
        let authority = origin
            .strip_prefix("//")
            .or_else(|| origin.split_once("://").map(|(_, rest)| rest))
            .map(|rest| rest.split(['/', '?', '#']).next().unwrap_or(""));
        let same = origin.is_empty() || authority == Some(context.authority.as_str());
        if context.header("sec-fetch-site") == "cross-site" || !same {
            return failure(403, "같은 앱 화면에서 요청해 주세요.");
        }
    }
    if boundary.config.desktop {
        if context.hostname != "127.0.0.1" {
            return failure(403, "Local access required");
        }
        if !desktop_path(&context.path) {
            return failure(404, "이 앱에서 제공하지 않는 기능입니다.");
        }
        if !authorized(&context, &boundary.token, context.path == "/desktop/start") {
            return failure(401, "앱 창에서 열어 주세요.");
        }
        if context.path == "/desktop/start" {
            let config = boundary.config.clone();
            let preferences =
                tokio::task::spawn_blocking(move || preferences::effective_preferences(&config))
                    .await;
            let target =
                match preferences {
                    Ok(Ok(value)) => {
                        if value["onboarding_completed"] == true {
                            format!(
                                "/{}",
                                value["startup_screen"]
                                    .as_str()
                                    .unwrap_or("sessions-dashboard")
                            )
                        } else {
                            "/onboarding".into()
                        }
                    }
                    Ok(Err(error)) if error.status == 409 => "/settings".into(),
                    Ok(Err(error)) => return ApiError(error).into_response(),
                    Err(_) => return failure(
                        503,
                        "로컬 설정을 처리하지 못했습니다. LocalBrain 실행 상태를 확인해 주세요.",
                    ),
                };
            let mut response = transport::redirect(&target);
            if let Ok(cookie) = format!(
                "localbrain-desktop={}; HttpOnly; Path=/; SameSite=Lax",
                boundary.token
            )
            .parse()
            {
                response.headers_mut().insert("set-cookie", cookie);
            }
            response
                .headers_mut()
                .insert("cache-control", "no-store, private".parse().unwrap());
            response
                .headers_mut()
                .insert("referrer-policy", "no-referrer".parse().unwrap());
            return response;
        }
    }
    let mut response = next.run(request).await;
    if boundary.config.desktop {
        let port = context
            .authority
            .rsplit(':')
            .next()
            .filter(|s| s.bytes().all(|b| b.is_ascii_digit()))
            .unwrap_or("80");
        let csp=format!("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self' ipc: http://ipc.localhost ws://127.0.0.1:{port}; object-src 'none'; base-uri 'self'; frame-ancestors 'none'");
        if let Ok(csp) = csp.parse() {
            response
                .headers_mut()
                .insert("content-security-policy", csp);
        }
    }
    response
        .headers_mut()
        .insert("x-content-type-options", "nosniff".parse().unwrap());
    response
        .headers_mut()
        .insert("referrer-policy", "same-origin".parse().unwrap());
    if !context.path.starts_with("/static/") {
        response
            .headers_mut()
            .insert("cache-control", "no-store, private".parse().unwrap());
    }
    response
}
