# EVAL-0018: Conversation-Focused Session Details Contract

## Metadata

- ID: `eval-0018-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260717-18`
- Attempt: `1`
- Feature: [feat-0018-conversation-focused-session-details](../feature/feat-0018-conversation-focused-session-details.md)
- Spec: [spec-0018-conversation-focused-session-details](../spec/spec-0018-conversation-focused-session-details.md)
- Execution Profile: `fullstack-product`
- Surface Lane: detail presentation read model and route identity
- Created: `2026-07-17`

## Contract Evidence

- `session_conversation_events` selects only normalized `message` rows in source sequence. The raw `session_events` API, Activity Event rows, tool names, source JSONL, and Session `event_count` remain unchanged.
- Filtering is based on `event_type`, so user and assistant text containing `Bash`, `exec`, or `Write` remains visible.
- `session_parent` admits only a same-source `work` direct child of a primary Session. `session_subsessions` returns only same-source `work` direct children owned by a primary Session.
- Existing Session lookup continues to reject grandchildren, unresolved children, and cross-source relations.
- Claude subagent filename identity remains distinct from a record-level parent `sessionId`, preventing a child import from colliding with its parent identity.
- Legacy Claude paths verify the source-derived parent identity, redirect an already normalized child to `/sessions/{child_id}`, and otherwise use the same message-only fallback presentation.

## Automated Evidence

- Mixed-message, tool-only, parent, direct-child, grandchild, and raw-row preservation tests passed.
- The complete 38-test suite passed, including stable-ID and curated-link preservation when an existing primary row is reclassified as a subsession and the pre-restart template-context regression.

## Findings And Regression

- No blocking contract finding.
- Workstream membership, raw event ownership, and primary-only statistics remain unchanged.

## Route

- Next action: `pass`
