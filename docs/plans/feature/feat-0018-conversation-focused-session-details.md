# FEAT-0018: Conversation-Focused Session Details

## Metadata

- ID: `feat-0018`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Created: `2026-07-17`
- Updated: `2026-07-19`

## Goal

- Make primary Session and valid subsession details read as conversations by omitting visible tool-call rows while preserving source data, counts, parent context, and existing relationship navigation.

## Acceptance Contract

- Primary Session and valid subsession timelines render human or parent-agent messages and assistant or child-agent messages in authoritative source order.
- Normalized `tool_call` rows, including Codex execution tools and Claude tools such as `Bash` and `Write`, are absent from the rendered conversation timeline.
- User or assistant message text is not hidden merely because it describes a tool action or result.
- Stored Activity Events, source JSONL, tool names, total event counts, search/index ownership, and future insight inputs are unchanged by the presentation filter.
- A detail with no conversational messages shows an intentional no-conversation state rather than tool rows or a misleading source failure.
- Valid user-facing subsessions retain parent, back, provenance, and direct-detail orientation; an unresolved-parent subsession has no user-facing detail access.
- For this increment, a valid user-facing subsession is a direct child of a primary Session. Deeper descendants remain stored but have no current Session detail presentation.
- A parent Session detail retains its Subsessions section as a second child-access path alongside the inventory-row dropdown.
- Workstream membership links and existing primary Session detail destinations remain intact.

## Scope Boundary

- In:
  - conversation-only presentation selection for primary Session and valid subsession details
  - message order and role-label preservation
  - no-conversation empty state for tool-only details
  - total event-count clarification without changing the stored value
  - source, parent, back, and Workstream membership context
  - retained parent-detail Subsessions section for direct-entry child discovery
  - valid child direct-detail and unresolved-parent access gating
  - responsive conversation reading and long-content containment
- Out:
  - deleting, reclassifying, or ceasing ingestion of tool-call events
  - hiding message text that happens to mention a tool
  - changing Session list pagination, dropdown, or row metadata
  - changing global Search, tool statistics, Sessions Dashboard, or Insights definitions
  - Session editing, annotations, summaries, or new AI analysis
  - including Workstream maintenance Runs as Session details

## Surface Lanes

- Backend presentation lane:
  - path roots: `src/localbrain/queries.py`, `src/localbrain/main.py`
  - dependencies: `feat-0015` passed and valid child-detail identity available from `feat-0017`
  - expected evidence: message-only presentation query or context, preserved stored event count, valid parent lookup, and unresolved-parent detail denial
  - evaluator ownership: `contract`, `functional`
- Frontend reading lane:
  - path roots: `src/localbrain/templates/session.html`, `src/localbrain/templates/subsession.html`, `src/localbrain/static/styles.css`
  - dependencies: backend presentation lane
  - expected evidence: source-ordered conversation, role labels, no tool rows, no-conversation state, parent context, long-content containment, and responsive reading
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- primary Session and valid subsession detail route identity
- unresolved-parent detail access behavior
- stored Activity Event versus presentation-event selection
- message order, role, timestamp, source, and parent context
- total event count versus visible conversation rows
- Workstream membership and back-link destinations

## Required Evaluators

- `contract`: presentation-only filtering, source-event preservation, count semantics, route identity, and parent access rules.
- `design`: conversation hierarchy, empty state, reading width, long content, metadata distinction, and responsive containment.
- `functional`: tool-row omission, message preservation and order, parent and back links, Workstream links, tool-only details, and 404 or inaccessible states.
- `ux-heuristic`: conversation scan clarity, hidden-event count comprehension, parent orientation, and duplicate child-access friction.

## User-Visible Outcome

- The user can open a Session or subsession and read the human–agent conversation without repetitive `exec`, `Bash`, `Write`, or other tool-call rows interrupting the flow.

## Entry And Exit

- Entry point: Session inventory row, subsession dropdown child, Search or Workstream Session link, direct valid detail URL, or the retained parent-detail Subsessions section.
- Exit or transition behavior: back, parent, and Workstream links preserve their existing destinations and shared Sessions navigation context.

## State Expectations

