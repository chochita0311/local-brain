# FEAT-0057: Data Model Value Dictionary Baseline

## Metadata

- ID: `feat-0057`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Establish one exhaustive, subject-owned contract for database-related bounded values so physical storage, logical meaning, presentation mode, and visible labels can be checked without runtime templates parsing Markdown or individual screens inventing fallback copy.

## Acceptance Contract

- The Data Model entrance links to one value-dictionary entrance and all nine subject owner documents link to one corresponding subject dictionary.
- Every current physical `CHECK` vocabulary, application-enforced stored family, relevant boolean-like field, and eligible database-backed derived family is either documented in the baseline or explicitly excluded with an owner and reason.
- Each included family defines its physical field or projection, allowed values, enforcement class, logical axis, defaults and fallback, producer, consumer, behavioral consequence, presentation mode, visible labels or technical visibility, and bounded help requirements.
- Each complete family uses exactly one presentation mode:
  - `direct`: every allowed value may render as its physical value;
  - `logical-label`: every allowed and permitted fallback value maps to an explicit logical label;
  - `internal-only`: no family value appears on ordinary product screens.
- A family never mixes translated or interpreted values with raw physical values.
- One repository-owned machine-readable registry is the executable authority for presentation mode and mappings. Subject Markdown remains the durable human-readable contract and is generated from or deterministically checked against that registry.
- Runtime templates and request handlers do not parse Markdown dictionaries.
- Automated parity checks compare current schema constraints, application constants, registry entries, subject dictionaries, and declared visible consumers. Missing values, duplicate ownership, incomplete logical mappings, and unapproved raw-token fallback fail.
- Physical database values, row contents, and compatible migration behavior remain unchanged.

## Scope Boundary

- In:
  - all nine current data-model subjects
  - physical `CHECK` and boolean-like value families
  - application-enforced stored values
  - eligible database-backed derived, manifest, and projection values
  - one machine-readable presentation registry
  - subject-oriented human dictionary documents and reciprocal links
  - ownership, completeness, parity, and stale-assumption checks
  - exact current visible-consumer inventory for later product normalization
- Out:
  - changing physical enum values or database rows
  - broad runtime localization
  - translating arbitrary user or external content
  - product-screen layout changes
  - silently converting internal values into user-facing states
  - consumer migrations owned by FEAT-0061 or another surface-owning Product Feature

## Surface Lanes

- Physical inventory lane:
  - path roots: `src/localbrain/schema.sql`, `db.py`, bounded-value constants, schema-presentation builders, and tests
  - dependencies: current effective 34-table plus FTS5 model and nine subject owners
  - expected evidence: exhaustive included/excluded family ledger with enforcement and producer ownership
  - evaluator ownership: `contract`
- Registry lane:
  - path roots: repository-owned structured value registry and its loader or checker
  - dependencies: physical inventory lane
  - expected evidence: one family key, one presentation mode, complete allowed values, fallbacks, labels, and technical visibility
  - evaluator ownership: `contract`, `functional`
- Documentation lane:
  - path roots: `docs/policies/project/data-model.md`, nine subject owners, and value-dictionary companions
  - dependencies: physical inventory and registry lanes
  - expected evidence: reciprocal navigation, clear logical definitions, consequence copy, and no duplicated table catalog
  - evaluator ownership: `contract`
- Parity lane:
  - path roots: `scripts/check-data-model-docs.py`, focused tests, and declared consumer inventory
  - dependencies: all prior lanes
  - expected evidence: deterministic failure on schema, constant, registry, dictionary, or consumer drift
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- `src/localbrain/schema.sql` physical constraints.
- `src/localbrain/db.py` compatible startup and application-enforced values.
- Bounded-value constants and database-backed derived projections.
- Machine-readable family key, presentation mode, value, fallback, label, help, and visibility shape.
- Data Model entrance, nine subject owners, and nine dictionary companions.
- Data-model documentation and consumer-parity checks.

## Entry And Exit

- Entry point: inspect one current data-model subject or run the data-model parity check.
- Exit or transition behavior: every current bounded family resolves to one owner and complete presentation contract, and downstream Product Features can consume mappings without guessing.

## State Expectations

- Complete: physical values, logical meaning, presentation mode, and all required mappings agree.
- Direct: all allowed values remain self-explanatory as one complete raw family.
- Logical label: every allowed and fallback state has an explicit mapping.
- Internal only: ordinary visible-consumer inventory contains no use of the family.
- Drift: the check names the family, missing or unexpected value, and owning subject without rewriting data.

## Dependencies

- PRD-0009 is `approved`.
- Current data-model documentation and `scripts/check-data-model-docs.py` remain the starting contract.
- No product consumer Feature may treat this draft as executable mapping truth before FEAT-0057 passes.

## Likely Affected Surfaces

- `docs/policies/project/data-model.md`
- `docs/policies/project/data-model/`
- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- bounded-value producers and projection constants under `src/localbrain/`
- `scripts/check-data-model-docs.py`
- focused schema, registry, and documentation tests
- documentation map and architecture links

## Pass Or Fail Checks

- Pass if all nine subjects have linked value dictionaries and no table catalog is duplicated.
- Pass if every in-scope current bounded family is documented or explicitly excluded.
- Pass if each family has one mode and every logical-label mapping is exhaustive.
- Pass if direct families expose all values consistently and internal-only families have no ordinary visible consumer.
- Pass if deterministic checks catch an added schema or application value, missing mapping, duplicate owner, and raw-token consumer fallback.
- Pass if no physical storage value, row, or compatible migration changes.
- Fail if templates parse Markdown, mappings have two authorities, one family mixes raw and logical labels, or missing values fall back silently.

## Regression Surfaces

- Current 34-table plus FTS5 Data Model contract and nine subject owners.
- Fresh schema and compatible startup parity.
- Generated Schema Explorer content.
- Existing physical values and persisted rows.
- Documentation map and repository privacy.

## Harness Trace

- Active spec doc: [spec-0057-data-model-value-dictionary-baseline](../spec/spec-0057-data-model-value-dictionary-baseline.md)
- Active run: [run-20260724-60-data-model-value-dictionary-baseline](../run/run-20260724-60-data-model-value-dictionary-baseline.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0057-contract-data-model-value-dictionary-baseline](../evaluation/eval-0057-contract-data-model-value-dictionary-baseline.md), [eval-0057-functional-data-model-value-dictionary-baseline](../evaluation/eval-0057-functional-data-model-value-dictionary-baseline.md)
- Latest fix note: not created

## Open Review Decisions

- Closed: package JSON is the executable authority and subject Markdown is generated deterministically.
- Closed: relevant boolean-like fields are included; open/versioned operator protocol fields are explicitly excluded with owners and reasons.

## Continuity Notes

- `2026-07-24`: initial draft made one executable registry plus nine subject dictionaries the prerequisite for consistent visible vocabulary without changing physical database values.
- `2026-07-24`: automatic sequential approval entered `run-20260724-60`; the registry, generated dictionaries, runtime loader, and parity checks passed without changing physical storage.
