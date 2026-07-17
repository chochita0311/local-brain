# FIX-0014: Context Explorer Continuity

## Metadata

- ID: `fix-0014`
- Status: `complete`
- Run ID: `run-20260716-14`
- Attempt: `3`
- Feature: [feat-0014-local-context-explorer](../feature/feat-0014-local-context-explorer.md)
- Spec: [spec-0014-local-context-explorer](../spec/spec-0014-local-context-explorer.md)
- Execution Profile: `frontend-product`
- Surface Lane: source rail, tree, and preview
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Input Reports

- [Design Attempt 2](../evaluation/eval-0014-design-context-explorer-attempt-2.md)
- [Functional Attempt 2](../evaluation/eval-0014-functional-context-explorer-attempt-2.md)
- [UX Attempt 2](../evaluation/eval-0014-ux-context-explorer-attempt-2.md)

## Fix Scope

- Preserve source tree DOM, disclosure state, scroll, and focus while changing documents.
- Keep URL history and visible, accessible selection synchronized with the preview.
- Reveal selected ancestors on direct entry and history restoration.
- Restore narrow touch geometry and AA contrast for the reported Context metadata.

## Changes Applied

- Added progressive enhancement for Context document links: fetch the existing destination HTML, parse the completed preview, and atomically replace only the preview region.
- Retained normal links as the no-JavaScript and failed-fetch fallback.
- Added abort handling for rapid selection, `pushState`, `popstate`, accessible current-document state, a bounded live announcement, and history focus restoration.
- Added direct-entry ancestor disclosure without replacing user-owned tree state.
- Applied the existing narrow touch-control role to tree document links and stronger semantic text roles to the reported small metadata.
- Added UI contract regression coverage for the preview-only update contract.

## Contract Or Lane Impact

- Contract surfaces touched: existing `/context?root=&document=` HTML route and browser history behavior; no API, schema, persistence, scanning, source-management, or deletion contract changed.
- Surface lanes touched: source tree and document preview only.
- Stale-assumption check needed: completed; normal link fallback, full-document destination, source selection, and unrelated shared interactions remain intact.

## Remaining Issues

- None inside the Attempt 2 finding set.
- The global missing meta description reported under Lighthouse SEO is outside this Feature and does not affect the accessibility result. Its follow-up is tracked in the [Project Backlog](../project/backlog.md).

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-07-16`: targeted Fix Agent pass completed and returned to Design, Functional, and UX Attempt 3 evaluation.
