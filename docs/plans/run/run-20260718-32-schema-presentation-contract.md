# RUN-20260718-32: Schema Presentation Contract

## Metadata

- ID: `run-20260718-32`
- Status: `passed`
- Feature: [feat-0027-schema-presentation-contract](../feature/feat-0027-schema-presentation-contract.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Active Spec: [spec-0027-schema-presentation-contract](../spec/spec-0027-schema-presentation-contract.md)
- Attempt: `1`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Generate, package, and validate the complete derived v1 Schema presentation contract without adding a product surface.

## Selected Loop

- Feature type: foundation.
- Surface: data.
- Surface lanes: value shape → generation → packaging/consumer readiness.
- Required evaluators: contract and functional.
- Current phase: complete.

## Surface Lanes

- Value shape and ownership:
  - path roots: Schema Presentation and Data Model policies
  - dependencies: passed FEAT-0026
  - validation evidence: exact v1 and provenance rules
  - evaluator ownership: contract
- Generation:
  - path roots: schema, migrations, generator, generated JSON
  - dependencies: value shape
  - validation evidence: isolated effective schema, deterministic/stale/malformed parity
  - evaluator ownership: contract, functional
- Packaging and consumer readiness:
  - path roots: loader, wheel, tests, owner docs
  - dependencies: generation
  - validation evidence: isolated installed load without repository/runtime dependencies
  - evaluator ownership: contract, functional

## Contract Surfaces

- v1 value shape, structural migration mode, Markdown semantic transformation, generated JSON, local loader, package data, stale/error/privacy boundaries.

## Invocation Context

- Golden sources: passed FEAT-0026 docs, `schema.sql`, `db.py`, local Mermaid bundle.
- Relevant policies: Data Model, Architecture, Developer Guide, Privacy, foundation-contract profile.
- Optional skills or tools expected: in-memory SQLite, Python tests, local Mermaid parser, wheel inspection.

## Current Artifacts

- Spec: [spec-0027-schema-presentation-contract](../spec/spec-0027-schema-presentation-contract.md)
- Contract evaluation: [eval-0027-contract-schema-presentation-contract](../evaluation/eval-0027-contract-schema-presentation-contract.md)
- Design evaluation: not required
- Functional evaluation: [eval-0027-functional-schema-presentation-contract](../evaluation/eval-0027-functional-schema-presentation-contract.md)
- UX heuristic evaluation: not required
- Fix log: not created
- Heuristic backlog: not required

## Evaluation Coverage

- Contract:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: schema, migrations, owner docs, v1 manifest, loader, wheel
  - Unverified claims: none
  - Acceptance impact: not applicable
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: in-memory SQLite, local Mermaid, failure fixtures, full tests, isolated installed package, privacy
  - Unverified claims: none
  - Acceptance impact: not applicable

## Current Route

- Next role: FEAT-0028 planner under the approved sequence.
- Current blocker classification: none.
- In-run route: complete.
- Post-run recommendation for human review: proceed to FEAT-0028; both evaluators passed.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: complete deterministic v1 presentation and installed consumer contract
  - notes: loader shape validation was tightened before final evaluation; no fix Run was required

## Post-Contract Regression Check

- Needed: yes.
- Result: PASS.
- Notes: 95 tests, schema/docs parity, nine Mermaid parses, package contents, isolated loading, privacy, and whitespace passed.

## Human Review Outcome

- Decision: automated feature boundary passed under the approved sequential workflow.
- Returned layer if any: none.
- Follow-up run: RUN-20260718-33 for FEAT-0028.

## Continuity Notes

- `2026-07-18`: run initialized after FEAT-0026 passed.
- `2026-07-18`: run passed with complete contract and functional evidence; no fix route was required.
