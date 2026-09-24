"""Pure validation of proposed Workstream candidates and normalized evidence.

Producers own source resolution and pair discovery. This module owns no source
access, corpus queries, persistence, or user organization.
"""

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from itertools import islice
from typing import Iterable, Mapping, Optional, Tuple

from .activity import parse_timestamp
from .workflow_projection import workflow_episode_key


WORKSTREAM_CANDIDATE_VERSION = "localbrain.workstream-candidate.v1"
ARTIFACT_KINDS = (
    "context-document",
    "wiki-item",
    "jira-item",
    "local-resource",
    "external-resource",
)
REFERENCE_KINDS = frozenset(
    {"user_mention", "assistant_mention", "resource_read", "tool_result"}
)
MAX_ARTIFACTS = 2_000
MAX_SESSIONS = 2_000
MAX_REFERENCES = 20_000
MAX_PAIRS = 200
MAX_MEMBERSHIPS = 2_000
MAX_REFERENCE_SAMPLES = 5
MAX_LATEST_SAMPLES = 5
MAX_OVERLAP_SAMPLES = 20
MAX_IDENTITY_LENGTH = 4_096
MAX_SOURCE_LENGTH = 300
MAX_TITLE_LENGTH = 500


class CandidateLimitError(ValueError):
    """The supplied scope exceeds a hard bound; no prefix is accepted."""


class _ExcludedFact(ValueError):
    pass


def _json_value(value):
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


class _Descriptor:
    def as_dict(self) -> dict:
        return _json_value(asdict(self))


def _text(value: object, field: str, limit: int = MAX_IDENTITY_LENGTH) -> str:
    if not isinstance(value, str):
        raise ValueError("{} must be text".format(field))
    text = value.strip()
    if (
        not text
        or len(text) > limit
        or any(ord(char) < 32 or ord(char) == 127 for char in text)
    ):
        raise ValueError("{} has invalid length or characters".format(field))
    try:
        text.encode("utf-8")
    except UnicodeError:
        raise ValueError("{} has invalid encoding".format(field)) from None
    return text


