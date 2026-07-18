import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from .activity import activity_summary, parse_timestamp


VALID_VIEWS = {"daily", "weekly", "cumulative"}
VALID_SOURCES = {"all", "claude", "codex"}
VALID_METRICS = {"tokens", "cost"}
VALID_BREAKDOWNS = {"source", "model", "project"}
PROJECTION_FORMULA_VERSION = "calendar-elapsed-v1"
CLAUDE_SYNTHETIC_MODEL = "<synthetic>"


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


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


def _format_duration(seconds: int) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes = remainder // 60
    if hours:
        return "{}h {}m".format(hours, minutes)
    return "{}m".format(minutes)


def _local_date(timestamp: object, zone: ZoneInfo) -> Optional[date]:
    parsed = timestamp if isinstance(timestamp, datetime) else parse_timestamp(timestamp)
    if parsed is None:
        return None
    return parsed.astimezone(zone).date()


def _earliest_usage_date(
    connection: sqlite3.Connection, source: str, zone: ZoneInfo
) -> Optional[date]:
    params: List[str] = [CLAUDE_SYNTHETIC_MODEL]
    source_filter = ""
    if source != "all":
        source_filter = "AND sources.kind = ?"
        params.append(source)
    rows = connection.execute(
        """
        SELECT usage_facts.occurred_at
        FROM usage_facts
        JOIN sources ON sources.id = usage_facts.source_id
        WHERE usage_facts.occurred_at IS NOT NULL
          AND NOT (
              sources.kind = 'claude'
              AND COALESCE(usage_facts.raw_model, '') = ?
          )
        {source_filter}
        """.format(source_filter=source_filter),
        tuple(params),
    ).fetchall()
    values = [
        value
        for value in (_local_date(row["occurred_at"], zone) for row in rows)
        if value is not None
    ]
    return min(values) if values else None


def normalize_usage_scope(
    connection: sqlite3.Connection,
    view: str = "daily",
    source: str = "all",
    metric: str = "tokens",
    breakdown: str = "source",
    from_value: Optional[str] = None,
    to_value: Optional[str] = None,
    timezone_name: str = "UTC",
    today: Optional[date] = None,
) -> dict:
    selected_view = view if view in VALID_VIEWS else "daily"
    selected_source = source if source in VALID_SOURCES else "all"
    selected_metric = metric if metric in VALID_METRICS else "tokens"
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


def _usage_rows(connection: sqlite3.Connection, source: str) -> List[sqlite3.Row]:
    params: List[str] = [CLAUDE_SYNTHETIC_MODEL]
    source_filter = ""
    if source != "all":
        source_filter = "AND sources.kind = ?"
        params.append(source)
    return connection.execute(
        """
        SELECT usage_facts.*, sources.kind AS source_kind,
               sessions.session_class, sessions.session_role, sessions.title AS session_title,
               usage_price_snapshots.label AS price_snapshot_label,
               current_workspace.id AS current_workspace_id,
               current_workspace.exists_now AS current_workspace_exists
        FROM usage_facts
        JOIN sources ON sources.id = usage_facts.source_id
        JOIN sessions ON sessions.id = usage_facts.session_id
        LEFT JOIN usage_price_snapshots
          ON usage_price_snapshots.id = usage_facts.price_snapshot_id
        LEFT JOIN workspaces AS current_workspace
          ON current_workspace.id = usage_facts.workspace_id_snapshot
        WHERE NOT (
            sources.kind = 'claude'
            AND COALESCE(usage_facts.raw_model, '') = ?
        ) {source_filter}
        ORDER BY usage_facts.occurred_at, usage_facts.id
        """.format(source_filter=source_filter),
        tuple(params),
    ).fetchall()


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


