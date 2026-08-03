# SPEC-0069: Session Source Scope And Provenance

## Metadata

- ID: `spec-0069`
- Status: `superseded`
- Run ID: `run-20260802-74`
- Attempt: `1`
- Parent Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: query/route → inventory presentation → detail presentation → docs
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- FEAT-0069, PRD-0012, and passed FEAT-0068 contracts.
- Current Session inventory, pagination, Projects, pins, detail, parent and
  Subsession query/routes/templates/client behavior.
- Design Constitution, Design Evaluation, Interaction Evaluation, Session owner
  docs, and source value dictionary.

## Implementation Goal

- Make stable registered Source keys the one Sessions browsing scope while
  exposing readable Source labels on every Session-oriented projection.

## Lane Order And Handoffs

1. Query/route owns eligible-primary-work filtering, registry-derived options,
   valid key normalization, selected counts, Project/workspace combinations, and
   detail return scope.
2. Inventory presentation consumes those options and projections without
   hard-coded source tabs or provider-level filtering.
3. Detail presentation consumes the same provenance and navigation scope for
   primary, parent, normalized child, and lazy Claude child views.
4. Docs reconcile the denominator, source scope, and readable provenance owner.

## In-Scope Behavior

- Add a registry query that returns local AI Session source key, provider kind,
  display label, and eligible-primary-work count in stable Source-ID order. It
  excludes Local Context without enumerating user-facing Claude/Codex keys.
- Sessions accepts `source=all` or one returned stable key. Unknown keys redirect
  to normalized all-source page 1 while retaining a valid workspace parameter.
- Source controls render `전체` followed by every registry option. Their GET links
  omit `page`, preserve workspace, and therefore start the new scope at page 1.
- Session inventory filters by `sources.kind`, never provider kind. Personal
  Codex and Codex Company are exact, disjoint scopes; all is their union with all
  other registered Session sources.
- `dashboard_stats` accepts an optional source key and applies it to visible
  Session-derived metrics. The selected headline label names its source. Project
  activity accepts the same key and excludes unrelated workspaces when scoped.
- The shared denominator remains `session_class = work` plus
  `session_role = primary`, with no timestamp predicate, across scope option
  counts, headline, pagination, inventory, source cards, and Project session
  aggregates.
- Inventory rows use provider kind only for the compact visual cue and display
  `source_name` as readable provenance. Subsession disclosure rows repeat the
  readable source label.
- Pinned Sessions remain global uncapped recall but show readable source label and
  provider cue for every row.
- Inventory detail links carry valid source/workspace orientation. Detail
  backlinks, parent links, normalized/lazy child links, and pin return URLs retain
  that orientation. Unknown detail scope falls back to all.
- Primary detail, normalized Subsession detail, child lists, parent notice, and
  lazy Claude Subsession detail expose readable source label.
- Existing pin eligibility, pagination size, Maintenance exclusion, parent
  integrity, conversation rendering, and source health remain unchanged.

## Out-Of-Scope Behavior

- Usage Dashboard source controls or composition (FEAT-0070).
- Combined-Codex tab, source settings editing, source removal, retention, parser,
  Usage normalization, Maintenance, Subsession, or pin policy changes.
- New source badge colors for roots sharing an existing provider.

## State And Interaction Contract

- Default/invalid: all-source option is selected; invalid source URL is removed by
  bounded redirect instead of creating a phantom empty tab.
- Selected: option, headline, rows, pagination, and Project results agree on one
  stable source key.
- Transition: source links preserve workspace and reset page; ordinary browser
  back/forward restores GET state without client-owned duplicate state.
- Empty: copy names the selected source and suggests changing source/project,
  without implying disablement or deletion.
- Detail: inventory orientation survives row, parent, child, pin, and list-back
  navigation when supplied; direct detail entry remains valid under all.
- Responsive: the peer source control may wrap/scroll within its existing control
  family; provenance text truncates or wraps within rows at 1440/920/700/320 and
  never relies on color/initials alone.

## Contract Surfaces

- `source` GET normalization and stable-key option projection
- eligible-primary-work denominator and source-filtered query parameters
- Session inventory/detail/parent/Subsession/pin provenance fields
- scoped detail/list URL composition
- visible source label and provider-cue semantics

## Acceptance Mapping

- Peer scopes → registry-derived options plus exact `sources.kind` filter.
- Aggregate parity/no age cutoff → shared denominator queries and synthetic old
  Sessions across three Sources.
- Transition continuity → source links omit page and preserve workspace; detail
  query orientation propagates through navigation.
- Readable provenance → visible labels on inventory, pinned, child, and detail
  surfaces with provider cue separate.
- Regression preservation → existing pagination, Projects, pins, parent/lazy
  child, conversation, sync, health, and privacy suites.

## Evaluation Focus

- Exact all/personal/company set membership and aggregate sum.
- Unknown key, source+workspace, page reset, bounded page, and direct detail URLs.
- Primary/Maintenance/Subsession denominator invariants and old-date inclusion.
- Visible personal/company Codex distinction without color-only semantics.
- Row/detail containment and control reachability at 1440/920/700/320.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: superseded for ordinary Session inventory-card presentation by
  [SPEC-0069-r2](spec-0069-r2-session-list-source-cues.md) after owner review.
  Its source scope, query, pinned, Subsession, and detail contracts remain the
  implementation basis where SPEC-0069-r2 does not override them.
