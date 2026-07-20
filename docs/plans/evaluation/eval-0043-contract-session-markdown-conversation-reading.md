# EVAL-0043: Session Markdown Conversation Reading — Contract

## Metadata

- ID: `eval-0043-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260720-48`
- Attempt: `1`
- Feature: [feat-0043-session-markdown-conversation-reading](../feature/feat-0043-session-markdown-conversation-reading.md)
- Spec: [spec-0043-session-markdown-conversation-reading](../spec/spec-0043-session-markdown-conversation-reading.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-rendering`
- Evidence Coverage: `complete`
- Created: `2026-07-20`

## Scope

- Evaluated eligible-role ownership, copied derived output, normalized and lazy event parity, no-source reference behavior, raw event preservation, order, counts, hidden-event boundaries, and independent renderer fallback.

## Producer And Consumer Evidence

- `conversation_event_view` copies every available SQLite row key or parsed event attribute before adding presentation-only fields.
- Only `user` and `assistant` roles with string text call `render_markdown`; another role receives no rendered field and retains escaped plain-text eligibility.
- The renderer is called without a `MarkdownReferenceContext`. Relative links and wikilinks therefore use the shared `no-source` state instead of searching Local Context Documents.
- Raw `text`, sequence, timestamps, role, source line, event type, and identifiers remain present and unchanged in the copied view.
- The existing `session_conversation_events` query and lazy Subsession `event_type == message` filter and sequence sort remain authoritative. Rendering runs only after those selections.
- Tool calls, source JSONL, normalized Activity Events, Session counts, Search ownership, parent relations, and memberships are not read or written by the adapter.
- The shared renderer converts one failure into an escaped `fallback` result, so adjacent messages and the conversation query are unaffected.

## Verification

- `uv run --no-sync python -m unittest tests.test_session_details -v` — 6 tests passed.
- Synthetic evidence covers normalized SQLite rows, lazy parsed events, raw-value and count preservation, eligible roles, a non-eligible role, no-source internal links, external and unsafe links, ordering, tool-only empty conversation, and isolated renderer failure.
- Post-contract verification passed all 170 repository tests after both template consumers were complete.

## Evidence Gaps

- None for the backend-rendering producer contract. Template hierarchy and rendered browser containment remain owned by downstream evaluators.

## Findings

- No implementation bug, source-ownership ambiguity, mutation path, hidden-event regression, or stale contract was found.

## Route

- Next action: `pass`; release the frontend-conversation lane.
