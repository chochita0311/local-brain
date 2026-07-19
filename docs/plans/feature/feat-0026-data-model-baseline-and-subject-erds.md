# FEAT-0026: Data Model Baseline And Subject ERDs

## Metadata

- ID: `feat-0026`
- Status: `passed`
- Type: `foundation`
- Surface: `docs`
- Execution Profile: `docs-content`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Goal

- Establish the complete human-readable baseline for LocalBrain's effective SQLite model so every current schema object, relationship, lifecycle rule, producer, consumer, and recovery boundary has one durable subject owner.

## Acceptance Contract

- `docs/policies/project/data-model.md` becomes the durable entry point for persistence ownership, the level-zero Mermaid ERD, lifecycle classes, cross-domain relations, baseline identity, and incremental update guidance.
- Eight subject documents under `docs/policies/project/data-model/` own exactly the subject areas and schema objects approved by PRD-0003.
- All 20 ordinary tables and the FTS5 `search_index` appear exactly once as a primary subject responsibility and remain visible in the global map.
- The level-zero ERD shows every object and every physical or application-enforced cross-domain edge without expanding all columns into an unreadable global diagram.
- Each subject document contains one focused Mermaid ERD and a complete human-readable catalog for its tables, columns, keys, constraints, indexes, relationships, producers, consumers, authority, mutation path, lifecycle class, rebuildability, deletion effect, recovery path, and fresh-schema or migration ownership.
- Physical foreign keys and polymorphic `entity_type` plus `entity_id` relations are visibly and textually distinct.
- The baseline reconciles `schema.sql`, compatible startup migrations, runtime-only indexes, current producers, current consumers, and synthetic contract tests. Any unexplained drift is recorded rather than silently normalized.
- Every table is classified as source-derived and rebuildable, user-curated and non-rebuildable, generated review state, operational history, fully derived projection, or an explicit mixed case.
- Project Architecture and the Documentation Map link to the new entry point without duplicating the complete catalog.
- The entry point defines the baseline-then-delta rule: later work updates only affected owner documents while those documents continue to describe complete current truth.
- No runtime rows or machine-specific values are inspected or copied; all tracked examples and rendered evidence are synthetic or schema-only.

## Scope Boundary

- In:
  - complete effective-schema inventory for the current 20 ordinary tables and FTS5 object
  - global Mermaid ERD
  - eight focused subject Mermaid ERDs
  - complete table and column catalogs
  - physical and application-enforced relationships
  - producer, consumer, authority, lifecycle, deletion, rebuild, and recovery classification
  - fresh-schema, compatible-migration, and runtime-index ownership
  - baseline identity and incremental maintenance guide
  - Project Architecture and Documentation Map links
  - Mermaid syntax and rendered-output validation through FEAT-0025
- Out:
  - `/schema` navigation or application route
  - packaged schema presentation manifest
  - keep, change, remove, or defer cleanup decisions owned by FEAT-0029
  - schema, migration, producer, or consumer behavior changes
  - runtime database rows, paths, content, URLs, credentials, or artifacts
  - generated app UI or JavaScript interaction behavior

## Surface Lanes

- Effective-schema inventory lane:
  - path roots: `src/localbrain/schema.sql`, `src/localbrain/db.py`, producers, consumers, synthetic tests
  - dependencies: approved PRD-0003
  - expected evidence: schema object, column, constraint, index, relation, producer, and consumer inventory with fresh and compatible ownership
  - evaluator ownership: `contract`
- Durable documentation lane:
  - path roots: `docs/policies/project/data-model.md`, `docs/policies/project/data-model/`
  - dependencies: inventory lane
  - expected evidence: complete ownership, semantic catalog, lifecycle, deletion, recovery, and baseline-delta guidance
  - evaluator ownership: `contract`
- Navigation and rendering lane:
  - path roots: Project Architecture, Documentation Map, Mermaid definitions
  - dependencies: durable documentation lane, passed FEAT-0025
  - expected evidence: valid links, locally rendered diagrams, subject coverage, and readable output
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- `schema.sql` fresh-database ownership
- `db.py` compatible migration and runtime-index ownership
- global and subject data-model documentation ownership
- table-to-subject mapping
- physical and polymorphic relation notation
- lifecycle, authority, rebuildability, deletion, and recovery vocabulary
- baseline identity and delta maintenance rules
- Architecture and Documentation Map source routing

