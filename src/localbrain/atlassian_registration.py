import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import parse_qs, urlsplit

from .atlassian import (
    AtlassianContractError,
    create_or_reuse_atlassian_stub,
    derive_atlassian_freshness,
    normalize_atlassian_url,
    register_atlassian_site,
    register_atlassian_space,
)
from .external_access import (
    ExternalAccessError,
    bind_source_instance_config_ref,
    capability_state,
    register_source_instance,
)
from .external_sync import ExternalSyncError, prepare_external_sync_run
from .workstreams import utc_now


JIRA_KEY = r"[A-Z][A-Z0-9_]*-[1-9][0-9]*"
JIRA_ISSUE_PATTERNS = (
    re.compile(r"/(?:browse|issues)/({})(?:/|$)".format(JIRA_KEY), re.I),
    re.compile(r"/projects/[^/]+/issues/({})(?:/|$)".format(JIRA_KEY), re.I),
)
JIRA_SPACE_PATTERNS = (
    re.compile(r"/(?:jira/software/c/)?projects/([A-Z][A-Z0-9_]*)(?:/|$)", re.I),
    re.compile(
        r"/plugins/servlet/project-config/([A-Z][A-Z0-9_]*)(?:/|$)", re.I
    ),
)
CONFLUENCE_PAGE_PATTERN = re.compile(
    r"/(?:wiki/)?(?:spaces/([^/]+)/)?pages/(\d+)(?:/|$)", re.I
)
CONFLUENCE_SPACE_PATTERN = re.compile(
    r"/(?:wiki/)?spaces/([^/]+)(?:/(?:overview)?)?/?$", re.I
)
CONFLUENCE_DISPLAY_SPACE_PATTERN = re.compile(
    r"/(?:wiki/)?display/([^/]+)/?$", re.I
)
CATALOG_MAX_CANDIDATES = 200
PROVIDER_LABELS = {
    "atlassian_cloud": "공식 Atlassian MCP",
    "mcp_gateway": "회사 MCP Gateway",
}


class AtlassianRegistrationError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RegistrationLocator:
    service: str
    kind: str
    normalized_url: str
    normalized_domain: str
    remote_id: Optional[str] = None
    remote_key: Optional[str] = None
    space_key: Optional[str] = None


def _fail(code: str, message: str) -> None:
    raise AtlassianRegistrationError(code, message)


def _bounded_text(
    value: Any,
    field: str,
    maximum: int,
    *,
    optional: bool = False,
) -> Optional[str]:
    if optional and (
        value is None
        or (isinstance(value, str) and not value.strip())
    ):
        return None
    if not isinstance(value, str) or not value.strip():
        _fail("invalid-input", "{} is required".format(field))
    cleaned = value.strip()
    if len(cleaned) > maximum:
        _fail("invalid-input", "{} is too long".format(field))
    return cleaned


