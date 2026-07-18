# SPEC-0024: Current-Month Projection

## Metadata

- ID: `spec-0024`
- Status: `approved`
- Run ID: `run-20260718-28`
- Attempt: `2`
- Parent Feature: [feat-0024-current-month-projection](../feature/feat-0024-current-month-projection.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `design`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Implementation Goal

- Remove the visible month-end projection from Cost mode without changing observed cost, MTD context, price coverage, freshness, filters, history, breakdowns, or the internal compatibility calculation.

## In-Scope Behavior

- Remove the projection conditional and all projection copy from `sessions_dashboard.html`.
- Remove the now-unused `usage-projection-context` style family.
- Render no projection element for Cost, Tokens, current, historical, partial, stale, unavailable, or failed states.
- Preserve the four-metric summary grid and all existing scope controls and partial dashboard replacement behavior.
- Keep `calendar-elapsed-v1` in the read model for compatibility; do not expose it through the current template.

## Out-Of-Scope Behavior

- Removing or redesigning the internal projection calculation, changing Usage Facts, price snapshots, query parameters, persistence, history, breakdown, trust, or scope-switch interactions.

## State And Interaction Contract

- No dashboard state renders a projected month-end element.
- Cost retains only the canonical observed estimate and its ordinary coverage detail in the summary card.
- Source, range, custom-date, Tokens/Cost, and breakdown controls continue replacing only the dashboard region and preserve scroll position.

## Evaluation Focus

- Absence of projection copy, value, provenance, timestamp, and dedicated style rules.
- Preservation of the four-metric family, Cost history, MTD strip, trust coverage, and scope controls.
- No backend or persistence regression.

## Open Blockers

- None. The former defer condition is satisfied by passed FEAT-0020, FEAT-0022, and FEAT-0023. Direct viewport evidence remains unavailable and must be recorded explicitly.

## Continuity Notes

- `2026-07-18`: approved `calendar-elapsed-v1` with exact local elapsed fraction, a three-complete-day gate, current-date containment, compatible priced facts, and no persistence.
- `2026-07-18`: Attempt 2 supersedes only the presentation contract after human review withdrew the visible projection; the internal calculation remains unchanged for compatibility.
