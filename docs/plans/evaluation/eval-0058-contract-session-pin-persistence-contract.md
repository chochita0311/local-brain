# EVAL-0058: Session Pin Persistence Contract — Contract

## Metadata

- ID: `eval-0058-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260724-61`
- Attempt: `1`
- Feature: [feat-0058-session-pin-persistence-contract](../feature/feat-0058-session-pin-persistence-contract.md)
- Spec: [spec-0058-session-pin-persistence-contract](../spec/spec-0058-session-pin-persistence-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: schema identity, ownership, eligibility, migration, and recovery
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Checks And Evidence

- Fresh and compatible databases expose exactly `session_id` and `pinned_at`; no status or soft-delete field exists.
- `session_id` is both the primary key and Session FK with `ON DELETE CASCADE`.
- The pin table is user-owned and non-rebuildable, while `sessions` remains source-derived.
- Only `work` plus `primary` Sessions are eligible. Missing, Maintenance, and Subsession inputs have distinct bounded error codes.
- Repeated pin cannot create a duplicate and preserves the first current pin time.
- Unpin deletes only the pin row; re-pin creates a new current time.
- Stable Session update preserves the pin. Explicit Session deletion removes it.
- Fresh DDL and compatible startup converge without changing retained Session rows.
- Data Model, Schema Presentation, cleanup audit, and value-dictionary exclusion ownership agree.

## Evidence Gaps

- None for persistence. UI actions and HTTP response behavior belong to FEAT-0059.

## Findings

- None.

## Route

- Next action: `pass`.
