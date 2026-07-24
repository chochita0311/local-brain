# PRD-0003: Data Model Visibility And Schema Cleanup

## Metadata

- ID: `prd-0003`
- Status: `passed`
- Owner role: `human`
- Created: `2026-07-17`
- Updated: `2026-07-24`

## Completion State

- FEAT-0025 through FEAT-0032, the separately approved FEAT-0035 through FEAT-0037, and follow-up FEAT-0052 passed their execution loops.
- LocalBrain owns a pinned offline Mermaid asset, the original complete 20-table plus FTS5/eight-subject baseline, a baseline-then-delta maintenance contract, deterministic package presentation, and the read-only `System > Schema` Explorer. Approved deltas now extend current truth to 34 ordinary tables plus FTS5 across nine subject areas.
- The current integrity ledger resolves all 512 schema objects to `keep 423`, `change 0`, `remove 0`, or `defer 89`, with evidence, risk, recovery, and automated stale checks.
- On `2026-07-19`, the human owner approved and passed all four migration boundaries. Boundary 4 became FEAT-0037 and now preserves which Workstream started a Maintenance Run through the compatible optional FK.
- On `2026-07-24`, FEAT-0052 added bounded diagram zoom without changing schema or Mermaid source; official ELK routing evaluation moved to draft PRD-0008.

## Request Summary

- Make the complete LocalBrain ERD, tables, columns, relations, indexes, migration behavior, and data ownership visible through durable human-readable documentation.
- Divide the schema into coherent subject areas so individual domains can be understood without losing the global relationship map.
- Audit every schema object and consumer before proposing table, column, constraint, or index cleanup.
- Establish one complete baseline, then keep the data model current through bounded change records and updates only to the affected schema objects, subject-area documents, and cross-domain views.
- Expose the same schema-only model inside LocalBrain through a locally rendered Mermaid `Schema` surface organized by the eight subject areas.

## Source Set

### Human Request

- Show all ERD and schema structure rather than explaining isolated tables only when a question arises.
- Choose a durable documentation location and a subject-area structure that remains usable as the application grows.
- Identify unnecessary or poorly owned table information and prepare reviewable cleanup decisions.
- Add `Schema` below `Sources` in the persistent `System` navigation so the model can be inspected without leaving LocalBrain.
- Render the global model and each subject area with a properly managed local Mermaid library rather than depending on an external diagram service or CDN.

### Supporting Documents

- [Project Architecture](../../policies/project/architecture.md): owns LocalBrain's durable implementation and persistence shape.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): governs local data, tracked examples, and schema inspection boundaries.
- [Design Constitution](../../policies/design/design-constitution.md): owns the persistent shell, navigation, Explorer family, responsive boundaries, local asset rule, and visual compatibility contract.
- [Design Evaluation](../../policies/design/design-evaluation.md) and [Interaction Evaluation](../../policies/experience/interaction-evaluation.md): own visible, responsive, selection, history, fallback, and client-asset evaluation expectations.
- [PRD-0002](prd-0002-session-browsing-and-subsession-organization.md): owns the already confirmed removal of `workspaces.git_branch` and addition of `sessions.git_branch`.
- [PRD-0004](prd-0004-session-usage-and-cost-dashboard.md): owns the passed Usage Record, immutable price snapshot, estimated-cost, and Project attribution contracts added after this PRD was first drafted.
- The official `mermaid` npm package usage contract: owns the supported browser-library installation, initialization, and rendering API.
- [Project Backlog](../project/backlog.md): owns residual schema work that remains open after an approved cleanup increment closes.

### Current Implementation References

- `src/localbrain/schema.sql`: canonical fresh-database DDL and declared indexes.
- `src/localbrain/db.py`: compatible startup migrations and runtime-only index creation.
- `src/localbrain/ingest/`: source producers for workspaces, Sessions, events, documents, and scan bookkeeping.
- `src/localbrain/usage.py` and `usage_queries.py`: Usage Record, immutable price snapshot, cost calculation, Project attribution, and Sessions Dashboard consumers.
- `src/localbrain/queries.py`, `retrieval.py`, `runner.py`, and `workstreams.py`: other major schema consumers and derived payload producers.
- `src/localbrain/templates/base.html`, `src/localbrain/static/`, and `src/localbrain/main.py`: current persistent navigation, locally served client assets, route composition, and server-rendered surface patterns.
- `pyproject.toml`: current Python-only dependency and packaging baseline; no JavaScript package manifest or build contract exists yet.
- `tests/`: synthetic schema setup, persistence fixtures, and behavior-level contract evidence.

