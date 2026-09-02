# Project Architecture

## Purpose

This document owns LocalBrain's durable implementation shape: runtime layers, package responsibilities, source adapters, persistence, ingestion behavior, and the current implementation baseline.

Product terminology and organization rules are defined in [Product Model](product.md). In-app maintenance execution is defined in [Maintenance Task Runner](../operations/claude-task-runner.md).

## Runtime Shape

- Runtime: local web server and browser UI
- Backend: Python and FastAPI
- Database: SQLite
- Search: SQLite FTS5
- Frontend: server-rendered Jinja2 with small JSON API interactions
- External integration boundary: approved MCP Gateway and source-specific adapters
- Later packaging: Tauri when feasible, with Electron as an alternative if integration constraints require it

The local web runtime validates the product workflow before native macOS lifecycle and distribution work begins.

```text
Claude / Codex / user-managed local context / local project and Git metadata
Approved external sources through MCP Gateway
                              |
                        Source adapters
                              |
                    Normalize and deduplicate
                              |
               SQLite event store + FTS5 index
                      /                 \
         Workstreams and resume        Insights
                      \                 /
                      Local web application
```

## Package Ownership

- `src/localbrain/main.py`: FastAPI routes, request models, and application composition
- `src/localbrain/db.py` and `schema.sql`: connection lifecycle, fresh schema, compatible startup migrations, and explicitly approved backup-backed structural repair
- `src/localbrain/ingest/`: source parsing, normalization, scanning, and deduplication
- `src/localbrain/session_sources.py`: private TOML bootstrap, validation, bounded
  diagnostics, and non-destructive local Session-source registry reconciliation
- `src/localbrain/session_references.py`: source-neutral safe URL, exact Markdown,
  and configured Atlassian reference resolution; file-scoped evidence replacement,
  Session-level bounds/fingerprints, and database-only detail projection
- `src/localbrain/contexts.py`: Local Context source registration and browsing behavior
- `src/localbrain/markdown.py`: shared safe Markdown and approved Obsidian-style parsing, derived render state, local code and MathML rendering, attachment deferral, and reusable consumer output governed by the [Markdown Rendering Contract](markdown-rendering.md)
- `src/localbrain/markdown_references.py`: one-FOLDERS-root Markdown and wikilink resolution, stable anchor identity, and bounded note-fragment extraction
- `src/localbrain/queries.py`: read models for dashboards, sessions, sources, search, and detail views
- `src/localbrain/usage.py`: immutable price snapshots, model normalization, and per-Usage-Record estimated-cost calculation
- `src/localbrain/usage_queries.py`: Sessions Dashboard scope normalization, summary, MTD, history buckets, freshness, and limitation states
- `src/localbrain/workstreams.py`: Workstreams, Threads, checkpoints, resources, links, Suggestions, and retrieval mappings
- `src/localbrain/retrieval.py`: deterministic candidate selection and evidence preparation
- `src/localbrain/runner.py`: maintenance Run preparation, execution, streaming, and structured result processing
- `src/localbrain/external_access.py`: stable external Source Instance registration, rebuildable capability observations, version-controlled Atlassian read policy, and fail-closed dispatch construction; it performs no external call
- `src/localbrain/external_sync.py`: source-neutral external-sync manifest/result validation, atomic query-envelope preparation, approved host-dispatch evidence validation, and source-fact authority separation
- `src/localbrain/atlassian.py`: stable External Resource-backed Site/Space/Item identity, scoped URL aliases, remote/local ownership, derived freshness, deterministic body normalization, and hash-gated FTS projection; it performs no external call
- `src/localbrain/atlassian_browse.py`: local Atlassian inventory filters,
  grouped search, canonical-URL-owned Site-first hierarchy descriptors, Item
  detail, user note/Topic/Tag mutation, and existing Workstream/Thread link
  projection; it performs no external or model call
- `src/localbrain/atlassian_evidence.py`: configured Site-scoped Item URL
  recognition plus source-owned bounded scan/evidence reconciliation
