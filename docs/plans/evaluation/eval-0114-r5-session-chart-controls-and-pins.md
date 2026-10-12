# EVAL-0114-R5: Session Chart Controls And Pins

## Metadata

- ID: `eval-0114-r5`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R5](../spec/spec-0114-r5-session-chart-controls-and-pins.md)
- Run: [RUN-145](../run/run-20261007-145-session-chart-controls-and-pins.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-07`

## Scope And Evidence

Primary performed sequential contract, rendered design, functional and UX review
of toolbar placement, durable visibility, pin display and source/view separators.
Screen-alignment `extend` uses the existing Chart, Dashboard source control,
filled pin shape/color and native control/surface/type rules. R4 camera/overview
evidence remains in [EVAL-0114-R4](eval-0114-r4-filtered-session-chart-overview.md).

Review used the ordinary application, isolated task-owned pages and native
mouse/key/selector actions. Numeric DOM checks inspect layout and exact pin
membership without persisting private content. In-memory synthetic Chart metadata
covers an earlier pinned member with a later unpinned aggregate host, a single
pin, an undated pin and storage branches. A controlled localStorage denial
exercises the fallback. No database fixture or real pin mutation was performed.

## Contract And Design Findings

- Existing Project disclosure now owns the toolbar's former date-navigation
  position. The extra filter row, date output and earlier/later/up/down buttons
  are absent. Axis dates and native zoom/fit/focus remain. Source review retains
  blank dragging, wheel/key ownership and the unchanged R4 endpoint resistance.
- Source separators use the Dashboard's shared rule for adjacent unselected
  options, with the same measured 1px divider/color. All and Company selections
  retain truthful active segments and Chart destinations. List/Chart has exactly
  two segments and no separator; the source label is `All`.
- All current eligible pin IDs come from the already-loaded complete pin list,
  with no added query, truncation or mutation. The browser intersects with Chart
  records and computes pin membership across each exact pixel bucket. Source
  colors and mixed-source neutral cues remain intact. A static native info halo
  and filled pin shape distinguish pin state from selected-target background;
  actual inspected reading targets remain 40px.
- Aggregate marking includes any pinned member and exposes exact pin count in
  its accessible name. Selector labels, preview status and undated text belong
  to the original Session. A native click on an actual pinned Chart point opens
  its original metadata preview. Synthetic native aggregate selection confirms
  that an unpinned host has no preview pin status, then choosing its pinned member
  shows status and the correct original detail URL. No synthetic detail request
  was made.

## Functional And Interaction Findings

- A native Project checkbox click saves the hidden choice immediately, leaves
  the disclosure open, clears its heading and produces the partial state. A fresh
  same-origin document with empty initial tab camera storage restores visibility
  from localStorage without copying selection. Closing the original review tab
  and opening another retains that choice. This observes fresh-tab/document
  persistence; browser-process restart itself was not performed.
- Programmatic native change events cover none/all: no Project shows the honest
  empty message and zero points, and all-selected stores an explicit empty hidden
  list. Synthetic document reloads verify migration from old tab hiding, retention
  of temporarily absent hidden keys, known-only display/counts and durable all
  overriding stale tab hiding. Controlled durable-storage denial leaves the
  explorer/filter usable and stores tab fallback when that storage is available.
- Camera/selection/scale remain tab state; durable folder choices are scoped by
  source/workspace and same browser origin. Clearing storage, private-mode
  expiry, another browser/origin or disabled durable storage limits persistence.
  Real source switching verifies scope-specific camera keys and Company-only
  records. Malformed durable values receive source review rather than runtime
  certification.
- Effective 1440/700/320px layouts have no outer horizontal overflow. Project
  disclosure remains at the toolbar's left, its narrow panel stays inside the
  window, and essential toolbar controls retain 40px height. Whole overview
  retains all displayed Project headings and pin cues with the canvas in view.
  The narrow source scroller reaches its final option. Native End selection
  restores reading scale and a contained in-flow preview with exact pin status.
- Native ordinary detail entry and browser Back restore Chart selection and
  durable visibility; original Workflow Focus destination remains available.
  Default List retains rows, pagination, recall column and existing pin controls,
  without a Chart renderer. Only its explicitly requested source/view header
  details change. The inspected final ordinary Chart/return has no console
  warnings or errors.

## Limits And Owner Review

Evidence is partial. Browser-process/OS restart, storage quota/private-mode
lifecycle, cross-tab live synchronization, physical touch/trackpad, stress and
automated suites were not run. Synthetic pin/storage cases establish browser
consumer behavior, not backend execution. Existing pin producer semantics receive
source review and real current-pin projection is observed. No new pin persistence,
observation producer, Workflow Focus or Auto Work behavior is introduced.

Owner review now concerns toolbar placement and pin legibility at reading/overview
sizes. There are no blocking findings or new approval gates. Changed-fact owner
documents and current planning routing retain that boundary; task review pages
and instrumentation are removed at closeout.
