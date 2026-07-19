# FEAT-0029 Schema Integrity And Cleanup Decisions

## Result

- Audit result: `complete`; all four owner-reviewed cleanup boundaries are implemented, including FEAT-0037's Maintenance Run Workstream FK parity repair.
- Inventory source: validated `localbrain.schema-presentation.v1` manifest, SHA-256 `709ddc54ddb0988e7de7d068dfbc586323e179091d409704b20b7c08c7220e67`.
- Coverage: 328 independently resolved objects: 21 tables/virtual tables, 244 columns, 20 explicit named indexes, 20 physical relations, and 23 application relations.
- Dispositions: `keep 273`, `change 0`, `remove 0`, `defer 55`.
- Runtime outcome: FEAT-0030 applied the row-free index boundary, FEAT-0031 restored the compatible Usage attribution CHECK, FEAT-0032 removed the all-null generic Activity Event metadata slot, FEAT-0035 enforced Session classification/indexing vocabularies plus the unique Run-to-Maintenance-Session relation, and FEAT-0037 restored the compatible Workstream FK while preserving retained rows.
- Approval effect: the original boundaries 1 through 4 are implemented. FEAT-0035 separately closed the Session/Run bridge, and only the two explicitly deferred audit groups remain open.

The explicit decision source is [audit-0029-schema-decisions.json](audit-0029-schema-decisions.json). The generated [resolved object ledger](audit-0029-schema-object-ledger.md) lists every object, its one disposition, object-specific rationale, risk, evidence register, and candidate or defer route.

## Audit Boundary

- `schema.sql`, `db.py`, runtime Python modules, synthetic tests, FEAT-0026 owner docs, and the FEAT-0027 manifest were inspected without opening the configured runtime database or reading user rows.
- SQLite FTS shadow tables are internal consequences of `search_index`; uniqueness autoindexes are internal consequences of primary/unique constraints. They are not independently owned application objects, but their coverage was inspected when judging redundant named indexes.
- Static use establishes known producers and consumers, not correctness by itself. A removal requires authority, lifecycle, rebuildability, deletion, recovery, and regression evidence in addition to absence of reads.
- Table evidence is inherited by each owned column, index, and outgoing relation only because the resolved ledger names that evidence group and retains an object-specific semantic contract and rationale.

## Decision Summary

### Keep

- All 21 current table identities remain necessary and resolve to `keep`; none is a table-removal candidate.
- All 23 current application relations remain. Heterogeneous Workstream/Thread/checkpoint links intentionally preserve unresolved historical identity, live link insertion validates targets, and source/search projections have explicit cleanup and rebuild paths. The former application-only Maintenance Run → Session identity is now represented by the enforced physical Session FK and is not counted twice.
- Integer local IDs and text source-stable/Run IDs remain separated by authority. Polymorphic IDs stay text because they cross several target families.
- Denormalized Session counts remain rebuildable summary fields. Usage capability JSON, Suggestion payload JSON, and Maintenance Run JSON remain versioned or heterogeneous evidence that has no stable relational-query owner today.
- Existing physical CASCADE, SET NULL, and RESTRICT rules remain; no destructive Workstream, Thread, checkpoint, Suggestion review, or frozen Usage attribution boundary is approved.

### Change Or Remove Candidates

No active change or remove candidate remains. FEAT-0030 indexes, FEAT-0031 Usage attribution, FEAT-0032 Activity Events, and FEAT-0037 Maintenance ownership are current keep contracts.

### Deferred Decisions

