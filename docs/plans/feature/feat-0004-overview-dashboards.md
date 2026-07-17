# FEAT-0004: Overview Dashboards

## Metadata

- ID: `feat-0004`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0001-ui-design-system-realignment](../prd/prd-0001-ui-design-system-realignment.md)
- Created: `2026-07-16`
- Updated: `2026-07-16`

## Goal

- Make Dashboard and Sessions Dashboard coherent overview surfaces whose metrics and summaries lead back to current work, source activity, or inspectable evidence.

## Acceptance Contract

- Dashboard prioritizes Workstream continuity, current Threads, checkpoint attention, unlinked evidence, and maintenance entry without becoming a generic widget wall.
- Sessions Dashboard preserves activity, source, tool, project, health, and attention summaries with traceable destinations or labels.
- Metric, card, panel, chart, status, and empty-state treatments consume the shared semantic system.
- Realistic long names, zero counts, sparse activity, missing paths, and narrow layouts remain contained and understandable.

## Scope Boundary

- In:
  - Dashboard heading, actions, metrics, Workstream summaries, queues, and maintenance panel
  - Sessions Dashboard metrics, charts, ranked lists, health, and attention panels
  - responsive overview composition and overview-specific empty states
- Out:
  - changing metric definitions or query calculations
  - new dashboard widgets or insights
  - Workstream detail behavior
  - source ingestion or maintenance execution changes

## Contract Surfaces

- `/` and `/sessions-dashboard` route contexts
- current Dashboard and Sessions Dashboard query outputs
- links from summaries to existing Workstreams, Sessions, Sources, Projects, and maintenance actions

## Required Evaluators

- `design`: hierarchy, density, alignment, traceability, charts, cards, and responsive containment.
- `functional`: links, maintenance marker action, state labels, and existing route behavior.
- `ux-heuristic`: scan order, attention clarity, and distinction between actionable and informational summaries.

## User-Visible Outcome

- The user can understand current work and session activity at a glance and follow each important summary to the existing underlying work or evidence.

## Entry And Exit

- Entry point: `/` or `/sessions-dashboard` from shared navigation.
- Exit or transition behavior: summary links open the existing owning Workstream, Session, Source, Project, or action surface without losing shell orientation.

## State Expectations

- Default: populated summaries have stable metadata and clear action hierarchy.
- Loading: no new client-side loading contract is introduced.
- Empty: zero-work and zero-activity states explain what is absent and offer at most one relevant recovery action.
- Error: existing route failures remain explicit and are not converted into empty success states.
- Success: metrics and summaries remain traceable rather than decorative.

## Dependencies

- `feat-0002` and `feat-0003` must be `passed`.

## Likely Affected Surfaces

- `src/localbrain/templates/dashboard.html`
- `src/localbrain/templates/sessions_dashboard.html`
- overview, metric, chart, panel, Workstream-card, and responsive selectors in `src/localbrain/static/styles.css`
- maintenance marker interaction in `src/localbrain/static/app.js` as a regression surface

## Pass Or Fail Checks

- Pass if each nondecorative summary has an understandable owner or destination.
- Pass if Workstream-first hierarchy remains stronger than generic activity statistics on Dashboard.
- Pass if zero, sparse, long-content, and narrow states remain contained.
- Pass if maintenance marker generation and copy remain operable with bounded feedback.
- Fail if visual renewal changes metric meaning or invents unsupported insight behavior.
- Fail if cards, charts, or queues become unreadable at compact or narrow widths.

## Regression Surfaces

- Dashboard overview queries and links
- Sessions Dashboard chart values and source/tool/project labels
- maintenance marker generation and copy behavior
- shared shell and global search

## Harness Trace

- Active spec doc: [spec-0004-overview-dashboards](../spec/spec-0004-overview-dashboards.md)
- Active run: [run-20260716-04-overview-dashboards](../run/run-20260716-04-overview-dashboards.md)
- Execution profile: `frontend-product`
- Latest evaluator report: [eval-0004-ux-overview-dashboards](../evaluation/eval-0004-ux-overview-dashboards.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-16`: initial draft grouped the two overview routes because they share summary composition but retain distinct product purposes.
- `2026-07-16`: executed and passed in `run-20260716-04`.
