"""Frozen, dated API-equivalent rates and an explicit Codex Spark proxy.

New models and price changes require an explicit, cited entry. Historical
snapshots are never edited after they have been used by a Usage Record.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Tuple


INSPECTED_ON = "2026-09-25"
UNAVAILABLE_SNAPSHOT_ID = "official-price-unavailable-20260925-v1"
OPENAI_FAST_URL = "https://openai.com/api-fast-mode/"
OPENAI_CHANGELOG_URL = "https://developers.openai.com/api/docs/changelog"
OPENAI_LAUNCH_URL = "https://openai.com/index/previewing-gpt-5-6-sol/"
ANTHROPIC_PRICING_URL = "https://platform.claude.com/docs/en/about-claude/pricing"
CCUSAGE_PRICING_URL = (
    "https://github.com/ccusage/ccusage/blob/v20.0.17/"
    "rust/crates/ccusage/src/pricing.rs"
)


@dataclass(frozen=True)
class PriceSpec:
    snapshot_id: str
    provider: str
    model: str
    service_tier: str
    effective_on: str
    input_rate: str
    output_rate: str
    cache_read_rate: str
    cache_write_rate: Optional[str]
    long_context_threshold: Optional[int]
    long_input_rate: Optional[str]
    long_output_rate: Optional[str]
    long_cache_read_rate: Optional[str]
    long_cache_write_rate: Optional[str]
    source_ref: str

    @property
    def price_row(self) -> tuple:
        return (
            self.snapshot_id,
            self.model,
            self.input_rate,
            self.output_rate,
            self.cache_write_rate,
            self.cache_read_rate,
            self.long_context_threshold,
            self.long_input_rate,
            self.long_output_rate,
            self.long_cache_write_rate,
            self.long_cache_read_rate,
        )


def _money(value: Decimal) -> str:
    return format(value, "f")


def _openai(
    model: str,
    effective_on: str,
    input_rate: str,
    output_rate: str,
    *,
    fast_factor: str = "2",
    fast_long_context: bool = True,
    source_ref: str,
) -> Tuple[PriceSpec, PriceSpec]:
    base_input = Decimal(input_rate)
    base_output = Decimal(output_rate)
    specs = []
    for tier, factor in (("standard", Decimal(1)), ("fast", Decimal(fast_factor))):
        short_input = base_input * factor
        short_output = base_output * factor
        long_supported = tier == "standard" or fast_long_context
        specs.append(
            PriceSpec(
                snapshot_id=(
                    "official-openai-{}-{}-{}-v1".format(
                        model.replace(".", "-"), tier, effective_on.replace("-", "")
                    )
                ),
                provider="codex",
                model=model,
                service_tier=tier,
                effective_on=effective_on,
                input_rate=_money(short_input),
                output_rate=_money(short_output),
                cache_read_rate=_money(short_input / Decimal(10)),
                # Codex JSONL does not report cache writes separately.
                cache_write_rate=None,
                long_context_threshold=272_000,
                long_input_rate=(
                    _money(short_input * 2) if long_supported else None
                ),
                long_output_rate=(
                    _money(short_output * Decimal("1.5"))
                    if long_supported
                    else None
                ),
                long_cache_read_rate=(
                    _money(short_input / Decimal(5)) if long_supported else None
                ),
                long_cache_write_rate=None,
                source_ref=(
                    source_ref
                    + (
                        "; " + OPENAI_FAST_URL
                        if tier == "fast" and source_ref != OPENAI_FAST_URL
                        else ""
                    )
                    + (
                        "; pre-July-30 Priority 2x is a historical estimate"
                        if tier == "fast"
                        and model.startswith("gpt-5.6-")
                        and effective_on < "2026-07-30"
                        else ""
                    )
                ),
            )
        )
    return specs[0], specs[1]


def _claude(model: str, effective_on: str, input_rate: str, output_rate: str) -> PriceSpec:
    base_input = Decimal(input_rate)
    return PriceSpec(
        snapshot_id="official-anthropic-{}-{}-v1".format(
            model.replace(".", "-"), effective_on.replace("-", "")
        ),
        provider="claude",
        model=model,
        service_tier="standard",
        effective_on=effective_on,
        input_rate=input_rate,
        output_rate=output_rate,
        cache_read_rate=_money(base_input / Decimal(10)),
        cache_write_rate=_money(base_input * Decimal("1.25")),
        long_context_threshold=None,
        long_input_rate=None,
        long_output_rate=None,
        long_cache_read_rate=None,
        long_cache_write_rate=None,
        source_ref=ANTHROPIC_PRICING_URL,
    )


PRICE_SPECS = (
    *_openai(
        "gpt-5.5", "2026-04-23", "5", "30", fast_factor="2.5",
        fast_long_context=False, source_ref=OPENAI_FAST_URL,
    ),
    *_openai(
        "gpt-5.6-sol", "2026-07-09", "5", "30",
        fast_long_context=False, source_ref=OPENAI_LAUNCH_URL,
    ),
    *_openai(
        "gpt-5.6-terra", "2026-07-09", "2.5", "15",
        fast_long_context=False, source_ref=OPENAI_LAUNCH_URL,
    ),
    *_openai(
        "gpt-5.6-luna", "2026-07-09", "1", "6",
        fast_long_context=False, source_ref=OPENAI_LAUNCH_URL,
    ),
    *_openai(
        "gpt-5.6-terra", "2026-07-30", "2", "12",
        fast_long_context=False, source_ref=OPENAI_CHANGELOG_URL,
    ),
    *_openai(
        "gpt-5.6-luna", "2026-07-30", "0.2", "1.2",
        fast_long_context=False, source_ref=OPENAI_CHANGELOG_URL,
    ),
    *_openai(
        "gpt-5.6-sol", "2026-08-05", "5", "30",
        source_ref=OPENAI_CHANGELOG_URL,
    ),
    *_openai(
        "gpt-5.6-terra", "2026-08-05", "2", "12",
        source_ref=OPENAI_CHANGELOG_URL,
    ),
    *_openai(
        "gpt-5.6-luna", "2026-08-05", "0.2", "1.2",
        source_ref=OPENAI_CHANGELOG_URL,
    ),
    *_openai(
        "gpt-5.6-sol", "2026-08-21", "4", "20",
        source_ref=OPENAI_CHANGELOG_URL,
    ),
    *_openai(
        "gpt-6-astra", "2026-09-03", "10", "50",
        source_ref="https://developers.openai.com/api/docs/models/gpt-6-astra",
    ),
    *_openai(
        "gpt-6-sol", "2026-09-22", "2", "10",
        source_ref="https://developers.openai.com/api/docs/models/gpt-6-sol",
    ),
    *_openai(
        "gpt-6-luna", "2026-09-22", "0.1", "0.5",
        source_ref="https://developers.openai.com/api/docs/models/gpt-6-luna",
    ),
    _claude("claude-haiku-4-5-20251001", "2025-10-01", "1", "5"),
    _claude("claude-sonnet-4-6", "2026-02-17", "3", "15"),
)


# OpenAI did not publish a Spark token rate. ccusage 20.0.17 resolves its
# model name to GPT-5.3-Codex; retain that explicitly chosen trend proxy.
SPARK_PROXY_SPECS = tuple(
    PriceSpec(
        snapshot_id=(
            "ccusage-20-0-17-spark-{}-proxy-20260926-v1".format(tier)
        ),
        provider="codex",
        model="gpt-5.3-codex-spark",
        service_tier=tier,
        effective_on="2026-02-12",
        input_rate=input_rate,
        output_rate=output_rate,
        cache_read_rate=cache_read_rate,
        cache_write_rate=None,
        long_context_threshold=None,
        long_input_rate=None,
        long_output_rate=None,
        long_cache_read_rate=None,
        long_cache_write_rate=None,
        source_ref=CCUSAGE_PRICING_URL,
    )
    for tier, input_rate, cache_read_rate, output_rate in (
        ("standard", "1.75", "0.175", "14"),
        ("fast", "3.50", "0.35", "28"),
    )
)


# A Codex request can exceed the published Standard context threshold even
# where its historical Fast API rate was not published. Keep those estimates
# separate from the dated publisher snapshots and retain the original short
# context rates from the selected publisher entry.
FAST_LONG_CONTEXT_PROXY_SPECS = tuple(
    PriceSpec(
        snapshot_id=(
            "ccusage-20-0-17-{}-fast-long-context-proxy-{}-20260926-v1".format(
                spec.model.replace(".", "-"), spec.effective_on.replace("-", "")
            )
        ),
        provider=spec.provider,
        model=spec.model,
        service_tier=spec.service_tier,
        effective_on=spec.effective_on,
        input_rate=spec.input_rate,
        output_rate=spec.output_rate,
        cache_read_rate=spec.cache_read_rate,
        cache_write_rate=spec.cache_write_rate,
        long_context_threshold=spec.long_context_threshold,
        long_input_rate=_money(Decimal(spec.input_rate) * 2),
        long_output_rate=_money(Decimal(spec.output_rate) * Decimal("1.5")),
        long_cache_read_rate=_money(Decimal(spec.cache_read_rate) * 2),
        long_cache_write_rate=None,
        source_ref=(
            spec.source_ref + "; " + CCUSAGE_PRICING_URL
            + "; historical Fast long-context rate extrapolated, not published"
        ),
    )
    for spec in PRICE_SPECS
    if spec.provider == "codex"
    and spec.service_tier == "fast"
    and spec.long_context_threshold is not None
    and spec.long_input_rate is None
    and spec.model in {
        "gpt-5.5", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"
    }
)


def select_snapshot(
    provider: str, model: Optional[str], occurred_at: Optional[str],
    service_tier: str = "standard",
    context_input_tokens: Optional[int] = None,
) -> str:
    if not model or not occurred_at or len(occurred_at) < 10:
        return UNAVAILABLE_SNAPSHOT_ID
    if provider == "claude" and model.startswith("anthropic/"):
        model = model.split("/", 1)[1]
    elif provider == "codex" and model.startswith("openai/"):
        model = model.split("/", 1)[1]
    candidates = (
        spec for spec in (*PRICE_SPECS, *SPARK_PROXY_SPECS)
        if spec.provider == provider
        and spec.model == model
        and spec.service_tier == service_tier
        and spec.effective_on <= occurred_at[:10]
    )
    selected = max(candidates, key=lambda spec: spec.effective_on, default=None)
    if selected is None:
        return UNAVAILABLE_SNAPSHOT_ID
    if (
        context_input_tokens is not None
        and selected.long_context_threshold is not None
        and context_input_tokens > selected.long_context_threshold
        and selected.long_input_rate is None
    ):
        proxy = next(
            (
                spec for spec in FAST_LONG_CONTEXT_PROXY_SPECS
                if spec.model == selected.model
                and spec.effective_on == selected.effective_on
                and spec.service_tier == selected.service_tier
            ),
            None,
        )
        if proxy is not None:
            return proxy.snapshot_id
    return selected.snapshot_id


def claude_1h_cache_rate(snapshot_id: Optional[str]) -> Optional[str]:
    spec = next(
        (
            item for item in PRICE_SPECS
            if item.provider == "claude" and item.snapshot_id == snapshot_id
        ),
        None,
    )
    return _money(Decimal(spec.input_rate) * 2) if spec else None
