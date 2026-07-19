# EVAL-0028: In-App Schema Explorer — UX Heuristic

## Metadata

- ID: `eval-0028-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260718-33`
- Attempt: `1`
- Feature: [feat-0028-in-app-schema-explorer](../feature/feat-0028-in-app-schema-explorer.md)
- Spec: [spec-0028-in-app-schema-explorer](../spec/spec-0028-in-app-schema-explorer.md)
- Execution Profile: `fullstack-product`
- Surface Lane: orientation, selection, comprehension, focus, fallback, and narrow friction
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: global-to-area-to-table schema exploration.
- Active spec: SPEC-0028 attempt 1.
- Evaluated build or commit: final rendered and interactive screen.

## Checks

- Traced the primary task from `System > Schema` through global model, one of eight subject owners, its table index, and complete table detail.
- Compared visible and programmatic current state for shell, area, and table; verified direct entry, back/forward, and partial navigation restore the same orientation.
- Verified heading copy changes from model to area to table, while baseline counts, subject map, focused diagram, owned-object index, and selected detail retain a stable information order.
- Verified physical versus application relations use both text labels and line style, not color alone.
- Verified the global internal-scroll instruction makes the dense canvas discoverable without introducing a custom zoom or diagram control.
- Verified every essential destination is an ordinary anchor, focus is visible and moves to the destination heading, rapid selection cannot display stale content, and failure feedback is fixed and bounded.
- Verified no-script and Mermaid-unavailable states retain the task path through subject/table links and the complete selected catalog.
- Verified 320px keeps all subjects, metrics, diagram, table index, lifecycle, semantic fields, and long columns in reading order without hover dependence.

## Evidence

- Direct Chrome interaction confirmed selected labels, `aria-current`, focus destination, URL, diagram, and detail identity settle together.
- True 320 device metrics reported client/document width `320/320` and retained all nine global-plus-subject links.
- Full-page 700 and narrow detail captures confirmed readable sequential catalog flow.

## Evidence Gaps

- None within the approved interaction contract.

## Findings

- No blocking UX contradiction or non-blocking suggestion remains. The global-scroll hint was added during evaluation before acceptance rather than deferred.

## Regression Notes

- Shared search and shell navigation remain discoverable. The Schema module owns only its local region and emits no shell timer, storage, or route-class behavior.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 with coherent model → area → table orientation and complete failure/narrow continuity.
