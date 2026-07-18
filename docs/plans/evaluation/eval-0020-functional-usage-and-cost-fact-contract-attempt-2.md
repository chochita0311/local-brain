# EVAL-0020: Usage And Cost Fact Contract — Functional Attempt 2

## Metadata

- ID: `eval-0020-functional-attempt-2`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-25`
- Attempt: `2`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: parser → persistence repair → dashboard read model
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Runtime cumulative-delta parsing, cache fallback, automatic version repair, repeat synchronization, data integrity, and dashboard consumption.

## Checks

- Exercised multiple positive Codex cumulative increments, unchanged observations, cached-input subtraction, and reasoning-as-output-subset behavior.
- Exercised Claude's positive nested cache breakdown against a contradictory zero aggregate.
- Exercised two files sharing one Session identity, obsolete Fact deletion, version freshness, repeat-scan skipping, and persistence rollback.
- Ran the full automated regression suite and isolated Python compilation.
- Ran the corrected contract through the configured private Session sources, repeated synchronization, checked SQLite integrity and legacy-version absence, and rendered the dashboard route from the refreshed read model.

## Evidence

- All 76 automated tests passed, including an active-file append race fixture.
- The first private repair processed every configured Session file without failure.
- Repeat synchronization skipped unchanged current-version files and reprocessed only actively changing Codex files.
- SQLite integrity returned `ok`; no Fact retained a legacy normalizer version.
- The Sessions Dashboard route returned a rendered `200` response containing the refreshed summary labels.
- Private source counts, paths, and aggregate values remain outside this tracked report.

## Evidence Gaps

- None for the approved runtime behavior.
- Acceptance impact: `not applicable`.

## Findings

- No implementation defect or acceptance blocker remains.
- Unsupported model prices correctly remain `unpriced`; this is explicit catalog coverage, not a failed usage refresh.

## Regression Notes

- Session parsing, attribution, dashboard ranges and breakdowns, source health, Search, Workstreams, runner, and UI contracts passed.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: Attempt 2 is the current Functional acceptance evidence for FEAT-0020.
- `2026-07-18`: later installed ccusage output invalidated this report as current acceptance evidence: LocalBrain's compared Codex tokens were materially higher while most model facts were unpriced and the configured fast tier was not represented. The historical PASS remains evidence only for the implemented Attempt 2 behavior.
