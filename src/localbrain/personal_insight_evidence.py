"""Bounded, read-only Session message evidence for future personal insight Runs."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import date, datetime, time, timedelta, timezone as datetime_timezone
from hashlib import sha256
import re
import sqlite3
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


MANIFEST_VERSION = "personal-insight-evidence-v1"
MAX_SESSIONS = 100
MAX_EXCERPTS = 300
MAX_EXCERPT_CHARS = 600
MAX_TOTAL_CHARS = 120_000
MAX_QUESTION_CHARS = 2_000
MAX_SEARCH_TERMS = 16
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_TERM_RE = re.compile(r"[^\W_]+", re.UNICODE)


def _utc_text(value: datetime) -> str:
    return value.astimezone(datetime_timezone.utc).isoformat().replace("+00:00", "Z")


def _strict_date(value: str | None, name: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        raise ValueError(f"{name} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a valid date") from error


def _terms(value: str) -> list[str]:
    return list(dict.fromkeys(match.group().casefold() for match in _TERM_RE.finditer(value)))


def _event_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=datetime_timezone.utc) if parsed.tzinfo is None else parsed


def _event_conditions(
    *, requested_at: str, start_at: str | None, end_at: str | None
) -> tuple[str, list[str]]:
    conditions = [
        "e.event_type = 'message'",
        "e.role IN ('user', 'assistant')",
        "e.text IS NOT NULL AND length(trim(e.text)) > 0",
        "(julianday(e.occurred_at) IS NULL OR julianday(e.occurred_at) <= julianday(?))",
    ]
    params = [requested_at]
    if start_at is not None:
        conditions.append("julianday(e.occurred_at) >= julianday(?)")
        params.append(start_at)
    if end_at is not None:
        conditions.append("julianday(e.occurred_at) < julianday(?)")
        params.append(end_at)
    return " AND ".join(conditions), params


def _source_registry(connection: sqlite3.Connection) -> dict[str, str]:
    return {
        row["kind"]: row["provider_kind"]
        for row in connection.execute(
            """
            SELECT kind, provider_kind FROM sources
            WHERE provider_kind IN ('claude', 'codex')
            ORDER BY kind
            """
        )
    }


def _eligible_sessions(
    connection: sqlite3.Connection,
    source_keys: list[str],
    event_where: str,
    event_params: list[str],
) -> list[dict[str, Any]]:
    if not source_keys:
        return []
    placeholders = ", ".join("?" for _ in source_keys)
    rows = connection.execute(
        f"""
        SELECT s.id AS session_id, src.kind AS source_key,
               src.provider_kind,
               COUNT(e.id) AS message_count,
               SUM(CASE WHEN julianday(e.occurred_at) IS NULL THEN 1 ELSE 0 END)
                   AS unknown_time_count,
               strftime('%Y-%m-%dT%H:%M:%SZ', MAX(julianday(e.occurred_at)))
                   AS latest_event_at
        FROM sessions AS s
        JOIN sources AS src ON src.id = s.source_id
        JOIN activity_events AS e ON e.session_id = s.id
        WHERE s.session_class = 'work'
          AND s.session_role = 'primary'
          AND s.index_policy = 'full'
          AND src.provider_kind IN ('claude', 'codex')
          AND src.kind IN ({placeholders})
          AND {event_where}
        GROUP BY s.id, src.kind, src.provider_kind
        ORDER BY s.id
        """,
        [*source_keys, *event_params],
    ).fetchall()
    return [dict(row) for row in rows]


def _spread_order(
    rows: Iterable[dict[str, Any]], zone: ZoneInfo
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], deque[dict[str, Any]]] = defaultdict(deque)
    for row in rows:
        latest = _event_time(row["latest_event_at"])
        month = latest.astimezone(zone).strftime("%Y-%m") if latest else "unknown"
        buckets[(row["source_key"], month)].append(row)
    for key, bucket in buckets.items():
        buckets[key] = deque(
            sorted(
                bucket,
                key=lambda row: (row["latest_event_at"] or "", -row["session_id"]),
                reverse=True,
            )
        )
    keys = sorted(buckets, key=lambda item: (item[1] != "unknown", item[1], item[0]), reverse=True)
    ordered: list[dict[str, Any]] = []
    while True:
        added = False
        for key in keys:
            if buckets[key]:
                ordered.append(buckets[key].popleft())
                added = True
        if not added:
            break
    return ordered


def _fts_ranked_session_ids(connection: sqlite3.Connection, terms: list[str]) -> list[int]:
    if not terms:
        return []
    expression = " OR ".join(f'body:"{term}"' for term in terms)
    rows = connection.execute(
        """
        SELECT entity_id, bm25(search_index) AS fts_score
        FROM search_index
        WHERE search_index MATCH ? AND entity_type = 'session'
        ORDER BY fts_score, entity_id
        """,
        (expression,),
    )
    seen: set[int] = set()
    ranked: list[int] = []
    for row in rows:
        if not str(row["entity_id"]).isdigit():
            continue
        session_id = int(row["entity_id"])
        if session_id not in seen:
            ranked.append(session_id)
            seen.add(session_id)
    return ranked


def _pick_events(
    connection: sqlite3.Connection,
    session: dict[str, Any],
    event_where: str,
    event_params: list[str],
    terms: set[str],
) -> list[tuple[dict[str, Any], set[str]]]:
    cursor = connection.execute(
        f"""
        SELECT e.id, e.sequence, e.occurred_at, e.role, e.text
        FROM activity_events AS e
        WHERE e.session_id = ? AND {event_where}
        ORDER BY e.sequence, e.id
        """,
        [session["session_id"], *event_params],
    )
    count = session["message_count"]
    spread_positions = {0, count // 2, count - 1}
    spread: list[tuple[dict[str, Any], set[str]]] = []
    ranked: list[tuple[int, int, int, str, dict[str, Any], set[str]]] = []
    for index, raw in enumerate(cursor):
        row = dict(raw)
        if index in spread_positions:
            spread.append((row, set()))
        if not terms:
            continue
        overlap = terms.intersection(_terms(row["text"]))
        if overlap:
            ranked.append(
                (
                    -len(overlap),
                    0 if row["role"] == "user" else 1,
                    row["sequence"],
                    row["id"],
                    row,
                    overlap,
                )
            )
            ranked.sort(key=lambda item: item[:4])
            del ranked[3:]
    if ranked:
        return [(item[4], item[5]) for item in ranked]
    return spread


def _excerpt(text: str, matched_terms: set[str], available: int) -> tuple[str, int, int]:
    start = 0
    if matched_terms:
        folded = text.casefold()
        positions = [folded.find(term) for term in matched_terms]
        found = [position for position in positions if position >= 0]
        if found:
            folded_position = min(found)
            original_position = 0
            consumed = 0
            while original_position < len(text):
                width = len(text[original_position].casefold())
                if consumed + width > folded_position:
                    break
                consumed += width
                original_position += 1
            start = max(0, original_position - 120)
    end = min(len(text), start + MAX_EXCERPT_CHARS, start + available)
    return text[start:end], start, end


def build_insight_evidence_manifest(
    connection: sqlite3.Connection,
    *,
    mode: str,
    requested_at: datetime,
    question: str | None = None,
    source_keys: Iterable[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    timezone: str = "Asia/Seoul",
) -> dict[str, Any]:
    """Select private, source-backed evidence without mutating its source tables."""
    if not isinstance(mode, str) or mode not in {"ask", "discover"}:
        raise ValueError("mode must be ask or discover")
    if not isinstance(requested_at, datetime) or requested_at.tzinfo is None:
        raise ValueError("requested_at must be timezone-aware")
    if not isinstance(timezone, str):
        raise ValueError("timezone must be an IANA timezone")
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("timezone must be an IANA timezone") from error
    first_date = _strict_date(date_from, "date_from")
    last_date = _strict_date(date_to, "date_to")
    if first_date and last_date and first_date > last_date:
        raise ValueError("date_from must not be after date_to")
    if mode == "ask":
        if not isinstance(question, str) or not question.strip():
            raise ValueError("ask requires a question")
        normalized_question = question.strip()
        if len(normalized_question) > MAX_QUESTION_CHARS:
            raise ValueError("question exceeds 2,000 characters")
    elif question is not None:
        raise ValueError("discover does not accept a question")
    else:
        normalized_question = None
    if source_keys is not None:
        if isinstance(source_keys, str):
            raise ValueError("source_keys must be a collection of source keys")
        requested_sources = list(source_keys)
        if not requested_sources or any(
            not isinstance(key, str) or not key for key in requested_sources
        ):
            raise ValueError("source_keys must be nonempty source keys")
        requested_sources = sorted(set(requested_sources))
    else:
        requested_sources = None

    frozen_at = _utc_text(requested_at)
    start_at = (
        _utc_text(datetime.combine(first_date, time.min, zone)) if first_date else None
    )
    end_at = (
        _utc_text(datetime.combine(last_date + timedelta(days=1), time.min, zone))
        if last_date
        else None
    )
    event_where, event_params = _event_conditions(
        requested_at=frozen_at, start_at=start_at, end_at=end_at
    )
    search_terms = _terms(normalized_question)[:MAX_SEARCH_TERMS] if normalized_question else []

    connection.execute("SAVEPOINT personal_insight_evidence_read")
    try:
        registry = _source_registry(connection)
        if requested_sources is None:
            selected_sources = sorted(registry)
        else:
            unknown = set(requested_sources) - set(registry)
            if unknown:
                raise ValueError("source_keys contains an unknown Claude/Codex source")
            selected_sources = requested_sources
        eligible = _eligible_sessions(
            connection, selected_sources, event_where, event_params
        )
        undated_excluded = 0
        if (first_date or last_date) and selected_sources:
            placeholders = ", ".join("?" for _ in selected_sources)
            undated_excluded = connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM sessions AS s
                JOIN sources AS src ON src.id = s.source_id
                JOIN activity_events AS e ON e.session_id = s.id
                WHERE s.session_class = 'work'
                  AND s.session_role = 'primary'
                  AND s.index_policy = 'full'
                  AND src.provider_kind IN ('claude', 'codex')
                  AND src.kind IN ({placeholders})
                  AND e.event_type = 'message'
                  AND e.role IN ('user', 'assistant')
                  AND e.text IS NOT NULL AND length(trim(e.text)) > 0
                  AND julianday(e.occurred_at) IS NULL
                """,
                selected_sources,
            ).fetchone()["count"]
        by_id = {row["session_id"]: row for row in eligible}
        coverage_by_source = {
            key: {
                "provider_kind": registry[key],
                "eligible_sessions": 0,
                "eligible_messages": 0,
                "selected_sessions": 0,
                "selected_excerpts": 0,
                "selected_undated_messages": 0,
                "selected_first_at": None,
                "selected_last_at": None,
            }
            for key in selected_sources
        }
        for row in eligible:
            source = coverage_by_source[row["source_key"]]
            source["eligible_sessions"] += 1
            source["eligible_messages"] += row["message_count"]

        if mode == "ask":
            ranked_ids = [
                session_id
                for session_id in _fts_ranked_session_ids(connection, search_terms)
                if session_id in by_id
            ]
            leading = [by_id[session_id] for session_id in ranked_ids[:70]]
            already = {row["session_id"] for row in leading}
            candidates = leading + _spread_order(
                (row for row in eligible if row["session_id"] not in already), zone
            )[: MAX_SESSIONS - len(leading)]
        else:
            ranked_ids = []
            candidates = _spread_order(eligible, zone)[:MAX_SESSIONS]

        included_sessions: list[dict[str, Any]] = []
        selected_excerpts = 0
        total_chars = 0
        lexical_excerpts = 0
        selected_times: list[datetime] = []
        selected_times_by_source: dict[str, list[datetime]] = defaultdict(list)
        unknown_selected_times = 0
        for session in candidates:
            if selected_excerpts >= MAX_EXCERPTS or total_chars >= MAX_TOTAL_CHARS:
                break
            chosen = _pick_events(
                connection, session, event_where, event_params,
                set(search_terms) if mode == "ask" else set(),
            )
            events = []
            for event, overlap in sorted(chosen, key=lambda item: (item[0]["sequence"], item[0]["id"])):
                if selected_excerpts >= MAX_EXCERPTS or total_chars >= MAX_TOTAL_CHARS:
                    break
                excerpt, start, end = _excerpt(
                    event["text"], overlap, MAX_TOTAL_CHARS - total_chars
                )
                if not excerpt:
                    break
                occurred = _event_time(event["occurred_at"])
                if occurred:
                    selected_time = occurred.astimezone(datetime_timezone.utc)
                    selected_times.append(selected_time)
                    selected_times_by_source[session["source_key"]].append(selected_time)
                else:
                    unknown_selected_times += 1
                    coverage_by_source[session["source_key"]]["selected_undated_messages"] += 1
                events.append(
                    {
                        "source_key": session["source_key"],
                        "provider_kind": session["provider_kind"],
                        "session_id": session["session_id"],
                        "event_id": event["id"],
                        "sequence": event["sequence"],
                        "role": event["role"],
                        "occurred_at": event["occurred_at"],
                        "text_revision": sha256(event["text"].encode("utf-8")).hexdigest(),
                        "text_length": len(event["text"]),
                        "excerpt": excerpt,
                        "excerpt_start": start,
                        "excerpt_end": end,
                        "selection_basis": "lexical" if overlap else "spread",
                        "session_url": f"/sessions/{session['session_id']}",
                    }
                )
                selected_excerpts += 1
                total_chars += len(excerpt)
                lexical_excerpts += bool(overlap)
            if events:
                included_sessions.append(
                    {
                        "source_key": session["source_key"],
                        "provider_kind": session["provider_kind"],
                        "session_id": session["session_id"],
                        "session_url": f"/sessions/{session['session_id']}",
                        "events": events,
                    }
                )
                source = coverage_by_source[session["source_key"]]
                source["selected_sessions"] += 1
                source["selected_excerpts"] += len(events)

        for key, times in selected_times_by_source.items():
            coverage_by_source[key]["selected_first_at"] = _utc_text(min(times))
            coverage_by_source[key]["selected_last_at"] = _utc_text(max(times))

        eligible_messages = sum(row["message_count"] for row in eligible)
        omissions = []
        if not eligible:
            omissions.append("no_eligible_messages")
        if len(eligible) > len(included_sessions):
            omissions.append("session_sample_limit")
        if eligible_messages > selected_excerpts:
            omissions.append("message_sample_limit")
        if total_chars >= MAX_TOTAL_CHARS:
            omissions.append("character_limit")
        if mode == "ask" and not ranked_ids:
            omissions.append("no_indexed_lexical_match")
        if mode == "ask" and ranked_ids and not lexical_excerpts:
            omissions.append("no_selected_message_lexical_match")
        if undated_excluded:
            omissions.append("undated_messages_excluded_by_date_scope")

        return {
            "version": MANIFEST_VERSION,
            "generated_at": frozen_at,
            "scope": {
                "mode": mode,
                "question": normalized_question,
                "source_keys": selected_sources,
                "date_from": date_from,
                "date_to": date_to,
                "timezone": timezone,
                "event_from_utc": start_at,
                "event_to_exclusive_utc": end_at,
                "requested_at": frozen_at,
            },
            "selection": {
                "method": "fts70_plus_source_month_spread_v1" if mode == "ask" else "source_month_spread_v1",
                "indexed_session_count": len(ranked_ids),
                "lexical_excerpt_count": lexical_excerpts,
                "lexical_match_state": (
                    "matched" if lexical_excerpts else "none"
                ) if mode == "ask" else "not_applicable",
            },
            "coverage": {
                "eligible_sessions": len(eligible),
                "eligible_messages": eligible_messages,
                "selected_sessions": len(included_sessions),
                "selected_excerpts": selected_excerpts,
                "excerpt_characters": total_chars,
                "eligible_undated_messages": sum(row["unknown_time_count"] for row in eligible),
                "undated_messages_excluded": undated_excluded,
                "selected_undated_messages": unknown_selected_times,
                "selected_first_at": _utc_text(min(selected_times)) if selected_times else None,
                "selected_last_at": _utc_text(max(selected_times)) if selected_times else None,
                "sources": coverage_by_source,
                "omission_reasons": omissions,
            },
            "sessions": included_sessions,
        }
    finally:
        connection.execute("RELEASE SAVEPOINT personal_insight_evidence_read")


