use super::{bind, Params, EMPTY};
use crate::{state::AppState, transport::RequestContext};
use axum::{response::Response, routing::MethodFilter, Router};
use localbrain_core::backend::{
    rendering::{render_markdown, MarkdownOptions},
    Result,
};
use serde_json::{json, Value};
use std::collections::BTreeSet;
const GUIDES: [(&str, &str, &str, &str, &str); 6] = [
    (
        "",
        "Getting started",
        "Install LocalBrain, connect sources, and start exploring.",
        "시작하기",
        "설치 후 소스를 연결하고 첫 자료를 찾아보세요.",
    ),
    (
        "settings",
        "Settings",
        "Know what each setting changes, where it applies, and when it takes effect.",
        "설정",
        "소스·검색·동기화·저장공간 설정을 확인하세요.",
    ),
    (
        "sessions-dashboard",
        "Sessions Dashboard",
        "Read usage, estimated costs, and activity over time.",
        "세션 대시보드",
        "사용량과 예상 비용, 기간별 활동을 살펴보세요.",
    ),
    (
        "sessions",
        "Sessions",
        "Browse conversations, manage pins, and explore recorded activity.",
        "세션",
        "대화를 읽고 핀과 활동 차트를 사용하세요.",
    ),
    (
        "local-contexts",
        "Local Contexts",
        "Browse registered document sources and read their contents.",
        "로컬 문서",
        "등록한 폴더·파일·메모를 찾아 읽으세요.",
    ),
    (
        "search",
        "Search",
        "Find keywords or search by meaning with an optional local model.",
        "검색",
        "키워드로 찾고, 필요하면 로컬 AI 검색을 준비하세요.",
    ),
];
fn guide(slug: &str, title: &str, description: &str) -> Value {
    json!({"slug":slug,"title":title,"description":description,"href":if slug.is_empty(){"/help".into()}else{format!("/help/{slug}")}})
}
fn page(state: &AppState, request: &RequestContext, params: &Params, _: &[u8]) -> Result<Response> {
    let lang = if request.parameter("lang") == "en" {
        "en"
    } else {
        "ko"
    };
    let english = lang == "en";
    let slug = params.get("slug").map(String::as_str).unwrap_or("");
    let mut guides = GUIDES
        .iter()
        .map(|&(slug, en, description, ko, ko_description)| {
            guide(
                slug,
                if english { en } else { ko },
                if english { description } else { ko_description },
            )
        })
        .collect::<Vec<_>>();
    if state.config.feature("terminal") {
        guides.push(guide(
            "terminal",
            if english { "Terminal" } else { "터미널" },
            if english {
                "Run shells in tabs and panes, or keep them in the background."
            } else {
                "탭·분할에서 셸을 실행하고 백그라운드 작업을 관리하세요."
            },
        ));
    }
    let index = guides.iter().position(|item| item["slug"] == slug);
    let mut error = None;
    let mut status = 200;
    let mut body = Value::Null;
    if index.is_none() {
        status = 404;
        error = Some(if english {
            "This guide could not be found. Choose a topic from the contents."
        } else {
            "설명서를 찾을 수 없습니다. 목차에서 항목을 선택해 주세요."
        });
    } else {
        let folder = state.config.web_root.join("content/docs");
        let folder = if english { folder } else { folder.join("ko") };
        let filename = if slug.is_empty() {
            "getting-started"
        } else {
            slug
        };
        match std::fs::read_to_string(folder.join(format!("{filename}.md"))) {
            Err(_) => {
                status = 503;
                error = Some(if english {
                    "This guide is unavailable. Choose another topic or try again."
                } else {
                    "설명서를 불러오지 못했습니다. 다른 항목을 선택하거나 다시 시도해 주세요."
                });
            }
            Ok(source) => {
                let mut routes = [
                    "/help",
                    "/help/settings",
                    "/help/sessions-dashboard",
                    "/help/sessions",
                    "/help/local-contexts",
                    "/help/search",
                    "/settings",
                    "/sessions-dashboard",
                    "/sessions",
                    "/projects",
                    "/context",
                    "/natural-search",
                ]
                .into_iter()
                .map(String::from)
                .collect::<BTreeSet<_>>();
                if state.config.feature("terminal") {
                    routes.extend(["/terminal".into(), "/help/terminal".into()]);
                }
                let rendered = render_markdown(
                    &source,
                    &MarkdownOptions {
                        app_doc_routes: routes,
                        app_doc_language: Some(lang),
                        ..Default::default()
                    },
                );
                if rendered.html.trim().is_empty() {
                    status = 503;
                    error = Some(if english {
                        "This guide is unavailable. Choose another topic."
                    } else {
                        "설명서 내용이 없습니다. 다른 항목을 선택해 주세요."
                    });
                }
                body = serde_json::to_value(rendered)?;
            }
        }
    }
    let current = index.map(|index| guides[index].clone());
    let previous = index.and_then(|index| index.checked_sub(1).map(|index| guides[index].clone()));
    let next = index.and_then(|index| guides.get(index + 1).cloned());
    state.render(request,"app-docs.html",json!({"active_page":"docs","guides":guides,"guide":current,"doc_language":lang,"body":body,"guide_error":error,"previous_guide":previous,"next_guide":next}),status)
}
pub fn install(router: Router<AppState>) -> Router<AppState> {
    bind(
        bind(router, "/help", MethodFilter::GET, page, EMPTY),
        "/help/{slug}",
        MethodFilter::GET,
        page,
        EMPTY,
    )
}
