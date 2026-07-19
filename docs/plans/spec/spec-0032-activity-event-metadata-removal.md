# SPEC-0032: Activity Event Metadata Removal

## Metadata

- ID: `spec-0032`
- Status: `approved`
- Run ID: `run-20260719-37`
- Attempt: `1`
- Parent Feature: [feat-0032-activity-event-metadata-removal](../feature/feat-0032-activity-event-metadata-removal.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: Activity Event schema and producer contract
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Source Set

- Human approval to remove the unused extension slot and add a concrete field later if a real contract emerges.
- FEAT-0029 audit evidence, FEAT-0032, current `activity_events` DDL, both parsers, scanner, and all current consumers.
- Data Model baseline/delta, privacy, architecture, developer guide, and foundation-contract profile.

## Implementation Goal

- Converge fresh and upgraded Activity Event schemas on the nine-field normalized event contract while refusing to discard any unexpected non-null metadata.

## In-Scope Behavior

- Delete the fresh `metadata_json` declaration.
- Remove `ParsedEvent.metadata` and the scanner's JSON serialization/binding.
- Add an idempotent compatible migration that checks `COUNT(*) WHERE metadata_json IS NOT NULL`; raise before DDL when nonzero, otherwise drop the column.
- Preserve all retained columns and rows and keep the composite UNIQUE autoindex coverage.
- Update only the Activity owner doc, generated presentation, current audit decision source/ledger, and delta execution artifacts.

## Out-Of-Scope Behavior

- No raw-payload ingestion, event-type change, table removal, event regeneration, Usage change, or Maintenance Run work.

## Affected Surfaces

- `schema.sql`, `db.py`, `ingest/common.py`, `ingest/scanner.py`
- schema/event regression tests
- Workspace And Session Activity owner doc
- generated Schema presentation and FEAT-0029 current ledger

## State And Interaction Contract

- Column absent: return without mutation.
- Column present and all values null: `ALTER TABLE ... DROP COLUMN`, then normal startup continues.
- Column present with any value: bounded error before `ALTER`; the surrounding startup transaction leaves the database unchanged.

## Data And Contract Assumptions

- Current official parsers have never produced metadata, but runtime preflight remains authoritative for a specific database.
- Activity Events are source-derived; nevertheless, a non-null value is treated as unknown evidence and never silently discarded.
- Retained columns are compared exactly in synthetic upgrade tests.

## Contract Surfaces

- Producer: `ParsedEvent` and scanner nine-field insert.
- Consumers: queries, activity calculation, retrieval, search projection; none receive a replacement metadata field.
- Source of truth: `schema.sql` fresh DDL and `db.py` compatible convergence.
- Generated consumers: Data Model documentation and Schema presentation.

## Acceptance Mapping

- No unused field: fresh PRAGMA and parser/scanner source checks.
- Safe compatible removal: all-null and non-null legacy fixtures.
- No event impact: exact retained-row equality, identity/count parity, UNIQUE/FK checks, consumer regressions.
- Idempotency: repeat compatible migration.

## Evaluation Focus

- Ensure `ALTER TABLE DROP COLUMN` does not remove or recreate unrelated event structure.
- Ensure static all-null evidence never bypasses runtime non-null refusal.
- Ensure no tracked artifact includes runtime row values.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: approved attempt 1 with an all-null runtime precondition and exact retained-value preservation.
