# FIX-0023: Sessions Dashboard Scope Continuity

## Metadata

- ID: `fix-0023-sessions-dashboard-scope-continuity`
- Status: `complete`
- Run ID: `run-20260718-22`
- Attempt: `2`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Execution Profile: `frontend-product`
- Surface Lane: Sessions Dashboard scope controls and browser history
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Input Reports

- Human runtime review found that Tokens/Cost and Source/Model/Project changes performed full-document navigation and reset the main page scroll position.
- Existing FEAT-0022 acceptance requires scope changes to update the same dashboard while preserving the persistent shell, URL state, selected state, and post-rerender control binding.

## Fix Scope

- Keep the document scroll position stable while changing link-backed Sessions Dashboard scope controls.
- Replace only the Sessions Dashboard region, not the persistent shell or full document.
- Preserve normal links as the no-JavaScript and failed-fetch fallback.
- Keep history, selected state, focus, local-time formatting, rapid-click cancellation, and an accessible transition announcement coherent.

## Changes Applied

- Added one replaceable `data-usage-dashboard` region and explicit scope-control identity to Source, Range, Tokens/Cost, and Source/Model/Project links.
- Added delegated progressive enhancement that fetches the existing GET destination, parses its completed server-rendered dashboard, swaps only the owned region, updates browser history and title, restores the captured document scroll position, and focuses the equivalent selected control without scrolling.
- Added `AbortController` handling for rapid changes, `popstate` restoration, an `aria-live` status, and a session-storage scroll fallback before normal full navigation on request failure.
- Refactored local-time formatting so newly adopted dashboard content receives the same client-side formatting as initial content.
- Added UI contract coverage for the partial replacement and scroll-preservation behavior.

## Contract Or Lane Impact

- Contract surfaces touched: existing `/sessions-dashboard` GET destinations and browser history behavior; query names, server read model, database, pricing, and visual styling remain unchanged.
- Surface lanes touched: frontend interaction only.
- Stale-assumption check needed: completed; normal link fallback, direct entry, back/forward routing, server-rendered selected state, and unrelated shared interactions remain intact.

## Remaining Issues

- Direct scripted browser interaction was unavailable in this environment. Static JavaScript validation, 77 automated tests, and a temporary-server `200` response verified the replacement hooks and asset delivery; the exact live scroll coordinate remains a human-runtime confirmation point.
- A separate ccusage comparison invalidated the current Codex normalizer and pricing acceptance basis. That is a FEAT-0020 Spec issue and was not absorbed into this frontend fix.

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-07-18`: targeted Fix Agent pass completed without changing dashboard layout or data semantics; screen-alignment used `extend` mode and preserved the existing visual system.
