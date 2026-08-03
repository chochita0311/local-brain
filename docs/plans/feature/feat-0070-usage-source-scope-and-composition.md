# FEAT-0070: Usage Source Scope And Composition

## Metadata

- ID: `feat-0070`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Goal

- Let the owner compare combined Usage with Claude, personal Codex, and Codex
  Company statistics independently under the same range, metric, model, Project,
  price, and Session-denominator contracts.

## Acceptance Contract

- Sessions Dashboard presents peer source scopes `All`, `Claude`, `Codex`, and
  `Codex Company`; `Codex` selects only personal Codex and no combined-Codex
  primary scope is introduced.
- Source scope and source breakdown group by stable source identity, not provider
  kind. Personal and company Codex remain separate even though both use Codex
  token, model, cumulative-delta, and price-normalization semantics.
- `All` totals, history, MTD context, projections, coverage, freshness, and
  composition include all accepted source identities under the current selected
  time/metric contract. Its source composition exposes one row per source and the
  compatible totals equal the source-row sum.
- Selecting one source applies the existing Daily, Weekly, Cumulative, custom-date,
  Tokens/Cost, Model, Project, price-coverage, and evidence behavior only to that
  source. GET state remains reproducible and invalid source keys fall back to
  `All`.
- Direct real-model Usage from primary work, Maintenance, and Subsessions remains
  eligible. The separately labeled Session count continues to include only
  usage-linked primary work Sessions in the selected period and source.
- Claude raw model `<synthetic>`, unsupported pricing, incomplete components,
  immutable price snapshots, first-observation Project attribution, and
  normalizer-version repair behavior remain unchanged.
- Freshness and trust rows consume FEAT-0068 per-source health, preserve previously
  calculated Usage during unavailable/error states, and distinguish Claude,
  personal Codex, and Codex Company by readable label.
- Analytical source, range, metric, and breakdown changes preserve surrounding
  document orientation and current progressive-enhancement behavior.

## Scope Boundary

- In:
  - registry-driven Usage source controls and stable-key scope normalization
  - all-source and per-source Usage fact selection, aggregates, history,
    projection, coverage, freshness, and breakdown queries
  - source-identity composition and readable dashboard provenance
  - exact Session-denominator and aggregate/source-sum verification
  - query-backed interaction, GET/no-script behavior, responsive rendering, and
    privacy-safe synthetic evidence
- Out:
  - Session ingestion, parser, token normalization, cumulative-delta repair, price
    calculation, snapshot, or Project-attribution semantic changes
  - Sessions inventory scopes and provenance owned by FEAT-0069
  - combined-Codex primary scope, nested account selector, or Gemini support
  - billing reconciliation, budget alerts, quotas, exports, or native account API
  - source settings editing, disablement, removal, purge, archive, or restore

## Surface Lanes

- Usage query and contract lane:
  - path roots: Usage scope normalization, fact selection, summaries, history,
    projections, coverage, composition, freshness, and focused tests
  - dependencies: passed FEAT-0068 and FEAT-0069 stable source consumers
  - expected evidence: stable-key isolation, all/source arithmetic parity, exact
    Session denominator, and unchanged normalization/pricing semantics
  - evaluator ownership: `contract`, `functional`
- Dashboard presentation lane:
  - path roots: Sessions Dashboard template, source controls, composition/trust
    rows, labels, source cues, and responsive styles
  - dependencies: Usage query and contract lane
  - expected evidence: peer scopes, readable Codex distinction, coverage context,
    selected-state clarity, and containment at all target widths
  - evaluator ownership: `design`, `functional`, `ux-heuristic`
- Dashboard interaction lane:
  - path roots: query URL construction, partial dashboard loading, back/forward,
    focus/live status, and no-script fallback
  - dependencies: Usage query and dashboard presentation lanes
  - expected evidence: coherent in-place analytical transitions and preserved
    range/metric/breakdown state when source changes
  - evaluator ownership: `functional`, `ux-heuristic`
- Durable contract lane:
  - path roots: product, architecture, Usage, interaction, design, and value owner
    docs
  - dependencies: all implementation lanes
  - expected evidence: source identity and provider normalization remain distinct
    and no stale hard-coded source vocabulary remains
  - evaluator ownership: `contract`

## Contract Surfaces

- Sessions Dashboard `source` GET parameter and stable-key normalization
- Usage fact source filtering and source-identity breakdown key
- combined/source aggregate arithmetic and compatible-total denominator
- usage-linked primary-work Session count denominator
- freshness/trust projection from per-source synchronization state
- dashboard source controls, composition rows, and query URL producer/consumer

## Required Evaluators

- `contract`: source-key fact selection, aggregate arithmetic, Usage versus Session
  denominators, freshness handoff, and preserved normalization/price ownership.
