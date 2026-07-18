# FIX-0017: Live Runtime Pagination Context

## Metadata

- ID: `fix-0017`
- Status: `complete`
- Run ID: `run-20260717-17`
- Attempt: `2`
- Feature: [feat-0017-paginated-session-inventory](../feature/feat-0017-paginated-session-inventory.md)
- Spec: [spec-0017-paginated-session-inventory](../spec/spec-0017-paginated-session-inventory.md)
- Execution Profile: `fullstack-product`
- Surface Lane: live route and template integration
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Input Reports

- Human live-runtime report: `GET /sessions` returned `500` because `pagination` was undefined in `sessions.html`.
- [Functional Re-evaluation Attempt 2](../evaluation/eval-0017-functional-live-runtime-attempt-2.md)

## Fix Scope

- Restore `/sessions` immediately when a long-running pre-change Python process reads the newly changed Jinja template.
- Apply the new route and schema contract after a controlled server restart.
- Add regression coverage for the partial-reload context boundary.

## Root Cause

- The running `:8000` Uvicorn process still held the pre-change `sessions_page` Python function, which did not provide `pagination`, `selected_inventory`, or Project preload context.
- Jinja template auto-reload independently read the new shared Sessions/Projects template and required those new values, producing a mixed-version runtime and `UndefinedError`.
- Initial completion evidence used a freshly started synthetic server, so it did not exercise this actual long-running-process state.

## Changes Applied

- Added default Session mode, title, and empty Project values at the shared template boundary.
- Render pagination only when the route has supplied the new pagination model. A pre-restart process therefore stays usable instead of returning `500`.
- Added a template regression test that renders the new template with the prior route context.
- Created a local temporary SQLite backup, restarted the actual `:8000` process with the same command, and allowed the compatible migration to run.

## Contract Or Lane Impact

- Contract surfaces touched: shared `sessions.html` context fallback only; the new route remains the authoritative pagination producer after restart.
- Surface lanes touched: live route/template integration and deployment transition.
- Stale-assumption check needed: completed against the actual local runtime and database without exposing indexed content.

## Remaining Issues

- None. The required post-migration source synchronization completed successfully and populated the source-backed hierarchy and branch contract.

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-07-17`: actual runtime failure reproduced, mixed-version boundary fixed, server restarted, migration and source synchronization verified, and functional Attempt 2 passed.
