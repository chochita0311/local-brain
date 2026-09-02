import json
import re
import sqlite3
import unicodedata
from typing import Any, Iterable, Mapping, Optional

from .atlassian import (
    ATTENTION_VALUES,
    AtlassianContractError,
    derive_atlassian_freshness,
    normalize_atlassian_url,
    project_atlassian_item_search,
    set_atlassian_item_axes,
)
from .atlassian_evidence import (
    atlassian_url_container_hint,
    normalize_atlassian_structural_scope,
    structural_scope_service,
)
from .atlassian_locators import describe_atlassian_url
from .atlassian_structure_references import (
    structure_reference_detail,
    structure_reference_preview,
    structure_reference_rows,
)
from .workstreams import utc_now


CLASSIFICATION_KINDS = {"topic", "tag"}
COVERAGE_VALUES = {"reference", "metadata", "indexed"}
FRESHNESS_VALUES = {"unknown", "current", "due", "stale", "unavailable"}
SERVICE_VALUES = {"jira", "confluence"}
ITEM_TYPE_VALUES = {"jira_issue", "confluence_page"}
MAX_NOTE_LENGTH = 50_000
MAX_TOPIC_DESCRIPTION = 4_000
MAX_CLASSIFICATION_NAME = 160
MAX_TAGS_PER_ITEM = 30
MAX_EXACT_QUERY_TOKENS = 12
MAX_EXACT_EXCERPT_LENGTH = 240
MAX_PREVIEW_METADATA_ENTRIES = 12
MAX_PREVIEW_METADATA_PATH = 160
MAX_PREVIEW_METADATA_VALUE = 240
MAX_PREVIEW_CONTENT = 1_200
MAX_PREVIEW_NOTE = 600
MAX_PREVIEW_CLASSIFICATIONS = 30
MAX_PREVIEW_EVIDENCE = 5
MAX_PREVIEW_ORGANIZATION = 5
MAX_SQLITE_INTEGER = 9_223_372_036_854_775_807
ADVANCED_FILTER_FIELDS = (
    "coverage",
    "freshness",
    "attention",
    "topic_id",
    "tag_id",
    "workstream_id",
)
REFERENCE_EXCLUDING_FILTER_FIELDS = (
    "source_instance_id",
    "space_id",
    "item_type",
    *ADVANCED_FILTER_FIELDS,
)


class AtlassianBrowseError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _fail(code: str, message: str) -> None:
    raise AtlassianBrowseError(code, message)


def _integer(value: Any, label: str) -> Optional[int]:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        _fail("invalid-filter", "{} must be an integer".format(label))
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        _fail("invalid-filter", "{} must be an integer".format(label))
    if normalized < 1 or normalized > MAX_SQLITE_INTEGER:
        _fail("invalid-filter", "{} is outside the supported range".format(label))
    return normalized


def _choice(value: Any, allowed: set[str], label: str) -> Optional[str]:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    if normalized not in allowed:
        _fail("invalid-filter", "Unsupported {} filter".format(label))
    return normalized


def normalize_browse_filters(values: Optional[Mapping[str, Any]] = None) -> dict:
    source = values or {}
    query = str(source.get("q") or "").strip()
    if len(query) > 300:
        _fail("invalid-query", "Query exceeds 300 characters")
    attention = _choice(
        source.get("attention"),
        ATTENTION_VALUES | {"all"},
        "attention",
    )
    raw_structural_scope = source.get("structural_scope")
    structural_scope = normalize_atlassian_structural_scope(
        raw_structural_scope
    )
    if raw_structural_scope not in (None, "") and structural_scope is None:
        _fail("invalid-filter", "Unsupported structural_scope filter")
    filters = {
        "q": query,
        "service": _choice(source.get("service"), SERVICE_VALUES, "service"),
        "source_instance_id": _integer(
            source.get("source_instance_id"), "source_instance_id"
        ),
        "site_id": _integer(source.get("site_id"), "site_id"),
        "space_id": _integer(source.get("space_id"), "space_id"),
        "structural_scope": structural_scope,
        "item_type": _choice(
            source.get("item_type"), ITEM_TYPE_VALUES, "item_type"
        ),
        "coverage": _choice(
            source.get("coverage"), COVERAGE_VALUES, "coverage"
        ),
        "freshness": _choice(
            source.get("freshness"), FRESHNESS_VALUES, "freshness"
        ),
        "attention": attention,
        "topic_id": _integer(source.get("topic_id"), "topic_id"),
        "tag_id": _integer(source.get("tag_id"), "tag_id"),
        "workstream_id": _integer(
            source.get("workstream_id"), "workstream_id"
        ),
    }
    if filters["space_id"] is not None and filters["structural_scope"]:
        _fail(
            "invalid-filter",
            "space_id and structural_scope cannot be combined",
        )
    if filters["structural_scope"] and filters["site_id"] is None:
        _fail(
            "invalid-filter",
            "structural_scope requires site_id",
        )
    return filters


def normalize_browse_structure(
    connection: sqlite3.Connection, filters: Mapping[str, Any]
) -> dict:
    normalized = dict(filters)
    space_id = normalized.get("space_id")
    if space_id is not None:
        space_owner = connection.execute(
            """
            SELECT site_id, service
            FROM atlassian_spaces
            WHERE id = ?
            """,
            (space_id,),
        ).fetchone()
        if space_owner is not None:
            if (
                normalized.get("service") is not None
                and space_owner["service"] != normalized["service"]
            ):
                _fail(
                    "invalid-filter",
                    "Space is unavailable for the selected service",
                )
            normalized["site_id"] = int(space_owner["site_id"])

    site_id = normalized.get("site_id")
    service = normalized.get("service")
    structural_service = structural_scope_service(
        normalized.get("structural_scope")
    )
    if (
        service is not None
        and structural_service is not None
        and service != structural_service
    ):
        _fail(
            "invalid-filter",
            "URL container is unavailable for the selected service",
        )
    if site_id is not None and service is not None:
        site_services = {
            str(row["service"])
            for row in connection.execute(
                """
                SELECT DISTINCT service
                FROM atlassian_items
                WHERE site_id = ?
                """,
                (site_id,),
            ).fetchall()
        }
        if space_id is None:
            site_services.update(
                str(row["service"])
                for row in connection.execute(
                    """
                    SELECT DISTINCT service
                    FROM atlassian_spaces
                    WHERE site_id = ?
                    """,
                    (site_id,),
                ).fetchall()
            )
            site_services.update(
                str(row["service"])
                for row in connection.execute(
                    """
                    SELECT DISTINCT service
                    FROM atlassian_structure_references AS reference
                    WHERE site_id = ?
                      AND EXISTS (
                          SELECT 1
                          FROM atlassian_structure_reference_evidence AS evidence
                          WHERE evidence.reference_id = reference.id
                      )
                    """,
                    (site_id,),
                ).fetchall()
            )
        if site_services and service not in site_services:
            _fail(
                "invalid-filter",
                "Site is unavailable for the selected service",
            )
    return normalized


def validate_browse_structural_scope(
    connection: sqlite3.Connection, filters: Mapping[str, Any]
) -> None:
    structural_scope = filters.get("structural_scope")
    if structural_scope is None:
        return

    def projected_scope(value: Any) -> str:
        hint = atlassian_url_container_hint(value)
        return (
            str(hint["structural_scope"])
            if hint is not None
            else "unclassified"
        )

    try:
        connection.create_function(
            "localbrain_atlassian_container_scope",
            1,
            projected_scope,
            deterministic=True,
        )
    except TypeError:
        connection.create_function(
            "localbrain_atlassian_container_scope", 1, projected_scope
        )
    row = connection.execute(
        """
        SELECT 1
        FROM atlassian_items
        JOIN atlassian_item_urls
          ON atlassian_item_urls.external_resource_id =
             atlassian_items.external_resource_id
         AND atlassian_item_urls.url_role = 'canonical'
        WHERE atlassian_items.site_id = ?
          AND atlassian_items.space_id IS NULL
          AND (? IS NULL OR atlassian_items.service = ?)
          AND localbrain_atlassian_container_scope(
                  atlassian_item_urls.normalized_url
              ) = ?
        LIMIT 1
        """,
        (
            filters.get("site_id"),
            filters.get("service"),
            filters.get("service"),
            structural_scope,
        ),
    ).fetchone()
    if row is None:
        row = connection.execute(
            """
            SELECT 1
            FROM atlassian_structure_references AS reference
            WHERE reference.site_id = ?
              AND (? IS NULL OR reference.service = ?)
              AND EXISTS (
                  SELECT 1
                  FROM atlassian_structure_reference_evidence
                  WHERE reference_id = reference.id
              )
              AND CASE
                    WHEN (
                        SELECT COUNT(DISTINCT container_hint)
                        FROM atlassian_structure_reference_evidence
                        WHERE reference_id = reference.id
                    ) = 1
                    THEN 'url:' || reference.service || ':' ||
                         (
                             SELECT MIN(container_hint)
                             FROM atlassian_structure_reference_evidence
                             WHERE reference_id = reference.id
                         )
                    ELSE 'unclassified'
                  END = ?
            LIMIT 1
            """,
            (
                filters.get("site_id"),
                filters.get("service"),
                filters.get("service"),
                structural_scope,
            ),
        ).fetchone()
    if row is None:
        _fail(
            "invalid-filter",
            "Structural scope is unavailable for the selected Site",
        )


def _exact_tokens(value: Any) -> tuple[str, ...]:
    tokens = tuple(
        unicodedata.normalize("NFKC", token).casefold()
        for token in re.findall(r"\w+", str(value or ""), flags=re.UNICODE)
    )
    return tokens


