# FEAT-0030: Schema Index Maintenance

## Metadata

- ID: `feat-0030`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Apply the owner-approved index-only audit boundary: remove three proven redundant named indexes and add three indexes that match current query prefixes without transforming any row.

## Acceptance Contract

- Fresh and upgraded databases omit `idx_events_session_sequence`, `idx_local_resources_path`, and `idx_checkpoint_resource_refs`.
- An upgraded database drops each redundant index only after confirming that a UNIQUE autoindex covers its required leading columns; unexpected drift fails before that index is removed.
- Fresh and upgraded databases contain `idx_checkpoints_workstream_version(workstream_id, version DESC)`, `idx_documents_source(source_id)`, and `idx_documents_workspace(workspace_id, mtime_ns DESC)`.
- The migration is idempotent and changes no table row, primary key, UNIQUE constraint, foreign key, or application relation.
- Synthetic EXPLAIN evidence selects every added index for its named current query.
- Schema owner docs, generated presentation, and the current cleanup ledger advance to the post-migration truth.

## Scope Boundary

- In:
  - exact six-index DDL delta approved from FEAT-0029
  - fresh schema and compatible startup migration parity
  - fail-safe autoindex preflight before redundant-index removal
  - query-plan, idempotency, row-preservation, generated-presentation, and audit checks
- Out:
  - column removal
  - row rewriting
  - Usage Fact constraint repair
  - Maintenance Run foreign-key repair
  - query rewrites or unrelated performance tuning

## Contract Surfaces

- `schema.sql` fresh named-index set
- `db.py` compatible/idempotent index migration
- current Workstream, checkpoint, Context Document, Activity Event, and Resource query prefixes
- Data Model owner docs, presentation manifest, and cleanup audit parity

## Required Evaluators

- `contract`: exact index identities/columns, autoindex preflight, fresh/upgrade parity, and current-truth artifact parity.
- `functional`: row preservation, migration idempotency, named query-plan use, and regression suite.

## State Expectations

- Fresh: only the post-migration named-index set exists.
- Compatible upgrade: redundant indexes are removed only with proven UNIQUE coverage and the new indexes are created.
- Drifted upgrade: migration aborts before removing an index whose required UNIQUE coverage is absent.
- Repeated startup: no additional schema or row change.

## Dependencies

- FEAT-0029 is `passed`.
- The human owner explicitly approved proposed migration boundary 1 on `2026-07-19`.

## Likely Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- schema migration and cleanup tests
- affected Data Model subject owners
- generated Schema presentation and cleanup audit artifacts

## Pass Or Fail Checks

- Pass if all six exact index outcomes hold on fresh and synthetic upgraded databases.
- Pass if every redundant DROP has a UNIQUE-autoindex preflight and a negative drift fixture proves fail-before-drop.
- Pass if pre/post table rows are identical and repeated migration is idempotent.
- Pass if EXPLAIN selects all three additions for their current query prefixes.
- Pass if generated schema and cleanup audit checks are current and the complete regression/privacy checks pass.
- Fail if any row, table constraint, identity, or unrelated index changes.

## Regression Surfaces

- Session detail ordering
- Local Resource path uniqueness and lookup
- checkpoint resource detail
- Workstream checkpoint allocation and retrieval
- Context source reconciliation and Project summaries
- schema presentation, cleanup audit, and repository privacy

## Harness Trace

- Active spec doc: [spec-0030-schema-index-maintenance](../spec/spec-0030-schema-index-maintenance.md)
- Active run: [run-20260719-35-schema-index-maintenance](../run/run-20260719-35-schema-index-maintenance.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract](../evaluation/eval-0030-contract-schema-index-maintenance.md), [functional](../evaluation/eval-0030-functional-schema-index-maintenance.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-19`: created as an approved Feature from the human-approved first FEAT-0029 migration boundary; no row transformation is authorized.
- `2026-07-19`: passed attempt 1 with fail-before-drop UNIQUE preflight, exact six-index convergence, unchanged synthetic rows, idempotent migration, three selected EXPLAIN plans, 112 passing tests, and current generated/audit/privacy evidence.
