# EVAL-0023: Usage Breakdown And Trust Functional

## Metadata

- ID: `eval-0023-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-23`
- Attempt: `1`
- Feature: [feat-0023-usage-breakdown-and-trust](../feature/feat-0023-usage-breakdown-and-trust.md)
- Spec: [spec-0023-usage-breakdown-and-trust](../spec/spec-0023-usage-breakdown-and-trust.md)
- Execution Profile: `fullstack-product`
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Evidence

- Model and Project local HTTP requests returned `200` and rendered the correct selected breakdown, preserved range/source/metric/custom dates, composition empty state, and trust region.
- Source and Project links target existing Session inventory filters; a single eligible model Session may target its existing detail route, while aggregated rows state that no exact filter exists.
- Native `details` owns high-cardinality and price explanation disclosure without JavaScript or transient binding state.
- Error and stale trust states do not remove the already selected usage summary, history, or composition.
- All 68 tests passed, including high-cardinality, alias, immutable Project, error retention, synthetic render, and UI semantic checks.

## Rendered Interaction Evidence

- Direct Model and Project routes rendered the correct selected control and retained source, range, and metric state.
- At `320`, native clicks expanded both the two-row composition overflow and the price explanation; the page retained zero horizontal overflow.
- Model-to-Project replacement preserved the exact document scroll position while updating URL, selection, content, and live feedback coherently.
- Synthetic Claude stale and Codex error files retained the 30 selected facts, prior successful timestamps, partial price coverage, and usable summary/history/composition regions.

## Findings

- No tested route, link, grouping, disclosure, or retained-data behavior failed.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-07-18`: post-run browser evidence closed the direct disclosure, scroll-continuity, and narrow-screen gap.
