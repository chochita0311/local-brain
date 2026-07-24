import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from markdown_it import MarkdownIt

from .workstreams import utc_now


NORMALIZER_VERSION = "localbrain.atlassian-normalizer.v1"
NORMALIZED_DOCUMENT_SCHEMA = "localbrain.atlassian-normalized.v1"
METADATA_SCHEMA = "localbrain.atlassian-metadata.v1"
FRESHNESS_INTERVALS = {
    "jira": timedelta(days=7),
    "confluence": timedelta(days=30),
}
SERVICES = frozenset(FRESHNESS_INTERVALS)
COVERAGE_VALUES = frozenset({"reference", "metadata", "indexed"})
ATTENTION_VALUES = frozenset({"normal", "pinned", "ignored", "archived"})
SUCCESS_OUTCOMES = frozenset({"resolved", "unchanged", "changed"})
FAILURE_OUTCOMES = frozenset({"unavailable", "not_found", "error"})
OUTCOMES = SUCCESS_OUTCOMES | FAILURE_OUTCOMES
SOURCE_FORMATS = frozenset(
    {
        "jira_adf",
        "confluence_adf",
        "confluence_html",
        "confluence_markdown",
        "plain_text",
    }
)
FORBIDDEN_METADATA_FIELDS = frozenset(
    {"body", "content", "description", "renderedbody", "rendered_body"}
)
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class AtlassianContractError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class NormalizedAtlassianUrl:
    observed_url: str
    normalized_url: str
    normalized_domain: str
    canonical_base_url: str


@dataclass(frozen=True)
class NormalizedContent:
    source_format: str
    source_body: str
    source_hash: str
    normalized_document_json: str
    normalized_text: str
    warning: Optional[str]


def _fail(code: str, message: str) -> None:
    raise AtlassianContractError(code, message)


def _clean_text(
    value: Any, label: str, maximum: int, *, optional: bool = False
) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        _fail("invalid-input", "{} must be a non-empty string".format(label))
    cleaned = value.strip()
    if len(cleaned) > maximum:
        _fail(
            "invalid-input",
            "{} exceeds {} characters".format(label, maximum),
        )
    return cleaned


def _canonical_json(value: Any, label: str, maximum: int = 2_000_000) -> str:
    try:
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise AtlassianContractError(
            "invalid-input", "{} must be JSON serializable".format(label)
        ) from exc
    if len(serialized.encode("utf-8")) > maximum:
        _fail("invalid-input", "{} exceeds {} bytes".format(label, maximum))
    return serialized


@contextmanager
def _atomic(connection: sqlite3.Connection, name: str):
    connection.execute("SAVEPOINT {}".format(name))
    try:
        yield
    except Exception:
        connection.execute("ROLLBACK TO {}".format(name))
        connection.execute("RELEASE {}".format(name))
        raise
    else:
        connection.execute("RELEASE {}".format(name))


def normalize_atlassian_url(url: str) -> NormalizedAtlassianUrl:
    observed = _clean_text(url, "url", 8000)
    assert observed is not None
    try:
        parsed = urlsplit(observed)
        port = parsed.port
    except ValueError as exc:
        raise AtlassianContractError("invalid-url", "URL is invalid") from exc
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        _fail("invalid-url", "Atlassian URLs must use HTTP or HTTPS")
    if parsed.username is not None or parsed.password is not None:
        _fail("invalid-url", "Atlassian URLs cannot contain credentials")
    try:
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise AtlassianContractError(
            "invalid-url", "Atlassian URL domain is invalid"
        ) from exc
    if not host:
        _fail("invalid-url", "Atlassian URL domain is empty")
    default_port = (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    )
    domain = host if port is None or default_port else "{}:{}".format(host, port)
    netloc = domain
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query = urlencode(sorted(query_pairs), doseq=True)
    normalized_url = urlunsplit((scheme, netloc, path, query, ""))
    return NormalizedAtlassianUrl(
        observed_url=observed,
        normalized_url=normalized_url,
        normalized_domain=domain,
        canonical_base_url=urlunsplit((scheme, netloc, "", "", "")),
    )


def _source_instance(connection: sqlite3.Connection, source_instance_id: int):
    row = connection.execute(
        """
        SELECT id, service, enabled
        FROM external_source_instances
        WHERE id = ?
        """,
        (source_instance_id,),
    ).fetchone()
    if not row:
        _fail("source-instance-not-found", "Source Instance does not exist")
    if not bool(row["enabled"]):
        _fail("source-instance-disabled", "Source Instance is disabled")
    return row


