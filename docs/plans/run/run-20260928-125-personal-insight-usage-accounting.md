# RUN-20260928-125: Personal Insight Usage Accounting

## Metadata

- ID: `run-20260928-125`
- Status: `passed`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md), approved usage accounting correction
- Execution Profile: `backend-product`
- Lanes: `data`, `backend`
- Required Evaluators: `contract`, `functional`
- Attempt: `1`
- Created: `2026-09-28`
- Updated: `2026-09-28`

## Goal And Authority

The owner requested that Insights analysis count toward estimated cost after review exposed a PRD-to-Feature planning gap. Restore that approved requirement while keeping analysis outside ordinary Sessions and future personal-analysis evidence. The existing analysis workflow, model choice, report, and execution directory remain the basis of this correction.

## Contract And Verification Boundary

Use the existing usage calculator and dashboard consumers, a metadata-only accounting parent, source-profile attribution, and unassigned Project attribution. Capture usage independently of report success and reconcile retained evidence idempotently. Verify with synthetic local data; this Run does not authorize a paid analysis or transmission of private Session excerpts.

## Execution And Evaluation

- Added a dedicated ephemeral-analysis usage normalizer. New Runs freeze their exact registered Codex Source and Standard tier; observed CLI usage is stored before report validation and enters the existing Decimal cost calculator and dashboard queries.
- Added a metadata-only Maintenance Session accounting parent with no workspace, events, conversation, search, or ordinary Session visibility. Its Run-derived identity prevents replay double counting. Native stale-file cleanup and Usage-contract repair preserve this separately owned projection.
- Startup recovers retained terminal Run summaries or CLI usage events, using indexed Usage identities to avoid repeatedly scanning native usage. Report failure, cancellation, or interruption retains emitted usage. Missing evidence is not fabricated.
- Updated the Feature/Spec correction, PRD continuity, README, architecture, privacy, data-model owners, and generated schema presentation. No table migration, price change, ordinary Session filter change, or dashboard layout change was needed.
- [Contract evaluation](../evaluation/eval-0110-contract-insight-usage-accounting.md): `PASS`; evidence coverage `complete` for the bounded local accounting contract.
- [Functional evaluation](../evaluation/eval-0110-functional-insight-usage-accounting.md): `PASS`; evidence coverage `partial` because no real provider was invoked. Synthetic tests and a running local server in isolated Chrome verified the affected consumers.

## Verification And Existing Failures

- The focused set covers Insights, usage, native Session synchronization, activity/project attribution, Session inventory, and schema presentation: 97 tests, 89 passed, 8 failed. All eight failures also reproduce from the unchanged Git HEAD in temporary checkouts: six older pricing/snapshot expectations in `test_usage_contract.py`, and two stale table-count/public-URL expectations in `test_schema_presentation.py`. They are not regressions from this correction and remain outside its scope.
- An isolated Chrome browser rendered synthetic analysis usage as $0.78 and 110K tokens in the selected Codex source, with Project `Unassigned` and zero primary work Sessions. `/sessions` had no analysis row or Session-detail link; Insights retained the Run history.
- Data-model ownership checks, generated schema presentation checks, privacy checks, and whitespace checks pass. No private Session content or paid model execution was used for validation.
- The preferred browser connector had an occupied profile. A separate task-owned headless Chrome profile provided the required rendered evidence. The synthetic server, database, browser profile, and temporary baseline checkouts were removed after verification.

## Post-Contract Review And Handoff

- Historical RUN-120 remains implementation history; its no-Usage boundary is explicitly superseded by this correction. The current requirement is cost inclusion with ordinary-Session and analysis-evidence exclusion.
- The running application must load the updated Python modules, normally through restart. Startup recovery then accounts for retained observations without rerunning analysis. The owner can review a real Insights Run after reload; actual provider compliance, emitted usage availability on early failure, and recommendation quality remain unobserved.
- No reusable design or interaction policy candidate was introduced. The remaining human review is the actual analysis result and its observed cost, not a new approval of the already requested accounting fix.
