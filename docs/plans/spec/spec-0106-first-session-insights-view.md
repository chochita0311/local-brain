# SPEC-0106: First Session Insights View

## Metadata

- ID: `spec-0106`
- Status: `approved`
- Parent Feature: [FEAT-0106](../feature/feat-0106-first-session-insights-view.md)
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `backend`, `frontend`
- Created: `2026-09-27`
- Updated: `2026-09-28`

## Implementation Goal

This document records the first-release view. [SPEC-0111](spec-0111-automatic-skill-load-observation.md) owns its approved observed-load terminology and automatic-read extension.

Expose an Insights view from the existing Sessions Dashboard heading action, with the most-used skill and complete all-time ranked list as its first content.

## Route And Interaction

- `/sessions-dashboard` keeps the fast Usage & Cost request. Its existing `세션 보기` heading link becomes `Insights`, pointing to `/sessions-dashboard/insights`.
- `/sessions-dashboard/insights` uses the same shell and active LNB item. Its heading action is `Usage & Cost`, pointing back to `/sessions-dashboard`.
- Native links make direct entry, refresh, browser history, and no-script navigation work. No extra tab row or first-page Insights query is introduced.

## Ranking And States

- Query valid observations only and group by normalized skill name across all source keys. Order by count descending and normalized name ascending on ties. Show the most-used skill at the top and every positive-count group in a compact table.
- Keep each row to skill name, observed-use count, and the latest parsable `occurred_at` from its admitted observations. Row order conveys rank without a separate number. Display `마지막 사용` after the count in compact local `YYYY.MM.DD HH:mm` form; label missing timestamps as unavailable. Do not render a row disclosure or fetch source and live Session detail for the first view. Historical observations with missing Sessions still count.
- Count all observed history without an `All time` or signal-coverage explainer line. Claude `Skill` calls and Codex-generated `<skill>` loads remain the admission contract; direct `SKILL.md` reads and mere mentions stay outside the count.
- If no observations exist, distinguish no recorded uses after extraction from initial or partial source coverage; do not imply that no skills were ever used. If observations remain but no current Session file is tracked, identify retained history and absent current source coverage.
- Do not show future analysis cards or recommendations as live results until their later Features exist.

## Surface Lanes

- Backend: bounded ranking and coverage projection from FEAT-0105 ledger plus route composition.
- Frontend: existing heading link, new Insights template, and scoped responsive styles.

## Evaluation Focus

- The initial Usage & Cost route does not call the Insights query.
- Both heading links, partial-coverage notice, long names, ties, empty and missing-time states, retained counts with missing Sessions, and full list readability across the design widths.
- The existing Sessions LNB link remains the direct raw Session inventory destination.

## Open Blockers

- None for acceptance. FEAT-0105 passed before FEAT-0106's formal product evaluation; the historical product implementation had already been built before that foundation acceptance was recorded.
