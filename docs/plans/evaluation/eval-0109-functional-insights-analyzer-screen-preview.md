# EVAL-0109 Functional: Insights Analyzer Screen Preview

## Metadata

- ID: `eval-0109-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run: [RUN-20260928-119](../run/run-20260928-119-insights-analyzer-screen-preview.md)
- Attempt: `1`
- Feature: [FEAT-0109](../feature/feat-0109-insights-analyzer-screen-preview.md)
- Spec: [SPEC-0109](../spec/spec-0109-insights-analyzer-screen-preview.md)
- Execution Profile: `frontend-product`
- Evidence Coverage: `partial`
- Created: `2026-09-28`

## Scope And Checks

- Directly loaded `/sessions-dashboard/insights` on the active local server. The source-backed leader, ordered list, counts, and local last-use times rendered; the route handler and query were unchanged.
- Browser inspection found the question text area and both analyzer buttons disabled. No analyzer Run or form submission is wired into this preview.
- Clicked the native example disclosure and observed it collapse; reloading restored the initially open example. The sample contains no Session link or review action.
- Clicked `Usage & Cost`, observed `/sessions-dashboard`, then returned by browser history to Insights.
- Checked viewport widths of 1440px and 320px; the document had no horizontal overflow at 320px.

## Evidence Gaps

- The no-skill and partial-synchronization states were not rendered with a separate runtime fixture. Source inspection shows the existing conditional ranking/empty branches remain inside the left column, the coverage notice remains above the grid, and the right preview is outside that conditional. This gap is non-blocking for a preview that does not change those data paths.
- No automated tests were requested or run. This report covers browser-observed presentation and interaction only.

## Findings And Route

- No functional defect found in the observed state. Route: `pass` to owner screen review.