- `src/localbrain/atlassian_evidence_sync.py`: explicit persisted-only Session
  projection and chunked Local Context Document evidence reconciliation,
  strict Jira Issue/Confluence Page admission with normalized-domain local
  Site/Item reuse, source-isolated transactions, commit-published resolver
  overlays, fixed outcome reports, and process-local single-flight; it performs
  no source, filesystem, external, model, or Refresh work
- `src/localbrain/atlassian_registration.py`: strict Jira/Confluence URL
  recognition, normalized-domain Site resolution, read-only URL container
  descriptors, local-only Item/Space registration, inventory projection, and
  explicit one-call partial Space-candidate maintenance composition
- `src/localbrain/atlassian_refresh.py`: local Item/Space/Thread/Workstream/all-known scope resolution, freshness-aware preview, mixed-instance bounded Run preparation, and atomic validated result application
- `src/localbrain/subagents.py`: lazy Claude Subsession compatibility discovery over the source-native `subagents/` directory
- `src/localbrain/schema_explorer.py`: manifest-only Schema query normalization and read model; it never opens the runtime database
- `src/localbrain/templates/`: server-rendered UI views
- `src/localbrain/static/`: browser behavior and visual presentation
- `src/localbrain/schema_presentation.py` and `schema-presentation.json`: bounded loader and derived package data for read-only Schema consumers

Keep source-specific parsing inside adapters and keep persistence or domain behavior out of templates.

## Source Adapters

Current adapters:

- Claude local session history
- Codex local session history
- user-managed folders and individual files
- Apple Notes through local macOS Automation
- local project and Git metadata discovered during scans

Each local Session source has a stable source key independent from its provider
kind. Source keys own provenance, filtering, and statistics; provider kind selects
the parser, Usage normalizer, and other adapter-specific semantics. Multiple
source keys may therefore reuse the Codex provider without sharing Session or
Usage identity.

The ordered local AI Session-source list is owned by private
`<LOCALBRAIN_DATA_DIR>/session-sources.toml`. A missing file is atomically seeded
once from the legacy Claude/Codex root settings plus the Codex Company default.
Established-file syntax and identity validation precede registry mutation;
omission, invalid paths, provider conflict, or an occupied-root change cannot
delete or silently relocate retained normalized data. Scanner dispatch consumes
this registry in the following multi-source synchronization contract.

Current external-access foundation:

- registered MCP Gateway Jira and Confluence Source Instance contracts
- registered official Atlassian Cloud Jira and Confluence Source Instance contracts
- explicit capability inspection operations
- bounded logical Jira and Confluence reads mapped to exact provider targets
- source-neutral external-sync maintenance contract for Claude or Codex, with a required injected read executor and no direct model access to broad Gateway tools
- local-only Jira ticket/project and Confluence Page/Space URL registration, plus explicit one-call partial Space-candidate discovery when a current capability and injected host executor are available
- local Atlassian browse/search/detail and user-owned Topic/Tag/note classification, plus explicit refresh previews and one bounded mixed-instance maintenance Run for known Items, with no live browse retrieval or implicit external call

### Adapter Extension Boundary

The [Project Roadmap](../../plans/project/roadmap.md) and [Project Backlog](../../plans/project/backlog.md) own adapter sequencing and named future targets. Any new external adapter must sit behind an approved connector boundary and follow the persistence modes in [Privacy And Data Handling](privacy-and-data.md).

## Persistence Model

The complete effective-schema map, physical and application relationships, lifecycle/recovery classifications, and nine subject catalogs are owned by [Data Model](data-model.md). This section keeps only the architectural grouping and cross-layer behavior.

The packaged consumer form is owned by [Schema Presentation](schema-presentation.md). Its generator applies fresh DDL and the compatible structural/index path only to SQLite `:memory:`, combines those facts with Data Model semantics, and emits derived JSON. Application consumers load that package data; they do not inspect a user database or repository Markdown.

Bounded database values use `src/localbrain/value-registry.json` as their executable physical/logical/presentation authority. The generated [Value Dictionaries](data-model/value-dictionaries.md) remain the human-readable subject projection; runtime code loads the registry and never parses Markdown.

