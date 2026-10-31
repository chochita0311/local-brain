from typing import Optional
from fastapi import Query, Request
from fastapi.responses import (
    HTMLResponse,
)
from localbrain.persistence.explorer import schema_explorer_page_data
from localbrain.app.templating import templates


def schema_page(
    request: Request,
    area: Optional[str] = Query(default=None),
    table: Optional[str] = Query(default=None),
):
    return templates.TemplateResponse(
        "schema.html",
        {
            "request": request,
            "active_page": "schema",
            "schema_view": schema_explorer_page_data(area=area, table=table),
        },
    )
