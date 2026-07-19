# EVAL-0033: Usage Record Dashboard Terminology — UX Heuristic

## Metadata

- ID: `eval-0033-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260719-38`
- Attempt: `1`
- Feature: [feat-0033-usage-record-dashboard-terminology](../feature/feat-0033-usage-record-dashboard-terminology.md)
- Spec: [spec-0033-usage-record-dashboard-terminology](../spec/spec-0033-usage-record-dashboard-terminology.md)
- Execution Profile: `fullstack-product`
- Surface Lane: count comprehension, consistency, and narrow reading order
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated whether a Dashboard user can understand what the count represents without learning warehouse-style Fact terminology.

## Checks And Evidence

- `usage records` reads as a count of selected stored usage entries next to Total tokens, pricing, Source, and coverage context; the screen no longer requires knowledge of an analytical Fact concept.
- Surrounding token, cost, Source, and calculation language keeps a usage record distinct from a Session, request, invoice line, or Activity Event.
- Singular/plural handling avoids `1 usage records`, and thousands separators make large counts scannable.
- The same term is repeated through summary, limitation, composition, freshness, Trust, and calculation explanation rather than switching between Fact, entry, row, or event.
- At 320px, one-column summary cards keep label → value → explanation reading order and remove the value collision found during the first rendered inspection.
- Existing controls, drill-down evidence, and the calculation disclosure remain discoverable; no new concept or interaction is introduced.

## Evidence Gaps

- None.

## Findings

- No blocking contradiction or non-blocking terminology suggestion remains.

## Regression Notes

- Internal engineering documents may continue to say Usage Fact; the product policy now explicitly owns the visible-versus-internal terminology boundary.

## Route

- Next action: `pass`.