def _aggregate_rows(rows: Iterable[Tuple[sqlite3.Row, datetime]], zone: ZoneInfo) -> dict:
    rows = list(rows)
    token_values = [row["total_tokens"] for row, _ in rows if row["total_tokens"] is not None]
    priced_values = [
        Decimal(row["estimated_cost_usd"])
        for row, _ in rows
        if row["calculation_state"] == "priced" and row["estimated_cost_usd"] is not None
    ]
    primary_sessions = {
        row["session_id"]
        for row, _ in rows
        if row["session_class"] == "work" and row["session_role"] == "primary"
    }
    active_days = {occurred_at.astimezone(zone).date() for _, occurred_at in rows}
    states: DefaultDict[str, int] = defaultdict(int)
    for row, _ in rows:
        states[row["calculation_state"]] += 1
    state_counts = dict(states)
    return {
        "fact_count": len(rows),
        "total_tokens": sum(token_values) if token_values else None,
        "token_fact_count": len(token_values),
        "estimated_cost": sum(priced_values, Decimal("0")) if priced_values else None,
        "priced_fact_count": len(priced_values),
        "session_count": len(primary_sessions),
        "active_days": len(active_days),
        "calculation_states": state_counts,
        "calculation_state_label": " · ".join(
            "{} {}".format(state, count)
            for state, count in sorted(state_counts.items())
        )
        or "No calculations",
    }


def _bucket_start(value: date, view: str) -> date:
    if view == "weekly":
        return value - timedelta(days=value.weekday())
    if view == "cumulative":
        return value.replace(day=1)
    return value


def _next_bucket(value: date, view: str) -> date:
    if view == "weekly":
        return value + timedelta(weeks=1)
    if view == "cumulative":
        if value.month == 12:
            return value.replace(year=value.year + 1, month=1)
        return value.replace(month=value.month + 1)
    return value + timedelta(days=1)


