# EVAL-0068: Multi-Source Session Synchronization And Health — Contract

## Metadata

- ID: `eval-0068-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-73`
- Attempt: `1`
- Feature: [feat-0068-multi-source-session-synchronization-and-health](../feature/feat-0068-multi-source-session-synchronization-and-health.md)
- Spec: [spec-0068-multi-source-session-synchronization-and-health](../spec/spec-0068-multi-source-session-synchronization-and-health.md)
- Execution Profile: `fullstack-product`
- Surface Lane: data/backend, API/integration, and durable owner contracts
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Evaluated source-ordered dispatch, identity ownership, transaction and deletion
  boundaries, persistent health, report vocabulary, and producer/consumer parity.

## Checks

- One Session action dispatches the ordered Claude, personal Codex, and Codex
  Company registrations independently; both Codex entries reuse the same parser
  and Usage contract.
- Source IDs, source-file sets, Session uniqueness, parent reconciliation, search
  projection, Activity IDs, Usage IDs, and stale deletion are source scoped.
- The same native Codex Session ID produces independent personal/company
  Sessions, Activity Events, Usage Records, and pins.
- Ready sources use independent transactions. Unexpected source failure rolls
  back only that source; missing roots and malformed configuration never invoke
  stale deletion and retain existing descendants.
- Persistent health distinguishes completed, empty, unavailable, configuration
  error, and scan failure. Latest failure does not advance latest success.
- The report exposes exact bounded aggregate and per-source keys; no raw parser
  exception or Session content is returned or stored.
- Fresh DDL bounds status/error values. Compatible startup adds nullable health
  columns idempotently without changing Source IDs or children.

## Evidence

- Focused synchronization/schema/UI contracts: 65 tests passed.
- Full repository suite: 315 tests passed in 2.245 seconds.
- Privacy check: passed for 672 candidate files.
- Generated schema presentation, cleanup ledger, and nine value dictionaries are
  current.
- `git diff --check`: passed.

## Evidence Gaps

- Synthetic temporary runtimes replace the owner's real source homes. This is
  deliberate and covers identity, collision, retention, and failure behavior
  without reading machine-specific content.

## Findings

- None.

## Route

- Next action: `pass`.
