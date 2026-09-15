import json
import queue
import re
import secrets
import sqlite3
import threading
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import parse_qs, parse_qsl, quote, urlencode, urlsplit

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

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
    register_atlassian_site_access,
    register_atlassian_url,
    register_space_catalog_candidate,
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
    ADVANCED_FILTER_FIELDS,
    AtlassianBrowseError,
    atlassian_item_detail,
    atlassian_item_preview,
    atlassian_structure_reference_detail,
    atlassian_structure_reference_preview,
    browse_inventory,
    normalize_browse_filters,
    normalize_browse_structure,
    validate_browse_structural_scope,
    update_atlassian_local_state,
)
from .atlassian_evidence_sync import sync_atlassian_local_evidence
from .atlassian_evidence import atlassian_url_container_hint
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
    session_source_scopes,
    session_subsessions,
    source_inventory,
)
from .session_pins import (
    SessionPinError,
    group_pinned_sessions,
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
from .session_context import (
    session_related_context,
    session_related_context_error,
)
from .session_reading import conversation_event_views
from .session_sources import load_and_reconcile_session_sources
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
from .workflow_focus import (
    workflow_focus_projection,
    workflow_session_is_eligible,
)
from .workflow_assertions import (
    WorkflowAssertionError,
    apply_workflow_assertion,
    undo_workflow_assertion,
)
from .workflow_correction import (
    MAX_WORKFLOW_CORRECTION_FORM_BYTES,
    WORKFLOW_CORRECTION_PARTIAL,
    WorkflowCorrectionRequestError,
    parse_workflow_correction_form,
    reject_cross_site_workflow_correction,
)
from .workflow_correction_view import workflow_relation_id
from .workflow_map import workflow_map_state_view, workflow_map_view


PACKAGE_ROOT = Path(__file__).resolve().parent
ATLASSIAN_SYNC_PARTIAL = "atlassian-local-evidence-sync"
ATLASSIAN_SYNC_RECEIPT_TTL_SECONDS = 5 * 60
ATLASSIAN_SYNC_RECEIPT_LIMIT = 32
ATLASSIAN_SYNC_FORM_BYTES = 8 * 1024
_ATLASSIAN_SYNC_RECEIPTS = OrderedDict()
_ATLASSIAN_SYNC_RECEIPT_LOCK = threading.Lock()
_ATLASSIAN_SYNC_RECEIPT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32}$")


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
    with transaction() as connection:
        app.state.session_source_registry = load_and_reconcile_session_sources(
            connection, settings
        )
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
    try:
        requested_page = int(page)
        page_is_valid = requested_page > 0
    except (TypeError, ValueError):
        requested_page = 1
        page_is_valid = False
    with connect() as connection:
        source_scopes = session_source_scopes(connection)
        source_scope_by_key = {
            item["source_key"]: item for item in source_scopes
        }
        source_is_valid = source == "all" or source in source_scope_by_key
        workspace_is_valid = workspace is None or connection.execute(
            "SELECT 1 FROM workspaces WHERE id = ?", (workspace,)
        ).fetchone() is not None
        if not source_is_valid or not workspace_is_valid:
            params = {}
            if source_is_valid and source != "all":
                params["source"] = source
            if workspace_is_valid and workspace is not None:
                params["workspace"] = workspace
            destination = "/sessions"
            if params:
                destination += "?{}".format(urlencode(params))
            return RedirectResponse(url=destination, status_code=303)
        selected_source = source if source != "all" else None
        projects = project_activity(connection, selected_source)
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
        pinned_sessions = list_all_pinned_sessions(connection)
        page_context = {
            "request": request,
            "active_page": "sessions",
            "selected_inventory": "sessions",
            "page_title": "Sessions",
            "selected_source": selected_source or "all",
            "selected_source_label": (
                source_scope_by_key[selected_source]["display_label"]
                if selected_source
                else "전체"
            ),
            "selected_workspace": workspace,
            "stats": dashboard_stats(connection, selected_source),
            "sessions": pagination["items"],
            "pagination": pagination,
            "pinned_sessions": pinned_sessions,
            "pinned_session_groups": group_pinned_sessions(pinned_sessions),
            "sources": source_inventory(connection),
            "session_source_scopes": source_scopes,
            "projects": projects,
            "project_count": len(projects),
            "missing_count": sum(
                1 for project in projects if not project["exists_now"]
            ),
            "sync_outcome": request.query_params.get("sync")
            if request.query_params.get("sync") in {"complete", "partial", "failed"}
            else None,
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


ATLASSIAN_VIEW_SERVICES = {
    "all": None,
    "jira": "jira",
    "wiki": "confluence",
}
ATLASSIAN_BROWSE_STATE_FIELDS = (
    "q",
    "source_instance_id",
    "item_type",
    "site_id",
    "space_id",
    "structural_scope",
    *ADVANCED_FILTER_FIELDS,
)
ATLASSIAN_EXPLORER_STATE_FIELDS = (
    *ATLASSIAN_BROWSE_STATE_FIELDS,
    "item",
    "reference",
)
MAX_SQLITE_INTEGER = 9_223_372_036_854_775_807
MAX_ATLASSIAN_FORM_BYTES = 160 * 1024


def _has_repeated_atlassian_explorer_state(
    pairs: Iterable[tuple[str, str]],
) -> bool:
    single_value_fields = {"view", *ATLASSIAN_EXPLORER_STATE_FIELDS}
    seen: set[str] = set()
    for key, _value in pairs:
        if key not in single_value_fields:
            continue
        if key in seen:
            return True
        seen.add(key)
    return False


def _normalize_atlassian_view(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "confluence":
        return "wiki"
    return normalized if normalized in ATLASSIAN_VIEW_SERVICES else "all"


def _atlassian_view_for_service(service: str) -> str:
    return "wiki" if service == "confluence" else "jira"


def _atlassian_browse_url(
    selected_view: str,
    filters: dict,
    **overrides,
) -> str:
    state = {
        key: filters.get(key) for key in ATLASSIAN_EXPLORER_STATE_FIELDS
    }
    state.update(overrides)
    query = {"view": _normalize_atlassian_view(selected_view)}
    query.update(
        {
            key: value
            for key, value in state.items()
            if value is not None and value != ""
        }
    )
    return "/atlassian?{}".format(urlencode(query))


def _atlassian_selected_item_id(value: Optional[str]) -> Optional[int]:
    if value in (None, ""):
        return None
    raw = str(value).strip()
    if not raw.isascii() or not raw.isdigit() or len(raw) > 19:
        raise AtlassianBrowseError(
            "invalid-selection",
            "선택한 Atlassian 링크/문서가 올바르지 않습니다.",
        )
    item_id = int(raw)
    if item_id < 1 or item_id > MAX_SQLITE_INTEGER:
        raise AtlassianBrowseError(
            "invalid-selection",
            "선택한 Atlassian 링크/문서가 올바르지 않습니다.",
        )
    return item_id


def _atlassian_selected_reference_id(
    value: Optional[str],
) -> Optional[int]:
    if value in (None, ""):
        return None
    raw = str(value).strip()
    if not raw.isascii() or not raw.isdigit() or len(raw) > 19:
        raise AtlassianBrowseError(
            "invalid-selection",
            "선택한 Atlassian 구조 참조가 올바르지 않습니다.",
        )
    reference_id = int(raw)
    if reference_id < 1 or reference_id > MAX_SQLITE_INTEGER:
        raise AtlassianBrowseError(
            "invalid-selection",
            "선택한 Atlassian 구조 참조가 올바르지 않습니다.",
        )
    return reference_id


def _atlassian_explorer_urls(browse: dict, selected_view: str) -> dict:
    filters = browse["filters"]
    service_urls = {
        view: _atlassian_browse_url(
            view,
            filters,
            site_id=None,
            space_id=None,
            structural_scope=None,
        )
        for view in ATLASSIAN_VIEW_SERVICES
    }
    for site in browse["hierarchy"]["sites"]:
        site["href"] = _atlassian_browse_url(
            selected_view,
            filters,
            site_id=site["id"],
            space_id=None,
            structural_scope=None,
        )
        site["active"] = (
            filters["site_id"] == site["id"]
            and filters["space_id"] is None
            and filters["structural_scope"] is None
        )
        for container in site["containers"]:
            container["href"] = _atlassian_browse_url(
                selected_view,
                filters,
                site_id=site["id"],
                space_id=(
                    container["id"]
                    if container["kind"] == "space"
                    else None
                ),
                structural_scope=container.get("structural_scope"),
            )
            container["active"] = (
                filters["site_id"] == site["id"]
                and (
                    filters["space_id"] == container["id"]
                    if container["kind"] == "space"
                    else filters["structural_scope"]
                    == container.get("structural_scope")
                )
            )
    clear_overrides = {
        field: None for field in ADVANCED_FILTER_FIELDS
    }
    return {
        "services": service_urls,
        "root": _atlassian_browse_url(
            selected_view,
            filters,
            site_id=None,
            space_id=None,
            structural_scope=None,
        ),
        "clear_filters": _atlassian_browse_url(
            selected_view, filters, **clear_overrides
        ),
        "reset": "/atlassian",
    }


def _validate_atlassian_explorer_structure(
    selected_view: str,
    values: Optional[dict],
) -> None:
    _normalize_atlassian_view(selected_view)


def _atlassian_inventory_return_path(
    value: Optional[str],
    connection=None,
    *,
    post_sync: bool = False,
) -> str:
    if not value or len(value) > 4_000:
        return "/atlassian"
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.path != "/atlassian":
        return "/atlassian"
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    if _has_repeated_atlassian_explorer_state(pairs):
        return "/atlassian"
    raw = dict(pairs)
    selected_view = _normalize_atlassian_view(raw.get("view", "all"))
    values = {
        key: raw.get(key) for key in ATLASSIAN_BROWSE_STATE_FIELDS
    }
    values["service"] = ATLASSIAN_VIEW_SERVICES[selected_view]
    try:
        _validate_atlassian_explorer_structure(selected_view, values)
        filters = normalize_browse_filters(values)
        if connection is None:
            with connect() as owned_connection:
                filters = normalize_browse_structure(
                    owned_connection, filters
                )
        else:
            filters = normalize_browse_structure(connection, filters)
        selected_item_id = _atlassian_selected_item_id(raw.get("item"))
        selected_reference_id = _atlassian_selected_reference_id(
            raw.get("reference")
        )
        if (
            selected_item_id is not None
            and selected_reference_id is not None
        ):
            raise AtlassianBrowseError(
                "invalid-selection",
                "Atlassian 선택은 한 번에 하나만 지정할 수 있습니다.",
            )
        if not (post_sync and selected_reference_id is not None):
            if connection is None:
                with connect() as owned_connection:
                    validate_browse_structural_scope(
                        owned_connection, filters
                    )
            else:
                validate_browse_structural_scope(connection, filters)
    except AtlassianBrowseError:
        return "/atlassian"

    if post_sync and selected_reference_id is not None:
        def canonicalize_reference(owned_connection):
            reference = atlassian_structure_reference_detail(
                owned_connection, selected_reference_id
            )
            if reference is None:
                return None
            expected_service = ATLASSIAN_VIEW_SERVICES[selected_view]
            if (
                expected_service is not None
                and reference["service"] != expected_service
            ):
                return None
            canonical_filters = dict(filters)
            canonical_filters["space_id"] = None
            if reference["lifecycle"] == "archived":
                canonical_filters["site_id"] = None
                canonical_filters["structural_scope"] = None
            else:
                canonical_filters["site_id"] = reference["site_id"]
                canonical_filters["structural_scope"] = reference[
                    "container_structural_scope"
                ]
            return canonical_filters

        if connection is None:
            with connect() as owned_connection:
                canonical_filters = canonicalize_reference(
                    owned_connection
                )
        else:
            canonical_filters = canonicalize_reference(connection)
        if canonical_filters is None:
            return "/atlassian"
        filters = canonical_filters
    return _atlassian_browse_url(
        selected_view,
        filters,
        item=selected_item_id,
        reference=selected_reference_id,
    )


def _prune_atlassian_sync_receipts(now: float) -> None:
    expired = [
        token
        for token, receipt in _ATLASSIAN_SYNC_RECEIPTS.items()
        if float(receipt["expires_at"]) <= now
    ]
    for token in expired:
        _ATLASSIAN_SYNC_RECEIPTS.pop(token, None)


def _store_atlassian_sync_receipt(report: dict, return_to: str) -> str:
    token = secrets.token_urlsafe(24)
    receipt = {
        "return_to": return_to,
        "report": json.loads(json.dumps(report)),
        "expires_at": time.monotonic()
        + ATLASSIAN_SYNC_RECEIPT_TTL_SECONDS,
    }
    with _ATLASSIAN_SYNC_RECEIPT_LOCK:
        now = time.monotonic()
        _prune_atlassian_sync_receipts(now)
        while token in _ATLASSIAN_SYNC_RECEIPTS:
            token = secrets.token_urlsafe(24)
        _ATLASSIAN_SYNC_RECEIPTS[token] = receipt
        while len(_ATLASSIAN_SYNC_RECEIPTS) > ATLASSIAN_SYNC_RECEIPT_LIMIT:
            _ATLASSIAN_SYNC_RECEIPTS.popitem(last=False)
    return token


def _verified_atlassian_sync_report(
    receipt_token: Optional[str], current_return_to: str
) -> Optional[dict]:
    token = str(receipt_token or "")
    if not _ATLASSIAN_SYNC_RECEIPT_PATTERN.fullmatch(token):
        return None
    with _ATLASSIAN_SYNC_RECEIPT_LOCK:
        _prune_atlassian_sync_receipts(time.monotonic())
        receipt = _ATLASSIAN_SYNC_RECEIPTS.get(token)
        if receipt is None or receipt["return_to"] != current_return_to:
            return None
        return json.loads(json.dumps(receipt["report"]))


def _atlassian_sync_receipt_url(return_to: str, token: str) -> str:
    parsed = urlsplit(return_to)
    pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key != "sync_receipt"
    ]
    pairs.append(("sync_receipt", token))
    query = urlencode(pairs)
    result = parsed.path
    if query:
        result = "{}?{}".format(result, query)
    return "{}#atlassian-sync-result".format(result)


ATLASSIAN_NOTICES = {
    "connection-created": "Site에 원격 접근 경로를 연결했습니다.",
    "connection-updated": "원격 접근 경로 설정을 저장했습니다.",
    "item-created": "Atlassian 링크/문서를 로컬에 등록했습니다.",
    "item-reused": "이미 등록된 Atlassian 링크/문서를 열었습니다.",
    "space-created": "Space를 로컬에 등록했습니다.",
    "space-reused": "이미 등록된 Space를 열었습니다.",
    "catalog-started": "Space 후보 조회 maintenance Run을 시작했습니다.",
}


def _atlassian_notice(value: Optional[str]) -> Optional[str]:
    return ATLASSIAN_NOTICES.get(str(value or "")[:80])


def _atlassian_add_return_path(
    value: Optional[str], connection=None
) -> str:
    try:
        parsed = urlsplit(value or "")
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
    except (TypeError, ValueError):
        return "/atlassian#atlassian-add-action"
    allowed = {"view", *ATLASSIAN_EXPLORER_STATE_FIELDS}
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.path != "/atlassian"
        or any(key not in allowed for key, _value in pairs)
    ):
        return "/atlassian#atlassian-add-action"
    safe = _atlassian_inventory_return_path(value, connection)
    return "{}#atlassian-add-action".format(safe)


