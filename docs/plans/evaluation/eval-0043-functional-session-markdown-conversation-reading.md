# EVAL-0043: Session Markdown Conversation Reading — Functional

## Metadata

- ID: `eval-0043-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260720-48`
- Attempt: `1`
- Feature: [feat-0043-session-markdown-conversation-reading](../feature/feat-0043-session-markdown-conversation-reading.md)
- Spec: [spec-0043-session-markdown-conversation-reading](../spec/spec-0043-session-markdown-conversation-reading.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-rendering`, `frontend-conversation`
- Evidence Coverage: `complete`
- Created: `2026-07-20`

## Scope

- Evaluated normalized and lazy event adaptation, eligible roles, raw preservation, no-source links, unsafe and external links, Markdown states, templates, primary and Subsession routes, hidden events, counts, order, parent context, and responsive containment.

## Checks And Evidence

- The presentation adapter preserves raw text and every available event value while attaching shared rendered output only to string bodies whose role is `user` or `assistant`.
- Normalized Session rows and lazy parsed Subsession events use the same adapter after the existing message-only filters and ordering.
- A synthetic non-eligible message role remained plain and received no rendered field. Tool-only Sessions retained the existing empty conversation while the raw event remained stored.
- Source-relative Markdown links and wikilinks produced the shared `no-source` state. HTTPS links retained explicit external treatment and security relations; unsafe schemes exposed no executable destination.
- A forced renderer failure produced one escaped fallback result without changing the event text or adjacent timeline ownership.
- Primary and Subsession templates share one macro, consume trusted `Markup` without a template `safe` filter, render properties separately, and retain escaped text fallback for non-eligible visible messages.
- Chrome MCP confirmed a primary route with 35 visible user and assistant messages, 35 Markdown bodies, headings, ten code blocks, three tables, role headers, and timestamps; visible tool rows remained zero.
- Chrome MCP confirmed a normalized Subsession route with 44 visible messages, 44 Markdown bodies, parent return and parent notice, role headers, timestamps, and zero tool rows.
- Live external links used `target="_blank"` and `rel="noopener noreferrer external"`; the page contained no image request or prefetch.
- Chrome MCP confirmed no message overflow or page overflow at `1440`, `920`, `700`, and emulated `320`; code and tables remained inside their cards.
- A clean reload reported no console errors, warnings, issues, or failed network requests.
- `uv run --no-sync python -m unittest discover -s tests -v` passed all 170 tests. JavaScript syntax, repository privacy, and diff whitespace checks also passed.

## Evidence Gaps

- None. The live dataset had no unresolved lazy-only Subsession route or empty conversation to open, but the lazy parsed-event adapter, compatibility route/template contract, tool-only empty state, and shared macro are covered by focused synthetic tests and source inspection.

## Findings

- No remaining role, rendering, safety, route, count, hidden-event, parent, containment, or regression defect was found.

## Regression Notes

- Parsing, ingestion, Activity Events, source JSONL, Search, Workstream membership, statistics, and Session inventory behavior were not changed.

## Route

- Next action: release Functional evaluation for FEAT-0043 and Run acceptance.
