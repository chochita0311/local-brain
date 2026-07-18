# PRD-0004: Session Usage And Cost Dashboard

## Metadata

- ID: `prd-0004`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Completion State

- All five implementation Features and the follow-up contract corrections through RUN-20260718-29 are `passed`.
- Current product behavior includes source-neutral usage facts, immutable Project and price snapshots, request-level Codex context-tier pricing, Daily/Weekly/Cumulative history, Source/Model/Project composition, and bounded trust states.
- The visible month-end projection was intentionally retired after human review, while its non-persisted read-model calculation remains internal compatibility behavior.
- The combined synthetic rendered-evidence pass at `1440`, `920`, `700`, and `320` is complete; no PRD-level acceptance gap remains.

## Request Summary

- Renew the Sessions Dashboard so the user can understand Claude and Codex token usage, estimated cost, activity history, and source, model, and Project composition without turning the page into a dense governance console.
- Preserve LocalBrain's source provenance and local-first trust model while using the owner-supplied Codex `/usage` output, the installed `ccusage` report dimensions, and the supplied company AI usage dashboard as references rather than as complete product specifications.

## Source Set

### Human Request

- Present usage clearly by meaningful metrics and make the associated monetary impact understandable.
- Keep the dashboard simple despite the large number of possible metrics.
- Use the owner-supplied Codex daily, weekly, and cumulative activity examples, the local `ccusage` package, the copied company usage dashboard, and the current LocalBrain Sessions Dashboard as references.
- Keep workflow and skill intelligence as a separate follow-up planning boundary in [PRD-0005](prd-0005-workflow-and-skill-intelligence.md).

### Golden Sources

- Owner-supplied Codex `/usage` examples: 12-month daily activity, weekly activity, cumulative activity, lifetime tokens, peak, streak, and longest-task summaries.
- Installed `ccusage` behavior inspected on 2026-07-18: `20.0.14` supplied the initial report dimensions and `20.0.17` supplied the later Codex event, fallback-model, fast-tier, and long-context parity reference. Both remain offline validation references rather than runtime dependencies.
- Owner-supplied company AI usage dashboard: month-to-date spend, projected month-end spend, remaining capacity, days remaining, source freshness, model or tool allocation, and compact metric hierarchy. It is a layout and information-hierarchy reference only; company-specific identity, quota governance, approval, and entitlement behavior does not transfer.
- [Design Constitution](../../policies/design/design-constitution.md): dashboard family, shell, provenance, hierarchy, density, responsive, state, and accessibility contract.

### Supporting Documents

- [Project Architecture](../../policies/project/architecture.md): current local runtime, source adapters, normalized activity, and read-model ownership.
- [Product Model](../../policies/project/product.md): Session, Project, Workstream, provenance, and reviewability responsibilities.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): local persistence, source boundaries, tracked evidence, and external-access constraints.
- [Design Evaluation](../../policies/design/design-evaluation.md): dashboard containment, source-use discipline, hierarchy, and rendered-evidence requirements.
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md): range changes, scope reset, state continuity, and control behavior.
- [Project Roadmap](../project/roadmap.md): planned Activity Insights phase.
- [PRD-0003](prd-0003-data-model-visibility-and-schema-cleanup.md): draft global data-model visibility and cleanup boundary; it does not own this PRD's usage and price semantics.
- [PRD-0005](prd-0005-workflow-and-skill-intelligence.md): sibling draft for personal workflow and skill insights.

### Current Implementation References

- `src/localbrain/templates/sessions_dashboard.html`: current scope controls, four-metric summary, usage history, one composition family, and trust presentation.
- `src/localbrain/main.py`: `/sessions-dashboard` query-state validation and route composition.
- `src/localbrain/usage_queries.py`: shared selected-Fact eligibility, period aggregation, breakdown, coverage, freshness, and internal projection compatibility read model.
- `src/localbrain/usage.py`: immutable price snapshots, request-level cost calculation, Usage Fact persistence, and source-level repair reconciliation.
- `src/localbrain/schema.sql`: normalized Usage Facts, immutable Project attribution fields, price snapshots, and model-price persistence.
- `src/localbrain/ingest/claude.py` and `src/localbrain/ingest/codex.py`: source-specific token, model, replay, pseudo-record, and contract-version normalization.
- `tests/test_usage_contract.py`, `tests/test_usage_dashboard.py`, `tests/test_activity_attribution.py`, and `tests/test_ui_contract.py`: synthetic contract, query, route, presentation, and interaction evidence.

