# RUN-20260719-40: Maintenance Session Usage Bridge

## Metadata

- ID: `run-20260719-40`
- Status: `returned-to-planning`
- Feature: [feat-0035-maintenance-session-usage-bridge](../feature/feat-0035-maintenance-session-usage-bridge.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Active Spec: [spec-0035-maintenance-session-usage-bridge](../spec/spec-0035-maintenance-session-usage-bridge.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal And Selected Loop

- Execute the approved Session integrity repair and Task Runner stream-to-Usage bridge.
- Route: `Orchestrator → Spec Agent → Builder → Contract Evaluator → Functional Evaluator → Fix Agent if required`.

## Surface Lanes

- Schema and migration: CHECK/FK/UNIQUE, backup-backed compatible repair, exact preservation.
- Runner producer: linked Session creation, stream normalization, lifecycle and historical reconciliation.
- Consumers: scanner preservation, retrieval exclusion, Dashboard eligibility.
- Documentation/generated: owner docs, deterministic Schema presentation, PRD continuity.

## Current Artifacts

- Spec: [spec-0035-maintenance-session-usage-bridge](../spec/spec-0035-maintenance-session-usage-bridge.md)
- Contract evaluation: [eval-0035-contract-maintenance-session-usage-bridge](../evaluation/eval-0035-contract-maintenance-session-usage-bridge.md)
- Functional evaluation: [eval-0035-functional-maintenance-session-usage-bridge](../evaluation/eval-0035-functional-maintenance-session-usage-bridge.md)
- Design/UX evaluation: not required; no visible layout or interaction change is in scope.

## Current Route

- Next role: Human owner.
- Current blocker classification: none.
- In-run route: attempt 1 passed Contract and Functional evaluation.
- Post-run recommendation for human review: accept.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: the Session contract and Runner Usage bridge were implemented, migrated, and verified without existing-row drift.
  - notes: the actual database preserved 171 existing Sessions exactly and added two metadata-only historical Run links. Their stream artifacts were absent, so no historical Usage Record was invented.

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: schema presentation, ingestion, Runner, retrieval, Usage Dashboard, actual local database, 139-test complete suite, privacy, compile, Mermaid, audit, and idempotency checks passed.

## Human Review Outcome

- Decision: rejected because the stream-backed producer retained `--no-session-persistence` despite the intended native Claude Session model.
- Returned layer if any: Feature planning.
- Follow-up run: [RUN-20260719-41](run-20260719-41-native-maintenance-session-and-runner-ui-consolidation.md)

## Continuity Notes

- `2026-07-19`: run initialized after direct owner approval of the Session-to-Run and Usage bridge; the separate Maintenance Run Workstream FK candidate remains unapproved.
- `2026-07-19`: Contract and Functional evaluators passed attempt 1. The actual database backup, exact retained-row comparison, two Maintenance Session backfills, integrity checks, and repeated startup passed; missing historical stream files remained explicit zero-Usage evidence.
- `2026-07-19`: owner review invalidated the producer assumption after evaluation. The schema constraint evidence remains reusable; the synthetic Session/backfill and no-persistence decisions do not.
