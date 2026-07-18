# RUN-20260717-15: Session And Subsession Source Contract

## Metadata

- ID: `run-20260717-15`
- Status: `complete`
- Feature: [feat-0015-session-subsession-source-contract](../feature/feat-0015-session-subsession-source-contract.md)
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Active Spec: [spec-0015-session-subsession-source-contract](../spec/spec-0015-session-subsession-source-contract.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Goal

- Execute the source-neutral hierarchy, branch ownership, migration, and consumer-exclusion contract required by downstream PRD-0002 Features.

## Selected Loop

- Feature type: `foundation`
- Surface: `data`
- Surface lanes: contract → ingestion and identity → consumer exclusion
- Required evaluators: Contract, Functional
- Current phase: Human review gate passed

## Surface Lanes

- Contract lane: durable product, architecture, Task Runner, and schema ownership; Contract evaluator.
- Ingestion and identity lane: parsers, scanner, schema, migration, reconciliation, synthetic fixtures; Contract and Functional evaluators.
- Consumer exclusion lane: queries, Search, Workstream organization, retrieval, runner payloads and artifacts; Contract and Functional evaluators.

## Contract Surfaces

- Session schema and identity, source metadata producers, compatible migration, Search/statistics predicates, Workstream maintenance bundles, and Project/resource payloads.

## Invocation Context

- Golden sources: approved PRD and human decisions recorded in FEAT-0015.
- Relevant policies: Product Model, Project Architecture, Privacy, Claude Task Runner, execution governance.
- Optional skills or tools expected: none for this non-visual foundation run.

## Current Artifacts

- Spec: [spec-0015-session-subsession-source-contract](../spec/spec-0015-session-subsession-source-contract.md)
- Contract evaluation: [eval-0015-contract-session-subsession-source](../evaluation/eval-0015-contract-session-subsession-source.md)
- Functional evaluation: [eval-0015-functional-session-subsession-source](../evaluation/eval-0015-functional-session-subsession-source.md)

## Current Route

- Next role: Feature 0016 Spec/Builder
- Current blocker classification: none
- In-run route: complete
- Post-run recommendation for human review: proceed to FEAT-0016

## Attempts

- Attempt 1:
  - status: complete
  - outcome: pass
  - notes: source contract, migration, reconciliation, consumer exclusion, and both required evaluators passed

## Post-Contract Regression Check

- Needed: yes
- Result: passed
- Notes: runtime workspace-branch consumers are absent and every Session-derived statistic, Search, Workstream candidate, retrieval, and runner surface uses the primary-Session predicate

## Human Review Outcome

- Decision: sequential execution authorized
- Returned layer if any: none
- Follow-up run: `run-20260717-16` after this Feature passes

## Continuity Notes

- `2026-07-17`: run initialized with no open planning blocker.
- `2026-07-17`: all 27 unit tests, compile check, diff check, and privacy check passed; Contract and Functional evaluation routed to pass.