def _atlassian_connections_view(value: Optional[str]) -> str:
    return "wiki" if str(value or "").strip().lower() in {
        "wiki",
        "confluence",
    } else "jira"


def _atlassian_connections_url(
    selected_view: str,
    *,
    notice: Optional[str] = None,
    catalog_run: Optional[str] = None,
    fragment: Optional[str] = None,
) -> str:
    query = {"view": _atlassian_connections_view(selected_view)}
    if _atlassian_notice(notice):
        query["notice"] = str(notice)
    if catalog_run and len(str(catalog_run)) <= 300:
        query["catalog_run"] = str(catalog_run)
    result = "/atlassian/connections?{}".format(urlencode(query))
    if fragment:
        result = "{}#{}".format(result, quote(fragment, safe="-_.~"))
    return result


def _atlassian_registration_handoff(result: dict) -> str:
    selected_view = _atlassian_view_for_service(result["service"])
    notice = "{}-{}".format(
        result["kind"],
        "created" if result["created"] else "reused",
    )
    if result["kind"] == "item":
        overrides = {
            "site_id": result["site_id"],
            "item": result["id"],
            "notice": notice,
        }
        if result.get("space_id") is not None:
            overrides["space_id"] = result["space_id"]
        else:
            hint = atlassian_url_container_hint(
                result.get("canonical_url")
            )
            overrides["structural_scope"] = (
                hint["structural_scope"]
                if hint is not None
                else "unclassified"
            )
        if result.get("attention") == "archived":
            overrides["attention"] = "archived"
        return _atlassian_browse_url(selected_view, {}, **overrides)
    return _atlassian_browse_url(
        selected_view,
        {},
        site_id=result["site_id"],
        space_id=result["id"],
        notice=notice,
    )


