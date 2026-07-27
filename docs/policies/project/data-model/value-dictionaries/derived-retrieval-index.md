<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Derived retrieval index Value Dictionary

Durable table owner: [docs/policies/project/data-model/derived-retrieval-index.md](../derived-retrieval-index.md)

This companion owns bounded physical/logical/presentation mappings only. It does not duplicate the table catalog.

## `search-index.entity-type`

- Physical field or projection: `search_index.entity_type`
- Allowed values: `session`, `document`, `atlassian_item`
- Enforcement: `projection`
- Logical axis: search projection owner
- Default: `NULL`
- Fallbacks: `null`: reject; `unknown`: reject; `invalid`: reject; `future`: reject
- Producers: `src/localbrain/retrieval.py`, `src/localbrain/atlassian.py`
- Consumers: `src/localbrain/retrieval.py`, `src/localbrain/atlassian_browse.py`
- Consequence: Selects the source table and result route for a derived row.
- Presentation mode: `internal-only`
- Labels: none; the family is not visible on ordinary screens.
- Help: none
- Visible consumer inventory: none.

## Explicit Exclusions

| Pattern | Owner | Reason |
| --- | --- | --- |
| `search_index.source_kind` | projection producers | Extensible internal provenance string; ordinary screens derive labels from the owning entity instead. |
