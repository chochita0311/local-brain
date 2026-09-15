"""Pure contracts for Session-backed workflow projections.

This module deliberately owns no persistence or I/O.  It defines the stable
value shapes that deterministic producers and product consumers share.
"""

import hashlib
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Tuple

from .activity import parse_timestamp


WORKFLOW_PROJECTION_VERSION = "localbrain.workflow-projection.v1"

ACTIVITY_STATES = frozenset({"active", "quiet", "unknown"})
LIFECYCLE_STATES = frozenset({"open", "closed", "unknown"})
CLOSURE_REASONS = frozenset(
    {"completed", "abandoned", "superseded", "merged", "other"}
)
AUTHORITY_STATES = frozenset(
    {
        "observed",
        "deterministic-candidate",
        "explicit-organization",
        "user-confirmed",
    }
)
WORKFLOW_RELATION_KINDS = frozenset(
    {"continues", "branches-from", "merged-into"}
)

STRONG_REASON_KINDS = frozenset(
    {
        "direct-source-relation",
        "shared-reference",
        "thread-membership",
        "workstream-membership",
        "user-assertion",
    }
)
SUPPORTING_REASON_KINDS = frozenset(
    {
        "same-workspace",
        "same-git-root",
        "same-git-branch",
        "lexical-overlap",
        "temporal-proximity",
    }
)
WORKFLOW_REASON_KINDS = STRONG_REASON_KINDS | SUPPORTING_REASON_KINDS

MAX_TITLE_CODE_POINTS = 500
MAX_EXPLICIT_FIELD_CODE_POINTS = 2_000
MAX_REASON_IDENTITY_CODE_POINTS = 500
MAX_EVIDENCE_KIND_CODE_POINTS = 80


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("{} must be non-empty text".format(field))
    return value.strip()


def _bounded_optional_text(value: object, limit: int) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:limit]


def _utc_timestamp(value: object) -> Optional[str]:
    parsed = parse_timestamp(value)
    return parsed.isoformat() if parsed is not None else None


def _mapping_value(row: Mapping[str, object], key: str) -> object:
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def workflow_episode_key(source_key: object, external_id: object) -> str:
    """Return an opaque stable key for one source-scoped native Session."""
    normalized_source = _required_text(source_key, "source_key")
    normalized_external = _required_text(external_id, "external_id")
    source_bytes = normalized_source.encode("utf-8")
    external_bytes = normalized_external.encode("utf-8")
    payload = (
        len(source_bytes).to_bytes(8, "big")
        + source_bytes
        + len(external_bytes).to_bytes(8, "big")
        + external_bytes
    )
    return "session:" + hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class WorkflowEpisode:
    episode_key: str
    session_id: int
    source_key: str
    destination: str
    observed_start_at: Optional[str]
    last_observed_at: Optional[str]
    display_title: Optional[str]
    workspace_id: Optional[int]
    workspace_name: Optional[str]
    git_branch: Optional[str]
    intent: Optional[str]
    outcome: Optional[str]
    next_action: Optional[str]
    evidence_counts: Tuple[Tuple[str, int], ...]
    activity_state: str
    lifecycle_state: str
    closure_reason: Optional[str]
    authority: str
    projection_version: str = WORKFLOW_PROJECTION_VERSION

    def as_dict(self) -> dict:
        return {
            "episode_key": self.episode_key,
            "session_id": self.session_id,
            "source_key": self.source_key,
            "destination": self.destination,
            "observed_start_at": self.observed_start_at,
            "last_observed_at": self.last_observed_at,
            "display_title": self.display_title,
            "workspace_id": self.workspace_id,
            "workspace_name": self.workspace_name,
            "git_branch": self.git_branch,
            "intent": self.intent,
            "outcome": self.outcome,
            "next_action": self.next_action,
            "evidence_counts": dict(self.evidence_counts),
            "activity_state": self.activity_state,
            "lifecycle_state": self.lifecycle_state,
            "closure_reason": self.closure_reason,
            "authority": self.authority,
            "projection_version": self.projection_version,
        }