## Current Findings

- Event, tool-call, and context-switch counts remain behavior evidence, not token usage or spend; the Sessions Dashboard now derives its usage hierarchy only from eligible Usage Facts.
- Usage Facts retain token components, raw and normalized model identity, immutable Project attribution, price snapshot, calculator version, and source capability state required for reproducible trend estimates.
- `ccusage` remains an independently versioned offline comparison reference. The page neither invokes it nor adopts its current JSON as an internal schema.
- Claude and Codex keep source-specific normalization rules for cache, reasoning, cumulative versus direct event usage, replay exclusion, fallback models, and pseudo-records while exposing one source-neutral read contract.
- Historical Project and price attribution remain frozen. Later Git-root discovery and ordinary catalog updates enrich current or future facts without silently rewriting past statistics.
- Estimated cost is model-priced trend context, not subscription charge, entitlement use, credit consumption, invoice, or actual payment.
- The dashboard uses one compact metric and history hierarchy. The company reference's repeated capacity, allocation, entitlement, and projection surfaces were not carried into the current product.

## Product Intent

- Let the user answer, at a glance, how much Claude and Codex activity occurred in a selected period, what it would cost under the stated price basis, how usage changed over time, and which source, model, or Project contributed to it.
- Make every number inspectable and honest about source coverage, calculation basis, freshness, exclusions, and unavailable pricing.
- Keep workflow behavior, repeated-process analysis, and skill recommendations out of the primary usage view so cost observability remains calm and understandable.

## Confirmed Scope

### Usage And Cost Semantics

- Define a source-neutral normalized usage record or equivalent read contract that can represent:
  - source kind and source record identity
  - Session and optional parent-Session identity
  - Project or workspace attribution when known
  - occurrence or aggregation period
  - model identity and raw source model name
  - input tokens
  - output tokens
  - cache-creation or cache-write tokens when supported
  - cache-read tokens when supported
  - reasoning tokens when separately reported
  - total-token semantics without double counting
  - one canonical estimated cost in USD when model-specific pricing is available
  - price snapshot identity or calculator version and calculation time
  - unavailable-price state when no compatible model price exists
  - source freshness and capability limitations
- Preserve original Claude and Codex local records as authority. Normalized usage and estimated cost remain derived, rebuildable LocalBrain facts.
- Include every directly observed real-model usage record in token and cost totals regardless of Session class or role, including primary work Sessions, maintenance Sessions, and subsessions. Retain source-generated pseudo assistant or API-error records as Session evidence but exclude them from usage dates, totals, coverage, breakdowns, and usage-linked Session counts. Prevent double counting when a source-level parent total already includes child usage.
- Keep workflow-oriented Session counts and behavior metrics on their explicitly labeled scope, such as primary work Sessions only, instead of applying that narrower scope to monetary totals.
- Calculate one canonical trend cost from the source adapter's supported model and token fields using the matching model-specific price snapshot. Do not calculate, store for comparison, or display parallel alternative cost figures for the same usage record.
- When the inspected model catalog defines a context-price boundary, choose the tier independently for each source usage record from its normalized input context. Do not promote one threshold crossing to an entire Session, day, or month.
- Freeze each historical cost against the price snapshot used when it was calculated. Later ordinary pricing updates apply only to new usage and never rewrite past dashboard statistics automatically; a separately approved corrective contract repair may replace an invalid snapshot without changing token or Project provenance.
- Use `ccusage` as a report-dimension and validation reference. It is not a required LocalBrain connector, source of authority, or page-time executable dependency.
- Never silently treat an unpriced model, missing token component, unreadable source record, or unsupported source capability as zero usage or zero cost.
- Label monetary values as estimates intended for trend comparison. Do not use wording equivalent to billed or actually paid.

### Project Attribution Semantics

- Preserve the Session-observed working path, source path, Git branch when supplied, and the basis used to resolve its Project or workspace as immutable provenance.
- Snapshot each usage record's Project or workspace attribution when the record is normalized. Historical Project breakdowns use that stored attribution rather than a later current-path lookup.
- Allow later scans to enrich current workspace metadata, including a Git root discovered after a directory becomes a Git repository, without silently reassigning prior Sessions or rewriting historical Project totals.
- Apply new or changed Project-path and Git-root relations only to source usage records first observed after the relation changes. Rebuilding derived facts for an older record must reuse its stored attribution snapshot; previously unassigned or differently assigned history remains stable unless a future, explicitly reviewable user action owns reconciliation.
- Keep automatic historical Project reconciliation and bulk retroactive reassignment outside this increment.

