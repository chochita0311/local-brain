# FIX-0019: Runtime Sync And Indicator Geometry

## Metadata

- ID: `fix-0019-runtime-sync-and-indicator-geometry`
- Status: `complete`
- Run ID: `run-20260718-19`
- Attempt: `2`
- Feature: [feat-0019-session-inventory-sync-toolbar](../feature/feat-0019-session-inventory-sync-toolbar.md)
- Spec: [spec-0019-session-inventory-sync-toolbar](../spec/spec-0019-session-inventory-sync-toolbar.md)
- Created: `2026-07-18`

## Trigger

- Human runtime review reported that the Sessions `동기화` button appeared inert after restart.
- Human visual review reported that the selected white surface did not keep the same text-relative horizontal margin as Atlassian's `Jira | Confluence` control.

## Classification

- `implementation bug`
- The approved scope and Session-only synchronization contract remain correct.

## Root Cause

- The action depended entirely on a JavaScript listener while static assets used stable unversioned URLs. A browser retaining the earlier script could render the new button without binding it.
- The selector used two forced equal-width grid tracks. Atlassian uses a per-label minimum width plus shared padding, so the selected white surface and text had different relative margins even though both controls referenced 58px.

## Fix

- Add file-derived versions to static asset URLs.
- Make the Sessions action a real POST form with a safe scope-preserving redirect fallback.
- Keep enhanced fetch behavior and expose `동기화 중...` immediately with `aria-busy`.
- Share the exact segment padding rules with Atlassian and measure the selected link's real left position and width for slider movement.

## Verification

- Actual `POST /api/sessions/sync`: 200 in 0.26 seconds; Claude and Codex reports only.
- Temporary no-JavaScript form POST: 303 with source, workspace, and page scope preserved.
- Temporary rendered HTML: numeric file-derived versions on CSS and JavaScript URLs.
- 46 unit tests, Python compilation, JavaScript syntax, diff whitespace, and privacy checks passed.
- In-app rendered capture remains unavailable in this environment; no unobserved pixel state is claimed.

## Result

- The button no longer has a JavaScript-only dead path, and the slider geometry now follows the same label-relative padding model as the Atlassian control.