def _exact_query_tokens(query: str) -> tuple[str, ...]:
    tokens = _exact_tokens(query)
    if query and not tokens:
        _fail("invalid-query", "Query has no searchable words")
    if len(tokens) > MAX_EXACT_QUERY_TOKENS:
        _fail(
            "invalid-query",
            "Query supports at most {} words".format(
                MAX_EXACT_QUERY_TOKENS
            ),
        )
    return tokens


def _contains_exact_phrase(value: Any, query_tokens: tuple[str, ...]) -> bool:
    value_tokens = _exact_tokens(value)
    width = len(query_tokens)
    if not width or len(value_tokens) < width:
        return False
    return any(
        value_tokens[index : index + width] == query_tokens
        for index in range(len(value_tokens) - width + 1)
    )


def _bounded_exact_excerpt(value: Any, query_tokens: tuple[str, ...]) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= MAX_EXACT_EXCERPT_LENGTH:
        return text
    folded = text.casefold()
    marker = query_tokens[0] if query_tokens else ""
    match_at = folded.find(marker) if marker else 0
    start = max(0, match_at - 72) if match_at >= 0 else 0
    end = min(len(text), start + MAX_EXACT_EXCERPT_LENGTH)
    if end - start < MAX_EXACT_EXCERPT_LENGTH:
        start = max(0, end - MAX_EXACT_EXCERPT_LENGTH)
    excerpt = "{}{}{}".format(
        "... " if start else "",
        text[start:end].strip(),
        " ..." if end < len(text) else "",
    )
    if len(excerpt) > MAX_EXACT_EXCERPT_LENGTH:
        excerpt = "{} ...".format(
            excerpt[: MAX_EXACT_EXCERPT_LENGTH - 4].rstrip()
        )
    return excerpt


def _flatten_exact_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, Mapping):
        for key in sorted(value):
            values.extend(_flatten_exact_values(value[key]))
    elif isinstance(value, list):
        for item in value:
            values.extend(_flatten_exact_values(item))
    elif value is not None:
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def _fts_expression(query: str) -> str:
    tokens = re.findall(r"[\w.-]+", query, flags=re.UNICODE)
    return " AND ".join(
        '"{}"'.format(token.replace('"', '""')) for token in tokens[:12]
    )


def _classification_maps(connection: sqlite3.Connection) -> tuple[dict, dict]:
    classifications = [
        dict(row)
        for row in connection.execute(
            """
            SELECT * FROM atlassian_classifications
            ORDER BY kind, normalized_name, id
            """
        ).fetchall()
    ]
    memberships: dict[int, dict[str, list[dict]]] = {}
    for row in connection.execute(
        """
        SELECT atlassian_item_classifications.external_resource_id,
               atlassian_classifications.*
        FROM atlassian_item_classifications
        JOIN atlassian_classifications
          ON atlassian_classifications.id =
             atlassian_item_classifications.classification_id
        ORDER BY atlassian_classifications.kind,
                 atlassian_classifications.normalized_name
        """
    ).fetchall():
        item_id = int(row["external_resource_id"])
        item = memberships.setdefault(item_id, {"topics": [], "tags": []})
        item["topics" if row["kind"] == "topic" else "tags"].append(
            {
                key: row[key]
                for key in (
                    "id",
                    "kind",
                    "name",
                    "normalized_name",
                    "description",
                )
            }
        )
    return {
        "topics": [
            item for item in classifications if item["kind"] == "topic"
        ],
        "tags": [item for item in classifications if item["kind"] == "tag"],
    }, memberships


def _workstream_membership_map(connection: sqlite3.Connection) -> dict[int, set[int]]:
    values: dict[int, set[int]] = {}
    rows = connection.execute(
        """
        SELECT CAST(workstream_links.entity_id AS INTEGER) AS item_id,
               workstream_links.workstream_id
        FROM workstream_links
        JOIN atlassian_items
          ON atlassian_items.external_resource_id =
             CAST(workstream_links.entity_id AS INTEGER)
        WHERE workstream_links.entity_type = 'external'
        UNION
        SELECT CAST(thread_links.entity_id AS INTEGER),
               threads.workstream_id
        FROM thread_links
        JOIN threads ON threads.id = thread_links.thread_id
        JOIN atlassian_items
          ON atlassian_items.external_resource_id =
             CAST(thread_links.entity_id AS INTEGER)
        WHERE thread_links.entity_type = 'external'
        """
    ).fetchall()
    for row in rows:
        values.setdefault(int(row["item_id"]), set()).add(
            int(row["workstream_id"])
        )
    return values


def _service_label(service: str) -> str:
    return "Jira" if service == "jira" else "Wiki"


def project_atlassian_item_container(item: dict) -> dict:
    service = str(item["service"])
    if item.get("space_id") is not None:
        item.update(
            {
                "container_kind": "space",
                "container_label": item.get("space_name") or "이름 없음",
                "container_service": service,
                "container_cue": _service_label(service),
                "container_structural_scope": None,
            }
        )
        return item
    hint = atlassian_url_container_hint(item.get("canonical_url"))
    if hint is not None:
        item.update(
            {
                "container_kind": "url",
                "container_label": hint["label"],
                "container_service": hint["service"],
                "container_cue": "{} · URL 기준".format(
                    _service_label(str(hint["service"]))
                ),
                "container_structural_scope": hint["structural_scope"],
            }
        )
        return item
    item.update(
        {
            "container_kind": "unclassified",
            "container_label": "소속 미확인",
            "container_service": None,
            "container_cue": None,
            "container_structural_scope": "unclassified",
        }
    )
    return item


