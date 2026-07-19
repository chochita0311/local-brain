# EVAL-0026: Data Model Baseline And Subject ERDs — Contract

## Metadata

- ID: `eval-0026-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-31`
- Attempt: `1`
- Feature: [feat-0026-data-model-baseline-and-subject-erds](../feature/feat-0026-data-model-baseline-and-subject-erds.md)
- Spec: [spec-0026-data-model-baseline-and-subject-erds](../spec/spec-0026-data-model-baseline-and-subject-erds.md)
- Execution Profile: `docs-content`
- Surface Lane: effective schema, durable owners, navigation and rendering
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: complete current SQLite baseline, level-zero and subject ERDs, table/column catalogs, relation and lifecycle semantics, navigation, and baseline-delta maintenance.
- Active spec: SPEC-0026 attempt 1.
- Evaluated build or commit: current unstaged FEAT-0026 documents and checks in the shared workspace.

## Checks

- Applied `schema.sql` to in-memory SQLite and compared effective objects, columns, physical foreign keys, and fresh indexes with the eight subject owner markers and catalogs.
- Parsed runtime index declarations in `db.py`, deduplicated repeated fresh declarations, and verified the 20-name effective union and per-table catalog coverage.
- Verified current `schema.sql` and `db.py` hashes against the entry baseline and confirmed no implementation file changed in this Feature.
- Reviewed all 20 ordinary tables and `search_index` for purpose, authority, producer, consumer, lifecycle, deletion, rebuild, recovery, constraints, indexes, and fresh/compatible ownership.
- Reviewed all 19 physical FKs and material application edges, including polymorphic targets, Suggestion targets/origin, maintenance Session identity, frozen workspace snapshot, scan path correlation, and search projection.
- Verified solid physical and dotted application notation in the global and focused ERDs and checked that the text never promotes application identities to SQLite FKs.
- Verified every object has exactly one primary subject owner and all eight documents have one focused ERD and complete column coverage.
- Verified Architecture and the Documentation Map route to the canonical entry without duplicating its complete catalog.
- Verified baseline-then-delta routing covers object, subject, column, constraint, index, relation, lifecycle, migration, and presentation changes.
- Verified no cleanup decision, runtime row, machine value, content sample, credential, or migration change entered the baseline.

## Evidence

- Environments checked: implementation source inspection, in-memory SQLite, static producer/consumer SQL trace, automated owner/catalog checker, local Mermaid parser, and rendered schema-only preview.
- `scripts/check-data-model-docs.py` reported 20 ordinary tables, one FTS5 object, 19 physical FKs, 20 explicit indexes, and eight exact owners.
- All catalog sections include every effective `PRAGMA table_info` column and every owning explicit index.
- `schema.sql` remains at `b19f3642c9b89cf01f65d39d6dc5ad716b22c187f22454bfe0ee38b06766377b`; `db.py` remains at `ceb8d58c7dd5a4edacc933a16a34fbc82609de610f26c7e7ae94056fa360bf51`.

## Evidence Gaps

- None within the Feature contract.

## Contract Evidence

- Producer surfaces: `schema.sql`, `db.py`, scanner, Context, Usage, Workstream, Runner, and search projection modules.
- Consumer surfaces: queries, retrieval, activity, usage queries, Workstream/Runner read models, and application routes described by the owning catalogs.
- Schemas, payloads, generated artifacts, commands, routes, config, or policy docs checked: fresh DDL, compatible columns, 20-index union, subject markers, Markdown links, Mermaid source, Architecture, Documentation Map, and Developer Guide delta rule.
- Stale-assumption check: content hashes, in-memory introspection, column/index tokens, exact subject mapping, and link validation are automated and covered by a unit test.

## Findings

- No unexplained schema drift, duplicate owner, missing catalog field, or cleanup inference remains.

## Regression Notes

- DDL, compatible migrations, producers, consumers, and application behavior were not modified. PRD-0002 Session branch/hierarchy and PRD-0004 Usage Fact/attribution contracts remain explicit.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 with complete schema, semantic ownership, lifecycle, recovery, and stale-reference evidence.
