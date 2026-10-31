import json
import sqlite3
from typing import List, Optional
from urllib.parse import parse_qs, parse_qsl, quote, urlencode, urlsplit
from fastapi import HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from starlette.concurrency import run_in_threadpool
from localbrain.app.edition import DESKTOP
from localbrain.foundation.paths import home_relative_path
from localbrain.persistence.db import connect, transaction
from localbrain.app.dashboard_queries import dashboard_stats
from localbrain.sessions.queries import (
    project_activity,
    session_conversation_events,
    session_inventory_page,
    session_chart_inventory,
    session_chart_activity,
    session_detail,
    session_id_prefix,
    session_parent,
    session_source_scopes,
    session_subsessions,
)
from localbrain.sources.queries import source_inventory
from localbrain.sessions.pins import (
    SessionPinError,
    group_pinned_sessions,
    list_all_pinned_sessions,
    pin_session as persist_session_pin,
    unpin_session as persist_session_unpin,
)
from localbrain.sessions.chart_preferences import (
    get_project_visibility,
    set_project_visibility,
    validate_hidden_projects,
)
from localbrain.resources.related_context import session_related_context, session_related_context_error
from localbrain.sessions.reading import conversation_event_views
from localbrain.sessions.subagents import list_subagents, load_subagent
from localbrain.sources.profiles import canonical_source_id, profile_map
from localbrain.app.templating import templates


