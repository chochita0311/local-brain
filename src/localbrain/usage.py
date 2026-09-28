import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Iterable, Optional, Tuple

from .ingest.common import ParsedUsageRecord, stable_id
from .official_pricing import (
    FAST_LONG_CONTEXT_PROXY_SPECS,
    INSPECTED_ON,
    PRICE_SPECS,
    SPARK_PROXY_SPECS,
    UNAVAILABLE_SNAPSHOT_ID,
    claude_1h_cache_rate,
    select_snapshot,
)


DEFAULT_PRICE_SNAPSHOT_ID = "ccusage-20.0.14-litellm-20260718"
CODEX_FAST_PRICE_SNAPSHOT_ID = "ccusage-20.0.17-codex-fast-20260718"
CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID = (
    "ccusage-20.0.17-codex-fast-context-tier-20260718"
)
CODEX_FAST_TIERED_SPARK_PRICE_SNAPSHOT_ID = (
    "ccusage-20.0.17-codex-fast-context-tier-spark-20260820"
)
CODEX_FAST_TIERED_ASTRA_INITIAL_PRICE_SNAPSHOT_ID = (
    "ccusage-codex-fast-context-tier-astra-20260924"
)
CODEX_FAST_TIERED_ASTRA_PRICE_SNAPSHOT_ID = (
    "ccusage-codex-fast-context-tier-astra-codex-fields-20260924"
)
CODEX_FAST_TIERED_SOL_PRICE_SNAPSHOT_ID = (
    "ccusage-codex-fast-context-tier-sol-codex-fields-20260924"
)
CALCULATOR_VERSION = "localbrain-usage-cost-v1"
CONTEXT_TIER_CALCULATOR_VERSION = "localbrain-usage-cost-v2-context-tier"
OFFICIAL_CALCULATOR_VERSION = "localbrain-usage-cost-v3-official-dated-tier"


class UsagePersistenceCache:
    def __init__(self) -> None:
        self.defaults_ready = False
        self.price_rows: Dict[
            tuple[str, Optional[str]], Optional[sqlite3.Row]
        ] = {}
        self.calculator_versions: Dict[str, str] = {}


DEFAULT_MODEL_PRICES: Dict[str, Tuple[str, str, Optional[str], Optional[str]]] = {
    "claude-haiku-4-5-20251001": ("1", "5", "1.25", "0.10"),
    "claude-sonnet-4-6": ("3", "15", "3.75", "0.30"),
    "gpt-5.5": ("5", "30", None, "0.50"),
}

CODEX_FAST_MODEL_PRICES: Dict[
    str, Tuple[str, str, Optional[str], Optional[str]]
] = {
    "gpt-5.5": ("12.5", "75", None, "1.25"),
    "gpt-5.6-sol": ("10", "60", None, "1"),
    "gpt-5.6-terra": ("5", "30", None, "0.50"),
    "gpt-5.6-luna": ("2", "12", None, "0.20"),
}

CODEX_FAST_TIERED_MODEL_PRICES = {
    "gpt-5.5": (
        "12.5",
        "75",
        None,
        "1.25",
        272_000,
        "25",
        "112.5",
        None,
        "2.5",
    ),
    "gpt-5.6-sol": (
        "10",
        "60",
        None,
        "1",
        272_000,
        "20",
        "90",
        None,
        "2",
    ),
    "gpt-5.6-terra": (
        "5",
        "30",
        None,
        "0.50",
        272_000,
        "10",
        "45",
        None,
        "1",
    ),
    "gpt-5.6-luna": (
        "2",
        "12",
        None,
        "0.20",
        200_000,
        "4",
        "18",
        None,
        "0.40",
    ),
}

CODEX_FAST_TIERED_SPARK_MODEL_PRICES = {
    **CODEX_FAST_TIERED_MODEL_PRICES,
    "gpt-5.3-codex-spark": (
        "3.5",
        "28",
        None,
        "0.35",
        None,
        None,
        None,
        None,
        None,
    ),
}

# Preserve the first snapshot for databases that observed the incomplete correction.
CODEX_FAST_TIERED_ASTRA_INITIAL_MODEL_PRICES = {
    "gpt-6-astra": (
        "10",
        "50",
        "12.5",
        "1",
        272_000,
        "20",
        "75",
        "25",
        "2",
    ),
}

CODEX_FAST_TIERED_ASTRA_MODEL_PRICES = {
    "gpt-6-astra": (
        "10",
        "50",
        None,
        "1",
        272_000,
        "20",
        "75",
        None,
        "2",
    ),
}

