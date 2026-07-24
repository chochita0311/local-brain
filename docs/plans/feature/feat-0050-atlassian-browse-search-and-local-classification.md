# FEAT-0050: Atlassian Browse, Search, And Local Classification

## Metadata

- ID: `feat-0050`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal

- Let the user browse, inspect, locally search, classify, and optionally organize Jira tickets and Confluence Pages as a personal knowledge base while keeping remote facts, local choices, related evidence, and refresh state visibly separate.

## Acceptance Contract

- Atlassian inventory presents Jira and Confluence Items across Source Instances without mixing identical keys from different domains.
- Inventory and local search support narrowing by service, Source Instance, Site or Space, Item type, coverage, freshness, attention, Topic, Tag, and optional Workstream relation.
- Ordinary inventory, filtering, detail, and search perform zero remote and zero synchronization-model calls.
- Search includes confirmed remote metadata and includes Jira description or Confluence body only when coverage is `indexed`.
- Every search result resolves to the stable FEAT-0046 Resource and exposes enough source, type, coverage, and freshness context to judge the result.
- Item detail separates:
  - remote identity, metadata, content, version, and freshness
  - local attention, notes, Topics, Tags, and Workstream or Thread relations
  - Session and Local Context evidence from FEAT-0047
  - latest relevant refresh or maintenance Run state
- Evidence links return to the owning local Session or Document and never appear as unattributed remote body text.
- The Canonical URL remains a user-activated external link and is never prefetched.
- Topics are flat reusable user-created groupings with a name and optional description and support many-to-many Item membership.
- Tags are lightweight free-form many-to-many Item labels independent of Topics and Workstreams.
- Attention supports `normal`, `pinned`, `ignored`, and `archived` independently from coverage and organization.
- An Item remains searchable, classifiable, and refreshable with no Workstream mapping.
- Local note, Topic, Tag, attention, and Workstream or Thread changes never write to Atlassian and remain usable while remote content is stale or unavailable.
- Generated Topic, Tag, or Workstream Suggestions are not created by this Feature.
- Empty, no-match, partial-content, stale, unavailable, archived, long-content, direct-entry, history, focus, and responsive states remain understandable and contained.

## Scope Boundary

- In:
  - Atlassian inventory and filters
  - Item detail and source-separated regions
  - global and Atlassian-scoped local FTS integration
  - remote metadata and indexed-body snippets
  - evidence navigation
  - local notes, attention, Topics, and Tags
  - optional existing Workstream and Thread linking
  - archived access and explicit filtering
  - direct entry, browser history, focus, long content, and responsive behavior
- Out:
  - registration owned by FEAT-0048
  - refresh execution owned by FEAT-0049
  - remote or federated live search
  - AI summaries, automatic classification, or automatic organization
  - Topic hierarchy
  - external write-back
  - comments, attachments, blogs, whiteboards, databases, or revision-history bodies
  - old/new migration comparison or cross-domain merge

## Surface Lanes

- Browse and search contract lane:
  - path roots: Atlassian and global search queries, filters, FTS resolution, and route tests
  - dependencies: FEAT-0046 and FEAT-0047 passed
  - expected evidence: source-correct eligibility, filters, snippets, stable result identity, no remote search, and evidence separation
  - evaluator ownership: `contract`, `functional`
- Local organization lane:
  - path roots: Topic, Tag, note, attention, and existing Workstream/Thread relation services plus data tests
  - dependencies: FEAT-0046 passed
  - expected evidence: flat Topic and free-form Tag ownership, many-to-many membership, independent axes, stale/unavailable durability, and no external writes
  - evaluator ownership: `contract`, `functional`
- Inventory and detail lane:
  - path roots: `src/localbrain/templates/atlassian.html`, Item detail template, `src/localbrain/templates/search.html`, styles, route-scoped interactions, and browser tests
  - dependencies: browse/search and local organization lanes plus FEAT-0048 and FEAT-0049
  - expected evidence: clear remote/local/evidence/refresh hierarchy, filters, direct links, empty/error states, history, focus, and responsive containment
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- Atlassian inventory and detail routes.
- Global and Atlassian-scoped search result shape.
- FTS eligibility and source-backed snippet attribution.
- Service, Source Instance, Space, type, coverage, freshness, attention, Topic, Tag, and Workstream filters.
- Topic, Tag, note, and attention ownership.
- Evidence and refresh-state projections.
- Existing Workstream and Thread Resource-link actions.
- External Canonical URL activation and no-prefetch boundary.

## Required Evaluators

- `contract`: search eligibility, source attribution, filter semantics, local ownership, evidence separation, Workstream linking, and no-remote/no-write guarantees.
- `design`: browse density, detail hierarchy, long content, filter adaptation, provenance, status, local classifications, empty/error states, and responsive containment.
- `functional`: inventory, every filter, metadata/body search eligibility, evidence navigation, notes, Topics, Tags, attention, Workstream links, stale/unavailable state, direct entry, history, and zero external calls.
- `ux-heuristic`: search trust, source distinction, knowledge-base use without Workstreams, classification clarity, archived recovery, and remote/local boundary comprehension.