def _item_rows(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        """
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.service,
               atlassian_items.item_type,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               atlassian_items.confirmed_at,
               atlassian_items.updated_at AS item_updated_at,
               external_resources.title AS local_title,
               external_resources.summary AS local_summary,
               atlassian_sites.id AS site_id,
               atlassian_sites.display_name AS site_name,
               atlassian_sites.normalized_domain,
               atlassian_spaces.id AS space_id,
               atlassian_spaces.name AS space_name,
               atlassian_spaces.space_key,
               external_source_instances.id AS source_instance_id,
               COALESCE(
                   external_source_instances.display_name, '로컬 전용'
               ) AS source_name,
               atlassian_item_urls.normalized_url AS canonical_url,
               atlassian_item_remote_state.metadata_json,
               atlassian_item_remote_state.remote_version,
               atlassian_item_remote_state.remote_updated_at,
               atlassian_item_remote_state.last_attempted_at,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.last_error_code,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale,
               atlassian_item_content.normalized_text,
               atlassian_item_content.normalization_warning,
               atlassian_item_content.applied_at AS content_applied_at,
               atlassian_item_local_state.note
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
        LEFT JOIN atlassian_item_local_state
          ON atlassian_item_local_state.external_resource_id =
             atlassian_items.external_resource_id
        ORDER BY CASE atlassian_items.attention WHEN 'pinned' THEN 0 ELSE 1 END,
                 atlassian_items.updated_at DESC,
                 atlassian_items.external_resource_id DESC
        """
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        except json.JSONDecodeError:
            item["metadata"] = {}
        item["freshness"] = derive_atlassian_freshness(
            item["service"], item
        )
        item["display_title"] = (
            item["metadata"].get("title")
            or item["metadata"].get("summary")
            or item["local_title"]
        )
        item.update(
            {
                "entity_kind": "item",
                "entity_id": int(item["id"]),
                "stable_key": "item:{}".format(item["id"]),
                "updated_at": item["item_updated_at"],
            }
        )
        items.append(project_atlassian_item_container(item))
    return items


def _item_url_map(connection: sqlite3.Connection) -> dict[int, list[dict]]:
    values: dict[int, list[dict]] = {}
    rows = connection.execute(
        """
        SELECT external_resource_id, url_role, normalized_url
        FROM atlassian_item_urls
        ORDER BY external_resource_id,
                 CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END,
                 id
        """
    ).fetchall()
    for row in rows:
        values.setdefault(int(row["external_resource_id"]), []).append(
            dict(row)
        )
    return values


def _normalized_query_url(query: str) -> Optional[str]:
    if not re.match(r"^https?://", query, flags=re.IGNORECASE):
        return None
    try:
        return normalize_atlassian_url(query).normalized_url
    except AtlassianContractError as exc:
        raise AtlassianBrowseError(
            "invalid-query", "HTTP(S) query URL is invalid"
        ) from exc


def _exact_identity_value(
    item: Mapping[str, Any],
    urls: Iterable[Mapping[str, Any]],
    query: str,
    normalized_query_url: Optional[str],
) -> Optional[str]:
    folded_query = query.casefold()
    for value in (item.get("remote_key"), item.get("remote_id")):
        if value is not None and str(value).casefold() == folded_query:
            return str(value)
    if normalized_query_url is None:
        return None
    for value in urls:
        if value.get("normalized_url") == normalized_query_url:
            return str(value["normalized_url"])
    return None


def _exact_title_values(item: Mapping[str, Any]) -> list[str]:
    metadata = item.get("metadata") or {}
    values = [
        item.get("local_title"),
        metadata.get("title") if isinstance(metadata, Mapping) else None,
        metadata.get("summary") if isinstance(metadata, Mapping) else None,
    ]
    return list(
        dict.fromkeys(str(value) for value in values if value is not None)
    )


def _exact_other_values(
    item: Mapping[str, Any], item_memberships: Mapping[str, list[dict]]
) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    metadata = item.get("metadata") or {}
    if isinstance(metadata, Mapping):
        other_metadata = {
            key: value
            for key, value in metadata.items()
            if key not in {"title", "summary"}
        }
        values.extend(
            ("metadata", value)
            for value in _flatten_exact_values(other_metadata)
        )
    if (
        item.get("coverage") == "indexed"
        and item.get("freshness") != "unavailable"
        and item.get("normalized_text")
    ):
        values.append(("content", str(item["normalized_text"])))
    if item.get("note"):
        values.append(("local", str(item["note"])))
    for topic in item_memberships.get("topics", []):
        if topic.get("name"):
            values.append(("local", str(topic["name"])))
        if topic.get("description"):
            values.append(("local", str(topic["description"])))
    for tag in item_memberships.get("tags", []):
        if tag.get("name"):
            values.append(("local", str(tag["name"])))
    return values


def _exact_item_matches(
    connection: sqlite3.Connection,
    items: Iterable[dict],
    memberships: Mapping[int, dict],
    query: str,
) -> Optional[dict[int, dict]]:
    cleaned = query.strip()
    if not cleaned:
        return None
    query_tokens = _exact_query_tokens(cleaned)
    urls_by_item = _item_url_map(connection)
    normalized_query_url = _normalized_query_url(cleaned)
    matches: dict[int, dict] = {}
    for item in items:
        item_id = int(item["id"])
        identity_value = _exact_identity_value(
            item,
            urls_by_item.get(item_id, []),
            cleaned,
            normalized_query_url,
        )
        if identity_value is not None:
            matches[item_id] = {
                "rank": 0,
                "role": "identity",
                "excerpt": _bounded_exact_excerpt(
                    identity_value, query_tokens
                ),
            }
            continue
        title_value = next(
            (
                value
                for value in _exact_title_values(item)
                if _contains_exact_phrase(value, query_tokens)
            ),
            None,
        )
        if title_value is not None:
            matches[item_id] = {
                "rank": 1,
                "role": "title",
                "excerpt": _bounded_exact_excerpt(
                    title_value, query_tokens
                ),
            }
            continue
        for role, value in _exact_other_values(
            item,
            memberships.get(item_id, {"topics": [], "tags": []}),
        ):
            if _contains_exact_phrase(value, query_tokens):
                matches[item_id] = {
                    "rank": 2,
                    "role": role,
                    "excerpt": _bounded_exact_excerpt(value, query_tokens),
                }
                break
    return matches


def _reference_url_map(
    connection: sqlite3.Connection,
    reference_ids: Iterable[int],
) -> dict[int, list[str]]:
    ids = tuple(sorted(set(int(value) for value in reference_ids)))
    if not ids:
        return {}
    values: dict[int, list[str]] = {}
    for offset in range(0, len(ids), 400):
        batch = ids[offset : offset + 400]
        placeholders = ",".join("?" for _ in batch)
        for row in connection.execute(
            """
            SELECT reference_id, safe_locator_url
            FROM atlassian_structure_reference_urls
            WHERE reference_id IN ({})
            ORDER BY reference_id,
                     CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END,
                     id
            """.format(placeholders),
            batch,
        ).fetchall():
            values.setdefault(int(row["reference_id"]), []).append(
                str(row["safe_locator_url"])
            )
    return values


def _normalized_reference_query_url(query: str) -> Optional[str]:
    if not re.match(r"^https?://", query, flags=re.IGNORECASE):
        return None
    locator = describe_atlassian_url(query)
    if locator.kind == "unsafe":
        _fail("invalid-query", "HTTP(S) query URL is invalid")
    return locator.safe_locator_url


def _exact_reference_matches(
    connection: sqlite3.Connection,
    references: Iterable[dict],
    query: str,
) -> Optional[dict[int, dict]]:
    cleaned = query.strip()
    if not cleaned:
        return None
    query_tokens = _exact_query_tokens(cleaned)
    reference_values = list(references)
    urls_by_reference = _reference_url_map(
        connection, (int(value["id"]) for value in reference_values)
    )
    normalized_url = _normalized_reference_query_url(cleaned)
    folded_query = unicodedata.normalize("NFKC", cleaned).casefold()
    matches: dict[int, dict] = {}
    for reference in reference_values:
        reference_id = int(reference["id"])
        identity = str(reference["reference_identity"])
        identity_value = None
        identity_role = "identity"
        if unicodedata.normalize("NFKC", identity).casefold() == folded_query:
            identity_value = identity
        elif normalized_url is not None:
            identity_value = next(
                (
                    value
                    for value in urls_by_reference.get(reference_id, [])
                    if value == normalized_url
                ),
                None,
            )
            identity_role = "url"
        if identity_value is not None:
            matches[reference_id] = {
                "rank": 0,
                "role": identity_role,
                "excerpt": _bounded_exact_excerpt(
                    identity_value, query_tokens
                ),
            }
            continue
        generated = "{} {}".format(
            reference["family_label"], reference["reference_identity"]
        )
        if _contains_exact_phrase(generated, query_tokens):
            matches[reference_id] = {
                "rank": 1,
                "role": "title",
                "excerpt": _bounded_exact_excerpt(generated, query_tokens),
            }
    return matches


def _filter_reference(
    reference: Mapping[str, Any],
    filters: Mapping[str, Any],
    *,
    matching_ids: Optional[set[int]],
) -> bool:
    if reference.get("lifecycle") == "archived":
        return False
    if matching_ids is not None and int(reference["id"]) not in matching_ids:
        return False
    if any(filters.get(field) not in (None, "") for field in REFERENCE_EXCLUDING_FILTER_FIELDS):
        return False
    for field in ("service", "site_id"):
        if filters.get(field) is not None and reference.get(field) != filters[field]:
            return False
    if (
        filters.get("structural_scope") is not None
        and reference.get("container_structural_scope")
        != filters["structural_scope"]
    ):
        return False
    return True


def _filter_item(
    item: dict,
    filters: dict,
    *,
    matching_ids: Optional[set[int]],
    memberships: Mapping[int, dict],
    workstreams: Mapping[int, set[int]],
) -> bool:
    if matching_ids is not None and item["id"] not in matching_ids:
        return False
    for field in (
        "service",
        "source_instance_id",
        "site_id",
        "space_id",
        "item_type",
        "coverage",
        "freshness",
    ):
        if filters[field] is not None and item[field] != filters[field]:
            return False
    if (
        filters["structural_scope"] is not None
        and item.get("container_structural_scope")
        != filters["structural_scope"]
    ):
        return False
    attention = filters["attention"]
    if attention is None and item["attention"] == "archived":
        return False
    if attention not in (None, "all") and item["attention"] != attention:
        return False
    item_classes = memberships.get(item["id"], {"topics": [], "tags": []})
    if filters["topic_id"] is not None and filters["topic_id"] not in {
        value["id"] for value in item_classes["topics"]
    }:
        return False
    if filters["tag_id"] is not None and filters["tag_id"] not in {
        value["id"] for value in item_classes["tags"]
    }:
        return False
    if (
        filters["workstream_id"] is not None
        and filters["workstream_id"] not in workstreams.get(item["id"], set())
    ):
        return False
    return True


def _selected_zero_space(
    connection: sqlite3.Connection,
    filters: Mapping[str, Any],
    eligible_items: Iterable[Mapping[str, Any]],
) -> Optional[dict]:
    if filters.get("site_id") is None or filters.get("space_id") is None:
        return None
    if any(
        (filters.get("service") is None or item.get("service") == filters["service"])
        and item.get("site_id") == filters["site_id"]
        and item.get("space_id") == filters["space_id"]
        for item in eligible_items
    ):
        return None
    row = connection.execute(
        """
        SELECT atlassian_spaces.id, atlassian_spaces.site_id,
               atlassian_spaces.service, atlassian_spaces.name,
               atlassian_spaces.space_key,
               atlassian_sites.display_name AS site_name,
               atlassian_sites.normalized_domain
        FROM atlassian_spaces
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_spaces.site_id
        WHERE atlassian_spaces.id = ?
          AND atlassian_spaces.site_id = ?
        """,
        (
            filters["space_id"],
            filters["site_id"],
        ),
    ).fetchone()
    if (
        row is None
        or filters.get("service") is not None
        and row["service"] != filters["service"]
    ):
        return None
    return dict(row)


def _selected_zero_structure(
    filters: Mapping[str, Any],
    eligible_entries: Iterable[Mapping[str, Any]],
    all_entries: Iterable[Mapping[str, Any]],
) -> Optional[dict]:
    structural_scope = filters.get("structural_scope")
    site_id = filters.get("site_id")
    if structural_scope is None or site_id is None:
        return None
    matches = lambda item: (
        int(item["site_id"]) == int(site_id)
        and (
            filters.get("service") is None
            or item.get("service") == filters["service"]
        )
        and item.get("container_structural_scope") == structural_scope
    )
    if any(matches(item) for item in eligible_entries):
        return None
    selected = next((dict(item) for item in all_entries if matches(item)), None)
    if selected is None:
        _fail(
            "invalid-filter",
            "Structural scope is unavailable for the selected Site",
        )
    return selected


def _hierarchy_projection(
    items: Iterable[Mapping[str, Any]],
    selected_empty_space: Optional[Mapping[str, Any]] = None,
    selected_empty_structure: Optional[Mapping[str, Any]] = None,
) -> dict:
    sites: dict[int, dict] = {}

    def site_node(
        site_id: int,
        *,
        normalized_domain: Any,
        display_name: Any = None,
    ) -> dict:
        return sites.setdefault(
            site_id,
            {
                "id": site_id,
                "name": normalized_domain,
                "display_name": display_name,
                "normalized_domain": normalized_domain,
                "count": 0,
                "item_count": 0,
                "reference_count": 0,
                "containers_by_key": {},
            },
        )

    def container_node(owner: dict, item: Mapping[str, Any]) -> dict:
        kind = str(item["container_kind"])
        if kind == "space":
            identity = (kind, int(item["space_id"]))
            value = {
                "kind": kind,
                "id": int(item["space_id"]),
                "structural_scope": None,
            }
        else:
            structural_scope = str(item["container_structural_scope"])
            identity = (kind, structural_scope)
            value = {
                "kind": kind,
                "id": None,
                "structural_scope": structural_scope,
            }
        value.update(
            {
                "name": item["container_label"],
                "count": 0,
                "item_count": 0,
                "reference_count": 0,
                "service": item.get("container_service"),
                "cue": item.get("container_cue"),
            }
        )
        return owner["containers_by_key"].setdefault(identity, value)

    for item in items:
        site_id = int(item["site_id"])
        owner = site_node(
            site_id,
            normalized_domain=item.get("normalized_domain"),
            display_name=item.get("site_name"),
        )
        owner["count"] += 1
        count_key = (
            "reference_count"
            if item.get("entity_kind") == "reference"
            else "item_count"
        )
        owner[count_key] += 1
        container = container_node(owner, item)
        container["count"] += 1
        container[count_key] += 1

    if selected_empty_space is not None:
        site_id = int(selected_empty_space["site_id"])
        owner = site_node(
            site_id,
            normalized_domain=selected_empty_space.get("normalized_domain"),
            display_name=selected_empty_space.get("site_name"),
        )
        space_id = int(selected_empty_space["id"])
        owner["containers_by_key"].setdefault(
            ("space", space_id),
            {
                "kind": "space",
                "id": space_id,
                "structural_scope": None,
                "name": selected_empty_space.get("name") or "이름 없음",
                "count": 0,
                "item_count": 0,
                "reference_count": 0,
                "service": selected_empty_space.get("service"),
                "cue": _service_label(
                    str(selected_empty_space.get("service"))
                ),
            },
        )

    if selected_empty_structure is not None:
        site_id = int(selected_empty_structure["site_id"])
        owner = site_node(
            site_id,
            normalized_domain=selected_empty_structure.get(
                "normalized_domain"
            ),
            display_name=selected_empty_structure.get("site_name"),
        )
        container_node(owner, selected_empty_structure)

    projected_sites = []
    for owner in sorted(
        sites.values(),
        key=lambda value: (
            str(value.get("normalized_domain") or "").casefold(),
            int(value["id"]),
        ),
    ):
        owner["containers"] = sorted(
            owner.pop("containers_by_key").values(),
            key=lambda value: (
                value["kind"] == "unclassified",
                str(value.get("name") or "").casefold(),
                str(value.get("kind") or ""),
                int(value.get("id") or 0),
                str(value.get("structural_scope") or ""),
            ),
        )
        projected_sites.append(owner)
    return {
        "eligible_count": sum(site["count"] for site in projected_sites),
        "count": sum(site["count"] for site in projected_sites),
        "item_count": sum(site["item_count"] for site in projected_sites),
        "reference_count": sum(
            site["reference_count"] for site in projected_sites
        ),
        "sites": projected_sites,
    }


def _active_structure(
    filters: Mapping[str, Any],
    items: Iterable[dict],
    selected_empty_space: Optional[Mapping[str, Any]] = None,
    selected_empty_structure: Optional[Mapping[str, Any]] = None,
) -> dict:
    service = filters.get("service")
    site_id = filters.get("site_id")
    space_id = filters.get("space_id")
    structural_scope = filters.get("structural_scope")
    if site_id is None and space_id is None and structural_scope is None:
        return {"kind": "root", "label": "모든 도메인"}

    all_items = list(items)
    if selected_empty_space is not None:
        return {
            "kind": "space",
            "label": "{} / {}".format(
                selected_empty_space.get("normalized_domain")
                or selected_empty_space.get("site_name"),
                selected_empty_space.get("name") or "이름 없음",
            ),
            "empty_registered_space": True,
        }
    if selected_empty_structure is not None:
        return {
            "kind": selected_empty_structure["container_kind"],
            "label": "{} / {}".format(
                selected_empty_structure.get("normalized_domain"),
                selected_empty_structure["container_label"],
            ),
            "empty_selected_structure": True,
        }
    selected_item = next(
        (
            item
            for item in all_items
            if (service is None or item["service"] == service)
            and (site_id is None or item["site_id"] == site_id)
            and (space_id is None or item.get("space_id") == space_id)
            and (
                structural_scope is None
                or item.get("container_structural_scope")
                == structural_scope
            )
        ),
        None,
    )
    if selected_item is None:
        return {"kind": "unavailable", "label": "Unavailable scope"}
    site_label = selected_item.get("normalized_domain") or selected_item.get(
        "site_name"
    )
    if space_id is not None:
        return {
            "kind": "space",
            "label": "{} / {}".format(
                site_label, selected_item.get("space_name") or "이름 없음"
            ),
        }
    if structural_scope == "unclassified":
        return {
            "kind": "unclassified",
            "label": "{} / 소속 미확인".format(site_label),
        }
    if structural_scope is not None:
        return {
            "kind": "url",
            "label": "{} / {}".format(
                site_label, selected_item.get("container_label")
            ),
        }
    return {"kind": "site", "label": str(site_label)}


def _ordered_browse_entries(entries: Iterable[dict], *, query: bool) -> list[dict]:
    values = list(entries)
    if query:
        return sorted(
            values,
            key=lambda value: (
                int(value["exact_match"]["rank"]),
                0 if value.get("entity_kind") == "item" else 1,
                int(value["id"]),
            ),
        )
    values.sort(key=lambda value: int(value["id"]), reverse=True)
    values.sort(key=lambda value: 0 if value.get("entity_kind") == "item" else 1)
    values.sort(key=lambda value: str(value.get("updated_at") or ""), reverse=True)
    values.sort(
        key=lambda value: (
            0
            if value.get("entity_kind") == "item"
            and value.get("attention") == "pinned"
            else 1
        )
    )
    return values


def browse_inventory(
    connection: sqlite3.Connection,
    values: Optional[Mapping[str, Any]] = None,
) -> dict:
    filters = normalize_browse_structure(
        connection, normalize_browse_filters(values)
    )
    options, memberships = _classification_maps(connection)
    workstream_memberships = _workstream_membership_map(connection)
    all_items = _item_rows(connection)
    all_references = structure_reference_rows(
        connection, include_archived=True
    )
    exact_matches = _exact_item_matches(
        connection,
        all_items,
        memberships,
        filters["q"],
    )
    matching_ids = (
        None if exact_matches is None else set(exact_matches)
    )
    exact_reference_matches = _exact_reference_matches(
        connection, all_references, filters["q"]
    )
    matching_reference_ids = (
        None
        if exact_reference_matches is None
        else set(exact_reference_matches)
    )
    eligible_filters = {
        **filters,
        "site_id": None,
        "space_id": None,
        "structural_scope": None,
    }
    eligible_items = [
        item
        for item in all_items
        if _filter_item(
            item,
            eligible_filters,
            matching_ids=matching_ids,
            memberships=memberships,
            workstreams=workstream_memberships,
        )
    ]
    eligible_references = [
        reference
        for reference in all_references
        if _filter_reference(
            reference,
            eligible_filters,
            matching_ids=matching_reference_ids,
        )
    ]
    items = []
    for item in all_items:
        if not _filter_item(
            item,
            filters,
            matching_ids=matching_ids,
            memberships=memberships,
            workstreams=workstream_memberships,
        ):
            continue
        item.update(
            memberships.get(item["id"], {"topics": [], "tags": []})
        )
        item["workstream_ids"] = sorted(
            workstream_memberships.get(item["id"], set())
        )
        if exact_matches is not None:
            item["exact_match"] = exact_matches[item["id"]]
        items.append(item)
    if exact_matches is not None:
        items.sort(
            key=lambda item: (
                item["exact_match"]["rank"],
                int(item["id"]),
            )
        )
    references = []
    for reference in all_references:
        if not _filter_reference(
            reference,
            filters,
            matching_ids=matching_reference_ids,
        ):
            continue
        if exact_reference_matches is not None:
            reference["exact_match"] = exact_reference_matches[
                int(reference["id"])
            ]
        references.append(reference)
    if exact_reference_matches is not None:
        references.sort(
            key=lambda reference: (
                reference["exact_match"]["rank"],
                int(reference["id"]),
            )
        )
    entries = _ordered_browse_entries(
        [*items, *references], query=bool(filters["q"])
    )
    selected_empty_space = _selected_zero_space(
        connection, filters, eligible_items
    )
    selected_empty_structure = _selected_zero_structure(
        filters,
        [*eligible_items, *eligible_references],
        [
            *all_items,
            *(
                reference
                for reference in all_references
                if reference["lifecycle"] != "archived"
            ),
        ],
    )
    options.update(
        {
            "sources": [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT DISTINCT external_source_instances.id,
                           external_source_instances.display_name,
                           external_source_instances.service
                    FROM external_source_instances
                    JOIN atlassian_site_bindings
                      ON atlassian_site_bindings.source_instance_id =
                         external_source_instances.id
                    ORDER BY external_source_instances.display_name,
                             external_source_instances.id
                    """
                )
            ],
            "sites": [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT DISTINCT atlassian_sites.id,
                           NULL AS source_instance_id,
                           atlassian_sites.normalized_domain,
                           atlassian_sites.display_name,
                           scoped_sites.service
                    FROM atlassian_sites
                    JOIN (
                        SELECT site_id, service FROM atlassian_items
                        UNION
                        SELECT site_id, service FROM atlassian_spaces
                        UNION
                        SELECT reference.site_id, reference.service
                        FROM atlassian_structure_references AS reference
                        WHERE EXISTS (
                            SELECT 1
                            FROM atlassian_structure_reference_evidence AS evidence
                            WHERE evidence.reference_id = reference.id
                        )
                    ) AS scoped_sites
                      ON scoped_sites.site_id = atlassian_sites.id
                    ORDER BY atlassian_sites.normalized_domain,
                             atlassian_sites.id
                    """
                )
            ],
            "spaces": [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, site_id, service, name, space_key
                    FROM atlassian_spaces
                    ORDER BY service, name, id
                    """
                )
            ],
            "workstreams": [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, name, status FROM workstreams
                    ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END,
                             name, id
                    """
                )
            ],
        }
    )
    return {
        "filters": filters,
        "items": items,
        "references": references,
        "entries": entries,
        "hierarchy": _hierarchy_projection(
            [*eligible_items, *eligible_references],
            selected_empty_space,
            selected_empty_structure,
        ),
        "eligible_count": len(eligible_items) + len(eligible_references),
        "eligible_item_count": len(eligible_items),
        "eligible_reference_count": len(eligible_references),
        "known_item_count": sum(
            filters["service"] is None
            or item["service"] == filters["service"]
            for item in all_items
        ),
        "known_reference_count": sum(
            reference["lifecycle"] != "archived"
            and (
                filters["service"] is None
                or reference["service"] == filters["service"]
            )
            for reference in all_references
        ),
        "known_count": sum(
            filters["service"] is None
            or item["service"] == filters["service"]
            for item in all_items
        )
        + sum(
            reference["lifecycle"] != "archived"
            and (
                filters["service"] is None
                or reference["service"] == filters["service"]
            )
            for reference in all_references
        ),
        "matching_count": len(entries),
        "matching_item_count": len(items),
        "matching_reference_count": len(references),
        "has_filters": any(value is not None and value != "" for value in filters.values()),
        "has_advanced_filters": any(
            filters[field] is not None for field in ADVANCED_FILTER_FIELDS
        ),
        "active_filter_count": sum(
            filters[field] is not None for field in ADVANCED_FILTER_FIELDS
        ),
        "active_structure": _active_structure(
            filters,
            [
                *all_items,
                *(
                    reference
                    for reference in all_references
                    if reference["lifecycle"] != "archived"
                ),
            ],
            selected_empty_space,
            selected_empty_structure,
        ),
        "options": options,
    }


