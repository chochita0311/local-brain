# SPEC-0104: Temporal Affinity Flow

## Metadata

- ID: `spec-0104`
- Status: `approved`
- Feature: [FEAT-0104](../feature/feat-0104-temporal-affinity-flow.md)
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Run: [RUN-117](../run/run-20260924-117-continuous-affinity-canvas.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend`, `frontend`
- Attempt: `1`
- Created: `2026-09-24`

## Presentation Contract

The `v2` reader separates `nodes` (24-item text list) from `map_nodes` (every
matching candidate at the current scope). `edges` aggregates the latter without
a list-page boundary. `map_scope` excludes list/evidence pages and selection;
it includes snapshot, hierarchy and search. Inventory remains text-only.
Reuse the existing bounded, validated report; do not recompute communities or
invent connections for lone observations. Source messages stay in exact-evidence
reads, not the graph payload. Preserve existing source/freshness authority.

Derive a shared UTC domain from all candidate message dates in the current scope,
before search/paging. At most 64 equal day-multiple periods cover that domain.
Per matching strand, retain every occurrence in an activity period or an explicit
unknown-time count. Each period carries actual first/last, a mean observed time,
occurrence and distinct Session counts. Global coverage remains unchanged.
Existing maximum-similarity edges gain deterministic original occurrence witness
dates; missing endpoints remain unplaced rather than invented. No new persistent
state, report schema or model execution. Period counts are not work duration.

`pick` retains its scope semantics. Optional `period` selects a valid present
period or `unknown` within that strand; reject stale/empty selections. Evidence
paging filters to those exact occurrence rows. Period links, clear-period and
all-strand links remain native and source-validated. Unknown records are reachable
outside the dated plane. Scope changes reset period; same-scope evidence keeps it.

## Design And Interaction Contract

Mismatch: the previous graph's x was arbitrary and dates appeared only in Trace.
Reframe resolved by constitution v22; implementation now extends Explorer/Trace.
Keep native shell/header/navigation, neutral surface and brand selection.

- SVG shared proportional x=time; y is deterministic similarity neighborhood
  order plus bounded source-edge attraction. Actual activity knots connect with
  monotone-x curves. Nonadjacent empty periods are dashed, never filled duration
  bars. Dates/ticks remain readable and match the zoomed time window.
  A knot represents one strand's occurrence aggregate in one period, not an
  individual vector or Session. Its base radius is
  `3 + min(4, log2(1 + occurrences))`: capped occurrence volume, not cohesion,
  distinct Session count, semantic confidence or work importance. A single
  observed period remains a point; it must not gain a fabricated connecting span.
- Undirected bridge curves anchor only at actual witness dates. Labels and
  counts disclose shown versus available connections. No lineage arrowheads.
- Click strand for whole evidence or activity knot for period evidence. Camera
  stays stable on selection. Explicit neighborhood lens fits selected/related
  strands; semantic detail increases on zoom without automatically changing scope.
- Visible zoom/pan/fit/reset plus keyboard; Ctrl/Meta-wheel anchors zoom, plain
  scroll belongs to the bounded map viewport when over it and the document
  outside it. Native horizontal scroll/trackpad and visible earlier/later
  controls traverse one continuous time plane; vertical scroll reaches all rows.
  Start at 200% for inspection, fit the entire time domain at 100%, reset to the
  initial view. Limit pan to content, without blank-page substitutes.
  Short camera/focus transitions only; reduced motion
  is immediate. Stable snapshot/URL/history, latest-request ownership and native
  failure paths from FEAT-0102 remain required.
- Shared breakpoints; labels never shrink below readable body-small. Dense maps
  may pan vertically instead of shrinking every title; fallback lists stay complete.
- Text-list paging lives inside the list disclosure, preserves disclosure,
  geometry, camera and reachable pagination controls, and never changes map
  membership or cross-list-page connections. All three hierarchy scales use
  the same continuous-canvas contract; search alone filters current scope.
- Whole-scope layout must avoid repeated all-node sorting and all-edge scans
  per knot. Large synthetic scope and actual boolean-only readiness checks
  accompany the former page-three regression; no hidden node cutoff.

## Validation And Open Blockers

No open boundary blockers. Unit checks: count conservation, exact date placement,
scope-stable domain, long gaps, repeated/unknown dates, edge witness provenance,
period filters and rejected obsolete periods, passive reads. Browser checks:
temporal geometry, curved rendering, period→source→return, camera/selection,
focus lens, hover, history/rapid input, resize, 1440/920/700/320, reduced motion,
no script and forced render failure. Synthetic visual review is required; actual
private runtime uses boolean-only readiness checks. Semantic identity is unverified
and outside acceptance. Task-owned scratch is removed before handoff.

## Continuity

`2026-09-24`: after RUN-116, the owner rejected arbitrary map pagination.
Corrected the weak scope/input contract before RUN-117; time, source authority,
circle meaning, grouping and storage are unchanged.
