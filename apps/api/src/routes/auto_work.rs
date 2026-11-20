use super::{bind, BodyLimit, Params, EMPTY};
use crate::{
    state::AppState,
    transport::{self, RequestContext},
};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    auto_work::{self, PreviewOptions},
    BackendError, Result,
};
use serde_json::json;
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
fn page(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    local(request)?;
    if request.parameter("mode") != "sample" {
        return state.render(request,"affinity-map.html",json!({"active_page":"auto-work","mapview":auto_work::affinity_page(&state.config,&request.query,None)}),200);
    }
    let notice = match request.parameter("notice") {
        "updated" => Some("현재 데이터로 분석 결과를 갱신했습니다. 분류 품질은 아직 미평가입니다."),
        "failed" => Some(
            "분석을 완료하지 못했습니다. 유효한 이전 결과는 유지됩니다. 다시 시도할 수 있습니다.",
        ),
        "busy" => Some("이미 분석 중입니다. 잠시 후 이 화면을 새로고침해 주세요."),
        _ => None,
    };
    let options = PreviewOptions {
        page: request
            .query
            .get("page")
            .cloned()
            .unwrap_or_else(|| "1".into()),
        flow: request.query.get("flow").cloned(),
        view: request
            .query
            .get("view")
            .cloned()
            .unwrap_or_else(|| "flows".into()),
        evidence_page: request
            .query
            .get("evidence_page")
            .cloned()
            .unwrap_or_else(|| "1".into()),
    };
    state.render(request,"auto-work.html",json!({"active_page":"auto-work","preview":auto_work::preview_page(&state.config,&options,None),"notice":notice,"notice_failed":request.parameter("notice")=="failed"}),200)
}
fn refresh(state: &AppState, request: &RequestContext, _: &Params, _: &[u8]) -> Result<Response> {
    local(request)?;
    if !request.same_origin() {
        return Err(BackendError::invalid(
            "origin",
            "Same-origin submission required",
        ));
    }
    let notice = match auto_work::prepare_preview(&state.config, None) {
        Ok(()) => "updated",
        Err(error) if ["PREVIEW_BUSY", "BUSY"].contains(&error.code.as_str()) => "busy",
        Err(_) => "failed",
    };
    Ok(transport::redirect(&format!(
        "/auto-work?mode=sample&notice={notice}"
    )))
}
pub fn install(router: Router<AppState>) -> Router<AppState> {
    let router = bind(router, "/auto-work", MethodFilter::GET, page, EMPTY);
    bind(
        router,
        "/auto-work/refresh",
        MethodFilter::POST,
        refresh,
        BodyLimit {
            status: 400,
            bytes: 0,
            message: "This action takes no input",
        },
    )
}
