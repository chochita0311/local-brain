# FEAT-0102: Full-History Affinity Map

## Metadata

- ID: `feat-0102`
- Status: `superseded`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-23`
- Updated: `2026-09-24`
- User review status: approved by continuous-through-UI authorization, 2026-09-23.

## Goal And User-Visible Outcome

In the existing Auto Work destination above Workstreams, explore the whole
admitted Session history as broad similarity groups, zoom into a neighborhood,
and inspect the original supporting passages without maintaining containers or
approving candidates. This is an observable intermediate step toward the work
flow map, not a claim that similarity is already meaningful work organization.

## Acceptance Contract

### 1. One Entry, Three Inspection Scales

- Reuse `/auto-work` and its current sidebar location. Introduce a clearly labeled
  full-history exploration view; retain the earlier sampled comparator as an
  explicitly separate previous-sample view. Never relabel its 60-Session output
  as full-history data or silently fall back to it when preparation is missing.
- Overview groups precede source nodes. Show coarse similarity groups, expand
  their subgroups/neighborhoods, then inspect exact Session/message evidence.
  Sessions are evidence containers, not automatically one workstream each.
- Use the existing simulation's hierarchy initially; do not force a desired
  number of clusters or claim its representative Session title is an inferred
  enduring category. Display fragmentation/overlap and retain access to all
  groups, singletons and exclusions through bounded paging/search.
- Selection illuminates relevant neighboring evidence without displacing the
  anchor. A stable, bounded constellation supports pan/zoom/fit/reset and a
  readable evidence inspector; no perpetual physics or required node editing.
- Show observed chronology in the inspected neighborhood/history without
  implying that time order, proximity or visual tension proves causation.

### 2. Separate Meaning And Authority

- Label group/edge meaning textually: similarity group and undirected affinity.
  Source evidence and inferred proximity remain distinct without color alone.
- No inferred continuation arrows, branching/merging, active/completed state,
  auto-generated goal summary or confirmed organization in this increment.
  Their absence is a scope boundary, not a broken-screen warning or review task.
- A later relationship layer needs its own approved consumer and real-context
  evidence. FEAT-0103's synthetic PASS, if any, does not automatically populate
  this map. Existing Session Focus keeps its own authority and remains a linked
  source-inspection surface rather than silently inheriting affinity edges.
- Preparation/coverage/freshness are visible at the scope where they matter.
  A usable map is not recorded as Workstream-replacement quality PASS.

### 3. Observation Without A Classification Queue

- Zoom, select, inspect and return are the primary actions. No naming, promotion,
  membership approval, per-Session labeling or correction queue is required.
- Keep snapshot/configuration-scoped direct links and browser back/forward.
  Returning preserves valid view/selection state; an obsolete selection explains
  its missing snapshot instead of jumping to an unrelated nearest group.
- Visible controls and keyboard paths cover zoom/reset/fit, group expansion,
  selection and inspector return. Pointer zoom must not steal ordinary scrolling.
- No-script/render-failure and narrow layouts offer a complete paged textual
  group/evidence path, not a static truncated preview. Maintain logical focus,
  reduced-motion behavior and readable Korean/English/mixed long labels.
- Browsing performs no model calls, embedding, source ingestion, automatic
  refresh or organization writes. A missing/stale report explains explicit
  preparation through the existing local command; visiting the page never starts it.

## Entry, Exit And State Expectations

- Entry: Auto Work sidebar or direct snapshot-scoped full-history URL.
- Exit: original Session evidence, existing Focus or return to the same map.
- Default: current prepared overview with full population and exclusion totals.
- Loading/busy: preserve context; no partial report or covert preparation.
- Empty: distinguish a valid empty eligible set from not-prepared data.
- Stale/expired: show snapshot limitation and preparation guidance; invalid exact
  evidence links cannot appear current. Missing source has a source-aware fallback.
- Error/render failure/no script: retain safe textual navigation and recovery.
- Success: the user can find a group, inspect its support and return without any
  classification action. This does not assert correct work identity or lifecycle.

## Scope Boundary

- In: existing navigation, whole-history affinity overview/neighborhood/evidence
  inspection, stable interaction and accessible fallback.
- Out: new source admission, inference/embedding services, goal/state extraction,
  relation overlay, production Workstream replacement, migration/cleanup, manual
  graph editing, persistent position preferences, new shell or design system.

## Surface Lanes

- Backend: read-only FEAT-0101 consumer and snapshot/evidence transport; source
  identity, coverage and no-hidden-work behavior are Contract/Functional gates.
- Frontend: existing Auto Work route/template/assets and linked source reading;
  Design, Functional and UX gates cover visual meaning and interaction continuity.

## Design Boundary

Apply the [Workflow Map Design Plan](../design/workflow-map-design-plan.md#relation-first-inspection-track)
in `extend` mode under the current Design Constitution. Reuse shared shell,
tokens, source-neutral semantics and Session/Explorer interaction patterns.
Define any new affinity/readiness state mapping in the constitution's owning
contracts before visible implementation; this draft grants no visual-law exception.
Renderer selection belongs to the approved Spec, with deterministic bounded
layout and fallback required; a new library is not presumed necessary.

## Dependencies

- [FEAT-0101](feat-0101-full-history-affinity-inspection-contract.md) must pass
  before build consumes its live report contract. Product spec follows the
  approved foundation boundary, not guessed private report semantics.
- Existing FEAT-0096 navigation and passed Session Focus/Trace remain intact.
- No FEAT-0098/0100 extraction or FEAT-0103 relationship-quality dependency.

## Likely Affected Surfaces

`main.py`, `auto_work.py`, `templates/auto-work.html`, `static/auto-work.js`, scoped
styles/tests, README usage and design/architecture owner docs where behavior changes.
Existing private values must never become tracked examples or screenshots.

## Pass Or Fail Checks

- Browser checks at `1440`, `920`, `700`, `320`: overview → neighborhood → exact
  source → return, keyboard, direct URL, back/forward, rapid selection, reset/fit,
  page scroll, repeated entry/handler registration and responsive focus retention.
- Use synthetic large/fragmented/multi-group histories and long labels. Verify
  total-set reachability, not merely attractive first-screen clustering.
- Check reduced motion, no script, render failure, missing/stale/expired report,
  stale selection and unavailable original evidence with complete source fallback.
- Verify actual local full-history readiness after FEAT-0101, retaining private
  evidence locally. Browser evidence must use the running app and loaded assets;
  template inspection alone cannot pass visible or interaction gates.
- Confirm no generation, ingestion, refresh or organization mutation from viewing.
  All four evaluators must pass; semantic work grouping remains unassessed.

## Regression Surfaces

The previous sampled view, existing sidebar/shell, Session detail/Focus,
Workstreams/Threads, simulation ownership and source-authority distinctions.

## Harness Trace

- Spec: [SPEC-0102](../spec/spec-0102-full-history-affinity-map.md).
- Run: [RUN-115](../run/run-20260923-115-full-history-affinity-map.md).

## Continuity Notes

- `2026-09-24`: owner review rejected freeform constellation geometry, returning
  the visual boundary to planning. [FEAT-0104](feat-0104-temporal-affinity-flow.md)
  supersedes the presentation with fluid left-to-right observed-time strands.
  Earlier technical evidence and the underlying source/read contract remain valid;
  neither establishes acceptance of the original visual direction.

- `2026-09-23`: implemented and verified under RUN-115. The actual local app now
  defaults to full-history affinity exploration; the old sample is a labeled
  separate tab. All four evaluators pass the inspection boundary with complete
  scoped evidence. Human review is of the working screen, not a classification
  queue; meaningful work identity and replacement quality remain unassessed.

- `2026-09-23`: drafted a whole-history observation surface independently of
  detailed extraction and the relation trial. No route or rendered UI changed.
