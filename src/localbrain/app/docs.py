"""Bundled user guides, independent of personal sources and the checkout."""
from localbrain.foundation.paths import package_root

from dataclasses import dataclass
from pathlib import Path

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
    Guide("search", "Search", "Find keywords, search by meaning, or ask your documents with a local model."),
)
GUIDES_BY_SLUG = {guide.slug: guide for guide in GUIDES}
APP_DOC_ROUTES = frozenset(guide.href for guide in GUIDES) | {
    "/settings", "/sessions-dashboard", "/sessions", "/projects", "/context", "/context-search", "/natural-search",
}


def install_routes(app, templates):
    def render_guide(request: Request, slug: str):
        guide = GUIDES_BY_SLUG.get(slug)
        body = None
        error = None
        status = 200
        previous = following = None
        if guide is None:
            error = "This guide could not be found. Choose a topic from the contents."
            status = 404
        else:
            index = GUIDES.index(guide)
            previous = GUIDES[index - 1] if index else None
            following = GUIDES[index + 1] if index + 1 < len(GUIDES) else None
            try:
                source = (CONTENT_ROOT / guide.filename).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                error = "This guide is unavailable. Choose another topic or try again."
                status = 503
            else:
                body = render_markdown(source, app_doc_routes=APP_DOC_ROUTES)
                if not str(body.html).strip():
                    error = "This guide is unavailable. Choose another topic."
                    status = 503
        return templates.TemplateResponse(request, "app-docs.html", {
            "active_page": "docs", "guides": GUIDES, "guide": guide,
            "body": body, "guide_error": error,
            "previous_guide": previous, "next_guide": following,
        }, status_code=status)

    @app.get("/help", response_class=HTMLResponse)
    def getting_started(request: Request):
        return render_guide(request, "")

    @app.get("/help/{slug}", response_class=HTMLResponse)
    def guide_page(request: Request, slug: str):
        return render_guide(request, slug)
