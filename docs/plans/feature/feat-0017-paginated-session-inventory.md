# FEAT-0017: Paginated Session Inventory

## Metadata

- ID: `feat-0017`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Created: `2026-07-17`
- Updated: `2026-07-27`

## Goal

- Let the user review top-level Sessions in stable 15-item pages, scan concise path and activity metadata, and open available subsessions from a conditional row-owned dropdown.

## Acceptance Contract

- One page contains at most 15 top-level Sessions after source, workspace, classification, and unresolved-parent rules are applied.
- Pagination communicates the current page, total result scope, compact numbered destinations with ellipses, and valid previous or next movement while preserving Claude or Codex and workspace filters.
- A filter or scope change that invalidates the current page resolves to a valid page instead of producing a misleading empty result.
- Every row preserves `CL` or `CX` provenance with an accessible full source label and shows local path, optional normalized branch, question count, total event count, and last activity.
- Visible `Claude` or `Codex` metadata text is removed when it only duplicates the row's source mark.
- A separate right-edge dropdown trigger exists only for top-level Sessions with displayable subsessions.
- The dropdown includes only direct children of that top-level Session. It does not flatten or expose descendants whose parent is itself a subsession.
- The dropdown exposes valid child destinations without nesting an interactive control inside the row's Session-detail link.
- The dropdown supplements rather than replaces the parent Session detail's Subsessions section.
- A scrolling child list is contained inside a non-scrolling overlay shell so the dropdown's solid border and rounded corners remain intact.
- Hover or focus-within feedback spans the complete Session row, including the right disclosure cell, without merging the sibling navigation and disclosure targets.
- Unresolved-parent subsessions are absent from inventory, counts, dropdowns, and direct user-facing detail lookup.
- Existing source and workspace filters, missing-path treatment, Session detail destinations, recent Local Context section, and source status section remain behaviorally intact unless separately approved.

## Scope Boundary

- In:
  - 15-item server-backed top-level Session pages
  - total result and page-boundary read model
  - page navigation with source and workspace scope preservation
  - concise Session row metadata hierarchy
  - accessible provenance after visible source-name deduplication
  - conditional right-edge subsession dropdown
  - valid child destination links and unresolved-parent exclusion
  - responsive pagination, row, and dropdown states
- Out:
  - configurable page size, infinite scroll, new sorting, bulk actions, or Session editing
  - parent/subsession source inference or schema ownership from `feat-0015`
  - global Search, Sessions Dashboard, or activity-metric policy changes
  - Session detail timeline filtering from `feat-0018`
  - removal or replacement of the parent Session detail Subsessions section
  - redefining or associating the existing recent Local Context section with files changed by a Session
  - Project inventory aggregation changes

## Surface Lanes

- Backend and read-model lane:
  - path roots: `src/localbrain/queries.py`, `src/localbrain/main.py`
  - dependencies: `feat-0015` passed
  - expected evidence: filtered top-level total, deterministic page bounds, 15-item slice, child availability, valid child destinations, and unresolved-parent exclusion
  - evaluator ownership: `contract`, `functional`
- Frontend and interaction lane:
  - path roots: `src/localbrain/templates/sessions.html`, `src/localbrain/static/styles.css`, `src/localbrain/static/app.js`
  - dependencies: backend lane and `feat-0016` passed
  - expected evidence: row metadata, separate detail and dropdown affordances, keyboard disclosure, dismissal, focus, pagination continuity, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- `/sessions` source, workspace, and page query state
- top-level result-count and 15-item page read model
- invalid, negative, missing, and out-of-range page behavior
- Session row provenance, path, branch, question, event, and time fields
- per-parent subsession count and child destination shape
- direct-child-only predicate based on the normalized parent relation
- parentless and non-displayable Session lookup predicate
- pagination, row link, and dropdown focus ownership

## Required Evaluators

- `contract`: page query and count semantics, filter preservation, child relation consumption, lookup gating, and producer/consumer shape.
- `design`: metadata hierarchy, source mark, right-edge control, dropdown placement, pagination separation, long content, and responsive containment.
- `functional`: page movement, invalid page recovery, filters, row links, child links, dropdown state, keyboard behavior, and no-child rows.
- `ux-heuristic`: occasional-review scan efficiency, affordance clarity, repeated pagination reach, and disclosure friction.

## User-Visible Outcome

- The user can review Sessions 15 at a time, understand where and on which branch work occurred, and inspect child runs without top-level subsession noise.

## Entry And Exit

- Entry point: the Sessions mode from persistent navigation, direct `/sessions`, a Project row, or an existing workspace-filtered Session link.
- Exit or transition behavior: row identity opens the parent detail; the separate dropdown opens child choices; pagination and filters stay in the Sessions inventory scope.

## State Expectations

