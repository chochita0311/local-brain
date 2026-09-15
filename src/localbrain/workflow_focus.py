"""Deterministic, read-only Session workflow Focus projection."""

import hashlib
import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple

from .activity import parse_timestamp
from .session_context import session_related_context
from .workflow_projection import (
    NormalizedWorkflowRelations,
    WorkflowDiagnostic,
    WorkflowEpisode,
    WorkflowRelation,
    WorkflowRelationReason,
    normalize_workflow_relations,
    workflow_episode_from_session,
)


WORKFLOW_FOCUS_VERSION = "localbrain.workflow-focus.v1"

MAX_WORKFLOW_CANDIDATES = 200
MAX_WORKFLOW_EPISODES = 24
MAX_WORKFLOW_BRANCH_ROOTS = 4
MAX_WORKFLOW_BRANCH_EPISODES = 4
MAX_WORKFLOW_EVIDENCE_PER_FAMILY = 5

FOCUS_STATUSES = frozenset({"ready", "missing", "ineligible"})
EVIDENCE_AVAILABILITY = frozenset(
    {"available", "stale", "unavailable", "missing", "archived", "unknown"}
)
EVIDENCE_AUTHORITIES = frozenset(
    {"observed", "explicit-organization"}
)


def _bounded_optional_text(value: object, limit: int = 500) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized[:limit] if normalized else None


def _positive_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("{} must be a positive integer".format(field))
    return value


def _entity_id(value: object) -> Optional[int]:
    try:
        normalized = int(str(value))
    except (TypeError, ValueError):
        return None
    return normalized if normalized > 0 else None


def _utc_timestamp(value: object) -> Optional[str]:
    parsed = parse_timestamp(value)
    return parsed.isoformat() if parsed is not None else None


def _opaque_identity(prefix: str, *values: object) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = str(value).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return "{}:{}".format(prefix, digest.hexdigest())


@dataclass(frozen=True)
class WorkflowEvidenceItem:
    evidence_key: str
    source_family: str
    identity: str
    destination: Optional[str]
    source_key: Optional[str]
    evidence_kind: str
    admission_reasons: Tuple[str, ...]
    observed_at: Optional[str]
    availability: str
    authority: str

    def as_dict(self) -> dict:
        return {
            "evidence_key": self.evidence_key,
            "source_family": self.source_family,
            "identity": self.identity,
            "destination": self.destination,
            "source_key": self.source_key,
            "evidence_kind": self.evidence_kind,
            "admission_reasons": list(self.admission_reasons),
            "observed_at": self.observed_at,
            "availability": self.availability,
            "authority": self.authority,
        }


@dataclass(frozen=True)
class WorkflowEvidenceGroup:
    source_family: str
    items: Tuple[WorkflowEvidenceItem, ...]
    retained_total: int
    observed_total: int
    partial: bool
    stale: bool

    def as_dict(self) -> dict:
        return {
            "source_family": self.source_family,
            "items": [item.as_dict() for item in self.items],
            "retained_total": self.retained_total,
            "observed_total": self.observed_total,
            "partial": self.partial,
            "stale": self.stale,
        }


@dataclass(frozen=True)
class WorkflowEpisodeView:
    episode: WorkflowEpisode
    evidence_groups: Tuple[WorkflowEvidenceGroup, ...]
    evidence_retained_total: int
    evidence_observed_total: int
    evidence_partial: bool

    def as_dict(self) -> dict:
        return {
            "episode": self.episode.as_dict(),
            "evidence_groups": [group.as_dict() for group in self.evidence_groups],
            "evidence_retained_total": self.evidence_retained_total,
            "evidence_observed_total": self.evidence_observed_total,
            "evidence_partial": self.evidence_partial,
        }


@dataclass(frozen=True)
class WorkflowFocusProjection:
    status: str
    selected_episode_key: Optional[str]
    episodes: Tuple[WorkflowEpisodeView, ...]
    relations: Tuple[WorkflowRelation, ...]
    diagnostics: Tuple[WorkflowDiagnostic, ...]
    candidate_observed_total: int
    candidate_retained_total: int
    episode_observed_total: int
    episode_retained_total: int
    branch_root_observed_total: int
    branch_root_retained_total: int
    projection_version: str = WORKFLOW_FOCUS_VERSION
    base_relations: Tuple[WorkflowRelation, ...] = ()
    base_episode_lifecycle: Tuple[Mapping[str, object], ...] = ()
    assertions: Tuple[Mapping[str, object], ...] = ()
    assertion_diagnostics: Tuple[Mapping[str, object], ...] = ()
    assertion_revision: Optional[str] = None
    assertion_overlay_version: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "selected_episode_key": self.selected_episode_key,
            "episodes": [episode.as_dict() for episode in self.episodes],
            "relations": [relation.as_dict() for relation in self.relations],
            "diagnostics": [item.as_dict() for item in self.diagnostics],
            "candidate_observed_total": self.candidate_observed_total,
            "candidate_retained_total": self.candidate_retained_total,
            "episode_observed_total": self.episode_observed_total,
            "episode_retained_total": self.episode_retained_total,
            "branch_root_observed_total": self.branch_root_observed_total,
            "branch_root_retained_total": self.branch_root_retained_total,
            "projection_version": self.projection_version,
            "base_relations": [
                relation.as_dict() for relation in self.base_relations
            ],
            "base_episode_lifecycle": [
                dict(item) for item in self.base_episode_lifecycle
            ],
            "assertions": [dict(item) for item in self.assertions],
            "assertion_diagnostics": [
                dict(item) for item in self.assertion_diagnostics
            ],
            "assertion_revision": self.assertion_revision,
            "assertion_overlay_version": self.assertion_overlay_version,
        }


