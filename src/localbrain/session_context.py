import sqlite3
from typing import Optional
from urllib.parse import urlsplit

from .ingest.common import trim_url_token
from .session_references import session_reference_projection


RELATED_CONTEXT_LIMIT = 100
RELATED_CONTEXT_CANDIDATE_LIMIT = 100
EVIDENCE_LABELS = {
    ("resource_read", "success"): "MCP 조회",
    ("resource_read", "failure"): "MCP 조회 실패",
    ("user_mention", None): "사용자 메시지에서 언급",
    ("assistant_mention", None): "Agent 응답에서 언급",
    ("tool_result", None): "도구 결과에서 확인",
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
    try:
        safe_value = trim_url_token(value.strip())
        parsed = urlsplit(safe_value)
        parsed.port
    except (TypeError, ValueError):
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    return safe_value


def _safe_url_detail(value: Optional[str]) -> Optional[str]:
    safe_value = _safe_external_href(value)
    if safe_value is None:
        return None
    parsed = urlsplit(safe_value)
    host = parsed.hostname or ""
    try:
        if parsed.port is not None:
            host = "{}:{}".format(host, parsed.port)
    except ValueError:
        return None
    return (host + (parsed.path or "/"))[:500]


def _safe_url_dedupe_key(value: Optional[str]) -> Optional[str]:
    safe_value = _safe_external_href(value)
    if safe_value is None:
        return None
    parsed = urlsplit(safe_value)
    host = (parsed.hostname or "").lower().rstrip(".")
    try:
        if parsed.port is not None:
            host = "{}:{}".format(host, parsed.port)
    except ValueError:
        return None
    return "destination:{}://{}{}".format(
        parsed.scheme.lower(), host, parsed.path or "/"
    )


def _local_resource_label(resource_type: Optional[str]) -> str:
    return {
        "repository": "로컬 저장소",
        "directory": "로컬 폴더",
        "file": "로컬 파일",
        "path": "로컬 경로",
    }.get(resource_type or "", "로컬 경로")


def _external_resource_label(resource_type: Optional[str]) -> str:
    return {
        "document": "문서",
        "jira": "Jira",
        "wiki": "Wiki",
        "slack": "Slack",
        "git": "Git",
        "url": "URL",
    }.get(resource_type or "", "외부 자료")


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
                   context_roots.label AS root_label
            FROM context_documents
            JOIN sources ON sources.id = context_documents.source_id
            LEFT JOIN context_roots
              ON context_roots.id = context_documents.context_root_id
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
        return {
            "target_key": "document:{}".format(entity_id),
            "dedupe_key": "document:{}".format(entity_id),
            "entity_type": "document",
            "entity_id": entity_id,
            "identity": row["title"],
            "detail": row["relative_path"],
            "kind_label": "Markdown",
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
            "dedupe_key": "local:{}".format(entity_id),
            "entity_type": "local",
            "entity_id": entity_id,
            "identity": row["title"],
            "detail": row["path"],
            "kind_label": resource_label,
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
               atlassian_items.service, atlassian_items.attention,
               atlassian_sites.normalized_domain
        FROM external_resources
        LEFT JOIN atlassian_items
          ON atlassian_items.external_resource_id = external_resources.id
        LEFT JOIN atlassian_sites
          ON atlassian_sites.id = atlassian_items.site_id
        WHERE external_resources.id = ?
        """,
        (entity_id,),
    ).fetchone()
    if row is None:
        return None
    if row["service"]:
        service_label = "Jira" if row["service"] == "jira" else "Confluence"
        archived = row["attention"] == "archived"
        return {
            "target_key": "atlassian:{}".format(entity_id),
            "dedupe_key": "atlassian:{}".format(entity_id),
            "entity_type": "atlassian",
            "entity_id": entity_id,
            "identity": row["title"],
            "detail": row["normalized_domain"],
            "kind_label": service_label,
            "availability": "archived" if archived else "available",
            "availability_label": "보관됨" if archived else None,
            "href": "/atlassian/items/{}".format(entity_id),
            "external": False,
        }
    resource_label = _external_resource_label(row["resource_type"])
    safe_href = _safe_external_href(row["url"])
    return {
        "target_key": "external:{}".format(entity_id),
        "dedupe_key": _safe_url_dedupe_key(safe_href)
        or "external:{}".format(entity_id),
        "entity_type": "external",
        "entity_id": entity_id,
        "identity": row["title"],
        "detail": _safe_url_detail(row["url"]),
        "kind_label": resource_label,
        "availability": "available" if safe_href else "unavailable",
        "availability_label": None if safe_href else "열 수 없음",
        "href": safe_href,
        "external": bool(safe_href),
    }


def _membership_candidates(
    connection: sqlite3.Connection,
    session_id: int,
) -> tuple[list[sqlite3.Row], bool, int]:
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
            SELECT 0 AS reason_rank, 'thread' AS reason_code,
                   threads.title AS scope_title,
                   thread_links.entity_type, thread_links.entity_id
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            WHERE thread_links.thread_id IN (
                    SELECT thread_id FROM session_threads
                  )
              AND thread_links.entity_type IN ('document', 'external', 'local')
            UNION ALL
            SELECT 1, 'workstream', workstreams.name,
                   workstream_links.entity_type, workstream_links.entity_id
            FROM workstream_links
            JOIN workstreams
              ON workstreams.id = workstream_links.workstream_id
            WHERE workstream_links.workstream_id IN (
                    SELECT workstream_id FROM session_workstreams
                  )
              AND workstream_links.entity_type IN (
                    'document', 'external', 'local'
                  )
            UNION ALL
            SELECT 1, 'workstream', workstreams.name,
                   thread_links.entity_type, thread_links.entity_id
            FROM thread_links
            JOIN threads ON threads.id = thread_links.thread_id
            JOIN workstreams ON workstreams.id = threads.workstream_id
            WHERE threads.workstream_id IN (
                    SELECT workstream_id FROM session_workstreams
                  )
              AND thread_links.entity_type IN ('document', 'external', 'local')
        ),
        target_keys AS (
            SELECT entity_type, entity_id, MIN(reason_rank) AS primary_rank,
                   COUNT(*) OVER () AS target_total
            FROM relationships
            GROUP BY entity_type, entity_id
            ORDER BY primary_rank, entity_type,
                     CAST(entity_id AS INTEGER), entity_id
            LIMIT ?
        ),
        ranked_relationships AS (
            SELECT relationships.*,
                   target_keys.primary_rank,
                   target_keys.target_total,
                   ROW_NUMBER() OVER (
                       PARTITION BY relationships.entity_type,
                                    relationships.entity_id
                       ORDER BY relationships.reason_rank,
                                relationships.scope_title COLLATE NOCASE,
                                relationships.reason_code
                   ) AS reason_position
            FROM relationships
            JOIN target_keys
              ON target_keys.entity_type = relationships.entity_type
             AND target_keys.entity_id = relationships.entity_id
        )
        SELECT reason_rank, reason_code, scope_title, entity_type, entity_id,
               primary_rank, target_total
        FROM ranked_relationships
        WHERE reason_position <= 3
        ORDER BY primary_rank, entity_type,
                 CAST(entity_id AS INTEGER), entity_id,
                 reason_rank, scope_title COLLATE NOCASE
        """,
        (
            str(session_id),
            str(session_id),
            RELATED_CONTEXT_CANDIDATE_LIMIT + 1,
        ),
    ).fetchall()
    if not rows:
        return [], False, 0
    observed_total = int(rows[0]["target_total"])
    accepted_keys = []
    for row in rows:
        key = (row["entity_type"], row["entity_id"])
        if key not in accepted_keys:
            accepted_keys.append(key)
    retained_keys = set(accepted_keys[:RELATED_CONTEXT_CANDIDATE_LIMIT])
    return (
        [
            row
            for row in rows
            if (row["entity_type"], row["entity_id"]) in retained_keys
        ],
        observed_total > RELATED_CONTEXT_CANDIDATE_LIMIT,
        observed_total,
    )


def _organization_projection(
    connection: sqlite3.Connection,
    session_id: int,
) -> dict:
    rows, truncated, observed_total = _membership_candidates(
        connection, session_id
    )
    items: dict[str, dict] = {}
    unavailable_keys = set()
    for row in rows:
        unresolved_key = "{}:{}".format(row["entity_type"], row["entity_id"])
        target = _load_target(
            connection, row["entity_type"], row["entity_id"]
        )
        if target is None:
            unavailable_keys.add(unresolved_key)
            continue
        item = items.setdefault(
            target["dedupe_key"],
            {
                **target,
                "organization": [],
                "primary_rank": int(row["primary_rank"]),
            },
        )
        organization = {
            "kind": row["reason_code"],
            "label": "{} · {}".format(
                "Thread" if row["reason_code"] == "thread" else "Workstream",
                row["scope_title"],
            ),
        }
        if organization not in item["organization"]:
            item["organization"].append(organization)

    ordered = sorted(
        items.values(),
        key=lambda item: (
            item["primary_rank"],
            (item["identity"] or "").casefold(),
            item["target_key"],
        ),
    )
    visible_unavailable_count = sum(
        item["availability"] in {"missing", "unavailable"}
        for item in ordered
    )
    return {
        "items": ordered,
        "observed_total": observed_total,
        "unavailable_count": len(unavailable_keys),
        "visible_unavailable_count": visible_unavailable_count,
        "truncated": truncated,
    }


def _direct_item(
    connection: sqlite3.Connection,
    raw_item: dict,
) -> dict:
    target_kind = raw_item["target_kind"]
    metadata = None
    if target_kind == "context_document":
        metadata = _load_target(
            connection, "document", raw_item["context_document_id"]
        )
    elif target_kind == "atlassian_item":
        metadata = _load_target(
            connection, "external", raw_item["external_resource_id"]
        )

    if metadata is None and target_kind == "url":
        href = _safe_external_href(raw_item["destination"])
        safe_identity = _safe_url_detail(href)
        metadata = {
            "target_key": raw_item["target_key"],
            "dedupe_key": _safe_url_dedupe_key(href)
            or raw_item["target_key"],
            "entity_type": "external",
            "entity_id": None,
            "identity": safe_identity or raw_item["identity"],
            "detail": safe_identity,
            "kind_label": "URL",
            "availability": "available" if href else "unavailable",
            "availability_label": None if href else "열 수 없음",
            "href": href,
            "external": bool(href),
        }
    elif metadata is None:
        metadata = {
            "target_key": raw_item["target_key"],
            "dedupe_key": raw_item["target_key"],
            "entity_type": target_kind,
            "entity_id": (
                raw_item["context_document_id"]
                or raw_item["external_resource_id"]
            ),
            "identity": raw_item["identity"],
            "detail": None,
            "kind_label": (
                "Markdown" if target_kind == "context_document" else "Atlassian"
            ),
            "availability": "unavailable",
            "availability_label": "열 수 없음",
            "href": None,
            "external": False,
        }

    evidence = []
    for summary in raw_item["evidence"]:
        label = EVIDENCE_LABELS.get(
            (summary["kind"], summary["outcome"])
        )
        if label:
            evidence.append({**summary, "label": label})
    identity = (
        metadata["identity"] if target_kind == "url" else raw_item["identity"]
    )
    detail = metadata["detail"]
    if detail and detail.casefold() == identity.casefold():
        detail = None
    return {
        **metadata,
        "target_key": raw_item["target_key"],
        "identity": identity,
        "detail": detail,
        "evidence": evidence,
        "observed_at": raw_item.get("observed_at"),
        "organization": [],
    }


def _group(
    *,
    key: str,
    label: str,
    items: list[dict],
    total: int,
    partial: bool = False,
    stale: bool = False,
    notices: Optional[list[str]] = None,
) -> dict:
    sections_by_label = {}
    for item in items:
        section_label = str(item.get("kind_label") or "기타").strip().upper()
        sections_by_label.setdefault(section_label, []).append(item)
    sections = [
        {"label": section_label, "rows": sections_by_label[section_label]}
        for section_label in sorted(sections_by_label, key=str.casefold)
    ]
    ordered_items = [
        item for section in sections for item in section["rows"]
    ]
    initial_items = ordered_items[:RELATED_CONTEXT_LIMIT]
    additional_items = ordered_items[RELATED_CONTEXT_LIMIT:]

    def section_items(section_slice: list[dict]) -> list[dict]:
        by_label = {}
        for item in section_slice:
            section_label = str(item.get("kind_label") or "기타").strip().upper()
            by_label.setdefault(section_label, []).append(item)
        return [
            {"label": section_label, "rows": by_label[section_label]}
            for section_label in sorted(by_label, key=str.casefold)
        ]

    initial_sections = section_items(initial_items)
    additional_sections = section_items(additional_items)
    if (
        initial_sections
        and additional_sections
        and initial_sections[-1]["label"] == additional_sections[0]["label"]
    ):
        additional_sections[0]["continuation"] = True

    return {
        "key": key,
        "label": label,
        "total": total,
        "items": ordered_items,
        "initial_items": initial_items,
        "additional_items": additional_items,
        "initial_sections": initial_sections,
        "additional_sections": additional_sections,
        "overflow_count": len(additional_items),
        "partial": partial,
        "stale": stale,
        "notices": notices or [],
    }


def session_related_context_error() -> dict:
    return {
        "state": "error",
        "groups": [],
        "item_count": 0,
    }


def session_related_context(
    connection: sqlite3.Connection,
    session_id: int,
    workspace_id: Optional[int] = None,
) -> dict:
    # workspace_id remains in the call contract for route compatibility. It is
    # intentionally not a candidate source for related materials.
    _ = workspace_id
    direct_projection = session_reference_projection(connection, session_id)
    organization_projection = _organization_projection(connection, session_id)

    direct_items = [
        _direct_item(connection, item) for item in direct_projection["items"]
    ]
    direct_by_key = {item["dedupe_key"]: item for item in direct_items}
    organization_items = []
    organization_overlap_count = 0
    for item in organization_projection["items"]:
        direct_item = direct_by_key.get(item["dedupe_key"])
        if direct_item is not None:
            direct_item["organization"] = item["organization"]
            organization_overlap_count += 1
            continue
        organization_items.append(item)

    direct_notices = []
    if direct_projection["partial"]:
        direct_notices.append(
            "총 {}개 중 {}개까지 확인했습니다.".format(
                direct_projection["observed_total"],
                direct_projection["retained_total"],
            )
        )
    if direct_projection["stale"]:
        direct_notices.append(
            "참조 동기화가 완료되지 않아 이전 결과일 수 있습니다."
        )

    organization_notices = []
    if organization_projection["truncated"]:
        organization_notices.append(
            "총 {}개 연결 중 {}개까지 확인했습니다.".format(
                organization_projection["observed_total"],
                RELATED_CONTEXT_CANDIDATE_LIMIT,
            )
        )
    if organization_projection["unavailable_count"]:
        organization_notices.append(
            "대상을 찾을 수 없는 연결 {}개는 표시하지 않았습니다.".format(
                organization_projection["unavailable_count"]
            )
        )

    direct_group = _group(
        key="direct",
        label="이 세션의 참조",
        items=direct_items,
        total=direct_projection["observed_total"],
        partial=direct_projection["partial"],
        stale=direct_projection["stale"],
        notices=direct_notices,
    )
    organization_group = _group(
        key="organization",
        label="연결된 작업",
        items=organization_items,
        total=max(
            len(organization_items),
            organization_projection["observed_total"]
            - organization_overlap_count,
        ),
        partial=(
            organization_projection["truncated"]
            or bool(organization_projection["unavailable_count"])
            or bool(organization_projection["visible_unavailable_count"])
        ),
        notices=organization_notices,
    )
    groups = [direct_group, organization_group]
    item_count = len(direct_items) + len(organization_items)
    if item_count == 0 and not any(group["notices"] for group in groups):
        state = "empty"
    elif any(group["partial"] or group["stale"] for group in groups):
        state = "partial"
    else:
        state = "ready"
    return {
        "state": state,
        "groups": groups,
        "item_count": item_count,
    }
