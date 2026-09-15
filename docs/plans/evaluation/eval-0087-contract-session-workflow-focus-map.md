# EVAL-0087 Contract: Session Workflow Focus Map

## Metadata

- ID: `eval-0087-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-20260914-97](../run/run-20260914-97-session-workflow-focus-map.md)
- Attempt: `1`
- Feature: [FEAT-0087](../feature/feat-0087-session-workflow-focus-map.md)
- Spec: [SPEC-0087](../spec/spec-0087-session-workflow-focus-map.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Session eligibility → Focus route → FEAT-0086 presentation`
- Evidence Coverage: `complete`
- Created: `2026-09-14`

## Checks And Evidence

- Eligible primary work Sessions receive one additive `작업 흐름` destination.
  The existing Session conversation, pin, metadata, Subsession, Related
  Materials, and source-cue contracts remain in their prior hierarchy; a
  workflow-eligibility failure is isolated from Session reading.
- `GET /sessions/{session_id}/workflow` invokes the FEAT-0086 producer exactly
  once and passes its result through a pure presentation adapter. SQL tracing
  and `total_changes` assertions prove zero DML; the route performs no source
  file, document body, connector, refresh, model, or fallback Session query.
- Missing, ineligible, unexpected-error, connected, partial, and unconnected
  states remain typed and bounded. Every state retains a safe local Session or
  Sessions destination and exposes neither native source identity nor private
  path data.
- The server-rendered contract retains every projected Episode, relation,
  authority, complete reason list, evidence family, availability state, and
  safe destination. Evidence remains nested under Episodes and never becomes a
  peer workflow node.
- Static and browser checks prove canonical Episode history, source-detail
  return, edge inspection, bounded branch disclosure, deterministic layout,
  disabled-before-ready controls, no-script fallback, and fail-closed malformed
  projection handling.
- Product, Architecture, Privacy, Design Constitution, and design-plan owners
  describe the same separate, read-only, Qwen-free Focus boundary. Data-model
  parity reports 41 ordinary tables, one FTS object, 54 foreign keys, 44
  indexes, and nine owners; the generated Schema Presentation and 623-object
  cleanup ledger are current.
- Focused Python checks passed `39/39`, JavaScript layout checks passed `5/5`,
  and the complete repository suite passed `521/521`. Privacy passed over `870`
  candidate files and `git diff --check` passed.

## Findings

- None.

## Current Route

- Current route: `PASS`; FEAT-0088 may add the separate user-assertion contract
  without changing this read-only presentation boundary.