def _atlassian_add_context(
    request: Request,
    *,
    return_to: str,
    form_state: Optional[dict] = None,
    form_error: Optional[str] = None,
) -> dict:
    return {
        "request": request,
        "active_page": "atlassian",
        "page_title": "Add Atlassian URL · LocalBrain",
        "return_to": return_to,
        "form_state": form_state or {},
        "form_error": form_error,
    }


def _atlassian_connections_context(
    connection,
    *,
    request: Request,
    selected_view: str,
    notice: Optional[str] = None,
    catalog_run: Optional[str] = None,
    access_form_state: Optional[dict] = None,
    access_error: Optional[str] = None,
    connection_form_state: Optional[dict] = None,
    connection_error: Optional[str] = None,
    connection_error_binding_id: Optional[int] = None,
    discovery_form_state: Optional[dict] = None,
    discovery_error: Optional[str] = None,
    candidate_form_state: Optional[dict] = None,
    candidate_error: Optional[str] = None,
) -> dict:
    selected_view = _atlassian_connections_view(selected_view)
    service = ATLASSIAN_VIEW_SERVICES[selected_view]
    scopes = registered_scope_overview(connection, service)
    sites = registration_sites(connection, service)
    catalog = None
    catalog_error = None
    if catalog_run and len(str(catalog_run)) <= 300:
        try:
            catalog = space_catalog_candidates(connection, str(catalog_run), service)
        except AtlassianRegistrationError as exc:
            catalog_error = str(exc)
    return {
        "request": request,
        "active_page": "atlassian",
        "page_title": "Atlassian Connections · LocalBrain",
        "selected_view": selected_view,
        "selected_service": service,
        "registered_scopes": scopes,
        "registered_scope_space_count": sum(
            len(scope["spaces"]) for scope in scopes
        ),
        "sites": sites,
        "notice": _atlassian_notice(notice),
        "catalog": catalog,
        "catalog_error": catalog_error,
        "catalog_run": str(catalog_run or "")[:300],
        "external_executor_ready": bool(
            getattr(request.app.state, "external_read_executor", None)
        ),
        "access_form_state": access_form_state or {},
        "access_error": access_error,
        "connection_form_state": connection_form_state or {},
        "connection_error": connection_error,
        "connection_error_binding_id": connection_error_binding_id,
        "discovery_form_state": discovery_form_state or {},
        "discovery_error": discovery_error,
        "candidate_form_state": candidate_form_state or {},
        "candidate_error": candidate_error,
    }


def _atlassian_preview_context(
    connection,
    *,
    selected_view: str,
    filters: dict,
    selected_item_id: Optional[int],
    selected_reference_id: Optional[int] = None,
) -> dict:
    clear_url = _atlassian_browse_url(
        selected_view,
        filters,
        item=None,
        reference=None,
    )
    selection_kind = (
        "item"
        if selected_item_id is not None
        else (
            "reference" if selected_reference_id is not None else None
        )
    )
    selected_id = (
        selected_item_id
        if selected_item_id is not None
        else selected_reference_id
    )
    context = {
        "state": "empty",
        "selection_kind": selection_kind,
        "selected_key": (
            "{}:{}".format(selection_kind, selected_id)
            if selection_kind is not None and selected_id is not None
            else None
        ),
        "selected_id": selected_id,
        "item": None,
        "reference": None,
        "entry": None,
        "clear_url": clear_url,
        "selected_url": None,
        "detail_url": None,
        "refresh_url": None,
        "document_title": "Atlassian · LocalBrain",
    }
    if selected_id is None:
        return context

    if selected_reference_id is not None:
        selected_url = _atlassian_browse_url(
            selected_view,
            filters,
            item=None,
            reference=selected_reference_id,
        )
        reference = atlassian_structure_reference_preview(
            connection,
            selected_reference_id,
            {
                **filters,
                "service": ATLASSIAN_VIEW_SERVICES[
                    _normalize_atlassian_view(selected_view)
                ],
            },
        )
        state = "missing"
        if reference is not None:
            if reference["lifecycle"] == "archived":
                state = "archived"
            elif reference["eligible"]:
                state = "selected"
            else:
                state = "out_of_scope"
        context.update(
            {
                "state": state,
                "reference": reference,
                "entry": reference,
                "selected_url": selected_url,
                "detail_url": (
                    "/atlassian/references/{}?{}".format(
                        selected_reference_id,
                        urlencode({"return_to": selected_url}),
                    )
                    if reference is not None
                    else None
                ),
                "document_title": (
                    "{} · Atlassian · LocalBrain".format(
                        reference["display_title"]
                    )
                    if reference is not None
                    else "Atlassian 구조 참조를 찾지 못함 · LocalBrain"
                ),
            }
        )
        return context

    selected_url = _atlassian_browse_url(
        selected_view,
        filters,
        item=selected_item_id,
        reference=None,
    )
    item = atlassian_item_preview(
        connection,
        selected_item_id,
        {
            **filters,
            "service": ATLASSIAN_VIEW_SERVICES[
                _normalize_atlassian_view(selected_view)
            ],
        },
    )
    context.update(
        {
            "state": (
                "missing"
                if item is None
                else ("selected" if item["eligible"] else "out_of_scope")
            ),
            "item": item,
            "entry": item,
            "selected_url": selected_url,
            "detail_url": (
                "/atlassian/items/{}?{}".format(
                    selected_item_id,
                    urlencode({"return_to": selected_url}),
                )
                if item is not None
                else None
            ),
            "refresh_url": (
                "/atlassian/refresh?{}".format(
                    urlencode(
                        {
                            "scope": "item",
                            "id": selected_item_id,
                            "return_to": selected_url,
                        }
                    )
                )
                if item is not None
                else None
            ),
            "document_title": (
                "{} · Atlassian · LocalBrain".format(
                    item["display_title"]
                )
                if item is not None
                else "Atlassian 링크/문서를 찾지 못함 · LocalBrain"
            ),
        }
    )
    return context


def _atlassian_page_context(
    connection,
    *,
    request: Request,
    selected_view: str,
    notice: Optional[str] = None,
    browse_values: Optional[dict] = None,
    selected_item_id: Optional[int] = None,
    selected_reference_id: Optional[int] = None,
    sync_receipt: Optional[str] = None,
) -> dict:
    selected_view = _normalize_atlassian_view(selected_view)
    selected_service = ATLASSIAN_VIEW_SERVICES[selected_view]
    _validate_atlassian_explorer_structure(selected_view, browse_values)
    browse = browse_inventory(
        connection,
        {
            **(browse_values or {}),
            "service": selected_service,
        },
    )
    explorer_urls = _atlassian_explorer_urls(browse, selected_view)
    return_url = _atlassian_browse_url(selected_view, browse["filters"])
    for entry in browse["entries"]:
        is_reference = entry["entity_kind"] == "reference"
        selection_url = _atlassian_browse_url(
            selected_view,
            browse["filters"],
            item=None if is_reference else entry["id"],
            reference=entry["id"] if is_reference else None,
        )
        entry["selection_url"] = selection_url
        entry["detail_url"] = "/atlassian/{}/{}?{}".format(
            "references" if is_reference else "items",
            entry["id"],
            urlencode({"return_to": selection_url}),
        )
        entry["selected"] = (
            entry["id"] == (
                selected_reference_id if is_reference else selected_item_id
            )
        )
    preview = _atlassian_preview_context(
        connection,
        selected_view=selected_view,
        filters=browse["filters"],
        selected_item_id=selected_item_id,
        selected_reference_id=selected_reference_id,
    )
    if (
        preview is not None
        and preview["state"] == "selected"
        and not any(entry["selected"] for entry in browse["entries"])
    ):
        preview["state"] = "out_of_scope"
        preview["entry"]["eligible"] = False
    add_return_to = _atlassian_add_return_path(
        _atlassian_browse_url(
            selected_view,
            browse["filters"],
            item=selected_item_id,
            reference=selected_reference_id,
        ),
        connection,
    )
    sync_return_to = _atlassian_browse_url(
        selected_view,
        browse["filters"],
        item=selected_item_id,
        reference=selected_reference_id,
    )
    return {
        "request": request,
        "active_page": "atlassian",
        "selected_view": selected_view,
        "browse": browse,
        "explorer_urls": explorer_urls,
        "return_url": return_url,
        "preview": preview,
        "page_title": preview["document_title"],
        "item_count": browse["known_count"],
        "notice": _atlassian_notice(notice),
        "add_return_to": add_return_to,
        "add_url": "/atlassian/add?{}".format(
            urlencode({"return_to": add_return_to})
        ),
        "connections_url": _atlassian_connections_url(
            selected_view if selected_view != "all" else "jira"
        ),
        "add_form_state": {},
        "add_form_error": None,
        "sync_return_to": sync_return_to,
        "sync_report": _verified_atlassian_sync_report(
            sync_receipt, sync_return_to
        ),
    }


