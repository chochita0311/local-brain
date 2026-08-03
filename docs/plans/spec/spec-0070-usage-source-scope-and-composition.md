# SPEC-0070: Usage Source Scope And Composition

## Metadata

- ID: `spec-0070`
- Status: `approved`
- Run ID: `run-20260802-75`
- Attempt: `1`
- Parent Feature: [feat-0070-usage-source-scope-and-composition](../feature/feat-0070-usage-source-scope-and-composition.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: Usage query/contract → dashboard presentation → interaction → docs
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-02`
- Updated: `2026-08-02`

## Source Set

- FEAT-0070, PRD-0012, and passed FEAT-0068/0069 contracts.
- Current Usage read model, Sessions Dashboard route/template/client behavior,
  Usage tests, Source registry/health, and source value dictionary.
- Design Constitution, Design Evaluation, Interaction Evaluation, Usage and
  Session owner contracts.

## Implementation Goal

- Make stable registered Session Source identity the one Usage scope and source
  composition key while preserving every existing Usage normalization, pricing,
  period, activity, and denominator rule.

## Lane Order And Handoffs

1. Usage query/contract owns dynamic source options, scope normalization, fact
   filtering, composition identity, health projection, and arithmetic parity.
2. Dashboard presentation consumes labels/provider cues without hard-coded
   Claude/Codex source controls or raw stable keys as user-facing provenance.
3. Interaction keeps the existing GET/no-script and partial-navigation contract
   across the expanded source option set.
4. Docs reconcile source identity, aggregate/source arithmetic, and health owner.

## In-Scope Behavior

- Query registered local AI Session sources whose provider adapter is Claude or
  Codex in stable Source-ID order. Produce `All` followed by each stable key,
  configured display label, and provider kind; empty registered sources remain
  selectable.
- Normalize `source` against that runtime option set. Unknown or omitted keys use
  `all`; valid future keys require no new hard-coded control vocabulary.
- Exact selected-source filtering remains `sources.kind = ?`. Provider kind is
  used only for adapter-derived synthetic exclusion and visual provider cues.
- Add configured source name to selected Usage rows. Source composition groups by
  stable source key, displays that name, retains provider cue separately, and
  links to the matching Sessions inventory scope.
- All-source aggregate, MTD, history, projection, limitations, coverage,
  freshness, and source composition consume the complete accepted Source set.
  Tokens, priced cost, Usage Record counts, and primary-work Session counts must
  equal the corresponding exact per-source sums under the same date range.
- Selected-source Daily, Weekly, Cumulative, custom dates, Tokens/Cost,
  Source/Model/Project composition, activity, coverage, and projection keep their
  current semantics.
- Direct real-model Maintenance and Subsession Usage remains eligible. Only the
  separately labeled Session denominator requires `work` plus `primary`.
- Freshness reads FEAT-0068 Source attempt/success/status/error fields and current
  Source File evidence. Completed/empty scans are current; unavailable,
  configuration error, or scan failure is attention/error; legacy rows without a
  source-level result retain the existing file-status fallback. Retained Usage
  stays visible.
- Trust rows expose configured source label, provider cue, selected Usage count,
  source scan status, last success, and bounded stale/error file evidence.
- Source-control links preserve valid view, metric, breakdown, and paired custom
  dates. Existing enhanced partial replacement, focus return, history state,
  scroll restoration, failure fallback, and ordinary links remain unchanged.
- Heading, history orientation, and empty copy use the selected source label,
  avoiding raw `codex-company` or obsolete two-provider wording.

## Out-Of-Scope Behavior

- Parser, normalizer, token, cumulative-delta, calculation, price snapshot,
  Project attribution, Activity segmentation, or Usage persistence changes.
- Combined-Codex scope, nested account selector, source editing/removal, Gemini,
  billing, budgets, export, quotas, or month-end projection presentation.
- New source colors for two roots sharing the same provider.

## State And Interaction Contract

- Default/invalid: `All` is selected and combines all accepted source identities.
- Selected: summary, MTD, history, composition, limitations, activity, freshness,
  and internal projection agree on one exact stable source key.
- Empty: names the selected source and period without implying aggregate data is
  empty or that the source is disabled/deleted.
- Attention: unavailable/error source health keeps retained Usage visible and
  explains that synchronization needs attention.
- Transition: source links retain view, metric, breakdown, and valid custom dates;
  the dashboard region alone changes, selected control receives focus, history
  state and scroll position remain recoverable, and no-script navigation works.
- Responsive: registry-driven source peers remain reachable through bounded
  horizontal overflow; configured labels and trust/composition rows wrap within
  existing 1440/920/700/320 layout families.

## Data And Contract Assumptions

- `sources.kind` is the stable user-facing source identity; `provider_kind` is the
  parser/normalizer family and may be shared.
- Registry reconciliation has already established unique accepted source keys and
  immutable provider-kind ownership.
- `usage_records.source_id` and `session_id` provide source-scoped fact and
  primary-work Session identity; no new schema is required.
- Existing `<synthetic>` exclusion, timestamp boundaries, immutable snapshot,
  coverage, and first-observation Project rules remain authoritative.

## Contract Surfaces

- Producer expectations: Usage read model emits ordered source controls, selected
  source label, exact source-key facts, source-name/provider composition, and
  source-level health/trust rows.
- Consumer expectations: route, template, and client treat controls as dynamic GET
  links and never infer source identity from provider cue or label.
- Generated artifacts: none unless an owner doc digest changes; rebuild schema
  presentation and cleanup audit when required by their existing contract.
- Source-of-truth owner: Source registry and scans, Usage and cost records,
  architecture, product, design, and interaction policies.
- Stale-assumption check: no `VALID_SOURCES` or hard-coded Claude/Codex-only
  dashboard controls, composition labels, or empty copy remain.

## Acceptance Mapping

- Peer scopes → ordered registry query, runtime normalization, and dynamic links.
- Independent Codex identities → exact `sources.kind` facts/composition with
  shared `provider_kind = codex` normalization and visual cue.
- Aggregate arithmetic → synthetic three-source token/cost/fact/Session tests.
- Existing Usage semantics → focused period, price, synthetic, Maintenance,
  Subsession, Project, coverage, projection, and activity regressions.
- Health/trust → FEAT-0068 source-level result mapping plus retained Usage test.
- Interaction continuity → GET URLs, partial replacement, focus/history/scroll,
  no-script links, DOM semantics, and responsive containment contracts.

## Evaluation Focus

- All/personal/company exact membership and aggregate per-source sums.
- Source composition key, configured label, provider cue, Sessions evidence link,
  compatible share, and trust row distinction.
- Invalid keys, custom dates, every range/metric/breakdown producer, and empty or
  retained-error state.
- Control and analytical containment at 1440/920/700/320.

## Open Blockers

- None.

## Continuity Notes

- `2026-08-02`: Spec locked after FEAT-0069 passed; no source, Usage, or design
  ambiguity remains for build.
