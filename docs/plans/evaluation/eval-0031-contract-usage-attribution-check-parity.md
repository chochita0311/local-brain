# EVAL-0031: Usage Attribution CHECK Parity — Contract

## Metadata

- ID: `eval-0031-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-36`
- Attempt: `1`
- Feature: [feat-0031-usage-attribution-check-parity](../feature/feat-0031-usage-attribution-check-parity.md)
- Spec: [spec-0031-usage-attribution-check-parity](../spec/spec-0031-usage-attribution-check-parity.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Usage Fact compatibility migration
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated only the approved compatible `usage_facts.attribution_basis` three-value CHECK repair, its recovery boundary, exact preservation guarantees, and affected current-truth artifacts.

## Checks And Evidence

- The repair derives replacement DDL from the compatible table and adds only `CHECK(attribution_basis IN ('git_root', 'workspace_path', 'unassigned'))`; it does not substitute fresh timestamp metadata.
- Preflight compares the complete column-name set with a fresh in-memory schema and refuses unknown or missing structure before table replacement.
- File-backed repair creates a non-overwriting sibling backup before normal DDL, validates it with `PRAGMA quick_check`, and retains the recovery point across repeated startup.
- The transactional gate compares pre/post `PRAGMA table_info`, row count, Fact ID coverage, and both directions of full-row `EXCEPT` before replacing the source table; foreign keys and three Usage indexes are verified before release.
- Null or unknown attribution values fail closed without coercion, recalculation, reattribution, or original-table mutation.
- Data Model owners, privacy/development contracts, deterministic presentation manifest, and the 329-object audit ledger are current at `keep 268`, `change 3`, `remove 1`, `defer 57`.

## Evidence Gaps

- None. The configured local database was already compliant, so no unnecessary live rebuild or backup was performed; file-backed migration behavior is covered by a synthetic database without recording private values.

## Findings

- None.

## Regression Notes

- Presentation, audit, Data Model, full repository, diff-whitespace, and privacy checks passed.

## Route

- Next action: `pass`.
