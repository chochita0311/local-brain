# EVAL-0014: Local Context Explorer Functional

## Metadata

- ID: `eval-0014-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260716-14`
- Attempt: `1`
- Feature: [feat-0014-local-context-explorer](../feature/feat-0014-local-context-explorer.md)
- Spec: [spec-0014-local-context-explorer](../spec/spec-0014-local-context-explorer.md)
- Execution Profile: `frontend-product`
- Surface Lane: Context explorer
- Created: `2026-07-16`

## Evidence Invalidation

- This Attempt 1 result is historical and is not current execution truth.
- Live Chrome evidence in [Attempt 2](./eval-0014-functional-context-explorer-attempt-2.md) proved that document selection rebuilds the tree and loses disclosure, scroll, focus, and visible selected context; the current evaluator result is `FAIL`.

## Scope And Checks

- Verified `/context` returns `200`, route query selection remains unchanged, add forms and remove endpoints retain selectors, and deletion confirmation retains index-only scope.
- Context root/source/tree tests and UI contract tests passed; full-document destinations remain anchors.

## Findings And Regression

- No findings. Scanning, extraction, registration, and deletion behavior were unchanged.

## Route

- Historical next action: `pass`; superseded by Attempt 2 route `fix`.
