"""Pure presentation adapter for the Session Workflow Focus route."""

from typing import Dict, Iterable, List, Mapping, Optional

from .value_registry import visible_value_label
from .workflow_correction_view import (
    enrich_workflow_corrections,
    workflow_relation_id,
)
from .workflow_focus import WorkflowFocusProjection


WORKFLOW_ROUTE_VERSION = "localbrain.workflow-map.v2"

RELATION_LABELS = {
    "continues": "continues",
    "branches-from": "branches from",
    "merged-into": "merged into",
}

AUTHORITY_LABELS = {
    "observed": "관측",
    "deterministic-candidate": "규칙 기반 후보",
    "explicit-organization": "직접 정리",
    "user-confirmed": "사용자 확인",
}

REASON_LABELS = {
    "direct-source-relation": "원본의 직접 관계",
    "shared-reference": "같은 자료 참조",
    "thread-membership": "같은 Thread",
    "workstream-membership": "같은 Workstream",
    "user-assertion": "사용자 확인",
    "same-workspace": "같은 workspace",
    "same-git-root": "같은 Git root",
    "same-git-branch": "같은 Git branch",
    "lexical-overlap": "문구 겹침",
    "temporal-proximity": "시간 인접",
}

EVIDENCE_FAMILY_LABELS = {
    "atlassian": "Atlassian",
    "external": "외부 링크",
    "git": "Git",
    "local-context": "Local Context",
    "local-resource": "로컬 자료",
    "organization": "연결된 작업",
    "session": "Subsessions",
    "slack": "Slack",
    "unknown": "분류되지 않은 자료",
}

EVIDENCE_KIND_LABELS = {
    "organization-link": "정리 연결",
    "structure-reference": "구조 참조",
    "subsession": "Subsession",
    "thread-membership": "Thread 연결",
    "workstream-membership": "Workstream 연결",
}

AVAILABILITY_LABELS = {
    "available": "사용 가능",
    "stale": "마지막 관측",
    "unavailable": "열 수 없음",
    "missing": "경로 없음",
    "archived": "보관됨",
    "unknown": "상태 미확인",
}


def _label(values: Mapping[str, str], value: object) -> str:
    normalized = str(value or "unknown")
    return values.get(normalized, normalized.replace("-", " "))


def _episode_title(episode: Mapping[str, object]) -> str:
    title = episode.get("display_title")
    return str(title) if isinstance(title, str) and title.strip() else "제목 없는 Session"


def _reason_view(reason: Mapping[str, object]) -> dict:
    kind = str(reason.get("kind") or "unknown")
    return {
        "kind": kind,
        "label": _label(REASON_LABELS, kind),
        "identity": str(reason.get("identity") or "근거 식별자 없음"),
        "observed_at": reason.get("observed_at"),
    }


def _evidence_group_view(group: Mapping[str, object]) -> dict:
    family = str(group.get("source_family") or "unknown")
    items = []
    for item in group.get("items") or ():
        if not isinstance(item, Mapping):
            continue
        availability = str(item.get("availability") or "unknown")
        authority = str(item.get("authority") or "observed")
        kind = str(item.get("evidence_kind") or "unknown")
        items.append(
            {
                **dict(item),
                "source_family": family,
                "source_label": EVIDENCE_FAMILY_LABELS.get(
                    family, family.replace("-", " ").title()
                ),
                "kind_label": _label(EVIDENCE_KIND_LABELS, kind),
                "availability_label": _label(
                    AVAILABILITY_LABELS, availability
                ),
                "authority_label": _label(AUTHORITY_LABELS, authority),
                "admission_labels": [
                    _label(REASON_LABELS, reason)
                    for reason in item.get("admission_reasons") or ()
                ],
            }
        )
    retained_total = max(int(group.get("retained_total") or 0), len(items))
    observed_total = max(
        int(group.get("observed_total") or 0), retained_total
    )
    return {
        "source_family": family,
        "label": EVIDENCE_FAMILY_LABELS.get(
            family, family.replace("-", " ").title()
        ),
        "items": items,
        "retained_total": retained_total,
        "observed_total": observed_total,
        "partial": bool(group.get("partial")),
        "stale": bool(group.get("stale")),
    }


