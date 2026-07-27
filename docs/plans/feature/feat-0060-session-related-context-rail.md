# FEAT-0060: Session Related Context Rail

## Metadata

- ID: `feat-0060`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Show deterministic context related to the selected Session in a right-side detail rail so context is explained where it is useful instead of appearing as an unrelated global recency feed.

## Acceptance Contract

- Persisted primary Session detail includes a `Related Context` rail built only from existing local database relationships and projections.
- The initial eligible relationship reasons are:
  - `이 Session에서 참조`: a registered Atlassian Item has existing Session evidence;
  - `같은 Thread`: an eligible Document or Resource shares explicit Thread membership;
  - `같은 Workstream`: an eligible Document or Resource shares explicit Workstream membership;
  - `같은 프로젝트`: an enabled Local Context Document resolves to the same `workspace_id`.
- Relationship precedence is Session evidence, Thread, Workstream, then workspace. One target appears once and exposes its strongest reason plus any additional bounded reasons.
- Global modification recency alone never makes an item related.
- Each entry retains its existing title, type, provenance, availability, and destination ownership; content bodies are not copied into Session storage.
- Loading Session detail performs no model call, embedding request, external read, capability inspection, source scan, maintenance Run, or relationship write.
- The read model is deterministic, bounded, deduplicated, and stable for the same database state.
- The rail does not shrink the conversation below a readable width.
- At compact widths it enters document flow after Session identity and orientation and before the long conversation, with keyboard order matching the visual order.
- Empty, partial, unavailable, missing-target, and query-error states remain bounded and do not fall back to recent documents or inferred suggestions.
- No new Session-to-context relationship table is added.

## Scope Boundary

- In:
  - same-workspace enabled Local Context Documents
  - shared explicit Workstream and Thread membership for eligible Documents and Resources
  - registered Atlassian Items with existing Session evidence
  - deterministic reason precedence, deduplication, ordering, and count limits
  - related-context query projection
  - right rail, narrow document-flow placement, provenance, unavailable, empty, and error states
- Out:
  - user-curated Session-to-context relationships
  - accepted inferred relevance or generated Suggestions
  - LLM, embeddings, remote search, hidden synchronization, or source scans
  - global recent Context
  - copying Document or Item content into Session records
  - native Claude or Codex resume
  - pin persistence or Pinned Sessions UI

## Surface Lanes

- Relationship projection lane:
  - path roots: Session queries, Workstream/Thread relationship helpers, Atlassian evidence queries, and focused tests
  - dependencies: current workspace, Workstream, Thread, Local Context, and Atlassian evidence contracts
  - expected evidence: eligibility, precedence, deduplication, deterministic bounds, unavailable behavior, and zero external/model work
  - evaluator ownership: `contract`, `functional`
- Detail route lane:
  - path roots: Session detail route and response context
  - dependencies: relationship projection lane
  - expected evidence: one local read model with bounded errors that cannot block the core conversation
  - evaluator ownership: `contract`, `functional`
- Detail presentation lane:
  - path roots: `templates/session.html`, shared detail/rail styles, client behavior if needed, and UI tests
  - dependencies: route lane and the Design Constitution
  - expected evidence: readable main column, right rail, relationship reasons, provenance, responsive order, focus, empty, and unavailable states
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, data-model, Session reading, and interaction owner docs
  - dependencies: completed read and presentation lanes
  - expected evidence: local projection ownership and explicit non-schema boundary
  - evaluator ownership: `contract`

## Contract Surfaces

- `sessions.workspace_id` and `context_documents.workspace_id`.
- `workstream_links` and `thread_links` polymorphic relationship rules.
- `atlassian_item_evidence.session_id`.
- Related-context projection shape, reason vocabulary, precedence, deduplication, and limits.
- Session detail route context and failure isolation.
- Responsive detail-and-rail layout.

## User-Visible Outcome

