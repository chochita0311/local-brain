# SPEC-0084: Project-Grouped Pinned Sessions

## Metadata

- ID: `spec-0084`
- Status: `approved`
- Run ID: `run-20261026-204`
- Prior scroll-containment evidence: [Run 181](../run/run-20261020-181-pinned-scroll-containment.md)
- Attempt: `1`
- Parent Feature: [feat-0084-project-grouped-pinned-sessions](../feature/feat-0084-project-grouped-pinned-sessions.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: read model → grouped inventory presentation → durable contract
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-02`
- Updated: `2026-10-26`

## Source Set

- Owner request and ordering clarification from `2026-09-02`.
- Passed FEAT-0058, FEAT-0059, and FEAT-0069 contracts.
- Current Pinned Sessions query, Sessions template, shared styles, tests, Product Contract, Design Constitution, Design Evaluation, and Interaction Evaluation.
- Screen Alignment mode: `extend`; no external target governs the change.

## Implementation Goal

- Project existing pinned Session rows into deterministic workspace groups and render that hierarchy without changing pin membership or interaction behavior.

## In-Scope Behavior

- Query `sessions.git_branch` and `workspaces.git_root` with every pinned Session.
- Build groups by workspace ID; use current cwd identity only as a defensive fallback when the workspace relation is unavailable.
- Render the home-abbreviated workspace path, falling back to cwd, then workspace display name, then the existing unavailable-path copy.
- Sort groups by Git-backed first, then that case-insensitive displayed heading, then stable identity. Cached display names may use mixed formats after incremental imports and must not override an available current path. Do not infer Git state from whether one Session has a branch.
- Preserve the existing activity/pin/ID order while appending Sessions within each group.
- Render a semantic group heading, source cue, title, optional branch, and activity date. Keep the total pin count based on Session membership.

## Out-Of-Scope Behavior

- Database or ingestion changes, group controls, group collapse, manual ordering, renaming, or source filtering.

## Affected Surfaces

- `session_pins.py`, `main.py`, `sessions.html`, shared styles, focused tests, and current contract docs.

## Surface Lanes

- Read model:
  - path roots: `src/localbrain/session_pins.py`, `src/localbrain/main.py`
  - dependency order: first
  - implementation responsibility: projection, grouping identity, labels, and deterministic sorting
  - validation evidence: focused unit and route/template tests
- Presentation:
  - path roots: template and shared CSS
  - dependency order: after read model
  - implementation responsibility: native group hierarchy and optional branch line
  - validation evidence: template contracts and rendered supported-width inspection

## State And Interaction Contract

- Grouping is presentation-only and introduces no interactive disclosure.
- In-place pin/unpin panel replacement keeps existing document scroll, panel scroll, and focus behavior.
- Empty, long-name, branchless, multiple-source, wide-scroller, and narrow-flow states remain contained.

## Data And Contract Assumptions

- `workspaces.git_root` is current Git classification truth; `sessions.git_branch` is Session-owned observed branch text.
- Row membership and pin lifecycle remain owned by `session_pins`; grouping creates no persisted state.

## Contract Surfaces

- Producer expectations: pinned query emits workspace identity/Git state and Session branch.
- Consumer expectations: panel consumes ordered groups and retains one destination per Session.
- Generated artifacts: none.
- Source-of-truth owner: Product Contract and workspace/Session Data Model.
- Stale-assumption check: current schema and query producers contain all required fields.

## Required Evaluators

- Contract: grouping remains derived and deterministic without persistence drift.
- Design: hierarchy, containment, spacing, boundaries, and responsive scroll ownership.
- Functional: order, membership, destinations, branch omission, pin refresh, and regression suite.
- UX heuristic: scan improvement and absence of unnecessary controls or repeated Project copy.

## Acceptance Mapping

- Git-first alphabetical groups → grouping helper and focused unit test.
- Newest-first Sessions per group → existing query order plus interleaved-group regression.
- Project heading and branch row → template and UI contract test.
- Preserved recall behavior → existing FEAT-0059 focused suite and browser check.

## Evaluation Focus

- Confirm headings do not create heavier nested-card language, row dividers retain single ownership, and branchless rows do not leave dead space.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-02`: approved after the owner selected Git-first alphabetical group ordering.
- `2026-10-26`: [Run 204](../run/run-20261026-204-pin-order-and-palette-focus.md) aligns sorting with the current home-path heading renderer after the owner reported changed ordering; pin membership, grouping identity and within-group ordering remain unchanged.

## Pinned Scroll Containment Correction — 2026-10-20

The owner reported blank document scrolling below Sessions. The current correction
uses the Frontend profile, Pinned Sessions scroll-containment lane, and
screen-alignment `extend`; [Run 181](../run/run-20261020-181-pinned-scroll-containment.md)
owns execution. The original grouping implementation and evidence remain historical.

Anchor absolutely positioned accessibility text inside the bounded Pinned Sessions
scroller so offscreen rows cannot enlarge the document. Preserve screen-reader
labels, all pins, ordering, recall links, panel height/insets, wide internal scrolling,
narrow document flow, pagination and pin-refresh scroll/focus continuity. Verify
empty/short/overflowing panels, long and short main lists, breakpoint reflow and
repeated scrolling in ordinary web and bundled WebKit. Refresh the delivered app's
CSS, signature and ZIP without changing stored data or backend behavior.