@dataclass(frozen=True)
class _SessionFact:
    episode: WorkflowEpisode
    instant: Optional[datetime]
    workspace_id: Optional[int]
    git_root: Optional[str]
    git_branch: Optional[str]
    thread_ids: frozenset
    workstream_ids: frozenset
    reference_keys: frozenset


@dataclass(frozen=True)
class _EdgeProposal:
    source_key: str
    target_key: str
    kind: str
    priority: int
    reasons: Tuple[WorkflowRelationReason, ...]
    source_at: str
    target_at: str


def _empty_projection(status: str) -> WorkflowFocusProjection:
    if status not in FOCUS_STATUSES:
        raise ValueError("unsupported workflow Focus status")
    return WorkflowFocusProjection(
        status=status,
        selected_episode_key=None,
        episodes=(),
        relations=(),
        diagnostics=(),
        candidate_observed_total=0,
        candidate_retained_total=0,
        episode_observed_total=0,
        episode_retained_total=0,
        branch_root_observed_total=0,
        branch_root_retained_total=0,
    )


def _session_row(
    connection: sqlite3.Connection, session_id: int
) -> Optional[sqlite3.Row]:
    return connection.execute(
        """
        SELECT sessions.*, sources.kind AS source_key,
               workspaces.display_name AS workspace_name,
               workspaces.git_root,
               (
                   SELECT activity_events.occurred_at
                   FROM activity_events
                   WHERE activity_events.session_id = sessions.id
                     AND julianday(activity_events.occurred_at) IS NOT NULL
                   ORDER BY julianday(activity_events.occurred_at),
                            activity_events.occurred_at, activity_events.id
                   LIMIT 1
               ) AS first_event_at
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.id = ?
        """,
        (session_id,),
    ).fetchone()


def workflow_session_is_eligible(
    connection: sqlite3.Connection, session_id: int
) -> bool:
    """Return whether Session detail may expose the Workflow Focus entry."""
    _positive_integer(session_id, "session_id")
    row = _session_row(connection, session_id)
    if row is None or (
        row["session_class"] != "work"
        or row["session_role"] != "primary"
        or row["index_policy"] != "full"
    ):
        return False
    if int(row["event_count"] or 0) > 0:
        return True
    return (
        connection.execute(
            """
            SELECT (
                EXISTS(SELECT 1 FROM activity_events WHERE session_id = ?)
                OR EXISTS(SELECT 1 FROM usage_records WHERE session_id = ?)
            )
            """,
            (session_id, session_id),
        ).fetchone()[0]
        == 1
    )


def _eligible_session_rows(connection: sqlite3.Connection) -> List[sqlite3.Row]:
    return connection.execute(
        """
        SELECT sessions.*, sources.kind AS source_key,
               workspaces.display_name AS workspace_name,
               workspaces.git_root,
               (
                   SELECT activity_events.occurred_at
                   FROM activity_events
                   WHERE activity_events.session_id = sessions.id
                     AND julianday(activity_events.occurred_at) IS NOT NULL
                   ORDER BY julianday(activity_events.occurred_at),
                            activity_events.occurred_at, activity_events.id
                   LIMIT 1
               ) AS first_event_at,
               (
                   SELECT COUNT(*)
                   FROM sessions AS children
                   WHERE children.parent_session_id = sessions.id
                     AND children.source_id = sessions.source_id
                     AND children.session_class = 'work'
                     AND children.session_role = 'subsession'
               ) AS subsession_count
        FROM sessions
        JOIN sources ON sources.id = sessions.source_id
        LEFT JOIN workspaces ON workspaces.id = sessions.workspace_id
        WHERE sessions.session_class = 'work'
          AND sessions.session_role = 'primary'
          AND sessions.index_policy = 'full'
          AND (
              sessions.event_count > 0
              OR EXISTS (
                  SELECT 1 FROM activity_events
                  WHERE activity_events.session_id = sessions.id
              )
              OR EXISTS (
                  SELECT 1 FROM usage_records
                  WHERE usage_records.session_id = sessions.id
              )
          )
        ORDER BY sessions.id
        """
    ).fetchall()