`System > Schema` serves the read-only `/schema` Explorer from that package data. Optional `area` and `table` query values select one of the nine owner areas and one owned table; invalid state normalizes to the nearest valid overview. Server-rendered links and catalogs remain complete without JavaScript, while the route-scoped module preserves shell continuity, history, focus, strict locally packaged Mermaid rendering, and bounded presentation-only diagram zoom. The route has no SQLite connection, row preview, external asset, SQL, edit, or cleanup action.

The current schema groups data into these responsibilities:

| Responsibility | Current entities |
| --- | --- |
| Source inventory | `sources`, `source_files`, `external_source_instances`, `external_source_capabilities`, `context_roots`, `workspaces` |
| Indexed activity | `sessions`, `activity_events`, `session_reference_scans`, `session_reference_evidence`, `usage_records`, immutable usage price snapshots, `context_documents`, FTS5 search tables |
| User organization | `workstreams`, `threads`, `checkpoints` |
| Linkable resources | `local_resources`, `external_resources`, Workstream and Thread links |
| Atlassian source memory | domain-first `atlassian_sites`, optional `atlassian_site_bindings`, access-optional `atlassian_spaces`, strict one-to-one `atlassian_items`, Item URL/remote/local/evidence owners, separate `atlassian_structure_references`, `atlassian_structure_reference_urls`, and `atlassian_structure_reference_evidence`, plus Item role rows and one bounded non-archived reference row in shared FTS |
| Review workflow | `suggestions`, checkpoint resource snapshots, Thread resource matches |
| Maintenance execution | `maintenance_runs`, source-neutral `external_sync_runs`, and artifacts under the runtime data directory |

Resources are canonical entities. A Session or Document is stored once and may relate to any number of Threads. Relationship-specific evidence is stored separately so the resource payload is not duplicated.

Checkpoint records are versioned, user-confirmed resume states. Confirmation captures a snapshot of resources linked to the Workstream and its Threads at that time.

## Ingestion Contract

### Core Invariants

- Preserve raw source identity and timestamps.
- Prefer append-only normalized activity events.
- Deduplicate by stable source ID where available and deterministic fingerprint otherwise.
- Keep imported content separate from user-confirmed checkpoints.
- Make search indexes and statistics rebuildable from stored normalized data where possible.
- Record source check time, status, failures, and refresh requirements.
- Do not re-import maintenance Run artifacts as ordinary Sessions or Local Context documents.
- Treat generated titles and summaries as presentation, never as stable identifiers.

### Reference Evidence And Reconciliation

- Treat Atlassian URL evidence as a derived locator: retain the owning source identity, event/line/occurrence, observed URL, and only allowlisted bounded result fields, never a copied excerpt or opaque tool payload.
- Treat source-neutral Session reference evidence as a separate derived projection from Activity Events, shared Resource metadata, remote content, and organization links. Retain only aggregate scan/version state plus deterministic target identity, event/line/ordinal, bounded observed identity, safe normalized destination, and approved tool-call outcome fields; never copy message excerpts or opaque tool payloads.
- Route standard Atlassian URL-family recognition through one pure, versioned
  locator owner before consumer-specific admission. The owner performs no
  SQLite, filesystem, Provider, capability, runner, model, connected-discovery,
  Refresh, or network work and returns only `item`, `structure`, `site`,
  `unsupported`, or `unsafe`. Recognized output drops fragment and arbitrary
  query but may retain the canonical allowlisted identity projection required
  to distinguish a structure reference. RapidBoard `rapidView` is Board
  identity; optional `projectKey` is only a grouping hint. Confluence keeps the
  recognized deployment-context prefix and either a valid Space/Page path or
  only canonical `pageId` on `pages/viewpage.action`. The Session adapter
  groups recognized URL rows by the semantic domain/service/Item-or-reference
  descriptor rather than whole locator spelling, retains the safe locator for
  later reparse, and keeps structure/site as generic URL targets. The passed
  foundation created no Atlassian structure-reference or Site row.
