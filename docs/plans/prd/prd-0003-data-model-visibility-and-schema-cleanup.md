# PRD-0003: Data Model Visibility And Schema Cleanup

## Metadata

- ID: `prd-0003`
- Status: `draft`
- Owner role: `human`
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Request Summary

- Make the complete LocalBrain ERD, tables, columns, relations, indexes, migration behavior, and data ownership visible through durable human-readable documentation.
- Divide the schema into coherent subject areas so individual domains can be understood without losing the global relationship map.
- Audit every schema object and consumer before proposing table, column, constraint, or index cleanup.

## Source Set

### Human Request

- Show all ERD and schema structure rather than explaining isolated tables only when a question arises.
- Choose a durable documentation location and a subject-area structure that remains usable as the application grows.
- Identify unnecessary or poorly owned table information and prepare reviewable cleanup decisions.

### Supporting Documents

- [Project Architecture](../../policies/project/architecture.md): owns LocalBrain's durable implementation and persistence shape.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): governs local data, tracked examples, and schema inspection boundaries.
- [PRD-0002](prd-0002-session-browsing-and-subsession-organization.md): owns the already confirmed removal of `workspaces.git_branch` and addition of `sessions.git_branch`.
- [Project Backlog](../project/backlog.md): owns residual schema work that remains open after an approved cleanup increment closes.

### Current Implementation References

- `src/localbrain/schema.sql`: canonical fresh-database DDL and declared indexes.
- `src/localbrain/db.py`: compatible startup migrations and runtime-only index creation.
- `src/localbrain/ingest/`: source producers for workspaces, Sessions, events, documents, and scan bookkeeping.
- `src/localbrain/queries.py`, `retrieval.py`, `runner.py`, and `workstreams.py`: major schema consumers and derived payload producers.
- `tests/`: synthetic schema setup, persistence fixtures, and behavior-level contract evidence.

## Current Implementation Findings

- The current schema declares 17 ordinary tables and one FTS5 virtual table, but no single document shows all relationships, ownership, rebuildability, or deletion behavior.
- `schema.sql` describes a fresh database while `db.py` adds compatible columns and indexes to existing databases. The effective runtime schema therefore cannot be understood safely from only one file.
- [Project Architecture](../../policies/project/architecture.md) currently groups tables by broad responsibility, but it intentionally does not provide a complete ERD or table and column catalog.
- Some relations are physical foreign keys, while `workstream_links`, `thread_links`, and `checkpoint_resource_refs` use polymorphic `entity_type` and `entity_id` pairs that SQLite cannot validate as ordinary foreign keys.
- Source-derived, user-curated, review-state, operational-history, and fully derived data do not yet have an explicit table-by-table recovery classification. That distinction must be known before destructive cleanup is safe.
- PRD-0002 has already identified one concrete ownership defect: a branch belongs to a Session observation rather than a workspace path. That targeted migration remains owned by PRD-0002 and becomes regression evidence for this wider audit.

## Product Intent

- Let the owner understand where any stored fact lives, why it exists, what it relates to, and whether it can be rebuilt before approving schema cleanup.
- Make future schema changes reviewable as domain changes instead of isolated DDL edits.
- Keep implementation truth and human explanation aligned without copying live personal data into the repository.

## Confirmed Scope

### Documentation Ownership

- Keep `src/localbrain/schema.sql` as the canonical fresh-schema implementation truth.
- Keep `src/localbrain/db.py` as the owner of compatible runtime migrations until a later approved migration system replaces it.
- Create `docs/policies/project/data-model.md` as the durable human entry point for persistence ownership, a global ERD, cross-domain relations, lifecycle classes, and links to detailed subject-area documents.
- Place subject-area details under `docs/policies/project/data-model/`. Each detail document owns table purpose, all columns at a human-readable level, keys, constraints, indexes, relationships, producers, consumers, authority, rebuildability, and deletion implications for its domain.
- Link the data-model entry point from [Project Architecture](../../policies/project/architecture.md) and the [Documentation Map](../../README.md) instead of duplicating the full catalog in either file.
- Keep active cleanup findings and decisions in this PRD and its eventual Feature, Spec, Run, and evaluation artifacts. Move only unresolved residual work to the Project Backlog; do not turn the durable data-model document into a speculative cleanup list.

