# EVAL-0022: Filter Synthetic Non-Usage — Contract Attempt 3

## Metadata

- ID: `eval-0022-contract-attempt-3`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-29`
- Attempt: `3`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Execution Profile: `fullstack-product`
- Surface Lane: dashboard selected-Fact eligibility
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Checks

- Verified the exclusion is exact to Claude raw model `<synthetic>` and occurs only in Sessions Dashboard queries.
- Verified storage, source provenance, Usage Facts, Activity Events, and Session browsing remain unchanged.
- Verified the filter owns the earliest Cumulative date, selected and MTD aggregates, history, coverage, projection compatibility value, breakdowns, freshness selected counts, and usage-linked Session counts through one shared row set.
- Verified real-model primary, maintenance, and subsession facts remain eligible.

## Evidence

- Synthetic SQLite fixtures retain the pseudo-model Fact while the dashboard omits it and keeps a priced Haiku subsession Fact.
- The complete 84-test suite passed.

## Findings

- No producer, storage, consumer, or documentation conflict remains.

## Route

- Next action: `pass`.