async def _bounded_urlencoded_form(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if (
        content_type.split(";", 1)[0].strip().lower()
        != "application/x-www-form-urlencoded"
    ):
        raise AtlassianRegistrationError(
            "invalid-form", "Form encoding is unsupported"
        )
    body = await request.body()
    if len(body) > MAX_ATLASSIAN_FORM_BYTES:
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


def _atlassian_sync_form_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={"code": "invalid-form", "message": message},
    )


async def _bounded_atlassian_sync_return_to(request: Request) -> str:
    content_type = request.headers.get("content-type", "")
    if (
        content_type.split(";", 1)[0].strip().lower()
        != "application/x-www-form-urlencoded"
    ):
        raise _atlassian_sync_form_error("Form encoding is unsupported")
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > ATLASSIAN_SYNC_FORM_BYTES:
            raise _atlassian_sync_form_error("Form is too large")
        chunks.append(chunk)
    try:
        pairs = parse_qsl(
            b"".join(chunks).decode("utf-8"),
            keep_blank_values=True,
            max_num_fields=2,
            encoding="utf-8",
            errors="strict",
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise _atlassian_sync_form_error("Form data is invalid") from exc
    if len(pairs) != 1 or pairs[0][0] != "return_to":
        raise _atlassian_sync_form_error(
            "Sync requires exactly one return_to field"
        )
    return_to = pairs[0][1]
    if len(return_to) > 4_000:
        raise _atlassian_sync_form_error("return_to is too large")
    return return_to


def _optional_form_int(value: Optional[str], field: str) -> Optional[int]:
    if value in {None, ""}:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AtlassianRegistrationError(
            "invalid-form", "{} is invalid".format(field)
        ) from exc
    if parsed < 1 or parsed > MAX_SQLITE_INTEGER:
        raise AtlassianRegistrationError(
            "invalid-form", "{} is invalid".format(field)
        )
    return parsed


@app.get("/atlassian", response_class=HTMLResponse)
def atlassian_page(
    request: Request,
    view: str = Query(default="all"),
    mode: str = Query(default="browse"),
    method: str = Query(default="url"),
    q: str = Query(default="", max_length=300),
    source_instance_id: Optional[int] = Query(default=None, ge=1),
    site_id: Optional[int] = Query(default=None, ge=1),
    space_id: Optional[int] = Query(default=None, ge=1),
    structural_scope: Optional[str] = None,
    item_type: Optional[str] = Query(default=None),
    coverage: Optional[str] = Query(default=None),
    freshness: Optional[str] = Query(default=None),
    attention: Optional[str] = Query(default=None),
    topic_id: Optional[int] = Query(default=None, ge=1),
    tag_id: Optional[int] = Query(default=None, ge=1),
    workstream_id: Optional[int] = Query(default=None, ge=1),
    notice: Optional[str] = Query(default=None),
    catalog_run: Optional[str] = Query(default=None),
    item: Optional[str] = None,
    reference: Optional[str] = None,
    sync_receipt: Optional[str] = None,
):
    if _has_repeated_atlassian_explorer_state(
        list(request.query_params.multi_items())
    ):
        raise HTTPException(
            status_code=400,
            detail="Explorer state fields must not be repeated",
        )
    if mode == "setup":
        if method == "connected":
            return RedirectResponse(
                url=_atlassian_connections_url(
                    view, notice=notice, catalog_run=catalog_run
                ),
                status_code=303,
            )
        legacy_state = {
            "view": view,
            "q": q,
            "source_instance_id": source_instance_id,
            "site_id": site_id,
            "space_id": space_id,
            "structural_scope": structural_scope,
            "item_type": item_type,
            "coverage": coverage,
            "freshness": freshness,
            "attention": attention,
            "topic_id": topic_id,
            "tag_id": tag_id,
            "workstream_id": workstream_id,
            "item": item,
            "reference": reference,
        }
        legacy_state = {
            key: value
            for key, value in legacy_state.items()
            if value is not None and value != ""
        }
        candidate = "/atlassian"
        if legacy_state:
            candidate = "{}?{}".format(candidate, urlencode(legacy_state))
        with connect() as connection:
            return_to = _atlassian_add_return_path(candidate, connection)
        return RedirectResponse(
            url="/atlassian/add?{}".format(
                urlencode({"return_to": return_to})
            ),
            status_code=303,
        )
    selected_view = _normalize_atlassian_view(view)
    try:
        selected_item_id = _atlassian_selected_item_id(item)
        selected_reference_id = _atlassian_selected_reference_id(
            reference
        )
        if (
            selected_item_id is not None
            and selected_reference_id is not None
        ):
            raise AtlassianBrowseError(
                "invalid-selection",
                "Atlassian 선택은 한 번에 하나만 지정할 수 있습니다.",
            )
    except AtlassianBrowseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    browse_values = {
        "q": q,
        "source_instance_id": source_instance_id,
        "site_id": site_id,
        "space_id": space_id,
        "structural_scope": structural_scope,
        "item_type": item_type,
        "coverage": coverage,
        "freshness": freshness,
        "attention": attention,
        "topic_id": topic_id,
        "tag_id": tag_id,
        "workstream_id": workstream_id,
    }
    is_preview_partial = (
        request.headers.get("X-LocalBrain-Partial")
        in {"atlassian-selection-preview", "atlassian-item-preview"}
    )
    with connect() as connection:
        try:
            if is_preview_partial:
                _validate_atlassian_explorer_structure(
                    selected_view, browse_values
                )
                filters = normalize_browse_structure(
                    connection,
                    normalize_browse_filters(
                        {
                            **browse_values,
                            "service": ATLASSIAN_VIEW_SERVICES[selected_view],
                        }
                    ),
                )
                validate_browse_structural_scope(connection, filters)
                preview = _atlassian_preview_context(
                    connection,
                    selected_view=selected_view,
                    filters=filters,
                    selected_item_id=selected_item_id,
                    selected_reference_id=selected_reference_id,
                )
                return templates.TemplateResponse(
                    "_atlassian-item-preview.html",
                    {
                        "request": request,
                        "preview": preview,
                    },
                    headers={"Vary": "X-LocalBrain-Partial"},
                )
            page_context = _atlassian_page_context(
                connection,
                request=request,
                selected_view=selected_view,
                browse_values=browse_values,
                notice=notice,
                selected_item_id=selected_item_id,
                selected_reference_id=selected_reference_id,
                sync_receipt=sync_receipt,
            )
        except AtlassianBrowseError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return templates.TemplateResponse(
        "atlassian.html",
        page_context,
        headers={"Vary": "X-LocalBrain-Partial"},
    )


def _execute_atlassian_evidence_sync() -> dict:
    connection = connect()
    try:
        return sync_atlassian_local_evidence(connection)
    finally:
        connection.close()


@app.post("/atlassian/sync")
async def atlassian_sync(request: Request):
    enhanced = (
        request.headers.get("X-LocalBrain-Partial")
        == ATLASSIAN_SYNC_PARTIAL
    )
    try:
        requested_return_to = await _bounded_atlassian_sync_return_to(request)
    except HTTPException as exc:
        if enhanced:
            return JSONResponse(
                {"detail": exc.detail},
                status_code=422,
                headers={"Vary": "X-LocalBrain-Partial"},
            )
        raise

    with connect() as connection:
        safe_return_to = _atlassian_inventory_return_path(
            requested_return_to, connection
        )

    report = await run_in_threadpool(_execute_atlassian_evidence_sync)

    with connect() as connection:
        safe_return_to = _atlassian_inventory_return_path(
            safe_return_to, connection, post_sync=True
        )

    if enhanced:
        return JSONResponse(
            {"report": report, "return_to": safe_return_to},
            status_code=409 if report["status"] == "busy" else 200,
            headers={"Vary": "X-LocalBrain-Partial"},
        )

    receipt = _store_atlassian_sync_receipt(report, safe_return_to)
    return RedirectResponse(
        url=_atlassian_sync_receipt_url(safe_return_to, receipt),
        status_code=303,
    )


@app.get("/atlassian/add", response_class=HTMLResponse)
def atlassian_add_page(
    request: Request,
    return_to: Optional[str] = None,
):
    with connect() as connection:
        safe_return_to = _atlassian_add_return_path(
            return_to, connection
        )
    return templates.TemplateResponse(
        "atlassian-add.html",
        _atlassian_add_context(
            request,
            return_to=safe_return_to,
        ),
    )


@app.get("/atlassian/connections", response_class=HTMLResponse)
def atlassian_connections_page(
    request: Request,
    view: Optional[str] = None,
    notice: Optional[str] = None,
    catalog_run: Optional[str] = None,
):
    raw_view = str(view or "").strip().lower()
    if raw_view not in {"jira", "wiki"}:
        return RedirectResponse(
            url=_atlassian_connections_url(
                raw_view,
                notice=notice,
                catalog_run=catalog_run,
            ),
            status_code=303,
        )
    with connect() as connection:
        page_context = _atlassian_connections_context(
            connection,
            request=request,
            selected_view=raw_view,
            notice=notice,
            catalog_run=catalog_run,
        )
    return templates.TemplateResponse(
        "atlassian-connections.html", page_context
    )


@app.post("/atlassian/register", response_class=HTMLResponse)
async def atlassian_register(request: Request):
    form = {}
    safe_return_to = "/atlassian#atlassian-add-action"
    try:
        form = await _bounded_urlencoded_form(request)
        with connect() as connection:
            safe_return_to = _atlassian_add_return_path(
                form.get("return_to"), connection
            )
        with transaction() as connection:
            result = register_atlassian_url(
                connection,
                url=form.get("url", ""),
            )
    except AtlassianRegistrationError as exc:
        page_context = _atlassian_add_context(
            request,
            return_to=safe_return_to,
            form_state={"url": form.get("url", "")},
            form_error=str(exc),
        )
        if (
            request.headers.get("X-LocalBrain-Partial")
            == "atlassian-add"
        ):
            return templates.TemplateResponse(
                "_atlassian-add-form.html",
                page_context,
                status_code=422,
                headers={"Vary": "X-LocalBrain-Partial"},
            )
        return templates.TemplateResponse(
            "atlassian-add.html", page_context, status_code=422
        )
    return RedirectResponse(
        url=_atlassian_registration_handoff(result),
        status_code=303,
    )


@app.post("/atlassian/access", response_class=HTMLResponse)
async def atlassian_register_access(request: Request):
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
                "site-required", "접근 경로를 연결할 Site를 선택하세요."
            )
        with transaction() as connection:
            result = register_atlassian_site_access(
                connection,
                site_id=site_id,
                service=service,
                provider_kind=form.get("provider_kind", ""),
                config_ref=form.get("config_ref", ""),
            )
    except AtlassianRegistrationError as exc:
        selected_view = _atlassian_view_for_service(
            form.get("service")
            if form.get("service") in {"jira", "confluence"}
            else "jira"
        )
        with connect() as connection:
            page_context = _atlassian_connections_context(
                connection,
                request=request,
                selected_view=selected_view,
                access_form_state=form,
                access_error=str(exc),
            )
        return templates.TemplateResponse(
            "atlassian-connections.html", page_context, status_code=422
        )
    return RedirectResponse(
        url=_atlassian_connections_url(
            _atlassian_view_for_service(service),
            notice=(
                "connection-created"
                if result["binding_created"]
                else "connection-updated"
            ),
            fragment="atlassian-connection-{}".format(
                result["binding_id"]
            ),
        ),
        status_code=303,
    )