Proposed durable document tree:

```text
docs/policies/project/data-model.md
docs/policies/project/data-model/
├── source-registry-and-scans.md
├── workspace-and-session-activity.md
├── local-context-corpus.md
├── work-organization-and-resources.md
├── review-and-resume-continuity.md
├── maintenance-execution.md
└── derived-retrieval-index.md
```

### Subject-Area Decomposition

Every current schema object has exactly one primary subject-area owner while cross-domain relationships remain visible in the global ERD.

| Subject area | Primary schema objects | Primary concern |
| --- | --- | --- |
| Source registry and scan bookkeeping | `sources`, `source_files` | source identity, scan state, file fingerprints, and ingestion errors |
| Workspace and Session activity | `workspaces`, `sessions`, `activity_events` | working paths, Git repository roots, source Sessions, parentage, per-Session branch context, and normalized events |
| Local Context corpus | `context_roots`, `context_documents` | user-managed context sources, imported documents, readability, and workspace association |
| Work organization and resources | `workstreams`, `threads`, `workstream_links`, `thread_links`, `local_resources`, `external_resources` | user organization, polymorphic relationships, and canonical linkable resources |
| Review and resume continuity | `suggestions`, `checkpoints`, `checkpoint_resource_refs` | review state, accepted continuity, snapshots, and referenced evidence |
| Maintenance execution | `maintenance_runs` | Task Runner lifecycle, artifacts, budgets, results, and Workstream association |
| Derived retrieval index | `search_index` | rebuildable FTS projection across source-backed and user-managed entities |

### ERD And Catalog Shape

- Provide a level-zero global ERD showing every schema object and all physical or polymorphic cross-domain relationships without listing every column in one unreadable diagram.
- Provide one focused ERD per subject area with primary keys, foreign keys, uniqueness boundaries, cascade behavior, and important cross-domain edges.
- Provide a complete table and column catalog next to the owning subject-area ERD. Exact SQL syntax remains linked to `schema.sql`; the catalog explains semantic meaning rather than pretending to replace DDL.
- Clearly distinguish physical foreign keys from application-enforced polymorphic relations.
- Record indexes, uniqueness constraints, status or type discriminators, JSON payload fields, timestamp formats, and fresh-schema versus compatible-migration ownership.

### Recovery And Cleanup Classification

- Classify every table as source-derived and rebuildable, user-curated and non-rebuildable, generated review state, operational history, or fully derived projection. Record mixed cases explicitly rather than forcing a false single label.
- Record the producer, major consumers, source of authority, mutation path, deletion effect, and recovery path for every table.
- Audit every table, column, index, and relation as `keep`, `change`, `remove`, or `defer`, with code-consumer evidence and migration risk.
- Check at minimum for unused fields, duplicated facts, wrong ownership, polymorphic referential gaps, inconsistent identifiers, missing or redundant indexes, timestamp inconsistency, status/value constraints, JSON fields hiding stable relational data, and fresh-schema/runtime-migration drift.
- Treat the audit as a decision artifact. Only cleanup items explicitly approved through a later Feature may alter runtime schema or data.

## Excluded Scope

- Reading, exporting, diagramming, or committing rows from the user's runtime database.
- Copying real paths, Session content, document bodies, URLs, credentials, Run artifacts, or other private local values into tracked documentation or fixtures.
- Replacing SQLite, introducing an ORM, or redesigning every table merely to produce a more uniform diagram.
- Performing broad table cleanup before the owner reviews the inventory, recovery classification, consumer evidence, and migration risk.
- Reopening the `workspaces.git_branch` decision already owned by PRD-0002.
- Treating an undocumented or apparently unused column as safe to delete without producer and consumer evidence.

## Uncertainty

