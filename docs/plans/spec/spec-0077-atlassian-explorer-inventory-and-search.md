# SPEC-0077: Atlassian Explorer Inventory And Search

## Metadata

- ID: `spec-0077`
- Status: `approved`
- Run ID: `run-20260829-87`
- Attempt: `1`
- Parent Feature: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
- Parent PRD: [PRD-0014](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `read-model -> route/shell -> presentation -> docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Source Set

- Human decision: approve the proposed Features sequentially and continue to
  completion.
- Parent Feature and PRD: FEAT-0077 and PRD-0014.
- Passed foundations: FEAT-0075 Explorer/state contract and FEAT-0076 exact
  retrieval contract.
- Golden runtime sources: the current Local Context Explorer family, shared
  shell, Atlassian Browse/detail routes, local Atlassian read model, and
  synthetic tests.
- Durable baselines: Design Constitution, Product Model, Atlassian Source
  Memory, Design Evaluation, and Interaction Evaluation.
- Alignment skill: `screen-alignment` in `extend` mode.

## Implementation Goal

- Replace the Atlassian Browse selector matrix with one responsive local
  Explorer whose service, structural scope, exact query, optional advanced
  filters, and full-detail return path are deterministic and URL-backed.

## In-Scope Behavior

- Normalize omitted or invalid `view` to presentation scope `all`; accept
  `all`, `jira`, and `wiki`, and retain `confluence` only as an inbound
  compatibility alias for `wiki`.
- Map `all` to no stored-service constraint, `jira` to stored `jira`, and
  `wiki` to stored `confluence`. Never coerce `all` to Jira.
- Render one All/Jira/Wiki segmented service control, one Atlassian-local exact
  query, a bounded Filters disclosure, current Refresh, and a functional Add
  link to the existing setup path until FEAT-0079.
- Hide the shared global query whenever `active_page == 'atlassian'` while
  retaining its header grid column and the Search destination so shell
  geometry and navigation continuity remain stable.
- Consume FEAT-0076 ordered exact results directly. Empty query retains the
  existing stable local inventory order; no fuzzy, token-AND, AI, provider, or
  remote fallback is available from this surface.
- Build hierarchy counts from the same service/query/advanced-filter eligible
  Item population as the list, before the current structural constraint is
  applied. Group eligible Items by Service only in All scope, then normalized
  Site, then Space/project, plus Site-local `Unclassified` for null Space.
- Include only hierarchy nodes backed by at least one eligible Item. Root and
  node counts exclude archived Items by default and honor explicit archived or
  all-attention filters exactly as the adjacent list does.
- Treat a selected Site as all eligible Items at that Site, a selected Space
  as the Site/Space intersection, and selected Unclassified as the Site/null-
  Space intersection. Explorer structural URL state always includes an
  explicit service;
  Site/Space/Unclassified destinations selected from combined All enter their
  Jira or Wiki branch, and ambiguous direct All-plus-structure inputs are
  rejected. `Unclassified` additionally requires its Site. The active node
  count must equal `matching_count`, including when one canonical Site owns
  Items from both services. A Site or Space known only to another service is
  rejected for the selected Explorer service instead of being labeled active.
  This Explorer route rule does not change the shared global Search contract,
  where Site and Space remain independently selectable diagnostic filters.
- Service changes preserve query and compatible advanced filters and reset
  Site/Space/Unclassified. Structure changes preserve service, query, and
  advanced filters. Query/filter submissions preserve service and structure.
- Keep Coverage, Freshness, Attention, Topic, Tag, and Workstream in one native
  disclosure. Remove Source Instance, Site, Space, and Item type selectors
  from that disclosure. Show an explicit active-filter count/summary, a clear-
  advanced-filters action that preserves query/structure, and a full reset.
- Project compact linked rows with stable title/key, service, Site/Space or
  Unclassified, useful coverage/freshness/attention cues, and a bounded exact
  match excerpt when a query exists. Duplicate keys remain distinguishable by
  Site context.
- Give each row an ordinary server-executable full-detail link carrying a
  local `return_to` inventory URL. Accept return paths only when scheme and
  authority are absent and the path is exactly `/atlassian`; otherwise fall
  back to `/atlassian`.
- On wide layouts keep a persistent hierarchy beside the list. At compact and
  narrow widths hide the persistent rail and expose the same hierarchy in a
  native disclosure before the list; the list stays the primary visible task
  and advanced filters never become an always-expanded gate.

## Out-Of-Scope Behavior

- Adjacent or asynchronous Item detail, selection history, and detail panes
  owned by FEAT-0078.
- One-URL Add reframe and Connections separation owned by FEAT-0079.
- Evidence Sync owned by FEAT-0080.
- AI retrieval, embeddings, model calls, nested Page/issue hierarchy, schema
  changes, source-body ownership changes, or remote Refresh changes.
- Relabeling or changing the historical global Search Atlassian adapter.

## Affected Surfaces

- `src/localbrain/atlassian_browse.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/base.html`
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/templates/atlassian-item.html`
- `src/localbrain/static/styles.css`
- focused Atlassian Browse/route/UI contract tests
- Product Model and Atlassian Source Memory owner docs

## Surface Lanes

- Read model:
  - responsibility: eligible hierarchy projection, count/list parity, and
    advanced-filter state derived from FEAT-0076 results
  - dependency order: first
  - evaluator ownership: contract, functional
- Route and shell:
  - responsibility: service mapping, canonical emitted URLs, safe return path,
    and one-query ownership
  - dependency order: after read model
  - evaluator ownership: contract, design, functional
- Presentation:
  - responsibility: hierarchy/list composition, progressive Filters, compact
    rows, accessible states, and responsive containment
  - dependency order: after route and shell
  - evaluator ownership: design, functional, ux-heuristic
- Documentation:
  - responsibility: runtime/owner-doc parity without duplicating the Design
    Constitution
  - dependency order: after behavior is fixed
  - evaluator ownership: contract

## State And Interaction Contract

- Default: All/root, empty query, no advanced filters, locally eligible list.
- Service: active tab and service eligibility change together; incompatible
  structure is absent from the emitted URL.
- Structure: active hierarchy node has `aria-current="page"`; its count and
  list count agree while query/filter state remains editable.
- Filters closed: summary exposes active-filter count and values; results stay
  visible. Filters open: six retained selectors and Apply/Clear/Reset are
  keyboard reachable in DOM order.
- Empty inventory: explain that Add can create a local reference; do not imply
  a remote connection is required.
- No result: preserve scope/query/filter controls and provide clear/reset
  recovery.
- Stale or unavailable: keep the local Item visible with a text label, never
  color alone.
- Direct detail return: Back returns to the exact canonical service,
  structure, query, and advanced-filter inventory URL supplied by the row.
- Error: invalid exact query is a bounded local 400 with no write or external
  work; unsafe detail return input degrades to `/atlassian`.

## Screen-Alignment Consistency List

- Retained components: shared shell, page heading, segmented controls,
  semantic buttons, status badges, native details/summary, form controls,
  empty-state panel, local row/list, focus ring, and Local Context Explorer
  rail/list composition.
- Retained visual roles: existing type scale, spacing, colors, borders,
  radii, elevation, semantic tokens, breakpoints, and shell geometry.
- Deliberate changes: Atlassian becomes the approved Explorer variant; the
  global query yields to one surface-local query; structural filters become a
  hierarchy; six advanced filters move into progressive disclosure.
- Intentional deviations: the current Atlassian equal-weight registration and
  selector-card composition is replaced as approved by FEAT-0075.
- New pattern introduced: none outside the approved Atlassian Explorer
  variant and current native disclosure vocabulary.

## Contract Surfaces

- URL input: `view`, `q`, `site_id`, `space_id`, `structural_scope`, and the six
  retained advanced-filter keys.
- URL output: `view=wiki` is canonical presentation output; emitted structural
  URLs include an explicit Jira or Wiki view, emitted Space and Unclassified
  URLs include their Site, and empty values are omitted.
- Read projection: `browse.hierarchy`, `eligible_count`, `matching_count`,
  `active_filter_count`, Item `detail_url`, and exact match projection.
- Shell ownership: no `.global-search` form for Atlassian-active pages; one
  reserved center grid cell remains.
- Data and external boundaries: read-only local SQLite; no schema, provider,
  capability, network, evidence scan, Refresh, or maintenance side effect.

## Required Evaluators

- Contract: service/URL/filter/read-model ownership, return-path safety,
  zero-hidden-I/O, owner-doc parity, and stale assumptions.
- Design: screen-alignment extend consistency, one-query hierarchy, calm row
  density, visible/programmatic state, and four-width geometry.
- Functional: exact consumer, hierarchy parity, filter intersections, links,
  error/empty/unavailable/duplicate-key/archived states, and regressions.
- UX heuristic: orientation, progressive disclosure, recovery, list-first
  narrow flow, action clarity, and keyboard/touch reachability.

## Acceptance Mapping

- Synthetic read-model tests cover All/Jira/Wiki, Site/Space/Unclassified,
  count parity, query/filter composition, duplicate keys, archived exclusion,
  and unavailable Items.
- Rendered route tests cover one search input, absent global query, canonical
  service/structure/filter URLs, hidden selector reduction, row destination,
  and safe detail return.
- Chrome checks at `1440`, `920`, `700`, and `320` cover initial-result
  reachability, hierarchy mode, filter disclosure, focus, long labels, active
  states, and horizontal containment using synthetic data only.
- Focused and full automated tests plus privacy/diff checks cover adjacent
  setup, registration, detail, Refresh, global Search, and shell regressions.

## Evaluation Focus

- Confirm hierarchy counts do not come from an unfiltered or structurally
  pre-filtered population.
- Confirm All is combined local eligibility and Wiki is not a third stored
  service.
- Confirm the six advanced filters do not reintroduce Site/Space/connection or
  Item-type selectors.
- Confirm no second visible query, dead placeholder action, remote/model call,
  nested content tree, or adjacent detail behavior enters this Feature.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-29`: approved for RUN-87 after FEAT-0075 and FEAT-0076 passed and
  the owner authorized sequential Feature approval and execution.
