# EVAL-0021: Activity And Project Attribution Contract Functional

## Metadata

- ID: `eval-0021-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260718-21`
- Attempt: `2`
- Feature: [feat-0021-activity-and-project-attribution-contract](../feature/feat-0021-activity-and-project-attribution-contract.md)
- Spec: [spec-0021-activity-and-project-attribution-contract](../spec/spec-0021-activity-and-project-attribution-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: attribution producer and activity runtime
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: runtime Project snapshot stability and activity calculation states.
- Active spec: SPEC-0021.
- Evaluated build: current working tree after FIX-0021.

## Checks

- Created, removed, and rediscovered synthetic Git state around repeated Session storage.
- Added a path after an unassigned fact already existed.
- Migrated a synthetic legacy usage fact.
- Exercised exact and over-threshold gaps, incomplete Sessions, invalid timestamps, concurrent overlap, range clipping, SQLite event reads, and Asia/Seoul day/week boundaries.

## Evidence

- Existing fact attribution and `attributed_at` remained unchanged through path → Git → path current-state transitions; new facts used the new basis.
- Canonical Git roots and workspace paths no longer diverge through macOS `/var` aliases.
- Exactly 30 minutes stayed in one segment; 30 minutes and one second opened a new segment.
- Incomplete activity stopped at the last event, and an invalid timestamp did not fail other Sessions.
- Two overlapping 20-minute Sessions produced 40 minutes of observed Session span but 30 minutes of estimated active time and one 30-minute longest active segment.
- Asia/Seoul local-day and Monday-week boundaries converted to the expected UTC instants.
- All 60 tests passed.

## Evidence Gaps

- None. Filesystem, database, overlap, and timezone states have deterministic synthetic coverage.

## Findings

- Initial implementation bug: noncanonical Git-root output could split one Project key on macOS. FIX-0021 corrected it.
- No remaining functional blocker.

## Regression Notes

- FEAT-0020 usage and cost behavior and all preexisting suites passed.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-07-18`: Functional re-evaluation passed after one bounded fix loop.
