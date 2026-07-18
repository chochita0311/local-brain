# SPEC-0016: Sessions And Projects Navigation

## Metadata

- ID: `spec-0016`
- Status: `approved`
- Run ID: `run-20260717-16`
- Attempt: `1`
- Parent Feature: [feat-0016-sessions-projects-navigation](../feature/feat-0016-sessions-projects-navigation.md)
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Surface Lane: persistent navigation → local inventory switch → route continuity
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Source Set

- Human request: place Sessions and Projects in one menu, use an Atlassian-like two-state sliding control, and default to Sessions.
- Parent Feature and approved PRD.
- Current rendered `/sessions`, `/projects`, and `/atlassian` surfaces at 1440px using synthetic local data.
- Design Constitution, Design Evaluation, Interaction Evaluation, and screen-alignment `adapt` method.

## Implementation Goal

- Preserve the LocalBrain browse family while making Sessions the single persistent destination and switching between already-supported Session and Project inventories through one accessible moving selector.

## In-Scope Behavior

- Remove the independent Projects item from persistent navigation and renumber the remaining destinations.
- Serve Sessions and Projects as two prepared panels under a shared Sessions destination on both existing routes.
- Keep `/sessions` as the default selected state and `/projects` as a direct Projects state.
- Progressively enhance the route links so selection, content visibility, URL, title, and browser history update atomically without replacing the shell.
- Retain normal links as a no-script and failed-enhancement fallback.
- Use a two-position indicator with semantic motion tokens and an instant reduced-motion fallback.
- Keep the local source filter, Project-to-workspace link, and direct detail routes valid.

## Out-Of-Scope Behavior

- Session pagination, row metadata redesign, subsession controls, detail timeline filtering, Project aggregation changes, or Atlassian surface changes.
- New data fields, sort controls, saved view state, or cross-session persistence.

## Affected Surfaces

- `/sessions`, `/projects`, and `/sessions?workspace=<id>`
- `src/localbrain/main.py`
- `src/localbrain/templates/base.html`, Sessions and Projects inventory templates, and one shared inventory template
- `src/localbrain/static/styles.css`, `app.js`
- UI contract and route/browser tests
- Product Model and Design Constitution navigation contracts

## Surface Lanes

- Persistent navigation lane:
  - dependency order: first
  - implementation responsibility: one active Sessions destination for both routes
  - validation evidence: LNB label/count and `aria-current` on direct entry
- Local inventory switch lane:
  - dependency order: after both route contexts expose both inventories
  - implementation responsibility: selected semantics, moving indicator, panel visibility, and fallback links
  - validation evidence: visible/programmatic parity, no blank state, responsive containment, reduced motion
- Route continuity lane:
  - dependency order: after switch behavior
  - implementation responsibility: direct entry, click, back, forward, workspace link, and no-script fallback
  - validation evidence: URL/title/panel/current-link parity in browser

## State And Interaction Contract

- `/sessions` and unsupported combined-entry state select Sessions.
- `/projects` selects Projects while the persistent Sessions LNB item remains current.
- Both panels are server-rendered before enhancement; exactly one panel is visible and its corresponding link has `aria-current="page"`.
- Enhanced selection updates the indicator and panel in one synchronous state commit, pushes the canonical route, and preserves the switch's current viewport anchor without exposing a placeholder or scroll jump.
- `popstate` restores the same state from the current canonical path without adding history.
- Reduced motion makes the indicator state change instant; selected text and programmatic state remain sufficient without motion.
- At 700px and below the two choices stretch within the content width and retain touch control height.

## Data And Contract Assumptions

- Projects remains the existing derived `project_activity` result; no schema or identity changes.
- Both route handlers may read both existing inventory queries so the browser can switch without a second request.
- Session source/workspace filters belong only to the Sessions inventory and reset when leaving it through the canonical Projects link.

## Contract Surfaces

- Producer expectations: both route handlers provide `selected_inventory`, Session context, and Project context to one shared presentation.
- Consumer expectations: links and browser state use only canonical `/sessions` and `/projects` paths.
- Source-of-truth owner: FastAPI route identity plus Design Constitution navigation and selection law.
- Stale-assumption check: all `active_page == 'projects'`, Projects LNB labels, and eight-destination policy claims are removed or updated.

## Required Evaluators

- Contract: route identity, one active destination, direct-link fallback, and durable docs.
- Design: `adapt` integrity, indicator geometry, hierarchy, shell preservation, and 1440/920/700/320 containment.
- Functional: default, click, direct URLs, back, forward, filters, Project-to-Session link, and no-script source shape.
- UX heuristic: switch clarity, selected-state parity, orientation, motion restraint, and absence of dead ends.

## Acceptance Mapping

- One persistent destination maps to `base.html` and both route contexts using `active_page = 'sessions'`.
- Default Sessions maps to `/sessions` and the shared template's initial state.
- Sliding selection maps to a semantic-token CSS indicator and the inventory state controller.
- Direct-link continuity maps to canonical anchor destinations and server-selected fallback panels.
- Durable alignment maps to Product Model and Design Constitution updates.

## Evaluation Focus

- Preserve the current shell literally outside the removed LNB row and renumbered source symbol.
- Do not copy target-only Atlassian content, controls, labels, or visual language.
- Confirm current and hidden panels never become simultaneously focusable.
- Check indicator placement after direct entry, click, back, forward, resizing, and reduced motion.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-17`: approved for sequential execution after FEAT-0015 passed; screen-alignment mode is `adapt`.
