"""Pure correction controls and assertion presentation for Workflow Focus."""

from typing import Callable, Dict, List, Mapping, Optional, Tuple

from .value_registry import visible_value_label
from .workflow_assertions import (
    WORKFLOW_ACTION_AFTER_MEANINGS,
    workflow_boundary_key,
)
from .workflow_projection import CLOSURE_REASONS


ASSERTION_RESOLUTION_LABELS = {
    "applied": "현재 적용됨",
    "unresolved": "현재 범위에서 적용 대기",
}

ASSERTION_RESOLUTION_REASON_LABELS = {
    "missing-source-episode": "출발 Episode가 현재 범위에 없습니다",
    "missing-endpoint": "한쪽 Episode가 현재 범위에 없습니다",
    "endpoint-time-order": "관측 시간 순서를 확인할 수 없습니다",
    "cycle": "순환 경로를 만들 수 있어 적용하지 않았습니다",
    "contradictory-incoming-boundary": "도착 Episode에 다른 진입 경계가 있습니다",
}

AUTHORITY_LABELS = {
    "observed": "관측",
    "deterministic-candidate": "규칙 기반 후보",
    "explicit-organization": "직접 정리",
    "user-confirmed": "사용자 확인",
}

RELATION_ACTIONS = {
    "continues": ("split-here", "merge-into"),
    "branches-from": ("same-flow", "merge-into"),
    "merged-into": ("same-flow",),
}

CLOSURE_REASON_ORDER = (
    "completed",
    "abandoned",
    "superseded",
    "merged",
    "other",
)


def workflow_relation_id(source_episode_key: str, target_episode_key: str) -> str:
    """Return one stable DOM/restoration identity for a relation boundary."""
    return "workflow-relation-{}".format(
        workflow_boundary_key("relation", source_episode_key, target_episode_key)
    )


def _authority_label(value: object) -> str:
    try:
        return AUTHORITY_LABELS[str(value)]
    except KeyError as exc:
        raise ValueError("workflow authority is not presentable") from exc


def _assertion_meaning_label(value: object) -> str:
    return visible_value_label("workflow-assertion.meaning", value)


def _closure_reason_label(value: object) -> str:
    return visible_value_label("workflow-assertion.closure-reason", value, fallback="null")


def _assertion_authority_label(value: object) -> str:
    return visible_value_label("workflow-assertion.authority", value)


def _title(
    episodes_by_key: Mapping[str, Mapping[str, object]], key: Optional[str]
) -> Optional[str]:
    if key is None:
        return None
    episode = episodes_by_key.get(key)
    if episode is None:
        return "현재 범위 밖 Episode"
    value = episode.get("display_title")
    return str(value) if isinstance(value, str) and value.strip() else "제목 없는 Session"


