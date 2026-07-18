import json
import sqlite3
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlencode

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .config import settings
from .contexts import (
    add_apple_notes_source,
    add_context_file,
    add_context_root,
    context_source_tree,
    list_context_sources,
    remove_context_root,
)
from .db import connect, init_db, transaction
from .ingest.scanner import scan_all, scan_context_root, scan_session_sources
from .queries import (
    dashboard_stats,
    document_detail,
    project_activity,
    recent_documents,
    search,
    session_conversation_events,
    session_inventory_page,
    session_detail,
    session_parent,
    session_subsessions,
    source_inventory,
)
from .runner import (
    cancel_run,
    get_run,
    list_runs,
    prepare_run,
    read_run_output,
    reconcile_interrupted_runs,
    runner_executable,
    shutdown_runs,
    start_run,
    task_choices,
)
from .subagents import list_subagents, load_subagent
from .usage_queries import usage_dashboard_data
from .workstreams import (
    add_link,
    create_checkpoint,
    create_external_resource,
    create_local_resource,
    create_thread,
    create_workstream,
    dashboard_overview,
    entity_memberships,
    generate_suggestions,
    get_workstream,
    list_workstreams,
    local_resource_detail,
    picker_resources,
    remove_link,
    resolve_suggestion,
    update_thread,
    update_workstream,
    utc_now,
)


PACKAGE_ROOT = Path(__file__).resolve().parent


class WorkstreamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    summary: Optional[str] = Field(default=None, max_length=2000)


class WorkstreamUpdate(WorkstreamCreate):
    status: str = Field(max_length=32)


class ThreadCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    summary: Optional[str] = Field(default=None, max_length=2000)
    current_goal: Optional[str] = Field(default=None, max_length=2000)
    next_action: Optional[str] = Field(default=None, max_length=2000)


class ThreadUpdate(ThreadCreate):
    status: str = Field(max_length=32)


class CheckpointCreate(BaseModel):
    current_goal: Optional[str] = Field(default=None, max_length=4000)
    confirmed_facts: Optional[str] = Field(default=None, max_length=12000)
    recent_decisions: Optional[str] = Field(default=None, max_length=12000)
    open_questions: Optional[str] = Field(default=None, max_length=12000)
    next_actions: Optional[str] = Field(default=None, max_length=12000)
    files_to_open: Optional[str] = Field(default=None, max_length=12000)


class LinkCreate(BaseModel):
    scope_type: str
    scope_id: int
    entity_type: str
    entity_id: str
    relation_type: str = Field(default="related-to", min_length=1, max_length=80)


class ExternalResourceCreate(BaseModel):
    resource_type: str
    title: str = Field(min_length=1, max_length=240)
    url: str = Field(min_length=1, max_length=2000)
    summary: Optional[str] = Field(default=None, max_length=4000)
    source_role: Optional[str] = Field(default=None, max_length=160)
    scope_type: str
    scope_id: int
    relation_type: str = Field(default="reference", min_length=1, max_length=80)


class LocalResourceCreate(BaseModel):
    path: str = Field(min_length=1, max_length=4000)
    title: Optional[str] = Field(default=None, max_length=240)
    summary: Optional[str] = Field(default=None, max_length=4000)
    scope_type: str
    scope_id: int
    relation_type: str = Field(default="reference", min_length=1, max_length=80)


class MaintenanceRunCreate(BaseModel):
    workstream_id: Optional[int] = None


class TaskRunCreate(BaseModel):
    task_type: str = Field(default="organize_resources", max_length=80)
    instruction: Optional[str] = Field(default=None, max_length=4000)
    refresh_suggestions: bool = False


class ContextRootCreate(BaseModel):
    path: str = Field(min_length=1, max_length=4000)


class ContextFileCreate(BaseModel):
    path: str = Field(min_length=1, max_length=4000)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    reconcile_interrupted_runs()
    try:
        yield
    finally:
        await shutdown_runs()