- `design`: peer source controls, composition/trust provenance, retained-data
  warning hierarchy, analytical density, and responsive containment.
- `functional`: every source/range/metric/breakdown combination, custom dates,
  projections, Maintenance/Subsession usage, unsupported coverage, freshness,
  back/forward, and no-script behavior.
- `ux-heuristic`: personal/company Codex distinction, analytical switch continuity,
  empty/error explanation, and trust in combined totals.

## User-Visible Outcome

- The owner can see total AI Usage or isolate company Codex statistics without
  changing the meaning of tokens, estimated cost, coverage, or Session counts.

## Entry And Exit

- Entry point: open Sessions Dashboard or select a peer Source control.
- Exit or transition behavior: the selected source updates summary, history,
  composition, coverage, and freshness as one coherent analytical state while
  preserving valid range, metric, breakdown, dates, URL, and document orientation.

## State Expectations

- Default: `All` combines every accepted local AI source and shows traceable source
  composition.
- Selected: one stable source key constrains every selected Usage and denominator
  consumer.
- Empty source: identifies that source and selected period without implying all
  sources lack Usage.
- Unavailable/error: retained calculated Usage remains visible with bounded source
  attention state and last-success context.
- Unsupported calculation: keeps existing explicit unavailable and coverage
  behavior rather than substituting zero.
- Loading/transition: current analytical controls remain stable, expose bounded
  live status, and do not jump the surrounding document.

## Dependencies

- [FEAT-0068](feat-0068-multi-source-session-synchronization-and-health.md) must be
  `passed` before build.
- [FEAT-0069](feat-0069-session-source-scope-and-provenance.md) must be `passed`
  before build so Session-source presentation and denominator terminology are
  already stable.

## Likely Affected Surfaces

- `src/localbrain/usage_queries.py`
- Usage Dashboard route/read-model adapters
- `src/localbrain/templates/sessions_dashboard.html`
- `src/localbrain/static/app.js`
- `src/localbrain/static/styles.css`
- value-registry source and Usage labels
- Usage scope, aggregate, history, projection, coverage, freshness, browser, and
  interaction tests
- product, architecture, Usage, design, and interaction owner docs

## Pass Or Fail Checks

- Pass if `All`, Claude, personal Codex, and Codex Company select exactly their
  intended Usage facts and `Codex` never includes company records.
- Pass if `All` compatible totals and source composition equal the sum of matching
  source rows for tokens, estimated cost, Usage facts, and eligible Sessions.
- Pass if Maintenance and Subsession direct Usage remains included while their
  Sessions remain excluded from the separately labeled primary-work denominator.
- Pass if range, dates, metric, breakdown, source, projections, price coverage,
  freshness, and GET/no-script state remain coherent across source changes.
- Pass if both Codex sources share normalization and price semantics but retain
  readable, statistically independent provenance at `1440`, `920`, `700`, and
  `320` widths.
- Fail on provider-grouped source totals, combined-Codex scope, denominator drift,
  recalculated price snapshots, source-switch scroll jumps, or hidden unavailable
  evidence.

## Regression Surfaces

- PRD-0004 Usage fact, summary, history, breakdown, trust, and projection contracts
- Claude `<synthetic>` exclusion and real-model Maintenance/Subsession inclusion
- immutable price snapshots and first-observation Project attribution
- Daily, Weekly, Cumulative, custom-date, Tokens/Cost, Model, and Project controls
- FEAT-0068 health and FEAT-0069 source identity/provenance contracts
- progressive dashboard loading, back/forward, responsive shell, and privacy

## Harness Trace

- Active spec doc: [spec-0070-usage-source-scope-and-composition](../spec/spec-0070-usage-source-scope-and-composition.md)
- Active run: [run-20260802-75-usage-source-scope-and-composition](../run/run-20260802-75-usage-source-scope-and-composition.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [Contract](../evaluation/eval-0070-contract-usage-source-scope-and-composition.md)
  - [Design](../evaluation/eval-0070-design-usage-source-scope-and-composition.md)
  - [Functional](../evaluation/eval-0070-functional-usage-source-scope-and-composition.md)
  - [UX heuristic](../evaluation/eval-0070-ux-usage-source-scope-and-composition.md)
- Latest fix note: none

## Continuity Notes

- `2026-08-02`: proposed as the final PRD-0012 Product Feature so Usage can consume
  passed source identity, configuration, ingestion, health, and Sessions
  provenance contracts without redefining them.
- `2026-08-02`: human owner approved this Feature boundary for sequential
  execution after FEAT-0069 passes.
- `2026-08-02`: RUN-20260802-75 entered the Fullstack Product execution loop.
- `2026-08-02`: attempt 1 passed all required source-level evaluators. Browser
  evidence remains an explicit non-blocking follow-up because the required
  in-app control capability was unavailable; 322 tests and privacy checks pass.