def _user_memberships(
    connection: sqlite3.Connection,
) -> Tuple[Dict[int, Set[int]], Dict[int, Set[int]]]:
    thread_ids: Dict[int, Set[int]] = defaultdict(set)
    workstream_ids: Dict[int, Set[int]] = defaultdict(set)
    rows = connection.execute(
        """
        SELECT 'workstream' AS scope_kind,
               workstream_links.workstream_id AS workstream_id,
               NULL AS thread_id,
               workstream_links.entity_id AS session_id
        FROM workstream_links
        WHERE workstream_links.entity_type = 'session'
          AND workstream_links.linked_by = 'user'
        UNION ALL
        SELECT 'thread', threads.workstream_id, thread_links.thread_id,
               thread_links.entity_id
        FROM thread_links
        JOIN threads ON threads.id = thread_links.thread_id
        WHERE thread_links.entity_type = 'session'
          AND thread_links.linked_by = 'user'
        ORDER BY scope_kind, workstream_id, thread_id, session_id
        """
    ).fetchall()
    for row in rows:
        session_id = _entity_id(row["session_id"])
        if session_id is None:
            continue
        workstream_ids[session_id].add(int(row["workstream_id"]))
        if row["thread_id"] is not None:
            thread_ids[session_id].add(int(row["thread_id"]))
    return thread_ids, workstream_ids


def _reference_keys(
    connection: sqlite3.Connection,
) -> Dict[int, Set[Tuple[str, str]]]:
    values: Dict[int, Set[Tuple[str, str]]] = defaultdict(set)
    rows = connection.execute(
        """
        SELECT session_id, target_kind, target_key
        FROM session_reference_evidence
        GROUP BY session_id, target_kind, target_key
        ORDER BY session_id, target_kind, target_key
        """
    ).fetchall()
    for row in rows:
        values[int(row["session_id"])].add(
            (str(row["target_kind"]), str(row["target_key"]))
        )
    return values


def _fact_instant(episode: WorkflowEpisode) -> Optional[datetime]:
    return parse_timestamp(episode.last_observed_at or episode.observed_start_at)


def _session_facts(connection: sqlite3.Connection) -> Dict[int, _SessionFact]:
    threads, workstreams = _user_memberships(connection)
    references = _reference_keys(connection)
    values = {}
    for row in _eligible_session_rows(connection):
        session_id = int(row["id"])
        counts = {
            "references": len(references.get(session_id, ())),
            "threads": len(threads.get(session_id, ())),
            "workstreams": len(workstreams.get(session_id, ())),
            "subsessions": max(0, int(row["subsession_count"] or 0)),
        }
        episode = workflow_episode_from_session(
            row,
            first_event_at=row["first_event_at"],
            evidence_counts=counts,
            activity_state="unknown",
            lifecycle_state="unknown",
            authority="observed",
        )
        values[session_id] = _SessionFact(
            episode=episode,
            instant=_fact_instant(episode),
            workspace_id=(
                int(row["workspace_id"])
                if row["workspace_id"] is not None
                else None
            ),
            git_root=_bounded_optional_text(row["git_root"], 8_000),
            git_branch=_bounded_optional_text(row["git_branch"], 500),
            thread_ids=frozenset(threads.get(session_id, ())),
            workstream_ids=frozenset(workstreams.get(session_id, ())),
            reference_keys=frozenset(references.get(session_id, ())),
        )
    return values


def _same_git_root(first: _SessionFact, second: _SessionFact) -> bool:
    return bool(first.git_root and first.git_root == second.git_root)


def _same_git_branch(first: _SessionFact, second: _SessionFact) -> bool:
    return bool(first.git_branch and first.git_branch == second.git_branch)


def _candidate_strength(
    selected: _SessionFact, candidate: _SessionFact
) -> Optional[int]:
    shared_threads = selected.thread_ids & candidate.thread_ids
    shared_workstreams = selected.workstream_ids & candidate.workstream_ids
    shared_references = selected.reference_keys & candidate.reference_keys
    same_root = _same_git_root(selected, candidate)
    same_branch = _same_git_branch(selected, candidate)
    same_workspace = bool(
        selected.workspace_id
        and selected.workspace_id == candidate.workspace_id
    )
    if shared_threads:
        return 0
    if shared_references and shared_workstreams:
        return 1
    if shared_references and same_root and same_branch:
        return 2
    if shared_references and (same_workspace or same_root):
        return 3
    if shared_workstreams and same_root:
        return 4 if same_branch else 5
    return None


def _temporal_distance(
    first: Optional[datetime], second: Optional[datetime]
) -> float:
    if first is None or second is None:
        return math.inf
    return abs((first - second).total_seconds())


def _instant_sort_value(value: Optional[datetime]) -> Tuple[int, float]:
    if value is None:
        return (1, 0.0)
    return (0, value.timestamp())


def _ordered_candidates(
    selected: _SessionFact, facts: Iterable[_SessionFact]
) -> Tuple[List[_SessionFact], int]:
    qualified = []
    for fact in facts:
        if fact.episode.episode_key == selected.episode.episode_key:
            continue
        strength = _candidate_strength(selected, fact)
        if strength is None:
            continue
        qualified.append((strength, fact))
    qualified.sort(
        key=lambda item: (
            item[0],
            _temporal_distance(selected.instant, item[1].instant),
            _instant_sort_value(item[1].instant),
            item[1].episode.episode_key,
        )
    )
    return (
        [item[1] for item in qualified[:MAX_WORKFLOW_CANDIDATES]],
        len(qualified),
    )