app = FastAPI(title="LocalBrain", version="0.2.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates")
templates.env.globals["asset_version"] = max(
    path.stat().st_mtime_ns
    for path in (PACKAGE_ROOT / "static").iterdir()
    if path.is_file()
)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    with connect() as connection:
        overview = dashboard_overview(connection)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "active_page": "dashboard",
            **overview,
        },
    )


@app.get("/sessions-dashboard", response_class=HTMLResponse)
def sessions_dashboard(
    request: Request,
    view: str = Query(default="daily"),
    source: str = Query(default="all"),
    metric: str = Query(default="tokens"),
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
            timezone_name=settings.timezone_name,
        )
        page_context = {
            "request": request,
            "active_page": "sessions-dashboard",
            "usage": usage,
        }
    return templates.TemplateResponse("sessions_dashboard.html", page_context)


@app.get("/workstreams", response_class=HTMLResponse)
def workstreams_page(request: Request):
    with connect() as connection:
        items = list_workstreams(connection)
    return templates.TemplateResponse(
        "workstreams.html",
        {
            "request": request,
            "active_page": "workstreams",
            "workstreams": items,
        },
    )


@app.get("/workstreams/{workstream_id}", response_class=HTMLResponse)
def show_workstream(request: Request, workstream_id: int):
    with connect() as connection:
        workstream = get_workstream(connection, workstream_id)
        if not workstream:
            raise HTTPException(status_code=404, detail="Workstream not found")
        resources = picker_resources(connection)
        runs = list_runs(connection, workstream_id)
    return templates.TemplateResponse(
        "workstream.html",
        {
            "request": request,
            "active_page": "workstreams",
            "workstream": workstream,
            "resources": resources,
            "runs": runs,
            "task_choices": task_choices(),
            "runner_available": bool(runner_executable()),
            "runner_cwd": str(Path.home()),
            "runner_mcp_budget": settings.mcp_call_budget,
        },
    )


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def show_run(request: Request, run_id: str):
    with connect() as connection:
        run = get_run(connection, run_id)
        if not run or not run["task_type"]:
            raise HTTPException(status_code=404, detail="Run not found")
        output = read_run_output(run)
        try:
            manifest = json.loads(run["source_snapshot_json"] or "{}")
            candidate_counts = manifest.get("retrieval", {}).get("counts", {})
        except json.JSONDecodeError:
            candidate_counts = {}
    return templates.TemplateResponse(
        "run.html",
        {
            "request": request,
            "active_page": "workstreams",
            "run": run,
            "output": output,
            "candidate_counts": candidate_counts,
        },
    )


@app.get("/sessions", response_class=HTMLResponse)
def sessions_page(
    request: Request,
    source: str = Query(default="all"),
    workspace: Optional[int] = Query(default=None),
    page: str = Query(default="1"),
):
    selected_source = source if source in {"claude", "codex"} else None
    try:
        requested_page = int(page)
        page_is_valid = requested_page > 0
    except (TypeError, ValueError):
        requested_page = 1
        page_is_valid = False
    with connect() as connection:
        projects = project_activity(connection)
        pagination = session_inventory_page(
            connection, selected_source, workspace, requested_page
        )
        if request.query_params.get("page") is not None and (
            not page_is_valid or requested_page != pagination["page"]
        ):
            params = {"page": pagination["page"]}
            if selected_source:
                params["source"] = selected_source
            if workspace is not None:
                params["workspace"] = workspace
            return RedirectResponse(
                url="/sessions?{}".format(urlencode(params)), status_code=303
            )
        page_context = {
            "request": request,
            "active_page": "sessions",
            "selected_inventory": "sessions",
            "page_title": "Sessions",
            "selected_source": selected_source or "all",
            "selected_workspace": workspace,
            "stats": dashboard_stats(connection),
            "sessions": pagination["items"],
            "pagination": pagination,
            "documents": recent_documents(connection),
            "sources": source_inventory(connection),
            "projects": projects,
            "project_count": len(projects),
            "missing_count": sum(
                1 for project in projects if not project["exists_now"]
            ),
        }
    return templates.TemplateResponse("sessions.html", page_context)


