# SPEC-0031: Usage Attribution CHECK Parity

## Metadata

- ID: `spec-0031`
- Status: `approved`
- Run ID: `run-20260719-36`
- Attempt: `1`
- Parent Feature: [feat-0031-usage-attribution-check-parity](../feature/feat-0031-usage-attribution-check-parity.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: Usage Fact compatibility migration
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Source Set

- Human request: restore boundary 3 with no stored-data impact.
- Parent feature: FEAT-0031.
- Parent PRD: PRD-0003.
- Golden sources: FEAT-0029 attribution candidate, PRD-0004 immutable Usage contracts, current fresh and compatible `usage_facts` DDL, Usage producers/consumers, and passed FEAT-0030.
- Relevant policies or contracts: Data Model baseline/delta, Privacy, Architecture, foundation-contract profile, execution governance.

## Implementation Goal

- Add only the missing compatible `attribution_basis` three-value CHECK through a backup-backed, transactional, exact-value-preserving migration that refuses unknown legacy states.

## In-Scope Behavior

- Detect a file-backed pre-existing `usage_facts` table without the approved CHECK before normal schema/compatible migrations and create a versioned sibling backup without overwriting an existing backup.
- Validate the backup with SQLite `quick_check` before structural repair.
- After existing compatible columns/backfills are ready, preflight the exact allowed attribution vocabulary and the expected table/column shape.
- Derive the replacement DDL from the current compatible table SQL and inject only `CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned'))`; do not substitute the whole fresh table definition.
- Within a SAVEPOINT, create a repair table, copy all columns by name, compare row count and both directions of full-row `EXCEPT`, verify IDs and foreign keys, replace the table, and restore the three Usage indexes.
- Roll back the SAVEPOINT and retain the original table on any error.
- Skip backup/rebuild for a fresh or already-compliant table; repeated startup is idempotent.

## Out-Of-Scope Behavior

- No attribution recalculation, invalid-value coercion, Fact regeneration, timestamp column metadata repair, price/normalizer/query/UI change, or other vocabulary enforcement.
- No Activity Event column removal or Maintenance Run foreign-key work.

## Affected Surfaces

- `src/localbrain/db.py`
- `tests/test_schema_migrations.py` and Usage regression tests
- Usage Data Model current-truth docs
- generated Schema presentation and current audit artifacts

## State And Interaction Contract

- Already compliant: return without write.
- Valid compatibility drift: backup once, repair in one SAVEPOINT, verify, release.
- Invalid value, unexpected definition, copy mismatch, or FK failure: rollback repair and raise a bounded error without rewriting data.
- Existing backup: preserve it; never overwrite the pre-migration recovery point.

## Data And Contract Assumptions

- Approved values are exactly `git_root`, `workspace_path`, and `unassigned`.
- Fact IDs and frozen attribution/cost fields are historical evidence and cannot be regenerated as a migration strategy.
- Existing compatible `attributed_at` nullability and other deferred timestamp metadata are preserved, even though fresh DDL may differ.
- Full-row SQLite equality via bidirectional `EXCEPT` is the commit gate; no private value enters logs or tracked evidence.

## Contract Surfaces

- Producer expectations: `usage.py` continues writing only approved basis values.
- Consumer expectations: Usage queries and Dashboard receive identical stored rows.
- Generated artifacts: Usage owner doc, Schema presentation, cleanup decision/ledger.
- Source-of-truth owner: fresh rule in `schema.sql`; exact compatible convergence in `db.py`.
- Stale-assumption check: table SQL delta, PRAGMA, backup/restore, invalid fixture, exact rows, Usage suite, generated checks, full tests, privacy.

## Required Evaluators

- Contract: one-constraint-only metadata delta, backup and rollback boundary, identity/value equality, generated parity.
- Functional: valid/invalid upgrade, idempotent restart, backup behavior, CHECK rejection, Usage regressions.

## Acceptance Mapping

- Three-value enforcement: repaired SQL plus invalid INSERT rejection.
- Zero stored-data impact: row count, ID set, and bidirectional full-row equality gates.
- No adjacent schema repair: pre/post column metadata comparison and SQL delta inspection.
- Recovery: file-backed non-overwritten backup with `quick_check` and restore comparison.
- Failure safety: invalid basis fixture retains original SQL/rows after rollback.

## Evaluation Focus

- Ensure the migration never derives historical attribution from current workspace paths.
- Ensure final Usage indexes exist after table replacement.
- Ensure a direct `_run_compatible_migrations(..., include_data_migrations=False)` does not rewrite a legacy table because data backfill/preflight prerequisites are intentionally unavailable.

## Open Blockers

- None. The owner explicitly approved the narrow vocabulary and zero-data-impact rule.

## Continuity Notes

- `2026-07-19`: approved attempt 1 after FEAT-0030 passed; only the missing compatible CHECK may change.
