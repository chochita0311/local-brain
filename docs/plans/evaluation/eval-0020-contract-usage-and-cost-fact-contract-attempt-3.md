# EVAL-0020: Usage And Cost Fact Contract — Contract Attempt 3

## Metadata

- ID: `eval-0020-contract-attempt-3`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-26`
- Attempt: `3`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: source normalization → corrective immutable pricing → source-level version repair
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Corrected Codex event-delta ownership, raw and normalized fallback-model provenance, replay-prefix exclusion, the approved `fast` trend-price snapshot, corrective snapshot assignment, and source-wide rebuild invariants.

## Checks

- Verified `last_token_usage` is the authoritative direct Codex event delta and `total_token_usage` subtraction is used only when direct usage is absent.
- Verified spawned and forked subsession replay prefixes seed cumulative fallback state without producing duplicate Usage Facts, while later original subsession activity remains eligible.
- Verified cached input is separated from source input, reasoning remains a subset of output, and all supported components have one owner.
- Verified `codex-auto-review` keeps its raw identity while resolving a dated normalized model and the approved immutable `fast` price snapshot.
- Verified ordinary conflict updates retain the existing price snapshot and that only the approved corrective producer can assign the Attempt 3 snapshot during replacement.
- Reconciled Feature, Spec, Product, Architecture, PRD, roadmap, backlog, Run, evaluation, and fix-note wording.

## Evidence

- Synthetic direct-first, cumulative-fallback, auto-review, forked replay, price-snapshot, source-union, rollback, freshness, and idempotency tests passed.
- Same-boundary installed-report comparison matched every supported Codex token dimension exactly after replay exclusion.
- The complete repository suite passed with 80 tests; compilation, diff validation, and repository privacy checks also passed.
- Private source paths and aggregate values were used only for local validation and are not copied into tracked evidence.

## Evidence Gaps

- None for the approved foundation contract.
- Acceptance impact: `not applicable`.

## Contract Evidence

- Producer surfaces: `ingest/codex.py`, `ingest/common.py`, and `ParsedUsageFact`.
- Persistence surfaces: `usage.py`, scanner source-level repair, immutable price snapshots, and `usage_facts` conflict behavior.
- Consumer surfaces: source-neutral usage queries and the Sessions Dashboard.
- Stale-assumption check: current owner documents no longer describe cumulative-only Codex normalization or the superseded Attempt 2 price behavior as current.

## Findings

- No remaining contract defect, spec gap, or planning gap in FEAT-0020 scope.
- LocalBrain intentionally uses flat approved model-tier rates for trend comparison. It does not reproduce invoice-level long-context tiering, and the UI continues to label the result as estimated trend cost.

## Regression Notes

- Claude normalization, Session hierarchy, activity-time rules, Project snapshots, source freshness, and dashboard aggregation contracts remain unchanged outside the bounded Codex repair.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: Attempt 3 supersedes Attempt 2 as current FEAT-0020 Contract acceptance evidence.
- `2026-07-18`: RUN-20260718-27 supersedes this report for current price-contract acceptance after request-level long-context tiers were approved; its token and replay findings remain historical evidence.
