# FEAT-0016: Sessions And Projects Navigation

## Metadata

- ID: `feat-0016`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Goal

- Give Sessions and their Project-derived grouping one persistent navigation destination with Sessions as the default and an accessible `Sessions | Projects` local view switch.

## Acceptance Contract

- Persistent Workspace navigation contains one Sessions destination instead of separate Sessions and Projects items.
- Entering the combined destination without an explicit Projects destination selects Sessions.
- `Sessions | Projects` exposes mutually exclusive visible and programmatic selection, with a selected indicator that moves under normal motion settings and becomes static without losing meaning under reduced motion.
- Existing `/sessions`, `/projects`, Session detail, and workspace-filtered Session links remain valid and preserve shell orientation.
- Projects remains a Session-derived inventory and does not become a Workstream, Source, or new persisted entity.
- The Product Model and Design Constitution navigation contracts are updated from eight stable destinations to the approved combined navigation model.

## Scope Boundary

- In:
  - persistent left navigation consolidation
  - Sessions-default combined destination behavior
  - shared `Sessions | Projects` view switch on both inventory modes
  - active navigation and selected-view semantics
  - normal-motion indicator movement and reduced-motion fallback
  - route-entry, back, forward, and direct-link continuity
  - durable navigation contract alignment
- Out:
  - Session query pagination or row metadata changes
  - subsession dropdowns, identity, ingestion, or detail behavior
  - Project persistence or aggregation changes
  - Atlassian data or behavior changes
  - global shell redesign beyond the changed destination count and active mapping

## Contract Surfaces

- `/sessions` and `/projects` GET route identity
- existing `/sessions?workspace=<id>` Project-to-Session transition
- active-page and selected-view template context
- persistent navigation destination count and labels
- selected-state accessibility semantics
- Product Model and Design Constitution navigation wording

## Required Evaluators

- `contract`: direct-link, route, active-page, durable navigation, and reduced-motion contract alignment.
- `design`: segmented-control hierarchy, sliding indicator, shell continuity, responsive containment, and provenance of the existing screen family.
- `functional`: default entry, mode switching, direct URLs, back and forward navigation, and existing links.
- `ux-heuristic`: view-switch clarity, orientation, motion restraint, and navigation density.

## User-Visible Outcome

- The user enters Sessions from one Workspace navigation item and can switch between individual Sessions and Project groupings without treating Projects as a separate top-level destination.

## Entry And Exit

- Entry point: Sessions item in persistent navigation, direct `/sessions`, direct `/projects`, or an existing Project link.
- Exit or transition behavior: switching views changes only the intended inventory mode, preserves the shared shell, and leaves direct destinations usable.

## State Expectations

- Default: Sessions is selected.
- Projects direct entry: Projects is selected while the persistent Sessions destination remains active.
- Transition: the selected indicator moves without exposing a blank or placeholder-only state.
- Reduced motion: selection changes instantly with the same readable and programmatic state.
- Narrow viewport: both choices remain reachable and the active choice remains visible.
- Invalid or unsupported mode: the user returns to the Sessions default without a dead end.

## Dependencies

- Parent PRD `prd-0002` must remain `approved`.
- This Feature is independent of `feat-0015` because it changes navigation and mode ownership rather than Session identity.

## Likely Affected Surfaces

- `src/localbrain/templates/base.html`
- `src/localbrain/templates/sessions.html`
- `src/localbrain/templates/projects.html`
- `src/localbrain/main.py`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js` only if progressive enhancement owns indicator continuity
- `tests/test_ui_contract.py`
- route and browser navigation tests
- `docs/policies/project/product.md`
- `docs/policies/design/design-constitution.md`

## Pass Or Fail Checks

- Pass if persistent navigation exposes one Sessions destination and no separate Projects destination.
- Pass if Sessions is the default and direct Projects entry selects Projects without losing the active Sessions navigation context.
- Pass if the visible selected state matches `aria-current`, tab, or equivalent programmatic semantics.
- Pass if the indicator moves under normal motion, resolves instantly under reduced motion, and never carries meaning through animation alone.
- Pass if `/sessions`, `/projects`, Session details, workspace-filtered Sessions, back, and forward navigation retain valid destinations.
- Pass if `1440`, `920`, `700`, and `320` viewport evidence preserves both choices and the stable shell.
- Fail if this Feature changes Project data, Session pagination, subsession behavior, or Atlassian scope.
- Fail if the durable navigation docs still claim separate stable Sessions and Projects destinations after implementation.

## Regression Surfaces

- Dashboard and Sessions Dashboard navigation
- Workstreams, Atlassian, Local Contexts, and Sources destinations
- global search and shared header
- Project rows linking to workspace-filtered Sessions
- Session detail back links and active navigation
- current responsive shell and reduced-motion contract

## Harness Trace

- Active spec doc: [spec-0016-sessions-projects-navigation](../spec/spec-0016-sessions-projects-navigation.md)
- Active run: [run-20260717-16-sessions-projects-navigation](../run/run-20260717-16-sessions-projects-navigation.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0016-ux-sessions-projects-navigation](../evaluation/eval-0016-ux-sessions-projects-navigation.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-17`: initial draft isolated persistent navigation and view ownership from pagination, subsession data, and detail presentation.
- `2026-07-17`: entered sequential execution after FEAT-0015 passed; `adapt` mode preserves the LocalBrain shell and borrows only the two-state sliding selector behavior.
- `2026-07-17`: all required evaluators passed; the combined destination and canonical route fallback are ready for the paginated Session inventory Feature.
