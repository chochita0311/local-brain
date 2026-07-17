# SPEC-0011: Workstream Evidence Review

## Metadata

- ID: `spec-0011`
- Status: `approved`
- Run ID: `run-20260716-11`
- Attempt: `1`
- Parent Feature: [feat-0011-workstream-evidence-review](../feature/feat-0011-workstream-evidence-review.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: confirmed evidence and Suggestion review
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, reversible Suggestion policy, Resource/link endpoints, and current relationship ownership.

## Implementation Goal

- Visually and interactively separate confirmed Resources from inferred Suggestions while preserving every current review and linking consequence.

## In-Scope Behavior

- Align Workstream/Thread Resource lists, type/relation labels, link and creation forms, pending Suggestions, excluded history, and review actions.
- Preserve link/unlink, create, generate, accept, reject, restore, supersede, reload, and destination behavior.
- Use brand for pending review, neutral for excluded history, and provenance only for origin.

## Out-Of-Scope Behavior

- Retrieval, confidence calculation, matching, batch review, or relationship data changes.

## Affected Surfaces

- evidence and Suggestion regions of `workstream.html`, related CSS, and API action handling in `app.js`.

## State And Interaction Contract

- Confirmed evidence and inferred Suggestions occupy distinct labeled structures.
- Destructive unlink retains explicit confirmation; action failures use a bounded live notice; inferred changes require acceptance.

## Acceptance Mapping

- Ownership and consequence map to relation labels, target copy, destinations, and confirmation.
- Reversibility maps to existing reject/restore and supersede flows.
- Empty-state distinction maps to separate confirmed, pending, and excluded branches.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved after Workstream core pass.
