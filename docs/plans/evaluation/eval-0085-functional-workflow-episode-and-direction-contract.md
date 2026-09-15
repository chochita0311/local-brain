# EVAL-0085 Functional: Workflow Episode And Direction Contract

## Metadata

- ID: `eval-0085-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run: [RUN-20260914-95](../run/run-20260914-95-workflow-episode-and-direction-contract.md)
- Attempt: `1`
- Feature: [FEAT-0085](../feature/feat-0085-workflow-episode-and-direction-contract.md)
- Spec: [SPEC-0085](../spec/spec-0085-workflow-episode-and-direction-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `Synthetic workflow descriptor and normalization fixtures`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Checks And Evidence

- Synthetic fixtures prove stable source-scoped identity across local row,
  title, and workspace changes, distinct identities across sources, and no
  delimiter-boundary collision.
- Timestamp fixtures prove UTC normalization, earliest/latest selection across
  Session and event observations, absent invalid observations, and the rule
  that a Session end never infers lifecycle closure.
- Descriptor fixtures prove field bounds, stable evidence-count ordering,
  primary-work eligibility, state and closure parity, JSON compatibility, and
  omission of native identity and local path from serialized output.
- Relation fixtures exercise all three approved direction kinds, reject weak
  signals alone, reject self-edges and non-forward time, enforce user and
  organization authority reasons, normalize bounded reason values, deduplicate
  reasons, and omit a cycle independently of input order.
- The focused suite passed `16/16` and the full repository suite passed
  `498/498`. Existing Session inventory, detail, pin, synchronization,
  reference-evidence, Workstream, Atlassian, Local Context, Search, Schema, and
  Task Runner tests remained green. The only test output was the pre-existing
  Starlette `TemplateResponse` deprecation warning.

## Findings

- None.

## Route

- Next action: `pass`.
