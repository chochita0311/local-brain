# FEAT-0043: Session Markdown Conversation Reading

## Metadata

- ID: `feat-0043`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Created: `2026-07-19`
- Updated: `2026-08-03`

## Goal

- Make visible Session and Subsession user and assistant messages easier to read as Markdown while preserving the existing conversation, role, source, count, parent, and hidden-event contracts.

## Acceptance Contract

- Only visible user and assistant message bodies consume the passed FEAT-0038 and FEAT-0039 renderer contracts.
- Plain messages remain natural, while supported Markdown, code, tables, and Obsidian authoring syntax gain readable hierarchy inside the existing conversation structure.
- Session and Subsession messages have no owning Local Context source by default; source-relative links, wikilinks, and note embeds remain readable but unresolved rather than guessing a global Document.
- HTTP and HTTPS links retain the shared explicit, activation-only, no-prefetch behavior; unsafe schemes remain disabled.
- System, source-specific, tool, and other structural events are not newly Markdown-rendered or exposed.
- Message order, role meaning, timestamps, Session and Subsession identity, parent context, Workstream memberships, total event counts, stored Activity Events, source JSONL, search ownership, and omission of tool rows remain unchanged.
- Long code, tables, URLs, headings, properties, math, and mixed Korean and English remain contained at every supported width.

## Scope Boundary

- In:
  - user and assistant body rendering on primary Session and valid Subsession detail
  - plain, supported, malformed, hostile, unresolved, deferred image, and renderer-failure presentation
  - role, timestamp, order, parent, source, count, membership, and responsive regression protection
  - conversation-appropriate Markdown styling that remains subordinate to role hierarchy
- Out:
  - Markdown rendering for system, source-specific, tool, or structural events
  - exposing hidden tool calls or changing the visible-event query
  - parser, ingestion, Activity Event, source JSONL, search, counts, or Session organization changes
  - guessing a Local Context source or globally resolving wikilinks from Session text
  - message editing, summaries, annotations, images, attachments, or AI analysis

## Surface Lanes

- Backend rendering lane:
  - path roots: Session and Subsession presentation context in `src/localbrain/main.py` or relevant query and renderer integration, plus route tests
  - dependencies: FEAT-0038 and FEAT-0039 passed; FEAT-0018 visible-event contract
  - expected evidence: renderer applies only to eligible user and assistant bodies with no owning-source guess and leaves stored events and counts unchanged
  - evaluator ownership: `contract`, `functional`
- Frontend conversation lane:
  - path roots: `src/localbrain/templates/session.html`, `src/localbrain/templates/subsession.html`, `src/localbrain/static/styles.css`
  - dependencies: backend rendering lane
  - expected evidence: Markdown hierarchy inside conversation cards, clear roles and timestamps, safe links, generic fallbacks, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- Primary Session and valid Subsession detail routes.
- FEAT-0018 visible user and assistant message selection and tool-row omission.
- FEAT-0038 renderer and FEAT-0039 no-owning-source reference behavior.
- Message role, timestamp, order, total count, source, parent, and Workstream membership semantics.
- Authoritative Activity Events and source JSONL versus derived rendered message bodies.

## Required Evaluators

- `contract`: eligible roles, derived-output ownership, no-source resolution, stored event and count preservation, and inherited visible-event contract.
- `design`: conversation hierarchy, Markdown typography, code and table containment, role priority, long content, and responsive reading.
- `functional`: primary and Subsession rendering, plain text, every supported syntax type, external and unsafe links, unresolved wikilinks, hidden events, order, counts, memberships, parent links, empty conversation, and fallbacks.
- `ux-heuristic`: conversation scan clarity, Markdown density, role distinction, link comprehension, and long-response friction.

## User-Visible Outcome

- The user can read Markdown-shaped prompts and responses as a clear conversation without tool rows returning or message metadata becoming secondary to decoration.

## Entry And Exit

- Entry point: primary Session detail, valid Subsession detail, or their existing direct, parent, Search, inventory, and Workstream destinations.
- Exit or transition behavior: back, parent, inventory, and Workstream links retain their existing destinations and orientation.

## State Expectations

