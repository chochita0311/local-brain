# SPEC-0083: Atlassian Structure Reference Sync And Explorer

## Metadata

- ID: `spec-0083`
- Status: `approved`
- Run ID: `run-20260901-93`
- Attempt: `1`
- Parent Feature: [FEAT-0083](../feature/feat-0083-atlassian-structure-reference-sync-and-explorer.md)
- Parent PRD: [PRD-0016](../prd/prd-0016-atlassian-standard-url-recognition.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: `persistence/Sync -> Explorer/Search read model -> presentation/interaction -> durable owners`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Source Set

- Human approval: execute the already approved sequential FEAT-0082 foundation
  and FEAT-0083 durable product outcome through completion.
- Parent boundary: PRD-0016 and FEAT-0083.
- Passed dependency: FEAT-0082, SPEC-0082, RUN-92 Attempt 1, and both complete
  Contract and Functional `PASS` evaluations.
- Passed regressions: FEAT-0077 through FEAT-0081, especially SPEC-0080 local
  evidence Sync, SPEC-0081 Site-first Explorer, and SPEC-0082 semantic locator.
- Design source: [Atlassian Structure Reference Design Plan](../design/atlassian-structure-reference-plan.md),
  `screen-alignment` extend mode, Design Constitution, Design Evaluation, and
  Interaction Evaluation.
- Durable owners: Product, Architecture, Privacy, Atlassian Source Memory,
  Workspace/Session Activity, work-organization/resource ownership, schema
  presentation, and value dictionaries.

## Implementation Goal

- Persist locally observed FEAT-0082 `structure` descriptors as stable,
  separately owned structure references and source evidence, reconcile them
  through the existing explicit local Sync action, and expose one honest
  Site-first Explorer/Search/list/preview/detail lifecycle without granting
  Item, persisted Space, access, remote-state, or local-edit authority.

## Durable Identity And Schema Contract

### Physical Owners

- Add exactly three fresh and compatible tables:
  `atlassian_structure_references`, `atlassian_structure_reference_urls`, and
  `atlassian_structure_reference_evidence`.
- A structure reference owns an independent positive SQLite integer `id`. It is
  not an `external_resources` or `atlassian_items` subtype and is not eligible
  for Item local notes, attention, Topic/Tag assignments, Workstream/Thread
  links, Refresh, Connections, or persisted Space relations in this Feature.
- `atlassian_structure_references` has:
  - `id INTEGER PRIMARY KEY`;
  - `site_id INTEGER NOT NULL` referencing `atlassian_sites.id` with
    `ON DELETE RESTRICT`;
  - `service TEXT NOT NULL`, checked to `jira` or `confluence`;
  - `reference_kind TEXT NOT NULL`, checked to `jira_project`, `jira_board`,
    `jira_filter`, `jira_dashboard`, `jira_service_portal`,
    `jira_service_project`, or `confluence_space`;
  - `reference_identity TEXT NOT NULL`, `1..300` code points;
  - `created_at` and `updated_at`, both non-null timestamps;
  - `UNIQUE(site_id, service, reference_kind, reference_identity)` and
    `UNIQUE(id, site_id)` for composite child ownership;
  - a service/kind check requiring every `jira_*` kind to use `jira` and only
    `confluence_space` to use `confluence`.
- `atlassian_structure_reference_urls` has:
  - `id INTEGER PRIMARY KEY`, required `reference_id` and `site_id`;
  - a composite cascading FK `(reference_id, site_id)` to the reference owner;
  - `url_role` checked to `canonical` or `alias`;
  - one non-empty privacy-safe `safe_locator_url` no longer than `8,000` code
    points, plus non-null first/last-observed timestamps;
  - `UNIQUE(site_id, safe_locator_url)` and one partial unique canonical row per
    reference;
  - indexes by `(reference_id, url_role)` and canonical reference identity.
- The first successfully committed candidate for a new semantic identity owns
  that reference's canonical safe locator. A later distinct FEAT-0082 safe
  locator for the same semantic identity is retained as an alias; it never
  replaces the canonical row or creates another reference. Exact alias reuse is
  read-only except for a successful changed-source observation that already
  owns an evidence write. URL rows survive evidence cleanup and therefore keep
  direct navigation stable while the reference is archived.
- A safe locator that already belongs to a different Site/reference identity is
  an `identity-collision` source failure. No producer reassigns or merges it.
  Only FEAT-0082 output may enter this table; raw query, JQL, fragment,
  credentials, and arbitrary source spelling never do.
- `atlassian_structure_reference_evidence` has:
  - `id INTEGER PRIMARY KEY` and a required cascading `reference_id` FK;
  - exactly one source owner: Session plus required `source_path` and
    `source_event_id`, or Context Document with those two fields null;
  - `source_channel` checked to `visible_text` or `approved_tool_result`;
  - positive `source_line` and `url_ordinal`, optional bounded `observed_at`;
  - `safe_locator_url TEXT NOT NULL` bounded to `8,000`, optional normalized
    `container_hint` bounded to `300`, current extractor version, one unique
    64-character `evidence_key`, and first/last/updated timestamps;
  - the same Session path `8,000` and source-shape checks as Item evidence;
  - indexes by reference/date, Session location, and Document location.
- Structure evidence persists only the safe locator supplied by FEAT-0082.
  Unlike authoritative Document Item evidence, it never stores the raw
  query-bearing observed spelling; source identity and source location preserve
  provenance without retaining forbidden URL material.

### Compatible Startup And Versioning

- Fresh `schema.sql` and an older compatible database both gain the three
  additive empty tables and indexes through ordinary idempotent startup. No
  existing table is rebuilt, no row is backfilled or reinterpreted, and no
  destructive-migration backup is required for this additive change.
- Startup tests assert exact columns, checks, FKs, unique constraints, partial
  canonical index, supporting indexes, `PRAGMA foreign_key_check`, and unchanged
  pre-existing Site/Space/Item/evidence rows. An unexpected pre-existing table
  with one of the new canonical names fails closed rather than being silently
  accepted.
- Bump `localbrain.atlassian-evidence.v3` exactly once to
  `localbrain.atlassian-evidence.v4`. FEAT-0082 locator and Session-reference
  versions remain `localbrain.atlassian-locator.v1` and
  `localbrain.session-reference.v3`.
- The value registry, schema presentation, Atlassian Source Memory catalog/ERD,
  and schema-cleanup audit own the new physical values and generated parity.

## Sync Admission And Evidence Lifecycle

### Candidate Admission

- The existing frozen Session/Document source population, `100`-row source
  batches, per-Session retained projection caps, Document `64 KiB` chunks,
  `8,000`-code-point carry, first-`500` URL evidence cap, source order, and
  process-local single-flight remain exactly as SPEC-0080.
- Every bounded candidate is classified once by the passed FEAT-0082 locator.
  Existing `item` admission remains unchanged. `structure` enters the new
  reference producer. `site` is report-only. `unsupported` and `unsafe` retain
  their fixed skip meanings.
- A `structure` candidate creates or reuses exactly one normalized-domain Site
  through the passed FEAT-0081 resolver and then one exact
  Site/service/kind/identity reference. Service-qualified action-start mappings
  win; otherwise exactly one domain Site is reused, none is registered locally,
  and duplicate domain owners are `ambiguous-site`.
- A `site` candidate creates no Site, reference, URL, evidence, Space, Item,
  binding, or other row. It increments only the bounded Site-only report unit.
- A structure candidate never creates or mutates `atlassian_spaces`, writes
  `space_id`, creates an Item/External Resource, copies Add registration
  consequences, or changes any remote/local Item owner.

### Per-Source Reconciliation

- Each Session or Document keeps one source transaction/savepoint. A newly
  created Site/reference/URL is source-local until commit and is published to
  the action resolver only after commit. Rollback removes all source writes and
  publishes no cached identity to later sources.
- Session structure evidence is merge-only. It consumes only eligible retained
  `target_kind=url` rows and the passed admitted evidence kinds; it never opens
  source files, advances or cleans `session_reference_scans`, deletes prior
  structure evidence, or overwrites another source location.
- A complete eligible Document scan owns bounded replacement for both Item and
  structure evidence from that Document. It inserts/reuses the deterministic
  first-`500` candidates, removes obsolete Document-owned evidence in both
  tables after EOF, and advances the shared Document scan to evidence v4.
  Overflow remains a truthful partial source outcome while permitting that
  complete bounded replacement. A failed/incomplete/unavailable pass removes
  nothing and retains its prior evidence.
- Evidence identity hashes reference ID, source owner and stable location,
  source channel, safe locator, normalized hint, and evidence version. Exact
  unchanged repeats perform no timestamp-only reference, URL, or evidence
  write. A changed safe locator/hint at one Document location replaces that
  location through complete-source reconciliation without changing reference
  identity.
- Reference and safe-locator rows are stable local memory after first committed
  creation. Removing the last evidence row does not delete them. The reference
  becomes derived `archived`; a later exact semantic candidate reuses the same
  ID and aliases and becomes active again.
- Session/Document deletion may cascade only its evidence. It cannot delete the
  stable reference or URL rows. Explicit destructive purge is out of scope.

### Hint Consensus And Availability

- Presentation grouping reads all currently retained evidence for one
  reference. It collects distinct non-null normalized `container_hint` values:
  exactly one distinct value groups the reference under that service-qualified
  URL child; zero or two-or-more distinct values place it under
  `소속 미확인`. Unhinted evidence neither creates nor conflicts with the one
  non-null consensus value. Complete Document cleanup may remove a conflict and
  deterministically restore the remaining single-hint group.
- Grouping never writes the consensus back as Space/containment authority.
  Canonical and alias URL spelling do not override evidence consensus.
- Lifecycle/availability is derived at read time:
  - `archived`: zero retained evidence rows;
  - `available`: at least one retained evidence owner is still an eligible
    current local Session projection or enabled/readable/ready Context Document;
  - `unavailable`: evidence remains but no evidence owner is currently eligible
    and locally available.
- One available source keeps a multiply supported reference `available`; an
  unavailable peer remains visible in the bounded evidence list. No remote
  freshness, content coverage, access readiness, or model result participates.
- Active and unavailable references remain in the default Explorer/Search
  population. Archived references are excluded there but remain reachable by
  direct reference detail and reusable by later Sync.

## Report, Receipt, And Request Contract

- Keep SPEC-0080 `status`, `sources`, `items`, Item `evidence`,
  `candidate_skips`, `scope_limits`, and per-source units unchanged. Extend the
  exact report with:
  - `structure_references`: action-wide disjoint distinct reference-ID counts
    `new` and `reused`;
  - `structure_evidence`: distinct evidence-key counts `new`, `reused`, and
    `removed`;
  - `site_only`: candidate-occurrence count after bounded parsing, not a unique
    domain/service/family count.
- Every source outcome adds `new_structure_references`,
  `reused_structure_references`, `new_structure_evidence`,
  `reused_structure_evidence`, `removed_structure_evidence`, and `site_only`.
  Aggregate reference IDs are distinct action-wide and intentionally are not
  the sum of overlapping per-source reuse counts.
- `site` no longer increments `unsupported_locator`; it increments `site_only`
  and is a valid complete candidate. Structure success is not a skip.
- Add fixed reason `identity-collision`; every existing reason retains its
  meaning. No reason or receipt exposes identity, domain, URL, hint, source
  path/title/text, or raw exception.
- Completion/no-change copy includes Item and reference units. A complete
  report is “no new local evidence” only when Item new/removed evidence,
  structure-reference new/removed evidence, and new identities are all zero.
  Site-only recognition remains visible but is not described as a created row.
- `POST /atlassian/sync`, zero execution inputs, `8 KiB` form cap, `4,000`
  return cap, repeated/unknown-field `422`, nonblocking process lock, statuses,
  HTTP codes, five-minute/32-entry verified receipt store, and full-batch retry
  remain SPEC-0080 contracts.
- Ordinary POST returns `303` to the post-work canonical return path plus the
  verified receipt. Enhanced POST returns
  `{ "report": <exact-report>, "return_to": <post-work-canonical-path> }`;
  `return_to` contains no receipt and is the same binding used by ordinary PRG.

## Explorer Read Model And Search Contract

### Polymorphic Eligible Population

- Browse produces one row discriminator, stable key, and ID:
  `item:<external_resource_id>` or `reference:<reference_id>`. Templates and
  client code may retain historical `item` names only inside Item-specific
  implementation owners; shared selection code must branch on the discriminator.
- Item eligibility remains unchanged. A reference is eligible when it is not
  archived, matches the selected service/Site/structural scope, and matches the
  query contract below.
- Coverage, freshness, attention, Topic, Tag, Source Instance, Item type,
  persisted Space, and Workstream filters are Item-owned. Any non-empty one of
  those fields excludes references rather than inventing a default reference
  value. Service, Site, URL-derived/unclassified structure, and query are the
  only shared reference filters.
- Empty-query ordering is pinned Items first, then all other rows by their
  owning `updated_at DESC`, discriminator `item` before `reference`, and numeric
  ID descending. Query ordering is match rank, discriminator `item` before
  `reference`, then numeric ID ascending.
- Root, Site, and child nodes expose `item_count`, `reference_count`, and their
  sum. UI omits a zero category, keeps link/document and `구조 참조` labels
  separate, and makes the node's total equal adjacent list membership.
- A reference with one hint consensus shares the same service-qualified URL
  child as null-`space_id` Items with that descriptor. `소속 미확인` is likewise
  shared. A persisted Space remains a distinct child even when its label equals
  a URL group; no label-based merge occurs.
- A reference-only Site/group is emitted because it has one eligible row.
  A report-only `site` candidate never emits a zero-count Site or child.
- Existing selected-zero persisted Space/Item-backed structure behavior remains
  Item-only. Archived references create no zero branch.

### Explorer Query And Global Search

- Explorer exact retrieval admits a reference at identity rank `0` for an exact
  normalized `reference_identity` or exact normalized canonical/alias safe URL.
  A contiguous NFKC-casefolded token phrase over the generated family label plus
  identity is rank `1`. Evidence source identity/text, raw URL spelling,
  `container_hint`, Site/Space label, and unavailable source content are not
  query owners. Excerpts are generated only from the winning safe field and
  remain at most `240` code points.
- Global `/search` gains `entity_type=atlassian_structure_reference` and only
  active/unavailable reference identity, generated family label, and safe URL
  projection. It adds no source text, hint, remote content, note, classification,
  or organization text.
- One deterministic search projection per active reference is rebuilt when its
  identity/URL/evidence-active state changes; archived references have no FTS
  rows. The result routes to `/atlassian/references/{id}` and shows service,
  domain, explicit reference-kind copy, `URL 기준 · Local evidence`, derived
  availability, and matched role.
- Global Search service and Site filters admit references. Every Item-only
  diagnostic/advanced filter, including Source Instance, persisted Space, Item
  type, coverage, freshness, attention, Topic, Tag, or Workstream, excludes
  references. Existing Item/Search behavior and non-Atlassian source results
  remain unchanged.

## Selection, Preview, Detail, And Return Contract

- Explorer URL state adds one optional positive `reference` field. `item` and
  `reference` are mutually exclusive, single-valued, ASCII-decimal, and bounded
  to SQLite integer range. Repeated, both-present, zero, overflow, or malformed
  selection is bounded `400` on GET and rejected by return sanitization.
- Reference rows use the ordinary direct link
  `/atlassian/references/{reference_id}?return_to=<safe-selection-url>` and an
  enhanced selection URL carrying `reference={id}`. Direct links remain fully
  executable without JavaScript.
- Selected projection mirrors the passed Item preview state split without
  widening scope: an unknown reference ID returns the bounded missing state; a
  known archived reference returns the archived state; and a known non-archived
  reference excluded by the current service, Site, structural scope, query, or
  Item-only filter returns the bounded out-of-scope state. The latter does not
  inject the row into the list, clear the excluding filter, or widen the
  current population.
- Selected-reference preview returns only:
  kind/identity, service, Site domain, generated family label, canonical safe
  locator, derived group/provenance, availability/lifecycle, evidence total,
  and the first five evidence rows. Evidence is ordered by effective observed/
  last-observed time descending and stable evidence ID descending and exposes
  only source kind/local ID, source channel/location, safe locator, optional
  hint, source availability, and bounded timestamps.
- The preview and full detail use the fixed authority copy:
  `Session/Local Context에서 URL 구조만 확인했습니다. Jira 링크/Wiki 문서·등록된 Project/Space·원격 조회 결과가 아닙니다.`
  They expose no Item coverage/freshness/attention, remote facts/body, local
  note, Topic/Tag, Workstream/Thread membership, Refresh readiness, binding, or
  connected state.
- `/atlassian/references/{id}` renders the same server-authored bounded read
  model. An unknown ID returns a bounded reference-not-found `404` with safe
  Explorer return. An archived known ID returns `200`, states that supporting
  local evidence is no longer retained, and preserves the safe locator plus
  history identity; it remains absent from ordinary Explorer/Search.
- The canonical external-open action uses the fixed canonical safe locator.
  Alias URLs remain inspectable only as a bounded total and exact-search owner;
  the preview does not render an unbounded alias list.
- Structural-scope validation includes active Item and reference rows. A normal
  forged/stale group remains bounded `400`. Post-Sync return sanitization has a
  narrow selected-reference rule: if the reference remains active—meaning any
  non-archived reference, whether derived `available` or `unavailable`—and its
  hint consensus moved, canonicalize Site/service/group to its current owner
  while preserving compatible query/advanced filters and selection; if it
  became archived, clear structural scope but preserve the reference selection
  at the Explorer root. Unknown or cross-service identity falls back to
  `/atlassian`.
- Ordinary scope/query/filter changes clear both selection fields and result
  scroll. Selecting either row preserves service, structure, query, filters,
  hierarchy disclosure, history, and practical list position. Close restores
  its initiating row or the results heading; back/forward and direct entry use
  the same owner rules.

## Enhanced And No-Script Interaction Contract

- The existing outer preview/dialog/scrim/inert owner remains one shared
  component. A polymorphic selection request uses one controller generation
  guard, but the partial response states whether it is Item or reference and
  never lets a stale response replace the latest selection.
- Structure-reference selection patches only the server-authored preview
  content. The outer modal/sheet owner, close control, inert/background lock,
  selected row, URL/history, hierarchy/list DOM, and scroll owners remain.
- Enhanced Sync keeps the existing four named Explorer fragments and adds one
  bounded selected-reference preview-content fragment. Item preview remains
  untouched. If a reference is selected, its evidence/availability/archive
  state patches in place; focused content restores to the nearest surviving
  control or preview heading, and compact modal ownership does not change.
- Enhanced Sync applies the returned canonical `return_to` with
  `history.replaceState` only when post-work reference grouping/archive state
  requires it. It adds no history entry. Current query, compatible filters,
  selected reference, hierarchy/list/detail scroll, compact disclosure, and
  open Add/detail owner otherwise remain stable.
- Server Jinja receipt rendering and enhanced JavaScript use the exact same
  report fields, zero/change test, count units, Site-only meaning, per-source
  records, recovery, and announcement copy. `busy` restores continuity without
  inventory refresh or false warning.
- No-script Sync retains POST→303→verified receipt and server-authored updated
  hierarchy/list/detail. No-script row selection reaches direct detail, whose
  back link preserves the sanitized selection state. Exact pixel/focus/modal
  restoration remains enhancement-only; every action and return stays reachable.

## Presentation And Responsive Contract

- The ordinary copy matrix is:
  - row type: `Jira Project 참조`, `Jira 보드 참조`, `Jira 필터 참조`,
    `Jira 대시보드 참조`, `Jira 서비스 포털 참조`,
    `Jira 서비스 Project 참조`, or `Wiki Space 참조`;
  - provenance: `구조 참조` and `URL 기준 · Local evidence`;
  - only-reference count: `구조 참조 N`;
  - mixed count: service-appropriate `링크/문서 N · 구조 참조 M` with zero
    category omitted;
  - Site-only Sync count: `도메인/서비스만 확인 N`;
  - unsupported: `지원하지 않는 Atlassian URL`.
- `All`, `Jira`, `Wiki`, `모든 도메인`, Site-first grouping, action order
  `Sync -> Add -> More`, and current hierarchy/list/detail reading order remain.
  No new primary action, search mode, modal family, hierarchy depth, token, or
  breakpoint is introduced.
- At `1440`, retain three adjacent hierarchy/list/preview regions. At `920`,
  use the current compact hierarchy and right drawer. At `700` and `320`, keep
  list-first one-column flow and the existing full-width sheet/direct-detail
  fallback. Long identities, labels, split counts, provenance, and safe URLs
  wrap inside their owners with zero page horizontal overflow and `40px`
  minimum interactive targets.
- DOM/keyboard order remains heading/actions, Sync status, service scopes,
  query/filters, hierarchy, list, preview. Exactly one hierarchy copy is visible
  and focusable per breakpoint. Reduced motion and semantic focus/status tokens
  remain inherited.

## Zero Hidden I/O And Authority Separation

- Schema migration, Sync, Browse, Explorer query, global Search, preview,
  direct detail, return sanitization, alias projection, availability, and FTS
  rebuild may read/write only bounded LocalBrain SQLite state and pure locator
  helpers.
- Calls to filesystem/source readers, Session/Context scanners, Provider/MCP,
  capabilities, runner/executor, connected discovery, Refresh, maintenance Run,
  model, embedding, or network code are exactly zero.
- Add remains its passed one-URL Item/Project/Space path and never creates or
  converts a structure reference. Connections and Refresh neither list nor
  target structure references. Equal persisted-Space/reference labels remain
  separate and neither side mutates the other.

## Out-Of-Scope Behavior

- Structure-reference local note, attention, archive edit, Topic/Tag,
  Workstream/Thread/checkpoint relation, or user-authored title.
- Item/External Resource conversion, persisted Project/Space inference,
  `space_id`, remote identity/content/freshness, binding, capability, or Refresh.
- Raw observed query/JQL/fragment retention, source excerpts, title/content
  inference, unbounded aliases/evidence in a read model, or source-file access.
- Manual structure-reference Add, per-reference retry/approval, purge UI,
  remote confirmation, another search mode, another hierarchy level, or AI.

## Affected Surfaces

- `src/localbrain/schema.sql`, compatible DB startup, schema presentation and
  value registry
- new structure-reference identity/evidence owner module
- `src/localbrain/atlassian_evidence_sync.py` and evidence version owner
- `src/localbrain/atlassian_browse.py`, `queries.py`, `main.py`
- Atlassian Explorer/reference detail/global Search templates, shared
  controller, semantic styles
- focused schema/Sync/browse/search/detail/route/UI/browser tests
- Product, Architecture, Privacy, Atlassian Source Memory, Design Constitution
  only where the implemented stable outcome requires owner parity

## Surface Lanes

- Persistence/Sync lane:
  - dependency order: first
  - responsibility: additive schema, stable identity/aliases/evidence,
    source-isolated reconciliation, availability, report/receipt, zero I/O
  - evaluator ownership: contract, functional
- Explorer/Search read-model lane:
  - dependency order: after persistence
  - responsibility: polymorphic population, filters/query/order/counts,
    grouping, selection/return, FTS/global result route, bounded detail
  - evaluator ownership: contract, functional
- Presentation/interaction lane:
  - dependency order: after read model
  - responsibility: copy, row/preview/detail, Sync parity, focus/history/scroll,
    no-script and four-width composition
  - evaluator ownership: design, functional, ux-heuristic
- Durable-owner lane:
  - dependency order: with final implemented contract
  - responsibility: data-model, product/privacy/architecture/design and
    generated artifacts without rewriting passed history
  - evaluator ownership: contract

## Required Evaluators

- Contract: schema/compatible startup, identity/aliases, evidence lifecycle,
  hint/availability derivation, report units, request/return, Search entity,
  bounds, zero-I/O, and owner parity.
- Design: Site-first mixed composition, reference/Space distinction, copy/count
  wrapping, reference preview/detail, Sync states, and four widths.
- Functional: fresh/repeat/change/remove/unavailable/rollback/collision,
  filters/search/counts, direct/enhanced/no-script, stale grouping, action
  separation, and full regressions.
- UX heuristic: local-evidence authority clarity, Item/Space distinction,
  orientation, focus/history/scroll recovery, narrow density, and failure paths.

## Acceptance Mapping

- Stable semantic identity -> fresh/repeat/alias/RapidBoard/conflicting-hint and
  cross-Site collision SQL graph tests.
- Source authority -> Session merge-only, Document replace, source deletion,
  unavailable retention, last-evidence archive, reactivation, and rollback
  overlay tests.
- Separate report -> exact aggregate/per-source JSON, Site-only denominator,
  server/enhanced copy parity, receipt binding, busy and no-change tests.
- Explorer -> only-reference/mixed/equal-label/unassigned/conflict/filter/query
  hierarchy/list/count parity and selected-zero regression.
- Search/detail -> exact identity/alias, generated label, global entity route,
  Item-only filter exclusion, evidence cap, unavailable/archive/missing and
  known-but-out-of-scope selected states with no population widening.
- Continuity -> item/reference mutual exclusion, safe return, post-Sync group
  move for available/unavailable references, archive normalization, partial
  selection, back/forward, rapid selection, focus and independent scroll owners.
- Chrome -> JavaScript-enabled matrix at `1440`, `920`, `700`, and `320`;
  no-script Sync/selection/detail at `1440` and `320`; breakpoint crossings
  `921 <-> 920` and `701 <-> 700`; warm-cache assets, failed partial fallback,
  modal/inert, reduced motion, `40px` targets, accessibility tree/Lighthouse,
  console errors, and zero horizontal overflow.

## Evaluation Focus

- Never let a safe URL spelling or grouping hint become identity/containment.
- Never count a Site-only candidate as a created reference or selectable node.
- Never let Item-only advanced state silently grant or fabricate reference axes.
- Never leave a selected reference preview or return URL stale after Sync moves
  its evidence-derived group or archives its last evidence.
- Never widen local Sync/Search/detail into source, remote, model, Refresh, or
  Connections work.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-01`: created only after FEAT-0082 and RUN-92 passed both required
  evaluators. The approved FEAT-0083 product boundary is now executable under
  RUN-93 Attempt 1.
- `2026-09-01`: locked separate retained reference/URL/evidence owners,
  evidence-derived availability/archive state, Item-only edit/filter exclusion,
  Site-only report treatment, mutually exclusive selection, global Search
  projection, and progressive Explorer/detail continuity without new authority.