CODEX_FAST_TIERED_SOL_MODEL_PRICES = {
    "gpt-6-sol": (
        "4",
        "20",
        None,
        "0.40",
        272_000,
        "8",
        "30",
        None,
        "0.80",
    ),
}

MODEL_ALIASES = {
    "anthropic/claude-haiku-4-5-20251001": "claude-haiku-4-5-20251001",
    "anthropic/claude-sonnet-4-6": "claude-sonnet-4-6",
    "openai/gpt-5.5": "gpt-5.5",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_model(raw_model: Optional[str]) -> Optional[str]:
    if not raw_model:
        return None
    value = raw_model.strip()
    if not value:
        return None
    if value.startswith(("anthropic/", "openai/")):
        return value.split("/", 1)[1]
    return MODEL_ALIASES.get(value, value)


def ensure_default_price_snapshot(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            DEFAULT_PRICE_SNAPSHOT_ID,
            "ccusage 20.0.14 embedded LiteLLM reference",
            "local inspection of ccusage 20.0.14 on 2026-07-18",
            CALCULATOR_VERSION,
            "2026-07-18T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (DEFAULT_PRICE_SNAPSHOT_ID, model_name) + rates
            for model_name, rates in DEFAULT_MODEL_PRICES.items()
        ],
    )


    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            CODEX_FAST_TIERED_SPARK_PRICE_SNAPSHOT_ID,
            "ccusage 20.0.17 Codex fast request-tier plus Spark trend reference",
            (
                "local parity inspection of ccusage 20.0.17 offline Codex "
                "pricing and fast multiplier on 2026-08-20"
            ),
            CONTEXT_TIER_CALCULATOR_VERSION,
            "2026-08-20T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million, long_context_threshold_tokens,
            long_context_input_usd_per_million,
            long_context_output_usd_per_million,
            long_context_cache_write_usd_per_million,
            long_context_cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (CODEX_FAST_TIERED_SPARK_PRICE_SNAPSHOT_ID, model_name) + rates
            for model_name, rates in CODEX_FAST_TIERED_SPARK_MODEL_PRICES.items()
        ],
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            CODEX_FAST_TIERED_ASTRA_INITIAL_PRICE_SNAPSHOT_ID,
            "Superseded Codex Fast GPT-6 Astra trend reference",
            (
                "ccusage Codex Fast model rule and OpenAI GPT-6 Astra rates "
                "inspected on 2026-09-24; cache-write fields unavailable in Codex logs"
            ),
            CONTEXT_TIER_CALCULATOR_VERSION,
            "2026-09-24T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million, long_context_threshold_tokens,
            long_context_input_usd_per_million,
            long_context_output_usd_per_million,
            long_context_cache_write_usd_per_million,
            long_context_cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (CODEX_FAST_TIERED_ASTRA_INITIAL_PRICE_SNAPSHOT_ID, model_name) + rates
            for model_name, rates in CODEX_FAST_TIERED_ASTRA_INITIAL_MODEL_PRICES.items()
        ],
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            CODEX_FAST_TIERED_ASTRA_PRICE_SNAPSHOT_ID,
            "ccusage Codex Fast GPT-6 Astra trend reference",
            (
                "ccusage Codex input, cache-read, and output fields with OpenAI "
                "GPT-6 Astra Fast rates inspected on 2026-09-24"
            ),
            CONTEXT_TIER_CALCULATOR_VERSION,
            "2026-09-24T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million, long_context_threshold_tokens,
            long_context_input_usd_per_million,
            long_context_output_usd_per_million,
            long_context_cache_write_usd_per_million,
            long_context_cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (CODEX_FAST_TIERED_ASTRA_PRICE_SNAPSHOT_ID, model_name) + rates
            for model_name, rates in CODEX_FAST_TIERED_ASTRA_MODEL_PRICES.items()
        ],
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            CODEX_FAST_TIERED_SOL_PRICE_SNAPSHOT_ID,
            "ccusage Codex Fast GPT-6 Sol trend reference",
            (
                "ccusage Codex token-component method and OpenAI GPT-6 Sol "
                "Fast rates inspected on 2026-09-24; ccusage 20.0.17 offline "
                "does not include the Sol rate"
            ),
            CONTEXT_TIER_CALCULATOR_VERSION,
            "2026-09-24T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million, long_context_threshold_tokens,
            long_context_input_usd_per_million,
            long_context_output_usd_per_million,
            long_context_cache_write_usd_per_million,
            long_context_cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (CODEX_FAST_TIERED_SOL_PRICE_SNAPSHOT_ID, model_name) + rates
            for model_name, rates in CODEX_FAST_TIERED_SOL_MODEL_PRICES.items()
        ],
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,
            "ccusage 20.0.17 Codex fast request-tier trend reference",
            (
                "local inspection of ccusage 20.0.17 fast base and "
                "long-context request pricing on 2026-07-18"
            ),
            CONTEXT_TIER_CALCULATOR_VERSION,
            "2026-07-18T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million, long_context_threshold_tokens,
            long_context_input_usd_per_million,
            long_context_output_usd_per_million,
            long_context_cache_write_usd_per_million,
            long_context_cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID, model_name) + rates
            for model_name, rates in CODEX_FAST_TIERED_MODEL_PRICES.items()
        ],
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            CODEX_FAST_PRICE_SNAPSHOT_ID,
            "ccusage 20.0.17 Codex fast-tier trend reference",
            (
                "local inspection of ccusage 20.0.17 embedded pricing and "
                "fast multipliers on 2026-07-18"
            ),
            CALCULATOR_VERSION,
            "2026-07-18T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (CODEX_FAST_PRICE_SNAPSHOT_ID, model_name) + rates
            for model_name, rates in CODEX_FAST_MODEL_PRICES.items()
        ],
    )


