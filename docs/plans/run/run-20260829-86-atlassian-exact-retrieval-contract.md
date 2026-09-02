# RUN-20260829-86: Atlassian Exact Retrieval Contract

## Metadata

- ID: `run-20260829-86`
- Status: `passed`
- Feature: [FEAT-0076](../feature/feat-0076-atlassian-exact-retrieval-contract.md)
- Parent PRD: [PRD-0014](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Active Spec: [SPEC-0076](../spec/spec-0076-atlassian-exact-retrieval-contract.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Goal

- Implement and evaluate deterministic exact Atlassian retrieval before any
  Explorer UI consumes it.

## Selected Loop

- Feature type: `foundation`
- Surface: backend query/read model and durable contract
- Surface lanes: query contract, index compatibility, documentation
- Required evaluators: contract, functional
- Current phase: complete

## Surface Lanes

- Query contract:
  - path roots: `src/localbrain/atlassian_browse.py`, focused tests
  - dependencies: passed FEAT-0075
  - validation evidence: identity/phrase/rank/filter matrix
  - evaluator ownership: contract, functional
- Index compatibility:
  - path roots: Atlassian projection and global Search consumer/tests
  - dependencies: query contract
  - validation evidence: existing projection/rebuild/global regressions
  - evaluator ownership: contract, functional
- Documentation:
  - path roots: Product Model and Atlassian Source Memory
  - dependencies: fixed behavior
  - validation evidence: implementation/owner parity
  - evaluator ownership: contract

## Contract Surfaces

- Query normalization and validation.
- Complete identity and contiguous one-value phrase matching.
- Eligible field ownership and bounded matched-value projection.
- Service/structure/advanced-filter intersection and stable ordering.
- Existing FTS/global Search compatibility and zero hidden I/O.

## Invocation Context

- Golden sources: existing role-separated projection and synthetic Atlassian
  Browse/Search tests.
- Relevant policies: Product Model, Atlassian Source Memory, privacy, and
  execution governance.
- Optional skills or tools expected: none; rendered browser evidence is not
  required because this run changes no visible surface.

## Current Artifacts

- Spec: [SPEC-0076](../spec/spec-0076-atlassian-exact-retrieval-contract.md)
- Contract evaluation: [EVAL-0076 Contract](../evaluation/eval-0076-contract-atlassian-exact-retrieval-contract.md)
- Design evaluation: not required
- Functional evaluation: [EVAL-0076 Functional](../evaluation/eval-0076-functional-atlassian-exact-retrieval-contract.md)
- UX heuristic evaluation: not required
- Fix log: pending only if an evaluator fails
- Heuristic backlog: not required

## Evaluation Coverage

- Contract:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: relational owners, query consumer, FTS
    compatibility consumer, policy, and synthetic contract matrix
  - Unverified claims: none
  - Acceptance impact: `not applicable`
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: in-memory SQLite; 38 Atlassian tests
  - Unverified claims: none inside the backend-only boundary
  - Acceptance impact: `not applicable`

## Current Route

- Next role: Orchestrator for FEAT-0077
- Current blocker classification: none
- In-run route: complete
- Post-run recommendation for human review: accept RUN-86 and advance under
  sequential approval

## Attempts

- Attempt 1:
  - status: passed
  - outcome: contract and functional evaluation passed with complete evidence
  - notes: no fix loop required

## Post-Contract Regression Check

- Needed: yes
- Result: passed
- Notes: FTS producers and global score merging stayed unchanged; exact-mode
  consumers, filters, owner docs, and fixtures use the new contract without
  cross-field or hidden-I/O assumptions.

## Human Review Outcome

- Decision: sequential execution approved; RUN-86 must pass before FEAT-0077.
- Returned layer if any: none
- Follow-up run: FEAT-0077 after this foundation passes

## Continuity Notes

- `2026-08-29`: RUN-86 initialized with the foundation-contract profile and
  contract/functional evaluator set.
- `2026-08-29`: exact read model and owner docs passed both evaluators; RUN-86
  closed without schema migration, index rebuild, or fix attempt.
