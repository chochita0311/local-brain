# FEAT-0031: Usage Attribution CHECK Parity

## Metadata

- ID: `feat-0031`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Make upgraded databases enforce the already-approved `usage_facts.attribution_basis` vocabulary while preserving every existing Usage Fact identity and stored value exactly.

## Acceptance Contract

- Fresh and upgraded `usage_facts` enforce only `git_root`, `workspace_path`, or `unassigned` for `attribution_basis`.
- A file-backed legacy database receives a non-overwriting pre-migration backup before structural repair begins.
- Migration preflight rejects any null, unknown, or structurally unexpected legacy state without changing the original table or its rows.
- The repair preserves every column definition except the missing attribution CHECK, every row and Fact ID, every token/cost/price value, and every frozen Project attribution value byte-for-byte at the SQLite value level.
- A bidirectional full-row comparison, row/ID parity, foreign-key check, and required-index restoration complete before the migration commits.
- Repeated startup is idempotent and does not rewrite an already-compliant table.

## Scope Boundary

- In:
  - narrow three-value `attribution_basis` vocabulary approved by the owner
  - backup, preflight, transactional table rebuild, exact-value comparison, rollback, and index restoration
  - fresh/compatible parity and invalid-row rejection tests
- Out:
  - recalculating or reattributing Usage Facts
  - correcting an unknown legacy value automatically
  - timestamp normalization or `attributed_at` nullability/default repair
  - pricing, normalizer, Dashboard, query, or Maintenance Run changes
  - other deferred closed vocabularies

## Contract Surfaces

- `usage_facts` table DDL and stable Fact identity
- compatible startup migration and local backup artifact
- Usage ingestion/repair and Dashboard consumers as protected regressions
- Data Model owner docs, presentation manifest, and cleanup audit parity

## Required Evaluators

- `contract`: exact one-constraint delta, stable schema metadata outside it, backup/failure boundary, identity/value preservation, and generated artifact parity.
- `functional`: valid upgrade, invalid preflight rollback, idempotent restart, Usage ingestion/repair/query regressions, and backup restore evidence.

## State Expectations

- Fresh or already compliant: no rebuild.
- Compatible valid legacy state: backup once, rebuild transactionally, compare all rows, restore indexes, commit.
- Invalid vocabulary or unexpected schema: abort without table or row mutation; retain the pre-migration backup.
- Repeated startup: no backup overwrite and no further rebuild.

## Dependencies

- FEAT-0030 must pass first.
- FEAT-0029 is `passed`.
- The human owner explicitly approved proposed migration boundary 3 and its three-value vocabulary on `2026-07-19`, with zero stored-data impact as a hard requirement.

## Likely Affected Surfaces

- `src/localbrain/db.py`
- Usage migration and contract tests
- Usage Data Model current-truth documentation
- generated Schema presentation and cleanup audit artifacts

## Pass Or Fail Checks

- Pass if every valid legacy value and Fact row is exactly identical after repair and the CHECK rejects a fourth value.
- Pass if invalid legacy values cause a rollback with the original table and rows intact.
- Pass if only the missing CHECK changes in the compatible table definition; deferred timestamp metadata remains unchanged.
- Pass if a restorable, non-overwritten backup exists for a file-backed migration.
- Pass if all Usage, schema, audit, full-suite, and privacy checks pass.
- Fail on any automatic reattribution, regeneration, row loss, ID change, timestamp-contract change, or backup omission.

## Regression Surfaces

- Usage Fact ingestion, idempotent repair, pricing snapshots, cost values, Project grouping, Dashboard history/trust, source cascades, and installed startup
- schema presentation, cleanup audit, and repository privacy

## Harness Trace

- Active spec doc: [spec-0031-usage-attribution-check-parity](../spec/spec-0031-usage-attribution-check-parity.md)
- Active run: [run-20260719-36-usage-attribution-check-parity](../run/run-20260719-36-usage-attribution-check-parity.md)
- Execution profile: `foundation-contract`
- Latest contract evaluator report: [eval-0031-contract-usage-attribution-check-parity](../evaluation/eval-0031-contract-usage-attribution-check-parity.md) (`PASS`)
- Latest functional evaluator report: [eval-0031-functional-usage-attribution-check-parity](../evaluation/eval-0031-functional-usage-attribution-check-parity.md) (`PASS`)
- Latest fix note: not created

## Continuity Notes

- `2026-07-19`: created as an approved but not-yet-active Feature from the human-approved third FEAT-0029 migration boundary; exact value preservation is the governing invariant.
- `2026-07-19`: entered RUN-20260719-36 after FEAT-0030 passed; SPEC-0031 limits compatible DDL change to the missing CHECK and requires backup, fail-closed preflight, and bidirectional full-row equality.
- `2026-07-19`: passed Contract and Functional evaluation with exact-row and column-metadata preservation, valid backup/recovery behavior, unexpected-state refusal, idempotency, 117 repository tests, and repository privacy checks.