- Default: first 15 top-level Sessions in descending recent-activity order.
- Filtered: page count and items reflect only the selected source and workspace scope.
- Parent with children: right-edge dropdown trigger and child count or accessible label are available.
- Nested descendants: preserved deeper subsessions do not appear in the top-level row dropdown, its child count, or user-facing inventory results.
- Parent without children: no empty, disabled, or placeholder dropdown trigger is rendered.
- Unresolved parent: the child is absent from user-facing results and counts.
- Empty data: explain that no Sessions exist.
- No filter match: distinguish the active filter from an empty source.
- Short final page: pagination remains close enough for repeated navigation and does not imply missing results.
- Invalid page: resolve to a valid bounded page with consistent URL and selected filters.
- Narrow viewport: essential identity, path, counts, time, and dropdown access remain available after secondary layout simplification; at most five numbered or ellipsis tokens remain centered above symmetric previous/next controls without horizontal overflow.

## Dependencies

- `feat-0015` must be `passed` before this Feature enters build.
- `feat-0016` must be `passed` so the inventory renders within the approved combined Sessions destination.

## Likely Affected Surfaces

- `src/localbrain/queries.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/sessions.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- query, route, UI contract, and browser-level interaction tests
- synthetic Claude, Codex, parent, child, unresolved-parent, branch, long-path, and multi-page fixtures

## Pass Or Fail Checks

- Pass if every page returns at most 15 eligible top-level Sessions and total pages match the filtered count.
- Pass if source and workspace filters survive previous and next navigation and invalid pages resolve predictably.
- Pass if subsessions never consume one of the 15 top-level slots.
- Pass if visible Session rows show path, optional branch, question count, total event count, and time without redundant visible source-name text.
- Pass if the source mark has an accessible full Claude or Codex label.
- Pass if only rows with valid children expose a separately operable dropdown and every child destination retains parent orientation.
- Pass if a top-level Session dropdown and child count contain only direct children and never flatten a grandchild or deeper descendant.
- Pass if pointer, keyboard, focus, outside dismissal, Escape dismissal, and dropdown selection work without triggering the parent row destination accidentally.
- Pass if parentless children are absent from inventory, counts, dropdowns, and user-facing detail lookup.
- Pass if synthetic evidence covers required empty, filtered, paged, long-content, missing-path, open-dropdown, no-child, and narrow states.
- Fail if pagination counts raw subsessions, if row and dropdown targets overlap, or if recent Local Context is represented as Session-changed files.

## Regression Surfaces

- Claude and Codex source filters
- `/sessions?workspace=<id>` Project transitions
- existing Session detail, Workstream membership, and Search destinations
- parent Session detail Subsessions access
- source status and recent Local Context sections
- missing and historical path presentation
- shell, combined Sessions/Projects mode, global search, and narrow navigation

## Feature Review Questions

- None. Global Search and statistics exclusion is owned and passed through `feat-0015`; this Feature consumes only the top-level and direct-child inventory contract.

## Harness Trace

- Active spec doc: [spec-0017-paginated-session-inventory](../spec/spec-0017-paginated-session-inventory.md)
- Active run: [run-20260717-17-paginated-session-inventory](../run/run-20260717-17-paginated-session-inventory.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract attempt 4](../evaluation/eval-0017-contract-responsive-page-size-attempt-4.md), [design attempt 4](../evaluation/eval-0017-design-responsive-page-size-attempt-4.md), [functional attempt 4](../evaluation/eval-0017-functional-responsive-page-size-attempt-4.md), [ux heuristic attempt 4](../evaluation/eval-0017-ux-responsive-page-size-attempt-4.md)
- Latest fix note: [fix-0017-fifteen-item-responsive-pagination](../fix/fix-0017-fifteen-item-responsive-pagination.md)

## Continuity Notes

- `2026-07-17`: initial draft joined pagination, row metadata, and row-owned child disclosure because they share one filtered Session inventory read model and interaction surface.
- `2026-07-17`: human review fixed the dropdown and child count at one direct-child depth; nested descendants remain preserved but are not flattened into the inventory.
- `2026-07-17`: entered sequential fullstack execution after FEAT-0015 and FEAT-0016 passed; screen-alignment mode is `extend`.
- `2026-07-17`: passed after 20-item query, direct-child disclosure, canonical page recovery, responsive browser checks, and the full 32-test suite completed without a blocking finding.
- `2026-07-17`: actual-runtime evidence invalidated the initial pass because a pre-change Python process loaded the new template without its new context. Attempt 2 passed after the compatibility fallback, controlled restart, actual schema migration, real page checks, and 38-test regression.
- `2026-07-17`: Attempt 3 passed after human runtime feedback added compact numbered page reach, preserved scroll-overlay boundaries, unified row hover feedback, symmetric 320px pagination, actual route verification, and a complete 40-test regression.
- `2026-07-17`: Attempt 4 passed after the default slice changed to 15 and viewport-specific page models limited desktop to seven and narrow screens to five tokens.
- `2026-07-19`: post-run human review aligned the preserved parent-detail child label with the source-neutral `Subsession` product term.
- `2026-07-27`: owner follow-up kept hover shading only for unselected page destinations and reduced the current-page treatment to the bold number without a square background.
