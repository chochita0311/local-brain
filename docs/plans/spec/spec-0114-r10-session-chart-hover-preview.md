# SPEC-0114-R10: Session Chart Hover Preview

## Metadata

- ID: `spec-0114-r10`
- Status: `superseded`
- Run: [RUN-150](../run/run-20261008-150-session-chart-hover-preview.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-08`

## Approved Boundary

Superseded as the active Spec by [R11](spec-0114-r11-session-chart-hover-region.md).
Its owner-requested continuous hover region replaces immediate node-exit dismissal
and pointer-inert temporary cards; this Run/evaluation remain historical evidence.

Owner requests Session-node hover explanations and clearer hover color, followed
by click holding the description, same-node repeat click releasing it and blank
canvas click clearing it. Use screen-alignment `extend`; primary performs all
roles sequentially. Affected surface: `/sessions?display=chart`, node preview and
selection bindings, native hover styles, shared preview markup and asset references.
Retain [R9](spec-0114-r9-session-chart-scaled-branch-labels.md) names and inherited
metadata, HEAD, pins, input, camera, persistence and frozen work boundaries.

## Interaction Contract

- Non-touch pointer entry or keyboard focus reveals original source, title, time,
  path, recorded branch and overlap count in the existing preview. Pointer exit or
  focus exit removes the transient description. Hover works at overview scale
  without changing scale, camera, selected Session, saved view or activity.
- Transient preview overlays even on narrow screens, accepts no pointer input,
  and hides close, member selector control, activity and detail actions. Its overlap
  count remains visible. It must not steal hover or create page-layout feedback.
- Click/tap/keyboard activation holds the original Session as selection. Held
  preview retains its original wide floating/narrow in-flow behavior and actions;
  overview activation retains existing focus to reading scale. Keyboard focus
  and pressed state remain accessible. Descriptions use no duplicate native tooltip.
  If a held wide pane would cover the clicked point, shift time position only as
  needed to keep repeat activation reachable; otherwise reading hold keeps position.
- Hovering another node adds a transient description beside that node; the held
  Session and loaded activity state stay unchanged and visible. Leaving removes
  only the transient card. Hovering a held aggregate uses its selected
  member. Exact-member selection remains available after holding an aggregate.
- Repeat activation of the node whose aggregate contains the held member clears
  selection and hover. Suppress immediate reappearance until that node is exited.
  Camera reprojection must not reveal another node's description under a stationary
  pointer; resume pointer hover only after intentional movement.
  Blank canvas click, close and Escape release the description. Menu and preview
  controls keep their meanings; blank drag and node pull do not become clicks.
- Camera/scale/filter/resize, true drag, cancellation, page hiding and node removal
  clear transient hover while retaining valid held selection. Hidden selected
  Projects retain their existing clearing behavior. Hover is never persisted.
- Strengthen node hover/focus target background and border with existing info
  surface/border/focus-width roles, preserving source fills, pin halo/icon and
  selected semantics. Add no colors, global tokens, controls or legend copy.
- Preview space is reserved only by held reading selection in the existing wide
  layout. A second instance of the native preview shares metadata rendering and
  strips selection actions, so transient hover never changes the held card's flow
  or camera bounds. Place it beside the target, or above/below when narrow, inside
  the canvas frame. No fetch, schema/backend, preference write,
  dependency or existing Workflow/Auto Work change belongs to this revision.

## Evaluation And Closeout

Review rendered pointer/focus entry-exit, hold/leave, repeat/blank/close/Escape
dismissal, A-held/B-hover restoration and exact-member metadata. Inspect hover
color, no camera/scale movement, overview/narrow overlay containment, reading
selection and drag-click separation. Distinguish browser observation, source review
and inherited evidence; no behavior-test or scripted regression suite is added or
run. Record partial gaps and acceptance impact. Run syntax, whitespace, privacy
and catalog checks. Bump matching JS/CSS references. Remove exact task-owned source
snapshots and any review artifacts before completion; no external write or commit.

## Open Blockers

None. The request extends existing preview/selection behavior within the approved
Chart; original observations and work organization remain unchanged.
