<!-- Generated from crates/core/resources/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Derived retrieval index Value Dictionary

Durable table owner: [docs/policies/project/data-model/derived-retrieval-index.md](../derived-retrieval-index.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `search-index.entity-type`

- Physical field or projection: `search_index.entity_type`
- Allowed values: `session`, `document`, `atlassian_item`, `atlassian_structure_reference`
- Enforcement: `projection`
- Logical axis: search projection owner
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `crates/core/src/backend/workstreams/retrieval.rs`, `crates/core/src/backend/atlassian/catalog/mod.rs`, `crates/core/src/backend/atlassian/structure_references.rs`
- Consumers: `crates/core/src/backend/workstreams/retrieval.rs`, `crates/core/src/backend/atlassian/browse.rs`, `crates/core/src/backend/atlassian/structure_references.rs`
- Consequence: Selects the source table and result route for a derived row.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `search_index.source_kind` | projection producers | Extensible internal provenance string; ordinary screens derive labels from the owning entity instead. |
