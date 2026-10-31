# Atlassian

This contract owns local Explorer behavior, URL admission, optional access, evidence Sync and approved remote Refresh. The [Maintenance Task Runner](../operations/claude-task-runner.md) owns process execution; the data-model subjects own durable rows.

## Atlassian Explorer, Add, Connections, Sync, And Refresh

### Scope, Terminology, And Retrieval

Atlassian is one local Explorer over persisted Jira links, Confluence
documents, and non-archived URL-derived structure references. The physical
data model retains `Item` as its internal stable identity term for links and
documents, but ordinary product copy uses `링크` in Jira-only context,
`문서` in Wiki-only context, and `링크/문서` in mixed context; structure
references retain their separate family and provenance labels. The
Explorer opens in `All`, with reversible `Jira` and user-facing `Wiki` scopes;
`Wiki` maps to stored `confluence` identity and does not rename persistence
vocabulary. One surface-local query owns Atlassian retrieval while the route is
active, and the shared-header global query is not simultaneously visible.
Local Browse and query work never call a model, provider, capability, or
maintenance runner.

The Explorer's exact query trims surrounding whitespace and treats an empty
value as unfiltered local Browse. A complete case-normalized Jira key or stored
remote/Page ID, or an exactly normalized canonical/alias URL, is an identity
match. Other text uses NFKC-plus-casefolded Unicode word tokens and matches only
when the complete token phrase is contiguous inside one owned value: a local
or approved remote title, one approved remote-metadata scalar, indexed
normalized content, the local note, one Topic name/description, or one Tag
name. Separate values never combine. Identity results precede title results,
which precede other owned-value results; ties use ascending stable local Item
ID. Evidence/source text, opaque payloads, Workstream names, Site/Space labels,
and unavailable remote bodies are not query owners. The shared cross-source
Search retains separately owned local FTS behavior. The current
structure-reference projection adds one independently typed result from reference
identity, generated family label, and privacy-safe locator only. It does not
index source text, hint, remote content, Item local memory, or organization
state, and the surface is not relabeled as Atlassian exact retrieval.

### Site-First Hierarchy And Counts

Every service scope projects the hierarchy under the `모든 도메인` root by
normalized Site domain first; Service is never a hierarchy parent. `All` keeps Jira and Wiki records under
the same canonical Site, while the top `Jira` and `Wiki` scopes reversibly
filter that population. Each Site has only three kinds of child structure:

- a persisted Jira project or Confluence Space, whose `space_id`, stored
  service, key, and display name remain authoritative;
- for a record with null `space_id`, a read-only container hint derived from
  exactly one canonical URL when a strict Jira Issue URL exposes its project
  key or a strict Confluence Page URL exposes its Space path segment; or
- one Site-local `소속 미확인` child when neither persisted containment nor
  an eligible canonical-URL hint exists.

Alias URLs, evidence URLs, titles, body text, nearby prose, and source paths do
not own hierarchy grouping. A URL hint never creates a Space, writes
`space_id`, merges into a same-labeled persisted Space, or represents remote
confirmation. Persisted containment always wins. Equal child labels remain
separate when service or persisted-versus-derived provenance differs and use a
compact non-color-only cue. The hierarchy does not claim a nested Confluence
Page or Jira issue tree. Its adjacent inventory keeps stable internal Item
identity, Site or Space context, and independent coverage, freshness,
attention, classification, organization, and provenance cues without
compressing those axes into one status. Identical keys on different Site
domains remain distinct. Archived records stay outside the default population
but remain recoverable through explicit state or direct detail.

