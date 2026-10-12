# SPEC-0114-R7: Session Chart Wheel Controls

## Metadata

- ID: `spec-0114-r7`
- Status: `superseded`
- Run: [RUN-147](../run/run-20261007-147-session-chart-wheel-controls.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-07`

## Approved Boundary

Superseded as the active Spec by [R8](spec-0114-r8-session-chart-head-reference-tracks.md).
R8 retains this wheel/zoom contract and corrects only HEAD layout eligibility.
The R7 Run and evaluation remain historical evidence for their recorded scope.

The owner explicitly requests checking the non-working Shift-wheel gesture and
adding Cmd+Shift-wheel horizontal spacing control. Retain the observation,
folder/branch, pin, database visibility, balanced end space, elastic blank drag
and frozen-workflow contracts of [R6](spec-0114-r6-local-chart-preferences-and-pan-space.md).
Use screen-alignment `extend`; primary owns all roles sequentially without delegation.
This bounded revision changes Chart input and owner documentation only.
Affected surface: `/sessions?display=chart`, its wheel handler, time/row projection,
resize/return state and executable asset reference.

## Input And Zoom Contract

- Cmd/Ctrl-wheel keeps existing whole-chart X/Y zoom. Visible plus/minus, keyboard
  plus/minus and whole-diagram fit keep their existing meanings.
- Shift-wheel moves horizontally from either vertical deltaY or already horizontal
  deltaX input. When both are nonzero, use the larger absolute component (deltaY
  for equal magnitudes), keeping its sign and never adding the components. Preserve line/page delta normalization
  for panning and existing ordinary wheel/document ownership.
- Cmd/Ctrl+Shift-wheel zooms the time axis only. Down reduces spacing and up
  increases it using the existing zoom curve. Accept the same two input forms.
  Keep rowScale, vertical camera, node/label/target size, Project order, branch
  pitch, selection and preview mode unchanged. Existing density-driven caption
  and aggregate compaction still applies. The pointer's time remains the
  anchor unless visible-time bounds require clamping.
- Time zoom retains the current full-period fit minimum, maximum, projected
  target/end insets, selected-activity extent and visible-Project denominator.
  Wheel movement does not gain elastic overshoot. At whole-time fit or a date
  end, a bounded wheel may have no movement; this is separate from ignored input.
- Save existing independent X scale and Y scale/camera in tab state. Refresh,
  viewport resize and detail return preserve vertical state when only the time
  axis is fitted; whole-diagram fit still explicitly resets both axes. A rendering
  resize must not turn time-only fit into an implicit vertical reset.
- Preserve current controls and omit footer instructions or extra navigation
  buttons. Document the shortcut as application behavior, not a platform standard.
  Bump the changed executable asset reference to avoid a stale binding.

## Evaluation And Closeout

Before editing, reproduce the old handler's ignored horizontal Shift delta with
synthetic local Sessions. Review both Shift input forms/directions, horizontal
modifier zoom from reading and overview scales, ordinary Cmd zoom, pointer anchor,
Y invariance, min/max boundaries, fit and fresh-document restoration. Check the
ordinary running app loads the changed binding and retains List/Chart navigation.
Native browser-protocol input and synthetic DOM branches must be distinguished
from physical mouse/trackpad and OS event conversion. A lack of physical-device
evidence is partial coverage, not permission to claim the reported device root cause.
Use private task-owned review state and remove it at closeout. No schema/backend,
preference or work mutations, external writes, dependency additions or unrelated
test suites are authorized by this revision. Report scoped checks and limits.

## Open Blockers

None. The requested mapping is explicitly approved; the current data and camera
contracts determine the implementation bounds.