def recognize_registration_url(
    url: str, *, expected_service: Optional[str] = None
) -> RegistrationLocator:
    try:
        normalized = normalize_atlassian_url(url)
    except AtlassianContractError as exc:
        raise AtlassianRegistrationError(exc.code, str(exc)) from exc
    parsed = urlsplit(normalized.normalized_url)
    path = parsed.path or "/"
    if "/rest/" in path.lower():
        _fail("unsupported-url", "REST endpoints cannot be registered")
    query = parse_qs(parsed.query)

    for pattern in JIRA_ISSUE_PATTERNS:
        match = pattern.search(path)
        if match:
            locator = RegistrationLocator(
                service="jira",
                kind="item",
                normalized_url=normalized.normalized_url,
                normalized_domain=normalized.normalized_domain,
                remote_key=match.group(1).upper(),
            )
            break
    else:
        locator = None
    if locator is None:
        for name in ("selectedIssue", "issueKey", "key"):
            values = query.get(name) or query.get(name.lower())
            candidate = values[0].strip().upper() if values else ""
            if re.fullmatch(JIRA_KEY, candidate):
                locator = RegistrationLocator(
                    service="jira",
                    kind="item",
                    normalized_url=normalized.normalized_url,
                    normalized_domain=normalized.normalized_domain,
                    remote_key=candidate,
                )
                break

    if locator is None:
        page_match = CONFLUENCE_PAGE_PATTERN.search(path)
        page_id = page_match.group(2) if page_match else None
        space_key = page_match.group(1) if page_match else None
        if page_id is None:
            for name in ("pageId", "pageid"):
                values = query.get(name)
                if values and values[0].strip().isdigit():
                    page_id = values[0].strip()
                    break
        if page_id is not None:
            locator = RegistrationLocator(
                service="confluence",
                kind="item",
                normalized_url=normalized.normalized_url,
                normalized_domain=normalized.normalized_domain,
                remote_id=page_id,
                space_key=space_key,
            )

    if locator is None:
        for pattern in JIRA_SPACE_PATTERNS:
            match = pattern.search(path)
            if match:
                locator = RegistrationLocator(
                    service="jira",
                    kind="space",
                    normalized_url=normalized.normalized_url,
                    normalized_domain=normalized.normalized_domain,
                    space_key=match.group(1).upper(),
                )
                break

    if locator is None:
        match = CONFLUENCE_SPACE_PATTERN.search(path)
        if not match:
            match = CONFLUENCE_DISPLAY_SPACE_PATTERN.search(path)
        if match:
            locator = RegistrationLocator(
                service="confluence",
                kind="space",
                normalized_url=normalized.normalized_url,
                normalized_domain=normalized.normalized_domain,
                space_key=match.group(1),
            )

    if locator is None:
        _fail(
            "unsupported-url",
            "Use a Jira issue/project URL or Confluence Page/Space URL",
        )
    if expected_service and locator.service != expected_service:
        _fail(
            "service-mismatch",
            "The URL does not belong to the selected Atlassian service",
        )
    return locator


def registration_sites(
    connection: sqlite3.Connection, service: str
) -> list[dict]:
    if service not in {"jira", "confluence"}:
        _fail("invalid-service", "Unsupported Atlassian service")
    rows = connection.execute(
        """
        SELECT atlassian_sites.id AS site_id,
               atlassian_sites.normalized_domain,
               atlassian_sites.canonical_base_url,
               atlassian_sites.display_name AS site_display_name,
               external_source_instances.id AS source_instance_id,
               external_source_instances.instance_key,
               external_source_instances.display_name,
               external_source_instances.display_name AS source_display_name,
               external_source_instances.provider_kind,
               external_source_instances.enabled,
               CASE WHEN external_source_instances.config_ref IS NULL
                    THEN 0 ELSE 1 END AS config_bound
        FROM atlassian_sites
        JOIN external_source_instances
          ON external_source_instances.id = atlassian_sites.source_instance_id
        WHERE external_source_instances.service = ?
        ORDER BY external_source_instances.display_name,
                 atlassian_sites.normalized_domain,
                 atlassian_sites.id
        """,
        (service,),
    ).fetchall()
    values = []
    for row in rows:
        item = dict(row)
        try:
            state = capability_state(connection, item["source_instance_id"])
        except ExternalAccessError:
            state = {"state": "error", "checked_at": None}
        item["capability_state"] = state["state"]
        item["capability_checked_at"] = state.get("checked_at")
        item["provider_label"] = PROVIDER_LABELS.get(
            item["provider_kind"], item["provider_kind"]
        )
        values.append(item)
    return values


def registration_preview(
    connection: sqlite3.Connection,
    *,
    url: str,
    expected_service: Optional[str] = None,
) -> dict:
    locator = recognize_registration_url(
        url, expected_service=expected_service
    )
    matches = [
        {
            "site_id": site["site_id"],
            "source_instance_id": site["source_instance_id"],
            "source_name": site["source_display_name"],
            "site_name": site["site_display_name"],
            "normalized_domain": site["normalized_domain"],
            "provider_kind": site["provider_kind"],
            "provider_label": site["provider_label"],
            "enabled": bool(site["enabled"]),
            "config_bound": bool(site["config_bound"]),
            "capability_state": site["capability_state"],
        }
        for site in registration_sites(connection, locator.service)
        if site["normalized_domain"] == locator.normalized_domain
    ]
    identifier = (
        locator.remote_key or locator.remote_id or locator.space_key
    )
    return {
        "service": locator.service,
        "kind": locator.kind,
        "normalized_url": locator.normalized_url,
        "normalized_domain": locator.normalized_domain,
        "identifier": identifier,
        "matches": matches,
        "suggested_site_name": locator.normalized_domain.split(".", 1)[0],
        "requires_connection": not any(
            match["enabled"] for match in matches
        ),
        "ambiguous": len(
            [match for match in matches if match["enabled"]]
        )
        > 1,
    }