def _ordered_group(values: Iterable[_SessionFact]) -> List[_SessionFact]:
    return sorted(
        (value for value in values if value.instant is not None),
        key=lambda value: (value.instant, value.episode.episode_key),
    )


def _reference_reason(reference: Tuple[str, str]) -> WorkflowRelationReason:
    return WorkflowRelationReason(
        "shared-reference", "reference:{}:{}".format(*reference)
    )


def _git_reasons(fact: _SessionFact) -> Tuple[WorkflowRelationReason, ...]:
    if not fact.git_root:
        return ()
    reasons = [
        WorkflowRelationReason(
            "same-git-root", _opaque_identity("git-root", fact.git_root)
        )
    ]
    if fact.git_branch:
        reasons.append(
            WorkflowRelationReason(
                "same-git-branch",
                _opaque_identity("git-branch", fact.git_root, fact.git_branch),
            )
        )
    return tuple(reasons)


def _add_edge(
    proposals: Dict[Tuple[str, str, str], _EdgeProposal],
    first: _SessionFact,
    second: _SessionFact,
    *,
    kind: str,
    priority: int,
    reasons: Iterable[WorkflowRelationReason],
) -> None:
    if first.instant is None or second.instant is None:
        return
    if first.instant == second.instant:
        return
    source, target = (
        (first, second) if first.instant < second.instant else (second, first)
    )
    source_at = source.episode.last_observed_at or source.episode.observed_start_at
    target_at = target.episode.last_observed_at or target.episode.observed_start_at
    if source_at is None or target_at is None:
        return
    normalized_reasons = tuple(
        sorted(
            set(reasons),
            key=lambda reason: (
                reason.kind,
                reason.identity,
                reason.observed_at or "",
            ),
        )
    )
    key = (source.episode.episode_key, target.episode.episode_key, kind)
    current = proposals.get(key)
    proposal = _EdgeProposal(
        source_key=key[0],
        target_key=key[1],
        kind=kind,
        priority=priority,
        reasons=normalized_reasons,
        source_at=source_at,
        target_at=target_at,
    )
    if current is None or priority < current.priority:
        proposals[key] = proposal
    elif priority == current.priority:
        proposals[key] = _EdgeProposal(
            source_key=current.source_key,
            target_key=current.target_key,
            kind=current.kind,
            priority=current.priority,
            reasons=tuple(
                sorted(
                    set(current.reasons) | set(normalized_reasons),
                    key=lambda reason: (
                        reason.kind,
                        reason.identity,
                        reason.observed_at or "",
                    ),
                )
            ),
            source_at=current.source_at,
            target_at=current.target_at,
        )


def _continues_proposals(
    facts: Iterable[_SessionFact],
    proposals: Dict[Tuple[str, str, str], _EdgeProposal],
) -> None:
    by_thread = defaultdict(list)
    by_reference_workstream = defaultdict(list)
    by_reference_git_branch = defaultdict(list)
    for fact in facts:
        for thread_id in fact.thread_ids:
            by_thread[thread_id].append(fact)
        for reference in fact.reference_keys:
            for workstream_id in fact.workstream_ids:
                by_reference_workstream[(reference, workstream_id)].append(fact)
            if fact.git_root and fact.git_branch:
                by_reference_git_branch[
                    (reference, fact.git_root, fact.git_branch)
                ].append(fact)

    for thread_id, members in sorted(by_thread.items()):
        ordered = _ordered_group(members)
        for first, second in zip(ordered, ordered[1:]):
            _add_edge(
                proposals,
                first,
                second,
                kind="continues",
                priority=20,
                reasons=(
                    WorkflowRelationReason(
                        "thread-membership", "thread:{}".format(thread_id)
                    ),
                ),
            )

    for (reference, workstream_id), members in sorted(
        by_reference_workstream.items(), key=lambda item: str(item[0])
    ):
        ordered = _ordered_group(members)
        for first, second in zip(ordered, ordered[1:]):
            _add_edge(
                proposals,
                first,
                second,
                kind="continues",
                priority=30,
                reasons=(
                    _reference_reason(reference),
                    WorkflowRelationReason(
                        "workstream-membership",
                        "workstream:{}".format(workstream_id),
                    ),
                ),
            )

    for (reference, _root, _branch), members in sorted(
        by_reference_git_branch.items(), key=lambda item: str(item[0])
    ):
        ordered = _ordered_group(members)
        for first, second in zip(ordered, ordered[1:]):
            _add_edge(
                proposals,
                first,
                second,
                kind="continues",
                priority=40,
                reasons=(
                    _reference_reason(reference),
                    *_git_reasons(first),
                ),
            )


