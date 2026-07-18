# RUN-20260718-21: Activity And Project Attribution Contract

## Metadata

- ID: `run-20260718-21`
- Status: `complete`
- Feature: [feat-0021-activity-and-project-attribution-contract](../feature/feat-0021-activity-and-project-attribution-contract.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [spec-0021-activity-and-project-attribution-contract](../spec/spec-0021-activity-and-project-attribution-contract.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Deliver and verify immutable first-observation Project attribution and bounded 30-minute activity metrics for later dashboard read models.

## Selected Loop

- Feature type: `foundation`
- Surface: `data`
- Surface lanes: attribution snapshot → activity calculation → durable contract
- Required evaluators: `contract`, `functional`
- Current phase: complete; sequential handoff to FEAT-0022

## Contract Surfaces

- Usage attribution columns, workspace-current metadata, first-observation conflict behavior, `ActivitySegment`, range boundaries, overlap merge, and metric labels.

## Invocation Context

- Golden sources: approved PRD, FEAT-0021, passed FEAT-0020, human-confirmed reconciliation and time rules.
- Relevant policies: Product Model, Project Architecture, foundation-contract profile.
- Optional skills or tools expected: none.

## Current Artifacts

- Spec: [spec-0021-activity-and-project-attribution-contract](../spec/spec-0021-activity-and-project-attribution-contract.md)
- Contract evaluation: [eval-0021-contract-activity-and-project-attribution-contract](../evaluation/eval-0021-contract-activity-and-project-attribution-contract.md)
- Functional evaluation: [eval-0021-functional-activity-and-project-attribution-contract](../evaluation/eval-0021-functional-activity-and-project-attribution-contract.md)
- Fix log: not created

## Evaluation Coverage

- Contract:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: schema, migration, path and Git transitions, policy and configuration parity
  - Unverified claims: none
  - Acceptance impact: not applicable
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: exact threshold, overlap, clipping, incomplete, invalid timestamp, SQLite, and timezone states
  - Unverified claims: none
  - Acceptance impact: not applicable

## Current Route

- Next role: Orchestrator for FEAT-0022
- Current blocker classification: none
- In-run route: complete after one fix and re-evaluation loop
- Post-run recommendation for human review: continue to FEAT-0022 under the owner's sequential execution instruction

## Attempts

- Attempt 1:
  - status: complete
  - outcome: Functional evaluation found one implementation bug in Git-root canonicalization
  - notes: no spec or planning gap
- Attempt 2:
  - status: complete
  - outcome: Contract and Functional evaluators passed after FIX-0021
  - notes: 60 tests, compilation, diff, and privacy checks passed

## Post-Contract Regression Check

- Needed: yes
- Result: passed
- Notes: current Session, Project inventory, workspace, usage, source synchronization, retrieval, runner, and UI-contract suites remain green.

## Human Review Outcome

- Decision: sequential execution authorized
- Returned layer if any: none
- Follow-up run: FEAT-0022 after this Feature passes

## Continuity Notes

- `2026-07-18`: Orchestrator confirmed the foundation profile, attribution-first lane order, and Contract plus Functional evaluators.
- `2026-07-18`: Attempt 1 routed a canonical-path implementation bug to FIX-0021; Attempt 2 passed complete evaluation.