def _instance_key_base(
    provider_kind: str, service: str, normalized_domain: str
) -> str:
    value = "{}-{}-{}".format(
        provider_kind.replace("_", "-"),
        service,
        normalized_domain,
    ).lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("._-")
    return value[:128]


def _new_instance_key(
    connection: sqlite3.Connection,
    *,
    provider_kind: str,
    service: str,
    normalized_domain: str,
    config_ref: Optional[str],
) -> str:
    base = _instance_key_base(
        provider_kind, service, normalized_domain
    )
    existing = connection.execute(
        """
        SELECT provider_kind, service, config_ref
        FROM external_source_instances
        WHERE instance_key = ?
        """,
        (base,),
    ).fetchone()
    requested_identity = (provider_kind, service, config_ref)
    if not existing or (
        existing["provider_kind"],
        existing["service"],
        existing["config_ref"],
    ) == requested_identity:
        return base
    digest = hashlib.sha256(
        "{}|{}|{}|{}".format(
            provider_kind,
            service,
            normalized_domain,
            config_ref or "unbound",
        ).encode("utf-8")
    ).hexdigest()[:8]
    candidate = "{}-{}".format(base[:119].rstrip("-"), digest)
    collision = connection.execute(
        """
        SELECT provider_kind, service, config_ref
        FROM external_source_instances
        WHERE instance_key = ?
        """,
        (candidate,),
    ).fetchone()
    if collision and (
        collision["provider_kind"],
        collision["service"],
        collision["config_ref"],
    ) != requested_identity:
        _fail(
            "source-key-collision",
            "A compatible local Source Instance key could not be generated",
        )
    return candidate


def _default_source_name(
    provider_kind: str, normalized_domain: str
) -> str:
    return "{} · {}".format(
        PROVIDER_LABELS.get(provider_kind, provider_kind),
        normalized_domain,
    )