Hierarchy counts and the adjacent list share one eligible population after
service, exact query, archived-default, and advanced filters. The current Site,
persisted child, URL child, or `소속 미확인` constraint applies only after
that population is formed, so the active node count equals list membership and
sibling counts stay navigable. In `All`, selecting only a Site intersects both
services; a persisted child carries its stored service, a URL child carries its
descriptor service, and `소속 미확인` intersects both services for that Site.
Jira/Wiki scopes apply their service before the same structure. Root and sibling
projections remain backed by eligible records. A narrow action-integration
exception keeps a valid explicitly selected persisted Project/Space or known
canonical-URL child, or a previously valid Site-local `소속 미확인`
selection reachable at count zero after filters: only that active node and its
Site ancestor are projected, the adjacent list remains empty, and no remote
discovery or new record is implied. The one advanced disclosure
contains only coverage, freshness, attention, Topic, Tag, and Workstream.
Source Instance remains a Connections or diagnostic concern, and internal Item
type derives from service.

### URL State, Selection, And Detail

The Explorer has one URL-backed state contract:

| Transition | Preserve | Reset or normalize |
| --- | --- | --- |
| open Atlassian without explicit state | shell and navigation continuity | `All`, hierarchy root, empty query, no advanced filters, no link/document or structure-reference selection |
| change `All / Jira / Wiki` scope | query and compatible advanced filters | structural scope, selected entry, result-local scroll, and unsupported hierarchy disclosure |
| change Site/child/`소속 미확인` scope | current top service scope, query, advanced filters, and reachable hierarchy orientation; `All` remains `All` while child service stays in persisted or descriptor identity | selected entry and result-local scroll |
| change query or advanced filters | service and structural scope plus entered URL-backed values | selected entry and result-local scroll |
| select a link/document or structure reference | service, structure, query, filters, hierarchy disclosure, and practical list position | only the mutually exclusive detail identity and its pane state advance |
| refresh or direct entry | every valid explicit URL-backed value | omitted values use defaults; forged, stale, repeated, mismatched, or otherwise invalid structure fails with a bounded visible validation state rather than hidden normalization |
| browser back or forward | the historical service, structure, query, filters, selection, and supported pane orientation | focus and each scroll owner restore to the nearest reachable historical anchor |
| cross a responsive breakpoint | eligible service, structure, query, filters, selection, and practical list position | unsupported persistent panes become explicit disclosures, sheets, or sequential destinations |

Wide Explorer state keeps hierarchy, list, and read-first detail adjacent with
intentional independent scroll ownership. Compact state keeps the list primary
and moves hierarchy and detail into bounded disclosures. Narrow state is
list-first and exposes hierarchy, filters, and detail as explicit sheets or
sequential destinations. Full-detail link/document routes remain the
direct-entry, local-edit, and no-script fallback; the separate read-only
structure-reference detail route provides the equivalent direct-entry and
no-script recovery without acquiring Item edit authority. Remote facts/content,
user-owned notes and
Topic/Tag classification, Session/Local Context evidence, Workstream/Thread
membership, and maintenance history remain separate authority regions.

One optional positive local internal Item ID or one optional positive local
structure-reference ID owns the selected Explorer state; the two identities
are mutually exclusive. Direct and enhanced selection use the same
server-authored, read-only preview contract for the selected entity, and the
enhanced response replaces only that preview without rebuilding hierarchy or
inventory. Unknown identities produce a bounded missing state. Known records
outside the active scope retain concise identity and explain that scope instead
of exposing unrelated detail; archived references remain a separately named
bounded direct-history state. Invalid structural combinations remain visible
local validation errors. Selection never starts a provider, model, capability,
source scan, Refresh, or maintenance action, and Setup never accepts selection
state. Both full-detail families remain executable without JavaScript; only
the link/document family owns local editing.

### Static Locator Admission

Static URL recognition and product admission are separate authorities. One
shared, pure Atlassian locator contract classifies bounded standard Jira and
Confluence URL families as `item`, `structure`, `site`, `unsupported`, or
`unsafe`. Recognized results carry service, family, normalized domain/base, and
a privacy-minimized safe locator. An Item carries exact Issue/Page identity; a
structure result carries a stable reference kind/identity and optional
non-authoritative Project/Space hint; a Site result carries no selectable
identity. Path or approved-query Item identity wins over structure/site, and an
exact structure identity wins over the family root. The safe locator removes
fragment, JQL, and arbitrary query while retaining only canonical allowlisted
identity projection: for example RapidBoard retains positive `rapidView` and
may retain one normalized `projectKey` only as a grouping hint.

