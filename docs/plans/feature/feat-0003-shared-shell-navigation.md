# FEAT-0003: Shared Shell And Global Navigation

## Metadata

- ID: `feat-0003`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Give every current route one stable, design-system-aligned shell with clear destination identity, global search access, and continuous responsive navigation.

## Acceptance Contract

- The shell preserves the three navigation groups and eight current destinations.
- Active location uses text, surface, and accent rather than color alone.
- Sidebar, workspace header, search, page canvas, and narrow navigation follow the constitution's geometry and semantic roles.
- Route changes preserve shell orientation without blank, placeholder-only, or debug-facing intermediate states.
- Every destination and global search remain keyboard reachable from desktop through the `320px` floor.

## Scope Boundary

- In:
  - persistent sidebar and brand region
  - grouped destination navigation and active treatment
  - workspace header, page location, global search, and Search link
  - desktop, compact, and narrow shell transformations
  - shell focus, hover, overflow, and reduced-motion behavior
- Out:
  - page-family content redesign
  - navigation destination changes
  - new routes, command palette, or mobile-only navigation model
  - search result redesign owned by `feat-0007`

## Contract Surfaces

- current HTML GET routes and `active_page` template context
- global search query parameter `q`
- Design Constitution shell geometry and navigation model

## Required Evaluators

- `design`: shell fidelity, alignment, focus, active state, and responsive containment.
- `functional`: route reachability, current-location state, search submission, keyboard order, and regression.
- `ux-heuristic`: orientation, navigation clarity, overflow friction, and non-blocking polish.

## User-Visible Outcome

- The user can enter any current route, understand where they are, move to every destination, and search without the application feeling visually reloaded or structurally inconsistent.

## Entry And Exit

- Entry point: any current HTML route.
- Exit or transition behavior: destination navigation changes the content route while preserving the shared shell and correct active location.

## State Expectations

- Default: all destinations and global search are available.
- Loading: the shell stays stable while destination content loads.
- Empty: not applicable to the shell; page-owned empty states remain in content.
- Error: route errors must not be presented as a valid active destination.
- Success: the destination loads with one correct active item and retained navigation access.

## Dependencies

- `feat-0002` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/base.html`
- shared shell, navigation, header, and search selectors in `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js` only if continuity or focus ownership requires shell coordination

## Pass Or Fail Checks

- Pass if all eight destinations remain reachable and identify the correct active route.
- Pass if the shell matches `220px`, `188px`, `920px`, `700px`, and `320px` contracts.
- Pass if narrow navigation scrolls without hiding the active destination or essential search access.
- Pass if focus is visible and follows the visual reading order.
- Fail if a route change flashes a blank shell or destroys navigation context.
- Fail if a destination, search, or current-location cue becomes unavailable at a supported width.

## Regression Surfaces

- all current HTML routes
- global search submission and query retention
- active navigation mapping for Dashboard, Sessions Dashboard, Workstreams, Sessions, Atlassian, Local Contexts, Projects, Sources, and Search

## Harness Trace

- Active spec doc: [spec-0003-shared-shell-navigation](../spec/spec-0003-shared-shell-navigation.md)
- Active run: [run-20260716-03-shared-shell-navigation](../run/run-20260716-03-shared-shell-navigation.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0003-ux-shared-shell](../evaluation/eval-0003-ux-shared-shell.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft isolated shared shell renewal from screen-family content changes.
- `2026-07-16`: executed and passed after the token foundation.
