from typing import Optional
from fastapi import Query, Request
from fastapi.responses import (
    HTMLResponse,
)
from localbrain.foundation.preferences import effective_preferences
from localbrain.persistence.db import connect
from localbrain.usage.queries import usage_dashboard_data
from localbrain.app.templating import templates


def sessions_dashboard(
    request: Request,
    view: str = Query(default="daily"),
    source: str = Query(default="all"),
    metric: str = Query(default="cost"),
    breakdown: str = Query(default="source"),
    from_date: Optional[str] = Query(default=None, alias="from"),
    to_date: Optional[str] = Query(default=None, alias="to"),
):
    with connect() as connection:
        usage = usage_dashboard_data(
            connection,
            view=view,
            source=source,
            metric=metric,
            breakdown=breakdown,
            from_value=from_date,
            to_value=to_date,
            timezone_name=effective_preferences()["timezone"],
            visible_only=True,
        )
        page_context = {
            "request": request,
            "active_page": "sessions-dashboard",
            "usage": usage,
        }
    return templates.TemplateResponse(request, "sessions_dashboard.html", page_context)
