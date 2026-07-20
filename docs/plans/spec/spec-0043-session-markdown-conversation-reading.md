# SPEC-0043: Session Markdown Conversation Reading

## Metadata

- ID: `spec-0043`
- Status: `approved`
- Run ID: `run-20260720-48`
- Attempt: `1`
- Parent Feature: [feat-0043-session-markdown-conversation-reading](../feature/feat-0043-session-markdown-conversation-reading.md)
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-rendering`, then `frontend-conversation`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-20`
- Updated: `2026-07-20`

## Source Set

- Approved FEAT-0043 and PRD-0006 acceptance contracts.
- Passed FEAT-0038/0039 shared renderer, safety, Obsidian syntax, and no-owning-source reference behavior.
- Passed FEAT-0018 primary Session and direct Subsession conversation-only presentation.
- Current Session and Subsession headings, detail strips, parent orientation, memberships, message cards, roles, timestamps, counts, empty state, and responsive shell.
- Design Constitution conversation timeline and detail-reading families, Design Evaluation, and Interaction Evaluation.
- Alignment mode: `screen-alignment` `extend`; current LocalBrain conversation presentation remains product truth.

## Implementation Goal

- Render only currently visible user and assistant message text through the shared Markdown contract while preserving the existing conversation query, raw event data, role hierarchy, counts, parent context, and message order.

## Backend Rendering Lane

- Add one pure presentation adapter that accepts either normalized SQLite message rows or lazy parsed Subsession events and returns a copied view.
- Preserve every available event field and the exact raw `text` value.
- For role `user` or `assistant` with string text, call `render_markdown(text)` without a `MarkdownReferenceContext`.
- Attach only derived `rendered_body`, `render_state`, and `render_properties` fields to the copied view.
- Leave other roles unrendered. Do not change `session_conversation_events`, parsing, ingestion, storage, source JSONL, event counts, ordering, Search, or tool-row omission.
- Apply the adapter after the existing normalized and lazy conversation filters and sorting are complete.
- A renderer failure remains local to one message through the shared escaped fallback result.

## Frontend Conversation Lane

- Keep the current Session and Subsession templates, timeline rows, rails, role labels, timestamps, empty state, parent links, memberships, source identity, and counts.
- Within an eligible message card, render valid YAML properties separately and render the trusted shared result in an `.event-text.markdown-body` container without a template `safe` filter.
- Retain escaped plain-text fallback markup for any non-eligible visible message.
- Reuse the shared Markdown components while adding only conversation-specific typography and spacing overrides needed to keep Markdown subordinate to the role header.
- Keep message cards within the existing conversation reading width. Code and tables own local overflow; URLs, headings, properties, math, and mixed scripts cannot widen the page.
- Do not add message actions, collapse controls, outline navigation, source selectors, link previews, image fetching, attachments, or JavaScript navigation.

## No-Source Link Contract

- Same-message heading and block fragments remain active local anchors.
- Relative Markdown links, wikilinks, note embeds, and source-dependent references render in the shared `no-source` unavailable state.
- HTTP and HTTPS links retain explicit external treatment, `noopener noreferrer external`, and activation-only behavior.
- Unsafe schemes and local file destinations expose no executable `href`.
- Standard images and attachment embeds remain deferred and initiate no request.

## Affected Surfaces

- `src/localbrain/main.py`
- a presentation adapter under `src/localbrain/`
- `src/localbrain/templates/session.html`
- `src/localbrain/templates/subsession.html`
- `src/localbrain/static/styles.css`
- Session detail and UI contract tests
- Product and Architecture current behavior contracts

## Surface Lanes

- Backend rendering:
  - producer: existing message-only normalized rows and lazy parsed events
  - consumer: copied message views with derived shared renderer output
  - validation: raw-field preservation, eligible-role rendering, non-eligible fallback, no-source references, independent failure, order and count invariants
  - evaluator ownership: Contract, Functional
- Frontend conversation:
  - producer: rendered message views
  - consumer: current Session and Subsession timelines
  - validation: template/CSS contracts plus browser review at `1440`, `920`, `700`, and `320`
  - evaluator ownership: Design, Functional, UX Heuristic

## Screen-Alignment Consistency List

- Retain literally: shell, Session heading, source badge, detail strip, parent notice, memberships, Subsessions list, conversation heading, role labels, timestamps, rails, card boundaries, count copy, and empty state.
- Reuse natively: shared `.markdown-body`, properties, code, table, callout, task, math, link, reference, deferred-image, and fallback families.
- New compatible treatment: compact heading scale and block spacing inside message cards only.
- Preserve product truth: no source is guessed, no hidden event is surfaced, and no message-level control or metadata is invented.
- Style ownership: existing timeline structure owns layout; shared Markdown owns blocks; conversation-specific rules own only scale and containment; semantic tokens own all visual values.

## Acceptance Mapping

- Eligible user and assistant rendering maps to the pure adapter and trusted template fields.
- Stored-data preservation maps to copied views, unchanged queries, and raw text assertions.
- No-source behavior maps to `render_markdown` without a reference context.
- Conversation hierarchy maps to retained card structure plus compact Markdown overrides.
- Primary and lazy or normalized Subsession parity maps to adapting both event shapes after existing filters.
- Fallback isolation maps to the shared per-message renderer result.
- Responsive containment maps to browser geometry at `1440`, `920`, `700`, and `320`.

## Evaluation Focus

- Confirm only user and assistant message bodies are rendered and tool rows remain absent.
- Confirm every raw event value, source file, count, order, parent, membership, and Search boundary remains unchanged.
- Confirm Session text never gains an owning Local Context source through inference.
- Confirm properties and Markdown remain subordinate to role and timestamp hierarchy.
- Confirm hostile HTML, unsafe links, long code, tables, URLs, math, mixed scripts, empty, and fallback states stay bounded per message.
- Confirm both normalized Subsession detail and lazy compatibility Subsession detail consume the same presentation contract.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-20`: Attempt 1 selects `screen-alignment` extend mode, backend-rendering before frontend-conversation, a pure copied-view adapter, and no client-side navigation change.
