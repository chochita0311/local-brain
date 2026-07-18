# EVAL-0020: Usage And Cost Fact Contract — Functional Attempt 4

## Metadata

- ID: `eval-0020-functional-attempt-4`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-27`
- Attempt: `4`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: schema migration → calculator → source repair → dashboard read model
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Fresh and compatible schema behavior, request-level tier calculation, Codex source-version repair, repeated synchronization, fixed-boundary reference comparison, database integrity, and dashboard consumption.

## Checks

- Exercised fresh snapshot seeding and compatible migration of every optional threshold and above-threshold rate column.
- Exercised base pricing at the exact threshold, long-context pricing above it, and a later lower-context Fact in the same Session.
- Exercised missing component and rate states without converting unavailable pricing into zero.
- Ran the full automated regression suite, Python compilation, and diff validation.
- Created a private online SQLite backup before repair, synchronized all Claude and Codex sources, repeated synchronization against active files, and checked source-version and Fact convergence.
- Compared LocalBrain and installed offline ccusage monthly reports over the same completed local-date boundary.
- Checked SQLite integrity and rendered the cumulative Codex cost dashboard from the repaired database.

## Evidence

- All 82 automated tests passed.
- The private repair and repeat synchronization completed without source failures; no legacy Codex Fact, stale Codex source version, wrong tiered snapshot, or wrong calculator version remained.
- Fixed-boundary Codex input, output, reasoning, cache-read, total tokens, and monthly estimated cost matched the installed report exactly.
- SQLite integrity returned `ok`.
- The Sessions Dashboard route rendered successfully from the refreshed database with the expected cumulative Codex cost state.

## Evidence Gaps

- No new visual or interaction behavior entered Attempt 4, so a new viewport capture is not required for this foundation-only correction.
- PRD-0004 retains its separate combined responsive viewport-evidence backlog item.
- Acceptance impact: `not applicable`.

## Findings

- No implementation defect or acceptance blocker remains.
- An actively running Session can append events after a completed-boundary comparison; ordinary incremental synchronization remains the correct convergence mechanism.

## Regression Notes

- Session parsing and attribution, dashboard ranges and breakdowns, scope-switch scroll continuity, projections, source health, Search, Workstreams, Task Runner, and UI contracts passed.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: Attempt 4 replaces Attempt 3 as the current FEAT-0020 Functional price-contract acceptance evidence.
