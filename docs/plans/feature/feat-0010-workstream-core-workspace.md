# FEAT-0010: Workstream Core Workspace

## Metadata

- ID: `feat-0010`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make Workstream identity, Threads, editing, and checkpoint recovery context form one clear workspace foundation before evidence review and maintenance controls are renewed.

## Acceptance Contract

- Workstream name, status, summary, and current checkpoint lead the detail route.
- Threads remain subordinate work units with visible state, goal, blocker, next action, and linked-evidence count where present.
- Workstream edit, Thread create and edit, and checkpoint create actions retain their current routes, values, consequences, and feedback.
- Empty Threads and missing checkpoint states explain what is absent and expose only the relevant current action.
- Dense core regions collapse without losing identity, state labels, edit access, or recovery context.

## Scope Boundary

- In:
  - Workstream heading, status, summary, current checkpoint, Workstream editor, Thread list and editors, new Thread form, and checkpoint form
  - core workspace hierarchy, forms, feedback, long content, empty states, and responsive composition
- Out:
  - confirmed Resources, link tools, and Suggestions owned by `feat-0011`
  - Run launcher, Run history, and maintenance marker owned by `feat-0013`
  - Workstream index owned by `feat-0005`
  - changes to Workstream, Thread, or checkpoint data contracts

## Contract Surfaces

- `/workstreams/{workstream_id}` core template context
- current Workstream, Thread, and checkpoint API endpoints and state vocabularies
- checkpoint version, confirmation, Resource snapshot count, and recovery-field meaning

## Required Evaluators

- `design`: hierarchy, state semantics, checkpoint priority, form grouping, density, and responsive containment.
- `functional`: Workstream edit, Thread create and edit, checkpoint creation, feedback, redirects or reloads, and regression.
- `ux-heuristic`: recovery orientation, edit clarity, checkpoint comprehension, and Thread scan friction.

## User-Visible Outcome

- The user can open a Workstream, understand its current recovery state, review its Threads, and update the existing structure without evidence or maintenance regions competing for primary attention.

## Entry And Exit

- Entry point: Workstream index, Dashboard, Search, or a related membership link.
- Exit or transition behavior: successful edits and checkpoint creation return to the same Workstream with the updated state clearly reflected.

## State Expectations

- Default: Workstream identity, checkpoint, and Threads follow one responsibility order.
- Loading: form submission remains bounded to the owning editor.
- Empty: no checkpoint and no Threads are distinct, explanatory states.
- Error: validation and action failures stay with the owning form and preserve recoverable input when supported.
- Success: saved Workstream, saved or added Thread, and confirmed checkpoint outcomes are visibly reflected.

## Dependencies

- `feat-0002` and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- core heading, checkpoint, Thread, Workstream editor, and checkpoint editor regions in `src/localbrain/templates/workstream.html`
- Workstream core, checkpoint, Thread, form, feedback, and responsive selectors in `src/localbrain/static/styles.css`
- shared API form handling in `src/localbrain/static/app.js`

## Pass Or Fail Checks

- Pass if Workstream-to-Thread hierarchy and current checkpoint priority are unambiguous.
- Pass if Workstream, Thread, and checkpoint actions retain their current payload and result behavior.
- Pass if all current Workstream and Thread states use the constitution's labels and semantic families.
- Pass if long goals, blockers, next actions, and checkpoint content remain contained at supported widths.
- Fail if evidence or maintenance controls become necessary to understand the core hierarchy.
- Fail if rerender or reload behavior leaves a repeated editor inactive after first use.

## Regression Surfaces

- Workstream detail route and identity
- Workstream and Thread editing
- Thread creation
- checkpoint creation, versioning, and Resource snapshot summary
- Dashboard and inventory links into the Workstream

## Harness Trace

- Active spec doc: [spec-0010-workstream-core-workspace](../spec/spec-0010-workstream-core-workspace.md)
- Active run: [run-20260716-10-workstream-core-workspace](../run/run-20260716-10-workstream-core-workspace.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0010-ux-workstream-core](../evaluation/eval-0010-ux-workstream-core.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft split core recovery structure from evidence review and maintenance execution to keep one loop-sized outcome.
- `2026-07-16`: executed and passed in `run-20260716-10`.