def register_atlassian_site(
    connection: sqlite3.Connection,
    *,
    source_instance_id: int,
    base_url: str,
    display_name: Optional[str] = None,
    remote_site_id: Optional[str] = None,
) -> dict:
    _source_instance(connection, source_instance_id)
    normalized = normalize_atlassian_url(base_url)
    display_name = _clean_text(
        display_name, "display_name", 300, optional=True
    )
    remote_site_id = _clean_text(
        remote_site_id, "remote_site_id", 300, optional=True
    )
    now = utc_now()
    with _atomic(connection, "atlassian_site_registration"):
        row = connection.execute(
            """
            SELECT * FROM atlassian_sites
            WHERE source_instance_id = ? AND normalized_domain = ?
            """,
            (source_instance_id, normalized.normalized_domain),
        ).fetchone()
        if row:
            if (
                remote_site_id is not None
                and row["remote_site_id"] not in {None, remote_site_id}
            ):
                _fail(
                    "site-identity-conflict",
                    "Site is already bound to a different remote identity",
                )
            if remote_site_id is not None:
                collision = connection.execute(
                    """
                    SELECT id FROM atlassian_sites
                    WHERE source_instance_id = ? AND remote_site_id = ? AND id != ?
                    """,
                    (source_instance_id, remote_site_id, row["id"]),
                ).fetchone()
                if collision:
                    _fail(
                        "site-identity-collision",
                        "Remote Site identity is already bound",
                    )
            connection.execute(
                """
                UPDATE atlassian_sites
                SET display_name = COALESCE(?, display_name),
                    remote_site_id = COALESCE(?, remote_site_id),
                    updated_at = ?
                WHERE id = ?
                """,
                (display_name, remote_site_id, now, row["id"]),
            )
            site_id = int(row["id"])
        else:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO atlassian_sites(
                        source_instance_id, normalized_domain, display_name,
                        remote_site_id, canonical_base_url, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_instance_id,
                        normalized.normalized_domain,
                        display_name,
                        remote_site_id,
                        normalized.canonical_base_url,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise AtlassianContractError(
                    "site-identity-collision",
                    "Site identity collides inside the Source Instance",
                ) from exc
            site_id = int(cursor.lastrowid)
    return dict(
        connection.execute(
            "SELECT * FROM atlassian_sites WHERE id = ?", (site_id,)
        ).fetchone()
    )


def register_atlassian_space(
    connection: sqlite3.Connection,
    *,
    site_id: int,
    name: str,
    remote_id: Optional[str] = None,
    space_key: Optional[str] = None,
    canonical_url: Optional[str] = None,
    coverage: Optional[str] = None,
) -> dict:
    site = connection.execute(
        """
        SELECT atlassian_sites.id, atlassian_sites.normalized_domain,
               atlassian_sites.canonical_base_url,
               external_source_instances.service
        FROM atlassian_sites
        JOIN external_source_instances
          ON external_source_instances.id = atlassian_sites.source_instance_id
        WHERE atlassian_sites.id = ?
        """,
        (site_id,),
    ).fetchone()
    if not site:
        _fail("site-not-found", "Atlassian Site does not exist")
    name = _clean_text(name, "name", 500)
    remote_id = _clean_text(remote_id, "remote_id", 300, optional=True)
    space_key = _clean_text(space_key, "space_key", 300, optional=True)
    if remote_id is None and space_key is None:
        _fail(
            "invalid-space-identity",
            "Space requires a remote ID or space key",
        )
    if coverage is not None and coverage not in {
        "selected-content",
        "full-content",
    }:
        _fail("invalid-space-coverage", "Unsupported Atlassian Space coverage")
    if canonical_url is None:
        locator = space_key or remote_id
        assert locator is not None
        canonical_url = "{}{}{}{}".format(
            site["canonical_base_url"].rstrip("/"),
            "/projects/" if site["service"] == "jira" else "/spaces/",
            locator,
            "" if site["service"] == "jira" else "/overview",
        )
    normalized_url = normalize_atlassian_url(canonical_url)
    if normalized_url.normalized_domain != site["normalized_domain"]:
        _fail(
            "space-site-mismatch",
            "Space URL does not belong to the selected Atlassian Site",
        )
    default_coverage = (
        "selected-content" if site["service"] == "jira" else "full-content"
    )
    predicates = []
    params: list[Any] = [site_id, site["service"]]
    if remote_id is not None:
        predicates.append("remote_id = ?")
        params.append(remote_id)
    if space_key is not None:
        predicates.append("space_key = ?")
        params.append(space_key)
    row = connection.execute(
        """
        SELECT * FROM atlassian_spaces
        WHERE site_id = ? AND service = ? AND ({})
        ORDER BY id
        LIMIT 1
        """.format(" OR ".join(predicates)),
        tuple(params),
    ).fetchone()
    now = utc_now()
    with _atomic(connection, "atlassian_space_registration"):
        if row:
            if (
                remote_id is not None
                and row["remote_id"] not in {None, remote_id}
            ) or (
                space_key is not None
                and row["space_key"] not in {None, space_key}
            ):
                _fail(
                    "space-identity-conflict",
                    "Space identifiers resolve to conflicting rows",
                )
            connection.execute(
                """
                UPDATE atlassian_spaces
                SET remote_id = COALESCE(remote_id, ?),
                    space_key = COALESCE(space_key, ?),
                    name = ?, canonical_url = ?,
                    coverage = COALESCE(?, coverage),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    remote_id,
                    space_key,
                    name,
                    normalized_url.normalized_url,
                    coverage,
                    now,
                    row["id"],
                ),
            )
            space_id = int(row["id"])
        else:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO atlassian_spaces(
                        site_id, service, remote_id, space_key, name,
                        canonical_url, coverage, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        site_id,
                        site["service"],
                        remote_id,
                        space_key,
                        name,
                        normalized_url.normalized_url,
                        coverage or default_coverage,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise AtlassianContractError(
                    "space-identity-collision",
                    "Space identity is already bound inside the Site",
                ) from exc
            space_id = int(cursor.lastrowid)
    return dict(
        connection.execute(
            "SELECT * FROM atlassian_spaces WHERE id = ?", (space_id,)
        ).fetchone()
    )


def _site_for_source_url(
    connection: sqlite3.Connection,
    source_instance_id: int,
    normalized: NormalizedAtlassianUrl,
) -> dict:
    row = connection.execute(
        """
        SELECT * FROM atlassian_sites
        WHERE source_instance_id = ? AND normalized_domain = ?
        """,
        (source_instance_id, normalized.normalized_domain),
    ).fetchone()
    if row:
        return dict(row)
    return register_atlassian_site(
        connection,
        source_instance_id=source_instance_id,
        base_url=normalized.canonical_base_url,
    )


def _matching_unbound_external_resource(
    connection: sqlite3.Connection,
    normalized: NormalizedAtlassianUrl,
    service: str,
) -> Optional[int]:
    matches = []
    resource_type = "jira" if service == "jira" else "wiki"
    rows = connection.execute(
        """
        SELECT external_resources.id, external_resources.url
        FROM external_resources
        LEFT JOIN atlassian_items
          ON atlassian_items.external_resource_id = external_resources.id
        WHERE external_resources.resource_type = ?
          AND atlassian_items.external_resource_id IS NULL
        ORDER BY external_resources.id
        """,
        (resource_type,),
    ).fetchall()
    for row in rows:
        try:
            candidate = normalize_atlassian_url(row["url"])
        except AtlassianContractError:
            continue
        if candidate.normalized_url == normalized.normalized_url:
            matches.append(int(row["id"]))
    if len(matches) > 1:
        _fail(
            "ambiguous-local-resource",
            "More than one unbound External Resource matches this URL",
        )
    return matches[0] if matches else None


def _item_type(service: str) -> str:
    return "jira_issue" if service == "jira" else "confluence_page"


def _item_row(connection: sqlite3.Connection, external_resource_id: int) -> dict:
    row = connection.execute(
        """
        SELECT atlassian_items.*,
               atlassian_sites.source_instance_id,
               atlassian_sites.normalized_domain
        FROM atlassian_items
        JOIN atlassian_sites ON atlassian_sites.id = atlassian_items.site_id
        WHERE atlassian_items.external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone()
    if not row:
        _fail("item-not-found", "Atlassian Item does not exist")
    return dict(row)


def _set_canonical_url(
    connection: sqlite3.Connection,
    *,
    external_resource_id: int,
    site_id: int,
    url: NormalizedAtlassianUrl,
    observed_at: str,
) -> None:
    collision = connection.execute(
        """
        SELECT external_resource_id FROM atlassian_item_urls
        WHERE site_id = ? AND normalized_url = ?
          AND external_resource_id != ?
        """,
        (site_id, url.normalized_url, external_resource_id),
    ).fetchone()
    if collision:
        _fail(
            "url-identity-collision",
            "Normalized URL is already bound to another Item in this Site",
        )
    existing = connection.execute(
        """
        SELECT id FROM atlassian_item_urls
        WHERE site_id = ? AND normalized_url = ?
          AND external_resource_id = ?
        """,
        (site_id, url.normalized_url, external_resource_id),
    ).fetchone()
    connection.execute(
        """
        UPDATE atlassian_item_urls
        SET url_role = 'alias'
        WHERE external_resource_id = ? AND url_role = 'canonical'
        """,
        (external_resource_id,),
    )
    if existing:
        connection.execute(
            """
            UPDATE atlassian_item_urls
            SET url_role = 'canonical', observed_url = ?,
                last_observed_at = ?
            WHERE id = ?
            """,
            (url.observed_url, observed_at, existing["id"]),
        )
    else:
        connection.execute(
            """
            INSERT INTO atlassian_item_urls(
                external_resource_id, site_id, url_role, observed_url,
                normalized_url, first_observed_at, last_observed_at
            ) VALUES (?, ?, 'canonical', ?, ?, ?, ?)
            """,
            (
                external_resource_id,
                site_id,
                url.observed_url,
                url.normalized_url,
                observed_at,
                observed_at,
            ),
        )


def create_or_reuse_atlassian_stub(
    connection: sqlite3.Connection,
    *,
    source_instance_id: int,
    url: str,
    title: Optional[str] = None,
    external_resource_id: Optional[int] = None,
    coverage: str = "reference",
    attention: str = "normal",
    observed_at: Optional[str] = None,
) -> dict:
    source = _source_instance(connection, source_instance_id)
    service = source["service"]
    normalized = normalize_atlassian_url(url)
    if coverage not in COVERAGE_VALUES:
        _fail("invalid-coverage", "Unsupported Atlassian coverage")
    if attention not in ATTENTION_VALUES:
        _fail("invalid-attention", "Unsupported Atlassian attention")
    title = _clean_text(title, "title", 500, optional=True)
    now = observed_at or utc_now()

    with _atomic(connection, "atlassian_stub_registration"):
        site = _site_for_source_url(
            connection, source_instance_id, normalized
        )
        existing_url = connection.execute(
            """
            SELECT external_resource_id FROM atlassian_item_urls
            WHERE site_id = ? AND normalized_url = ?
            """,
            (site["id"], normalized.normalized_url),
        ).fetchone()
        if existing_url:
            existing_id = int(existing_url["external_resource_id"])
            if (
                external_resource_id is not None
                and external_resource_id != existing_id
            ):
                _fail(
                    "url-identity-collision",
                    "URL is already bound to another local Resource",
                )
            connection.execute(
                """
                UPDATE atlassian_item_urls
                SET observed_url = ?, last_observed_at = ?
                WHERE site_id = ? AND normalized_url = ?
                """,
                (
                    normalized.observed_url,
                    now,
                    site["id"],
                    normalized.normalized_url,
                ),
            )
            return _item_row(connection, existing_id)

        if external_resource_id is None:
            external_resource_id = _matching_unbound_external_resource(
                connection, normalized, service
            )
        if external_resource_id is not None:
            resource = connection.execute(
                "SELECT id FROM external_resources WHERE id = ?",
                (external_resource_id,),
            ).fetchone()
            if not resource:
                _fail(
                    "resource-not-found",
                    "External Resource does not exist",
                )
            bound = connection.execute(
                """
                SELECT external_resource_id, site_id, service
                FROM atlassian_items
                WHERE external_resource_id = ?
                """,
                (external_resource_id,),
            ).fetchone()
            if bound and (
                int(bound["site_id"]) != int(site["id"])
                or bound["service"] != service
            ):
                _fail(
                    "resource-already-bound",
                    "External Resource is already bound to another Atlassian Item",
                )
            resource_id = external_resource_id
        else:
            cursor = connection.execute(
                """
                INSERT INTO external_resources(
                    resource_type, title, url, source_role, updated_at
                ) VALUES (?, ?, ?, 'remote-reference', ?)
                """,
                (
                    "jira" if service == "jira" else "wiki",
                    title or normalized.normalized_url,
                    normalized.observed_url,
                    now,
                ),
            )
            resource_id = int(cursor.lastrowid)
            bound = None

        if not bound:
            connection.execute(
                """
                INSERT INTO atlassian_items(
                    external_resource_id, site_id, service, item_type,
                    coverage, attention, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resource_id,
                    site["id"],
                    service,
                    _item_type(service),
                    coverage,
                    attention,
                    now,
                ),
            )
        _set_canonical_url(
            connection,
            external_resource_id=resource_id,
            site_id=site["id"],
            url=normalized,
            observed_at=now,
        )
        _project_item_search(connection, resource_id, now)
    return _item_row(connection, resource_id)


def bind_atlassian_remote_identity(
    connection: sqlite3.Connection,
    external_resource_id: int,
    *,
    remote_id: str,
    remote_key: Optional[str] = None,
    canonical_url: Optional[str] = None,
    space_id: Optional[int] = None,
    confirmed_at: Optional[str] = None,
) -> dict:
    item = _item_row(connection, external_resource_id)
    remote_id = _clean_text(remote_id, "remote_id", 300)
    remote_key = _clean_text(remote_key, "remote_key", 300, optional=True)
    now = confirmed_at or utc_now()
    normalized_url = (
        normalize_atlassian_url(canonical_url)
        if canonical_url is not None
        else None
    )
    if (
        normalized_url is not None
        and normalized_url.normalized_domain != item["normalized_domain"]
    ):
        _fail(
            "site-domain-mismatch",
            "Canonical URL belongs to a different Site domain",
        )
    if space_id is not None:
        space = connection.execute(
            "SELECT site_id, service FROM atlassian_spaces WHERE id = ?",
            (space_id,),
        ).fetchone()
        if (
            not space
            or int(space["site_id"]) != int(item["site_id"])
            or space["service"] != item["service"]
        ):
            _fail(
                "space-boundary-mismatch",
                "Space does not belong to the Item Site and service",
            )

    with _atomic(connection, "atlassian_remote_binding"):
        current = connection.execute(
            """
            SELECT remote_id, remote_key
            FROM atlassian_items
            WHERE external_resource_id = ?
            """,
            (external_resource_id,),
        ).fetchone()
        if current["remote_id"] not in {None, remote_id}:
            _fail(
                "remote-identity-conflict",
                "Item is already bound to a different remote ID",
            )
        if (
            remote_key is not None
            and current["remote_key"] not in {None, remote_key}
        ):
            _fail(
                "remote-key-conflict",
                "Item is already bound to a different remote key",
            )
        collision = connection.execute(
            """
            SELECT external_resource_id FROM atlassian_items
            WHERE site_id = ? AND service = ? AND remote_id = ?
              AND external_resource_id != ?
            """,
            (
                item["site_id"],
                item["service"],
                remote_id,
                external_resource_id,
            ),
        ).fetchone()
        if collision:
            _fail(
                "remote-identity-collision",
                "Remote identity is already bound to another Item",
            )
        if remote_key is not None:
            key_collision = connection.execute(
                """
                SELECT external_resource_id FROM atlassian_items
                WHERE site_id = ? AND service = ? AND remote_key = ?
                  AND external_resource_id != ?
                """,
                (
                    item["site_id"],
                    item["service"],
                    remote_key,
                    external_resource_id,
                ),
            ).fetchone()
            if key_collision:
                _fail(
                    "remote-key-collision",
                    "Remote key is already bound to another Item",
                )
        if normalized_url is not None:
            _set_canonical_url(
                connection,
                external_resource_id=external_resource_id,
                site_id=item["site_id"],
                url=normalized_url,
                observed_at=now,
            )
        connection.execute(
            """
            UPDATE atlassian_items
            SET remote_id = ?, remote_key = COALESCE(?, remote_key),
                space_id = COALESCE(?, space_id),
                confirmed_at = COALESCE(confirmed_at, ?), updated_at = ?
            WHERE external_resource_id = ?
            """,
            (
                remote_id,
                remote_key,
                space_id,
                now,
                now,
                external_resource_id,
            ),
        )
    return _item_row(connection, external_resource_id)


def set_atlassian_item_axes(
    connection: sqlite3.Connection,
    external_resource_id: int,
    *,
    coverage: Optional[str] = None,
    attention: Optional[str] = None,
    changed_at: Optional[str] = None,
) -> dict:
    _item_row(connection, external_resource_id)
    if coverage is not None and coverage not in COVERAGE_VALUES:
        _fail("invalid-coverage", "Unsupported Atlassian coverage")
    if attention is not None and attention not in ATTENTION_VALUES:
        _fail("invalid-attention", "Unsupported Atlassian attention")
    now = changed_at or utc_now()
    with _atomic(connection, "atlassian_item_axes"):
        connection.execute(
            """
            UPDATE atlassian_items
            SET coverage = COALESCE(?, coverage),
                attention = COALESCE(?, attention),
                updated_at = ?
            WHERE external_resource_id = ?
            """,
            (coverage, attention, now, external_resource_id),
        )
        if coverage is not None and coverage != "indexed":
            connection.execute(
                """
                DELETE FROM search_index
                WHERE entity_type = 'atlassian_item' AND entity_id = ?
                """,
                (str(external_resource_id),),
            )
            connection.execute(
                """
                DELETE FROM atlassian_item_content
                WHERE external_resource_id = ?
                """,
                (external_resource_id,),
            )
            if coverage == "reference":
                connection.execute(
                    """
                    UPDATE atlassian_item_remote_state
                    SET metadata_json = '{}', known_changed = 0,
                        projection_stale = 0, updated_at = ?
                    WHERE external_resource_id = ?
                    """,
                    (now, external_resource_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE atlassian_item_remote_state
                    SET known_changed = 0, projection_stale = 0,
                        updated_at = ?
                    WHERE external_resource_id = ?
                    """,
                    (now, external_resource_id),
                )
        if coverage is not None:
            _project_item_search(connection, external_resource_id, now)
    return _item_row(connection, external_resource_id)


def _bounded_warnings(warnings: Iterable[str]) -> tuple[list[str], Optional[str]]:
    unique = []
    for warning in warnings:
        if warning not in unique:
            unique.append(warning[:200])
        if len(unique) >= 20:
            break
    return unique, "; ".join(unique) if unique else None


def _append_block(blocks: list[dict], block_type: str, text: str) -> None:
    normalized = re.sub(r"[ \t]+", " ", text).strip()
    if normalized:
        blocks.append({"type": block_type, "text": normalized})


def _adf_inline_text(node: Any, warnings: list[str]) -> str:
    if not isinstance(node, Mapping):
        warnings.append("ignored non-object ADF node")
        return ""
    node_type = node.get("type")
    if node_type == "text":
        return str(node.get("text") or "")
    if node_type == "hardBreak":
        return "\n"
    if node_type in {"mention", "emoji", "inlineCard"}:
        attrs = node.get("attrs")
        if isinstance(attrs, Mapping):
            for key in ("text", "displayName", "shortName", "url"):
                value = attrs.get(key)
                if isinstance(value, str) and value:
                    return value
    content = node.get("content")
    if isinstance(content, Sequence) and not isinstance(content, (str, bytes)):
        return "".join(_adf_inline_text(child, warnings) for child in content)
    if node_type not in {
        "doc",
        "paragraph",
        "heading",
        "blockquote",
        "codeBlock",
        "bulletList",
        "orderedList",
        "listItem",
        "table",
        "tableRow",
        "tableCell",
        "tableHeader",
        "panel",
        "expand",
        "rule",
        "mediaSingle",
        "mediaGroup",
        "status",
    }:
        warnings.append("unsupported ADF node: {}".format(node_type or "unknown"))
    return ""


def _walk_adf(node: Any, blocks: list[dict], warnings: list[str]) -> None:
    if not isinstance(node, Mapping):
        warnings.append("ignored non-object ADF node")
        return
    node_type = str(node.get("type") or "unknown")
    content = node.get("content")
    children = (
        list(content)
        if isinstance(content, Sequence) and not isinstance(content, (str, bytes))
        else []
    )
    block_types = {
        "paragraph",
        "heading",
        "blockquote",
        "codeBlock",
        "listItem",
        "tableCell",
        "tableHeader",
        "panel",
        "expand",
    }
    if node_type in block_types:
        _append_block(
            blocks,
            node_type,
            "".join(_adf_inline_text(child, warnings) for child in children),
        )
        nested_block_types = {
            "bulletList",
            "orderedList",
            "table",
            "tableRow",
            "panel",
            "expand",
        }
        for child in children:
            if isinstance(child, Mapping) and child.get("type") in nested_block_types:
                _walk_adf(child, blocks, warnings)
        return
    known_containers = {
        "doc",
        "bulletList",
        "orderedList",
        "table",
        "tableRow",
        "mediaSingle",
        "mediaGroup",
    }
    if node_type not in known_containers and node_type not in {
        "text",
        "hardBreak",
        "mention",
        "emoji",
        "inlineCard",
        "rule",
        "status",
    }:
        warnings.append("unsupported ADF node: {}".format(node_type))
    for child in children:
        _walk_adf(child, blocks, warnings)


class _SafeTextHTMLParser(HTMLParser):
    BLOCK_TAGS = frozenset(
        {
            "address",
            "article",
            "aside",
            "blockquote",
            "br",
            "div",
            "dl",
            "dt",
            "dd",
            "figcaption",
            "figure",
            "footer",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "hr",
            "li",
            "main",
            "nav",
            "ol",
            "p",
            "pre",
            "section",
            "table",
            "td",
            "th",
            "tr",
            "ul",
        }
    )
    IGNORED_TAGS = frozenset(
        {"script", "style", "form", "iframe", "object", "embed", "template"}
    )

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self._parts: list[str] = []
        self._ignored_depth = 0
        self.warnings: list[str] = []

    def _flush(self) -> None:
        _append_block(self.blocks, "html", " ".join(self._parts))
        self._parts = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in self.IGNORED_TAGS:
            self._ignored_depth += 1
            self.warnings.append("ignored active HTML tag: {}".format(tag))
            return
        if not self._ignored_depth and tag in self.BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.IGNORED_TAGS:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if not self._ignored_depth and tag in self.BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and data:
            self._parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush()


def _normalize_markdown(source: str) -> tuple[list[dict], list[str]]:
    # Parse raw HTML as distinct tokens so it can be omitted rather than
    # accidentally indexed as literal Markdown text.
    parser = MarkdownIt("commonmark", {"html": True})
    tokens = parser.parse(source)
    blocks: list[dict] = []
    warnings: list[str] = []
    for token in tokens:
        if token.type in {"fence", "code_block"}:
            _append_block(blocks, "code", token.content)
        elif token.type == "inline":
            parts = []
            for child in token.children or []:
                if child.type in {"text", "code_inline"}:
                    parts.append(child.content)
                elif child.type in {"softbreak", "hardbreak"}:
                    parts.append("\n")
                elif child.type == "html_inline":
                    warnings.append("ignored inline HTML")
            _append_block(blocks, "markdown", "".join(parts))
        elif token.type in {"html_block"}:
            warnings.append("ignored HTML block")
    return blocks, warnings


def normalize_atlassian_content(
    source_format: str, content: Any
) -> NormalizedContent:
    if source_format not in SOURCE_FORMATS:
        _fail("unsupported-content-format", "Unsupported Atlassian content format")
    blocks: list[dict] = []
    warnings: list[str] = []
    if source_format in {"jira_adf", "confluence_adf"}:
        if not isinstance(content, Mapping):
            _fail("invalid-content", "ADF content must be an object")
        source_body = _canonical_json(content, "ADF content")
        _walk_adf(content, blocks, warnings)
    elif source_format == "confluence_html":
        if not isinstance(content, str):
            _fail("invalid-content", "Confluence HTML content must be text")
        source_body = content
        parser = _SafeTextHTMLParser()
        try:
            parser.feed(content)
            parser.close()
        except Exception as exc:
            raise AtlassianContractError(
                "invalid-content", "Confluence HTML could not be parsed"
            ) from exc
        blocks = parser.blocks
        warnings.extend(parser.warnings)
    elif source_format == "confluence_markdown":
        if not isinstance(content, str):
            _fail("invalid-content", "Confluence Markdown content must be text")
        source_body = content
        blocks, warnings = _normalize_markdown(content)
    else:
        if not isinstance(content, str):
            _fail("invalid-content", "Plain content must be text")
        source_body = content
        for paragraph in re.split(r"\n\s*\n", content):
            _append_block(blocks, "plain", paragraph)
    if len(source_body.encode("utf-8")) > 2_000_000:
        _fail("invalid-content", "Atlassian content exceeds 2000000 bytes")
    warnings, warning = _bounded_warnings(warnings)
    normalized_text = "\n\n".join(block["text"] for block in blocks)
    document = {
        "schema": NORMALIZED_DOCUMENT_SCHEMA,
        "blocks": blocks,
        "warnings": warnings,
    }
    return NormalizedContent(
        source_format=source_format,
        source_body=source_body,
        source_hash=hashlib.sha256(source_body.encode("utf-8")).hexdigest(),
        normalized_document_json=_canonical_json(
            document, "normalized document"
        ),
        normalized_text=normalized_text,
        warning=warning,
    )


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise AtlassianContractError(
            "invalid-timestamp", "Timestamp must be ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def derive_atlassian_freshness(
    service: str,
    remote_state: Optional[Mapping[str, Any]],
    *,
    now: Optional[datetime] = None,
) -> str:
    if service not in SERVICES:
        _fail("invalid-service", "Unsupported Atlassian service")
    state = dict(remote_state or {})
    if state.get("last_outcome") in FAILURE_OUTCOMES:
        return "unavailable"
    if bool(state.get("known_changed")) or bool(state.get("projection_stale")):
        return "stale"
    last_successful = _parse_time(state.get("last_successful_at"))
    if last_successful is None:
        return "unknown"
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    if current - last_successful >= FRESHNESS_INTERVALS[service]:
        return "due"
    return "current"


def atlassian_item_state(
    connection: sqlite3.Connection,
    external_resource_id: int,
    *,
    now: Optional[datetime] = None,
) -> dict:
    item = _item_row(connection, external_resource_id)
    remote = connection.execute(
        """
        SELECT * FROM atlassian_item_remote_state
        WHERE external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone()
    item["freshness"] = derive_atlassian_freshness(
        item["service"], dict(remote) if remote else None, now=now
    )
    item["remote_state"] = dict(remote) if remote else None
    item["urls"] = [
        dict(row)
        for row in connection.execute(
            """
            SELECT * FROM atlassian_item_urls
            WHERE external_resource_id = ?
            ORDER BY url_role DESC, id
            """,
            (external_resource_id,),
        ).fetchall()
    ]
    return item


def _single_request_fact(
    request_results: Iterable[Mapping[str, Any]], key: str
) -> Any:
    values = []
    fingerprints = set()
    for request in request_results:
        value = request.get(key)
        if value is None or value == {}:
            continue
        fingerprint = _canonical_json(value, key)
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            values.append(value)
    if len(values) > 1:
        _fail(
            "conflicting-provider-facts",
            "Validated requests returned conflicting {}".format(key),
        )
    return values[0] if values else None


def _merge_metadata(
    request_results: Iterable[Mapping[str, Any]]
) -> dict:
    merged: dict[str, Any] = {}
    fingerprints: dict[str, str] = {}
    for request in request_results:
        metadata = request.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            _fail("invalid-provider-result", "Remote metadata must be an object")
        if len(metadata) > 100:
            _fail("invalid-provider-result", "Remote metadata is not bounded")
        for raw_key, value in metadata.items():
            if not isinstance(raw_key, str) or not raw_key.strip():
                _fail(
                    "invalid-provider-result",
                    "Remote metadata field names must be text",
                )
            key = raw_key.strip()
            if len(key) > 120:
                _fail(
                    "invalid-provider-result",
                    "Remote metadata field name is too long",
                )
            if key.lower() in FORBIDDEN_METADATA_FIELDS:
                _fail(
                    "remote-content-in-metadata",
                    "Remote body content cannot be stored as metadata",
                )
            _validate_metadata_value(value, depth=0)
            fingerprint = _canonical_json(value, "metadata field", 100_000)
            if key in fingerprints and fingerprints[key] != fingerprint:
                _fail(
                    "conflicting-provider-facts",
                    "Validated requests returned conflicting metadata",
                )
            fingerprints[key] = fingerprint
            merged[key] = value
    _canonical_json(merged, "remote metadata", 500_000)
    return merged


def _validate_metadata_value(value: Any, *, depth: int) -> None:
    if depth > 20:
        _fail(
            "invalid-provider-result",
            "Remote metadata nesting is too deep",
        )
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if not isinstance(raw_key, str):
                _fail(
                    "invalid-provider-result",
                    "Remote metadata field names must be text",
                )
            if raw_key.strip().lower() in FORBIDDEN_METADATA_FIELDS:
                _fail(
                    "remote-content-in-metadata",
                    "Remote body content cannot be stored as metadata",
                )
            _validate_metadata_value(child, depth=depth + 1)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for child in value:
            _validate_metadata_value(child, depth=depth + 1)


def _content_fact(
    service: str,
    request_results: Iterable[Mapping[str, Any]],
    explicit_format: Optional[str],
) -> tuple[Optional[str], Any]:
    raw = _single_request_fact(request_results, "content")
    if raw is None:
        return None, None
    source_format = explicit_format
    body = raw
    if isinstance(raw, Mapping) and set(raw) == {"format", "body"}:
        provider_format = raw["format"]
        body = raw["body"]
        format_map = {
            "jira_adf": "jira_adf",
            "confluence_adf": "confluence_adf",
            "adf": "jira_adf" if service == "jira" else "confluence_adf",
            "atlas_doc_format": (
                "jira_adf" if service == "jira" else "confluence_adf"
            ),
            "storage": "confluence_html",
            "html": "confluence_html",
            "markdown": "confluence_markdown",
            "plain_text": "plain_text",
            "text": "plain_text",
        }
        if provider_format not in format_map:
            _fail(
                "unsupported-content-format",
                "Provider content format is unsupported",
            )
        inferred = format_map[provider_format]
        if source_format is not None and source_format != inferred:
            _fail(
                "content-format-mismatch",
                "Explicit and provider content formats do not match",
            )
        source_format = inferred
    if source_format is None:
        if isinstance(body, Mapping):
            source_format = (
                "jira_adf" if service == "jira" else "confluence_adf"
            )
        elif isinstance(body, str):
            source_format = "plain_text"
        else:
            _fail(
                "invalid-content",
                "Provider content must be text or ADF",
            )
    if source_format not in SOURCE_FORMATS:
        _fail("unsupported-content-format", "Unsupported Atlassian content format")
    if service == "jira" and source_format not in {"jira_adf", "plain_text"}:
        _fail("content-format-mismatch", "Jira content format is invalid")
    if service == "confluence" and source_format == "jira_adf":
        _fail("content-format-mismatch", "Confluence content format is invalid")
    return source_format, body


def _identity_facts(request_results: Iterable[Mapping[str, Any]]) -> dict:
    merged: dict[str, Any] = {}
    allowed = {"remote_id", "remote_key", "canonical_url"}
    for request in request_results:
        identity = request.get("identity") or {}
        if not isinstance(identity, Mapping):
            _fail("invalid-provider-result", "Remote identity must be an object")
        if not set(identity).issubset(allowed):
            _fail(
                "invalid-provider-result",
                "Remote identity contains unsupported fields",
            )
        for key, value in identity.items():
            if key in merged and merged[key] != value:
                _fail(
                    "conflicting-provider-facts",
                    "Validated requests returned conflicting identity",
                )
            merged[key] = value
    return merged


def _remote_version_facts(
    request_results: Iterable[Mapping[str, Any]]
) -> tuple[Optional[str], Optional[str]]:
    version = _single_request_fact(request_results, "remote_version")
    updated_at = _single_request_fact(request_results, "remote_updated_at")
    if version is not None:
        version = _clean_text(version, "remote_version", 300)
    if updated_at is not None:
        updated_at = _clean_text(updated_at, "remote_updated_at", 100)
        _parse_time(updated_at)
    return version, updated_at


def _canonical_item_url(
    connection: sqlite3.Connection, external_resource_id: int
) -> str:
    row = connection.execute(
        """
        SELECT normalized_url FROM atlassian_item_urls
        WHERE external_resource_id = ? AND url_role = 'canonical'
        """,
        (external_resource_id,),
    ).fetchone()
    return row["normalized_url"] if row else ""


def _flatten_search_values(value: Any, prefix: str = "") -> list[str]:
    values = []
    if isinstance(value, Mapping):
        for key in sorted(value):
            label = "{}.{}".format(prefix, key) if prefix else str(key)
            values.extend(_flatten_search_values(value[key], label))
    elif isinstance(value, list):
        for item in value:
            values.extend(_flatten_search_values(item, prefix))
    elif value is not None:
        text = str(value).strip()
        if text:
            values.append("{}: {}".format(prefix, text) if prefix else text)
    return values


def _projection_values(
    connection: sqlite3.Connection, external_resource_id: int
) -> list[dict]:
    row = connection.execute(
        """
        SELECT atlassian_items.service, atlassian_items.coverage,
               atlassian_items.remote_key,
               external_resources.title AS local_title,
               atlassian_item_remote_state.metadata_json,
               atlassian_item_content.normalized_text,
               atlassian_item_local_state.note
        FROM atlassian_items
        JOIN external_resources
          ON external_resources.id = atlassian_items.external_resource_id
        LEFT JOIN atlassian_item_remote_state
          ON atlassian_item_remote_state.external_resource_id =
             atlassian_items.external_resource_id
        LEFT JOIN atlassian_item_content
          ON atlassian_item_content.external_resource_id =
             atlassian_items.external_resource_id
        LEFT JOIN atlassian_item_local_state
          ON atlassian_item_local_state.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone()
    if not row:
        return []
    try:
        metadata = json.loads(row["metadata_json"] or "{}")
    except json.JSONDecodeError:
        metadata = {}
    remote_title = (
        metadata.get("title")
        or metadata.get("summary")
        or row["local_title"]
    )
    canonical_url = _canonical_item_url(connection, external_resource_id)
    base = {
        "entity_type": "atlassian_item",
        "entity_id": str(external_resource_id),
        "path": canonical_url,
    }
    identity_body = "\n".join(
        value
        for value in (row["remote_key"], canonical_url)
        if value
    )
    values = [
        {
            **base,
            "source_kind": "atlassian:{}:identity".format(row["service"]),
            "title": str(row["local_title"] or remote_title or ""),
            "body": identity_body,
        }
    ]
    metadata_text = "\n".join(_flatten_search_values(metadata))
    if metadata_text:
        values.append(
            {
                **base,
                "source_kind": "atlassian:{}:metadata".format(
                    row["service"]
                ),
                "title": str(remote_title or row["local_title"] or ""),
                "body": metadata_text,
            }
        )
    if row["coverage"] == "indexed" and row["normalized_text"]:
        values.append(
            {
                **base,
                "source_kind": "atlassian:{}:content".format(
                    row["service"]
                ),
                "title": str(remote_title or row["local_title"] or ""),
                "body": row["normalized_text"],
            }
        )
    classifications = connection.execute(
        """
        SELECT atlassian_classifications.kind,
               atlassian_classifications.name,
               atlassian_classifications.description
        FROM atlassian_item_classifications
        JOIN atlassian_classifications
          ON atlassian_classifications.id =
             atlassian_item_classifications.classification_id
        WHERE atlassian_item_classifications.external_resource_id = ?
        ORDER BY atlassian_classifications.kind,
                 atlassian_classifications.normalized_name
        """,
        (external_resource_id,),
    ).fetchall()
    local_parts = []
    if row["note"]:
        local_parts.append("note: {}".format(row["note"]))
    for classification in classifications:
        local_parts.append(
            "{}: {}".format(
                classification["kind"], classification["name"]
            )
        )
        if classification["description"]:
            local_parts.append(
                "topic description: {}".format(
                    classification["description"]
                )
            )
    if local_parts:
        values.append(
            {
                **base,
                "source_kind": "atlassian:local",
                "title": str(row["local_title"] or remote_title or ""),
                "body": "\n".join(local_parts),
            }
        )
    return values


def _project_item_search(
    connection: sqlite3.Connection,
    external_resource_id: int,
    changed_at: str,
) -> bool:
    values = _projection_values(connection, external_resource_id)
    current = [
        dict(row)
        for row in connection.execute(
            """
            SELECT entity_type, entity_id, source_kind, title, body, path
            FROM search_index
            WHERE entity_type = 'atlassian_item' AND entity_id = ?
            ORDER BY source_kind, title, body, path
            """,
            (str(external_resource_id),),
        ).fetchall()
    ]
    values = sorted(
        values,
        key=lambda value: (
            value["source_kind"],
            value["title"],
            value["body"],
            value["path"],
        ),
    )
    projection_hash = hashlib.sha256(
        _canonical_json(values, "search projection").encode("utf-8")
    ).hexdigest()
    existing_content = connection.execute(
        """
        SELECT search_projection_hash
        FROM atlassian_item_content
        WHERE external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone()
    if current == values:
        if (
            existing_content
            and existing_content["search_projection_hash"] != projection_hash
        ):
            connection.execute(
                """
                UPDATE atlassian_item_content
                SET search_projection_hash = ?, updated_at = ?
                WHERE external_resource_id = ?
                """,
                (projection_hash, changed_at, external_resource_id),
            )
        return False
    connection.execute(
        """
        DELETE FROM search_index
        WHERE entity_type = 'atlassian_item' AND entity_id = ?
        """,
        (str(external_resource_id),),
    )
    connection.executemany(
        """
        INSERT INTO search_index(
            entity_type, entity_id, source_kind, title, body, path
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                value["entity_type"],
                value["entity_id"],
                value["source_kind"],
                value["title"],
                value["body"],
                value["path"],
            )
            for value in values
        ],
    )
    if existing_content:
        connection.execute(
            """
            UPDATE atlassian_item_content
            SET search_projection_hash = ?, updated_at = ?
            WHERE external_resource_id = ?
            """,
            (projection_hash, changed_at, external_resource_id),
        )
    return True


def project_atlassian_item_search(
    connection: sqlite3.Connection,
    external_resource_id: int,
    *,
    changed_at: Optional[str] = None,
) -> bool:
    _item_row(connection, external_resource_id)
    return _project_item_search(
        connection, external_resource_id, changed_at or utc_now()
    )


def rebuild_atlassian_search_index(
    connection: sqlite3.Connection, *, rebuilt_at: Optional[str] = None
) -> int:
    now = rebuilt_at or utc_now()
    item_ids = [
        int(row["external_resource_id"])
        for row in connection.execute(
            """
            SELECT external_resource_id
            FROM atlassian_items
            ORDER BY external_resource_id
            """
        ).fetchall()
    ]
    with _atomic(connection, "atlassian_search_rebuild"):
        connection.execute(
            "DELETE FROM search_index WHERE entity_type = 'atlassian_item'"
        )
        connection.execute(
            """
            UPDATE atlassian_item_content
            SET search_projection_hash = NULL, updated_at = ?
            """,
            (now,),
        )
        projected = sum(
            bool(_project_item_search(connection, item_id, now))
            for item_id in item_ids
        )
    return projected


def _upsert_remote_state(
    connection: sqlite3.Connection,
    external_resource_id: int,
    *,
    metadata: Optional[dict],
    remote_version: Optional[str],
    remote_updated_at: Optional[str],
    attempted_at: str,
    outcome: str,
    error_code: Optional[str],
    known_changed: Optional[bool],
    projection_stale: Optional[bool],
) -> None:
    existing = connection.execute(
        """
        SELECT metadata_json, last_successful_at, last_confirmed_at,
               known_changed, projection_stale
        FROM atlassian_item_remote_state
        WHERE external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone()
    if existing:
        try:
            prior_metadata = json.loads(existing["metadata_json"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise AtlassianContractError(
                "invalid-stored-state",
                "Stored Atlassian metadata is invalid",
            ) from exc
        if not isinstance(prior_metadata, dict):
            _fail(
                "invalid-stored-state",
                "Stored Atlassian metadata must be an object",
            )
    else:
        prior_metadata = {}
    if metadata is not None:
        prior_metadata.update(metadata)
    metadata_json = _canonical_json(
        prior_metadata, "remote metadata", 500_000
    )
    successful = outcome in SUCCESS_OUTCOMES
    last_successful = attempted_at if successful else (
        existing["last_successful_at"] if existing else None
    )
    last_confirmed = attempted_at if successful else (
        existing["last_confirmed_at"] if existing else None
    )
    known_changed_value = (
        int(known_changed)
        if known_changed is not None
        else (int(existing["known_changed"]) if existing else 0)
    )
    projection_stale_value = (
        int(projection_stale)
        if projection_stale is not None
        else (int(existing["projection_stale"]) if existing else 0)
    )
    connection.execute(
        """
        INSERT INTO atlassian_item_remote_state(
            external_resource_id, metadata_schema_version, metadata_json,
            remote_version, remote_updated_at, last_attempted_at,
            last_successful_at, last_confirmed_at, last_outcome,
            last_error_code, known_changed, projection_stale, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(external_resource_id) DO UPDATE SET
            metadata_schema_version = excluded.metadata_schema_version,
            metadata_json = excluded.metadata_json,
            remote_version = COALESCE(
                excluded.remote_version,
                atlassian_item_remote_state.remote_version
            ),
            remote_updated_at = COALESCE(
                excluded.remote_updated_at,
                atlassian_item_remote_state.remote_updated_at
            ),
            last_attempted_at = excluded.last_attempted_at,
            last_successful_at = excluded.last_successful_at,
            last_confirmed_at = excluded.last_confirmed_at,
            last_outcome = excluded.last_outcome,
            last_error_code = excluded.last_error_code,
            known_changed = excluded.known_changed,
            projection_stale = excluded.projection_stale,
            updated_at = excluded.updated_at
        """,
        (
            external_resource_id,
            METADATA_SCHEMA,
            metadata_json,
            remote_version,
            remote_updated_at,
            attempted_at,
            last_successful,
            last_confirmed,
            outcome,
            error_code,
            known_changed_value,
            projection_stale_value,
            attempted_at,
        ),
    )


def apply_atlassian_target_result(
    connection: sqlite3.Connection,
    external_resource_id: int,
    target_result: Mapping[str, Any],
    *,
    checked_at: Optional[str] = None,
    source_format: Optional[str] = None,
) -> dict:
    item = _item_row(connection, external_resource_id)
    if not isinstance(target_result, Mapping):
        _fail("invalid-provider-result", "Target result must be an object")
    allowed_keys = {"target_id", "locator", "outcome", "requests"}
    if not set(target_result).issubset(allowed_keys):
        _fail(
            "invalid-provider-result",
            "Target result contains unsupported fields",
        )
    outcome = target_result.get("outcome")
    if outcome not in OUTCOMES:
        _fail("invalid-provider-result", "Target outcome is unsupported")
    request_results = target_result.get("requests")
    if not isinstance(request_results, list) or not request_results:
        _fail(
            "invalid-provider-result",
            "Target result requires validated request results",
        )
    attempted_at = checked_at or utc_now()
    _parse_time(attempted_at)

    with _atomic(connection, "atlassian_target_application"):
        if outcome in FAILURE_OUTCOMES:
            error_codes = {
                request.get("error", {}).get("code")
                for request in request_results
                if isinstance(request, Mapping)
                and isinstance(request.get("error"), Mapping)
                and request["error"].get("code")
            }
            error_code = sorted(error_codes)[0] if error_codes else outcome
            _upsert_remote_state(
                connection,
                external_resource_id,
                metadata=None,
                remote_version=None,
                remote_updated_at=None,
                attempted_at=attempted_at,
                outcome=outcome,
                error_code=error_code[:80],
                known_changed=None,
                projection_stale=None,
            )
            return atlassian_item_state(connection, external_resource_id)

        identity = _identity_facts(request_results)
        remote_id = identity.get("remote_id")
        if item["remote_id"] is None and remote_id is None:
            _fail(
                "missing-remote-identity",
                "A successful first check requires a remote ID",
            )
        if remote_id is not None:
            bind_atlassian_remote_identity(
                connection,
                external_resource_id,
                remote_id=remote_id,
                remote_key=identity.get("remote_key"),
                canonical_url=identity.get("canonical_url"),
                confirmed_at=attempted_at,
            )
        elif any(
            identity.get(key) is not None
            for key in ("remote_key", "canonical_url")
        ):
            _fail(
                "incomplete-remote-identity",
                "Remote identity details require a remote ID",
            )

        metadata = _merge_metadata(request_results)
        metadata_update = metadata if metadata else None
        remote_version, remote_updated_at = _remote_version_facts(
            request_results
        )
        content_format, raw_content = _content_fact(
            item["service"], request_results, source_format
        )
        if item["coverage"] == "reference" and metadata:
            _fail(
                "coverage-mismatch",
                "Reference coverage cannot store remote metadata",
            )
        if item["coverage"] != "indexed" and raw_content is not None:
            _fail(
                "coverage-mismatch",
                "Only indexed coverage can store remote content",
            )
        content_changed = False
        if raw_content is not None:
            normalized = normalize_atlassian_content(
                content_format, raw_content
            )
            existing_content = connection.execute(
                """
                SELECT source_hash, normalizer_version
                FROM atlassian_item_content
                WHERE external_resource_id = ?
                """,
                (external_resource_id,),
            ).fetchone()
            if (
                not existing_content
                or existing_content["source_hash"] != normalized.source_hash
                or existing_content["normalizer_version"] != NORMALIZER_VERSION
            ):
                connection.execute(
                    """
                    INSERT INTO atlassian_item_content(
                        external_resource_id, source_format, source_body,
                        source_hash, normalized_document_json, normalized_text,
                        normalizer_version, normalization_warning,
                        remote_version, remote_updated_at, applied_at,
                        search_projection_hash, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                    ON CONFLICT(external_resource_id) DO UPDATE SET
                        source_format = excluded.source_format,
                        source_body = excluded.source_body,
                        source_hash = excluded.source_hash,
                        normalized_document_json =
                            excluded.normalized_document_json,
                        normalized_text = excluded.normalized_text,
                        normalizer_version = excluded.normalizer_version,
                        normalization_warning =
                            excluded.normalization_warning,
                        remote_version = excluded.remote_version,
                        remote_updated_at = excluded.remote_updated_at,
                        applied_at = excluded.applied_at,
                        search_projection_hash = NULL,
                        updated_at = excluded.updated_at
                    """,
                    (
                        external_resource_id,
                        normalized.source_format,
                        normalized.source_body,
                        normalized.source_hash,
                        normalized.normalized_document_json,
                        normalized.normalized_text,
                        NORMALIZER_VERSION,
                        normalized.warning,
                        remote_version,
                        remote_updated_at,
                        attempted_at,
                        attempted_at,
                    ),
                )
                content_changed = True

        content_exists = bool(
            connection.execute(
                """
                SELECT 1 FROM atlassian_item_content
                WHERE external_resource_id = ?
                """,
                (external_resource_id,),
            ).fetchone()
        )
        projection_stale = (
            item["coverage"] == "indexed"
            and not content_exists
        )
        known_changed = (
            outcome == "changed"
            and item["coverage"] == "indexed"
            and raw_content is None
        )
        _upsert_remote_state(
            connection,
            external_resource_id,
            metadata=metadata_update,
            remote_version=remote_version,
            remote_updated_at=remote_updated_at,
            attempted_at=attempted_at,
            outcome=outcome,
            error_code=None,
            known_changed=known_changed,
            projection_stale=projection_stale,
        )
        if content_changed or metadata_update is not None:
            _project_item_search(
                connection, external_resource_id, attempted_at
            )
        elif item["coverage"] == "indexed" and content_exists:
            _project_item_search(
                connection, external_resource_id, attempted_at
            )
    return atlassian_item_state(connection, external_resource_id)


def purge_atlassian_item(
    connection: sqlite3.Connection,
    external_resource_id: int,
) -> dict:
    _item_row(connection, external_resource_id)
    entity_id = str(external_resource_id)
    with _atomic(connection, "atlassian_item_purge"):
        removed = {
            "workstream_links": connection.execute(
                """
                DELETE FROM workstream_links
                WHERE entity_type = 'external' AND entity_id = ?
                """,
                (entity_id,),
            ).rowcount,
            "thread_links": connection.execute(
                """
                DELETE FROM thread_links
                WHERE entity_type = 'external' AND entity_id = ?
                """,
                (entity_id,),
            ).rowcount,
            "checkpoint_resource_refs": connection.execute(
                """
                DELETE FROM checkpoint_resource_refs
                WHERE entity_type = 'external' AND entity_id = ?
                """,
                (entity_id,),
            ).rowcount,
            "search_rows": connection.execute(
                """
                DELETE FROM search_index
                WHERE entity_type = 'atlassian_item' AND entity_id = ?
                """,
                (entity_id,),
            ).rowcount,
        }
        deleted = connection.execute(
            "DELETE FROM external_resources WHERE id = ?",
            (external_resource_id,),
        ).rowcount
        if deleted != 1:
            _fail(
                "purge-failed",
                "Atlassian Item purge did not remove its External Resource",
            )
    return {"external_resource_id": external_resource_id, **removed}
