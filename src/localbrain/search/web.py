from typing import Optional
from urllib.parse import urlencode
from fastapi import HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from localbrain.app.edition import DESKTOP
from localbrain.atlassian.browse import (
    AtlassianBrowseError,
    browse_inventory,
    normalize_browse_filters,
)
from localbrain.persistence.db import connect
from localbrain.search.legacy import search
from localbrain.app.templating import templates


def search_page(
    request: Request,
    q: str = Query(default="", max_length=300),
    source: str = Query(default="all"),
    service: Optional[str] = Query(default=None),
    source_instance_id: Optional[int] = Query(default=None, ge=1),
    site_id: Optional[int] = Query(default=None, ge=1),
    space_id: Optional[int] = Query(default=None, ge=1),
    item_type: Optional[str] = Query(default=None),
    coverage: Optional[str] = Query(default=None),
    freshness: Optional[str] = Query(default=None),
    attention: Optional[str] = Query(default=None),
    topic_id: Optional[int] = Query(default=None, ge=1),
    tag_id: Optional[int] = Query(default=None, ge=1),
    workstream_id: Optional[int] = Query(default=None, ge=1),
):
    """Deprecated keyword-search entry point retained for existing URLs."""
    if DESKTOP:
        return RedirectResponse("/natural-search?" + urlencode({"q": q, "mode": "keyword"}), status_code=303)
    selected_source = (
        source if source in {"all", "sessions", "documents", "atlassian"} else "all"
    )
    filter_values = {
        "service": service,
        "source_instance_id": source_instance_id,
        "site_id": site_id,
        "space_id": space_id,
        "item_type": item_type,
        "coverage": coverage,
        "freshness": freshness,
        "attention": attention,
        "topic_id": topic_id,
        "tag_id": tag_id,
        "workstream_id": workstream_id,
    }
    with connect() as connection:
        try:
            filters = normalize_browse_filters(filter_values)
            results = (
                search(
                    connection,
                    q,
                    source_scope=selected_source,
                    atlassian_filters=filters,
                )
                if q.strip()
                else []
            )
            search_options = browse_inventory(connection)["options"]
        except AtlassianBrowseError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request, "search.html",
        {
            "request": request,
            "active_page": "search",
            "query": q,
            "results": results,
            "selected_source": selected_source,
            "filters": filters,
            "search_options": search_options,
        },
    )