def _branch_proposals(
    facts: Iterable[_SessionFact],
    proposals: Dict[Tuple[str, str, str], _EdgeProposal],
) -> None:
    ordered = _ordered_group(facts)
    for target_index, target in enumerate(ordered):
        if not target.git_root or not target.git_branch:
            continue
        has_same_branch_predecessor = any(
            source.git_root == target.git_root
            and source.git_branch == target.git_branch
            and (
                bool(source.thread_ids & target.thread_ids)
                or bool(source.reference_keys & target.reference_keys)
            )
            for source in ordered[:target_index]
        )
        if has_same_branch_predecessor:
            continue
        candidates = []
        for source in ordered[:target_index]:
            if (
                not source.git_root
                or source.git_root != target.git_root
                or not source.git_branch
                or source.git_branch == target.git_branch
            ):
                continue
            shared_references = source.reference_keys & target.reference_keys
            shared_threads = source.thread_ids & target.thread_ids
            shared_workstreams = source.workstream_ids & target.workstream_ids
            if not (shared_references or shared_threads or shared_workstreams):
                continue
            signal_rank = (
                0 if shared_references else (1 if shared_threads else 2)
            )
            candidates.append(
                (
                    _temporal_distance(source.instant, target.instant),
                    signal_rank,
                    source.episode.episode_key,
                    source,
                    shared_references,
                    shared_threads,
                    shared_workstreams,
                )
            )
        if not candidates:
            continue
        (
            _distance,
            signal_rank,
            _source_key,
            source,
            shared_references,
            shared_threads,
            shared_workstreams,
        ) = min(candidates, key=lambda item: item[:3])
        reasons: List[WorkflowRelationReason] = []
        if shared_references:
            reasons.append(_reference_reason(sorted(shared_references)[0]))
        elif shared_threads:
            reasons.append(
                WorkflowRelationReason(
                    "thread-membership",
                    "thread:{}".format(min(shared_threads)),
                )
            )
        else:
            reasons.append(
                WorkflowRelationReason(
                    "workstream-membership",
                    "workstream:{}".format(min(shared_workstreams)),
                )
            )
        reasons.extend(_git_reasons(source)[:1])
        _add_edge(
            proposals,
            source,
            target,
            kind="branches-from",
            priority=signal_rank,
            reasons=reasons,
        )


def _normalized_relations(
    facts: Iterable[_SessionFact],
) -> Tuple[NormalizedWorkflowRelations, Dict[Tuple[str, str, str], int]]:
    values = list(facts)
    proposals: Dict[Tuple[str, str, str], _EdgeProposal] = {}
    _continues_proposals(values, proposals)
    _branch_proposals(values, proposals)

    by_target = defaultdict(list)
    for proposal in proposals.values():
        by_target[proposal.target_key].append(proposal)
    selected = []
    priorities = {}
    for target_key in sorted(by_target):
        proposal = min(
            by_target[target_key],
            key=lambda item: (
                item.priority,
                _temporal_distance(
                    parse_timestamp(item.source_at),
                    parse_timestamp(item.target_at),
                ),
                item.source_key,
                item.kind,
            ),
        )
        relation = WorkflowRelation(
            source_episode_key=proposal.source_key,
            target_episode_key=proposal.target_key,
            kind=proposal.kind,
            authority="deterministic-candidate",
            reasons=proposal.reasons,
            source_observed_at=proposal.source_at,
            target_observed_at=proposal.target_at,
        )
        selected.append(relation)
        priorities[(proposal.source_key, proposal.target_key, proposal.kind)] = (
            proposal.priority
        )
    return normalize_workflow_relations(selected), priorities


def _focus_neighborhood(
    selected: _SessionFact,
    facts: Mapping[str, _SessionFact],
    normalized: NormalizedWorkflowRelations,
    priorities: Mapping[Tuple[str, str, str], int],
    candidate_ranks: Mapping[str, int],
) -> Tuple[Set[str], Set[Tuple[str, str, str]], int, int, int]:
    adjacency = defaultdict(list)
    for relation in normalized.relations:
        edge_key = (
            relation.source_episode_key,
            relation.target_episode_key,
            relation.kind,
        )
        adjacency[relation.source_episode_key].append((relation, True))
        adjacency[relation.target_episode_key].append((relation, False))

    selected_key = selected.episode.episode_key
    connected = {selected_key}
    pending = [selected_key]
    while pending:
        current = pending.pop()
        for relation, forward in adjacency.get(current, ()):
            neighbor = (
                relation.target_episode_key
                if forward
                else relation.source_episode_key
            )
            if neighbor not in connected:
                connected.add(neighbor)
                pending.append(neighbor)
    observed_branch_roots = {
        relation.target_episode_key
        for relation in normalized.relations
        if relation.kind == "branches-from"
        and relation.source_episode_key in connected
        and relation.target_episode_key in connected
    }

    retained = {selected_key}
    branch_owner: Dict[str, Optional[str]] = {selected_key: None}
    branch_counts: Dict[str, int] = defaultdict(int)
    retained_branch_roots: Set[str] = set()
    traversed: Set[Tuple[str, str, str]] = set()

    while len(retained) < MAX_WORKFLOW_EPISODES:
        options = []
        for current in sorted(retained):
            for relation, forward in adjacency.get(current, ()):
                neighbor = (
                    relation.target_episode_key
                    if forward
                    else relation.source_episode_key
                )
                if neighbor in retained or neighbor not in connected:
                    continue
                edge_key = (
                    relation.source_episode_key,
                    relation.target_episode_key,
                    relation.kind,
                )
                options.append(
                    (
                        candidate_ranks.get(neighbor, MAX_WORKFLOW_CANDIDATES + 1),
                        0 if relation.kind == "continues" else 1,
                        priorities.get(edge_key, 99),
                        _instant_sort_value(facts[neighbor].instant),
                        neighbor,
                        current,
                        relation,
                        forward,
                    )
                )
        if not options:
            break
        accepted = False
        for option in sorted(options, key=lambda item: item[:5]):
            neighbor, current, relation, forward = (
                option[4],
                option[5],
                option[6],
                option[7],
            )
            owner = branch_owner.get(current)
            root = None
            if relation.kind == "branches-from":
                root = relation.target_episode_key
                if root not in retained_branch_roots:
                    if len(retained_branch_roots) >= MAX_WORKFLOW_BRANCH_ROOTS:
                        continue
                    retained_branch_roots.add(root)
                    branch_counts[root] = 0 if forward else 1
                next_owner = root if forward else None
            else:
                next_owner = owner
            if (
                next_owner is not None
                and branch_counts[next_owner] >= MAX_WORKFLOW_BRANCH_EPISODES
            ):
                continue
            retained.add(neighbor)
            branch_owner[neighbor] = next_owner
            if next_owner is not None:
                branch_counts[next_owner] += 1
            traversed.add(
                (
                    relation.source_episode_key,
                    relation.target_episode_key,
                    relation.kind,
                )
            )
            accepted = True
            break
        if not accepted:
            break

    return (
        retained,
        traversed,
        len(connected),
        len(observed_branch_roots),
        len(retained_branch_roots),
    )


