# EVAL-0037: Maintenance Run Workstream FK Parity — Functional

## Metadata

- ID: `eval-0037-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-42`
- Attempt: `1`
- Feature: [feat-0037-maintenance-run-workstream-fk-parity](../feature/feat-0037-maintenance-run-workstream-fk-parity.md)
- Spec: [spec-0037-maintenance-run-workstream-fk-parity](../spec/spec-0037-maintenance-run-workstream-fk-parity.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Maintenance Run Workstream ownership
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated fresh behavior, valid and null compatible associations, invalid-state refusal, recovery, dependent references, deletion semantics, idempotency, and Runner/Workstream regressions.

## Checks And Evidence

- Four focused migration tests cover fresh `SET NULL`, a legacy additive column order, valid and null Workstream values, exact full-Run and dependent-link preservation, orphan and unexpected-shape refusal, migration-table collision, file backup, and repeated startup.
- The complete schema migration, audit, Runner, and Workstream regression set passed 41 tests.
- The complete repository suite passed 142 tests, including Task Runner lifecycle, native Maintenance Session ingestion, Usage ownership, Workstream organization, Suggestions, schema presentation, and UI contracts.
- The actual local database migration retained all six Maintenance Run rows and all 15 non-null Suggestion origin links exactly, reported zero orphan Workstream IDs, and passed backup `quick_check`, exact backup snapshot comparison, FK checks, `integrity_check`, and a second idempotent startup.
- Current Data Model, deterministic presentation, generated cleanup ledger, Mermaid, privacy, and diff-whitespace checks passed without recording runtime values or paths in tracked evidence.

## Evidence Gaps

- None.

## Findings

- None.

## Regression Notes

- Historical Runs without a native Maintenance Session were not backfilled or deleted. Future native Runner Sessions continue to use FEAT-0036's producer and classification contract.

## Route

- Next action: `pass`.
