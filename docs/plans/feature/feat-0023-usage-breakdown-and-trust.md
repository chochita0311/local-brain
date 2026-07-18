# FEAT-0023: Usage Breakdown And Trust

## Metadata

- ID: `feat-0023`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Let the user explain a selected-period total by Source, Model, and Project and determine whether the estimate is complete, current, priced, and traceable without turning Sessions Dashboard into a dense governance console.

## Acceptance Contract

- Source, Model, and Project breakdowns consume the same selected period, source, metric, and custom-range contract as FEAT-0022.
- Each supported breakdown row provides period-scoped tokens, canonical estimated cost or explicit unavailable state, eligible Session count, share of the compatible total, and last activity when the underlying facts support them.
- Source provenance remains visually and semantically distinct from selection, health, freshness, pricing availability, and error state.
- Model rows preserve an inspectable raw model value when normalization or grouping changes the display label.
- Model rows consume the eligible real-model set and never create a row or price-coverage limitation for Claude `<synthetic>` assistant or API-error evidence.
- Project rows use the immutable attribution snapshot from FEAT-0021 rather than current-path reconciliation, and unresolved attribution remains explicitly Unassigned.
- High-cardinality Model and Project data uses a compact ranked list or table with bounded paging or disclosure rather than repeated large cards.
- Resolvable Project and Session evidence links to existing LocalBrain destinations. Returning to the dashboard preserves useful query scope when the approved route contract supports it.
- The trust region states last successful source synchronization, last successful usage or cost calculation, source coverage, partial token support, unpriced models, stale calculations, and failed refreshes without exposing internal storage paths.
- No activity, no matching activity, incomplete source coverage, unavailable pricing, stale data, and calculation failure are separate states.
- A refresh or calculation failure keeps previously valid data visible with a stale or partial label rather than replacing it with an empty success state.
- Concise disclosure explains the active price snapshot and unavailable-price meaning without claiming estimated cost is actual billing.
- The composition and trust regions fit after the summary and history in one coherent reading order at `1440`, `920`, `700`, and `320` widths.

## Scope Boundary

- In:
  - Source, Model, and Project breakdown modes
  - period-scoped token, cost, Session, share, and last-activity values
  - raw versus normalized model traceability
  - snapshot-based Project attribution and Unassigned state
  - compact ranking, bounded pagination, or disclosure for high cardinality
  - links to existing resolvable Project and Session evidence
  - synchronization, calculation, coverage, pricing, stale, partial, and failure trust states
  - price-snapshot and unavailable-price explanation
  - responsive, accessible, synthetic route, query, UI, and browser evidence
- Out:
  - summary and primary history ownership from FEAT-0022
  - current-month projection from FEAT-0024
  - automatic Project reconciliation, path aliases, bulk historical reassignment, or Project editing
  - budgets, caps, quotas, allocation, approvals, currency conversion, or actual billing
  - tool-call frequency, context switching, repeated workflows, and skill recommendations
  - new detail routes or shared-shell redesign

## Surface Lanes

- Breakdown read-model lane:
  - path roots: `src/localbrain/queries.py`, `src/localbrain/main.py`
  - dependencies: FEAT-0020, FEAT-0021, and FEAT-0022 passed
  - expected evidence: compatible denominators, ranked Source, Model, and Project values, raw-model traceability, Unassigned attribution, drill-down targets, and bounded cardinality
  - evaluator ownership: `contract`, `functional`
- Trust-state read-model lane:
  - path roots: source synchronization, usage calculation, query, and route modules selected by the Spec
  - dependencies: FEAT-0020 capability and price states
  - expected evidence: freshness, coverage, partial, unpriced, stale, retained-valid-data, and failure state fixtures
  - evaluator ownership: `contract`, `functional`
- Frontend and interaction lane:
  - path roots: `src/localbrain/templates/sessions_dashboard.html`, `src/localbrain/static/styles.css`, `src/localbrain/static/app.js`
  - dependencies: both read-model lanes and FEAT-0022 dashboard hierarchy
  - expected evidence: compact ranking, accessible mode state, evidence links, bounded disclosure, reading order, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- Source, Model, and Project breakdown read-model shapes and compatible denominators
- source provenance versus status semantics
- raw and normalized model identity presentation
- snapshot Project attribution and Unassigned grouping
- Session-count eligibility and share calculation
- ranked-result cardinality, ordering, and bounded continuation behavior
- existing Project and Session route targets with dashboard-scope return state
- source synchronization and usage-calculation freshness values
- coverage, partial, unpriced, stale, retained-valid-data, and failure states
- price-snapshot explanation content and disclosure ownership

## Required Evaluators

- `contract`: denominator parity, grouping identity, model and Project traceability, drill-down shape, freshness, coverage, pricing, and retained-valid-data contracts.
- `design`: ranked density, hierarchy after history, provenance versus status, disclosure containment, long labels, and representative responsive rendering.
- `functional`: mode changes, ordering, shares, Unassigned data, evidence links, return scope, partial pricing, stale data, and refresh failure behavior.
- `ux-heuristic`: comparison efficiency, trust comprehension, drill-down clarity, disclosure friction, and avoidance of governance-console or card-wall patterns.

