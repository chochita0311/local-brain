"""The distributed product boundary is selected by the executable, never TOML."""

import hmac
import os
import re
import sys
from urllib.parse import urlsplit

from fastapi.responses import JSONResponse, RedirectResponse


DESKTOP = bool(getattr(sys, "frozen", False)) or os.environ.get("LOCALBRAIN_EDITION") == "desktop"
_ALLOWED = re.compile(
    r"^/(?:$|static/.*|desktop/(?:start|shutdown)|settings|onboarding|"
    r"help(?:/(?:settings|sessions-dashboard|sessions|local-contexts|search))?|"
    r"sessions-dashboard|projects|sessions(?:/\d+(?:/(?:pin|unpin|chart-activity)|/(?:subsessions|subagents)/[^/]+)?|/chart/project-visibility|/sync)?|"
    r"context(?:/.*)?|context-search|documents/\d+|natural-search(?:/.*)?|search|"
    r"api/(?:health|settings(?:/.*)?|sessions(?:/.*)?|session-chart(?:/.*)?|"
    r"context-(?:roots|files|sources)(?:/.*)?|context-search/(?:status|answer|unload)|natural-search/status))$"
)


def _error_response(detail, status_code):
    # WKWebView may otherwise guess a legacy encoding when showing raw JSON.
    return JSONResponse(
        {"detail": detail}, status_code=status_code,
        media_type="application/json; charset=utf-8",
        headers={"Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff"},
    )


def install_boundary(app, config):
    @app.middleware("http")
    async def local_boundary(request, call_next):
        path = request.url.path
        if request.url.hostname not in {"localhost", "127.0.0.1", "::1"}:
            return _error_response("Local access required", 403)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if request.headers.get("sec-fetch-site") == "cross-site" or (
                origin and urlsplit(origin).netloc != request.url.netloc
            ):
                return _error_response("같은 앱 화면에서 요청해 주세요.", 403)
        if DESKTOP:
            if request.url.hostname != "127.0.0.1":
                return _error_response("Local access required", 403)
            if not _ALLOWED.fullmatch(path) or any(part in path.split("/") for part in ("workflow", "insights", "runs")):
                return _error_response("이 앱에서 제공하지 않는 기능입니다.", 404)
            token = os.environ.get("LOCALBRAIN_DESKTOP_TOKEN", "")
            supplied = request.cookies.get("localbrain-desktop", "")
            if request.headers.get("authorization", "").startswith("Bearer "):
                supplied = request.headers["authorization"][7:]
            if path == "/desktop/start":
                supplied = request.query_params.get("token", "")
            if not token or not hmac.compare_digest(token, supplied):
                return _error_response("앱 창에서 열어 주세요.", 401)
            if path == "/desktop/start":
                from .preferences import effective_preferences, PreferencesError
                try:
                    values = effective_preferences(config)
                    target = "/" + values["startup_screen"] if values["onboarding_completed"] else "/onboarding"
                except PreferencesError:
                    target = "/settings"
                response = RedirectResponse(target, status_code=303)
                # The initial top-level navigation comes from tauri://localhost.
                # Strict drops this cookie on WKWebView's redirect to the app.
                # Lax admits that GET; the token and origin checks still guard writes.
                response.set_cookie("localbrain-desktop", token, httponly=True, samesite="lax")
                response.headers["Cache-Control"] = "no-store, private"
                response.headers["Referrer-Policy"] = "no-referrer"
                return response
        response = await call_next(request)
        if DESKTOP:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; font-src 'self' data:; connect-src 'self' ipc: http://ipc.localhost; "
                "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if not path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store, private"
        return response


def desktop_related_context(view):
    if not DESKTOP or not view or view.get("state") == "error":
        return view
    groups = []
    for group in view.get("groups", []):
        if group.get("key") == "organization":
            continue
        items = []
        for item in group.get("items", []):
            href = item.get("href") or ""
            if item.get("entity_type") == "atlassian" or href.startswith(("/atlassian", "/workstreams", "/local-resources")):
                continue
            items.append({**item, "organization": []})
        if items:
            groups.append({**group, "items": items})
    return {**view, "groups": groups, "state": view.get("state") if groups else "empty"}
