# FEAT-0034: Usage Record Canonical Terminology

## Metadata

- ID: `feat-0034`
- Status: `passed`
- Type: `foundation`
- Surface: `fullstack`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0004-session-usage-and-cost-dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md)
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Goal

- Make `Usage Record` the single current product and engineering term by renaming the persisted entity, parser type, producer/consumer APIs, read-model keys, tests, and owner documentation without changing any usage value or behavior.

## Acceptance Contract

- Fresh databases define `usage_records`; upgraded databases rename an existing `usage_facts` table in place and preserve every column, row, ID, constraint, relation, and value.
- Current code uses `ParsedUsageRecord`, `usage_records`, `usage_record_id`, and explicit record-count names; legacy Fact names remain only inside bounded compatibility detection or historical artifacts.
- Dashboard values, scopes, prices, coverage, attribution, repair, and visible `usage record(s)` copy remain identical.
- Migration is idempotent and fails closed if both legacy and canonical tables exist.
- Schema presentation, Data Model owner docs, audit decisions, architecture, Product glossary, README, PRD continuity, and tests describe `Usage Record` as current truth.

## Scope Boundary

- In:
  - table and explicit index rename through a compatible startup migration
  - parser dataclass, Parsed Session collection, producer/storage/reconciliation names
  - query aliases and aggregate count keys
  - current owner docs, generated Schema presentation, cleanup audit, tests, and Dashboard regression evidence
- Out:
  - changing row shape, source identity, token normalization, pricing, immutable attribution, eligibility, repair rules, or UI layout
  - rewriting historical Feature/Run/Evaluation prose whose purpose is to record the former contract
  - changing `source_record_id`, which remains the upstream provider record identity
  - changing `maintenance_runs` behavior

## Surface Lanes

- Persistence and ingestion lane: schema, compatible rename, parser types, storage/reconciliation.
- Query and presentation lane: SQL consumers, explicit count keys, unchanged visible Dashboard output.
- Documentation and generated lane: Data Model owner filename/content, deterministic manifest, audit ledger, Product/Architecture/PRD continuity.

## Required Evaluators

- `contract`: canonical naming completeness, fail-closed/idempotent migration, exact row/schema preservation, generated-source parity.
- `functional`: ingestion, repair, pricing, Dashboard, runtime upgrade, full regressions, and privacy.

## Dependencies

- FEAT-0033 is `passed` and established the human-facing `usage record(s)` term.
- The human owner approved complete internal terminology unification on `2026-07-19`.

## Pass Or Fail Checks

- Pass if a legacy fixture and the actual local database contain only `usage_records` afterward with identical row values and valid integrity checks.
- Pass if fresh schema and all current code/tests use canonical Record terminology, except explicitly labeled legacy compatibility checks.
- Pass if Dashboard rendering and all existing usage calculations are unchanged.
- Fail on coexistence without refusal, row copy/rebuild drift, stale current owner docs, or any metric change.

## Harness Trace

- Active spec doc: [spec-0034-usage-record-canonical-terminology](../spec/spec-0034-usage-record-canonical-terminology.md)
- Active run: [run-20260719-39-usage-record-canonical-terminology](../run/run-20260719-39-usage-record-canonical-terminology.md)
- Execution profile: `foundation-contract`
- Latest evaluator reports: [contract](../evaluation/eval-0034-contract-usage-record-canonical-terminology.md), [functional](../evaluation/eval-0034-functional-usage-record-canonical-terminology.md)

## Continuity Notes

- `2026-07-19`: approved directly from the owner request to avoid a permanent UI/internal vocabulary split after FEAT-0033.
- `2026-07-19`: passed after exact synthetic and actual-runtime table-name migration evidence, canonical code/docs/generated artifacts, 126 repository tests, isolated HTTP Dashboard rendering, and privacy verification.
