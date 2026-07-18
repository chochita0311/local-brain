# RUN-20260718-27: Long-Context Cost Contract Attempt 4

## Metadata

- ID: `run-20260718-27`
- Status: `passed`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Attempt: `4`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Replace the flat Codex fast-price limitation with a reproducible per-fact long-context tier that matches the frozen ccusage 20.0.17 request boundary while retaining trend-estimate semantics and runtime independence.

## Selected Loop

- Feature type: foundation
- Surface lanes: immutable tier schema → calculator v2 → Codex corrective snapshot → transactional source repair → dashboard regression
- Required evaluators: Contract and Functional
- Current phase: complete

## Contract Surfaces

- `usage_model_prices` tier fields, calculator boundary and component ownership, Codex producer snapshot, normalizer version, corrective repair, Project snapshot preservation, aggregate consumers, and disclosure wording.

## Invocation Context

- Golden sources: human-approved request-tier decision, local JSONL component evidence, installed ccusage 20.0.17 fast report, frozen model thresholds and rates, approved PRD-0004 and SPEC-0020.
- Relevant policies: Architecture, Product Model, Privacy And Data Handling, foundation-contract profile.
- Optional skills or tools expected: workflow-context-sync for source reconciliation; ccusage remains an offline validation reference and is not a runtime dependency.

## Current Artifacts

- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Contract evaluation: [eval-0020-contract-attempt-4](../evaluation/eval-0020-contract-usage-and-cost-fact-contract-attempt-4.md)
- Functional evaluation: [eval-0020-functional-attempt-4](../evaluation/eval-0020-functional-usage-and-cost-fact-contract-attempt-4.md)
- Fix log: [fix-0025-long-context-cost-contract-attempt-4](../fix/fix-0025-long-context-cost-contract-attempt-4.md)

## Current Route

- Next role: human review or ordinary incremental synchronization
- Current blocker classification: none
- In-run route: implement → boundary tests → full regression → back up private DB → version repair → same-boundary cost comparison → integrity and route checks
- Post-run recommendation for human review: accept the request-tier cost baseline and use ordinary refresh for newly appended active-session events

## Attempts

- Attempt 4:
  - status: passed
  - outcome: immutable request-tier snapshot, calculator v2, and private corrective repair completed
  - notes: a fixed completed local-date boundary matched installed offline ccusage token dimensions and monthly estimated cost exactly

## Post-Contract Regression Check

- Needed: yes
- Result: PASS; 82 tests, compilation, diff validation, private repair, repeat synchronization, fixed-boundary reference parity, SQLite integrity, and dashboard rendering passed.
- Notes: token totals, source repair, frozen Project attribution, Claude pricing, dashboard aggregation, scroll continuity, and projection remain stable.

## Human Review Outcome

- Decision: approved request-level long-context contract and implementation
- Returned layer if any: SPEC-0020 corrected and approved
- Follow-up run: this run

## Continuity Notes

- `2026-07-18`: initialized after human approval to align LocalBrain's canonical trend estimate with the ccusage request-tier boundary.
- `2026-07-18`: completed after a private database backup, source-wide version repair, repeat incremental synchronization, exact fixed-boundary ccusage token and cost comparison, integrity check, rendered route check, and complete regression suite.
