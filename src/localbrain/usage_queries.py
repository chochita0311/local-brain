import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from heapq import merge
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from .activity import activity_summary, parse_timestamp


VALID_VIEWS = {"daily", "weekly", "monthly", "cumulative"}
VALID_METRICS = {"tokens", "cost"}
VALID_BREAKDOWNS = {"source", "model", "project"}
PROJECTION_FORMULA_VERSION = "calendar-elapsed-v1"
CLAUDE_SYNTHETIC_MODEL = "<synthetic>"
CODEX_ZERO_TOKEN_SNAPSHOT_SQL = """(
    sources.provider_kind = 'codex'
    AND usage_records.total_semantics LIKE 'last_token_usage;%'
    AND usage_records.input_tokens = 0
    AND usage_records.output_tokens = 0
    AND usage_records.cache_write_tokens IS NULL
    AND usage_records.cache_read_tokens = 0
    AND usage_records.reasoning_tokens = 0
    AND usage_records.total_tokens = 0
    AND usage_records.source_total_tokens > 0
)"""


def _usage_source_options(connection: sqlite3.Connection) -> List[dict]:
    return [
        {
            "value": row["kind"],
            "label": row["name"],
            "provider_kind": row["provider_kind"],
        }
        for row in connection.execute(
            """
            SELECT kind, provider_kind, name
            FROM sources
            WHERE provider_kind IN ('claude', 'codex')
            ORDER BY id
            """
        ).fetchall()
    ]


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _eligible_usage_where(source: str) -> Tuple[str, List[str]]:
    params = [CLAUDE_SYNTHETIC_MODEL]
    source_filter = ""
    if source != "all":
        source_filter = "AND sources.kind = ?"
        params.append(source)
    return (
        """
        sources.provider_kind IN ('claude', 'codex')
        AND NOT (
            sources.provider_kind = 'claude'
            AND COALESCE(usage_records.raw_model, '') = ?
        )
        AND NOT {zero_token_snapshot}
        {source_filter}
        """.format(
            zero_token_snapshot=CODEX_ZERO_TOKEN_SNAPSHOT_SQL,
            source_filter=source_filter,
        ),
        params,
    )


def _format_tokens(value: Optional[int]) -> str:
    if value is None:
        return "Unavailable"
    for divisor, suffix in (
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ):
        if abs(value) >= divisor:
            scaled = Decimal(value) / Decimal(divisor)
            precision = Decimal("0.01") if scaled < 10 else Decimal("0.1")
            formatted = format(scaled.quantize(precision), "f").rstrip("0").rstrip(".")
            return "{}{}".format(formatted, suffix)
    return "{:,}".format(value)


def _format_cost(value: Optional[Decimal]) -> str:
    if value is None:
        return "Unavailable"
    precision = Decimal("0.0001") if value < Decimal("0.01") else Decimal("0.01")
    digits = abs(precision.as_tuple().exponent)
    return "${}".format(format(value, ",.{}f".format(digits)))