- Explicit Atlassian local evidence Sync may consume that retained Session URL
  projection without reopening its source. It merge-inserts only missing
  Atlassian sightings, never advances or cleans Session-owned Atlassian scan
  state, and records the safe normalized locator rather than claiming an
  unavailable original spelling. Enabled, readable, ready Context Documents
  use a finite chunked persisted-body pass and retain the deterministic first
  bounded evidence set; only a complete pass may replace obsolete Document
  sightings. Strict Jira Issue and Confluence Page locators are admitted even
  without a pre-registered Site: the current source transaction may create one
  normalized-domain Site and its Site-scoped URL Item, with no binding or
  access state. A source-local resolver overlay is reused inside that source
  and is published to the action-wide resolver only after commit; rollback
  discards it. Explicit Sync Document currentness compares its persisted
  content/source fingerprint, successful status, and extractor/resolver version
  and does not reopen registered-Site fingerprint as an idempotency owner.
- When that same explicit Sync receives a shared locator `structure` result, it
  resolves or creates only the normalized-domain Site plus an independent stable
  `(Site, service, reference kind, reference identity)` structure reference,
  privacy-safe canonical/alias locator rows, and source-separated Session or
  Document evidence. Session reconciliation remains merge-only; a complete
  changed Document pass replaces only that Document's structure evidence. Loss
  of the last evidence archives the reference and removes its FTS row but keeps
  stable identity and URL history for direct inspection and later reuse. Optional
  Project/Space hints drive read-only grouping consensus and never create a Space,
  Item, binding, access, remote state, local edit, classification, or organization
  row. A shared locator `site` result remains report-only and creates no entity.
