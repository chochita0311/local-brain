# EVAL-0033: Usage Record Dashboard Terminology — Contract

## Metadata

- ID: `eval-0033-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-38`
- Attempt: `1`
- Feature: [feat-0033-usage-record-dashboard-terminology](../feature/feat-0033-usage-record-dashboard-terminology.md)
- Spec: [spec-0033-usage-record-dashboard-terminology](../spec/spec-0033-usage-record-dashboard-terminology.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Usage read-model display copy and stable internal Fact contract
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated the owner-selected `usage records` Dashboard vocabulary, count formatting, and the boundary that keeps Usage Fact as the internal schema and engineering term.

## Checks And Evidence

- `usage_facts`, `ParsedUsageFact`, `fact_count`, token and price coverage keys, persistence, SQL aggregation, attribution, and price semantics remain unchanged.
- Dashboard summary, limitations, Source rows, composition evidence, Trust labels, and calculation explanation use `usage record(s)` and contain no visible `usage facts`, `facts priced`, `each fact`, or `normalized usage facts` phrase.
- Counts use singular and plural correctly; large displayed counts use thousands separators, so the owner example reads as `10,720 usage records`.
- The only non-copy behavior is a presentation-only narrow Usage summary grid rule. It does not alter the read model, metric values, denominators, route state, or controls.
- Focused Usage/UI contracts passed 31 tests; the complete Python suite passed 121 tests.

## Evidence Gaps

- None.

## Findings

- None.

## Regression Notes

- Activity Events, Sessions, source provenance, model normalization, Project snapshots, and immutable trend-cost calculation remain separate and unchanged.

## Route

- Next action: `pass`.
