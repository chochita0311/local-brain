import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import unquote, urlsplit

from .atlassian import (
    AtlassianContractError,
    bind_atlassian_site_access,
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
from .atlassian_locators import (
    atlassian_item_container_hint,
    atlassian_page_title_hint,
    describe_atlassian_url,
)
from .workstreams import utc_now


CATALOG_MAX_CANDIDATES = 200
MAX_SQLITE_INTEGER = 9_223_372_036_854_775_807
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
    title_hint: Optional[str] = None


def _fail(code: str, message: str) -> None:
    raise AtlassianRegistrationError(code, message)


@contextmanager
def _registration_savepoint(connection: sqlite3.Connection, name: str):
    connection.execute("SAVEPOINT {}".format(name))
    try:
        yield
    except Exception:
        connection.execute("ROLLBACK TO {}".format(name))
        connection.execute("RELEASE {}".format(name))
        raise
    else:
        connection.execute("RELEASE {}".format(name))


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
    described = describe_atlassian_url(url)
    if described.kind == "unsafe":
        _fail("invalid-url", "Atlassian URL is invalid")
    try:
        owner_url = normalize_atlassian_url(url)
    except AtlassianContractError as exc:
        raise AtlassianRegistrationError(exc.code, str(exc)) from exc
    if described.kind == "item":
        assert described.service is not None
        assert described.safe_locator_url is not None
        assert described.normalized_domain is not None
        assert described.item_identity is not None
        locator = RegistrationLocator(
            service=described.service,
            kind="item",
            normalized_url=owner_url.normalized_url,
            normalized_domain=described.normalized_domain,
            remote_id=(
                described.item_identity
                if described.item_identity_kind == "confluence_page"
                else None
            ),
            remote_key=(
                described.item_identity
                if described.item_identity_kind == "jira_issue"
                else None
            ),
            space_key=atlassian_item_container_hint(url),
            title_hint=atlassian_page_title_hint(url),
        )
    elif described.kind == "structure" and described.reference_kind in {
        "jira_project",
        "confluence_space",
    }:
        assert described.service is not None
        assert described.safe_locator_url is not None
        assert described.normalized_domain is not None
        assert described.reference_identity is not None
        locator = RegistrationLocator(
            service=described.service,
            kind="space",
            normalized_url=owner_url.normalized_url,
            normalized_domain=described.normalized_domain,
            space_key=described.reference_identity,
        )
    else:
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
               atlassian_site_bindings.id AS binding_id,
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
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.site_id = atlassian_sites.id
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_site_bindings.source_instance_id
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
        item["capability_availability"] = state.get("availability")
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
    identifier = (
        locator.remote_key or locator.remote_id or locator.space_key
    )
    return {
        "service": locator.service,
        "kind": locator.kind,
        "normalized_url": locator.normalized_url,
        "normalized_domain": locator.normalized_domain,
        "identifier": identifier,
    }


def _bootstrap_title(locator: RegistrationLocator) -> str:
    if locator.remote_key:
        return locator.remote_key
    if locator.kind == "space" and locator.space_key:
        return locator.space_key
    if locator.service == "confluence" and locator.remote_id:
        if locator.title_hint:
            candidate = re.sub(r"[-_]+", " ", locator.title_hint).strip()
            if candidate:
                return candidate
        parts = [
            unquote(part).strip()
            for part in urlsplit(locator.normalized_url).path.split("/")
            if part.strip()
        ]
        try:
            page_index = parts.index(locator.remote_id)
        except ValueError:
            page_index = -1
        if page_index >= 0 and page_index + 1 < len(parts):
            candidate = re.sub(
                r"[-_]+", " ", parts[page_index + 1]
            ).strip()
            if candidate:
                return candidate
        return locator.remote_id
    return locator.space_key or locator.remote_id or locator.normalized_domain


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


def register_atlassian_site_access(
    connection: sqlite3.Connection,
    *,
    site_id: int,
    service: str,
    provider_kind: str,
    config_ref: str,
) -> dict:
    if service not in {"jira", "confluence"}:
        _fail("invalid-service", "Unsupported Atlassian service")
    if provider_kind not in PROVIDER_LABELS:
        _fail(
            "invalid-provider",
            "Select an official Atlassian MCP or company MCP Gateway access path",
        )
    reference = _bounded_text(config_ref, "config_ref", 300)
    site = connection.execute(
        "SELECT * FROM atlassian_sites WHERE id = ?",
        (site_id,),
    ).fetchone()
    if not site:
        _fail("site-not-found", "Atlassian Site does not exist")
    existing = connection.execute(
        """
        SELECT *
        FROM external_source_instances
        WHERE provider_kind = ?
          AND service = ?
          AND config_ref = ?
        ORDER BY id
        """,
        (provider_kind, service, reference),
    ).fetchall()
    if len(existing) > 1:
        _fail(
            "ambiguous-source",
            "More than one Source Instance owns this access reference",
        )
    connection.execute("SAVEPOINT atlassian_site_access_setup")
    try:
        if existing:
            source = dict(existing[0])
            if not bool(source["enabled"]):
                _fail(
                    "source-instance-disabled",
                    "The matching access path is disabled",
                )
            source_created = False
        else:
            instance_key = _new_instance_key(
                connection,
                provider_kind=provider_kind,
                service=service,
                normalized_domain=site["normalized_domain"],
                config_ref=reference,
            )
            source = register_source_instance(
                connection,
                instance_key=instance_key,
                provider_kind=provider_kind,
                service=service,
                display_name=_default_source_name(
                    provider_kind, site["normalized_domain"]
                ),
                config_ref=reference,
            )
            source_created = True
        before = connection.execute(
            """
            SELECT id FROM atlassian_site_bindings
            WHERE site_id = ? AND source_instance_id = ?
            """,
            (site_id, source["id"]),
        ).fetchone()
        binding = bind_atlassian_site_access(
            connection,
            site_id=site_id,
            source_instance_id=int(source["id"]),
        )
        connection.execute(
            """
            UPDATE atlassian_items
            SET source_instance_id = ?, updated_at = ?
            WHERE site_id = ? AND service = ?
              AND source_instance_id IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM atlassian_site_bindings AS other_binding
                  JOIN external_source_instances AS other_source
                    ON other_source.id =
                       other_binding.source_instance_id
                  WHERE other_binding.site_id = ?
                    AND other_source.service = ?
                    AND other_binding.source_instance_id != ?
              )
            """,
            (
                source["id"],
                utc_now(),
                site_id,
                service,
                site_id,
                service,
                source["id"],
            ),
        )
        connection.execute(
            """
            UPDATE atlassian_spaces
            SET source_instance_id = ?, updated_at = ?
            WHERE site_id = ? AND service = ?
              AND source_instance_id IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM atlassian_site_bindings AS other_binding
                  JOIN external_source_instances AS other_source
                    ON other_source.id =
                       other_binding.source_instance_id
                  WHERE other_binding.site_id = ?
                    AND other_source.service = ?
                    AND other_binding.source_instance_id != ?
              )
            """,
            (
                source["id"],
                utc_now(),
                site_id,
                service,
                site_id,
                service,
                source["id"],
            ),
        )
    except (AtlassianContractError, ExternalAccessError) as exc:
        connection.execute("ROLLBACK TO atlassian_site_access_setup")
        connection.execute("RELEASE atlassian_site_access_setup")
        raise AtlassianRegistrationError(
            getattr(exc, "code", "access-setup-failed"), str(exc)
        ) from exc
    except Exception:
        connection.execute("ROLLBACK TO atlassian_site_access_setup")
        connection.execute("RELEASE atlassian_site_access_setup")
        raise
    else:
        connection.execute("RELEASE atlassian_site_access_setup")
    return {
        "binding_id": int(binding["binding_id"]),
        "site_id": site_id,
        "source_instance_id": int(source["id"]),
        "source_created": source_created,
        "binding_created": before is None,
        "service": service,
    }


def update_atlassian_connection(
    connection: sqlite3.Connection,
    *,
    source_instance_id: int,
    site_id: int,
    enabled: bool,
    config_ref: Optional[str] = None,
) -> dict:
    row = connection.execute(
        """
        SELECT external_source_instances.*,
               atlassian_site_bindings.id AS binding_id,
               atlassian_sites.id AS site_id,
               atlassian_sites.canonical_base_url,
               atlassian_sites.display_name AS site_display_name
        FROM external_source_instances
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.source_instance_id =
             external_source_instances.id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_site_bindings.site_id
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
            display_name=row["display_name"],
            config_ref=current_ref,
            enabled=enabled,
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
        "binding_id": int(row["binding_id"]),
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
        SELECT atlassian_sites.*
        FROM atlassian_sites
        WHERE atlassian_sites.normalized_domain = ?
        ORDER BY atlassian_sites.id
        """,
        (locator.normalized_domain,),
    ).fetchall()
    if site_id is not None:
        selected = [row for row in rows if int(row["id"]) == int(site_id)]
        if len(selected) != 1:
            _fail(
                "site-mismatch",
                "The selected Site does not own this URL",
            )
        result = dict(selected[0])
        result["service"] = locator.service
        return result
    if not rows:
        site = register_atlassian_site(
            connection,
            base_url=locator.normalized_url,
        )
        site["service"] = locator.service
        return site
    if len(rows) > 1:
        rows = rows[:1]
    result = dict(rows[0])
    result["service"] = locator.service
    return result


def register_atlassian_url(
    connection: sqlite3.Connection,
    *,
    url: str,
    service: Optional[str] = None,
    site_id: Optional[int] = None,
    source_instance_id: Optional[int] = None,
    title: Optional[str] = None,
) -> dict:
    # ``service`` remains accepted for internal caller compatibility, but URL
    # recognition is the only pre-confirmation service authority.
    locator = recognize_registration_url(url)
    service = locator.service
    local_title = (
        _bounded_text(title, "title", 500, optional=True)
        or _bootstrap_title(locator)[:500]
    )
    with _registration_savepoint(connection, "atlassian_url_registration"):
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
                    source_instance_id=source_instance_id,
                    url=locator.normalized_url,
                    service=service,
                    site_id=int(site["id"]),
                    title=local_title,
                )
            except AtlassianContractError as exc:
                raise AtlassianRegistrationError(exc.code, str(exc)) from exc
            result = {
                "kind": "item",
                "created": before is None,
                "id": int(item["external_resource_id"]),
                "site_id": int(item["site_id"]),
                "space_id": (
                    int(item["space_id"])
                    if item.get("space_id") is not None
                    else None
                ),
                "attention": item["attention"],
                "service": service,
                "canonical_url": locator.normalized_url,
            }
        else:
            existing = connection.execute(
                """
                SELECT id, canonical_url FROM atlassian_spaces
                WHERE site_id = ? AND service = ? AND space_key = ?
                """,
                (site["id"], service, locator.space_key),
            ).fetchone()
            if (
                existing is not None
                and existing["canonical_url"] != locator.normalized_url
            ):
                _fail(
                    "space-url-conflict",
                    "This Space key is already registered from a different URL",
                )
            try:
                space = register_atlassian_space(
                    connection,
                    site_id=int(site["id"]),
                    service=service,
                    source_instance_id=source_instance_id,
                    name=local_title,
                    space_key=locator.space_key,
                    canonical_url=locator.normalized_url,
                )
            except AtlassianContractError as exc:
                raise AtlassianRegistrationError(exc.code, str(exc)) from exc
            result = {
                "kind": "space",
                "created": existing is None,
                "id": int(space["id"]),
                "site_id": int(space["site_id"]),
                "service": service,
            }
    return result


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
               COALESCE(
                   external_source_instances.display_name, '로컬 전용'
               ) AS source_name,
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
        LEFT JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_items.source_instance_id
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
                   COALESCE(
                       external_source_instances.display_name, '로컬 전용'
                   ) AS source_name
            FROM atlassian_spaces
            JOIN atlassian_sites
              ON atlassian_sites.id = atlassian_spaces.site_id
            LEFT JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_spaces.source_instance_id
            WHERE atlassian_spaces.service = ?
            ORDER BY atlassian_spaces.name, atlassian_spaces.id
            """,
            (service,),
        ).fetchall()
    ]
    return {"items": items, "spaces": spaces}


def registered_scope_overview(
    connection: sqlite3.Connection, service: str
) -> list[dict]:
    """Return cached connection scope without materializing Item rows."""
    if service not in {"jira", "confluence"}:
        _fail("invalid-service", "Unsupported Atlassian service")
    connections = registration_sites(connection, service)
    site_rows = connection.execute(
        """
        SELECT atlassian_sites.id AS site_id,
               atlassian_sites.normalized_domain,
               atlassian_sites.display_name,
               COALESCE(item_counts.item_count, 0) AS item_count
        FROM atlassian_sites
        LEFT JOIN (
            SELECT site_id, COUNT(*) AS item_count
            FROM atlassian_items
            WHERE service = ?
            GROUP BY site_id
        ) AS item_counts ON item_counts.site_id = atlassian_sites.id
        WHERE EXISTS (
            SELECT 1 FROM atlassian_spaces
            WHERE atlassian_spaces.site_id = atlassian_sites.id
              AND atlassian_spaces.service = ?
        ) OR item_counts.item_count IS NOT NULL OR EXISTS (
            SELECT 1
            FROM atlassian_site_bindings
            JOIN external_source_instances
              ON external_source_instances.id =
                 atlassian_site_bindings.source_instance_id
            WHERE atlassian_site_bindings.site_id = atlassian_sites.id
              AND external_source_instances.service = ?
        )
        ORDER BY atlassian_sites.normalized_domain, atlassian_sites.id
        """,
        (service, service, service),
    ).fetchall()
    spaces = connection.execute(
        """
        SELECT atlassian_spaces.id, atlassian_spaces.site_id,
               atlassian_spaces.service, atlassian_spaces.remote_id,
               atlassian_spaces.space_key, atlassian_spaces.name,
               atlassian_spaces.canonical_url, atlassian_spaces.coverage,
               atlassian_sites.normalized_domain
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        WHERE atlassian_spaces.service = ?
        ORDER BY atlassian_spaces.name, atlassian_spaces.id
        """,
        (service,),
    ).fetchall()
    groups = {
        int(row["site_id"]): {
            "site_id": int(row["site_id"]),
            "normalized_domain": row["normalized_domain"],
            "display_name": row["display_name"]
            or row["normalized_domain"],
            "connections": [],
            "spaces": [],
            "item_count": int(row["item_count"]),
        }
        for row in site_rows
    }
    for value in connections:
        group = groups.get(int(value["site_id"]))
        if group is not None:
            group["connections"].append(value)
    for row in spaces:
        group = groups.get(int(row["site_id"]))
        if group is not None:
            group["spaces"].append(dict(row))
    return sorted(
        groups.values(),
        key=lambda item: (
            str(item["display_name"]).lower(),
            item["normalized_domain"],
            item["site_id"],
        ),
    )


def prepare_space_catalog_run(
    connection: sqlite3.Connection,
    *,
    site_id: int,
    source_instance_id: Optional[int] = None,
    target_domain: Optional[str] = None,
    runner: str = "claude",
    run_root=None,
) -> str:
    sites = connection.execute(
        """
        SELECT atlassian_sites.*, external_source_instances.id AS source_instance_id,
               external_source_instances.service
        FROM atlassian_sites
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.site_id = atlassian_sites.id
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_site_bindings.source_instance_id
        WHERE atlassian_sites.id = ?
          AND external_source_instances.enabled = 1
          AND (? IS NULL OR external_source_instances.id = ?)
        ORDER BY
          CASE WHEN external_source_instances.id =
                    atlassian_sites.source_instance_id
               THEN 0 ELSE 1 END,
          external_source_instances.id
        """,
        (site_id, source_instance_id, source_instance_id),
    ).fetchall()
    if not sites:
        _fail("site-not-found", "The selected Atlassian Site is unavailable")
    if len(sites) > 1:
        _fail(
            "ambiguous-source",
            "Select one access binding for this Atlassian Site",
        )
    site = sites[0]
    if (
        target_domain is not None
        and target_domain.strip().lower() != site["normalized_domain"]
    ):
        _fail(
            "target-connection-mismatch",
            "선택한 MCP 연결은 조회 대상 Site에 속하지 않습니다.",
        )
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
    source_instance_id: Optional[int] = None,
    space_key: str,
    name: str,
    remote_id: Optional[str] = None,
) -> dict:
    key = _bounded_text(space_key, "space_key", 300)
    title = _bounded_text(name, "name", 500)
    remote_id = _bounded_text(
        remote_id, "remote_id", 300, optional=True
    )
    sites = connection.execute(
        """
        SELECT atlassian_sites.*,
               external_source_instances.id AS source_instance_id,
               external_source_instances.service
        FROM atlassian_sites
        JOIN atlassian_site_bindings
          ON atlassian_site_bindings.site_id = atlassian_sites.id
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_site_bindings.source_instance_id
        WHERE atlassian_sites.id = ?
          AND external_source_instances.service = ?
          AND external_source_instances.enabled = 1
          AND (? IS NULL OR external_source_instances.id = ?)
        ORDER BY external_source_instances.id
        """,
        (site_id, service, source_instance_id, source_instance_id),
    ).fetchall()
    if len(sites) != 1:
        _fail(
            "site-mismatch",
            "The selected Site access binding is unavailable or ambiguous",
        )
    site = sites[0]
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
            service=service,
            source_instance_id=int(site["source_instance_id"]),
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
        "site_id": int(space["site_id"]),
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
    connection: sqlite3.Connection,
    run_id: str,
    service: Optional[str] = None,
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
    if not row or (service is not None and row["service"] != service):
        _fail("catalog-not-found", "Space discovery Run was not found")
    service = str(row["service"])
    result = {
        "run_id": run_id,
        "status": row["status"],
        "partial": True,
        "service": service,
        "site_id": None,
        "source_instance_id": row["source_instance_id"],
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


def register_space_catalog_candidate(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    candidate_key: str,
) -> dict:
    key = _bounded_text(candidate_key, "candidate_key", 300)
    catalog = space_catalog_candidates(connection, run_id)
    matches = [
        candidate
        for candidate in catalog["candidates"]
        if candidate.get("key") == key
    ]
    try:
        site_id = int(catalog.get("site_id"))
        source_instance_id = int(catalog.get("source_instance_id"))
    except (TypeError, ValueError, OverflowError):
        site_id = 0
        source_instance_id = 0
    if (
        len(matches) != 1
        or site_id < 1
        or site_id > MAX_SQLITE_INTEGER
        or source_instance_id < 1
        or source_instance_id > MAX_SQLITE_INTEGER
    ):
        _fail(
            "candidate-not-found",
            "The selected Space candidate is no longer available",
        )
    candidate = matches[0]
    return register_space_candidate(
        connection,
        site_id=site_id,
        service=str(catalog["service"]),
        source_instance_id=source_instance_id,
        space_key=str(candidate["key"]),
        name=str(candidate["name"]),
        remote_id=(
            str(candidate["remote_id"])
            if candidate.get("remote_id") is not None
            else None
        ),
    )