def _latest_refresh_run(
    connection: sqlite3.Connection, external_resource_id: int
) -> Optional[dict]:
    target_id = "atlassian-item-{}".format(external_resource_id)
    rows = connection.execute(
        """
        SELECT maintenance_runs.id, maintenance_runs.status,
               maintenance_runs.runner, maintenance_runs.summary,
               maintenance_runs.error, maintenance_runs.created_at,
               maintenance_runs.started_at, maintenance_runs.completed_at,
               maintenance_runs.source_snapshot_json
        FROM maintenance_runs
        JOIN external_sync_runs
          ON external_sync_runs.maintenance_run_id = maintenance_runs.id
        WHERE maintenance_runs.task_type = 'external_source_sync'
        ORDER BY maintenance_runs.created_at DESC, maintenance_runs.id DESC
        LIMIT 200
        """
    ).fetchall()
    for row in rows:
        try:
            manifest = json.loads(row["source_snapshot_json"] or "{}")
        except json.JSONDecodeError:
            continue
        if not isinstance(manifest, Mapping):
            continue
        if any(
            isinstance(target, Mapping)
            and target.get("target_id") == target_id
            for target in manifest.get("targets") or []
        ):
            value = dict(row)
            value.pop("source_snapshot_json", None)
            return value
    return None


