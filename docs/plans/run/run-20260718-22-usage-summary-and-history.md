# RUN-20260718-22: Usage Summary And History

## Metadata

- ID: `run-20260718-22`
- Status: `passed`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Deliver and verify the four-metric usage summary, native GET scope controls, and one token-or-cost history family.

## Selected Loop

- Feature type: `product`
- Surface: `fullstack`
- Surface lanes: read model → route → frontend content → evidence
- Required evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Current phase: complete

## Surface Lanes

- Read model and route:
  - path roots: `usage_queries.py`, `activity.py`, `main.py`
  - dependencies: passed FEAT-0020 and FEAT-0021
  - validation evidence: deterministic scope, summary, bucket, freshness, and HTTP fixtures
  - evaluator ownership: `contract`, `functional`
- Frontend content:
  - path roots: Sessions Dashboard template and shared styles
  - dependencies: stable route model
  - validation evidence: synthetic render, semantics, representative widths where browser runtime permits
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- `/sessions-dashboard` GET state, local calendar bounds, usage summary/read model, history buckets, selected semantics, and bounded unavailable states.

## Invocation Context

- Golden sources: approved PRD/Feature/Spec, current Sessions Dashboard, Codex usage and company hierarchy references.
- Relevant policies: Design Constitution, Design Evaluation, Interaction Evaluation, Product Model, Project Architecture.
- Optional skills or tools expected: `screen-alignment` in `adapt` mode; in-app Browser if its runtime becomes available.

## Current Artifacts

- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Contract evaluation: [eval-0022-contract-usage-summary-and-history](../evaluation/eval-0022-contract-usage-summary-and-history.md)
- Design evaluation: [eval-0022-design-usage-summary-and-history](../evaluation/eval-0022-design-usage-summary-and-history.md)
- Functional evaluation: [eval-0022-functional-usage-summary-and-history](../evaluation/eval-0022-functional-usage-summary-and-history.md)
- UX heuristic evaluation: [eval-0022-ux-usage-summary-and-history](../evaluation/eval-0022-ux-usage-summary-and-history.md)
- Fix log: [fix-0023-sessions-dashboard-scope-continuity](../fix/fix-0023-sessions-dashboard-scope-continuity.md)

## Evaluation Coverage

- Contract: PASS, complete evidence.
- Design: PASS, complete evidence, including direct synthetic rendering at `1440`, `920`, `700`, and exact mobile-emulated `320`.
- Functional: PASS, complete evidence, including bounded narrow-screen disclosures and exact scroll-position continuity during analytical scope replacement.
- UX heuristic: PASS, complete evidence across desktop, compact, and narrow reading sequences.

## Current Route

- Next role: none; the parent PRD is `passed`.
- Current blocker classification: none
- In-run route: complete
- Post-run closure: the later combined dashboard review closed the original viewport and interaction evidence gap without changing this Run's implementation.

## Attempts

- Attempt 2:
  - status: passed with partial browser evidence
  - input: human runtime report that link-backed scope switches reset the main document scroll
  - outcome: the same GET destinations now replace only the Sessions Dashboard region, preserve the captured scroll coordinate, history, selected state, and focus, and retain normal-link fallback
- Attempt 1:
  - status: passed
  - outcome: source, route, synthetic render, local HTTP, full suite, and privacy checks passed
  - notes: browser runtime availability remains an explicit final-acceptance evidence constraint

## Post-Contract Regression Check

- Needed: yes
- Result: PASS; 66 tests passed.
- Notes: shared shell, Sessions, Projects, source synchronization, and prior usage contracts remained green.

## Human Review Outcome

- Decision: sequential execution authorized
- Returned layer if any: none
- Follow-up run: FEAT-0023 after this Feature completes

## Continuity Notes

- `2026-07-18`: Orchestrator selected fullstack-product, read-model-first lane order, and screen-alignment `adapt` mode.
- `2026-07-18`: Attempt 1 passed and routed sequential execution to FEAT-0023; direct viewport evidence remains combined PRD follow-up work.
- `2026-07-18`: Attempt 2 addressed the confirmed scope-continuity defect with screen-alignment `extend` mode, 77 passing tests, JavaScript syntax validation, and temporary-server HTML/asset `200` checks. Direct scripted browser interaction was unavailable, so exact live scroll-coordinate evidence remains partial.
- `2026-07-18`: RUN-20260718-29 supersedes the selected-Fact eligibility detail after human review classified Claude `<synthetic>` records as stored evidence rather than usage; the original layout and interaction results remain valid.
- `2026-07-18`: post-run browser evidence completed the `1440`, `920`, `700`, and `320` checks and confirmed exact Model-to-Project scroll continuity; PRD-0004 is `passed`.