def _relation_views(
    relations: Iterable[Mapping[str, object]],
    episodes_by_key: Mapping[str, Mapping[str, object]],
) -> List[dict]:
    values = []
    for relation in relations:
        source_key = str(relation.get("source_episode_key") or "")
        target_key = str(relation.get("target_episode_key") or "")
        source = episodes_by_key.get(source_key)
        target = episodes_by_key.get(target_key)
        if source is None or target is None:
            raise ValueError("workflow relation references an absent Episode")
        kind = str(relation.get("kind") or "")
        if kind not in RELATION_LABELS:
            raise ValueError("workflow relation kind is not presentable")
        authority = str(relation.get("authority") or "")
        values.append(
            {
                **dict(relation),
                "relation_id": workflow_relation_id(source_key, target_key),
                "label": RELATION_LABELS[kind],
                "authority_label": _label(AUTHORITY_LABELS, authority),
                "source_title": _episode_title(source),
                "target_title": _episode_title(target),
                "reasons": [
                    _reason_view(reason)
                    for reason in relation.get("reasons") or ()
                    if isinstance(reason, Mapping)
                ],
            }
        )
    return values


def workflow_map_view(
    projection: WorkflowFocusProjection,
    requested_session_id: int,
) -> dict:
    """Return a bounded template/client view from one FEAT-0086 payload."""
    if isinstance(requested_session_id, bool) or requested_session_id <= 0:
        raise ValueError("requested_session_id must be positive")
    payload = projection.as_dict()
    status = str(payload.get("status") or "")
    if status not in {"ready", "missing", "ineligible"}:
        raise ValueError("unsupported workflow route state")
    if status != "ready":
        return workflow_map_state_view(status, requested_session_id)

    raw_episodes = payload.get("episodes") or []
    selected_key = payload.get("selected_episode_key")
    if not raw_episodes or not isinstance(selected_key, str):
        raise ValueError("ready workflow projection requires a selected Episode")

    episodes_by_key: Dict[str, Mapping[str, object]] = {}
    for item in raw_episodes:
        if not isinstance(item, Mapping) or not isinstance(
            item.get("episode"), Mapping
        ):
            raise ValueError("workflow Episode view is malformed")
        episode = item["episode"]
        key = str(episode.get("episode_key") or "")
        if not key or key in episodes_by_key:
            raise ValueError("workflow Episode key is absent or duplicated")
        episodes_by_key[key] = episode
    if selected_key not in episodes_by_key:
        raise ValueError("selected workflow Episode is absent")

    relations = _relation_views(payload.get("relations") or (), episodes_by_key)
    adjacent: Dict[str, List[dict]] = {key: [] for key in episodes_by_key}
    for relation in relations:
        adjacent[relation["source_episode_key"]].append(relation)
        adjacent[relation["target_episode_key"]].append(relation)

    episodes = []
    evidence_partial = False
    for item in raw_episodes:
        episode = dict(item["episode"])
        key = str(episode["episode_key"])
        groups = [
            _evidence_group_view(group)
            for group in item.get("evidence_groups") or ()
            if isinstance(group, Mapping)
        ]
        partial = bool(item.get("evidence_partial")) or any(
            group["partial"] or group["stale"] for group in groups
        )
        evidence_partial = evidence_partial or partial
        episodes.append(
            {
                **episode,
                "title": _episode_title(episode),
                "authority_label": _label(
                    AUTHORITY_LABELS, episode.get("authority")
                ),
                "activity_label": _label({}, episode.get("activity_state")),
                "lifecycle_label": visible_value_label(
                    "workflow-assertion.meaning",
                    "lifecycle:{}".format(
                        episode.get("lifecycle_state") or "unknown"
                    ),
                ),
                "evidence_groups": groups,
                "evidence_retained_total": int(
                    item.get("evidence_retained_total") or 0
                ),
                "evidence_observed_total": int(
                    item.get("evidence_observed_total") or 0
                ),
                "evidence_partial": partial,
                "relations": adjacent[key],
                "selected": key == selected_key,
                "workflow_destination": "/sessions/{}/workflow".format(
                    int(episode["session_id"])
                ),
            }
        )

    correction = enrich_workflow_corrections(
        payload, episodes, relations, episodes_by_key, _reason_view
    )
    episodes = correction["episodes"]
    relations = correction["relations"]
    selected_episode = next(item for item in episodes if item["selected"])
    episode_partial = int(payload.get("episode_observed_total") or 0) > int(
        payload.get("episode_retained_total") or 0
    )
    branch_partial = int(payload.get("branch_root_observed_total") or 0) > int(
        payload.get("branch_root_retained_total") or 0
    )
    candidate_partial = int(payload.get("candidate_observed_total") or 0) > int(
        payload.get("candidate_retained_total") or 0
    )
    client_projection = {
        "status": "ready",
        "selected_episode_key": selected_key,
        "assertion_revision": correction["revision"],
        "episodes": [
            {
                "episode_key": item["episode_key"],
                "session_id": item["session_id"],
                "workflow_destination": item["workflow_destination"],
                "observed_start_at": item["observed_start_at"],
                "last_observed_at": item["last_observed_at"],
                "title": item["title"],
                "lifecycle_state": item["lifecycle_state"],
                "authority": item["authority"],
                "active_assertion_id": (
                    item["active_lifecycle_assertion"]["id"]
                    if item["active_lifecycle_assertion"] is not None
                    else None
                ),
            }
            for item in episodes
        ],
        "relations": [
            {
                "relation_id": item["relation_id"],
                "boundary_key": item["boundary_key"],
                "source_episode_key": item["source_episode_key"],
                "target_episode_key": item["target_episode_key"],
                "kind": item["kind"],
                "label": item["label"],
                "authority": item["authority"],
                "authority_label": item["authority_label"],
                "active_assertion_id": (
                    item["active_assertion"]["id"]
                    if item["active_assertion"] is not None
                    else None
                ),
            }
            for item in relations
        ],
        "projection_version": payload.get("projection_version"),
        "route_version": WORKFLOW_ROUTE_VERSION,
    }
    return {
        "status": "ready",
        "requested_session_id": requested_session_id,
        "correction_destination": "/sessions/{}/workflow/corrections".format(
            requested_session_id
        ),
        "assertion_revision": correction["revision"],
        "session_destination": str(selected_episode["destination"]),
        "selected_episode": selected_episode,
        "episodes": episodes,
        "relations": relations,
        "assertions": correction["assertions"],
        "assertion_count": len(correction["assertions"]),
        "diagnostics": payload.get("diagnostics") or [],
        "unconnected": not relations,
        "partial": (
            episode_partial
            or branch_partial
            or candidate_partial
            or evidence_partial
        ),
        "candidate_observed_total": int(
            payload.get("candidate_observed_total") or 0
        ),
        "candidate_retained_total": int(
            payload.get("candidate_retained_total") or 0
        ),
        "episode_observed_total": int(
            payload.get("episode_observed_total") or len(episodes)
        ),
        "episode_retained_total": int(
            payload.get("episode_retained_total") or len(episodes)
        ),
        "branch_root_observed_total": int(
            payload.get("branch_root_observed_total") or 0
        ),
        "branch_root_retained_total": int(
            payload.get("branch_root_retained_total") or 0
        ),
        "client_projection": client_projection,
    }


def workflow_map_state_view(status: str, requested_session_id: int) -> dict:
    states = {
        "missing": {
            "title": "Session을 찾을 수 없습니다",
            "message": "이 주소에 해당하는 작업 Session이 현재 로컬 인덱스에 없습니다.",
            "destination": "/sessions",
            "destination_label": "Sessions 목록",
        },
        "ineligible": {
            "title": "작업 흐름을 만들 수 없는 Session입니다",
            "message": "기본 작업 Session의 관측된 활동만 작업 흐름 Episode가 됩니다.",
            "destination": "/sessions/{}".format(requested_session_id),
            "destination_label": "Session 상세",
        },
        "unexpected-error": {
            "title": "작업 흐름을 표시할 수 없습니다",
            "message": "Session 원문은 그대로이며, 흐름 투영만 불러오지 못했습니다.",
            "destination": "/sessions/{}".format(requested_session_id),
            "destination_label": "Session 상세로 돌아가기",
        },
    }
    if status not in states:
        raise ValueError("unsupported workflow state")
    return {
        "status": status,
        "requested_session_id": requested_session_id,
        **states[status],
    }
