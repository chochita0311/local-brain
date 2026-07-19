# FEAT-0035: Maintenance Session Usage Bridge

## Metadata

- ID: `feat-0035`
- Status: `superseded`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Keep `maintenance_runs` as the Task Runner execution ledger while connecting every in-app Task Runner execution to one metadata-only Maintenance Session and its directly observed Usage Records.

## Acceptance Contract

- Fresh and upgraded databases enforce `session_class IN ('work', 'maintenance')` and `index_policy IN ('full', 'metadata_only')`.
- `sessions.maintenance_run_id` is a nullable foreign key to `maintenance_runs.id`, is unique when present, and can identify only a primary metadata-only Maintenance Session.
- The compatible Session-table repair is backup-backed, rejects invalid values, duplicate Run links, orphan Run links, or an unexpected table shape, and preserves every existing Session row, ID, child foreign key, user-curated relation, and Usage Record.
- Preparing an in-app Task Runner execution creates its `maintenance_runs` ledger row and exactly one linked Maintenance Session whose source path is the private `stream.jsonl` artifact.
- Claude `stream-json` assistant usage is normalized through the existing Claude token/model/pricing contract. A final-result aggregate is used only as a bounded fallback when no assistant usage is available, so the two representations are never double counted.
- Completed, failed, cancelled, and interrupted executions retain directly observed usage. Historical in-app Runs with an existing stream artifact are backfilled idempotently; marker-only prepared rows do not receive synthetic Sessions.
- Maintenance Sessions remain outside activity events, full-text search, ordinary Session lists, Workstream retrieval, candidate evidence, fingerprints, and work statistics.
- Maintenance Usage Records remain included in Dashboard token and estimated-cost totals while the primary-work Session denominator continues to exclude them.
- Ordinary Claude source cleanup and usage-contract reconciliation do not delete Runner-owned Sessions or Usage Records.
- Run lifecycle, artifacts, structured results, and Suggestion provenance remain owned by `maintenance_runs.id`.

## Scope Boundary

- In:
  - fresh Session constraints and backup-backed compatible table repair
  - one linked Maintenance Session per in-app Task Runner Run
  - stream-json usage parsing, pricing, idempotent reconciliation, and terminal-state finalization
  - eligible historical Run backfill
  - manual marker FK validation and fail-closed duplicate handling
  - scanner preservation and Dashboard regression evidence
  - canonical Data Model, Schema presentation, architecture, Task Runner policy, and PRD continuity
- Out:
  - removing `maintenance_runs`
  - persisting an additional ordinary Claude CLI Session for in-app Runs
  - creating separate LocalBrain Session rows for Runner subagents
  - changing visible Dashboard layout, filters, or copy
  - indexing Runner prompts, output, artifacts, or activity text
  - deleting or coercing an invalid legacy Session row to make migration succeed

## Surface Lanes

- Schema and migration lane: fresh DDL, compatible repair, backup, exact preservation, FK/CHECK/UNIQUE validation.
- Runner producer lane: Run preparation, Maintenance Session creation, stream usage normalization, terminal-state reconciliation, historical backfill.
- Consumer lane: scanner/contract-repair preservation, retrieval exclusion, Dashboard totals and denominator regression.
- Documentation and generated lane: Data Model owners, Schema presentation, architecture, Task Runner policy, PRD and evaluation trace.

## Required Evaluators

- `contract`: fresh/compatible parity, value vocabulary, FK/UNIQUE/cardinality, backup and fail-closed behavior, producer ownership, generated schema parity, stale-assumption checks.
- `functional`: completed/failed/cancelled/interrupted and historical Run paths, no double counting, scanner preservation, Dashboard eligibility, idempotency, full regression, privacy.

## Dependencies

- FEAT-0029 established the cleanup decision ledger.
- FEAT-0031 established the backup-backed compatible constraint-repair pattern.
- FEAT-0034 established the canonical Usage Record contract.
- The human owner separately approved the Session-to-Run relation and Usage bridge on `2026-07-19`; the older `maintenance_runs.workstream_id` compatibility candidate remains outside this Feature.

## Pass Or Fail Checks

- Pass if invalid Session values and duplicate/orphan Run relations are refused before mutation while valid legacy rows and all dependent rows remain exact.
- Pass if one prepared Task Runner Run immediately has one linked Maintenance Session and repeated synchronization never creates a second.
- Pass if assistant usage and result-level aggregate representations cannot both contribute, every terminal path preserves observed usage, and existing stream-backed Runs backfill once.
- Pass if maintenance usage changes token/cost totals but never the primary-work Session count or work candidate set.
- Fail on silent value coercion, orphan linkage, duplicate Run Sessions, usage double counting, scanner deletion, search/retrieval leakage, or unbacked structural mutation.

## Harness Trace

- Active spec doc: [spec-0035-maintenance-session-usage-bridge](../spec/spec-0035-maintenance-session-usage-bridge.md)
- Active run: [run-20260719-40-maintenance-session-usage-bridge](../run/run-20260719-40-maintenance-session-usage-bridge.md)
- Execution profile: `foundation-contract`
- Latest evaluator reports: [contract](../evaluation/eval-0035-contract-maintenance-session-usage-bridge.md), [functional](../evaluation/eval-0035-functional-maintenance-session-usage-bridge.md)

## Continuity Notes

- `2026-07-19`: approved directly by the owner after confirming that `maintenance_runs` is necessary as the execution extension ledger and that the missing Session/Usage bridge, not the table, is the defect.
- `2026-07-19`: passed Contract and Functional evaluation after backup-backed actual migration, exact preservation of 171 existing Sessions, two metadata-only historical Run links, 139 repository tests, generated-schema parity, privacy, and idempotency checks. Historical stream files were absent, so no old Usage Record was invented.
- `2026-07-19`: human review invalidated the producer portion: `--no-session-persistence` and a synthetic stream-backed Session duplicate the native Claude Session model and add unnecessary ownership. The CHECK/FK/UNIQUE schema repair remains valid, but [FEAT-0036](feat-0036-native-maintenance-session-and-runner-ui-consolidation.md) supersedes this Feature as the current Runner-to-Session contract.