- Compose primary Session `관련 자료` only at the bounded SQLite read layer. It consumes existing evidence and explicit organization relations without hidden query expansion, writes, parsing, model work, or external I/O; the [Product Model](product.md#session-detail-and-related-evidence) owns group eligibility, ordering, counts, and disclosure behavior.
- Map every successfully parsed Session JSONL to its normalized Session and
  reference contract in `source_files`. Reconcile changed paths independently,
  then finalize one aggregate Session set; when a prior set is partial or errored,
  reparse current siblings before applying the 100-target bound so a multi-file
  native Session cannot lose unchanged evidence.
- Build one immutable eligible-Context-document lookup per Session sync. Exact
  absolute and cwd-relative paths use its normalized-path index; basename
  references use its workspace/name index and preserve the existing exact-one
  ambiguity rule. The cache is request-local and never changes Context content.

Original Claude and Codex JSONL remains the authoritative Session source. LocalBrain stores normalized searchable text, selected metadata, source paths, source line numbers, and deterministic IDs so the index can be rebuilt. Provider-native event and Usage identities are additionally source-key scoped when a noncanonical source such as Codex Company reuses the Codex adapter, preventing globally keyed descendants from colliding while preserving existing personal Codex IDs.

### Session Eligibility

Provider parsing is followed by one shared meaningful-Session eligibility gate. A
parsed file must contain at least one normalized Activity Event or one direct
Usage Record; title, name, identity, timestamp, cwd, branch, or other metadata
alone describes an empty native stub. A successful readable-source scan stores no
normalized Session or source-file evidence for a new stub and reconciles an
existing empty projection after reparsing current sibling files. The source JSONL
is never deleted. Because an ignored stub retains no freshness row, later syncs
inspect it again and import it once Event or Usage evidence appears.

### Usage Normalization And Repair

Token usage is a separate derived-record lane from searchable Activity Events. Both adapters preserve one stable source-record identity, the raw model name, non-cached input, output, cache-write, cache-read, reasoning, source-total, and normalized-total semantics when those values are available. Claude input is already non-cached and its cache creation and cache read values remain additive. When Claude reports a zero cache-creation aggregate that contradicts a positive internally consistent ephemeral breakdown, the adapter uses the breakdown and records that bounded fallback. Each Codex `token_count` event contributes its direct `last_token_usage` when available; `total_token_usage` is Session-cumulative and is subtracted from the preceding observation only as a fallback. Spawned or forked subsession replay prefixes seed that cumulative baseline but do not produce copied records. Unchanged zero deltas are ignored, source input has cached input subtracted, and reasoning output remains an informational subset of output rather than an additional total.

Every directly observed Usage Record is eligible regardless of Session class or role. Maintenance Sessions and subsessions therefore remain excluded from ordinary Search and workflow statistics while still contributing their own direct usage. Current Claude and Codex observations carry a `direct` aggregation scope. LocalBrain does not persist a second parent rollup, so parent and child direct records are each counted once; the reserved `includes_children` scope requires a downstream rollup to exclude covered child records if a future source explicitly provides such an aggregate. A repeated source record updates one deterministic Usage Record, and malformed later evidence cannot erase a previously valid record. Session source files record the usage normalizer contract that processed them, and each Usage Record records its independent normalizer version. Unchanged file metadata is current only when this contract version also matches.

When a normalizer contract changes, ordinary Session synchronization performs a versioned Usage-only repair rather than requiring a user-facing aggregate reset. If any current file for a source has an older Usage contract version, synchronization reparses every current file for that source and reconciles their complete Usage Record union inside one source-level savepoint: matching identities update, new identities insert, and obsolete source identities delete. It does not replace the Session, Activity Event, search, Atlassian evidence, or generalized-reference lanes merely because the Usage contract changed. This boundary preserves all observations when one Session identity spans several files. A repair identity inherits the closest prior price snapshot and frozen Project attribution unless an approved corrective producer explicitly assigns a new immutable snapshot to repair an invalid token or service-tier contract. Ordinary new records under an unchanged contract receive the snapshot and current Project evidence available when first observed. Immutable snapshot/model price lookups are cached for one source repair and each Session's Usage upserts are issued as one batch without changing identity, ordering, values, or savepoint rollback. Any parse or persistence failure rolls back the complete source replacement and does not advance its source-file contract versions. Source freshness retains the size and modification time observed before parsing, so bytes appended to an active JSONL during the read remain detectable on the next synchronization. The next unchanged synchronization skips all now-current files, making the repair idempotent.

Estimated USD cost is a local trend estimate, not billed spend. Each Usage Record retains the immutable price-snapshot identifier, calculator version, calculation time, and explicit `priced`, `unpriced`, `partial`, or `failed` state used when it was first observed. A growing source record may be recalculated only against its retained snapshot. New prices require a new snapshot identifier and apply only to newly observed records; historical records are not repriced except for the explicit corrective-repair exception above.

The embedded catalogs include the inspected ccusage 20.0.14 Claude-oriented reference and approved ccusage 20.0.17-referenced Codex `fast` rates. The corrective 2026-08-20 Codex snapshot retains the earlier base and long-context boundaries and adds exact `gpt-5.3-codex-spark` parity with ccusage 20.0.17: GPT-5.3 Codex input, output, and cache-read rates with its 2x fast multiplier and no long-context tier. Contract repair assigns that new snapshot only to exact Spark observations; the earlier cited snapshot remains unchanged.

`usage_model_prices` stores optional threshold and above-threshold component rates. Calculator v2 evaluates each Usage Record independently from non-cached input plus cache read, keeps the exact threshold on the base tier, and uses long-context rates only above it; compaction can return a later record in the same Session to the base tier. This preserves trend semantics while matching the frozen request-price boundary. No catalog creates a runtime ccusage, network, or page-render dependency.

Each new Usage Record also freezes its first-observation Project attribution. A currently discovered Git root produces a `git:<canonical-root>` key; otherwise a resolved workspace produces a `path:<canonical-path>` key; missing evidence stays `unassigned`. Workspace ID, name, canonical path, Git root, basis, and attribution time are snapshots rather than live Project joins. Conflict updates preserve them, so a later Git initialization, path move, or workspace enrichment can affect only new records. Current `workspaces.git_root` follows current filesystem evidence and may change without rewriting historical usage. Legacy or previously unassigned records are not reconciled automatically.

### Analytical Read Models

Activity time is derived separately from usage and cost. Valid Activity Event timestamps form per-Session segments: a gap of exactly 30 minutes remains continuous, while a greater gap starts a new segment. Segments end at the last observed event, are clipped with inclusive-start/exclusive-end range boundaries, and are merged across concurrent Sessions before estimated active seconds and the longest active segment are calculated. Observed Session span remains a separate first-to-last-event value. Single-event segments contribute zero inferred duration, and no value is extended to the current time. Local day and Monday-week boundaries use an explicit IANA timezone.

The Sessions Dashboard read model normalizes `view`, `source`, `metric`, `from`, and `to` GET state before querying Usage Records. Its accepted Source options are loaded in Source-ID order from registered Claude/Codex adapter sources, with `All` first; an unknown stable key falls back to `All`. Exact facts use `sources.kind`, while `provider_kind` remains only the adapter semantic for rules such as Claude synthetic exclusion and may be shared by personal Codex and Codex Company. Daily uses 30 inclusive local days, Weekly uses 12 Monday-based local weeks, and Cumulative uses monthly running buckets from the earliest eligible real-model usage date. Valid paired custom dates replace only the bounds; malformed, partial, or reversed pairs retain the selected view, source, and metric while falling back to the view default. Token and priced-cost totals include every direct real-model record, including maintenance and subsession records, while the usage-linked Session denominator includes only primary work Sessions. Claude records whose raw model is exactly `<synthetic>` remain persisted but are removed at the dashboard query boundary from dates, totals, coverage, breakdowns, and Session counts. Records without usable timestamps or supported pricing remain explicit coverage limitations rather than zero values.

The same read model normalizes `breakdown=source|model|project`. It groups by stable source key with configured display name and separate provider cue, normalized model while retaining raw identities, or the immutable Usage Record Project key; current workspace joins may enable a browse link but never change a historical group. Personal and company Codex therefore remain separate source rows. Compatible shares use the selected supported token total or priced-cost total, and the `All` compatible total equals its source-row sum. The first eight ranked groups remain visible and additional groups use native disclosure. Source trust consumes the persistent latest FEAT-0068 source attempt, success, status, and bounded error plus source-file stale/error evidence. Completed/empty is current; unavailable, configuration error, or scan failure requires attention; legacy rows without a source-level result retain file-status fallback. Previously calculated records remain visible and the last source success remains distinct from the failed attempt.

Current-month projection remains a non-persisted compatibility calculation in the read model but is not rendered by the Sessions Dashboard. `calendar-elapsed-v1` divides source-scoped compatible MTD estimated cost by the timezone-aware fraction elapsed between local month start and next local month start. It requires three complete local days, a Cost view whose range contains today, and at least one priced Usage Record. Calculation time, source scope, input total, elapsed fraction, formula version, coverage, and freshness state travel with the internal value. It never updates Usage Records or their price snapshots and never runs for a historical-only range.

### Synchronization And Session Inventory Read Models

The Sessions inventory owns a Session-only incremental synchronization action. It scans every validated source in the ordered private Session-source registry—currently Claude, personal Codex, and Codex Company—regardless of the selected inventory filter, and does not scan Local Context sources. Each accepted file carries independent Session-projection, Usage-normalizer, and generalized-reference versions. A version mismatch reparses the source files needed by that concern but writes only the owned derived lane; a natural file change, missing Session mapping, forced scan, or eligibility repair still refreshes every affected lane. Each source has an independent transaction, source-file set, stale-deletion boundary, and persistent latest attempt/success/status/error health. Unavailable or invalid sources skip stale reconciliation and retain their normalized data; an unexpected failure rolls back only that source. The existing JSON API returns a bounded per-source report plus complete, partial, or failed aggregate outcome. An additive NDJSON endpoint emits bounded source key/label, repair kinds, and throttled file counts to the same Sessions result region; it emits no paths or content, and callback/display failure cannot change synchronization. The Sources inventory owns the wider scan that appends every enabled Local Context root without weakening those Session-source commit boundaries. Both web actions retain the source-file freshness check. An otherwise-current source is reparsed only when its versioned Atlassian evidence scan or enabled configured-Site fingerprint is missing or changed; once all owned contracts are current, the source is skipped.

Sessions browsing derives its ordered peer source controls from the same registry
and uses the stable source key, never provider kind, as GET and query identity.
`all` plus each source-specific view share one primary-work/primary-role
denominator across headline count, inventory, pagination, and Project grouping;
the inventory adds no timestamp cutoff. Unknown source keys and missing workspace
IDs normalize to a valid URL while preserving the other valid scope. Ordinary
inventory and Pinned cards expose source-specific `CL`, `CX`, or `CC` cues with
the configured display label in accessible text instead of repeating it visibly.
Detail headings and normalized or lazy Subsession projections derive the same
cue and provenance class from stable source identity rather than shared provider
kind. Their configured source display label remains in accessible cue text rather
than being repeated visibly in detail headings or parent-detail Subsession rows.
The child projection carries the existing `user_message_count` beside
`event_count`; a lazy Claude child derives the same question count from its
source events. The detail row renders question, event, then activity date.
Detail links retain the selected source/workspace only as return orientation.

### Adapter-specific Rules

- Import Claude primary and direct `subagents/*.jsonl` files with distinct Session
  roles and a source-backed parent relation. Deeper descendants of the native
  `subagents` tree, including `workflows/**/journal.jsonl`, are internal artifacts
  rather than Session candidates. A successful scan excludes them from the valid
  source-file set and reconciles any prior false normalized Session without
  deleting the native artifact. Use the direct child filename stem as child
  identity; its record-level `sessionId` may denote the owning parent.
- Use the first Codex `session_meta` record as the file identity because a rollout file may contain older embedded metadata.
- Read Codex parent and Git context from that same primary metadata record; later embedded metadata never replaces the file identity.
- Treat first-record `source.subagent.other=guardian` as provider-internal approval activity. Retain its normalized Session identity, parent relation, and direct Usage Records under maintenance plus metadata-only policy while excluding its prompts and decisions from Activity Events and ordinary Session/Subsession presentation.
- Index human and assistant message text plus tool names; do not index opaque tool arguments or result payloads. Approved Atlassian read results may be inspected ephemerally only through bounded URL, remote-ID, and title field/container allowlists, and only the resulting locator evidence is persisted.
- Preserve historical `cwd_raw` independently from an optional resolved current Project relation.
- Handle a Session file that is still growing or partially written without discarding previously valid records.

### Session Policies

Claude and Codex histories are parsed into normalized Sessions and Activity Events. An in-app Task Runner Run persists the selected runner's normal native Session; the internal Run header classifies that source-backed primary as maintenance and links it uniquely to the Run ledger. Its child Sessions inherit maintenance and metadata-only policy through the resolved parent relation without taking the Run FK. Maintenance Sessions stay excluded from events, search, workflow statistics, and the Sessions Dashboard primary-work Session denominator, while their direct Usage Records remain eligible for token and estimated-cost totals:

```text
[LOCALBRAIN_RUN: lb-<12 hex characters>]
[MODE: maintenance]
```

Provider-internal Codex guardian histories use the same maintenance and metadata-only exclusion boundary without a Run link. Their source metadata, parent relation, and direct Usage Records remain available for provenance and usage totals, while repeated approval-review prompts and decisions never appear as user questions, conversation events, or ordinary Subsessions.

Claude and Codex subsessions are normalized as source-backed Session rows with a retained source parent identity and a nullable resolved parent self-reference. Unresolved, unsafe, and deeper child relations remain stored but do not fall back to top-level presentation. Only primary work Sessions contribute to global Search, Session-derived statistics, Workstream organization candidates, Workstream maintenance retrieval, or Atlassian URL evidence. Maintenance and subsession output can never rediscover its own external-sync targets.

Session detail presentation selects normalized `message` events in source sequence for primary Sessions and eligible direct children. Codex response-only turns exclude source-expanded repository/environment instructions and `<skill>` bodies before choosing the visible user-authored prompt, preserving the user's literal `$skill` request while keeping provider context out of titles, conversation, search, and reference evidence. A copied presentation view renders only user and assistant text through the shared Markdown contract without an owning Local Context source; raw source JSONL, source-relative unresolved references, `tool_call` rows, tool names, and the Session's complete retained event count remain unchanged. Parent details list same-source direct children as Subsessions; child details resolve only to a same-source primary parent. `/sessions/{id}/subsessions/{file}` is the canonical lazy compatibility route. Existing Claude `/subagents/` links redirect to that route, which still reads the source-native `subagents/` directory and uses the same message-only Markdown presentation.

Session branch metadata is stored per Session from authoritative JSONL. Workspaces retain the currently discovered canonical `git_root` of the containing repository and do not store a branch value; historical Project attribution belongs to Usage Record snapshots instead.

### Local Context Sources

The `context_roots` registry owns folders, individual files, and Apple Notes sources shown in Local Contexts.

- Folder registration scans supported content recursively.
- Overlapping parent and child folder roots are rejected to keep document ownership unambiguous.
- Hidden and generated directories such as `.git`, `node_modules`, `dist`, and `build` are excluded.
- Removing a source disables browsing and search and clears its derived Atlassian URL sightings without deleting original local files or stable Atlassian Items.
- Re-adding a previously removed path restores and refreshes that source.
- Individual text files are registered independently from folder roots.
- PDF text is currently indexed only when macOS Spotlight exposes readable content.
- Unsupported files remain registered with an `unreadable` state and do not create preview documents.
- Apple Notes indexing records account, folder, title, plaintext, and modification time after macOS grants Automation access.

## Current Implementation Baseline

Implemented in the current vertical slice:

- additive SQLite startup migrations over the local index
- user-created Workstreams and nested Threads
- versioned checkpoints with linked-resource snapshots
- Thread-first links to Sessions, Local Contexts, projects, local paths, and external references
- Workstream-level links for resources shared by multiple Threads
- manual Jira, Wiki, Slack, Git, document, and generic URL references
- reversible keyword-based Session and Document link Suggestions
- Workstream-first Dashboard and separate Sessions Dashboard
- maintenance Session exclusion and source-neutral Claude/Codex subsession normalization
- source-neutral Claude/Codex Usage Records with immutable local trend-cost snapshots
- reproducible Sessions Dashboard usage summary, MTD context, GET scope, and Daily, Weekly, or Cumulative token/cost history
- durable Maintenance Task Runner history, Claude/Codex external-sync parity, streaming result handling, cancellation, and reviewable structured output
- deterministic SQLite/FTS5 retrieval without hard candidate or evidence-count caps
- normalized many-to-many Thread resource matches with reusable fingerprints and deduplicated evidence
- source browsing for folders, files, and Apple Notes
- context-aware full Document reading with an owning FOLDERS tree, bounded non-FOLDERS fallback, and source-preserving Markdown presentation
- safe Markdown conversation reading for visible Session and Subsession user and assistant messages without Local Context source guessing
- Atlassian stable source memory, bounded Session/Local Context URL evidence,
  strict zero-configuration local Site/Item admission, Site-first Explorer
  hierarchy with read-only canonical-URL container hints, grouped local search,
  Item detail, notes, Topic/Tag classification, exact Workstream/Thread links,
  explicit partial Space discovery, and explicit known-Item refresh previews
  without implicit remote ingestion or model calls

Open implementation work is tracked in the [Project Backlog](../../plans/project/backlog.md).

## Architectural Constraints

### General Constraints

- LocalBrain remains local-first and single-user during the MVP.
- External integration starts read-only.

### External Access And Synchronization Constraints

- External Source Instance registration is durable local state, while its latest capability observation is rebuildable operational state. Only version-controlled policy may map a logical operation to an external target.
- Capability inspection is explicit. Application startup, browse, search, and ordinary local preview do not inspect or refresh external capabilities.
- Static Jira/Confluence URL classification is configured-domain independent and
  local-only. It normalizes the bounded HTTP(S) host/path, rejects credentials
  and REST endpoints, applies path/query Item identity before structure identity
  and then Site-family root, and exposes no raw query or JQL. A parser result
  grants no access or persistence authority by itself. Explicit evidence Sync
  admits `item` into the passed Site/Item path and `structure` into separate
  reference, privacy-safe URL, and source-evidence owners keyed by
  Site/service/kind/identity; `site` remains report-only. Registration consumes
  its separately approved Add families and may still persist its passed
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

### Persistence And Portability Constraints

- User review state and source provenance must survive rescans and suggestion refreshes.
- A failed maintenance Run must not clear the existing review queue.
- Historical source paths must remain visible when their current Project relation is missing or changes.
- The SQLite schema and runtime data must remain portable to a later desktop wrapper.
- Desktop packaging must not obscure data location, permissions, backup, or shutdown behavior.