def _unicode_codepoint_length(value: str) -> int:
    length = 0
    index = 0
    while index < len(value):
        codepoint = ord(value[index])
        if (
            0xD800 <= codepoint <= 0xDBFF
            and index + 1 < len(value)
            and 0xDC00 <= ord(value[index + 1]) <= 0xDFFF
        ):
            index += 2
        else:
            index += 1
        length += 1
    return length


def _unicode_prefix(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    parts = []
    index = 0
    length = 0
    while index < len(value) and length < limit:
        codepoint = ord(value[index])
        if (
            0xD800 <= codepoint <= 0xDBFF
            and index + 1 < len(value)
            and 0xDC00 <= ord(value[index + 1]) <= 0xDFFF
        ):
            parts.append(value[index : index + 2])
            index += 2
        else:
            parts.append(value[index])
            index += 1
        length += 1
    return "".join(parts)


def _preview_excerpt(value: Any, limit: int) -> tuple[Any, bool]:
    if value is None:
        return None, False
    text = str(value)
    if _unicode_codepoint_length(text) <= limit:
        return text, False
    return "{}…".format(_unicode_prefix(text, limit - 1)), True


def _preview_metadata_scalars(
    value: Any, prefix: str = "", *, top_level: bool = False
) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if isinstance(value, Mapping):
        for key in sorted(value, key=lambda item: str(item)):
            if top_level and key in {"title", "summary"}:
                continue
            escaped_key = (
                str(key)
                .replace("\\", "\\\\")
                .replace(".", "\\.")
                .replace("[", "\\[")
                .replace("]", "\\]")
            )
            path = (
                "{}.{}".format(prefix, escaped_key)
                if prefix
                else escaped_key
            )
            values.extend(_preview_metadata_scalars(value[key], path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = "{}[{}]".format(prefix, index)
            values.extend(_preview_metadata_scalars(child, path))
    elif prefix and value is not None:
        if isinstance(value, (bool, int, float)):
            text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        elif isinstance(value, str):
            text = str(value)
        else:
            return values
        values.append((prefix, text))
    return values


def _preview_metadata_summary(metadata: Mapping[str, Any]) -> tuple[list, int]:
    scalars = sorted(
        _preview_metadata_scalars(metadata, top_level=True),
        key=lambda item: item[0],
    )
    summary = []
    for path, value in scalars[:MAX_PREVIEW_METADATA_ENTRIES]:
        bounded_path, path_truncated = _preview_excerpt(
            path, MAX_PREVIEW_METADATA_PATH
        )
        bounded_value, value_truncated = _preview_excerpt(
            value, MAX_PREVIEW_METADATA_VALUE
        )
        summary.append(
            {
                "path": bounded_path,
                "value": bounded_value,
                "path_truncated": path_truncated,
                "value_truncated": value_truncated,
            }
        )
    return summary, len(scalars)


def _preview_item_row(
    connection: sqlite3.Connection, external_resource_id: int
) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT atlassian_items.external_resource_id AS id,
               atlassian_items.service,
               atlassian_items.item_type,
               atlassian_items.coverage,
               atlassian_items.attention,
               atlassian_items.remote_id,
               atlassian_items.remote_key,
               atlassian_items.source_instance_id,
               external_resources.title AS local_title,
               atlassian_sites.id AS site_id,
               atlassian_sites.display_name AS site_name,
               atlassian_sites.normalized_domain,
               atlassian_spaces.id AS space_id,
               atlassian_spaces.name AS space_name,
               atlassian_spaces.space_key,
               (
                   SELECT atlassian_item_urls.normalized_url
                   FROM atlassian_item_urls
                   WHERE atlassian_item_urls.external_resource_id =
                         atlassian_items.external_resource_id
                     AND atlassian_item_urls.url_role = 'canonical'
                   ORDER BY atlassian_item_urls.id
                   LIMIT 1
               ) AS canonical_url,
               atlassian_item_remote_state.metadata_json,
               atlassian_item_remote_state.remote_version,
               atlassian_item_remote_state.remote_updated_at,
               atlassian_item_remote_state.last_attempted_at,
               atlassian_item_remote_state.last_successful_at,
               atlassian_item_remote_state.last_outcome,
               atlassian_item_remote_state.last_error_code,
               atlassian_item_remote_state.known_changed,
               atlassian_item_remote_state.projection_stale
        FROM atlassian_items
        JOIN external_resources
          ON external_resources.id = atlassian_items.external_resource_id
        JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN atlassian_spaces
          ON atlassian_spaces.id = atlassian_items.space_id
        LEFT JOIN atlassian_item_remote_state
          ON atlassian_item_remote_state.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone()
    if row is None:
        return None
    item = dict(row)
    try:
        metadata = json.loads(item.pop("metadata_json") or "{}")
    except (json.JSONDecodeError, TypeError):
        metadata = {}
    if not isinstance(metadata, Mapping):
        metadata = {}
    item["metadata"] = metadata
    item["freshness"] = derive_atlassian_freshness(item["service"], item)
    item["display_title"] = (
        metadata.get("title")
        or metadata.get("summary")
        or item["local_title"]
    )
    return project_atlassian_item_container(item)


def _preview_identity(item: Mapping[str, Any], *, eligible: bool) -> dict:
    return {
        "id": int(item["id"]),
        "eligible": eligible,
        "service": item.get("service"),
        "item_type": item.get("item_type"),
        "display_title": item.get("display_title"),
        "local_title": item.get("local_title"),
        "remote_key": item.get("remote_key"),
        "source_instance_id": item.get("source_instance_id"),
        "site_id": item.get("site_id"),
        "site_name": item.get("site_name"),
        "normalized_domain": item.get("normalized_domain"),
        "space_id": item.get("space_id"),
        "space_name": item.get("space_name"),
        "space_key": item.get("space_key"),
        "container_kind": item.get("container_kind"),
        "container_label": item.get("container_label"),
        "container_service": item.get("container_service"),
        "container_cue": item.get("container_cue"),
        "container_structural_scope": item.get(
            "container_structural_scope"
        ),
        "canonical_url": item.get("canonical_url"),
        "coverage": item.get("coverage"),
        "freshness": item.get("freshness"),
        "attention": item.get("attention"),
    }


def _preview_item_urls(
    connection: sqlite3.Connection, external_resource_id: int
) -> list[dict]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT url_role, normalized_url
            FROM atlassian_item_urls
            WHERE external_resource_id = ?
            ORDER BY CASE url_role WHEN 'canonical' THEN 0 ELSE 1 END, id
            """,
            (external_resource_id,),
        ).fetchall()
    ]


def _preview_all_classifications(
    connection: sqlite3.Connection, external_resource_id: int
) -> dict[str, list[dict]]:
    memberships: dict[str, list[dict]] = {"topics": [], "tags": []}
    rows = connection.execute(
        """
        SELECT atlassian_classifications.id,
               atlassian_classifications.kind,
               atlassian_classifications.name,
               atlassian_classifications.normalized_name,
               atlassian_classifications.description
        FROM atlassian_item_classifications
        JOIN atlassian_classifications
          ON atlassian_classifications.id =
             atlassian_item_classifications.classification_id
        WHERE atlassian_item_classifications.external_resource_id = ?
        ORDER BY atlassian_classifications.kind,
                 atlassian_classifications.normalized_name,
                 atlassian_classifications.id
        """,
        (external_resource_id,),
    ).fetchall()
    for row in rows:
        value = dict(row)
        memberships["topics" if row["kind"] == "topic" else "tags"].append(
            value
        )
    return memberships


def _preview_requested_classifications(
    connection: sqlite3.Connection,
    external_resource_id: int,
    *,
    topic_id: Optional[int],
    tag_id: Optional[int],
) -> dict[str, list[dict]]:
    memberships: dict[str, list[dict]] = {"topics": [], "tags": []}
    if topic_id is None and tag_id is None:
        return memberships
    rows = connection.execute(
        """
        SELECT atlassian_classifications.id,
               atlassian_classifications.kind
        FROM atlassian_item_classifications
        JOIN atlassian_classifications
          ON atlassian_classifications.id =
             atlassian_item_classifications.classification_id
        WHERE atlassian_item_classifications.external_resource_id = ?
          AND (
              (atlassian_classifications.kind = 'topic'
               AND ? IS NOT NULL
               AND atlassian_classifications.id = ?)
              OR
              (atlassian_classifications.kind = 'tag'
               AND ? IS NOT NULL
               AND atlassian_classifications.id = ?)
          )
        """,
        (external_resource_id, topic_id, topic_id, tag_id, tag_id),
    ).fetchall()
    for row in rows:
        key = "topics" if row["kind"] == "topic" else "tags"
        memberships[key].append({"id": int(row["id"])})
    return memberships


def _preview_classification_projection(
    connection: sqlite3.Connection,
    external_resource_id: int,
) -> tuple[dict, dict]:
    rows = connection.execute(
        """
        WITH ranked_classifications AS (
            SELECT atlassian_classifications.id,
                   atlassian_classifications.kind,
                   atlassian_classifications.name,
                   atlassian_classifications.normalized_name,
                   COUNT(*) OVER (
                       PARTITION BY atlassian_classifications.kind
                   ) AS preview_total,
                   ROW_NUMBER() OVER (
                       PARTITION BY atlassian_classifications.kind
                       ORDER BY atlassian_classifications.normalized_name,
                                atlassian_classifications.id
                   ) AS preview_rank
            FROM atlassian_item_classifications
            JOIN atlassian_classifications
              ON atlassian_classifications.id =
                 atlassian_item_classifications.classification_id
            WHERE atlassian_item_classifications.external_resource_id = ?
        )
        SELECT id, kind, name, normalized_name, preview_total
        FROM ranked_classifications
        WHERE preview_rank <= ?
        ORDER BY kind, normalized_name, id
        """,
        (external_resource_id, MAX_PREVIEW_CLASSIFICATIONS),
    ).fetchall()
    values = {
        "topic": {"items": [], "total": 0, "truncated": False},
        "tag": {"items": [], "total": 0, "truncated": False},
    }
    for row in rows:
        kind = str(row["kind"])
        values[kind]["total"] = int(row["preview_total"])
        values[kind]["items"].append(
            {
                "id": int(row["id"]),
                "name": row["name"],
                "normalized_name": row["normalized_name"],
            }
        )
    for value in values.values():
        value["truncated"] = value["total"] > len(value["items"])
    return values["topic"], values["tag"]


def _preview_classification_projection_from_memberships(
    memberships: Mapping[str, list[dict]],
) -> tuple[dict, dict]:
    values = []
    for source_key in ("topics", "tags"):
        ordered = sorted(
            memberships.get(source_key, []),
            key=lambda item: (str(item.get("normalized_name") or ""), int(item["id"])),
        )
        items = [
            {
                "id": int(item["id"]),
                "name": item.get("name"),
                "normalized_name": item.get("normalized_name"),
            }
            for item in ordered[:MAX_PREVIEW_CLASSIFICATIONS]
        ]
        values.append(
            {
                "items": items,
                "total": len(ordered),
                "truncated": len(ordered) > len(items),
            }
        )
    return values[0], values[1]


def _preview_text_values(
    connection: sqlite3.Connection,
    external_resource_id: int,
) -> dict:
    row = connection.execute(
        """
        SELECT SUBSTR(
                   atlassian_item_content.normalized_text, 1, ?
               ) AS normalized_text,
               SUBSTR(
                   atlassian_item_local_state.note, 1, ?
               ) AS note
        FROM atlassian_items
        LEFT JOIN atlassian_item_content
          ON atlassian_item_content.external_resource_id =
             atlassian_items.external_resource_id
        LEFT JOIN atlassian_item_local_state
          ON atlassian_item_local_state.external_resource_id =
             atlassian_items.external_resource_id
        WHERE atlassian_items.external_resource_id = ?
        """,
        (
            MAX_PREVIEW_CONTENT + 1,
            MAX_PREVIEW_NOTE + 1,
            external_resource_id,
        ),
    ).fetchone()
    return dict(row) if row is not None else {"normalized_text": None, "note": None}


def _preview_text_matches(
    connection: sqlite3.Connection,
    external_resource_id: int,
    query_tokens: tuple[str, ...],
    *,
    include_content: bool,
) -> bool:
    function_name = "localbrain_atlassian_exact_phrase"
    connection.create_function(
        function_name,
        1,
        lambda value: int(_contains_exact_phrase(value, query_tokens)),
        deterministic=True,
    )
    try:
        row = connection.execute(
            """
            SELECT CASE
                     WHEN ? = 1
                      AND atlassian_items.coverage = 'indexed'
                     THEN localbrain_atlassian_exact_phrase(
                              atlassian_item_content.normalized_text
                          )
                     ELSE 0
                   END AS content_matches,
                   localbrain_atlassian_exact_phrase(
                       atlassian_item_local_state.note
                   ) AS note_matches
            FROM atlassian_items
            LEFT JOIN atlassian_item_content
              ON atlassian_item_content.external_resource_id =
                 atlassian_items.external_resource_id
            LEFT JOIN atlassian_item_local_state
              ON atlassian_item_local_state.external_resource_id =
                 atlassian_items.external_resource_id
            WHERE atlassian_items.external_resource_id = ?
            """,
            (int(include_content), external_resource_id),
        ).fetchone()
    finally:
        connection.create_function(function_name, 1, None)
    return bool(
        row
        and (int(row["content_matches"] or 0) or int(row["note_matches"] or 0))
    )


def _preview_has_workstream(
    connection: sqlite3.Connection,
    external_resource_id: int,
    workstream_id: int,
) -> bool:
    return (
        connection.execute(
            """
            SELECT 1
            FROM workstream_links
            WHERE workstream_links.entity_type = 'external'
              AND workstream_links.entity_id = ?
              AND workstream_links.workstream_id = ?
            UNION ALL
            SELECT 1
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            WHERE thread_links.entity_type = 'external'
              AND thread_links.entity_id = ?
              AND threads.workstream_id = ?
            LIMIT 1
            """,
            (
                str(external_resource_id),
                workstream_id,
                str(external_resource_id),
                workstream_id,
            ),
        ).fetchone()
        is not None
    )


def _preview_evidence(
    connection: sqlite3.Connection, external_resource_id: int
) -> dict:
    rows = connection.execute(
        """
        WITH ranked_evidence AS (
            SELECT atlassian_item_evidence.id,
                   atlassian_item_evidence.session_id,
                   atlassian_item_evidence.document_id,
                   atlassian_item_evidence.source_channel,
                   atlassian_item_evidence.source_line,
                   atlassian_item_evidence.observed_url,
                   atlassian_item_evidence.observed_at,
                   atlassian_item_evidence.last_observed_at,
                   sessions.title AS session_title,
                   context_documents.title AS document_title,
                   context_documents.relative_path AS document_path,
                   COALESCE(
                       atlassian_item_evidence.observed_at,
                       atlassian_item_evidence.last_observed_at
                   ) AS observed_order,
                   COUNT(*) OVER () AS preview_total,
                   ROW_NUMBER() OVER (
                       ORDER BY COALESCE(
                                    atlassian_item_evidence.observed_at,
                                    atlassian_item_evidence.last_observed_at
                                ) DESC,
                                atlassian_item_evidence.id DESC
                   ) AS preview_rank
            FROM atlassian_item_evidence
            LEFT JOIN sessions
              ON sessions.id = atlassian_item_evidence.session_id
            LEFT JOIN context_documents
              ON context_documents.id =
                 atlassian_item_evidence.document_id
            WHERE atlassian_item_evidence.external_resource_id = ?
        )
        SELECT id, session_id, document_id, source_channel, source_line,
               observed_url, observed_at, last_observed_at,
               session_title, document_title, document_path,
               observed_order, preview_total
        FROM ranked_evidence
        WHERE preview_rank <= ?
        ORDER BY observed_order DESC, id DESC
        """,
        (external_resource_id, MAX_PREVIEW_EVIDENCE),
    ).fetchall()
    items = []
    for row in rows:
        value = dict(row)
        value.pop("preview_total", None)
        value.pop("observed_order", None)
        items.append(value)
    total = int(rows[0]["preview_total"]) if rows else 0
    return {
        "items": items,
        "total": total,
        "truncated": total > len(items),
    }


def _preview_organization(
    connection: sqlite3.Connection, external_resource_id: int
) -> dict:
    rows = connection.execute(
        """
        WITH item_organization AS (
            SELECT workstream_links.id AS link_id,
                   'workstream' AS scope_type,
                   workstreams.id AS scope_id,
                   workstreams.id AS workstream_id,
                   workstreams.name AS workstream_name,
                   NULL AS thread_id,
                   NULL AS thread_title,
                   workstream_links.relation_type
            FROM workstream_links
            JOIN workstreams
              ON workstreams.id = workstream_links.workstream_id
            WHERE workstream_links.entity_type = 'external'
              AND workstream_links.entity_id = ?
            UNION ALL
            SELECT thread_links.id,
                   'thread',
                   threads.id,
                   workstreams.id,
                   workstreams.name,
                   threads.id,
                   threads.title,
                   thread_links.relation_type
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            JOIN workstreams
              ON workstreams.id = threads.workstream_id
            WHERE thread_links.entity_type = 'external'
              AND thread_links.entity_id = ?
        )
        SELECT item_organization.*, COUNT(*) OVER () AS preview_total
        FROM item_organization
        ORDER BY workstream_name, thread_title
        LIMIT ?
        """,
        (
            str(external_resource_id),
            str(external_resource_id),
            MAX_PREVIEW_ORGANIZATION,
        ),
    ).fetchall()
    items = []
    for row in rows:
        value = dict(row)
        value.pop("preview_total", None)
        items.append(value)
    total = int(rows[0]["preview_total"]) if rows else 0
    return {
        "items": items,
        "total": total,
        "truncated": total > len(items),
    }


def atlassian_item_preview(
    connection: sqlite3.Connection,
    external_resource_id: int,
    values: Optional[Mapping[str, Any]] = None,
) -> Optional[dict]:
    filters = normalize_browse_structure(
        connection, normalize_browse_filters(values)
    )
    cleaned_query = filters["q"]
    query_tokens = _exact_query_tokens(cleaned_query) if cleaned_query else ()
    normalized_query_url = (
        _normalized_query_url(cleaned_query) if cleaned_query else None
    )
    item = _preview_item_row(connection, external_resource_id)
    if item is None:
        return None

    scalar_filters = {
        **filters,
        "topic_id": None,
        "tag_id": None,
        "workstream_id": None,
    }
    if not _filter_item(
        item,
        scalar_filters,
        matching_ids=None,
        memberships={},
        workstreams={},
    ):
        return _preview_identity(item, eligible=False)

    exact_memberships: Optional[dict[str, list[dict]]] = None
    exact_match = not cleaned_query
    if cleaned_query:
        identity_value = _exact_identity_value(
            item,
            _preview_item_urls(connection, external_resource_id),
            cleaned_query,
            normalized_query_url,
        )
        exact_match = identity_value is not None or any(
            _contains_exact_phrase(value, query_tokens)
            for value in _exact_title_values(item)
        )
        if not exact_match:
            exact_memberships = _preview_all_classifications(
                connection, external_resource_id
            )
            exact_match = any(
                _contains_exact_phrase(value, query_tokens)
                for _role, value in _exact_other_values(
                    item, exact_memberships
                )
            )
        if not exact_match:
            exact_match = _preview_text_matches(
                connection,
                external_resource_id,
                query_tokens,
                include_content=item.get("freshness") != "unavailable",
            )
        if not exact_match:
            return _preview_identity(item, eligible=False)

    memberships = exact_memberships or _preview_requested_classifications(
        connection,
        external_resource_id,
        topic_id=filters["topic_id"],
        tag_id=filters["tag_id"],
    )
    workstream_ids: set[int] = set()
    if filters["workstream_id"] is not None and _preview_has_workstream(
        connection, external_resource_id, filters["workstream_id"]
    ):
        workstream_ids.add(filters["workstream_id"])
    if not _filter_item(
        item,
        filters,
        matching_ids={int(item["id"])} if cleaned_query else None,
        memberships={int(item["id"]): memberships},
        workstreams={int(item["id"]): workstream_ids},
    ):
        return _preview_identity(item, eligible=False)

    if exact_memberships is None:
        topics, tags = _preview_classification_projection(
            connection, external_resource_id
        )
    else:
        topics, tags = _preview_classification_projection_from_memberships(
            exact_memberships
        )
    text_values = _preview_text_values(connection, external_resource_id)
    content_excerpt, content_truncated = _preview_excerpt(
        text_values.get("normalized_text"), MAX_PREVIEW_CONTENT
    )
    note_excerpt, note_truncated = _preview_excerpt(
        text_values.get("note"), MAX_PREVIEW_NOTE
    )
    metadata_summary, metadata_total = _preview_metadata_summary(
        item["metadata"]
    )
    recent_refresh_run = _latest_refresh_run(
        connection, external_resource_id
    )
    return {
        **_preview_identity(item, eligible=True),
        "last_attempted_at": item.get("last_attempted_at"),
        "last_successful_at": item.get("last_successful_at"),
        "last_outcome": item.get("last_outcome"),
        "remote_id": item.get("remote_id"),
        "remote_version": item.get("remote_version"),
        "remote_updated_at": item.get("remote_updated_at"),
        "last_error_code": item.get("last_error_code"),
        "metadata_summary": metadata_summary,
        "metadata_summary_total": metadata_total,
        "metadata_summary_truncated": (
            metadata_total > len(metadata_summary)
        ),
        "content_excerpt": content_excerpt,
        "content_truncated": content_truncated,
        "note_excerpt": note_excerpt,
        "note_truncated": note_truncated,
        "topics": topics,
        "tags": tags,
        "evidence": _preview_evidence(connection, external_resource_id),
        "organization": _preview_organization(
            connection, external_resource_id
        ),
        "recent_refresh_run": recent_refresh_run,
        "history_scope": "recent-200",
        "history_complete": False,
        "history_absence": (
            None
            if recent_refresh_run is not None
            else "not found in recent history"
        ),
    }


def atlassian_structure_reference_preview(
    connection: sqlite3.Connection,
    reference_id: int,
    values: Optional[Mapping[str, Any]] = None,
) -> Optional[dict]:
    filters = normalize_browse_structure(
        connection, normalize_browse_filters(values)
    )
    reference = structure_reference_preview(connection, reference_id)
    if reference is None:
        return None
    exact_matches = _exact_reference_matches(
        connection, [reference], filters["q"]
    )
    eligible = _filter_reference(
        reference,
        filters,
        matching_ids=(
            None if exact_matches is None else set(exact_matches)
        ),
    )
    reference["eligible"] = eligible
    if exact_matches is not None and reference_id in exact_matches:
        reference["exact_match"] = exact_matches[reference_id]
    return reference


def atlassian_structure_reference_detail(
    connection: sqlite3.Connection, reference_id: int
) -> Optional[dict]:
    return structure_reference_detail(connection, reference_id)


def atlassian_item_detail(
    connection: sqlite3.Connection, external_resource_id: int
) -> Optional[dict]:
    item = next(
        (
            value
            for value in _item_rows(connection)
            if value["id"] == external_resource_id
        ),
        None,
    )
    if item is None:
        return None
    options, memberships = _classification_maps(connection)
    item.update(
        memberships.get(item["id"], {"topics": [], "tags": []})
    )
    item["selected_topic_ids"] = {
        topic["id"] for topic in item["topics"]
    }
    item["memberships"] = [
        dict(row)
        for row in connection.execute(
            """
            SELECT workstream_links.id AS link_id,
                   'workstream' AS scope_type,
                   workstreams.id AS scope_id,
                   workstreams.id AS workstream_id,
                   workstreams.name AS workstream_name,
                   NULL AS thread_id,
                   NULL AS thread_title,
                   workstream_links.relation_type
            FROM workstream_links
            JOIN workstreams
              ON workstreams.id = workstream_links.workstream_id
            WHERE workstream_links.entity_type = 'external'
              AND workstream_links.entity_id = ?
            UNION ALL
            SELECT thread_links.id,
                   'thread',
                   threads.id,
                   workstreams.id,
                   workstreams.name,
                   threads.id,
                   threads.title,
                   thread_links.relation_type
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            JOIN workstreams
              ON workstreams.id = threads.workstream_id
            WHERE thread_links.entity_type = 'external'
              AND thread_links.entity_id = ?
            ORDER BY workstream_name, thread_title
            """,
            (str(external_resource_id), str(external_resource_id)),
        ).fetchall()
    ]
    item["evidence"] = [
        dict(row)
        for row in connection.execute(
            """
            SELECT atlassian_item_evidence.id,
                   atlassian_item_evidence.session_id,
                   atlassian_item_evidence.document_id,
                   atlassian_item_evidence.source_channel,
                   atlassian_item_evidence.source_line,
                   atlassian_item_evidence.observed_url,
                   atlassian_item_evidence.observed_at,
                   sessions.title AS session_title,
                   context_documents.title AS document_title,
                   context_documents.relative_path AS document_path
            FROM atlassian_item_evidence
            LEFT JOIN sessions
              ON sessions.id = atlassian_item_evidence.session_id
            LEFT JOIN context_documents
              ON context_documents.id =
                 atlassian_item_evidence.document_id
            WHERE atlassian_item_evidence.external_resource_id = ?
            ORDER BY COALESCE(
                         atlassian_item_evidence.observed_at,
                         atlassian_item_evidence.last_observed_at
                     ) DESC,
                     atlassian_item_evidence.id DESC
            """,
            (external_resource_id,),
        ).fetchall()
    ]
    item["latest_refresh_run"] = _latest_refresh_run(
        connection, external_resource_id
    )
    item["classification_options"] = options
    item["workstreams"] = []
    for row in connection.execute(
        """
        SELECT id, name, status FROM workstreams
        ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, name, id
        """
    ).fetchall():
        workstream = dict(row)
        workstream["threads"] = [
            dict(thread)
            for thread in connection.execute(
                """
                SELECT id, title, status FROM threads
                WHERE workstream_id = ?
                ORDER BY position, title, id
                """,
                (row["id"],),
            ).fetchall()
        ]
        item["workstreams"].append(workstream)
    return item


def _classification_name(value: Any, label: str) -> tuple[str, str]:
    name = " ".join(str(value or "").split())
    if not name or len(name) > MAX_CLASSIFICATION_NAME:
        _fail(
            "invalid-classification",
            "{} must be 1-{} characters".format(
                label, MAX_CLASSIFICATION_NAME
            ),
        )
    return name, name.casefold()


def _upsert_classification(
    connection: sqlite3.Connection,
    *,
    kind: str,
    name: str,
    description: Optional[str] = None,
    changed_at: str,
) -> int:
    if kind not in CLASSIFICATION_KINDS:
        _fail("invalid-classification", "Unsupported classification kind")
    name, normalized_name = _classification_name(name, kind)
    if kind == "tag":
        description = None
    elif description is not None:
        description = str(description).strip() or None
        if description and len(description) > MAX_TOPIC_DESCRIPTION:
            _fail(
                "invalid-topic-description",
                "Topic description exceeds 4000 characters",
            )
    connection.execute(
        """
        INSERT INTO atlassian_classifications(
            kind, name, normalized_name, description, updated_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(kind, normalized_name) DO UPDATE SET
            name = excluded.name,
            description = CASE
                WHEN excluded.kind = 'topic'
                THEN excluded.description
                ELSE NULL
            END,
            updated_at = excluded.updated_at
        """,
        (kind, name, normalized_name, description, changed_at),
    )
    return int(
        connection.execute(
            """
            SELECT id FROM atlassian_classifications
            WHERE kind = ? AND normalized_name = ?
            """,
            (kind, normalized_name),
        ).fetchone()["id"]
    )


def update_atlassian_local_state(
    connection: sqlite3.Connection,
    external_resource_id: int,
    *,
    note: str,
    attention: str,
    topic_ids: Iterable[int] = (),
    tags: str = "",
    new_topic_name: str = "",
    new_topic_description: str = "",
    changed_at: Optional[str] = None,
) -> dict:
    if not connection.execute(
        """
        SELECT 1 FROM atlassian_items WHERE external_resource_id = ?
        """,
        (external_resource_id,),
    ).fetchone():
        _fail("item-not-found", "Atlassian 링크/문서를 찾을 수 없습니다")
    note = str(note or "").strip()
    if len(note) > MAX_NOTE_LENGTH:
        _fail("invalid-note", "Local note exceeds 50000 characters")
    if attention not in ATTENTION_VALUES:
        _fail("invalid-attention", "Unsupported attention state")
    now = changed_at or utc_now()
    normalized_topic_ids = list(dict.fromkeys(int(value) for value in topic_ids))
    if normalized_topic_ids:
        placeholders = ",".join("?" for _ in normalized_topic_ids)
        valid = {
            int(row["id"])
            for row in connection.execute(
                """
                SELECT id FROM atlassian_classifications
                WHERE kind = 'topic' AND id IN ({})
                """.format(placeholders),
                tuple(normalized_topic_ids),
            ).fetchall()
        }
        if valid != set(normalized_topic_ids):
            _fail("invalid-topic", "A selected Topic was not found")
    has_new_topic = bool(str(new_topic_name or "").strip())
    if has_new_topic:
        _classification_name(new_topic_name, "topic")
        description = str(new_topic_description or "").strip()
        if len(description) > MAX_TOPIC_DESCRIPTION:
            _fail(
                "invalid-topic-description",
                "Topic description exceeds 4000 characters",
            )
    tag_names = []
    tag_keys = set()
    for value in str(tags or "").split(","):
        name = value.strip()
        key = name.casefold()
        if name and key not in tag_keys:
            tag_names.append(name)
            tag_keys.add(key)
    if len(tag_names) > MAX_TAGS_PER_ITEM:
        _fail("too-many-tags", "링크/문서는 Tag를 최대 30개까지 지원합니다")
    for name in tag_names:
        _classification_name(name, "tag")

    connection.execute("SAVEPOINT atlassian_local_state")
    try:
        if has_new_topic:
            normalized_topic_ids.append(
                _upsert_classification(
                    connection,
                    kind="topic",
                    name=new_topic_name,
                    description=new_topic_description,
                    changed_at=now,
                )
            )
            normalized_topic_ids = list(dict.fromkeys(normalized_topic_ids))
        tag_ids = [
            _upsert_classification(
                connection,
                kind="tag",
                name=name,
                changed_at=now,
            )
            for name in tag_names
        ]
        if note:
            connection.execute(
                """
                INSERT INTO atlassian_item_local_state(
                    external_resource_id, note, updated_at
                ) VALUES (?, ?, ?)
                ON CONFLICT(external_resource_id) DO UPDATE SET
                    note = excluded.note,
                    updated_at = excluded.updated_at
                """,
                (external_resource_id, note, now),
            )
        else:
            connection.execute(
                """
                DELETE FROM atlassian_item_local_state
                WHERE external_resource_id = ?
                """,
                (external_resource_id,),
            )
        for kind in ("topic", "tag"):
            connection.execute(
                """
                DELETE FROM atlassian_item_classifications
                WHERE external_resource_id = ?
                  AND classification_id IN (
                      SELECT id FROM atlassian_classifications
                      WHERE kind = ?
                  )
                """,
                (external_resource_id, kind),
            )
        connection.executemany(
            """
            INSERT INTO atlassian_item_classifications(
                external_resource_id, classification_id
            ) VALUES (?, ?)
            """,
            [
                (external_resource_id, classification_id)
                for classification_id in normalized_topic_ids + tag_ids
            ],
        )
        set_atlassian_item_axes(
            connection,
            external_resource_id,
            attention=attention,
            changed_at=now,
        )
        project_atlassian_item_search(
            connection, external_resource_id, changed_at=now
        )
    except Exception:
        connection.execute("ROLLBACK TO atlassian_local_state")
        connection.execute("RELEASE atlassian_local_state")
        raise
    connection.execute("RELEASE atlassian_local_state")
    return atlassian_item_detail(connection, external_resource_id) or {}


def atlassian_search_results(
    connection: sqlite3.Connection,
    query: str,
    values: Optional[Mapping[str, Any]] = None,
    *,
    limit: int = 80,
) -> list[dict]:
    expression = _fts_expression(query)
    if not expression:
        return []
    inventory = browse_inventory(
        connection, {**dict(values or {}), "q": ""}
    )
    allowed_items = {item["id"]: item for item in inventory["items"]}
    allowed_references = {
        reference["id"]: reference
        for reference in inventory["references"]
    }
    reference_matches = _exact_reference_matches(
        connection, allowed_references.values(), query
    ) or {}
    grouped: dict[tuple[str, int], dict] = {}
    rows = connection.execute(
        """
        SELECT entity_type, entity_id, source_kind, title, path,
               snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
               highlight(search_index, 3, '[[', ']]') AS matched_title,
               bm25(search_index) AS score
        FROM search_index
        WHERE search_index MATCH ?
          AND entity_type IN (
              'atlassian_item', 'atlassian_structure_reference'
          )
        ORDER BY score
        LIMIT 400
        """,
        (expression,),
    ).fetchall()
    for row in rows:
        entity_type = str(row["entity_type"])
        entity_id = int(row["entity_id"])
        if entity_type == "atlassian_structure_reference":
            reference = allowed_references.get(entity_id)
            if reference is None:
                continue
            exact = reference_matches.get(entity_id)
            role = exact["role"] if exact is not None else "url"
            grouped[(entity_type, entity_id)] = {
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "source_kind": "atlassian:{}".format(reference["service"]),
                "title": "{} · {}".format(
                    reference["family_label"],
                    reference["reference_identity"],
                ),
                "path": reference["canonical_url"],
                "excerpt": (
                    exact["excerpt"]
                    if exact is not None
                    else (row["excerpt"] or row["matched_title"])
                ),
                "score": row["score"],
                "match_roles": [role],
                "entity_kind": "reference",
                "service": reference["service"],
                "normalized_domain": reference["normalized_domain"],
                "reference_kind": reference["reference_kind"],
                "reference_identity": reference["reference_identity"],
                "family_label": reference["family_label"],
                "availability": reference["availability"],
                "provenance": reference["provenance"],
                "container_kind": reference["container_kind"],
                "container_label": reference["container_label"],
                "container_service": reference["container_service"],
                "container_cue": reference["container_cue"],
            }
            continue
        item_id = entity_id
        item = allowed_items.get(item_id)
        if item is None:
            continue
        result = grouped.setdefault(
            (entity_type, item_id),
            {
                "entity_type": "atlassian_item",
                "entity_id": str(item_id),
                "source_kind": "atlassian:{}".format(item["service"]),
                "title": item["display_title"],
                "path": item["canonical_url"],
                "excerpt": row["excerpt"] or row["matched_title"],
                "score": row["score"],
                "match_roles": [],
                "service": item["service"],
                "item_type": item["item_type"],
                "source_name": item["source_name"],
                "normalized_domain": item["normalized_domain"],
                "space_name": item["space_name"],
                "container_kind": item["container_kind"],
                "container_label": item["container_label"],
                "container_service": item["container_service"],
                "container_cue": item["container_cue"],
                "coverage": item["coverage"],
                "freshness": item["freshness"],
                "attention": item["attention"],
            },
        )
        role = row["source_kind"].rsplit(":", 1)[-1]
        if role not in result["match_roles"]:
            result["match_roles"].append(role)
        if row["score"] < result["score"]:
            result["score"] = row["score"]
            result["excerpt"] = row["excerpt"] or row["matched_title"]
    return sorted(
        grouped.values(),
        key=lambda result: (
            result["score"],
            result["title"],
            result["entity_type"],
            result["entity_id"],
        ),
    )[:limit]
