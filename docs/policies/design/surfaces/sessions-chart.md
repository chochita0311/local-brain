# Sessions Chart Design

This is the durable Chart presentation companion of the [Design Constitution](../design-constitution.md).
[Sessions](../../project/sessions.md) owns source eligibility, timestamp projection,
HTTP inputs and private preference persistence; this file owns layout, controls,
geometry, pointer/keyboard behavior, motion and visual recovery.

## Layout And Interaction

Chart removes the secondary recall column and uses the full main content width.
It places actual recorded time from left to right and uses one
recorded launch folder per Project band on Y. The fixed left axis sorts folder
names case-insensitively, breaks ties by full path and puts missing paths last;
equal leaf names remain separate and their paths stay inspectable. It does not
merge Git roots or infer actual work identity. Project headings retain their names
while their branch tracks scroll and scale with the vertical projection. Homes remain fixed per displayed Project set;
zoom changes their screen projection, and hiding Projects closes empty row space.

Stored branch names form rightward guides inside each band. Exact `HEAD` is a
checkout reference, excluded from branch names only in layout while remaining
inspectable as original metadata. Folders with only HEAD/missing values use one
line without an empty baseline or fork curve. When named branches exist, observed
master is the baseline, otherwise observed main; feature-only data uses a neutral
guide without inventing a branch. HEAD/missing records in mixed named-branch
folders share one `브랜치 없음` track and are never assigned to master/main.
This layout rule does not infer repository status. Branch name order is
fixed. Each branch guide starts at first retained observation; its curved join
is a layout aid and never denotes actual Git ancestry, merge, duration or work
completion. Keep this meaning in recorded preview metadata and owner documents
without adding a footer legend, instruction paragraph or prose to nodes.

Reading-scale native source circles retain 40px targets and short titles. Pixel-overlap
on the same track exposes an exact count and a native selector for every original
Session. Mixed-source aggregates use a neutral cue; the selector and preview
retain each original source. Membership remains independent of List pagination.
The lower count/legend/instruction region is omitted. A native Project checkbox
disclosure above the diagram owns all/partial/none visibility, shows paths for
equal names and reserves an inner scrolling region inside its stable menu frame. No
decorative star field or inferred Session relationship is introduced.

The Project disclosure owns the left toolbar position. Toolbar date range and
directional buttons are omitted; axis dates,
dragging and keyboard navigation retain time/vertical exploration. Project choices
persist per source/workspace in the private LocalBrain DB and are shared by browsers
using that DB, separately from tab camera state. Browser site-data clearing does not
erase confirmed visibility. Genuine preference load/save failure exposes contextual
recovery beside the control and keeps filtering/navigation usable. List/Chart is a two-segment control without a divider. Its shared source
filter uses `All` and the Dashboard separator between adjacent unselected options.

Pinned Session points retain source colors and add a static halo in the existing
pin info color plus the established filled pin shape. Do not pulse the halo or
reuse the selection target background as pin state. Aggregates show the cue if
any member is pinned and expose exact pin counts through accessible names; selector
and preview status belong to each original Session. Overview retains the scaled
pin cue and undated pinned links retain text status. Pin display creates no new
mutation action.

Empty-space drag, zoom, whole-diagram fit and
chronological keyboard navigation expose offscreen history. Reading branch pitch
is 48px, with 40px Project headings and 8px separation. Ordinary Cmd/Ctrl-wheel
and visible/keyboard zoom reduce vertical geometry down to all displayed Projects
fitting the canvas. Cmd/Ctrl+Shift-wheel changes time spacing alone around the
pointer; vertical projection, camera, target size and preview mode stay stable.
Shift-wheel pans horizontally from either wheel axis, using the dominant component
once for diagonal input. Preserve bounded movement, independent tab X/Y state and
vertical position when only time is fitted or the viewport resizes. Whole-diagram
fit still resets both axes. Overview retains Project/branch names at every scale:
name typography, branch-label height and vertical padding shrink with rowScale.
Project heading measurement uses its resolved scaled line height, preserving room
for the first branch. No minimum-font or scale cutoff hides branch labels;
whole-fit text may be tiny. Fixed axis width/insets, reading-scale tokens,
ellipsis and full-name titles stay native, and time-only zoom keeps label size.
Overview omits Project paths and crowded Session titles and scales plot targets;
choosing a Project or Session restores reading scale. It withholds the held preview
while preserving selection; temporary hover descriptions remain available at
reading size without changing scale. Fit brings the whole canvas into view. Ordinary scroll
belongs to the map when it can move and to the document otherwise; empty-space
touch retains vertical document scrolling. Small point pulling and gentle
same-track response remain transient around fixed time anchors; guides never
move. Release settles exactly and stops animation. Cancellation, camera change,
resize and page hiding clear offsets/capture; reduced motion omits peer motion
and returns immediately. No dragged layout is persisted.