- Default: conversational messages render from first to last in source order.
- Mixed messages and tools: only messages appear; total event metadata remains truthful.
- Tool-only detail: show an intentional no-conversation state without implying ingestion failure.
- No subsessions: no child section or child-only control is implied.
- Parent with subsessions: the Subsessions section remains available above the conversation timeline.
- Nested descendants: no list entry, retained Subsessions entry, or direct user-facing detail is exposed beyond one direct-child depth.
- Valid child: source and parent relationship remain visible and navigable.
- Unresolved parent: no user-facing detail is available.
- Long content: prompts, replies, paths inside messages, identifiers, and mixed Korean and English remain contained.
- Narrow viewport: roles, message content, timestamps, parent navigation, and essential metadata remain readable.

## Dependencies

- `feat-0015` must be `passed` before this Feature enters build.
- `feat-0017` must define and pass valid child destinations before subsession detail entry can be accepted end to end.

## Likely Affected Surfaces

- `src/localbrain/queries.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/session.html`
- `src/localbrain/templates/subsession.html`
- `src/localbrain/static/styles.css`
- `tests/test_parsers.py` as a non-mutation regression surface
- route, query, UI contract, and browser-level detail tests
- synthetic mixed-message, tool-only, long-content, Claude child, Codex child, and unresolved-parent fixtures

## Pass Or Fail Checks

- Pass if no normalized `tool_call` row is rendered on primary Session or valid subsession details.
- Pass if every user, assistant, parent-agent, and child-agent message remains in source order with its timestamp and role meaning.
- Pass if stored Activity Event rows, source JSONL, tool names, and total event counts remain unchanged.
- Pass if a tool-only detail produces a bounded no-conversation state rather than an empty broken surface.
- Pass if valid children retain source and parent orientation and unresolved-parent children cannot be opened through a user-facing route.
- Pass if only primary Sessions and their direct children have user-facing detail presentation and deeper descendants remain inaccessible without deleting their stored source-backed relation.
- Pass if the parent Session detail Subsessions section remains usable and reaches the same valid child destinations as the inventory dropdown.
- Pass if Workstream membership, back, parent, and direct links remain valid.
- Pass if `1440`, `920`, `700`, and `320` rendered evidence contains long mixed content without horizontal overflow.
- Fail if tool events are deleted, if messages mentioning tools are hidden, or if displayed event totals silently change to message-only counts.

## Regression Surfaces

- Session and subsession route identity and 404 behavior
- source timestamps, message order, event counts, and provenance
- Workstream membership and parent links
- Session search and tool/statistics data ownership
- Session inventory and subsession dropdown destinations
- shared shell, combined Sessions/Projects navigation, and reading-width contract

## Feature Review Questions

- Human review may choose the exact empty-state copy and whether it reports the number of hidden tool events; the state itself is required.

## Harness Trace

- Active spec doc: [spec-0018-conversation-focused-session-details](../spec/spec-0018-conversation-focused-session-details.md)
- Active run: [run-20260717-18-conversation-focused-session-details](../run/run-20260717-18-conversation-focused-session-details.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract terminology attempt 2](../evaluation/eval-0018-contract-subsession-terminology-attempt-2.md), [design terminology attempt 2](../evaluation/eval-0018-design-subsession-terminology-attempt-2.md), [functional terminology attempt 2](../evaluation/eval-0018-functional-subsession-terminology-attempt-2.md), [ux terminology attempt 2](../evaluation/eval-0018-ux-subsession-terminology-attempt-2.md)
- Latest fix note: [fix-0018-subsession-terminology](../fix/fix-0018-subsession-terminology.md)

## Continuity Notes

- `2026-07-17`: initial draft kept tool events as source data and narrowed only the Session and subsession reading presentation.
- `2026-07-17`: human Feature review retained the parent Session detail Subagents section in addition to the inventory-row dropdown.
- `2026-07-17`: human review limited user-facing subsession details and retained Subagents entries to direct children of a primary Session.
- `2026-07-17`: entered sequential fullstack execution after FEAT-0017 passed; screen-alignment mode is `extend`.
- `2026-07-17`: passed after message-only presentation, unified direct-child orientation, retained Subagents access, legacy Claude compatibility, tool-only empty state, responsive and actual-runtime browser checks, and the full 38-test suite completed without a blocking finding.
- `2026-07-19`: post-run human review resolved the product term as `Subsession`; the parent detail label, canonical lazy route, template, and implementation-facing names were aligned while preserving source-native Claude compatibility.