def sessions_page(
    request: Request,
    source: str = Query(default="all"),
    workspace: Optional[int] = Query(default=None),
    page: str = Query(default="1"),
    display: str = Query(default="list"),
):
    selected_display = "chart" if display == "chart" else "list"
    try:
        requested_page = int(page)
        page_is_valid = requested_page > 0
    except (TypeError, ValueError):
        requested_page = 1
        page_is_valid = False
    with connect() as connection:
        source = canonical_source_id(source)
        source_scopes = session_source_scopes(connection)
        source_scope_by_key = {
            str(item["id"]): item for item in source_scopes
        }
        source_is_valid = source == "all" or source in source_scope_by_key
        workspace_is_valid = workspace is None or connection.execute(
            "SELECT 1 FROM workspaces WHERE id = ?", (workspace,)
        ).fetchone() is not None
        if not source_is_valid or not workspace_is_valid:
            params = {}
            if selected_display == "chart":
                params["display"] = "chart"
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
            if selected_display == "chart":
                params["display"] = "chart"
            if selected_source:
                params["source"] = selected_source
            if workspace is not None:
                params["workspace"] = workspace
            return RedirectResponse(
                url="/sessions?{}".format(urlencode(params)), status_code=303
            )
        pinned_sessions = list_all_pinned_sessions(connection)
        chart_project_preference = {"hidden_projects": None, "available": True}
        if selected_display == "chart":
            try:
                chart_project_preference["hidden_projects"] = get_project_visibility(
                    connection, selected_source or "all", workspace
                )
            except (sqlite3.Error, ValueError):
                chart_project_preference["available"] = False
        page_context = {
            "request": request,
            "active_page": "sessions",
            "selected_inventory": "sessions",
            "selected_display": selected_display,
            "chart_project_preference": chart_project_preference,
            "chart_sessions": session_chart_inventory(
                connection, selected_source, workspace
            ) if selected_display == "chart" else [],
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
        metadata = profile_map(connection)
        for item in page_context["chart_sessions"]:
            profile = metadata.get(str(item["source_id"]), {"id": item["source_id"], "color": "gray"})
            item.update(source_id=profile["id"], color=profile["color"])
            if item["project_key"]:
                item["project_path"] = home_relative_path(item["project_key"])
    return templates.TemplateResponse("sessions.html", page_context)


def _save_chart_project_visibility(
    source: str, workspace: Optional[int], hidden_projects: List[str], only_if_missing: bool
) -> List[str]:
    try:
        with transaction() as connection:
            source = canonical_source_id(source)
            if source != "all" and source not in {
                str(item["id"]) for item in session_source_scopes(connection)
            }:
                raise HTTPException(status_code=400, detail="Invalid source scope")
            if workspace is not None and connection.execute(
                "SELECT 1 FROM workspaces WHERE id = ?", (workspace,)
            ).fetchone() is None:
                raise HTTPException(status_code=400, detail="Invalid workspace scope")
            result = set_project_visibility(
                connection, source, workspace, hidden_projects,
                only_if_missing=only_if_missing,
            )
        return result
    except (sqlite3.Error, ValueError) as error:
        raise HTTPException(status_code=503, detail="Project preferences unavailable") from error


async def save_chart_project_visibility(
    request: Request,
    source: str = Query(default="all"),
    workspace: Optional[int] = Query(default=None, ge=-(2**63), le=2**63 - 1),
):
    if request.url.hostname not in {"localhost", "127.0.0.1", "::1"} or request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        raise HTTPException(status_code=400, detail="Local access required")
    origin = request.headers.get("origin")
    if origin and origin != "{}://{}".format(request.url.scheme, request.url.netloc):
        raise HTTPException(status_code=400, detail="Same-origin submission required")
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(status_code=415, detail="JSON submission required")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 65_536:
            raise HTTPException(status_code=413, detail="Project preferences are too large")
        body.extend(chunk)
    try:
        payload = json.loads(body)
        if not isinstance(payload, dict) or set(payload) - {"hidden_projects", "only_if_missing"}:
            raise ValueError("Invalid preference payload")
        hidden_projects = validate_hidden_projects(payload.get("hidden_projects"))
        only_if_missing = payload.get("only_if_missing", False)
        if not isinstance(only_if_missing, bool):
            raise ValueError("Invalid migration option")
    except (ValueError, RecursionError) as error:
        raise HTTPException(status_code=400, detail="Invalid Project preferences") from error
    result = await run_in_threadpool(
        _save_chart_project_visibility, source, workspace, hidden_projects, only_if_missing
    )
    return JSONResponse({"hidden_projects": result}, headers={"Cache-Control": "no-store"})


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


def show_session_chart_activity(session_id: int):
    with connect() as connection:
        activity = session_chart_activity(connection, session_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse(activity, headers={"Cache-Control": "no-store"})


def _session_navigation_state(
    connection: sqlite3.Connection,
    source: str,
    workspace: Optional[int],
):
    source = canonical_source_id(source)
    valid_source_keys = {
        str(item["id"]) for item in session_source_scopes(connection)
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
        short_session_id = session_id_prefix(connection, session["external_id"])
        selected_source, selected_workspace, navigation_query = (
            _session_navigation_state(connection, source, workspace)
        )
        session_list_url = "/sessions{}".format(navigation_query)
        if request.query_params.get("display") == "chart":
            params = {"display": "chart"}
            if selected_source != "all":
                params["source"] = selected_source
            if selected_workspace is not None:
                params["workspace"] = selected_workspace
            return_page = request.query_params.get("page", "1")
            if return_page.isdigit() and int(return_page) > 1:
                params["page"] = return_page
            session_list_url = "/sessions?{}".format(urlencode(params))
        events = conversation_event_views(
            session_conversation_events(connection, session_id)
        )
        parent = session_parent(connection, session_id)
        direct_children = session_subsessions(connection, session_id)
        related_context = None
        workflow_available = False
        if session["session_role"] == "primary":
            try:
                workflow_reader = getattr(request.app.state, "session_workflow_available", None)
                workflow_available = bool(not DESKTOP and workflow_reader and workflow_reader(connection, session_id))
            except Exception:
                workflow_available = False
            try:
                related_context = session_related_context(
                    connection,
                    session_id,
                )
            except Exception:
                related_context = session_related_context_error()

    subsessions = [
        {
            "url": "/sessions/{}{}".format(child["id"], navigation_query),
            "source_id": child["source_id"],
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
                    "source_id": session["source_id"],
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
            "short_session_id": short_session_id,
            "events": events,
            "parent": parent,
            "subsessions": subsessions,
            "related_context": related_context,
            "selected_source": selected_source,
            "selected_workspace": selected_workspace,
            "navigation_query": navigation_query,
            "workflow_available": workflow_available,
            "session_list_url": session_list_url,
            "search_return": request.app.state.search_return(request.query_params["search_return"]) if request.query_params.get("search_return") and getattr(request.app.state, "search_return", None) else None,
            "parent_url": (
                "/sessions/{}{}".format(parent["id"], navigation_query)
                if parent
                else None
            ),
        },
    )


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


def redirect_legacy_subagent_route(session_id: int, file_name: str):
    return RedirectResponse(
        url="/sessions/{}/subsessions/{}".format(session_id, quote(file_name)),
        status_code=308,
    )
