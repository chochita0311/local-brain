# EVAL-0114-R4: Filtered Session Chart Overview

## Metadata

- ID: `eval-0114-r4`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R4](../spec/spec-0114-r4-filtered-session-chart-overview.md)
- Run: [RUN-144](../run/run-20261006-144-filtered-session-chart-overview.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-06`

## Scope And Evidence

Primary performed sequential contract, rendered design, functional and UX review
of the owner-requested filter, spacing, endpoint and overview refinement. Native
screen-alignment extend uses the current screen and existing disclosure/menu,
type, control and surface rules. Prior Project/branch observation contracts remain
in [EVAL-0114-R3](eval-0114-r3-project-branch-session-chart.md).

Review used the ordinary local application and two task-owned browser pages,
real mouse/key gestures and temporary numeric DOM instrumentation. A controlled
media-query response exercised the new reduced-motion camera branch. No fixture
database, extra server or automated test was created. No private source content,
paths, inventory totals, IDs or screenshots are persisted here.

## Contract And Design Findings

- Changes are limited to Chart assets/template URLs and changed-fact owners.
  Observation SQL, ingestion, Session Workflow Focus and Auto Work producers are
  unchanged. The existing List is preserved.
- Footer totals, layout legend and instructions are absent from the final native
  DOM. Recorded preview metadata and owner docs retain honest guide semantics;
  actual unknown-time, error, List fallback and detail destinations remain.
- Project checkbox visibility uses only known recorded folder keys. Changes
  immediately hide/repack rows, clear hidden selection/activity and expose honest
  all/partial/none states. Duplicate names retain paths in the option list and
  tooltip. Search receives source review: it narrows option labels only. It never
  changes source/workspace eligibility, deletes records or classifies work.
- Reading branch pitch is measured at 48px, with 40px headings and 8px separation.
  Every inspected reading point retains its 40px target. Homes are computed per
  visible Project set; zoom projects them with a separate vertical scale rather
  than changing branch membership or inferred relationships.
- The left axis stays fixed while the whole diagram can shrink vertically.
  Overview omits crowded title/branch/cue text and preview while preserving
  selection. Project names and projected points remain available; Project/Session
  focus restores reading scale. Overview plot/label targets are smaller by design;
  native menu/toolbar/preview controls and reading targets retain ordinary sizes.
- Review found typography token values in rem had been treated as pixel lengths
  for overview headings. The correction measures resolved line height and uses
  the native title line-height role. Final inspected Project text and reading
  path rows stay inside their heading/axis, including the last overview label.

## Functional And Interaction Findings

- Native checkbox click restores a hidden Project, keeping the menu open for
  multiple choices. Programmatic native change events cover partial/none/all:
  hidden rows disappear, partial selection becomes indeterminate, all-hidden
  canvas says no Project is selected and select-all restores the diagram. Native
  Enter opens the disclosure; Escape closes it and restores trigger focus.
- Minus repeated to its minimum and whole-view fit both show every selected
  Project band within the canvas. The represented original Session count matches
  the dated scoped inventory rather than only one List page. Fit brings the whole
  canvas within the browser window with a small end inset. No footer is required
  to reach or interpret the view.
- Real overview point and Project-label clicks restore reading scale. Point
  selection opens the ordinary metadata/detail preview; Project focus retains a
  meaningful native focus target after axis replacement. Chronological Home/End
  select only visible Projects and restore the reading preview.
- Real blank-space drags at both date ends move less than the 40px extension
  bound, show resistance, and return to the exact original endpoint. Saved camera
  time contains no transient overshoot and selection is unchanged. The controlled
  reduced-motion branch returns on the next render rather than springing.
- Real reading point dragging still moves only its same-track peers, keeps guide
  paths fixed, returns all transforms exactly and does not select/open a preview.
  Source review confirms camera/filter/resize/page-hide cancellation and no idle
  spring loop.
- With a hidden Project, ordinary detail and its Sessions Chart backlink restore
  the exact camera/scale/selection/visibility state. Pressed-host membership
  matches the original selected Session. Explicit retained activity GET succeeds,
  draws points and restores reading scale with the preview visible.
- Version-four storage adds validated known hidden keys and finite vertical scale;
  migration discards old-spacing Y while retaining valid time/zoom/selection.
  Migration/stale-state rules receive source review; current reload/detail return
  is directly observed.
- Effective 1440, 700 and 320px viewports have no outer horizontal overflow. The
  Project menu stays inside the window with 40px option rows and a bounded inner
  scroller. Whole overview fits all selected rows; at 320px reading preview follows
  the canvas and essential actions remain contained.
- Default List retains native rows, pagination and Pinned Sessions, with no Chart
  script or Project checkbox menu. Final ordinary Chart loads revision-eight
  assets, shows the new controls and complete overview, and has no application
  console warnings or errors.

## Limits, Closeout And Owner Review

`pass` for this inspectable frontend increment with partial evidence coverage.
Automated suites, physical-device/trackpad permutations, actual OS motion-setting
changes and large-corpus stress were not run. The media-query shim proves the
JavaScript reduced-motion camera branch, not OS/CSS preference integration. Earlier
unknown-time/read-error/no-script/render/storage recovery evidence remains in
[EVAL-0114](eval-0114-observed-session-chart.md) with current source review.

The next owner review concerns checkbox filter reach, overview legibility and
camera tension. Dense overview targets deliberately trade reading detail for
whole-diagram structure and return to reading scale on selection. No new inference,
Git history, work classification or Auto Work resumption is authorized.

JavaScript syntax, whitespace, repository privacy and regenerated catalog checks
support their specific scopes; no automated test result is claimed. Task review
pages, controlled preferences and numeric instrumentation are removed.
No task filesystem scratch or extra server remains. The ordinary local Chart
stays available with the final overview for owner inspection.
