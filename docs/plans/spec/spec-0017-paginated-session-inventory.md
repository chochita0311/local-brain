# SPEC-0017: Paginated Session Inventory

## Metadata

- ID: `spec-0017`
- Status: `approved`
- Run ID: `run-20260717-17`
- Attempt: `4`
- Parent Feature: [feat-0017-paginated-session-inventory](../feature/feat-0017-paginated-session-inventory.md)
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: backend read model → frontend inventory and disclosure → route/interaction integration
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-17`
- Updated: `2026-07-19`

## Source Set

- Human request: show Sessions 15 at a time, use responsive compact numbered pagination, remove redundant source text, display local path/branch/questions/events, and expose child Sessions through a conditional right-edge dropdown while retaining the detail Subsessions section.
- Passed FEAT-0015 hierarchy contract and FEAT-0016 combined destination.
- Current rendered Session inventory, Product Model, Design Constitution, Design Evaluation, and Interaction Evaluation.
- screen-alignment `extend` mode using the existing browse and inventory family.

## Implementation Goal

- Produce one deterministic primary-Session page model and render concise, separately operable parent links, direct-child disclosure, and filter-preserving page controls.

## In-Scope Behavior

- Count and page only `work` Sessions with `session_role = 'primary'`, after source and workspace filters.
- Sort by `COALESCE(last_event_at, started_at) DESC, sessions.id DESC`, use a fixed page size of 15, and derive a minimum one-page boundary for empty results.
- Parse page input defensively. Missing means page 1; nonnumeric, zero, negative, and out-of-range values redirect to the canonical valid page while preserving valid source/workspace filters.
- Fetch displayable direct children only for parent IDs on the current page.
- Render each row as a parent detail link plus an independent disclosure control only when direct children exist.
- Remove visible source name text while retaining CL/CX and an accessible full source name.
- Show canonical local path, optional per-Session branch, question and event counts, and last activity.
- Add pagination status, desktop page-number destinations capped at seven tokens, narrow destinations capped at five tokens, and previous/next destinations below the Session list while retaining the fixed LIMIT/OFFSET query.
- Keep overlay framing on the outer subsession panel and scrolling on its inner child list so scrollbars cannot erase the border or rounded corners.
- Apply row-level hover and focus-within feedback across the parent-link and disclosure columns while retaining independent sibling controls.
- Support pointer and keyboard toggle, outside click, Escape, selection dismissal, and one-open-disclosure behavior.

## Out-Of-Scope Behavior

- Page-size selection, sorting controls, infinite scroll, nested hierarchy, detail event filtering, Project aggregation, Search/statistics policy, or changes to parent detail Subsessions.

## Affected Surfaces

- `src/localbrain/queries.py`, `main.py`
- `/sessions` page/source/workspace query contract
- `src/localbrain/templates/sessions.html`
- `src/localbrain/static/styles.css`, `app.js`
- query and UI contract tests plus local browser evidence

## Surface Lanes

- Backend/read-model lane:
  - dependency order: first
  - responsibility: primary count, bounded page, deterministic order, direct-child map, canonical page metadata
  - validation evidence: synthetic 47-parent, child, grandchild, orphan, source, workspace, and boundary tests
  - evaluators: Contract, Functional
- Frontend/interaction lane:
  - dependency order: backend contract passed locally
  - responsibility: metadata hierarchy, independent row and disclosure targets, dropdown and pagination presentation
  - validation evidence: template/UI tests and 1440/920/700/320 rendered states
  - evaluators: Design, Functional, UX
- Route/integration lane:
  - dependency order: both prior lanes
  - responsibility: parsing, canonical redirect, filter preservation, direct destinations, combined-view continuity
  - validation evidence: local HTTP and browser navigation
  - evaluators: Contract, Functional

## State And Interaction Contract

- Page 1 is the default and no more than 15 parent rows render.
- Empty unfiltered data explains that no Sessions are indexed; filtered zero results explain that the active scope has no match.
- The page footer always reports the filtered total and page position. It renders every page for small result sets and first/last/current-adjacent destinations separated by ellipses for large result sets. Previous/next are links only when valid and otherwise render as labeled unavailable controls.
- Source/workspace filter links reset page to 1. Pagination preserves those filters.
- Parent title/content link and child disclosure button are sibling interactive regions and never nest.
- A trigger uses `aria-expanded` and `aria-controls`; its panel starts hidden and contains normal child detail links.
- Opening one panel closes another. Trigger repeat, outside pointer, Escape, or selecting a child closes it; Escape restores trigger focus.
- The downward cue does not reverse direction when open.
- Narrow rows preserve source mark, title, path, child trigger, time, and count metadata without horizontal overflow. At 320px, at most five page tokens occupy a centered row above previous/next controls.

## Data And Contract Assumptions

- `session_inventory_page` returns `items`, `total`, `page`, `page_size`, `total_pages`, desktop `page_items`, narrow `compact_page_items`, `previous_page`, and `next_page`; both page arrays use `None` only as an ellipsis marker.
- Every item carries a `subsessions` list built by `child.parent_session_id = parent.id`, child `session_role = 'subsession'`, both rows `session_class = 'work'`, parent role primary, and same source identity.
- Grandchildren fail the current-page parent-ID predicate and unresolved children have no parent ID, so neither can appear.
- Child links use the existing display-gated `/sessions/{id}` route.

## Contract Surfaces

- Producer expectations: query layer owns filtered count, bounded page, and direct-child shape.
- Consumer expectations: route redirects invalid page state and template treats only returned children as displayable.
- Source-of-truth owner: FEAT-0015 Session relation and the canonical route query.
- Stale-assumption check: direct calls to `recent_sessions` from the inventory route and whole-row anchor styling are removed; other primary consumers remain unchanged.

## Required Evaluators

- Contract: primary-only total/slice, canonical page state, filters, direct-child predicate, and lookup gating.
- Design: scan hierarchy, separate affordances, dropdown attachment, pagination row, long content, open state, and viewports.
- Functional: all page boundaries, filters, redirects, row/child navigation, keyboard/outside/Escape behavior, and combined-view history.
- UX heuristic: occasional-review efficiency, page reach, disclosure clarity, no-child silence, and repeated navigation reach.

## Acceptance Mapping

- Fixed 15-item pages map to the read-model `LIMIT/OFFSET` contract.
- Filter-preserving movement and invalid recovery map to route parsing and canonical redirects.
- Concise metadata maps to the row template and accessible provenance label.
- One-depth child disclosure maps to the same-source parent FK query and sibling interaction structure.
- Parent detail preservation maps to no changes in the current detail Subsessions presentation path.

## Evaluation Focus

- Verify child rows do not consume parent page slots.
- Verify stale Search rows or orphan identities cannot affect inventory count or disclosure.
- Inspect 15-row and short-final-page footer reach, long path/title/branch containment, open dropdown attachment, and no-child row geometry.
- Confirm source/status side content and combined Sessions/Projects switching still work after pagination.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-17`: approved for sequential execution after FEAT-0015 and FEAT-0016 passed; screen-alignment mode is `extend`.
- `2026-07-17`: Attempt 3 revised only the approved pagination and disclosure presentation contract; the 20-item LIMIT/OFFSET semantics and one-depth relation remained unchanged.
- `2026-07-17`: Attempt 4 changed the approved page size to 15 and split desktop and narrow page-item arrays while retaining LIMIT/OFFSET, filters, and one-depth relation semantics.
- `2026-07-19`: post-run human review aligned the preserved parent-detail child label with the source-neutral `Subsession` product term.
