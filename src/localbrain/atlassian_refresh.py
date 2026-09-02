import json
import re
import sqlite3
from typing import Any, Iterable, Mapping, Optional

from .atlassian import (
    AtlassianContractError,
    apply_atlassian_target_result,
    bind_atlassian_remote_identity,
    create_or_reuse_atlassian_stub,
    derive_atlassian_freshness,
    normalize_atlassian_url,
    resolve_atlassian_site_access,
    set_atlassian_item_axes,
)
from .atlassian_browse import project_atlassian_item_container
from .external_access import ExternalAccessError, capability_state
from .external_sync import (
    RESULT_SCHEMA_VERSION,
    ExternalSyncError,
    prepare_external_sync_run,
)
from .atlassian_registration import recognize_registration_url
from .workstreams import utc_now


SCOPE_KINDS = {"item", "space", "thread", "workstream", "all_known"}
DEFAULT_SELECTED_FRESHNESS = {"unknown", "due", "stale", "unavailable"}
PRODUCT_CALL_BUDGET = 20
CONFLUENCE_CATALOG_LIMIT = 200
ITEM_TARGET_PATTERN = re.compile(r"^atlassian-item-([1-9][0-9]*)$")
CATALOG_TARGET_PATTERN = re.compile(
    r"^atlassian-space-catalog-([1-9][0-9]*)-([1-9][0-9]*)$"
)
JIRA_METADATA_FIELDS = (
    "key",
    "summary",
    "status",
    "issuetype",
    "priority",
    "labels",
    "components",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolution",
    "project",
    "parent",
)
CONFLUENCE_METADATA_FIELDS = (
    "title",
    "space",
    "version",
    "labels",
    "ancestors",
)


class AtlassianRefreshError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _fail(code: str, message: str) -> None:
    raise AtlassianRefreshError(code, message)


def _integer(value: Any, label: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool):
        _fail("invalid-input", "{} must be an integer".format(label))
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        _fail("invalid-input", "{} must be an integer".format(label))
    if normalized < minimum:
        _fail("invalid-input", "{} is outside the supported range".format(label))
    return normalized


def _scope_identity(
    connection: sqlite3.Connection,
    scope_kind: str,
    scope_id: Optional[int],
) -> dict:
    if scope_kind not in SCOPE_KINDS:
        _fail("invalid-scope", "Unsupported Atlassian refresh scope")
    if scope_kind == "all_known":
        return {
            "kind": scope_kind,
            "id": None,
            "label": "알려진 모든 Atlassian 링크/문서",
            "return_to": "/atlassian",
        }
    normalized_id = _integer(scope_id, "scope_id")
    if scope_kind == "item":
        row = connection.execute(
            """
            SELECT external_resources.title
            FROM atlassian_items
            JOIN external_resources
              ON external_resources.id =
                 atlassian_items.external_resource_id
            WHERE atlassian_items.external_resource_id = ?
            """,
            (normalized_id,),
        ).fetchone()
        return_to = "/atlassian"
    elif scope_kind == "space":
        row = connection.execute(
            "SELECT name AS title FROM atlassian_spaces WHERE id = ?",
            (normalized_id,),
        ).fetchone()
        return_to = "/atlassian"
    elif scope_kind == "thread":
        row = connection.execute(
            """
            SELECT threads.title, threads.workstream_id
            FROM threads WHERE id = ?
            """,
            (normalized_id,),
        ).fetchone()
        return_to = (
            "/workstreams/{}".format(row["workstream_id"]) if row else "/workstreams"
        )
    else:
        row = connection.execute(
            "SELECT name AS title FROM workstreams WHERE id = ?",
            (normalized_id,),
        ).fetchone()
        return_to = "/workstreams/{}".format(normalized_id)
    if not row:
        _fail("scope-not-found", "The selected refresh scope was not found")
    return {
        "kind": scope_kind,
        "id": normalized_id,
        "label": row["title"],
        "return_to": return_to,
    }