@app.get("/api/atlassian/registration-preview")
def atlassian_registration_preview(
    url: str = Query(min_length=1, max_length=8000),
    service: Optional[str] = Query(default=None),
):
    try:
        with connect() as connection:
            return registration_preview(connection, url=url)
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
        if not (
            1 <= source_instance_id <= MAX_SQLITE_INTEGER
            and 1 <= site_id <= MAX_SQLITE_INTEGER
        ):
            raise AtlassianRegistrationError(
                "invalid-form", "Connection path is invalid"
            )
        form = await _bounded_urlencoded_form(request)
        with transaction() as connection:
            result = update_atlassian_connection(
                connection,
                source_instance_id=source_instance_id,
                site_id=site_id,
                enabled=form.get("enabled") == "1",
                config_ref=form.get("config_ref") or None,
            )
    except AtlassianRegistrationError as exc:
        with connect() as connection:
            authority = None
            if (
                1 <= source_instance_id <= MAX_SQLITE_INTEGER
                and 1 <= site_id <= MAX_SQLITE_INTEGER
            ):
                authority = connection.execute(
                    """
                    SELECT external_source_instances.service,
                           atlassian_site_bindings.id AS binding_id
                    FROM external_source_instances
                    LEFT JOIN atlassian_site_bindings
                      ON atlassian_site_bindings.source_instance_id =
                         external_source_instances.id
                     AND atlassian_site_bindings.site_id = ?
                    WHERE external_source_instances.id = ?
                    """,
                    (site_id, source_instance_id),
                ).fetchone()
            service = (
                authority["service"]
                if authority
                and authority["service"] in {"jira", "confluence"}
                else "jira"
            )
            page_context = _atlassian_connections_context(
                connection,
                request=request,
                selected_view=_atlassian_view_for_service(service),
                connection_form_state=form,
                connection_error=str(exc),
                connection_error_binding_id=(
                    int(authority["binding_id"])
                    if authority and authority["binding_id"] is not None
                    else None
                ),
            )
        return templates.TemplateResponse(
            "atlassian-connections.html", page_context, status_code=422
        )
    return RedirectResponse(
        url=_atlassian_connections_url(
            _atlassian_view_for_service(result["service"]),
            notice="connection-updated",
            fragment="atlassian-connection-{}".format(
                result["binding_id"]
            ),
        ),
        status_code=303,
    )


@app.post("/atlassian/spaces/discover", response_class=HTMLResponse)
async def atlassian_discover_spaces(request: Request):
    form = {}
    try:
        form = await _bounded_urlencoded_form(request)
        site_id = _optional_form_int(form.get("site_id"), "Site")
        if site_id is None:
            raise AtlassianRegistrationError(
                "site-required", "조회할 Site를 선택하세요."
            )
        binding_id = _optional_form_int(
            form.get("binding_id"), "Access binding"
        )
        if binding_id is None:
            raise AtlassianRegistrationError(
                "binding-required", "조회에 사용할 MCP 접근 경로를 선택하세요."
            )
        runner = form.get("runner", "claude")
        if runner not in {"claude", "codex"}:
            raise AtlassianRegistrationError(
                "invalid-runner", "Maintenance runner is invalid"
            )
        with transaction() as connection:
            binding = connection.execute(
                """
                SELECT atlassian_site_bindings.site_id,
                       external_source_instances.id AS source_instance_id,
                       external_source_instances.service,
                       atlassian_sites.normalized_domain
                FROM atlassian_site_bindings
                JOIN external_source_instances
                  ON external_source_instances.id =
                     atlassian_site_bindings.source_instance_id
                JOIN atlassian_sites
                  ON atlassian_sites.id = atlassian_site_bindings.site_id
                WHERE atlassian_site_bindings.id = ?
                  AND atlassian_site_bindings.site_id = ?
                """,
                (binding_id, site_id),
            ).fetchone()
            if not binding:
                raise AtlassianRegistrationError(
                    "binding-mismatch",
                    "선택한 MCP 접근 경로가 현재 Site에 속하지 않습니다.",
                )
            service = str(binding["service"])
            executor = getattr(
                request.app.state, "external_read_executor", None
            )
            if executor is None:
                raise AtlassianRegistrationError(
                    "executor-unavailable",
                    "Approved host-side read executor is not connected",
                )
            if not runner_executable(runner):
                raise AtlassianRegistrationError(
                    "runner-unavailable",
                    "{} runner is unavailable".format(
                        runner.capitalize()
                    ),
                )
            run_id = prepare_space_catalog_run(
                connection,
                site_id=site_id,
                source_instance_id=int(binding["source_instance_id"]),
                target_domain=str(binding["normalized_domain"]),
                runner=runner,
            )
        start_run(run_id, executor)
    except AtlassianRegistrationError as exc:
        with connect() as connection:
            raw_binding_id = str(form.get("binding_id") or "")
            binding_lookup_id = (
                int(raw_binding_id)
                if raw_binding_id.isascii()
                and raw_binding_id.isdigit()
                and 0 < len(raw_binding_id) <= 19
                else -1
            )
            authority = connection.execute(
                """
                SELECT external_source_instances.service
                FROM atlassian_site_bindings
                JOIN external_source_instances
                  ON external_source_instances.id =
                     atlassian_site_bindings.source_instance_id
                WHERE atlassian_site_bindings.id = ?
                """,
                (binding_lookup_id,),
            ).fetchone()
            service = (
                authority["service"]
                if authority
                and authority["service"] in {"jira", "confluence"}
                else "jira"
            )
            page_context = _atlassian_connections_context(
                connection,
                request=request,
                selected_view=_atlassian_view_for_service(service),
                discovery_form_state=form,
                discovery_error=str(exc),
            )
        return templates.TemplateResponse(
            "atlassian-connections.html", page_context, status_code=422
        )
    return RedirectResponse(
        url=_atlassian_connections_url(
            _atlassian_view_for_service(service),
            notice="catalog-started",
            catalog_run=run_id,
            fragment="atlassian-catalog-results",
        ),
        status_code=303,
    )


