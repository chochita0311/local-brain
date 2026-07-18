# EVAL-0020: Usage And Cost Fact Contract — Functional Attempt 3

## Metadata

- ID: `eval-0020-functional-attempt-3`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-26`
- Attempt: `3`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: parser → source-level repair → dashboard read model
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Runtime direct-event-first Codex parsing, replay exclusion, model and price resolution, automatic source-version repair, repeated synchronization, integrity, and dashboard consumption.

## Checks

- Exercised multiple direct events in one turn, cumulative-only fallback events, unchanged observations, cached-input subtraction, reasoning ownership, and dated auto-review normalization.
- Exercised initial spawned or forked replay records followed by original subsession activity.
- Exercised explicit corrective snapshot assignment while preserving frozen Project attribution, source-file unions, obsolete Fact deletion, and failure rollback.
- Ran the full automated regression suite, isolated Python compilation, diff validation, and repository privacy scan.
- Created a private online SQLite backup, ran the corrective all-source synchronization, repeated synchronization against active files, checked source and Fact contract convergence, verified pricing coverage and SQLite integrity, and rendered the dashboard route from the repaired read model.
- Compared LocalBrain and the installed ccusage report over the same local date boundary and token dimensions.

## Evidence

- All 80 automated tests passed.
- The private repair completed without source failures; all current Codex files and facts converged on the Attempt 3 contract and no legacy Codex Fact remained.
- Same-boundary Codex input, output, cache-read, and total tokens matched the installed report exactly.
- Repeated synchronization skipped unchanged files and processed only active files that had appended bytes.
- SQLite integrity returned `ok`; supported compared facts were priced by the corrective snapshot.
- The Sessions Dashboard route rendered successfully from the refreshed database, and scope-switch interaction tests retained the dashboard scroll position by replacing only the dashboard region.

## Evidence Gaps

- Direct in-app browser viewport capture was unavailable because the browser skill's required runtime was not exposed in this environment.
- Acceptance impact: `non-blocking`; this foundation repair changes normalized data, while the route render and existing interaction contract are covered automatically. PRD-0004 retains its separate combined viewport-evidence backlog item.

## Findings

- No implementation defect or acceptance blocker remains.
- The flat model-tier trend cost is intentionally slightly lower than the installed report when that report applies long-context tiering. This is expected under the approved non-invoice trend contract.
- An actively running Codex Session can append events between two comparisons; the dashboard request performs ordinary incremental synchronization and converges on refresh.

## Regression Notes

- Session parsing, attribution, dashboard ranges and breakdowns, scope-switch continuity, projection, source health, Search, Workstreams, Task Runner, and UI contracts passed.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: Attempt 3 replaces Attempt 2 as current FEAT-0020 Functional acceptance evidence.
- `2026-07-18`: RUN-20260718-27 supersedes this report for current price-contract acceptance after the flat-tier exclusion was removed by human decision.
