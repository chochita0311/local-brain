from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import (
    ParsedEvent,
    ParsedSession,
    compact_title,
    read_json_lines,
    session_policy,
    stable_id,
    text_from_content,
)


def _message_content(record: Dict[str, Any]) -> Any:
    message = record.get("message")
    if isinstance(message, dict):
        return message.get("content")
    return message


def parse_claude_session(path: Path) -> ParsedSession:
    external_id = path.stem
    cwd: Optional[str] = None
    git_branch: Optional[str] = None
    explicit_title: Optional[str] = None
    first_user_text = ""
    timestamps: List[str] = []
    events: List[ParsedEvent] = []
    skipped_lines = 0
    is_subsession = path.parent.name == "subagents"
    parent_external_id = path.parent.parent.name if is_subsession else None

    for line_number, record in read_json_lines(path):
        if not isinstance(record, dict):
            skipped_lines += 1
            continue

        if not is_subsession:
            external_id = str(record.get("sessionId") or external_id)
        cwd = record.get("cwd") or cwd
        branch = record.get("gitBranch")
        if isinstance(branch, str) and branch.strip():
            git_branch = branch.strip()
        timestamp = record.get("timestamp")
        if isinstance(timestamp, str):
            timestamps.append(timestamp)

        record_type = record.get("type")
        if record_type == "ai-title" and isinstance(record.get("aiTitle"), str):
            explicit_title = record["aiTitle"].strip()
            continue
        if record_type == "last-prompt" and not explicit_title:
            value = record.get("lastPrompt")
            if isinstance(value, str) and value.strip():
                explicit_title = compact_title(value, path.stem)
            continue

        if record_type not in {"user", "assistant"}:
            continue
        if record.get("isMeta"):
            continue

        is_tool_result = bool(record.get("sourceToolAssistantUUID")) or (
            "toolUseResult" in record
        )
        if record_type == "user" and is_tool_result:
            continue

        text = text_from_content(_message_content(record))
        if text:
            if record_type == "user" and not first_user_text:
                first_user_text = text
            events.append(
                ParsedEvent(
                    event_id=stable_id("claude", external_id, line_number, record_type),
                    sequence=line_number * 10,
                    source_line=line_number,
                    event_type="message",
                    occurred_at=timestamp if isinstance(timestamp, str) else None,
                    role=record_type,
                    text=text,
                )
            )

        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if record_type == "assistant" and isinstance(content, list):
            for offset, item in enumerate(content, start=1):
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name")
                    if isinstance(tool_name, str):
                        events.append(
                            ParsedEvent(
                                event_id=stable_id(
                                    "claude", external_id, line_number, "tool", offset
                                ),
                                sequence=line_number * 10 + offset,
                                source_line=line_number,
                                event_type="tool_call",
                                occurred_at=(
                                    timestamp if isinstance(timestamp, str) else None
                                ),
                                role="assistant",
                                tool_name=tool_name,
                            )
                        )

    fallback = Path(cwd).name if cwd else path.parent.name.strip("-") or path.stem
    title = compact_title(explicit_title or first_user_text, fallback)
    session_class, index_policy, maintenance_run_id = session_policy(events)
    if session_class == "maintenance":
        title = "LocalBrain maintenance" + (
            " · " + maintenance_run_id if maintenance_run_id else ""
        )
    return ParsedSession(
        external_id=external_id,
        source_path=str(path),
        cwd_raw=cwd,
        git_branch=git_branch,
        title=title,
        started_at=min(timestamps) if timestamps else None,
        ended_at=max(timestamps) if timestamps else None,
        last_event_at=max(timestamps) if timestamps else None,
        events=events,
        skipped_lines=skipped_lines,
        session_class=session_class,
        index_policy=index_policy,
        maintenance_run_id=maintenance_run_id,
        session_role="subsession" if is_subsession else "primary",
        parent_external_id=parent_external_id,
    )