@app.post("/atlassian/spaces/register", response_class=HTMLResponse)
async def atlassian_register_space_candidate(request: Request):
    form = {}
    try:
        form = await _bounded_urlencoded_form(request)
        catalog_run = str(form.get("catalog_run") or "")
        if not catalog_run or len(catalog_run) > 300:
            raise AtlassianRegistrationError(
                "catalog-required", "Space candidate has no catalog Run"
            )
        with transaction() as connection:
            result = register_space_catalog_candidate(
                connection,
                run_id=catalog_run,
                candidate_key=form.get("candidate_key", ""),
            )
    except AtlassianRegistrationError as exc:
        with connect() as connection:
            run_id = str(form.get("catalog_run") or "")[:300]
            authority = connection.execute(
                """
                SELECT external_sync_runs.service
                FROM external_sync_runs
                WHERE external_sync_runs.maintenance_run_id = ?
                """,
                (run_id,),
            ).fetchone()
            service = (
                authority["service"]
                if authority
                and authority["service"] in {"jira", "confluence"}
                else "jira"
            )
            page_context = _atlassian_connections_context(
                connection,
                request=request,
                selected_view=_atlassian_view_for_service(service),
                catalog_run=run_id,
                candidate_form_state=form,
                candidate_error=str(exc),
            )
        return templates.TemplateResponse(
            "atlassian-connections.html", page_context, status_code=422
        )
    return RedirectResponse(
        url=_atlassian_registration_handoff(result),
        status_code=303,
    )


@app.get("/atlassian/items/{item_id}", response_class=HTMLResponse)
def atlassian_item_page(
    request: Request,
    item_id: int,
    notice: Optional[str] = Query(default=None),
    return_to: Optional[str] = None,
):
    with connect() as connection:
        item = atlassian_item_detail(connection, item_id)
        safe_return_to = _atlassian_inventory_return_path(
            return_to, connection
        )
    if not item:
        raise HTTPException(status_code=404, detail="Atlassian 링크/문서를 찾을 수 없습니다")
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
            "return_to": safe_return_to,
            "refresh_url": "/atlassian/refresh?{}".format(
                urlencode(
                    {
                        "scope": "item",
                        "id": item_id,
                        "return_to": safe_return_to,
                    }
                )
            ),
            "notice": notices.get(notice),
            "form_error": None,
        },
    )


@app.get("/atlassian/references/{reference_id}", response_class=HTMLResponse)
def atlassian_reference_page(
    request: Request,
    reference_id: int,
    return_to: Optional[str] = None,
):
    with connect() as connection:
        reference = atlassian_structure_reference_detail(
            connection, reference_id
        )
        safe_return_to = _atlassian_inventory_return_path(
            return_to, connection
        )
    if not reference:
        return templates.TemplateResponse(
            "atlassian-reference-missing.html",
            {
                "request": request,
                "active_page": "atlassian",
                "return_to": safe_return_to,
            },
            status_code=404,
        )
    return templates.TemplateResponse(
        "atlassian-reference.html",
        {
            "request": request,
            "active_page": "atlassian",
            "reference": reference,
            "return_to": safe_return_to,
        },
    )


@app.post("/atlassian/items/{item_id}/local", response_class=HTMLResponse)
async def atlassian_update_local(request: Request, item_id: int):
    form = {}
    safe_return_to = "/atlassian"
    try:
        form = await _bounded_urlencoded_form(request)
        with transaction() as connection:
            safe_return_to = _atlassian_inventory_return_path(
                form.get("return_to"), connection
            )
            topic_ids = [
                _optional_form_int(value, "Topic")
                for value in form.get("topic_id", [])
            ]
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
                status_code=404, detail="Atlassian 링크/문서를 찾을 수 없습니다"
            ) from exc
        item["note"] = form.get("note", item.get("note") or "")
        item["attention"] = form.get("attention", item["attention"])
        selected_topic_ids = set()
        for raw in form.get("topic_id", []):
            try:
                value = _optional_form_int(raw, "Topic")
            except AtlassianRegistrationError:
                continue
            if value is not None:
                selected_topic_ids.add(value)
        item["selected_topic_ids"] = selected_topic_ids
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
                "return_to": safe_return_to,
                "refresh_url": "/atlassian/refresh?{}".format(
                    urlencode(
                        {
                            "scope": "item",
                            "id": item_id,
                            "return_to": safe_return_to,
                        }
                    )
                ),
                "notice": None,
                "form_error": str(exc),
            },
            status_code=422,
        )
    return RedirectResponse(
        url="/atlassian/items/{}?{}#local-organization".format(
            item_id,
            urlencode(
                {
                    "notice": "local-saved",
                    "return_to": safe_return_to,
                }
            ),
        ),
        status_code=303,
    )


