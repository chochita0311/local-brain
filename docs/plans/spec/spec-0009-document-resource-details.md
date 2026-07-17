# SPEC-0009: Document And Resource Details

## Metadata

- ID: `spec-0009`
- Status: `approved`
- Run ID: `run-20260716-09`
- Attempt: `1`
- Parent Feature: [feat-0009-document-resource-details](../feature/feat-0009-document-resource-details.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Document and local Resource details
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, detail route contexts, availability fields, and membership links.

## Implementation Goal

- Make both local-evidence routes calm reading surfaces with provenance, availability, relationships, technical paths, and reliable return navigation.

## In-Scope Behavior

- Align headings, metadata, membership strips, availability labels, document/note bodies, paths, and responsive reading widths.
- Preserve historical paths, current body rendering, missing evidence, route errors, and all existing links.

## Out-Of-Scope Behavior

- Extraction, rich text, Resource editing, relationship changes, or new Markdown behavior.

## Affected Surfaces

- `document.html`, `local_resource.html`, and document/resource selectors in `styles.css`.

## State And Interaction Contract

- Available is success, missing is warning, and absent notes or memberships are neutral empty states.
- Evidence content remains visually distinct from navigation and metadata.

## Acceptance Mapping

- Provenance and path priority map to the heading and detail strip.
- Availability mapping uses labeled success or warning roles.
- Long body and path containment maps to reading width, pre-wrap, and overflow-wrap rules.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved after shared detail foundations passed.
