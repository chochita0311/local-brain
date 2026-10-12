# SPEC-0114-R5: Session Chart Controls And Pins

## Metadata

- ID: `spec-0114-r5`
- Status: `superseded`
- Superseded by: [SPEC-0114-R6](spec-0114-r6-local-chart-preferences-and-pan-space.md); pin/toolbar contracts remain unless explicitly revised there.
- Run: [RUN-145](../run/run-20261007-145-session-chart-controls-and-pins.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `frontend-product`
- Surface Lanes: `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-07`

## Approved Direction

The owner directly requests Project filtering in the former date-navigation
position, removal of horizontal/date and vertical toolbar navigation, durable
Project choices, a native pinned Session cue, and revised view/source separators.
Extend the current screen under the Design Constitution. R4 camera, compact
tracks, overview, drag, keyboard, selection and recovery contracts remain.

## Contract

- Put the existing Project disclosure at the left of the Chart toolbar. Remove
  the toolbar date range and earlier/later/up/down buttons. Retain axis dates,
  blank dragging, chronological keys, zoom, fit and selected focus.
- Persist Project visibility in browser-local durable storage per source and
  workspace. A fresh tab/document reads that preference even without navigation
  state. Migrate existing tab visibility when no durable preference exists;
  durable all-selected overrides stale tab hiding. Validate folder keys, retain
  temporarily absent hidden keys, and keep camera/selection in tab storage.
  Storage denial must not prevent in-memory filtering or existing navigation.
  Browser storage clearing, another browser/origin and private-mode expiry are
  outside the persistence guarantee. Never write these choices to SQLite.
- Read all current eligible pin identities from the already-loaded Sessions pin
  inventory, intersected with Chart records. Add a static native halo and the
  existing pin shape without changing source colors or implying selection.
  A grouped point is marked when any member is pinned, with exact accessible pin
  count and pinned labels in its selector. Preview status reflects the selected
  original member, not the host point. Undated pinned links retain that cue.
  This revision introduces no pin/unpin control or database mutation.
- List/Chart has two adjacent segments without a separator. The shared Sessions
  source filter uses `All` and the Dashboard family separator rule between
  adjacent unselected options. Preserve source/workspace/page destinations.
  Only these shared header details change in List; its rows and recall rail
  remain intact. Workflow Focus and stopped Auto Work remain outside scope.

## Execution And Review

Primary owns implementation and sequential contract/design/functional/UX review.
Use rendered baseline, the Dashboard/pin family, wide/700/320px composition,
fresh-document durable visibility, migration and storage-denial branches, single
and aggregate pin truth, exact-member selection and original List/detail routes.
Existing real pins are read-only; synthetic client metadata may cover absent
pin/undated cases without a fixture database. State their evidence limits.
No automated test suite is added/run. Remove task-owned review pages and
instrumentation at closeout and keep the ordinary application available.

## Open Blockers

None. The owner approves this bounded refinement. Producer SQL, inference,
Git-history reads, recorded membership and work organization are unchanged.
