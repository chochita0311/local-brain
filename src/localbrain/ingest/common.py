"""Provider-neutral identity, JSONL, text and Session-classification helpers."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .contracts import ParsedEvent


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


def source_native_event_id(
    record: Dict[str, Any], fallback: str
) -> str:
    for value in (
        record.get("uuid"),
        record.get("id"),
        record.get("event_id"),
        record.get("eventId"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


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