def ensure_official_price_snapshots(connection: sqlite3.Connection) -> None:
    """Seed dated publisher rates and explicitly labeled trend proxies."""
    price_specs = (*PRICE_SPECS, *SPARK_PROXY_SPECS, *FAST_LONG_CONTEXT_PROXY_SPECS)
    connection.execute(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            UNAVAILABLE_SNAPSHOT_ID,
            "No independently published model price",
            "OpenAI and Anthropic official pricing inspected on " + INSPECTED_ON,
            OFFICIAL_CALCULATOR_VERSION,
            INSPECTED_ON + "T00:00:00Z",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_price_snapshots(
            id, label, source_ref, calculator_version, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                spec.snapshot_id,
                (
                    "ccusage 20.0.17 Spark {} proxy; no published Spark rate".format(
                        spec.service_tier
                    )
                    if spec in SPARK_PROXY_SPECS
                    else (
                        "ccusage-style {} Fast long-context proxy effective {}; "
                        "no published historical tier rate".format(
                            spec.model, spec.effective_on
                        )
                        if spec in FAST_LONG_CONTEXT_PROXY_SPECS
                        else "{} {} {} effective {}".format(
                            spec.provider, spec.model, spec.service_tier, spec.effective_on
                        )
                    )
                ),
                spec.source_ref
                + " (inspected "
                + (
                    "2026-09-26"
                    if spec in (*SPARK_PROXY_SPECS, *FAST_LONG_CONTEXT_PROXY_SPECS)
                    else INSPECTED_ON
                )
                + ")",
                OFFICIAL_CALCULATOR_VERSION,
                (
                    "2026-09-26T00:00:00Z"
                    if spec in (*SPARK_PROXY_SPECS, *FAST_LONG_CONTEXT_PROXY_SPECS)
                    else INSPECTED_ON + "T00:00:00Z"
                ),
            )
            for spec in price_specs
        ],
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO usage_model_prices(
            snapshot_id, model_name, input_usd_per_million,
            output_usd_per_million, cache_write_usd_per_million,
            cache_read_usd_per_million, long_context_threshold_tokens,
            long_context_input_usd_per_million,
            long_context_output_usd_per_million,
            long_context_cache_write_usd_per_million,
            long_context_cache_read_usd_per_million
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [spec.price_row for spec in price_specs],
    )


