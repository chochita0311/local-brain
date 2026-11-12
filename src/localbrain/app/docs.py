"""Bundled user guides, independent of personal sources and the checkout."""
from localbrain.foundation.paths import package_root

from dataclasses import dataclass, replace

from fastapi import Request
from fastapi.responses import HTMLResponse

from localbrain.rendering.markdown import render_markdown


CONTENT_ROOT = package_root() / "content" / "docs"


@dataclass(frozen=True)
class Guide:
    slug: str
    title: str
    description: str

    @property
    def href(self):
        return "/help" + ("/" + self.slug if self.slug else "")

    @property
    def filename(self):
        return (self.slug or "getting-started") + ".md"


GUIDES = (
    Guide("", "Getting started", "Install LocalBrain, connect sources, and start exploring."),
    Guide("settings", "Settings", "Know what each setting changes, where it applies, and when it takes effect."),
    Guide("sessions-dashboard", "Sessions Dashboard", "Read usage, estimated costs, and activity over time."),
    Guide("sessions", "Sessions", "Browse conversations, manage pins, and explore recorded activity."),
    Guide("local-contexts", "Local Contexts", "Browse registered document sources and read their contents."),
    Guide("search", "Search", "Find keywords or search by meaning with an optional local model."),
)
GUIDES_BY_SLUG = {guide.slug: guide for guide in GUIDES}
TERMINAL_GUIDE = Guide("terminal", "Terminal", "Run shells in tabs and panes, or keep them in the background.")
APP_DOC_ROUTES = frozenset(guide.href for guide in GUIDES) | {
    "/settings", "/sessions-dashboard", "/sessions", "/projects", "/context", "/natural-search",
    "/terminal", "/help/terminal",
}

KOREAN_GUIDES = (
    ("시작하기", "설치 후 소스를 연결하고 첫 자료를 찾아보세요."),
    ("설정", "소스·검색·동기화·저장공간 설정을 확인하세요."),
    ("세션 대시보드", "사용량과 예상 비용, 기간별 활동을 살펴보세요."),
    ("세션", "대화를 읽고 핀과 활동 차트를 사용하세요."),
    ("로컬 문서", "등록한 폴더·파일·메모를 찾아 읽으세요."),
    ("검색", "키워드로 찾고, 필요하면 로컬 AI 검색을 준비하세요."),
)


def install_routes(app, templates):
    def render_guide(request: Request, slug: str):
        language = request.query_params.get("lang", "ko")
        if language not in {"ko", "en"}:
            language = "ko"
        guides = GUIDES if language == "en" else tuple(
            replace(guide, title=title, description=description)
            for guide, (title, description) in zip(GUIDES, KOREAN_GUIDES)
        )
        terminal_available = "terminal" in getattr(app.state, "feature_packages", ())
        if terminal_available:
            guides += (TERMINAL_GUIDE if language == "en" else replace(
                TERMINAL_GUIDE, title="터미널", description="탭·분할에서 셸을 실행하고 백그라운드 작업을 관리하세요."),)
        guide = next((item for item in guides if item.slug == slug), None)
        english = language == "en"
        def href(item):
            return item.href + "?lang=" + language
        body = None
        error = None
        status = 200
        previous = following = None
        if guide is None:
            error = ("This guide could not be found. Choose a topic from the contents." if english
                     else "설명서를 찾을 수 없습니다. 목차에서 항목을 선택해 주세요.")
            status = 404
        else:
            index = guides.index(guide)
            previous = guides[index - 1] if index else None
            following = guides[index + 1] if index + 1 < len(guides) else None
            try:
                folder = CONTENT_ROOT if english else CONTENT_ROOT / "ko"
                source = (folder / guide.filename).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                error = ("This guide is unavailable. Choose another topic or try again." if english
                         else "설명서를 불러오지 못했습니다. 다른 항목을 선택하거나 다시 시도해 주세요.")
                status = 503
            else:
                routes = APP_DOC_ROUTES if terminal_available else APP_DOC_ROUTES - {"/terminal", "/help/terminal"}
                body = render_markdown(source, app_doc_routes=routes, app_doc_language=language)
                if not str(body.html).strip():
                    error = ("This guide is unavailable. Choose another topic." if english
                             else "설명서 내용이 없습니다. 다른 항목을 선택해 주세요.")
                    status = 503
        return templates.TemplateResponse(request, "app-docs.html", {
            "active_page": "docs", "guides": guides, "guide": guide,
            "doc_language": language, "guide_href": href,
            "body": body, "guide_error": error,
            "previous_guide": previous, "next_guide": following,
        }, status_code=status)

    @app.get("/help", response_class=HTMLResponse)
    def getting_started(request: Request):
        return render_guide(request, "")

    @app.get("/help/{slug}", response_class=HTMLResponse)
    def guide_page(request: Request, slug: str):
        return render_guide(request, slug)