def workflow_episode_from_session(
    row: Mapping[str, object],
    *,
    first_event_at: object = None,
    intent: object = None,
    outcome: object = None,
    next_action: object = None,
    evidence_counts: Optional[Mapping[str, int]] = None,
    activity_state: str = "unknown",
    lifecycle_state: str = "unknown",
    closure_reason: Optional[str] = None,
    authority: str = "observed",
) -> WorkflowEpisode:
    """Build one bounded Episode descriptor from normalized Session metadata."""
    if _mapping_value(row, "session_class") != "work":
        raise ValueError("workflow Episode requires a work Session")
    if _mapping_value(row, "session_role") != "primary":
        raise ValueError("workflow Episode requires a primary Session")

    raw_session_id = _mapping_value(row, "id")
    if (
        isinstance(raw_session_id, bool)
        or not isinstance(raw_session_id, int)
        or raw_session_id <= 0
    ):
        raise ValueError("session_id must be a positive integer")

    source_key = _required_text(_mapping_value(row, "source_key"), "source_key")
    external_id = _required_text(
        _mapping_value(row, "external_id"), "external_id"
    )

    observed_values = [
        _mapping_value(row, "started_at"),
        first_event_at
        if first_event_at is not None
        else _mapping_value(row, "first_event_at"),
        _mapping_value(row, "last_event_at"),
        _mapping_value(row, "ended_at"),
    ]
    parsed_values = [
        parsed
        for parsed in (parse_timestamp(value) for value in observed_values)
        if parsed is not None
    ]
    observed_start_at = min(parsed_values).isoformat() if parsed_values else None
    last_observed_at = max(parsed_values).isoformat() if parsed_values else None

    if activity_state not in ACTIVITY_STATES:
        raise ValueError("unsupported activity_state")
    if lifecycle_state not in LIFECYCLE_STATES:
        raise ValueError("unsupported lifecycle_state")
    if authority not in AUTHORITY_STATES:
        raise ValueError("unsupported authority")
    if lifecycle_state == "closed":
        if closure_reason not in CLOSURE_REASONS:
            raise ValueError("closed lifecycle requires a supported closure_reason")
    elif closure_reason is not None:
        raise ValueError("closure_reason is allowed only for closed lifecycle")

    workspace_id = _mapping_value(row, "workspace_id")
    if isinstance(workspace_id, bool) or (
        workspace_id is not None
        and (not isinstance(workspace_id, int) or workspace_id <= 0)
    ):
        raise ValueError("workspace_id must be a positive integer or absent")

    normalized_counts = []
    for kind, count in (evidence_counts or {}).items():
        normalized_kind = _required_text(kind, "evidence kind")
        if len(normalized_kind) > MAX_EVIDENCE_KIND_CODE_POINTS:
            raise ValueError("evidence kind exceeds the supported bound")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("evidence count must be a non-negative integer")
        normalized_counts.append((normalized_kind, count))
    normalized_counts.sort(key=lambda item: item[0])

    return WorkflowEpisode(
        episode_key=workflow_episode_key(source_key, external_id),
        session_id=raw_session_id,
        source_key=source_key,
        destination="/sessions/{}".format(raw_session_id),
        observed_start_at=observed_start_at,
        last_observed_at=last_observed_at,
        display_title=_bounded_optional_text(
            _mapping_value(row, "title"), MAX_TITLE_CODE_POINTS
        ),
        workspace_id=workspace_id,
        workspace_name=_bounded_optional_text(
            _mapping_value(row, "workspace_name"), MAX_TITLE_CODE_POINTS
        ),
        git_branch=_bounded_optional_text(
            _mapping_value(row, "git_branch"), MAX_TITLE_CODE_POINTS
        ),
        intent=_bounded_optional_text(intent, MAX_EXPLICIT_FIELD_CODE_POINTS),
        outcome=_bounded_optional_text(outcome, MAX_EXPLICIT_FIELD_CODE_POINTS),
        next_action=_bounded_optional_text(
            next_action, MAX_EXPLICIT_FIELD_CODE_POINTS
        ),
        evidence_counts=tuple(normalized_counts),
        activity_state=activity_state,
        lifecycle_state=lifecycle_state,
        closure_reason=closure_reason,
        authority=authority,
    )


@dataclass(frozen=True)
class WorkflowRelationReason:
    kind: str
    identity: str
    observed_at: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "identity": self.identity,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class WorkflowRelation:
    source_episode_key: str
    target_episode_key: str
    kind: str
    authority: str
    reasons: Tuple[WorkflowRelationReason, ...]
    source_observed_at: Optional[str]
    target_observed_at: Optional[str]
    projection_version: str = WORKFLOW_PROJECTION_VERSION

    def as_dict(self) -> dict:
        return {
            "source_episode_key": self.source_episode_key,
            "target_episode_key": self.target_episode_key,
            "kind": self.kind,
            "authority": self.authority,
            "reasons": [reason.as_dict() for reason in self.reasons],
            "source_observed_at": self.source_observed_at,
            "target_observed_at": self.target_observed_at,
            "projection_version": self.projection_version,
        }


@dataclass(frozen=True)
class WorkflowDiagnostic:
    code: str
    source_episode_key: Optional[str]
    target_episode_key: Optional[str]
    relation_kind: Optional[str]

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "source_episode_key": self.source_episode_key,
            "target_episode_key": self.target_episode_key,
            "relation_kind": self.relation_kind,
        }


@dataclass(frozen=True)
class NormalizedWorkflowRelations:
    relations: Tuple[WorkflowRelation, ...]
    diagnostics: Tuple[WorkflowDiagnostic, ...]
    projection_version: str = WORKFLOW_PROJECTION_VERSION

    def as_dict(self) -> dict:
        return {
            "relations": [relation.as_dict() for relation in self.relations],
            "diagnostics": [diagnostic.as_dict() for diagnostic in self.diagnostics],
            "projection_version": self.projection_version,
        }


