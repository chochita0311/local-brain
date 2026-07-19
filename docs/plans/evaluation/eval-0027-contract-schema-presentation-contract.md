# EVAL-0027: Schema Presentation Contract — Contract

## Metadata

- ID: `eval-0027-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260718-32`
- Attempt: `1`
- Feature: [feat-0027-schema-presentation-contract](../feature/feat-0027-schema-presentation-contract.md)
- Spec: [spec-0027-schema-presentation-contract](../spec/spec-0027-schema-presentation-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: value shape, source ownership, generation, and package consumer boundary
- Evidence Coverage: `complete`
- Created: `2026-07-18`

## Scope

- Active feature: deterministic, packageable, schema-only v1 presentation contract for later read-only Schema consumers.
- Active spec: SPEC-0027 attempt 1.
- Evaluated build or commit: current unstaged FEAT-0027 implementation, policy, generated manifest, tests, and wheel in the shared workspace.

## Checks

- Reviewed the exact `localbrain.schema-presentation.v1` field, source-role, ordering, derived-output, change, and failure rules in the durable Schema Presentation policy.
- Verified executable structure remains owned by `schema.sql` and `db.py`, semantic truth remains in the Data Model owner documents, and the JSON is marked derived and non-executable.
- Built effective structure only in SQLite `:memory:` through fresh DDL and the actual compatible structure/index path with data migrations disabled.
- Verified eight ordered subjects own exactly 20 ordinary tables and one FTS5 object, including 245 columns, 20 explicit indexes, 19 physical relations, and 24 application relations.
- Verified physical facts come from SQLite introspection, application relations come from dotted global Mermaid edges, and table semantics and all nine Mermaid definitions are transformed from their approved Markdown owners.
- Verified every table has columns, keys, constraints, indexes, physical relations, purpose/authority, producers, consumers, lifecycle, rebuildability, deletion effect, recovery, and DDL ownership.
- Reviewed the bounded loader for version, baseline counts, source records, global view, subject shape, table shape, one-owner parity, relationships, and missing or invalid package states.
- Verified no route, template, navigation, CSS, runtime-row query, cleanup decision, or executable DDL source was added by this Feature.

## Evidence

- `schema.sql` SHA-256: `b19f3642c9b89cf01f65d39d6dc5ad716b22c187f22454bfe0ee38b06766377b`.
- `db.py` SHA-256: `fe6e70719632ee859ba2c6a95ef2bbe408a9a2296d70d23e160269df97126ac3`; the only behavior delta is an explicit structural-only invocation option while the runtime default remains data-inclusive.
- Generated manifest SHA-256: `740d156a13f43b7d7ebdfc2b9b5b1cad3f3df9f00e91d081fc5d2cc521647c3b`, 155,239 bytes, without a generation timestamp.
- Automated tests prove exact owner order, current counts, required semantics, exact Mermaid transformation, byte determinism, in-memory-only connection use, disabled Context/data migration, stale/missing failure, loader shape rejection, and repository-relative provenance.

## Evidence Gaps

- None within the Feature contract.

## Contract Evidence

- Producer surfaces: fresh DDL, compatible structural/index migration path, Data Model entry, and eight subject owner documents.
- Consumer surfaces: packaged JSON and `load_schema_presentation()`; FEAT-0028 remains outside this Run.
- Generated artifacts and schemas checked: v1 JSON, baseline digests, nine Mermaid strings, subject/table catalogs, relation arrays, wheel inventory, and loader validation.
- Stale-assumption check: data-model parity, source hashes, local Mermaid parsing, complete extraction, deterministic regenerated-byte comparison, and installed-package loading all passed.

## Findings

- No duplicate executable schema, hand-maintained application ERD, incomplete owner, runtime-data fallback, or unbounded loader error remains.

## Regression Notes

- Existing startup callers retain `include_data_migrations=True` by default. The schema-only generator opts out explicitly and the full application suite passes.

## Route

- Next action: `pass`.

## Continuity Notes

- `2026-07-18`: passed attempt 1 with complete deterministic v1 ownership, schema/semantic parity, bounded loading, and installed-package evidence.