def register_atlassian_url_with_connection(
    connection: sqlite3.Connection,
    *,
    url: str,
    service: str,
    provider_kind: str,
    source_name: Optional[str] = None,
    site_name: Optional[str] = None,
    config_ref: Optional[str] = None,
    title: Optional[str] = None,
) -> dict:
    locator = recognize_registration_url(url, expected_service=service)
    if provider_kind not in PROVIDER_LABELS:
        _fail(
            "invalid-provider",
            "Select an official Atlassian MCP or company MCP Gateway access path",
        )
    source_name = _bounded_text(
        source_name, "source_name", 160, optional=True
    ) or _default_source_name(provider_kind, locator.normalized_domain)
    site_name = _bounded_text(
        site_name, "site_name", 300, optional=True
    ) or locator.normalized_domain.split(".", 1)[0]
    config_ref = _bounded_text(
        config_ref, "config_ref", 300, optional=True
    )
    base_url = urlsplit(locator.normalized_url)
    canonical_base_url = "{}://{}".format(
        base_url.scheme, base_url.netloc
    )
    existing_sources = connection.execute(
        """
        SELECT external_source_instances.*
        FROM external_source_instances
        JOIN atlassian_sites
          ON atlassian_sites.source_instance_id =
             external_source_instances.id
        WHERE external_source_instances.provider_kind = ?
          AND external_source_instances.service = ?
          AND external_source_instances.config_ref IS ?
          AND atlassian_sites.normalized_domain = ?
        ORDER BY external_source_instances.id
        """,
        (
            provider_kind,
            service,
            config_ref,
            locator.normalized_domain,
        ),
    ).fetchall()
    if len(existing_sources) > 1:
        _fail(
            "ambiguous-source",
            "More than one compatible Source Instance exists; select its Site explicitly",
        )
    connection.execute("SAVEPOINT atlassian_connection_onboarding")
    try:
        if existing_sources:
            source = dict(existing_sources[0])
            if not bool(source["enabled"]):
                _fail(
                    "source-instance-disabled",
                    "The compatible Source Instance is disabled; edit it before reuse",
                )
            source_created = False
        else:
            instance_key = _new_instance_key(
                connection,
                provider_kind=provider_kind,
                service=service,
                normalized_domain=locator.normalized_domain,
                config_ref=config_ref,
            )
            before_source = connection.execute(
                """
                SELECT id FROM external_source_instances
                WHERE instance_key = ?
                """,
                (instance_key,),
            ).fetchone()
            source = register_source_instance(
                connection,
                instance_key=instance_key,
                provider_kind=provider_kind,
                service=service,
                display_name=source_name,
                config_ref=config_ref,
            )
            source_created = before_source is None
        before_site = connection.execute(
            """
            SELECT id FROM atlassian_sites
            WHERE source_instance_id = ? AND normalized_domain = ?
            """,
            (source["id"], locator.normalized_domain),
        ).fetchone()
        site = register_atlassian_site(
            connection,
            source_instance_id=int(source["id"]),
            base_url=canonical_base_url,
            display_name=site_name,
        )
        result = register_atlassian_url(
            connection,
            url=locator.normalized_url,
            service=service,
            site_id=int(site["id"]),
            title=title,
        )
    except (AtlassianContractError, ExternalAccessError) as exc:
        connection.execute(
            "ROLLBACK TO atlassian_connection_onboarding"
        )
        connection.execute(
            "RELEASE atlassian_connection_onboarding"
        )
        raise AtlassianRegistrationError(
            getattr(exc, "code", "connection-setup-failed"), str(exc)
        ) from exc
    except Exception:
        connection.execute(
            "ROLLBACK TO atlassian_connection_onboarding"
        )
        connection.execute(
            "RELEASE atlassian_connection_onboarding"
        )
        raise
    else:
        connection.execute(
            "RELEASE atlassian_connection_onboarding"
        )
    return {
        **result,
        "source_instance_id": int(source["id"]),
        "site_id": int(site["id"]),
        "source_created": source_created,
        "site_created": before_site is None,
    }


def update_atlassian_connection(
    connection: sqlite3.Connection,
    *,
    source_instance_id: int,
    site_id: int,
    source_name: str,
    site_name: str,
    enabled: bool,
    config_ref: Optional[str] = None,
) -> dict:
    row = connection.execute(
        """
        SELECT external_source_instances.*,
               atlassian_sites.id AS site_id,
               atlassian_sites.canonical_base_url,
               atlassian_sites.display_name AS site_display_name
        FROM external_source_instances
        JOIN atlassian_sites
          ON atlassian_sites.source_instance_id =
             external_source_instances.id
        WHERE external_source_instances.id = ?
          AND atlassian_sites.id = ?
        """,
        (source_instance_id, site_id),
    ).fetchone()
    if not row:
        _fail(
            "connection-not-found",
            "The selected Source Instance/Site does not exist",
        )
    source_name = _bounded_text(source_name, "source_name", 160)
    site_name = _bounded_text(site_name, "site_name", 300)
    config_ref = _bounded_text(
        config_ref, "config_ref", 300, optional=True
    )
    connection.execute("SAVEPOINT atlassian_connection_edit")
    try:
        current_ref = row["config_ref"]
        if current_ref is not None and config_ref not in {
            None,
            current_ref,
        }:
            _fail(
                "source-instance-identity-conflict",
                "A bound connection reference cannot be changed",
            )
        if current_ref is None and config_ref is not None:
            source = bind_source_instance_config_ref(
                connection, source_instance_id, config_ref
            )
            current_ref = source["config_ref"]
        source = register_source_instance(
            connection,
            instance_key=row["instance_key"],
            provider_kind=row["provider_kind"],
            service=row["service"],
            display_name=source_name,
            config_ref=current_ref,
            enabled=enabled,
        )
        connection.execute(
            """
            UPDATE atlassian_sites
            SET display_name = ?, updated_at = ?
            WHERE id = ? AND source_instance_id = ?
            """,
            (site_name, utc_now(), site_id, source_instance_id),
        )
        site = connection.execute(
            "SELECT * FROM atlassian_sites WHERE id = ?", (site_id,)
        ).fetchone()
    except (AtlassianContractError, ExternalAccessError) as exc:
        connection.execute("ROLLBACK TO atlassian_connection_edit")
        connection.execute("RELEASE atlassian_connection_edit")
        raise AtlassianRegistrationError(
            getattr(exc, "code", "connection-edit-failed"), str(exc)
        ) from exc
    except Exception:
        connection.execute("ROLLBACK TO atlassian_connection_edit")
        connection.execute("RELEASE atlassian_connection_edit")
        raise
    else:
        connection.execute("RELEASE atlassian_connection_edit")
    return {
        "source_instance_id": int(source["id"]),
        "site_id": int(site["id"]),
        "service": source["service"],
        "enabled": bool(source["enabled"]),
        "config_bound": source["config_ref"] is not None,
    }