def _relation_sort_key(relation: WorkflowRelation) -> tuple:
    raw_reasons = relation.reasons if isinstance(relation.reasons, tuple) else ()
    reason_key = tuple(
        sorted(
            (
                str(reason.kind),
                str(reason.identity),
                str(reason.observed_at or ""),
            )
            for reason in raw_reasons
        )
    )
    return (
        str(relation.source_observed_at or ""),
        str(relation.target_observed_at or ""),
        str(relation.source_episode_key),
        str(relation.target_episode_key),
        str(relation.kind),
        reason_key,
    )


def _diagnostic(code: str, relation: WorkflowRelation) -> WorkflowDiagnostic:
    return WorkflowDiagnostic(
        code=code,
        source_episode_key=(
            relation.source_episode_key
            if isinstance(relation.source_episode_key, str)
            else None
        ),
        target_episode_key=(
            relation.target_episode_key
            if isinstance(relation.target_episode_key, str)
            else None
        ),
        relation_kind=relation.kind if isinstance(relation.kind, str) else None,
    )


def _path_exists(adjacency: Mapping[str, set], start: str, target: str) -> bool:
    pending = [start]
    visited = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(sorted(adjacency.get(current, ()), reverse=True))
    return False


def normalize_workflow_relations(
    relations: Iterable[WorkflowRelation],
) -> NormalizedWorkflowRelations:
    """Return deterministic valid acyclic relations plus omission diagnostics."""
    retained = []
    diagnostics = []
    adjacency = {}
    seen = set()

    for relation in sorted(tuple(relations), key=_relation_sort_key):
        source_key = relation.source_episode_key
        target_key = relation.target_episode_key
        if (
            not isinstance(source_key, str)
            or not source_key.strip()
            or not isinstance(target_key, str)
            or not target_key.strip()
            or relation.kind not in WORKFLOW_RELATION_KINDS
            or relation.authority not in AUTHORITY_STATES
            or not isinstance(relation.reasons, tuple)
        ):
            diagnostics.append(_diagnostic("invalid-value", relation))
            continue
        source_key = source_key.strip()
        target_key = target_key.strip()
        if source_key == target_key:
            diagnostics.append(_diagnostic("self-edge", relation))
            continue

        source_at = _utc_timestamp(relation.source_observed_at)
        target_at = _utc_timestamp(relation.target_observed_at)
        if source_at is None or target_at is None:
            diagnostics.append(_diagnostic("invalid-value", relation))
            continue
        parsed_source = parse_timestamp(source_at)
        parsed_target = parse_timestamp(target_at)
        if parsed_source is None or parsed_target is None or parsed_target <= parsed_source:
            diagnostics.append(_diagnostic("non-forward-time", relation))
            continue

        normalized_reasons = []
        invalid_reason = False
        for reason in relation.reasons:
            if (
                not isinstance(reason, WorkflowRelationReason)
                or reason.kind not in WORKFLOW_REASON_KINDS
                or not isinstance(reason.identity, str)
                or not reason.identity.strip()
                or len(reason.identity.strip()) > MAX_REASON_IDENTITY_CODE_POINTS
            ):
                invalid_reason = True
                break
            observed_at = None
            if reason.observed_at is not None:
                observed_at = _utc_timestamp(reason.observed_at)
                if observed_at is None:
                    invalid_reason = True
                    break
            normalized_reasons.append(
                WorkflowRelationReason(
                    kind=reason.kind,
                    identity=reason.identity.strip(),
                    observed_at=observed_at,
                )
            )
        if invalid_reason:
            diagnostics.append(_diagnostic("invalid-value", relation))
            continue

        normalized_reasons = sorted(
            set(normalized_reasons),
            key=lambda reason: (reason.kind, reason.identity, reason.observed_at or ""),
        )
        reason_kinds = {reason.kind for reason in normalized_reasons}
        if not reason_kinds.intersection(STRONG_REASON_KINDS):
            diagnostics.append(_diagnostic("missing-strong-reason", relation))
            continue
        if (
            relation.authority == "user-confirmed"
            and "user-assertion" not in reason_kinds
        ) or (
            relation.authority == "explicit-organization"
            and not reason_kinds.intersection(
                {"thread-membership", "workstream-membership"}
            )
        ):
            diagnostics.append(_diagnostic("authority-reason-mismatch", relation))
            continue

        normalized = WorkflowRelation(
            source_episode_key=source_key.strip(),
            target_episode_key=target_key.strip(),
            kind=relation.kind,
            authority=relation.authority,
            reasons=tuple(normalized_reasons),
            source_observed_at=source_at,
            target_observed_at=target_at,
        )
        semantic_key = (
            normalized.source_episode_key,
            normalized.target_episode_key,
            normalized.kind,
            normalized.authority,
            normalized.reasons,
        )
        if semantic_key in seen:
            continue
        if _path_exists(adjacency, target_key, source_key):
            diagnostics.append(_diagnostic("cycle-omitted", normalized))
            continue
        seen.add(semantic_key)
        retained.append(normalized)
        adjacency.setdefault(source_key, set()).add(target_key)

    return NormalizedWorkflowRelations(
        relations=tuple(retained), diagnostics=tuple(diagnostics)
    )
