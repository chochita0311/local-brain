# EVAL-0114-R10: Session Chart Hover Preview

## Metadata

- ID: `eval-0114-r10`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R10](../spec/spec-0114-r10-session-chart-hover-preview.md)
- Run: [RUN-150](../run/run-20261008-150-session-chart-hover-preview.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-08`

## Scope And Evidence

Primary performed sequential contract, rendered design, functional and UX review
using screen-alignment `extend`. Inspected the ordinary running Chart after
cache-bypassing reload. Browser tool pointer hover/click, keyboard Tab/Enter/Escape
and node drag exercised the changed interaction. Page-side reads inspected state,
metadata equality, computed color, positions and containment. Programmatic focus
positioned the keyboard review before native Tab; exact aggregate-member change
used the existing select's change event. These are bounded manual browser
observations, not physical-device certification or a scripted regression suite.
Inline rendered views were reviewed at 1440/320px. No private titles, paths,
records, snapshots or payloads are persisted in this artifact.

## Contract Review

- A separate transient instance of the native preview shares original metadata
  filling with the held pane. Its close/member/activity/detail controls are
  removed; overlap count and original pin status remain. It accepts no pointer
  input and reserves no camera space, including in narrow layout.
- Pointer/focus entry fills the transient card, and exit clears it. Hover updates
  only ephemeral presentation, not selected Session, activity, camera, scale,
  sessionStorage or the Project preference API. Activity state preservation is
  supported by source review; the loaded-activity case is not rerun.
- Node activation holds selection through the existing path. Activation of the
  representative whose stack contains the held member releases selection. Blank
  click, close and Escape use the same clearing path. Native button semantics,
  pressed state, description references and the original exact-member selector
  remain; the duplicate native title tooltip is removed.
- The held wide pane shifts X only when it would cover the activated point,
  retaining reading Y/scale. Existing overview activation restores reading scale.
  The transient pane fits beside the point or above/below in narrow space.
- Cancellation clears transient hover. A cursor-position guard prevents another
  node from opening beneath a stationary pointer after reprojection; actual
  movement resumes hover. True drag clears hover while the existing capture and
  click-suppression path remains. Hidden selected Projects retain their original
  filter clearing. Hover is not serialized.
- Existing info surface/border, focus-width border and card elevation strengthen
  hover/focus. Source fills, static pin halo/icon and selected semantics remain.
  No new token, dependency, fetch, backend/schema or List/Workflow/Auto Work edit
  belongs to R10. Asset references are JS `-16` and CSS `-14`.
- Current product/design/planning owners describe both preview states. The
  architecture overview paragraph also corrects its stale branch-label omission
  wording to the already approved R9 continuous scaling contract.

## Rendered Results

- Reading hover shows original metadata without selection, camera/point-position
  changes or stage-height changes. Pointer exit closes it. Background resolves
  to the native info surface, border to native info color at 2px, and the reviewed
  card does not cover its hovered target.
- Native activation holds the metadata and detail destination after pointer exit.
  Hovering another point leaves that held Session intact; leaving closes only
  the transient description. Pressed state belongs to the held aggregate.
- Repeat activation and blank-canvas activation clear both descriptions. Initial
  review found that dismissal could project another point beneath a stationary
  pointer and reopen a transient card. After the cursor guard, repeat and blank
  dismissal leave both cards closed; moving onto another node opens hover again.
- Changing the exact member of an aggregate preserves its original metadata and
  detail destination. Native activation of its representative then releases it.
  Native close and Escape also release selection. Native Tab reveals the next
  point's temporary description, Enter holds it and Escape clears it.
- Whole-diagram fit shows a reading-size transient description while retaining
  the fitted rowScale and point positions. Exit closes it; activation restores
  reading scale and holds the selected original Session.
- At 320px, the overview transient card remains inside the canvas and does not
  cover the target; title size remains 14px. Held selection follows the chart in
  flow. Hovering/leaving another node preserves its stage height and the held
  description, with no outer horizontal overflow or render failure.
- Native node drag/release closes transient hover, produces no held selection or
  pressed point, and returns without residual displacement or transforms. No
  drag-as-click activation is observed in this bounded path.
- Final ordinary reload at 1440px shows matching JS/CSS versions, no duplicate
  IDs or node-title tooltips, source/pin cues present and both descriptions closed.
  Scoped console review contains no error/warning.

## Design And UX Review

The native metadata card supplies context before activation, while selected
description/actions remain stable. Temporary overlay placement keeps the target
visible and avoids hover-driven reflow. Info background/border strengthen the
target without changing source or pin meaning. Tap and keyboard activation retain
access to full values/actions; essential access does not depend on hover.
Existing state, binding, responsive continuity and canvas evaluation rules cover
this change; no new reusable heuristic is proposed.

## Evidence Gaps And Acceptance Impact

- Touch/OS input, alternate engines, intermediate widths, maximum-length content
  and stress are not separately exercised. Non-blocking for this bounded change:
  wide/320px pointer and native keyboard/drag behavior are observed; responsive
  placement and original held actions receive source review.
- Loaded activity, detail/back, source/workspace, preference persistence, reduced
  motion, blank-drag tension and wheel gestures are not rerun. Their established
  handlers/producers retain inherited evidence, not new certification. Source
  review establishes that hover does not enter those write/fetch/selection paths.
  R7 physical wheel review remains open.
- No behavior tests or scripted regression suite are added or run. Static checks
  establish only syntax, whitespace, documentation and repository privacy scope.

## Static Checks

- `node --check src/localbrain/static/session-chart.js`: pass.
- `git diff --check`: pass.
- `scripts/check-repo-privacy.sh`: pass, 1212 candidate files.
- `scripts/build-plan-artifact-catalog.py build` and `check`: catalog current.

## Route And Closeout

- Route: `pass`; no open blocking interaction finding.
- Owner review concerns hover emphasis and description hold/release; no new scope
  decision or work-organization approval is required.
- Source-only before snapshots are task-owned and removed at closeout. No new
  process, exported screenshot, external write, staging, commit or backend restart
  is needed. The ordinary app and refreshed 1440px inspection page remain available.
