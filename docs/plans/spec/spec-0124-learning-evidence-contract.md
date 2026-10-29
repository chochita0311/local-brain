# SPEC-0124: Learning Evidence Contract

## Metadata
- ID: `spec-0124`
- Status: `approved`
- Run: [RUN-162](../run/run-20261016-162-learning-evidence-contract.md)
- Attempt: `1`
- Parent Feature: [FEAT-0124](../feature/feat-0124-learning-evidence-contract.md)
- Parent PRD: [PRD-0022](../prd/prd-0022-work-grounded-learning-dashboard.md)
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`
- Created: `2026-10-16`
- Updated: `2026-10-16`

## Implementation Goal

Write one owner policy for a reviewed local learning packet and its consumers.
The user's continuation authorizes this prerequisite before product implementation.

## In-Scope Behavior And Acceptance Mapping

1. Packet and source ownership: stable keys, immutable content revisions, explicit
   reviewed import, snapshot hash semantics and atomic idempotent imports.
2. Attempt state: answer/confidence before feedback, separate reading, one final
   self-assessment and no objective correctness or mastery claim.
3. Selection: configured local dates, one review per day, visible interval rules,
   finite selection from pre-day history, reversible visibility.
4. Trust: official/work roles, source age and deployed version uncertainty, no
   automatic fetch/model, private storage and separate future quality admission.

## Required Evaluators And Open Blockers

Contract review is a source-level document inspection. No runtime tests or product
benefit claims belong to this foundation pass. There are no unresolved decisions
that prevent the reviewed-content pilot; automated candidates remain unactivated.
