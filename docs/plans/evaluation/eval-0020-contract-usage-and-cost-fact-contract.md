# EVAL-0020: Usage And Cost Fact Contract

## Metadata

- ID: `eval-0020-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `FAIL`
- Run ID: `run-20260718-20`
- Attempt: `1`
- Feature: [feat-0020-usage-and-cost-fact-contract](../feature/feat-0020-usage-and-cost-fact-contract.md)
- Spec: [spec-0020-usage-and-cost-fact-contract](../spec/spec-0020-usage-and-cost-fact-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: source normalization → immutable pricing → persistence
- Evidence Coverage: `partial`
- Created: `2026-07-18`

## Scope

- Active feature: source-neutral Claude and Codex usage facts and immutable local trend-cost provenance.
- Active spec: SPEC-0020.
- Evaluated build: current working tree for RUN-20260718-20 Attempt 1.

## Checks

- Compared Claude and Codex producer fields with `ParsedUsageFact` and `usage_facts` ownership.
- Checked non-cached input, output, cache-write, cache-read, reasoning-subset, source-total, and normalized-total semantics.
- Checked stable record identity, direct aggregation scope, maintenance and subsession inclusion, and repeat-scan behavior.
- Checked immutable snapshot rows, per-million decimal rates, stored calculator provenance, and the priced, unpriced, partial, and failed states.
- Checked upgraded-database source invalidation so existing Session files are reprocessed once, followed by idempotent startup.
- Checked Product Model and Project Architecture for producer, storage, rebuild, scope, and ccusage ownership parity.

## Evidence

- Synthetic Claude evidence produced non-cached input, output, cache creation, and cache read components and a deterministic Sonnet estimate.
- Synthetic Codex evidence retained the latest `turn_id` observation, subtracted cached input, and did not add reasoning output twice.
- SQLite constraints preserve deterministic identity, direct versus includes-children scope, immutable snapshot references, nonnegative tokens, and numeric-cost/state consistency.
- Historical-snapshot evidence changed an in-progress fact's tokens after a new default snapshot was introduced; the fact retained its original snapshot and original rates.
- A temporary legacy database gained all three usage tables, marked its existing Codex source stale once, seeded one snapshot and three model prices, and remained current on the next startup.
- All 53 repository unit tests, Python compilation with an isolated pycache, diff whitespace, and repository privacy checks passed.

## Evidence Gaps

- Attempt 1 did not cover multiple positive Codex cumulative observations within one turn or one Session identity spanning multiple source files. Private runtime records were not copied into tracked evidence.
- Acceptance impact: `blocking`.

## Contract Evidence

- Producer surfaces: `ingest/claude.py`, `ingest/codex.py`, and `ParsedUsageFact`.
- Consumer surfaces: scanner persistence now; downstream aggregate consumers remain owned by later Features.
- Schemas, payloads, generated artifacts, commands, routes, config, or policy docs checked: `usage_facts`, `usage_price_snapshots`, `usage_model_prices`, `usage.py`, startup migration behavior, Product Model, and Project Architecture.
- Stale-assumption check: existing primary-only Search and workflow-statistics consumers remain unchanged; the broader all-direct-usage scope is isolated to the new fact lane.

## Findings

- Severity: blocking.
- Classification: `spec gap`.
- Description: latest-per-turn identity and Session-scoped replacement were insufficient for cumulative Codex observations and multi-file Session identities.
- Evidence: private post-run aggregate validation and source-identity inspection.
- Fix hint: use cumulative deltas and source-file-union version repair; evaluated in Attempt 2.

## Regression Notes

- Existing parser message/tool output, Session identities, search indexing, source synchronization, maintenance exclusion, subsession browsing, and primary-only statistics passed unchanged.

## Route

- Next action: `spec-review`

## Continuity Notes

- `2026-07-18`: contract evaluation passed with complete synthetic, schema, migration, and policy evidence.
- `2026-07-18`: superseded after private post-run validation exposed a blocking spec gap; see the Attempt 2 contract evaluation.
