# EVAL-0035: Maintenance Session Usage Bridge — Functional

> Historical evidence only: human review later invalidated the stream-backed producer assumption. FEAT-0036/RUN-41 supersede that producer contract while retaining the schema-constraint evidence.

## Metadata

- ID: `eval-0035-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-40`
- Attempt: `1`
- Feature: [feat-0035-maintenance-session-usage-bridge](../feature/feat-0035-maintenance-session-usage-bridge.md)
- Spec: [spec-0035-maintenance-session-usage-bridge](../spec/spec-0035-maintenance-session-usage-bridge.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Task Runner lifecycle, ingestion preservation, Usage Dashboard regression, and runtime upgrade
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated Runner preparation and every terminal/recovery path, stream normalization and reconciliation, manual-marker cardinality, work-consumer exclusion, actual database migration, and repository-wide regression behavior.

## Checks And Evidence

- Synthetic assistant usage produced one priced Usage Record and ignored the larger result aggregate, proving no double count. Repeated reconciliation remained one record.
- Result-level per-model usage backfilled a historical completed Run. Completed, failed, cancelled, and interrupted paths retained observed usage; missing and malformed streams produced no Usage Record.
- A registered marker cannot link two Sessions to one Run. An unregistered marker remains classified as maintenance but receives no orphan physical link.
- Runner-owned Sessions and Usage Records survive ordinary source cleanup and Usage contract repair. They create no Activity Events or FTS rows and do not enter Runner retrieval candidates.
- Dashboard regression evidence includes direct Maintenance tokens and estimated cost while returning zero primary-work Sessions for a maintenance-only fixture.
- The complete Python suite passed 139 tests. Compilation, nine Mermaid diagrams, Data Model parity, generated Schema presentation, the cleanup ledger, Mermaid assets, repository privacy across 397 candidate files, and diff whitespace checks passed.
- Actual startup and a second idempotency startup left 173 Sessions, two unique Run links, 11,734 Usage Records, zero FK errors, and `quick_check=ok`; the migration backup digest was unchanged on the second startup.

## Evidence Gaps

- The two historical runtime streams were no longer present, so their old token usage cannot be recovered. Future Runs synchronize while the stream exists at terminal finalization; missing historical evidence remains explicit rather than estimated.

## Findings

- None.

## Regression Notes

- No visible layout, Session-list eligibility, Workstream candidate set, activity/search content, existing Usage Record, price, or attribution value changed.

## Route

- Next action: `pass` and request human owner acceptance.
