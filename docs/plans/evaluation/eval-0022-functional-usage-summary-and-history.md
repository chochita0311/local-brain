# EVAL-0022: Usage Summary And History Functional

## Metadata

- ID: `eval-0022-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-22`
- Attempt: `1`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Execution Profile: `fullstack-product`
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Evidence

- Native GET links and the paired date form preserve view, source, metric, and valid custom bounds without client code.
- Invalid date pairs retain the selected non-date scope, use its default bounds, and render one bounded status message.
- Empty source, filtered no-match, unpriced cost, mixed price coverage, freshness, and calculation context are owned by the summary or history region.
- Temporary-server checks returned `200` for default, custom Weekly Codex Cost, and reversed-date fallback URLs.
- All 66 tests passed, including synthetic read-model and template render coverage.

## Rendered Interaction Evidence

- The synthetic dashboard rendered all Source, Range, Tokens/Cost, date, and breakdown controls with matching current-state semantics at every required width.
- Exact `320` mobile emulation exposed all 30 history columns through a bounded `290px` local scroller while the page itself remained exactly `320px` wide.
- With the composition control visible, a browser click from Model to Project preserved `scrollY` exactly at `1708.5`, updated the URL and selected state together, and announced the bounded replacement through the live status region.
- Native breakdown and price disclosures opened by click at `320`; their rows and explanation remained present and contained.

## Findings

- No tested route, data, form, or selected-state failure remains.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: post-run browser checks closed the direct interaction and narrow-screen evidence gap.
