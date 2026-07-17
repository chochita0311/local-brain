# FEAT-0012: Run Console

## Metadata

- ID: `feat-0012`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make the maintenance Run route a trustworthy execution surface where lifecycle status, cancellation, technical output, error context, artifacts, and return navigation stay visible and semantically correct.

## Acceptance Contract

- Prepared, queued, running, cancelling, cancelled, completed, failed, and interrupted states use the constitution's exact semantic mapping and text labels.
- Run identity, configuration metadata, status, cancellation, update time, evidence counts, errors, and artifacts remain outside or above the independently scrollable output region.
- Polling and cancellation retain active bindings and do not expose raw intermediate implementation states.
- Long output, paths, errors, IDs, and artifact metadata remain readable and contained from desktop through narrow layouts.
- Reusable Run status presentation is stable for later consumption by the Workstream workspace.

## Scope Boundary

- In:
  - `/runs/{run_id}`
  - Run heading, lifecycle status, metadata, cancellation, console, errors, artifacts, polling feedback, return link, and responsive presentation
  - reusable visual treatment for Run status summaries consumed later by `feat-0010`
- Out:
  - Run preparation, execution, persistence, cancellation semantics, artifacts, retrieval, or MCP behavior changes
  - Workstream maintenance launcher and history layout owned by `feat-0010`
  - new terminal controls, log search, retry, or execution stages

## Contract Surfaces

- Run detail GET route and `GET /api/runs/{run_id}` polling payload
- `POST /api/runs/{run_id}/cancel` behavior
- current Run state vocabulary and terminal-state behavior
- output, error, artifact, evidence-count, and MCP-budget fields

## Required Evaluators

- `design`: technical hierarchy, status semantics, console readability, error and artifact containment, and responsive presentation.
- `functional`: polling, active-state continuation, cancellation, terminal states, error feedback, links, and retained bindings.
- `ux-heuristic`: execution confidence, cancellation clarity, long-output navigation, and distinction between status and output.

## User-Visible Outcome

- The user can monitor and cancel an active Run, read long output, understand terminal results or failure context, and inspect artifacts without losing status or control ownership.

## Entry And Exit

- Entry point: Workstream Run history or direct `/runs/{run_id}` route.
- Exit or transition behavior: polling continues only for active states, cancellation moves through `cancelling`, terminal states stop polling, and the return link opens the owning Workstream.

## State Expectations

- Default: prepared or terminal Run metadata and output remain readable.
- Loading: queued and active polling states remain labeled without clearing prior output.
- Empty: absent output or artifacts is explicit and does not hide Run status.
- Error: failed polling, execution error, and failed Run state remain distinguishable and bounded.
- Success: completed status, final output, evidence counts, and artifacts remain visible together.

## Dependencies

- `feat-0002` and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/run.html`
- Run status, details, console, error, artifact, action, and responsive selectors in `src/localbrain/static/styles.css`
- Run polling and cancellation interaction in `src/localbrain/static/app.js`
- Workstream Run summary selectors only when needed to expose the reusable status contract for `feat-0010`

## Pass Or Fail Checks

- Pass if every current Run state has the correct label and semantic family.
- Pass if polling continues only for active states and stops for terminal states.
- Pass if cancellation remains usable and moves through the expected visible state.
- Pass if prior output is not cleared during ordinary polling and long output does not widen the page.
- Pass if error context and artifacts remain available outside the output scroll region.
- Fail if controls lose bindings after an update or cancellation attempt.
- Fail if `prepared` or `running` is mapped to the wrong feedback family.

## Regression Surfaces

- Run detail route and 404 behavior
- Run polling payload consumption
- cancellation request and state transition
- output, error, evidence, artifact, and MCP-budget display
- Workstream link and shared Run status summary

## Harness Trace

- Active spec doc: [spec-0012-run-console](../spec/spec-0012-run-console.md)
- Active run: [run-20260716-12-run-console](../run/run-20260716-12-run-console.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0012-ux-run-console](../evaluation/eval-0012-ux-run-console.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft isolated Run lifecycle presentation before the Workstream workspace consumes its summary states.
- `2026-07-16`: executed and passed in `run-20260716-12`.
