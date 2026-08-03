# FEAT-0065: Session Source Enabled Field Removal

## Metadata

- ID: `feat-0065`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Remove the unused `sources.enabled` field so the local Session source registry
  no longer advertises a lifecycle control that does not exist.

## Acceptance Contract

- Fresh databases omit only `sources.enabled` from the `sources` table.
- Compatible startup removes the legacy field idempotently while preserving every
  retained source value, source ID, child row, uniqueness constraint, and foreign
  key relationship.
- Session synchronization continues to scan every registered Session source and
  source inventory queries no longer select the removed field.
- `context_roots.enabled` and `external_source_instances.enabled` retain their
  existing behavior and contracts.
- Current data-model, value-registry, Schema presentation, and cleanup-ledger
  artifacts contain no live `sources.enabled` contract.

## Scope Boundary

- In:
  - fresh `sources` DDL and compatible one-column removal
  - scanner upsert and source inventory projection cleanup
  - migration, idempotency, source-scan, and adjacent-enable regression tests
  - current owner docs and derived schema/value/audit artifacts
- Out:
  - multi-source source-key migration or settings-file implementation
  - Session source enable/disable UI or replacement flag
  - any change to Context root or external Source Instance enablement
  - runtime source deletion, descendant deletion, or native file mutation

## Contract Surfaces

- `sources` fresh and compatible schema
- scanner registry upsert and Session-source scan selection
- source inventory query shape
- Local Context and external access enablement isolation
- generated Data Model value dictionaries, Schema presentation, and cleanup ledger

## Required Evaluators

- `contract`: exact field removal, retained schema/identity/FK parity, consumer
  cleanup, adjacent enablement isolation, and generated-artifact freshness.
- `functional`: compatible upgrade, repeat startup, Session scanning, source
  inventory, and Context/external enablement regressions.

## Dependencies

- PRD-0012 is approved for sequential Feature execution.
- Human owner explicitly selected field removal as the first implementation slice
  on `2026-08-02`.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/queries.py`
- schema and ingestion tests
- Source Registry Data Model owner and derived schema/value/audit artifacts

## Pass Or Fail Checks

- Pass if fresh and upgraded `sources` tables omit only `enabled` and preserve
  retained rows, IDs, descendants, uniqueness, and foreign keys exactly.
- Pass if repeated migration is a no-op and Session scanning remains unconditional
  for registered sources.
- Pass if searches find no current `sources.enabled` producer, consumer, schema,
  or generated contract outside historical execution evidence.
- Pass if targeted, full-suite, generated-artifact, and privacy checks pass.
- Fail on changes to `context_roots.enabled`,
  `external_source_instances.enabled`, source identity, or descendant data.

## Regression Surfaces

- Claude/Codex synchronization, Sources inventory, Local Context registration and
  removal, external access authorization, schema generation, and startup migration.

## Harness Trace

- Active spec doc: [spec-0065-session-source-enabled-field-removal](../spec/spec-0065-session-source-enabled-field-removal.md)
- Active run: [run-20260802-70-session-source-enabled-field-removal](../run/run-20260802-70-session-source-enabled-field-removal.md)
- Execution profile: `foundation-contract`
- Latest evaluator reports:
  [contract](../evaluation/eval-0065-contract-session-source-enabled-field-removal.md)
  and [functional](../evaluation/eval-0065-functional-session-source-enabled-field-removal.md)
- Latest fix note: not created

## Continuity Notes

- `2026-08-02`: owner approved this narrow first implementation slice after code
  inspection proved the field does not control Session synchronization.
- `2026-08-02`: attempt 1 passed fresh and legacy schema, exact retained-data,
  idempotency, scanner/query, adjacent enablement, generated-artifact, 293-test,
  and privacy checks.
