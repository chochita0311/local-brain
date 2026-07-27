import json
import re
import sqlite3
from typing import Any, Iterable, Mapping, Optional

from .atlassian import (
    ATTENTION_VALUES,
    derive_atlassian_freshness,
    project_atlassian_item_search,
    set_atlassian_item_axes,
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
    if normalized < 1:
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
    query = str(source.get("q") or "").strip()[:300]
    attention = _choice(
        source.get("attention"),
        ATTENTION_VALUES | {"all"},
        "attention",
    )
    return {
        "q": query,
        "service": _choice(source.get("service"), SERVICE_VALUES, "service"),
        "source_instance_id": _integer(
            source.get("source_instance_id"), "source_instance_id"
        ),
        "site_id": _integer(source.get("site_id"), "site_id"),
        "space_id": _integer(source.get("space_id"), "space_id"),
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


def _fts_expression(query: str) -> str:
    tokens = re.findall(r"[\w.-]+", query, flags=re.UNICODE)
    return " AND ".join(
        '"{}"'.format(token.replace('"', '""')) for token in tokens[:12]
    )


def _matching_item_ids(
    connection: sqlite3.Connection, query: str
) -> Optional[set[int]]:
    expression = _fts_expression(query)
    if not expression:
        return None
    return {
        int(row["entity_id"])
        for row in connection.execute(
            """
            SELECT DISTINCT entity_id
            FROM search_index
            WHERE search_index MATCH ?
              AND entity_type = 'atlassian_item'
            """,
            (expression,),
        ).fetchall()
    }


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
               external_source_instances.display_name AS source_name,
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
        JOIN external_source_instances
          ON external_source_instances.id =
             atlassian_sites.source_instance_id
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
        items.append(item)
    return items


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


def browse_inventory(
    connection: sqlite3.Connection,
    values: Optional[Mapping[str, Any]] = None,
) -> dict:
    filters = normalize_browse_filters(values)
    options, memberships = _classification_maps(connection)
    workstream_memberships = _workstream_membership_map(connection)
    all_items = _item_rows(connection)
    matching_ids = _matching_item_ids(connection, filters["q"])
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
        items.append(item)
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
                    JOIN atlassian_sites
                      ON atlassian_sites.source_instance_id =
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
                    SELECT atlassian_sites.id,
                           atlassian_sites.source_instance_id,
                           atlassian_sites.normalized_domain,
                           atlassian_sites.display_name,
                           external_source_instances.service
                    FROM atlassian_sites
                    JOIN external_source_instances
                      ON external_source_instances.id =
                         atlassian_sites.source_instance_id
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
        "known_count": sum(
            filters["service"] is None
            or item["service"] == filters["service"]
            for item in all_items
        ),
        "matching_count": len(items),
        "has_filters": any(value is not None and value != "" for value in filters.values()),
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
        ORDER BY maintenance_runs.created_at DESC
        LIMIT 200
        """
    ).fetchall()
    for row in rows:
        try:
            manifest = json.loads(row["source_snapshot_json"] or "{}")
        except json.JSONDecodeError:
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
        _fail("item-not-found", "Atlassian Item was not found")
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
        _fail("too-many-tags", "An Item supports at most 30 Tags")
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
        connection, {**dict(values or {}), "q": query}
    )
    allowed = {item["id"]: item for item in inventory["items"]}
    grouped: dict[int, dict] = {}
    rows = connection.execute(
        """
        SELECT entity_id, source_kind, title, path,
               snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
               highlight(search_index, 3, '[[', ']]') AS matched_title,
               bm25(search_index) AS score
        FROM search_index
        WHERE search_index MATCH ?
          AND entity_type = 'atlassian_item'
        ORDER BY score
        LIMIT 400
        """,
        (expression,),
    ).fetchall()
    for row in rows:
        item_id = int(row["entity_id"])
        item = allowed.get(item_id)
        if item is None:
            continue
        result = grouped.setdefault(
            item_id,
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
        key=lambda result: (result["score"], result["title"], result["entity_id"]),
    )[:limit]
