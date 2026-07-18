# FEAT-0019: Session Inventory Sync Toolbar

## Metadata

- ID: `feat-0019`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Align the Sessions inventory selector with the Atlassian inventory pattern and provide a same-row Session-only synchronization action.

## Acceptance Contract

- The Sessions description is followed by one toolbar row containing `Sessions | Projects` on the left and `동기화` on the right.
- The selector matches the compact Atlassian selector position, content-based segment width, and text-to-selected-surface padding while retaining its sliding selected indicator, direct links, and accessible selection state.
- `동기화` uses the same primary-button contract as the Sources scan action, exposes working, success, and failure feedback, and remains executable through a server POST fallback when browser JavaScript is stale or unavailable.
- The action incrementally scans configured Claude and Codex JSONL sources and reconciles Session hierarchy without scanning Local Context sources.
- The Sessions source-status summary shows only Claude and Codex Session sources and omits the local database path annotation.
- The Sources-wide scan keeps its current Claude, Codex, and enabled Local Context scope.

## Scope Boundary

- In:
  - Sessions header and toolbar structure
  - selector geometry and responsive same-row containment
  - Session-only scan service and API endpoint
  - button loading, success, failure, and reload behavior
- Out:
  - Session ingestion semantics, freshness rules, or source parser changes
  - Sources page layout or full-scan scope changes
  - Local Context registration or scanning changes

## Surface Lanes

- Frontend lane:
  - path roots: `templates/sessions.html`, `static/styles.css`, `static/app.js`
  - dependencies: existing combined inventory and Sources primary action
  - expected evidence: 1440, 700, and 320px rendered geometry plus state semantics
  - evaluator ownership: design, functional, UX
- Backend lane:
  - path roots: `ingest/scanner.py`, `main.py`
  - dependencies: existing incremental Session scanners
  - expected evidence: report contains only Claude and Codex and leaves `scan_all` unchanged
  - evaluator ownership: contract, functional

## Contract Surfaces

- `POST /api/sessions/sync` returns the existing per-source imported, skipped, and failed count shape for `claude` and `codex` only.
- `POST /api/scan` remains the wider Sources scan and continues returning `claude`, `codex`, and `context` reports.

## Required Evaluators

- `contract`: endpoint scope separation and unchanged full-scan response ownership.
- `design`: toolbar position, compact selector geometry, primary action parity, and responsive containment.
- `functional`: loading, success, failure, refresh, and Session/Project switch regression.
- `ux-heuristic`: action naming, same-row hierarchy, feedback clarity, and accidental full-scan risk.

## User-Visible Outcome

- The user can refresh Session and Project activity from the combined inventory without navigating to Sources or unintentionally scanning Local Context documents.

## Entry And Exit

- Entry point: `/sessions` or `/projects`.
- Exit or transition behavior: successful synchronization reloads the current inventory route after bounded feedback.

## State Expectations

- Default: selector and enabled `동기화` action share one row.
- Loading: action is disabled and reads `동기화 중...`.
- Error: the action is restored and an adjacent error region explains failure.
- Success: imported change count appears before the current route reloads.

## Dependencies

- FEAT-0015 through FEAT-0018 remain passed.

## Likely Affected Surfaces

- `src/localbrain/templates/sessions.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/main.py`
- tests and durable ingestion/navigation owner docs

## Pass Or Fail Checks

- Pass if the toolbar matches the approved row and geometry at supported widths.
- Pass if Session sync cannot invoke the Local Context scanner.
- Pass if Sources full scan still includes Context.
- Pass if selector navigation, history, and accessible current state remain intact.

## Regression Surfaces

- `/sources` full scan
- `/sessions`, `/projects`, and browser-history switching
- Session pagination, filters, and Subsession disclosure

## Harness Trace

- Active spec doc: [spec-0019-session-inventory-sync-toolbar](../spec/spec-0019-session-inventory-sync-toolbar.md)
- Active run: [run-20260718-19-session-inventory-sync-toolbar](../run/run-20260718-19-session-inventory-sync-toolbar.md)
- Execution profile: `fullstack-product`
- Latest evaluator report: [eval-0019-functional-session-inventory-sync-toolbar](../evaluation/eval-0019-functional-session-inventory-sync-toolbar.md)
- Latest fix note: [fix-0019-runtime-sync-and-indicator-geometry](../fix/fix-0019-runtime-sync-and-indicator-geometry.md)

## Continuity Notes

- `2026-07-18`: human approved the toolbar placement, primary action parity, and Session-only synchronization scope for implementation.
- `2026-07-18`: implementation and required evaluators passed; rendered browser capture remains an explicit environment evidence gap rather than an observed viewport claim.
- `2026-07-18`: human runtime review found a non-responsive JavaScript-only action and unequal text-to-selection padding. FIX-0019 added versioned static assets, a form POST fallback, immediate working feedback, and a measured content-width slider.
- `2026-07-18`: human review narrowed the Sessions source-status summary to Claude and Codex and removed the database-path annotation.
