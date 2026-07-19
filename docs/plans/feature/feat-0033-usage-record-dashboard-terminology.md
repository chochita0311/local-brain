# FEAT-0033: Usage Record Dashboard Terminology

## Metadata

- ID: `feat-0033`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Replace data-model terminology such as “normalized usage facts” with plain “usage records” throughout the Sessions Dashboard so count and coverage labels are immediately understandable.

## Acceptance Contract

- The Total tokens summary describes the count as `usage records`, without the implementation-facing `normalized` or `facts` wording.
- Summary, Source rows, Trust details, price coverage, and limitation messages use one consistent `usage record(s)` vocabulary.
- Internal table names, parser types, read-model keys, aggregation rules, values, eligibility, price semantics, and immutable attribution remain unchanged.
- Existing Dashboard hierarchy, scope controls, history, breakdowns, trust hierarchy, and interactions remain unchanged.
- At the 320px acceptance width, the Usage summary uses one column so long unavailable values and the clearer record labels remain readable without page-level horizontal overflow.

## Scope Boundary

- In:
  - visible Sessions Dashboard strings currently using `fact` or `usage fact`
  - the minimum narrow-width Usage summary containment correction required to keep those labels readable
  - source/read-model string tests and template UI-contract coverage
  - rendered desktop and narrow browser verification
- Out:
  - renaming `usage_facts`, `ParsedUsageFact`, `fact_count`, or internal code concepts
  - changing numbers, denominators, pricing, token normalization, filters, URLs, JavaScript, or layout outside the narrow Usage summary
  - translating the whole screen or changing durable Data Model terminology

## Surface Lanes

- Read-model copy lane:
  - path roots: `src/localbrain/usage_queries.py`, usage read-model tests
  - dependencies: passed PRD-0004 usage contracts
  - expected evidence: identical values and states with user-facing `usage records` copy
  - evaluator ownership: `contract`, `functional`
- Frontend copy lane:
  - path roots: `src/localbrain/templates/sessions_dashboard.html`, `src/localbrain/static/styles.css`, UI contract tests
  - dependencies: read-model copy lane
  - expected evidence: no visible `usage facts`/`facts priced`, unchanged structure and controls, desktop containment and one-column narrow Usage summary
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- Sessions Dashboard summary detail strings
- Source and Trust region labels
- pricing/coverage/limitation explanation strings
- internal-versus-visible terminology boundary

## Required Evaluators

- `contract`: unchanged read-model values/keys and internal Usage Fact contract; complete visible terminology replacement.
- `design`: unchanged hierarchy and containment at representative desktop and narrow widths.
- `functional`: positive populated Dashboard render, existing controls and scopes, no stale visible `fact` copy.
- `ux-heuristic`: count and coverage comprehension with `usage records` and no new ambiguity with Activity Events.

## User-Visible Outcome

- A count such as `10,720 usage records` reads as a number of stored usage entries rather than an unexplained analytical “Fact” concept.

## Entry And Exit

- Entry point: `/sessions-dashboard`.
- Exit or transition behavior: unchanged; all scope, metric, period, breakdown, navigation, and history behavior remains intact.

## State Expectations

- Populated: summary and trust regions consistently say `usage records`.
- Partial/unpriced/untimed: limitation messages use the same vocabulary while preserving exact coverage numbers.
- Empty: existing empty state is unchanged.
- Narrow viewport: replacement strings remain contained; at 320px only the Usage summary changes from two columns to one, while controls and reading order stay unchanged.

## Dependencies

- PRD-0004 and FEAT-0020 through FEAT-0024 are `passed`.
- The human owner requested a more understandable alternative to `facts` on `2026-07-19`; `usage records` is the selected visible term.

## Likely Affected Surfaces

- `src/localbrain/usage_queries.py`
- `src/localbrain/templates/sessions_dashboard.html`
- `src/localbrain/static/styles.css`
- `tests/test_usage_dashboard.py`
- `tests/test_ui_contract.py`
- user-facing README and Product terminology boundary
- PRD-0004 continuity artifacts

## Pass Or Fail Checks

- Pass if a populated Dashboard visibly contains `usage records` and no user-facing `usage facts`, `facts priced`, or `normalized usage facts` remains.
- Pass if internal schema/type/key names remain unchanged and all usage totals and coverage tests remain identical.
- Pass if desktop and 320px rendered states preserve containment and all existing controls remain reachable.
- Fail if the table is renamed, values change, Activity Event terminology is reused, or layout outside the narrow Usage summary is rewritten.

## Regression Surfaces

- Sessions Dashboard summary, Source composition, Trust details, partial/unpriced limitations, scope switches, responsive layout, empty state, Usage ingestion and query contracts.

## Harness Trace

- Active spec doc: [spec-0033-usage-record-dashboard-terminology](../spec/spec-0033-usage-record-dashboard-terminology.md)
- Active run: [run-20260719-38-usage-record-dashboard-terminology](../run/run-20260719-38-usage-record-dashboard-terminology.md)
- Execution profile: `fullstack-product`
- Latest contract evaluator report: [eval-0033-contract-usage-record-dashboard-terminology](../evaluation/eval-0033-contract-usage-record-dashboard-terminology.md) (`PASS`)
- Latest design evaluator report: [eval-0033-design-usage-record-dashboard-terminology](../evaluation/eval-0033-design-usage-record-dashboard-terminology.md) (`PASS`)
- Latest functional evaluator report: [eval-0033-functional-usage-record-dashboard-terminology](../evaluation/eval-0033-functional-usage-record-dashboard-terminology.md) (`PASS`)
- Latest UX heuristic evaluator report: [eval-0033-ux-usage-record-dashboard-terminology](../evaluation/eval-0033-ux-usage-record-dashboard-terminology.md) (`PASS`)
- Latest fix note: not created

## Continuity Notes

- `2026-07-19`: approved as a visible-copy-only follow-up; `usage records` replaces implementation-facing Fact language without renaming persistence or read-model contracts.
- `2026-07-19`: exact 320px rendered inspection exposed an existing two-column collision between the summary's long unavailable values. The frontend lane adds a Usage-summary-only one-column narrow rule so the approved terminology remains readable; no control, metric, or wider layout changes.
- `2026-07-19`: passed with consistent singular/plural `usage record(s)` copy, thousands-separated large counts, populated and empty browser evidence, exact 1440/320 containment, 121 repository tests, and privacy verification.
