# SPEC-0050: Atlassian Browse, Search, And Local Classification

## Metadata

- ID: `spec-0050`
- Status: `approved`
- Run ID: `run-20260723-55`
- Attempt: `1`
- Feature: [feat-0050-atlassian-browse-search-and-local-classification](../feature/feat-0050-atlassian-browse-search-and-local-classification.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Execution Profile: `fullstack-product`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Source Set

- Approved PRD-0007 and FEAT-0050.
- Passed FEAT-0046 stable identity/content/FTS contract, FEAT-0047 evidence, FEAT-0048 registration, and FEAT-0049 explicit refresh.
- Current global Search, Workstream/Thread link, safe reading, Design Constitution, Design Evaluation, Interaction Evaluation, Product, Architecture, Privacy, and data-model owners.

## Implementation Goal

- Make every known Atlassian Item usable as a local knowledge object: locally browse and search it, inspect authoritative remote and local regions, trace evidence, add flat Topics/Tags/notes/attention, and optionally link it to existing work without any provider or model call.

## Locked Product Decisions

- Unfiltered inventory and global Search exclude `archived`; direct detail remains available and `attention=archived` or `attention=all` recovers it.
- Topic descriptions are created and maintained in the Item detail classification region. Inventory rows display Topic names only.
- The existing Atlassian screen gains `Browse` and `Add / discover` modes. `Browse` is the default; FEAT-0048 forms and catalog results remain in the explicit setup mode.
- Jira and Confluence remain first-class service views. No cross-domain merge, migration comparison, or remote live search is introduced.

## Data Contract

- Add `atlassian_item_local_state` as the one-to-one owner of a bounded local note. It cascades with the stable Item and is never written by refresh.
- Add `atlassian_classifications` with `kind IN ('topic', 'tag')`, user-visible name, deterministic case-folded `normalized_name`, and optional Topic-only description. Identity is unique by kind and normalized name.
- Add `atlassian_item_classifications` as the many-to-many membership table. Membership removal never deletes the reusable classification.
- Continue using `atlassian_items.attention` for `normal`, `pinned`, `ignored`, and `archived`.
- Continue using existing `workstream_links` and `thread_links` with `entity_type = external` and the stable External Resource ID. Detail mutations call the existing link service; no duplicate relation model is added.
- Existing databases receive only additive table/index creation. Stable Item IDs, URLs, remote state/content, evidence, and organization remain unchanged.

## Search Projection Contract

- One stable Item may own several derived FTS rows, all with `entity_type = atlassian_item` and the same stable ID:
  - `<service>:identity` for local display identity, confirmed remote key, and canonical URL
  - `<service>:metadata` only when bounded confirmed remote metadata exists
  - `<service>:content` only when coverage is `indexed` and normalized source content exists
  - `atlassian:local` only when a local note, Topic, or Tag exists
- Search projection is fully derived and atomically replaced for one Item. Current rows are compared before replacement, so unchanged projections are not rewritten.
- Reference coverage contributes identity only. Metadata coverage adds confirmed metadata but never a body. Indexed coverage may add normalized Jira description or Confluence Page body.
- Global Search groups multiple matching FTS rows by stable Item, retains matched projection roles/snippets, and displays service, Source Instance, Site/Space, coverage, freshness, attention, and canonical local detail link.
- Atlassian inventory query uses the same local FTS identity set before applying structured filters. No query path inspects capabilities, starts a Run, calls a provider, or invokes a model.

## Browse And Filter Contract

- `/atlassian` accepts bookmarkable GET state for `mode`, `view`, `q`, Source Instance, Site, Space, Item type, coverage, freshness, attention, Topic, Tag, and Workstream.
- Filters are conjunctive and resolve by stable Item identity. An empty database differs from a populated inventory with no matches.
- Filter options are local projections derived from current Source Instances, Sites, Spaces, reusable classifications, and Workstreams.
- Default ordering is pinned first, then latest local Item update and stable ID. Archived is excluded unless explicitly requested.
- Canonical URLs are ordinary explicit external links using `target="_blank"` and `rel="noreferrer"`; no prefetch is emitted.

## Detail And Mutation Contract

- `/atlassian/items/{id}` is direct-entry safe and renders four distinct regions:
  - remote identity, metadata, normalized body, version/update evidence, coverage, freshness, and explicit refresh/external-link actions
  - local note, attention, Topics, Tags, and optional Workstream/Thread relations
  - Session and Local Context evidence with owner-local navigation and no copied excerpt
  - latest relevant explicit refresh Run state derived from retained local Run manifests
- POST local-state mutations are server-rendered/no-script compatible, bounded, and redirect back to the detail anchor with a local-only notice.
- Topic names/descriptions, comma-separated Tags, notes, and attention are normalized and validated before one transaction. Duplicate case-folded names reuse the same classification.
- Workstream linking accepts one existing Workstream or one of its Threads; unlinking uses the existing link identity. Invalid cross-Workstream Thread selection fails before mutation.
- No local mutation creates a Suggestion, remote write, refresh Run, or synchronization model call.

## Interaction And Visual Contract

- Use `screen-alignment` in `extend` mode and existing LocalBrain shell, toolbar, filter, card, badge, form, and reading-region families.
- Browse defaults place search/filter and known Items before setup actions. Detail places source truth before local organization, then evidence and Run history.
- GET filters and links preserve browser history naturally. POST uses redirect-after-write. Error responses preserve entered local fields.
- Labels, URLs, metadata values, notes, tags, topic descriptions, body content, and evidence locations must wrap inside their owner at `1440`, `920`, `700`, and `320`; no page-level horizontal overflow is allowed.
- Empty, no-match, partial/reference, stale, unavailable, archived direct-entry, long-content, focus, and no-script states require explicit copy.

## Surface Lanes And Order

1. Data and contract lane:
   - paths: schema, compatible startup, Atlassian owner docs, classification/search service, unit tests
   - gate: additive migration, ownership, projection eligibility, filters, mutation invariants
   - evaluators: contract, functional
2. Integration lane:
   - paths: global Search, Workstream/Thread links, evidence/Run projections, routes
   - gate: stable links, grouped source-attributed hits, no external activity
   - evaluators: contract, functional
3. Frontend lane:
   - paths: Atlassian browse/setup, Item detail, global Search, route-scoped interaction and shared styles
   - gate: information hierarchy, states, focus/history, responsive containment
   - evaluators: design, functional, ux-heuristic
4. Documentation/regression lane:
   - paths: Product, Architecture, Privacy, Search/Workstream/Atlassian data model, README, generated schema/audit
   - gate: full regression and all generated-artifact checks
   - evaluators: contract

## Acceptance Mapping

- FEAT inventory/filter/search criteria map to the browse query, grouped FTS result, and filter-option contracts.
- Remote/local/evidence/refresh separation maps to the four-region detail contract and independent schema owners.
- Topic, Tag, note, attention, and optional work mapping map to additive local tables plus existing stable Item/link identities.
- No-remote/no-write guarantees map to GET-only local queries and transactional local POST services with no executor dependency.
- Archived, partial, stale/unavailable, history/focus, direct entry, and responsive criteria map to explicit route and visual states.

## Evaluation Focus

- Contract: additive schema, stable IDs, classification uniqueness, search eligibility/attribution, link ownership, evidence separation, no external side effects.
- Design: browse/setup hierarchy, dense filters, detail regions, long content, state mapping, source distinction, responsive containment.
- Functional: every filter, grouped FTS roles, metadata/body/local eligibility, mutations, link validation/removal, archived recovery, evidence/Run navigation, no-script routes, regressions.
- UX heuristic: search trust, source/domain distinction, classification without Workstream, archived recovery, and remote/local comprehension.

## Open Blockers

- None. Owner-approved recommended defaults and passed dependency Features are sufficient for implementation.
