# SPEC-0022: Usage Summary And History

## Metadata

- ID: `spec-0022`
- Status: `approved`
- Run ID: `run-20260718-29`
- Attempt: `3`
- Parent Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: usage read model → GET route state → Sessions Dashboard overview
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human-approved PRD-0004 and FEAT-0022.
- Passed usage, cost, attribution, activity, and timezone contracts from FEAT-0020 and FEAT-0021.
- Current Sessions Dashboard and LocalBrain Design Constitution.
- Owner-supplied Codex `/usage` and company dashboard as directional information-hierarchy references only.
- Screen Alignment skill in `adapt` mode.

## Implementation Goal

- Replace the event/tool-oriented Sessions Dashboard overview with one reproducible usage summary and one token-or-cost history family while keeping the existing shell, native controls, and calm dashboard density.

## In-Scope Behavior

- Normalize `view`, `source`, `metric`, `from`, and `to` GET parameters.
- Daily defaults to 30 inclusive local days; Weekly to the current plus previous 11 Monday-based weeks; Cumulative to the first observed usage date through today.
- A valid paired custom range overrides only date bounds. Partial, malformed, or reversed pairs fall back to the selected view default and produce one bounded message with HTTP 200.
- Query all direct usage facts in `[local start, local day after end)` with source filtering.
- At the dashboard query boundary, exclude Claude facts whose raw model is exactly `<synthetic>` from the earliest Cumulative date, selected and MTD aggregates, history, coverage, Source/Model/Project breakdowns, and usage-linked Session counts. Do not delete or rewrite the stored Fact or Session activity evidence.
- Return priced estimated cost, total normalized tokens, usage-linked primary-work Session count, active days, and FEAT-0021 activity context.
- Keep real-model maintenance and subsession facts in token and cost totals while Session count admits only `session_class=work` and `session_role=primary` facts.
- Provide MTD tokens and priced estimated cost as secondary context.
- Build Daily bars per date, Weekly bars per local Monday, and Cumulative monthly running totals across the selected window.
- Tokens and Cost reuse the same chart. Cost bars use priced facts only and expose coverage limitations when any selected fact is unpriced, partial, failed, or lacks a usable time.
- Show source freshness, last calculation, price snapshot labels, and bounded validation, empty, no-match, partial, unpriced, stale, and failure messages.
- Implement controls as ordinary GET links and one GET date form so direct entry, refresh, and no-script operation share one contract.

## Out-Of-Scope Behavior

- Source, Model, and Project ranked breakdowns; detailed trust drill-down; month-end projection; budgets; caps; quotas; tool calls; context switches; Workflow Intelligence; or shell redesign.

## Affected Surfaces

- `src/localbrain/usage_queries.py`
- `src/localbrain/activity.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/sessions_dashboard.html`
- `src/localbrain/static/styles.css`
- query, route, template, UI-contract, and HTTP tests
- `README.md` and Project Product/Architecture owner docs where user-visible dashboard behavior changes

## Surface Lanes

- Read model:
  - path roots: usage queries and activity source filter
  - dependency order: first
  - implementation responsibility: scope normalization, calendar windows, totals, buckets, MTD, freshness, and limitation states
  - validation evidence: deterministic SQLite fixtures and timezone boundaries
- Route contract:
  - path roots: `main.py`
  - dependency order: after read model
  - implementation responsibility: raw query capture, normalized context, and stable HTTP 200 fallback
  - validation evidence: direct function and temporary HTTP requests
- Frontend content lane:
  - path roots: Sessions Dashboard template and shared stylesheet
  - dependency order: after route shape
  - implementation responsibility: four-metric band, one history surface, native GET controls, trust context, and responsive containment
  - validation evidence: synthetic template rendering, UI contract, local HTTP, and viewport rendering when browser runtime is available

## State And Interaction Contract

- Defaults are `daily`, `all`, `tokens`, and no custom dates.
- Selected links carry `aria-current="page"`; the metric fieldset uses ordinary navigation links with visible selected state.
- Source and view changes preserve metric and a valid custom pair. Clearing dates returns to the selected view default.
- Custom form contains hidden normalized view, source, and metric inputs.
- Empty all-source state says no usage has been indexed; filtered no-match state retains the selected source and says no matching usage exists.
- Cost with no priced facts renders unavailable, not `$0`; mixed coverage renders the priced estimate plus an explicit limitation.
- The shared shell, global search, sidebar, and Sessions/Projects routes do not change.

## Data And Contract Assumptions

- Historical Project snapshots are not needed in this Feature's overview read model.
- Effective usage time prefers `usage_facts.occurred_at`; facts without it are excluded from period buckets and counted in coverage limitations.
- `total_tokens` is the normalized non-double-counting total from FEAT-0020.
- Currency totals sum stored decimal strings as `Decimal` in Python.
- Active days use usable usage-fact dates. Activity duration uses source-filtered Activity Events and may therefore have different capability coverage.
- Cumulative monthly buckets are the bounded all-history presentation; each value is a running total from the selected range start.

## Contract Surfaces

- Producer expectations: `usage_dashboard_data` returns normalized scope, summary, MTD, history, freshness, pricing labels, and limitation states.
- Consumer expectations: template reads only that model and keeps all scope state in GET URLs or fields.
- Generated artifacts: none outside the rendered response.
- Source-of-truth owner: usage facts and stored price snapshots for tokens/cost, Activity Events for estimated time, sources/source_files for freshness.
- Stale-assumption check: existing event, tool, Project, and context-switch queries remain available elsewhere but no longer define Sessions Dashboard usage.

## Required Evaluators

- Contract: URL normalization, inclusive local dates, scope, priced/unavailable behavior, and producer/template parity.
- Design: screen-alignment `adapt`; preserve shell, metric-band family, one calm history surface, semantic tokens, and 1440/920/700/320 containment.
- Functional: direct/default/custom/invalid queries, source and metric switches, empty/filtered/partial/unpriced/stale/failure data, and no-script GET behavior.
- UX heuristic: scan order, label honesty, selected-state clarity, no-card-wall discipline, and scope continuity.

## Acceptance Mapping

- Default and custom windows map to scope normalization and local UTC bounds.
- Four metrics map to one existing-family `overview-metrics` band.
- Token/cost and daily/weekly/cumulative modes map to one `usage-history-panel`.
- MTD and freshness map to one subordinate context strip.
- Limitation states map to bounded messages inside summary or history, never global alerts.

## Evaluation Focus

- Verify all-direct usage totals versus primary-work Session count.
- Verify Cumulative means running total and Cost never becomes actual billed spend.
- Verify invalid custom dates do not alter selected view/source/metric.
- Verify 30 Daily bars remain readable without shrinking below approved text roles and narrow layouts contain horizontal density locally.
- Verify no company quota, entitlement, allocation, or donut language transfers.

## Open Blockers

- None. The in-app browser runtime is not currently exposed; if still unavailable after implementation, Design and interaction reports must record the rendered-evidence gap rather than claim unobserved geometry.

## Continuity Notes

- `2026-07-18`: approved in screen-alignment `adapt` mode with a frozen shell and current LocalBrain content truth ahead of external references.
- `2026-07-18`: Attempt 3 adds one consumer-only eligibility boundary: retain Claude `<synthetic>` records in storage and Session evidence, exclude them from every dashboard usage consumer, and preserve all real-model subsession usage.
