# EVAL-0031: Usage Attribution CHECK Parity — Functional

## Metadata

- ID: `eval-0031-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-36`
- Attempt: `1`
- Feature: [feat-0031-usage-attribution-check-parity](../feature/feat-0031-usage-attribution-check-parity.md)
- Spec: [spec-0031-usage-attribution-check-parity](../spec/spec-0031-usage-attribution-check-parity.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Usage Fact compatibility migration
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated valid and invalid legacy upgrades, recovery behavior, idempotency, CHECK enforcement, and protected Usage consumers.

## Checks And Evidence

- A valid synthetic legacy table retained every full-row SQLite value and column-metadata tuple, restored all three Usage indexes, passed foreign-key checks, and rejected a fourth attribution value.
- An invalid attribution fixture and an unexpected extra-column fixture both retained their original table SQL and rows after bounded failure.
- A file-backed fixture produced a `quick_check`-valid pre-migration backup containing the original schema and rows; a second startup neither overwrote the backup nor rebuilt the compliant table.
- Focused schema, Data Model, presentation, and audit checks passed 26 tests.
- The complete repository suite passed 117 tests, including Usage ingestion/repair, price snapshots, Dashboard grouping, activity attribution, source cascades, and schema presentation.
- Repository privacy passed 376 candidate files, and the configured runtime preflight reported a valid CHECK, zero invalid attribution rows, and `quick_check=ok` without reading values into tracked evidence.

## Evidence Gaps

- None.

## Findings

- None.

## Regression Notes

- No Usage Fact regeneration, Project reattribution, token/cost rewrite, timestamp-contract repair, UI change, Activity Event cleanup, or Maintenance Run migration occurred.

## Route

- Next action: `pass`.