- Confirm whether the proposed `docs/policies/project/data-model/` subject-area split is preferred over keeping all seven domains as sections in one large `data-model.md` file.
- Decide after the audit whether approved cleanup should be one migration Feature or several domain-sized Features; the decision cannot be made safely before cleanup candidates and dependencies are known.
- Decide whether documentation drift prevention should be a lightweight schema verification test, a generated catalog section, or a required manual review checklist.

## Constraints

- Code and the effective SQLite schema remain implementation truth; documentation must describe them accurately and must not become a second executable schema.
- All tracked diagrams, examples, and tests use synthetic identifiers and paths.
- Cleanup must distinguish rebuildable imported data from non-rebuildable user organization and review decisions before any destructive migration.
- Compatible migrations must preserve stable IDs and relations needed by user-curated Workstreams, Threads, checkpoints, links, and reviewed Suggestions.
- A schema change must update its owning subject-area documentation in the same execution boundary.
- The likely initial execution profile is `docs-content` for inventory and ownership, followed by `foundation-contract` for data integrity decisions and approved migrations.
- Required evaluation includes Contract review for completeness, source-of-truth parity, recovery classification, migration safety, and stale-assumption checks. Functional review becomes required for any runtime migration.

## Acceptance Envelope

- A reader can start at `docs/policies/project/data-model.md`, see the full database boundary, and reach every subject area without consulting conversation history.
- All 17 ordinary tables and the FTS5 virtual table appear exactly once as a primary subject-area responsibility and remain visible in the global ERD.
- Every table has a complete human-readable column catalog, keys, constraints, indexes, producers, consumers, authority, lifecycle class, rebuildability, deletion effect, and recovery path.
- Physical foreign keys, application-enforced polymorphic relationships, and cross-domain edges are visually and textually distinguishable.
- Fresh-schema DDL and compatible runtime migrations have an explicit parity check, and any current drift is recorded rather than silently normalized.
- The cleanup audit gives every schema object a supported `keep`, `change`, `remove`, or `defer` outcome and identifies migration dependencies before runtime work is approved.
- No runtime database content or machine-specific private value enters tracked documentation, fixtures, diagrams, or evaluation evidence.
- Project Architecture and the Documentation Map link to the durable data-model entry point without duplicating its detailed catalog.
- No cleanup migration begins until the owner approves the relevant post-audit Feature boundary.

## Candidate Features

- `Data Model Inventory And Subject ERDs` (`foundation`, `docs`): create the durable global map, seven subject-area catalogs, recovery classifications, and schema/migration parity inventory.
- `Schema Integrity And Cleanup Decisions` (`foundation`, `data`): trace producers and consumers, classify every object as keep/change/remove/defer, and produce bounded migration candidates with risk evidence.
- `Approved Schema Cleanup Migrations` (`foundation`, `data`): apply only the owner-approved cleanup decisions, split by domain when needed to preserve stable IDs and non-rebuildable data.

Feature documents are not created from this draft PRD until the human owner accepts its boundary. The audit may change the number and order of cleanup Features, so migration Features must not be precommitted before evidence exists.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human request | primary | complete ERD visibility, durable placement, subject-area decomposition, and table cleanup review | does not pre-approve unknown destructive migrations |
| `schema.sql` and `db.py` | implementation truth | fresh DDL, compatible migrations, indexes, foreign keys, defaults, and value shapes | contain no semantic explanation of every producer or consumer |
| Current Python consumers | implementation evidence | actual reads, writes, payloads, joins, deletion paths, and application-enforced relations | usage alone does not prove that a field should remain |
| Project Architecture | durable owner | persistence boundaries and package ownership | links to the detailed data model instead of duplicating it |
| PRD-0002 | approved adjacent contract | Session branch ownership and obsolete workspace branch removal | wider cleanup cannot change that approved direction implicitly |

## Continuity Notes

- `2026-07-17`: created the draft after the workspace-versus-Session branch ownership review exposed the absence of a complete, navigable data-model reference.
- `2026-07-17`: proposed one durable entry document, seven subject-area detail documents, and a separate planning trail for cleanup so implementation truth, durable explanation, and active migration decisions do not overlap.