### Activity-Time Semantics

- Distinguish observed Session span from estimated active time.
- Build activity segments from consecutive observed events. Events separated by 30 minutes or less belong to the same segment; a gap longer than 30 minutes starts a new segment.
- Calculate estimated active time from the bounded activity segments rather than the full first-to-last Session span.
- Define longest active segment as the longest continuous activity segment under the same 30-minute rule. Do not present it as equivalent to Codex's server-supplied longest-running-turn metric.
- End an incomplete Session at its last observed event rather than the current time.
- Merge overlapping activity segments when calculating total active time across concurrent Sessions so the same wall-clock interval is not counted twice.
- Label active time and longest active segment as estimates rather than exact focused-work duration.

### Dashboard Information Hierarchy

- Retain `/sessions-dashboard` and the current persistent LocalBrain shell.
- Provide one dominant Overview surface with:
  - period and source selection
  - last-calculated or last-synchronized state
  - a compact four-metric summary
  - one primary Usage and Cost History panel
  - a compact cost-composition region
  - a Source, Model, and Project breakdown surface
  - a bounded data-coverage and pricing-health region
- The initial summary metrics are:
  - canonical estimated cost for the selected period, with its price-snapshot context
  - total tokens for the selected period, with compact token-component context
  - Session count, with a derived average only when its denominator is complete
  - active days, with streak, peak, or longest-active-segment context only when the metric contract supports it
- Keep Cost mode limited to observed selected-period and month-to-date estimates. Do not surface a projected month-end value in the summary.

### Period And History Views

- Support source scope for all supported sources, Claude, and Codex without losing the visible selected period.
- Provide `Tokens` and `Cost` metric modes and daily, weekly, and cumulative aggregation modes inside one history family.
- Use the most recent 30 local-calendar days as the default Daily window, the most recent 12 local-calendar weeks as the default Weekly window, and all eligible usage history as the default Cumulative window.
- Keep current-month usage and cost available as explicitly labeled month-to-date summary context rather than shortening the default Daily trend at the start of each month.
- Represent range and view state through idempotent GET query parameters so refresh, browser history, and bookmarks reproduce the selected dashboard state.
- Use `view=daily|weekly|cumulative` for the history view and inclusive local-calendar `from=YYYY-MM-DD` and `to=YYYY-MM-DD` parameters for a custom range. When `from` and `to` are absent, apply the selected view's default window.
- Use the owner-supplied 12-month activity treatment as the reference for long-range daily density, streak, peak, and cumulative context without reproducing terminal glyphs literally.
- Avoid a default dual-axis chart that asks the user to compare token and cost scales simultaneously.
- Range, source, metric, and aggregation controls must expose visible and programmatic selected state and remain reachable at supported viewport widths.

### Breakdown And Traceability

- Provide Source, Model, and Project breakdowns with period-scoped tokens, cost, Session count, share, and last activity when supported.
- Prefer a compact ranked list or table over large repeated cards for high-cardinality model and Project data.
- Link Project and Session-backed summaries to existing LocalBrain browse or detail destinations when identity is resolvable.
- Keep source provenance distinct from health, selection, price availability, and cost status.
- Move current tool-call frequency and context-switch analysis out of the primary cost hierarchy and into the PRD-0005 workflow-insight boundary.

### Trust, Freshness, And Failure States

- Show the last successful source synchronization and last successful usage or cost calculation without exposing internal storage paths on the ordinary dashboard.
- Show source coverage, partially supported token fields, unpriced models, stale calculations, and failed refreshes as explicit bounded states.
- Distinguish no activity, no matching activity, unavailable pricing, incomplete source coverage, and calculation failure.
- Keep previously valid data visible with a stale or partial label when a refresh fails, rather than replacing it with an empty success state.
- Explain the active pricing snapshot and unavailable-price state in concise user-facing language with deeper details available through bounded disclosure.

### Responsive And Interaction Expectations

