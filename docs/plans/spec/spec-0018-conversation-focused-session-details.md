# SPEC-0018: Conversation-Focused Session Details

## Metadata

- ID: `spec-0018`
- Status: `approved`
- Run ID: `run-20260717-18`
- Attempt: `1`
- Parent Feature: [feat-0018-conversation-focused-session-details](../feature/feat-0018-conversation-focused-session-details.md)
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: backend presentation read model → detail reading surface → legacy-route integration
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Source Set

- Human request: hide visible `exec`, `Bash`, `Write`, and other tool events without deleting source data; keep the parent-detail Subagents area; expose one direct-child depth for both Claude and Codex.
- Passed FEAT-0015 source-neutral relation and FEAT-0017 valid child destinations.
- Existing Session and Claude lazy-subagent detail routes, Product Model, Design Constitution, Design Evaluation, and Interaction Evaluation.
- screen-alignment `extend` mode using the existing detail-reading family.

## Implementation Goal

- Render primary Sessions and valid direct children through one conversation-focused detail contract while retaining raw events, parent orientation, Workstream links, the parent Subagents section, and safe legacy Claude destinations.

## In-Scope Behavior

- Select only normalized `message` Activity Events for the visible timeline, ordered by `sequence` and stable row ID from the first message onward.
- Keep `session_events` and stored Activity Events unchanged for provenance and non-presentation consumers.
- Label the Session-level event count as the source-backed total and state that tool activity is hidden from the reading timeline.
- Render an intentional conversation-empty state for a tool-only Session.
- Resolve a direct child’s eligible primary parent and render a parent backlink and child role orientation.
- Query same-source, `work`, direct subsessions for a primary detail and render them in the existing Subagents section for Claude and Codex.
- Do not render a Subagents section on a child detail and do not expose grandchildren.
- Preserve valid legacy Claude lazy-subagent links. Validate that their source-derived parent identity matches the requested primary; redirect to the normalized child detail when an equivalent imported child exists, otherwise render the legacy source through the same message-only presentation.
- Preserve current Workstream membership destinations.

## Out-Of-Scope Behavior

- Event deletion or reclassification, parser changes, Search/statistics changes, message summarization, annotations, nested child presentation, Session editing, or Workstream-maintenance inclusion.

## Affected Surfaces

- `src/localbrain/queries.py`, `src/localbrain/main.py`, `src/localbrain/subagents.py`
- `/sessions/{id}` and `/sessions/{id}/subagents/{file}`
- `src/localbrain/templates/session.html`, `subagent.html`
- `src/localbrain/static/styles.css`
- detail query, route contract, template, and browser tests

## Surface Lanes

- Backend presentation lane:
  - dependency order: first
  - responsibility: message-only selection, parent and direct-child queries, raw-count preservation, lookup gating
  - validation evidence: in-memory mixed, tool-only, child, grandchild, and orphan fixtures
  - evaluators: Contract and Functional
- Frontend reading lane:
  - dependency order: backend contract passed locally
  - responsibility: unified role hierarchy, parent context, retained Subagents section, empty state, count clarification, long-content containment
  - validation evidence: template contracts and 1440/920/700/320 browser renders
  - evaluators: Design, Functional, and UX
- Legacy-route integration lane:
  - dependency order: normalized path complete
  - responsibility: direct-parent validation, normalized redirect, message-only fallback
  - validation evidence: synthetic Claude files and route behavior
  - evaluators: Contract and Functional

## State And Interaction Contract

- A primary detail links back to the Sessions inventory; a child detail links to its eligible primary parent and also offers inventory return.
- A parent with direct children renders the retained Subagents section above the conversation. A parent without children does not render an empty child section.
- Child entries use normal links to the same valid destinations exposed by the inventory dropdown.
- Message role labels are `나` and source agent for a primary Session, and `상위 Agent` and child agent for a subsession.
- The visible timeline never branches on tool name because tool rows never enter its presentation model.
- A no-message detail remains a complete detail page with metadata, orientation, and explanatory empty copy.
- Long prompts, replies, paths, identifiers, and mixed Korean/English wrap inside the established reading width without horizontal overflow.

## Data And Contract Assumptions

- `session_conversation_events` is a presentation query and filters `event_type = 'message'` without mutating the raw event API or database rows.
- `session_parent` returns a parent only for a same-source `work` direct child whose parent is primary.
- `session_subsessions` returns only same-source `work` direct children when the requested owner is primary.
- `session.event_count` remains the full normalized source count and is never recomputed from visible messages.
- A message mentioning `exec`, `Bash`, `Write`, or another tool remains visible because filtering uses `event_type`, not text.
- Existing Claude lazy paths are compatibility input, not a second normalized hierarchy owner.

## Contract Surfaces

- Producer expectations: query layer owns eligible detail identity, parent relation, direct children, and message-only selection.
- Consumer expectations: route supplies raw total and visible messages separately; templates never inspect or suppress tool text.
- Source-of-truth owner: original JSONL, normalized Session relation, and Activity Events.
- Stale-assumption check: Claude-only parent children and mixed tool/message timeline rendering are removed from the primary detail path; legacy source links remain bounded compatibility paths.

## Required Evaluators

- Contract: presentation-only filter, raw row/count preservation, parent/child predicates, legacy validation, and route identity.
- Design: conversation hierarchy, parent context, retained child section, count distinction, empty state, long content, and responsive containment.
- Functional: mixed and tool-only details, message order and text preservation, child links, parent links, Workstream links, legacy redirect/fallback, and inaccessible descendants.
- UX heuristic: reading continuity, hidden-event comprehension, parent orientation, and duplicate entry-path consistency.

## Acceptance Mapping

- Tool omission maps to the message-only presentation query and timeline template.
- Raw preservation maps to unchanged storage, raw query, and source count.
- Unified child orientation maps to parent/direct-child queries and the shared Session template.
- Existing Subagents retention maps to the source-neutral direct-child list plus bounded Claude compatibility fallback.
- Empty-state acceptance maps to an explicit message-only empty panel.

## Evaluation Focus

- Verify that a message containing a tool word remains visible while an adjacent tool event is absent.
- Compare database row and `event_count` totals before and after rendering.
- Inspect primary, direct-child, tool-only, long-content, no-child, and retained Subagents states.
- Confirm nested and unresolved subsessions still return no user-facing detail.

## Open Blockers

- None. Empty-state copy will state that no conversational messages exist and that tool activity remains included in the source event count.

## Continuity Notes

- `2026-07-17`: approved for sequential execution after FEAT-0017 passed; screen-alignment mode is `extend`.