@app.get("/context", response_class=HTMLResponse)
def context_page(
    request: Request,
    root: Optional[int] = Query(default=None),
    document: Optional[int] = Query(default=None),
):
    with connect() as connection:
        sources = list_context_sources(connection)
        folders = [
            item for item in sources
            if item["source_type"] in {"folder", "apple_notes"}
        ]
        files = [item for item in sources if item["source_type"] == "file"]
        selected_source = next(
            (item for item in sources if item["id"] == root), None
        )
        if selected_source is None and sources:
            selected_source = sources[0]
        tree = (
            context_source_tree(connection, selected_source["id"])
            if selected_source else []
        )
        selected_document = document_detail(connection, document) if document else None
        if (
            selected_document
            and selected_source
            and selected_document["context_root_id"] != selected_source["id"]
        ):
            selected_document = None
        if selected_source and selected_source["source_type"] == "file" and not selected_document:
            first_document = connection.execute(
                "SELECT id FROM context_documents WHERE context_root_id = ? LIMIT 1",
                (selected_source["id"],),
            ).fetchone()
            if first_document:
                selected_document = document_detail(connection, first_document["id"])
    return templates.TemplateResponse(
        "context.html",
        {
            "request": request,
            "active_page": "context",
            "selected_source": selected_source,
            "selected_document": selected_document,
            "tree": tree,
            "folders": folders,
            "files": files,
            "has_apple_notes": any(
                item["source_type"] == "apple_notes" for item in folders
            ),
            "document_count": sum(item["document_count"] for item in sources),
            "source_count": len(sources),
            "total_bytes": sum(item["total_bytes"] or 0 for item in sources),
        },
    )


@app.get("/atlassian", response_class=HTMLResponse)
def atlassian_page(
    request: Request, view: str = Query(default="jira")
):
    selected_view = view if view in {"jira", "confluence"} else "jira"
    return templates.TemplateResponse(
        "atlassian.html",
        {
            "request": request,
            "active_page": "atlassian",
            "selected_view": selected_view,
        },
    )


@app.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request):
    with connect() as connection:
        projects = project_activity(connection)
        pagination = session_inventory_page(connection)
        page_context = {
            "request": request,
            "active_page": "sessions",
            "selected_inventory": "projects",
            "page_title": "Projects",
            "selected_source": "all",
            "selected_workspace": None,
            "stats": dashboard_stats(connection),
            "sessions": pagination["items"],
            "pagination": pagination,
            "documents": recent_documents(connection),
            "sources": source_inventory(connection),
            "projects": projects,
            "project_count": len(projects),
            "missing_count": sum(
                1 for project in projects if not project["exists_now"]
            ),
        }
    return templates.TemplateResponse(
        "sessions.html",
        page_context,
    )


@app.post("/sessions/sync")
def sync_sessions_page(
    view: str = Query(default="sessions"),
    source: str = Query(default="all"),
    workspace: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
):
    scan_session_sources()
    if view == "projects":
        return RedirectResponse(url="/projects", status_code=303)
    params = {}
    if source in {"claude", "codex"}:
        params["source"] = source
    if workspace is not None:
        params["workspace"] = workspace
    if page > 1:
        params["page"] = page
    destination = "/sessions"
    if params:
        destination += "?{}".format(urlencode(params))
    return RedirectResponse(url=destination, status_code=303)


