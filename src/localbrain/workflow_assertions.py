"""Append-only user assertions and deterministic workflow projection overlay."""

import hashlib
import json
import re
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .activity import parse_timestamp
from .workflow_projection import (
    CLOSURE_REASONS,
    WorkflowRelation,
    WorkflowRelationReason,
)


WORKFLOW_ASSERTION_VERSION = "localbrain.workflow-assertion.v1"
WORKFLOW_ASSERTION_OVERLAY_VERSION = "localbrain.workflow-assertion-overlay.v1"

WORKFLOW_ASSERTION_KINDS = frozenset(
    {"same-flow", "split-here", "merge-into", "close", "reopen"}
)
WORKFLOW_BOUNDARY_KINDS = frozenset({"relation", "lifecycle"})
WORKFLOW_ASSERTION_AUTHORITIES = frozenset({"user-confirmed"})
WORKFLOW_RELATION_MEANINGS = frozenset(
    {
        "relation:absent",
        "relation:continues",
        "relation:branches-from",
        "relation:merged-into",
    }
)
WORKFLOW_LIFECYCLE_MEANINGS = frozenset(
    {"lifecycle:unknown", "lifecycle:open", "lifecycle:closed"}
)
WORKFLOW_ASSERTION_MEANINGS = (
    WORKFLOW_RELATION_MEANINGS | WORKFLOW_LIFECYCLE_MEANINGS
)

MAX_WORKFLOW_ASSERTION_NOTE_CODE_POINTS = 1_000
MAX_WORKFLOW_ASSERTION_HISTORY = 100

_EPISODE_KEY_PATTERN = re.compile(r"^session:[0-9a-f]{64}$")
_RELATION_ACTIONS = frozenset({"same-flow", "split-here", "merge-into"})
WORKFLOW_ACTION_AFTER_MEANINGS = {
    "same-flow": "relation:continues",
    "split-here": "relation:branches-from",
    "merge-into": "relation:merged-into",
    "close": "lifecycle:closed",
    "reopen": "lifecycle:open",
}


class WorkflowAssertionError(ValueError):
    """Bounded domain rejection suitable for a local product response."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _reject(code: str, message: str) -> None:
    raise WorkflowAssertionError(code, message)


def _episode_key(value: object, field: str) -> str:
    if not isinstance(value, str):
        _reject("invalid-request", "{} must be an Episode key".format(field))
    normalized = value.strip()
    if not _EPISODE_KEY_PATTERN.fullmatch(normalized):
        _reject("invalid-request", "{} must be a stable Episode key".format(field))
    return normalized


def _positive_optional_integer(value: object, field: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _reject("invalid-request", "{} must be a positive integer".format(field))
    return value


def _normalized_note(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        _reject("invalid-note", "note must be text")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > MAX_WORKFLOW_ASSERTION_NOTE_CODE_POINTS:
        _reject("invalid-note", "note exceeds the supported bound")
    return normalized


def _created_at(value: object = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    parsed = parse_timestamp(value)
    if parsed is None:
        _reject("invalid-created-at", "created_at must be a valid timestamp")
    return parsed.astimezone(timezone.utc).isoformat()


def _length_delimited_digest(parts: Iterable[object]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = str(part).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def workflow_boundary_key(
    boundary_kind: str,
    source_episode_key: object,
    target_episode_key: object = None,
) -> str:
    """Return the stable chain key for one Episode or Episode-pair boundary."""
    if boundary_kind not in WORKFLOW_BOUNDARY_KINDS:
        _reject("invalid-request", "unsupported boundary kind")
    source_key = _episode_key(source_episode_key, "source_episode_key")
    if boundary_kind == "lifecycle":
        if target_episode_key is not None:
            _reject("invalid-request", "lifecycle boundary has no target Episode")
        return _length_delimited_digest((boundary_kind, source_key))
    target_key = _episode_key(target_episode_key, "target_episode_key")
    return _length_delimited_digest((boundary_kind, source_key, target_key))


def _row_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def _active_assertion(
    connection: sqlite3.Connection, boundary_key: str
) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT assertions.*
        FROM workflow_assertions AS assertions
        WHERE assertions.boundary_key = ?
          AND NOT EXISTS (
              SELECT 1
              FROM workflow_assertions AS successor
              WHERE successor.supersedes_assertion_id = assertions.id
          )
        ORDER BY assertions.boundary_version DESC, assertions.id DESC
        LIMIT 1
        """,
        (boundary_key,),
    ).fetchone()
    return _row_dict(row) if row is not None else None


