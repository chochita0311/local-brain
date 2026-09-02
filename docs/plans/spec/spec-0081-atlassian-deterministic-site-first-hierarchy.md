# SPEC-0081: Atlassian Deterministic Site-First Hierarchy

## Metadata

- ID: `spec-0081`
- Status: `approved`
- Run ID: `run-20260901-91`
- Attempt: `1`
- Parent Feature: [FEAT-0081](../feature/feat-0081-atlassian-deterministic-site-first-hierarchy.md)
- Parent PRD: [PRD-0015](../prd/prd-0015-atlassian-site-first-url-organization.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: `contract/backend → Explorer presentation → durable owners`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-09-01`
- Updated: `2026-09-01`

## Source Set

- Human request: domain-first Project/Space hierarchy, deterministic URL
  handling, and no visible Item jargon.
- Parent Feature and PRD: FEAT-0081 and PRD-0015.
- Golden sources: current Explorer, passed FEAT-0077 through FEAT-0080,
  Product, Source Memory, Design Constitution, and Interaction Evaluation.

## Implementation Goal

- Implement a deterministic local admission and hierarchy projection whose
  primary structural node is Site domain and whose child grouping never
  requires hidden inference or persisted Space mutation.

## In-Scope Behavior

- Split URL parsing from configured-scope admission. Strict local recognition
  returns service, normalized URL/domain, Jira key or Confluence Page ID, and
  optional URL container descriptor.
- Resolver semantics are covered by the versioned Atlassian evidence extractor.
  Jira descriptor is the uppercase key before the final `-digits`. Confluence
  descriptor is the strict UTF-8 percent-decoded-once, NFKC-normalized,
  non-empty segment immediately after `spaces` only when the same path contains
  a following `pages/{digits}` segment. Descriptor length is `1..300`; control
  characters, `/`, `\\`, dot segments, invalid decoding, or bounds produce no
  descriptor. The canonical descriptor is a raw normalized value; ordinary
  query encoding happens exactly once when the server emits a URL.
- During Sync, an accepted strict locator with no service-qualified admission
  mapping resolves Site by normalized domain. Exactly one existing Site is
  reused for both Jira and Wiki; more than one is `ambiguous-site`; none calls
  the existing local Site registration contract for its normalized base URL.
  It then creates or reuses the link exactly as existing configured Sync does.
  No binding or Source Instance is invented.
- At action start, existing Site/binding choices remain frozen and
  service-qualified only for admission/access selection. A locally created
  domain Site is staged inside the current source savepoint, becomes available
  to later candidates in that source, and enters the action-wide resolver only
  after that source commits. Rollback cannot leave a cached nonexistent Site.
- Explicit Sync Document currentness uses content/source fingerprint, the
  current evidence extractor/resolver version, and successful status. It does
  not use the registered Site/service fingerprint. The authoritative source
  scanner alone uses registered scope as a freshness input. Explicit Sync may
  retain the action-start mapping fingerprint in the shared scan-row field for
  diagnostics, but it does not compare that value for reuse. The resolver
  version changes for this Feature so existing rows are re-evaluated once;
  after that, unchanged explicit Sync is read-only reuse.
- URL admission remains bounded by current source/URL caps and source savepoints.
- Browse assigns every eligible row one structural descriptor:
  - persisted: `space_id` with persisted name/key and service;
  - URL: null `space_id` plus deterministic descriptor and service;
  - unassigned: neither persisted nor URL descriptor.
- Hierarchy projection groups Site first. Child identity is persisted
  `space:{id}` or URL `url:{service}:{normalized-key}`; unassigned is one
  Site-local node. Equal labels remain separate when service or provenance
  differs and use compact cues.
- Site selection under All carries `site_id` without forcing a service.
  A persisted child carries `space_id` and uses that row's stored service; a URL
  child carries its service-qualified `structural_scope`; unassigned under All
  intersects both services. Jira/Wiki view supplies its service filter.
- The existing single-valued `structural_scope` request field is extended from
  compatibility value `unclassified` to also accept
  `url:jira:<PROJECT_KEY>` and `url:confluence:<normalized-space-segment>`.
  Its total decoded length is at most 320 code points. Jira suffix is
  `[A-Z][A-Z0-9_]*` and at most 300 code points. Confluence suffix is exactly
  the validated descriptor above and at most 300 code points. Unknown prefix,
  empty suffix, invalid Unicode/value, repeated parameter, or service mismatch
  is a bounded `400`. Server-authored query output follows the existing fixed
  Explorer field order and form encoding exactly once.
- `structural_scope` remains in the existing canonical selection, clear,
  return, partial, back/forward, detail, edit, and Refresh-return allowlist.
  Unsafe `return_to` falls back to the Explorer root.
- `space_id` and `structural_scope` are mutually exclusive. A
  `structural_scope` requires explicit `site_id`; a known `space_id` resolves
  and canonicalizes to its persisted owner Site, and server-emitted Space URLs
  include both owner `site_id` and `space_id`. `view=all` accepts Site,
  persisted Space, URL descriptor, and unassigned structure. A Jira/Wiki view
  rejects a URL descriptor owned by the other service.
- A selected URL descriptor must exist on at least one current canonical URL
  for that Site/service before structure filters; a selected unassigned node
  must likewise exist before query/advanced filters. Known selected nodes may
  be projected at count zero after filtering, while forged or stale values are
  bounded invalid state.
- Active structure labels use `domain / child`; the hierarchy root label is
  `모든 도메인` in every top service scope.
- Grouping derives from the one `url_role='canonical'` URL owned by each link.
  Alias URLs and evidence URLs never choose or merge a hierarchy group. A
  missing or invalid canonical URL descriptor yields `소속 미확인`.
- Ordinary product copy maps Jira-only context to `링크`, Wiki-only context to
  `문서`, and mixed context to `링크/문서`. Explorer, Add, preview, full
  detail, Sync, Connections, Refresh, global Search, and browser live copy are
  in scope. Physical schema, code/API/route/data-selector names,
  value-registry keys, diagnostics, and historical planning artifacts remain
  unchanged.

## Out-Of-Scope Behavior

- Persisting URL descriptors, creating Space rows, or changing `space_id`.
- Any schema, value-registry, physical Item identity, or access-binding change.
- Merging a URL descriptor into a persisted Space solely because labels match.
- Parsing generic URLs, Jira projects, Confluence Space-only URLs, REST URLs,
  titles, content, prose, or key-only text.
- Remote reads, capability checks, models, embeddings, or Refresh execution.

## Affected Surfaces

- URL recognition and local evidence Sync
- Atlassian browse filters/read model and route URL helpers
- Explorer hierarchy template and small native service/provenance cues
- Sync/result/search/detail user-facing terminology
- Product, Design Constitution, Source Memory, plans, and generated catalog
- focused and full regression tests

## Surface Lanes

- Contract/backend:
  - dependency order: first
  - implementation responsibility: recognizer, admission, descriptor, filters,
    hierarchy/read model, canonical URLs
  - validation evidence: deterministic fixtures, SQL traces, route tests
- Explorer presentation:
  - dependency order: after read-model contract
  - implementation responsibility: domain-first DOM, labels, cues, responsive
    containment, progressive route behavior
  - validation evidence: UI contract and Chrome four-width matrix
- Durable owners:
  - dependency order: with finalized contract
  - implementation responsibility: current owner rules and generated indexes
  - validation evidence: data-model/design/catalog checks

## State And Interaction Contract

- Existing hierarchy/list/detail scroll owners and selection controller remain.
- Replacing the service-parent DOM must not alter list/detail identity, query,
  filters, or browser history semantics. Site/child transitions keep the
  existing contract of clearing current selection and result-local scroll;
  Sync fragment replacement preserves current selection and scroll exactly.
- Compact hierarchy disclosure retains DOM/visual/focus order and active-node
  reachability. Equal labels always include a non-color-only type cue.
- Empty, zero-count explicitly selected persisted Space, URL child, and
  unassigned states remain bounded and truthful.

## Data And Contract Assumptions

- URL container descriptors are derived values owned by the read model and are
  not local or remote Space identity.
- Same logical input means same strict URLs, normalized source locations, Site
  state, evidence extractor/resolver version, and filters. Database IDs,
  timestamps, and receipt tokens are not reproducibility owners.
- Existing persisted containment always takes precedence over URL grouping.
- Source evidence remains Session/Document provenance, not hierarchy.

## Contract Surfaces

- Producer expectations: Sync emits stable Site/link/evidence and no Space
  writes; Browse emits stable Site-first node descriptors.
- Consumer expectations: route/template/JS use only emitted descriptors and
  retain ordinary fallback links.
- Generated artifacts: plan catalog, schema/data-model dictionaries only if
  their source owners change.
- Source-of-truth owner: Product, Design Constitution, Atlassian Source Memory.
- Stale-assumption check: service-first hierarchy, explicit-service structural
  URLs, configured-domain skip, `Unclassified`, and visible Item copy.

## Required Evaluators

- Contract: identity, admission, no-Space-write, owner docs, routes.
- Design: native hierarchy density, cues, four-width containment.
- Functional: empty/repeat Sync, filters/counts, history/focus/regressions.
- UX heuristic: orientation, terminology, mixed-service ambiguity, empty/error.

## Acceptance Mapping

- Empty Sync → strict admission tests with zero existing Atlassian rows.
- Same-domain mixed-service Sync → one Site reused by Jira and Wiki, with
  service-qualified links and no binding.
- Transaction publication → same-source duplicate reuse, later-source
  post-commit reuse, and forced late-source rollback that exposes no partial row
  or cached Site ID to the following source.
- Deterministic grouping → pure parser fixtures plus fresh/repeat graph parity.
- Domain-first tree → Browse/template/UI-contract tests and Chrome.
- No persisted inference → SQL trace forbidding Space/space_id writes.
- Terminology → rendered-template assertions.
- Continuity → selected/filtered/direct/back-forward/compact browser checks.

## Evaluation Focus

- Prevent service duplication, label collisions, stale structural parameters,
  accidental Space authority, or empty-Sync inventory pollution from unsupported
  URLs.

## Open Blockers

- None.

## Continuity Notes

- `2026-09-01`: approved Attempt 1 with a read-only URL descriptor rather than
  persisted containment, preserving deterministic Sync and provenance.
