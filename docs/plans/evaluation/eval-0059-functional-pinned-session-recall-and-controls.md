# EVAL-0059: Pinned Session Recall And Controls — Functional

## Metadata

- ID: `eval-0059-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260724-64`
- Attempt: `1`
- Feature: [feat-0059-pinned-session-recall-and-controls](../feature/feat-0059-pinned-session-recall-and-controls.md)
- Spec: [spec-0059-pinned-session-recall-and-controls](../spec/spec-0059-pinned-session-recall-and-controls.md)
- Execution Profile: `fullstack-product`
- Surface Lane: queries, routes, controls, and regressions
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Checks And Evidence

- Pin and unpin update only one FEAT-0058 row and are idempotent in their existing directions.
- Inventory and detail show current state after each redirect.
- Source, workspace, page, and detail destinations survive valid returns; Projects mode is allowlisted and the client refreshes hidden return state from the current URL.
- External return targets fail closed to `/sessions`.
- Every current pin remains visible in deterministic order, including more than 100 synthetic pins.
- Clicking pin or Subsession does not navigate through the Session row link.
- Primary detail exposes one control; persisted Subsession detail exposes none.
- Filtered inventory, empty panel, populated panel, error notice, inline storage error, wide scroller, and narrow ordinary flow are bounded.
- Focused tests and synthetic browser interaction passed.

## Evidence Gaps

- No deliberate disk-full operating-system fault was injected; the SQLite error route and adjacent truthful presentation are covered structurally.

## Findings

- None.

## Route

- Next action: `pass`.