def _enum(value: object, allowed, field: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError("unsupported {}".format(field))
    return value


def _flag(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError("{} must be boolean".format(field))
    return value


def _title(value: object) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())[:MAX_TITLE_LENGTH]
    if not text:
        return None
    try:
        text.encode("utf-8")
    except UnicodeError:
        return None
    return text


def _digest(prefix: str, *values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return prefix + ":" + digest.hexdigest()


def _revision(prefix: str, value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return _digest(prefix, payload)


def _opaque(value: object, prefix: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(prefix + r":[0-9a-f]{64}", value) is None
    ):
        raise ValueError("invalid {} key".format(prefix))
    return value


def _row(row: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(row, Mapping):
        raise ValueError("normalized fact must be a mapping")
    return row


def _utc_timestamp(value: object) -> Optional[str]:
    try:
        parsed = parse_timestamp(value)
    except (ValueError, OverflowError):
        parsed = None
    return parsed.isoformat(timespec="microseconds") if parsed is not None else None


def candidate_artifact_key(
    kind: object, source_scope: object, source_identity: object
) -> str:
    """Hash an already resolved, canonical source identity, never an alias."""
    return _digest(
        "artifact",
        _enum(kind, ARTIFACT_KINDS, "artifact kind"),
        _text(source_scope, "source_scope", MAX_SOURCE_LENGTH),
        _text(source_identity, "source_identity"),
    )


def workstream_candidate_key(first: object, second: object) -> str:
    anchors = sorted((_opaque(first, "artifact"), _opaque(second, "artifact")))
    if anchors[0] == anchors[1]:
        raise ValueError("candidate requires distinct artifacts")
    return _digest("candidate", WORKSTREAM_CANDIDATE_VERSION, *anchors)


@dataclass(frozen=True)
class CandidateArtifact(_Descriptor):
    artifact_key: str
    kind: str
    source_scope_key: str
    display_title: Optional[str]
    identity_state: str
    enabled: bool
    is_container: bool
    availability: str
    freshness: str


def candidate_artifact_from_record(row: Mapping[str, object]) -> CandidateArtifact:
    row = _row(row)
    kind = _enum(row.get("kind"), ARTIFACT_KINDS, "artifact kind")
    scope = _text(row.get("source_scope"), "source_scope", MAX_SOURCE_LENGTH)
    return CandidateArtifact(
        artifact_key=candidate_artifact_key(kind, scope, row.get("source_identity")),
        kind=kind,
        source_scope_key=_digest("source", kind, scope),
        display_title=_title(row.get("title")),
        identity_state=_enum(
            row.get("identity_state", "unresolved"),
            {"resolved", "unresolved", "ambiguous"},
            "identity state",
        ),
        enabled=_flag(row.get("enabled", False), "enabled"),
        is_container=_flag(row.get("is_container", False), "is_container"),
        availability=_enum(
            row.get("availability", "unknown"),
            {"available", "unavailable", "missing", "unknown"},
            "availability",
        ),
        freshness=_enum(
            row.get("freshness", "unknown"),
            {"current", "stale", "unknown"},
            "freshness",
        ),
    )


@dataclass(frozen=True)
class CandidateSession(_Descriptor):
    episode_key: str
    session_id: int
    source_key: str
    display_title: Optional[str]
    destination: str


def candidate_session_from_record(row: Mapping[str, object]) -> CandidateSession:
    row = _row(row)
    if (
        row.get("session_class") != "work"
        or row.get("session_role") != "primary"
        or row.get("index_policy") != "full"
    ):
        raise _ExcludedFact("ineligible-session")
    count = row.get("event_count", 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("event_count must be a non-negative integer")
    has_events = _flag(row.get("has_activity_events", False), "has_activity_events")
    has_usage = _flag(row.get("has_usage_records", False), "has_usage_records")
    if not (count > 0 or has_events or has_usage):
        raise _ExcludedFact("ineligible-session")
    session_id = row.get("id")
    if (
        isinstance(session_id, bool)
        or not isinstance(session_id, int)
        or session_id <= 0
    ):
        raise ValueError("session_id must be a positive integer")
    source = _text(row.get("source_key"), "source_key", MAX_SOURCE_LENGTH)
    native_id = _text(row.get("external_id"), "external_id")
    return CandidateSession(
        episode_key=workflow_episode_key(source, native_id),
        session_id=session_id,
        source_key=source,
        display_title=_title(row.get("title")),
        destination="/sessions/{}".format(session_id),
    )


@dataclass(frozen=True)
class CandidateReference(_Descriptor):
    reference_key: str
    episode_key: str
    artifact_key: str
    evidence_kind: str
    read_outcome: Optional[str]
    observed_at: Optional[str]
    authority: str = "observed"

    @property
    def supports_membership(self) -> bool:
        if self.evidence_kind in {"user_mention", "assistant_mention"}:
            return self.read_outcome is None
        return self.read_outcome == "success"


def candidate_reference_from_record(row: Mapping[str, object]) -> CandidateReference:
    row = _row(row)
    episode_key = _opaque(row.get("episode_key"), "session")
    artifact_key = _opaque(row.get("artifact_key"), "artifact")
    occurrence = _text(row.get("reference_identity"), "reference_identity")
    outcome = row.get("read_outcome")
    if outcome is not None:
        _enum(outcome, {"success", "failure"}, "read outcome")
    return CandidateReference(
        reference_key=_digest("reference", episode_key, artifact_key, occurrence),
        episode_key=episode_key,
        artifact_key=artifact_key,
        evidence_kind=_enum(
            row.get("evidence_kind"), REFERENCE_KINDS, "evidence kind"
        ),
        read_outcome=outcome,
        observed_at=_utc_timestamp(row.get("observed_at")),
    )


@dataclass(frozen=True)
class CandidateCoverage(_Descriptor):
    complete: bool = False
    unexamined_session_count: Optional[int] = None

    def __post_init__(self):
        _flag(self.complete, "complete")
        count = self.unexamined_session_count
        if count is not None and (
            isinstance(count, bool) or not isinstance(count, int) or count < 0
        ):
            raise ValueError(
                "unexamined_session_count must be non-negative or unknown"
            )
        if self.complete and count != 0:
            raise ValueError("complete coverage requires zero unexamined Sessions")


@dataclass(frozen=True)
class CandidateAnchorSupport(_Descriptor):
    artifact_key: str
    references: Tuple[CandidateReference, ...]
    reference_count: int
    observed_start_at: Optional[str]
    last_observed_at: Optional[str]
    unknown_time_count: int


@dataclass(frozen=True)
class CandidateMembership(_Descriptor):
    session: CandidateSession
    supports: Tuple[CandidateAnchorSupport, ...]
    authority: str = "deterministic-candidate"


@dataclass(frozen=True)
class CandidateOverlap(_Descriptor):
    candidate_key: str
    shared_artifact_count: int
    shared_session_count: int


@dataclass(frozen=True)
class WorkstreamCandidate(_Descriptor):
    candidate_key: str
    anchors: Tuple[CandidateArtifact, ...]
    label: str
    label_authority: str
    label_artifact_key: Optional[str]
    members: Tuple[CandidateMembership, ...]
    membership_revision: str
    observed_start_at: Optional[str]
    last_observed_at: Optional[str]
    latest_observations: Tuple[CandidateReference, ...]
    latest_observation_count: int
    unknown_time_count: int
    overlaps: Tuple[CandidateOverlap, ...] = ()
    overlap_count: int = 0
    authority: str = "deterministic-candidate"
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    activity_state: str = "unknown"
    lifecycle_state: str = "unknown"
    closure_reason: Optional[str] = None
    contract_version: str = WORKSTREAM_CANDIDATE_VERSION


@dataclass(frozen=True)
class CandidateDiagnostic(_Descriptor):
    code: str
    count: int


@dataclass(frozen=True)
class NormalizedWorkstreamCandidates(_Descriptor):
    candidates: Tuple[WorkstreamCandidate, ...]
    diagnostics: Tuple[CandidateDiagnostic, ...]
    coverage: CandidateCoverage
    revision: str
    scope: str = "supplied-facts"
    contract_version: str = WORKSTREAM_CANDIDATE_VERSION


def _bounded_rows(rows: Iterable, limit: int, field: str) -> tuple:
    if isinstance(rows, (str, bytes, Mapping)):
        raise ValueError("{} must be an iterable of facts".format(field))
    try:
        bounded = tuple(islice(iter(rows), limit + 1))
    except TypeError:
        raise ValueError("{} must be an iterable of facts".format(field)) from None
    if len(bounded) > limit:
        raise CandidateLimitError("{} exceeds the supported bound".format(field))
    return bounded


def _unique_facts(rows, factory, key_field: str, kind: str, diagnostics):
    facts = {}
    conflicts = set()
    for row in rows:
        try:
            fact = factory(row)
        except _ExcludedFact:
            diagnostics["ineligible-session"] += 1
            continue
        except (ValueError, TypeError):
            diagnostics["invalid-" + kind] += 1
            continue
        key = getattr(fact, key_field)
        if key in facts and facts[key] != fact:
            conflicts.add(key)
        else:
            facts[key] = fact
    for key in conflicts:
        facts.pop(key, None)
    if conflicts:
        diagnostics["conflicting-" + kind] += len(conflicts)
    return facts


def _ordered_references(references) -> tuple:
    # Stable secondary key also makes ties and unknown timestamps reproducible.
    by_key = sorted(references, key=lambda ref: ref.reference_key)
    return tuple(
        sorted(by_key, key=lambda ref: ref.observed_at or "", reverse=True)
    )


def _bounds(references) -> tuple:
    times = [ref.observed_at for ref in references if ref.observed_at is not None]
    return (min(times) if times else None, max(times) if times else None)


def _candidate(anchors, members, full_evidence) -> WorkstreamCandidate:
    key = workstream_candidate_key(*(anchor.artifact_key for anchor in anchors))
    label_sources = sorted(
        (anchor for anchor in anchors if anchor.display_title),
        key=lambda anchor: (ARTIFACT_KINDS.index(anchor.kind), anchor.artifact_key),
    )
    label_source = label_sources[0] if label_sources else None
    observations = _ordered_references(full_evidence)
    first, last = _bounds(observations)
    latest = tuple(
        ref for ref in observations
        if last is not None and ref.observed_at == last
    )
    return WorkstreamCandidate(
        candidate_key=key,
        anchors=anchors,
        label=label_source.display_title if label_source else "Unnamed work candidate",
        label_authority="source-metadata" if label_source else "fallback",
        label_artifact_key=label_source.artifact_key if label_source else None,
        members=tuple(members),
        membership_revision=_revision(
            "membership",
            {
                "candidate_key": key,
                "references": [
                    ref.as_dict() for ref in sorted(
                        observations, key=lambda ref: ref.reference_key
                    )
                ],
            },
        ),
        observed_start_at=first,
        last_observed_at=last,
        latest_observations=latest[:MAX_LATEST_SAMPLES],
        latest_observation_count=len(latest),
        unknown_time_count=sum(ref.observed_at is None for ref in observations),
    )


def normalize_workstream_candidates(
    artifacts: Iterable[Mapping[str, object]],
    sessions: Iterable[Mapping[str, object]],
    references: Iterable[Mapping[str, object]],
    pairs: Iterable[Tuple[str, str]],
    *,
    coverage: Optional[CandidateCoverage] = None,
) -> NormalizedWorkstreamCandidates:
    """Validate supplied pairs without querying or discovering any source.

    Coverage refers to the producer's supplied scope, not the whole corpus.
    Hard limits fail explicitly; reference and overlap samples retain totals.
    """
    if coverage is None:
        coverage = CandidateCoverage()
    if not isinstance(coverage, CandidateCoverage):
        raise ValueError("coverage must be CandidateCoverage")
    diagnostics = Counter()
    artifact_facts = _unique_facts(
        _bounded_rows(artifacts, MAX_ARTIFACTS, "artifacts"),
        candidate_artifact_from_record, "artifact_key", "artifact", diagnostics,
    )
    session_facts = _unique_facts(
        _bounded_rows(sessions, MAX_SESSIONS, "sessions"),
        candidate_session_from_record, "episode_key", "session", diagnostics,
    )
    reference_facts = _unique_facts(
        _bounded_rows(references, MAX_REFERENCES, "references"),
        candidate_reference_from_record, "reference_key", "reference", diagnostics,
    )
    pair_rows = _bounded_rows(pairs, MAX_PAIRS, "pairs")

    admitted_artifacts = {}
    for key, fact in sorted(artifact_facts.items()):
        if not fact.enabled:
            diagnostics["disabled-artifact"] += 1
        elif fact.identity_state != "resolved":
            diagnostics[fact.identity_state + "-artifact"] += 1
        elif fact.is_container:
            diagnostics["container-artifact"] += 1
        else:
            admitted_artifacts[key] = fact

    supports = defaultdict(lambda: defaultdict(list))
    for ref in reference_facts.values():
        if ref.episode_key not in session_facts:
            diagnostics["missing-session"] += 1
        elif ref.artifact_key not in artifact_facts:
            diagnostics["missing-artifact"] += 1
        elif ref.artifact_key not in admitted_artifacts:
            diagnostics["excluded-reference"] += 1
        elif not ref.supports_membership:
            diagnostics["weak-reference"] += 1
        else:
            supports[ref.episode_key][ref.artifact_key].append(ref)

    unique_pairs = set()
    for pair in pair_rows:
        try:
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise ValueError("invalid pair")
            first, second = sorted(_opaque(key, "artifact") for key in pair)
            if first == second:
                raise ValueError("pair requires distinct anchors")
        except (TypeError, ValueError):
            diagnostics["invalid-pair"] += 1
            continue
        unique_pairs.add((first, second))

    candidates = []
    membership_count = 0
    for pair in sorted(unique_pairs):
        if any(key not in artifact_facts for key in pair):
            diagnostics["missing-pair-anchor"] += 1
            continue
        if any(key not in admitted_artifacts for key in pair):
            diagnostics["excluded-pair"] += 1
            continue
        members = []
        full_evidence = []
        for episode_key in sorted(supports):
            evidence = supports[episode_key]
            if not all(key in evidence for key in pair):
                continue
            anchor_supports = []
            for key in pair:
                ordered = _ordered_references(evidence[key])
                first, last = _bounds(ordered)
                anchor_supports.append(
                    CandidateAnchorSupport(
                        artifact_key=key,
                        references=ordered[:MAX_REFERENCE_SAMPLES],
                        reference_count=len(ordered),
                        observed_start_at=first,
                        last_observed_at=last,
                        unknown_time_count=sum(
                            ref.observed_at is None for ref in ordered
                        ),
                    )
                )
                full_evidence.extend(ordered)
            members.append(
                CandidateMembership(
                    session=session_facts[episode_key],
                    supports=tuple(anchor_supports),
                )
            )
        if len(members) < 2:
            diagnostics["insufficient-sessions"] += 1
            continue
        membership_count += len(members)
        if membership_count > MAX_MEMBERSHIPS:
            raise CandidateLimitError("memberships exceeds the supported bound")
        candidates.append(
            _candidate(
                tuple(admitted_artifacts[key] for key in pair),
                members,
                full_evidence,
            )
        )

    candidates.sort(key=lambda item: item.candidate_key)
    member_keys = {
        item.candidate_key: {member.session.episode_key for member in item.members}
        for item in candidates
    }
    anchor_keys = {
        item.candidate_key: {anchor.artifact_key for anchor in item.anchors}
        for item in candidates
    }
    with_overlap = []
    for candidate in candidates:
        overlaps = []
        for other in candidates:
            if candidate.candidate_key == other.candidate_key:
                continue
            shared_anchors = len(
                anchor_keys[candidate.candidate_key] & anchor_keys[other.candidate_key]
            )
            shared_sessions = len(
                member_keys[candidate.candidate_key] & member_keys[other.candidate_key]
            )
            if shared_anchors or shared_sessions:
                overlaps.append(
                    CandidateOverlap(
                        other.candidate_key, shared_anchors, shared_sessions
                    )
                )
        with_overlap.append(
            replace(
                candidate,
                overlaps=tuple(overlaps[:MAX_OVERLAP_SAMPLES]),
                overlap_count=len(overlaps),
            )
        )

    result = NormalizedWorkstreamCandidates(
        candidates=tuple(with_overlap),
        diagnostics=tuple(
            CandidateDiagnostic(code, count)
            for code, count in sorted(diagnostics.items())
        ),
        coverage=coverage,
        revision="",
    )
    return replace(result, revision=_revision("projection", result.as_dict()))
