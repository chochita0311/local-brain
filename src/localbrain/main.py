import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, parse_qsl, quote, urlencode, urlsplit

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
    context_document_preview,
    context_document_reader,
    context_source_tree,
    list_context_sources,
    remove_context_root,
)
from .atlassian_registration import (
    AtlassianRegistrationError,
    prepare_space_catalog_run,
    registration_preview,
    register_atlassian_url,
    register_atlassian_url_with_connection,
    register_space_candidate,
    registered_scope_overview,
    registration_inventory,
    registration_sites,
    space_catalog_candidates,
    update_atlassian_connection,
)
from .atlassian_refresh import (
    AtlassianRefreshError,
    prepare_atlassian_refresh_run,
    refresh_preview,
    refresh_run_result,
)
from .atlassian_browse import (
    AtlassianBrowseError,
    atlassian_item_detail,
    browse_inventory,
    normalize_browse_filters,
    update_atlassian_local_state,
)
from .db import connect, init_db, transaction
from .ingest.scanner import scan_all, scan_context_root, scan_session_sources
from .queries import (
    dashboard_stats,
    document_detail,
    project_activity,
    search,
    session_conversation_events,
    session_inventory_page,
    session_detail,
    session_parent,
    session_subsessions,
    source_inventory,
)
from .session_pins import (
    SessionPinError,
    list_all_pinned_sessions,
    pin_session as persist_session_pin,
    unpin_session as persist_session_unpin,
)
from .runner import (
    cancel_run,
    get_run,
    list_runs,
    prepare_run,
    read_run_output,
    reconcile_interrupted_runs,
    runner_command_preview,
    runner_executable,
    shutdown_runs,
    start_run,
    task_choices,
)
from .schema_explorer import schema_explorer_page_data
from .session_context import RELATED_CONTEXT_LIMIT, session_related_context
from .session_reading import conversation_event_views
from .subagents import list_subagents, load_subagent
from .usage_queries import usage_dashboard_data
from .value_registry import display_value_label, visible_value_help
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
app.state.external_read_executor = None
app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates")
templates.env.globals["asset_version"] = max(
    path.stat().st_mtime_ns
    for path in (PACKAGE_ROOT / "static").iterdir()
    if path.is_file()
)
templates.env.globals["value_label"] = display_value_label
templates.env.globals["value_help"] = visible_value_help


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
            "runner_command": runner_command_preview(),
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
            "pinned_sessions": list_all_pinned_sessions(connection),
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
        if selected_document:
            selected_document = context_document_preview(connection, selected_document)
        tree = (
            context_source_tree(
                connection,
                selected_source["id"],
                selected_document["id"] if selected_document else None,
            )
            if selected_source else []
        )
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


def _atlassian_page_context(
    connection,
    *,
    request: Request,
    selected_view: str,
    notice: Optional[str] = None,
    form_state: Optional[dict] = None,
    form_error: Optional[str] = None,
    catalog_run: Optional[str] = None,
    selected_mode: str = "browse",
    selected_add_method: str = "url",
    browse_values: Optional[dict] = None,
) -> dict:
    inventory = registration_inventory(connection, selected_view)
    browse = browse_inventory(
        connection,
        {
            **(browse_values or {}),
            "service": selected_view,
        },
    )
    catalog = None
    catalog_error = None
    if catalog_run:
        try:
            catalog = space_catalog_candidates(
                connection, catalog_run, selected_view
            )
        except AtlassianRegistrationError as exc:
            catalog_error = str(exc)
    notices = {
        "connection-created": "연결과 Atlassian reference를 로컬에 등록했습니다.",
        "connection-updated": "Source Instance와 Site 표시 정보를 저장했습니다.",
        "item-created": "Item reference를 로컬에 등록했습니다.",
        "item-reused": "이미 등록된 Item reference를 열었습니다.",
        "space-created": "Space를 로컬에 등록했습니다.",
        "space-reused": "이미 등록된 Space를 열었습니다.",
        "catalog-started": "Space 후보 조회 maintenance Run을 시작했습니다.",
    }
    registered_scopes = registered_scope_overview(
        connection, selected_view
    )
    return {
        "request": request,
        "active_page": "atlassian",
        "selected_view": selected_view,
        "selected_mode": selected_mode,
        "selected_add_method": selected_add_method,
        "sites": registration_sites(connection, selected_view),
        "registered_scopes": registered_scopes,
        "registered_scope_space_count": sum(
            len(scope["spaces"]) for scope in registered_scopes
        ),
        "inventory": inventory,
        "browse": browse,
        "item_count": browse["known_count"],
        "space_count": len(inventory["spaces"]),
        "notice": notices.get(notice),
        "form_state": form_state or {},
        "form_error": form_error,
        "catalog": catalog,
        "catalog_error": catalog_error,
        "external_executor_ready": bool(
            getattr(request.app.state, "external_read_executor", None)
        ),
    }