## User-Visible Outcome

- The user can find and understand a known Jira ticket or Confluence Page from local state, see where it was encountered, classify it using personal Topics and Tags, and connect it to work only when useful.

## Entry And Exit

- Entry point: Atlassian navigation, global Search, a Workstream or Thread Resource link, related Session or Document evidence, or direct Item URL.
- Exit or transition behavior: list-to-detail and search-to-detail preserve filter context when supported; evidence returns to its owning local source; Canonical URL activation leaves LocalBrain only through an explicit external link.

## State Expectations

- Default: inventory and detail identify service, Source Instance, coverage, and freshness before secondary classification.
- Empty: no Items differs from no filter matches and offers the appropriate registration or reset path.
- Partial: reference and metadata-only Items remain useful without fabricated snippets.
- Stale or unavailable: last-known content remains readable with visible limitations and refresh context.
- Archived: directly reachable and available through an explicit filter; proposed default inventory and search exclude it.
- Error: a failed local query or mutation preserves filters and entered local values where recovery is possible.
- Success: remote facts, local organization, evidence, and refresh state agree on one stable Item identity.

## Dependencies

- FEAT-0046 and FEAT-0047 must be `passed`.
- FEAT-0048 and FEAT-0049 must be `passed` before the complete visible workflow enters build.
- Existing global Search, Workstream/Thread Resource links, safe Markdown reading, and Design Constitution contracts remain authoritative.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/queries.py`
- `src/localbrain/retrieval.py`
- `src/localbrain/workstreams.py`
- FEAT-0046 Atlassian domain and search modules
- `src/localbrain/templates/atlassian.html`
- a new Atlassian Item detail template
- `src/localbrain/templates/search.html`
- `src/localbrain/static/styles.css`
- route-scoped interaction code under `src/localbrain/static/`
- query, search, Workstream, route, interaction, Markdown, accessibility, and responsive tests
- Product, Search, Workstream, and Atlassian data-model owner documentation

## Pass Or Fail Checks

- Pass if inventory and search distinguish Source Instances and never merge identical cross-domain keys.
- Pass if metadata and indexed-body eligibility are correct and every snippet retains its remote source.
- Pass if all approved filters produce reproducible local-only results and distinguish no-data from no-match.
- Pass if Item detail keeps remote, local, evidence, and refresh regions semantically separate.
- Pass if notes, attention, Topics, Tags, and Workstream/Thread links survive stale and unavailable remote state and perform no external writes.
- Pass if an unmapped Item remains fully usable as local knowledge.
- Pass if evidence and Canonical URL links follow their correct local or explicit external boundary.
- Pass if direct entry, back/forward, focus, long content, empty, partial, stale, unavailable, archived, and `1440`/`920`/`700`/`320` states remain usable.
- Fail on implicit remote search, unattributed evidence, cross-instance merge, local-field overwrite, generated classification, inaccessible archived content, or shell/content overflow.

## Regression Surfaces

- Existing global Search source filters and result resolution.
- Workstream and Thread External Resource links and checkpoints.
- FEAT-0048 registration and FEAT-0049 refresh orientation.
- Shared safe Markdown reading and external-link safety.
- Persistent shell, active navigation, history, focus, and responsive behavior.

## Harness Trace

- Active spec doc: [spec-0050-atlassian-browse-search-and-local-classification](../spec/spec-0050-atlassian-browse-search-and-local-classification.md)
- Active run: [run-20260723-55-atlassian-browse-search-and-local-classification](../run/run-20260723-55-atlassian-browse-search-and-local-classification.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [contract](../evaluation/eval-0050-contract-atlassian-browse-search-and-local-classification.md)
  - [design](../evaluation/eval-0050-design-atlassian-browse-search-and-local-classification.md)
  - [functional](../evaluation/eval-0050-functional-atlassian-browse-search-and-local-classification.md)
  - [ux-heuristic](../evaluation/eval-0050-ux-atlassian-browse-search-and-local-classification.md)
- Latest fix note: not created

## Open Review Decisions

- None. Archived Items are excluded from unfiltered inventory and Search but remain directly reachable and available through `attention=archived` or `attention=all`. Topic descriptions are managed in the bounded Item detail classification region, while Item lists show Topic names only.

## Continuity Notes

- `2026-07-23`: initial draft combined inventory, local Search, Item detail, evidence navigation, Topics, Tags, notes, attention, and optional Workstream organization because they form one local knowledge-base outcome over the same stable Item read model.
- `2026-07-23`: owner-approved sequential execution and recommended defaults advanced the Feature to RUN-20260723-55 after FEAT-0049 passed.
- `2026-07-23`: attempt 1 passed all four required evaluations with additive local note/Topic/Tag ownership, role-separated FTS, grouped source-aware Search, browse/setup separation, four-region Item detail, existing Workstream/Thread links, exact `1440`/`920`/`700`/`320` containment, and 256 passing regressions.
