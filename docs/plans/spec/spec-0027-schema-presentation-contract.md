# SPEC-0027: Schema Presentation Contract

## Metadata

- ID: `spec-0027`
- Status: `approved`
- Run ID: `run-20260718-32`
- Attempt: `1`
- Parent Feature: [feat-0027-schema-presentation-contract](../feature/feat-0027-schema-presentation-contract.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: value shape and ownership, generation, packaging and consumer readiness
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human request: let the later in-app Schema surface use the same complete subject model as durable docs.
- Parent feature: FEAT-0027.
- Parent PRD: approved PRD-0003.
- Golden sources: passed FEAT-0026 owner docs, `schema.sql`, actual compatible structural migrations/indexes in `db.py`, and the pinned local Mermaid parser.
- Relevant policies or contracts: Data Model, Developer Guide, Architecture, Privacy And Data Handling, passed FEAT-0025/0026, and foundation-contract profile.

## Implementation Goal

- Generate and package one byte-stable `localbrain.schema-presentation.v1` JSON manifest from isolated effective schema facts and approved Markdown semantics, with a bounded Python loader and no runtime database, docs, Node, or network dependency.

## In-Scope Behavior

- Add a durable Schema Presentation contract document defining exact v1 ownership, fields, ordering, derivation, failure behavior, and commands.
- Add a schema-only mode to compatible migrations that applies columns/indexes without reading paths or mutating data; runtime behavior remains the default.
- Build an in-memory SQLite database from `schema.sql`, apply the real compatible structural path, and introspect tables, columns, primary/unique/check constraints, explicit indexes, and physical FKs.
- Parse subject order/ownership, lifecycle classes, global and subject Mermaid, table semantic bullets, column contracts, and application relations from FEAT-0026 Markdown.
- Generate sorted, stable JSON at `src/localbrain/schema-presentation.json` with `derived: true`, baseline/source digests, eight subjects, 21 object catalogs, 19 physical relations, and all documented application relations.
- Add write/check modes, temporary-output support, bounded errors for missing semantic fields, and local Mermaid validation before output.
- Add `src/localbrain/schema_presentation.py` loader returning available/manifest or bounded `manifest-unavailable`/`manifest-invalid` without fallback introspection.
- Verify wheel inclusion and isolated installed loading with repository docs, Node, runtime DB, and network unavailable.

## Out-Of-Scope Behavior

- No route, navigation, template, CSS, browser interaction, runtime row query, cleanup decision, DDL change, semantic catalog rewrite, or app-specific second ERD.

## Affected Surfaces

- structural-only invocation path in `db.py`
- schema presentation contract policy
- generator/checker scripts and generated package JSON
- Python manifest loader
- Developer Guide and Architecture links
- determinism, malformed/stale, loader, package, and privacy tests

## Surface Lanes

- Value shape and ownership:
  - path roots: Schema Presentation policy and FEAT-0026 Data Model docs
  - dependency order: first
  - implementation responsibility: exact v1 fields, source roles, ordering, derived/non-executable status
  - validation evidence: contract review and schema tests
- Generation:
  - path roots: generator, `schema.sql`, `db.py`, generated JSON
  - dependency order: after value shape
  - implementation responsibility: isolated effective facts plus parsed semantic truth and deterministic bytes
  - validation evidence: two-generation equality, stale and malformed fixtures, exact parity
- Packaging and consumer readiness:
  - path roots: loader, wheel, tests, Architecture/Developer Guide
  - dependency order: after generated output
  - implementation responsibility: bounded installed runtime loading with no source fallback
  - validation evidence: wheel inventory and isolated Node-free load

## State And Interaction Contract

- Current output: check regenerates in memory and matches committed bytes.
- Physical drift: object/column/constraint/index/relation or source digest changes output and fails check.
- Semantic drift: missing owner, bullet, column contract, lifecycle mapping, or Mermaid fails with the owner path/table.
- Invalid Mermaid: local parser check fails before manifest acceptance.
- Missing installed manifest: loader returns `available=False`, `error_code="manifest-unavailable"`.
- Malformed/wrong-schema manifest: loader returns `available=False`, `error_code="manifest-invalid"` without raw parser details.
- Valid installed manifest: loader returns the parsed v1 document and performs no DB, docs, Node, or network access.

## Data And Contract Assumptions

- Physical facts come only from SQLite `:memory:` after fresh DDL and the real compatible structural/index path.
- Semantic fields come only from Data Model Markdown and are not manually duplicated in Python or JSON.
- Generated JSON is presentation data, never executable DDL or migration input.
- Ordered subjects follow the entry map; tables follow subject marker order; physical arrays use deterministic table/column/name order; JSON keys are sorted.
- Runtime-compatible migrations retain their existing default data migration behavior; schema generation opts out explicitly.

## Contract Surfaces

- Producer expectations: schema and owner docs jointly produce the complete derived manifest.
- Consumer expectations: FEAT-0028 loads only through `schema_presentation.py` and renders supplied definitions; it does not inspect schema/docs.
- Generated artifacts: `src/localbrain/schema-presentation.json`.
- Source-of-truth owner: executable structure in schema/migrations, semantics in Data Model docs, transformation in generator.
- Stale-assumption check: source digests, complete extraction, regenerated-byte comparison, loader validation, and installed wheel test.

## Required Evaluators

- Contract: exact v1 shape, ownership, physical/semantic provenance, complete parity, derived status, privacy, and downstream readiness.
- Design: not required; no surface.
- Functional: deterministic/stale/malformed behavior, Mermaid validation, isolated schema path, wheel contents, installed loader, regressions.
- UX heuristic: not required.

## Acceptance Mapping

- Versioned shape: Schema Presentation policy and loader schema check.
- Isolated effective facts: `:memory:` plus structural-only actual migration call.
- Semantic transformation: parsed owner documents and their source hashes.
- Complete contents: manifest tests across eight subjects, 21 objects, every column/index/FK/application relation and semantic field.
- Same ERDs: exact Markdown Mermaid strings in generated JSON.
- Determinism/staleness: write/check and two-byte generation tests.
- Privacy: no rows, configured paths, runtime values, or network inputs; serialized allow/deny assertions and repository scan.
- Installed use: final wheel expansion and loader test outside repository path with Node absent.
- No UI: route/template/navigation diffs remain absent.

## Evaluation Focus

- Verify structural-only migrations cannot skip an effective runtime index and cannot execute Context path discovery.
- Verify application relations derive from dotted global Mermaid edges and physical relations derive from PRAGMA, with no manual duplicate registry.
- Verify check failure is bounded and loader never falls back to a runtime database or repository docs.
- Verify generated semantics are complete enough for table detail without parsing prose in FEAT-0028.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-18`: approved attempt 1 after FEAT-0026 established complete parseable semantic owners and rendered Mermaid definitions.
