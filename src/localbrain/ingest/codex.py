from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import (
    ParsedEvent,
    ParsedSession,
    compact_title,
    read_json_lines,
    session_policy,
    stable_id,
)


def parse_codex_session(path: Path) -> ParsedSession:
    external_id = path.stem
    cwd: Optional[str] = None
    first_user_text = ""
    timestamps: List[str] = []
    events: List[ParsedEvent] = []
    skipped_lines = 0
    session_meta_seen = False
    primary_started_at: Optional[str] = None
    git_branch: Optional[str] = None
    session_role = "primary"
    parent_external_id: Optional[str] = None

    for line_number, record in read_json_lines(path):
        if not isinstance(record, dict):
            skipped_lines += 1
            continue

        timestamp = record.get("timestamp")
        if isinstance(timestamp, str):
            timestamps.append(timestamp)
        record_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue

        if record_type == "session_meta":
            if not session_meta_seen:
                external_id = str(
                    payload.get("id") or payload.get("session_id") or external_id
                )
                cwd = payload.get("cwd") or cwd
                git = payload.get("git")
                if isinstance(git, dict):
                    branch = git.get("branch")
                    if isinstance(branch, str) and branch.strip():
                        git_branch = branch.strip()
                source = payload.get("source")
                subagent = source.get("subagent") if isinstance(source, dict) else None
                parent_value = payload.get("parent_thread_id") or payload.get(
                    "forked_from_id"
                )
                if not parent_value and isinstance(subagent, dict):
                    parent_value = (
                        subagent.get("parent_thread_id")
                        or subagent.get("parent_id")
                        or subagent.get("thread_id")
                    )
                if parent_value is not None:
                    value = str(parent_value).strip()
                    parent_external_id = value or None
                source_marks_subsession = bool(
                    subagent not in (None, False, "")
                    or (isinstance(source, str) and source.lower() == "subagent")
                )
                if source_marks_subsession or parent_external_id:
                    session_role = "subsession"
                primary_started_at = timestamp if isinstance(timestamp, str) else None
                session_meta_seen = True
            continue

        if record_type == "turn_context":
            if not cwd:
                cwd = payload.get("cwd") or cwd
            continue

        if record_type == "event_msg":
            payload_type = payload.get("type")
            role = None
            text = None
            if payload_type == "user_message":
                role = "user"
                text = payload.get("message")
            elif payload_type == "agent_message":
                role = "assistant"
                text = payload.get("message")

            if role and isinstance(text, str) and text.strip():
                text = text.strip()
                if role == "user" and not first_user_text:
                    first_user_text = text
                events.append(
                    ParsedEvent(
                        event_id=stable_id("codex", external_id, line_number, role),
                        sequence=line_number * 10,
                        source_line=line_number,
                        event_type="message",
                        occurred_at=timestamp if isinstance(timestamp, str) else None,
                        role=role,
                        text=text,
                    )
                )
            continue

        if record_type == "response_item" and payload.get("type") in {
            "function_call",
            "custom_tool_call",
        }:
            tool_name = payload.get("name")
            if isinstance(tool_name, str):
                events.append(
                    ParsedEvent(
                        event_id=stable_id("codex", external_id, line_number, "tool"),
                        sequence=line_number * 10,
                        source_line=line_number,
                        event_type="tool_call",
                        occurred_at=timestamp if isinstance(timestamp, str) else None,
                        role="assistant",
                        tool_name=tool_name,
                    )
                )

    title = compact_title(first_user_text, path.stem)
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
        started_at=primary_started_at or (min(timestamps) if timestamps else None),
        ended_at=max(timestamps) if timestamps else None,
        last_event_at=max(timestamps) if timestamps else None,
        events=events,
        skipped_lines=skipped_lines,
        session_class=session_class,
        index_policy=index_policy,
        maintenance_run_id=maintenance_run_id,
        session_role=session_role,
        parent_external_id=parent_external_id,
    )
