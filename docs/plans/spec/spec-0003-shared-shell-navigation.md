# SPEC-0003: Shared Shell And Global Navigation

## Metadata

- ID: `spec-0003`
- Status: `approved`
- Run ID: `run-20260716-03`
- Attempt: `1`
- Parent Feature: [feat-0003-shared-shell-navigation](../feature/feat-0003-shared-shell-navigation.md)
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: shared shell
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Source Set

- Feature, PRD, Design Constitution, Interaction Evaluation, current route map, and `active_page` contexts.

## Implementation Goal

- Align the persistent shell to semantic geometry and make location, global search, keyboard entry, and narrow navigation explicit without changing destinations.

## In-Scope Behavior

- Preserve the three navigation groups and eight destinations.
- Add `aria-current`, a skip link, a focusable main region, semantic focus, and a stable Search handoff.
- Transform the `220px` sidebar to `188px` compact and horizontal narrow navigation at `700px`, with a `320px` floor.

## Out-Of-Scope Behavior

- Destination changes, a command palette, client-side routing, or page-family redesign.

## Affected Surfaces

- `src/localbrain/templates/base.html`
- shared shell selectors in `src/localbrain/static/styles.css`
- `tests/test_ui_contract.py`

## State And Interaction Contract

- Active location combines label, surface, and accent; hover never substitutes for current state.
- Keyboard order starts with skip navigation, then destination navigation, global search, and page content.

## Contract Surfaces

- Producer: route `active_page` context and `/search?q=`.
- Consumer: shared base template.
- Stale-assumption check: all existing GET routes remain linked and no client router is introduced.

## Acceptance Mapping

- Destination preservation maps to the eight base-template links.
- Orientation and non-color current state map to `aria-current` and active shell selectors.
- Reachability maps to focus-visible, skip-link, responsive CSS, and route smoke checks.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-16`: approved after `feat-0002` foundation completion.