## Current Implementation Findings

- The current schema declares 20 ordinary tables and one FTS5 virtual table, but no single document shows all relationships, ownership, rebuildability, or deletion behavior.
- `schema.sql` describes a fresh database while `db.py` adds compatible columns and indexes to existing databases. The effective runtime schema therefore cannot be understood safely from only one file.
- [Project Architecture](../../policies/project/architecture.md) currently groups tables by broad responsibility, but it intentionally does not provide a complete ERD or table and column catalog.
- Some relations are physical foreign keys, while `workstream_links`, `thread_links`, and `checkpoint_resource_refs` use polymorphic `entity_type` and `entity_id` pairs that SQLite cannot validate as ordinary foreign keys.
- Source-derived, user-curated, review-state, operational-history, and fully derived data do not yet have an explicit table-by-table recovery classification. That distinction must be known before destructive cleanup is safe.
- PRD-0002 has already identified one concrete ownership defect: a branch belongs to a Session observation rather than a workspace path. That targeted migration remains owned by PRD-0002 and becomes regression evidence for this wider audit.
- PRD-0004 added `usage_price_snapshots`, `usage_model_prices`, and the table now named `usage_records` after this draft was created. Those tables have distinct immutability, attribution, recalculation, and recovery rules and therefore need their own subject-area owner.
- The persistent `System` navigation currently ends at `Sources`, and the application has no route for schema exploration.
- The current app loads locally served CSS and one JavaScript file without a JavaScript package manifest or frontend dependency pipeline. Mermaid therefore needs an explicit version, lock, packaging, offline-runtime, and asset-freshness contract before a product screen depends on it.

## Product Intent

- Let the owner understand where any stored fact lives, why it exists, what it relates to, and whether it can be rebuilt before approving schema cleanup.
- Make future schema changes reviewable as domain changes instead of isolated DDL edits.
- Avoid repeating the full inventory for every later change: preserve one complete current-state reference while each Feature, Spec, Run, and continuity note describes only its affected delta.
- Let the owner move from a global relationship overview into one subject area and one table without reading raw DDL or leaving the local application.
- Keep implementation truth and human explanation aligned without copying live personal data into the repository.

## Confirmed Scope

### Documentation Ownership

- Keep `src/localbrain/schema.sql` as the canonical fresh-schema implementation truth.
- Keep `src/localbrain/db.py` as the owner of compatible runtime migrations until a later approved migration system replaces it.
- Create `docs/policies/project/data-model.md` as the durable human entry point for persistence ownership, a global ERD, cross-domain relations, lifecycle classes, and links to detailed subject-area documents.
- Place subject-area details under `docs/policies/project/data-model/`. Each detail document owns table purpose, all columns at a human-readable level, keys, constraints, indexes, relationships, producers, consumers, authority, rebuildability, and deletion implications for its domain.
- Use the proposed entry document and subject-area directory as the approved documentation shape; do not collapse the complete catalog into one growing file.
- Link the data-model entry point from [Project Architecture](../../policies/project/architecture.md) and the [Documentation Map](../../README.md) instead of duplicating the full catalog in either file.
- Keep active cleanup findings and decisions in this PRD and its eventual Feature, Spec, Run, and evaluation artifacts. Move only unresolved residual work to the Project Backlog; do not turn the durable data-model document into a speculative cleanup list.

Proposed durable document tree:

