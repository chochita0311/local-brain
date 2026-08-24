from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import (
    ApprovedResourceCall,
    ParsedEvent,
    ParsedSession,
    ParsedUsageRecord,
    approved_resource_call,
    approved_result_reference_candidates,
    approved_tool_result_evidence,
    compact_title,
    read_json_lines,
    session_policy,
    stable_id,
    source_native_event_id,
    text_from_content,
    token_value,
    tool_result_failed,
    tool_result_completed,
    visible_reference_candidates,
    visible_url_evidence,
)


CLAUDE_USAGE_CONTRACT_VERSION = "claude-message-usage-v2-source-repair"
CLAUDE_SESSION_CONTRACT_VERSION = "claude-session-v1"


def _message_content(record: Dict[str, Any]) -> Any:
    message = record.get("message")
    if isinstance(message, dict):
        return message.get("content")
    return message


def _claude_usage_record(
    external_id: str,
    line_number: int,
    timestamp: Optional[str],
    record: Dict[str, Any],
) -> Optional[ParsedUsageRecord]:
    message = record.get("message")
    if not isinstance(message, dict):
        return None
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None

    raw_model = message.get("model")
    if not isinstance(raw_model, str) or not raw_model.strip():
        raw_model = None
    else:
        raw_model = raw_model.strip()

    component_states: Dict[str, str] = {}
    malformed = False

    def required(name: str) -> Optional[int]:
        nonlocal malformed
        if name not in usage:
            component_states[name] = "missing"
            return None
        value, state = token_value(usage.get(name))
        component_states[name] = state
        malformed = malformed or state == "malformed"
        return value

    input_tokens = required("input_tokens")
    output_tokens = required("output_tokens")

    cache_write_source = usage.get("cache_creation_input_tokens")
    cache_creation = usage.get("cache_creation")
    nested_cache_write = None
    if isinstance(cache_creation, dict):
        cache_values = [
            cache_creation.get("ephemeral_1h_input_tokens", 0),
            cache_creation.get("ephemeral_5m_input_tokens", 0),
        ]
        if all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in cache_values
        ):
            nested_cache_write = sum(cache_values)
        else:
            nested_cache_write = "malformed"
    if cache_write_source is None:
        cache_write_source = 0 if nested_cache_write is None else nested_cache_write
        component_states["cache_write_source"] = (
            "nested_breakdown" if nested_cache_write is not None else "default_zero"
        )
    elif (
        cache_write_source == 0
        and isinstance(nested_cache_write, int)
        and nested_cache_write > 0
    ):
        cache_write_source = nested_cache_write
        component_states["cache_write_source"] = "nested_preferred_over_zero_aggregate"
    elif (
        isinstance(cache_write_source, int)
        and isinstance(nested_cache_write, int)
        and cache_write_source != nested_cache_write
    ):
        component_states["cache_write_source"] = "aggregate_breakdown_mismatch"
    else:
        component_states["cache_write_source"] = "aggregate"
    cache_write_tokens, cache_write_state = token_value(cache_write_source)
    component_states["cache_write_tokens"] = cache_write_state
    malformed = malformed or cache_write_state == "malformed"

    cache_read_source = usage.get("cache_read_input_tokens", 0)
    cache_read_tokens, cache_read_state = token_value(cache_read_source)
    component_states["cache_read_tokens"] = cache_read_state
    malformed = malformed or cache_read_state == "malformed"

    source_total_tokens = None
    if "total_tokens" in usage:
        source_total_tokens, total_state = token_value(usage.get("total_tokens"))
        component_states["source_total_tokens"] = total_state
        malformed = malformed or total_state == "malformed"
    else:
        component_states["source_total_tokens"] = "not_reported"

    total_tokens = None
    if None not in (
        input_tokens,
        output_tokens,
        cache_write_tokens,
        cache_read_tokens,
    ):
        total_tokens = (
            input_tokens
            + output_tokens
            + cache_write_tokens
            + cache_read_tokens
        )

    model_state = "available" if raw_model else "missing"
    component_states["model"] = model_state
    component_states["reasoning_tokens"] = "not_separately_reported"
    if malformed:
        capability_state = "malformed"
    elif raw_model is None or input_tokens is None or output_tokens is None:
        capability_state = "partial"
    else:
        capability_state = "complete"

    record_identity = (
        message.get("id")
        or record.get("uuid")
        or stable_id("claude-usage-line", external_id, line_number)
    )
    source_record_id = str(record_identity)
    return ParsedUsageRecord(
        usage_record_id=stable_id("claude-usage", external_id, source_record_id),
        source_record_id=source_record_id,
        source_line=line_number,
        occurred_at=timestamp,
        raw_model=raw_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_write_tokens=cache_write_tokens,
        cache_read_tokens=cache_read_tokens,
        reasoning_tokens=None,
        source_total_tokens=source_total_tokens,
        total_tokens=total_tokens,
        total_semantics=(
            "normalized_non_cached_input_plus_output_plus_cache_write_plus_cache_read;"
            "reasoning_not_separately_reported"
        ),
        capability_state=capability_state,
        capability=component_states,
    )


