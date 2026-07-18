# EVAL-0020: Usage And Cost Fact Contract — Contract Attempt 2

## Metadata

- ID: `eval-0020-contract-attempt-2`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-25`
- Attempt: `2`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: source normalization → source-level version repair → persistence
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Corrected Claude and Codex usage producers, normalizer-version ownership, source-wide replacement boundary, immutable price and Project snapshots, and rebuild idempotency.

## Checks

- Compared cumulative Codex component ownership and zero-delta behavior with the normalized Fact contract.
- Verified the bounded Claude cache-create fallback records provenance rather than silently changing semantics.
- Verified source-file and Fact normalizer versions are independent from price-calculator versions.
- Verified one source-level savepoint owns exact-set deletion only after every current source file parses and persists successfully.
- Verified files sharing one Session identity contribute a union rather than deleting one another's facts.
- Verified replacement identities inherit historical price and Project snapshots and that failure preserves the prior source-wide set.
- Reconciled Feature, Spec, Product, Architecture, README, Run, Fix, and owner-plan wording.

## Evidence

- Synthetic multi-delta, nested cache, shared-Session-file, obsolete-identity, failure-rollback, freshness, and repeated-scan tests passed.
- Fresh and compatible SQLite schema paths retain explicit normalizer versions and immutable price references.
- The complete repository suite passed with 76 tests.
- Private live values were used only for local validation and were not copied into tracked evidence.

## Evidence Gaps

- None for the approved foundation contract.
- Acceptance impact: `not applicable`.

## Contract Evidence

- Producer surfaces: `ingest/claude.py`, `ingest/codex.py`, and `ParsedUsageFact`.
- Consumer surfaces: scanner repair, `usage_facts`, and downstream dashboard queries.
- Checked artifacts: schema, compatible migration, source freshness, exact-set helper, snapshot preservation, Product Model, Project Architecture, README, Feature, and Spec.
- Stale-assumption check: no latest-per-turn or per-Session deletion assumption remains in current owner documents or implementation.

## Findings

- No remaining contract defect, spec gap, or planning gap in FEAT-0020 scope.

## Regression Notes

- Session identity, hierarchy, Activity Events, Search, workflow statistics, Project snapshots, and pricing consumers remain unchanged outside the bounded repair lane.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: Attempt 2 replaces the invalidated Attempt 1 acceptance evidence.
- `2026-07-18`: later official ccusage adapter evidence invalidated this report as current acceptance evidence because the evaluated cumulative-only producer differs from the `last_token_usage`-first source contract. The historical PASS records the checks performed against Attempt 2, not current FEAT-0020 acceptance.
