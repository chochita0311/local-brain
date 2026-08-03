# EVAL-0070: Usage Source Scope And Composition — Functional

## Metadata

- ID: `eval-0070-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260802-75`
- Attempt: `1`
- Feature: [feat-0070-usage-source-scope-and-composition](../feature/feat-0070-usage-source-scope-and-composition.md)
- Spec: [spec-0070-usage-source-scope-and-composition](../spec/spec-0070-usage-source-scope-and-composition.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Usage read model, template, GET links, and enhanced navigation
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Verified aggregate/source selection, periods, metrics, composition, coverage,
  health, empty/error states, URL continuity, partial navigation, and regressions.

## Checks

- Controls expose `All`, Claude, personal Codex, and Codex Company in registry
  order, including an empty registered source.
- Company scope contains only company Usage; personal Codex remains disjoint even
  with matching record shapes and one shared provider adapter.
- Aggregate tokens, estimated cost, Usage Records, primary-work Sessions, MTD,
  and Daily history equal exact per-source results.
- Maintenance and Subsession records increase company Usage and cost but not the
  primary-work Session denominator.
- Source composition names Codex Company, carries Codex provider cue, and links to
  `/sessions?source=codex-company`.
- Source links preserve Weekly, Cost, Model, and paired custom dates. Unknown
  combined-Codex input returns `All` rather than creating a hidden grouping.
- An unavailable company source keeps three selected Usage Records visible,
  reports error freshness, retains last success, and exposes bounded consequence.
- Existing Daily/Weekly/Cumulative, custom invalid fallback, Tokens/Cost,
  Model/Project, unpriced/synthetic, projection, activity, and cardinality tests
  pass.
- Partial dashboard replacement keeps request cancellation, focus restoration,
  history/popstate, scroll restoration, and full-navigation failure fallback.

## Evidence

- Full repository suite: 322 tests passed.
- Focused Usage/UI/value/schema suite: 60 tests passed.

## Evidence Gaps

- Direct browser pointer, focus, history, and horizontal-scroll observation was
  unavailable because the Browser skill's required in-app control capability was
  not exposed. Route/read-model, generated links, rendered DOM, and client
  transition contracts are covered deterministically.

## Findings

- None.

## Route

- Next action: `pass`.
