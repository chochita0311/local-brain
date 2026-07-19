# SPEC-0034: Usage Record Canonical Terminology

## Metadata

- ID: `spec-0034`
- Status: `approved`
- Run ID: `run-20260719-39`
- Attempt: `1`
- Parent Feature: [feat-0034-usage-record-canonical-terminology](../feature/feat-0034-usage-record-canonical-terminology.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Surface: `fullstack`
- Execution Profile: `foundation-contract`
- Surface Lanes: persistence and ingestion → query and presentation → docs and generated artifacts
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Implementation Goal

- Rename the normalized source-backed usage entity to `Usage Record` at every current contract boundary while treating `usage_facts` only as a one-way legacy upgrade input.

## Migration Contract

1. Before fresh DDL runs, detect `usage_facts` and `usage_records` from `sqlite_master`.
2. Refuse startup if both exist; do not merge or choose a winner.
3. If only `usage_facts` exists, preserve the existing attribution-backup precondition, rename the table in place to `usage_records`, and replace only its explicit legacy index names.
4. Run canonical fresh DDL and compatible column/CHECK/index migrations against `usage_records`.
5. If only `usage_records` or neither exists, perform no name migration.
6. Prove idempotency, table SQL/column metadata/row equality, foreign-key validity, and absence of the legacy table.

## Canonical Name Mapping

- `usage_facts` → `usage_records`
- `ParsedUsageFact` → `ParsedUsageRecord`
- `fact_id` → `usage_record_id`
- Parsed Session `usage_facts` → `usage_records`
- `store_usage_facts` → `store_usage_records`
- `reconcile_usage_fact_contract` → `reconcile_usage_record_contract`
- `fact_count` → `usage_record_count`
- `token_fact_count` → `token_covered_record_count`
- `priced_fact_count` → `priced_record_count`
- `selected_fact_count` → `selected_usage_record_count`

`source_record_id` remains unchanged because it identifies the upstream Claude/Codex record from which the LocalBrain Usage Record was derived.

## Invariants

- The persisted `id` values are unchanged; the new code-level name is `usage_record_id`.
- No table rebuild or data transformation is part of the name migration.
- Token components, model normalization, total semantics, source capability, price snapshot, calculation version/state, Project attribution, imported/calculated timestamps, and repair semantics remain byte-equivalent.
- Visible Dashboard copy and responsive layout remain unchanged from FEAT-0033.

## Evidence

- Fresh/canonical/legacy/coexistence synthetic migration tests.
- Exact pre/post ordered-row digest and schema metadata comparison on the actual local database without placing private values in tracked artifacts.
- Current-name search with bounded allowlist for legacy compatibility and historical artifacts.
- Generated Schema presentation and cleanup audit checks.
- Focused Usage/Schema/Dashboard tests, complete suite, browser route, and privacy scan.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: attempt 1 approved by the human owner; migration is a name-only in-place boundary, not a rebuild or semantic rewrite.
