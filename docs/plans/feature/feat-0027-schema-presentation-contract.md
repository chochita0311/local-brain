# FEAT-0027: Schema Presentation Contract

## Metadata

- ID: `feat-0027`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Establish one deterministic, packageable, schema-only presentation contract that combines effective physical schema facts with the approved human semantics and can be consumed by both verification and the later Schema Explorer without creating a second executable schema.

## Acceptance Contract

- A versioned `localbrain.schema-presentation.v1` manifest shape is documented and generated deterministically.
- Effective physical facts are derived from an isolated schema-only database created from `schema.sql` plus compatible startup migrations and runtime indexes, never from user rows.
- Human semantic facts remain owned by the approved data-model documents and are transformed into the manifest rather than manually re-entered for the application.
- The manifest contains baseline identity; ordered subject identifiers and labels; global and subject Mermaid definitions; table purpose and ownership; columns; keys; constraints; indexes; physical and application-enforced relations; producers; consumers; authority; lifecycle class; rebuildability; deletion effect; recovery path; and fresh-schema or migration ownership.
- Every manifest table belongs to exactly one subject, and the manifest object set exactly matches the effective schema baseline.
- Generated Mermaid definitions and table catalogs are the same deterministic representation used by later product consumers; a separate hand-maintained application ERD is prohibited.
- Generation is deterministic, and a check mode fails when committed or packaged presentation output is stale, incomplete, malformed, or inconsistent with the schema or durable docs.
- The generated output is explicitly derived. `schema.sql` and `db.py` remain executable truth, while the data-model documents remain semantic truth.
- The packaged manifest contains no row values, runtime paths, source names, document content, URLs, credentials, Run artifacts, or machine-specific state.
- An installed LocalBrain package can load the manifest without access to repository docs, Node.js, a runtime database, or the network.
- No application route or visible navigation is added by this Feature.

## Scope Boundary

- In:
  - schema-only isolated effective-database construction
  - versioned schema presentation manifest
  - extraction of physical schema facts
  - transformation of approved data-model semantics
  - global and subject Mermaid definitions as presentation data
  - deterministic generate and check behavior
  - stale, malformed, missing, and mismatch failure contracts
  - package inclusion and Python load contract
  - synthetic contract fixtures
- Out:
  - `/schema` route, persistent navigation, templates, CSS, or browser interaction
  - Mermaid dependency installation or browser adapter owned by FEAT-0025
  - rewriting the approved data-model catalog
  - runtime row introspection or private database access
  - schema cleanup decisions or migrations
  - treating the manifest as writable DDL or an alternative migration source

## Surface Lanes

- Value-shape and ownership lane:
  - path roots: data-model policy docs, schema presentation contract docs, synthetic fixtures
  - dependencies: passed FEAT-0026
  - expected evidence: exact v1 fields, physical-versus-semantic ownership, derived-output status, and failure rules
  - evaluator ownership: `contract`
- Generation lane:
  - path roots: bounded Python generator or module, `schema.sql`, `db.py`, generated manifest
  - dependencies: value-shape and ownership lane
  - expected evidence: deterministic schema-only generation with exact object, subject, relation, and Mermaid parity
  - evaluator ownership: `contract`, `functional`
- Packaging and consumer-readiness lane:
  - path roots: package data, Python manifest loader, tests, architecture and developer docs
  - dependencies: generation lane
  - expected evidence: installed package loads the same manifest without repository docs, runtime rows, Node, or network
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- `localbrain.schema-presentation.v1` value shape
- effective schema construction and introspection boundary
- physical schema fact ownership
- semantic documentation ownership
- table-to-subject mapping and order
- physical and application-enforced relation representation
- Mermaid source representation
- deterministic generated-output and stale-check behavior
- package data and Python loader behavior
- no-row and local-only privacy boundary

## Required Evaluators

- `contract`: manifest value shape, source ownership, derived status, exact schema and subject parity, relation semantics, packaging, and downstream readiness.
- `functional`: deterministic generation, stale checks, malformed inputs, clean installed-package loading, and no-row evidence.

## User-Visible Outcome

- This foundation Feature adds no screen. It ensures the later Schema Explorer consumes a complete, stable, privacy-safe model without duplicating the schema or documentation.

## Entry And Exit

- Entry point: documented schema-presentation generate and check commands and the Python manifest loader.
- Exit or transition behavior: a valid packaged v1 manifest is available to FEAT-0028; invalid or stale input fails before a product route can present it as current.

## State Expectations

- Current: generation is stable and check mode passes without diff.
- Physical drift: check mode identifies affected objects and fails.
- Documentation drift: missing subject or semantic fields fail with the owning document and object identified.
- Malformed Mermaid: validation fails before packaging.
- Missing packaged manifest: the loader returns a bounded unavailable result rather than reading user data as fallback.
- Success: schema, docs, manifest, Mermaid definitions, and installed package agree.

## Dependencies

- FEAT-0025 is `passed` for local Mermaid validation.
- FEAT-0026 is `passed` and owns the complete semantic baseline.

## Likely Affected Surfaces

- bounded schema presentation generator and Python loader under `src/localbrain/`
- package-owned generated schema presentation data
- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `docs/policies/project/data-model.md`
- `docs/policies/project/data-model/`
- `docs/policies/project/architecture.md`
- `docs/policies/project/developer-guide.md`
- schema presentation, determinism, packaging, and privacy tests

## Pass Or Fail Checks

- Pass if two clean generations produce byte-stable presentation output.
- Pass if the v1 manifest exactly covers all 20 ordinary tables and FTS5, all eight subjects, and every approved physical or application-enforced relation.
- Pass if removing or changing a schema object, owner entry, relation, catalog field, or Mermaid definition makes check mode fail with bounded evidence.
- Pass if physical facts come from the isolated effective schema and semantic facts trace to the owning data-model document.
- Pass if no manually maintained application-only ERD or duplicate catalog is required.
- Pass if an installed package loads the manifest with repository docs, runtime DB, Node, and network unavailable.
- Pass if the manifest contains only schema and approved semantic metadata.
- Fail if generation reads or serializes any runtime row or machine-specific value.
- Fail if the manifest can silently override DDL, migrations, or durable semantic documentation.

## Regression Surfaces

- fresh and compatible SQLite initialization
- runtime-only index creation
- package build and static asset inclusion
- data-model documentation ownership
- repository privacy and synthetic evidence
- Python-only runtime operation

## Harness Trace

- Active spec doc: [spec-0027-schema-presentation-contract](../spec/spec-0027-schema-presentation-contract.md)
- Active run: [run-20260718-32-schema-presentation-contract](../run/run-20260718-32-schema-presentation-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract](../evaluation/eval-0027-contract-schema-presentation-contract.md), [functional](../evaluation/eval-0027-functional-schema-presentation-contract.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-18`: initial draft separated the deterministic schema-only consumer contract from both the human baseline and the later visible Schema Explorer.
- `2026-07-18`: entered the sequential loop after FEAT-0026 passed; SPEC-0027 fixes the Markdown-to-manifest transformation, isolated effective-schema, loader, and package contracts.
- `2026-07-18`: passed attempt 1 with a byte-stable v1 manifest, exact eight-subject and 21-object ownership, isolated structural generation, bounded loader validation, 95 passing tests, and final installed-wheel evidence.