def resolve_insight_evidence_reference(
    connection: sqlite3.Connection, reference: dict[str, Any]
) -> dict[str, Any]:
    """Review a frozen reference against current normalized source evidence."""
    required = {
        "source_key", "provider_kind", "session_id", "event_id", "sequence",
        "role", "occurred_at", "text_revision",
    }
    if not isinstance(reference, dict) or not required.issubset(reference):
        raise ValueError("reference is missing required fields")
    session_id = reference["session_id"]
    if not isinstance(session_id, int) or isinstance(session_id, bool) or session_id <= 0:
        raise ValueError("reference has an invalid session_id")
    row = connection.execute(
        """
        SELECT s.id AS session_id, s.session_class, s.session_role, s.index_policy,
               src.kind AS source_key, src.provider_kind,
               e.id AS event_id, e.event_type, e.sequence, e.role,
               e.occurred_at, e.text
        FROM sessions AS s
        JOIN sources AS src ON src.id = s.source_id
        LEFT JOIN activity_events AS e ON e.session_id = s.id AND e.id = ?
        WHERE s.id = ?
        """,
        (reference["event_id"], session_id),
    ).fetchone()
    if row is None:
        return {"status": "unavailable", "session_url": None}
    session_url = f"/sessions/{session_id}"
    if row["event_id"] is None:
        return {"status": "unavailable", "session_url": session_url}
    current_digest = sha256((row["text"] or "").encode("utf-8")).hexdigest()
    unchanged = (
        row["session_class"] == "work"
        and row["session_role"] == "primary"
        and row["index_policy"] == "full"
        and row["source_key"] == reference["source_key"]
        and row["provider_kind"] == reference["provider_kind"]
        and row["event_type"] == "message"
        and row["role"] in {"user", "assistant"}
        and row["role"] == reference["role"]
        and row["sequence"] == reference["sequence"]
        and row["occurred_at"] == reference["occurred_at"]
        and current_digest == reference["text_revision"]
    )
    return {"status": "current" if unchanged else "stale", "session_url": session_url}
