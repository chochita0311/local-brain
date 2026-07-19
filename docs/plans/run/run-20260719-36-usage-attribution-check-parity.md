# RUN-20260719-36: Usage Attribution CHECK Parity

## Metadata

- ID: `run-20260719-36`
- Status: `passed`
- Feature: [feat-0031-usage-attribution-check-parity](../feature/feat-0031-usage-attribution-check-parity.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Active Spec: [spec-0031-usage-attribution-check-parity](../spec/spec-0031-usage-attribution-check-parity.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Execute and evaluate the owner-approved, zero-data-impact Usage attribution CHECK repair.

## Selected Loop

- Feature type: foundation.
- Surface: data.
- Surface lanes: one Usage compatibility migration lane.
- Required evaluators: contract, functional.
- Current phase: complete.

## Contract Surfaces

- `usage_facts` compatible DDL, stable Fact IDs/rows, backup/rollback, Usage indexes, generated Schema presentation, and current cleanup audit.

## Invocation Context

- Golden sources: FEAT-0029 `align-usage-attribution-check`, PRD-0004 immutable Usage contracts, and passed FEAT-0030.
- Relevant policies: Data Model, Architecture, Privacy, foundation-contract profile, execution governance.
- Optional skills or tools expected: synthetic SQLite legacy fixtures, SAVEPOINT/backup/PRAGMA/EXCEPT evidence, Usage regression tests, generated checks, privacy scanner.

## Current Artifacts

- Spec: [spec-0031-usage-attribution-check-parity](../spec/spec-0031-usage-attribution-check-parity.md)
- Contract evaluation: [eval-0031-contract-usage-attribution-check-parity](../evaluation/eval-0031-contract-usage-attribution-check-parity.md) (`PASS`)
- Design evaluation: not required
- Functional evaluation: [eval-0031-functional-usage-attribution-check-parity](../evaluation/eval-0031-functional-usage-attribution-check-parity.md) (`PASS`)
- UX heuristic evaluation: not required
- Fix log: not created
- Heuristic backlog: not required

## Current Route

- Next role: Human Reviewer; implementation and required evaluation are complete.
- Current blocker classification: none.
- In-run route: complete.
- Post-run recommendation for human review: accept; complete preservation and recovery evidence passed.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: one-constraint-only delta with fail-closed invalid-state handling and exact stored-value preservation.
  - notes: synthetic file-backed upgrades, invalid values, unexpected shape, idempotency, and recovery all passed.

## Post-Contract Regression Check

- Needed: yes.
- Result: pass.
- Notes: Usage contracts/dashboard/activity, schema presentation/audit, 117 full tests, privacy, and value-free runtime preflight passed.

## Human Review Outcome

- Decision: owner approved boundary 3 and exact preservation on `2026-07-19`.
- Returned layer if any: not applicable.
- Follow-up run: none in the current approval set.

## Continuity Notes

- `2026-07-19`: Orchestrator selected `foundation-contract`, one Usage migration lane, and Contract plus Functional evaluators; Spec Agent approved SPEC-0031 and handed off to Builder.
- `2026-07-19`: Builder added a non-overwriting validated backup, exact-shape/value preflight, SAVEPOINT rebuild, bidirectional full-row and ID comparison, FK/index restoration, and idempotent skip path.
- `2026-07-19`: Contract and Functional evaluators passed attempt 1; the actual local database was already compliant, so runtime verification correctly performed no Usage table rebuild and recorded no private values.
