# Schema Presentation

## Purpose

This contract defines the deterministic, package-owned data consumed by LocalBrain's read-only Schema surfaces. It is a derived presentation of the complete [Data Model](data-model.md), never executable DDL, a migration source, or an authority over runtime rows.

## Source Ownership

- `src/localbrain/schema.sql` owns fresh executable structure.
- `src/localbrain/db.py` owns compatible structure and runtime-only indexes. Generation invokes its real structural path against SQLite `:memory:` with data migrations disabled.
- `docs/policies/project/data-model.md` and its eight subject documents own order, subject ownership, lifecycle/recovery semantics, column explanations, application relations, and Mermaid definitions.
- `scripts/schema_presentation_builder.py` owns transformation and validation only.
- `src/localbrain/schema-presentation.json` is committed derived output and is packaged with LocalBrain.
- `src/localbrain/schema_presentation.py` is the only application loader. Consumers must not parse repository Markdown or introspect a runtime database as fallback.

## V1 Shape

The top-level `schema` is exactly `localbrain.schema-presentation.v1` and `derived` is exactly `true`.

| Field | Contract |
| --- | --- |
| `baseline` | Baseline ID, current object/relation/index/subject counts, and repository-relative source roles plus SHA-256 digests. No generation timestamp is stored. |
| `global.mermaid` | Exact reviewed global Mermaid definition from Data Model. |
| `subjects` | Eight ordered entries with stable kebab-case `id`, display `label`, repository-relative semantic `document`, ordered `table_ids`, and exact focused `mermaid`. |
| `tables` | Ordered table/FTS catalogs grouped by subject order. Each table occurs exactly once. |
| `relationships.physical` | SQLite-FK facts derived from `PRAGMA foreign_key_list`, including source/target columns and update/delete actions. |
| `relationships.application` | Dotted global-ERD relations parsed from semantic truth, including source/target tables, cardinalities, label, and application enforcement. |

Each table contains:

| Field | Contract |
| --- | --- |
| `id`, `kind`, `subject_id`, `semantic_document` | Stable object identity, ordinary/FTS5 kind, one primary subject owner, and semantic source. |
| `columns` | Effective ordered columns with SQLite type, nullability, default SQL, primary-key position, and Markdown semantic contract. |
| `constraints` | Ordered primary key, unique column groups, balanced `CHECK` expressions, and the owning document's constraint explanation. |
| `indexes` | Effective explicit indexes after compatible structure, with uniqueness, partial state, ordered columns, and sort direction. SQLite autoindexes are excluded. |
| `foreign_keys` | Table-local physical target, columns, and update/delete behavior. |
| `semantics` | Purpose/authority, lifecycle contract and class, rebuildability code, producers, consumers, deletion effect, recovery path, DDL/migration ownership, and documented constraints. |

The current baseline has eight subjects, 20 ordinary tables plus one FTS5 object, 244 effective columns, 20 explicit indexes, 20 physical relations, and 23 application relations. Count changes are accepted only with the implementation and semantic owners updated together.

## Determinism And Failure

Generation uses subject order, marker table order, SQLite column/key order, and sorted relation/index/JSON keys. It stores no wall-clock time, absolute path, environment, configured source, or row value. Two builds from identical sources must be byte-identical.

```bash
uv run python scripts/build-schema-presentation.py build
uv run python scripts/build-schema-presentation.py check
```

Both modes run the pinned local Mermaid parser first. Build writes the package output. Check regenerates in memory and fails when the output is missing or byte-stale. Missing owners, lifecycle mappings, semantic bullets, columns, counts, relations, diagrams, or source digests fail with a bounded owner/object message.

`load_schema_presentation()` returns:

- `available=True` with the v1 manifest when its minimal shape and exact object ownership are valid;
- `available=False`, `error_code="manifest-unavailable"` when package data cannot be read;
- `available=False`, `error_code="manifest-invalid"` for decoding, JSON, version, derived-status, count, or ownership failure.

The loader never exposes parser internals to a screen and never falls back to docs, SQLite, Node, npm, a CDN, or network access.

## Product Consumer

`localbrain.schema_explorer` is the bounded read model for `GET /schema`. It normalizes optional `area` and `table` query state against v1, projects only the selected table's related physical and application edges, and supplies ordinary server-rendered links plus approved text and Mermaid definitions. An invalid area returns the global overview; an invalid or cross-area table returns the valid area overview. Raw invalid query values are not reflected.

The route never opens the configured database or reads repository Markdown. Missing or invalid package data produces the loader's intentional unavailable state. JavaScript progressively replaces only the Schema region for history and focus continuity, but it is not a data producer and the complete selected table catalog remains executable HTML without it.

## Privacy And Packaging

Only schema identifiers and approved semantic text enter the manifest. Runtime rows, configured or source paths, source names, document/session content, URLs, credentials, Run artifacts, and machine state are prohibited. Repository-relative owner paths and source hashes are allowed provenance.

The wheel must contain `localbrain/schema-presentation.json` and `localbrain/schema_presentation.py`. An installed package must load them with the repository, Node, runtime database, and network unavailable.

## Change Rule

Update the executable and Data Model owners first, run their parity checks, rebuild the manifest, review the JSON delta, then run check, tests, wheel verification, and privacy scanning. Product surfaces consume v1 but do not hand-edit it. A breaking shape requires a new schema identifier and an approved consumer migration.
