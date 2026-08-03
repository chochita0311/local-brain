# SPEC-0065: Session Source Enabled Field Removal

## Metadata

- ID: `spec-0065`
- Status: `approved`
- Run ID: `run-20260802-70`
- Attempt: `1`
- Parent Feature: [feat-0065-session-source-enabled-field-removal](../feature/feat-0065-session-source-enabled-field-removal.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: Session source registry schema and consumers
- Required Evaluators: `contract`, `functional`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- Human approval to remove `sources.enabled` as the first PRD-0012 implementation
  slice.
- Parent PRD and Feature, current `sources` DDL, compatible migrations, scanner,
  source inventory query, current data-model owners, and generated contracts.
- Architecture, privacy, PRD/Feature governance, and foundation-contract profile.

## Implementation Goal

- Converge fresh and upgraded databases on a `sources` registry with no false
  enablement field while preserving all real source identity and normalized data.

## In-Scope Behavior

- Delete the fresh `sources.enabled` declaration.
- Remove the scanner's `enabled = 1` conflict update and the source inventory
  projection of the field.
- Add an idempotent compatible `ALTER TABLE sources DROP COLUMN enabled` path.
- Add synthetic migration evidence with mixed legacy values and child rows,
  retained-value comparison, uniqueness/FK validation, and repeat migration.
- Update current owner docs and regenerate current value dictionary, Schema
  presentation, and cleanup ledger artifacts.

## Out-Of-Scope Behavior

- No settings file, source-key redesign, company Codex scanner, new source tabs,
  enablement replacement, Context/external behavior change, or runtime DB mutation
  outside ordinary future application startup.

## Affected Surfaces

- `schema.sql`, `db.py`, `ingest/scanner.py`, `queries.py`
- schema migration and source scan/query regression tests
- Source Registry Data Model and derived value/schema/audit artifacts
- PRD/Feature/Run continuity

## State And Interaction Contract

- Fresh or already migrated: the field is absent and compatible migration is a
  no-op.
- Legacy: the field is dropped regardless of its unused `0` or `1` value, with all
  retained columns and descendants preserved.
- Session synchronization: registered sources remain scanned without consulting a
  database enablement flag.

## Data And Contract Assumptions

- Implementation inspection proved no read path branches on `sources.enabled`.
- The field contains no authoritative user intent because no supported producer
  can disable a Session source and scanner upsert overwrote it to `1`.
- `context_roots.enabled` and `external_source_instances.enabled` are separate,
  live contracts and must remain byte-for-byte outside directly regenerated docs.

## Contract Surfaces

- Producer expectations: scanner upsert owns kind, name, and root only.
- Consumer expectations: source inventory receives no `enabled` member; templates
  already do not consume it.
- Generated artifacts: value dictionaries, Schema presentation, and current schema
  cleanup ledger are derived and must be regenerated from updated owners.
- Source-of-truth owner: `schema.sql` for fresh DDL, `db.py` for compatible
  convergence, and Source Registry Data Model for semantic truth.
- Stale-assumption check: exact repository search plus generator checks.

## Required Evaluators

- Contract: required.
- Design: not required.
- Functional: required for migration and scan/query behavior.
- UX heuristic: not required.

## Acceptance Mapping

- Fresh omission: PRAGMA schema test.
- Safe compatible removal: legacy mixed-value fixture with exact retained rows,
  descendants, indexes, and foreign-key checks.
- Idempotency: repeated compatible migration.
- Consumer cleanup: scanner/query tests and source search.
- Isolation: Context and external enablement tests plus full suite.
- Generated parity: value dictionary, Schema presentation, cleanup audit, and
  privacy checks.

## Evaluation Focus

- Ensure one-column removal does not rebuild or renumber the source parent table.
- Ensure no broad search-and-replace touches the two real enabled contracts.
- Ensure historical audit evidence may mention the former field while every
  current owner and generated artifact reflects its removal.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: approved attempt 1 for the owner-selected, one-field Foundation
  removal with Contract and Functional evaluation.