@app.get("/sources", response_class=HTMLResponse)
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
        },
    )


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
def show_session(request: Request, session_id: int):
    with connect() as connection:
        session = session_detail(connection, session_id)
        if not session or session["session_class"] != "work":
            raise HTTPException(status_code=404, detail="Session not found")
        events = session_conversation_events(connection, session_id)
        parent = session_parent(connection, session_id)
        direct_children = session_subsessions(connection, session_id)
        memberships = entity_memberships(connection, "session", session_id)

    subagents = [
        {
            "url": "/sessions/{}".format(child["id"]),
            "source_kind": child["source_kind"],
            "external_id": child["external_id"],
            "title": child["title"],
            "event_count": child["event_count"],
            "last_event_at": child["last_event_at"],
            "source_path": child["source_path"],
        }
        for child in direct_children
    ]
    if session["session_role"] == "primary" and session["source_kind"] == "claude":
        normalized_paths = {item["source_path"] for item in subagents}
        normalized_external_ids = {item["external_id"] for item in subagents}
        for item in list_subagents(session["source_path"], session["external_id"]):
            if (
                item["source_path"] in normalized_paths
                or item["external_id"] in normalized_external_ids
            ):
                continue
            subagents.append(
                {
                    "url": "/sessions/{}/subagents/{}".format(
                        session_id, quote(item["file_name"])
                    ),
                    "source_kind": "claude",
                    "external_id": item["external_id"],
                    "title": item["title"],
                    "event_count": item["event_count"],
                    "last_event_at": item["last_event_at"],
                    "source_path": item["source_path"],
                }
            )
    return templates.TemplateResponse(
        "session.html",
        {
            "request": request,
            "active_page": "sessions",
            "session": session,
            "events": events,
            "parent": parent,
            "memberships": memberships,
            "subagents": subagents,
        },
    )


@app.get("/sessions/{session_id}/subagents/{file_name}", response_class=HTMLResponse)
def show_subagent(request: Request, session_id: int, file_name: str):
    with connect() as connection:
        session = session_detail(connection, session_id)
        if (
            not session
            or session["source_kind"] != "claude"
            or session["session_role"] != "primary"
        ):
            raise HTTPException(status_code=404, detail="Parent session not found")
        direct_children = session_subsessions(connection, session_id)
    subagent = load_subagent(session["source_path"], file_name)
    if not subagent or subagent.parent_external_id != session["external_id"]:
        raise HTTPException(status_code=404, detail="Subagent not found")
    normalized_child = next(
        (
            child
            for child in direct_children
            if child["source_path"] == subagent.source_path
            or child["external_id"] == subagent.external_id
        ),
        None,
    )
    if normalized_child:
        return RedirectResponse(
            url="/sessions/{}".format(normalized_child["id"]), status_code=303
        )
    conversation_events = sorted(
        (event for event in subagent.events if event.event_type == "message"),
        key=lambda event: event.sequence,
    )
    return templates.TemplateResponse(
        "subagent.html",
        {
            "request": request,
            "active_page": "sessions",
            "session": session,
            "subagent": subagent,
            "events": conversation_events,
            "event_count": len(subagent.events),
            "file_name": file_name,
        },
    )


@app.get("/documents/{document_id}", response_class=HTMLResponse)
def show_document(request: Request, document_id: int):
    with connect() as connection:
        document = document_detail(connection, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        memberships = entity_memberships(connection, "document", document_id)
    return templates.TemplateResponse(
        "document.html",
        {
            "request": request,
            "active_page": "context",
            "document": document,
            "memberships": memberships,
        },
    )


@app.get("/local-resources/{resource_id}", response_class=HTMLResponse)
def show_local_resource(request: Request, resource_id: int):
    with connect() as connection:
        resource = local_resource_detail(connection, resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Local resource not found")
        memberships = entity_memberships(connection, "local", resource_id)
    return templates.TemplateResponse(
        "local_resource.html",
        {
            "request": request,
            "active_page": "context",
            "resource": resource,
            "memberships": memberships,
        },
    )


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = Query(default="", max_length=300)):
    with connect() as connection:
        results = search(connection, q) if q.strip() else []
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "active_page": "search",
            "query": q,
            "results": results,
        },
    )


@app.post("/api/workstreams")
def api_create_workstream(payload: WorkstreamCreate):
    try:
        with transaction() as connection:
            workstream_id = create_workstream(connection, payload.name, payload.summary)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 이름의 Workstream이 있습니다.") from exc
    return {"ok": True, "id": workstream_id, "redirect": "/workstreams/{}".format(workstream_id)}


