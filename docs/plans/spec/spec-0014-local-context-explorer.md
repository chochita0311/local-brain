# SPEC-0014: Local Context Explorer

## Metadata

- ID: `spec-0014`
- Status: `approved`
- Run ID: `run-20260716-14`
- Attempt: `3`
- Parent Feature: [feat-0014-local-context-explorer](../feature/feat-0014-local-context-explorer.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: source rail, tree, and preview
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, `/context?root=&document=` selection model, source APIs, and durable source-state mapping.

## Implementation Goal

- Align source selection, tree orientation, preview, source management, health, and narrow sequential use without changing indexing consequences.

## In-Scope Behavior

- Apply semantic rail, selected item, source type, tree, preview, path, health, empty/error, form, and responsive roles.
- Map pending info, ready success, missing warning, and error/unreadable danger with labels.
- Preserve direct query entry, add/remove endpoints, full-document link, tree disclosure, and index-only deletion language.

## Out-Of-Scope Behavior

- Scanning/extraction behavior, Automation, new source types, lazy loading, pagination, or in-source search.

## Affected Surfaces

- `context.html`, Context selectors in `styles.css`, and source add/remove handling in `app.js`.

## State And Interaction Contract

- Selected source, selected document, tree item, and preview identity remain synchronized.
- Destructive removal requires confirmation and states that original files and Apple Notes are not deleted.
- Narrow order is sources → tree → preview, with every action keyboard reachable.

## Acceptance Mapping

- State correctness maps to `.source-status` semantic selectors.
- Selection model maps to existing query parameters, active classes, and destinations.
- Narrow sequential use maps to one-column explorer rules below `700px`.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved as the final sequential PRD Feature run.
- `2026-07-16`: reused unchanged for Attempt 3 because Chrome evidence classified the failure as implementation-only; no Feature or Spec boundary changed.
