# FEAT-0126: Code Learning Contract

## Metadata
- ID: `feat-0126`
- Status: `passed`
- Type: `foundation`
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract
- Parent PRD: [PRD-0023](../prd/prd-0023-code-and-command-learning.md)
- Created: `2026-10-17`
- Updated: `2026-10-17`
- Approval: owner said “확인한대로 진행해봐” after reviewing the PRD, storyboard
  and the proposed source-contract → reviewed reader → later generation sequence.

## Goal And Acceptance Contract
Resolve the versioned scene/question contract, daily depth/selection rules and
retrieval versus generation boundary before extending the reader. The owner also
asked what Qwen learns, how difficult questions are and how they are selected.

## Scope Boundary
In: [Code learning policy](../../policies/project/code-command-learning.md).
Out: executable producer/renderer, model execution, automatic discovery, source
monitoring, objective grading and effectiveness validation.

## Dependencies And Regression Surfaces
The existing [learning policy](../../policies/project/work-grounded-learning.md)
retains version-1 intake, immutable lesson revisions, attempts and visibility.
The new contract must preserve historical records without fabricating code.

## Pass Or Fail Checks
Document inspection must resolve source identity, literal bytes, command evidence
state, diff before/after, question-to-line references, authored versus generated
provenance, daily eligibility/order, adaptive-depth predicates, same-day feedback
exposure, old-packet compatibility and missing-evidence fallback.

## Harness Trace
- Spec: [SPEC-0126](../spec/spec-0126-code-learning-contract.md)
- Run: [RUN-164](../run/run-20261017-164-code-learning-contract.md)

