# EVAL-0036: Native Maintenance Session And Runner UI Consolidation — Functional

## Metadata

- ID: `eval-0036-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-41`
- Attempt: `1`
- Feature: [feat-0036-native-maintenance-session-and-runner-ui-consolidation](../feature/feat-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Spec: [spec-0036-native-maintenance-session-and-runner-ui-consolidation](../spec/spec-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Runner lifecycle, Session ingestion, routes, templates, generated contracts, and actual DB cleanup
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Checks And Evidence

- Targeted Runner, Session contract, ingestion policy, and UI contract tests passed before the full suite.
- Full repository suite passed: 138 tests covering ingestion, parsers, retrieval, Runner, schema migrations/presentation/audit, Session hierarchy, UI, Usage/cost, Dashboard, and Workstreams.
- Privacy check passed across 401 candidate files.
- Data Model docs, deterministic Schema presentation, 328-object cleanup ledger, and pinned Mermaid assets are current.
- Synthetic localhost routes returned 200 for Workstream and Dashboard; the Workstream rendered the selected base request, actual `claude --print ...` command, and stdin explanation. Both routes omitted marker controls.
- Native-parent regression proves the child relation, maintenance classification, metadata-only policy, zero event/search projection, null child Run FK, and work-stat exclusion.
- Actual DB cleanup deleted exactly two empty synthetic Sessions, retained their two Run ledgers, and passed integrity/FK checks.

## Evidence Gaps

- A new billable Claude Task Runner execution was not launched solely for evaluation. Parser marker behavior, native source normalization, command construction, terminal synchronization, child inheritance, and existing real-source ingestion are covered without incurring an external model run.
- Acceptance impact: non-blocking; no untested synthetic stream producer remains.

## Findings

- None.

## Route

- Next action: `pass`.
