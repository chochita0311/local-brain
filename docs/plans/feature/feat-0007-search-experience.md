# FEAT-0007: Search Experience

## Metadata

- ID: `feat-0007`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Give the user one coherent search entry and results experience that preserves the query, distinguishes result provenance, contains long excerpts, and separates an empty query from no matches.

## Acceptance Contract

- Global search and page search submit to the existing `/search?q=` contract and visibly preserve the active query.
- Result rows distinguish Session, Document, and supported source identity without confusing result type with status.
- Long titles, excerpts, paths, and mixed scripts remain readable and contained.
- Empty-query and zero-result states explain different conditions and provide an appropriate next action.

## Scope Boundary

- In:
  - shared global-search handoff into `/search`
  - Search heading, query field, submit action, result count, result rows, excerpts, type or provenance labels, and empty states
  - responsive search composition
- Out:
  - search ranking, indexing, query parsing, result schema, or FTS behavior
  - autocomplete, saved searches, new filters, pagination, or external search
  - redesign of destination detail pages

## Contract Surfaces

- `/search?q=` route and query limit
- current search-result fields and destination links
- shared-header global search from `feat-0003`

## Required Evaluators

- `design`: query hierarchy, result rows, excerpts, provenance labels, focus, and responsive containment.
- `functional`: submission, query retention, result links, empty query, no matches, and keyboard behavior.
- `ux-heuristic`: search-state clarity, result scan friction, and affordance accuracy.

## User-Visible Outcome

- The user can search from the shared shell, understand what each result is and where it came from, and open the correct existing detail surface.

## Entry And Exit

- Entry point: shared global search, Search navigation link, or direct `/search?q=` URL.
- Exit or transition behavior: result selection opens the existing Session or Document destination while retaining understandable shell context.

## State Expectations

- Default: blank search invites a query without pretending that no data exists.
- Loading: current server navigation keeps the shell stable; no new client loading contract is introduced.
- Empty: blank query and zero matching results use different messages.
- Error: route or result errors are not converted into a no-match state.
- Success: query, result count, type, provenance, excerpt, and destination remain clear.

## Dependencies

- `feat-0001`, `feat-0002`, and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/search.html`
- global search structure in `src/localbrain/templates/base.html` only when Search handoff requires alignment
- search, result, provenance, excerpt, empty-state, and responsive selectors in `src/localbrain/static/styles.css`

## Pass Or Fail Checks

- Pass if submitting from global and page search preserves the exact visible query.
- Pass if blank query and no-match states are distinct.
- Pass if every result retains a correct destination and readable source or type cue.
- Pass if long excerpts and paths remain contained from desktop to `320px`.
- Fail if visual changes alter result ranking or query meaning.
- Fail if a full row advertises clickability beyond its actual link target.

## Regression Surfaces

- global search and `/search?q=` submission
- Session and Document result links
- search-result provenance and current query retention
- shared shell focus and navigation

## Harness Trace

- Active spec doc: [spec-0007-search-experience](../spec/spec-0007-search-experience.md)
- Active run: [run-20260716-07-search-experience](../run/run-20260716-07-search-experience.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0007-ux-search](../evaluation/eval-0007-ux-search.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft separated Search from general inventory work because query states and destination integrity form one independent loop.
- `2026-07-16`: executed and passed in `run-20260716-07`.
