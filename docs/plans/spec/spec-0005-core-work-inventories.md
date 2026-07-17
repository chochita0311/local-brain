# SPEC-0005: Core Work Inventories

## Metadata

- ID: `spec-0005`
- Status: `approved`
- Run ID: `run-20260716-05`
- Attempt: `1`
- Parent Feature: [feat-0005-core-work-inventories](../feature/feat-0005-core-work-inventories.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Workstream and Session inventories
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, Workstream state model, current list routes, filters, and creation API.

## Implementation Goal

- Present Workstreams and Sessions as related, scannable inventories while preserving state, provenance, filtering, creation, and detail navigation.

## In-Scope Behavior

- Apply semantic row, card, filter, form, status, provenance, timestamp, empty, and responsive treatments.
- Keep Workstream API submission and redirect and Session source/workspace query parameters unchanged.
- Use labels with Claude and Codex provenance; use product feedback families only for actual states.

## Out-Of-Scope Behavior

- New sorting, pagination, batch actions, schema changes, or detail redesign.

## Affected Surfaces

- `workstreams.html`, `sessions.html`, shared form handling, and inventory selectors.

## State And Interaction Contract

- No-data and filter-no-match remain distinguishable in template copy.
- Form feedback stays in the owning form with `aria-live`; errors do not use blocking browser alerts.

## Acceptance Mapping

- Workstream hierarchy maps to name, status, Thread/checkpoint counts, and activity rows.
- Session provenance maps to labeled source marks and metadata.
- Behavior preservation maps to unchanged endpoints, query fields, and row destinations.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved after shared shell pass.