Date-end panning reserves the same target-frame inset at both ends: four card
spacing units (64px), capped by 20% of usable width and free projected-target space
on narrow plots. Source circles are centered in their 40px targets; fit and limits
account for those targets, and guides retain the same frame inset. The existing
reading-scale cap may leave more unused space for a short observed period. Bounds
use visible observations and selected visible activity; filtering retains endpoint
anchoring, refits whole-time fit or preserves a bounded middle time anchor. Only
blank dragging can stretch at most two native control widths (80px), capped at
half usable plot width, beyond the first/latest visible observation with resistance
and return. Transient overshoot is never saved. Floating reading
preview space is reserved when focusing/bounding time content.

Session-node hover/focus uses the existing information surface and border,
focus-width border and card elevation so the target is apparent. Source fills,
static pin halo/icon and selected/pressed meaning remain separate. Original source,
title, time, recorded path/branch, pin status and overlap count appear in a
temporary native preview; avoid a duplicate browser-title tooltip. The node,
description and geometric passage between facing edges form one hover region,
including left/right and narrow above/below placement. Moving into or resting in
the card keeps it open. Exit from the complete pointer/focus region closes it
after the native state-duration grace (120ms); reentry cancels the pending exit.
Keyboard focus in either the node or card retains it, with Escape dismissal from
both. Clicking text in the temporary card does not hold selection. Activation of
the node holds the selected Session;
repeat activation of the same aggregate, blank click, close or Escape releases it.
After release, another node projected under a stationary pointer must not reopen
a card until deliberate pointer movement. Keyboard focus and activation retain
accessible description and pressed state. Drag/pull input must not become a click.

The compact held preview floats wide and follows the chart at 700px or narrower.
Hovering another point adds a separate instance of the same native metadata
component, leaving the held description and activity unchanged. Temporary cards
overlay on narrow screens too, reserve no camera space, support pointer reading,
text selection and local scrolling, and omit close, exact-member control, activity
and detail actions; overlap counts
remain visible. Place them beside the point, or above/below when necessary, within
the canvas frame without covering the target. Hovering a held aggregate describes
its selected original member. Hover never saves view state or loads activity.
New transient descriptions reset internal scroll to the top; mouse text clicks
do not create lasting focus retention.
The passage retains hover geometrically without an invisible input overlay;
blank canvas click/drag remain available. Blank click clears a temporary-only
description too. Temporary-card input does not pin, navigate or drag the chart.
Camera/scale/filter/resize, true drag, cancellation, page hiding and node removal
clear transient hover and pending exit callbacks. Hidden selection retains the existing filter behavior.
A held wide pane may shift time only as needed to keep the activated point
reachable for repeat click; reading hold otherwise retains position. Existing
overview activation restores reading focus.
Recorded path/branch, activity observations, undated counts, detail return and
fallback retain explicit meaning. Script/render/storage or activity failures
preserve List/detail access and reduced motion retains controls and selection.
Showing or changing a hover description does not change the camera, scale, page
layout, held selection or loaded activity.

## Scope And Recovery Details

Project search narrows the menu only. Hiding a Project closes its row gap and
clears hidden selection/activity; it does not delete/classify records, change the
source/workspace scope or filter List. Database loss needs backup recovery or
reselection; unconfirmed choices are not saved. The Session contract owns exact
preference migration and HTTP validation.

The node/card/passage share pointer ownership; visible keyboard focus can retain
the card, while mouse text clicks do not create lasting focus retention. Node
hover descriptions have no member/activity/detail actions; held previews retain
exact-member selection, activity actions and the ordinary detail link.

Selected Event points may share a pixel bucket: expose the exact occurrence
count and observed endpoint times without a duration bar or Session edge.
Camera rendering never changes source or preference data. Camera, resize, page
hiding and cancellation clear offsets/capture and pending exit callbacks; there
is no idle simulation loop.

Only visible first/latest Project observations and explicitly loaded activity of
a visible selection determine panning bounds. Hiding an endpoint contracts the
bound unless another visible observation retains that time. Reserve floating
preview space; guide ends use the same frame inset. Short periods can underfill
the right side at the existing reading-scale cap. The internal time origin
remains fixed. Whole-time fit or a reached date end can prevent further bounded
movement.

Detail return retains Chart/source/workspace/List-page orientation, tab-local
camera/selection/vertical scale and database-owned Project visibility. Missing
script, rendering failure and empty/undated scopes preserve List/detail access;
failed activity retrieval permits retry. Browsing invokes no ingestion or model.
Undated Sessions remain accessible.

## Camera Entry And Transient State

Initial reading entry fits time and starts at the alphabetical top. Whole fit
also scales Y and brings the canvas into view. Fit retains the existing base
reading-scale/one-day cap, so short periods can underfill the right side.
A cursor guard prevents stationary-pointer hover reappearance after reprojection;
genuine movement resumes it. Small transient drag offsets couple only same-track
neighbors; a damped spring returns to exact anchors, with no idle simulation or
persisted layout. Guides and activity times stay fixed.
The original time anchor remains indicated during a pull. Pull distance stays
bounded to its track; pulling creates no relationship or persisted position.
