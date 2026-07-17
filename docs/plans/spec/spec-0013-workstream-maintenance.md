# SPEC-0013: Workstream Maintenance

## Metadata

- ID: `spec-0013`
- Status: `approved`
- Run ID: `run-20260716-13`
- Attempt: `1`
- Parent Feature: [feat-0013-workstream-maintenance](../feature/feat-0013-workstream-maintenance.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Workstream maintenance tools
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, Task Runner fields/policy, Run history, maintenance marker API, and clipboard interaction.

## Implementation Goal

- Present Run configuration/history and marker generation as distinct operational paths that hand off clearly to the renewed Run detail.

## In-Scope Behavior

- Align runner availability, form, policy strip, Run history/status, marker output, copy feedback, errors, and responsive layout.
- Preserve task/model/cwd/refresh/budget payload, Run redirect, history links, marker API, and maintenance-session separation.

## Out-Of-Scope Behavior

- Runner execution, retrieval, task definitions, marker semantics, or Run detail changes.

## Affected Surfaces

- maintenance regions of `workstream.html`, maintenance CSS, API form/marker/copy handlers in `app.js`.

## State And Interaction Contract

- Unavailable runner uses danger; empty history is neutral; start errors remain in the form; marker/copy feedback stays in its panel.
- Marker generation never resembles the primary in-app Run action.

## Acceptance Mapping

- Configuration visibility maps to the existing form and policy strip.
- Reusable lifecycle mapping maps to Run history badges from `feat-0012`.
- Distinct paths map to separate headings, actions, results, and consequences.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved after Run console pass.