```text
docs/policies/project/data-model.md
docs/policies/project/data-model/
├── source-registry-and-scans.md
├── workspace-and-session-activity.md
├── usage-and-cost-records.md
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
| Usage and cost records | `usage_price_snapshots`, `usage_model_prices`, `usage_records` | normalized source observations, immutable pricing evidence, estimated-cost calculation, and frozen Project attribution |
| Local Context corpus | `context_roots`, `context_documents` | user-managed context sources, imported documents, readability, and workspace association |
| Work organization and resources | `workstreams`, `threads`, `workstream_links`, `thread_links`, `local_resources`, `external_resources` | user organization, polymorphic relationships, and canonical linkable resources |
| Review and resume continuity | `suggestions`, `checkpoints`, `checkpoint_resource_refs` | review state, accepted continuity, snapshots, and referenced evidence |
| Maintenance execution | `maintenance_runs` | Task Runner lifecycle, artifacts, budgets, results, and Workstream association |
| Derived retrieval index | `search_index` | rebuildable FTS projection across source-backed and user-managed entities |

### ERD And Catalog Shape

- Author the global and subject-area diagrams in Mermaid syntax so the tracked definition remains text-reviewable and can be rendered in both documentation and the local application.
- Provide a level-zero global ERD showing every schema object and all physical or polymorphic cross-domain relationships without listing every column in one unreadable diagram.
- Provide one focused ERD per subject area with primary keys, foreign keys, uniqueness boundaries, cascade behavior, and important cross-domain edges.
- Provide a complete table and column catalog next to the owning subject-area ERD. Exact SQL syntax remains linked to `schema.sql`; the catalog explains semantic meaning rather than pretending to replace DDL.
- Clearly distinguish physical foreign keys from application-enforced polymorphic relations.
- Record indexes, uniqueness constraints, status or type discriminators, JSON payload fields, timestamp formats, and fresh-schema versus compatible-migration ownership.

### Schema Presentation And Mermaid Contract

- Introduce Mermaid as a version-pinned npm project dependency with a committed lockfile and a reproducible local asset build. Mermaid is a build-time dependency and locally served browser asset, not a required external runtime service.
- Package the approved Mermaid distribution with LocalBrain and load it only from LocalBrain-owned static paths. The `Schema` route must remain usable without a CDN, external editor, telemetry, or network connection.
- Initialize Mermaid through its supported browser API with a restrictive security configuration. Render only application-owned schema definitions; do not accept arbitrary Mermaid source from imported documents, Session content, query parameters, or runtime database rows.
- Derive one schema-only presentation model deterministically from fresh-schema DDL, compatible migrations, runtime indexes, and approved subject metadata. Documentation and the web surface must consume the same Mermaid definitions or deterministic outputs rather than maintain two manually entered ERDs.
- Add an automated parity check that detects object, column, key, constraint, index, or relationship drift between the effective schema and the schema presentation model. Generated presentation data remains a verification and rendering artifact, not a replacement for `schema.sql` or `db.py`.
- Ensure packaged installations contain every Mermaid asset needed by the `Schema` route. `node_modules` and package-manager caches remain untracked and are never runtime requirements.
- Treat a Mermaid load or render failure as a bounded enhancement failure: the server-rendered subject navigation and textual table catalog remain available and no raw implementation error replaces the page.

### In-App Schema Explorer

- Add `Schema` immediately below `Sources` in the persistent `System` navigation and expose the canonical route at `/schema`.
- The default `/schema` view presents the level-zero global ERD, the current baseline summary, and entry points to all eight subject areas.
- A subject-area selection presents that area's focused Mermaid ERD and complete table catalog without mixing unrelated domain details into the same diagram.
- A table selection exposes its purpose, columns, keys, constraints, indexes, physical and application-enforced relations, producers, consumers, authority, lifecycle class, rebuildability, deletion effect, recovery path, and fresh-schema or migration ownership.
- Preserve the selected subject area and optional table in canonical URL state so direct entry, refresh, and browser back and forward restore the same visible and programmatic selection.
- Keep subject navigation and table links as ordinary executable links. Mermaid rendering progressively enhances the schema view and must not become the only path to any catalog information.
- Render schema structure and approved semantic metadata only. The route does not select, aggregate, preview, export, or expose user rows, runtime paths, Session content, document bodies, URLs, credentials, or maintenance artifacts.
- Fit the existing Explorer screen family and shared shell rather than creating a separate visual system. The implementation Feature updates the Design Constitution's stable navigation from seven to eight destinations before adopting the new route.

### Baseline And Incremental Maintenance Contract

- The first approved documentation Feature establishes a complete effective-schema baseline across `schema.sql`, compatible startup migrations, runtime-only indexes, producers, consumers, and synthetic contract tests.
- After that baseline passes, the durable data-model documents remain a complete description of current truth, but each later Feature, Spec, Run, and continuity note records only the affected tables, columns, constraints, indexes, relationships, lifecycle rules, and owner documents.
- A schema change updates the current-state catalog in place only for its affected subject areas. It updates the level-zero global ERD only when a schema object is added or removed, subject ownership changes, or a cross-domain edge changes.
- A focused subject ERD changes only when a relationship, key, uniqueness boundary, cascade rule, or subject ownership visible in that diagram changes. Pure producer, consumer, lifecycle, or semantic changes update the table catalog without redrawing unrelated diagrams.
- Changes to a table, column, constraint, index, discriminator, JSON contract, timestamp rule, producer, consumer, authority, rebuildability, deletion effect, or recovery path must name the owning subject-area document in the approved Feature and Spec and update that document in the same execution boundary.
- New schema objects must declare a subject-area owner before implementation. Removing or moving an object must preserve a migration and recovery record in the execution artifacts while removing stale current-state documentation from its former owner.
- Project Architecture changes only when package ownership, persistence boundaries, or cross-domain behavior changes. The Documentation Map changes only when entry points or subject-area files change.
- Full inventory repetition or a new complete baseline is not required for an isolated delta. Re-baseline only when automated or manual parity checks find unexplained drift, or when the owner approves a material subject-area reorganization.
- Delta history never replaces current truth: `schema.sql` and `db.py` remain executable implementation owners, the data-model documents remain the complete human-readable current state, and planning and execution artifacts preserve why each approved change happened.

### Recovery And Cleanup Classification

- Classify every table as source-derived and rebuildable, user-curated and non-rebuildable, generated review state, operational history, or fully derived projection. Record mixed cases explicitly rather than forcing a false single label.
- Record the producer, major consumers, source of authority, mutation path, deletion effect, and recovery path for every table.
- Audit every table, column, index, and relation as `keep`, `change`, `remove`, or `defer`, with code-consumer evidence and migration risk.
- Check at minimum for unused fields, duplicated facts, wrong ownership, polymorphic referential gaps, inconsistent identifiers, missing or redundant indexes, timestamp inconsistency, status/value constraints, JSON fields hiding stable relational data, and fresh-schema/runtime-migration drift.
- Treat the audit as a decision artifact. Only cleanup items explicitly approved through a later Feature may alter runtime schema or data.

## Excluded Scope

- Reading, exporting, diagramming, or committing rows from the user's runtime database.
- Copying real paths, Session content, document bodies, URLs, credentials, Run artifacts, or other private local values into tracked documentation or fixtures.
- Editing tables, columns, constraints, indexes, migrations, or database rows from the `Schema` screen.
- Adding a SQL console, general database browser, row inspector, or schema mutation controls to the application.
- Loading Mermaid from a CDN or external web editor at runtime, or transmitting the schema or rendered diagram to an external service.
- Replacing the current server-rendered application with a frontend framework or requiring Node.js in order to run the installed LocalBrain server.
- Replacing SQLite, introducing an ORM, or redesigning every table merely to produce a more uniform diagram.
- Performing broad table cleanup before the owner reviews the inventory, recovery classification, consumer evidence, and migration risk.
- Reopening the `workspaces.git_branch` decision already owned by PRD-0002.
- Treating an undocumented or apparently unused column as safe to delete without producer and consumer evidence.

## Uncertainty

- Decide after the audit whether approved cleanup should be one migration Feature or several domain-sized Features; the decision cannot be made safely before cleanup candidates and dependencies are known.
- Decide during the approved Schema Explorer Feature whether the eight-area selector is a desktop rail, tabs, or another existing control pattern. The selected pattern must remain URL-addressable and transform into an in-flow control at narrow widths without changing the eight-area information contract.

## Constraints

- Code and the effective SQLite schema remain implementation truth; documentation must describe them accurately and must not become a second executable schema.
- All tracked diagrams, examples, and tests use synthetic identifiers and paths.
- Cleanup must distinguish rebuildable imported data from non-rebuildable user organization and review decisions before any destructive migration.
- Compatible migrations must preserve stable IDs and relations needed by user-curated Workstreams, Threads, checkpoints, links, and reviewed Suggestions.
- A schema change must update its owning subject-area documentation in the same execution boundary.
- After the initial baseline, child planning and execution artifacts must stay delta-scoped and must not duplicate unrelated subject-area inventories merely to demonstrate completeness.
- Use `docs-content` for the baseline inventory and subject documentation, `foundation-contract` for the schema presentation model and data integrity decisions, `infra-devtool` for the reproducible local Mermaid dependency and asset contract, and `fullstack-product` for the visible `/schema` surface.
- The Schema Explorer Feature declares ordered `data/contract → backend route → frontend rendering and navigation → docs and design-policy parity` surface lanes. Contract evidence passes before dependent lanes are accepted.
- Required Schema Explorer evaluation includes Contract review for schema-only parity and route state, Design review for shell and responsive fidelity, Functional review for end-to-end and no-script behavior, and UX Heuristic plus Interaction review for selection, direct entry, history restoration, focus, asset freshness, and fallback continuity.
- Rendered evaluation uses synthetic schema-only evidence at `1440`, `920`, `700`, and `320` widths and covers global, each subject-area pattern, long identifiers, direct table entry, invalid URL state, Mermaid failure, and no-script fallback.
- Required cleanup evaluation includes Contract review for completeness, source-of-truth parity, recovery classification, migration safety, and stale-assumption checks. Functional review becomes required for any runtime migration.

## Acceptance Envelope

- A reader can start at `docs/policies/project/data-model.md`, see the full database boundary, and reach every subject area without consulting conversation history.
- All 20 ordinary tables and the FTS5 virtual table appear exactly once as a primary subject-area responsibility and remain visible in the global ERD.
- Every table has a complete human-readable column catalog, keys, constraints, indexes, producers, consumers, authority, lifecycle class, rebuildability, deletion effect, and recovery path.
- Physical foreign keys, application-enforced polymorphic relationships, and cross-domain edges are visually and textually distinguishable.
- Fresh-schema DDL and compatible runtime migrations have an explicit parity check, and any current drift is recorded rather than silently normalized.
- The cleanup audit gives every schema object a supported `keep`, `change`, `remove`, or `defer` outcome and identifies migration dependencies before runtime work is approved.
- No runtime database content or machine-specific private value enters tracked documentation, fixtures, diagrams, or evaluation evidence.
- Project Architecture and the Documentation Map link to the durable data-model entry point without duplicating its detailed catalog.
- The durable entry point explains the baseline-and-delta maintenance contract, and a later isolated schema change can name and update only its affected owner documents while leaving unrelated subject areas untouched.
- `System > Schema` opens `/schema`, marks the matching navigation item current, and preserves the existing shared-shell geometry and narrow navigation reachability.
- `/schema` shows the global Mermaid ERD by default and lets the owner reach each of the eight focused subject ERDs and every table catalog through URL-addressable controls and ordinary fallback links.
- The browser loads a pinned, locally packaged Mermaid asset with no runtime network dependency, and an asset or render failure leaves the complete server-rendered textual catalog usable.
- The documentation and web surface are proven against the same effective schema presentation model, and automated parity evidence fails on unexplained object, column, key, constraint, index, or relationship drift.
- Direct entry, refresh, back and forward navigation, keyboard operation, reduced motion, and supported widths preserve a coherent subject and table selection without clipping long technical content.
- The route exposes no runtime rows and offers no schema or database mutation action.
- No cleanup migration begins until the owner approves the relevant post-audit Feature boundary.

## Candidate Features

- [FEAT-0025: Local Mermaid Asset Contract](../feature/feat-0025-local-mermaid-asset-contract.md) (`foundation`, `infra`, `infra-devtool`): establish the pinned npm dependency, lockfile, local static packaging, offline-runtime, security, license, and asset-freshness contract without introducing a Node runtime requirement.
- [FEAT-0026: Data Model Baseline And Subject ERDs](../feature/feat-0026-data-model-baseline-and-subject-erds.md) (`foundation`, `docs`, `docs-content`): create the durable global map, eight subject-area catalogs, recovery classifications, schema/migration parity inventory, and incremental update guide.
- [FEAT-0027: Schema Presentation Contract](../feature/feat-0027-schema-presentation-contract.md) (`foundation`, `data`, `foundation-contract`): produce one deterministic schema-only presentation model and automated parity boundary shared by documentation and product consumers.
- [FEAT-0028: In-App Schema Explorer](../feature/feat-0028-in-app-schema-explorer.md) (`product`, `fullstack`, `fullstack-product`): add `System > Schema`, `/schema`, global and eight-area Mermaid views, table catalogs, URL-restorable selection, responsive behavior, and progressive textual fallback.
- [FEAT-0029: Schema Integrity And Cleanup Decisions](../feature/feat-0029-schema-integrity-and-cleanup-decisions.md) (`foundation`, `data`, `foundation-contract`): trace producers and consumers, classify every object as keep/change/remove/defer, and produce bounded migration candidates with risk evidence.
- [FEAT-0030: Schema Index Maintenance](../feature/feat-0030-schema-index-maintenance.md) (`foundation`, `data`, `foundation-contract`): remove three proven redundant indexes and add three query-supporting indexes without row transformation.
- [FEAT-0031: Usage Attribution CHECK Parity](../feature/feat-0031-usage-attribution-check-parity.md) (`foundation`, `data`, `foundation-contract`): restore the three-value compatible CHECK through backup-backed, exact-value-preserving migration.
- [FEAT-0032: Activity Event Metadata Removal](../feature/feat-0032-activity-event-metadata-removal.md) (`foundation`, `data`, `foundation-contract`): remove the unused generic metadata slot only after an all-null preflight.
- [FEAT-0035: Maintenance Session Usage Bridge](../feature/feat-0035-maintenance-session-usage-bridge.md) (`superseded`): retain its valid Session classification and Run relation constraint repair, but replace its rejected synthetic stream-backed producer.
- [FEAT-0036: Native Maintenance Session And Runner UI Consolidation](../feature/feat-0036-native-maintenance-session-and-runner-ui-consolidation.md) (`product`, `fullstack`, `fullstack-product`): link the persisted native Claude Session, propagate maintenance policy to its children, remove marker creation surfaces, and show the exact shared Runner command.
- [FEAT-0037: Maintenance Run Workstream FK Parity](../feature/feat-0037-maintenance-run-workstream-fk-parity.md) (`foundation`, `data`, `foundation-contract`): restore the compatible optional Workstream-to-Run FK through backup-backed, orphan-refusing, exact-value-preserving migration.
- [FEAT-0052: Schema Diagram Zoom Navigation](../feature/feat-0052-schema-diagram-zoom-navigation.md) (`product`, `frontend`, `frontend-product`, `passed`): add bounded visible controls and modifier-wheel/pinch zoom to the existing local Mermaid Schema panels without changing diagram source or ordinary scrolling.

The human owner approved step-by-step execution in Feature ID order. FEAT-0025 through FEAT-0032 passed. Human review returned FEAT-0035's producer contract and approved FEAT-0036 as its correction, then approved FEAT-0037 to close the final Workstream ownership compatibility boundary.

## Source Map

| Source | Priority | Contribution | Boundary |
| --- | --- | --- | --- |
| Human request | primary | complete ERD visibility, durable placement, subject-area decomposition, locally rendered Schema Explorer, and table cleanup review | does not pre-approve unknown destructive migrations or schema editing from the UI |
| `schema.sql` and `db.py` | implementation truth | fresh DDL, compatible migrations, indexes, foreign keys, defaults, and value shapes | contain no semantic explanation of every producer or consumer |
| Current Python consumers | implementation evidence | actual reads, writes, payloads, joins, deletion paths, and application-enforced relations | usage alone does not prove that a field should remain |
| Project Architecture | durable owner | persistence boundaries and package ownership | links to the detailed data model instead of duplicating it |
| PRD-0002 | approved adjacent contract | Session branch ownership and obsolete workspace branch removal | wider cleanup cannot change that approved direction implicitly |
| PRD-0004 | passed adjacent contract | Usage Record, price snapshot, long-context cost, and immutable Project attribution ownership | the wider audit documents and preserves those contracts unless a later approved Feature changes them |

## Continuity Notes

- `2026-07-17`: created the draft after the workspace-versus-Session branch ownership review exposed the absence of a complete, navigable data-model reference.
- `2026-07-17`: proposed one durable entry document, seven subject-area detail documents, and a separate planning trail for cleanup so implementation truth, durable explanation, and active migration decisions do not overlap.
- `2026-07-18`: reconciled the draft with PRD-0004's three usage and cost tables, expanded the baseline to 20 ordinary tables plus FTS5 across eight subject areas, and confirmed a baseline-then-delta maintenance contract for future schema changes.
- `2026-07-18`: expanded the draft with a locally packaged Mermaid browser dependency and a read-only `System > Schema` explorer for the global model, eight subject areas, and URL-restorable table detail; the revised boundary remains `draft` pending human approval.
- `2026-07-18`: the human owner approved the revised PRD boundary and requested Feature decomposition; FEAT-0025 through FEAT-0029 were created as draft review targets, while cleanup migration Features remain gated on the completed audit and a later owner decision.
- `2026-07-18`: the human owner approved sequential Feature execution; FEAT-0025 passed with the reproducible local Mermaid asset, strict adapter, packaging, privacy, and runtime-independence contract.
- `2026-07-18`: FEAT-0026 passed with the complete 20-table plus FTS5 baseline, eight subject catalogs, nine local Mermaid renders, automated parity, lifecycle/recovery ownership, and delta maintenance guide.
- `2026-07-18`: FEAT-0027 passed with the deterministic package-owned v1 schema presentation, exact schema/semantic transformation, bounded loader validation, and installed-wheel evidence; FEAT-0028 is next.
- `2026-07-18`: FEAT-0028 passed with `System > Schema`, global/eight-area/table exploration, strict local Mermaid, URL/history/focus continuity, progressive textual fallback, exact supported-width containment, and installed-package evidence; FEAT-0029 is next.
- `2026-07-18`: FEAT-0029 passed with 329 exhaustive object decisions, five evidence-backed cleanup candidate groups, two canonical deferrals, synthetic index and legacy-upgrade proof, corrected current-truth presentation, 108 tests, package/privacy evidence, and an intact owner gate. PRD-0003 is `passed`; no cleanup migration Feature was created.
- `2026-07-19`: owner-approved FEAT-0030 passed after removing three redundant named indexes and adding three query-prefix indexes with row-preservation, failure-preflight, idempotency, and query-plan evidence.
- `2026-07-19`: owner-approved FEAT-0031 passed after adding the missing compatible Usage attribution CHECK through non-overwriting backup, fail-closed shape/value preflight, exact full-row comparison, rollback, and idempotency evidence. At that point, boundaries 2 and 4 remained unapproved.
- `2026-07-19`: the owner approved boundary 2 as FEAT-0032 after confirming `metadata_json` was an unused initial extension hook; the migration is constrained to all-null legacy state and exact retained-event preservation.
- `2026-07-19`: the owner separately approved the Session-to-Run relation and Usage bridge as FEAT-0035 after confirming that `maintenance_runs` remains the execution ledger; this did not approve the older `maintenance_runs.workstream_id` compatibility candidate.
- `2026-07-19`: FEAT-0032 passed after actual and synthetic all-null preflight, exact retained-value comparison, non-null refusal, generated schema/audit parity, full tests, and privacy checks. At that point, boundary 4 was the only remaining unapproved migration.
- `2026-07-19`: FEAT-0035 passed after enforcing Session class/index policy and a unique optional Run FK, adding the Runner stream Usage producer, preserving 171 actual Sessions exactly, backfilling two metadata-only Run Sessions, passing 139 tests, and refusing to invent Usage for missing historical stream files.
- `2026-07-19`: final owner review rejected FEAT-0035's `--no-session-persistence` and synthetic stream-backed producer. FEAT-0036 supersedes that part with the persisted native Claude Session, keeps the valid schema repair, removes the redundant marker UI/API, and exposes the exact Runner command plus stdin boundary.
- `2026-07-19`: FEAT-0036 passed with native Claude Session ownership, maintenance child propagation, marker-surface removal, exact command visibility, and complete contract/design/functional/interaction evidence.
- `2026-07-19`: the owner approved boundary 4 after confirming that `maintenance_runs.workstream_id` records the Workstream from which the maintenance execution was started. FEAT-0037 passed with exact preservation of six actual Run rows and 15 Suggestion origin links, zero orphans, validated backup, FK/integrity checks, and idempotent startup.
- `2026-07-24`: growing ERDs exposed a readability gap in the passed Schema Explorer. The owner approved follow-up FEAT-0052 for modifier-wheel/pinch zoom and visible controls; straight ER edge routing remains outside the Feature because Mermaid 11.16.0 does not expose an ER curve option.
- `2026-07-24`: FEAT-0052 passed with bounded `10%–300%` controls, pointer-anchored modifier zoom, unchanged ordinary scrolling, replacement binding, package/schema/privacy guards, and 260 passing tests. Direct rendered input replay remains a non-blocking first-use check because the required browser control was unavailable.
- `2026-07-24`: the owner moved official ELK companion-layout evaluation and possible orthogonal ER routing into draft [PRD-0008](prd-0008-connected-atlassian-validation-and-schema-erd-routing.md). PRD-0003 and FEAT-0052 remain passed; no renderer dependency or routing behavior changed here.
