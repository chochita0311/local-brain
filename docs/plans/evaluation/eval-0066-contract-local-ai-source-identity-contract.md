# EVAL-0066: Local AI Source Identity Contract — Contract

## Metadata

- ID: `eval-0066-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260802-71`
- Attempt: `1`
- Feature: [feat-0066-local-ai-source-identity-contract](../feature/feat-0066-local-ai-source-identity-contract.md)
- Spec: [spec-0066-local-ai-source-identity-contract](../spec/spec-0066-local-ai-source-identity-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: Source registry identity and provider semantics
- Evidence Coverage: `complete`
- Created: `2026-08-02`

## Scope

- Evaluated the stable source-key/provider-kind split, compatible migration,
  producer and consumer ownership, and generated Data Model contracts.

## Checks

- Fresh `sources` DDL retains unique `kind` as the stable source key and adds a
  required, bounded `provider_kind` adapter identity.
- Compatible startup creates a non-overwriting verified database backup before
  rebuilding a legacy Source table and preserves exact Source IDs, children,
  pins, uniqueness, and foreign keys.
- Repeat startup is idempotent.
- Source upsert refuses provider mutation under an occupied source key before
  changing its display label or root.
- Provider-specific scanning, Usage exclusion, stale-contract repair, Claude
  parent fallback, and native Subsession behavior consume provider kind.
- Provenance, filtering, Session ownership, source breakdown, and search
  projection continue to consume stable source key.
- The same native external Session ID coexists under `codex` and
  `codex-company`, both using provider kind `codex`.
- Data Model, value dictionary, Schema presentation, and cleanup audit are
  current at 389 columns and 528 audited objects.

## Evidence

- Targeted identity and migration tests: 6 passed.
- Generated-contract and activity tests: 28 passed.
- Full repository suite: 297 tests passed in 2.042 seconds.
- Privacy check: passed for 662 candidate files.
- `git diff --check`: passed.

## Evidence Gaps

- The private runtime database was not opened or migrated during evaluation.
  Synthetic file-backed migration tests cover the exact backup and retention
  contract without exposing personal data.

## Findings

- None.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-08-02`: attempt 1 passed with stable identity, provider dispatch,
  descendant preservation, generated-contract, full-suite, and privacy evidence.
