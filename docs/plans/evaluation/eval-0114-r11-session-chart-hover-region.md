# EVAL-0114-R11: Session Chart Hover Region

## Metadata

- ID: `eval-0114-r11`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R11](../spec/spec-0114-r11-session-chart-hover-region.md)
- Run: [RUN-151](../run/run-20261009-151-session-chart-hover-region.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-09`

## Scope And Evidence

Primary performed sequential contract, rendered design, functional and UX review
using screen-alignment `extend`. Ordinary local Chart inspection used native
browser hover/click, Tab/Escape/PageDown and node drag. Page-side reads inspected
metadata, selection, geometry and scroll. A temporary pointer-inert DOM marker
located passage midpoints so the native hover tool could stop there; it did not
intercept input or add data. Programmatic focus positioned keyboard review.
These are bounded manual observations, not a scripted regression suite or
physical-device certification. Inline narrow rendering was inspected. No private
record names, paths, snapshots or payloads are persisted here.

## Contract Review

- Existing native node and temporary metadata component share hover ownership
  with a convex passage between facing edges. Geometry covers left/right and
  above/below placement without creating an invisible input overlay. Source/pin
  cues, original metadata, held selection/activity and layout remain unchanged.
- Leaving pointer and visible keyboard-focus ownership starts one native 120ms
  exit timer. Reentry cancels it; continuous outside movement does not restart it.
  Existing `setHovered(null)` cancellation paths clear pending callbacks even
  when hovered state is already null. Drag/selection/filter/camera/node removal
  retain their clearing paths. Timer lifecycle receives source review.
- Temporary card input now accepts reading, text selection and local scrolling.
  It has native keyboard focus and Escape release, with no close/member/activity/
  detail actions. Mouse card focus alone does not retain it after pointer exit.
  New hovered metadata resets local scroll to zero; reentry to the still-active
  item within its retained region does not.
- Hover stays ephemeral: no selected-ID, persisted view, activity fetch or
  preference write is introduced. Blank click additionally clears temporary-only
  hover. Node activation, aggregate repeat release, stationary-pointer guard,
  overview focus and held exact-member actions retain their existing meaning.
- Before-source comparison confines R11 to hover ownership, card input and asset
  refs. Final ordinary runtime loads JS `-19` and CSS `-15`; backend/data, List,
  Workflow Focus and Auto Work receive no R11 edits. Owner documents reconcile
  R10's pointer-inert/immediate-exit policy with R11's explicit owner correction.

## Rendered Results

- Before editing, native hover from node to temporary card immediately hid it;
  computed card pointer-events was `none`. After editing, the card receives
  pointer input and remains visible while the pointer rests inside it.
- At 1440px, left and right passage midpoints retain original metadata beyond
  the exit grace with neither node nor card hovered. Crossing into the card and
  returning to the node retains it. Exiting to the toolbar closes temporary hover.
  Point positions, rowScale, stage height and held selection do not change.
- Clicking inside the temporary card produces no pressed point or held preview;
  subsequent pointer exit closes it. Native blank click in the right passage
  closes temporary-only hover without holding a Session.
- A-held/B-hover keeps A's held Session/detail destination and stage geometry.
  Leaving B closes only the temporary description. Native repeat activation
  releases the held node without immediate stationary-pointer reopening.
- Native Tab reveals node metadata; programmatic transfer to the card retains
  visible keyboard focus even with the pointer outside. Native Escape from the
  card closes descriptions. This is focus/activation evidence, not certification
  of the entire tab traversal across the complete inventory.
- Whole overview retains temporary reading metadata without changing rowScale.
  At 320px, an above-card passage midpoint retains it inside the canvas with no
  outer overflow or stage reflow. Native PageDown in the clipped card scrolls
  it by 61px while document Y and chart projection stay unchanged. Escape closes
  it. This scroll observation precedes the final scroll-reset-only refinement;
  source review supports its preserved mechanics and reset on metadata change.
- Final ordinary JS `-19` observation confirms node activation restores reading
  scale and holds selection; repeat activation releases it. Native node drag
  creates no held/pressed selection, stops dragging and leaves no displacement or
  transforms. Temporary hover is observed after release on the underlying point;
  this is hover presentation, not a drag-as-click hold. Source review confirms
  hover/timer clearing during the actual drag.
- Final cache-bypassing reload at 1440px shows matching JS/CSS versions, closed
  descriptions, no observation marker, outer overflow or fallback. Scoped console
  review has no error/warning.

## Design And UX Review

The node and description now behave as one reading interaction while blank
canvas gestures retain their input ownership. Geometry preserves a slow passage,
with finite native grace outside rather than indefinite hover after departure.
The existing card, source colors, pin cue, typography, overlay and focus treatment
remain native. Keyboard and held actions retain access to full values; essential
access is not hover-only. Existing composite-state, overflow-reveal and interaction
continuity rules cover this refinement; no new reusable heuristic is proposed.

## Evidence Gaps And Acceptance Impact

- Narrow below placement, exhaustive widths/scales, maximum-length stress,
  alternate engines, OS/touch and physical wheel input are not separately rerun.
  Non-blocking for the bounded correction: left/right and narrow above passage
  retention are observed; the mirrored below geometry and cancellation lifecycle
  receive source review. Native timings are not a high-resolution duration trace.
- Local wheel and touch scrolling and nonzero-scroll retargeting are not
  separately observed on the final build. Non-blocking: native PageDown local
  scrolling is observed during the Run; final code resets scroll synchronously
  only when hovered metadata changes and otherwise retains the original scroller.
- Loaded activity, exact-member selector, detail/back, preference persistence,
  source/workspace, reduced motion and blank-drag tension are not rerun. Their
  producers and handlers retain inherited evidence rather than new certification.
  R7 physical wheel review remains open.
- No behavior tests or scripted regression suite are added or run. Static checks
  support only syntax, whitespace, privacy and document-catalog scope.

## Static Checks

- `node --check src/localbrain/static/session-chart.js`: pass.
- `git diff --check`: pass.
- `scripts/check-repo-privacy.sh`: pass, 1215 candidate files.
- `scripts/build-plan-artifact-catalog.py build` and `check`: catalog current.

## Route And Closeout

- Route: `pass`; no blocking hover-continuity finding remains.
- Owner screen review concerns moving into the description and reading there.
  No new work-organization decision or producer approval is required.
- DOM passage witnesses are removed; source snapshots are removed at closeout.
  No new process, exported screenshot, external write, staging, commit or backend
  restart is required. The ordinary app and released-description 1440px page remain.