def parse_claude_session(path: Path) -> ParsedSession:
    external_id = path.stem
    cwd: Optional[str] = None
    git_branch: Optional[str] = None
    explicit_title: Optional[str] = None
    first_user_text = ""
    timestamps: List[str] = []
    events: List[ParsedEvent] = []
    usage_by_record: Dict[str, ParsedUsageRecord] = {}
    url_evidence = []
    reference_candidates = []
    approved_tool_calls: Dict[str, ApprovedResourceCall] = {}
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

        message_content = _message_content(record)
        is_tool_result = (
            bool(record.get("sourceToolAssistantUUID"))
            or "toolUseResult" in record
            or (
                isinstance(message_content, list)
                and any(
                    isinstance(item, dict) and item.get("type") == "tool_result"
                    for item in message_content
                )
            )
        )
        if record_type == "user" and is_tool_result:
            content = message_content
            items = content if isinstance(content, list) else []
            for offset, item in enumerate(items, start=1):
                if not isinstance(item, dict) or item.get("type") != "tool_result":
                    continue
                tool_use_id = item.get("tool_use_id")
                call = approved_tool_calls.get(tool_use_id)
                if not isinstance(tool_use_id, str) or call is None:
                    continue
                result_event_id = source_native_event_id(
                    record,
                    stable_id(
                        "claude",
                        external_id,
                        line_number,
                        "approved-tool-result",
                        offset,
                    ),
                )
                failed = tool_result_failed(item, record.get("toolUseResult"))
                completed = tool_result_completed(item.get("content"))
                if not failed and completed:
                    url_evidence.extend(
                        approved_tool_result_evidence(
                            item.get("content"),
                            source_line=line_number,
                            source_event_id=result_event_id,
                            observed_at=(
                                timestamp if isinstance(timestamp, str) else None
                            ),
                        )
                    )
                if failed or completed:
                    reference_candidates.extend(
                        approved_result_reference_candidates(
                            call,
                            item.get("content"),
                            source_line=line_number,
                            source_event_id=result_event_id,
                            observed_at=(
                                timestamp if isinstance(timestamp, str) else None
                            ),
                            failed=failed,
                        )
                    )
            continue

        text = text_from_content(_message_content(record))
        if text:
            if record_type == "user" and not first_user_text:
                first_user_text = text
            event_id = stable_id("claude", external_id, line_number, record_type)
            events.append(
                ParsedEvent(
                    event_id=event_id,
                    sequence=line_number * 10,
                    source_line=line_number,
                    event_type="message",
                    occurred_at=timestamp if isinstance(timestamp, str) else None,
                    role=record_type,
                    text=text,
                )
            )
            url_evidence.extend(
                visible_url_evidence(
                    text,
                    source_line=line_number,
                    source_event_id=event_id,
                    observed_at=timestamp if isinstance(timestamp, str) else None,
                )
            )
            reference_candidates.extend(
                visible_reference_candidates(
                    text,
                    role=record_type,
                    source_line=line_number,
                    source_event_id=source_native_event_id(record, event_id),
                    observed_at=timestamp if isinstance(timestamp, str) else None,
                )
            )

        message = record.get("message")
        if record_type == "assistant":
            usage_record = _claude_usage_record(
                external_id,
                line_number,
                timestamp if isinstance(timestamp, str) else None,
                record,
            )
            if usage_record:
                previous = usage_by_record.get(usage_record.source_record_id)
                if not (
                    previous
                    and previous.capability_state != "malformed"
                    and usage_record.capability_state == "malformed"
                ):
                    usage_by_record[usage_record.source_record_id] = usage_record
        content = message.get("content") if isinstance(message, dict) else None
        if record_type == "assistant" and isinstance(content, list):
            for offset, item in enumerate(content, start=1):
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name")
                    if isinstance(tool_name, str):
                        tool_use_id = item.get("id")
                        if isinstance(tool_use_id, str):
                            call = approved_resource_call(
                                tool_name, tool_use_id, item.get("input")
                            )
                            if call is not None:
                                approved_tool_calls[tool_use_id] = call
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
        usage_records=list(usage_by_record.values()),
        url_evidence=url_evidence,
        reference_candidates=reference_candidates,
    )