def price_existing_unpriced_spark_records(connection: sqlite3.Connection) -> int:
    """Apply the selected ccusage proxy to retained Spark token observations."""
    rows = connection.execute(
        """
        SELECT usage_records.id, usage_records.source_record_id,
               usage_records.source_line, usage_records.occurred_at,
               usage_records.raw_model, usage_records.input_tokens,
               usage_records.output_tokens, usage_records.cache_write_tokens,
               usage_records.cache_read_tokens, usage_records.reasoning_tokens,
               usage_records.source_total_tokens, usage_records.total_tokens,
               usage_records.total_semantics, usage_records.aggregation_scope,
               usage_records.capability_state, usage_records.capability_json
        FROM usage_records
        JOIN sources ON sources.id = usage_records.source_id
        WHERE sources.provider_kind = 'codex'
          AND usage_records.model_name = 'gpt-5.3-codex-spark'
          AND usage_records.calculation_state = 'unpriced'
          AND usage_records.price_snapshot_id = ?
        """,
        (UNAVAILABLE_SNAPSHOT_ID,),
    ).fetchall()
    if not rows:
        return 0
    calculated_at = utc_now()
    updates = []
    for row in rows:
        try:
            capability = json.loads(row["capability_json"] or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(capability, dict):
            continue
        tier = capability.get("service_tier")
        if tier not in {"standard", "fast"}:
            continue
        snapshot_id = select_snapshot(
            "codex", "gpt-5.3-codex-spark", row["occurred_at"], tier
        )
        if snapshot_id == UNAVAILABLE_SNAPSHOT_ID:
            continue
        price = _price_row(connection, snapshot_id, "gpt-5.3-codex-spark")
        if price is None:
            raise RuntimeError("Spark proxy price snapshot is unavailable")
        record = ParsedUsageRecord(
            usage_record_id=row["id"],
            source_record_id=row["source_record_id"],
            source_line=row["source_line"],
            occurred_at=row["occurred_at"],
            raw_model=row["raw_model"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            cache_write_tokens=row["cache_write_tokens"],
            cache_read_tokens=row["cache_read_tokens"],
            reasoning_tokens=row["reasoning_tokens"],
            source_total_tokens=row["source_total_tokens"],
            total_tokens=row["total_tokens"],
            total_semantics=row["total_semantics"],
            aggregation_scope=row["aggregation_scope"],
            capability_state=row["capability_state"],
            capability=capability,
        )
        state, cost = calculate_estimated_cost(record, price)
        if state != "priced" or cost is None:
            continue
        updates.append((cost, snapshot_id, calculated_at, row["id"]))
    cursor = connection.executemany(
        """
        UPDATE usage_records
        SET calculation_state = 'priced', estimated_cost_usd = ?,
            price_snapshot_id = ?, calculator_version = ?, calculated_at = ?
        WHERE id = ? AND model_name = 'gpt-5.3-codex-spark'
          AND calculation_state = 'unpriced' AND price_snapshot_id = ?
        """,
        [
            (cost, snapshot_id, OFFICIAL_CALCULATOR_VERSION, calculated_at,
             record_id, UNAVAILABLE_SNAPSHOT_ID)
            for cost, snapshot_id, calculated_at, record_id in updates
        ],
    )
    return cursor.rowcount


def price_existing_partial_fast_long_context_records(
    connection: sqlite3.Connection,
) -> int:
    """Apply the approved historical Fast long-context proxy to partial rows."""
    proxy_ids = {spec.snapshot_id for spec in FAST_LONG_CONTEXT_PROXY_SPECS}
    official_ids = tuple(
        spec.snapshot_id for spec in PRICE_SPECS
        if spec.provider == "codex"
        and spec.service_tier == "fast"
        and spec.long_input_rate is None
        and any(
            proxy.model == spec.model
            and proxy.effective_on == spec.effective_on
            for proxy in FAST_LONG_CONTEXT_PROXY_SPECS
        )
    )
    if not official_ids:
        return 0
    placeholders = ", ".join("?" for _ in official_ids)
    rows = connection.execute(
        f"""
        SELECT usage_records.id, usage_records.model_name,
               usage_records.price_snapshot_id, usage_records.source_record_id,
               usage_records.source_line, usage_records.occurred_at,
               usage_records.raw_model, usage_records.input_tokens,
               usage_records.output_tokens, usage_records.cache_write_tokens,
               usage_records.cache_read_tokens, usage_records.reasoning_tokens,
               usage_records.source_total_tokens, usage_records.total_tokens,
               usage_records.total_semantics, usage_records.aggregation_scope,
               usage_records.capability_state, usage_records.capability_json
        FROM usage_records
        JOIN sources ON sources.id = usage_records.source_id
        WHERE sources.provider_kind = 'codex'
          AND usage_records.calculation_state = 'partial'
          AND usage_records.price_snapshot_id IN ({placeholders})
        """,
        official_ids,
    ).fetchall()
    if not rows:
        return 0
    calculated_at = utc_now()
    updates = []
    for row in rows:
        try:
            capability = json.loads(row["capability_json"] or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(capability, dict) or capability.get("service_tier") != "fast":
            continue
        input_tokens = row["input_tokens"]
        cache_read_tokens = row["cache_read_tokens"]
        if input_tokens is None or cache_read_tokens is None:
            continue
        model_name = row["model_name"]
        current_snapshot_id = select_snapshot(
            "codex", model_name, row["occurred_at"], "fast"
        )
        if current_snapshot_id != row["price_snapshot_id"]:
            continue
        proxy_id = select_snapshot(
            "codex", model_name, row["occurred_at"], "fast",
            context_input_tokens=input_tokens + cache_read_tokens,
        )
        if proxy_id not in proxy_ids:
            continue
        price = _price_row(connection, proxy_id, model_name)
        if price is None:
            raise RuntimeError("Fast long-context proxy price snapshot is unavailable")
        record = ParsedUsageRecord(
            usage_record_id=row["id"],
            source_record_id=row["source_record_id"],
            source_line=row["source_line"],
            occurred_at=row["occurred_at"],
            raw_model=row["raw_model"],
            input_tokens=input_tokens,
            output_tokens=row["output_tokens"],
            cache_write_tokens=row["cache_write_tokens"],
            cache_read_tokens=cache_read_tokens,
            reasoning_tokens=row["reasoning_tokens"],
            source_total_tokens=row["source_total_tokens"],
            total_tokens=row["total_tokens"],
            total_semantics=row["total_semantics"],
            aggregation_scope=row["aggregation_scope"],
            capability_state=row["capability_state"],
            capability=capability,
        )
        state, cost = calculate_estimated_cost(record, price)
        if state == "priced" and cost is not None:
            updates.append((cost, proxy_id, calculated_at, row["id"], current_snapshot_id))
    cursor = connection.executemany(
        """
        UPDATE usage_records
        SET calculation_state = 'priced', estimated_cost_usd = ?,
            price_snapshot_id = ?, calculator_version = ?, calculated_at = ?
        WHERE id = ? AND calculation_state = 'partial'
          AND price_snapshot_id = ?
        """,
        [
            (cost, proxy_id, OFFICIAL_CALCULATOR_VERSION, calculated_at,
             record_id, previous_id)
            for cost, proxy_id, calculated_at, record_id, previous_id in updates
        ],
    )
    return cursor.rowcount


def _price_row(
    connection: sqlite3.Connection, snapshot_id: str, model_name: Optional[str]
) -> Optional[sqlite3.Row]:
    if not model_name:
        return None
    return connection.execute(
        """
        SELECT * FROM usage_model_prices
        WHERE snapshot_id = ? AND model_name = ?
        """,
        (snapshot_id, model_name),
    ).fetchone()


def calculate_estimated_cost(
    record: ParsedUsageRecord,
    price_row: Optional[sqlite3.Row],
) -> Tuple[str, Optional[str]]:
    if record.capability_state == "malformed":
        return "failed", None
    if price_row is None:
        return "unpriced", None
    if record.input_tokens is None or record.output_tokens is None:
        return "partial", None

    threshold = price_row["long_context_threshold_tokens"]
    if threshold is not None and record.cache_read_tokens is None:
        return "partial", None
    context_input_tokens = record.input_tokens + (record.cache_read_tokens or 0)
    long_context = threshold is not None and context_input_tokens > threshold

    def selected_rate(base_column: str, long_context_column: str) -> Optional[str]:
        return (
            price_row[long_context_column]
            if long_context
            else price_row[base_column]
        )

    input_rate = selected_rate(
        "input_usd_per_million",
        "long_context_input_usd_per_million",
    )
    output_rate = selected_rate(
        "output_usd_per_million",
        "long_context_output_usd_per_million",
    )
    if input_rate is None or output_rate is None:
        return "partial", None
    components = [
        (record.input_tokens, input_rate),
        (record.output_tokens, output_rate),
    ]
    one_hour_tokens = record.capability.get("cache_write_1h_tokens", 0)
    if not isinstance(one_hour_tokens, int) or isinstance(one_hour_tokens, bool):
        return "partial", None
    if one_hour_tokens < 0:
        return "partial", None
    five_minute_cache_writes = record.cache_write_tokens
    if one_hour_tokens:
        if five_minute_cache_writes is None or one_hour_tokens > five_minute_cache_writes:
            return "partial", None
        one_hour_rate = claude_1h_cache_rate(price_row["snapshot_id"])
        if one_hour_rate is None:
            return "partial", None
        five_minute_cache_writes -= one_hour_tokens
        components.append((one_hour_tokens, one_hour_rate))
    for tokens, base_rate, component_rate in (
        (
            five_minute_cache_writes,
            price_row["cache_write_usd_per_million"],
            selected_rate(
                "cache_write_usd_per_million",
                "long_context_cache_write_usd_per_million",
            ),
        ),
        (
            record.cache_read_tokens,
            price_row["cache_read_usd_per_million"],
            selected_rate(
                "cache_read_usd_per_million",
                "long_context_cache_read_usd_per_million",
            ),
        ),
    ):
        if long_context and base_rate is not None and component_rate is None:
            return "partial", None
        if component_rate is None:
            continue
        if tokens is None:
            return "partial", None
        components.append((tokens, component_rate))

    amount = sum(
        Decimal(tokens) * Decimal(rate) / Decimal(1_000_000)
        for tokens, rate in components
    )
    return "priced", format(amount.quantize(Decimal("0.000000000001")), "f")


def _price_existing_incomplete_codex_records(
    connection: sqlite3.Connection,
    model_name: str,
    target_snapshot_id: str,
    eligible_snapshot_ids: Tuple[str, ...],
) -> int:
    price = _price_row(connection, target_snapshot_id, model_name)
    if price is None:
        raise RuntimeError(f"{model_name} price snapshot is unavailable")
    placeholders = ", ".join("?" for _ in eligible_snapshot_ids)
    rows = connection.execute(
        f"""
        SELECT usage_records.id, usage_records.source_record_id,
               usage_records.source_line, usage_records.occurred_at,
               usage_records.raw_model, usage_records.input_tokens,
               usage_records.output_tokens, usage_records.cache_write_tokens,
               usage_records.cache_read_tokens, usage_records.reasoning_tokens,
               usage_records.source_total_tokens, usage_records.total_tokens,
               usage_records.total_semantics, usage_records.aggregation_scope,
               usage_records.capability_state
        FROM usage_records
        JOIN sources ON sources.id = usage_records.source_id
        WHERE sources.provider_kind = 'codex'
          AND usage_records.model_name = ?
          AND usage_records.calculation_state IN ('unpriced', 'partial')
          AND usage_records.price_snapshot_id IN ({placeholders})
        """,
        (model_name, *eligible_snapshot_ids),
    ).fetchall()
    if not rows:
        return 0
    calculated_at = utc_now()
    updates = []
    for row in rows:
        record = ParsedUsageRecord(
            usage_record_id=row["id"],
            source_record_id=row["source_record_id"],
            source_line=row["source_line"],
            occurred_at=row["occurred_at"],
            raw_model=row["raw_model"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            cache_write_tokens=row["cache_write_tokens"],
            cache_read_tokens=row["cache_read_tokens"],
            reasoning_tokens=row["reasoning_tokens"],
            source_total_tokens=row["source_total_tokens"],
            total_tokens=row["total_tokens"],
            total_semantics=row["total_semantics"],
            aggregation_scope=row["aggregation_scope"],
            capability_state=row["capability_state"],
        )
        state, cost = calculate_estimated_cost(record, price)
        updates.append(
            (
                state,
                cost,
                target_snapshot_id,
                CONTEXT_TIER_CALCULATOR_VERSION,
                calculated_at,
                row["id"],
                model_name,
                *eligible_snapshot_ids,
            )
        )
    cursor = connection.executemany(
        f"""
        UPDATE usage_records
        SET calculation_state = ?, estimated_cost_usd = ?,
            price_snapshot_id = ?, calculator_version = ?, calculated_at = ?
        WHERE id = ? AND model_name = ?
          AND calculation_state IN ('unpriced', 'partial')
          AND price_snapshot_id IN ({placeholders})
        """,
        updates,
    )
    return cursor.rowcount


def price_existing_incomplete_astra_records(connection: sqlite3.Connection) -> int:
    """Correct Codex Astra observations missing a compatible price snapshot."""
    return _price_existing_incomplete_codex_records(
        connection,
        "gpt-6-astra",
        CODEX_FAST_TIERED_ASTRA_PRICE_SNAPSHOT_ID,
        (
            CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,
            CODEX_FAST_TIERED_ASTRA_INITIAL_PRICE_SNAPSHOT_ID,
        ),
    )


def price_existing_incomplete_sol_records(connection: sqlite3.Connection) -> int:
    """Price previously observed Codex Sol requests with published Fast rates."""
    return _price_existing_incomplete_codex_records(
        connection,
        "gpt-6-sol",
        CODEX_FAST_TIERED_SOL_PRICE_SNAPSHOT_ID,
        (CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID,),
    )


def _snapshot_calculator_version(
    connection: sqlite3.Connection, snapshot_id: str
) -> str:
    row = connection.execute(
        "SELECT calculator_version FROM usage_price_snapshots WHERE id = ?",
        (snapshot_id,),
    ).fetchone()
    return row["calculator_version"] if row else CALCULATOR_VERSION


def _attribution_snapshot(
    connection: sqlite3.Connection, workspace_id: Optional[int]
) -> dict:
    attributed_at = utc_now()
    if workspace_id is None:
        return {
            "workspace_id_snapshot": None,
            "project_key": None,
            "project_name_snapshot": None,
            "project_path_snapshot": None,
            "project_git_root_snapshot": None,
            "attribution_basis": "unassigned",
            "attributed_at": attributed_at,
        }
    workspace = connection.execute(
        """
        SELECT id, display_name, canonical_path, git_root
        FROM workspaces WHERE id = ?
        """,
        (workspace_id,),
    ).fetchone()
    if not workspace:
        return {
            "workspace_id_snapshot": None,
            "project_key": None,
            "project_name_snapshot": None,
            "project_path_snapshot": None,
            "project_git_root_snapshot": None,
            "attribution_basis": "unassigned",
            "attributed_at": attributed_at,
        }
    git_root = workspace["git_root"]
    canonical_path = workspace["canonical_path"]
    basis = "git_root" if git_root else "workspace_path"
    key_path = git_root or canonical_path
    return {
        "workspace_id_snapshot": workspace["id"],
        "project_key": "{}:{}".format(
            "git" if basis == "git_root" else "path", key_path
        ),
        "project_name_snapshot": workspace["display_name"],
        "project_path_snapshot": canonical_path,
        "project_git_root_snapshot": git_root,
        "attribution_basis": basis,
        "attributed_at": attributed_at,
    }


def store_usage_records(
    connection: sqlite3.Connection,
    source_id: int,
    session_id: int,
    usage_records: Iterable[ParsedUsageRecord],
    workspace_id: Optional[int] = None,
    normalizer_version: str = "legacy-v1",
    identity_scope: Optional[str] = None,
    cache: Optional[UsagePersistenceCache] = None,
) -> None:
    persistence_cache = cache or UsagePersistenceCache()
    if not persistence_cache.defaults_ready:
        ensure_default_price_snapshot(connection)
        ensure_official_price_snapshots(connection)
        persistence_cache.defaults_ready = True
    records = sorted(list(usage_records), key=lambda item: (item.source_line, item.usage_record_id))
    existing_rows = connection.execute(
        "SELECT * FROM usage_records WHERE session_id = ? ORDER BY source_line, id",
        (session_id,),
    ).fetchall()
    existing_by_id = {row["id"]: row for row in existing_rows}

    def stored_record_id(record: ParsedUsageRecord) -> str:
        if identity_scope is None:
            return record.usage_record_id
        return stable_id(
            "source-scoped-usage", identity_scope, record.usage_record_id
        )
    contract_changed = bool(existing_rows) and any(
        row["normalizer_version"] != normalizer_version for row in existing_rows
    )

    def reference_row(record: ParsedUsageRecord) -> Optional[sqlite3.Row]:
        exact = existing_by_id.get(stored_record_id(record))
        if exact is not None:
            return exact
        if not contract_changed:
            return None
        prior = [row for row in existing_rows if row["source_line"] <= record.source_line]
        if prior:
            return max(prior, key=lambda row: (row["source_line"], row["id"]))
        if existing_rows:
            return min(existing_rows, key=lambda row: (row["source_line"], row["id"]))
        return None

    connection.execute("SAVEPOINT usage_record_reconcile")
    try:
        upsert_values = []
        for record in records:
            record_id = stored_record_id(record)
            existing = existing_by_id.get(record_id)
            reference = reference_row(record)
            if (
                existing
                and existing["capability_state"] != "malformed"
                and record.capability_state == "malformed"
            ):
                continue

            snapshot_id = record.price_snapshot_id or (
                reference["price_snapshot_id"]
                if reference and reference["price_snapshot_id"]
                else DEFAULT_PRICE_SNAPSHOT_ID
            )
            model_name = normalize_model(record.normalized_model or record.raw_model)
            price_key = (snapshot_id, model_name)
            if price_key not in persistence_cache.price_rows:
                persistence_cache.price_rows[price_key] = _price_row(
                    connection, snapshot_id, model_name
                )
            price = persistence_cache.price_rows[price_key]
            if snapshot_id not in persistence_cache.calculator_versions:
                persistence_cache.calculator_versions[snapshot_id] = (
                    _snapshot_calculator_version(connection, snapshot_id)
                )
            calculator_version = persistence_cache.calculator_versions[
                snapshot_id
            ]
            calculation_state, estimated_cost_usd = calculate_estimated_cost(
                record, price
            )
            if reference:
                attribution = {
                    column: reference[column]
                    for column in (
                        "workspace_id_snapshot",
                        "project_key",
                        "project_name_snapshot",
                        "project_path_snapshot",
                        "project_git_root_snapshot",
                        "attribution_basis",
                        "attributed_at",
                    )
                }
            else:
                attribution = _attribution_snapshot(connection, workspace_id)
            calculated_at = (
                existing["calculated_at"]
                if existing
                and existing["normalizer_version"] == normalizer_version
                and existing["calculator_version"] == calculator_version
                and existing["price_snapshot_id"] == snapshot_id
                and existing["calculation_state"] == calculation_state
                and existing["estimated_cost_usd"] == estimated_cost_usd
                and all(
                    existing[column] == value
                    for column, value in (
                        ("raw_model", record.raw_model),
                        ("input_tokens", record.input_tokens),
                        ("output_tokens", record.output_tokens),
                        ("cache_write_tokens", record.cache_write_tokens),
                        ("cache_read_tokens", record.cache_read_tokens),
                        ("reasoning_tokens", record.reasoning_tokens),
                        ("source_total_tokens", record.source_total_tokens),
                        ("total_tokens", record.total_tokens),
                    )
                )
                else utc_now()
            )
            upsert_values.append(
                (
                    record_id,
                    source_id,
                    session_id,
                    record.source_record_id,
                    record.source_line,
                    record.occurred_at,
                    record.raw_model,
                    model_name,
                    record.input_tokens,
                    record.output_tokens,
                    record.cache_write_tokens,
                    record.cache_read_tokens,
                    record.reasoning_tokens,
                    record.source_total_tokens,
                    record.total_tokens,
                    record.total_semantics,
                    record.aggregation_scope,
                    record.capability_state,
                    json.dumps(
                        record.capability, ensure_ascii=False, sort_keys=True
                    ),
                    calculation_state,
                    estimated_cost_usd,
                    snapshot_id,
                    calculator_version,
                    normalizer_version,
                    calculated_at,
                    attribution["workspace_id_snapshot"],
                    attribution["project_key"],
                    attribution["project_name_snapshot"],
                    attribution["project_path_snapshot"],
                    attribution["project_git_root_snapshot"],
                    attribution["attribution_basis"],
                    attribution["attributed_at"],
                    utc_now(),
                )
            )
        connection.executemany(
            """
                INSERT INTO usage_records(
                    id, source_id, session_id, source_record_id, source_line,
                    occurred_at, raw_model, model_name, input_tokens, output_tokens,
                    cache_write_tokens, cache_read_tokens, reasoning_tokens,
                    source_total_tokens, total_tokens, total_semantics,
                    aggregation_scope, capability_state, capability_json,
                    calculation_state, estimated_cost_usd, price_snapshot_id,
                    calculator_version, normalizer_version, calculated_at,
                    workspace_id_snapshot, project_key, project_name_snapshot,
                    project_path_snapshot, project_git_root_snapshot,
                    attribution_basis, attributed_at, imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source_record_id = excluded.source_record_id,
                    source_line = excluded.source_line,
                    occurred_at = excluded.occurred_at,
                    raw_model = excluded.raw_model,
                    model_name = excluded.model_name,
                    input_tokens = excluded.input_tokens,
                    output_tokens = excluded.output_tokens,
                    cache_write_tokens = excluded.cache_write_tokens,
                    cache_read_tokens = excluded.cache_read_tokens,
                    reasoning_tokens = excluded.reasoning_tokens,
                    source_total_tokens = excluded.source_total_tokens,
                    total_tokens = excluded.total_tokens,
                    total_semantics = excluded.total_semantics,
                    aggregation_scope = excluded.aggregation_scope,
                    capability_state = excluded.capability_state,
                    capability_json = excluded.capability_json,
                    calculation_state = excluded.calculation_state,
                    estimated_cost_usd = excluded.estimated_cost_usd,
                    price_snapshot_id = excluded.price_snapshot_id,
                    calculator_version = excluded.calculator_version,
                    normalizer_version = excluded.normalizer_version,
                    calculated_at = excluded.calculated_at,
                    imported_at = excluded.imported_at
            """,
            upsert_values,
        )

    except Exception:
        connection.execute("ROLLBACK TO usage_record_reconcile")
        connection.execute("RELEASE usage_record_reconcile")
        raise
    else:
        connection.execute("RELEASE usage_record_reconcile")


def reconcile_usage_record_contract(
    connection: sqlite3.Connection,
    source_id: int,
    expected_usage_record_ids: Iterable[str],
) -> None:
    connection.execute(
        """
        CREATE TEMP TABLE IF NOT EXISTS expected_usage_record_ids (
            id TEXT PRIMARY KEY
        )
        """
    )
    connection.execute("DELETE FROM expected_usage_record_ids")
    connection.executemany(
        "INSERT OR IGNORE INTO expected_usage_record_ids(id) VALUES (?)",
        ((usage_record_id,) for usage_record_id in expected_usage_record_ids),
    )
    connection.execute(
        """
        DELETE FROM usage_records
        WHERE source_id = ?
          AND id NOT IN (SELECT id FROM expected_usage_record_ids)
        """,
        (source_id,),
    )
    connection.execute("DELETE FROM expected_usage_record_ids")
