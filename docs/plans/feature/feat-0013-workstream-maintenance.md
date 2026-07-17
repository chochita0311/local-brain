# FEAT-0013: Workstream Maintenance

## Metadata

- ID: `feat-0013`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make Workstream maintenance entry, Run configuration, Run history, and maintenance-marker controls one clear operational region that leads reliably into the renewed Run console.

## Acceptance Contract

- Runner availability, task type, model, working directory, refresh choice, MCP budget, and submit action remain visible before execution.
- Run history uses the reusable lifecycle presentation from `feat-0012` and links to the correct Run detail.
- Maintenance marker generation and copy remain distinct from starting an in-app Run.
- Running, unavailable, empty-history, validation, submission, and copy-feedback states are bounded to their owning controls.
- Existing Run-start and marker APIs, payloads, redirect behavior, and maintenance-session separation remain unchanged.

## Scope Boundary

- In:
  - Workstream Task Runner panel, configuration form, policy summary, Run history, runner availability, maintenance marker, and copy feedback
  - maintenance-region hierarchy, state, action, form, empty, error, and responsive presentation
- Out:
  - Run detail and console owned by `feat-0012`
  - Workstream core structure owned by `feat-0010`
  - Resource and Suggestion review owned by `feat-0011`
  - runner execution, retrieval, persistence, task definitions, MCP budget, or marker semantics changes

## Contract Surfaces

- `POST /api/workstreams/{workstream_id}/runs` payload and redirect
- `POST /api/maintenance-runs` marker response
- Runner availability, task choices, model, working directory, refresh flag, and MCP-budget template context
- current Run history state and destination fields

## Required Evaluators

- `design`: operational hierarchy, lifecycle status, form density, console handoff, feedback, and responsive containment.
- `functional`: Run start, validation, redirect, Run history links, marker generation, clipboard copy, unavailable state, and regression.
- `ux-heuristic`: distinction between marker and in-app Run, configuration clarity, execution confidence, and error recovery.

## User-Visible Outcome

- The user can understand runner availability, configure and start an existing maintenance task, revisit prior Runs, or create a maintenance marker without confusing the available execution paths.

## Entry And Exit

- Entry point: maintenance regions within `/workstreams/{workstream_id}`.
- Exit or transition behavior: starting a Run follows the current redirect to Run detail; history links open Run detail; marker generation remains on the Workstream and exposes copy feedback.

## State Expectations

- Default: configuration and policy context are visible before execution.
- Loading: submit, marker generation, and clipboard actions use bounded working feedback.
- Empty: no Run history is explicit without hiding the launcher.
- Error: runner unavailable, validation, start, marker, and copy failures remain distinguishable.
- Success: started Run redirects correctly; generated marker and copied state are visibly confirmed.

## Dependencies

- `feat-0002`, `feat-0003`, `feat-0010`, and `feat-0012` must be `passed`.

## Likely Affected Surfaces

- Task Runner, Run history, and maintenance-marker regions in `src/localbrain/templates/workstream.html`
- task-runner, Run summary, form, marker, feedback, and responsive selectors in `src/localbrain/static/styles.css`
- API form, maintenance marker, copy, and Run-start interactions in `src/localbrain/static/app.js`

## Pass Or Fail Checks

- Pass if Run start retains the current payload, validation, and redirect behavior.
- Pass if every Run history row uses the correct lifecycle label and opens the correct Run.
- Pass if marker generation and in-app Run start cannot be mistaken for the same action.
- Pass if unavailable, empty, error, working, and success states remain bounded and labeled.
- Fail if a rerender or feedback update leaves Run, marker, or copy controls inactive.
- Fail if visual changes imply unsupported execution or external write behavior.

## Regression Surfaces

- Workstream Run preparation and start
- runner availability and task choices
- Run history links and lifecycle status
- maintenance marker generation and clipboard copy
- maintenance-session exclusion from ordinary work statistics

## Harness Trace

- Active spec doc: [spec-0013-workstream-maintenance](../spec/spec-0013-workstream-maintenance.md)
- Active run: [run-20260716-13-workstream-maintenance](../run/run-20260716-13-workstream-maintenance.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0013-ux-workstream-maintenance](../evaluation/eval-0013-ux-workstream-maintenance.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft separated maintenance entry from Workstream structure, evidence review, and Run detail execution.
- `2026-07-16`: executed and passed in `run-20260716-13`.