- Preserve the shared shell and current `/sessions-dashboard` destination.
- Use the Design Constitution's `920px`, `700px`, and `320px` boundaries; simplify layout and metadata before reducing type.
- Keep one coherent reading order: scope, summary, history, composition or breakdown, and trust state.
- Preserve selected range and source state when following a breakdown and returning when the route contract supports it.
- Ensure essential data and actions do not depend on hover.
- Use bounded loading, working, stale, empty, partial, and error states inside the owning dashboard region.

## Excluded Scope

- Company quota allocation, entitlement tiers, approval chains, request-more actions, organization governance, or employee identity behavior from the supplied company dashboard.
- Claiming that calculated token cost equals subscription fees, company spend, credits, invoices, or actual personal payment.
- Billing-provider or company-finance integration.
- Currency conversion, exchange-rate history, tax, or KRW display in the initial increment.
- Personal monthly budgets, caps, spend-limit warnings, or quota-governance behavior.
- Automatic historical Project reconciliation or bulk retroactive Project reassignment from later path or Git-root discovery.
- Workflow topics, repeated errors, file-type analysis, tool-sequence analysis, productivity interpretation, skill usage, or skill recommendations; those belong to PRD-0005.
- New external AI services, remote pricing calls at page render time, telemetry, cloud sync, or external writes.
- Treating `ccusage` as a required installed dependency, source adapter, or canonical LocalBrain schema.
- Broad shared-shell redesign, new navigation destinations, or company-dashboard visual cloning.

## Uncertainty

- No unresolved product-boundary questions remain from the initial review.
- Feature and Spec review still own bounded implementation details such as invalid or partial date-parameter handling, the exact Project-attribution snapshot shape, and pagination or chart-density limits. Those details must preserve the confirmed behavior above and must not reopen budget scope or automatic historical reconciliation.

## User-Visible Flows And Interaction Expectations

### Open And Orient

- The user opens Sessions Dashboard and immediately sees the active period, source scope, calculation freshness, estimated cost, token usage, Session volume, and activity context.
- The surface does not require the user to understand source JSONL, pricing files, or `ccusage` commands.

### Change Scope

- The user changes period, source, metric, or aggregation and sees one coherent replacement state without losing the persistent shell or exposing partial internal data.
- Scope changes make exclusions and partial coverage visible rather than silently changing the denominator.

### Inspect Composition

- The user compares Source, Model, or Project contribution and can follow resolvable Project or Session evidence to existing LocalBrain destinations.
- Returning to the dashboard preserves the useful scope when supported by the approved route contract.

### Understand Trust

- The user can determine which pricing snapshot produced an estimate and whether the result is stale, partial, or unavailable.
- A source failure or unknown model price leaves prior valid information visible with an explicit limitation and recovery path.

## Constraints

- Explicit human direction and the approved PRD boundary govern scope.
- Original Claude and Codex local records remain authority; normalized usage and snapshot-priced cost remain derived and rebuildable.
- LocalBrain remains local-first, single-user, and usable without an external network call.
- No local Session content, model history, price input, path, or report output may be transmitted externally without explicit approval.
- Runtime data, reports, screenshots, tests, and fixtures follow [Privacy And Data Handling](../../policies/project/privacy-and-data.md); tracked evidence uses synthetic content.
- Metric definitions must be reproducible, versioned where price or normalization rules can change, and explicit about unavailable fields.
- Design borrows information hierarchy from references only inside the Sessions Dashboard content boundary; the shared shell and Design Constitution remain authoritative.
- The likely execution model begins with a `foundation-contract` Feature for usage and price semantics, followed by `fullstack-product` Features for read models and presentation.
- Visible Features require Contract, Design, Functional, and UX Heuristic evaluation as applicable, including rendered checks at representative `1440`, `920`, `700`, and `320` widths.
- Future scope or contract changes still require the repository's human approval gates; completed Run evidence does not authorize silent expansion.

## Acceptance Envelope

