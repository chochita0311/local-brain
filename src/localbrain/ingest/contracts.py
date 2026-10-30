"""Lightweight ingestion contracts shared by adapters and their consumers."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


CODEX_SESSION_REVISION = 12
CLAUDE_SESSION_REVISION = 7

CODEX_USAGE_CONTRACT_VERSION = "codex-last-token-usage-v8-official-dated-service-tier"
CLAUDE_USAGE_CONTRACT_VERSION = "claude-message-usage-v3-official-pricing"


class SessionRevisionError(RuntimeError):
    """The current runtime cannot safely replace this source's Session results."""

@dataclass
class ParsedEvent:
    event_id: str
    sequence: int
    source_line: int
    event_type: str
    occurred_at: Optional[str] = None
    role: Optional[str] = None
    text: Optional[str] = None
    tool_name: Optional[str] = None
    message_phase: Optional[str] = None


@dataclass(frozen=True)
class ParsedUrlEvidence:
    observed_url: str
    source_line: int
    url_ordinal: int
    source_channel: str
    source_event_id: Optional[str] = None
    observed_at: Optional[str] = None
    observed_remote_id: Optional[str] = None
    observed_title: Optional[str] = None


@dataclass(frozen=True)
class ParsedReferenceCandidate:
    reference_kind: str
    reference: str
    evidence_kind: str
    source_line: int
    evidence_ordinal: int
    source_event_id: Optional[str] = None
    observed_at: Optional[str] = None
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None
    read_outcome: Optional[str] = None


@dataclass(frozen=True)
class ParsedSkillObservation:
    native_event_id: str
    skill_name: str
    signal_kind: str
    source_line: int
    occurred_at: Optional[str] = None
    skill_locator: Optional[str] = None
    request_key: Optional[str] = None


@dataclass(frozen=True)
class ApprovedResourceCall:
    tool_name: str
    tool_call_id: str
    target_hints: tuple[tuple[str, str], ...]


@dataclass
class ParsedUsageRecord:
    usage_record_id: str
    source_record_id: str
    source_line: int
    occurred_at: Optional[str]
    raw_model: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    cache_write_tokens: Optional[int]
    cache_read_tokens: Optional[int]
    reasoning_tokens: Optional[int]
    source_total_tokens: Optional[int]
    total_tokens: Optional[int]
    total_semantics: str
    aggregation_scope: str = "direct"
    capability_state: str = "complete"
    capability: Dict[str, Any] = field(default_factory=dict)
    normalized_model: Optional[str] = None
    price_snapshot_id: Optional[str] = None


@dataclass
class ParsedSession:
    external_id: str
    source_path: str
    cwd_raw: Optional[str]
    git_branch: Optional[str]
    title: str
    started_at: Optional[str]
    ended_at: Optional[str]
    last_event_at: Optional[str]
    events: List[ParsedEvent]
    skipped_lines: int = 0
    session_class: str = "work"
    index_policy: str = "full"
    maintenance_run_id: Optional[str] = None
    session_role: str = "primary"
    parent_external_id: Optional[str] = None
    usage_records: List[ParsedUsageRecord] = field(default_factory=list)
    skill_observations: List[ParsedSkillObservation] = field(default_factory=list)
    url_evidence: List[ParsedUrlEvidence] = field(default_factory=list)
    reference_candidates: List[ParsedReferenceCandidate] = field(default_factory=list)
