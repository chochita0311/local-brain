# SPEC-0114: Observed Session Chart

## Metadata

- ID: `spec-0114`
- Status: `superseded`
- Run: [RUN-141](../run/run-20261006-141-observed-session-chart.md)
- Attempt: `1`
- Parent Feature: [FEAT-0114](../feature/feat-0114-observed-session-chart.md)
- Parent PRD: [PRD-0019](../prd/prd-0019-observed-session-chart.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `observations`, `frontend`, `docs`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-10-06`

## Source Set And Implementation Goal

Implement the approved Feature under the Design Constitution, preserving frozen List and Workflow Focus regions. The Chochita Archive reference contributes spatial node/card exploration and selection-focused navigation; native shell/tokens/data own the implementation.

## State And Interaction Contract

- `/sessions` defaults to List; `display=chart` selects Chart. Switch links retain source/workspace and List page. Source links retain display; sync retains display through the existing inventory action. Projects keeps its existing view contract.
- In Chart, remove the secondary column structurally. The chart's selected preview overlays the canvas on wide screens and follows it on narrow screens.
- One point per retained primary work Session is anchored to the most recent valid `last_event_at` or `started_at`, falling back to valid Event time when both are unusable. Parse into UTC for ordering; labels use browser local time consistently with existing inventory. No time is fabricated.
- All matching Session metadata is available independently of List pagination. Deterministic horizontal time and collision-avoidance lanes support viewport rendering without changing membership or grouping by paths/branches.
- Start with recent observed time visible; earlier history stays reachable through pan/time controls and full-period fit. Selected focus and fit change the camera explicitly. Selection alone preserves layout.
- Node selection exposes source, title, observed time, recorded execution path/branch and a safe detail destination. Activity is an explicit read of the selected Session's retained Event timestamps, with undated count disclosed. Render observations as points; no continuous-duration bar or cross-Session edge.
- Use native buttons/links, visible and programmatic selection, a live status, keyboard chronological traversal and native page scroll. Ctrl/Command+wheel may zoom over the bounded viewport; ordinary wheel scrolls the bounded map or outer document as appropriate. Reduced motion removes animated camera transitions.
- Persist only camera/selection/page in scope-specific browser session storage; storage failure does not prevent browsing. Validate saved IDs/ranges against current data. A detail destination carries Chart display state, and its ordinary Sessions backlink restores Chart; existing Workflow Focus links/contracts do not change.
- Missing/undated Sessions remain reachable; no-script or render failure exposes the existing complete paginated List. A failed activity request has a retry and detail destination, without stale substituted points.

## Data And Contract Assumptions

- Existing `sessions`, `sources`, `workspaces` and `activity_events` own the data. No schema migration, model, source scan, body parse, organization or new runtime cache is introduced.
- Inventory scope is exactly `session_class=work`, `session_role=primary`, with optional stable source key and workspace ID, matching the existing read model. Metadata-only native stubs already have no normalized Session projection.
- Activity GET is `/sessions/{id}/chart-activity`; only retained eligible primary work rows succeed. Return valid ordered timestamp occurrences, total/undated counts and source-backed metadata time fallbacks. No Event text, tool arguments, source paths or source-native IDs.
- Browsing uses SQLite SELECT only. No cutoff, inferred relationship, importance score or closure state is added.

## Affected Surfaces And Acceptance Mapping

- `queries.py` read projections and `main.py` additive display/activity routes: Feature 2–4 and observation regressions.
- `sessions.html`, new `session-chart.js`/`session-chart.css`, existing detail backlink context: Feature 1–6, reference adaptation and responsive/keyboard/round-trip evidence.
- Product, architecture, Design Constitution/governance and planning links: Feature 7 and changed-fact ownership.

## Evaluation Focus

Contract: full matching denominator, field minimization, timestamp validity, eligible-only activity and no database writes. Functional: controls, selection/activity, filters, pagination scope, sync return and detail/back. Design: native tokens, full width and node/card spatial exploration; 1440, 700 and 320px. UX: clear selection versus opening detail, date orientation, recovery and no fixed preview column.

## Open Blockers

None. Later inference is a separate owner decision after inspecting this version.

## Continuity Notes

- `2026-10-06`: The first increment passed under this Spec. Owner review subsequently approved a fixed irregular field and elastic point dragging; [SPEC-0114-R2](spec-0114-r2-stable-session-constellation.md) supersedes the layout/interaction contract for the next Run. Existing data and frozen-region evidence remains historical first-increment evidence.
