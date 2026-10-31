"""Read projection of resources directly observed in a Session.

Shared resource identity and Local Context availability enrich retained evidence.
Optional product registrations and organization membership are not read here.
"""
import sqlite3
from typing import Optional
from urllib.parse import urlsplit

from localbrain.references.urls import trim_url_token
from localbrain.sessions.references import session_reference_projection


RELATED_CONTEXT_LIMIT = 100
EVIDENCE_LABELS = {
    ("resource_read", "success"): "MCP 조회",
    ("resource_read", "failure"): "MCP 조회 실패",
    ("user_mention", None): "사용자 메시지에서 언급",
    ("assistant_mention", None): "Agent 응답에서 언급",
    ("tool_result", None): "도구 결과에서 확인",
}


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


def _direct_item(raw_item: dict) -> dict:
    is_url = raw_item["target_kind"] == "url"
    href = _safe_external_href(raw_item["destination"]) if is_url else raw_item["destination"]
    detail = _safe_url_detail(href) if is_url else raw_item["relative_path"] or raw_item["locator"]
    identity = raw_item["identity"]
    if is_url and not raw_item["product"]:
        identity = _safe_url_detail(href) or identity
    metadata = {
        "resource_id": raw_item["resource_id"],
        "entity_type": "external" if is_url else "document",
        "entity_id": raw_item["context_document_id"],
        "kind_label": {"jira": "Jira", "confluence": "Confluence"}.get(raw_item["product"], "URL") if is_url else "Markdown",
        "availability": "available" if href else "unavailable",
        "availability_label": None if href else "열 수 없음",
        "href": href,
        "external": bool(is_url and href),
    }

    evidence = []
    for summary in raw_item["evidence"]:
        label = EVIDENCE_LABELS.get(
            (summary["kind"], summary["outcome"])
        )
        if label:
            evidence.append({**summary, "label": label})
    if detail and detail.casefold() == identity.casefold():
        detail = None
    return {
        **metadata,
        "target_key": raw_item["target_key"],
        "identity": identity,
        "detail": detail,
        "evidence": evidence,
        "observed_at": raw_item.get("observed_at"),
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
) -> dict:
    direct_projection = session_reference_projection(connection, session_id)
    direct_items = [
        _direct_item(item) for item in direct_projection["items"]
    ]

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

    direct_group = _group(
        key="direct",
        label="이 세션의 참조",
        items=direct_items,
        total=direct_projection["observed_total"],
        partial=direct_projection["partial"],
        stale=direct_projection["stale"],
        notices=direct_notices,
    )
    groups = [direct_group]
    item_count = len(direct_items)
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
