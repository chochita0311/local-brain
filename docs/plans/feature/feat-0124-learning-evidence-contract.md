# FEAT-0124: Learning Evidence Contract

## Metadata
- ID: `feat-0124`
- Status: `passed`
- Type: `foundation`
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`
- Parent PRD: [PRD-0022](../prd/prd-0022-work-grounded-learning-dashboard.md)
- Created: `2026-10-16`
- Updated: `2026-10-17`

## Goal And Acceptance Contract

Define immutable lessons, work/official evidence roles, reviewed import ownership,
answer/self-assessment meaning, daily selection and source/version uncertainty.
Downstream product work must not guess what counts as learning or overwrite the
evidence used for a prior answer. Import identity, transaction boundaries, source
link admission, no-model behavior, local storage and future admission are explicit.

## Scope Boundary

In: the [learning policy](../../policies/project/work-grounded-learning.md).
Out: schema/code changes, screens, generation, source fetching and effectiveness claims.

## Contract Surfaces

Packet version 1, snapshot fingerprints, lesson revisions, attempt state machine,
timezone/date scheduling, one-new/two-review selection and visibility ownership.
Existing privacy/storage policies remain authoritative.

## Pass Or Fail Checks

Document review must resolve producer/consumer roles, field ownership, immutable
versus mutable data, branch outcomes and later admission without runtime claims.

## Harness Trace

- Spec: [SPEC-0124](../spec/spec-0124-learning-evidence-contract.md)
- Run: [RUN-162](../run/run-20261016-162-learning-evidence-contract.md)
- Evaluation: [EVAL-0124](../evaluation/eval-0124-learning-evidence-contract.md)

## Continuity

2026-10-17: document review made the curator's declared reviewer role explicit.
Assistant review remains separate from owner review; unknown reviewer remains
unknown. This resolves provenance without admitting automated generation.