@app.post("/atlassian/items/{item_id}/links", response_class=HTMLResponse)
async def atlassian_add_local_link(request: Request, item_id: int):
    form = {}
    safe_return_to = "/atlassian"
    try:
        form = await _bounded_urlencoded_form(request)
        with transaction() as connection:
            safe_return_to = _atlassian_inventory_return_path(
                form.get("return_to"), connection
            )
            target = form.get("target", "")
            scope_type, raw_scope_id = target.split(":", 1)
            scope_id = _optional_form_int(raw_scope_id, "Link target")
            if (
                scope_type not in {"workstream", "thread"}
                or scope_id is None
            ):
                raise AtlassianBrowseError(
                    "invalid-link", "Select a Workstream or Thread"
                )
            if not atlassian_item_detail(connection, item_id):
                raise AtlassianBrowseError(
                    "item-not-found", "Atlassian 링크/문서를 찾을 수 없습니다"
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
        with connect() as connection:
            item = atlassian_item_detail(connection, item_id)
        if not item:
            raise HTTPException(
                status_code=404, detail="Atlassian 링크/문서를 찾을 수 없습니다"
            ) from exc
        return templates.TemplateResponse(
            "atlassian-item.html",
            {
                "request": request,
                "active_page": "atlassian",
                "item": item,
                "return_to": safe_return_to,
                "refresh_url": "/atlassian/refresh?{}".format(
                    urlencode(
                        {
                            "scope": "item",
                            "id": item_id,
                            "return_to": safe_return_to,
                        }
                    )
                ),
                "notice": None,
                "form_error": str(exc),
            },
            status_code=422,
        )
    return RedirectResponse(
        url="/atlassian/items/{}?{}#local-organization".format(
            item_id,
            urlencode(
                {"notice": "linked", "return_to": safe_return_to}
            ),
        ),
        status_code=303,
    )


@app.post(
    "/atlassian/items/{item_id}/links/{scope_type}/{scope_id}/{link_id}",
    response_class=HTMLResponse,
)
async def atlassian_remove_local_link(
    request: Request,
    item_id: int,
    scope_type: str,
    scope_id: int,
    link_id: int,
):
    form = {}
    safe_return_to = "/atlassian"
    try:
        form = await _bounded_urlencoded_form(request)
        with transaction() as connection:
            safe_return_to = _atlassian_inventory_return_path(
                form.get("return_to"), connection
            )
            if not atlassian_item_detail(connection, item_id):
                raise AtlassianBrowseError(
                    "item-not-found", "Atlassian 링크/문서를 찾을 수 없습니다"
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
        with connect() as connection:
            item = atlassian_item_detail(connection, item_id)
        if not item:
            raise HTTPException(
                status_code=404, detail="Atlassian 링크/문서를 찾을 수 없습니다"
            ) from exc
        return templates.TemplateResponse(
            "atlassian-item.html",
            {
                "request": request,
                "active_page": "atlassian",
                "item": item,
                "return_to": safe_return_to,
                "refresh_url": "/atlassian/refresh?{}".format(
                    urlencode(
                        {
                            "scope": "item",
                            "id": item_id,
                            "return_to": safe_return_to,
                        }
                    )
                ),
                "notice": None,
                "form_error": str(exc),
            },
            status_code=422,
        )
    return RedirectResponse(
        url="/atlassian/items/{}?{}#local-organization".format(
            item_id,
            urlencode(
                {"notice": "unlinked", "return_to": safe_return_to}
            ),
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
                "invalid-retry", "Retry 링크/문서 선택이 올바르지 않습니다"
            ) from exc
        if item_id < 1:
            raise AtlassianRefreshError(
                "invalid-retry", "Retry 링크/문서 선택이 올바르지 않습니다"
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
    return_to: Optional[str] = None,
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
    safe_return_to = (
        _atlassian_inventory_return_path(return_to, connection)
        if return_to is not None
        else preview["scope"]["return_to"]
    )
    return {
        "request": request,
        "active_page": "atlassian",
        "preview": preview,
        "scope_kind": scope_kind,
        "scope_id": scope_id,
        "page": page,
        "run_result": run_result,
        "form_error": form_error,
        "return_to": safe_return_to,
        "return_to_encoded": quote(safe_return_to, safe=""),
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
    return_to: Optional[str] = None,
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
                return_to=return_to,
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
    return_to: Optional[str] = None
    safe_return_to = "/atlassian"
    try:
        form = await _bounded_urlencoded_form(request)
        return_to = str(form["return_to"]) if "return_to" in form else None
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
                _optional_form_int(value, "Atlassian 링크/문서") for value in raw_ids
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
            if return_to is not None:
                safe_return_to = _atlassian_inventory_return_path(
                    return_to, connection
                )
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
                    return_to=return_to,
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
    if return_to is not None:
        query["return_to"] = safe_return_to
    return RedirectResponse(
        url="/atlassian/refresh?{}".format(urlencode(query)),
        status_code=303,
    )


@app.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request):
    with connect() as connection:
        projects = project_activity(connection)
        pagination = session_inventory_page(connection)
        source_scopes = session_source_scopes(connection)
        pinned_sessions = list_all_pinned_sessions(connection)
        page_context = {
            "request": request,
            "active_page": "sessions",
            "selected_inventory": "projects",
            "page_title": "Projects",
            "selected_source": "all",
            "selected_source_label": "전체",
            "selected_workspace": None,
            "stats": dashboard_stats(connection),
            "sessions": pagination["items"],
            "pagination": pagination,
            "pinned_sessions": pinned_sessions,
            "pinned_session_groups": group_pinned_sessions(pinned_sessions),
            "sources": source_inventory(connection),
            "session_source_scopes": source_scopes,
            "projects": projects,
            "project_count": len(projects),
            "missing_count": sum(
                1 for project in projects if not project["exists_now"]
            ),
            "sync_outcome": request.query_params.get("sync")
            if request.query_params.get("sync") in {"complete", "partial", "failed"}
            else None,
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
    report = scan_session_sources()
    outcome = report.get("outcome")
    if outcome not in {"complete", "partial", "failed"}:
        outcome = "failed"
    if view == "projects":
        return RedirectResponse(
            url="/projects?{}".format(urlencode({"sync": outcome})),
            status_code=303,
        )
    params = {"sync": outcome}
    valid_source_keys = {
        item.get("source_key")
        for item in report.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("source_key"), str)
    }
    if source in valid_source_keys:
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
            "sync_outcome": request.query_params.get("sync")
            if request.query_params.get("sync") in {"complete", "partial", "failed"}
            else None,
        },
    )


@app.post("/sources/scan")
def scan_sources_page():
    report = scan_all()
    outcome = report.get("outcome")
    if outcome not in {"complete", "partial", "failed"}:
        outcome = "failed"
    return RedirectResponse(
        url="/sources?{}".format(urlencode({"sync": outcome})),
        status_code=303,
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


def _session_navigation_state(
    connection: sqlite3.Connection,
    source: str,
    workspace: Optional[int],
):
    valid_source_keys = {
        item["source_key"] for item in session_source_scopes(connection)
    }
    selected_source = source if source in valid_source_keys else "all"
    selected_workspace = workspace
    if selected_workspace is not None and connection.execute(
        "SELECT 1 FROM workspaces WHERE id = ?", (selected_workspace,)
    ).fetchone() is None:
        selected_workspace = None
    params = {}
    if selected_source != "all":
        params["source"] = selected_source
    if selected_workspace is not None:
        params["workspace"] = selected_workspace
    query = "?{}".format(urlencode(params)) if params else ""
    return selected_source, selected_workspace, query


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
def show_session(
    request: Request,
    session_id: int,
    source: str = Query(default="all"),
    workspace: Optional[int] = Query(default=None),
):
    if not isinstance(source, str):
        source = "all"
    if isinstance(workspace, bool) or not isinstance(workspace, int):
        workspace = None
    with connect() as connection:
        session = session_detail(connection, session_id)
        if not session or session["session_class"] != "work":
            raise HTTPException(status_code=404, detail="Session not found")
        selected_source, selected_workspace, navigation_query = (
            _session_navigation_state(connection, source, workspace)
        )
        events = conversation_event_views(
            session_conversation_events(connection, session_id)
        )
        parent = session_parent(connection, session_id)
        direct_children = session_subsessions(connection, session_id)
        memberships = entity_memberships(connection, "session", session_id)
        related_context = None
        workflow_available = False
        if session["session_role"] == "primary":
            try:
                workflow_available = workflow_session_is_eligible(
                    connection, session_id
                )
            except Exception:
                workflow_available = False
            try:
                related_context = session_related_context(
                    connection,
                    session_id,
                    session["workspace_id"],
                )
            except Exception:
                related_context = session_related_context_error()

    subsessions = [
        {
            "url": "/sessions/{}{}".format(child["id"], navigation_query),
            "source_kind": child["source_kind"],
            "provider_kind": child["provider_kind"],
            "source_name": child["source_name"],
            "external_id": child["external_id"],
            "title": child["title"],
            "user_message_count": child["user_message_count"],
            "event_count": child["event_count"],
            "last_event_at": child["last_event_at"],
            "source_path": child["source_path"],
        }
        for child in direct_children
    ]
    if session["session_role"] == "primary" and session["provider_kind"] == "claude":
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
                    ) + navigation_query,
                    "source_kind": session["source_kind"],
                    "provider_kind": session["provider_kind"],
                    "source_name": session["source_name"],
                    "external_id": item["external_id"],
                    "title": item["title"],
                    "user_message_count": item["user_message_count"],
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
            "selected_source": selected_source,
            "selected_workspace": selected_workspace,
            "navigation_query": navigation_query,
            "workflow_available": workflow_available,
            "session_list_url": "/sessions{}".format(navigation_query),
            "parent_url": (
                "/sessions/{}{}".format(parent["id"], navigation_query)
                if parent
                else None
            ),
        },
    )


@app.get("/sessions/{session_id}/workflow", response_class=HTMLResponse)
def show_session_workflow(
    request: Request,
    session_id: int,
    workflow_result: Optional[str] = None,
):
    feedback = {
        "corrected": {
            "kind": "success",
            "code": "workflow-corrected",
            "message": "작업 흐름 경계를 사용자 확인으로 반영했습니다.",
        },
        "undone": {
            "kind": "success",
            "code": "workflow-undone",
            "message": "이전 경계를 되돌려 작업 흐름을 다시 투영했습니다.",
        },
    }.get(workflow_result)
    return _workflow_page_response(
        request, session_id, correction_feedback=feedback
    )


def _workflow_page_response(
    request: Request,
    session_id: int,
    *,
    correction_feedback: Optional[dict] = None,
    preferred_status_code: Optional[int] = None,
):
    try:
        with connect() as connection:
            projection = workflow_focus_projection(connection, session_id)
        workflow = workflow_map_view(projection, session_id)
    except Exception:
        workflow = workflow_map_state_view("unexpected-error", session_id)
        status_code = 500
    else:
        status_code = {
            "ready": 200,
            "missing": 404,
            "ineligible": 422,
        }[workflow["status"]]
        if preferred_status_code is not None and workflow["status"] == "ready":
            status_code = preferred_status_code
    return templates.TemplateResponse(
        "session-workflow.html",
        {
            "request": request,
            "active_page": "sessions",
            "workflow": workflow,
            "workflow_correction_feedback": correction_feedback,
        },
        status_code=status_code,
    )


_WORKFLOW_CORRECTION_CONFLICTS = frozenset(
    {
        "conflict",
        "duplicate-active",
        "assertion-not-active",
        "assertion-not-found",
        "requires-active-closure",
        "not-tip",
        "missing-endpoint",
        "cycle",
        "contradictory-boundary",
    }
)