## User-Visible Outcome

- The user can identify which source, model, or Project contributed to the selected total and understand why a cost may be partial, stale, or unavailable before trusting or drilling into it.

## Entry And Exit

- Entry point: breakdown and trust regions below FEAT-0022's summary and history on `/sessions-dashboard`.
- Exit or transition behavior: selecting Source, Model, or Project changes the composition view in place; resolvable evidence opens existing LocalBrain destinations and preserves a useful return scope.

## State Expectations

- Default: compact Source breakdown aligned to the active dashboard scope.
- Model: normalized label with raw source identity inspectable when they differ.
- Project: stored snapshot attribution with a visible Unassigned row when needed.
- High cardinality: initial ranked subset remains scannable and continuation does not destabilize the page.
- Partial pricing: token totals remain available while priced share and unavailable records are distinguished.
- Stale: prior valid values remain visible with last-success and stale labels.
- Failed refresh: the trust region explains the failure and recovery boundary without showing a false empty success state.
- No activity or no match: explanation reflects the active scope and does not imply a source failure.
- Narrow viewport: ranking becomes a contained list before essential labels, values, or links are removed.

## Dependencies

- PRD-0004 was `approved` during execution and is now `passed`.
- FEAT-0020 must be `passed` for usage, model, price, capability, and freshness facts.
- FEAT-0021 must be `passed` for stable Project attribution.
- FEAT-0022 must be `passed` so the breakdown consumes an established dashboard route, query state, and hierarchy.

## Likely Affected Surfaces

- `src/localbrain/queries.py`
- `src/localbrain/main.py`
- source synchronization and usage-calculation state modules selected by the Spec
- `src/localbrain/templates/sessions_dashboard.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- breakdown, denominator, attribution, pricing-state, route, UI-contract, accessibility, and browser tests
- synthetic unknown-model, long-label, Unassigned, partial, stale, failure, and high-cardinality fixtures

## Pass Or Fail Checks

- Pass if Source, Model, and Project totals reconcile to the compatible selected-scope total or explain the exact unsupported remainder.
- Pass if every row's tokens, cost, Session count, share, and last activity use documented support and denominator rules.
- Pass if provenance cannot be mistaken for health, selection, pricing, or success state.
- Pass if normalized Model rows retain inspectable raw source identity.
- Pass if Project rows use stored attribution snapshots and later Git-root enrichment does not change historical grouping.
- Pass if unresolved attribution appears as Unassigned rather than disappearing or using a current-path guess.
- Pass if high-cardinality data stays compact and usable without repeated large cards or horizontal page overflow.
- Pass if resolvable evidence links reach existing destinations and preserve useful dashboard return scope.
- Pass if sync, calculation, coverage, partial, unpriced, stale, and failure states are distinct and truthful.
- Pass if a failed refresh retains previously valid data and does not render an empty success state.
- Pass if representative `1440`, `920`, `700`, and `320` evidence preserves scope, ranking meaning, trust context, and essential actions.
- Fail if budget, allocation, quota, actual billing, Workflow Intelligence, or automatic Project reconciliation enters the surface.

## Regression Surfaces

- FEAT-0022 summary, history, URL state, and responsive hierarchy
- existing Session and Project routes, filters, and missing-path behavior
- source synchronization and source-health presentation
- Claude and Codex provenance semantics
- shared dashboard, list, table, disclosure, focus, and narrow-view patterns
- local-only operation, private runtime data, and synthetic evidence requirements

## Feature Review Questions

- None. The Spec may choose bounded page size or disclosure geometry but must preserve compact ranking and compatible totals.

## Harness Trace

- Active spec doc: [spec-0023-usage-breakdown-and-trust](../spec/spec-0023-usage-breakdown-and-trust.md)
- Active run: [run-20260718-23-usage-breakdown-and-trust](../run/run-20260718-23-usage-breakdown-and-trust.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract](../evaluation/eval-0023-contract-usage-breakdown-and-trust.md), [design](../evaluation/eval-0023-design-usage-breakdown-and-trust.md), [functional](../evaluation/eval-0023-functional-usage-breakdown-and-trust.md), [ux](../evaluation/eval-0023-ux-usage-breakdown-and-trust.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-18`: initial draft separated explanatory composition and trust states from the primary summary and history so the default dashboard remains calm.
- `2026-07-18`: sequential execution approved an eight-row native disclosure, compatible selected-metric shares, immutable Project grouping, and a bounded trust region under screen-alignment `adapt` mode.
- `2026-07-18`: Attempt 1 passed 68 tests, Model/Project local HTTP checks, source-level design and interaction review, and privacy verification. Direct viewport evidence remains a PRD-level human acceptance gap.
- `2026-07-18`: RUN-20260718-29 removed Claude `<synthetic>` pseudo-model rows from the shared selected Fact set while retaining real-model subsession rows such as Haiku.
- `2026-07-18`: post-run synthetic renders at all required widths closed the combined composition, trust, disclosure, and long-label evidence gap; PRD-0004 is `passed`.