def _scope_item_ids(
    connection: sqlite3.Connection,
    scope_kind: str,
    scope_id: Optional[int],
) -> list[int]:
    if scope_kind == "item":
        return [_integer(scope_id, "scope_id")]
    if scope_kind == "space":
        rows = connection.execute(
            """
            SELECT external_resource_id
            FROM atlassian_items
            WHERE space_id = ?
            ORDER BY external_resource_id
            """,
            (_integer(scope_id, "scope_id"),),
        ).fetchall()
    elif scope_kind == "thread":
        rows = connection.execute(
            """
            SELECT DISTINCT atlassian_items.external_resource_id
            FROM thread_links
            JOIN atlassian_items
              ON atlassian_items.external_resource_id =
                 CAST(thread_links.entity_id AS INTEGER)
            WHERE thread_links.thread_id = ?
              AND thread_links.entity_type = 'external'
            ORDER BY atlassian_items.external_resource_id
            """,
            (_integer(scope_id, "scope_id"),),
        ).fetchall()
    elif scope_kind == "workstream":
        normalized_id = _integer(scope_id, "scope_id")
        rows = connection.execute(
            """
            SELECT external_resource_id
            FROM (
                SELECT atlassian_items.external_resource_id
                FROM workstream_links
                JOIN atlassian_items
                  ON atlassian_items.external_resource_id =
                     CAST(workstream_links.entity_id AS INTEGER)
                WHERE workstream_links.workstream_id = ?
                  AND workstream_links.entity_type = 'external'
                UNION
                SELECT atlassian_items.external_resource_id
                FROM threads
                JOIN thread_links
                  ON thread_links.thread_id = threads.id
                JOIN atlassian_items
                  ON atlassian_items.external_resource_id =
                     CAST(thread_links.entity_id AS INTEGER)
                WHERE threads.workstream_id = ?
                  AND thread_links.entity_type = 'external'
            )
            ORDER BY external_resource_id
            """,
            (normalized_id, normalized_id),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT external_resource_id
            FROM atlassian_items
            ORDER BY external_resource_id
            """
        ).fetchall()
    return [int(row["external_resource_id"]) for row in rows]


def _request_count(service: str, coverage: str) -> int:
    return 2 if service == "jira" and coverage == "indexed" else 1


def _item_rows(
    connection: sqlite3.Connection, item_ids: Iterable[int]
) -> list[dict]:
    normalized_ids = list(dict.fromkeys(int(item_id) for item_id in item_ids))
    if not normalized_ids:
        return []
    placeholders = ",".join("?" for _ in normalized_ids)
    rows = connection.execute(
        """
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.service,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               external_resources.title,
               atlassian_spaces.id AS space_id,
               atlassian_spaces.name AS space_name,
               atlassian_sites.id AS site_id,
               atlassian_sites.normalized_domain,
               external_source_instances.id AS source_instance_id,
               external_source_instances.display_name AS source_name,
               external_source_instances.enabled AS source_enabled,
               atlassian_item_urls.normalized_url AS canonical_url,
               atlassian_item_remote_state.remote_version,
               atlassian_item_remote_state.remote_updated_at,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale,
               atlassian_item_content.source_hash AS content_hash,
               atlassian_item_content.applied_at AS content_applied_at
        FROM atlassian_items
        JOIN external_resources
          ON external_resources.id = atlassian_items.external_resource_id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_items.source_instance_id
        LEFT JOIN atlassian_spaces
          ON atlassian_spaces.id = atlassian_items.space_id
        LEFT JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        LEFT JOIN atlassian_item_remote_state
          ON atlassian_item_remote_state.external_resource_id =
             atlassian_items.external_resource_id
        LEFT JOIN atlassian_item_content
          ON atlassian_item_content.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.external_resource_id IN ({})
        """.format(placeholders),
        tuple(normalized_ids),
    ).fetchall()
    by_id = {int(row["id"]): dict(row) for row in rows}
    if set(by_id) != set(normalized_ids):
        _fail("item-not-found", "선택한 Atlassian 링크/문서를 찾지 못했습니다")
    items = []
    capability_cache = {}
    for item_id in normalized_ids:
        item = by_id[item_id]
        access = None
        if item["source_instance_id"] is None:
            try:
                access = resolve_atlassian_site_access(
                    connection,
                    site_id=int(item["site_id"]),
                    service=item["service"],
                )
            except AtlassianContractError:
                access = None
            if access is not None:
                item["source_instance_id"] = int(access["id"])
                item["source_name"] = access["display_name"]
                item["source_enabled"] = access["enabled"]
        if item["source_instance_id"] is None:
            item["capability_state"] = "unbound"
            item["freshness"] = derive_atlassian_freshness(
                item["service"], item
            )
            item["request_count"] = _request_count(
                item["service"], item["coverage"]
            )
            item["selectable"] = False
            items.append(project_atlassian_item_container(item))
            continue
        source_id = int(item["source_instance_id"])
        if source_id not in capability_cache:
            try:
                capability_cache[source_id] = capability_state(
                    connection, source_id
                )["state"]
            except ExternalAccessError:
                capability_cache[source_id] = "error"
        item["capability_state"] = capability_cache[source_id]
        item["freshness"] = derive_atlassian_freshness(
            item["service"], item
        )
        item["request_count"] = _request_count(
            item["service"], item["coverage"]
        )
        item["selectable"] = bool(
            item["source_enabled"]
            and item["capability_state"] == "current"
            and item["canonical_url"]
        )
        items.append(project_atlassian_item_container(item))
    return items


def refresh_preview(
    connection: sqlite3.Connection,
    *,
    scope_kind: str,
    scope_id: Optional[int] = None,
    page: int = 1,
    selected_ids: Optional[Iterable[int]] = None,
) -> dict:
    scope = _scope_identity(connection, scope_kind, scope_id)
    normalized_page = _integer(page, "page")
    items = _item_rows(
        connection,
        _scope_item_ids(connection, scope_kind, scope_id),
    )
    explicit_selection = (
        set(int(value) for value in selected_ids)
        if selected_ids is not None
        else None
    )
    selected_calls = 0
    for item in items:
        wants_selection = (
            item["id"] in explicit_selection
            if explicit_selection is not None
            else item["freshness"] in DEFAULT_SELECTED_FRESHNESS
        )
        fits = (
            selected_calls + item["request_count"]
            <= PRODUCT_CALL_BUDGET
        )
        item["selected"] = bool(item["selectable"] and wants_selection and fits)
        item["overflow"] = bool(item["selectable"] and wants_selection and not fits)
        if item["selected"]:
            selected_calls += item["request_count"]

    catalog = None
    if scope_kind == "space":
        space = connection.execute(
            """
            SELECT atlassian_spaces.*, atlassian_sites.normalized_domain,
                   external_source_instances.id AS source_instance_id,
                   external_source_instances.display_name AS source_name,
                   external_source_instances.enabled
            FROM atlassian_spaces
            JOIN atlassian_sites
              ON atlassian_sites.id = atlassian_spaces.site_id
            LEFT JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_spaces.source_instance_id
            WHERE atlassian_spaces.id = ?
            """,
            (scope["id"],),
        ).fetchone()
        if not space:
            _fail("scope-not-found", "The selected Space was not found")
        space = dict(space)
        if space["source_instance_id"] is None:
            try:
                access = resolve_atlassian_site_access(
                    connection,
                    site_id=int(space["site_id"]),
                    service=space["service"],
                )
            except AtlassianContractError:
                access = None
            if access is not None:
                space["source_instance_id"] = int(access["id"])
                space["source_name"] = access["display_name"]
                space["enabled"] = access["enabled"]
        if space["service"] == "confluence":
            if space["source_instance_id"] is None:
                state = "unbound"
            else:
                try:
                    state = capability_state(
                        connection, int(space["source_instance_id"])
                    )["state"]
                except ExternalAccessError:
                    state = "error"
            catalog = {
                "space_id": int(space["id"]),
                "space_key": space["space_key"],
                "coverage": space["coverage"],
                "page": normalized_page,
                "limit": CONFLUENCE_CATALOG_LIMIT,
                "request_count": 1,
                "capability_state": state,
                "selectable": bool(
                    space["source_instance_id"] is not None
                    and space["enabled"]
                    and state == "current"
                ),
            }
            catalog["selected"] = bool(
                catalog["selectable"]
                and selected_calls < PRODUCT_CALL_BUDGET
            )
            if catalog["selected"]:
                selected_calls += 1
    return {
        "scope": scope,
        "items": items,
        "catalog": catalog,
        "target_count": len(items),
        "selected_count": sum(item["selected"] for item in items),
        "selected_calls": selected_calls,
        "call_budget": PRODUCT_CALL_BUDGET,
        "page": normalized_page,
    }


def _known(item: Mapping[str, Any]) -> dict:
    return {
        "remote_version": item.get("remote_version"),
        "remote_updated_at": item.get("remote_updated_at"),
        "content_hash": item.get("content_hash"),
    }


def build_item_refresh_target(item: Mapping[str, Any]) -> dict:
    item_id = int(item["id"])
    service = item["service"]
    coverage = item["coverage"]
    try:
        observed_locator = recognize_registration_url(
            item["canonical_url"], expected_service=service
        )
    except Exception as exc:
        raise AtlassianRefreshError(
            getattr(exc, "code", "missing-item-locator"), str(exc)
        ) from exc
    requests = []
    if service == "jira":
        key = item.get("remote_key") or observed_locator.remote_key
        if not isinstance(key, str) or not key:
            _fail(
                "missing-item-locator",
                "Jira refresh requires a stored issue key",
            )
        fields = (
            ["key"]
            if coverage == "reference"
            else list(JIRA_METADATA_FIELDS)
        )
        requests.append(
            {
                "request_id": "atlassian-item-{}-metadata".format(item_id),
                "logical_operation": "jira.search_metadata",
                "arguments": {
                    "jql": 'key = "{}"'.format(key),
                    "fields": fields,
                    "limit": 1,
                },
            }
        )
        target_coverage = ["metadata"]
        if coverage == "indexed":
            target_coverage.append("content")
            requests.append(
                {
                    "request_id": "atlassian-item-{}-content".format(
                        item_id
                    ),
                    "logical_operation": "jira.read_description",
                    "arguments": {"issue_key": key},
                }
            )
        field_allowlist = fields
    else:
        page_id = item.get("remote_id") or observed_locator.remote_id
        if not isinstance(page_id, str) or not page_id:
            _fail(
                "missing-item-locator",
                "Confluence refresh requires a stored Page ID",
            )
        field_allowlist = list(CONFLUENCE_METADATA_FIELDS)
        if coverage == "indexed":
            target_coverage = ["metadata", "content", "hierarchy"]
            requests.append(
                {
                    "request_id": "atlassian-item-{}-content".format(
                        item_id
                    ),
                    "logical_operation": "confluence.read_page",
                    "arguments": {"page_id": page_id},
                }
            )
        else:
            target_coverage = ["metadata"]
            requests.append(
                {
                    "request_id": "atlassian-item-{}-metadata".format(
                        item_id
                    ),
                    "logical_operation": "confluence.search_pages",
                    "arguments": {
                        "cql": 'id = "{}" AND type = page'.format(page_id),
                        "limit": 1,
                    },
                }
            )
    return {
        "target_id": "atlassian-item-{}".format(item_id),
        "source_instance_id": int(item["source_instance_id"]),
        "locator": {"kind": "url", "value": item["canonical_url"]},
        "coverage": target_coverage,
        "field_allowlist": field_allowlist,
        "known": _known(item),
        "requests": requests,
    }


def _catalog_target(
    connection: sqlite3.Connection, catalog: Mapping[str, Any]
) -> dict:
    space = connection.execute(
        """
        SELECT atlassian_spaces.*, atlassian_sites.canonical_base_url,
               external_source_instances.id AS source_instance_id
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_spaces.source_instance_id
        WHERE atlassian_spaces.id = ?
          AND atlassian_spaces.service = 'confluence'
        """,
        (catalog["space_id"],),
    ).fetchone()
    if not space:
        _fail("scope-not-found", "Confluence Space was not found")
    space = dict(space)
    if space["source_instance_id"] is None:
        try:
            access = resolve_atlassian_site_access(
                connection,
                site_id=int(space["site_id"]),
                service="confluence",
            )
        except AtlassianContractError:
            access = None
        if access is None:
            _fail(
                "source-instance-unbound",
                "Confluence Space has no unambiguous access binding",
            )
        space["source_instance_id"] = int(access["id"])
    page = int(catalog["page"])
    return {
        "target_id": "atlassian-space-catalog-{}-{}".format(
            space["id"], page
        ),
        "source_instance_id": int(space["source_instance_id"]),
        "locator": {
            "kind": "source_root",
            "value": space["canonical_url"],
        },
        "coverage": ["metadata"],
        "field_allowlist": ["pages", "next_page", "complete"],
        "known": {},
        "requests": [
            {
                "request_id": "atlassian-space-catalog-{}-{}".format(
                    space["id"], page
                ),
                "logical_operation": "confluence.search_pages",
                "arguments": {
                    "cql": 'space = "{}" AND type = page'.format(
                        space["space_key"]
                    ),
                    "limit": CONFLUENCE_CATALOG_LIMIT,
                    "offset": (page - 1) * CONFLUENCE_CATALOG_LIMIT,
                },
            }
        ],
    }


def prepare_atlassian_refresh_run(
    connection: sqlite3.Connection,
    *,
    scope_kind: str,
    scope_id: Optional[int],
    selected_item_ids: Iterable[int],
    include_catalog: bool = False,
    page: int = 1,
    runner: str = "claude",
    run_root=None,
) -> str:
    selected = list(dict.fromkeys(int(value) for value in selected_item_ids))
    preview = refresh_preview(
        connection,
        scope_kind=scope_kind,
        scope_id=scope_id,
        page=page,
        selected_ids=selected,
    )
    by_id = {int(item["id"]): item for item in preview["items"]}
    if not set(selected).issubset(by_id):
        _fail(
            "selection-outside-scope",
            "선택한 링크/문서가 Refresh 범위를 벗어났습니다",
        )
    targets = []
    selected_calls = 0
    for item_id in selected:
        item = by_id[item_id]
        if not item["selectable"]:
            _fail(
                "target-unavailable",
                "선택한 링크/문서를 현재 연결 상태로 Refresh할 수 없습니다",
            )
        target = build_item_refresh_target(item)
        targets.append(target)
        selected_calls += len(target["requests"])
    if include_catalog:
        catalog = preview["catalog"]
        if not catalog or not catalog["selectable"]:
            _fail(
                "catalog-unavailable",
                "The selected Space catalog cannot be refreshed",
            )
        targets.append(_catalog_target(connection, catalog))
        selected_calls += 1
    if not targets:
        _fail("empty-selection", "Select at least one refresh target")
    if selected_calls > PRODUCT_CALL_BUDGET:
        _fail(
            "call-budget-exceeded",
            "Selected targets exceed the 20-call refresh batch",
        )
    source_ids = {
        int(target["source_instance_id"]) for target in targets
    }
    source_instance_id = (
        next(iter(source_ids)) if len(source_ids) == 1 else None
    )
    workstream_id = (
        int(scope_id) if scope_kind == "workstream" else None
    )
    try:
        return prepare_external_sync_run(
            connection,
            runner=runner,
            source_instance_id=source_instance_id,
            source_kind="atlassian",
            scope_kind=scope_kind,
            targets=targets,
            workstream_id=workstream_id,
            call_budget=PRODUCT_CALL_BUDGET,
            run_root=run_root,
        )
    except (ExternalAccessError, ExternalSyncError) as exc:
        raise AtlassianRefreshError(
            getattr(exc, "code", "refresh-unavailable"), str(exc)
        ) from exc


def _item_application_row(
    connection: sqlite3.Connection, external_resource_id: int
) -> dict:
    row = connection.execute(
        """
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.coverage,
               atlassian_items.site_id,
               atlassian_items.service,
               external_source_instances.id AS source_instance_id,
               atlassian_item_urls.normalized_url AS canonical_url
        FROM atlassian_items
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_items.source_instance_id
        LEFT JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        WHERE atlassian_items.external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone()
    if not row:
        _fail("item-not-found", "Refresh result Item was not found")
    item = dict(row)
    if item["source_instance_id"] is None:
        try:
            access = resolve_atlassian_site_access(
                connection,
                site_id=int(item["site_id"]),
                service=item["service"],
            )
        except AtlassianContractError:
            access = None
        if access is not None:
            item["source_instance_id"] = int(access["id"])
    return item


def _reference_safe_result(target_result: Mapping[str, Any]) -> dict:
    safe = dict(target_result)
    safe_requests = []
    for request in target_result["requests"]:
        value = dict(request)
        value["metadata"] = {}
        value["content"] = None
        value["content_hash"] = None
        safe_requests.append(value)
    safe["requests"] = safe_requests
    return safe


def _catalog_pages(target_result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    values = []
    for request in target_result.get("requests") or []:
        metadata = request.get("metadata")
        if not isinstance(metadata, Mapping):
            continue
        pages = metadata.get("pages")
        if isinstance(pages, list):
            values.extend(
                page for page in pages[:CONFLUENCE_CATALOG_LIMIT]
                if isinstance(page, Mapping)
            )
    return values[:CONFLUENCE_CATALOG_LIMIT]


def _apply_catalog_result(
    connection: sqlite3.Connection,
    target_id: str,
    target_result: Mapping[str, Any],
    target: Mapping[str, Any],
    checked_at: str,
    manifest_source_id: Optional[int],
) -> int:
    match = CATALOG_TARGET_PATTERN.fullmatch(target_id)
    if not match:
        _fail("invalid-target", "Catalog target identity is invalid")
    space_id = int(match.group(1))
    space = connection.execute(
        """
        SELECT atlassian_spaces.*, atlassian_sites.id AS site_id,
               atlassian_sites.canonical_base_url,
               external_source_instances.id AS source_instance_id
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_spaces.source_instance_id
        WHERE atlassian_spaces.id = ?
          AND atlassian_spaces.service = 'confluence'
        """,
        (space_id,),
    ).fetchone()
    if not space:
        _fail("scope-not-found", "Catalog Space was not found")
    space = dict(space)
    if space["source_instance_id"] is None:
        try:
            access = resolve_atlassian_site_access(
                connection,
                site_id=int(space["site_id"]),
                service="confluence",
            )
        except AtlassianContractError:
            access = None
        if access is None:
            _fail(
                "source-instance-unbound",
                "Catalog Space has no unambiguous access binding",
            )
        space["source_instance_id"] = int(access["id"])
    target_source_id = target.get(
        "source_instance_id", manifest_source_id
    )
    if target_source_id != int(space["source_instance_id"]):
        _fail(
            "source-instance-mismatch",
            "Catalog target Source Instance changed",
        )
    if target_result["outcome"] not in {"resolved", "unchanged", "changed"}:
        return 0
    created = 0
    for page in _catalog_pages(target_result):
        page_id = page.get("id") or page.get("remote_id")
        title = page.get("title") or page.get("name")
        if not isinstance(page_id, (str, int)) or not str(page_id).strip():
            continue
        page_id = str(page_id).strip()
        if not isinstance(title, str) or not title.strip():
            title = "Confluence Page {}".format(page_id)
        raw_url = page.get("url") or page.get("canonical_url")
        if not isinstance(raw_url, str) or not raw_url.strip():
            raw_url = "{}/spaces/{}/pages/{}".format(
                space["canonical_base_url"].rstrip("/"),
                space["space_key"],
                page_id,
            )
        try:
            normalized = normalize_atlassian_url(raw_url)
        except AtlassianContractError:
            continue
        existing = connection.execute(
            """
            SELECT atlassian_items.external_resource_id
            FROM atlassian_item_urls
            JOIN atlassian_items
              ON atlassian_items.external_resource_id =
                 atlassian_item_urls.external_resource_id
            WHERE atlassian_item_urls.site_id = ?
              AND atlassian_item_urls.normalized_url = ?
            """,
            (space["site_id"], normalized.normalized_url),
        ).fetchone()
        try:
            item = create_or_reuse_atlassian_stub(
                connection,
                source_instance_id=int(space["source_instance_id"]),
                url=normalized.normalized_url,
                title=title.strip()[:500],
            )
        except AtlassianContractError as exc:
            raise AtlassianRefreshError(exc.code, str(exc)) from exc
        item_id = int(item["external_resource_id"])
        if int(item["site_id"]) != int(space["site_id"]):
            _fail(
                "site-mismatch",
                "Catalog Page resolved outside the registered Space Site",
            )
        connection.execute(
            """
            UPDATE atlassian_items SET space_id = ?, updated_at = ?
            WHERE external_resource_id = ?
            """,
            (space_id, checked_at, item_id),
        )
        try:
            bind_atlassian_remote_identity(
                connection,
                item_id,
                remote_id=page_id,
                canonical_url=normalized.normalized_url,
                space_id=space_id,
                confirmed_at=checked_at,
            )
        except AtlassianContractError as exc:
            raise AtlassianRefreshError(exc.code, str(exc)) from exc
        if existing is None:
            set_atlassian_item_axes(
                connection, item_id, coverage="indexed"
            )
            connection.execute(
                """
                INSERT INTO atlassian_item_remote_state(
                    external_resource_id, metadata_json,
                    projection_stale, updated_at
                ) VALUES (?, '{}', 1, ?)
                ON CONFLICT(external_resource_id) DO UPDATE SET
                    projection_stale = 1,
                    updated_at = excluded.updated_at
                """,
                (item_id, checked_at),
            )
            created += 1
    return created


def apply_atlassian_refresh_result(
    connection: sqlite3.Connection,
    *,
    manifest: Mapping[str, Any],
    result: Mapping[str, Any],
    checked_at: Optional[str] = None,
) -> dict:
    if result.get("schema") != RESULT_SCHEMA_VERSION:
        _fail("invalid-result", "External sync result schema is unsupported")
    if result.get("run_id") != manifest.get("run_id"):
        _fail("invalid-result", "Refresh result Run ID does not match")
    manifest_targets = {
        target["target_id"]: target for target in manifest.get("targets") or []
    }
    result_targets = result.get("targets")
    if not isinstance(result_targets, list):
        _fail("invalid-result", "Refresh result targets are invalid")
    by_id = {}
    for target_result in result_targets:
        target_id = (
            target_result.get("target_id")
            if isinstance(target_result, Mapping)
            else None
        )
        if (
            not isinstance(target_id, str)
            or target_id in by_id
            or target_id not in manifest_targets
        ):
            _fail("invalid-result", "Refresh result target mapping is invalid")
        if target_result.get("locator") != manifest_targets[target_id]["locator"]:
            _fail("invalid-result", "Refresh result locator changed")
        by_id[target_id] = target_result
    if set(by_id) != set(manifest_targets):
        _fail("invalid-result", "Refresh result target set is incomplete")

    applied_at = checked_at or utc_now()
    applied_items = 0
    cataloged_items = 0
    connection.execute("SAVEPOINT atlassian_refresh_apply")
    try:
        for target_id, target in manifest_targets.items():
            target_result = by_id[target_id]
            item_match = ITEM_TARGET_PATTERN.fullmatch(target_id)
            if item_match:
                item_id = int(item_match.group(1))
                item = _item_application_row(connection, item_id)
                target_source_id = target.get(
                    "source_instance_id",
                    manifest.get("source", {}).get("instance_id"),
                )
                if target_source_id != int(item["source_instance_id"]):
                    _fail(
                        "source-instance-mismatch",
                        "Refresh target Source Instance changed",
                    )
                if target["locator"]["value"] != item["canonical_url"]:
                    _fail(
                        "locator-mismatch",
                        "Refresh target canonical URL changed",
                    )
                application_result = (
                    _reference_safe_result(target_result)
                    if item["coverage"] == "reference"
                    else target_result
                )
                try:
                    apply_atlassian_target_result(
                        connection,
                        item_id,
                        application_result,
                        checked_at=applied_at,
                    )
                except AtlassianContractError as exc:
                    raise AtlassianRefreshError(exc.code, str(exc)) from exc
                applied_items += 1
            elif CATALOG_TARGET_PATTERN.fullmatch(target_id):
                cataloged_items += _apply_catalog_result(
                    connection,
                    target_id,
                    target_result,
                    target,
                    applied_at,
                    manifest.get("source", {}).get("instance_id"),
                )
            else:
                _fail("invalid-target", "Refresh target type is unsupported")
    except Exception:
        connection.execute("ROLLBACK TO atlassian_refresh_apply")
        connection.execute("RELEASE atlassian_refresh_apply")
        raise
    connection.execute("RELEASE atlassian_refresh_apply")
    return {
        "applied_items": applied_items,
        "cataloged_items": cataloged_items,
        "checked_at": applied_at,
    }


def is_atlassian_refresh_manifest(manifest: Mapping[str, Any]) -> bool:
    targets = manifest.get("targets")
    return bool(
        isinstance(targets, list)
        and targets
        and all(
            isinstance(target.get("target_id"), str)
            and (
                ITEM_TARGET_PATTERN.fullmatch(target["target_id"])
                or CATALOG_TARGET_PATTERN.fullmatch(target["target_id"])
            )
            for target in targets
            if isinstance(target, Mapping)
        )
        and all(isinstance(target, Mapping) for target in targets)
    )


def refresh_run_result(
    connection: sqlite3.Connection, run_id: str
) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT maintenance_runs.status,
               maintenance_runs.structured_result_json,
               external_sync_runs.requested_scope_kind,
               external_sync_runs.service
        FROM maintenance_runs
        JOIN external_sync_runs
          ON external_sync_runs.maintenance_run_id = maintenance_runs.id
        WHERE maintenance_runs.id = ?
          AND maintenance_runs.task_type = 'external_source_sync'
        """,
        (run_id,),
    ).fetchone()
    if not row:
        return None
    targets = []
    if row["structured_result_json"]:
        try:
            payload = json.loads(row["structured_result_json"])
        except json.JSONDecodeError:
            payload = {}
        for target in payload.get("targets") or []:
            target_id = target.get("target_id")
            match = (
                ITEM_TARGET_PATTERN.fullmatch(target_id)
                if isinstance(target_id, str)
                else None
            )
            targets.append(
                {
                    "target_id": target_id,
                    "item_id": int(match.group(1)) if match else None,
                    "outcome": target.get("outcome"),
                }
            )
    return {
        "run_id": run_id,
        "status": row["status"],
        "scope_kind": row["requested_scope_kind"],
        "service": row["service"],
        "targets": targets,
        "retry_item_ids": [
            target["item_id"]
            for target in targets
            if target["item_id"] is not None
            and target["outcome"] in {
                "unavailable",
                "not_found",
                "error",
            }
        ],
    }
