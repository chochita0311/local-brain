from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import (
    ParsedEvent,
    ParsedSession,
    ParsedUsageRecord,
    compact_title,
    read_json_lines,
    session_policy,
    stable_id,
    token_value,
)
from ..usage import CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID


CODEX_USAGE_CONTRACT_VERSION = "codex-last-token-usage-v4-fast-context-tier"

CODEX_AUTO_REVIEW_FALLBACKS = (
    ("2026-04-23", "gpt-5.5"),
    ("2026-03-05", "gpt-5.4"),
    ("2026-02-05", "gpt-5.3-codex"),
    ("2025-12-11", "gpt-5.2-codex"),
    ("2025-11-13", "gpt-5.1-codex"),
    ("2025-09-15", "gpt-5-codex"),
    ("2025-08-07", "gpt-5"),
)


def _resolved_codex_model(
    raw_model: Optional[str], timestamp: Optional[str]
) -> tuple:
    if raw_model is None:
        return "gpt-5", "missing_source_fallback"
    if raw_model != "codex-auto-review":
        return raw_model, "source"
    event_date = timestamp[:10] if isinstance(timestamp, str) else ""
    for released_on, model in CODEX_AUTO_REVIEW_FALLBACKS:
        if event_date >= released_on:
            return model, "dated_auto_review_fallback"
    return "gpt-5", "dated_auto_review_fallback_before_snapshot"


