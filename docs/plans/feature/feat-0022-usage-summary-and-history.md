# FEAT-0022: Usage Summary And History

## Metadata

- ID: `feat-0022`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Let the user open Sessions Dashboard and immediately understand selected-period token usage, canonical estimated cost, Session volume, activity context, and trend through one calm summary and one history family.

## Acceptance Contract

- `/sessions-dashboard` remains the destination inside the existing persistent LocalBrain shell.
- The default Daily view covers the most recent 30 inclusive local-calendar days, Weekly covers the most recent 12 local-calendar weeks, and Cumulative covers all eligible usage history.
- Current-month usage and cost remain available as explicitly labeled MTD context without replacing the stable Daily default window.
- Dashboard periods, totals, coverage, history, and usage-linked Session counts exclude Claude raw model `<synthetic>` records while retaining real-model maintenance and subsession usage.
- Scope is reproducible through GET query state: `view=daily|weekly|cumulative`, `source=all|claude|codex`, `metric=tokens|cost`, and paired inclusive `from=YYYY-MM-DD` and `to=YYYY-MM-DD` custom dates.
- A valid custom date pair overrides the selected view's default window while the selected view continues to own aggregation presentation.
- A malformed, partial, or reversed custom range falls back deterministically to the selected view's default window and shows a bounded validation message rather than a raw error or misleading empty result.
- The initial summary contains at most four primary metrics: canonical estimated cost, total tokens, explicitly scoped Session count, and active days with bounded streak, peak, or longest-active-segment context when supported.
- Cost is labeled estimated and carries concise price-snapshot context. Session count states its eligible Session scope and does not narrow usage or cost totals.
- One primary history family switches between Tokens and Cost and between Daily, Weekly, and Cumulative without a default dual axis.
- Scope changes replace the summary and history coherently, preserve the persistent shell, expose selected state visibly and programmatically, and keep URL, controls, and rendered data aligned.
- The screen exposes last-calculated or last-synchronized context without showing ordinary users internal storage paths.
- Loading, no activity, no matching activity, partial coverage, unpriced cost, stale data, and calculation failure remain bounded inside the owning summary or history region.
- The dashboard follows the existing design constitution at representative `1440`, `920`, `700`, and `320` widths and does not become a repeated KPI-card wall.

## Scope Boundary

- In:
  - `/sessions-dashboard` summary and primary history family
  - four-metric hierarchy
  - Daily, Weekly, and Cumulative modes
  - Tokens and Cost modes
  - all-source, Claude, and Codex scope
  - 30-day, 12-week, all-history, MTD, and custom-range behavior
  - reproducible GET query state and deterministic invalid-range fallback
  - data freshness context
  - responsive, accessible, empty, partial, stale, unpriced, loading, and failure states
  - synthetic route, query, UI-contract, and browser evidence
- Out:
  - Source, Model, and Project ranked breakdowns and detailed trust region owned by FEAT-0023
  - month-end projection owned by deferred FEAT-0024
  - budgets, caps, quota warnings, currency conversion, actual billing, and company governance
  - activity or attribution contract invention from FEAT-0021
  - tool-call, context-switch, repeated-workflow, and skill analysis from PRD-0005
  - shared-shell or navigation redesign

## Surface Lanes

- Read-model and route lane:
  - path roots: `src/localbrain/queries.py`, `src/localbrain/main.py`
  - dependencies: FEAT-0020 and FEAT-0021 passed
  - expected evidence: deterministic period buckets, scope totals, summary values, URL parsing, fallback behavior, freshness, and unavailable states
  - evaluator ownership: `contract`, `functional`
