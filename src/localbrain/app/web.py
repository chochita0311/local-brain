from fastapi import Request
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from localbrain.app.edition import DESKTOP
from localbrain.foundation.preferences import effective_preferences
from localbrain.learning.web import render_home
from localbrain.app.templating import templates


def dashboard(request: Request):
    if DESKTOP:
        values = effective_preferences()
        return RedirectResponse("/" + values["startup_screen"] if values["onboarding_completed"] else "/onboarding", status_code=303)
    return render_home(request, templates)


def health():
    return {"status": "ok", "edition": "desktop" if DESKTOP else "web"}