def _codex_model_from_mapping(value: Any) -> Optional[str]:
    if not isinstance(value, dict):
        return None
    for candidate in (value.get("model"), value.get("model_name")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    metadata = value.get("metadata")
    if isinstance(metadata, dict):
        candidate = metadata.get("model")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _codex_subagent_replay_second(path: Path) -> Optional[str]:
    try:
        with path.open("rb") as handle:
            header = handle.read(16 * 1024)
            if b"thread_spawn" not in header and b"forked_from_id" not in header:
                return None
    except OSError:
        return None

    first_second: Optional[str] = None
    for _, record in read_json_lines(path):
        if not isinstance(record, dict) or record.get("type") != "event_msg":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "token_count":
            continue
        info = payload.get("info")
        if not isinstance(info, dict) or not any(
            isinstance(info.get(name), dict)
            for name in ("last_token_usage", "total_token_usage")
        ):
            continue
        timestamp = record.get("timestamp")
        if not isinstance(timestamp, str) or len(timestamp) < 19:
            continue
        second = timestamp[:19]
        if first_second is None:
            first_second = second
        else:
            return first_second if second == first_second else None
    return None


def _update_previous_total_usage(
    previous_total_usage: Dict[str, int], payload: Dict[str, Any]
) -> None:
    info = payload.get("info")
    cumulative = info.get("total_token_usage") if isinstance(info, dict) else None
    if not isinstance(cumulative, dict):
        return
    for name in (
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    ):
        value = cumulative.get(name)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            previous_total_usage[name] = value


def _codex_usage_record(
    external_id: str,
    line_number: int,
    timestamp: Optional[str],
    payload: Dict[str, Any],
    turn_id: Optional[str],
    raw_model: Optional[str],
    previous_usage: Dict[str, int],
) -> Optional[ParsedUsageRecord]:
    info = payload.get("info")
    if not isinstance(info, dict):
        return None
    direct_usage = info.get("last_token_usage")
    cumulative_usage = info.get("total_token_usage")
    if isinstance(direct_usage, dict):
        usage = direct_usage
        usage_source = "last_token_usage"
    elif isinstance(cumulative_usage, dict):
        usage = cumulative_usage
        usage_source = "cumulative_delta"
    else:
        return None

    component_states: Dict[str, str] = {}
    malformed = False
    reset_seen = False

    def normalized_component(name: str) -> Optional[int]:
        nonlocal malformed, reset_seen
        if name not in usage:
            component_states[name] = "missing"
            return None
        value, state = token_value(usage.get(name))
        if state == "malformed" or value is None:
            component_states[name] = "malformed"
            malformed = True
            return None
        if usage_source == "last_token_usage":
            component_states[name] = "direct_event"
            return value
        previous = previous_usage.get(name, 0)
        if value < previous:
            component_states[name] = "cumulative_reset"
            reset_seen = True
            return value
        component_states[name] = "cumulative_delta"
        return value - previous

    source_input_tokens = normalized_component("input_tokens")
    output_tokens = normalized_component("output_tokens")
    cache_read_tokens = normalized_component("cached_input_tokens")
    reasoning_tokens = normalized_component("reasoning_output_tokens")
    source_total_tokens = normalized_component("total_tokens")

    observed_deltas = (
        source_input_tokens,
        output_tokens,
        cache_read_tokens,
        reasoning_tokens,
        source_total_tokens,
    )
    if not malformed and all(value in (None, 0) for value in observed_deltas):
        return None

    input_tokens = None
    if source_input_tokens is not None and cache_read_tokens is not None:
        if cache_read_tokens <= source_input_tokens:
            input_tokens = source_input_tokens - cache_read_tokens
        else:
            malformed = True
            component_states["input_tokens"] = "malformed_cache_exceeds_input"
    component_states["cache_write_tokens"] = "not_supported"
    component_states["model"] = "available" if raw_model else "missing"
    normalized_model, model_resolution = _resolved_codex_model(raw_model, timestamp)
    component_states["usage_source"] = usage_source
    component_states["model_resolution"] = model_resolution

    total_tokens = None
    if None not in (input_tokens, output_tokens, cache_read_tokens):
        total_tokens = input_tokens + output_tokens + cache_read_tokens
    if (
        reasoning_tokens is not None
        and output_tokens is not None
        and reasoning_tokens > output_tokens
    ):
        malformed = True
        component_states["reasoning_output_tokens"] = "malformed_exceeds_output"
    if source_total_tokens is not None and total_tokens is not None:
        component_states["source_total_consistency"] = (
            "matches" if source_total_tokens == total_tokens else "mismatch"
        )

    if malformed:
        capability_state = "malformed"
    elif (
        reset_seen
        or raw_model is None
        or component_states.get("source_total_consistency") == "mismatch"
        or None in (
            input_tokens,
            output_tokens,
            cache_read_tokens,
            reasoning_tokens,
        )
    ):
        capability_state = "partial"
    else:
        capability_state = "complete"

    record_identity = stable_id(
        "codex-usage-record",
        CODEX_USAGE_CONTRACT_VERSION,
        external_id,
        turn_id or "unscoped",
        line_number,
    )
    return ParsedUsageRecord(
        usage_record_id=stable_id(
            "codex-usage", CODEX_USAGE_CONTRACT_VERSION, external_id, record_identity
        ),
        source_record_id=str(record_identity),
        source_line=line_number,
        occurred_at=timestamp,
        raw_model=raw_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_write_tokens=None,
        cache_read_tokens=cache_read_tokens,
        reasoning_tokens=reasoning_tokens,
        source_total_tokens=source_total_tokens,
        total_tokens=total_tokens,
        total_semantics=(
            "{};source_input_includes_cache_read;"
            "normalized_non_cached_input_plus_output_plus_cache_read;reasoning_subset_of_output"
        ).format(usage_source),
        capability_state=capability_state,
        capability=component_states,
        normalized_model=normalized_model,
        price_snapshot_id=CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,
    )


def parse_codex_session(path: Path) -> ParsedSession:
    external_id = path.stem
    cwd: Optional[str] = None
    first_user_text = ""
    timestamps: List[str] = []
    events: List[ParsedEvent] = []
    usage_by_record: Dict[str, ParsedUsageRecord] = {}
    skipped_lines = 0
    session_meta_seen = False
    primary_started_at: Optional[str] = None
    git_branch: Optional[str] = None
    session_role = "primary"
    parent_external_id: Optional[str] = None
    current_turn_id: Optional[str] = None
    current_model: Optional[str] = None
    previous_total_usage: Dict[str, int] = {}
    replay_second = _codex_subagent_replay_second(path)
    skip_subagent_replay = replay_second is not None

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
            turn_value = payload.get("turn_id")
            current_turn_id = str(turn_value) if turn_value else None
            model_value = payload.get("model")
            current_model = (
                model_value.strip()
                if isinstance(model_value, str) and model_value.strip()
                else None
            )
            continue

        if record_type == "event_msg":
            payload_type = payload.get("type")
            if payload_type == "token_count":
                if skip_subagent_replay:
                    event_second = timestamp[:19] if isinstance(timestamp, str) else None
                    if event_second == replay_second:
                        _update_previous_total_usage(previous_total_usage, payload)
                        continue
                    skip_subagent_replay = False
                info = payload.get("info")
                parsed_model = _codex_model_from_mapping(payload) or (
                    _codex_model_from_mapping(info) if isinstance(info, dict) else None
                )
                if parsed_model:
                    current_model = parsed_model
                usage_record = _codex_usage_record(
                    external_id,
                    line_number,
                    timestamp if isinstance(timestamp, str) else None,
                    payload,
                    current_turn_id,
                    current_model,
                    previous_total_usage,
                )
                _update_previous_total_usage(previous_total_usage, payload)
                if usage_record:
                    usage_by_record[usage_record.source_record_id] = usage_record
                continue
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
        usage_records=list(usage_by_record.values()),
    )
