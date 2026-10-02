"""Observed ephemeral analysis usage, independent of report success."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from pathlib import Path

from .ingest.common import ParsedUsageRecord, stable_id, token_value
from .official_pricing import select_snapshot
from .usage import normalize_model, store_usage_records
from .usage_queries import _format_cost


NORMALIZER_VERSION = "personal-insight-cli-usage-v1"
SESSION_PREFIX = "localbrain-insight:"
logger = logging.getLogger(__name__)


def insight_usage_cost(connection, run_id: str) -> dict | None:
    """Read the same stored estimate used by Usage & Cost; never price on GET."""
    row = connection.execute(
        """SELECT usage.calculation_state, usage.estimated_cost_usd,
                  usage.price_snapshot_id, prices.label AS price_label
           FROM usage_records AS usage
           LEFT JOIN usage_price_snapshots AS prices ON prices.id = usage.price_snapshot_id
           WHERE usage.id = ? AND usage.normalizer_version = ?""",
        (stable_id("personal-insight-usage", run_id), NORMALIZER_VERSION),
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    cost = (
        Decimal(row["estimated_cost_usd"])
        if row["calculation_state"] == "priced" and row["estimated_cost_usd"] is not None
        else None
    )
    result["cost_label"] = (
        "<$0.0001" if cost is not None and 0 < cost < Decimal("0.0001")
        else _format_cost(cost) if cost is not None else None
    )
    return result


def insight_usage_source(connection, options: dict) -> dict:
    """Resolve only the exact registered home, never a similarly named account."""
    root = (Path(options["codex_home"]).expanduser() / "sessions").resolve()
    matches = [
        dict(row) for row in connection.execute(
            "SELECT id, kind, root_path FROM sources WHERE provider_kind = 'codex'"
        )
        if Path(row["root_path"]).expanduser().resolve() == root
        and (not options.get("usage_source_key") or row["kind"] == options["usage_source_key"])
    ]
    if len(matches) != 1:
        raise ValueError("분석 프로필의 비용 집계 Source를 확인할 수 없습니다. Sources에서 해당 Codex 홈을 등록해 주세요.")
    return matches[0]


def _usage_record(run: dict, usage: dict, options: dict, occurred_at: str, source_line: int):
    components = {}
    malformed = False

    def component(key):
        nonlocal malformed
        if key not in usage:
            components[key] = "missing"
            return None
        value, state = token_value(usage[key])
        if value is not None and value > 2**63 - 1:
            value, state = None, "malformed"
        components[key] = state
        malformed |= state == "malformed"
        return value

    inclusive_input = component("input_tokens")
    cached_input = component("cached_input_tokens")
    output = component("output_tokens")
    reasoning = component("reasoning_output_tokens")
    input_tokens = None
    if inclusive_input is not None and cached_input is not None:
        if cached_input > inclusive_input:
            malformed = True
            components["cached_input_tokens"] = "malformed_exceeds_input"
        else:
            input_tokens = inclusive_input - cached_input
    if reasoning is not None and output is not None and reasoning > output:
        malformed = True
        components["reasoning_output_tokens"] = "malformed_exceeds_output"
    total = inclusive_input + output if inclusive_input is not None and output is not None else None
    if total is not None and total > 2**63 - 1:
        malformed, total = True, None
    model = run.get("resolved_model") or run["model"]
    normalized_model = normalize_model(model)
    tier = options.get("service_tier", "standard")
    components.update({
        "usage_source": "codex_exec_turn_completed",
        "usage_evidence": "run_stream" if source_line else "retained_run_usage_json",
        "context_scope": "turn_total",
        "model_resolution": "observed" if run.get("resolved_model") else "selected_unverified",
        "service_tier": tier,
        "service_tier_source": "frozen_run_setting" if "service_tier" in options else "unmarked_default_assumption",
        "cache_write_tokens": "not_supported",
        "insight_run_id": run["id"],
    })
    identity = stable_id("personal-insight-usage", run["id"])
    return ParsedUsageRecord(
        usage_record_id=identity, source_record_id=run["id"], source_line=source_line,
        occurred_at=occurred_at, raw_model=model, normalized_model=normalized_model,
        input_tokens=input_tokens, output_tokens=output, cache_write_tokens=None,
        cache_read_tokens=cached_input, reasoning_tokens=reasoning,
        source_total_tokens=None, total_tokens=total,
        total_semantics=(
            "codex_exec_turn_total;source_input_includes_cache_read;"
            "normalized_non_cached_input_plus_output_plus_cache_read;reasoning_subset_of_output"
        ),
        capability_state=(
            "malformed" if malformed else "partial"
            if None in (input_tokens, cached_input, output, reasoning) else "complete"
        ),
        capability=components,
        price_snapshot_id=select_snapshot(
            "codex", normalized_model, occurred_at, tier,
            context_input_tokens=inclusive_input,
        ),
    )


def store_insight_usage(connection, run: dict, usage: dict, *, observed_at: str, source_line: int = 0) -> None:
    """Upsert one Run summary; repeated reads cannot create additional usage."""
    options = json.loads(run["settings_json"])
    source = insight_usage_source(connection, options)
    record = _usage_record(run, usage, options, observed_at, source_line)
    existing = connection.execute(
        "SELECT occurred_at, price_snapshot_id FROM usage_records WHERE id = ?",
        (record.usage_record_id,),
    ).fetchone()
    if existing:
        record.occurred_at = existing["occurred_at"]
        record.price_snapshot_id = existing["price_snapshot_id"]
    connection.execute(
        """INSERT INTO sessions(
            source_id, external_id, source_path, cwd_raw, title, started_at,
            ended_at, last_event_at, session_class, session_role, index_policy
        ) VALUES (?, ?, ?, ?, 'Insights analysis', ?, ?, ?, 'maintenance', 'primary', 'metadata_only')
        ON CONFLICT(source_id, external_id) DO UPDATE SET
            ended_at = excluded.ended_at, last_event_at = excluded.last_event_at""",
        (
            source["id"], SESSION_PREFIX + run["id"], run["stream_path"],
            str(Path(run["stream_path"]).parent), run.get("started_at") or run["created_at"],
            run.get("completed_at") or observed_at, record.occurred_at,
        ),
    )
    session_id = connection.execute(
        "SELECT id FROM sessions WHERE source_id = ? AND external_id = ?",
        (source["id"], SESSION_PREFIX + run["id"]),
    ).fetchone()["id"]
    store_usage_records(
        connection, source["id"], session_id, [record],
        normalizer_version=NORMALIZER_VERSION,
    )
    connection.execute(
        "UPDATE personal_insight_runs SET usage_json = ?, resolved_model = COALESCE(?, resolved_model) WHERE id = ?",
        (json.dumps(usage, ensure_ascii=False), run.get("resolved_model"), run["id"]),
    )


def recover_insight_usage(connection) -> int:
    """Recover terminal Runs from retained observations without invoking a model."""
    recovered = 0
    rows = connection.execute(
        "SELECT * FROM personal_insight_runs WHERE status NOT IN ('queued', 'running')",
    ).fetchall()
    for row in rows:
        run = dict(row)
        # The usage table can be large; use its primary key rather than scanning
        # all native observations for each retained analysis Run on startup.
        if connection.execute(
            "SELECT 1 FROM usage_records WHERE id = ? AND normalizer_version = ?",
            (stable_id("personal-insight-usage", run["id"]), NORMALIZER_VERSION),
        ).fetchone():
            continue
        try:
            usage = json.loads(run["usage_json"]) if run["usage_json"] else None
            source_line = 0
            if not isinstance(usage, dict):
                path = Path(run["stream_path"])
                if not path.is_file():
                    continue
                with path.open(encoding="utf-8", errors="replace") as stream:
                    for number, line in enumerate(stream, 1):
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(event, dict):
                            continue
                        if isinstance(event.get("model"), str):
                            run["resolved_model"] = event["model"]
                        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                            usage, source_line = event["usage"], number
            if not isinstance(usage, dict):
                continue
            connection.execute("SAVEPOINT insight_usage_recovery")
            try:
                store_insight_usage(
                    connection, run, usage, source_line=source_line,
                    observed_at=run["completed_at"] or run["started_at"] or run["created_at"],
                )
            except Exception:
                connection.execute("ROLLBACK TO insight_usage_recovery")
                raise
            finally:
                connection.execute("RELEASE insight_usage_recovery")
            recovered += 1
        except (OSError, ValueError, KeyError, TypeError):
            logger.warning("Insight usage recovery unavailable for %s", run["id"])
    return recovered
