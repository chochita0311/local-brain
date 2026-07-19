# FEAT-0032: Activity Event Metadata Removal

## Metadata

- ID: `feat-0032`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Remove the never-produced `activity_events.metadata_json` extension slot without changing normalized event identity, ordering, content, provenance, or consumers.

## Acceptance Contract

- Fresh databases omit `activity_events.metadata_json`.
- Upgraded databases remove the column only when every stored value is `NULL`; any non-null value fails before schema mutation.
- `ParsedEvent` no longer exposes an unused metadata dictionary and scanner inserts only the nine retained event fields.
- Every retained Activity Event value, row count, deterministic ID, UNIQUE boundary, Session cascade, and ordering path remains unchanged.
- Repeated startup is idempotent.

## Scope Boundary

- In:
  - remove the unused fresh-schema column, parser extension member, and scanner binding
  - fail-closed compatible column removal
  - fresh, valid legacy, non-null refusal, and idempotency tests
  - affected Session/Activity current-truth docs and generated Schema/audit artifacts
- Out:
  - removing `activity_events` or any event row
  - storing new tool arguments, results, or opaque source payloads
  - changing event types, text eligibility, Session ingestion, activity calculation, or retrieval
  - Usage Dashboard terminology work, which belongs to FEAT-0033

## Contract Surfaces

- `activity_events` DDL and compatible migration
- `ParsedEvent` normalized payload and scanner insert contract
- Session detail, activity attribution, retrieval evidence, and search regressions
- Schema presentation and cleanup decision ledger

## Required Evaluators

- `contract`: exact one-column removal, fail-closed legacy preflight, producer/consumer parity, generated artifacts.
- `functional`: valid upgrade, non-null refusal, idempotency, event row preservation, Session/activity/retrieval regressions.

## State Expectations

- Fresh or already migrated: no `metadata_json` column and no extra write.
- Legacy with all-null metadata: remove only the column.
- Legacy with any non-null metadata: raise before mutation and retain the table and values.

## Dependencies

- FEAT-0030 and FEAT-0031 are `passed`.
- The human owner explicitly approved cleanup boundary 2 on `2026-07-19` after confirming the field was an unused initial extension hook.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/scanner.py`
- schema migration and event consumer tests
- Workspace/Session Activity Data Model owner and generated schema/audit artifacts

## Pass Or Fail Checks

- Pass if fresh and compatible schemas omit only `metadata_json`.
- Pass if all retained values are identical after a valid legacy upgrade.
- Pass if one non-null metadata value blocks removal without mutation.
- Pass if Session detail, activity, retrieval, full-suite, and privacy checks pass.
- Fail on any event-row deletion, content change, source-line loss, identity change, or automatic discard of non-null metadata.

## Regression Surfaces

- Claude/Codex parsing, Session import and conversation detail, active-time attribution, retrieval evidence, search indexing, schema presentation, privacy.

## Harness Trace

- Active spec doc: [spec-0032-activity-event-metadata-removal](../spec/spec-0032-activity-event-metadata-removal.md)
- Active run: [run-20260719-37-activity-event-metadata-removal](../run/run-20260719-37-activity-event-metadata-removal.md)
- Execution profile: `foundation-contract`
- Latest contract evaluator report: [eval-0032-contract-activity-event-metadata-removal](../evaluation/eval-0032-contract-activity-event-metadata-removal.md) (`PASS`)
- Latest functional evaluator report: [eval-0032-functional-activity-event-metadata-removal](../evaluation/eval-0032-functional-activity-event-metadata-removal.md) (`PASS`)
- Latest fix note: not created

## Continuity Notes

- `2026-07-19`: owner approved boundary 2; the Feature requires an all-null preflight rather than assuming static producer evidence proves every local database value.
- `2026-07-19`: passed after fresh omission, all-null legacy removal, non-null refusal, exact retained-value equality, actual runtime count/digest parity, 120 repository tests, generated artifact parity, and privacy verification.
