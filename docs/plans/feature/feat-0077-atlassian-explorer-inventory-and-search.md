# FEAT-0077: Atlassian Explorer Inventory And Search

## Metadata

- ID: `feat-0077`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md)
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Goal

- Replace the initial Atlassian selector matrix with a responsive Explorer
  inventory where the user can choose Site/Space scope, search exactly once,
  and open a known Item without configuring advanced filters first.

## Acceptance Contract

- `/atlassian` opens in `All` scope and shows `All / Jira / Wiki`, one
  surface-local exact query input, one bounded Filters action, and the
  functional actions available at this execution stage.
- The shared global topbar query is not simultaneously visible on Atlassian;
  entering or leaving the route preserves shell geometry and navigation
  continuity.
- The hierarchy groups persisted Items by Service when useful, normalized
  Site, Space/project, and `Unclassified` for null Space. Counts describe the
  same eligible population as the adjacent list.
- The center list uses compact, stable rows with title/key, service, Site or
  Space, and only the coverage/freshness/provenance cues needed to distinguish
  the Item. Repeated labels and equal-weight card metadata are removed.
- Item rows remain ordinary links to the existing full-detail route in this
  Feature. Adjacent asynchronous detail replacement belongs to FEAT-0078.
- The query consumes the passed FEAT-0076 exact read model and never falls back
  to fuzzy, AI, provider, or token-AND behavior.
- Site and Space move into structural navigation. Coverage, freshness,
  attention, Topic, Tag, and Workstream remain available in one advanced
  Filters disclosure with a compact active-filter summary and clear/reset.
  Source Instance stays a Connections/diagnostic concern; Item type derives
  from service and is not a primary filter.
- Service, structural scope, query, and advanced filters are represented in
  stable URL state. Equivalent scope changes follow the FEAT-0075 preserve or
  reset contract.
- Wide layouts keep a persistent hierarchy and list; compact layouts may move
  hierarchy into a disclosure/drawer; narrow layouts are list-first and never
  place the full advanced-filter set before results.
- Empty, no-result, unavailable Site/Space, long label, duplicate key across
  Sites, stale, archived/default-excluded, and active-filter states remain
  understandable without color alone.
- Initial primary results are visible without traversing an always-expanded
  ten-selector matrix at supported widths.

## Scope Boundary

- In:
  - Explorer hierarchy and compact inventory list
  - `All / Jira / Wiki` scope and one surface-local exact search
  - advanced Filters disclosure, active summary, clear/reset, and URL state
  - shell query handoff on the Atlassian route
  - responsive hierarchy/list composition and all required states
  - full-detail link destination and no-script path
- Out:
  - in-context detail region or asynchronous Item replacement
  - one-URL Add reframe or Connections relocation
  - local evidence Sync action
  - exact query semantics owned by FEAT-0076
  - AI retrieval control or placeholder
  - nested Confluence Page/Jira issue hierarchy
  - remote Refresh behavior changes

## Surface Lanes

- Read-model lane:
  - path roots: Atlassian hierarchy/count/list projections and route tests
  - dependencies: passed FEAT-0075 and FEAT-0076
  - expected evidence: All/Jira/Wiki eligibility, Site/Space/Unclassified
    grouping, count/list parity, exact query, filters, and stable URL state
  - evaluator ownership: `contract`, `functional`
- Route and shell lane:
  - path roots: Atlassian route, shared shell conditional query ownership, and
    direct-entry/history behavior
  - dependencies: read-model lane and FEAT-0075 state contract
  - expected evidence: `All` default, explicit scope restoration, one query
    owner, no-script navigation, and shell continuity
  - evaluator ownership: `contract`, `design`, `functional`
- Presentation lane:
  - path roots: Atlassian templates, local interaction JavaScript, shared
    semantic-token styles, and UI/browser tests
  - dependencies: route and shell lane
  - expected evidence: calm hierarchy/list, progressive filters, active state,
    result reachability, containment, accessibility, and responsive order
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product and design owner docs
  - dependencies: completed presentation behavior
  - expected evidence: runtime/owner-doc parity without duplicating the Design
    Constitution
  - evaluator ownership: `contract`

## Contract Surfaces

- Atlassian Explorer route and URL/query parameters.
- FEAT-0076 exact retrieval consumer shape.
- Service/Site/Space/Unclassified hierarchy and count projection.
- Retained advanced-filter vocabulary and clear/reset behavior.
- Shared-shell search visibility and handoff.
- Full-detail destinations, semantic selection, and responsive DOM order.

## User-Visible Outcome

- Opening Atlassian immediately shows recognizable Site/Space organization and
  links, with one exact search and optional advanced filters, so the user can
  find and open an Item without first navigating a setup or selector matrix.

## Entry And Exit

- Entry point: open `/atlassian`, a scoped Explorer URL, or return from an Item
  detail route.
- Exit or transition behavior: change reversible service/structure/query/filter
  state, open an Item at its full-detail destination, or leave through the
  stable LocalBrain shell.

