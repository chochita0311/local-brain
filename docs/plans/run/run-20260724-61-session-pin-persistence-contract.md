# RUN-20260724-61: Session Pin Persistence Contract

## Metadata

- ID: `run-20260724-61`
- Status: `passed`
- Feature: [feat-0058-session-pin-persistence-contract](../feature/feat-0058-session-pin-persistence-contract.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Active Spec: [spec-0058-session-pin-persistence-contract](../spec/spec-0058-session-pin-persistence-contract.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal And Selected Loop

- Deliver durable pin state without mixing owner intent into source-derived Session columns or entering product UI scope.
- Route: `Orchestrator → Spec Agent → foundation Builder → Contract Evaluator → Functional Evaluator`.

## Delivered Contract

- Added the two-column `session_pins` table with Session primary-key cascade ownership.
- Added bounded pin, unpin, membership, and deterministic list operations.
- Fixed eligibility to persisted primary work Sessions; Maintenance Sessions and Subsessions fail closed.
- Preserved the first `pinned_at` across repeated pin; unpin deletes the row; re-pin creates a new interval.
- Kept all operations local to SQLite.
- Updated the Data Model, generated Schema Presentation, value-dictionary exclusion ledger, and complete schema cleanup audit.

## Current Artifacts

- Spec: [spec-0058-session-pin-persistence-contract](../spec/spec-0058-session-pin-persistence-contract.md)
- Contract evaluation: [eval-0058-contract-session-pin-persistence-contract](../evaluation/eval-0058-contract-session-pin-persistence-contract.md) — `PASS`
- Functional evaluation: [eval-0058-functional-session-pin-persistence-contract](../evaluation/eval-0058-functional-session-pin-persistence-contract.md) — `PASS`
- Fix log: not created

## Verification Evidence

- `61` focused schema, migration, ingestion, Session, registry, presentation, cleanup-audit, and pin-operation tests passed.
- Six pin-focused tests cover fresh and compatible creation, idempotency, re-pin, rejection, deterministic listing, update preservation, and deletion cascade.
- Data Model parity passed at 35 ordinary tables, one FTS5 object, 40 physical FKs, 33 explicit indexes, and nine subject owners.
- Schema Presentation freshness, 516-object cleanup audit, value dictionaries, and all nine Mermaid parses passed.
- No product route, template, source file, external service, or runtime user database was mutated.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: separate row-presence persistence and query contract delivered.
  - notes: generated Schema Presentation and its audit digest were deliberately refreshed after the owner document changed.

## Human Review Outcome

- Decision: automatic sequential approval authorized on `2026-07-24`.
- Returned layer if any: none.
- Follow-up run: FEAT-0054.

## Continuity Notes

- `2026-07-24`: the visible pin control and Pinned Sessions panel remain exclusively in FEAT-0059.