def _active_assertions_for_keys(
    connection: sqlite3.Connection, episode_keys: Sequence[str]
) -> List[dict]:
    if not episode_keys:
        return []
    placeholders = ", ".join("?" for _ in episode_keys)
    rows = connection.execute(
        """
        SELECT assertions.*
        FROM workflow_assertions AS assertions
        WHERE (
            assertions.source_episode_key IN ({placeholders})
            OR assertions.target_episode_key IN ({placeholders})
        )
          AND NOT EXISTS (
              SELECT 1
              FROM workflow_assertions AS successor
              WHERE successor.supersedes_assertion_id = assertions.id
          )
        ORDER BY assertions.created_at, assertions.id
        """.format(placeholders=placeholders),
        tuple(episode_keys) + tuple(episode_keys),
    ).fetchall()
    return [_row_dict(row) for row in rows]


def _assertion_predecessor(
    connection: sqlite3.Connection, assertion: Mapping[str, object]
) -> Optional[dict]:
    predecessor_id = assertion.get("supersedes_assertion_id")
    if predecessor_id is None:
        return None
    predecessor = connection.execute(
        "SELECT * FROM workflow_assertions WHERE id = ?",
        (predecessor_id,),
    ).fetchone()
    if predecessor is None:
        return None
    prior_id = predecessor["supersedes_assertion_id"]
    if prior_id is None:
        return None
    prior = connection.execute(
        "SELECT * FROM workflow_assertions WHERE id = ?",
        (prior_id,),
    ).fetchone()
    return _row_dict(prior) if prior is not None else None


def _base_relations(projection) -> Tuple[WorkflowRelation, ...]:
    if projection.assertion_overlay_version:
        return tuple(projection.base_relations)
    return tuple(projection.relations)


def _base_lifecycle(projection) -> Dict[str, dict]:
    if projection.assertion_overlay_version:
        return {
            str(item["episode_key"]): dict(item)
            for item in projection.base_episode_lifecycle
        }
    return {
        view.episode.episode_key: {
            "episode_key": view.episode.episode_key,
            "lifecycle_state": view.episode.lifecycle_state,
            "closure_reason": view.episode.closure_reason,
            "authority": view.episode.authority,
        }
        for view in projection.episodes
    }


def _base_episode_views(projection, lifecycle_by_key: Mapping[str, Mapping[str, object]]):
    values = []
    for view in projection.episodes:
        base = lifecycle_by_key[view.episode.episode_key]
        episode = replace(
            view.episode,
            lifecycle_state=str(base["lifecycle_state"]),
            closure_reason=base.get("closure_reason"),
            authority=str(base["authority"]),
        )
        values.append(replace(view, episode=episode))
    return tuple(values)


def _episode_map(projection) -> Dict[str, object]:
    return {view.episode.episode_key: view.episode for view in projection.episodes}


def _relation_pair(relation: WorkflowRelation) -> Tuple[str, str]:
    return relation.source_episode_key, relation.target_episode_key


def _relation_kind_from_meaning(meaning: str) -> Optional[str]:
    if meaning == "relation:absent":
        return None
    return meaning.split(":", 1)[1]


def _meaning_for_relation(relation: Optional[WorkflowRelation]) -> str:
    return "relation:{}".format(relation.kind) if relation else "relation:absent"


def _path_exists(
    relations: Iterable[WorkflowRelation], start: str, target: str
) -> bool:
    adjacency: Dict[str, set] = {}
    for relation in relations:
        adjacency.setdefault(relation.source_episode_key, set()).add(
            relation.target_episode_key
        )
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


def _episode_time(episode: object) -> Optional[str]:
    value = episode.observed_start_at or episode.last_observed_at
    parsed = parse_timestamp(value)
    return parsed.isoformat() if parsed is not None else None


def _strictly_forward(source: object, target: object) -> bool:
    source_at = parse_timestamp(_episode_time(source))
    target_at = parse_timestamp(_episode_time(target))
    return bool(source_at is not None and target_at is not None and target_at > source_at)


