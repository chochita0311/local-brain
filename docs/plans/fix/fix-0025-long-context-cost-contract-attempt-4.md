# FIX-0025: Long-Context Cost Contract Attempt 4

## Metadata

- ID: `fix-0025-long-context-cost-contract-attempt-4`
- Status: `complete`
- Run ID: `run-20260718-27`
- Attempt: `4`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Codex request-context pricing and derived-Fact repair
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Input Reports

- Attempt 3 matched installed-report Codex token dimensions but retained a bounded monthly cost difference because LocalBrain applied only the flat fast tier.
- Request-level inspection isolated the full difference to model-specific long-context pricing.
- Human review approved matching the frozen ccusage request-tier boundary while retaining trend, snapshot, local-only, and non-invoice semantics.

## Fix Scope

- Extend immutable model-price rows with an optional context threshold and above-threshold component rates.
- Calculate the tier independently for each Usage Fact from non-cached input plus cache read.
- Keep the exact threshold on the base tier; use the long-context tier only above it.
- Preserve reasoning as an output subset and permit a post-compaction Fact to return to base pricing.
- Add one immutable tiered Codex fast snapshot and calculator v2 without mutating prior price snapshots.
- Version the Codex producer and repair the complete private Codex Fact set automatically without a reset button.
- Preserve Claude pricing, Project attribution snapshots, direct-event token normalization, replay exclusion, and all dashboard interactions.

## Exclusions

- No runtime ccusage dependency, remote pricing lookup, page-render subprocess, or invoice reconciliation.
- No Session-wide, daily, or monthly inherited price tier.
- No personal budget, cap, quota, tax, currency conversion, or billed-spend semantics.
- No ordinary retroactive repricing outside this explicitly approved corrective contract.

## Validation

- 82 automated tests passed, including threshold, compaction, price-freeze, migration, repair, aggregation, and interaction regression coverage.
- A fixed completed local-date boundary matched installed offline ccusage monthly token dimensions and cost exactly.
- Private backup, source-wide repair, repeat synchronization, source-version convergence, snapshot and calculator coverage, SQLite integrity, dashboard rendering, compilation, and diff validation passed.

## Remaining Issues

- None in FEAT-0020 scope.
- PRD-0004's separate combined responsive viewport-evidence backlog item remains unchanged.

## Return Decision

- `pass`

## Continuity Notes

- `2026-07-18`: completed after human approval of the request-level tier boundary and private data refresh.
