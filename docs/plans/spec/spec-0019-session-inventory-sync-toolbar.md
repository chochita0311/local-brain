# SPEC-0019: Session Inventory Sync Toolbar

## Metadata

- ID: `spec-0019`
- Status: `approved`
- Run ID: `run-20260718-19`
- Attempt: `1`
- Parent Feature: [feat-0019-session-inventory-sync-toolbar](../feature/feat-0019-session-inventory-sync-toolbar.md)
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: Sessions toolbar → Session-only API → existing incremental scanners
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human request: place the Sessions selector below its description, match the Atlassian selector's position and size, retain a same-row primary `동기화` action, and synchronize only Session-related sources.
- Parent Feature and approved PRD.
- Existing Atlassian toolbar, Sources primary scan action, Session scanner, and `scan_all` implementation.
- Design Constitution, Design Evaluation, Interaction Evaluation, and screen-alignment `match` mode.

## Implementation Goal

- Recompose the Sessions heading into the existing inventory-toolbar family and expose a scoped web synchronization path without duplicating or changing Session ingestion rules.

## In-Scope Behavior

- Move the selector out of the page-heading action region into a following `section-toolbar`.
- Use the Atlassian selector's 58px minimum and content-based segment geometry while retaining an indicator that measures the selected link's real left position and width.
- Add a `primary-button` Session synchronization control on the same row.
- Generalize the browser scan binding so Sources scan and Sessions sync keep independent endpoints and labels, expose immediate working feedback, and do not own the only executable path.
- Version static asset URLs and provide a Session-only form POST redirect fallback so stale or unavailable JavaScript cannot leave the visible action inert.
- Add a scanner-level Session-only report function and `POST /api/sessions/sync`.

## Out-Of-Scope Behavior

- Changing `POST /api/scan`, forced-scan behavior, parser rules, pagination, or Local Context handling.

## Affected Surfaces

- `/sessions`, `/projects`, `/api/sessions/sync`, and `/api/scan`
- Sessions template, shared CSS/JS, scanner composition, application routes, tests, and owner docs

## Surface Lanes

- Frontend: structure and component geometry first; browser states after endpoint binding.
- Backend: reuse `_scan_session_source` for Claude and Codex inside one transaction; do not call `_scan_context_documents`.

## State And Interaction Contract

- Direct and enhanced Sessions/Projects selection remains unchanged.
- The sync button disables during the enhanced request, swaps its visible label, reports success or failure, and reloads only after success.
- Without current JavaScript, the form posts to the Session-only server action and returns to the selected inventory, source, workspace, and page scope.
- Error restores the idle state without changing inventory selection.
- At narrow widths the toolbar overrides the general stacked section-toolbar behavior and retains one row.

## Data And Contract Assumptions

- Session sync uses `force=False`, preserving size, mtime, and healthy-status freshness checks.
- Session scanning continues to remove stale Session source records and reconcile parent relations.
- Local Context source state is untouched by the scoped endpoint.

## Contract Surfaces

- Producer expectations: `scan_session_sources()` returns `claude` and `codex` report keys only.
- Consumer expectations: the Sessions control posts to `/api/sessions/sync`; Sources continues posting to `/api/scan`.
- Source-of-truth owner: scanner composition in `ingest/scanner.py` and ingestion scope in Project Architecture.
- Stale-assumption check: README no longer requires navigating to Sources to import Sessions.

## Required Evaluators

- Contract: source-key scope and full-scan preservation.
- Design: target geometry, row alignment, primary button parity, and supported viewports.
- Functional: request states, endpoint result, reload, and selector regression.
- UX heuristic: label clarity and synchronization-scope honesty.

## Acceptance Mapping

- Toolbar structure maps to `sessions.html` and `.inventory-toolbar`.
- Geometry maps to `.inventory-switch` using existing semantic component roles.
- Session-only scope maps to `scan_session_sources()` and `/api/sessions/sync`.
- Feedback maps to the generalized `bindScanAction()` browser behavior.

## Evaluation Focus

- Ensure `context` is absent only from the scoped report and remains present in `scan_all`.
- Confirm the selector does not stretch back to its previous 100px-per-segment geometry.
- Confirm no button click is performed against the user's runtime data during visual QA.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-18`: approved directly from the human's implementation request; no unresolved scope choice remains.
- `2026-07-18`: runtime correction replaced equal-width tracks with selected-link measurement and added cache-safe progressive enhancement.
