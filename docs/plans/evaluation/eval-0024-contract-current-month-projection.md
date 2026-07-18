# EVAL-0024: Current-Month Projection Contract

## Metadata

- ID: `eval-0024-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-24`
- Attempt: `1`
- Feature: [feat-0024-current-month-projection](../feature/feat-0024-current-month-projection.md)
- Spec: [spec-0024-current-month-projection](../spec/spec-0024-current-month-projection.md)
- Execution Profile: `fullstack-product`
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Checks

- Verified `calendar-elapsed-v1`, exact timezone-aware local-month duration, calculation time, source scope, MTD input, elapsed fraction, complete-day count, price coverage, and source freshness outputs.
- Verified the three-complete-day gate, current-date range containment, Cost-only visibility, historical suppression, no-usage, unpriced, partial, and stale states.
- Verified projection reads canonical stored priced facts without updating Usage Facts or snapshots.

## Evidence

- A deterministic July 18 noon UTC fixture scaled `$0.005072` compatible MTD cost over 17.5 of 31 days to a displayed `$0.0090` month-end direction.
- Claude-only scope used its own `$0.001052` MTD input and complete coverage.
- Tokens and July 1–10 historical-only scopes suppressed projection; July 3 returned insufficient history; empty and all-unpriced sources remained distinct unavailable states.
- A source error retained and labeled a stale projection input.
- All 70 tests, compilation, diff, and repository privacy checks passed.

## Findings

- No formula, eligibility, provenance, or immutability defect remains.

## Route

- Next action: `pass`
