# SPEC-0114-R11: Session Chart Hover Region

## Metadata

- ID: `spec-0114-r11`
- Status: `approved`
- Run: [RUN-151](../run/run-20261009-151-session-chart-hover-region.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-09`

## Approved Boundary

Owner reports that moving from a Session node into its description immediately
closes it and requests a continuous hover region. This supersedes R10's immediate
node-exit dismissal and pointer-inert transient card. Use screen-alignment `extend`;
primary owns orchestration, spec, implementation and sequential evaluation. Change
only the Chart hover controller, its card input style, matching asset references
and owner documents. Existing metadata, held selection, source/pin meanings, layout,
producers, List, Workflow Focus and stopped Auto Work retain their boundaries.

## Interaction Contract

- The originating node, temporary description and geometric passage between
  their facing edges form one hover region. Support right/left and narrow
  above/below placements. Crossing the gap or resting inside the card must not
  dismiss it. Another node still updates transient metadata without changing held
  selection or activity.
- Leaving the complete region closes the temporary description after the native
  120ms state-duration grace. Reentry cancels that exit. The grace is finite,
  not restarted continuously outside, and has no stale callback after selection,
  camera/filter/resize, drag, node removal, page hiding or render failure.
- The temporary card accepts pointer reading, text selection and local scrolling.
  It gains keyboard focus so keyboard focus in the node/card retains the description;
  leaving both focus and hover ownership closes it. Escape dismisses from the
  card as well as the canvas. Clicks or scroll inside the card do not pin, navigate
  or drag the chart. It still omits close/member/activity/detail actions.
  New transient metadata starts at the top rather than inheriting another card's
  internal scroll position. Mouse text clicks do not create lasting focus retention.
- Only actual input on the card belongs to it. The gap is a geometric retention
  check, not an invisible hit overlay; blank canvas click/drag remain available.
  Blank click clears transient descriptions even when no held Session exists.
- Activation still holds selection; same aggregate, blank click, close or Escape
  releases it. Held description/activity, original member metadata, stationary-
  pointer reprojection guard, overview focus and camera reservation stay intact.
  Transient reading never changes projection, persistence or starts a fetch.
- Use the existing metadata card, geometry and state-duration token. Add no color,
  global token, dependency, source/data write or new work organization behavior.

## Evaluation And Closeout

Observe node-to-card passage, card rest/return/exit, other-node hover, blank click,
held/repeat release, keyboard card/Escape and node drag separation. Inspect wide,
overview and narrow above/below placement, metadata and stable geometry. Distinguish
native browser input, programmatic focus/DOM witnesses, source review and inherited
evidence. No behavior tests or scripted regression suite are added or run. Record
partial gaps and their acceptance impact. Run syntax, whitespace, privacy and
planning-catalog checks; bump JS/CSS references and remove exact task-owned source
snapshots and any review by-products. No external write or commit.

## Open Blockers

None. This is the owner's bounded correction to the existing hover interaction.