## Required Evaluators

- `contract`: completeness, source fidelity, one-owner mapping, relation classification, lifecycle and recovery ownership, migration parity, and stale-reference checks.
- `functional`: links, Mermaid syntax and rendered output, document navigation, and generated-view readability.

## User-Visible Outcome

- This foundation Feature does not add an application route. A repository reader can understand the complete data model without conversation history or raw DDL traversal.

## Entry And Exit

- Entry point: `docs/policies/project/data-model.md`.
- Exit or transition behavior: each global object or subject link reaches one owning subject catalog; FEAT-0027 can derive a schema-only presentation contract without rediscovering ownership.

## State Expectations

- Baseline current: every effective object is owned and all parity checks pass.
- Known drift: the baseline identifies the mismatch, owner, and evidence without changing runtime behavior.
- Unknown semantic owner: evaluation fails rather than placing the object in a miscellaneous domain.
- Mixed lifecycle: the table records each component explicitly rather than using a false single classification.
- Diagram unavailable: the textual relationship and catalog remain complete, while rendered validation failure blocks Feature acceptance.
- Success: the global map, eight subjects, effective schema, and owner links agree.

## Dependencies

- PRD-0003 is `approved`.
- FEAT-0025 must be `passed` before Mermaid rendered-output evidence is accepted.

## Likely Affected Surfaces

- `docs/policies/project/data-model.md`
- `docs/policies/project/data-model/source-registry-and-scans.md`
- `docs/policies/project/data-model/workspace-and-session-activity.md`
- `docs/policies/project/data-model/usage-and-cost-facts.md`
- `docs/policies/project/data-model/local-context-corpus.md`
- `docs/policies/project/data-model/work-organization-and-resources.md`
- `docs/policies/project/data-model/review-and-resume-continuity.md`
- `docs/policies/project/data-model/maintenance-execution.md`
- `docs/policies/project/data-model/derived-retrieval-index.md`
- `docs/policies/project/architecture.md`
- `docs/README.md`
- bounded schema inventory and link/render verification

## Pass Or Fail Checks

- Pass if the documented object list exactly matches the effective 20-table plus FTS5 schema and each object has one primary subject owner.
- Pass if every table catalog covers every effective column, key, constraint, index, relation, producer, consumer, lifecycle, deletion, rebuild, recovery, and schema-or-migration owner.
- Pass if global and subject Mermaid definitions render locally and remain readable at their intended levels of detail.
- Pass if physical foreign keys and application-enforced polymorphic edges cannot be mistaken for one another.
- Pass if fresh DDL, compatible migrations, and runtime-only indexes are reconciled and any drift is explicit.
- Pass if Architecture and the Documentation Map link to the canonical entry without duplicating its catalog.
- Pass if the baseline-delta guide tells a later Feature exactly which documents to update for each kind of schema change.
- Pass if tracked evidence contains no runtime row, private path, content, URL, credential, or artifact.
- Fail if an apparently unused field is classified as removable before FEAT-0029 traces its consumers.

## Regression Surfaces

- `schema.sql` and `db.py` implementation ownership
- Project Architecture and Developer Guide responsibilities
- PRD-0002 Session branch and hierarchy contract
- PRD-0004 usage, price snapshot, and Project attribution contract
- repository privacy and synthetic-evidence boundary

## Harness Trace

- Active spec doc: [spec-0026-data-model-baseline-and-subject-erds](../spec/spec-0026-data-model-baseline-and-subject-erds.md)
- Active run: [run-20260718-31-data-model-baseline-and-subject-erds](../run/run-20260718-31-data-model-baseline-and-subject-erds.md)
- Execution profile: `docs-content`
- Latest evaluator report: [contract](../evaluation/eval-0026-contract-data-model-baseline-and-subject-erds.md), [functional](../evaluation/eval-0026-functional-data-model-baseline-and-subject-erds.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-18`: initial draft made the complete baseline a separate documentation Feature that depends on the local Mermaid contract but does not pre-approve cleanup or application UI.
- `2026-07-18`: entered the sequential execution loop after FEAT-0025 passed; SPEC-0026 fixes the 20-table, one-FTS5, eight-subject baseline and validation contract.
- `2026-07-18`: passed attempt 1 with exact object/column/index ownership, nine locally parsed and rendered Mermaid ERDs, complete lifecycle/recovery catalogs, 85 passing tests, and a passing privacy scan.
