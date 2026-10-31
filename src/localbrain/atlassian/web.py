import json
import re
import secrets
import threading
import time
from collections import OrderedDict
from typing import Iterable, Optional
from urllib.parse import parse_qsl, quote, urlencode, urlsplit
from fastapi import HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from starlette.concurrency import run_in_threadpool
from localbrain.atlassian.registration import (
    AtlassianRegistrationError,
    prepare_space_catalog_run,
    registration_preview,
    register_atlassian_site_access,
    register_atlassian_url,
    register_space_catalog_candidate,
    registered_scope_overview,
    registration_sites,
    space_catalog_candidates,
    update_atlassian_connection,
)
from localbrain.atlassian.refresh import (
    AtlassianRefreshError,
    prepare_atlassian_refresh_run,
    refresh_preview,
    refresh_run_result,
)
from localbrain.atlassian.browse import (
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
from localbrain.atlassian.evidence_sync import sync_atlassian_local_evidence
from localbrain.atlassian.evidence import atlassian_url_container_hint
from localbrain.persistence.db import connect, transaction
from localbrain.atlassian.runner import start_run
from localbrain.foundation.agent_cli import runner_executable
from localbrain.app.templating import templates
from localbrain.app.forms import FormError, bounded_urlencoded_form


ATLASSIAN_SYNC_PARTIAL = "atlassian-local-evidence-sync"


ATLASSIAN_SYNC_RECEIPT_TTL_SECONDS = 5 * 60


ATLASSIAN_SYNC_RECEIPT_LIMIT = 32


ATLASSIAN_SYNC_FORM_BYTES = 8 * 1024


_ATLASSIAN_SYNC_RECEIPTS = OrderedDict()


_ATLASSIAN_SYNC_RECEIPT_LOCK = threading.Lock()


_ATLASSIAN_SYNC_RECEIPT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32}$")


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
    try:
        return await bounded_urlencoded_form(
            request, multiple_fields={"item_id", "topic_id"},
        )
    except FormError as exc:
        raise AtlassianRegistrationError(exc.code, str(exc)) from exc


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
                    request, "_atlassian-item-preview.html",
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
        request, "atlassian.html",
        page_context,
        headers={"Vary": "X-LocalBrain-Partial"},
    )


def _execute_atlassian_evidence_sync() -> dict:
    connection = connect()
    try:
        return sync_atlassian_local_evidence(connection)
    finally:
        connection.close()


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


def atlassian_add_page(
    request: Request,
    return_to: Optional[str] = None,
):
    with connect() as connection:
        safe_return_to = _atlassian_add_return_path(
            return_to, connection
        )
    return templates.TemplateResponse(
        request, "atlassian-add.html",
        _atlassian_add_context(
            request,
            return_to=safe_return_to,
        ),
    )


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
        request, "atlassian-connections.html", page_context
    )


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
                request, "_atlassian-add-form.html",
                page_context,
                status_code=422,
                headers={"Vary": "X-LocalBrain-Partial"},
            )
        return templates.TemplateResponse(
            request, "atlassian-add.html", page_context, status_code=422
        )
    return RedirectResponse(
        url=_atlassian_registration_handoff(result),
        status_code=303,
    )


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
            request, "atlassian-connections.html", page_context, status_code=422
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
            request, "atlassian-connections.html", page_context, status_code=422
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
            request, "atlassian-connections.html", page_context, status_code=422
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
            request, "atlassian-connections.html", page_context, status_code=422
        )
    return RedirectResponse(
        url=_atlassian_registration_handoff(result),
        status_code=303,
    )


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
        request, "atlassian-item.html",
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
            request, "atlassian-reference-missing.html",
            {
                "request": request,
                "active_page": "atlassian",
                "return_to": safe_return_to,
            },
            status_code=404,
        )
    return templates.TemplateResponse(
        request, "atlassian-reference.html",
        {
            "request": request,
            "active_page": "atlassian",
            "reference": reference,
            "return_to": safe_return_to,
        },
    )


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
            request, "atlassian-item.html",
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
            request.app.state.add_organization_link(
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
            request, "atlassian-item.html",
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
            request.app.state.remove_organization_link(connection, scope_type, scope_id, link_id)
    except (AtlassianBrowseError, ValueError) as exc:
        with connect() as connection:
            item = atlassian_item_detail(connection, item_id)
        if not item:
            raise HTTPException(
                status_code=404, detail="Atlassian 링크/문서를 찾을 수 없습니다"
            ) from exc
        return templates.TemplateResponse(
            request, "atlassian-item.html",
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
        request, "atlassian-refresh.html", page_context
    )


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
            request, "atlassian-refresh.html", page_context, status_code=422
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
