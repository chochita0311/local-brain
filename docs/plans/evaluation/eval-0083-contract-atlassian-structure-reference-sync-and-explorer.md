# EVAL-0083 Contract: Atlassian Structure Reference Sync And Explorer

## Metadata

- ID: `eval-0083-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260901-93`
- Attempt: `1`
- Feature: [FEAT-0083](../feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md)
- Spec: [SPEC-0083](../spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `persistence/Sync; Explorer/Search read model; durable owners`
- Evidence Coverage: `complete`
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Scope

- Evaluated additive schema and compatible startup, semantic reference identity
  and safe aliases, source-separated evidence and lifecycle, explicit local Sync
  atomicity/reporting, FTS cleanup, Explorer/Search/list/preview/detail state,
  safe return handling, action separation, zero hidden I/O, privacy, and durable
  owner parity against PRD-0016, FEAT-0083, SPEC-0083, and RUN-93 Attempt 1.

## Checks And Evidence

- The implemented boundary matches the approved outcome rather than granting
  Item, persisted Space, access, or remote authority. PRD-0016 assigns durable
  reference/evidence and Explorer/Search projection to FEAT-0083; FEAT-0083 fixes
  per-source reconciliation, split counts, lifecycle, and action separation; and
  SPEC-0083 plus RUN-93 enumerate the same contract and validation surfaces
  (`docs/plans/prd/prd-0016-atlassian-standard-url-recognition.md:42-78,104-134`;
  `docs/plans/feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md:17-64,81-119,163-177`;
  `docs/plans/spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md:35-115,469-500`;
  `docs/plans/run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md:32-70,122-153`).
- Fresh schema owns exactly the separate reference, safe-URL, and evidence tables
  with Site/service/kind/identity uniqueness, canonical/alias and evidence-source
  checks, cascading child ownership, and six explicit indexes. Compatible startup
  compares complete table, foreign-key, SQL, and index signatures to the canonical
  in-memory graph and fails closed on partial or incompatible owners
  (`src/localbrain/schema.sql:745-835,1025-1045`;
  `src/localbrain/db.py:53-64,77-128,228-300`;
  `tests/test_atlassian_structure_references.py:233-383`).
- Semantic identity is the exact Site/service/reference-kind/reference-identity
  tuple. The first safe locator remains canonical, variants become aliases, a
  cross-owner safe-URL collision fails without reassignment, and deterministic
  evidence keys preserve exact Session/Document provenance. Exact unchanged
  reuse performs no observation or timestamp write under
  `localbrain.atlassian-evidence.v4`; lifecycle, availability, hint consensus,
  bounded five-row evidence, and active-only FTS projection are all derived from
  the evidence owner (`src/localbrain/ingest/common.py:9-10`;
  `src/localbrain/atlassian_structure_references.py:90-204,243-376,421-488,519-786`;
  `tests/test_atlassian_structure_references.py:384-560`).
- Explicit Sync admits a `structure` descriptor only through the independent
  reference owner while a `site` descriptor remains report-only. Session input
  consumes the persisted projection and is merge-only; a complete changed
  Document owns bounded replacement; unavailable sources retain evidence. The
  exact aggregate/per-source report separates Items, references, reference
  evidence, Site-only candidates, skips, limits, and outcomes. Frozen source
  populations, one savepoint per source, publication only after commit,
  identity-collision isolation, and non-blocking single flight preserve atomicity
  (`src/localbrain/atlassian_evidence_sync.py:97-203,332-451,799-893,896-1203,1206-1308,1342-1423`;
  `tests/test_atlassian_evidence_sync.py:761-1262,1414-1482,1686-1775`;
  `tests/test_atlassian_sync_routes.py:132-360`).
- Every scanner path that removes an owning Session or Local Context Document now
  snapshots the affected reference IDs before the cascading parent delete and
  reprojects each FTS owner afterward. Direct regressions cover stale Session,
  empty Session, file-document, and folder-document removal and prove the stable
  reference becomes archived while its active Search row disappears
  (`src/localbrain/ingest/scanner.py:371-406,409-447,567-602,1424-1440,1703-1716`;
  `tests/test_atlassian_structure_references.py:561-684`).
- Explorer forms one polymorphic eligible population, keeps link/document and
  structure-reference counts separate, applies structural scope after that
  denominator, and preserves reference-only, mixed, conflict, unavailable,
  archived, filtered, and selected-zero behavior. Exact identity/alias/generated
  label query, Item-only advanced-filter exclusion, bounded preview/detail, and
  active-only shared Search use the same read-only reference owner
  (`src/localbrain/atlassian_browse.py:152-327,772-884,977-1142,1220-1497,2279-2309,2629-2704`;
  `tests/test_atlassian_browse.py:2117-2305`).
- Item and reference selections are mutually exclusive and independently bounded.
  Explorer return paths reject external, repeated, invalid, or cross-service
  state; post-Sync return canonicalization follows a moved active grouping and
  clears structural scope for an archived reference without losing its direct
  selection. An unknown direct reference renders a bounded server-authored `404`
  with a sanitized Explorer return and performs no write
  (`src/localbrain/main.py:558-761,992-1243,1282-1535,1985-2016`;
  `src/localbrain/templates/atlassian-reference-missing.html:1-14`;
  `tests/test_atlassian_browse.py:2168-2305`).
- Manual Add retains only its passed Issue/Page/Project/Space subset and rejects
  Board, Filter, Dashboard, and JSM reference kinds. Connections, Refresh, local
  edits, classifications, and Workstream organization never consume a structure
  reference as an Item. Product, Architecture, Privacy, Atlassian Source Memory,
  the generated value dictionary, and the Design Constitution own the same
  local-only, privacy-safe, read-only authority and availability vocabulary
  (`src/localbrain/atlassian_registration.py:97-155`;
  `tests/test_atlassian_registration.py:235-264`;
  `docs/policies/project/product.md:140-169,248-330`;
  `docs/policies/project/architecture.md:160-203,363-399`;
  `docs/policies/project/privacy-and-data.md:80-116`;
  `docs/policies/project/data-model/atlassian-source-memory.md:458-532`;
  `docs/policies/project/data-model/value-dictionaries/atlassian-source-memory.md:8-38,104-118,216-230`;
  `docs/policies/design/design-constitution.md:519-521,616-664`).
- The supplied Chrome execution receipt began with an empty synthetic Atlassian
  registry and one Session plus one Local Context RapidBoard locator. Sync created
  one domain Site, one `jira_board` identity `37746`, the URL-derived `JPDI`
  grouping, and two bounded provenance rows. A second Sync was idempotent, the
  canonical safe locator was reduced to the approved RapidBoard identity/hint
  projection, and the browser observed no remote request. This corroborates the
  persisted-only candidate, identity, grouping, evidence, and zero-external-I/O
  contract exercised by the focused tests
  (`tests/test_atlassian_evidence_sync.py:245-393,1013-1203,1264-1301`;
  `tests/test_atlassian_browse.py:2117-2305`).
- Independent verification passed `162/162` focused structure-reference, Sync,
  Browse, route, registration, Refresh, schema, value-registry, and UI tests;
  `41/41` UI-contract tests; and the final repository regression receipt
  `480/480`. Python compile, JavaScript syntax, `git diff --check`, repository
  privacy over `836` candidate files, generated value registry and nine
  dictionaries, plan-artifact catalog pre-evaluation check, schema presentation,
  cleanup audit, data-model owner, and Mermaid gates passed. The owner receipts
  report `41` ordinary tables plus one
  FTS5 object, `54` physical foreign keys, `44` explicit indexes, `9` subject
  owners, `9` Mermaid diagrams, and `623` cleanup objects with `keep=518`,
  `change=0`, `remove=0`, and `defer=105`.

## Findings

- None.

## Current Route

- Current route: `PASS`.
