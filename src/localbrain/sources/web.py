import json
import time
from typing import Optional
from urllib.parse import urlencode
from fastapi import Query, Request
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from localbrain.foundation.config import settings
from localbrain.persistence.db import connect
from localbrain.ingest.scanner import scan_all
from localbrain.sources.queries import source_inventory
from localbrain.app.templating import templates


def sync_sessions_page(
    request: Request,
    view: str = Query(default="sessions"),
    source: str = Query(default="all"),
    workspace: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    display: str = Query(default="list"),
):
    request.app.state.session_sync.request()
    params = {"source": source, "display": display, "page": page}
    if isinstance(workspace, int):
        params["workspace"] = workspace
    return RedirectResponse(("/projects?" if view == "projects" else "/sessions?") + urlencode(params), status_code=303)


def sources_page(request: Request):
    with connect() as connection:
        sources = source_inventory(connection)
    return templates.TemplateResponse(
        "sources.html",
        {
            "request": request,
            "active_page": "sources",
            "sources": sources,
            "database_path": str(settings.database_path),
            "sync_outcome": request.query_params.get("sync")
            if request.query_params.get("sync") in {"complete", "partial", "failed"}
            else None,
        },
    )


def scan_sources_page():
    report = scan_all()
    outcome = report.get("outcome")
    if outcome not in {"complete", "partial", "failed"}:
        outcome = "failed"
    return RedirectResponse(
        url="/sources?{}".format(urlencode({"sync": outcome})),
        status_code=303,
    )


def scan_sources():
    return {"ok": True, "report": scan_all()}


def sync_session_sources(request: Request):
    return {"ok": True, "state": request.app.state.session_sync.request()}


def session_sync_status(request: Request):
    return request.app.state.session_sync.status()


def stream_session_sources(request: Request):
    service = request.app.state.session_sync
    service.request()
    return StreamingResponse(_session_sync_event_stream(service), media_type="application/x-ndjson")


def _session_sync_event_stream(service):
    while True:
        state = service.status()
        if not state["running"] and not state["queued"]:
            yield json.dumps({"type": "result", "ok": not bool(state.get("error")),
                              "report": state.get("report", {}), "state": state}) + "\n"
            break
        if state.get("progress"):
            yield json.dumps(state["progress"]) + "\n"
        time.sleep(1)
