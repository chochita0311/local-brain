# SPEC-0026: Data Model Baseline And Subject ERDs

## Metadata

- ID: `spec-0026`
- Status: `approved`
- Run ID: `run-20260718-31`
- Attempt: `1`
- Parent Feature: [feat-0026-data-model-baseline-and-subject-erds](../feature/feat-0026-data-model-baseline-and-subject-erds.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `docs`
- Execution Profile: `docs-content`
- Surface Lane: effective-schema inventory, durable documentation, navigation and rendering
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Source Set

- Human request: establish the complete model once, display it by subject with Mermaid, and make later work update only affected schema areas.
- Parent feature: FEAT-0026.
- Parent PRD: approved PRD-0003.
- Golden sources: `schema.sql`, compatible migrations and runtime indexes in `db.py`, current SQL producers/consumers, and synthetic behavior tests.
- Relevant policies or contracts: Project Architecture, Developer Guide, Privacy And Data Handling, passed FEAT-0025, and docs-content profile.

## Implementation Goal

- Create one complete schema-only data-model baseline with a level-zero ERD, eight focused ERDs, exact object ownership, complete column catalogs, lifecycle and recovery semantics, and automated parity/render checks without changing runtime behavior.

## In-Scope Behavior

- Create `docs/policies/project/data-model.md` as the entry point and the eight approved subject documents beneath `docs/policies/project/data-model/`.
- Own exactly 20 ordinary tables plus the FTS5 `search_index` once across the subject documents.
- Document the current 19 physical foreign keys and every material application-enforced edge, including polymorphic link targets, suggestion targets/origins, Session maintenance-run identity, Usage Fact workspace snapshots, source-file correlations, and search projections.
- Catalog every effective column, primary/unique/check constraint, explicit effective index, producer, consumer, authority, lifecycle class, rebuildability, deletion effect, recovery path, and fresh/migration/runtime-index owner.
- Record the baseline identity from `schema.sql` and `db.py`, current object and relation counts, known fresh-versus-compatible ownership, and no silent drift.
- Add a deterministic schema-only checker for object/column/index/owner/hash/link parity and a local Mermaid parser check for all nine diagram blocks.
- Link the canonical entry from Project Architecture and the Documentation Map without copying the detailed catalog.
- State the baseline-then-delta maintenance routing for future table, column, index, relation, lifecycle, subject, and cross-domain changes.

## Out-Of-Scope Behavior

- Do not modify DDL, startup migrations, indexes, producers, consumers, runtime data, cleanup status, application routes, navigation, packaged presentation manifests, or client interactions.
- Do not classify any object as removable; record current semantics only.
- Do not inspect a user database or include machine paths, runtime values, source content, credentials, or screenshots containing private data.

## Affected Surfaces

- canonical data-model entry and eight subject documents
- Project Architecture and Documentation Map links
- schema documentation parity and Mermaid parser checks
- focused synthetic tests for those checks

## Surface Lanes

- Effective-schema inventory:
  - path roots: `schema.sql`, `db.py`, Python SQL producers/consumers, tests
  - dependency order: first
  - implementation responsibility: authoritative object, column, constraint, index, relation, and lifecycle evidence
  - validation evidence: in-memory SQLite plus static migration/index/consumer inspection
- Durable documentation:
  - path roots: data-model entry and eight subject documents
  - dependency order: after inventory
  - implementation responsibility: complete current truth and one primary subject owner per object
  - validation evidence: automated coverage checker and contract review
- Navigation and rendering:
  - path roots: Architecture, Documentation Map, nine Mermaid blocks
  - dependency order: after documents
  - implementation responsibility: discoverability, valid links, locally parseable and readable diagrams
  - validation evidence: link scan, local Mermaid parser, rendered browser inspection

## State And Interaction Contract

- Current baseline: all counts, columns, explicit indexes, hashes, subject markers, and Mermaid blocks pass.
- Schema or `db.py` change without owner-doc update: the checker fails on the baseline hash and relevant inventory.
- Missing or duplicate subject owner: the checker fails.
- Missing table column or explicit index: the checker fails in the owning document.
- Invalid Mermaid: the local parser exits non-zero and names the owning file.
- Diagram rendering unavailable or unreadable: textual catalogs remain useful, but Feature acceptance remains blocked.
- No runtime database is opened; the checker applies `schema.sql` only to an in-memory SQLite connection.

## Data And Contract Assumptions

- Fresh DDL owns all current objects and 13 explicit indexes; `db.py` owns compatible column additions/removal and seven additional effective index names, while repeating six fresh index statements idempotently.
- Effective current identity is 20 ordinary tables, one FTS5 table, 19 physical FKs, and 20 unique explicit index names; SQLite autoindexes and FTS shadow tables are implementation internals, not primary schema objects.
- Application edges are semantically real but not SQLite-enforced and must use a visually distinct non-identifying/dotted Mermaid relation plus explicit text.
- Lifecycle categories describe recovery characteristics, not cleanup decisions.

## Contract Surfaces

- Producer expectations: implementation DDL, migrations, and SQL modules remain unchanged and authoritative.
- Consumer expectations: readers and FEAT-0027 use the canonical subject ownership and textual semantics without rediscovery.
- Generated artifacts: none; diagrams remain tracked Mermaid source in Markdown.
- Source-of-truth owner: implementation for structure and owner docs for durable human explanation.
- Stale-assumption check: hashes, in-memory schema introspection, explicit-index union, subject markers, column tokens, link targets, and Mermaid parsing.

## Required Evaluators

- Contract: exact source fidelity, one-owner mapping, complete catalogs, relation notation, lifecycle/recovery truth, compatible ownership, and absence of cleanup inference.
- Design: not required; no product surface.
- Functional: automated schema/doc/link parity, all nine Mermaid parser results, local rendered readability, tests, and privacy boundary.
- UX heuristic: not required; no product interaction.

## Acceptance Mapping

- Durable entry and eight owners: fixed document tree plus subject map.
- 20+FTS coverage: in-memory SQLite inventory versus exact subject markers.
- Global model and edges: level-zero ERD plus physical/application edge registry.
- Complete catalogs: checker-enforced column/index tokens and evaluator review of semantics, producers, consumers, lifecycle, deletion, recovery, and ownership.
- Fresh/migration/runtime reconciliation: baseline identity and per-subject ownership notes.
- Links: Architecture and Documentation Map canonical links plus local link validation.
- Baseline-delta guide: change-type routing table in the entry document.
- Local Mermaid: passed FEAT-0025 parser and rendered browser evidence.
- Privacy: schema-only source, synthetic checks, repository privacy scan.

## Evaluation Focus

- Check mixed lifecycle cases instead of treating all imported tables as freely rebuildable.
- Check every polymorphic target and historical snapshot edge is labeled application-enforced, never as a physical FK.
- Check effective indexes include the seven runtime-only names and avoid double-counting six idempotent duplicates.
- Check global readability and each focused ERD at ordinary desktop width.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-18`: approved attempt 1 after FEAT-0025 passed and schema-only inventory confirmed 20 ordinary tables, one FTS5 object, 19 physical FKs, and 20 effective explicit indexes.
