# RUN-20260718-25: Usage Contract Repair

## Metadata

- ID: `run-20260718-25`
- Status: `complete`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Attempt: `2`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Correct the invalid Codex latest-per-turn usage assumption, align the bounded Claude cache-create edge case with the local ccusage reference, and make future normalizer-contract changes converge through safe synchronization without a user-facing reset control.

## Finding Classification

- Classification: `spec gap` discovered by live local post-run validation.
- Earlier invalid assumption: one latest Codex `last_token_usage` observation represented one complete turn.
- Corrected evidence: a tool-heavy turn can contain several positive model-call increments, while `total_token_usage` provides the monotonic Session cumulative owner.

## Selected Loop

- Surface lanes: source normalization → versioned persistence repair → durable contract → live local backfill evidence
- Required evaluators: Contract and Functional
- Current phase: complete; Attempt 2 was later invalidated by stronger source-adapter and live-report evidence

## Contract Surfaces

- Claude cache-create fallback, Codex cumulative-delta identity and component math, source-file normalizer version, Usage Fact normalizer version, transactional source-file-union replacement, immutable price and Project snapshots, and synchronization idempotency.

## Attempts

- Post-run invalidation:
  - status: awaiting human return decision
  - evidence: official ccusage Codex parsing selects `last_token_usage` when present and uses cumulative subtraction only as fallback; the installed report also resolves fallback models and the configured fast service tier
  - impact: LocalBrain currently overstates the compared Codex token total while pricing only a minority of facts at standard-like rates, so Attempt 2 cannot remain acceptance evidence for FEAT-0020
  - recommendation: return SPEC-0020 for a second versioned normalization and pricing repair; do not mutate the runtime database until that direction is approved
- Attempt 2:
  - status: passed
  - input: human-approved repair direction and live local aggregate evidence
  - outcome: cumulative-delta and bounded cache fallback shipped; source-level version repair converged without a reset control; unchanged files skipped on repeat synchronization

## Evaluation Coverage

- Contract:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: producer and persistence source, schema migration, synthetic shared-Session files, failure rollback, policy parity
  - Unverified claims: none
  - Acceptance impact: `not applicable`
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: 76 automated tests, private local all-source repair, active-file append detection, repeat synchronization, SQLite integrity, rendered route response
  - Unverified claims: none; private runtime values remain outside tracked artifacts
  - Acceptance impact: `not applicable`

## Current Artifacts

- Contract evaluation: [eval-0020-contract-attempt-2](../evaluation/eval-0020-contract-usage-and-cost-fact-contract-attempt-2.md)
- Functional evaluation: [eval-0020-functional-attempt-2](../evaluation/eval-0020-functional-usage-and-cost-fact-contract-attempt-2.md)
- Fix log: [fix-0022-usage-normalizer-contract-repair](../fix/fix-0022-usage-normalizer-contract-repair.md)

## Post-Contract Regression Check

- Needed: yes
- Consumers: Sessions Dashboard summary, history, breakdown, trust, and projection; Session synchronization; source freshness; pricing and Project attribution.
- Result: passed
- Notes: the full suite passed, the actual SQLite database reported integrity `ok`, the read model returned refreshed aggregates, and the route rendered a successful response.

## Human Review Outcome

- Decision: the human approved the Attempt 2 direction and requested that local refresh; later evidence now requires a new human decision.
- Returned layer if any: recommended `SPEC-0020`, not yet approved.
- Follow-up run: pending.

## Continuity Notes

- `2026-07-18`: human owner requested the corrected contract, safe data refresh, and consideration of future contract changes without exposing an aggregate-reset button.
- `2026-07-18`: private runtime backup was retained, all configured Session files repaired without failure, no legacy normalizer facts remained, and repeat synchronization skipped unchanged files while retaining active-file incrementality.
- `2026-07-18`: later ccusage source and live-report comparison invalidated the cumulative-only parser and incomplete standard-price acceptance basis. The Run no longer carries a passed result; a new repair is intentionally paused before code or runtime-data mutation.
