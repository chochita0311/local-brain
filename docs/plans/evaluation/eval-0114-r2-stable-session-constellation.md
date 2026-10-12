# EVAL-0114-R2: Stable Session Constellation

## Metadata

- ID: `eval-0114-r2`
- Status: `complete`
- Evaluator Types: `contract`, `design`, `functional`, `ux-heuristic`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Spec: [SPEC-0114-R2](../spec/spec-0114-r2-stable-session-constellation.md)
- Run: [RUN-142](../run/run-20261006-142-stable-session-constellation.md), attempt `1`
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Created: `2026-10-06`

## Scope And Evidence

The primary performed sequential contract, rendered design, functional and UX
review of the owner-approved fixed irregular field and elastic point dragging.
Screen-alignment adapt preserves native typography, surfaces, source colors and
shell. Chochita/Obsidian contribute exploration and motion direction only. No
private Session content, identifiers, inventory totals or captures are retained.

Review used the ordinary running local application, a separate isolated browser
context, real browser drag/click/key gestures and temporary numeric DOM/event
instrumentation. The isolated context and review-only markers are removed at
closeout. No new fixture database, preview server or automated test was created.

## Contract Findings

- Home Y is seeded from Session ID and collision-resolved once at a fixed
  reference time scale. No cwd/branch/title/project grouping participates. X
  remains the observed time projection; camera/zoom updates do not rerun homes.
  Identical scope/data reproduces homes; scope/data changes may resolve them
  differently. Recorded source cues retain their original meanings.
- Transient offsets, velocities and geometric neighbor weights live only in
  memory. Motion painting does not redraw the axis, change activity timestamps
  or save positions. Local response is capped at 24 nearby peers and creates no
  edge. Rest anchors remain visible during displacement. Release settles to
  exact zero and stops the animation loop.
- Session storage contains only center time, scale, camera Y, selected ID and
  List page. A cold context with prior-version state and a synthetic extreme
  lane Y discards that lane coordinate. Reload and detail return retain the
  valid current camera and selection without offsets.
- This Run changes only Chart assets/template URLs and owner documents. The
  first increment's read projections, activity GET, List row template, detail
  navigation, Workflow Focus and Auto Work code were not edited. Changed-fact
  owners and planning links now describe stable homes and transient motion.

## Rendered Design And Functional Findings

- The baseline's aligned rows and large square source cards are replaced by
  irregular native 24px source circles with 40px targets. Dense scales keep
  points and suppress overlapping captions; selection/preview exposes full
  titles. A compact focus caption stays outside its 40px hit area and ignores
  pointer events, preserving neighboring targets.
- Measured homes remain equal across selection, zoom, focus, activity expansion,
  resize and reload for the same records. Full-period and source-specific Chart
  render without the Pinned Sessions column; whole/visible counts retain their
  distinction. Selected activity remains observation points, with the existing
  detail destination and no inferred duration.
- Actual node dragging moves the point and nearby peers, displays the original
  anchor and returns all transforms to zero after release. Selection stays
  unchanged by the drag. A subsequent ordinary click selects exactly one point
  and opens its preview. The spring runs while returning and schedules no new
  spring frames after settling.
- During a real captured gesture, an injected pointer-cancel signal clears all
  displacement, capture and dragging state immediately. Native End/Escape keys
  select the latest point, reveal its preview and clear selection respectively.
- Real empty-space dragging changes the time camera without changing homes or
  introducing point offsets. Existing time/zoom/focus controls stay usable.
- Detail's ordinary Chart backlink restores display, camera time, zoom, camera Y,
  selection and homes. Its Workflow link retains the existing destination.
- Effective 1440, 700 and 320px browser viewports show no outer horizontal
  overflow. The preview floats at desktop and follows the canvas at 700/320px;
  essential controls and detail actions remain inside the viewport. Node targets
  reserve touch dragging while empty canvas keeps vertical document scrolling.
- All-source and Codex Company scope use the shared renderer and original source
  denominator. Default List still renders its rows, pagination and Pinned
  Sessions column, with no Chart script. Warm navigation loads the revised
  Chart asset URLs and binds the revised controls. Inspected pages have no
  application console warnings or errors.

## Reduced Motion And Evidence Limits

A controlled `matchMedia` response in the isolated context exercised the reduced
motion JavaScript branch with a real drag: only the pulled point moved, release
restored it immediately and scheduled zero spring frames. Source review confirms
the preference-change handler calls the same cancellation owner. This proves the branch;
it does not certify a physical operating-system setting change. Native media
query styles and cancellation handlers were reviewed in source.

Automated regression suites, physical touch/trackpad permutations, actual OS
motion-setting changes and large-corpus stress were not run. These gaps are
non-blocking for the Spec's inspectable frontend revision; the required mouse
gesture, fixed-coordinate, state-return and viewport evidence is directly
observed. Prior empty/undated/error/no-script/storage recovery evidence remains
in [EVAL-0114](eval-0114-observed-session-chart.md); those fixture states were
not rerun here and their unchanged fallback paths receive source review only.
Owner preference for density and spring strength remains the next human review.

## Checks And Route

JavaScript syntax, `git diff --check`, repository privacy and generated artifact
catalog checks pass within their respective scopes. No automated test result is
claimed. Source owners and current planning routes have no remaining collision-row
assumption; the first Spec/Run/evaluation retain that historical design explicitly.

`pass` for this revision with the evidence limits above. Keep the local Chart
available for owner inspection; preserve the existing List, Workflow Focus and
stopped Auto Work boundaries.