def _summary(
    assertion: Mapping[str, object],
    *,
    resolution: str,
    resolution_reason: Optional[str] = None,
    base_relation: Optional[WorkflowRelation] = None,
    restored_assertion_id: Optional[int] = None,
) -> dict:
    return {
        "id": int(assertion["id"]),
        "boundary_key": str(assertion["boundary_key"]),
        "boundary_version": int(assertion["boundary_version"]),
        "boundary_kind": str(assertion["boundary_kind"]),
        "assertion_kind": str(assertion["assertion_kind"]),
        "is_undo": bool(assertion["is_undo"]),
        "source_episode_key": str(assertion["source_episode_key"]),
        "target_episode_key": assertion["target_episode_key"],
        "before_meaning": str(assertion["before_meaning"]),
        "after_meaning": str(assertion["after_meaning"]),
        "before_closure_reason": assertion["before_closure_reason"],
        "after_closure_reason": assertion["after_closure_reason"],
        "note": assertion["note"],
        "authority": str(assertion["authority"]),
        "contract_version": str(assertion["contract_version"]),
        "supersedes_assertion_id": assertion["supersedes_assertion_id"],
        "created_at": str(assertion["created_at"]),
        "resolution": resolution,
        "resolution_reason": resolution_reason,
        "base_relation": base_relation.as_dict() if base_relation else None,
        "restored_assertion_id": restored_assertion_id,
    }


