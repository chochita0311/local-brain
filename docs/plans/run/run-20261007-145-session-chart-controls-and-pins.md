# RUN-145: Session Chart Controls And Pins

## Metadata

- ID: `run-20261007-145`
- Status: `passed`
- Attempt: `1`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R5](../spec/spec-0114-r5-session-chart-controls-and-pins.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-07`

## Direction And Ownership

The owner requests toolbar simplification, durable Project filtering, native pin
visibility and view/source separator alignment. Primary owns intent, browser
persistence, screen-alignment extend, frontend implementation and owner documents.
Existing all-pin data is already available to the template; no backend change is
needed. R4 tab visibility was not a browser-restart guarantee and is superseded.

## Progress

- Rendered baseline confirms the separate filter row, date and arrow controls,
  List/Chart separator and untranslated All label. Source review confirms only
  sessionStorage visibility and an existing complete eligible pin inventory.
- R5 Spec records the owner-approved boundary and frontend/docs lanes.
- Implemented toolbar filter placement and directional/date removal, separate
  durable Project preferences with old-tab migration/fallback, read-only native
  pin halo/icon with exact-member status, and shared view/source separator rules.
- [EVAL-0114-R5](../evaluation/eval-0114-r5-session-chart-controls-and-pins.md)
  records `PASS` with partial coverage: native filter and pin/selector actions,
  fresh-document visibility, controlled migration/denial, exact aggregate truth,
  List/source/detail continuity and 1440/700/320px composition. Browser-process
  restart, physical device, OS, stress and automated suites remain unclaimed.
- JS syntax, whitespace, privacy and generated-catalog checks support their
  checked scopes. Final Chart uses revision-ten assets on the ordinary application.
  Task-owned review pages/instrumentation are removed; no task files or extra
  server are retained.

## Review Boundary

Review covers filter placement, durable browser choices, visible pin state and
source/view controls. Original List rows/recall, observation truth, Workflow Focus
and stopped Auto Work retain their boundaries.
