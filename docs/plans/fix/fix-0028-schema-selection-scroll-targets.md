# FIX-0028: Schema Selection Scroll Targets

## Metadata

- ID: `fix-0028-schema-selection-scroll-targets`
- Status: `complete`
- Run ID: `run-20260718-33`
- Attempt: `2`
- Feature: [feat-0028-in-app-schema-explorer](../feature/feat-0028-in-app-schema-explorer.md)
- Spec: [spec-0028-in-app-schema-explorer](../spec/spec-0028-in-app-schema-explorer.md)
- Execution Profile: `frontend-product`
- Surface Lane: `/schema` selection, focus, and document scroll
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Input Report

- Human review identified two context-loss cases: selecting a Model area and selecting an Owned object both focused and scrolled to the top-level `Schema` heading instead of the newly selected content.

## Fix Scope

- Move Model area selection to the selected relationship-map heading.
- Move Owned object selection to the selected table-detail heading.
- Preserve direct-entry position, ordinary no-script links, progressive Mermaid rendering, latest-request wins, and back/forward restoration.

## Changes Applied

- Added explicit page, area, and table focus roles to the existing Schema headings.
- Derived the contextual destination from the canonical URL and used the closest available heading as a bounded fallback for normalized invalid states.
- Applied the existing sticky-shell scroll offset to every Schema focus target.
- Extended source and browser QA to assert target identity, sticky-shell clearance, nearest reachable document position, history restoration, rapid selection, and existing responsive states.

## Contract Or Lane Impact

- Contract surfaces touched: FEAT-0028 contextual focus and document-orientation behavior only.
- Surface lanes touched: frontend `/schema` interaction module, Schema template, shared stylesheet, and browser/source tests.
- Alignment authority: `screen-alignment` extend mode; the existing Explorer hierarchy, tokens, shell, and responsive breakpoints remain unchanged.
- Stale-assumption check needed: none; the packaged schema and route/query contracts did not change.

## Validation

- JavaScript syntax checks passed for the Schema interaction and browser QA modules.
- The complete automated suite passed: 108 tests.
- Browser QA passed at `1440`, `920`, `700`, and `320`, including contextual area/table focus, exact or nearest reachable sticky offset, back/forward, rapid selection, no-script, Mermaid failure, warm-cache, and invalid-query states.
- Browser evidence: `/tmp/localbrain-schema-scroll-browser-qa`.
- Repository privacy check passed across 365 candidate files.

## Remaining Issues

- None in scope.

## Return Decision

- `pass`