async def _bounded_urlencoded_form(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/x-www-form-urlencoded"):
        raise AtlassianRegistrationError(
            "invalid-form", "Form encoding is unsupported"
        )
    body = await request.body()
    if len(body) > 32_768:
        raise AtlassianRegistrationError("invalid-form", "Form is too large")
    try:
        parsed = parse_qs(
            body.decode("utf-8"),
            keep_blank_values=True,
            max_num_fields=128,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise AtlassianRegistrationError(
            "invalid-form", "Form data is invalid"
        ) from exc
    return {
        key: values if key in {"item_id", "topic_id"} else values[-1]
        for key, values in parsed.items()
        if values
    }


def _optional_form_int(value: Optional[str], field: str) -> Optional[int]:
    if value in {None, ""}:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AtlassianRegistrationError(
            "invalid-form", "{} is invalid".format(field)
        ) from exc
    if parsed < 1:
        raise AtlassianRegistrationError(
            "invalid-form", "{} is invalid".format(field)
        )
    return parsed


@app.get("/atlassian", response_class=HTMLResponse)
def atlassian_page(
    request: Request,
    view: str = Query(default="jira"),
    mode: str = Query(default="browse"),
    method: str = Query(default="url"),
    q: str = Query(default="", max_length=300),
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
    notice: Optional[str] = Query(default=None),
    catalog_run: Optional[str] = Query(default=None),
):
    selected_view = view if view in {"jira", "confluence"} else "jira"
    selected_mode = mode if mode in {"browse", "setup"} else "browse"
    selected_add_method = (
        method if method in {"url", "connected"} else "url"
    )
    browse_values = {
        "q": q,
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
            page_context = _atlassian_page_context(
                connection,
                request=request,
                selected_view=selected_view,
                selected_mode=selected_mode,
                selected_add_method=selected_add_method,
                browse_values=browse_values,
                notice=notice,
                catalog_run=catalog_run,
            )
        except AtlassianBrowseError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return templates.TemplateResponse(
        "atlassian.html",
        page_context,
    )


@app.post("/atlassian/register", response_class=HTMLResponse)
async def atlassian_register(request: Request):
    form = {}
    try:
        form = await _bounded_urlencoded_form(request)
        service = form.get("service", "")
        if service not in {"jira", "confluence"}:
            raise AtlassianRegistrationError(
                "invalid-service", "Atlassian service is invalid"
            )
        with transaction() as connection:
            if form.get("site_id") == "new":
                result = register_atlassian_url_with_connection(
                    connection,
                    url=form.get("url", ""),
                    service=service,
                    provider_kind=form.get("provider_kind", ""),
                    source_name=form.get("source_name") or None,
                    site_name=form.get("site_name") or None,
                    config_ref=form.get("config_ref") or None,
                    title=form.get("title") or None,
                )
            else:
                site_id = _optional_form_int(
                    form.get("site_id"), "Site"
                )
                result = register_atlassian_url(
                    connection,
                    url=form.get("url", ""),
                    service=service,
                    site_id=site_id,
                    title=form.get("title") or None,
                )
    except AtlassianRegistrationError as exc:
        selected_view = (
            form.get("service")
            if form.get("service") in {"jira", "confluence"}
            else "jira"
        )
        with connect() as connection:
            page_context = _atlassian_page_context(
                connection,
                request=request,
                selected_view=selected_view,
                selected_mode="setup",
                selected_add_method="url",
                form_state=form,
                form_error=str(exc),
            )
        return templates.TemplateResponse(
            "atlassian.html", page_context, status_code=422
        )
    notice = (
        "connection-created"
        if result.get("source_created") or result.get("site_created")
        else "{}-{}".format(
            result["kind"],
            "created" if result["created"] else "reused",
        )
    )
    fragment = "atlassian-{}-{}".format(result["kind"], result["id"])
    return RedirectResponse(
        url="/atlassian?{}#{}".format(
            urlencode(
                {
                    "view": service,
                    "mode": "setup",
                    "method": "url",
                    "notice": notice,
                }
            ),
            fragment,
        ),
        status_code=303,
    )


@app.get("/api/atlassian/registration-preview")
def atlassian_registration_preview(
    url: str = Query(min_length=1, max_length=8000),
    service: Optional[str] = Query(default=None),
):
    expected_service = (
        service if service in {"jira", "confluence"} else None
    )
    try:
        with connect() as connection:
            return registration_preview(
                connection,
                url=url,
                expected_service=expected_service,
            )
    except AtlassianRegistrationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@app.post(
    "/atlassian/connections/{source_instance_id}/sites/{site_id}",
    response_class=HTMLResponse,
)
async def atlassian_update_connection(
    request: Request, source_instance_id: int, site_id: int
):
    form = {}
    try:
        form = await _bounded_urlencoded_form(request)
        service = form.get("service", "")
        if service not in {"jira", "confluence"}:
            raise AtlassianRegistrationError(
                "invalid-service", "Atlassian service is invalid"
            )
        with transaction() as connection:
            result = update_atlassian_connection(
                connection,
                source_instance_id=source_instance_id,
                site_id=site_id,
                source_name=form.get("source_name", ""),
                site_name=form.get("site_name", ""),
                enabled=form.get("enabled") == "1",
                config_ref=form.get("config_ref") or None,
            )
            if result["service"] != service:
                raise AtlassianRegistrationError(
                    "service-mismatch",
                    "The connection does not belong to this service",
                )
    except AtlassianRegistrationError as exc:
        selected_view = (
            form.get("service")
            if form.get("service") in {"jira", "confluence"}
            else "jira"
        )
        with connect() as connection:
            page_context = _atlassian_page_context(
                connection,
                request=request,
                selected_view=selected_view,
                selected_mode="setup",
                form_state=form,
                form_error=str(exc),
            )
        return templates.TemplateResponse(
            "atlassian.html", page_context, status_code=422
        )
    return RedirectResponse(
        url="/atlassian?{}#atlassian-connection-{}".format(
            urlencode(
                {
                    "view": service,
                    "mode": "setup",
                    "method": "url",
                    "notice": "connection-updated",
                }
            ),
            site_id,
        ),
        status_code=303,
    )


@app.post("/atlassian/spaces/discover", response_class=HTMLResponse)
async def atlassian_discover_spaces(request: Request):
    form = {}
    try:
        form = await _bounded_urlencoded_form(request)
        service = form.get("service", "")
        if service not in {"jira", "confluence"}:
            raise AtlassianRegistrationError(
                "invalid-service", "Atlassian service is invalid"
            )
        site_id = _optional_form_int(form.get("site_id"), "Site")
        if site_id is None:
            raise AtlassianRegistrationError(
                "site-required", "조회에 사용할 MCP 연결을 선택하세요."
            )
        target_domain = (form.get("target_domain") or "").strip().lower()
        if not target_domain:
            raise AtlassianRegistrationError(
                "target-required", "조회할 Site를 선택하세요."
            )
        runner = form.get("runner", "claude")
        if runner not in {"claude", "codex"}:
            raise AtlassianRegistrationError(
                "invalid-runner", "Maintenance runner is invalid"
            )
        executor = getattr(request.app.state, "external_read_executor", None)
        if executor is None:
            raise AtlassianRegistrationError(
                "executor-unavailable",
                "Approved host-side read executor is not connected",
            )
        if not runner_executable(runner):
            raise AtlassianRegistrationError(
                "runner-unavailable",
                "{} runner is unavailable".format(runner.capitalize()),
            )
        with transaction() as connection:
            run_id = prepare_space_catalog_run(
                connection,
                site_id=site_id,
                target_domain=target_domain,
                runner=runner,
            )
        start_run(run_id, executor)
    except AtlassianRegistrationError as exc:
        selected_view = (
            form.get("service")
            if form.get("service") in {"jira", "confluence"}
            else "jira"
        )
        with connect() as connection:
            page_context = _atlassian_page_context(
                connection,
                request=request,
                selected_view=selected_view,
                selected_mode="setup",
                selected_add_method="connected",
                form_state=form,
                form_error=str(exc),
            )
        return templates.TemplateResponse(
            "atlassian.html", page_context, status_code=422
        )
    return RedirectResponse(
        url="/atlassian?{}".format(
            urlencode(
                {
                    "view": service,
                    "mode": "setup",
                    "method": "connected",
                    "notice": "catalog-started",
                    "catalog_run": run_id,
                }
            )
        ),
        status_code=303,
    )


@app.post("/atlassian/spaces/register", response_class=HTMLResponse)
async def atlassian_register_space_candidate(request: Request):
    form = {}
    try:
        form = await _bounded_urlencoded_form(request)
        service = form.get("service", "")
        if service not in {"jira", "confluence"}:
            raise AtlassianRegistrationError(
                "invalid-service", "Atlassian service is invalid"
            )
        site_id = _optional_form_int(form.get("site_id"), "Site")
        if site_id is None:
            raise AtlassianRegistrationError(
                "site-required", "Space candidate has no Site"
            )
        with transaction() as connection:
            result = register_space_candidate(
                connection,
                site_id=site_id,
                service=service,
                space_key=form.get("space_key", ""),
                name=form.get("name", ""),
                remote_id=form.get("remote_id") or None,
            )
    except AtlassianRegistrationError as exc:
        selected_view = (
            form.get("service")
            if form.get("service") in {"jira", "confluence"}
            else "jira"
        )
        with connect() as connection:
            page_context = _atlassian_page_context(
                connection,
                request=request,
                selected_view=selected_view,
                selected_mode="setup",
                form_state=form,
                form_error=str(exc),
            )
        return templates.TemplateResponse(
            "atlassian.html", page_context, status_code=422
        )
    notice = "space-{}".format(
        "created" if result["created"] else "reused"
    )
    return RedirectResponse(
        url="/atlassian?{}#atlassian-space-{}".format(
            urlencode(
                {"view": service, "mode": "setup", "notice": notice}
            ),
            result["id"],
        ),
        status_code=303,
    )


@app.get("/atlassian/items/{item_id}", response_class=HTMLResponse)
def atlassian_item_page(
    request: Request,
    item_id: int,
    notice: Optional[str] = Query(default=None),
):
    with connect() as connection:
        item = atlassian_item_detail(connection, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Atlassian Item not found")
    notices = {
        "local-saved": "로컬 메모와 분류를 저장했습니다.",
        "linked": "기존 Workstream 관계를 추가했습니다.",
        "unlinked": "로컬 Workstream 관계를 제거했습니다.",
    }
    return templates.TemplateResponse(
        "atlassian-item.html",
        {
            "request": request,
            "active_page": "atlassian",
            "item": item,
            "notice": notices.get(notice),
            "form_error": None,
        },
    )


@app.post("/atlassian/items/{item_id}/local", response_class=HTMLResponse)
async def atlassian_update_local(request: Request, item_id: int):
    form = {}
    try:
        form = await _bounded_urlencoded_form(request)
        topic_ids = [
            _optional_form_int(value, "Topic")
            for value in form.get("topic_id", [])
        ]
        with transaction() as connection:
            update_atlassian_local_state(
                connection,
                item_id,
                note=form.get("note", ""),
                attention=form.get("attention", "normal"),
                topic_ids=[
                    value for value in topic_ids if value is not None
                ],
                tags=form.get("tags", ""),
                new_topic_name=form.get("new_topic_name", ""),
                new_topic_description=form.get(
                    "new_topic_description", ""
                ),
            )
    except (AtlassianBrowseError, AtlassianRegistrationError) as exc:
        with connect() as connection:
            item = atlassian_item_detail(connection, item_id)
        if not item:
            raise HTTPException(
                status_code=404, detail="Atlassian Item not found"
            ) from exc
        item["note"] = form.get("note", item.get("note") or "")
        item["attention"] = form.get("attention", item["attention"])
        item["selected_topic_ids"] = {
            value
            for value in (
                _optional_form_int(raw, "Topic")
                for raw in form.get("topic_id", [])
            )
            if value is not None
        }
        item["tags"] = [
            {"name": value.strip()}
            for value in form.get("tags", "").split(",")
            if value.strip()
        ]
        return templates.TemplateResponse(
            "atlassian-item.html",
            {
                "request": request,
                "active_page": "atlassian",
                "item": item,
                "notice": None,
                "form_error": str(exc),
            },
            status_code=422,
        )
    return RedirectResponse(
        url="/atlassian/items/{}?notice=local-saved#local-organization".format(
            item_id
        ),
        status_code=303,
    )


@app.post("/atlassian/items/{item_id}/links", response_class=HTMLResponse)
async def atlassian_add_local_link(request: Request, item_id: int):
    try:
        form = await _bounded_urlencoded_form(request)
        target = form.get("target", "")
        scope_type, raw_scope_id = target.split(":", 1)
        scope_id = _optional_form_int(raw_scope_id, "Link target")
        if scope_type not in {"workstream", "thread"} or scope_id is None:
            raise AtlassianBrowseError(
                "invalid-link", "Select a Workstream or Thread"
            )
        with transaction() as connection:
            if not atlassian_item_detail(connection, item_id):
                raise AtlassianBrowseError(
                    "item-not-found", "Atlassian Item was not found"
                )
            add_link(
                connection,
                scope_type,
                scope_id,
                "external",
                str(item_id),
                "reference",
            )
    except (
        AtlassianBrowseError,
        AtlassianRegistrationError,
        ValueError,
        LookupError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(
        url="/atlassian/items/{}?notice=linked#local-organization".format(
            item_id
        ),
        status_code=303,
    )


@app.post(
    "/atlassian/items/{item_id}/links/{scope_type}/{scope_id}/{link_id}",
    response_class=HTMLResponse,
)
def atlassian_remove_local_link(
    item_id: int, scope_type: str, scope_id: int, link_id: int
):
    try:
        with transaction() as connection:
            if not atlassian_item_detail(connection, item_id):
                raise AtlassianBrowseError(
                    "item-not-found", "Atlassian Item was not found"
                )
            if scope_type == "workstream":
                link = connection.execute(
                    """
                    SELECT 1 FROM workstream_links
                    WHERE id = ? AND workstream_id = ?
                      AND entity_type = 'external' AND entity_id = ?
                    """,
                    (link_id, scope_id, str(item_id)),
                ).fetchone()
            elif scope_type == "thread":
                link = connection.execute(
                    """
                    SELECT 1 FROM thread_links
                    WHERE id = ? AND thread_id = ?
                      AND entity_type = 'external' AND entity_id = ?
                    """,
                    (link_id, scope_id, str(item_id)),
                ).fetchone()
            else:
                link = None
            if not link:
                raise AtlassianBrowseError(
                    "link-not-found",
                    "The selected local relation was not found",
                )
            remove_link(connection, scope_type, scope_id, link_id)
    except (AtlassianBrowseError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(
        url="/atlassian/items/{}?notice=unlinked#local-organization".format(
            item_id
        ),
        status_code=303,
    )


def _refresh_retry_ids(value: Optional[str]) -> Optional[list[int]]:
    if not value:
        return None
    values = []
    for raw in value.split(",")[:20]:
        try:
            item_id = int(raw)
        except (TypeError, ValueError) as exc:
            raise AtlassianRefreshError(
                "invalid-retry", "Retry Item selection is invalid"
            ) from exc
        if item_id < 1:
            raise AtlassianRefreshError(
                "invalid-retry", "Retry Item selection is invalid"
            )
        if item_id not in values:
            values.append(item_id)
    return values or None


def _atlassian_refresh_context(
    connection,
    *,
    request: Request,
    scope_kind: str,
    scope_id: Optional[int],
    page: int,
    retry: Optional[str] = None,
    selected_ids: Optional[list[int]] = None,
    run_id: Optional[str] = None,
    form_error: Optional[str] = None,
) -> dict:
    retry_ids = selected_ids
    if retry_ids is None:
        retry_ids = _refresh_retry_ids(retry)
    preview = refresh_preview(
        connection,
        scope_kind=scope_kind,
        scope_id=scope_id,
        page=page,
        selected_ids=retry_ids,
    )
    run_result = refresh_run_result(connection, run_id) if run_id else None
    return {
        "request": request,
        "active_page": "atlassian",
        "preview": preview,
        "scope_kind": scope_kind,
        "scope_id": scope_id,
        "page": page,
        "run_result": run_result,
        "form_error": form_error,
        "external_executor_ready": bool(
            getattr(request.app.state, "external_read_executor", None)
        ),
        "runner_ready": {
            runner: bool(runner_executable(runner))
            for runner in ("claude", "codex")
        },
    }


@app.get("/atlassian/refresh", response_class=HTMLResponse)
def atlassian_refresh_page(
    request: Request,
    scope: str = Query(default="all_known"),
    scope_id: Optional[int] = Query(default=None, alias="id"),
    page: int = Query(default=1, ge=1),
    retry: Optional[str] = Query(default=None),
    run_id: Optional[str] = Query(default=None, alias="run"),
):
    try:
        with connect() as connection:
            page_context = _atlassian_refresh_context(
                connection,
                request=request,
                scope_kind=scope,
                scope_id=scope_id,
                page=page,
                retry=retry,
                run_id=run_id,
            )
    except AtlassianRefreshError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        "atlassian-refresh.html", page_context
    )


@app.post("/atlassian/refresh", response_class=HTMLResponse)
async def atlassian_start_refresh(request: Request):
    scope_kind = "all_known"
    scope_id = None
    page = 1
    selected_ids: list[int] = []
    try:
        form = await _bounded_urlencoded_form(request)
        scope_kind = str(form.get("scope", "all_known"))
        scope_id = _optional_form_int(
            form.get("scope_id"), "Refresh scope"
        )
        page = _optional_form_int(form.get("page"), "Page") or 1
        raw_ids = form.get("item_id", [])
        if isinstance(raw_ids, str):
            raw_ids = [raw_ids]
        selected_ids = [
            item_id
            for item_id in (
                _optional_form_int(value, "Item") for value in raw_ids
            )
            if item_id is not None
        ]
        runner = str(form.get("runner", "claude"))
        if runner not in {"claude", "codex"}:
            raise AtlassianRefreshError(
                "invalid-runner", "Maintenance runner is invalid"
            )
        executor = getattr(request.app.state, "external_read_executor", None)
        if executor is None:
            raise AtlassianRefreshError(
                "executor-unavailable",
                "Approved host-side read executor is not connected",
            )
        if not runner_executable(runner):
            raise AtlassianRefreshError(
                "runner-unavailable",
                "{} runner is unavailable".format(runner.capitalize()),
            )
        with transaction() as connection:
            run_id = prepare_atlassian_refresh_run(
                connection,
                scope_kind=scope_kind,
                scope_id=scope_id,
                selected_item_ids=selected_ids,
                include_catalog=form.get("include_catalog") == "true",
                page=page,
                runner=runner,
            )
        start_run(run_id, executor)
    except (AtlassianRegistrationError, AtlassianRefreshError) as exc:
        try:
            with connect() as connection:
                page_context = _atlassian_refresh_context(
                    connection,
                    request=request,
                    scope_kind=scope_kind,
                    scope_id=scope_id,
                    page=page,
                    selected_ids=selected_ids,
                    form_error=str(exc),
                )
        except AtlassianRefreshError as context_exc:
            raise HTTPException(
                status_code=422, detail=str(context_exc)
            ) from context_exc
        return templates.TemplateResponse(
            "atlassian-refresh.html", page_context, status_code=422
        )
    query = {"scope": scope_kind, "page": page, "run": run_id}
    if scope_id is not None:
        query["id"] = scope_id
    return RedirectResponse(
        url="/atlassian/refresh?{}".format(urlencode(query)),
        status_code=303,
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
            "pinned_sessions": list_all_pinned_sessions(connection),
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


def _session_pin_destination(
    return_to: str,
    session_id: int,
    *,
    error: Optional[str] = None,
) -> str:
    parsed = urlsplit(return_to)
    path = parsed.path
    detail_id = None
    if path.startswith("/sessions/"):
        suffix = path.removeprefix("/sessions/")
        detail_id = int(suffix) if suffix.isdigit() else None
    if path not in {"/sessions", "/projects"} and detail_id is None:
        path = "/sessions"
        query_items = []
    elif parsed.scheme or parsed.netloc:
        path = "/sessions"
        query_items = []
    else:
        query_items = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key not in {"pin_error", "pin_session"}
        ]
    if error:
        query_items.extend((("pin_error", error), ("pin_session", str(session_id))))
    query = urlencode(query_items)
    return "{}{}#session-pin-{}".format(
        path,
        "?{}".format(query) if query else "",
        session_id,
    )


@app.post("/sessions/{session_id}/pin")
async def pin_session_page(request: Request, session_id: int):
    form = parse_qs(
        (await request.body())[:4096].decode("utf-8", errors="replace"),
        keep_blank_values=True,
    )
    return_to = str(form.get("return_to", ["/sessions"])[0] or "/sessions")
    try:
        with transaction() as connection:
            persist_session_pin(connection, session_id)
    except SessionPinError as exc:
        error = (
            "missing"
            if exc.code == "session-not-found"
            else "ineligible"
        )
        return RedirectResponse(
            url=_session_pin_destination(return_to, session_id, error=error),
            status_code=303,
        )
    except sqlite3.Error:
        return RedirectResponse(
            url=_session_pin_destination(
                return_to, session_id, error="storage-unavailable"
            ),
            status_code=303,
        )
    return RedirectResponse(
        url=_session_pin_destination(return_to, session_id),
        status_code=303,
    )


@app.post("/sessions/{session_id}/unpin")
async def unpin_session_page(request: Request, session_id: int):
    form = parse_qs(
        (await request.body())[:4096].decode("utf-8", errors="replace"),
        keep_blank_values=True,
    )
    return_to = str(form.get("return_to", ["/sessions"])[0] or "/sessions")
    try:
        with transaction() as connection:
            persist_session_unpin(connection, session_id)
    except sqlite3.Error:
        return RedirectResponse(
            url=_session_pin_destination(
                return_to, session_id, error="storage-unavailable"
            ),
            status_code=303,
        )
    return RedirectResponse(
        url=_session_pin_destination(return_to, session_id),
        status_code=303,
    )


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


@app.get("/schema", response_class=HTMLResponse)
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


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
def show_session(request: Request, session_id: int):
    with connect() as connection:
        session = session_detail(connection, session_id)
        if not session or session["session_class"] != "work":
            raise HTTPException(status_code=404, detail="Session not found")
        events = conversation_event_views(
            session_conversation_events(connection, session_id)
        )
        parent = session_parent(connection, session_id)
        direct_children = session_subsessions(connection, session_id)
        memberships = entity_memberships(connection, "session", session_id)
        related_context = None
        if session["session_role"] == "primary":
            try:
                related_context = session_related_context(
                    connection,
                    session_id,
                    session["workspace_id"],
                )
            except sqlite3.Error:
                related_context = {
                    "state": "error",
                    "items": [],
                    "limit": RELATED_CONTEXT_LIMIT,
                    "candidate_count": 0,
                    "overflow_count": 0,
                    "unavailable_count": 0,
                    "visible_unavailable_count": 0,
                    "scan_truncated": False,
                }

    subsessions = [
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
        normalized_paths = {item["source_path"] for item in subsessions}
        normalized_external_ids = {item["external_id"] for item in subsessions}
        for item in list_subagents(session["source_path"], session["external_id"]):
            if (
                item["source_path"] in normalized_paths
                or item["external_id"] in normalized_external_ids
            ):
                continue
            subsessions.append(
                {
                    "url": "/sessions/{}/subsessions/{}".format(
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
            "subsessions": subsessions,
            "related_context": related_context,
        },
    )


@app.get("/sessions/{session_id}/subsessions/{file_name}", response_class=HTMLResponse)
def show_subsession(request: Request, session_id: int, file_name: str):
    with connect() as connection:
        session = session_detail(connection, session_id)
        if (
            not session
            or session["source_kind"] != "claude"
            or session["session_role"] != "primary"
        ):
            raise HTTPException(status_code=404, detail="Parent session not found")
        direct_children = session_subsessions(connection, session_id)
    subsession = load_subagent(session["source_path"], file_name)
    if not subsession or subsession.parent_external_id != session["external_id"]:
        raise HTTPException(status_code=404, detail="Subsession not found")
    normalized_child = next(
        (
            child
            for child in direct_children
            if child["source_path"] == subsession.source_path
            or child["external_id"] == subsession.external_id
        ),
        None,
    )
    if normalized_child:
        return RedirectResponse(
            url="/sessions/{}".format(normalized_child["id"]), status_code=303
        )
    conversation_events = conversation_event_views(
        sorted(
            (event for event in subsession.events if event.event_type == "message"),
            key=lambda event: event.sequence,
        )
    )
    return templates.TemplateResponse(
        "subsession.html",
        {
            "request": request,
            "active_page": "sessions",
            "session": session,
            "subsession": subsession,
            "events": conversation_events,
            "event_count": len(subsession.events),
            "file_name": file_name,
        },
    )


@app.get("/sessions/{session_id}/subagents/{file_name}", include_in_schema=False)
def redirect_legacy_subagent_route(session_id: int, file_name: str):
    return RedirectResponse(
        url="/sessions/{}/subsessions/{}".format(session_id, quote(file_name)),
        status_code=308,
    )


@app.get("/documents/{document_id}", response_class=HTMLResponse)
def show_document(request: Request, document_id: int):
    with connect() as connection:
        document = document_detail(connection, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        reader = context_document_reader(connection, document)
        memberships = entity_memberships(connection, "document", document_id)
    return templates.TemplateResponse(
        "document.html",
        {
            "request": request,
            "active_page": "context",
            **reader,
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
        "search.html",
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
        data["status_label"] = display_value_label(
            "maintenance.status", data["status"]
        )
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
