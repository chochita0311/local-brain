# FEAT-0106: First Session Insights View

## Metadata

- ID: `feat-0106`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend`, `frontend`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Created: `2026-09-27`
- Updated: `2026-09-28`

## Goal

Let the owner switch from Usage & Cost to a first Insights view and read the most-used skill plus the complete observed-use ranking.

## Acceptance Contract

- Replace `세션 보기` in the Sessions Dashboard heading with `Insights`. The Insights heading offers a reciprocal `Usage & Cost` link in the same position. Both links use distinct bookmarkable routes, preserve the Sessions Dashboard shell, and work without JavaScript.
- The initial Insights view shows the leading skill immediately and every skill with at least one admitted observed use in descending count order. Currently installed skills with zero observed uses do not appear; formerly installed skills with retained observations do.
- The ranking counts all observed history and has its own source-coverage/empty state. Usage & Cost date, metric, and breakdown controls do not scope it. The first view does not display an `All time` or signal-coverage explainer line.
- The displayed count sums the same normalized skill name across Claude Code, Codex, and Codex Company. Rows follow rank order without a redundant rank-number column; each shows name, count, and the latest admitted event time under `마지막 사용`. No source or Session disclosure is shown. A missing event time is labeled unavailable rather than replaced with sync time.
- Retained observations whose Session is gone continue to contribute to the count.
- The Usage & Cost first request does not run Insights analysis or load its ranking.

## Scope Boundary

- In: Insights route, source-neutral ranking query, simple first-view presentation, reciprocal heading navigation, empty/partial coverage states, and owner docs.
- Out: frequent-question analysis, workflow suggestions, inferred skills, extra date/project filters, ranking by quality or productivity, and background external analysis.
- The owner chose same-name aggregation for the visible ranking. Normalize harmless case and surrounding whitespace differences before grouping; preserve source-specific identity in storage for later use.

## Surface Lanes

- Backend: ranking/coverage query and route; consumes passed FEAT-0105 observation contract.
- Frontend: heading action replacement and new Insights template/styles within the existing shell.

## Contract Surfaces

- Routes: `/sessions-dashboard` and proposed `/sessions-dashboard/insights`.
- Data: source-backed observation rows from FEAT-0105, grouped for display only.
- Design: existing Sessions Dashboard heading action, density, responsive layout, and active LNB state.

## Pass Or Fail Checks

- Both directions of the heading navigation render directly, after refresh, and through browser history.
- Ranking order is count descending with a stable tie rule; the leading skill is visible before scrolling and the full used-only list remains available.
- An absent source Session retains its count; ranking rows contain no Session links.
- Empty, partial, and long-list states remain readable at the design constitution's representative widths.
- Usage & Cost route and current cost/token interactions remain unaffected.

## Dependencies

- FEAT-0105 foundation acceptance before this product Feature's formal acceptance. The historical product implementation existed before that acceptance was recorded.

## Regression Surfaces

- Sessions Dashboard route, heading and source/date controls, Sessions LNB destination, responsive shell, and fast initial usage view.

## Harness Trace

- Spec: [SPEC-0106](../spec/spec-0106-first-session-insights-view.md)
- Run: [RUN-20260928-124](../run/run-20260928-124-first-session-insights-view.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract](../evaluation/eval-0106-contract-first-session-insights-view.md), [design](../evaluation/eval-0106-design-first-session-insights-view.md), [functional](../evaluation/eval-0106-functional-first-session-insights-view.md), and [UX](../evaluation/eval-0106-ux-first-session-insights-view.md)

## Continuity Notes

- `2026-10-02`: [FEAT-0111](feat-0111-automatic-skill-load-observation.md) extends the view with observed-load wording and a concise count explanation alongside automatic-read admission. The first-release layout/navigation contract and earlier evaluations remain historical evidence.

- `2026-09-27`: proposed from the owner's confirmed heading-action navigation and first skill-ranking scope. The owner chose same-name counts summed across sources and explicit-only source signals; the planned product build depended on a passed observation contract.
- `2026-09-27`: the owner removed the redundant `사용 순위` section heading and separate rank-number display, and requested a `마지막 사용` column after the count.
- `2026-09-28`: formal evaluation of the existing view passed after FEAT-0105 acceptance. Synthetic browser review covered navigation and filled, empty, partial, long-list, and retained-without-current-file states. The historical build preceded foundation acceptance; this dependency-order gap is recorded in RUN-124.
