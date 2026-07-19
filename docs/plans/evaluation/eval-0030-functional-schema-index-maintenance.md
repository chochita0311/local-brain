# EVAL-0030: Schema Index Maintenance — Functional

## Metadata

- ID: `eval-0030-functional`
- Status: `complete`
- Evaluator Type: `functional`
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

- Evaluated migration behavior, row preservation, idempotency, failure behavior, query plans, and named regressions.

## Checks And Evidence

- A synthetic upgraded database retained exact pre/post rows across Activity Events, Local Resources, checkpoint references, checkpoints, and Context Documents.
- Running the compatible migration twice produced the same rows and post-migration index set.
- Missing UNIQUE coverage failed before any redundant index was removed.
- EXPLAIN selected `idx_checkpoints_workstream_version`, `idx_documents_source`, and `idx_documents_workspace` for their named current queries.
- Full suite passed 112 tests; repository privacy passed 370 candidate files.

## Evidence Gaps

- None blocking. No private row read was required for this row-free migration.

## Findings

- None.

## Regression Notes

- Session event ordering, Resource uniqueness, checkpoint detail/allocation, Context reconciliation/summaries, Schema Explorer presentation input, and audit checks passed.

## Route

- Next action: `pass`.