The classifier performs no I/O and grants no access or persistence authority.
Each caller explicitly admits its subset: Session reference repair may group
generic URLs by semantic target, retain the canonical safe locator for later
reparse and navigate through it; this projection creates no Atlassian Item,
structure reference or Site. Explicit local evidence Sync separately admits
Item and structure locators under the action rules below. Registration retains
its approved Add families, including its Project/Space subset.

Current structure memory persists stable identity, privacy-safe locator aliases
and source evidence under owners separate from Item and Space. Site-family roots
are report-only, without a selectable zero-count row. Non-archived references
appear in Site-first Explorer and the narrow shared-Search projection. Zero
retained evidence keeps stable identity direct-only as archived; retained but
currently unusable evidence is shown as unavailable rather than deleted or
treated as fresh.

### Action Consequences

Atlassian actions have distinct consequences:

- `Sync` deterministically reconciles recognized Atlassian URL evidence from
  the retained safe-URL projection of eligible primary work Sessions and the
  persisted bodies of enabled, readable, ready Local Context Documents. Session
  evidence is merge-only because the authoritative Session scanner remains its
  cleanup owner; a completely read Document owns bounded replace-derived
  evidence. A strict Jira Issue or Confluence Page URL may create or reuse one
  normalized-domain Site and one Site-scoped normalized-URL record even when no
  Site, binding, or inventory existed at action start. The same normalized
  domain is one Site across Jira and Wiki; service qualifies URL admission, not
  Site identity. Each source is atomic: a new Site is source-local until that
  source transaction commits, then becomes available to later sources; rollback
  discards both the rows and its resolver overlay. Explicit Sync Document
  currentness is owned by content/source fingerprint, successful status, and
  the current extractor/resolver version, not by registered Site/service
  fingerprint. Sync imports no authoritative source content and performs no
  external or model work. It reconciles eligible
  structure descriptors into separately owned references, safe URLs, and
  evidence while a `site` result remains report-only. Reports keep bounded
  source, link/document, structure-reference, evidence, Site-only, and
  candidate-skip outcomes distinct. Unchanged repeat Sync is read-only reuse,
  and retry repeats the whole local scope.
- `Add` registers or reuses one real Jira link, Confluence document, Jira
  project, or Confluence Space URL locally. Key-only text is not evidence.
  Service, Site, kind, and available identity are inferred locally; Provider,
  Source Instance, capability,
  runner, and remote readiness are not prerequisites.
- `Connections` owns optional Site access bindings, Provider/configuration
  references, readiness, and connected discovery. Connected discovery selects
  Site, eligible bound access path, and Claude or Codex runner, may return
  partial candidates, and registers nothing without explicit confirmation.
- `Refresh` is the existing explicit remote maintenance path. Link/document,
  Space, Thread, Workstream, and all-known entry points first resolve a local
  preview
  with no external or model call. The preview shows exact known targets,
  Source Instance, Site/Space, coverage, freshness, timestamps, and calculated
  reads; unknown, due, stale, and unavailable targets default selected while
  current targets remain opt-in. A Run selects at most 20 pre-authorized reads.
  “All known” means only records already in LocalBrain. Jira Space refresh
  checks selected known links only. A Confluence full-content Space may additionally
  request one explicit catalog page of at most 200 regular Pages; cataloged
  Pages are indexed-intent stale stubs whose bodies require later explicit
  batches.

### Access And Entity Boundaries

Optional access failure never blocks Explorer Browse, local query,
link/document detail, local classification, Add, or Sync. Source Instance remains the internal
access, capability, and policy boundary; Site remains domain identity, and a
Site reachable through several access paths remains one target rather than
connection-specific duplicate inventory.

