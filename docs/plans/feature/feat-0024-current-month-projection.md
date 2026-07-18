# FEAT-0024: Current-Month Projection

## Metadata

- ID: `feat-0024`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Current Product Decision

- Human review on `2026-07-18` withdrew the visible projection because it added unnecessary secondary information to Cost mode. RUN-20260718-28 removes the projection markup and dedicated styles for every scope while retaining the non-persisted calculation only as internal compatibility behavior. The sections below preserve the historical Attempt 1 acceptance contract and evidence.
- Current user-visible outcome: the dashboard shows observed selected-period and explicitly labeled MTD cost context only. Reintroducing a projection requires a new human product decision rather than reactivating the retained read-model field.

## Historical Goal — Attempt 1

- Add a bounded current-month trend projection that helps the user understand likely month-end estimated cost without introducing a budget, cap, quota, or billing claim.

## Historical Acceptance Contract — Attempt 1

- Projection is deferred until FEAT-0020 and FEAT-0022 are passed and their usage, price, range, source, and metric contracts are stable.
- Projection appears only as supporting context when the active range includes the current local calendar month in the approved MTD scope and Cost is the relevant metric.
- The projected month-end value uses only canonical snapshot-priced usage facts already accepted by FEAT-0020.
- The deterministic initial formula is current MTD estimated cost divided by elapsed local-calendar month fraction, multiplied by the full local-calendar month duration.
- Projection remains unavailable until at least three complete local-calendar days have elapsed in the month. The UI explains insufficient history instead of rendering a volatile zero or unsupported number.
- The projection stores or returns its calculation timestamp, input MTD total, elapsed fraction, source scope, formula version, and coverage state.
- Recalculation updates the projection as a current derived trend; it never rewrites historical usage facts or their original price snapshots.
- Partial source coverage or unpriced usage produces an explicitly partial projection or unavailable state according to the same compatible-denominator rules as the dashboard.
- Projection is labeled estimated and directional. It does not claim forecast accuracy, billed spend, personal payment, entitlement consumption, or a limit.
- The value appears as concise supporting context to the existing cost summary and does not add a duplicate primary chart, allocation control, donut, budget bar, cap warning, or request-more action.
- Non-current-month and custom historical ranges remain unchanged and do not show a misleading month-end projection.

## Historical Scope Boundary — Attempt 1

- In:
  - current-local-month eligibility
  - deterministic month-fraction projection formula and version
  - minimum-history threshold
  - source scope and compatible priced denominator
  - calculation time, input, coverage, partial, unavailable, and stale state
  - concise supporting presentation in the existing cost summary
  - synthetic formula, date-boundary, partial, unavailable, route, UI, and browser evidence
- Out:
  - personal budgets, caps, targets, warnings, quotas, allocation, approval, or request-more behavior
  - actual billing, invoice reconciliation, subscription fees, credits, currency conversion, or tax
  - predictive modeling, seasonality, weekday weighting, model-specific forecasts, or external AI
  - a second projection chart or new dashboard route
  - historical-month backcasts or automatic repricing

## Historical Surface Lanes — Attempt 1

- Projection contract and calculation lane:
  - path roots: usage calculation and query modules selected by the Spec, `src/localbrain/queries.py`
  - dependencies: FEAT-0020 passed
  - expected evidence: deterministic formula, version, current-month boundary, minimum-history, source scope, partial pricing, and recalculation fixtures
  - evaluator ownership: `contract`, `functional`
- Route and presentation lane:
  - path roots: `src/localbrain/main.py`, `src/localbrain/templates/sessions_dashboard.html`, `src/localbrain/static/styles.css`, `src/localbrain/static/app.js`
  - dependencies: calculation lane and FEAT-0022 passed
  - expected evidence: bounded supporting context, eligible visibility, unavailable explanation, no budget semantics, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Historical Contract Surfaces — Attempt 1

- current local-calendar month and elapsed-fraction definition
- minimum three-complete-day eligibility threshold
- projection input, output, formula version, calculation time, and source scope
- compatible priced denominator, partial coverage, unavailable, stale, and failure state
- FEAT-0022 cost-summary read-model extension
- query-state eligibility for current-month and custom ranges
- estimate and trend user-facing terminology

## Historical Required Evaluators — Attempt 1

- `contract`: formula inputs, local-time boundaries, versioning, source scope, compatible denominator, historical-fact immutability, and read-model shape.
- `design`: supporting hierarchy, estimate labeling, partial or unavailable state, and absence of duplicate governance or allocation patterns.
- `functional`: current and historical ranges, early-month threshold, source changes, partial pricing, stale calculation, and recalculation behavior.
- `ux-heuristic`: projection comprehension, false-precision risk, hierarchy, and avoidance of budget or billing implications.

## Historical User-Visible Outcome — Attempt 1