def _related_family(item: Mapping[str, object]) -> str:
    entity_type = str(item.get("entity_type") or "")
    label = str(item.get("kind_label") or "").casefold()
    if entity_type == "document":
        return "local-context"
    if entity_type == "atlassian" or label in {"jira", "confluence", "wiki"}:
        return "atlassian"
    if entity_type == "local":
        return "local-resource"
    if label == "slack":
        return "slack"
    if label == "git":
        return "git"
    return "external"


def _availability(value: object, *, stale: bool = False) -> str:
    normalized = str(value or "unknown")
    if stale and normalized == "available":
        return "stale"
    return normalized if normalized in EVIDENCE_AVAILABILITY else "unknown"


def _related_evidence(
    connection: sqlite3.Connection,
    fact: _SessionFact,
) -> Tuple[List[WorkflowEvidenceItem], Dict[str, int], Set[str]]:
    projection = session_related_context(connection, fact.episode.session_id)
    items = []
    observed_hints: Dict[str, int] = defaultdict(int)
    stale_families: Set[str] = set()
    for group in projection.get("groups", ()):
        group_items = list(group.get("items", ()))
        families = defaultdict(int)
        for raw in group_items:
            family = _related_family(raw)
            families[family] += 1
            direct = group.get("key") == "direct"
            reasons = ["direct-reference" if direct else "organization"]
            for organization in raw.get("organization", ()):
                kind = str(organization.get("kind") or "")
                if kind in {"thread", "workstream"}:
                    reasons.append("{}-membership".format(kind))
            evidence = list(raw.get("evidence", ()))
            evidence_kind = (
                str(evidence[0].get("kind"))
                if direct and evidence
                else "organization-link"
            )
            observed_at = _utc_timestamp(raw.get("observed_at"))
            identity = _bounded_optional_text(raw.get("identity")) or "Unknown evidence"
            target_key = _bounded_optional_text(raw.get("target_key"), 500)
            if target_key is None:
                target_key = _opaque_identity("evidence", family, identity)
            items.append(
                WorkflowEvidenceItem(
                    evidence_key="related:{}".format(target_key),
                    source_family=family,
                    identity=identity,
                    destination=_bounded_optional_text(raw.get("href"), 8_000),
                    source_key=fact.episode.source_key if direct else "localbrain",
                    evidence_kind=evidence_kind,
                    admission_reasons=tuple(sorted(set(reasons))),
                    observed_at=observed_at,
                    availability=_availability(
                        raw.get("availability"), stale=bool(group.get("stale"))
                    ),
                    authority="observed" if direct else "explicit-organization",
                )
            )
            if group.get("stale"):
                stale_families.add(family)
        for family, count in families.items():
            observed_hints[family] += count
        unresolved = max(0, int(group.get("total") or 0) - len(group_items))
        if unresolved:
            observed_hints["unknown"] += unresolved
            if group.get("stale"):
                stale_families.add("unknown")
    return items, observed_hints, stale_families


