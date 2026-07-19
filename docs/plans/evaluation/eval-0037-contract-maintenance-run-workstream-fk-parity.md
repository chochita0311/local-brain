# EVAL-0037: Maintenance Run Workstream FK Parity — Contract

## Metadata

- ID: `eval-0037-contract`
- Status: `complete`
- Evaluator Type: `contract`
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

- Evaluated only the approved `maintenance_runs.workstream_id → workstreams.id ON DELETE SET NULL` compatible repair, its recovery boundary, retained operational history, and current-truth artifacts.

## Checks And Evidence

- Fresh and repaired databases expose exactly one nullable Workstream FK with `NO ACTION` update and `SET NULL` deletion behavior.
- Startup creates the versioned sibling backup before additive or structural migration work, validates it with SQLite `quick_check`, and never overwrites it on repeated startup.
- Preflight requires the complete supported column-name contract, permits only the documented compatible `updated_at` metadata variant and physical column-order drift, and refuses orphan associations, unknown fields, or a pre-existing migration table without coercion.
- Replacement SQL transforms only the plain `workstream_id INTEGER` definition. The transaction copies by quoted source-column names and requires exact `table_info`, full Run rows, Session Run links, Suggestion origin links, and global `foreign_key_check` before release.
- Workstream deletion nulls only the optional Run association. Run state, artifact references, linked Session identity, and Suggestion origin evidence remain present.
- Data Model ownership, privacy contract, deterministic Schema presentation, and the 328-object audit ledger are current at `keep 273`, `change 0`, `remove 0`, `defer 55`.

## Evidence Gaps

- None. The actual database had no linked Maintenance Session rows for its historical Runs, so exact dependent-Session preservation is additionally proven with synthetic linked rows.

## Findings

- None.

## Regression Notes

- Timestamp normalization, Run status/task vocabularies, Suggestion physical FK design, artifact contents, and native Claude Session behavior did not change.

## Route

- Next action: `pass`.
