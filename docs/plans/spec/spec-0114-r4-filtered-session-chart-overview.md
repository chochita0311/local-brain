# SPEC-0114-R4: Filtered Session Chart Overview

## Metadata

- ID: `spec-0114-r4`
- Status: `superseded`
- Superseded by: [SPEC-0114-R5](spec-0114-r5-session-chart-controls-and-pins.md); camera, geometry and recovery contracts remain unless explicitly revised there.
- Run: [RUN-144](../run/run-20261006-144-filtered-session-chart-overview.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-06`

## Approved Direction And Diagnosis

The owner requests a cleaner Chart, Excel-like Project checkboxes, restrained date
ends, closer branch tracks and zooming far enough to see the whole diagram.
Existing zoom changes X only and fit stops at full time width, while world Y stays
unscaled. The fixed left axis consumes width but does not cause the vertical zoom
limit. Extend the current native screen; no reference styling or backend change.

## Display And Visibility Contract

- Remove the footer's total/visible/Project counts, layout legend and instructions.
  Preserve actual empty/unknown-time/error/fallback destinations and accessible
  control names. Guide semantics remain recorded observations in owner docs and
  preview metadata, never actual Git ancestry or duration.
- Add a native checkbox disclosure above the diagram. Individual Project choices
  apply immediately; select-all supports all/partial/none and option search only
  narrows the menu. Folder key stays canonical and duplicate names show paths.
  Hiding a Project clears its selection/activity and compacts remaining rows.
  No records, source/workspace scope, List or work identity change.
- Reading geometry uses 48px branch pitch, 40px Project heading and 8px Project
  separation, through existing tokens. Homes remain fixed per displayed Project
  set; zoom changes projection only. Source colors, saved branch meaning and
  original Session destinations remain intact.

## Camera, Overview And Interaction Contract

- Time zoom retains the full-period minimum while vertical scale can decrease to
  fit all displayed rows. Minus/modified wheel can reach that scale; whole-view
  fit aligns all selected Projects and observed time within the canvas. The left
  axis remains fixed. Overview uses compact single-line Project labels and omits
  crowded branch/title text; projected point targets scale with the plot. Project
  or Session selection restores reading scale and the existing preview/detail
  path. Overview withholds the preview while preserving selection, so fit remains
  unobstructed; selected focus restores it. Whole fit brings the canvas within the
  browser's visible area. Reading targets and toolbar/filter/preview controls
  retain native sizes.
- Observed bounds use visible Projects plus explicit selected activity. Endpoint
  camera limits reserve a small native inset rather than a half/full empty screen.
  Blank drag can stretch at most one 40px control width past an end through a
  resistance curve, then springs to the boundary. Reduced motion returns at once.
  Controls/wheel settle within bounds; transient overshoot is never saved.
  Floating preview space is reserved when bounding/focusing reading content.
- Save visibility and vertical scale with scope-specific version-four browser
  navigation state. Validate known folder keys and finite camera/scale values.
  Migrate earlier valid selection/time/zoom but discard old-spacing Y. Detail and
  reload restore current state. All-hidden and undated-only views remain usable.
- Keep same-track point tension, click/drag separation, cancellation, chronological
  keys and explicit activity retrieval. Resizing, filtering, selection, new camera
  input and page hide cancel motion. No idle physics loop or database mutation.

## Execution And Review

Primary owns frontend assets/template then changed-fact design/product/architecture
and planning documents. Sequential contract/design/functional/UX review uses the
rendered baseline, Project all/partial/none, dense selection, reading/overview
zoom, real endpoint drag/release, detail return and 1440/700/320px composition.
Native family surfaces/tokens guide the filter. No automated test addition/run,
physical-device or stress certification is claimed. Task review pages and private
instrumentation are removed at closeout; ordinary server stays available.

## Open Blockers

None. The owner explicitly authorizes this visible refinement. Recorded data,
List, Session Workflow Focus and the stopped Auto Work track remain frozen.
