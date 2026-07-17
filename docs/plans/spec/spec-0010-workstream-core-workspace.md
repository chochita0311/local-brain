# SPEC-0010: Workstream Core Workspace

## Metadata

- ID: `spec-0010`
- Status: `approved`
- Run ID: `run-20260716-10`
- Attempt: `1`
- Parent Feature: [feat-0010-workstream-core-workspace](../feature/feat-0010-workstream-core-workspace.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Workstream core detail
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, Workstream and Thread state models, checkpoint contract, and existing edit APIs.

## Implementation Goal

- Establish a clear Workstream → checkpoint → Thread → editor hierarchy without changing recovery data or action consequences.

## In-Scope Behavior

- Align Workstream identity/status, checkpoint summary, Thread rows/editors, Workstream editor, new Thread, and checkpoint form.
- Preserve current field names, values, endpoints, reloads, versioning, Resource snapshot count, and empty branches.
- Use active/success, paused/warning, blocked/danger, and done/archived neutral state roles.

## Out-Of-Scope Behavior

- Evidence review, Run maintenance, index changes, or data-contract changes.

## Affected Surfaces

- core regions of `workstream.html`, Workstream selectors in `styles.css`, and shared form feedback in `app.js`.

## State And Interaction Contract

- Form submission is bounded to its editor; success reloads the same Workstream and error remains in an `aria-live` result.
- No-checkpoint and no-Thread states remain independent and expose only current actions.

## Acceptance Mapping

- Primary hierarchy maps to heading, checkpoint band, and Thread list ordering.
- State mapping maps to badges and Thread markers.
- Dense-content containment maps to collapsible editors and narrow one-column layout.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved before evidence and maintenance child runs.