| Defer group | Objects | Blocking dependency | Canonical owner |
| --- | ---: | --- | --- |
| `canonical-timestamp-contract` | 43 columns | Approve UTC storage form, parser inputs, precision, timezone rendering, legacy preservation, and comparison semantics before rewriting mixed source/Python/SQLite text. | [Project Backlog](../project/backlog.md#schema-audit-timestamp-contract) |
| `closed-vocabulary-constraints` | 12 columns | Approve extensibility, state-machine values, invalid legacy-row handling, FTS enforcement, and table-rebuild sequencing before adding checks. Session class and index policy were split out and completed by FEAT-0035. | [Project Backlog](../project/backlog.md#schema-audit-closed-vocabularies) |

The timestamp group is high-risk where lexical SQL comparisons or non-rebuildable chronology are involved. In particular, Workstream latest activity combines source timestamp text, SQLite `datetime()` output, and Python ISO resource updates; the audit does not guess at a migration target without a durable format contract.

## Required Smell Checks

| Dimension | Finding |
| --- | --- |
| Unused fields | FEAT-0032 removed the one supported unused field, `activity_events.metadata_json`; remaining low-read fields retain explicit provenance, presentation, recovery, or operational-history roles. |
| Duplicated facts | Session counts remain rebuildable summary caches; capability and Run JSON remain detailed evidence rather than a second authoritative entity set. |
| Wrong ownership | No subject move. All 21 schema objects retain exactly one FEAT-0026 owner. |
| Polymorphic referential gaps | All 23 application edges remain intentional. Closed entity-type enforcement is deferred; target deletion may preserve historical unresolved identity by contract. |
| Identifier inconsistencies | Integer local identities and text stable/source identities are intentional. No ID conversion is proposed. |
| Missing/redundant indexes | FEAT-0030 removed the three redundant names only after UNIQUE-autoindex preflight and added the three query-prefix indexes selected by synthetic EXPLAIN. Low-cardinality Session indexes remain because current filters/orderings use them. |
| Timestamp inconsistency | Confirmed across source strings, Python timezone-aware ISO strings, and SQLite defaults; all affected time columns are deferred to one canonical contract. |
| Status/type constraints | Existing Session role, Usage state, numeric, priced-cost, and attribution checks remain. FEAT-0031 resolved Usage attribution and FEAT-0035 resolved Session class/index policy; twelve wider code-bounded fields remain deferred. |
| Stable data hidden in JSON | No stable independently queried entity set was found. Empty event metadata is removed; heterogeneous/versioned evidence remains JSON. |
| Deletion behavior | Physical rules match fresh and upgraded ownership. FEAT-0037 makes future Workstream deletion null only the optional Run association while preserving Run, Session, Suggestion, and artifact history. |
| Fresh/compatible drift | Object, column, named-index, Usage attribution, Session/Run, and Maintenance ownership contracts match after startup. Only the explicitly deferred timestamp-column metadata differences remain. |

## Proposed Migration Feature Boundaries

The original review groups now have explicit execution state. The order prevents a low-risk structural change from being coupled to preserved historical state.

1. Index-only cleanup and additions: implemented by FEAT-0030 with no row transformation.
2. Source-derived Activity Event cleanup: implemented by FEAT-0032 after an all-null runtime preflight and exact retained-value comparison.
3. Usage attribution constraint parity: implemented by FEAT-0031 with backup, invalid-value refusal, and exact full-row preservation.
4. Maintenance ownership parity: implemented by FEAT-0037 with a validated non-overwriting backup, orphan refusal, exact full-Run preservation, dependent-link comparison, and Workstream `SET NULL` behavior.

FEAT-0035 is a separately approved Session integrity boundary: it restores `session_class` and `index_policy` CHECK parity and adds the unique optional `sessions.maintenance_run_id` FK. FEAT-0037 independently closes the Workstream-to-Run direction.

Timestamp normalization and the wider closed-vocabulary work remain backlog decisions and must not be silently absorbed into these boundaries. Source-derived tables and non-rebuildable organization/review tables are not combined in one destructive migration.

## Verification Evidence

- The audit checker fails on manifest digest or count drift, missing/extra table decisions, unknown overrides, duplicate identities, invalid dispositions, incomplete candidate safety fields, missing evidence/test links, stale generated ledger bytes, or missing defer backlog anchors.
- FEAT-0030 synthetic upgrades prove all three redundant named indexes are removed only after UNIQUE-autoindex coverage, every affected row is unchanged, and repeated migration is idempotent.
- Synthetic EXPLAIN selects each of the three current query-supporting indexes for its named query prefix.
- FEAT-0031 synthetic upgrades prove non-overwritten `quick_check` backup, exact row/ID/column-metadata preservation, invalid-value refusal, bidirectional full-row equality, foreign-key validity, index restoration, and idempotent restart.
- FEAT-0032 synthetic upgrades prove fresh omission, all-null-only compatible removal, non-null refusal before mutation, exact retained-event equality, and idempotent restart; actual runtime verification compared count and a retained-value digest before and after without recording private values here.
- FEAT-0035 synthetic upgrades prove Session class/index policy CHECKs, unique FK cardinality and linked-row shape, backup non-overwrite, invalid/orphan/duplicate refusal, exact child-row preservation, Runner stream Usage reconciliation, and Dashboard/retrieval boundaries.
- FEAT-0037 synthetic upgrades prove fresh/compatible FK parity, backup non-overwrite, exact Run and dependent-link preservation, orphan/unexpected-shape refusal, future Workstream `SET NULL`, and idempotency. The actual local database retained all six Run rows and 15 Suggestion origin links exactly, had zero orphans, and passed backup, FK, and integrity checks without recording private values here.
- A synthetic schema-only fixture keeps data-repair migrations disabled while proving nullable/no-default compatible timestamp additions; normal startup now closes the approved Usage and Maintenance constraint gaps.
- Current-truth docs and the derived Schema presentation state the remaining timestamp metadata differences without exposing cleanup decisions in the Schema Explorer.
- The current full repository, data-model/presentation/audit, Mermaid, privacy, and runtime-preservation results are recorded in RUN-20260719-42 and its Contract/Functional evaluations; the original no-runtime-change audit evidence remains in RUN-20260718-34.

## Owner Review Gate

The owner approved boundaries 1 through 4 as FEAT-0030 through FEAT-0032 and FEAT-0037 on `2026-07-19`, and separately approved the FEAT-0035/FEAT-0036 Maintenance Session and native Runner path. No active cleanup migration remains authorized by this audit; either deferred group requires a new explicit Feature approval.