def _revision(
    projection,
    base_relations: Sequence[WorkflowRelation],
    assertions: Sequence[Mapping[str, object]],
) -> str:
    material = {
        "selected_episode_key": projection.selected_episode_key,
        "episodes": [
            {
                "episode_key": view.episode.episode_key,
                "observed_start_at": view.episode.observed_start_at,
                "last_observed_at": view.episode.last_observed_at,
            }
            for view in projection.episodes
        ],
        "base_relations": [relation.as_dict() for relation in base_relations],
        "assertions": [
            {
                key: item.get(key)
                for key in (
                    "id",
                    "boundary_key",
                    "boundary_version",
                    "source_episode_key",
                    "target_episode_key",
                    "after_meaning",
                    "after_closure_reason",
                    "resolution",
                )
            }
            for item in assertions
        ],
    }
    serialized = json.dumps(
        material, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return "workflow-revision:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def overlay_workflow_assertions(connection: sqlite3.Connection, projection):
    """Apply active user assertions after the deterministic Focus projection."""
    if projection.status != "ready":
        return projection

    base_relations = _base_relations(projection)
    base_lifecycle = _base_lifecycle(projection)
    base_views = _base_episode_views(projection, base_lifecycle)
    base_projection = replace(projection, episodes=base_views, relations=base_relations)
    episodes = _episode_map(base_projection)
    active = _active_assertions_for_keys(connection, tuple(sorted(episodes)))

    effective_by_pair = {_relation_pair(item): item for item in base_relations}
    summaries: List[dict] = []
    diagnostics: List[dict] = []
    lifecycle_assertions: Dict[str, Tuple[Mapping[str, object], Optional[dict]]] = {}

    for assertion in active:
        source_key = str(assertion["source_episode_key"])
        target_key = assertion["target_episode_key"]
        restored = (
            _assertion_predecessor(connection, assertion)
            if bool(assertion["is_undo"])
            else None
        )
        restored_id = int(restored["id"]) if restored is not None else None

        if assertion["boundary_kind"] == "lifecycle":
            if source_key not in episodes:
                reason = "missing-source-episode"
                summaries.append(
                    _summary(
                        assertion,
                        resolution="unresolved",
                        resolution_reason=reason,
                        restored_assertion_id=restored_id,
                    )
                )
                diagnostics.append(
                    {"code": reason, "assertion_id": int(assertion["id"])}
                )
                continue
            lifecycle_assertions[source_key] = (assertion, restored)
            summaries.append(
                _summary(
                    assertion,
                    resolution="applied",
                    restored_assertion_id=restored_id,
                )
            )
            continue

        pair = (source_key, str(target_key or ""))
        base_relation = next(
            (item for item in base_relations if _relation_pair(item) == pair),
            None,
        )
        source = episodes.get(pair[0])
        target = episodes.get(pair[1])
        if source is None or target is None:
            reason = "missing-endpoint"
        elif not _strictly_forward(source, target):
            reason = "endpoint-time-order"
        else:
            proposed_kind = _relation_kind_from_meaning(
                str(assertion["after_meaning"])
            )
            other_relations = [
                relation
                for key, relation in effective_by_pair.items()
                if key != pair
            ]
            if proposed_kind and _path_exists(
                other_relations, pair[1], pair[0]
            ):
                reason = "cycle"
            elif proposed_kind in {"continues", "branches-from"} and any(
                relation.target_episode_key == pair[1]
                and relation.source_episode_key != pair[0]
                and relation.kind in {"continues", "branches-from"}
                for relation in other_relations
            ):
                reason = "contradictory-incoming-boundary"
            else:
                reason = None

        if reason is not None:
            summaries.append(
                _summary(
                    assertion,
                    resolution="unresolved",
                    resolution_reason=reason,
                    base_relation=base_relation,
                    restored_assertion_id=restored_id,
                )
            )
            diagnostics.append(
                {"code": reason, "assertion_id": int(assertion["id"])}
            )
            continue

        effective_by_pair.pop(pair, None)
        kind = _relation_kind_from_meaning(str(assertion["after_meaning"]))
        restore_base = bool(assertion["is_undo"]) and restored is None
        if kind is not None:
            if restore_base and base_relation is not None and base_relation.kind == kind:
                effective_by_pair[pair] = base_relation
            else:
                effective_by_pair[pair] = WorkflowRelation(
                    source_episode_key=pair[0],
                    target_episode_key=pair[1],
                    kind=kind,
                    authority="user-confirmed",
                    reasons=(
                        WorkflowRelationReason(
                            kind="user-assertion",
                            identity="assertion:{}".format(int(assertion["id"])),
                            observed_at=str(assertion["created_at"]),
                        ),
                    ),
                    source_observed_at=_episode_time(source),
                    target_observed_at=_episode_time(target),
                )
        summaries.append(
            _summary(
                assertion,
                resolution="applied",
                base_relation=base_relation,
                restored_assertion_id=restored_id,
            )
        )

    effective_views = []
    for view in base_views:
        episode = view.episode
        active_lifecycle = lifecycle_assertions.get(episode.episode_key)
        if active_lifecycle is not None:
            assertion, restored = active_lifecycle
            state = str(assertion["after_meaning"]).split(":", 1)[1]
            restore_base = bool(assertion["is_undo"]) and restored is None
            episode = replace(
                episode,
                lifecycle_state=state,
                closure_reason=assertion["after_closure_reason"],
                authority=(episode.authority if restore_base else "user-confirmed"),
            )
        effective_views.append(replace(view, episode=episode))

    effective_relations = tuple(
        sorted(
            effective_by_pair.values(),
            key=lambda item: (
                item.source_observed_at or "",
                item.target_observed_at or "",
                item.source_episode_key,
                item.target_episode_key,
                item.kind,
            ),
        )
    )
    assertion_summaries = tuple(
        sorted(
            summaries,
            key=lambda item: (
                item["created_at"], item["id"]
            ),
        )
    )
    return replace(
        projection,
        episodes=tuple(effective_views),
        relations=effective_relations,
        base_relations=base_relations,
        base_episode_lifecycle=tuple(
            base_lifecycle[key] for key in sorted(base_lifecycle)
        ),
        assertions=assertion_summaries,
        assertion_diagnostics=tuple(diagnostics),
        assertion_revision=_revision(
            base_projection, base_relations, assertion_summaries
        ),
        assertion_overlay_version=WORKFLOW_ASSERTION_OVERLAY_VERSION,
    )


def _projection_episode(projection, episode_key: str):
    for view in projection.episodes:
        if view.episode.episode_key == episode_key:
            return view.episode
    return None


def _effective_relation(projection, source_key: str, target_key: str):
    return next(
        (
            relation
            for relation in projection.relations
            if relation.source_episode_key == source_key
            and relation.target_episode_key == target_key
        ),
        None,
    )


def _current_projection(
    connection: sqlite3.Connection, projection, expected_revision: object
):
    if not isinstance(expected_revision, str) or not expected_revision:
        _reject("conflict", "current projection revision is required")
    current = overlay_workflow_assertions(connection, projection)
    if current.assertion_revision != expected_revision:
        _reject("conflict", "workflow projection changed")
    return current


def _assert_expected_active(
    active: Optional[Mapping[str, object]], expected_active_assertion_id: object
) -> None:
    expected = _positive_optional_integer(
        expected_active_assertion_id, "expected_active_assertion_id"
    )
    active_id = int(active["id"]) if active is not None else None
    if expected != active_id:
        _reject("conflict", "workflow assertion boundary changed")


def _savepoint(connection: sqlite3.Connection, name: str):
    connection.execute("SAVEPOINT {}".format(name))


def _rollback_savepoint(connection: sqlite3.Connection, name: str):
    connection.execute("ROLLBACK TO SAVEPOINT {}".format(name))
    connection.execute("RELEASE SAVEPOINT {}".format(name))


def _release_savepoint(connection: sqlite3.Connection, name: str):
    connection.execute("RELEASE SAVEPOINT {}".format(name))


def _is_assertion_write_conflict(error: sqlite3.IntegrityError) -> bool:
    message = str(error)
    return any(
        constraint in message
        for constraint in (
            "workflow_assertions.boundary_key, workflow_assertions.boundary_version",
            "workflow_assertions.supersedes_assertion_id",
        )
    )


def _insert_assertion(
    connection: sqlite3.Connection,
    *,
    boundary_key: str,
    boundary_kind: str,
    assertion_kind: str,
    is_undo: bool,
    source_episode_key: str,
    target_episode_key: Optional[str],
    source_session_id: Optional[int],
    target_session_id: Optional[int],
    before_meaning: str,
    after_meaning: str,
    before_closure_reason: Optional[str],
    after_closure_reason: Optional[str],
    note: Optional[str],
    supersedes_assertion_id: Optional[int],
    created_at: str,
) -> int:
    version_row = connection.execute(
        """
        SELECT COALESCE(MAX(boundary_version), 0) + 1
        FROM workflow_assertions
        WHERE boundary_key = ?
        """,
        (boundary_key,),
    ).fetchone()
    boundary_version = int(version_row[0])
    cursor = connection.execute(
        """
        INSERT INTO workflow_assertions(
            boundary_key, boundary_version, boundary_kind, assertion_kind,
            is_undo, source_episode_key, target_episode_key,
            source_session_id, target_session_id, before_meaning,
            after_meaning, before_closure_reason, after_closure_reason, note,
            authority, contract_version, supersedes_assertion_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  'user-confirmed', ?, ?, ?)
        """,
        (
            boundary_key,
            boundary_version,
            boundary_kind,
            assertion_kind,
            int(is_undo),
            source_episode_key,
            target_episode_key,
            source_session_id,
            target_session_id,
            before_meaning,
            after_meaning,
            before_closure_reason,
            after_closure_reason,
            note,
            WORKFLOW_ASSERTION_VERSION,
            supersedes_assertion_id,
            created_at,
        ),
    )
    return int(cursor.lastrowid)


def apply_workflow_assertion(
    connection: sqlite3.Connection,
    projection,
    *,
    assertion_kind: object,
    source_episode_key: object,
    target_episode_key: object = None,
    close_reason: object = None,
    note: object = None,
    expected_active_assertion_id: object = None,
    expected_revision: object,
    created_at: object = None,
) -> dict:
    """Append one validated user assertion without committing the outer transaction."""
    if projection.status != "ready":
        _reject("invalid-projection", "workflow projection must be ready")
    projection = _current_projection(connection, projection, expected_revision)
    if assertion_kind not in WORKFLOW_ASSERTION_KINDS:
        _reject("invalid-action", "unsupported workflow assertion")

    source_key = _episode_key(source_episode_key, "source_episode_key")
    source = _projection_episode(projection, source_key)
    if source is None:
        _reject("missing-endpoint", "source Episode is not in the projection")
    normalized_note = _normalized_note(note)
    normalized_created_at = _created_at(created_at)

    if assertion_kind in _RELATION_ACTIONS:
        target_key = _episode_key(target_episode_key, "target_episode_key")
        target = _projection_episode(projection, target_key)
        if target is None:
            _reject("missing-endpoint", "target Episode is not in the projection")
        if source_key == target_key:
            _reject("self-relation", "workflow relation cannot target itself")
        if not _strictly_forward(source, target):
            code = (
                "merge-before-source"
                if assertion_kind == "merge-into"
                else "non-forward-time"
            )
            _reject(code, "workflow relation must move forward in observed time")
        boundary_kind = "relation"
        boundary_key = workflow_boundary_key(
            boundary_kind, source_key, target_key
        )
        active = _active_assertion(connection, boundary_key)
        current = _effective_relation(projection, source_key, target_key)
        before_meaning = _meaning_for_relation(current)
        after_meaning = WORKFLOW_ACTION_AFTER_MEANINGS[str(assertion_kind)]
        before_closure_reason = None
        after_closure_reason = None
        if assertion_kind == "split-here" and before_meaning != "relation:continues":
            _reject("requires-continues", "split requires a continues boundary")

        if (
            active is not None
            and active["after_meaning"] == after_meaning
            and active["after_closure_reason"] is None
        ):
            _reject("duplicate-active", "the same assertion is already active")
        _assert_expected_active(active, expected_active_assertion_id)

        other_relations = [
            relation
            for relation in projection.relations
            if not (
                relation.source_episode_key == source_key
                and relation.target_episode_key == target_key
            )
        ]
        if _path_exists(other_relations, target_key, source_key):
            _reject("cycle", "workflow assertion would create a cycle")
        proposed_kind = _relation_kind_from_meaning(after_meaning)
        if proposed_kind in {"continues", "branches-from"} and any(
            relation.target_episode_key == target_key
            and relation.source_episode_key != source_key
            and relation.kind in {"continues", "branches-from"}
            for relation in other_relations
        ):
            _reject(
                "contradictory-boundary",
                "target Episode already has an active incoming boundary",
            )
        target_session_id = target.session_id
    else:
        if target_episode_key is not None:
            _reject("invalid-request", "lifecycle assertion has no target Episode")
        target_key = None
        target = None
        boundary_kind = "lifecycle"
        boundary_key = workflow_boundary_key(boundary_kind, source_key)
        active = _active_assertion(connection, boundary_key)
        before_meaning = "lifecycle:{}".format(source.lifecycle_state)
        before_closure_reason = source.closure_reason
        after_meaning = WORKFLOW_ACTION_AFTER_MEANINGS[str(assertion_kind)]
        target_session_id = None

        if assertion_kind == "close":
            if close_reason not in CLOSURE_REASONS:
                _reject("invalid-close-reason", "close requires a supported reason")
            if any(
                relation.source_episode_key == source_key
                for relation in projection.relations
            ):
                _reject("not-tip", "only a current workflow tip can be closed")
            after_closure_reason = str(close_reason)
        else:
            if close_reason is not None:
                _reject("invalid-close-reason", "reopen does not accept a reason")
            if active is None or active["after_meaning"] != "lifecycle:closed":
                _reject("requires-active-closure", "reopen requires an active closure")
            after_closure_reason = None

        if (
            active is not None
            and active["after_meaning"] == after_meaning
            and active["after_closure_reason"] == after_closure_reason
        ):
            _reject("duplicate-active", "the same assertion is already active")
        _assert_expected_active(active, expected_active_assertion_id)

    savepoint = "workflow_assertion_apply"
    _savepoint(connection, savepoint)
    try:
        assertion_id = _insert_assertion(
            connection,
            boundary_key=boundary_key,
            boundary_kind=boundary_kind,
            assertion_kind=str(assertion_kind),
            is_undo=False,
            source_episode_key=source_key,
            target_episode_key=target_key,
            source_session_id=source.session_id,
            target_session_id=target_session_id,
            before_meaning=before_meaning,
            after_meaning=after_meaning,
            before_closure_reason=before_closure_reason,
            after_closure_reason=after_closure_reason,
            note=normalized_note,
            supersedes_assertion_id=(int(active["id"]) if active else None),
            created_at=normalized_created_at,
        )
        effective = overlay_workflow_assertions(connection, projection)
    except sqlite3.IntegrityError as error:
        _rollback_savepoint(connection, savepoint)
        if _is_assertion_write_conflict(error):
            _reject("conflict", "workflow assertion boundary changed")
        raise
    except Exception:
        _rollback_savepoint(connection, savepoint)
        raise
    _release_savepoint(connection, savepoint)
    row = connection.execute(
        "SELECT * FROM workflow_assertions WHERE id = ?", (assertion_id,)
    ).fetchone()
    return {"assertion": _row_dict(row), "projection": effective}


def undo_workflow_assertion(
    connection: sqlite3.Connection,
    projection,
    *,
    assertion_id: object,
    expected_revision: object,
    created_at: object = None,
) -> dict:
    """Append a reversal for the selected current assertion."""
    if projection.status != "ready":
        _reject("invalid-projection", "workflow projection must be ready")
    projection = _current_projection(connection, projection, expected_revision)
    normalized_id = _positive_optional_integer(assertion_id, "assertion_id")
    row = connection.execute(
        "SELECT * FROM workflow_assertions WHERE id = ?", (normalized_id,)
    ).fetchone()
    if row is None:
        _reject("assertion-not-found", "workflow assertion does not exist")
    active = _row_dict(row)
    current = _active_assertion(connection, str(active["boundary_key"]))
    if current is None or int(current["id"]) != normalized_id:
        _reject("assertion-not-active", "only the current assertion can be undone")

    source_key = str(active["source_episode_key"])
    target_key = active["target_episode_key"]
    source = _projection_episode(projection, source_key)
    target = (
        _projection_episode(projection, str(target_key))
        if target_key is not None
        else None
    )
    if source is None or (active["boundary_kind"] == "relation" and target is None):
        _reject("missing-endpoint", "assertion endpoint is not in the projection")

    savepoint = "workflow_assertion_undo"
    _savepoint(connection, savepoint)
    try:
        reversal_id = _insert_assertion(
            connection,
            boundary_key=str(active["boundary_key"]),
            boundary_kind=str(active["boundary_kind"]),
            assertion_kind=str(active["assertion_kind"]),
            is_undo=True,
            source_episode_key=source_key,
            target_episode_key=target_key,
            source_session_id=source.session_id,
            target_session_id=(target.session_id if target is not None else None),
            before_meaning=str(active["after_meaning"]),
            after_meaning=str(active["before_meaning"]),
            before_closure_reason=active["after_closure_reason"],
            after_closure_reason=active["before_closure_reason"],
            note=None,
            supersedes_assertion_id=normalized_id,
            created_at=_created_at(created_at),
        )
        effective = overlay_workflow_assertions(connection, projection)
    except sqlite3.IntegrityError as error:
        _rollback_savepoint(connection, savepoint)
        if _is_assertion_write_conflict(error):
            _reject("conflict", "workflow assertion boundary changed")
        raise
    except Exception:
        _rollback_savepoint(connection, savepoint)
        raise
    _release_savepoint(connection, savepoint)
    reversal = connection.execute(
        "SELECT * FROM workflow_assertions WHERE id = ?", (reversal_id,)
    ).fetchone()
    return {"assertion": _row_dict(reversal), "projection": effective}


def workflow_assertion_history(
    connection: sqlite3.Connection,
    boundary_key: object,
    *,
    limit: int = MAX_WORKFLOW_ASSERTION_HISTORY,
) -> dict:
    """Return the newest bounded chain in chronological order."""
    if not isinstance(boundary_key, str) or not re.fullmatch(
        r"[0-9a-f]{64}", boundary_key
    ):
        _reject("invalid-request", "boundary_key must be a stable digest")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        _reject("invalid-request", "history limit must be between 1 and 100")
    total = int(
        connection.execute(
            "SELECT COUNT(*) FROM workflow_assertions WHERE boundary_key = ?",
            (boundary_key,),
        ).fetchone()[0]
    )
    rows = connection.execute(
        """
        SELECT assertions.*,
               NOT EXISTS (
                   SELECT 1 FROM workflow_assertions AS successor
                   WHERE successor.supersedes_assertion_id = assertions.id
               ) AS is_active
        FROM workflow_assertions AS assertions
        WHERE assertions.boundary_key = ?
        ORDER BY assertions.boundary_version DESC, assertions.id DESC
        LIMIT ?
        """,
        (boundary_key, limit),
    ).fetchall()
    values = [_row_dict(row) for row in reversed(rows)]
    active_id = next(
        (int(item["id"]) for item in values if bool(item["is_active"])), None
    )
    return {
        "boundary_key": boundary_key,
        "assertions": values,
        "observed_total": total,
        "retained_total": len(values),
        "partial": total > len(values),
        "active_assertion_id": active_id,
        "contract_version": WORKFLOW_ASSERTION_VERSION,
    }