_WORKFLOW_CORRECTION_MESSAGES = {
    "cross-site-request": "다른 사이트에서 시작된 작업 흐름 교정은 받지 않습니다.",
    "invalid-form": "교정 요청 형식을 읽을 수 없습니다.",
    "invalid-request": "교정 요청의 필드가 현재 작업과 맞지 않습니다.",
    "invalid-action": "지원하지 않는 작업 흐름 교정입니다.",
    "invalid-note": "메모는 1,000자 안에서 입력해 주세요.",
    "invalid-close-reason": "지원되는 종료 사유를 선택해 주세요.",
    "conflict": "작업 흐름이 달라졌습니다. 새로 고친 뒤 다시 확인해 주세요.",
    "duplicate-active": "같은 교정이 이미 적용되어 있습니다. 현재 흐름을 다시 확인해 주세요.",
    "assertion-not-active": "이 교정은 더 이상 현재 상태가 아닙니다. 새로 고쳐 주세요.",
    "assertion-not-found": "되돌릴 교정을 찾을 수 없습니다. 새로 고쳐 주세요.",
    "requires-active-closure": "현재 사용자 종료 경계가 없어 다시 열 수 없습니다.",
    "not-tip": "다음 Episode가 있는 지점은 종료할 수 없습니다.",
    "missing-endpoint": "교정할 Episode가 현재 흐름 범위에 없습니다.",
    "cycle": "이 교정은 순환 경로를 만들 수 있어 적용하지 않았습니다.",
    "contradictory-boundary": "도착 Episode에 다른 진입 경계가 있어 적용하지 않았습니다.",
    "self-relation": "같은 Episode를 관계의 양쪽으로 지정할 수 없습니다.",
    "non-forward-time": "관계는 관측 시간상 앞으로 이어져야 합니다.",
    "merge-before-source": "병합 지점은 출발 Episode보다 뒤여야 합니다.",
    "requires-continues": "현재 이어짐 관계에서만 분기로 바꿀 수 있습니다.",
    "invalid-projection": "이 Session에서는 작업 흐름을 교정할 수 없습니다.",
    "correction-failed": "교정을 적용하지 못했습니다. 현재 흐름은 바뀌지 않았습니다.",
}


def _workflow_correction_error(code: str, status_code: int) -> dict:
    safe_code = code if code in _WORKFLOW_CORRECTION_MESSAGES else "correction-failed"
    return {
        "kind": "conflict" if status_code == 409 else "error",
        "code": safe_code,
        "message": _WORKFLOW_CORRECTION_MESSAGES[safe_code],
        "reload": status_code == 409,
    }


def _workflow_vary(response):
    current = response.headers.get("vary")
    values = [item.strip() for item in current.split(",")] if current else []
    if "X-LocalBrain-Partial" not in values:
        values.append("X-LocalBrain-Partial")
    response.headers["Vary"] = ", ".join(item for item in values if item)
    return response


async def _workflow_correction_body(request: Request) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Content length is invalid.", status_code=400
            ) from exc
        if declared_length < 0:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Content length is invalid.", status_code=400
            )
        if declared_length > MAX_WORKFLOW_CORRECTION_FORM_BYTES:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Form is too large.", status_code=400
            )
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_WORKFLOW_CORRECTION_FORM_BYTES:
            raise WorkflowCorrectionRequestError(
                "invalid-form", "Form is too large.", status_code=400
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _workflow_correction_failure_response(
    request: Request,
    session_id: int,
    *,
    code: str,
    status_code: int,
    enhanced: bool,
):
    feedback = _workflow_correction_error(code, status_code)
    if enhanced:
        payload = {
            "status": "error",
            "code": feedback["code"],
            "message": feedback["message"],
        }
        if feedback["reload"]:
            payload["reload_url"] = "/sessions/{}/workflow".format(session_id)
        return _workflow_vary(JSONResponse(payload, status_code=status_code))
    return _workflow_vary(
        _workflow_page_response(
            request,
            session_id,
            correction_feedback=feedback,
            preferred_status_code=status_code,
        )
    )


@app.post("/sessions/{session_id}/workflow/corrections")
async def correct_session_workflow(request: Request, session_id: int):
    enhanced = (
        request.headers.get("x-localbrain-partial")
        == WORKFLOW_CORRECTION_PARTIAL
    )
    try:
        reject_cross_site_workflow_correction(
            request.headers.get("sec-fetch-site")
        )
        body = await _workflow_correction_body(request)
        correction = parse_workflow_correction_form(
            request.headers.get("content-type"), body
        )
    except WorkflowCorrectionRequestError as error:
        return _workflow_correction_failure_response(
            request,
            session_id,
            code=error.code,
            status_code=error.status_code,
            enhanced=enhanced,
        )

    try:
        with transaction() as connection:
            projection = workflow_focus_projection(connection, session_id)
            if correction.action == "undo":
                result = undo_workflow_assertion(
                    connection,
                    projection,
                    assertion_id=correction.assertion_id,
                    expected_revision=correction.expected_revision,
                )
            else:
                result = apply_workflow_assertion(
                    connection,
                    projection,
                    assertion_kind=correction.action,
                    source_episode_key=correction.source_episode_key,
                    target_episode_key=correction.target_episode_key,
                    close_reason=correction.close_reason,
                    note=correction.note,
                    expected_active_assertion_id=(
                        correction.expected_active_assertion_id
                    ),
                    expected_revision=correction.expected_revision,
                )
    except WorkflowAssertionError as error:
        status_code = 409 if error.code in _WORKFLOW_CORRECTION_CONFLICTS else 422
        return _workflow_correction_failure_response(
            request,
            session_id,
            code=error.code,
            status_code=status_code,
            enhanced=enhanced,
        )
    except Exception:
        return _workflow_correction_failure_response(
            request,
            session_id,
            code="correction-failed",
            status_code=500,
            enhanced=enhanced,
        )

    assertion = result["assertion"]
    result_code = (
        "workflow-undone" if correction.action == "undo" else "workflow-corrected"
    )
    result_message = (
        "이전 경계를 되돌려 작업 흐름을 다시 투영했습니다."
        if correction.action == "undo"
        else "작업 흐름 경계를 사용자 확인으로 반영했습니다."
    )
    if enhanced:
        boundary = {
            "kind": str(assertion["boundary_kind"]),
            "source_episode_key": str(assertion["source_episode_key"]),
            "target_episode_key": assertion["target_episode_key"],
        }
        if boundary["kind"] == "relation":
            boundary["relation_id"] = workflow_relation_id(
                boundary["source_episode_key"],
                str(boundary["target_episode_key"]),
            )
        return _workflow_vary(
            JSONResponse(
                {
                    "status": "ok",
                    "code": result_code,
                    "message": result_message,
                    "reload_url": "/sessions/{}/workflow".format(session_id),
                    "boundary": boundary,
                }
            )
        )
    redirect_result = "undone" if correction.action == "undo" else "corrected"
    return _workflow_vary(
        RedirectResponse(
            "/sessions/{}/workflow?workflow_result={}#workflow-correction-feedback".format(
                session_id, redirect_result
            ),
            status_code=303,
        )
    )


@app.get("/sessions/{session_id}/subsessions/{file_name}", response_class=HTMLResponse)
def show_subsession(
    request: Request,
    session_id: int,
    file_name: str,
    source: str = Query(default="all"),
    workspace: Optional[int] = Query(default=None),
):
    if not isinstance(source, str):
        source = "all"
    if isinstance(workspace, bool) or not isinstance(workspace, int):
        workspace = None
    with connect() as connection:
        session = session_detail(connection, session_id)
        if (
            not session
            or session["provider_kind"] != "claude"
            or session["session_role"] != "primary"
        ):
            raise HTTPException(status_code=404, detail="Parent session not found")
        direct_children = session_subsessions(connection, session_id)
        selected_source, selected_workspace, navigation_query = (
            _session_navigation_state(connection, source, workspace)
        )
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
            url="/sessions/{}{}".format(
                normalized_child["id"], navigation_query
            ),
            status_code=303,
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
            "selected_source": selected_source,
            "selected_workspace": selected_workspace,
            "navigation_query": navigation_query,
            "session_list_url": "/sessions{}".format(navigation_query),
            "parent_url": "/sessions/{}{}".format(
                session["id"], navigation_query
            ),
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


def _session_sync_event_stream():
    events = queue.Queue()
    finished = object()

    def publish(event):
        events.put(event)

    def synchronize():
        try:
            report = scan_session_sources(progress=publish)
            events.put({"type": "result", "ok": True, "report": report})
        except Exception:
            events.put(
                {
                    "type": "error",
                    "ok": False,
                    "message": (
                        "Session sources could not be synchronized; "
                        "existing data was retained."
                    ),
                }
            )
        finally:
            events.put(finished)

    worker = threading.Thread(target=synchronize, daemon=True)
    worker.start()
    while True:
        event = events.get()
        if event is finished:
            break
        yield json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"


@app.post("/api/sessions/sync/stream")
def stream_session_sources():
    return StreamingResponse(
        _session_sync_event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "database": str(settings.database_path)}
