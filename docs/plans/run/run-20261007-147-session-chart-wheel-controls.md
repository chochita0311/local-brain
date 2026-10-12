# RUN-147: Session Chart Wheel Controls

## Metadata

- ID: `run-20261007-147`
- Status: `passed`
- Attempt: `1`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R7](../spec/spec-0114-r7-session-chart-wheel-controls.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-07`

## Direction And Ownership

Owner approves Shift-wheel verification/fix and independent time-axis modifier
zoom. Primary owns requirements, implementation, integration and sequential
contract/design/functional/UX review. Existing R6 producers and frozen work
surfaces remain outside this bounded frontend/docs revision.

## Progress

- Current source confirms Shift-wheel reads deltaY alone; a horizontal deltaX
  input is discarded. Whole-time fit and endpoint clamping can also prevent motion.
- Approved R7 Spec defines both input forms, dominant-component handling,
  pointer-time anchoring and stable vertical state through navigation/resize.
- The retained old script reproduces ignored horizontal Shift input while the
  vertical form moves. The changed handler accepts both, routes Cmd/Ctrl+Shift
  to X-only zoom and keeps ordinary whole zoom. Time-fitted resize preserves Y.
- Scoped native/synthetic browser checks pass both directions, diagonal and
  line/page normalization, pointer anchoring, bounds, selection and Y restoration.
  Wide/700/320px geometry and rendered wide/320px views remain native and contained.
- The ordinary running app loads suffix `-12`, passes native wheel and List/Chart
  return checks, and its inspection page is refreshed. No backend restart is needed.

## Review Boundary

Owner can review Shift horizontal movement after zooming into history and use
Cmd+Shift-wheel to change only time spacing. Physical-device/OS conversion is
separate evidence from controlled native browser input.

## Result And Closeout

- Result: `PASS`, partial evidence coverage, attempt `1`.
- Evaluation: [EVAL-0114-R7](../evaluation/eval-0114-r7-session-chart-wheel-controls.md).
- Thirty fixture cases and seven ordinary-app cases support the bounded gesture
  contract; numeric invariants pass. Physical-device/OS conversion and unrelated
  test suites are unclaimed. The original device cause remains a review limit.
- README, product/design and current planning owners are updated. Script syntax,
  whitespace/privacy and generated planning-catalog checks support their scopes.
- Task-owned local server/browser processes, synthetic fixture, profiles,
  screenshots and review output are removed. Ordinary app remains available.

## Next Owner Review

Use Shift-wheel after increasing time scale, then Cmd+Shift-wheel for horizontal
spacing. A fully fitted time range has no horizontal pan distance. The current
List, DB choices and frozen work surfaces retain their existing contracts.
