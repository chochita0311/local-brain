# RUN-20260928-123: Skill Observation And Retention

## Metadata

- ID: `run-20260928-123`
- Status: `passed`
- Feature: [FEAT-0105](../feature/feat-0105-skill-observation-retention.md)
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Active Spec: [SPEC-0105](../spec/spec-0105-skill-observation-retention.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-28`
- Updated: `2026-09-28`

## Goal And Boundary

Close the previously implemented skill-observation foundation against its approved contract. This review uses synthetic source files and databases; it does not run the personal-improvement analyzer or read private Session content.

## Execution Record

- Inspected the Claude/Codex explicit-signal parsers, native event key, bounded ledger, scan transaction, correction path, coverage query, schema, migration, and owning data-model documents.
- Added synthetic tests for signal admission and rejection, idempotent replay, resumed and new Sessions, moved and removed source files, name grouping, maintenance and targeted native-event correction, direct work subsessions, coverage, and compatible startup migration.
- Attempt 1 found that zero current-version files among tracked files were reported as `not_scanned`. Corrected the coverage rule so this is `partial`; added a zero-current regression case and updated the owning product/data contract.
- Attempt 2 passed [contract evaluation](../evaluation/eval-0105-contract-skill-observation-retention.md) and [functional evaluation](../evaluation/eval-0105-functional-skill-observation-retention.md). Eight focused skill tests, 16 parser tests, 17 Session-sync tests, 29 schema-migration tests, and the data-model-document checker passed.

## Post-Contract Regression Check

- Existing Session-only extraction backfill remains a Session repair and does not recalculate Usage Record prices. The previously stale sync expectation was updated to this approved contract.
- Fresh and compatible schema paths expose the ledger and indexes while preserving existing Session rows. The ledger has no cascading Session foreign key, and a deleted source file leaves its historical observations available.
- Usage & Cost reads its own usage query; no skill-ranking query is called on its initial route.

## Evidence Limit

The checks used synthetic records; this Run does not claim that a private local corpus was rescanned or that an analysis model produced a report. Those are separate activities.
