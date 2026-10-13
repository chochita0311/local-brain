# SPEC-0119: Local Natural Search Engine

## Metadata

- ID: `spec-0119`
- Status: `approved`
- Run: [RUN-156](../run/run-20261012-156-local-natural-search-engine.md)
- Attempt: 1
- Parent Feature: [FEAT-0119](../feature/feat-0119-local-natural-search-engine.md)
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Execution Profile: `backend-product`
- Surface: backend/data
- Required Evaluators: contract, functional
- Created: `2026-10-12`

## Source Set And Goal

Implement the [approved search contracts](../../policies/project/natural-language-search.md). FEAT-0115–0118 passed their contract review. Runtime modules live in `src/localbrain/natural_search/`; tests use isolated synthetic databases. Existing FTS and affinity vectors are not migrated.

This records the original engine contract. Its RRF ordering was superseded by
[SPEC-0122](spec-0122-natural-search-ranking-precision.md), then the current
original/focused-view ordering in [SPEC-0123](spec-0123-general-work-search.md).
The linked search policy owns the current default; the historical rules below
remain evidence of this implementation stage.

## Data And State Contract

- A read-only snapshot of normalized eligible source bodies is the input. Parent hash includes body/locator/title metadata. Current source membership and revision are checked before result delivery.
- Molecule splitter uses Qwen token offsets and original character spans, structural breakpoints, explicit context budget and no body truncation. Each original span has parent/event/line provenance.
- The encoder loads verified local pinned Qwen assets through the existing installation owner. Strict per-input lengths prevent the old mean-of-windows behavior. Unit tests may inject a deterministic encoder; production never substitutes it.
- Store `<data>/natural-search.json` activation/settings and `<cache>/natural-search/{index.sqlite3,building.sqlite3,writer.lock,status.json}`. Databases identify owner, source binding and complete profile. One process writer lock; staging retains compatible vectors for resume. Current compatible vectors can be reused. Publish only a complete generation with atomic replace; never mutate the reader generation.
- Default target512/dimension512/overlap0 and initial cosine cutoff0.7 are comparison settings. FEAT-0121 subsequently selected cutoff0.45 after measuring both; the [search owner](../../policies/project/natural-language-search.md) owns the current default. Binary vectors are normalized float32. Index tables own parent metadata, fragments and FTS token rows, deduplicated vectors and generation metadata. This is private derived state, outside the primary schema.
- Foreground retrieval reads one generation, exact numpy cosine over stored vectors and bounded lexical candidates, then groups by parent. Hybrid uses RRF; cutoff is dense cosine, not RRF. Exact Latin identifiers have an explicit lexical admission reason. No hidden corpus limit.
- Query conditions follow the owner calendar/type/literal-exclusion contract; ambiguous exclusions are displayed as unapplied. Parent counts and partial coverage remain distinct from candidate/page limits.
- Worker starts only after durable activation. A running app polls normalized DB/WAL changes after Sync and coalesces refreshes. Cache loss is recoverable. CLI preparation is explicit; CLI scan invokes refresh when enabled. Cross-process writers are serialized; background encoding yields to waiting foreground queries.

## Affected Surfaces

New natural_search modules, CLI entry dispatch, application lifecycle, storage accounting, tests and installation/retrieval owner documentation.

## Failure And Recovery

Missing runtime/assets, incompatible/corrupt index, busy writer, interrupted build, source removed/changed and no eligible data have bounded error/state codes. Exceptions never print source bodies or credentials. Query logs are not persisted by the search engine. No network fallback or unrequested download.

## Acceptance Mapping

1. Full source admission/provenance → source/splitter unit fixtures, including long tails and maintenance/child/disabled exclusions.
2. Rebuild/reuse/recovery → two prepares, changed input, interrupted prepare, generation atomicity and current-source checks.
3. Query and score contract → deterministic vector/FTS fixtures, explicit/ambiguous filters, parent deduplication, cutoff, empty vs unavailable.
4. Local-only resources → read-only source DB, bounded private roots, installed-model contract, no network inference.
5. Actual encoder behavior → separate local-model comparison, not inferred from fake-encoder tests.

## Open Blockers

None for the implementation contract. Empirical default selection and resource observations are reported by FEAT-0121.