- Default: user and assistant bodies render in authoritative order with roles and timestamps clear.
- Plain text: no Markdown markers are required and the message remains natural.
- Unresolved: source-relative and wikilink syntax remains readable without a guessed destination.
- Empty: the existing no-conversation state remains intentional when no visible message exists.
- Error: one malformed or failed message uses the shared bounded fallback without breaking adjacent messages or the whole timeline.
- Success: every eligible message is readable and every ineligible or hidden event retains its existing contract.

## Dependencies

- FEAT-0038 and FEAT-0039 must be `passed` before this Feature enters build.
- FEAT-0018 Conversation-Focused Session Details must remain `passed`.

## Likely Affected Surfaces

- Session and Subsession presentation context in `src/localbrain/main.py` or relevant queries
- `src/localbrain/templates/session.html`
- `src/localbrain/templates/subsession.html`
- `src/localbrain/static/styles.css`
- Session detail, source-preservation, UI contract, responsive, and browser tests with synthetic conversations

## Pass Or Fail Checks

- Pass if every visible user and assistant body uses the shared renderer and plain text remains natural.
- Pass if system, source-specific, tool, and structural events are neither newly rendered nor newly exposed.
- Pass if source-relative links and wikilinks stay unresolved without an owning source, external links require activation, and unsafe schemes remain disabled.
- Pass if message order, roles, timestamps, counts, parent context, memberships, Activity Events, source JSONL, search ownership, and tool-row omission remain unchanged.
- Pass if long Markdown, code, tables, properties, math, URLs, and mixed scripts remain contained at `1440`, `920`, `700`, and `320`.
- Pass if one malformed or failed message falls back independently without breaking the conversation.
- Fail if Markdown decoration obscures role hierarchy, if hidden events return, or if rendering mutates stored source data.

## Regression Surfaces

- FEAT-0018 primary and Subsession route, message-only presentation, empty state, tool omission, order, count, parent, and membership behavior
- source ingestion, Activity Events, search, tool statistics, and Sessions Dashboard
- shared shell, combined Sessions navigation, and reading-width containment

## Harness Trace

- Active spec doc: [spec-0043-session-markdown-conversation-reading](../spec/spec-0043-session-markdown-conversation-reading.md)
- Active run: [run-20260720-48-session-markdown-conversation-reading](../run/run-20260720-48-session-markdown-conversation-reading.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [Contract — PASS, complete](../evaluation/eval-0043-contract-session-markdown-conversation-reading.md)
  - [Design — PASS, complete](../evaluation/eval-0043-design-session-markdown-conversation-reading.md)
  - [Functional — PASS, complete](../evaluation/eval-0043-functional-session-markdown-conversation-reading.md)
  - [UX Heuristic — PASS, complete](../evaluation/eval-0043-ux-session-markdown-conversation-reading.md)
- Latest fix note:
  - [Session Markdown technical-content overflow](../fix/fix-0043-session-markdown-technical-content-overflow.md)

## Continuity Notes

- `2026-07-19`: initial draft limited Markdown to visible user and assistant bodies and preserved FEAT-0018's conversation-only presentation, no-owning-source link behavior, and stored-event boundaries.
- `2026-07-20`: the owner continued the authorized sequential PRD-0006 workflow after FEAT-0042 passed. FEAT-0043 is approved under `fullstack-product`, with backend-rendering then frontend-conversation lanes and `screen-alignment` extend mode.
- `2026-07-20`: copied rendering, shared templates, browser evidence, responsive containment, full regression, and all four evaluators passed. FEAT-0043 and the six-Feature PRD-0006 execution sequence are complete.
- `2026-08-03`: owner review of a real Java-log Session exposed a multiline dollar-math false positive and direct indented-code overflow that the earlier synthetic long-content fixture did not cover. The bounded follow-up is tracked in FIX-0043 without reopening the approved feature boundary.
- `2026-08-03`: FIX-0043 completed with a same-line inline-math boundary, bounded
  generated MathML and direct indented-code overflow, a structural regression
  fixture, fresh-process browser checks at `1440`, `920`, `700`, and `320`, 352
  passing repository tests, and privacy verification. FEAT-0043 remains closed
  as `passed`.