def _positive_identity(value: object, field: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("{} is malformed".format(field))
    return value


def _assertion_view(
    raw: Mapping[str, object],
    episodes_by_key: Mapping[str, Mapping[str, object]],
) -> dict:
    for field in (
        "boundary_key",
        "boundary_kind",
        "assertion_kind",
        "source_episode_key",
        "before_meaning",
        "after_meaning",
        "authority",
        "resolution",
        "created_at",
    ):
        if not isinstance(raw.get(field), str):
            raise ValueError("workflow assertion summary is malformed")
    assertion_id = _positive_identity(raw.get("id"), "assertion id")
    supersedes_id = _positive_identity(
        raw.get("supersedes_assertion_id"), "superseded assertion id"
    )
    restored_id = _positive_identity(
        raw.get("restored_assertion_id"), "restored assertion id"
    )
    boundary_kind = str(raw["boundary_kind"])
    source_key = str(raw["source_episode_key"])
    target_value = raw.get("target_episode_key")
    target_key = str(target_value) if target_value is not None else None
    if boundary_kind == "relation" and target_key is None:
        raise ValueError("workflow relation assertion has no target")
    if boundary_kind == "lifecycle" and target_key is not None:
        raise ValueError("workflow lifecycle assertion has a target")
    if boundary_kind not in {"relation", "lifecycle"}:
        raise ValueError("workflow assertion boundary is not presentable")
    expected_boundary = workflow_boundary_key(
        boundary_kind, source_key, target_key
    )
    if raw["boundary_key"] != expected_boundary:
        raise ValueError("workflow assertion boundary identity is inconsistent")
    resolution = str(raw["resolution"])
    if resolution not in ASSERTION_RESOLUTION_LABELS:
        raise ValueError("workflow assertion resolution is not presentable")
    resolution_reason = raw.get("resolution_reason")
    if (
        resolution_reason is not None
        and resolution_reason not in ASSERTION_RESOLUTION_REASON_LABELS
    ):
        raise ValueError("workflow assertion diagnostic is not presentable")
    before_reason = raw.get("before_closure_reason")
    after_reason = raw.get("after_closure_reason")
    return {
        "id": assertion_id,
        "boundary_key": expected_boundary,
        "boundary_kind": boundary_kind,
        "assertion_kind": str(raw["assertion_kind"]),
        "assertion_kind_label": visible_value_label(
            "workflow-assertion.kind", raw["assertion_kind"]
        ),
        "is_undo": bool(raw.get("is_undo")),
        "source_episode_key": source_key,
        "target_episode_key": target_key,
        "source_title": _title(episodes_by_key, source_key),
        "target_title": _title(episodes_by_key, target_key),
        "before_meaning": str(raw["before_meaning"]),
        "after_meaning": str(raw["after_meaning"]),
        "before_meaning_label": _assertion_meaning_label(raw["before_meaning"]),
        "after_meaning_label": _assertion_meaning_label(raw["after_meaning"]),
        "before_closure_reason": before_reason,
        "after_closure_reason": after_reason,
        "before_closure_reason_label": _closure_reason_label(before_reason),
        "after_closure_reason_label": _closure_reason_label(after_reason),
        "note_present": bool(raw.get("note")),
        "authority": str(raw["authority"]),
        "authority_label": _assertion_authority_label(raw["authority"]),
        "supersedes_assertion_id": supersedes_id,
        "restored_assertion_id": restored_id,
        "created_at": str(raw["created_at"]),
        "resolution": resolution,
        "resolution_label": ASSERTION_RESOLUTION_LABELS[resolution],
        "resolution_reason": resolution_reason,
        "resolution_reason_label": (
            ASSERTION_RESOLUTION_REASON_LABELS[resolution_reason]
            if resolution_reason is not None
            else None
        ),
        "endpoints_resolved": (
            source_key in episodes_by_key
            and (target_key is None or target_key in episodes_by_key)
        ),
    }


def _action_view(
    *,
    action: str,
    source_key: str,
    target_key: Optional[str],
    source_title: str,
    target_title: Optional[str],
    before_meaning: str,
    after_meaning: str,
    before_authority: str,
    after_authority: str,
    revision: str,
    active: Optional[Mapping[str, object]],
    assertion_id: Optional[int] = None,
    current_close_reason: Optional[str] = None,
    display_label: Optional[str] = None,
) -> dict:
    boundary_kind = "relation" if target_key is not None else "lifecycle"
    boundary_key = workflow_boundary_key(boundary_kind, source_key, target_key)
    active_id = int(active["id"]) if active is not None else None
    selected_reason = "completed"
    if action == "close" and current_close_reason in CLOSURE_REASONS:
        selected_reason = next(
            item for item in CLOSURE_REASON_ORDER if item != current_close_reason
        )
    return {
        "action_id": "workflow-correction-{}-{}".format(boundary_key, action),
        "action": action,
        "action_label": (
            "되돌리기"
            if action == "undo"
            else visible_value_label("workflow-assertion.kind", action)
        ),
        "display_label": display_label,
        "boundary_kind": boundary_kind,
        "boundary_key": boundary_key,
        "source_episode_key": source_key,
        "target_episode_key": target_key,
        "source_title": source_title,
        "target_title": target_title,
        "before_meaning": before_meaning,
        "after_meaning": after_meaning,
        "before_meaning_label": _assertion_meaning_label(before_meaning),
        "after_meaning_label": _assertion_meaning_label(after_meaning),
        "before_authority_label": _authority_label(before_authority),
        "after_authority_label": _authority_label(after_authority),
        "expected_revision": revision,
        "expected_active_assertion_id": active_id,
        "assertion_id": assertion_id,
        "supersedes_assertion_id": active_id,
        "is_close": action == "close",
        "is_undo": action == "undo",
        "current_close_reason": current_close_reason,
        "selected_close_reason_label": _closure_reason_label(selected_reason),
        "close_reason_options": [
            {
                "value": reason,
                "label": _closure_reason_label(reason),
                "selected": reason == selected_reason,
                "current": reason == current_close_reason,
            }
            for reason in CLOSURE_REASON_ORDER
        ],
    }


def _undo_action(
    assertion: Mapping[str, object],
    *,
    before_authority: str,
    after_authority: str,
    revision: str,
) -> dict:
    return _action_view(
        action="undo",
        source_key=str(assertion["source_episode_key"]),
        target_key=assertion.get("target_episode_key"),
        source_title=str(assertion["source_title"]),
        target_title=assertion.get("target_title"),
        before_meaning=str(assertion["after_meaning"]),
        after_meaning=str(assertion["before_meaning"]),
        before_authority=before_authority,
        after_authority=after_authority,
        revision=revision,
        active=assertion,
        assertion_id=int(assertion["id"]),
    )


def enrich_workflow_corrections(
    payload: Mapping[str, object],
    episodes: List[dict],
    relations: List[dict],
    episodes_by_key: Mapping[str, Mapping[str, object]],
    reason_view: Callable[[Mapping[str, object]], dict],
) -> dict:
    """Attach exact active assertions and allowed controls to a Focus view."""
    revision = payload.get("assertion_revision")
    if not isinstance(revision, str):
        raise ValueError("ready workflow projection requires an assertion revision")

    assertions = []
    relation_assertions: Dict[Tuple[str, str], dict] = {}
    lifecycle_assertions: Dict[str, dict] = {}
    for raw in payload.get("assertions") or ():
        if not isinstance(raw, Mapping):
            raise ValueError("workflow assertion summary is malformed")
        assertion = _assertion_view(raw, episodes_by_key)
        assertions.append(assertion)
        if assertion["boundary_kind"] == "relation":
            pair = (
                assertion["source_episode_key"],
                assertion["target_episode_key"],
            )
            if pair in relation_assertions:
                raise ValueError("workflow relation assertion is duplicated")
            relation_assertions[pair] = assertion
        else:
            source_key = assertion["source_episode_key"]
            if source_key in lifecycle_assertions:
                raise ValueError("workflow lifecycle assertion is duplicated")
            lifecycle_assertions[source_key] = assertion

    base_relations = {}
    for raw in payload.get("base_relations") or ():
        if not isinstance(raw, Mapping):
            raise ValueError("base workflow relation is malformed")
        pair = (
            str(raw.get("source_episode_key") or ""),
            str(raw.get("target_episode_key") or ""),
        )
        if pair[0] not in episodes_by_key or pair[1] not in episodes_by_key:
            raise ValueError("base workflow relation references an absent Episode")
        base_relations[pair] = raw

    base_lifecycle = {}
    for raw in payload.get("base_episode_lifecycle") or ():
        if not isinstance(raw, Mapping) or raw.get("episode_key") not in episodes_by_key:
            raise ValueError("base workflow lifecycle is malformed")
        base_lifecycle[str(raw["episode_key"])] = raw

    effective_pairs = set()
    outgoing = set()
    enriched_relations = []
    for relation in relations:
        source_key = str(relation["source_episode_key"])
        target_key = str(relation["target_episode_key"])
        pair = (source_key, target_key)
        effective_pairs.add(pair)
        outgoing.add(source_key)
        active = relation_assertions.get(pair)
        base = base_relations.get(pair)
        authority = str(relation["authority"])
        actions = [
            _action_view(
                action=action,
                source_key=source_key,
                target_key=target_key,
                source_title=str(relation["source_title"]),
                target_title=str(relation["target_title"]),
                before_meaning="relation:{}".format(relation["kind"]),
                after_meaning=WORKFLOW_ACTION_AFTER_MEANINGS[action],
                before_authority=authority,
                after_authority="user-confirmed",
                revision=revision,
                active=active,
            )
            for action in RELATION_ACTIONS[str(relation["kind"])]
        ]
        if active is not None and active["endpoints_resolved"]:
            restored_authority = (
                str(base.get("authority") or "deterministic-candidate")
                if base is not None and active["supersedes_assertion_id"] is None
                else "user-confirmed"
            )
            actions.append(
                _undo_action(
                    active,
                    before_authority=authority,
                    after_authority=restored_authority,
                    revision=revision,
                )
            )
        enriched_relations.append(
            {
                **relation,
                "boundary_key": workflow_boundary_key(
                    "relation", source_key, target_key
                ),
                "user_confirmed": authority == "user-confirmed",
                "active_assertion": active,
                "base_relation": dict(base) if base is not None else None,
                "base_reasons": [
                    reason_view(reason)
                    for reason in (base.get("reasons") or ())
                    if isinstance(reason, Mapping)
                ] if base is not None else [],
                "correction_actions": actions,
            }
        )

    detached: Dict[str, List[dict]] = {key: [] for key in episodes_by_key}
    for pair, assertion in relation_assertions.items():
        if pair in effective_pairs:
            continue
        owner = pair[0] if pair[0] in episodes_by_key else pair[1]
        if owner not in detached:
            continue
        item = dict(assertion)
        item["undo_action"] = None
        if assertion["endpoints_resolved"]:
            base = base_relations.get(pair)
            restored_authority = (
                str(base.get("authority") or "deterministic-candidate")
                if base is not None and assertion["supersedes_assertion_id"] is None
                else "user-confirmed"
            )
            item["undo_action"] = _undo_action(
                assertion,
                before_authority="user-confirmed",
                after_authority=restored_authority,
                revision=revision,
            )
        detached[owner].append(item)

    enriched_episodes = []
    for episode in episodes:
        key = str(episode["episode_key"])
        authority = str(episode["authority"])
        lifecycle = lifecycle_assertions.get(key)
        base = base_lifecycle.get(key, episode)
        state = str(episode.get("lifecycle_state") or "unknown")
        is_tip = key not in outgoing
        actions = []
        if is_tip and state in {"open", "unknown"}:
            actions.append(
                _action_view(
                    action="close",
                    source_key=key,
                    target_key=None,
                    source_title=str(episode["title"]),
                    target_title=None,
                    before_meaning="lifecycle:{}".format(state),
                    after_meaning="lifecycle:closed",
                    before_authority=authority,
                    after_authority="user-confirmed",
                    revision=revision,
                    active=lifecycle,
                )
            )
        elif (
            is_tip
            and state == "closed"
            and lifecycle is not None
            and lifecycle["after_meaning"] == "lifecycle:closed"
        ):
            actions.append(
                _action_view(
                    action="close",
                    source_key=key,
                    target_key=None,
                    source_title=str(episode["title"]),
                    target_title=None,
                    before_meaning="lifecycle:closed",
                    after_meaning="lifecycle:closed",
                    before_authority=authority,
                    after_authority="user-confirmed",
                    revision=revision,
                    active=lifecycle,
                    current_close_reason=episode.get("closure_reason"),
                    display_label="종료 사유 고치기",
                )
            )
        if lifecycle is not None and lifecycle["after_meaning"] == "lifecycle:closed":
            actions.append(
                _action_view(
                    action="reopen",
                    source_key=key,
                    target_key=None,
                    source_title=str(episode["title"]),
                    target_title=None,
                    before_meaning="lifecycle:closed",
                    after_meaning="lifecycle:open",
                    before_authority=authority,
                    after_authority="user-confirmed",
                    revision=revision,
                    active=lifecycle,
                )
            )
        if lifecycle is not None and lifecycle["endpoints_resolved"]:
            restored_authority = (
                str(base.get("authority") or "observed")
                if lifecycle["supersedes_assertion_id"] is None
                else "user-confirmed"
            )
            actions.append(
                _undo_action(
                    lifecycle,
                    before_authority=authority,
                    after_authority=restored_authority,
                    revision=revision,
                )
            )
        enriched_episodes.append(
            {
                **episode,
                "user_confirmed": authority == "user-confirmed",
                "active_lifecycle_assertion": lifecycle,
                "detached_relation_assertions": detached[key],
                "correction_actions": actions,
                "closure_reason_label": _closure_reason_label(
                    episode.get("closure_reason")
                ),
            }
        )

    adjacent: Dict[str, List[dict]] = {key: [] for key in episodes_by_key}
    for relation in enriched_relations:
        adjacent[str(relation["source_episode_key"])].append(relation)
        adjacent[str(relation["target_episode_key"])].append(relation)
    enriched_episodes = [
        {**episode, "relations": adjacent[str(episode["episode_key"])]}
        for episode in enriched_episodes
    ]

    return {
        "revision": revision,
        "assertions": assertions,
        "episodes": enriched_episodes,
        "relations": enriched_relations,
    }
