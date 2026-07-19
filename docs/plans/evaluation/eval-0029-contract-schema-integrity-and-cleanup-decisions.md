# EVAL-0029: Schema Integrity And Cleanup Decisions — Contract

## Metadata

- ID: `eval-0029-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-34`
- Attempt: `1`
- Feature: [feat-0029-schema-integrity-and-cleanup-decisions](../feature/feat-0029-schema-integrity-and-cleanup-decisions.md)
- Spec: [spec-0029-schema-integrity-and-cleanup-decisions](../spec/spec-0029-schema-integrity-and-cleanup-decisions.md)
- Execution Profile: `foundation-contract`
- Surface Lane: object/consumer evidence, decision classification, migration proposal
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: planning-only exhaustive schema integrity and cleanup audit.
- Active spec: SPEC-0029 attempt 1.
- Evaluated artifact set: decision source, generated object ledger, human review summary, audit checker/tests, corrected current-truth docs, regenerated presentation manifest, backlog anchors, and current unstaged PRD-0003 worktree.

## Contract Surface Results

| Surface | Result | Evidence |
| --- | --- | --- |
| Effective inventory | PASS | Manifest digest is pinned; resolved counts are exactly 21 tables, 245 columns, 20 named indexes, 19 physical relations, and 24 application relations. |
| One-decision invariant | PASS | 329 unique kind/object identities resolve exactly once to `keep 259`, `change 9`, `remove 4`, or `defer 57`; unknown overrides, count drift, missing tables, duplicate JSON keys, and stale ledger bytes fail. |
| Evidence trace | PASS | Every table has subject/current-doc ownership, fresh/compatible source, purpose/authority, producers, consumers, lifecycle, rebuildability, deletion, recovery, runtime references, and synthetic test references. Every child object links to its table evidence plus an object contract/rationale. |
| Change/remove safety | PASS | All five candidate groups define defect, target contract, affected objects/consumers, dependency, preservation, rollback/recovery, verification, and risk. Every changed/removed current object points to one group. |
| Keep support | PASS | Default keep is applied only to manifest objects with a documented semantic contract and inspected table evidence; table-level keep decisions state distinct authority and consumer need. Current existence alone is not the rationale. |
| Defer routing | PASS | All 57 defers identify one of two blockers and exactly one stable Project Backlog anchor; no unresolved migration is implied. |
| Lifecycle safety | PASS | Source-rebuildable Activity Event cleanup, index-only changes, frozen Usage attribution, non-rebuildable checkpoints/resources, and operational Run history remain in separate preservation boundaries. |
| Drift ownership | PASS | Proven legacy constraint differences are corrected in current-truth docs and derived presentation; cleanup dispositions remain only under `docs/plans/`. |
| Migration gate | PASS | Four ordered candidate boundaries are proposals only. No migration Feature, DDL, data mutation, or owner approval is created by this Run. |
| Privacy/no-runtime change | PASS | No runtime database was opened. Runtime hash comparison changed only derived `schema-presentation.json`; schema, migration, producer, consumer, route, template, JS, and CSS bytes remained unchanged. Repository privacy scan passed. |

## Producer And Consumer Evidence

- Structural producers inspected: `schema.sql`, `_run_compatible_migrations`, all 20 named-index definitions, fresh constraints, compatible additions/backfills, and FTS declaration.
- Semantic producers inspected: Data Model entry and eight subject owners transformed into the v1 presentation manifest.
- Runtime producers inspected: ingestion/scanner and parsers, Usage normalization/repair, Context lifecycle, Workstream/Thread/checkpoint/resource operations, Suggestion review, Task Runner, and search projection maintenance.
- Consumers inspected: query/read models, activity attribution, retrieval, usage dashboards, Workstream/Thread/checkpoint views, Runner list/detail/reconciliation, Schema loader/explorer, and 108 synthetic tests.
- Protected adjacent contracts: PRD-0002 Session/workspace ownership and PRD-0004 frozen Usage Fact, price, cost, and Project attribution remain unchanged.

