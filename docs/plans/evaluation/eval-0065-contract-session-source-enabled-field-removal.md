# EVAL-0065: Session Source Enabled Field Removal — Contract

## Metadata

- ID: `eval-0065-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-70`
- Attempt: `1`
- Feature: [feat-0065-session-source-enabled-field-removal](../feature/feat-0065-session-source-enabled-field-removal.md)
- Spec: [spec-0065-session-source-enabled-field-removal](../spec/spec-0065-session-source-enabled-field-removal.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Session source registry schema and consumers
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Evaluated only removal of the unused `sources.enabled` field and its direct
  schema, migration, producer, consumer, and generated-contract surfaces.

## Checks

- Fresh `sources` DDL omits only `enabled` and retains the six approved fields.
- Compatible migration drops the legacy field idempotently.
- A synthetic legacy table with both `0` and `1` values preserves every retained
  source value, explicit source ID, child `source_files` and `sessions` row,
  `UNIQUE(kind)` coverage, and all foreign-key checks.
- Scanner upsert owns only kind, name, and root; source inventory no longer
  projects the removed field.
- Exact current-source search found no live `sources.enabled` producer, consumer,
  schema, value family, or generated semantic contract.
- `context_roots.enabled` and `external_source_instances.enabled` remain present
  in their distinct producers and consumers.
- Value Dictionary, Schema presentation, and current cleanup ledger checks pass.

## Evidence

- Environments checked: in-memory fresh SQLite, synthetic legacy SQLite with
  child rows, repository source inspection, generated artifact checks, and full
  automated suite.
- Targeted migration and source-inventory suite: 8 tests passed.
- Full repository suite: 293 tests passed.
- Privacy check: passed for 653 candidate files.
- `git diff --check`: passed.

## Evidence Gaps

- The private runtime database was intentionally not opened or migrated during
  evaluation. This does not block acceptance because compatible startup behavior
  is covered by the exact synthetic legacy shape and the Feature does not require
  mutating private runtime data as test evidence.

## Contract Evidence

- Producer surfaces: `schema.sql`, `db.py`, `ingest/scanner.py`.
- Consumer surfaces: `queries.py`, Sources inventory template contract, Data Model
  generators, and schema cleanup audit.
- Schemas and generated artifacts checked: fresh PRAGMA, legacy PRAGMA, unique
  autoindex, foreign keys, value registry/dictionaries, Schema presentation, and
  cleanup ledger.
- Stale-assumption check: current implementation and owner docs contain only the
  intentional legacy-migration or planning-history references.

## Findings

- None.

## Regression Notes

- Session synchronization remains unconditional for registered sources. Local
  Context and external Source Instance enablement contracts remain unchanged.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-08-02`: attempt 1 passed with exact retained-data, identity, descendant,
  FK, uniqueness, consumer, generated-artifact, full-suite, and privacy evidence.