- When the owner opens a Session, nearby Local Context, organization links, and Atlassian references appear with an explicit reason they are related, without leaving the conversation or triggering hidden work.

## Entry And Exit

- Entry point: open a persisted primary Session detail route.
- Exit or transition behavior: open one related item at its existing destination or continue reading the Session with the main conversation orientation intact.

## State Expectations

- Populated: deduplicated entries are grouped or ordered by relationship strength with visible reason and provenance.
- Empty: concise local-only explanation; no recent or suggested substitute.
- Partial: available entries render while unavailable targets retain bounded provenance or are excluded according to the fixed Spec rule.
- Error: the conversation remains readable and the rail exposes a bounded local error.
- Narrow: rail content follows Session orientation and precedes the long conversation without focus or width traps.

## Dependencies

- PRD-0009 is `approved`.
- PRD-0002 and PRD-0006 remain passed Session inventory and reading contracts.
- No new foundation schema Feature is required for the initial projection.
- FEAT-0059 may run first to reduce overlapping Session detail changes, but its pin persistence is not a data dependency for this Feature.

## Likely Affected Surfaces

- `src/localbrain/queries.py`
- `src/localbrain/workstreams.py`
- Atlassian evidence query helpers
- `src/localbrain/main.py`
- `src/localbrain/templates/session.html`
- `src/localbrain/static/styles.css`
- Session detail, Workstream/Thread, Atlassian evidence, route, and UI tests
- product, interaction, and data-model owner docs

## Pass Or Fail Checks

- Pass if every item has at least one approved relationship reason and global recency alone returns nothing.
- Pass if one target is deduplicated and reason precedence is deterministic.
- Pass if the same database state produces the same bounded order and result.
- Pass if Session detail causes no external, model, embedding, scan, capability, maintenance, or relationship mutation.
- Pass if main conversation and rail remain readable at `1440`, `920`, `700`, and `320`.
- Pass if empty, partial, unavailable, and error states do not block the Session body.
- Fail on a new relationship table, inferred relevance, hidden work, copied content bodies, unexplained entries, or recency fallback.

## Regression Surfaces

- PRD-0006 Session Markdown conversation reading.
- Session parent/Subsession orientation and direct-link entry.
- Local Context document routes and availability.
- Workstream and Thread polymorphic links.
- Atlassian evidence and Item detail ownership.
- Responsive detail surfaces and repository privacy.

## Harness Trace

- Active spec doc: [spec-0060-session-related-context-rail](../spec/spec-0060-session-related-context-rail.md)
- Active run: [run-20260724-65-session-related-context-rail](../run/run-20260724-65-session-related-context-rail.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [contract](../evaluation/eval-0060-contract-session-related-context-rail.md) — `PASS`
  - [design](../evaluation/eval-0060-design-session-related-context-rail.md) — `PASS`
  - [functional](../evaluation/eval-0060-functional-session-related-context-rail.md) — `PASS`
  - [ux-heuristic](../evaluation/eval-0060-ux-session-related-context-rail.md) — `PASS`
- Latest fix note: not created

## Open Review Decisions

- Closed: emit at most `12` targets after scanning at most `48` candidates from each of Session evidence, shared organization membership, and same-workspace Documents.
- Closed: order by strongest relationship reason, case-insensitive title, target type, and stable target ID.
- Closed: keep resolved missing local paths, archived Atlassian Items, and unsafe external destinations visible with explicit availability; omit malformed or unresolved polymorphic targets and report a bounded count.

## Continuity Notes

- `2026-07-24`: initial draft fixed a local deterministic projection and right-rail boundary without adding a relationship table or relevance service.
- `2026-07-24`: automatically approved for sequential execution under the owner's two-PRD workflow authorization.
- `2026-07-24`: passed with a `12`-item display cap, `48`-candidate per-source scan bounds, evidence-first ordering, visible resolved-unavailable states, isolated query errors, and responsive right-rail/document-flow behavior.
