# SPEC-0114-R9: Session Chart Scaled Branch Labels

## Metadata

- ID: `spec-0114-r9`
- Status: `superseded`
- Run: [RUN-149](../run/run-20261007-149-session-chart-scaled-branch-labels.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-07`

## Approved Boundary

Superseded as the active Spec by [R10](spec-0114-r10-session-chart-hover-preview.md).
R10 retains proportional branch/Project names; this Run/evaluation remain
historical evidence for their recorded scope.

The owner requests scaling branch labels with the diagram instead of hiding them
as the screen zooms out. Use screen-alignment `extend` under the native constitution;
primary performs all roles sequentially without delegation. Affected surface:
`/sessions?display=chart`, branch-label construction, Project/branch typography and
branch box geometry, the JS/CSS asset references and owner documentation. Retain
[R8](spec-0114-r8-session-chart-head-reference-tracks.md) HEAD handling and inherited
input, observations, pins, persistence, camera and frozen List/workflow boundaries.

## Label And Projection Contract

- Remove the branch-label cutoff `trackStep * rowScale >= hitSize`. Viewport
  culling remains, but zoom alone never hides a visible track's label.
- Scale the native branch caption size, box height and vertical padding by the
  same rowScale used for track positions and Session targets. Keep monospace,
  source meaning, selected color/weight, ellipsis and full-name title intact.
- Scale Project-name typography by rowScale too. The existing resolved line-height
  measurement then fits its heading inside the compressed Project band without
  covering the first branch label. Reading-scale font/geometry stays unchanged.
  Fixed axis width and horizontal insets remain native; Project paths remain
  omitted in overview, and crowded Session captions/preview keep their policy.
- Names remain present at whole-diagram fit, even when the resulting text is tiny.
  No minimum-font cutoff or new hidden-label threshold is introduced. Existing
  Project/Session focus restores reading scale, and full labels remain inspectable
  through their native title/metadata.
- Cmd/Ctrl+Shift time-only zoom retains rowScale, so it does not resize these
  names. Ordinary zoom/fit changes their typography with vertical projection.
- Do not change guides, membership, ordering, times, selection, pins, filters,
  stored preferences, data producers or existing work surfaces. Bump both changed
  asset references; add no controls, tokens, dependencies or UI instruction copy.

## Evaluation And Closeout

Observe the existing branch-label disappearance before editing, then inspect
reading, half-scale and whole-fit rendered labels/guide alignment. Review Project
heading separation, full-name metadata and return to reading through its existing
focus control at wide and compact viewports, plus matching asset freshness.
Use browser observation and source review; no behavior-test or scripted regression
suite is added or run. Distinguish observed scale states from inherited gesture,
data/persistence and device evidence. Report narrow evidence gaps with acceptance
impact. Run syntax, whitespace, privacy and planning-catalog checks. Retain no
task-owned review debris, process, screenshot export or temporary path at closeout.

## Open Blockers

None. This replaces the previous overview branch-label omission policy with the
owner's explicit request to shrink labels while preserving their visibility.