- Frontend and interaction lane:
  - path roots: `src/localbrain/templates/sessions_dashboard.html`, `src/localbrain/static/styles.css`, `src/localbrain/static/app.js`
  - dependencies: read-model and route lane
  - expected evidence: summary hierarchy, one history family, bound controls, accessible selected state, continuity, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Evidence lane:
  - path roots: `tests/`, synthetic browser artifacts allowed by repository privacy policy
  - dependencies: backend and frontend lanes
  - expected evidence: route, contract, state, interaction, and representative viewport validation without private runtime data
  - evaluator ownership: `contract`, `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- `/sessions-dashboard` GET query parameters and default behavior
- inclusive local-calendar date and week boundaries
- source, metric, view, and custom-range normalization
- summary and history read-model shapes
- Session-count eligibility label versus all-usage token and cost scope
- canonical estimated-cost and price-snapshot presentation
- activity metric labels from FEAT-0021
- freshness, partial, unpriced, stale, empty, and failure state values
- progressive-enhancement fallback and control-binding ownership

## Required Evaluators

- `contract`: query parameters, date boundaries, read-model shapes, metric scope, source coverage, pricing state, and producer/consumer parity.
- `design`: dashboard hierarchy, one-history-family containment, source provenance, state treatment, chart density, and `1440`, `920`, `700`, and `320` rendering.
- `functional`: default and custom periods, source and metric changes, URL restoration, malformed ranges, loading, empty, partial, stale, and failure behavior.
- `ux-heuristic`: scan efficiency, control clarity, metric comprehension, no-card-wall discipline, and query-state continuity.

## User-Visible Outcome

- The user can answer how many tokens were used, their canonical estimated cost, how usage changed, and the relevant Session and activity context without leaving Sessions Dashboard or interpreting raw source files.

## Entry And Exit

- Entry point: persistent `Sessions Dashboard` navigation or direct `/sessions-dashboard` URL with optional query state.
- Exit or transition behavior: scope controls update the same dashboard; existing resolvable Session and Project destinations remain available to later breakdown work without replacing this overview.

## State Expectations

- Default: Daily, all sources, Tokens, most recent 30 local-calendar days.
- Weekly: most recent 12 local-calendar weeks unless a valid custom range is supplied.
- Cumulative: all eligible usage history unless a valid custom range is supplied.
- Custom range: both inclusive dates are visible and reproducible in the URL.
- Invalid range: selected view default is used and a bounded validation message explains the fallback.
- Loading or working: the owning region remains stable and controls do not expose incomplete mixed-scope values.
- Empty source: explain that no eligible source usage exists.
- No match: preserve selected filters and distinguish them from an empty source.
- Partial or unpriced: token facts remain visible while cost limitation is explicit.
- Stale or failed refresh: previously valid data remains visible with an honest state label.
- Narrow viewport: scope, metrics, chart meaning, and trust context remain readable without horizontal page overflow.

## Dependencies

- PRD-0004 was `approved` during execution and is now `passed`.
- FEAT-0020 must be `passed` for usage and canonical estimated-cost semantics.
- FEAT-0021 must be `passed` for Project-independent activity metrics, date boundaries, and longest-active-segment wording.

## Likely Affected Surfaces

- `src/localbrain/queries.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/sessions_dashboard.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- usage summary, period bucket, query parameter, route, UI-contract, accessibility, and browser tests
- synthetic long-label, empty, partial, unpriced, stale, error, and responsive fixtures

## Pass Or Fail Checks

- Pass if direct `/sessions-dashboard` entry without query parameters renders Daily, all sources, Tokens, and the latest 30 inclusive local-calendar days.
- Pass if Weekly renders 12 local-calendar weeks and Cumulative renders all eligible usage history by default.
- Pass if paired valid `from` and `to` values reproduce the same custom result after refresh, back or forward navigation, and direct entry.
- Pass if malformed, partial, or reversed custom dates produce the documented default-window fallback and bounded message without a raw error.
- Pass if source, metric, view, and date controls stay aligned with the URL and rendered totals.
- Pass if the four primary metrics retain their documented scope and estimated cost never appears as actual billing.
- Pass if maintenance and subsession usage remains in token and cost totals while Session count states its separately approved denominator.
- Pass if Tokens and Cost share one history family and no default dual-axis comparison appears.
- Pass if no activity, no match, partial, unpriced, stale, and failure states are visibly distinct.
- Pass if keyboard, focus, programmatic selected state, progressive enhancement, and post-rerender control binding remain usable.
- Pass if representative `1440`, `920`, `700`, and `320` evidence shows one coherent reading order without clipping or hidden essential controls.
- Fail if the screen depends on `ccusage`, a network price lookup, or private tracked runtime evidence.

## Regression Surfaces

- persistent shell and Sessions Dashboard navigation
- current source synchronization and source-health presentation
- existing Session and Project routes and counts
- Sessions, Projects, Search, Workstream, and Local Context screens
- shared semantic tokens, forms, focus, and responsive breakpoints
- local-only operation and repository privacy rules

## Feature Review Questions

- None. Invalid custom ranges use the selected view's default window with bounded validation; exact response status and markup belong to the Spec.

## Harness Trace

- Active spec doc: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Active run: [run-20260718-29-filter-synthetic-non-usage](../run/run-20260718-29-filter-synthetic-non-usage.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract attempt 3](../evaluation/eval-0022-contract-filter-synthetic-non-usage-attempt-3.md), [functional attempt 3](../evaluation/eval-0022-functional-filter-synthetic-non-usage-attempt-3.md)
- Latest fix note: [fix-0027-filter-synthetic-non-usage](../fix/fix-0027-filter-synthetic-non-usage.md)

## Continuity Notes

- `2026-07-18`: initial draft kept the overview to four metrics and one history family while assigning ranked composition and deeper trust states to FEAT-0023.
- `2026-07-18`: FEAT-0020 and FEAT-0021 passed; sequential execution moved this Feature into `in-loop` with screen-alignment `adapt` mode and a frozen shared shell.
- `2026-07-18`: Attempt 1 passed 66 tests, local HTTP default/custom/fallback checks, source-level screen alignment, documentation parity, and privacy verification. Direct viewport evidence remains a PRD-level human acceptance gap.
- `2026-07-18`: human runtime feedback reopened the frontend interaction lane. Attempt 2 now swaps only the server-rendered dashboard region for link-backed scope changes, preserves document scroll and history, and passed 77 tests plus temporary-server response verification; direct scripted scroll-coordinate evidence remains unavailable.
- `2026-07-18`: human review separated stored evidence from monetary usage. Attempt 3 excludes Claude `<synthetic>` records at the dashboard read boundary, retains real Haiku subsession usage, and passed 84 tests plus a private read-only runtime check.
- `2026-07-18`: post-run synthetic renders and browser interaction checks closed the Attempt 1 viewport and scroll-continuity gaps; PRD-0004 is `passed`.
