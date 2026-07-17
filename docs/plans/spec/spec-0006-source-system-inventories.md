# SPEC-0006: Source And System Inventories

## Metadata

- ID: `spec-0006`
- Status: `approved`
- Run ID: `run-20260716-06`
- Attempt: `1`
- Parent Feature: [feat-0006-source-system-inventories](../feature/feat-0006-source-system-inventories.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Projects, Sources, and Atlassian
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, project/source query outputs, scan API, and Atlassian planned-state routes.

## Implementation Goal

- Align system inventories and unavailable connector views without changing data meaning or implying unsupported integration behavior.

## In-Scope Behavior

- Use semantic availability, health, planned, path, scan-feedback, row, and responsive roles.
- Preserve Project-to-Sessions links, `/api/scan`, refresh timing, and Atlassian `view` switching.
- Keep healthy, missing, error, and planned labels explicit.

## Out-Of-Scope Behavior

- Connector authentication, new health metrics, ingestion changes, or source-management actions.

## Affected Surfaces

- `projects.html`, `sources.html`, `atlassian.html`, `styles.css`, and scan handling in `app.js`.

## State And Interaction Contract

- Scan working, success, and failure remain bounded to the Sources action region.
- Planned Atlassian content remains informational and contains no false writable affordance.

## Acceptance Mapping

- Long path and state containment maps to inventory row truncation and responsive rules.
- Correct health meaning maps to explicit success, warning, and danger roles.
- Behavior retention maps to unchanged routes and scan request.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved as the sixth sequential run.
