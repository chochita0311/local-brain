# RUN-20260719-37: Activity Event Metadata Removal

## Metadata

- ID: `run-20260719-37`
- Status: `passed`
- Feature: [feat-0032-activity-event-metadata-removal](../feature/feat-0032-activity-event-metadata-removal.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Active Spec: [spec-0032-activity-event-metadata-removal](../spec/spec-0032-activity-event-metadata-removal.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Execute the owner-approved, fail-closed removal of the unused Activity Event metadata extension slot.

## Selected Loop

- Feature type: foundation.
- Surface: data.
- Surface lane: Activity Event schema and producer contract.
- Required evaluators: contract, functional.
- Current phase: complete.

## Contract Surfaces

- Fresh/compatible Activity Event DDL, parser/scanner payload, retained event values, consumer regressions, generated schema and audit artifacts.

## Invocation Context

- Golden sources: FEAT-0029 candidate, current parsers/scanner/consumers, Data Model owner, and human approval.
- Relevant policies: Data Model, Architecture, Privacy, Developer Guide, foundation-contract profile.
- Expected tools: synthetic SQLite legacy fixtures, PRAGMA evidence, generated checks, runtime count-only preflight, full tests, privacy scanner.

## Current Artifacts

- Spec: [spec-0032-activity-event-metadata-removal](../spec/spec-0032-activity-event-metadata-removal.md)
- Contract evaluation: [eval-0032-contract-activity-event-metadata-removal](../evaluation/eval-0032-contract-activity-event-metadata-removal.md) (`PASS`)
- Design evaluation: not required
- Functional evaluation: [eval-0032-functional-activity-event-metadata-removal](../evaluation/eval-0032-functional-activity-event-metadata-removal.md) (`PASS`)
- UX heuristic evaluation: not required
- Fix log: not created

## Current Route

- Next role: Human Reviewer; implementation and required evaluation are complete.
- Current blocker classification: none.
- In-run route: complete.
- Post-run recommendation for human review: accept; non-null metadata is never silently discarded.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: one-column removal with fail-closed preflight and exact retained-event preservation.
  - notes: synthetic and actual runtime verification passed without recording private values in tracked evidence.

## Post-Contract Regression Check

- Needed: yes.
- Result: pass.
- Notes: Session/activity/retrieval, schema presentation/audit, 120 full tests, privacy, and actual runtime pre/post comparison passed.

## Human Review Outcome

- Decision: owner approved boundary 2 on `2026-07-19`.
- Returned layer if any: not applicable.
- Follow-up run: FEAT-0033 after this Feature passes.

## Continuity Notes

- `2026-07-19`: Orchestrator selected `foundation-contract` with Contract and Functional evaluation; Spec Agent approved the all-null-only removal contract.
- `2026-07-19`: Builder removed the fresh column, parser member, scanner binding, and all-null legacy column; actual retained event count and digest were identical before and after.
- `2026-07-19`: Contract and Functional evaluators passed attempt 1; FEAT-0033 may now enter its separate visible-product loop.
