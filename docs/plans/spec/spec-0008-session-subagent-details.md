# SPEC-0008: Session And Subagent Details

## Metadata

- ID: `spec-0008`
- Status: `approved`
- Run ID: `run-20260716-08`
- Attempt: `1`
- Parent Feature: [feat-0008-session-subagent-details](../feature/feat-0008-session-subagent-details.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: Session and Claude subagent details
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Constitution, Session/subagent route contexts, event vocabulary, and membership links.

## Implementation Goal

- Align both technical reading routes around provenance, parent context, metadata, relationship navigation, and a contained event timeline.

## In-Scope Behavior

- Apply semantic source marks, reading widths, metadata strips, memberships, subagent lists, event rails, technical typography, and narrow layout.
- Preserve event order and roles, source labels, parent and back links, subagent filenames, and Workstream destinations.

## Out-Of-Scope Behavior

- Parsing, indexing, event selection, annotations, editing, or displayed-payload changes.

## Affected Surfaces

- `session.html`, `subagent.html`, and detail/timeline selectors in `styles.css`.

## State And Interaction Contract

- Provenance always includes text; parent-agent and tool activity retain current labels.
- Optional membership, subagent, or event absence is neutral and does not masquerade as a route error.

## Acceptance Mapping

- Identity-first reading order maps to heading, detail strip, relationships, then timeline.
- Parent orientation maps to back and parent links.
- Long-content containment maps to `overflow-wrap`, bounded reading widths, and responsive columns.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved for the eighth sequential run.