- Every displayed token and monetary metric has a documented source scope, time scope, inclusion rule, component rule, and freshness state.
- Token and cost totals include directly observed maintenance and subsession usage without parent-child double counting, while primary-work behavior metrics retain their separately labeled scope.
- Each usage record contributes at most one snapshot-priced estimated cost, and unavailable pricing never appears as zero or actual billing.
- Historical estimated costs remain stable after later model-price updates.
- Estimated active time and longest active segment use the approved 30-minute activity-segment rule, last-observed-event ending, and overlapping-segment deduplication, and the UI does not equate the latter with Codex longest-running-turn duration.
- Daily defaults to the most recent 30 days, Weekly to the most recent 12 weeks, and Cumulative to all eligible usage history; current-month summaries remain available as explicitly labeled MTD context.
- Custom date ranges and the selected history view are reproducible through inclusive local-calendar GET query parameters.
- Historical Project breakdowns use snapshot attribution and remain stable when later scans discover a Git root or change current workspace metadata.
- Total tokens do not double count cache or reasoning components, and source capability differences remain visible.
- The default dashboard lets the user understand selected-period usage and cost through at most four primary summary metrics, one history family, one breakdown family, and one bounded trust region.
- Daily, weekly, cumulative, Source, Model, Project, empty, stale, partial, unpriced, and failure states remain understandable and contained.
- Existing Session, Project, source-health, source synchronization, shell, and navigation behavior does not regress.
- Every nondecorative summary either links to inspectable LocalBrain evidence or states why no drill-down is available.
- The dashboard remains usable without `ccusage` installed and without a network connection.
- Synthetic contract, query, route, UI, and browser evidence proves the approved metric definitions and representative responsive states.
- No Workflow or Skill Intelligence behavior is implemented implicitly through this PRD.

## Candidate Features

- [FEAT-0020: Usage And Cost Fact Contract](../feature/feat-0020-usage-and-cost-fact-contract.md) (`foundation`, `data`, `passed`): define source-neutral token components, model identity, Session scope, parent-child deduplication, immutable price provenance, canonical estimated cost, freshness, and source capability rules.
- [FEAT-0021: Activity And Project Attribution Contract](../feature/feat-0021-activity-and-project-attribution-contract.md) (`foundation`, `data`, `passed`): define Session-time Project attribution snapshots, current Git metadata enrichment boundaries, 30-minute activity segments, overlap handling, and longest-active-segment semantics.
- [FEAT-0022: Usage Summary And History](../feature/feat-0022-usage-summary-and-history.md) (`product`, `fullstack`, `passed`): provide period and source scope, four-metric summary, token or cost mode, and daily, weekly, or cumulative history.
- [FEAT-0023: Usage Breakdown And Trust](../feature/feat-0023-usage-breakdown-and-trust.md) (`product`, `fullstack`, `passed`): provide Source, Model, and Project composition, drill-downs, coverage, stale, partial, unpriced, and failure states.
- [FEAT-0024: Current-Month Projection](../feature/feat-0024-current-month-projection.md) (`product`, `fullstack`, historical `passed`): its calculation remains internal compatibility behavior, while RUN-20260718-28 retires the visible projection from the dashboard.

The human owner approved this boundary, and all five Feature loops plus the later normalization, pricing, presentation, pseudo-record, and responsive-evidence checks passed.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human request | primary | clear usage, monetary context, simple hierarchy, and reference selection | does not authorize company governance, billing integration, or Workflow Intelligence |
| Codex `/usage` examples | primary visual and metric reference | long-range activity, daily/weekly/cumulative modes, lifetime, peak, streak, and longest-task cues | terminal presentation and current labels are not direct screen specifications |
| Installed `ccusage` behavior | primary data-dimension reference | token components, models, costs, periods, Sessions, blocks, burn rate, projection, JSON, and offline behavior | not a connector, source of authority, mandatory dependency, or stable internal schema |
| Supplied company dashboard | supporting information-hierarchy reference | compact KPI hierarchy, projection, freshness, cost composition, and trust cues | identity, allocation, entitlement, approval, quota, and organization behavior do not transfer |
| Current LocalBrain code and schema | implementation truth | normalized Usage Facts, immutable attribution and price snapshots, route state, history, composition, trust, and retained Session evidence | behavior-oriented event counts remain separate from usage and cost denominators |
| Design and interaction policies | durable presentation contract | shell, dashboard family, density, provenance, responsive, accessibility, and state behavior | do not decide token or price semantics |
| PRD-0005 | sibling planning boundary | workflow, error, file, topic, tool-sequence, and skill intelligence | must not expand the cost dashboard into a generic insight wall |

## Continuity Notes