def resolve_registration_site(
    connection: sqlite3.Connection,
    locator: RegistrationLocator,
    *,
    site_id: Optional[int] = None,
) -> dict:
    rows = connection.execute(
        """
        SELECT atlassian_sites.*,
               external_source_instances.id AS source_instance_id,
               external_source_instances.service,
               external_source_instances.display_name AS source_name,
               external_source_instances.enabled
        FROM atlassian_sites
        JOIN external_source_instances
          ON external_source_instances.id = atlassian_sites.source_instance_id
        WHERE atlassian_sites.normalized_domain = ?
          AND external_source_instances.service = ?
          AND external_source_instances.enabled = 1
        ORDER BY external_source_instances.id, atlassian_sites.id
        """,
        (locator.normalized_domain, locator.service),
    ).fetchall()
    if site_id is not None:
        selected = [row for row in rows if int(row["id"]) == int(site_id)]
        if len(selected) != 1:
            _fail(
                "site-mismatch",
                "The selected Source Instance/Site does not own this URL",
            )
        return dict(selected[0])
    if not rows:
        _fail(
            "site-not-configured",
            "No enabled Source Instance/Site matches this URL",
        )
    if len(rows) > 1:
        _fail(
            "ambiguous-site",
            "More than one Source Instance matches; select one explicitly",
        )
    return dict(rows[0])


def register_atlassian_url(
    connection: sqlite3.Connection,
    *,
    url: str,
    service: str,
    site_id: Optional[int] = None,
    title: Optional[str] = None,
) -> dict:
    locator = recognize_registration_url(url, expected_service=service)
    site = resolve_registration_site(connection, locator, site_id=site_id)
    if locator.kind == "item":
        before = connection.execute(
            """
            SELECT atlassian_items.external_resource_id
            FROM atlassian_item_urls
            JOIN atlassian_items
              ON atlassian_items.external_resource_id =
                 atlassian_item_urls.external_resource_id
            WHERE atlassian_item_urls.site_id = ?
              AND atlassian_item_urls.normalized_url = ?
            """,
            (site["id"], locator.normalized_url),
        ).fetchone()
        try:
            item = create_or_reuse_atlassian_stub(
                connection,
                source_instance_id=int(site["source_instance_id"]),
                url=locator.normalized_url,
                title=_bounded_text(title, "title", 500, optional=True),
            )
        except AtlassianContractError as exc:
            raise AtlassianRegistrationError(exc.code, str(exc)) from exc
        return {
            "kind": "item",
            "created": before is None,
            "id": int(item["external_resource_id"]),
            "service": service,
        }

    existing = connection.execute(
        """
        SELECT id FROM atlassian_spaces
        WHERE site_id = ? AND service = ? AND space_key = ?
        """,
        (site["id"], service, locator.space_key),
    ).fetchone()
    try:
        space = register_atlassian_space(
            connection,
            site_id=int(site["id"]),
            name=_bounded_text(title, "title", 500, optional=True)
            or locator.space_key
            or "Atlassian Space",
            space_key=locator.space_key,
            canonical_url=locator.normalized_url,
        )
    except AtlassianContractError as exc:
        raise AtlassianRegistrationError(exc.code, str(exc)) from exc
    return {
        "kind": "space",
        "created": existing is None,
        "id": int(space["id"]),
        "service": service,
    }


