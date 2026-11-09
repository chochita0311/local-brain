from urllib.parse import urlencode
from fastapi import Query, Request
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from localbrain.app.edition import DESKTOP
from localbrain.foundation.preferences import effective_preferences
from localbrain.app.templating import templates


def dashboard(request: Request):
    if DESKTOP:
        values = effective_preferences()
        return RedirectResponse("/" + values["startup_screen"] if values["onboarding_completed"] else "/onboarding", status_code=303)
    from localbrain.learning.web import render_home
    return render_home(request, templates)


def desktop_legacy_search(q: str = Query(default="", max_length=300)):
    return RedirectResponse("/natural-search?" + urlencode({"q": q}), status_code=303)


def health():
    return {"status": "ok", "edition": "desktop" if DESKTOP else "web"}