@app.post("/api/context-roots")
def api_add_context_root(payload: ContextRootCreate):
    try:
        with transaction() as connection:
            root_id = add_context_root(connection, payload.path)
            imported, skipped, failed = scan_context_root(
                connection, root_id, force=True
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "id": root_id,
        "report": {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        },
        "redirect": "/context?root={}".format(root_id),
    }


@app.post("/api/context-files")
def api_add_context_file(payload: ContextFileCreate):
    try:
        with transaction() as connection:
            source_id = add_context_file(connection, payload.path)
            imported, skipped, failed = scan_context_root(
                connection, source_id, force=True
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "id": source_id,
        "report": {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        },
        "redirect": "/context?root={}".format(source_id),
    }


@app.post("/api/context-sources/apple-notes")
def api_add_apple_notes_source():
    with transaction() as connection:
        source_id = add_apple_notes_source(connection)
        imported, skipped, failed = scan_context_root(
            connection, source_id, force=True
        )
    return {
        "ok": True,
        "id": source_id,
        "report": {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        },
        "redirect": "/context?root={}".format(source_id),
    }


@app.delete("/api/context-roots/{root_id}")
def api_remove_context_root(root_id: int):
    try:
        with transaction() as connection:
            remove_context_root(connection, root_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@app.delete("/api/context-sources/{source_id}")
def api_remove_context_source(source_id: int):
    return api_remove_context_root(source_id)


@app.put("/api/workstreams/{workstream_id}")
def api_update_workstream(workstream_id: int, payload: WorkstreamUpdate):
    try:
        with transaction() as connection:
            update_workstream(
                connection, workstream_id, payload.name, payload.status, payload.summary
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 이름의 Workstream이 있습니다.") from exc
    return {"ok": True}


@app.post("/api/workstreams/{workstream_id}/threads")
def api_create_thread(workstream_id: int, payload: ThreadCreate):
    try:
        with transaction() as connection:
            thread_id = create_thread(
                connection,
                workstream_id,
                payload.title,
                payload.summary,
                payload.current_goal,
                payload.next_action,
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 제목의 Thread가 있습니다.") from exc
    return {"ok": True, "id": thread_id}


@app.put("/api/threads/{thread_id}")
def api_update_thread(thread_id: int, payload: ThreadUpdate):
    try:
        with transaction() as connection:
            update_thread(
                connection,
                thread_id,
                payload.title,
                payload.status,
                payload.summary,
                payload.current_goal,
                payload.next_action,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="같은 제목의 Thread가 있습니다.") from exc
    return {"ok": True}


@app.post("/api/workstreams/{workstream_id}/checkpoints")
def api_create_checkpoint(workstream_id: int, payload: CheckpointCreate):
    with transaction() as connection:
        checkpoint_id = create_checkpoint(
            connection,
            workstream_id,
            payload.current_goal,
            payload.confirmed_facts,
            payload.recent_decisions,
            payload.open_questions,
            payload.next_actions,
            payload.files_to_open,
        )
    return {"ok": True, "id": checkpoint_id}


@app.post("/api/links")
def api_add_link(payload: LinkCreate):
    try:
        with transaction() as connection:
            link_id = add_link(
                connection,
                payload.scope_type,
                payload.scope_id,
                payload.entity_type,
                payload.entity_id,
                payload.relation_type,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "id": link_id}


@app.delete("/api/links/{scope_type}/{scope_id}/{link_id}")
def api_remove_link(scope_type: str, scope_id: int, link_id: int):
    try:
        with transaction() as connection:
            remove_link(connection, scope_type, scope_id, link_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.post("/api/external-resources")
def api_create_external_resource(payload: ExternalResourceCreate):
    try:
        with transaction() as connection:
            resource_id = create_external_resource(
                connection,
                payload.resource_type,
                payload.title,
                payload.url,
                payload.summary,
                payload.source_role,
            )
            add_link(
                connection,
                payload.scope_type,
                payload.scope_id,
                "external",
                str(resource_id),
                payload.relation_type,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "id": resource_id}


@app.post("/api/local-resources")
def api_create_local_resource(payload: LocalResourceCreate):
    try:
        with transaction() as connection:
            resource_id = create_local_resource(
                connection,
                payload.path,
                payload.title,
                payload.summary,
            )
            add_link(
                connection,
                payload.scope_type,
                payload.scope_id,
                "local",
                str(resource_id),
                payload.relation_type,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "id": resource_id}


@app.post("/api/workstreams/{workstream_id}/suggestions")
def api_generate_suggestions(workstream_id: int):
    try:
        with transaction() as connection:
            created = generate_suggestions(connection, workstream_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "created": created}


@app.post("/api/suggestions/{suggestion_id}/{action}")
def api_resolve_suggestion(suggestion_id: int, action: str):
    try:
        with transaction() as connection:
            resolve_suggestion(connection, suggestion_id, action)
    except (ValueError, LookupError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.post("/api/maintenance-runs")
def api_create_maintenance_run(payload: MaintenanceRunCreate):
    run_id = "lb-{}".format(uuid.uuid4().hex[:12])
    with transaction() as connection:
        connection.execute(
            """
            INSERT INTO maintenance_runs(
                id, workstream_id, runner, cwd, status, started_at, updated_at
            ) VALUES (?, ?, 'claude', ?, 'prepared', ?, ?)
            """,
            (
                run_id,
                payload.workstream_id,
                str(Path.home()),
                utc_now(),
                utc_now(),
            ),
        )
        target = None
        if payload.workstream_id:
            target = get_workstream(connection, payload.workstream_id)
    target_text = ""
    if target:
        target_text = "\n대상 Workstream: {} (LocalBrain #{})".format(
            target["name"], target["id"]
        )
    marker = (
        "[LOCALBRAIN_RUN: {run_id}]\n"
        "[MODE: maintenance]\n"
        "LocalBrain의 작업 우선순위와 Dashboard 갱신안을 검토해줘. "
        "원본 자원을 다시 복제하지 말고 변경점, 제안, 체크포인트 후보만 정리해줘."
        "{target_text}"
    ).format(run_id=run_id, target_text=target_text)
    return {"ok": True, "run_id": run_id, "marker": marker}


@app.post("/api/workstreams/{workstream_id}/runs")
async def api_start_task_run(workstream_id: int, payload: TaskRunCreate):
    if not runner_executable():
        raise HTTPException(status_code=503, detail="Claude CLI를 찾을 수 없습니다.")
    try:
        with transaction() as connection:
            active = connection.execute(
                """
                SELECT id FROM maintenance_runs
                WHERE workstream_id = ? AND status IN ('queued', 'running', 'cancelling')
                LIMIT 1
                """,
                (workstream_id,),
            ).fetchone()
            if active:
                raise ValueError("이 Workstream에서 이미 실행 중인 작업이 있습니다.")
            run_id = prepare_run(
                connection,
                workstream_id,
                payload.task_type,
                payload.instruction,
                refresh_suggestions=payload.refresh_suggestions,
            )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    start_run(run_id)
    return {"ok": True, "run_id": run_id, "redirect": "/runs/{}".format(run_id)}


@app.get("/api/runs/{run_id}")
def api_run_status(run_id: str):
    with connect() as connection:
        run = get_run(connection, run_id)
        if not run or not run["task_type"]:
            raise HTTPException(status_code=404, detail="Run not found")
        data = dict(run)
        data["output"] = read_run_output(run)
    return {"ok": True, "run": data}


@app.post("/api/runs/{run_id}/cancel")
async def api_cancel_run(run_id: str):
    cancelled = await cancel_run(run_id)
    if not cancelled:
        raise HTTPException(status_code=409, detail="중지할 수 있는 실행 상태가 아닙니다.")
    return {"ok": True}


@app.post("/api/scan")
def scan_sources():
    return {"ok": True, "report": scan_all()}


@app.post("/api/sessions/sync")
def sync_session_sources():
    return {"ok": True, "report": scan_session_sources()}


@app.get("/api/health")
def health():
    return {"status": "ok", "database": str(settings.database_path)}
