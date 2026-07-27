import sqlite3
from typing import Optional
from urllib.parse import urlsplit


RELATED_CONTEXT_LIMIT = 12
RELATED_CONTEXT_CANDIDATE_LIMIT = 48
REASON_ORDER = (
    ("session-reference", "이 Session에서 참조"),
    ("same-thread", "같은 Thread"),
    ("same-workstream", "같은 Workstream"),
    ("same-workspace", "같은 프로젝트"),
)
REASON_LABELS = dict(REASON_ORDER)
REASON_RANK = {
    reason: position for position, (reason, _) in enumerate(REASON_ORDER)
}


def _positive_entity_id(value: object) -> Optional[int]:
    try:
        entity_id = int(str(value))
    except (TypeError, ValueError):
        return None
    return entity_id if entity_id > 0 else None


def _safe_external_href(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def _local_resource_label(resource_type: Optional[str]) -> str:
    return {
        "repository": "Local Repository",
        "directory": "Local Directory",
        "file": "Local File",
        "path": "Local Path",
    }.get(resource_type or "", "Local Path")


def _external_resource_label(resource_type: Optional[str]) -> str:
    return {
        "document": "Document",
        "jira": "Jira",
        "wiki": "Wiki",
        "slack": "Slack",
        "git": "Git",
        "url": "URL",
    }.get(resource_type or "", "External")


def _load_target(
    connection: sqlite3.Connection,
    entity_type: str,
    raw_entity_id: object,
) -> Optional[dict]:
    entity_id = _positive_entity_id(raw_entity_id)
    if entity_id is None:
        return None
    if entity_type == "document":
        row = connection.execute(
            """
            SELECT context_documents.id, context_documents.title,
                   context_documents.relative_path,
                   sources.name AS source_name,
                   context_roots.label AS root_label,
                   workspaces.display_name AS workspace_name
            FROM context_documents
            JOIN sources ON sources.id = context_documents.source_id
            LEFT JOIN context_roots
              ON context_roots.id = context_documents.context_root_id
            LEFT JOIN workspaces
              ON workspaces.id = context_documents.workspace_id
            WHERE context_documents.id = ?
              AND (
                context_documents.context_root_id IS NULL
                OR context_roots.enabled = 1
              )
            """,
            (entity_id,),
        ).fetchone()
        if row is None:
            return None
        provenance = row["root_label"] or row["source_name"] or "Local Context"
        return {
            "target_key": "document:{}".format(entity_id),
            "entity_type": "document",
            "entity_id": entity_id,
            "title": row["title"],
            "detail": row["relative_path"],
            "resource_label": "Local Context",
            "provenance": provenance,
            "availability": "available",
            "availability_label": None,
            "href": "/documents/{}".format(entity_id),
            "external": False,
        }
    if entity_type == "local":
        row = connection.execute(
            """
            SELECT id, title, path, resource_type, exists_now
            FROM local_resources
            WHERE id = ?
            """,
            (entity_id,),
        ).fetchone()
        if row is None:
            return None
        resource_label = _local_resource_label(row["resource_type"])
        available = bool(row["exists_now"])
        return {
            "target_key": "local:{}".format(entity_id),
            "entity_type": "local",
            "entity_id": entity_id,
            "title": row["title"],
            "detail": row["path"],
            "resource_label": resource_label,
            "provenance": resource_label,
            "availability": "available" if available else "missing",
            "availability_label": None if available else "경로 없음",
            "href": "/local-resources/{}".format(entity_id),
            "external": False,
        }
    if entity_type != "external":
        return None
    row = connection.execute(
        """
        SELECT external_resources.id, external_resources.title,
               external_resources.url, external_resources.resource_type,
               atlassian_items.service, atlassian_items.item_type,
               atlassian_items.attention,
               atlassian_sites.display_name AS site_name,
               atlassian_sites.normalized_domain,
               atlassian_spaces.name AS space_name
        FROM external_resources
        LEFT JOIN atlassian_items
          ON atlassian_items.external_resource_id = external_resources.id
        LEFT JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        LEFT JOIN atlassian_spaces
          ON atlassian_spaces.id = atlassian_items.space_id
        WHERE external_resources.id = ?
        """,
        (entity_id,),
    ).fetchone()
    if row is None:
        return None
    if row["service"]:
        service_label = "Jira" if row["service"] == "jira" else "Confluence"
        provenance_parts = [
            row["site_name"] or row["normalized_domain"],
            row["space_name"],
        ]
        return {
            "target_key": "external:{}".format(entity_id),
            "entity_type": "atlassian",
            "entity_id": entity_id,
            "title": row["title"],
            "detail": row["normalized_domain"],
            "resource_label": service_label,
            "provenance": " · ".join(
                part for part in provenance_parts if part
            ) or service_label,
            "availability": (
                "archived" if row["attention"] == "archived" else "available"
            ),
            "availability_label": (
                "보관됨" if row["attention"] == "archived" else None
            ),
            "href": "/atlassian/items/{}".format(entity_id),
            "external": False,
        }
    resource_label = _external_resource_label(row["resource_type"])
    safe_href = _safe_external_href(row["url"])
    return {
        "target_key": "external:{}".format(entity_id),
        "entity_type": "external",
        "entity_id": entity_id,
        "title": row["title"],
        "detail": row["url"],
        "resource_label": resource_label,
        "provenance": resource_label,
        "availability": "available" if safe_href else "unavailable",
        "availability_label": None if safe_href else "열 수 없음",
        "href": safe_href,
        "external": bool(safe_href),
    }


def _membership_candidates(
    connection: sqlite3.Connection,
    session_id: int,
) -> tuple[list[sqlite3.Row], bool]:
    rows = connection.execute(
        """
        WITH session_threads AS (
            SELECT thread_links.thread_id
            FROM thread_links
            WHERE thread_links.entity_type = 'session'
              AND thread_links.entity_id = ?
        ),
        session_workstreams AS (
            SELECT workstream_links.workstream_id
            FROM workstream_links
            WHERE workstream_links.entity_type = 'session'
              AND workstream_links.entity_id = ?
            UNION
            SELECT threads.workstream_id
            FROM session_threads
            JOIN threads ON threads.id = session_threads.thread_id
        ),
        relationships AS (
            SELECT 1 AS reason_rank, 'same-thread' AS reason_code,
                   thread_links.entity_type, thread_links.entity_id
            FROM thread_links
            WHERE thread_links.thread_id IN (SELECT thread_id FROM session_threads)
              AND thread_links.entity_type IN ('document', 'external', 'local')
            UNION ALL
            SELECT 2, 'same-workstream',
                   workstream_links.entity_type, workstream_links.entity_id
            FROM workstream_links
            WHERE workstream_links.workstream_id IN (
                    SELECT workstream_id FROM session_workstreams
                  )
              AND workstream_links.entity_type IN ('document', 'external', 'local')
            UNION ALL
            SELECT 2, 'same-workstream',
                   thread_links.entity_type, thread_links.entity_id
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            WHERE threads.workstream_id IN (
                    SELECT workstream_id FROM session_workstreams
                  )
              AND thread_links.entity_type IN ('document', 'external', 'local')
        )
        SELECT DISTINCT reason_rank, reason_code, entity_type, entity_id
        FROM relationships
        ORDER BY reason_rank, entity_type,
                 CAST(entity_id AS INTEGER), entity_id
        LIMIT ?
        """,
        (
            str(session_id),
            str(session_id),
            RELATED_CONTEXT_CANDIDATE_LIMIT + 1,
        ),
    ).fetchall()
    return (
        rows[:RELATED_CONTEXT_CANDIDATE_LIMIT],
        len(rows) > RELATED_CONTEXT_CANDIDATE_LIMIT,
    )


def _workspace_document_candidates(
    connection: sqlite3.Connection,
    workspace_id: Optional[int],
) -> tuple[list[sqlite3.Row], bool]:
    if workspace_id is None:
        return [], False
    rows = connection.execute(
        """
        SELECT context_documents.id AS entity_id
        FROM context_documents
        LEFT JOIN context_roots
          ON context_roots.id = context_documents.context_root_id
        WHERE context_documents.workspace_id = ?
          AND (
            context_documents.context_root_id IS NULL
            OR context_roots.enabled = 1
          )
        ORDER BY context_documents.title COLLATE NOCASE,
                 context_documents.id
        LIMIT ?
        """,
        (workspace_id, RELATED_CONTEXT_CANDIDATE_LIMIT + 1),
    ).fetchall()
    return (
        rows[:RELATED_CONTEXT_CANDIDATE_LIMIT],
        len(rows) > RELATED_CONTEXT_CANDIDATE_LIMIT,
    )


def _session_evidence_candidates(
    connection: sqlite3.Connection,
    session_id: int,
) -> tuple[list[sqlite3.Row], bool]:
    rows = connection.execute(
        """
        SELECT DISTINCT external_resource_id AS entity_id
        FROM atlassian_item_evidence
        WHERE session_id = ?
        ORDER BY external_resource_id
        LIMIT ?
        """,
        (session_id, RELATED_CONTEXT_CANDIDATE_LIMIT + 1),
    ).fetchall()
    return (
        rows[:RELATED_CONTEXT_CANDIDATE_LIMIT],
        len(rows) > RELATED_CONTEXT_CANDIDATE_LIMIT,
    )


def session_related_context(
    connection: sqlite3.Connection,
    session_id: int,
    workspace_id: Optional[int],
) -> dict:
    candidates: dict[str, dict] = {}
    unresolved_keys: set[str] = set()
    scan_truncated = False

    def include(entity_type: str, entity_id: object, reason: str) -> None:
        normalized_id = _positive_entity_id(entity_id)
        unresolved_key = "{}:{}".format(entity_type, entity_id)
        if normalized_id is None:
            unresolved_keys.add(unresolved_key)
            return
        target = _load_target(connection, entity_type, normalized_id)
        if target is None:
            unresolved_keys.add(unresolved_key)
            return
        item = candidates.setdefault(
            target["target_key"],
            {**target, "reason_codes": set()},
        )
        item["reason_codes"].add(reason)

    evidence_rows, truncated = _session_evidence_candidates(
        connection, session_id
    )
    scan_truncated = scan_truncated or truncated
    for row in evidence_rows:
        include("external", row["entity_id"], "session-reference")

    membership_rows, truncated = _membership_candidates(connection, session_id)
    scan_truncated = scan_truncated or truncated
    for row in membership_rows:
        include(row["entity_type"], row["entity_id"], row["reason_code"])

    workspace_rows, truncated = _workspace_document_candidates(
        connection, workspace_id
    )
    scan_truncated = scan_truncated or truncated
    for row in workspace_rows:
        include("document", row["entity_id"], "same-workspace")

    ordered = []
    for item in candidates.values():
        reasons = sorted(item.pop("reason_codes"), key=REASON_RANK.__getitem__)
        item["reasons"] = [
            {"code": reason, "label": REASON_LABELS[reason]}
            for reason in reasons
        ]
        item["primary_reason"] = item["reasons"][0]
        item["_sort_key"] = (
            REASON_RANK[reasons[0]],
            (item["title"] or "").casefold(),
            item["entity_type"],
            item["entity_id"],
        )
        ordered.append(item)
    ordered.sort(key=lambda item: item["_sort_key"])
    overflow_count = max(0, len(ordered) - RELATED_CONTEXT_LIMIT)
    items = ordered[:RELATED_CONTEXT_LIMIT]
    for item in items:
        item.pop("_sort_key", None)
    unavailable_count = len(unresolved_keys)
    visible_unavailable_count = sum(
        item["availability"] in {"missing", "unavailable"} for item in items
    )
    state = "empty" if not items else "ready"
    if (
        unavailable_count
        or visible_unavailable_count
        or overflow_count
        or scan_truncated
    ):
        state = "partial"
    return {
        "state": state,
        "items": items,
        "limit": RELATED_CONTEXT_LIMIT,
        "candidate_count": len(ordered),
        "overflow_count": overflow_count,
        "unavailable_count": unavailable_count,
        "visible_unavailable_count": visible_unavailable_count,
        "scan_truncated": scan_truncated,
    }
