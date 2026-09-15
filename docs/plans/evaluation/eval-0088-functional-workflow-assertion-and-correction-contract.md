# EVAL-0088 Functional: Workflow Assertion And Correction Contract

## Metadata

- ID: `eval-0088-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run: [RUN-20260914-98](../run/run-20260914-98-workflow-assertion-and-correction-contract.md)
- Attempt: `1`
- Feature: [FEAT-0088](../feature/feat-0088-workflow-assertion-and-correction-contract.md)
- Spec: [SPEC-0088](../spec/spec-0088-workflow-assertion-and-correction-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `validated action → append-only assertion → effective projection`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Checks And Evidence

- Seventeen assertion tests cover stable directional boundary keys, exact DDL
  values and key shape, `same-flow`, `split-here`, `merge-into`, close-reason
  correction, `reopen`, undo, undo-of-undo redo, and a bounded honest history.
- Exact active-state and freshly recomputed projection revisions reject stale
  writes. Duplicate, missing endpoint, self-edge, reversed time, merge-before-
  source, cycle, contradictory incoming boundary, non-tip close, invalid reopen,
  overlong note, chain race, and injected insertion failure all write nothing.
- Source Session deletion retains history while nulling only lookup aids. A
  later Session with the same source key and native identity restores the same
  Episode key and reapplies the user-confirmed boundary deterministically.
- Repeated overlay reads are byte-equivalent, versioned, and execute zero DML.
  A changed user relation carries `user-confirmed` authority and a user-
  assertion reason while the complete deterministic base candidate remains
  separately inspectable.
- Idempotent schema application preserves all assertion rows. Generated Schema
  Presentation, ten value dictionaries, Data Model Mermaid, and the 649-object
  audit reproduce the new owner without a data repair or external access.
- Existing Focus and Session Workflow Map regression checks passed alongside
  the assertion tests (`40/40`), and the complete repository suite passed
  `538/538`. Repository privacy and whitespace checks also passed.

## Findings

- None.

## Route

- Next action: `pass`.
