# EVAL-0034: Usage Record Canonical Terminology — Contract

## Metadata

- ID: `eval-0034-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-39`
- Attempt: `1`
- Feature: [feat-0034-usage-record-canonical-terminology](../feature/feat-0034-usage-record-canonical-terminology.md)
- Spec: [spec-0034-usage-record-canonical-terminology](../spec/spec-0034-usage-record-canonical-terminology.md)
- Execution Profile: `foundation-contract`
- Surface Lane: persistence and ingestion → query and presentation → docs and generated artifacts
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated the approved one-way Usage Fact → Usage Record terminology migration and exact preservation boundary. No Usage semantics or Dashboard layout change was accepted.

## Checks And Evidence

- Fresh DDL defines only `usage_records` and its three canonical explicit indexes.
- Compatible startup detects the legacy name before fresh DDL, refuses legacy/canonical coexistence, renames in place, replaces only explicit legacy index names, and is idempotent.
- Synthetic legacy migration preserved ordered rows, IDs, column metadata, constraints, attribution CHECK behavior, and foreign-key validity; combined legacy-name plus attribution-CHECK repair also passed through the existing backup precondition.
- Current parser, storage, repair, query, count-key, Dashboard template, tests, Data Model owner, Architecture, Product, PRD continuity, generated Schema presentation, and cleanup audit use canonical Record terminology.
- Legacy Fact identifiers remain only where compatibility detection, migration fixtures, explicit name mappings, or historical artifacts require them.
- Schema presentation and the 328-object cleanup ledger are deterministic and current at `keep 269`, `change 2`, `remove 0`, `defer 57`.

## Evidence Gaps

- None. The unavailable in-app browser connector was not required to assess a foundation-only naming contract; the unchanged route was covered by template/UI contracts, the prior FEAT-0033 rendered evidence, and a fresh local HTTP render.

## Findings

- None.

## Regression Notes

- Token values, price snapshots, estimated cost, source identity, Project attribution, eligibility, repair semantics, visible copy, and responsive styles are unchanged.

## Route

- Next action: `pass`.
