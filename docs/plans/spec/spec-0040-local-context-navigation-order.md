# SPEC-0040: Local Context Navigation Order

## Metadata

- ID: `spec-0040`
- Status: `passed`
- Run ID: `run-20260719-45`
- Attempt: `1`
- Parent Feature: [feat-0040-local-context-navigation-order](../feature/feat-0040-local-context-navigation-order.md)
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: `shared-shell-navigation`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Source Set

- Human request: move `06 Local Contexts` directly after Sessions.
- Parent Feature: exact `04 Sessions → 05 Local Contexts → 06 Atlassian → 07 Sources → 08 Schema` order with all routes and shell behavior preserved.
- Golden source: current shared shell implementation.
- Durable baseline: Design Constitution navigation, typography, focus, responsive, and shell-continuity rules.
- Evaluation baselines: Design Evaluation visible/programmatic selection parity and shell preservation; Interaction Evaluation navigation continuity.
- Alignment skill: `screen-alignment` in `extend` mode.

## Implementation Goal

- Reorder exactly two existing Workspace links and their numeric symbols in shared DOM order without changing their destinations, active mapping, group, component classes, focus semantics, CSS, JavaScript, or shell geometry.

## In-Scope Behavior

- In `base.html`, keep Sessions first at `04`.
- Move the existing `/context` link immediately after it and change only its symbol from `06` to `05`.
- Move the existing `/atlassian` link immediately after Local Contexts and change only its symbol from `05` to `06`.
- Keep Sources and Schema in System at `07` and `08`.
- Add a deterministic UI contract test for visible text order, matching DOM/tab order, unchanged hrefs, and unchanged `active_page` values.
- Verify the shared shell in a rendered browser at `1440`, `920`, `700`, and `320` widths, including `/context` active state and navigation reachability.

## Out-Of-Scope Behavior

- Any route, label, group, icon, class, CSS, JavaScript, search, shell geometry, transition, Local Context content, or responsive-system change.
- Reordering Overview or System groups.
- Adding dropdowns, overflow controls, shortcuts, or persisted navigation state.

## Affected Surfaces

- `src/localbrain/templates/base.html`
- `tests/test_ui_contract.py`
- workflow Spec, Run, and evaluator artifacts

## Surface Lane

- Shared shell navigation:
  - path roots: `base.html` and UI contract tests
  - responsibility: exact DOM and symbol order while retaining existing link semantics
  - evaluator ownership: Design, Functional, UX Heuristic
  - rendered evidence: `/context` at four constitution widths plus keyboard-order inspection

## State And Interaction Contract

- DOM order, visible order, and sequential keyboard order are identical.
- `/context` retains `active_page == 'context'` and exposes exactly one `aria-current=page` when active.
- `/atlassian` retains `active_page == 'atlassian'` and its unchanged href.
- Narrow navigation uses the existing shell behavior and remains reachable; this Feature introduces no new state or handler.
- Shared shell regions do not move, resize, disappear, or restyle because only existing link order changes.

## Screen-Alignment Consistency List

- Retained components: `.lnb`, `.lnb-nav`, `.nav-group`, `.lnb-item`, `.nav-symbol`, active class, `aria-current`, brand, footer, workspace header, search, and main canvas.
- Retained visual roles: typography, spacing, target height, focus-visible outline, active fill, borders, overflow, breakpoints, and shell geometry.
- Deliberate change: only the relative DOM order and numeric symbols of Local Contexts and Atlassian.
- Intentional deviations: none.
- New pattern introduced: none.

## Contract Surfaces

- Destination hrefs: `/sessions`, `/context`, `/atlassian`, `/sources`, `/schema` unchanged.
- Active mappings: `sessions`, `context`, `atlassian`, `sources`, `schema` unchanged.
- Shared Jinja inheritance: every extending page receives one updated shell order.
- No data, API, route, generated artifact, CSS token, or JS binding change.

## Required Evaluators

- Design: exact order and numbering, retained active treatment, unchanged shell geometry, four rendered widths.
- Functional: unchanged href and active mapping, one current item, DOM/tab order, every destination reachable.
- UX Heuristic: Sessions and Local Contexts are adjacent and scanning/orientation remain clear without added friction.

## Acceptance Mapping

- Exact visible order maps to one template substring-order assertion and rendered shell inspection.
- Keyboard order maps to unchanged anchor DOM sequence and browser Tab traversal.
- Active state maps to `/context` rendered `aria-current=page` and unchanged condition.
- Responsive reachability maps to four viewport checks without overflow-induced disappearance or clipping.
- Shell preservation maps to a zero-CSS, zero-JavaScript diff and rendered containment.

## Evaluation Focus

- Confirm Local Contexts is not merely renumbered while remaining below Atlassian.
- Confirm Jinja active conditions stay attached to the correct href and label.
- Confirm compact shell behavior exposes the same five destinations at all required widths.
- Confirm no unrelated shell or page styling entered the diff.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: Attempt 1 locked a two-link DOM reorder with no new visual or interaction pattern.
- `2026-07-19`: Attempt 1 passed all required evaluators; the implementation remained a two-link reorder with no CSS, JavaScript, route, or geometry change.