def registration_inventory(
    connection: sqlite3.Connection, service: str
) -> dict:
    item_rows = connection.execute(
        """
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               external_resources.title,
               atlassian_sites.id AS site_id,
               atlassian_sites.normalized_domain,
               external_source_instances.id AS source_instance_id,
               external_source_instances.display_name AS source_name,
               atlassian_item_urls.normalized_url AS canonical_url,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale
        FROM atlassian_items
        JOIN external_resources
          ON external_resources.id = atlassian_items.external_resource_id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        JOIN external_source_instances
          ON external_source_instances.id = atlassian_sites.source_instance_id
        LEFT JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        LEFT JOIN atlassian_item_remote_state
          ON atlassian_item_remote_state.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.service = ?
        ORDER BY atlassian_items.updated_at DESC,
                 atlassian_items.external_resource_id DESC
        """,
        (service,),
    ).fetchall()
    items = []
    for row in item_rows:
        item = dict(row)
        item["freshness"] = derive_atlassian_freshness(service, item)
        items.append(item)
    spaces = [
        dict(row)
        for row in connection.execute(
            """
            SELECT atlassian_spaces.*,
                   atlassian_sites.normalized_domain,
                   external_source_instances.id AS source_instance_id,
                   external_source_instances.display_name AS source_name
            FROM atlassian_spaces
            JOIN atlassian_sites
              ON atlassian_sites.id = atlassian_spaces.site_id
            JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_sites.source_instance_id
            WHERE atlassian_spaces.service = ?
            ORDER BY atlassian_spaces.name, atlassian_spaces.id
            """,
            (service,),
        ).fetchall()
    ]
    return {"items": items, "spaces": spaces}


def prepare_space_catalog_run(
    connection: sqlite3.Connection,
    *,
    site_id: int,
    runner: str = "claude",
    run_root=None,
) -> str:
    site = connection.execute(
        """
        SELECT atlassian_sites.*, external_source_instances.id AS source_instance_id,
               external_source_instances.service
        FROM atlassian_sites
        JOIN external_source_instances
          ON external_source_instances.id = atlassian_sites.source_instance_id
        WHERE atlassian_sites.id = ? AND external_source_instances.enabled = 1
        """,
        (site_id,),
    ).fetchone()
    if not site:
        _fail("site-not-found", "The selected Atlassian Site is unavailable")
    try:
        state = capability_state(
            connection, int(site["source_instance_id"])
        )
    except ExternalAccessError as exc:
        raise AtlassianRegistrationError(exc.code, str(exc)) from exc
    if state["state"] != "current":
        _fail(
            "capability-not-current",
            "The Source Instance read capability is {}".format(state["state"]),
        )
    if site["service"] == "jira":
        operation = "jira.search_metadata"
        arguments = {
            "jql": "project is not EMPTY ORDER BY project",
            "fields": ["project"],
            "limit": 100,
        }
        field = "project"
    else:
        operation = "confluence.search_pages"
        arguments = {"cql": "type = page", "limit": 200}
        field = "space"
    try:
        return prepare_external_sync_run(
            connection,
            runner=runner,
            source_instance_id=int(site["source_instance_id"]),
            source_kind="atlassian",
            scope_kind="space",
            targets=[
                {
                    "target_id": "space-catalog-site-{}".format(site_id),
                    "locator": {
                        "kind": "source_root",
                        "value": site["canonical_base_url"],
                    },
                    "coverage": ["metadata"],
                    "field_allowlist": [field],
                    "known": {},
                    "requests": [
                        {
                            "request_id": "space-catalog-request-{}".format(
                                site_id
                            ),
                            "logical_operation": operation,
                            "arguments": arguments,
                        }
                    ],
                }
            ],
            call_budget=1,
            run_root=run_root,
        )
    except (ExternalAccessError, ExternalSyncError) as exc:
        raise AtlassianRegistrationError(
            getattr(exc, "code", "catalog-unavailable"), str(exc)
        ) from exc


