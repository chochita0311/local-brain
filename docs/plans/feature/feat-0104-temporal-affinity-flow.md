# FEAT-0104: Temporal Affinity Flow

## Metadata

- ID: `feat-0104`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend`, `frontend`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
- Created: `2026-09-24`
- User review status: bounded temporal correction approved by explicit direction
  and prior continuous-through-UI redesign authorization.

## Outcome And Boundary

Replace Auto Work's freeform constellation with a fluid left-to-right map of
observed similar material. x is actual elapsed time on a shared scale, not node
index or force position. Similarity governs strand neighborhoods and bounded
vertical attraction. Curved strands expose recurring activity across long gaps;
undirected cross-strand links do not claim causality, merge or same-work identity.
This is still pre-quality affinity inspection, not a finished Workstream replacement.

Reuse passed FEAT-0101 source/read authority. Derive only bounded presentation
bins and existing-edge witness times, without new storage, model calls, source
admission, identity, training, organization writes or cleanup. All eligible
history remains covered; only the text list is paginated, never the map. There
is no 60-Session cap or top-N graph cutoff.
FEAT-0103 is independent and unexecuted. Existing sample and Session Focus stay intact.

## Acceptance

- Shared factual time axis, curved activity strands, source-backed undirected
  bridges, explicit temporal aggregation and gaps, no fake dates for unknowns.
- Period selection inspects that strand's exact original evidence; whole-strand
  evidence and all periods remain accessible without JavaScript.
- Pan, zoom, fit/reset and selected-neighborhood lens; details emerge on zoom,
  pointer/focus highlights related paths, no ongoing decorative motion.
- Same-scope selection cannot relayout; direct links, repeated/rapid selection,
  source-return, history and resize preserve coherent scope/camera/focus.
- One continuous canvas contains every matching strand and its cross-list-page
  connections. Horizontal scroll traverses time; vertical scroll reaches other
  strands. List paging cannot change graph membership, layout or camera.
- Native shell, global Search, tokens and 1440/920/700/320 containment. Complete
  paginated text fallback, no script, render failure and reduced motion.
- Current/missing/busy/stale/expired/invalid/empty/obsolete states retain the
  reader's truth and cannot silently show the old sample.

## Lanes And Evidence

Backend (`session_affinity.py`, unit fixtures/tests): time projection and period
queries derived from existing report. Contract gate before frontend acceptance.
Frontend (template, map JS, scoped CSS, browser QA): temporal geometry, fluid
observation and exact-source journey. Design/Functional/UX gates use synthetic
rendered data; actual handoff returns readiness booleans only.
Owner docs change with behavior; preserve unrelated dirty work.

## Harness Trace

- Spec: [SPEC-0104](../spec/spec-0104-temporal-affinity-flow.md)
- Run: [RUN-117](../run/run-20260924-117-continuous-affinity-canvas.md)

## Continuity

`2026-09-24`: owner review identified arbitrary 24-item graph pagination as a
spec gap in the same temporal-flow outcome. The existing continuous-through-UI
authorization covers a corrected spec and new Run. RUN-116 is historical scoped
evidence, not acceptance of discontinuous map navigation.

RUN-117 passes the corrected continuous-canvas boundary with three-page and
larger-scope browser evidence, unchanged source authority, stable list/camera
state and a running local handoff. Task-owned synthetic artifacts are removed.

`2026-09-24`: temporal read projection and interactive UI pass the four scoped
evaluators. The actual local screen uses the existing whole-history calculation.
No training, re-embedding, source ingestion or organization change. Human visual
preference and semantic work-identity quality are not preemptively accepted.
