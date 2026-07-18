# RUN-20260718-26: Usage Contract Repair Attempt 3

## Metadata

- ID: `run-20260718-26`
- Status: `passed`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Attempt: `3`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Replace the invalid cumulative-only Codex facts with direct-event-first facts, resolve auto-review model provenance, attach one immutable current fast-tier trend snapshot, and refresh the private local database safely and idempotently.

## Selected Loop

- Feature type: foundation
- Surface lanes: source normalization → immutable corrective pricing → transactional source repair → dashboard regression
- Required evaluators: Contract and Functional
- Current phase: complete

## Contract Surfaces

- `ParsedUsageFact` producer hints, Codex token-event precedence, cumulative fallback state, raw and normalized model identity, price-snapshot assignment, source-version repair, Project snapshot preservation, and downstream usage queries.

## Invocation Context

- Golden sources: local JSONL evidence, installed ccusage 20.0.17 behavior and output, current local Codex `fast` configuration, approved PRD-0004 and SPEC-0020.
- Relevant policies: Architecture, Product Model, Privacy And Data Handling, foundation-contract profile.
- Optional skills or tools expected: workflow-context-sync for source reconciliation; ccusage remains read-only validation reference and is not a runtime dependency.

## Current Artifacts

- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Contract evaluation: [eval-0020-contract-attempt-3](../evaluation/eval-0020-contract-usage-and-cost-fact-contract-attempt-3.md)
- Functional evaluation: [eval-0020-functional-attempt-3](../evaluation/eval-0020-functional-usage-and-cost-fact-contract-attempt-3.md)
- Fix log: [fix-0024-usage-contract-repair-attempt-3](../fix/fix-0024-usage-contract-repair-attempt-3.md)

## Current Route

- Next role: human review or ordinary incremental synchronization
- Current blocker classification: none
- In-run route: implement → test → back up private DB → version repair → compare → regress
- Post-run recommendation for human review: accept the repaired dashboard baseline; allow ordinary refresh to ingest newly appended active-session events

## Attempts

- Attempt 3:
  - status: passed
  - outcome: direct-event-first Fact repair and private refresh completed without a reset control
  - notes: same-boundary token dimensions matched the installed ccusage report; LocalBrain's flat model-tier trend cost remained intentionally slightly below the report because invoice-level long-context tiering is excluded

## Post-Contract Regression Check

- Needed: yes
- Result: PASS; 80 tests, compilation, privacy, diff validation, route rendering, source-version convergence, repeat synchronization, and SQLite integrity passed.
- Notes: Sessions Dashboard, aggregation filters, scope-switch scroll continuity, projection, source freshness, Project attribution, and repeated synchronization remain stable.

## Human Review Outcome

- Decision: approved direction with the request to refresh implementation and local data
- Returned layer if any: SPEC-0020 corrected and approved
- Follow-up run: this run

## Continuity Notes

- `2026-07-18`: initialized after the human approved direct-event-first Codex repair and a current fast-tier trend estimate.
- `2026-07-18`: completed after a private database backup, source-wide version repair, repeat incremental synchronization, same-boundary ccusage token comparison, integrity check, rendered route check, and complete regression suite.
- `2026-07-18`: superseded as current cost-contract evidence after human review approved request-level long-context pricing. Attempt 3 remains the valid token-normalization baseline; RUN-20260718-27 owns the price-tier correction.