- `2026-07-18`: created the initial draft from the owner-supplied Codex activity examples, installed `ccusage` inspection, company dashboard reference, current Sessions Dashboard, and durable LocalBrain contracts.
- `2026-07-18`: separated usage and cost observability from Workflow And Skill Intelligence so the primary dashboard can remain simple and each data contract can be reviewed independently.
- `2026-07-18`: recorded model-priced cost as an estimate and left the default period and optional personal budget open for human review.
- `2026-07-18`: human review fixed the monetary scope to all directly observed usage, including maintenance Sessions and subsessions, with source-aware parent-child deduplication and separately labeled primary-work behavior metrics.
- `2026-07-18`: human review chose one ccusage-like model-specific trend estimate instead of parallel reported and calculated costs, froze historical values to their original pricing snapshots, and fixed estimated active time and longest active segment to 30-minute activity segments.
- `2026-07-18`: human review set Daily to 30 days, Weekly to 12 weeks, and Cumulative to all ingested history; chose reproducible GET query parameters for custom dates; excluded all personal budget and cap behavior; and froze historical Project attribution while allowing current workspace and Git metadata enrichment.
- `2026-07-18`: clarified that LocalBrain's 30-minute-derived metric is longest active segment, not Codex's server-supplied longest-running-turn duration.
- `2026-07-18`: human owner approved the PRD boundary. Feature Planner split the accepted scope into two foundation contracts, two core dashboard product Features, and one deferred current-month projection Feature.
- `2026-07-18`: FEAT-0020 through FEAT-0024 passed their execution loops with 70 tests, local HTTP checks, and privacy verification. Source-level Design, Functional, and UX evaluations pass; direct combined `1440`, `920`, `700`, and `320` browser evidence remains required before human post-run acceptance.
- `2026-07-18`: live post-run validation invalidated FEAT-0020's synthetic latest-per-turn Codex assumption. Human review approved a return to Spec for cumulative-delta normalization, bounded Claude cache-create parity, and automatic versioned repair without a user-facing aggregate-reset control; RUN-20260718-25 owns the correction and private local backfill.
- `2026-07-18`: RUN-20260718-25 passed with cumulative Codex deltas, bounded Claude cache-create fallback, source-file-union contract repair, private local refresh, and no aggregate-reset control. FEAT-0020 is restored to `passed`.
- `2026-07-18`: a later installed-report and official-adapter comparison invalidated RUN-20260718-25 as current acceptance evidence. FEAT-0020 is blocked pending human approval to revise SPEC-0020 around `last_token_usage`-first normalization, dated fallback models, model coverage, and configured service-tier pricing; no second runtime repair has been run.
- `2026-07-18`: human review approved Attempt 3. RUN-20260718-26 passed with direct-event-first Codex normalization, cumulative fallback, spawned and forked replay exclusion, dated fallback models, one immutable `fast` trend-price snapshot, private local repair, and repeat-sync integrity evidence. FEAT-0020 is restored to `passed` without a reset control or runtime ccusage dependency.
- `2026-07-18`: human review approved a return to SPEC-0020 after the remaining cost variance was isolated to request-level long-context tiers. Attempt 4 keeps trend and non-invoice semantics while requiring model-specific context thresholds and above-threshold rates from the frozen ccusage reference.
- `2026-07-18`: RUN-20260718-27 passed with per-Fact request-context tiers, an immutable calculator-v2 snapshot, private corrective repair, and exact fixed-boundary token and estimated-cost parity against the installed offline ccusage reference.
- `2026-07-18`: human review found the visible `Projected month end` detail unnecessary. RUN-20260718-28 removed the entire projection block and its dedicated styles from Cost mode while retaining the existing observed-cost, MTD, coverage, freshness, filters, and internal compatibility calculation.
- `2026-07-18`: human review confirmed that real Haiku subsession usage remains monetary usage while Claude `<synthetic>` assistant and API-error records are evidence rather than usage. RUN-20260718-29 keeps those records in SQLite and Session activity but excludes them from every Sessions Dashboard usage consumer.
- `2026-07-18`: documentation reconciliation replaced stale baseline and blocked-state wording with the completed implementation truth. PRD status remains `approved` only for the open combined rendered-evidence requirement; no functional Feature remains blocked.
- `2026-07-18`: a privacy-safe synthetic dashboard passed direct rendered checks at `1440`, `920`, `700`, and exact mobile-emulated `320`. Scope controls, the four-metric band, 30-day local chart scrolling, long Model and Project labels, overflow and price disclosures, error/stale trust states, and in-place scroll continuity remained contained and usable. PRD-0004 is `passed`.