- During the current month, the user can see a modest, clearly estimated month-end cost direction beside the current cost without interpreting it as a spending limit or invoice.

## Historical Entry And Exit — Attempt 1

- Entry point: the cost summary on `/sessions-dashboard` while the active range is eligible for current-month projection.
- Exit or transition behavior: changing to an ineligible historical range, Tokens metric, or unsupported scope removes the projection context while preserving the rest of the dashboard state.

## Historical State Expectations — Attempt 1

- Eligible: at least three complete local-calendar days have elapsed and compatible priced MTD usage exists.
- Early month: projection is unavailable with a concise insufficient-history explanation.
- No usage: projection is unavailable rather than forcing a zero forecast.
- Partial pricing or coverage: the projection is explicitly partial and identifies the unsupported remainder when known.
- Stale calculation: the last valid projection remains visible with its calculation time and stale label.
- Failure: the cost summary remains usable and explains that projection could not be refreshed.
- Historical range: no projection element is rendered.
- Narrow viewport: projection remains secondary to the canonical cost and does not create a new horizontal overflow or card row.

## Historical Dependencies — Attempt 1

- PRD-0004 was `approved` during execution and is now `passed`.
- FEAT-0020 must be `passed` for canonical snapshot-priced cost and coverage semantics.
- FEAT-0022 must be `passed` for the dashboard summary, query state, and current-month context.
- This deferred Feature is not required for FEAT-0023 or for the core usage dashboard to pass.

## Historical Likely Affected Surfaces — Attempt 1

- usage calculation and projection module selected by the Spec
- `src/localbrain/queries.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/sessions_dashboard.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- projection formula, local-time, threshold, source-scope, route, UI-contract, accessibility, and browser tests
- synthetic early-month, partial, unpriced, stale, failure, and narrow-view fixtures

## Historical Pass Or Fail Checks — Attempt 1

- Pass if identical MTD inputs, local calculation time, source scope, and formula version produce the same projection.
- Pass if the value uses canonical snapshot-priced facts and never reprices historical usage.
- Pass if fewer than three complete local-calendar days produces an explicit insufficient-history state.
- Pass if no usage, unavailable pricing, partial coverage, stale data, and calculation failure remain distinct.
- Pass if changing source scope or calculation time updates the projection inputs and visible provenance coherently.
- Pass if historical and ineligible custom ranges show no month-end projection.
- Pass if the projection remains subordinate to canonical cost and introduces no duplicate primary chart or large KPI card.
- Pass if the user-facing language contains no budget, cap, quota, entitlement, billing, invoice, or actual-payment implication.
- Pass if representative responsive evidence preserves the existing summary hierarchy and essential controls.
- Fail if the Feature introduces predictive AI, external services, company governance, or a user budget.

## Historical Regression Surfaces — Attempt 1

- FEAT-0022 summary, history, query state, empty states, and responsive layout
- FEAT-0020 historical price snapshots and canonical estimated cost
- FEAT-0023 trust and partial-coverage wording
- existing source synchronization and failure behavior
- local-only operation and privacy-safe synthetic evidence

## Historical Feature Review Questions — Attempt 1

- None. The three-complete-day threshold and elapsed-local-month-fraction formula are the proposed boundary for human review; changing either before approval updates this Feature rather than the parent PRD.

## Harness Trace

- Active spec doc: [spec-0024-current-month-projection](../spec/spec-0024-current-month-projection.md)
- Active run: [run-20260718-28-retire-cost-projection-presentation](../run/run-20260718-28-retire-cost-projection-presentation.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [design attempt 2](../evaluation/eval-0024-design-retire-cost-projection-attempt-2.md), [functional attempt 2](../evaluation/eval-0024-functional-retire-cost-projection-attempt-2.md)
- Latest fix note: [fix-0026-retire-cost-projection-presentation](../fix/fix-0026-retire-cost-projection-presentation.md)

## Continuity Notes

- `2026-07-18`: initial deferred draft proposed one deterministic month-fraction trend estimate and explicitly excluded every budget, cap, allocation, and billing behavior.
- `2026-07-18`: defer dependencies passed; sequential execution activated `calendar-elapsed-v1` with a three-complete-day gate and no projection persistence.
- `2026-07-18`: Attempt 1 passed 70 tests, current Cost/Tokens/historical local HTTP visibility checks, source-level review, and privacy verification. Direct viewport evidence remains a PRD-level human acceptance gap.
- `2026-07-18`: human review superseded the visible outcome after finding the projection detail unnecessary. Attempt 2 passed with the presentation removed, the internal read model preserved, and 83 regression tests green.
- `2026-07-18`: the combined responsive evidence pass closed the remaining PRD-level viewport gap after the visible projection had already been retired; PRD-0004 is `passed`.