A structure reference is a distinct read-only Explorer/Search entity, not an
Item or persisted Space. Its optional container hint owns presentation grouping
only. It has no local note, attention, Topic/Tag, Workstream/Thread,
Connections, Refresh, remote-fact, or content authority. A Site-only recognition
is report-only. Item and structure-reference selection are mutually exclusive;
known filtered references produce an out-of-scope state without widening the
current population, while unknown and archived identities remain separately
named bounded states.

The `링크` / `문서` / `링크/문서` mapping applies to Explorer rows and
counts, Add, preview, full detail, Sync reports and announcements, Connections,
Refresh, and shared global Search. Physical schema, internal APIs and routes,
data attributes/selectors, diagnostics, value-registry keys, and historical
artifacts retain `Item` where it is the stable engineering identity.

## External Access And Synchronization Constraints

- External Source Instance registration is durable local state, while its latest capability observation is rebuildable operational state. Only version-controlled policy may map a logical operation to an external target.
- Capability inspection is explicit. Application startup, browse, search, and ordinary local preview do not inspect or refresh external capabilities.
- Static Jira/Confluence URL classification is configured-domain independent and
  local-only. It normalizes the bounded HTTP(S) host/path, rejects credentials
  and REST endpoints, applies path/query Item identity before structure identity
  and then Site-family root, and exposes no raw query or JQL. A parser result
  grants no access or persistence authority by itself. Explicit evidence Sync
  admits `item` into the Site/Item path and `structure` into separate
  reference, privacy-safe URL, and source-evidence owners keyed by
  Site/service/kind/identity; `site` remains report-only. Registration consumes
  its separately approved Add families and may persist its approved
  Project/Space subset. The structure-reference path cannot reuse
  `external_resources`, Item/Space/access/remote-state tables as authority.
- Atlassian page load, service switching, local URL preview and registration,
  access setup, connection editing, local inventory filtering, Site-first
  hierarchy projection, grouped search, detail reading, note/Topic/Tag edits,
  and Workstream/Thread link edits perform no external or model call. A valid
  URL resolves or creates the normalized-domain Site and Item/Space locally
  without a Source Instance, Provider, configuration reference, or capability.
  Jira and Confluence on the same normalized domain reuse one Site; service is
  an admission/access qualifier, not Site identity. Optional access setup is a
  separate action that binds the registered Site to a real Source Instance only
  after the user supplies Provider and a validated Cloud ID or Gateway
  configuration alias; URL shape never selects Provider.
- Atlassian local evidence Sync is one explicit zero-execution-input action over
  already persisted Session-reference and Context Document state. It uses a
  process-local non-blocking single-flight owner and one short transaction per
  source. An `item` result for a strict Jira Issue or Confluence Page URL may
  create or reuse a normalized-domain Site and Site-scoped normalized-URL Item
  even from an empty inventory. A `structure` result may create or reuse that
  Site plus a separately owned stable reference, privacy-safe locator, and
  evidence; it creates no Item or Space. A `site` result is report-only. New
  resolver state is source-local and enters the later-source action cache only
  after the source transaction commits, so failure leaves no partial Site,
  Item, structure reference, evidence, or cached nonexistent identity. The
  action creates no binding or maintenance Run and calls no source
  parser/importer, filesystem, Provider, capability, executor, runner, model,
  connected discovery, or Refresh path. A bounded process-local receipt
  supports POST/Redirect/GET but never becomes SQLite history or result
  authority.
- Atlassian Item FTS uses deterministic role rows under one stable Item ID:
  identity is always eligible, bounded metadata follows metadata/indexed
  coverage, normalized remote body follows indexed coverage, and local
  note/Topic/Tag text remains a separate local role. Separately, each
  non-archived structure reference owns at most one
  `atlassian_structure_reference` row containing only reference identity,
  generated family label, and privacy-safe locator. Last-evidence cleanup
  archives the reference and removes that row. Shared Search keeps the two
  entity types distinct and resolves their current relational owners before
  display.
