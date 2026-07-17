# FEAT-0005: Core Work Inventories

## Metadata

- ID: `feat-0005`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Give the user consistent, scannable Workstream and Session inventory surfaces while preserving creation, filtering, source identity, timestamps, and navigation to existing details.

## Acceptance Contract

- Workstreams lead with name, status, Thread and checkpoint context, activity, and a clear path to detail.
- Sessions preserve source identity, project or workspace context, timestamps, metadata, and filters without treating provenance as status.
- Workstream creation and Session filtering retain their current route and API consequences.
- Rows, status labels, forms, filters, long content, empty states, and narrow transformations follow shared component roles.

## Scope Boundary

- In:
  - `/workstreams` index, new-Workstream entry, status and summary rows
  - `/sessions` inventory, source and workspace filtering, Session and recent-document summaries
  - list, filter, form, metadata, empty, and responsive presentation shared by these two core inventories
- Out:
  - Workstream detail owned by `feat-0010`
  - Session detail owned by `feat-0008`
  - changing Workstream creation or Session query behavior
  - new sorting, pagination, batch actions, or organization capabilities

## Contract Surfaces

- `/workstreams` and `/sessions` GET route parameters and template contexts
- `POST /api/workstreams` request and redirect behavior
- source and workspace filter query parameters

## Required Evaluators

- `design`: row hierarchy, metadata alignment, form treatment, status semantics, and responsive containment.
- `functional`: Workstream creation, filter changes, detail links, empty states, and current navigation behavior.
- `ux-heuristic`: scan clarity, filter comprehension, action hierarchy, and no-data versus no-match distinctions.

## User-Visible Outcome

- The user can scan, create, filter, and open core work records through two visually related inventories without losing source or state meaning.

## Entry And Exit

- Entry point: `/workstreams` or `/sessions` from shared navigation or related overview links.
- Exit or transition behavior: creation redirects according to the existing API contract; rows open their current detail routes; filters update only the intended result scope.

## State Expectations

- Default: rows expose stable identity, status or source, key metadata, and destination affordance.
- Loading: existing server navigation remains bounded by the stable shell.
- Empty: distinguish no Workstreams or Sessions from a filter with no matching Sessions.
- Error: form errors preserve entered values and stay near the owning action when supported by the current contract.
- Success: created Workstream or selected filter state is visibly reflected after navigation.

## Dependencies

- `feat-0002` and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/workstreams.html`
- `src/localbrain/templates/sessions.html`
- inventory row, filter, form, source-identity, status, empty-state, and responsive selectors in `src/localbrain/static/styles.css`
- shared API form handling in `src/localbrain/static/app.js` as a regression surface

## Pass Or Fail Checks

- Pass if Workstream and Session rows remain scannable with long mixed-script content.
- Pass if source identity is visually distinct from product status and always labeled.
- Pass if Workstream creation, source filtering, workspace filtering, and detail links retain behavior.
- Pass if supported narrow layouts retain identity, destination, and essential actions.
- Fail if visual changes alter query semantics or imply unavailable list actions.
- Fail if no-data and no-match states become indistinguishable.

## Regression Surfaces

- Workstream creation API and redirect
- Session source and workspace filters
- Session and Workstream detail links
- shared shell, global search, and provenance contract

## Harness Trace

- Active spec doc: [spec-0005-core-work-inventories](../spec/spec-0005-core-work-inventories.md)
- Active run: [run-20260716-05-core-work-inventories](../run/run-20260716-05-core-work-inventories.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0005-ux-core-inventories](../evaluation/eval-0005-ux-core-inventories.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft paired Workstreams and Sessions as the two core work inventories while keeping their detail surfaces separate.
- `2026-07-16`: executed and passed in `run-20260716-05`.
