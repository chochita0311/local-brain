# SPEC-0037: Maintenance Run Workstream FK Parity

## Metadata

- ID: `spec-0037`
- Status: `approved`
- Run ID: `run-20260719-42`
- Attempt: `1`
- Parent Feature: [feat-0037-maintenance-run-workstream-fk-parity](../feature/feat-0037-maintenance-run-workstream-fk-parity.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Implementation Goal

- Rebuild only a compatible `maintenance_runs` table that lacks its fresh-schema Workstream FK, preserving all operational evidence and failing closed on ambiguity.

## Migration Contract

1. Startup detects the exact `workstream_id → workstreams.id ON DELETE SET NULL` relation before `schema.sql` and compatible migration execution.
2. When a pre-existing Maintenance Run table lacks the relation, startup creates and validates a non-overwriting `-pre-maintenance-workstream-fk-v1.bak` beside the database.
3. Compatible additive columns run before table reconstruction so the source has the complete expected column set.
4. Preflight compares source column contracts by name to fresh DDL while allowing only the documented compatible `updated_at TEXT` nullable/no-default variant and arbitrary physical column order.
5. Preflight rejects an existing migration temp table and every non-null `workstream_id` without a current `workstreams.id` target.
6. Source SQL is transformed only at the plain nullable `workstream_id INTEGER` definition to add `REFERENCES workstreams(id) ON DELETE SET NULL`; no other column metadata or constraint is rewritten.
7. With foreign keys disabled only around one explicit immediate transaction and legacy rename behavior enabled, the migration renames the source, creates the transformed table, copies by quoted source-column names, compares complete ordered Run rows, drops the legacy table, and commits.
8. Postflight restores FK mode, requires the exact FK, exact dependent Session and Suggestion reference snapshots, and an empty global `foreign_key_check`.
9. Repeated execution is a no-op.

## Data Policy

- Valid and null associations are preserved byte-for-value.
- Orphan associations abort. They are not set to null automatically because that would erase the only stored Workstream attribution without owner review.
- `ON DELETE SET NULL` applies only to future explicit Workstream deletion after the FK exists.
- Run IDs, statuses, timestamps, counters, JSON fields, summaries, errors, and artifact paths remain exact.

## Evaluation Focus

- Fresh/compatible parity and legacy additive column-order tolerance.
- File backup creation, validation, non-overwrite, rollback, and idempotency.
- Exact Run rows plus Session/Suggestion dependent identities before and after.
- Valid, null, orphan, unexpected shape, temp-table collision, and Workstream deletion states.
- Actual local database preflight/migration with retained-row comparison and integrity checks.

## Open Blockers

- None. Actual preflight reports zero orphan Workstream IDs.