def _membership_evidence(
    connection: sqlite3.Connection, session_id: int
) -> List[WorkflowEvidenceItem]:
    rows = connection.execute(
        """
        SELECT 'workstream' AS scope_kind, workstreams.id AS workstream_id,
               NULL AS thread_id, workstreams.name AS identity,
               workstream_links.created_at, workstream_links.linked_by
        FROM workstream_links
        JOIN workstreams ON workstreams.id = workstream_links.workstream_id
        WHERE workstream_links.entity_type = 'session'
          AND workstream_links.entity_id = ?
        UNION ALL
        SELECT 'thread', workstreams.id, threads.id, threads.title,
               thread_links.created_at, thread_links.linked_by
        FROM thread_links
        JOIN threads ON threads.id = thread_links.thread_id
        JOIN workstreams ON workstreams.id = threads.workstream_id
        WHERE thread_links.entity_type = 'session'
          AND thread_links.entity_id = ?
        ORDER BY scope_kind, workstream_id, thread_id
        """,
        (str(session_id), str(session_id)),
    ).fetchall()
    items = []
    for row in rows:
        thread_id = int(row["thread_id"]) if row["thread_id"] is not None else None
        scope_kind = str(row["scope_kind"])
        suffix = "thread:{}".format(thread_id) if thread_id else "workstream"
        destination = "/workstreams/{}".format(int(row["workstream_id"]))
        if thread_id:
            destination += "#thread-{}".format(thread_id)
        items.append(
            WorkflowEvidenceItem(
                evidence_key="organization:{}:{}".format(
                    int(row["workstream_id"]), suffix
                ),
                source_family="organization",
                identity=_bounded_optional_text(row["identity"]) or "Untitled",
                destination=destination,
                source_key="localbrain",
                evidence_kind="{}-membership".format(scope_kind),
                admission_reasons=("{}-membership".format(scope_kind),),
                observed_at=_utc_timestamp(row["created_at"]),
                availability="available",
                authority="explicit-organization",
            )
        )
    return items


def _subsession_evidence(
    connection: sqlite3.Connection, session_id: int
) -> Tuple[List[WorkflowEvidenceItem], int]:
    rows = connection.execute(
        """
        SELECT children.id, children.title, children.started_at,
               children.last_event_at, sources.kind AS source_key,
               COUNT(*) OVER () AS observed_total
        FROM sessions AS parents
        JOIN sessions AS children ON children.parent_session_id = parents.id
        JOIN sources ON sources.id = children.source_id
        WHERE parents.id = ?
          AND parents.session_class = 'work'
          AND parents.session_role = 'primary'
          AND children.session_class = 'work'
          AND children.session_role = 'subsession'
          AND children.source_id = parents.source_id
        ORDER BY COALESCE(children.last_event_at, children.started_at) DESC,
                 children.id DESC
        LIMIT ?
        """,
        (session_id, MAX_WORKFLOW_EVIDENCE_PER_FAMILY + 1),
    ).fetchall()
    total = int(rows[0]["observed_total"]) if rows else 0
    return (
        [
            WorkflowEvidenceItem(
                evidence_key="subsession:{}".format(int(row["id"])),
                source_family="session",
                identity=_bounded_optional_text(row["title"]) or "Untitled Session",
                destination="/sessions/{}".format(int(row["id"])),
                source_key=str(row["source_key"]),
                evidence_kind="subsession",
                admission_reasons=("subsession",),
                observed_at=_utc_timestamp(
                    row["last_event_at"] or row["started_at"]
                ),
                availability="available",
                authority="observed",
            )
            for row in rows
        ],
        total,
    )


def _structure_evidence(
    connection: sqlite3.Connection, session_id: int
) -> Tuple[List[WorkflowEvidenceItem], int, bool]:
    rows = connection.execute(
        """
        SELECT structure_refs.id, structure_refs.service,
               structure_refs.reference_kind, structure_refs.reference_identity,
               MAX(evidence.observed_at) AS observed_at,
               scans.status AS scan_status,
               COUNT(*) OVER () AS observed_total
        FROM atlassian_structure_reference_evidence AS evidence
        JOIN atlassian_structure_references AS structure_refs
          ON structure_refs.id = evidence.reference_id
        LEFT JOIN session_reference_scans AS scans
          ON scans.session_id = evidence.session_id
        WHERE evidence.session_id = ?
        GROUP BY structure_refs.id, structure_refs.service,
                 structure_refs.reference_kind, structure_refs.reference_identity,
                 scans.status
        ORDER BY CASE WHEN MAX(evidence.observed_at) IS NULL THEN 1 ELSE 0 END,
                 MAX(evidence.observed_at), structure_refs.id
        """,
        (session_id,),
    ).fetchall()
    total = int(rows[0]["observed_total"]) if rows else 0
    stale = any(row["scan_status"] == "error" for row in rows)
    items = []
    for row in rows:
        scan_status = row["scan_status"]
        availability = (
            "available"
            if scan_status in {"ok", "partial"}
            else ("stale" if scan_status == "error" else "unknown")
        )
        items.append(
            WorkflowEvidenceItem(
                evidence_key="atlassian-structure:{}".format(int(row["id"])),
                source_family="atlassian",
                identity=_bounded_optional_text(row["reference_identity"])
                or str(row["reference_kind"]),
                destination="/atlassian/references/{}".format(int(row["id"])),
                source_key="atlassian:{}".format(str(row["service"])),
                evidence_kind="structure-reference",
                admission_reasons=("structure-reference",),
                observed_at=_utc_timestamp(row["observed_at"]),
                availability=availability,
                authority="observed",
            )
        )
    return items, total, stale


