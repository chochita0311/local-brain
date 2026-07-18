import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


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
    metadata: Dict[str, Any] = field(default_factory=dict)


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


def stable_id(*parts: object) -> str:
    value = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
