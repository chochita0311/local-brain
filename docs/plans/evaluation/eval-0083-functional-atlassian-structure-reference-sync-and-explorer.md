# EVAL-0083 Functional: Atlassian Structure Reference Sync And Explorer

## Metadata

- ID: `eval-0083-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260901-93`
- Attempt: `1`
- Feature: [FEAT-0083](../feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md)
- Spec: [SPEC-0083](../spec/spec-0083-atlassian-structure-reference-sync-and-explorer.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `persistence/Sync -> Explorer/Search read model -> presentation/interaction`
- Evidence Coverage: `complete`
- Created: `2026-09-01`

## Checks And Evidence

- The additive schema keeps structure references, their canonical/alias safe
  locators, and their Session/Document evidence in three independent owners
  with the required service/kind, identity, source-shape, cardinality, FK, and
  index constraints (`src/localbrain/schema.sql:745-836`,
  `src/localbrain/schema.sql:1025-1045`). Fresh startup, compatible startup,
  and fail-closed pre-existing-shape validation are implemented at
  `src/localbrain/db.py:247-300` and exercised by
  `tests/test_atlassian_structure_references.py:233-383`.
- Stable Site/service/kind/identity reuse, first-canonical plus bounded alias
  ownership, collision rejection, deterministic evidence keys, Document
  replacement, derived hint consensus/availability/lifecycle, bounded preview,
  archive, FTS removal, and same-ID reactivation are owned by
  `src/localbrain/atlassian_structure_references.py:90-768`. Identity, alias,
  hint conflict, exact-repeat read-only behavior, archive/reactivation, preview
  caps, and collision fixtures cover those transitions at
  `tests/test_atlassian_structure_references.py:384-559`.
- Explicit local Sync classifies each bounded locator once, treats Site-only as
  report-only, admits structure references without Item/Space authority, keeps
  Session evidence merge-only, replaces complete Document-owned evidence, and
  reprojects every affected reference before source commit
  (`src/localbrain/atlassian_evidence_sync.py:799-1039`,
  `src/localbrain/atlassian_evidence_sync.py:1042-1203`). Action-wide distinct
  report units, per-source publication after commit, frozen source population,
  source isolation, identity-collision failure, and nonblocking single-flight
  are preserved at `src/localbrain/atlassian_evidence_sync.py:1206-1423`.
  Fresh/repeat/change/overflow/unavailable/rollback/collision/report/zero-I/O
  coverage is exercised by `tests/test_atlassian_evidence_sync.py:657-759`,
  `tests/test_atlassian_evidence_sync.py:761-1262`, and
  `tests/test_atlassian_evidence_sync.py:1302-1989`.
- All four Session/Document owner-removal branches now snapshot affected
  reference IDs before the evidence cascade and rebuild their FTS projection
  after owner deletion (`src/localbrain/ingest/scanner.py:371-406`,
  `src/localbrain/ingest/scanner.py:409-447`,
  `src/localbrain/ingest/scanner.py:522-607`,
  `src/localbrain/ingest/scanner.py:1424-1440`,
  `src/localbrain/ingest/scanner.py:1703-1720`). Direct regressions prove stale
  Session, empty Session, file Document, and folder Document removal all leave
  the stable reference archived and remove its active Search projection
  (`tests/test_atlassian_structure_references.py:561-684`).
- Explorer exact identity/alias/generated-label matching, Item-only filter
  exclusion, active/unavailable reference admission, archived exclusion,
  polymorphic ordering, Site/child split counts, selected-zero behavior, and
  shared-but-not-merged URL groups are implemented at
  `src/localbrain/atlassian_browse.py:772-884` and
  `src/localbrain/atlassian_browse.py:1245-1490`. Global Atlassian Search uses
  the bounded structure-reference projection and direct detail route without
  source text or Item-owned authority (`src/localbrain/atlassian_browse.py:2629-2749`).
  Reference-only hierarchy/count parity, direct reload, exact Search, archived
  exclusion, and post-Sync regrouping are covered by
  `tests/test_atlassian_browse.py:2117-2331`.
- Preview and full detail share the bounded reference read model
  (`src/localbrain/atlassian_browse.py:2279-2309`). Explorer return
  sanitization rejects malformed, repeated, cross-service, and unsafe state and
  canonically regroups or archives a selected reference after Sync
  (`src/localbrain/main.py:668-761`). The direct route now server-renders an
  unknown reference as a bounded `404` with its sanitized Explorer return and
  no writes, while known and archived references render `200`
  (`src/localbrain/main.py:1985-2016`,
  `src/localbrain/templates/atlassian-reference-missing.html:1-15`,
  `tests/test_atlassian_browse.py:2168-2303`).
- The strict zero-input Sync request, verified receipt, ordinary `303`, and
  enhanced JSON return share the same canonical post-work path and bounded
  report (`src/localbrain/main.py:1275-1314`,
  `src/localbrain/main.py:1496-1536`,
  `tests/test_atlassian_sync_routes.py:132-377`). The shared controller retains
  one modal/sheet owner, selection generation guard, independent hierarchy,
  list, preview, and page scroll owners, five server-authored Sync fragments,
  and canonical `history.replaceState` without a new history entry
  (`src/localbrain/static/atlassian.js:860-1053`,
  `src/localbrain/static/atlassian.js:1075-1419`). UI-contract coverage pins
  fallback, focus/history/modal, reference copy/count, and responsive family
  behavior at `tests/test_ui_contract.py:1628-1770`.
- Chrome functional evidence used the synthetic RapidBoard target carrying
  `projectKey=JPDI` and `rapidView=37746`. Empty state became one Site, one
  `JPDI` URL group, and reference `37746` with
  both Session and Document evidence; repeat Sync created no rows. Search,
  reference preview/direct detail, unknown/out-of-scope, archive/reactivation,
  and post-Sync canonical return all remained coherent. The enhanced path used
  `replaceState` without a history increment; the no-script path completed
  POST -> `303` -> verified receipt and a `320px` direct-detail return. Network
  traffic was limited to local `POST /atlassian/sync` and local Explorer GETs,
  with zero console errors.
- Independent current-tree verification passed the focused blocker regression
  matrix `38/38`, the broader Atlassian/UI matrix `193/193`, generated
  data-model/schema/value/audit checks `23/23`, and the full repository suite
  `480/480`. Python compilation, JavaScript syntax, repository privacy over
  `835` candidate files, and `git diff --check` also passed. The only runtime
  warning was the existing Starlette `TemplateResponse` deprecation notice.

## Findings

- None.

## Route

- Next action: `pass`
