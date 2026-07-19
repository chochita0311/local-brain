# EVAL-0030: Schema Index Maintenance — Contract

## Metadata

- ID: `eval-0030-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-35`
- Attempt: `1`
- Feature: [feat-0030-schema-index-maintenance](../feature/feat-0030-schema-index-maintenance.md)
- Spec: [spec-0030-schema-index-maintenance](../spec/spec-0030-schema-index-maintenance.md)
- Execution Profile: `foundation-contract`
- Surface Lane: schema and compatible index migration
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated only the approved removal of three redundant names, addition of three query-prefix indexes, compatible convergence, and affected current-truth artifacts.

## Checks And Evidence

- Fresh PRAGMA evidence omits `idx_events_session_sequence`, `idx_local_resources_path`, and `idx_checkpoint_resource_refs` and retains the owning UNIQUE autoindexes.
- Compatible migration preflights all present redundant indexes before any DROP; a synthetic table without required UNIQUE coverage raises while all three explicit names remain.
- Fresh and compatible PRAGMA index shapes match the three approved additions, including descending `version` and `mtime_ns` keys.
- The effective named-index count remains 20; no table, column, physical relation, application relation, or UNIQUE constraint changed.
- Data Model owner docs, deterministic presentation manifest, decision source, and generated 329-object ledger are current at `keep 266`, `change 5`, `remove 1`, `defer 57`.

## Evidence Gaps

- Private runtime query performance was not measured; the Feature contracts query-prefix support rather than a production latency claim. Acceptance impact: not applicable.

## Findings

- None.

## Regression Notes

- Generated schema, audit, data-model, complete tests, diff whitespace, and privacy checks passed.

## Route

- Next action: `pass`.
