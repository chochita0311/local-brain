# SPEC-0004: Overview Dashboards

## Metadata

- ID: `spec-0004`
- Status: `approved`
- Run ID: `run-20260716-04`
- Attempt: `1`
- Parent Feature: [feat-0004-overview-dashboards](../feature/feat-0004-overview-dashboards.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Dashboard and Sessions Dashboard
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, existing dashboard templates, query outputs, and maintenance-marker interaction.

## Implementation Goal

- Reconcile both overview families with the shared metric, panel, chart, status, empty-state, and responsive roles while retaining Workstream-first hierarchy.

## In-Scope Behavior

- Migrate overview selectors to semantic surfaces, borders, elevation, brand, feedback, and provenance roles.
- Keep current metric definitions, links, maintenance marker action, chart inputs, and server-rendered empty behavior.
- Contain long labels and collapse the 12-column grid at compact and narrow widths.

## Out-Of-Scope Behavior

- New widgets, insight calculations, query changes, or client-side loading states.

## Affected Surfaces

- `dashboard.html`, `sessions_dashboard.html`, overview selectors in `styles.css`, and bounded marker feedback in `app.js`.

## State And Interaction Contract

- Activity uses brand emphasis, source mix uses provenance, health uses success or danger, and attention uses warning.
- Marker failures use the shared live notice; successful marker generation remains in its owning panel.

## Acceptance Mapping

- Workstream continuity maps to the existing Dashboard ordering.
- Traceability maps to existing summary links and labels.
- Sparse, zero, long, and narrow containment maps to current empty branches and responsive grid rules.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved for sequential overview alignment.