def _evidence_groups(
    connection: sqlite3.Connection, fact: _SessionFact
) -> Tuple[Tuple[WorkflowEvidenceGroup, ...], int, int, bool]:
    related, observed_hints, stale_families = _related_evidence(connection, fact)
    values = list(related)
    retained_hints: Dict[str, int] = defaultdict(int)
    values.extend(_membership_evidence(connection, fact.episode.session_id))
    subsessions, subsession_total = _subsession_evidence(
        connection, fact.episode.session_id
    )
    values.extend(subsessions)
    if subsession_total:
        retained_hints["session"] = subsession_total
        observed_hints["session"] = max(
            observed_hints.get("session", 0), subsession_total
        )
    structures, structure_total, structure_stale = _structure_evidence(
        connection, fact.episode.session_id
    )
    values.extend(structures)
    if structure_total:
        observed_hints["atlassian"] = max(
            observed_hints.get("atlassian", 0), structure_total
        )
    if structure_stale:
        stale_families.add("atlassian")

    deduplicated = {}
    for item in values:
        if item.availability not in EVIDENCE_AVAILABILITY:
            continue
        if item.authority not in EVIDENCE_AUTHORITIES:
            continue
        key = (item.source_family, item.evidence_key)
        current = deduplicated.get(key)
        if current is None or (
            current.authority == "explicit-organization"
            and item.authority == "observed"
        ):
            deduplicated[key] = item

    by_family = defaultdict(list)
    for item in deduplicated.values():
        by_family[item.source_family].append(item)
    families = sorted(set(by_family) | set(observed_hints))
    groups = []
    for family in families:
        items = sorted(
            by_family.get(family, ()),
            key=lambda item: (
                0 if item.authority == "observed" else 1,
                0 if item.observed_at else 1,
                item.observed_at or "",
                item.identity.casefold(),
                item.evidence_key,
            ),
        )
        retained_total = max(len(items), retained_hints.get(family, 0))
        observed_total = max(retained_total, observed_hints.get(family, 0))
        visible = tuple(items[:MAX_WORKFLOW_EVIDENCE_PER_FAMILY])
        groups.append(
            WorkflowEvidenceGroup(
                source_family=family,
                items=visible,
                retained_total=retained_total,
                observed_total=observed_total,
                partial=(
                    observed_total > retained_total
                    or retained_total > len(visible)
                ),
                stale=family in stale_families,
            )
        )
    retained_total = sum(group.retained_total for group in groups)
    observed_total = sum(group.observed_total for group in groups)
    return (
        tuple(groups),
        retained_total,
        observed_total,
        any(group.partial or group.stale for group in groups),
    )


def workflow_focus_projection(
    connection: sqlite3.Connection, session_id: int
) -> WorkflowFocusProjection:
    """Build one deterministic Focus graph without mutating or refreshing data."""
    _positive_integer(session_id, "session_id")
    selected_row = _session_row(connection, session_id)
    if selected_row is None:
        return _empty_projection("missing")
    if (
        selected_row["session_class"] != "work"
        or selected_row["session_role"] != "primary"
        or selected_row["index_policy"] != "full"
    ):
        return _empty_projection("ineligible")

    facts_by_id = _session_facts(connection)
    selected = facts_by_id.get(session_id)
    if selected is None:
        return _empty_projection("ineligible")
    candidates, candidate_observed_total = _ordered_candidates(
        selected, facts_by_id.values()
    )
    classification = [selected, *candidates]
    facts_by_key = {fact.episode.episode_key: fact for fact in classification}
    candidate_ranks = {
        fact.episode.episode_key: index
        for index, fact in enumerate(candidates)
    }
    normalized, priorities = _normalized_relations(classification)
    (
        retained_keys,
        traversed,
        episode_observed_total,
        observed_roots,
        retained_roots,
    ) = (
        _focus_neighborhood(
            selected,
            facts_by_key,
            normalized,
            priorities,
            candidate_ranks,
        )
    )

    retained_relations = tuple(
        relation
        for relation in normalized.relations
        if (
            relation.source_episode_key,
            relation.target_episode_key,
            relation.kind,
        )
        in traversed
    )
    retained_facts = sorted(
        (facts_by_key[key] for key in retained_keys),
        key=lambda fact: (
            _instant_sort_value(fact.instant),
            fact.episode.episode_key,
        ),
    )
    episode_views = []
    for fact in retained_facts:
        groups, retained_evidence, observed_evidence, partial = _evidence_groups(
            connection, fact
        )
        episode_views.append(
            WorkflowEpisodeView(
                episode=fact.episode,
                evidence_groups=groups,
                evidence_retained_total=retained_evidence,
                evidence_observed_total=observed_evidence,
                evidence_partial=partial,
            )
        )

    projection = WorkflowFocusProjection(
        status="ready",
        selected_episode_key=selected.episode.episode_key,
        episodes=tuple(episode_views),
        relations=retained_relations,
        diagnostics=normalized.diagnostics,
        candidate_observed_total=candidate_observed_total,
        candidate_retained_total=len(candidates),
        episode_observed_total=episode_observed_total,
        episode_retained_total=len(episode_views),
        branch_root_observed_total=observed_roots,
        branch_root_retained_total=retained_roots,
    )
    from .workflow_assertions import overlay_workflow_assertions

    return overlay_workflow_assertions(connection, projection)
