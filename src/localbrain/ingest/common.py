import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


EVIDENCE_EXTRACTOR_VERSION = "localbrain.atlassian-evidence.v1"
URL_PATTERN = re.compile(r"https?://[^\s<>'\"`]+", re.IGNORECASE)
APPROVED_ATLASSIAN_TOOL_NAMES = frozenset(
    {
        "atlassian.getAccessibleAtlassianResources",
        "atlassian.searchJiraIssuesUsingJql",
        "atlassian.searchConfluenceUsingCql",
        "atlassian.getConfluencePage",
        "jira__searchIssuesByJql",
        "jira__getProjectDetails",
        "wiki__searchWiki",
        "wiki__getPageById",
        "wiki__getChildPages",
    }
)
APPROVED_GATEWAY_TARGETS = frozenset(
    {
        "jira__searchIssuesByJql",
        "jira__getProjectDetails",
        "wiki__searchWiki",
        "wiki__getPageById",
        "wiki__getChildPages",
    }
)
RESULT_CONTAINER_FIELDS = frozenset(
    {
        "content",
        "data",
        "issue",
        "issues",
        "page",
        "pages",
        "result",
        "results",
        "text",
        "value",
        "values",
    }
)
RESULT_URL_FIELDS = frozenset(
    {"browserurl", "canonicalurl", "link", "self", "url", "weburl"}
)
RESULT_REMOTE_ID_FIELDS = frozenset(
    {"id", "issueid", "pageid", "remoteid"}
)
RESULT_TITLE_FIELDS = frozenset({"name", "summary", "title"})
MAX_RESULT_DEPTH = 8
MAX_RESULT_NODES = 2_000
MAX_RESULT_CANDIDATES = 100
MAX_RESULT_STRING_BYTES = 1_000_000


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
    url_evidence: List[ParsedUrlEvidence] = field(default_factory=list)


def stable_id(*parts: object) -> str:
    value = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token_value(value: Any) -> tuple:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None, "malformed"
    return value, "available"


def read_json_lines(path: Path) -> Iterable[tuple]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                yield line_number, json.loads(raw_line)
            except (json.JSONDecodeError, TypeError):
                yield line_number, None


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    chunks = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"text", "input_text", "output_text"}:
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
    return "\n\n".join(chunks)


def _trim_url(value: str) -> str:
    return value.rstrip(".,;:!?)]}")


def visible_url_evidence(
    text: str,
    *,
    source_line: int,
    source_event_id: Optional[str] = None,
    observed_at: Optional[str] = None,
) -> List[ParsedUrlEvidence]:
    evidence = []
    for ordinal, match in enumerate(URL_PATTERN.finditer(text or ""), start=1):
        observed_url = _trim_url(match.group(0))
        if not observed_url:
            continue
        evidence.append(
            ParsedUrlEvidence(
                observed_url=observed_url,
                source_line=source_line,
                url_ordinal=ordinal,
                source_channel="visible_text",
                source_event_id=source_event_id,
                observed_at=observed_at,
            )
        )
    return evidence


def _normalized_field_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _mapping_value(mapping: Dict[str, Any], fields: frozenset) -> Optional[str]:
    for key, value in mapping.items():
        if _normalized_field_name(key) not in fields:
            continue
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
    return None


def _json_container(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) > MAX_RESULT_STRING_BYTES:
        return None
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return None
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        return None


def approved_atlassian_tool_call(tool_name: Any, arguments: Any = None) -> bool:
    if not isinstance(tool_name, str) or not tool_name.strip():
        return False
    cleaned = tool_name.strip()
    if cleaned in APPROVED_ATLASSIAN_TOOL_NAMES:
        return True
    if any(
        cleaned == target
        or cleaned.endswith("." + target)
        or cleaned.endswith("__" + target)
        for target in APPROVED_GATEWAY_TARGETS
    ):
        return True
    if cleaned not in {
        "mcp_gateway.gateway_dispatch",
        "gateway_dispatch",
        "mcp__mcp_gateway__gateway_dispatch",
    }:
        return False
    parsed_arguments = _json_container(arguments)
    if not isinstance(parsed_arguments, dict):
        return False
    for key in ("capability", "capability_name", "name", "target", "tool"):
        value = parsed_arguments.get(key)
        if isinstance(value, str) and value in APPROVED_GATEWAY_TARGETS:
            return True
    return False


def approved_tool_result_evidence(
    value: Any,
    *,
    source_line: int,
    source_event_id: Optional[str] = None,
    observed_at: Optional[str] = None,
) -> List[ParsedUrlEvidence]:
    root = _json_container(value)
    if root is None:
        return []
    nodes_seen = 0
    raw_candidates = []

    def visit(node: Any, depth: int) -> None:
        nonlocal nodes_seen
        if (
            depth > MAX_RESULT_DEPTH
            or nodes_seen >= MAX_RESULT_NODES
            or len(raw_candidates) >= MAX_RESULT_CANDIDATES
        ):
            return
        nodes_seen += 1
        parsed = _json_container(node)
        if parsed is not node and parsed is not None:
            visit(parsed, depth + 1)
            return
        if isinstance(node, list):
            for child in node[:MAX_RESULT_NODES]:
                visit(child, depth + 1)
            return
        if not isinstance(node, dict):
            return

        remote_id = _mapping_value(node, RESULT_REMOTE_ID_FIELDS)
        title = _mapping_value(node, RESULT_TITLE_FIELDS)
        urls = []
        for key, candidate in node.items():
            if _normalized_field_name(key) not in RESULT_URL_FIELDS:
                continue
            if isinstance(candidate, str):
                urls.extend(_trim_url(match.group(0)) for match in URL_PATTERN.finditer(candidate))
        for url in urls:
            if url:
                raw_candidates.append((url, remote_id, title))
                if len(raw_candidates) >= MAX_RESULT_CANDIDATES:
                    return

        for key, child in node.items():
            if _normalized_field_name(key) not in RESULT_CONTAINER_FIELDS:
                continue
            visit(child, depth + 1)

    visit(root, 0)
    evidence = []
    for ordinal, (url, remote_id, title) in enumerate(raw_candidates, start=1):
        evidence.append(
            ParsedUrlEvidence(
                observed_url=url,
                source_line=source_line,
                url_ordinal=ordinal,
                source_channel="approved_tool_result",
                source_event_id=source_event_id,
                observed_at=observed_at,
                observed_remote_id=(remote_id[:300] if remote_id else None),
                observed_title=(title[:500] if title else None),
            )
        )
    return evidence


def compact_title(text: str, fallback: str, limit: int = 96) -> str:
    line = " ".join(text.split())
    if not line:
        return fallback
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip() + "..."


MAINTENANCE_HEADER_PATTERN = re.compile(
    r"^\s*\[\s*LOCALBRAIN_RUN\s*:\s*(lb-[0-9a-f]{12})\s*\]"
    r"\s*\n\s*\[\s*MODE\s*:\s*maintenance\s*\]",
    re.IGNORECASE,
)


def session_policy(events: List[ParsedEvent]) -> tuple:
    for event in events:
        if event.event_type != "message" or event.role != "user" or not event.text:
            continue
        header = MAINTENANCE_HEADER_PATTERN.match(event.text)
        if header:
            return "maintenance", "metadata_only", header.group(1).lower()
    return "work", "full", None
