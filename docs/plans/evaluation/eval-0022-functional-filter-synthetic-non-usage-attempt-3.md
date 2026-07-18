# EVAL-0022: Filter Synthetic Non-Usage — Functional Attempt 3

## Metadata

- ID: `eval-0022-functional-attempt-3`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-29`
- Attempt: `3`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Execution Profile: `fullstack-product`
- Surface Lane: query → Sessions Dashboard read model
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Checks

- Exercised a stored zero-token Claude `<synthetic>` primary Fact and a priced Haiku subsession Fact.
- Verified Cumulative begins with eligible usage rather than the earlier pseudo-message.
- Verified aggregate Fact, token, cost, coverage, Session, and Model rows omit the pseudo-model while the database row remains present.
- Verified all existing period, source, price, maintenance, subsession, history, breakdown, trust, and interaction tests.

## Evidence

- All 84 automated tests passed.
- A private read-only runtime query confirmed `<synthetic>` is absent from Model output and the existing Haiku group remains present and fully priced.

## Findings

- No functional blocker remains; no runtime backfill is needed because the change is read-time filtering.

## Route

- Next action: `pass`.
