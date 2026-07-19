# EVAL-0032: Activity Event Metadata Removal — Contract

## Metadata

- ID: `eval-0032-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-37`
- Attempt: `1`
- Feature: [feat-0032-activity-event-metadata-removal](../feature/feat-0032-activity-event-metadata-removal.md)
- Spec: [spec-0032-activity-event-metadata-removal](../spec/spec-0032-activity-event-metadata-removal.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Activity Event schema and producer contract
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated only the owner-approved removal of the unused generic Activity Event metadata slot and the affected producer/current-truth boundaries.

## Checks And Evidence

- Fresh `activity_events` has exactly the nine retained normalized fields and keeps its Session cascade and composite UNIQUE boundary.
- `ParsedEvent` and scanner no longer expose or serialize generic metadata; Claude/Codex message and tool-call construction remains unchanged.
- Compatible migration checks the runtime table and refuses any non-null metadata count before `ALTER TABLE`; an absent column is an idempotent no-op.
- A valid legacy fixture retained every remaining column value, deterministic event ID, row count, and FK state exactly.
- Workspace/Session Activity documentation, Data Model hashes, deterministic Schema presentation, and the 328-object cleanup ledger are current at `keep 269`, `change 2`, `remove 0`, `defer 57`.

## Evidence Gaps

- None. Actual runtime verification used count and retained-value digest comparison without placing runtime values in tracked artifacts.

## Findings

- None.

## Regression Notes

- No event type, content, ordering, source provenance, consumer, or Usage behavior changed.

## Route

- Next action: `pass`.
