# FEAT-0040: Local Context Navigation Order

## Metadata

- ID: `feat-0040`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Place Local Contexts directly after Sessions so the primary navigation follows the owner's intended work sequence without changing routes or shell behavior.

## Acceptance Contract

- Main navigation presents `04 Sessions`, `05 Local Contexts`, `06 Atlassian`, `07 Sources`, and `08 Schema` in that order.
- Every destination keeps its existing route, label, group ownership, active-state semantics, keyboard reachability, and narrow-screen access.
- Reordering does not change content routes, introduce a new destination, or alter the persistent shell geometry.

## Scope Boundary

- In:
  - order and numeric prefixes of Sessions, Local Contexts, Atlassian, Sources, and Schema
  - active state, focus order, and narrow horizontal navigation verification after reorder
- Out:
  - route, group, label, icon, search, shell geometry, theme, or destination behavior changes
  - Local Context content, Markdown rendering, source tree, or resizable pane behavior

## Contract Surfaces

- Shared shell destination order and labels.
- Existing destination URLs and `active_page` mapping.
- Keyboard and visual order across desktop, compact, and narrow shell layouts.

## Required Evaluators

- `design`: destination order, numbering, active treatment, and responsive shell stability.
- `functional`: route destinations, active mapping, tab order, and narrow navigation reachability.
- `ux-heuristic`: Sessions-to-Local-Contexts adjacency and orientation after reorder.

## User-Visible Outcome

- The user finds `05 Local Contexts` immediately after `04 Sessions` while every existing destination continues to work as before.

## Entry And Exit

- Entry point: any route rendering the shared shell.
- Exit or transition behavior: selecting a destination opens its unchanged route and marks exactly that destination active.

## State Expectations

- Default: the approved eight destinations remain present in their existing groups.
- Loading: shell continuity remains unchanged during route navigation.
- Empty: not applicable.
- Error: an invalid route does not appear as a valid active destination.
- Success: visual order, keyboard order, destination, and active state agree.

## Dependencies

- FEAT-0003 Shared Shell And Global Navigation must remain `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/base.html`
- shared-shell UI contract tests
- browser evidence at representative desktop and narrow widths

## Pass Or Fail Checks

- Pass if the visible and keyboard order is `04 Sessions`, `05 Local Contexts`, `06 Atlassian`, `07 Sources`, `08 Schema`.
- Pass if every item reaches its existing route and exposes the correct active state.
- Pass if all destinations remain reachable at `1440`, `920`, `700`, and `320` widths.
- Fail if numbering and DOM order disagree, a route changes, a destination disappears, or the active indicator moves to the wrong item.

## Regression Surfaces

- all shared-shell routes
- navigation grouping, active state, keyboard focus order, and narrow overflow
- global search and workspace header continuity

## Harness Trace

- Active spec doc: [spec-0040-local-context-navigation-order](../spec/spec-0040-local-context-navigation-order.md)
- Active run: [run-20260719-45-local-context-navigation-order](../run/run-20260719-45-local-context-navigation-order.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [Design](../evaluation/eval-0040-design-local-context-navigation-order.md), [Functional](../evaluation/eval-0040-functional-local-context-navigation-order.md), [UX Heuristic](../evaluation/eval-0040-ux-local-context-navigation-order.md)
- Latest fix note:

## Continuity Notes

- `2026-07-19`: initial draft kept navigation order separate because it is independently shippable and has no dependency on the Markdown renderer or Local Context content changes.
- `2026-07-19`: the sequential PRD-0006 workflow activated FEAT-0040 as the only in-loop Feature under `frontend-product`; `screen-alignment` uses extend mode on the shared shell navigation lane.
- `2026-07-19`: Attempt 1 passed Functional and UX evaluation plus Design with a non-blocking rendered-browser evidence suggestion; DOM, live server markup, responsive invariants, 164 tests, and privacy passed.
