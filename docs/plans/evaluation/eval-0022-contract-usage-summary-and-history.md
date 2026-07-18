# EVAL-0022: Usage Summary And History Contract

## Metadata

- ID: `eval-0022-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-22`
- Attempt: `1`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Execution Profile: `fullstack-product`
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Checks

- Verified default Daily, Weekly, Cumulative, and valid or invalid paired custom-date normalization.
- Verified local inclusive-day bounds, Monday-based week buckets, monthly cumulative running totals, source filters, MTD scope, and URL preservation.
- Verified all-direct token and estimated-cost totals against the separately scoped usage-linked primary-work Session denominator.
- Verified unsupported pricing and unusable timestamps remain limitations or unavailable states rather than zero-valued summary cost.
- Verified read-model, route, template, Product Model, Project Architecture, and README parity.

## Evidence

- Deterministic SQLite fixtures cover primary, maintenance, subsession, priced, and unpriced facts across Claude and Codex.
- Daily produced 30 inclusive dates, Weekly 12 Monday buckets, and Cumulative started from the earliest usable usage time.
- Default, valid custom, and reversed custom local HTTP requests each returned `200`; selected state and fallback messaging matched the URL contract.
- The complete 66-test suite, isolated compilation, diff check, and repository privacy check passed.

## Findings

- No contract defect, spec gap, or stale consumer assumption remains.

## Route

- Next action: `pass`
