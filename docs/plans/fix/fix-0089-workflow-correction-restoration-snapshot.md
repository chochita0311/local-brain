# FIX-0089: Workflow Correction Restoration Snapshot

## Metadata

- ID: `fix-0089-workflow-correction-restoration-snapshot`
- Status: `complete`
- Run: [RUN-20260914-99](../run/run-20260914-99-workflow-boundary-corrections.md)
- Attempt: `2`
- Feature: [FEAT-0089](../feature/feat-0089-workflow-boundary-corrections.md)
- Spec: [SPEC-0089](../spec/spec-0089-workflow-boundary-corrections.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `Focus correction submit and orientation restoration`
- Created: `2026-09-14`
- Updated: `2026-09-14`

## Input Reports

- [EVAL-0089 Design](../evaluation/eval-0089-design-workflow-boundary-corrections.md)
  and [EVAL-0089 Functional](../evaluation/eval-0089-functional-workflow-boundary-corrections.md)
  supplied the rendered orientation-restoration finding returned from Attempt
  1.
- Repeated synthetic Chrome evaluation found an intermittent correction-success
  mismatch: the requested map pan `140/59` sometimes returned as `76/53` even
  though the selected Episode, zoom, disclosures, Trace scroll, page scroll,
  authority, and assertion focus were restored.

## Fix Scope

- Preserve the interaction state that existed when the user submitted, before
  button focus, fieldset disablement, or response latency can change it.
- Preserve meaningful assertion focus without allowing its deferred browser
  scroll to overwrite the stored map coordinates.
- Keep the same one-shot bounded storage, local POST, reload, history, privacy,
  no-script, and failure contracts.

## Changes Applied

- Captured the restoration snapshot synchronously after form serialization and
  before disabling the owning fieldset or starting `fetch`.
- Combined only the validated response's result code and corrected boundary
  focus with that frozen snapshot.
- Applied assertion focus first and restored map, Trace, and page coordinates on
  the following animation frame, then exposed a bounded completion signal for
  browser verification.
- Extended browser diagnostics with pre/post viewport dimensions and a bounded
  timing trace so a future scroll regression reports the exact displacement.

## Contract Or Lane Impact

- Contract surfaces touched: enhanced correction success orientation only.
- Surface lanes touched: route-scoped Workflow Map controller, static contract
  test, and synthetic browser QA.
- Stale-assumption check needed: none; assertion semantics, request/response,
  server rendering, and persistence did not change.

## Validation

- Correction static tests passed `13/13` and controller tests passed `7/7`.
- The complete four-width correction scenario passed twice consecutively after
  the fix, including exact `140/59` map pan, `120%` scale, selected Episode,
  branch/evidence disclosure, Trace/page scroll, assertion focus, close,
  reopen, undo, stale conflict, cancel, renderer failure, and no-script submit.
- Full-suite, generated-owner, diff, and privacy evidence is retained by
  RUN-20260914-99 and the final FEAT-0089 evaluations.

## Remaining Issues

- None in scope.

## Return Decision

- `pass`

## Continuity Notes

- `2026-09-14`: a repeated rendered check caught response-time snapshot drift;
  Attempt 2 fixed the ownership point and passed repeated browser evaluation.
