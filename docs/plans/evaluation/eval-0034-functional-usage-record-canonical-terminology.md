# EVAL-0034: Usage Record Canonical Terminology — Functional

## Metadata

- ID: `eval-0034-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-39`
- Attempt: `1`
- Feature: [feat-0034-usage-record-canonical-terminology](../feature/feat-0034-usage-record-canonical-terminology.md)
- Spec: [spec-0034-usage-record-canonical-terminology](../spec/spec-0034-usage-record-canonical-terminology.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Usage persistence, ingestion, repair, query, and Dashboard regression
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated fresh, canonical, legacy, coexistence, repeated-startup, actual-runtime, ingestion, pricing, attribution, Dashboard, marker-boundary, and repository-wide regression behavior.

## Checks And Evidence

- The actual local database was backed up before migration. Its legacy table became `usage_records`; ordered full-row digest, row count, and column metadata matched before and after, the legacy table is absent, `foreign_key_check` returned no errors, and SQLite `quick_check` passed.
- Focused Usage, Dashboard, attribution, migration, and UI contracts passed 71 tests before full-suite evaluation.
- The complete Python suite passed 126 tests, including the four legacy-name migration cases and explicit web-created versus manually supplied maintenance-marker persistence boundaries.
- `/sessions-dashboard` returned `200` from an isolated local server, rendered canonical `usage record` copy, and contained no visible legacy Usage Fact phrase.
- Mermaid asset checks, all nine Data Model diagrams, Data Model ownership parity, generated Schema presentation, cleanup ledger, compilation, repository privacy, and diff whitespace checks passed.

## Evidence Gaps

- None.

## Findings

- None.

## Regression Notes

- No source rescan, Usage Record regeneration, repricing, reattribution, metric change, layout change, or Maintenance Run behavior change occurred.

## Route

- Next action: `pass`.