## Generated And Synthetic Evidence

- `scripts/check-schema-cleanup-audit.py --check` passed with 329 current decisions and rejects missing table coverage, incorrect expected counts, and incomplete preservation fields in negative fixtures.
- Synthetic PRAGMA inspection proved the three remove-candidate indexes have UNIQUE autoindexes with the required leading columns.
- Synthetic EXPLAIN inspection selected each proposed checkpoint/source/workspace index for its named query prefix.
- A synthetic legacy schema upgraded through the actual structural migration path proved the missing Usage attribution CHECK, nullable/no-default compatible timestamp additions, and missing Maintenance Workstream FK.
- Data Model parity passed at 20 ordinary tables, one FTS5 object, 19 physical foreign keys, 20 explicit indexes, and eight owners.
- Nine Mermaid definitions parsed through the pinned local bundle; Schema presentation regeneration/check passed.
- Full test suite passed 108 of 108 tests. The existing Starlette TemplateResponse deprecation warning remains unrelated and non-blocking.
- Post-correction browser regression passed at `1440`, `920`, `700`, and exact `320`: all nine subject entries, long Usage table detail, Mermaid rendering, global contained scroll, URL/history/focus, rapid selection, warm cache, blocked adapter, no-script fallback, invalid-state non-reflection, and document-width containment remained valid. Evidence is local-only under `/tmp/localbrain-feat29-browser-qa-final-evidence`.
- Final wheel SHA-256 is `31813e4c81e6aeb2d60d842592e8c714b21c04e08780547a5db6c820ae8a6ca3`; its packaged presentation manifest SHA-256 is `0f85df5c7124c17361e435408f8fb8fa156573d0926bceb77aafa5583d19d902` and required Schema assets remain present.
- Repository privacy scan passed 364 candidate files; `git diff --check` passed.

## Stale-Assumption Check

- Presentation digest and every semantic source digest are current.
- Manifest/object count drift, table decision drift, unknown object overrides, orphan candidate/defer groups, missing backlog anchors, missing test evidence, and generated-ledger staleness are automated failures.
- Simple source search did not establish removal by itself: `activity_events.metadata_json` also has no parser producer, resolves to NULL at the scanner boundary, has no consumer, and belongs to a source-rebuildable table.
- SQLite autoindexes and FTS shadow tables are explicitly scoped as internal consequences and inspected through their application-owned UNIQUE/virtual-table contracts rather than counted as independent migration objects.
- Current code use was not treated as correctness proof: mixed timestamp text, unconstrained state/type values, missing compatible constraints, redundant indexes, and missing query-prefix indexes were still recorded.

## Evidence Gaps And Risk Routing

- Private runtime row conformity, table cardinality, legacy invalid values, and backup recoverability were intentionally not inspected. High-risk candidate groups require synthetic-plus-approved preflight and backup/restore evidence before implementation.
- Representative production performance was not measured. Proposed index additions are low-risk review candidates supported by query-prefix and synthetic EXPLAIN evidence, not a claim of measured user-visible speedup.
- Canonical timestamp and closed-vocabulary targets are unresolved by design and therefore `defer`, not evaluator-invented contracts.
- These gaps do not block the audit contract because they are named dependencies or deferrals and no runtime migration is authorized.

## Findings Classification

- Implementation bugs in FEAT-0029 artifacts: none.
- Spec gaps: none.
- Planning gaps: none.
- Cleanup findings are the Feature's intended outputs, not defects to send to the Fix Agent.

## Route

- Recommended next route: `pass` to human owner review.
- The owner may approve, reject, defer, or regroup each proposed migration boundary.
- Do not create FEAT-0030 or any cleanup migration until that separate decision is explicit.

## Continuity Notes

- `2026-07-18`: Contract evaluation passed with complete object coverage, evidence and safety fields, automated stale checks, synthetic structural evidence, current-truth correction, full regression, packaging, privacy, and an intact owner gate.
