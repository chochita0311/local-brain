# FIX-0024: Usage Contract Repair Attempt 3

## Metadata

- ID: `fix-0024-usage-contract-repair-attempt-3`
- Status: `complete`
- Run ID: `run-20260718-26`
- Attempt: `3`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Codex normalization, pricing, and derived-fact repair
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Input Reports

- Human review found Codex token and estimated-cost totals inconsistent with substantially heavier observed Codex activity.
- Attempt 2 repaired same-turn loss but incorrectly treated Session-cumulative subtraction as the primary contract.
- Installed ccusage output and adapter inspection showed direct `last_token_usage` events are primary, cumulative totals are fallback state, auto-review needs dated model resolution, and the current local Codex tier uses broader model pricing.
- Same-second replayed prefixes in spawned and forked local histories caused an additional bounded overcount until excluded.

## Fix Scope

- Prefer each positive direct Codex token event and use cumulative subtraction only when direct usage is absent.
- Preserve raw model identity, resolve normalized model identity with dated auto-review fallback, and attach one approved immutable `fast` trend-price snapshot.
- Detect and exclude copied spawned or forked replay prefixes without excluding later original subsession work.
- Permit the approved corrective producer to replace the invalid prior price snapshot while ordinary synchronization remains historically immutable.
- Version the corrected normalizer contract, repair the complete private Codex source-file union automatically, and verify repeat-sync idempotency without exposing a reset button.
- Preserve the existing partial dashboard-region navigation so metric and breakdown switches do not reset the page scroll position.

## Exclusions

- No runtime ccusage dependency, remote pricing lookup, or page-render subprocess.
- No invoice-level long-context tier reproduction, budget, cap, quota, or billed-spend semantics.
- No retroactive ordinary repricing outside this approved corrective contract.
- No change to Claude usage, activity-time segmentation, Session hierarchy, or frozen Project-attribution policy.

## Validation

- 80 automated tests passed, including direct-first, fallback, replay, model, price, repair, and scroll-continuity coverage.
- Same-boundary LocalBrain and installed ccusage Codex token dimensions matched exactly.
- The remaining small cost difference is explained by intentionally omitted invoice-level long-context tiering.
- Private backup, repair synchronization, repeat synchronization, source-version convergence, price coverage, SQLite integrity, dashboard route rendering, compilation, diff validation, and repository privacy checks passed.

## Remaining Issues

- None in FEAT-0020 scope.
- PRD-0004's separate combined responsive viewport-evidence backlog item remains unchanged.

## Return Decision

- `pass`

## Continuity Notes

- `2026-07-18`: completed after human approval of the corrected Spec and private data refresh.
- `2026-07-18`: superseded only for price-tier acceptance by RUN-20260718-27; Attempt 3 token parsing, replay exclusion, and model resolution remain current foundations.
