import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Iterable, Optional, Tuple

from .ingest.common import ParsedUsageRecord


DEFAULT_PRICE_SNAPSHOT_ID = "ccusage-20.0.14-litellm-20260718"
CODEX_FAST_PRICE_SNAPSHOT_ID = "ccusage-20.0.17-codex-fast-20260718"
CODEX_FAST_TIERED_PRICE_SNAPSHOT_ID = (
    "ccusage-20.0.17-codex-fast-context-tier-20260718"
)
CALCULATOR_VERSION = "localbrain-usage-cost-v1"
CONTEXT_TIER_CALCULATOR_VERSION = "localbrain-usage-cost-v2-context-tier"

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
    for tokens, base_rate, component_rate in (
        (
            record.cache_write_tokens,
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
) -> None:
    ensure_default_price_snapshot(connection)
    records = sorted(list(usage_records), key=lambda item: (item.source_line, item.usage_record_id))
    existing_rows = connection.execute(
        "SELECT * FROM usage_records WHERE session_id = ? ORDER BY source_line, id",
        (session_id,),
    ).fetchall()
    existing_by_id = {row["id"]: row for row in existing_rows}
    contract_changed = bool(existing_rows) and any(
        row["normalizer_version"] != normalizer_version for row in existing_rows
    )

    def reference_row(record: ParsedUsageRecord) -> Optional[sqlite3.Row]:
        exact = existing_by_id.get(record.usage_record_id)
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
        for record in records:
            existing = existing_by_id.get(record.usage_record_id)
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
            price = _price_row(connection, snapshot_id, model_name)
            calculator_version = _snapshot_calculator_version(connection, snapshot_id)
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
            connection.execute(
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
                (
                    record.usage_record_id,
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
                    json.dumps(record.capability, ensure_ascii=False, sort_keys=True),
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
                ),
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
