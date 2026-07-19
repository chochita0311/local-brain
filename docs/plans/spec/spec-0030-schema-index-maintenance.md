# SPEC-0030: Schema Index Maintenance

## Metadata

- ID: `spec-0030`
- Status: `approved`
- Run ID: `run-20260719-35`
- Attempt: `1`
- Parent Feature: [feat-0030-schema-index-maintenance](../feature/feat-0030-schema-index-maintenance.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: schema and compatible index migration
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Source Set

- Human request: proceed with approved boundary 1.
- Parent feature: FEAT-0030.
- Parent PRD: PRD-0003.
- Golden sources: FEAT-0029 decision summary and resolved object ledger, current `schema.sql`, compatible migration path, current query consumers, and synthetic audit tests.
- Relevant policies or contracts: Data Model baseline/delta ownership, Architecture, Privacy, foundation-contract profile, and execution-loop governance.

## Implementation Goal

- Move fresh and upgraded databases to the exact approved post-audit index set through an idempotent row-free migration with fail-safe redundancy proof.

## In-Scope Behavior

- Delete the three redundant CREATE INDEX definitions from fresh and compatible DDL.
- Add the three exact query-supporting definitions to fresh and compatible DDL.
- Before each existing redundant index is dropped, inspect `PRAGMA index_list/index_xinfo` and require a UNIQUE autoindex whose leading columns match the approved prefix.
- If coverage is absent, raise a bounded migration error before that DROP.
- Test fresh state, synthetic upgraded state, negative drift, unchanged rows, repeated execution, and EXPLAIN selection.
- Update only affected current-truth subject docs and regenerate the presentation/audit artifacts.

## Out-Of-Scope Behavior

- No table rebuild, row UPDATE, column change, query rewrite, metadata removal, Usage CHECK, Maintenance FK, timestamp, or wider vocabulary work.

## Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `tests/test_schema_migrations.py` and affected cleanup/data-model tests
- affected subject docs and derived presentation/audit artifacts

## State And Interaction Contract

- Migration is automatic on normal initialization, idempotent, and transactional under the caller's connection boundary.
- Absence of a redundant index is success; presence requires proven UNIQUE coverage before removal.
- New indexes use `CREATE INDEX IF NOT EXISTS` and do not imply row mutation.

## Data And Contract Assumptions

- SQLite UNIQUE constraints own the replacement autoindexes; their leading-column coverage is inspected, not assumed.
- The named query prefixes in FEAT-0029 remain current.
- Index names are application-owned constants and no runtime row values enter tracked evidence.

## Contract Surfaces

- Producer expectations: fresh schema and compatible migration converge on one 20-index set.
- Consumer expectations: current queries retain or gain the intended leading-key plan without result changes.
- Generated artifacts: Schema presentation and current audit ledger are derived from the effective schema and affected semantic owners.
- Source-of-truth owner: `schema.sql` for fresh DDL; `db.py` for existing-database convergence.
- Stale-assumption check: manifest/audit checker, PRAGMA parity, EXPLAIN, full tests, and privacy.

## Required Evaluators

- Contract: exact names/columns/order, preflight safety, fresh/compatible parity, docs/generated parity.
- Functional: no row delta, idempotency, query-plan use, runtime migration failure behavior, regressions.

## Acceptance Mapping

- Exact remove/add set: fresh and compatible PRAGMA assertions.
- Safe drops: positive and missing-autoindex negative fixtures.
- No row impact: deterministic pre/post row snapshots.
- Query support: three EXPLAIN assertions.
- Current truth: Data Model, presentation, and audit checks.

## Evaluation Focus

- Ensure schema initialization cannot recreate a removed redundant index before the compatibility path runs.
- Ensure a drift failure leaves the affected explicit index present.
- Ensure descending `version` and `mtime_ns` metadata are preserved in the new indexes.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: approved attempt 1 under the owner-approved exact six-index boundary.