- Accessible-Space discovery is a separately submitted maintenance Run, uses the selected Source Instance and Site, consumes at most one policy-authorized metadata search call, labels results as partial, and registers no candidate until explicit confirmation.
- Atlassian refresh scope resolution and preview are local-only. Item, Space, Thread, Workstream, and all-known selections are bounded to already-known Items, default by derived freshness, show calculated reads, and cannot queue more than 20 reads. A mixed-instance selection remains one Run whose targets each carry their own pre-authorized Source Instance; single-instance manifests retain the original envelope shape.
- Jira Space refresh reads only selected known Items. Confluence may explicitly enumerate one 200-Page catalog page for a registered Space; new Page identities become stale indexed-intent stubs, while body retrieval remains a later explicit selected batch.
- External read authorization intersects enabled registration, current observation, and static policy. Unknown, stale, unavailable, unauthorized, error, disabled, arbitrary-tool, and write-shaped requests fail before dispatch.
- External synchronization persists a generic maintenance parent plus one source-neutral query envelope. Its model process receives only host-validated local evidence; source facts come from the approved executor and cannot be authored by model output. A validated Atlassian refresh result is applied in the same database transaction as the terminal Run state, so invalid target/source/locator mappings cannot partially mutate Items.

## External Access Foundation

Current external-access foundation:

- registered MCP Gateway Jira and Confluence Source Instance contracts
- registered official Atlassian Cloud Jira and Confluence Source Instance contracts
- explicit capability inspection operations
- bounded logical Jira and Confluence reads mapped to exact provider targets
- source-neutral external-sync maintenance contract for Claude or Codex, with a required injected read executor and no direct model access to broad Gateway tools
- local-only Jira ticket/project and Confluence Page/Space URL registration, plus explicit one-call partial Space-candidate discovery when a current capability and injected host executor are available
- local Atlassian browse/search/detail and user-owned Topic/Tag/note classification, plus explicit refresh previews and one bounded mixed-instance maintenance Run for known Items, with no live browse retrieval or implicit external call

## Implementation Ownership

- `src/localbrain/atlassian/access.py`: stable external Source Instance registration, rebuildable capability observations, version-controlled Atlassian read policy, and fail-closed dispatch construction; it performs no external call

- `src/localbrain/atlassian/sync.py`: source-neutral external-sync manifest/result validation, atomic query-envelope preparation, approved host-dispatch evidence validation, and source-fact authority separation

- `src/localbrain/atlassian/catalog.py`: stable External Resource-backed Site/Space/Item identity, scoped URL aliases, remote/local ownership, derived freshness, deterministic body normalization, and hash-gated FTS projection; it performs no external call

- `src/localbrain/atlassian/browse.py`: local Atlassian inventory filters,
  grouped search, canonical-URL-owned Site-first hierarchy descriptors, Item
  detail, user note/Topic/Tag mutation, and existing Workstream/Thread link
  projection; it performs no external or model call

- `src/localbrain/atlassian/evidence.py`: configured Site-scoped Item URL
  recognition plus source-owned bounded scan/evidence reconciliation

- `src/localbrain/atlassian/evidence_sync.py`: explicit persisted-only Session
  projection and chunked Local Context Document evidence reconciliation,
  strict Jira Issue/Confluence Page admission with normalized-domain local
  Site/Item reuse, source-isolated transactions, commit-published resolver
  overlays, fixed outcome reports, and process-local single-flight; it performs
  no source, filesystem, external, model, or Refresh work

- `src/localbrain/atlassian/registration.py`: strict Jira/Confluence URL
  recognition, normalized-domain Site resolution, read-only URL container
  descriptors, local-only Item/Space registration, inventory projection, and
  explicit one-call partial Space-candidate maintenance composition

- `src/localbrain/atlassian/refresh.py`: local Item/Space/Thread/Workstream/all-known scope resolution, freshness-aware preview, mixed-instance bounded Run preparation, and atomic validated result application