def register_space_candidate(
    connection: sqlite3.Connection,
    *,
    site_id: int,
    service: str,
    space_key: str,
    name: str,
    remote_id: Optional[str] = None,
) -> dict:
    key = _bounded_text(space_key, "space_key", 300)
    title = _bounded_text(name, "name", 500)
    remote_id = _bounded_text(
        remote_id, "remote_id", 300, optional=True
    )
    site = connection.execute(
        """
        SELECT atlassian_sites.*, external_source_instances.service
        FROM atlassian_sites
        JOIN external_source_instances
          ON external_source_instances.id = atlassian_sites.source_instance_id
        WHERE atlassian_sites.id = ? AND external_source_instances.enabled = 1
        """,
        (site_id,),
    ).fetchone()
    if not site or site["service"] != service:
        _fail(
            "site-mismatch",
            "The selected Source Instance/Site is unavailable",
        )
    canonical_url = "{}{}{}{}".format(
        site["canonical_base_url"].rstrip("/"),
        "/projects/" if service == "jira" else "/spaces/",
        key,
        "" if service == "jira" else "/overview",
    )
    existing = connection.execute(
        """
        SELECT id FROM atlassian_spaces
        WHERE site_id = ? AND service = ? AND space_key = ?
        """,
        (site_id, service, key),
    ).fetchone()
    try:
        space = register_atlassian_space(
            connection,
            site_id=site_id,
            name=title,
            remote_id=remote_id,
            space_key=key,
            canonical_url=canonical_url,
        )
    except AtlassianContractError as exc:
        raise AtlassianRegistrationError(exc.code, str(exc)) from exc
    return {
        "kind": "space",
        "created": existing is None,
        "id": int(space["id"]),
        "service": service,
    }


def _candidate_objects(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
    elif isinstance(value, list):
        for item in value[:CATALOG_MAX_CANDIDATES]:
            if isinstance(item, Mapping):
                yield item


def space_catalog_candidates(
    connection: sqlite3.Connection, run_id: str, service: str
) -> dict:
    row = connection.execute(
        """
        SELECT maintenance_runs.status, maintenance_runs.structured_result_json,
               external_sync_runs.service,
               external_sync_runs.source_instance_id
        FROM maintenance_runs
        JOIN external_sync_runs
          ON external_sync_runs.maintenance_run_id = maintenance_runs.id
        WHERE maintenance_runs.id = ?
        """,
        (run_id,),
    ).fetchone()
    if not row or row["service"] != service:
        _fail("catalog-not-found", "Space discovery Run was not found")
    result = {
        "run_id": run_id,
        "status": row["status"],
        "partial": True,
        "site_id": None,
        "candidates": [],
    }
    if not row["structured_result_json"]:
        return result
    try:
        payload = json.loads(row["structured_result_json"])
    except (TypeError, json.JSONDecodeError):
        _fail("catalog-invalid", "Space discovery result is invalid")
    candidates = {}
    field = "project" if service == "jira" else "space"
    for target in payload.get("targets") or []:
        target_id = target.get("target_id")
        if isinstance(target_id, str) and target_id.startswith(
            "space-catalog-site-"
        ):
            try:
                result["site_id"] = int(
                    target_id[len("space-catalog-site-") :]
                )
            except ValueError:
                pass
        for request in target.get("requests") or []:
            metadata = request.get("metadata")
            if not isinstance(metadata, Mapping):
                continue
            for raw in _candidate_objects(metadata.get(field)):
                key = raw.get("key") or raw.get("space_key")
                remote_id = raw.get("id") or raw.get("remote_id")
                name = raw.get("name") or raw.get("title") or key or remote_id
                if (
                    not isinstance(name, str)
                    or not name.strip()
                    or not isinstance(key, str)
                    or not key.strip()
                ):
                    continue
                identity = str(key or remote_id or name).strip()
                candidates.setdefault(
                    identity,
                    {
                        "key": str(key).strip() if key is not None else None,
                        "remote_id": (
                            str(remote_id).strip()
                            if remote_id is not None
                            else None
                        ),
                        "name": name.strip()[:500],
                    },
                )
    result["candidates"] = list(candidates.values())[:CATALOG_MAX_CANDIDATES]
    return result