def _format_history_bar_value(value: Decimal, metric: str) -> str:
    prefix = "$" if metric == "cost" else ""
    if metric == "cost" and Decimal("0") < value < Decimal("1"):
        return "<$1"
    units = (
        (Decimal("1000000000000"), "T"),
        (Decimal("1000000000"), "B"),
        (Decimal("1000000"), "M"),
        (Decimal("1000"), "K"),
    )
    for index, (divisor, suffix) in enumerate(units):
        if value >= divisor:
            rounded = int((value / divisor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if rounded >= 1000 and index > 0:
                return "{}1{}".format(prefix, units[index - 1][1])
            return "{}{:,}{}".format(prefix, rounded, suffix)
    rounded = int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if rounded >= 1000:
        return "{}1K".format(prefix)
    return "{}{:,}".format(prefix, rounded)


def _format_duration(seconds: int) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes = remainder // 60
    if hours:
        return "{}h {}m".format(hours, minutes)
    return "{}m".format(minutes)


def _format_usage_record_count(value: int, modifier: str = "") -> str:
    prefix = "{} ".format(modifier) if modifier else ""
    return "{:,} {}usage record{}".format(
        value, prefix, "" if value == 1 else "s"
    )


def _earliest_usage_date(
    connection: sqlite3.Connection, source: str, zone: ZoneInfo
) -> Optional[date]:
    eligible_where, params = _eligible_usage_where(source)
    rows = connection.execute(
        """
        SELECT usage_records.occurred_at
        FROM usage_records
        JOIN sources ON sources.id = usage_records.source_id
        WHERE usage_records.occurred_at IS NOT NULL
          AND {eligible_where}
        ORDER BY usage_records.occurred_at
        """.format(eligible_where=eligible_where),
        tuple(params),
    )
    earliest = None
    for row in rows:
        raw_time = row["occurred_at"]
        raw_day = _parse_date(raw_time[:10])
        if earliest is not None and raw_day is not None:
            # A source-local date more than one day later cannot precede
            # the earliest UTC instant, even with the largest ISO offset.
            if raw_day > earliest.date() + timedelta(days=1):
                break
        parsed = parse_timestamp(raw_time)
        if parsed is not None and (earliest is None or parsed < earliest):
            earliest = parsed
    return earliest.astimezone(zone).date() if earliest is not None else None


def normalize_usage_scope(
    connection: sqlite3.Connection,
    view: str = "daily",
    source: str = "all",
    metric: str = "cost",
    breakdown: str = "source",
    from_value: Optional[str] = None,
    to_value: Optional[str] = None,
    timezone_name: str = "UTC",
    today: Optional[date] = None,
) -> dict:
    selected_view = view if view in VALID_VIEWS else "daily"
    source_options = _usage_source_options(connection)
    source_options_by_key = {item["value"]: item for item in source_options}
    selected_source = source if source in source_options_by_key else "all"
    selected_source_label = (
        source_options_by_key[selected_source]["label"]
        if selected_source != "all"
        else "All"
    )
    selected_metric = metric if metric in VALID_METRICS else "cost"
    selected_breakdown = breakdown if breakdown in VALID_BREAKDOWNS else "source"
    current_day = today or datetime.now(ZoneInfo(timezone_name)).date()
    validation_message = None
    custom = False
    parsed_from = _parse_date(from_value)
    parsed_to = _parse_date(to_value)

    if from_value or to_value:
        if parsed_from is not None and parsed_to is not None and parsed_from <= parsed_to:
            start_day, end_day = parsed_from, parsed_to
            custom = True
        else:
            validation_message = (
                "Custom dates require a valid inclusive From and To pair. "
                "The selected view's default range is shown instead."
            )
    if not custom:
        if selected_view == "daily":
            start_day, end_day = current_day - timedelta(days=29), current_day
        elif selected_view == "weekly":
            current_monday = current_day - timedelta(days=current_day.weekday())
            start_day, end_day = current_monday - timedelta(weeks=11), current_day
        else:
            start_day = _earliest_usage_date(
                connection, selected_source, ZoneInfo(timezone_name)
            ) or current_day
            end_day = current_day

    zone = ZoneInfo(timezone_name)
    start_local = datetime.combine(start_day, datetime.min.time(), tzinfo=zone)
    end_local = datetime.combine(
        end_day + timedelta(days=1), datetime.min.time(), tzinfo=zone
    )
    return {
        "view": selected_view,
        "source": selected_source,
        "source_label": selected_source_label,
        "source_options": source_options,
        "metric": selected_metric,
        "breakdown": selected_breakdown,
        "from_date": start_day,
        "to_date": end_day,
        "from_iso": start_day.isoformat(),
        "to_iso": end_day.isoformat(),
        "input_from": from_value or "",
        "input_to": to_value or "",
        "custom": custom,
        "validation_message": validation_message,
        "timezone": timezone_name,
        "start_utc": start_local.astimezone(timezone.utc),
        "end_utc": end_local.astimezone(timezone.utc),
        "period_label": "{} – {} · {}".format(
            start_day.isoformat(), end_day.isoformat(), timezone_name
        ),
    }


def _usage_rows(
    connection: sqlite3.Connection,
    source: str,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
    visible_only: bool = False,
    unusual_only: bool = False,
    stream: bool = False,
) -> Iterable[sqlite3.Row]:
    eligible_where, params = _eligible_usage_where(source)
    time_filter = ""
    raw_window = (
        (
            (start_utc.date() - timedelta(days=1)).isoformat(),
            (end_utc.date() + timedelta(days=2)).isoformat(),
        )
        if start_utc is not None and end_utc is not None
        else None
    )
    if unusual_only:
        time_filter = """
            AND (
                usage_records.occurred_at IS NULL
                OR strftime('%s', usage_records.occurred_at) IS NULL
                OR usage_records.occurred_at != trim(usage_records.occurred_at)
                OR date(substr(usage_records.occurred_at, 1, 10), '+0 days')
                   != substr(usage_records.occurred_at, 1, 10)
            )
        """
        if raw_window is not None:
            # The ordinary window query already includes unusual timestamps
            # whose raw values fall inside it.
            time_filter += """
                AND (
                    usage_records.occurred_at IS NULL
                    OR usage_records.occurred_at < ?
                    OR usage_records.occurred_at >= ?
                )
            """
            params.extend(raw_window)
    elif raw_window is not None:
        # Raw source timestamps can carry an ISO offset. The indexed window
        # includes its neighboring source dates; _rows_in_range applies the
        # exact UTC boundaries after parsing each candidate.
        time_filter = (
            "AND usage_records.occurred_at >= ? "
            "AND usage_records.occurred_at < ?"
        )
        params.extend(raw_window)
    if visible_only:
        columns = """
            usage_records.id, usage_records.occurred_at,
            usage_records.session_id,
            usage_records.raw_model, usage_records.model_name,
            usage_records.total_tokens, usage_records.estimated_cost_usd,
            usage_records.calculation_state,
            usage_records.project_key, usage_records.project_name_snapshot,
            sources.kind AS source_kind, sources.provider_kind,
            sources.name AS source_name,
            sessions.session_class, sessions.session_role,
            NULL AS current_workspace_id
        """
        auxiliary_joins = ""
    else:
        columns = """
            usage_records.*, sources.kind AS source_kind,
            sources.provider_kind, sources.name AS source_name,
            sessions.session_class, sessions.session_role,
            sessions.title AS session_title,
            usage_price_snapshots.label AS price_snapshot_label,
            current_workspace.id AS current_workspace_id,
            current_workspace.exists_now AS current_workspace_exists
        """
        auxiliary_joins = """
            LEFT JOIN usage_price_snapshots
              ON usage_price_snapshots.id = usage_records.price_snapshot_id
            LEFT JOIN workspaces AS current_workspace
              ON current_workspace.id = usage_records.workspace_id_snapshot
        """
    cursor = connection.execute(
        """
        SELECT {columns}
        FROM usage_records
        JOIN sources ON sources.id = usage_records.source_id
        JOIN sessions ON sessions.id = usage_records.session_id
        {auxiliary_joins}
        WHERE {eligible_where}
        {time_filter}
        ORDER BY usage_records.occurred_at, usage_records.id
        """.format(
            columns=columns,
            auxiliary_joins=auxiliary_joins,
            eligible_where=eligible_where,
            time_filter=time_filter,
        ),
        tuple(params),
    )
    return cursor if stream else cursor.fetchall()


def _has_eligible_usage(connection: sqlite3.Connection, source: str) -> bool:
    eligible_where, params = _eligible_usage_where(source)
    row = connection.execute(
        """
        SELECT 1
        FROM usage_records
        JOIN sources ON sources.id = usage_records.source_id
        JOIN sessions ON sessions.id = usage_records.session_id
        WHERE {eligible_where}
        LIMIT 1
        """.format(eligible_where=eligible_where),
        tuple(params),
    ).fetchone()
    return row is not None


def _rows_in_range(
    rows: Iterable[sqlite3.Row], start: datetime, end: datetime
) -> Tuple[List[Tuple[sqlite3.Row, datetime]], int]:
    selected = []
    untimed = 0
    for row in rows:
        occurred_at = parse_timestamp(row["occurred_at"])
        if occurred_at is None:
            untimed += 1
            continue
        if start <= occurred_at < end:
            selected.append((row, occurred_at))
    return selected, untimed


def _aggregate_rows(
    rows: Iterable[Tuple[sqlite3.Row, datetime]],
    zone: ZoneInfo,
    include_details: bool = True,
) -> dict:
    usage_record_count = 0
    total_tokens = 0
    token_covered_record_count = 0
    estimated_cost = Decimal("0")
    priced_record_count = 0
    primary_sessions = set()
    active_days = set()
    states: DefaultDict[str, int] = defaultdict(int)
    aggregation_scopes: DefaultDict[str, int] = defaultdict(int)
    capability_states: DefaultDict[str, int] = defaultdict(int)
    attribution_bases: DefaultDict[str, int] = defaultdict(int)
    for row, occurred_at in rows:
        usage_record_count += 1
        if row["total_tokens"] is not None:
            total_tokens += row["total_tokens"]
            token_covered_record_count += 1
        if row["calculation_state"] == "priced" and row["estimated_cost_usd"] is not None:
            estimated_cost += Decimal(row["estimated_cost_usd"])
            priced_record_count += 1
        if row["session_class"] == "work" and row["session_role"] == "primary":
            primary_sessions.add(row["session_id"])
        active_days.add(occurred_at.astimezone(zone).date())
        if include_details:
            states[row["calculation_state"]] += 1
            aggregation_scopes[row["aggregation_scope"]] += 1
            capability_states[row["capability_state"]] += 1
            attribution_bases[row["attribution_basis"]] += 1
    return {
        "usage_record_count": usage_record_count,
        "total_tokens": total_tokens if token_covered_record_count else None,
        "token_covered_record_count": token_covered_record_count,
        "estimated_cost": estimated_cost if priced_record_count else None,
        "priced_record_count": priced_record_count,
        "session_count": len(primary_sessions),
        "active_days": len(active_days),
        "calculation_states": dict(states),
        "aggregation_scopes": dict(aggregation_scopes),
        "capability_states": dict(capability_states),
        "attribution_bases": dict(attribution_bases),
    }


def _bucket_start(value: date, view: str) -> date:
    if view == "weekly":
        return value - timedelta(days=value.weekday())
    if view in {"monthly", "cumulative"}:
        return value.replace(day=1)
    return value


def _next_bucket(value: date, view: str) -> date:
    if view == "weekly":
        return value + timedelta(weeks=1)
    if view in {"monthly", "cumulative"}:
        if value.month == 12:
            return value.replace(year=value.year + 1, month=1)
        return value.replace(month=value.month + 1)
    return value + timedelta(days=1)


def _history_from_buckets(buckets: Dict[date, Decimal], scope: dict) -> List[dict]:
    current = _bucket_start(scope["from_date"], scope["view"])
    last = _bucket_start(scope["to_date"], scope["view"])
    if scope["custom"]:
        nonzero_dates = [bucket_date for bucket_date, value in buckets.items() if value > 0]
        if nonzero_dates:
            current = max(current, min(nonzero_dates))
            last = min(last, max(nonzero_dates))
    items = []
    running = Decimal("0")
    while current <= last:
        value = buckets.get(current, Decimal("0"))
        if scope["view"] == "cumulative":
            running += value
            value = running
        items.append({"date": current, "value": value})
        current = _next_bucket(current, scope["view"])

    maximum = max((item["value"] for item in items), default=Decimal("0"))
    for index, item in enumerate(items):
        item["bar_percent"] = (
            0
            if maximum == 0 or item["value"] == 0
            else max(4, round(item["value"] / maximum * 100))
        )
        item["value_label"] = (
            _format_tokens(int(item["value"]))
            if scope["metric"] == "tokens"
            else _format_cost(item["value"])
        )
        item["bar_label"] = _format_history_bar_value(item["value"], scope["metric"])
        item["label"] = (
            item["date"].strftime("%Y-%m")
            if scope["view"] in {"monthly", "cumulative"}
            else item["date"].strftime("%m/%d")
        )
        if scope["view"] == "daily":
            item["show_label"] = (
                index == 0
                or index == len(items) - 1
                or item["date"].day in {1, 15}
            )
        else:
            stride = max(1, len(items) // 6)
            item["show_label"] = index % stride == 0 or index == len(items) - 1
    return items


def _freshness(connection: sqlite3.Connection, source: str) -> dict:
    params: List[str] = []
    source_filter = ""
    if source != "all":
        source_filter = "AND sources.kind = ?"
        params.append(source)
    rows = connection.execute(
        """
        SELECT sources.kind, sources.provider_kind, sources.name,
               sources.last_scanned_at AS last_attempt_at,
               sources.last_scan_success_at,
               sources.last_scan_status,
               sources.last_scan_error,
               MAX(CASE WHEN source_files.status = 'ok'
                        THEN source_files.last_scanned_at END) AS last_healthy_file_at,
               SUM(CASE WHEN source_files.status = 'stale' THEN 1 ELSE 0 END) AS stale_count,
               SUM(CASE WHEN source_files.status = 'error' THEN 1 ELSE 0 END) AS error_count
        FROM sources
        LEFT JOIN source_files ON source_files.source_id = sources.id
        WHERE sources.provider_kind IN ('claude', 'codex') {source_filter}
        GROUP BY sources.id, sources.kind, sources.provider_kind, sources.name,
                 sources.last_scanned_at, sources.last_scan_success_at,
                 sources.last_scan_status, sources.last_scan_error
        ORDER BY sources.id
        """.format(source_filter=source_filter),
        tuple(params),
    ).fetchall()
    source_rows = []
    for row in rows:
        if row["last_scan_status"] in {
            "unavailable",
            "configuration_error",
            "scan_failed",
        }:
            row_status = "error"
        elif row["error_count"]:
            row_status = "error"
        elif row["stale_count"]:
            row_status = "stale"
        elif row["last_scan_status"] in {"completed", "empty"} or row["last_attempt_at"]:
            row_status = "current"
        else:
            row_status = "not_synchronized"
        source_rows.append(
            {
                "kind": row["kind"],
                "provider_kind": row["provider_kind"],
                "name": row["name"],
                "status": row_status,
                "scan_status": row["last_scan_status"],
                "scan_error": row["last_scan_error"],
                "last_attempt_at": row["last_attempt_at"],
                "last_successful_at": (
                    row["last_scan_success_at"]
                    or (
                        row["last_attempt_at"]
                        if row_status == "current"
                        else row["last_healthy_file_at"]
                    )
                ),
                "stale_count": row["stale_count"] or 0,
                "error_count": row["error_count"] or 0,
            }
        )
    error_count = sum(row["error_count"] for row in source_rows)
    stale_count = sum(row["stale_count"] for row in source_rows)
    successful_values = [
        row["last_successful_at"] for row in source_rows if row["last_successful_at"]
    ]
    attempt_values = [row["last_attempt_at"] for row in source_rows if row["last_attempt_at"]]
    if any(row["status"] == "error" for row in source_rows):
        status = "error"
    elif any(row["status"] == "stale" for row in source_rows):
        status = "stale"
    elif successful_values:
        status = "current"
    else:
        status = "not_synchronized"
    return {
        "status": status,
        "last_synchronized_at": max(successful_values, default=None),
        "last_attempt_at": max(attempt_values, default=None),
        "stale_count": stale_count,
        "error_count": error_count,
        "sources": source_rows,
    }


def _breakdown_identity(row: sqlite3.Row, mode: str) -> Tuple[str, str]:
    if mode == "source":
        return row["source_kind"], row["source_name"]
    if mode == "model":
        identity = row["model_name"] or row["raw_model"]
        return identity or "unknown-model", identity or "Unknown model"
    return (
        (row["project_key"], row["project_name_snapshot"] or "Attributed project")
        if row["project_key"]
        else ("unassigned", "Unassigned")
    )


def _breakdown_from_groups(
    grouped: Dict[str, dict],
    compatible_total: Decimal,
    has_compatible_total: bool,
    scope: dict,
) -> dict:
    items = []
    for group in grouped.values():
        tokens = (
            group["total_tokens"] if group["token_covered_record_count"] else None
        )
        estimated_cost = (
            group["estimated_cost"] if group["priced_record_count"] else None
        )
        metric_value = (
            Decimal(tokens)
            if scope["metric"] == "tokens" and tokens is not None
            else estimated_cost
            if scope["metric"] == "cost"
            else None
        )
        share = (
            metric_value / compatible_total * 100
            if metric_value is not None and compatible_total and has_compatible_total
            else None
        )
        evidence_url = None
        evidence_label = None
        if scope["breakdown"] == "source":
            evidence_url = "/sessions?{}".format(urlencode({"source": group["key"]}))
            evidence_label = "Browse source Sessions"
        elif scope["breakdown"] == "project" and group["current_workspace_id"]:
            evidence_url = "/sessions?{}".format(
                urlencode({"workspace": group["current_workspace_id"]})
            )
            evidence_label = "Browse current Project Sessions"
        elif len(group["primary_session_ids"]) == 1:
            evidence_url = "/sessions/{}".format(next(iter(group["primary_session_ids"])))
            evidence_label = "Open Session evidence"
        if evidence_url:
            evidence_note = None
        elif scope["breakdown"] == "model":
            evidence_note = (
                "Usage spans multiple primary Sessions."
                if group["primary_session_ids"]
                else "No primary work Session in this model group."
            )
        else:
            evidence_note = "Aggregated usage has no exact current inventory filter."
        items.append(
            {
                "key": group["key"],
                "label": group["label"],
                "source_kind": group["source_kind"],
                "provider_kind": group["provider_kind"],
                "tokens": tokens,
                "tokens_label": _format_tokens(tokens),
                "estimated_cost": estimated_cost,
                "cost_label": _format_cost(estimated_cost),
                "session_count": len(group["primary_session_ids"]),
                "usage_record_count": group["usage_record_count"],
                "token_covered_record_count": group["token_covered_record_count"],
                "priced_record_count": group["priced_record_count"],
                "share": share,
                "share_label": "Unavailable" if share is None else "{}%".format(format(share.quantize(Decimal("0.1")), "f")),
                "last_activity_at": group["last_activity_at"],
                "raw_models": sorted(group["raw_models"]),
                "metric_value": metric_value,
                "evidence_url": evidence_url,
                "evidence_label": evidence_label,
                "evidence_note": evidence_note,
            }
        )
    items.sort(
        key=lambda item: (
            item["metric_value"] is None,
            -(item["metric_value"] or Decimal("0")),
            item["label"].lower(),
        )
    )
    titles = {
        "source": ("By source", "Source provenance"),
        "model": ("By model", "Normalized model with raw identity"),
        "project": ("By Project", "First-observation Project snapshot"),
    }
    return {
        "mode": scope["breakdown"],
        "title": titles[scope["breakdown"]][0],
        "subtitle": titles[scope["breakdown"]][1],
        "rows": items,
        "primary_rows": items[:8],
        "overflow_rows": items[8:],
        "compatible_total_label": (
            _format_tokens(int(compatible_total))
            if scope["metric"] == "tokens" and has_compatible_total
            else _format_cost(compatible_total)
            if has_compatible_total
            else "Unavailable"
        ),
    }


def _dashboard_projection(
    rows: Iterable[Tuple[sqlite3.Row, datetime]],
    scope: dict,
    zone: ZoneInfo,
    include_details: bool,
) -> Tuple[dict, List[dict], dict]:
    usage_record_count = 0
    total_tokens = 0
    token_covered_record_count = 0
    estimated_cost = Decimal("0")
    priced_record_count = 0
    primary_sessions = set()
    active_days = set()
    states: DefaultDict[str, int] = defaultdict(int)
    aggregation_scopes: DefaultDict[str, int] = defaultdict(int)
    capability_states: DefaultDict[str, int] = defaultdict(int)
    attribution_bases: DefaultDict[str, int] = defaultdict(int)
    buckets: Dict[date, Decimal] = defaultdict(Decimal)
    grouped: Dict[str, dict] = {}
    compatible_total = Decimal("0")
    has_compatible_total = False
    metric = scope["metric"]
    mode = scope["breakdown"]
    view = scope["view"]

    for row, occurred_at in rows:
        usage_record_count += 1
        local_day = occurred_at.astimezone(zone).date()
        active_days.add(local_day)
        token_value = row["total_tokens"]
        cost_value = (
            Decimal(row["estimated_cost_usd"])
            if row["calculation_state"] == "priced"
            and row["estimated_cost_usd"] is not None
            else None
        )
        if token_value is not None:
            total_tokens += token_value
            token_covered_record_count += 1
        if cost_value is not None:
            estimated_cost += cost_value
            priced_record_count += 1
        is_primary = row["session_class"] == "work" and row["session_role"] == "primary"
        if is_primary:
            primary_sessions.add(row["session_id"])
        if include_details:
            states[row["calculation_state"]] += 1
            aggregation_scopes[row["aggregation_scope"]] += 1
            capability_states[row["capability_state"]] += 1
            attribution_bases[row["attribution_basis"]] += 1

        bucket_value = token_value if metric == "tokens" else cost_value
        if bucket_value is not None:
            buckets[_bucket_start(local_day, view)] += Decimal(bucket_value)

        key, label = _breakdown_identity(row, mode)
        group = grouped.get(key)
        if group is None:
            group = {
                "key": key,
                "label": label,
                "total_tokens": 0,
                "token_covered_record_count": 0,
                "estimated_cost": Decimal("0"),
                "priced_record_count": 0,
                "usage_record_count": 0,
                "raw_models": set(),
                "primary_session_ids": set(),
                "last_activity_at": occurred_at,
                "current_workspace_id": row["current_workspace_id"],
                "source_kind": row["source_kind"] if mode == "source" else None,
                "provider_kind": row["provider_kind"] if mode == "source" else None,
            }
            grouped[key] = group
        group["usage_record_count"] += 1
        if token_value is not None:
            group["total_tokens"] += token_value
            group["token_covered_record_count"] += 1
        if cost_value is not None:
            group["estimated_cost"] += cost_value
            group["priced_record_count"] += 1
        if bucket_value is not None:
            compatible_total += Decimal(bucket_value)
            has_compatible_total = True
        if row["raw_model"]:
            group["raw_models"].add(row["raw_model"])
        if is_primary:
            group["primary_session_ids"].add(row["session_id"])
        if occurred_at > group["last_activity_at"]:
            group["last_activity_at"] = occurred_at

    aggregate = {
        "usage_record_count": usage_record_count,
        "total_tokens": total_tokens if token_covered_record_count else None,
        "token_covered_record_count": token_covered_record_count,
        "estimated_cost": estimated_cost if priced_record_count else None,
        "priced_record_count": priced_record_count,
        "session_count": len(primary_sessions),
        "active_days": len(active_days),
        "calculation_states": dict(states),
        "aggregation_scopes": dict(aggregation_scopes),
        "capability_states": dict(capability_states),
        "attribution_bases": dict(attribution_bases),
    }
    return (
        aggregate,
        _history_from_buckets(buckets, scope),
        _breakdown_from_groups(grouped, compatible_total, has_compatible_total, scope),
    )


def _duration_microseconds(value: timedelta) -> Decimal:
    return Decimal(
        (value.days * 86_400 + value.seconds) * 1_000_000 + value.microseconds
    )


def current_month_projection(
    rows: Iterable[Tuple[sqlite3.Row, datetime]],
    scope: dict,
    zone: ZoneInfo,
    calculated_at: datetime,
    freshness: dict,
) -> dict:
    local_now = (
        calculated_at.astimezone(zone)
        if calculated_at.tzinfo is not None
        else calculated_at.replace(tzinfo=zone)
    )
    current_day = local_now.date()
    visible = (
        scope["metric"] == "cost"
        and scope["from_date"] <= current_day <= scope["to_date"]
    )
    base = {
        "visible": visible,
        "formula_version": PROJECTION_FORMULA_VERSION,
        "calculated_at": local_now.astimezone(timezone.utc).isoformat(),
        "source": scope["source"],
        "month": current_day.strftime("%Y-%m"),
        "projected_cost": None,
        "value_label": "Unavailable",
        "input_mtd_cost": None,
        "input_label": "Unavailable",
        "elapsed_fraction": None,
        "complete_days": (current_day - current_day.replace(day=1)).days,
        "usage_record_count": 0,
        "priced_record_count": 0,
        "coverage_state": "unavailable",
        "status": "not_applicable",
        "reason": None,
    }
    if not visible:
        return base

    aggregate = _aggregate_rows(rows, zone)
    base.update(
        {
            "input_mtd_cost": aggregate["estimated_cost"],
            "input_label": _format_cost(aggregate["estimated_cost"]),
            "usage_record_count": aggregate["usage_record_count"],
            "priced_record_count": aggregate["priced_record_count"],
        }
    )
    if base["complete_days"] < 3:
        base.update(
            {
                "status": "insufficient_history",
                "reason": "Available after three complete local-calendar days.",
            }
        )
        return base
    if aggregate["usage_record_count"] == 0:
        base.update(
            {
                "status": "no_usage",
                "reason": "No current-month usage is available for this source scope.",
            }
        )
        return base
    if aggregate["estimated_cost"] is None:
        base.update(
            {
                "status": "unavailable",
                "reason": "Current-month usage has no compatible snapshot-priced cost.",
            }
        )
        return base

    try:
        month_start = datetime.combine(
            current_day.replace(day=1), datetime.min.time(), tzinfo=zone
        )
        if current_day.month == 12:
            next_month = month_start.replace(year=current_day.year + 1, month=1)
        else:
            next_month = month_start.replace(month=current_day.month + 1)
        elapsed = _duration_microseconds(local_now - month_start)
        full_month = _duration_microseconds(next_month - month_start)
        if elapsed <= 0 or full_month <= 0:
            raise ValueError("invalid local month duration")
        elapsed_fraction = elapsed / full_month
        projected = aggregate["estimated_cost"] / elapsed_fraction
    except (ArithmeticError, ValueError):
        base.update(
            {
                "status": "failed",
                "reason": "Month-end trend could not be calculated.",
            }
        )
        return base

    coverage_state = (
        "complete"
        if aggregate["priced_record_count"] == aggregate["usage_record_count"]
        else "partial"
    )
    status = (
        "stale"
        if freshness["status"] in {"stale", "error"}
        else "partial"
        if coverage_state == "partial"
        else "current"
    )
    base.update(
        {
            "projected_cost": projected,
            "value_label": _format_cost(projected),
            "elapsed_fraction": format(
                elapsed_fraction.quantize(Decimal("0.000001")), "f"
            ),
            "coverage_state": coverage_state,
            "status": status,
            "reason": (
                "Uses compatible priced usage records only."
                if coverage_state == "partial"
                else "Directional estimate from current-month compatible usage."
            ),
        }
    )
    return base


def _scope_url(scope: dict, **updates: object) -> str:
    values = {
        "view": scope["view"],
        "source": scope["source"],
        "metric": scope["metric"],
        "breakdown": scope["breakdown"],
    }
    if scope["custom"]:
        values["from"] = scope["from_iso"]
        values["to"] = scope["to_iso"]
    values.update(updates)
    if values.get("breakdown") == "source":
        values.pop("breakdown", None)
    return "/sessions-dashboard?{}".format(urlencode(values))


def usage_dashboard_data(
    connection: sqlite3.Connection,
    view: str = "daily",
    source: str = "all",
    metric: str = "cost",
    breakdown: str = "source",
    from_value: Optional[str] = None,
    to_value: Optional[str] = None,
    timezone_name: str = "UTC",
    today: Optional[date] = None,
    now: Optional[datetime] = None,
    visible_only: bool = False,
) -> dict:
    zone = ZoneInfo(timezone_name)
    scope_today = today
    if scope_today is None and now is not None:
        scope_today = (
            now.astimezone(zone).date()
            if now.tzinfo is not None
            else now.replace(tzinfo=zone).date()
        )
    scope = normalize_usage_scope(
        connection,
        view=view,
        source=source,
        metric=metric,
        breakdown=breakdown,
        from_value=from_value,
        to_value=to_value,
        timezone_name=timezone_name,
        today=scope_today,
    )
    if visible_only:
        candidate_rows = merge(
            _usage_rows(
                connection,
                scope["source"],
                start_utc=scope["start_utc"],
                end_utc=scope["end_utc"],
                visible_only=True,
                stream=True,
            ),
            _usage_rows(
                connection,
                scope["source"],
                start_utc=scope["start_utc"],
                end_utc=scope["end_utc"],
                visible_only=True,
                unusual_only=True,
                stream=True,
            ),
            key=lambda row: (row["occurred_at"] or "", row["id"]),
        )
        untimed_count = 0

        def selected_visible_rows():
            nonlocal untimed_count
            for row in candidate_rows:
                occurred_at = parse_timestamp(row["occurred_at"])
                if occurred_at is None:
                    untimed_count += 1
                elif scope["start_utc"] <= occurred_at < scope["end_utc"]:
                    yield row, occurred_at

        aggregate, history, breakdown_result = _dashboard_projection(
            selected_visible_rows(), scope, zone, include_details=False
        )
    else:
        usage_rows = _usage_rows(connection, scope["source"])
        selected_rows, untimed_count = _rows_in_range(
            usage_rows, scope["start_utc"], scope["end_utc"]
        )
        aggregate, history, breakdown_result = _dashboard_projection(
            selected_rows, scope, zone, include_details=True
        )
    activity = None
    month_rows = []
    month_to_date = None
    current_moment = None
    if not visible_only:
        activity = activity_summary(
            connection,
            start=scope["start_utc"],
            end=scope["end_utc"],
            source_kind=None if scope["source"] == "all" else scope["source"],
        )
        current_moment = now or (
            datetime.combine(today, datetime.min.time(), tzinfo=zone)
            + timedelta(hours=12)
            if today is not None
            else datetime.now(zone)
        )
        if current_moment.tzinfo is None:
            current_moment = current_moment.replace(tzinfo=zone)
        current_day = scope_today or current_moment.astimezone(zone).date()
        month_start = current_day.replace(day=1)
        month_start_utc = datetime.combine(
            month_start, datetime.min.time(), tzinfo=zone
        ).astimezone(timezone.utc)
        month_end_utc = current_moment.astimezone(timezone.utc) + timedelta(microseconds=1)
        month_rows, _ = _rows_in_range(usage_rows, month_start_utc, month_end_utc)
        month_to_date = _aggregate_rows(month_rows, zone)

    limitations = []
    if untimed_count:
        limitations.append(
            "{} {} no usable occurrence time and {} excluded from history.".format(
                _format_usage_record_count(untimed_count),
                "has" if untimed_count == 1 else "have",
                "is" if untimed_count == 1 else "are",
            )
        )
    if aggregate["usage_record_count"] and aggregate["token_covered_record_count"] < aggregate["usage_record_count"]:
        limitations.append(
            "Token totals cover {:,} of {}.".format(
                aggregate["token_covered_record_count"],
                _format_usage_record_count(aggregate["usage_record_count"], "selected"),
            )
        )

    snapshot_labels = (
        sorted(
            {
                row["price_snapshot_label"]
                for row, _ in selected_rows
                if row["price_snapshot_label"]
            }
        )
        if not visible_only
        else []
    )
    last_calculated_at = (
        max(
            (row["calculated_at"] for row, _ in selected_rows if row["calculated_at"]),
            default=None,
        )
        if not visible_only
        else None
    )
    summary = [
        {
            "label": "Cost",
            "value": _format_cost(aggregate["estimated_cost"]),
            "detail": "{:,} of {} priced · trend estimate".format(
                aggregate["priced_record_count"],
                _format_usage_record_count(aggregate["usage_record_count"]),
            ),
            "state": "unavailable" if aggregate["estimated_cost"] is None else "default",
        },
        {
            "label": "Total tokens",
            "value": _format_tokens(aggregate["total_tokens"]),
            "detail": _format_usage_record_count(aggregate["usage_record_count"]),
            "state": "unavailable" if aggregate["total_tokens"] is None else "default",
        },
        {
            "label": "Primary work Sessions",
            "value": "{:,}".format(aggregate["session_count"]),
            "detail": "usage-linked; maintenance and subsessions excluded only here",
            "state": "default",
        },
        {
            "label": "Active days",
            "value": "{:,}".format(aggregate["active_days"]),
            "detail": (
                "{} est. active · longest segment {}".format(
                    _format_duration(activity["estimated_active_seconds"]),
                    _format_duration(activity["longest_active_segment_seconds"]),
                )
                if activity is not None
                else ""
            ),
            "state": "default",
        },
    ]

    controls = {
        "views": [
            {"value": value, "label": label, "url": _scope_url(scope, view=value)}
            for value, label in (
                ("daily", "Daily"),
                ("weekly", "Weekly"),
                ("monthly", "Monthly"),
            )
        ],
        "sources": [
            {
                "value": "all",
                "label": "All",
                "provider_kind": None,
                "url": _scope_url(scope, source="all"),
            },
            *[
                {
                    **option,
                    "url": _scope_url(scope, source=option["value"]),
                }
                for option in scope["source_options"]
            ],
        ],
        "metrics": [
            {"value": value, "label": label, "url": _scope_url(scope, metric=value)}
            for value, label in (("cost", "Cost"), ("tokens", "Tokens"))
        ],
        "breakdowns": [
            {"value": value, "label": label, "url": _scope_url(scope, breakdown=value)}
            for value, label in (
                ("source", "Source"),
                ("model", "Model"),
                ("project", "Project"),
            )
        ],
    }
    freshness = None
    projection = None
    if not visible_only:
        freshness = _freshness(connection, scope["source"])
        source_usage_record_counts: DefaultDict[str, int] = defaultdict(int)
        for row, _ in selected_rows:
            source_usage_record_counts[row["source_kind"]] += 1
        for source_row in freshness["sources"]:
            source_row["selected_usage_record_count"] = source_usage_record_counts[source_row["kind"]]
        projection = current_month_projection(
            month_rows,
            scope,
            zone,
            current_moment,
            freshness,
        )
    if visible_only:
        has_source_usage = bool(aggregate["usage_record_count"]) or _has_eligible_usage(
            connection, scope["source"]
        )
    else:
        has_source_usage = bool(usage_rows)
    return {
        "scope": scope,
        "controls": controls,
        "summary": summary,
        "aggregate": aggregate,
        "month_to_date": (
            {
                **month_to_date,
                "tokens_label": _format_tokens(month_to_date["total_tokens"]),
                "cost_label": _format_cost(month_to_date["estimated_cost"]),
            }
            if month_to_date is not None
            else None
        ),
        "activity": activity,
        "history": history,
        "history_has_values": bool(
            aggregate["token_covered_record_count"]
            if scope["metric"] == "tokens"
            else aggregate["priced_record_count"]
        ),
        "history_title": (
            "Cumulative cost"
            if scope["view"] == "cumulative" and scope["metric"] == "cost"
            else "Cumulative tokens"
            if scope["view"] == "cumulative"
            else "Monthly cost"
            if scope["view"] == "monthly" and scope["metric"] == "cost"
            else "Monthly tokens"
            if scope["view"] == "monthly"
            else "Cost history"
            if scope["metric"] == "cost"
            else "Token history"
        ),
        "history_unit": "USD" if scope["metric"] == "cost" else "normalized tokens",
        "freshness": freshness,
        "projection": projection,
        "breakdown": breakdown_result,
        "last_calculated_at": last_calculated_at,
        "snapshot_labels": snapshot_labels,
        "limitations": limitations,
        "has_usage": bool(aggregate["usage_record_count"]),
        "empty_kind": "source" if not has_source_usage else "filtered",
    }
