# SPEC-0074: Session-Centric Related Materials Rail

## Metadata

- ID: `spec-0074`
- Status: `approved`
- Run ID: `run-20260803-84`
- Attempt: `1`
- Parent Feature: [feat-0074-session-centric-related-materials-rail](../feature/feat-0074-session-centric-related-materials-rail.md)
- Parent PRD: [prd-0013-session-centric-related-context-evidence](../prd/prd-0013-session-centric-related-context-evidence.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: read model → route → presentation → durable contracts
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Source Set

- Human-approved PRD-0013 and FEAT-0074, including the independent 10-item
  initial display decision.
- Passed FEAT-0072 evidence ownership and FEAT-0073 bounded Session reference
  projection.
- Existing primary Session detail route, Related Context projection/template,
  Session detail responsive layout, and explicit Thread/Workstream relations.
- Agent Workflow, Fullstack Product profile, Design Constitution, Design
  Evaluation, Interaction Evaluation, Product, Architecture, and Data Model
  owner documents.

## Implementation Goal

- Replace the ambient flat Related Context rail with a bounded local `관련 자료`
  read model that gives direct Session evidence priority and exposes only
  explicitly shared work organization after it.

## Lane Order And Handoffs

1. Read model composes FEAT-0073 direct evidence with eligible explicit
   Thread/Workstream Documents and Resources, removes ambient workspace
   candidates, deduplicates by stable target, and returns independent groups.
2. Route loads that projection for primary Sessions only and isolates local
   SQLite failures from the conversation surface.
3. Presentation renders the two approved groups, truthful states, independent
   totals, and native keyboard-operable overflow disclosure after item 10.
4. Durable contract owners are revised to describe the new projection without
   rewriting FEAT-0060 historical evidence.

## In-Scope Behavior

- `이 세션의 참조` consumes `session_reference_projection` and uses its
  Session-observed identity, safe destination, evidence kind/outcome, total,
  partial, and stale state.
- Direct evidence labels are exactly `MCP 조회`, `MCP 조회 실패`, `사용자
  메시지에서 언급`, `Agent 응답에서 언급`, and `도구 결과에서 확인`.
  Successful reads suppress failure-only presentation for the same target.
- `연결된 작업` contains only enabled Documents or Resources linked through a
  Thread/Workstream explicitly shared with the Session. Thread reasons sort
  before Workstream reasons. Same workspace/path/repository and global recency
  never generate candidates or counts.
- A target present in both groups remains only in the direct group. Its
  organization relationship may be retained as a concise secondary reason on
  that direct row without changing direct ordering or count.
- Each group returns all retained eligible items, an independent total, the
  first 10-item slice, and overflow count. The template keeps the first 10
  visible and places the remainder in a native reversible disclosure labelled
  `N개 더 보기`.
- Direct ordering is successful read, failure-only read, tool-result
  observation, user mention, then Agent mention, followed by deterministic
  normalized source occurrence and target identity supplied by FEAT-0073.
  Organization ordering is Thread then Workstream and stable target identity.
- Unavailable, archived, unsafe, partial, and stale states remain explicit in
  text. A direct 100-target partial result reports observed and retained totals;
  an error reports that prior evidence may be stale. Organization candidate
  query limits report their own bounded partial state.
- Local Context Documents retain `/documents/{id}`, Atlassian Items retain
  `/atlassian/items/{id}`, local Resources retain their owned route, and only
  safe HTTP(S) destinations open externally with `noopener noreferrer`.
- The primary Session rail heading is `관련 자료` with exactly the eligible
  groups `이 세션의 참조` and `연결된 작업`. Empty groups do not invent
  fallback content; the rail retains a concise overall empty state when both
  groups are empty.
- Subsession detail receives no rail and primary detail does not load or merge
  child evidence.
- Detail opening performs bounded SQLite reads only. It performs no JSONL/file
  read, source scan, relationship mutation, external/MCP/model/embedding work,
  or maintenance Run.
- Presentation extends the existing Session detail rail and semantic tokens.
  At `920px` and below, DOM and visual order remain identity/orientation →
  related materials → conversation. At `700px` and `320px`, identities,
  destinations, state text, and disclosure controls wrap without horizontal
  overflow or focus traps.

## Out-Of-Scope Behavior

- Same-workspace/path/repository candidates, inferred relevance, recent context,
  semantic ranking, manual ordering, relationship editing, remote refresh,
  exact `대화에서 보기`, Subsession rail, or child evidence roll-up.

## Affected Surfaces

- `src/localbrain/session_context.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/session.html`
- `src/localbrain/templates/_session_related_context.html`
- `src/localbrain/static/styles.css`
- Session related-context/reference, route, rendered UI, responsive, and
  interaction contract tests
- Product, Architecture, Design, Interaction, and Data Model owner documents

## State And Interaction Contract

- Ready: one or both groups show independent totals and at most 10 initial rows.
- Expanded: native disclosure reveals only the owning group's retained remainder
  and can collapse without navigation or focus loss.
- Empty: no direct or explicit organization material; no ambient fallback.
- Failure-only: the row says `MCP 조회 실패` and never implies remote content.
- Partial: the group states observed versus retained scope or bounded candidate
  limits without presenting retained rows as complete.
- Stale/error: evidence remains visibly qualified or rail failure remains local;
  conversation reading continues.
- Unsafe/missing/archived: the row remains present, destination affordance and
  text match actual availability, and color is not the only cue.

## Contract Surfaces

- FEAT-0073 direct reference projection as producer.
- Explicit Thread/Workstream relationship projection.
- Stable target deduplication and strongest-group precedence.
- Two-group vocabulary, evidence labels, order, totals, initial-10 disclosure,
  partial/stale/error states, and owned destinations.
- Primary-only route and zero-hidden-I/O boundary.
- Responsive layout, semantic token use, keyboard disclosure, focus, and
  long-string containment.

## Required Evaluators

- Contract: group eligibility, deduplication, evidence vocabulary, destination
  ownership, route isolation, primary/Subsession boundary, hidden-I/O boundary,
  and durable owner docs.
- Design: existing Session detail hierarchy, calm rail density, semantic-token
  use, independent groups, 10-item simplification, responsive order, and
  long-string containment at `1440`, `920`, `700`, and `320`.
- Functional: direct evidence states, explicit organization, ambient exclusion,
  counts/disclosure, partial/stale/error paths, route continuation, safe links,
  and regressions.
- UX Heuristic: relationship clarity, truthful labels, disclosure discoverability
  and reversibility, keyboard/focus order, and conversation continuity.

## Acceptance Mapping

- Session-centric evidence → direct projection supplies observed identity and
  approved evidence summaries.
- No ambient context → membership query has no workspace/recent candidate lane.
- Strongest-group uniqueness → target-key dedup removes organization duplicates.
- Bounded calm display → independent totals plus first 10 and native disclosure.
- Truthful incomplete state → explicit partial/stale/error and availability copy.
- Reading continuity → primary-only local route isolation and established
  responsive DOM order.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-03`: Spec Agent selected native disclosure because it preserves
  keyboard operation and collapse behavior without adding a client-side state
  owner or hidden JavaScript dependency.
