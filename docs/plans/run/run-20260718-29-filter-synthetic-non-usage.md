# RUN-20260718-29: Filter Synthetic Non-Usage

## Metadata

- ID: `run-20260718-29`
- Status: `passed`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Active Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Attempt: `3`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Keep Claude `<synthetic>` assistant and API-error evidence stored while preventing it from appearing as usage or price coverage in Sessions Dashboard.

## Selected Loop

- Surface lanes: dashboard selected-Fact query → summary/history/breakdown consumers → evidence and owner docs.
- Storage invariant: no parser, Usage Fact, Activity Event, source record, or migration change.
- Current phase: complete.

## Current Artifacts

- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Contract evaluation: [eval-0022-contract-filter-synthetic-non-usage-attempt-3](../evaluation/eval-0022-contract-filter-synthetic-non-usage-attempt-3.md)
- Functional evaluation: [eval-0022-functional-filter-synthetic-non-usage-attempt-3](../evaluation/eval-0022-functional-filter-synthetic-non-usage-attempt-3.md)
- Fix log: [fix-0027-filter-synthetic-non-usage](../fix/fix-0027-filter-synthetic-non-usage.md)

## Attempts

- Attempt 3:
  - status: passed
  - outcome: pseudo-model records remain stored but every dashboard usage consumer excludes them
  - notes: real Haiku subsession usage remains included and priced

## Post-Contract Regression Check

- Needed: yes.
- Result: PASS; 84 tests and a private read-only runtime query passed.
- Notes: the runtime Model breakdown omits `<synthetic>` and retains the fully priced Haiku group.

## Human Review Outcome

- Decision: DB and Session activity retain non-usage evidence; the usage and cost surface shows only real model usage.
- Returned layer if any: FEAT-0022 and SPEC-0022 selected-Fact eligibility.

## Continuity Notes

- `2026-07-18`: completed as a consumer-only correction with no backfill, migration, or database write.