def _history(
    rows: Iterable[Tuple[sqlite3.Row, datetime]], scope: dict, zone: ZoneInfo
) -> List[dict]:
    buckets: Dict[date, Decimal] = defaultdict(Decimal)
    for row, occurred_at in rows:
        local_day = occurred_at.astimezone(zone).date()
        key = _bucket_start(local_day, scope["view"])
        if scope["metric"] == "tokens":
            if row["total_tokens"] is not None:
                buckets[key] += Decimal(row["total_tokens"])
        elif row["calculation_state"] == "priced" and row["estimated_cost_usd"]:
            buckets[key] += Decimal(row["estimated_cost_usd"])

    current = _bucket_start(scope["from_date"], scope["view"])
    last = _bucket_start(scope["to_date"], scope["view"])
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
        item["label"] = (
            item["date"].strftime("%Y-%m")
            if scope["view"] == "cumulative"
            else item["date"].strftime("%m/%d")
        )
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
        SELECT sources.kind, sources.name, sources.last_scanned_at AS last_attempt_at,
               MAX(CASE WHEN source_files.status = 'ok'
                        THEN source_files.last_scanned_at END) AS last_healthy_file_at,
               SUM(CASE WHEN source_files.status = 'stale' THEN 1 ELSE 0 END) AS stale_count,
               SUM(CASE WHEN source_files.status = 'error' THEN 1 ELSE 0 END) AS error_count
        FROM sources
        LEFT JOIN source_files ON source_files.source_id = sources.id
        WHERE sources.kind IN ('claude', 'codex') {source_filter}
        GROUP BY sources.id, sources.kind, sources.name, sources.last_scanned_at
        ORDER BY sources.kind
        """.format(source_filter=source_filter),
        tuple(params),
    ).fetchall()
    source_rows = []
    for row in rows:
        if row["error_count"]:
            row_status = "error"
        elif row["stale_count"]:
            row_status = "stale"
        elif row["last_attempt_at"]:
            row_status = "current"
        else:
            row_status = "not_synchronized"
        source_rows.append(
            {
                "kind": row["kind"],
                "name": row["name"],
                "status": row_status,
                "last_attempt_at": row["last_attempt_at"],
                "last_successful_at": (
                    row["last_attempt_at"]
                    if row_status == "current"
                    else row["last_healthy_file_at"]
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
    if error_count:
        status = "error"
    elif stale_count:
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
        return row["source_kind"], {
            "claude": "Claude",
            "codex": "Codex",
        }.get(row["source_kind"], row["source_kind"].title())
    if mode == "model":
        identity = row["model_name"] or row["raw_model"]
        return identity or "unknown-model", identity or "Unknown model"
    return (
        (row["project_key"], row["project_name_snapshot"] or "Attributed project")
        if row["project_key"]
        else ("unassigned", "Unassigned")
    )


def _breakdown(
    rows: Iterable[Tuple[sqlite3.Row, datetime]], scope: dict, zone: ZoneInfo
) -> dict:
    selected_rows = list(rows)
    compatible_total = (
        sum(
            (Decimal(row["total_tokens"]) for row, _ in selected_rows if row["total_tokens"] is not None),
            Decimal("0"),
        )
        if scope["metric"] == "tokens"
        else sum(
            (
                Decimal(row["estimated_cost_usd"])
                for row, _ in selected_rows
                if row["calculation_state"] == "priced"
                and row["estimated_cost_usd"] is not None
            ),
            Decimal("0"),
        )
    )
    has_compatible_total = any(
        row["total_tokens"] is not None
        if scope["metric"] == "tokens"
        else row["calculation_state"] == "priced" and row["estimated_cost_usd"] is not None
        for row, _ in selected_rows
    )
    grouped: Dict[str, dict] = {}
    for row, occurred_at in selected_rows:
        key, label = _breakdown_identity(row, scope["breakdown"])
        group = grouped.setdefault(
            key,
            {
                "key": key,
                "label": label,
                "rows": [],
                "raw_models": set(),
                "primary_session_ids": set(),
                "current_workspace_id": row["current_workspace_id"],
                "source_kind": row["source_kind"] if scope["breakdown"] == "source" else None,
            },
        )
        group["rows"].append((row, occurred_at))
        if row["raw_model"]:
            group["raw_models"].add(row["raw_model"])
        if row["session_class"] == "work" and row["session_role"] == "primary":
            group["primary_session_ids"].add(row["session_id"])

    items = []
    for group in grouped.values():
        aggregate = _aggregate_rows(group["rows"], zone)
        metric_value = (
            Decimal(aggregate["total_tokens"])
            if scope["metric"] == "tokens" and aggregate["total_tokens"] is not None
            else aggregate["estimated_cost"]
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
        items.append(
            {
                "key": group["key"],
                "label": group["label"],
                "source_kind": group["source_kind"],
                "tokens": aggregate["total_tokens"],
                "tokens_label": _format_tokens(aggregate["total_tokens"]),
                "estimated_cost": aggregate["estimated_cost"],
                "cost_label": _format_cost(aggregate["estimated_cost"]),
                "session_count": aggregate["session_count"],
                "fact_count": aggregate["fact_count"],
                "token_fact_count": aggregate["token_fact_count"],
                "priced_fact_count": aggregate["priced_fact_count"],
                "share": share,
                "share_label": "Unavailable" if share is None else "{}%".format(format(share.quantize(Decimal("0.1")), "f")),
                "last_activity_at": max(
                    (occurred_at for _, occurred_at in group["rows"]), default=None
                ),
                "raw_models": sorted(group["raw_models"]),
                "metric_value": metric_value,
                "evidence_url": evidence_url,
                "evidence_label": evidence_label,
                "evidence_note": None if evidence_url else "Aggregated usage has no exact current inventory filter.",
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
        "fact_count": 0,
        "priced_fact_count": 0,
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
            "fact_count": aggregate["fact_count"],
            "priced_fact_count": aggregate["priced_fact_count"],
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
    if aggregate["fact_count"] == 0:
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
        if aggregate["priced_fact_count"] == aggregate["fact_count"]
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
                "Uses compatible priced facts only."
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
    metric: str = "tokens",
    breakdown: str = "source",
    from_value: Optional[str] = None,
    to_value: Optional[str] = None,
    timezone_name: str = "UTC",
    today: Optional[date] = None,
    now: Optional[datetime] = None,
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
    all_rows = _usage_rows(connection, scope["source"])
    selected_rows, untimed_count = _rows_in_range(
        all_rows, scope["start_utc"], scope["end_utc"]
    )
    aggregate = _aggregate_rows(selected_rows, zone)
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
    month_rows, _ = _rows_in_range(all_rows, month_start_utc, month_end_utc)
    month_to_date = _aggregate_rows(month_rows, zone)

    limitations = []
    if untimed_count:
        limitations.append(
            "{} usage facts have no usable occurrence time and are excluded from history.".format(
                untimed_count
            )
        )
    unavailable_cost_count = aggregate["fact_count"] - aggregate["priced_fact_count"]
    if aggregate["fact_count"] and unavailable_cost_count:
        limitations.append(
            "Estimated cost covers {} of {} selected usage facts; unsupported or incomplete pricing remains unavailable.".format(
                aggregate["priced_fact_count"], aggregate["fact_count"]
            )
        )
    if aggregate["fact_count"] and aggregate["token_fact_count"] < aggregate["fact_count"]:
        limitations.append(
            "Token totals cover {} of {} selected usage facts.".format(
                aggregate["token_fact_count"], aggregate["fact_count"]
            )
        )

    snapshot_labels = sorted(
        {
            row["price_snapshot_label"]
            for row, _ in selected_rows
            if row["price_snapshot_label"]
        }
    )
    last_calculated_at = max(
        (row["calculated_at"] for row, _ in selected_rows if row["calculated_at"]),
        default=None,
    )
    summary = [
        {
            "label": "Estimated cost",
            "value": _format_cost(aggregate["estimated_cost"]),
            "detail": "{} of {} facts priced · trend estimate".format(
                aggregate["priced_fact_count"], aggregate["fact_count"]
            ),
            "state": "unavailable" if aggregate["estimated_cost"] is None else "default",
        },
        {
            "label": "Total tokens",
            "value": _format_tokens(aggregate["total_tokens"]),
            "detail": "{} normalized usage facts".format(aggregate["fact_count"]),
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
            "detail": "{} est. active · longest segment {}".format(
                _format_duration(activity["estimated_active_seconds"]),
                _format_duration(activity["longest_active_segment_seconds"]),
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
                ("cumulative", "Cumulative"),
            )
        ],
        "sources": [
            {"value": value, "label": label, "url": _scope_url(scope, source=value)}
            for value, label in (
                ("all", "All"),
                ("claude", "Claude"),
                ("codex", "Codex"),
            )
        ],
        "metrics": [
            {"value": value, "label": label, "url": _scope_url(scope, metric=value)}
            for value, label in (("tokens", "Tokens"), ("cost", "Cost"))
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
    freshness = _freshness(connection, scope["source"])
    source_fact_counts: DefaultDict[str, int] = defaultdict(int)
    for row, _ in selected_rows:
        source_fact_counts[row["source_kind"]] += 1
    for source_row in freshness["sources"]:
        source_row["selected_fact_count"] = source_fact_counts[source_row["kind"]]
    projection = current_month_projection(
        month_rows,
        scope,
        zone,
        current_moment,
        freshness,
    )
    return {
        "scope": scope,
        "controls": controls,
        "summary": summary,
        "aggregate": aggregate,
        "month_to_date": {
            **month_to_date,
            "tokens_label": _format_tokens(month_to_date["total_tokens"]),
            "cost_label": _format_cost(month_to_date["estimated_cost"]),
        },
        "activity": activity,
        "history": _history(selected_rows, scope, zone),
        "history_has_values": bool(
            aggregate["token_fact_count"]
            if scope["metric"] == "tokens"
            else aggregate["priced_fact_count"]
        ),
        "history_title": (
            "Cumulative estimated cost"
            if scope["view"] == "cumulative" and scope["metric"] == "cost"
            else "Cumulative tokens"
            if scope["view"] == "cumulative"
            else "Estimated cost history"
            if scope["metric"] == "cost"
            else "Token history"
        ),
        "history_unit": "estimated USD" if scope["metric"] == "cost" else "normalized tokens",
        "freshness": freshness,
        "projection": projection,
        "breakdown": _breakdown(selected_rows, scope, zone),
        "last_calculated_at": last_calculated_at,
        "snapshot_labels": snapshot_labels,
        "limitations": limitations,
        "has_usage": bool(aggregate["fact_count"]),
        "empty_kind": "source" if not all_rows else "filtered",
        "clear_date_url": "/sessions-dashboard?{}".format(
            urlencode(
                {
                    "view": scope["view"],
                    "source": scope["source"],
                    "metric": scope["metric"],
                    **(
                        {"breakdown": scope["breakdown"]}
                        if scope["breakdown"] != "source"
                        else {}
                    ),
                }
            )
        ),
    }
