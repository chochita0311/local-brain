# FEAT-0037: Maintenance Run Workstream FK Parity

## Metadata

- ID: `feat-0037`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Give upgraded databases the same optional `maintenance_runs.workstream_id → workstreams.id ON DELETE SET NULL` ownership relation as fresh databases without changing any retained Run or dependent record.

## Acceptance Contract

- Fresh and upgraded databases expose one physical nullable FK from `maintenance_runs.workstream_id` to `workstreams.id` with `ON DELETE SET NULL`.
- A non-overwriting, SQLite-validated backup is created before the first compatible structural mutation.
- Preflight requires the exact supported Maintenance Run column contract and rejects every non-null Workstream ID whose target is absent; no orphan value is silently coerced or deleted.
- Compatible repair preserves every Maintenance Run column value and ID exactly, regardless of legacy additive column order or the already documented compatible `updated_at` metadata difference.
- Linked `sessions.maintenance_run_id`, `suggestions.origin_run_id`, Run artifacts, indexes, and lifecycle state remain unchanged.
- Deleting a Workstream sets the Run's `workstream_id` to null and does not delete the Run, its Session, Suggestion provenance, or artifact references.
- Repeated startup is a no-op and preserves the first valid backup.

## Scope Boundary

- In:
  - FK detection and backup-backed compatible `maintenance_runs` rebuild
  - exact shape/value/orphan preflight and post-copy comparison
  - dependent Session/Suggestion preservation and SET NULL behavior
  - actual local database migration after synthetic proof
  - Data Model, Schema presentation, audit decision, PRD, and harness continuity
- Out:
  - changing Run status/task vocabularies or timestamp formats/defaults
  - deleting `maintenance_runs` or artifact files
  - adding a physical FK to `suggestions.origin_run_id`
  - changing the native Claude Maintenance Session contract from FEAT-0036

## Contract Surfaces

- `maintenance_runs.workstream_id` DDL and `PRAGMA foreign_key_list`.
- Startup backup `localbrain.db-pre-maintenance-workstream-fk-v1.bak`.
- Compatible table reconstruction, Run row order-independent exact comparison, and `foreign_key_check`.
- Workstream deletion semantics consumed by Runner history and operational provenance.

## Dependencies

- FEAT-0029 identified and bounded the fresh/compatible drift.
- FEAT-0031 and FEAT-0035 established the non-overwriting backup and exact-value-preserving rebuild patterns.
- FEAT-0036 keeps `maintenance_runs` as the execution ledger linked to a native Claude Session.

## Pass Or Fail Checks

- Pass if fresh and migrated schemas expose the same FK target and delete action.
- Pass if valid/null Workstream associations, every Run field, dependent Session FK, and Suggestion origin survive exactly.
- Pass if orphan or unexpected-shape input fails before table mutation and before any value coercion.
- Pass if Workstream deletion nulls only the optional association and repeated startup is idempotent.
- Fail on Run deletion, ID drift, artifact-field drift, orphan coercion, dependent relation loss, backup overwrite, or FK-check error.

## Regression Surfaces

- Task Runner creation/list/detail/restart behavior.
- Native Maintenance Session linkage and Usage ownership.
- Suggestion provenance and Workstream deletion.
- Schema presentation and cleanup audit counts/decisions.

## Harness Trace

- Active spec doc: [spec-0037-maintenance-run-workstream-fk-parity](../spec/spec-0037-maintenance-run-workstream-fk-parity.md)
- Active run: [run-20260719-42-maintenance-run-workstream-fk-parity](../run/run-20260719-42-maintenance-run-workstream-fk-parity.md)
- Execution profile: `foundation-contract`
- Latest contract evaluator report: [eval-0037-contract-maintenance-run-workstream-fk-parity](../evaluation/eval-0037-contract-maintenance-run-workstream-fk-parity.md) (`PASS`)
- Latest functional evaluator report: [eval-0037-functional-maintenance-run-workstream-fk-parity](../evaluation/eval-0037-functional-maintenance-run-workstream-fk-parity.md) (`PASS`)
- Latest fix note: not created

## Continuity Notes

- `2026-07-19`: the human owner approved the last FEAT-0029 migration boundary after confirming that `workstream_id` identifies the Workstream from which a Maintenance Run was executed.
- `2026-07-19`: passed Contract and Functional evaluation after synthetic valid/null/orphan/shape/collision coverage, exact actual-DB preservation, validated backup, fresh/compatible parity, 142 repository tests, and privacy/document checks.
