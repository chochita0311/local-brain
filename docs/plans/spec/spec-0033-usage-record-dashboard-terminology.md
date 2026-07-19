# SPEC-0033: Usage Record Dashboard Terminology

## Metadata

- ID: `spec-0033`
- Status: `approved`
- Run ID: `run-20260719-38`
- Attempt: `1`
- Parent Feature: [feat-0033-usage-record-dashboard-terminology](../feature/feat-0033-usage-record-dashboard-terminology.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: read-model copy → frontend copy → rendered verification
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Source Set

- Human feedback that `normalized usage facts` and `usage facts` are not self-explanatory on the Dashboard.
- FEAT-0033, passed PRD-0004 and its Usage summary/breakdown/trust contracts.
- Current read-model strings, Sessions Dashboard template, Design Constitution, Design Evaluation, and Interaction Evaluation.

## Implementation Goal

- Establish `usage record(s)` as the complete user-facing count vocabulary while keeping Fact as an internal analytical and persistence term.

## In-Scope Behavior

- Replace visible read-model and template phrases:
  - `normalized usage facts` → `usage records`
  - `selected usage facts` → `selected usage records`
  - `facts priced` / `facts have...` → equivalent `usage records` wording
  - Fact-first pricing explanation → record-first explanation
- Add tests proving positive populated copy and absence of stale visible terminology.
- Verify the route at desktop and exact 320px; keep desktop and interaction layout unchanged, and use one narrow Usage summary column where the existing two-column cards collide.

## Out-Of-Scope Behavior

- No schema, dataclass, read-model key, metric, denominator, query, state, route, JavaScript, or navigation change.
- No CSS or layout change outside a `max-width: 700px` Usage-summary-only one-column containment rule.
- No broad English/Korean localization or other terminology cleanup.

## Affected Surfaces

- `usage_queries.py` user-facing strings
- `sessions_dashboard.html` visible labels and explanation
- `styles.css` narrow Usage summary containment
- Usage Dashboard and UI contract tests
- user-facing README and Product terminology boundary
- PRD-0004 continuity notes

## Lane Order And Handoff

1. Read-model copy lane keeps the same dictionary shape and values while replacing only visible strings.
2. Frontend copy lane replaces template literals without structural markup changes and constrains only the narrow Usage summary to one column.
3. Contract check proves internal names unchanged; rendered evaluation checks the positive terminology and exact 320px containment.

## State And Interaction Contract

- Existing route state and controls are untouched.
- No nodes, controls, or regions are added or removed; only the narrow Usage summary's existing cards stack in the same reading order.
- Direct load and scope controls continue to use the same URLs and selected state.

## Data And Contract Assumptions

- `usage record` means one selected normalized source usage entry; it does not imply one Session, request, invoice line, or Activity Event.
- Price/token coverage continues to report compatible subsets of the same selected record count.
- Internal Fact vocabulary remains correct for engineering documentation and code.

## Contract Surfaces

- Producer: Usage Dashboard read model and template literals.
- Consumer: visible `/sessions-dashboard` summary, composition, trust, and limitation copy.
- Stable internals: `usage_facts`, `ParsedUsageFact`, `fact_count`, `token_fact_count`, `priced_fact_count`.

## Acceptance Mapping

- Plain count label: populated Total tokens summary contains `<count> usage records`.
- Consistency: source, trust, price, and limitation strings contain no visible Fact terminology.
- No behavior drift: Usage query values and existing UI structure/control tests pass.
- Rendered quality: desktop remains unchanged and exact 320px has no page-level horizontal overflow from the Usage summary.

## Evaluation Focus

- Check the rendered page, not only source replacements.
- Ensure `usage records` cannot be mistaken for Activity Events by leaving the surrounding token/cost context intact.
- Ensure the shorter copy does not introduce an unexplained bare `records` label.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: approved attempt 1; copy-only lane order preserves internal Fact contracts and existing Dashboard behavior.
- `2026-07-19`: the rendered 320px check found an existing collision in the two-column Usage summary. Attempt 1 includes the smallest surface-specific responsive correction: the same four cards stack in one column below 700px.
