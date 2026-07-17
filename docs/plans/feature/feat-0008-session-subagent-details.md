# FEAT-0008: Session And Subagent Details

## Metadata

- ID: `feat-0008`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make Session and Claude subagent detail routes coherent technical reading surfaces with clear provenance, metadata, parent context, timeline structure, and long-content containment.

## Acceptance Contract

- Session detail leads with source identity, title, path or project context, timestamps, metadata, Workstream memberships, and available subagents before the event timeline.
- Subagent detail preserves its parent Session relationship and distinguishes parent-agent, assistant, and tool activity without inventing new event meaning.
- Reading width, technical typography, event rails, metadata zones, and back or parent links follow the design system.
- Long prompts, tool names, timestamps, identifiers, and mixed content remain contained and readable.

## Scope Boundary

- In:
  - `/sessions/{session_id}` and `/sessions/{session_id}/subagents/{file_name}`
  - heading, provenance, metadata, membership, subagent list, timeline, event, empty, and responsive presentation
- Out:
  - parser, indexing, event selection, subagent discovery, or Session identity changes
  - editing or annotating Sessions
  - changing which tool payloads are indexed or displayed
  - general Session inventory owned by `feat-0005`

## Contract Surfaces

- Session and subagent GET route parameters and template contexts
- current event roles, event types, timestamps, source metadata, and parent relation
- Workstream membership links

## Required Evaluators

- `design`: reading width, hierarchy, provenance, event structure, mono usage, and responsive containment.
- `functional`: parent and back links, membership links, subagent links, event rendering, and route regressions.
- `ux-heuristic`: reading continuity, metadata density, parent orientation, and affordance clarity.

## User-Visible Outcome

- The user can read a Session or subagent history for sustained periods, understand its source and parent context, and follow existing relationships without horizontal overflow or metadata confusion.

## Entry And Exit

- Entry point: Session inventory, Search result, Workstream Resource, or parent Session subagent list.
- Exit or transition behavior: parent, back, membership, and related-resource links return to their existing destinations with shell orientation intact.

## State Expectations

- Default: source, metadata, relationships, and timeline have one clear reading order.
- Loading: no new client loading contract is introduced.
- Empty: missing optional memberships, subagents, or events are stated without implying route failure.
- Error: missing or invalid Session and subagent routes retain current error behavior.
- Success: long event content remains readable and every relationship link is usable.

## Dependencies

- `feat-0001`, `feat-0002`, and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/session.html`
- `src/localbrain/templates/subagent.html`
- Session heading, detail strip, membership, subagent list, timeline, event, technical-content, and responsive selectors in `src/localbrain/static/styles.css`

## Pass Or Fail Checks

- Pass if source and parent context remain visible without relying on color alone.
- Pass if long event text, paths, IDs, and tool names do not widen the page.
- Pass if all parent, membership, subagent, and back links retain destinations.
- Pass if narrow content preserves event role, text, and timestamp meaning.
- Fail if visual grouping changes event semantics or hides unavailable evidence.
- Fail if direct route entry loses enough context that the user cannot identify the Session or parent.

## Regression Surfaces

- Session and subagent route identity and 404 behavior
- event ordering and role labels
- Workstream membership and parent links
- shared shell and source-provenance roles

## Harness Trace

- Active spec doc: [spec-0008-session-subagent-details](../spec/spec-0008-session-subagent-details.md)
- Active run: [run-20260716-08-session-subagent-details](../run/run-20260716-08-session-subagent-details.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0008-ux-session-details](../evaluation/eval-0008-ux-session-details.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft paired Session and subagent detail because they share one source-backed technical reading model.
- `2026-07-16`: executed and passed in `run-20260716-08`.