## State Expectations

- Default: `All`, hierarchy root, empty exact query, no advanced filters, list
  visible.
- Scoped: active service and Site/Space/Unclassified selection are visible and
  reflected in the result count and URL.
- Filters open: bounded disclosure/sheet with retained axes and accessible
  apply/clear behavior; results remain the primary task.
- Empty inventory: hierarchy/list state explains how Add or later Sync can
  provide local records without presenting remote setup as required.
- No result: query and active scope remain editable and clearable.
- Unavailable/stale: existing local Items remain visible with truthful state.
- Error: local failure is bounded; shell and full-detail destinations remain
  usable where available.
- Narrow: list first, hierarchy/filters in explicit sheets, no horizontal
  overflow or hidden unsupported mode.

## Dependencies

- FEAT-0075 and FEAT-0076 must be `passed` before this Feature enters build.
- FEAT-0078 depends on this Feature passing.
- FEAT-0079 and FEAT-0080 use this Feature's action region and inventory
  refresh behavior.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/atlassian_browse.py`
- `src/localbrain/templates/base.html`
- `src/localbrain/templates/atlassian.html`
- `src/localbrain/static/atlassian.js`
- `src/localbrain/static/app.js` only at the shared shell owner
- `src/localbrain/static/styles.css`
- Atlassian browse/search/route/UI tests
- product and design owner docs

## Pass Or Fail Checks

- Pass if `/atlassian` defaults to `All`, Jira/Wiki scopes work, and exactly
  one visible query input owns Atlassian retrieval.
- Pass if Site/Space/Unclassified counts and list membership agree for Jira,
  Wiki, combined, null-Space, duplicate-key, and unavailable states.
- Pass if exact queries use FEAT-0076 semantics and retained filters are hidden
  behind one accessible disclosure with honest active/clear state.
- Pass if Item links remain server-executable and return/navigation preserve
  approved scope state.
- Pass if rendered synthetic checks at `1440`, `920`, `700`, and `320` keep
  initial results reachable, labels contained, active states programmatic, and
  hierarchy/filters usable by keyboard and touch.
- Fail on a second visible query input, Jira coercion for `All`, an expanded
  ten-selector gate, hidden valid Items, unsupported nested hierarchy, dead
  action placeholders, or any remote/model call.

## Regression Surfaces

- Global Search and shell behavior on non-Atlassian routes.
- Existing Atlassian Item full-detail route and external navigation.
- PRD-0007 service, Site, Space, filter, archive, and local-search eligibility.
- PRD-0010 URL-only Add and optional access paths until FEAT-0079 replaces
  their primary composition.
- Local Context Explorer styling and state ownership without component drift.

## Harness Trace

- Approved spec: [SPEC-0077](../spec/spec-0077-atlassian-explorer-inventory-and-search.md)
- Completed run: [RUN-20260829-87](../run/run-20260829-87-atlassian-explorer-inventory-and-search.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports from Attempt 2:
  - [contract](../evaluation/eval-0077-r2-contract-atlassian-structural-scope-parity.md) — `PASS`
  - [design](../evaluation/eval-0077-r2-design-atlassian-structural-scope-parity.md) — `PASS`
  - [functional](../evaluation/eval-0077-r2-functional-atlassian-structural-scope-parity.md) — `PASS`
  - [UX heuristic](../evaluation/eval-0077-r2-ux-atlassian-structural-scope-parity.md) — `PASS`
- Latest fix note: [FIX-0077](../fix/fix-0077-atlassian-structural-scope-parity.md)

## Resolved Review Decisions

- Retain coverage, freshness, attention, Topic, Tag, and Workstream in advanced
  Filters; remove Source Instance, Site, Space, and Item type from that sheet.
- Keep Item rows on the existing full-detail route until FEAT-0078.

## Continuity Notes

- `2026-08-29`: proposed after PRD-0014 approval as the first user-visible
  Explorer increment, dependent on FEAT-0075 and FEAT-0076.
- `2026-08-29`: FEAT-0075 and FEAT-0076 passed. The owner's sequential
  approval activated this Feature as the only in-loop target with
  `screen-alignment` in `extend` mode and resolved both review decisions.
- `2026-08-29`: RUN-87 Attempt 1 passed with 86 focused regression tests,
  four-width Chrome evidence, Accessibility 100, and all required evaluators.
- `2026-08-29`: a post-pass canonical audit found a shared-Site service-branch
  count mismatch and an unsupported Site-less Unclassified scope. FEAT-0077
  reopened for FIX-0077 and Attempt 2; FEAT-0078 returned to draft/dependency wait.
- `2026-08-29`: Attempt 2 passed after service-qualified structural URLs,
  service compatibility, safe return-path parity, preserved global Search
  filters, 88 focused regressions, four-width Chrome checks, and all four R2
  evaluators passed. FEAT-0078 may resume.
