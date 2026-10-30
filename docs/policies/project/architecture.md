# Project Architecture

## Purpose

This document owns LocalBrain's durable implementation shape: runtime layers, package responsibilities, source adapters, persistence, ingestion behavior, and the current capabilities and their owners.

Product terminology and organization rules are defined in [Product Model](product.md). In-app maintenance execution is defined in [Maintenance Task Runner](../operations/claude-task-runner.md).

## Runtime Shape

- Runtime: local web server with browser UI, or Tauri window with a bundled backend
- Backend: Python and FastAPI
- Database: SQLite
- Search: existing SQLite FTS5 plus optional local Qwen semantic ordering and lexical exact-identifier admission
- Context Search: isolated Qwen4B/8B native tool loop over admitted Local Context and received copies; request/page-memory dialogue, no embedding prerequisite or chat schema
- Frontend: server-rendered Jinja2 with small JSON API interactions
- External integration boundary: approved MCP Gateway and source-specific adapters
- Desktop packaging: Tauri 2 and a PyInstaller Python 3.11 bundle, Apple Silicon

The standalone test edition admits Sessions, Sessions Dashboard, Local Context,
search, Context Search, settings, onboarding and bundled English Docs. Its immutable runtime boundary excludes the
unfinished development surfaces; [Desktop App And Settings](desktop-app-and-settings.md)
owns lifecycle, local authentication and source/settings contracts.

The [installation/storage contract](installation-and-storage.md) owns independent
macOS source/tool/wheel setup and optional local-model requirements. Packaged
`serve`, `doctor`, `models`, `simulate`, `search`, `learning`, and `storage` commands use the same
configured runtime paths. Public model assets are shared within the local user
account; LocalBrain owns its model metadata and optional Python dependencies.
Runtime state is rejected inside repositories, uses owner-only permissions, and
has bounded migration-copy retirement after successful committed initialization.
Ordinary startup creates no permanent log or evaluation archive.

`config.py` separates durable data, private rebuildable cache and development
archive roots. `storage_layout.py` owns explicit recognized-directory moves,
destination-conflict refusal and expired-cache retirement under existing writer
locks. Packaged readers and simulation use the configured cache root. Saved
Run reports remain durable data; development archives are never normal startup
outputs. Shared public weights and the primary DB are outside layout migration.

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

- `app_docs.py`, package `content/docs/`, `templates/app-docs.html` and `static/app-docs.css`: fixed user-guide registry, canonical English content and in-app reader. [In-App Documentation](app-documentation.md) owns the product routes, shared Markdown link exception, package delivery and content boundary.
- `preferences.py`, `source_settings.py`, `settings_web.py`: shared local preferences,
  optimistic configuration revisions, source registration/reconnection and UI APIs.
- `source_sync.py`, `session_sync.py`, `context_sync.py`, `local_operations.py`: independent
  completion-based Session and Context scheduling, persisted health outside the main DB,
  and process/thread exclusion for mutations.
- `edition.py`, `desktop.py`, `desktop/src-tauri/`: route/runtime admission, per-launch
  local authentication, native window/process lifecycle and bundled resources.
- `keyword_search.py`, `model_setup.py`, `storage_recovery.py`: model-free eligible
  FTS retrieval, explicit cancellable public-model installation, private backup,
  restart-only restore and bounded owned-cache cleanup.
- `learning.py`, `learning_cli.py`, `learning_web.py`: reviewed local packet
  intake, immutable lessons/source snapshots, personal attempts, deterministic
  daily selection and native home/library/reader forms. Durable state is in the
  main DB; this flow does not invoke search, generation or external retrieval.
- `natural_search/`: eligible read-only source snapshot, original-span molecularization,
  private SQLite/FTS/vector generations, persistent offline Qwen encoder, explicit
  condition interpretation, parent-ranked retrieval and Sync refresh worker.
  `main.py` owns loopback routes and app lifecycle; templates and `natural-search.js`
  own the shared header and evidence navigation. Keyword search is the default;
  AI search is explicit. The legacy `/search` URL redirects to keyword mode in
  the desktop edition and remains compatible in development web. [Natural-Language Search](natural-language-search.md)
  owns the detailed source, score, input-budget, refresh and recovery contracts.
  Laya and Qwen Reranker are development comparisons, not runtime dependencies.

- `work_state.py`: pure source-claim/reported-state projection: unchanged
  synthetic-supplied v1 plus model-aware v2 provenance/lifecycle effects, governed
  by [Source Claims And Work State](source-claims-and-work-state.md).
  Separates exact anchors, attributed interpretations, scoped target bindings and
  current state; preserves historical pending claims, partial order, corrections,
  unresolved support and replay identities. The projector has no source reader,
  model call, persistent ledger, automatic target discovery or product consumer.
  It cannot certify the truth of a supplied interpretation or unblock admission.
- `work_claims.py`, `work_claim_assessment.py`, `work_claim_trial.py`: separately
  invoked synthetic-only extraction/binding adapter, conditional versus end-to-end
  scoring and bounded failure-preserving evaluation. No private or UI consumer.
  This adapter invokes the installed generative model during explicit trials;
  it is separate from the pure state projector and the affinity-map producer.

- `work_context_model.py`, `work_context.py`, `work_context_staged.py`,
  `work_context_choices.py`, `work_context_classified.py`, `work_context_selected.py`, and
  `work_context_evaluation.py`:
  explicit public-model installation, independently verified offline generation,
  exact quoted work-unit/pair-relation contracts and synthetic-only admission
  evaluation. The current [quoted work-context contract](#quoted-work-context-model-contract)
  owns the model, packet, generation and output boundaries. The evaluation opens no source
  DB and introduces no product consumer, training, organization write or automatic
  inference. Quoted fields retain role and locator; validity is not entailment.
  Staged inference validates intermediate source quotes and keeps full original
  context; it never fills missing output evidence. Thinking-mode protocol strips
  reasoning before decoding/storage. Strategy/stage/runtime identities separate
  caches; development and holdout gates are independent.
  MPS generation uses eager attention; the attention implementation is part of
  the runtime fingerprint.
  The installer admits only the allowlisted pinned 4B/8B catalog. Verification
  resolves the owner and model-specific assets, and inference identity uses that
  verified model; a 4B default must not label an 8B result.
  `model_cache.py` resolves public pretrained assets in the user-wide Hugging
  Face Hub cache. Installation metadata remains in the explicit private model
  root: the directory owner marker stays v1, while a
  `localbrain.work-context-model.v2` model manifest has a Hub-relative snapshot.
  Legacy v1 manifests remain readable. Verification confines selected assets to
  their model repository and preserves their pinned hashes and inference identity.
  `model_catalog.py` pins the supported public identities and feature requirements;
  `model_installation.py` owns independent LocalBrain embedding setup with a
  `localbrain.semantic-model/v1` Hub-relative manifest. The embedding adapter
  also accepts compatible older app-local and Hub-relative snapshot manifests.
  Private vectors and outputs remain in LocalBrain's runtime storage.
  App cleanup never owns deletion of shared public weights.
  Future trained adapters/checkpoints require separate durable project storage
  under the privacy policy.
  The opt-in classified strategy separates model-selected source roles and work
  membership from serialization. Its finite answer-code decoder constrains syntax,
  not truth; source spans are not work-unit boundaries. Original context and
  explicit model-selected citations feed the existing quote validators. Unknown
  membership, ambiguous spans and packet/case bounds fail without source loss
  being disguised as complete reconstruction. No private producer consumes it yet.
  The separate selected strategy chooses whole-conversation anchors before their
  field evidence through the same bounded decoder; it preserves anchors without
  silently filling missing citations or changing the classified comparator.
  The opt-in `work_context_evidence.py` strategy assesses literal source facets
  before grouping independently resumable outcomes. Pairwise anchor/membership
  checks refuse ambiguous bridges; unit audits inspect proposed fields against
  original records. Continuation requires model-selected goal support,
  compatible scope and explicit linkage, with automatic uncertainty on support
  the model judges missing or conflicting. This does not guarantee recognition
  of semantic errors. Only model-selected facts are serialized. Its semantic
  label decoder explicitly admits up to 32 characters while legacy default codes
  remain bounded to eight; both keep the eight-token/EOS grammar.
  Evidence evaluation has failure-preserving, hashed terminal observations,
  changed-config/corrupt-cache refusal and bounded incomplete-case retries.
  Original development and compositional gates are separate. Holdout requires a
  complete identity-matched report whose observations/split scores are revalidated;
  primary semantic review remains required. No product consumer is admitted by
  valid syntax, automatic withholding or same-model auditing alone.

- `work_context_diagnostic.py`: opt-in fixed-model synthetic protocol diagnosis,
  separate from extraction/admission and any product producer. Its frozen matrix
  independently controls option order and numeric mapping; label/text responses
  keep the same source context and alternative meanings. Semantic, protocol and
  literal-citation results are distinct. Prompt/template hashes and actual answer
  token IDs make rendering auditable. Completed wrong/invalid/refused observations
  remain cached, changed configurations refuse reuse, and cumulative attempt/time
  budgets survive clean interruption. An unclean in-flight reservation blocks
  automatic restart. Diagnostic completeness never grants model admission.
  No database, holdout, new dependency, model or UI is involved.

- `work_role_comparison.py`: a separate matched synthetic formulation diagnostic.
  It reuses unchanged evidence-first facet definitions and relation inference,
  contrasting independent questions with one complete role-set decision. Compound
  roles, identical focused spans with different later context, and canonical/
  reversed option orders remain explicit. Scoring compares role sets per context,
  not incompatible raw call counts; relationship controls are scored separately.
  An execution meter wraps existing `choose` without changing the decoder or
  existing strategies. Every choice reserves cumulative call/time accounting;
  incomplete observations have bounded attempts, while completed refusals/errors
  are hashed and replayed. Existing private evaluation storage ownership applies.
  Prompt/template/token audits are synthetic diagnostics, not private-source
  discovery, model admission, training or a product producer.

- `session_simulation.py`, `session_simulation_model.py`, and
  `session_simulation_graph.py`: explicitly invoked full-Session experiment;
  source-read-only inventory, separately owned replayable cache, verified local
  embeddings and experimental two-resolution affinity communities. The
  [simulation producer contract](#full-history-simulation-producer)
  owns current report/lifecycle definitions; the [Developer Guide](developer-guide.md#full-history-simulation-and-model-trials) owns command operation. No automatic preparation, source migration,
  production identity or causal-lineage inference is introduced.
  Source messages are exhaustively chunked (1,800 characters by default), encoded,
  and linked by thresholded cosine nearest-neighbor similarity. Weighted Louvain
  first forms coarse communities, then runs within each parent to form finer
  communities. These are nested similarity groups, not two successive
  work-identity merges. Disconnected components and singletons remain explicit;
  one Session can contribute chunks to several groups. Group counts are derived,
  not a fixed number of Workstreams.
  Inventory uses bounded character read-ahead with unchanged exhaustive chunk
  boundaries. The ordered v2 grouping engine canonicalizes node and neighbor
  insertion for each Louvain pass, including nested communities; fixed RNG seed
  alone does not guarantee cross-process replay. Every cosine-distance batch is
  validated for finite, valid values. Grouping version changes do not invalidate
  otherwise compatible cached embedding vectors.

- `session_affinity.py`: passive whole-history simulation consumer. It validates
  the existing source-bound owner under a shared nonblocking lock and rechecks
  the full admitted source manifest. One process-memory index is invalidated by
  report or source DB/WAL file changes; it creates no second runtime owner,
  persistent corpus, model call or organization table. Snapshot-scoped coarse
  groups, subgroups and occurrence-preserving Session evidence have complete
  paged text access; a separate whole-scope map projection aggregates actual
  undirected affinity across text-page boundaries. Exact quotes
  are independently resolved from current original records. Stale/expired/
  invalid output never presents old evidence as current and triggers no work.
  [affinity reader contract](#affinity-reader-contract-and-states)
  owns bounds and states. Group labels are representative Session titles, not
  generated category names or confirmed work identities.

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
- `src/localbrain/skill_observations.py`: durable skill evidence, event replay guards, and the Insights use/reference Session ranking
- `src/localbrain/personal_insight_evidence.py`: read-only, bounded Claude/Codex primary-work message selection for later personal insight Runs; it produces a versioned private evidence value and reviews current references without a new table or model call
- `src/localbrain/personal_insight_guidance.py` and `personal_insight_guides/`: product-neutral, versioned core and category playbooks, selective routing, and strict finding/no-finding/evidence-request values. `personal_insight_guide.md` is the historical v1 resource
- `src/localbrain/personal_insight_runs.py`: independent analysis-only Run lifecycle, frozen Session evidence and selected guide provenance, no-tools CLI invocation, validated results, and private Markdown artifact generation
- `src/localbrain/personal_insight_usage.py`: ephemeral analysis usage normalization, exact Codex source binding, metadata-only accounting projection, and retained-observation recovery
- `src/localbrain/workstreams.py`: Workstreams, Threads, checkpoints, resources, links, Suggestions, and retrieval mappings
- `src/localbrain/workstream_candidates.py`: pure candidate identity, supplied
  pair/member validation, revisions, evidence/time/coverage descriptors, and
  bounded serialization; no database discovery or organization mutation
- `src/localbrain/work_reconstruction.py`: isolated experimental text extraction,
  semantic grouping, exact synthetic corrections, and metadata-only comparator
- `src/localbrain/work_reconstruction_scoring.py`: independent expectation
  validation, integer quality measures, and identity/assignment replay measures
- `src/localbrain/work_reconstruction_input.py`: explicit manifest validation and
  bounded read-only access to already-indexed selected records
- `src/localbrain/work_reconstruction_preparation.py`: explicitly invoked,
  prediction-independent chronological sampling, frozen manifests, omission
  accounting, and unknown-assessment placeholders; no independent answer key
- `src/localbrain/work_reconstruction_experiment.py` and
  `scripts/experiment-work-reconstruction.py`: opt-in local comparison command,
  supervised resource bounds, and private owner/expiry-bound result publication
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
- `src/localbrain/session_chart_preferences.py`: scoped, bounded user-selected Chart visibility in the private primary DB, independent of observations and browser camera state
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

Each Session profile uses the existing numeric `sources.id` independently from
`provider_kind`, which chooses parsing and usage normalization. Multiple profiles
can use Codex without sharing Session or Usage identity. The redundant `kind`
column is removed. A one-time migration converts structured dependents to the
existing PK; no alias field or mapping table remains. Event/Usage PKs are retained
by matching existing native unique keys on re-ingestion.

The ordered Session list is owned by private `session-sources.toml` in the data
directory. Version 2 uses `source_id`, name, provider, root, color and optional
Home/enablement. Fresh installation writes an empty list; an established database
can seed retained registrations. Valid v1 files migrate without moving originals
or replacing record IDs. Color/order project into `sources.profile_color` and
`profile_position`; settings and source filters share numeric IDs and TOML order.
Invalid identities, provider conflicts or occupied-root changes preserve retained
data. Provider-level scan entry points collect each registered matching profile.
The [source settings contract](desktop-app-and-settings.md#generalized-session-profiles)
owns editing, persistence and reconnect rules.

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

The complete effective-schema map, physical and application relationships, lifecycle/recovery classifications, and eleven subject catalogs are owned by [Data Model](data-model.md). This section keeps only the architectural grouping and cross-layer behavior.

The packaged consumer form is owned by [Schema Presentation](schema-presentation.md). Its generator applies fresh DDL and the compatible structural/index path only to SQLite `:memory:`, combines those facts with Data Model semantics, and emits derived JSON. Application consumers load that package data; they do not inspect a user database or repository Markdown.

Bounded database values use `src/localbrain/value-registry.json` as their executable physical/logical/presentation authority. The generated [Value Dictionaries](data-model/value-dictionaries.md) remain the human-readable subject projection; runtime code loads the registry and never parses Markdown.

`System > Schema` serves the read-only `/schema` Explorer from that package data. Optional `area` and `table` query values select one of the eleven owner areas and one owned table; invalid state normalizes to the nearest valid overview. Server-rendered links and catalogs remain complete without JavaScript, while the route-scoped module preserves shell continuity, history, focus, strict locally packaged Mermaid rendering, and bounded presentation-only diagram zoom. The route has no SQLite connection, row preview, external asset, SQL, edit, or cleanup action.

The current schema groups data into these responsibilities:

| Responsibility | Current entities |
| --- | --- |
| Source inventory | `sources`, `source_files`, `external_source_instances`, `external_source_capabilities`, `context_roots`, `workspaces` |
| Indexed activity | `sessions`, `activity_events`, `session_reference_scans`, `session_reference_evidence`, `usage_records`, immutable usage price snapshots, `context_documents`, FTS5 search tables |
| Reviewed learning | immutable lesson/source revisions in `learning_lessons`, personal attempts in `learning_attempts`, and stable-key visibility in `learning_visibility`; [Personal Learning](data-model/personal-learning.md) owns their table contracts |
| Workflow correction | append-only `workflow_assertions` keyed by stable Episode boundaries |
| User organization | `workstreams`, `threads`, `checkpoints` |
| Linkable resources | `local_resources`, `external_resources`, Workstream and Thread links |
| Atlassian source memory | domain-first `atlassian_sites`, optional `atlassian_site_bindings`, access-optional `atlassian_spaces`, strict one-to-one `atlassian_items`, Item URL/remote/local/evidence owners, separate `atlassian_structure_references`, `atlassian_structure_reference_urls`, and `atlassian_structure_reference_evidence`, plus Item role rows and one bounded non-archived reference row in shared FTS |
| Review workflow | `suggestions`, checkpoint resource snapshots, Thread resource matches |
| Run execution | independent `maintenance_runs` / `external_sync_runs` and `personal_insight_runs` histories, with separate artifact roots under the runtime data directory |

Resources are canonical entities. A Session or Document is stored once and may relate to any number of Threads. Relationship-specific evidence is stored separately so the resource payload is not duplicated.

Checkpoint records are versioned, user-confirmed resume states. Confirmation captures a snapshot of resources linked to the Workstream and its Threads at that time.

## Ingestion Contract

This family owns source capture, normalization, reconciliation and explicit
collection. Workflow projections, user corrections and analytical consumers
have separate contracts below.

Original Claude and Codex JSONL remains the authoritative Session source. LocalBrain stores normalized searchable text, selected metadata, source paths, source line numbers, and deterministic IDs so the index can be rebuilt. New provider-native event and Usage identities are scoped by the numeric Source ID when profiles share an adapter. Re-ingestion matches retained native unique keys to preserve existing event and Usage PKs; the one-time upgrade may read old string keys solely to migrate dependent references.

### Ingestion Module Ownership

- `ingest/contracts.py` owns parsed DTOs and provider revision metadata. It imports
  neither native adapters nor synchronization services. `common.py` owns shared
  identity, JSONL, text/title helpers and the existing maintenance classifier.
- `ingest/providers/` decodes Codex and Claude native formats. Provider-specific
  replay, source-adjacent configuration and pricing selection remain here.
- `ingest/evidence/` extracts reference candidates, approved tool-result evidence
  and skill signals from source data. It does not reconcile persisted evidence.
- `ingest/sync/sessions.py` orchestrates one admitted Session source;
  `session_store.py` owns Session/activity/Usage persistence and lifecycle;
  `contexts.py` owns folder/file/Notes ingestion; `storage.py` owns shared
  source/file/workspace/search operations and revision admission; `control.py`
  owns the single cancellation context and callback-safe progress delivery.
- `ingest/scanner.py` composes adapters, resolves registered sources, reports
  outcomes and owns the outer transactions. Each registered Session source
  commits independently. Normal Context collection keeps its existing grouped
  transaction; direct `scan_context_root(connection, ...)` uses the caller's
  transaction. Lower services do not import the coordinator or create commits.

Session result revisions are nullable positive integers in
`source_files.session_contract_version`; Codex and Claude increase independently.
They identify stored results, while the executable contains one current parser
per provider. A newer stored revision stops that source before projection/lifecycle writes,
including forced Sync and same-source reconnection. Null or lower revisions need
actual Session repair; a Session-only repair leaves current Usage unchanged.
[Source Registry And Scans](data-model/source-registry-and-scans.md) owns the
storage constraint, exact legacy conversion and bounded failure contract.

Source edits update a development server only after its process reloads or
restarts. A packaged native backend contains its own code copy and must be
rebuilt and replaced. New revision admission does not retrofit old executables.

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
  later reparse, and keeps structure/site as generic URL targets. Pure
  classification and Session projection create no Atlassian structure-reference
  or Site row; explicit Sync owns the separate admission below.
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

### Session Eligibility

Provider parsing is followed by one shared meaningful-Session eligibility gate. A
parsed file must contain at least one normalized Activity Event, direct Usage
Record, or admitted skill observation; title, name, identity, timestamp, cwd, branch, or other metadata
alone describes an empty native stub. A successful readable-source scan stores no
normalized Session or source-file evidence for a new stub and reconciles an
existing empty projection after reparsing current sibling files. The source JSONL
is never deleted. Because an ignored stub retains no freshness row, later syncs
inspect it again and import it once Event, Usage, or admitted skill observation evidence appears.

### Usage Normalization And Repair

Token usage is a separate derived-record lane from searchable Activity Events. Both adapters preserve one stable source-record identity, the raw model name, non-cached input, output, cache-write, cache-read, reasoning, source-total, and normalized-total semantics when those values are available. Claude input is already non-cached and its cache creation and cache read values remain additive. When Claude reports a zero cache-creation aggregate that contradicts a positive internally consistent ephemeral breakdown, the adapter uses the breakdown and records that bounded fallback. Each Codex `token_count` event contributes its direct `last_token_usage` when available; `total_token_usage` is Session-cumulative and is subtracted from the preceding observation only as a fallback. Spawned or forked subsession replay prefixes seed that cumulative baseline but do not produce copied records. The dashboard ignores zero request deltas even when the source total repeats earlier nonzero history; source input has cached input subtracted, and reasoning output remains an informational subset of output rather than an additional total.

Every directly observed Usage Record is eligible regardless of Session class or role. Maintenance Sessions and subsessions therefore remain excluded from ordinary Search and workflow statistics while still contributing their own direct usage. Current Claude and Codex observations carry a `direct` aggregation scope. LocalBrain does not persist a second parent rollup, so parent and child direct records are each counted once; the reserved `includes_children` scope requires a downstream rollup to exclude covered child records if a future source explicitly provides such an aggregate. A repeated source record updates one deterministic Usage Record, and malformed later evidence cannot erase a previously valid record. Session source files record the usage normalizer contract that processed them, and each Usage Record records its independent normalizer version. Unchanged file metadata is current only when this contract version also matches.

When a normalizer contract changes, ordinary Session synchronization performs a versioned Usage-only repair rather than requiring a user-facing aggregate reset. If any current file for a source has an older Usage contract version, synchronization reparses every current file for that source and reconciles their complete native Usage Record union inside one source-level savepoint: matching identities update, new identities insert, and obsolete source identities delete. It does not replace the Session, Activity Event, search, Atlassian evidence, or generalized-reference lanes merely because the Usage contract changed. This boundary preserves all observations when one Session identity spans several files. A repair identity inherits the closest prior price snapshot and frozen Project attribution unless an approved corrective producer explicitly assigns a new immutable snapshot to repair an invalid token or service-tier contract. Ordinary new records under an unchanged contract receive the snapshot and current Project evidence available when first observed. Immutable snapshot/model price lookups are cached for one source repair and each Session's Usage upserts are issued as one batch without changing identity, ordering, values, or savepoint rollback. Any parse or persistence failure rolls back the complete source replacement and does not advance its source-file contract versions. Source freshness retains the size and modification time observed before parsing, so bytes appended to an active JSONL during the read remain detectable on the next synchronization. The next unchanged synchronization skips all now-current files, making the repair idempotent. Native stale-Session and Usage reconciliation preserve independent insight accounting parents and their Usage Records.

Estimated USD cost is a local API-equivalent trend estimate, not billed spend or subscription credit use. Each Usage Record retains an immutable price-snapshot identifier, calculator version, calculation time, and explicit `priced`, `unpriced`, `partial`, or `failed` state. A growing source record normally keeps its cited snapshot. A corrective producer can reparse native usage and assign newly seeded official snapshots to existing records only through an explicit correction; prior snapshot rows remain immutable, and Usage IDs, token counts, and frozen Project attribution are preserved. Later publisher price changes require new dated snapshots and an explicit historical correction when appropriate.

The legacy ccusage 20.0.14/20.0.17 catalogs remain as historical evidence. Current pricing comes from frozen model-specific OpenAI and Anthropic entries with published effective dates, except for the explicitly chosen Spark and historical Fast long-context proxies. The Codex adapter reads `thread_settings_applied` in file order: `priority`/`fast` uses Fast, `default` uses Standard, and unmarked/unsupported settings fall back to that source home's current config with provenance recorded in `capability_json`. GPT-5.6 Terra/Luna change on July 30, Sol on August 21, GPT-6 Astra starts on September 3, and GPT-6 Sol/Luna start on September 22. The pre-July-30 GPT-5.6 Priority 2x multiplier is labeled as a historical inference because an archived publisher tier table was unavailable. For other models, an exact model/tier/context combination with no published price remains partial; a Standard rate is not silently substituted for Fast. Exact GPT-5.3-Codex-Spark has no independently published API rate; the explicit proxy borrows ccusage 20.0.17's GPT-5.3-Codex Standard or Fast estimate in a separate labeled snapshot. Startup reprices previously unpriced Spark records and eligible partial Fast long-context records with explicit proxy snapshots, retaining Usage identity, tokens, and attribution. The dashboard excludes persisted Codex zero-request rows whose source total repeats earlier history, preserving their local source and database evidence.

`usage_model_prices` stores optional threshold and above-threshold component rates. Calculator v3 evaluates each Usage Record independently from non-cached input plus cache read, keeps the exact threshold on the base tier, and uses long-context rates only above it; compaction can return a later record in the same Session to the base tier. GPT-5.6 Fast long context before its August 5 API availability and GPT-5.5 Fast long context have no published applicable tier rate. The explicitly labeled ccusage-style proxy uses the contemporaneous short-context Fast rate, doubles input and cached input for requests above 272K input tokens, and multiplies output by 1.5; a separate snapshot label and source identify this as a trend estimate, never an official historical Fast long-context rate. New records select that proxy only for the matching model, date, tier, and request size. Claude's observed 1-hour cache writes use their separate publisher rate; Codex logs do not expose cache writes as a separate component, so that component is absent from the estimate. No catalog creates a runtime ccusage, network, or page-render dependency. Future unknown model names remain unpriced until a cited entry is added.

Each new Usage Record also freezes its first-observation Project attribution. A currently discovered Git root produces a `git:<canonical-root>` key; otherwise a resolved workspace produces a `path:<canonical-path>` key; missing evidence stays `unassigned`. Workspace ID, name, canonical path, Git root, basis, and attribution time are snapshots rather than live Project joins. Conflict updates preserve them, so a later Git initialization, path move, or workspace enrichment can affect only new records. Current `workspaces.git_root` follows current filesystem evidence and may change without rewriting historical usage. Legacy or previously unassigned records are not reconciled automatically.

### Session Synchronization

Every repair/force path below requires successful
[Session revision admission](data-model/source-registry-and-scans.md#source_files).
A higher stored revision is refused before projection or lifecycle writes;
bounded source failure-health recording still occurs.

The Sessions inventory owns a Session-only incremental synchronization action. It scans every validated source in the ordered private Session-source registry—the user’s enabled Codex/Claude profiles—regardless of the selected inventory filter, and does not scan Local Context sources. Each accepted file carries independent Session-projection, Usage-normalizer, and generalized-reference versions. After successful Session revision admission, a stale contract reparses the source files needed by that concern but writes only the owned derived lane; a natural file change, missing Session mapping, forced scan, or eligibility repair still refreshes every affected lane. Each source has an independent transaction, source-file set, stale-deletion boundary, and persistent latest attempt/success/status/error health. Unavailable or invalid sources skip stale reconciliation and retain their normalized data; an unexpected failure rolls back only that source. The JSON request API queues or joins the common collector; its status API exposes the bounded per-source report plus complete, partial, or failed aggregate outcome. An additive NDJSON endpoint emits bounded source ID/label, repair kinds, and throttled file counts to the same Sessions result region; it emits no paths or content, and callback/display failure cannot change synchronization. The development-web Sources inventory owns the wider scan that appends every enabled Local Context root without weakening those Session-source commit boundaries. Both web actions retain the source-file freshness check. An otherwise-current source is reparsed only when its versioned Atlassian evidence scan or enabled configured-Site fingerprint is missing or changed; once all owned contracts are current, the source is skipped.

The shared backend schedules Session and Local Context collection independently,
defaulting to 10 and 30 minutes after each domain's completion. The Sync settings
use 10/20/30/60-minute or Off choices and preserve existing saved intervals.
Manual requests and multiple backends share one writer lock and coalesce pending
work. Each domain's latest health lives outside the primary DB; per-source/file
state stays in the registry. Background collection does not reload the reading
surface or add a status banner. The existing Sessions manual action remains.
See [the common runtime contract](desktop-app-and-settings.md); shared scheduling
checks do not establish simultaneous native/web startup acceptance.

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

Session branch metadata is stored per Session from authoritative JSONL. Workspaces retain the currently discovered canonical `git_root` of the containing repository and do not store a branch value; historical Project attribution belongs to Usage Record snapshots instead.

[Session Conversation And Identity Reading](#session-conversation-and-identity-reading)
owns detail/copy presentation. [Skill Observation Capture](#skill-observation-capture)
owns source signals; the analytical sections own ranking and analysis Runs.

### Skill Observation Capture

Session Insights retains native invocation/context, completed instruction reads, named references and identifiable skill script executions. `ingest/evidence/skill_loads.py` correlates calls/results and request provenance. `ingest/evidence/skill_usage.py` matches source-established skill identifiers and unambiguous plugin aliases in normalized visible user/assistant messages without interpreting use wording or language. Generated catalogs/instructions and tool-output text are not conversation references. Script evidence uses completed native Codex CommandExecution records or non-error Claude Bash results, checking a literal executable or supported interpreter script argument within a known skill root's `scripts/` directory. Dynamic commands and heredoc bodies are excluded from this bounded command grammar; logged commands are never executed. Names/locators come from the same Session's native loads or completed reads, not current installed inventory.

Scanner persists source-scoped evidence during changed-file ingestion, and Session parser upgrades backfill available files without recomputing Usage prices. The [skill observation ledger](data-model/workspace-and-session-activity.md#skill_observations) owns native/fallback identity, request provenance, signal vocabulary, row-preserving migration, corrections, maintenance exclusion and retained history. Historical declarations remain references; the parser generates no new declarations. Source message text is not copied into this ledger.

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

## Workflow Projection And Correction

The pure descriptor contract precedes the database read projection. User
assertions overlay that projection through a separate mutation boundary;
the route renders the resulting payload.

### Workflow Projection Contract

- `workflow_projection.py` owns the versioned, pure descriptor boundary for
  workflow Episodes, directional relations, reasons, and omission diagnostics.
  Importing or calling this contract performs no SQLite, filesystem, source,
  connector, network, model, embedding, or maintenance work.
- One Episode corresponds only to an eligible primary work Session. Its opaque
  key is derived from a length-delimited numeric source ID and source-native
  Session ID; local row ID is carried only as the current `/sessions/{id}`
  navigation destination. No Episode table exists. The source-PK upgrade converts
  retained assertion boundaries for existing Sessions; assertion IDs and history
  remain unchanged.
- Observation time, activity, lifecycle, closure reason, and authority remain
  separate descriptor fields. `sessions.ended_at` may extend the observation
  bound but cannot infer lifecycle closure.
- Relation normalization accepts only `continues`, `branches-from`, and
  `merged-into`, requires a strictly later target plus at least one strong
  source, organization, or user-assertion reason, and deterministically omits
  self-edges, invalid values, unsupported authority/reason combinations, and
  edges that would form a directed cycle. Workspace, Git, lexical, and temporal
  signals are supporting evidence only.
- Descriptor serialization is bounded and excludes source messages, document
  bodies, opaque payloads, raw local paths, and source-native Session IDs.
  Database-backed producers must assemble this shape from already-normalized
  facts without weakening the contract or persisting an inferred graph.

### Workflow Focus Read Model

- `workflow_focus.py` is the sole initial database-backed producer of the
  versioned Session Focus payload. It accepts one local Session ID, validates
  primary-work meaningful eligibility, and returns `ready`, `missing`, or
  `ineligible` without adding a route or persistence owner.
- The producer reads Session/source/workspace metadata, privacy-minimized direct
  reference keys, user-authored organization links, current Related Materials,
  direct-child metadata, and persisted Atlassian structure-reference identity.
  It never selects Activity Event text, Context Document body, source path for
  output, remote body, opaque payload, or search text.
- Candidate admission is exact and conjunctive. Shared user Thread is
  sufficient; otherwise shared reference or user Workstream must combine with
  the documented workspace/Git fact. Classification sees at most 200 candidates
  and uses stable strength, temporal-distance, observation, and Episode-key
  ordering. Generated or accepted-suggestion membership may remain evidence but
  is not directional authority in this baseline.
- The relation producer creates adjacent `continues` candidates and nearest-
  earlier `branches-from` candidates, selects at most one derived incoming edge
  per Episode, emits no heuristic `merged-into`, and delegates forward-time,
  reason, and acyclic validation to `workflow_projection.py`.
- Stable outward traversal owns the 24-Episode, four-branch-root, and four-
  Episodes-per-branch limits. Evidence assembly reuses the stricter Related
  Materials destination boundary, groups source families with a five-item
  presentation limit, and reports observed versus retained totals and
  stale/partial state.
- The entire call is a SQLite read projection. It performs no DML, schema work,
  cache write, source parse, filesystem check, connector/capability operation,
  Refresh, network request, model call, or background scheduling. Repeating it
  against unchanged SQLite state returns the same semantic ordering.

### Workflow Assertion Ledger And Overlay

- `workflow_assertions.py` owns the only workflow-correction mutation and
  overlay boundary. The `workflow_assertions` table is append-only application
  state keyed by a digest of stable Episode identity; nullable Session foreign
  keys are current lookup aids with `ON DELETE SET NULL`, and one unique
  self-supersession link prevents a history fork.
- The domain exposes exact create, undo, history, and overlay operations. Each
  write recomputes the current overlay, compares an optimistic projection
  revision, validates endpoints, forward time, incoming-boundary consistency,
  cycles, tip closure, and active supersession, then appends inside one bounded
  savepoint without committing its caller's outer transaction.
- Focus first constructs the unchanged source and deterministic
  candidate projection. Active user assertions then replace only the effective
  selected relation pair or Episode lifecycle. The read model retains
  `base_relations`, base lifecycle, resolution summaries, diagnostics, and a
  deterministic revision so presentation and Trace can distinguish observed,
  candidate, and user-confirmed authority.
- Assertion rows survive Session deletion and projection rebuild. An absent or
  newly incompatible endpoint makes the active assertion unresolved rather
  than deleting it or weakening graph invariants; restoration of the same
  source-scoped native identity can resolve it again.
- These operations read or write only normalized SQLite state. They perform no
  source-file, Git, connector, remote, Refresh, synchronization, model,
  embedding, training, or Workstream-organization mutation.

### Session Workflow Focus Route

- `workflow_map.py` is the pure presentation adapter for one validated
  `WorkflowFocusProjection`; `workflow_correction_view.py` adds registry-backed
  active-assertion summaries, stable boundary identities, exact consequence
  previews, and only currently valid actions without querying a second
  authority. `GET /sessions/{id}/workflow` opens one SQLite connection, invokes
  `workflow_focus_projection` once, closes that read scope, and then renders
  only the returned payload. It has no detail-query fallback, source/body
  access, connector, background task, model call, or write.
- `workflow_session_is_eligible` shares the primary-work/full-index/
  meaningful-activity predicate with Session detail. Its failure is isolated so
  the existing Session route omits only the additive Workflow link and still
  renders conversation, pin, Subsessions, and Related Materials.
- `session-workflow.html` is the complete server fallback and Trace owner.
  Every retained Episode, relation, reason, evidence group, availability, and
  safe destination exists before enhancement. Its correction partial uses
  ordinary forms and exposes exact before/after, endpoints, authority,
  supersession, close reason, bounded note, cancel, and recovery controls before
  JavaScript runs. Missing, ineligible, and unexpected projection states render
  bounded local destinations with `404`, `422`, and `500` respectively; a
  connected or unconnected ready projection is `200`.
- `workflow_correction.py` owns the strict `application/x-www-form-urlencoded`
  boundary for `POST /sessions/{id}/workflow/corrections`: at most 16 KiB and
  eight fields, exact action-specific shapes, one optimistic projection
  revision, bounded note, strict percent decoding, and same-origin Fetch
  Metadata. The route reconstructs Focus and performs exactly one assertion
  apply or undo inside one transaction. Success commits once; parse,
  validation, conflict, and unexpected failure roll back completely and expose
  only fixed local messages. Enhanced requests receive bounded JSON with
  `200`, `409`, `422`, `400`, or `500`; ordinary forms receive a same-route
  `303` on success or a server-rendered current map on failure.
- `workflow-map.js` is a route-scoped fixed renderer. Observation order and
  stable Episode keys determine positions; `continues` retains a lane and
  `branches-from` allocates the next stable lane. It draws no force simulation
  and persists no durable layout. Selection and bounded branch disclosure
  change only DOM state; Episode selection pushes the target Session's canonical
  Workflow route, and back/forward restores an in-payload focus without
  recomputation. Immediately before an enhanced correction it records a
  bounded, versioned, path-scoped one-shot restoration envelope in
  `sessionStorage`; the following successful same-route render consumes and
  removes it after restoring only selected Episode, branch/evidence disclosure,
  scale, pan, Trace/page scroll, corrected-boundary focus, and a fixed result
  code. Failure does not reload or replace the graph and re-enables only the
  owning form.
- The graph owns only modified wheel/pinch zoom and its bounded scroll region.
  Ordinary wheel input remains with page or viewport scrolling. At the existing
  `920px` breakpoint direction becomes vertical; at `700px` and below the
  graphical viewport yields to the server lineage. Renderer failure does the
  same while leaving controls disabled and Trace navigable.

## Analytical And Session Read Models

### Analytical Read Models

Activity time is derived separately from usage and cost. Valid Activity Event timestamps form per-Session segments: a gap of exactly 30 minutes remains continuous, while a greater gap starts a new segment. Segments end at the last observed event, are clipped with inclusive-start/exclusive-end range boundaries, and are merged across concurrent Sessions before estimated active seconds and the longest active segment are calculated. Observed Session span remains a separate first-to-last-event value. Single-event segments contribute zero inferred duration, and no value is extended to the current time. Local day and Monday-week boundaries use an explicit IANA timezone.

The Sessions Dashboard read model normalizes `view`, `source`, `metric`, `from`, and `to` GET state before querying Usage Records. Its accepted Source options are loaded in configured TOML order from registered Claude/Codex profiles, with `All` first; an unknown ID falls back to `All`. Old nonnumeric source-key links fall back to `All`. Exact filters use `sources.id`, while `provider_kind` remains only the adapter semantic for rules such as Claude synthetic exclusion and may be shared by personal Codex and Codex Company. Daily uses 30 inclusive local days, Weekly uses 12 Monday-based local weeks, and Monthly uses separate monthly buckets from the earliest eligible real-model usage date. Legacy `view=cumulative` links still produce monthly running totals but are absent from the visible range control. Valid paired custom dates replace only the bounds; malformed, partial, or reversed pairs retain the selected view, source, and metric while falling back to the view default. Token and priced-cost totals include direct real-model records, including maintenance and subsession records, while the usage-linked Session denominator includes only primary work Sessions. Claude records whose raw model is exactly `<synthetic>` remain persisted but are removed at the dashboard query boundary from dates, totals, coverage, breakdowns, and Session counts. The same boundary excludes Codex `last_token_usage` rows with zero request components and a source total that only repeats earlier history; those rows remain in the database. Records without usable timestamps remain explicit history limitations. Unsupported or incomplete pricing never becomes zero: the cost value is unavailable when none can be priced and carries a compact partial indicator when only some records can be priced.

The rendered Sessions Dashboard uses the existing Usage Record table directly, without a materialized aggregate or separate snapshot database. Its `All` query uses the `(occurred_at, id)` index; source-scoped queries retain the `(source_id, occurred_at)` index. SQL limits candidate rows to the selected UTC dates plus adjacent source dates, then Python applies the exact inclusive-start/exclusive-end UTC bounds so source offsets do not change selection. A narrow SQL probe includes unusual or unusable timestamps outside that indexed window for the history limitation state; the two ordered cursors are merged without loading or counting records twice. Monthly's earliest-date lookup reads index-ordered candidates only through the offset-safe earliest window. The rendered route streams selected rows and computes summary, history, and composition in one pass without retaining a selected-row list. After accumulating overall values and history, the shared projection admits only `session_class=work` records to Project groups and their compatible share denominator; work subsessions remain included. Maintenance is excluded before group identity, ordering, latest activity and evidence are derived. Source/Model keep all eligible records. The full compatibility read model still materializes its rows for MTD and price-snapshot details but uses the same selected-range projection. The rendered route omits unshown activity-time, MTD, projection, freshness, and price-snapshot detail calculations.

For every default or custom range, history buckets start and end at the first and last buckets whose selected metric has a positive value. The same rule applies to All and every registered source, source/metric/view switches, date changes, and direct or history navigation, across Daily, Weekly, Monthly, and legacy Cumulative views. The requested start and end dates continue to govern row selection, totals, date inputs, and URL state; only the rendered history bounds are shortened. Empty buckets between those endpoints remain visible to preserve calendar gaps. Default Daily and Weekly query windows remain 30 inclusive local days and 12 Monday-based local weeks, while their rendered bucket counts follow the selected data. If the selected metric has no positive bucket, its existing unavailable or zero-history behavior applies. Daily axis labels mark the first and last rendered buckets and the 1st and 15th of each visible month; Weekly and Monthly retain their regular bucket labels with both endpoints.

Cost is the default `metric` when the query parameter is absent or invalid. The visible metric control orders Cost before Tokens. History retains Decimal values for bar height, aggregation, and accessible detail while its bar-top display rounds to whole dollars or compact whole token units; positive costs below one dollar display `<$1`.

The same read model normalizes `breakdown=source|model|project`. It groups by numeric source ID with configured display name and profile color, normalized model while retaining raw identities, or the immutable Usage Record Project key; current workspace joins may enable a browse link but never change a historical group. Personal and company Codex therefore remain separate source rows. Compatible shares use the selected supported token total or priced-cost total, and the `All` compatible total equals its source-row sum. The first eight ranked groups remain visible and additional groups use native disclosure. While expanded, the same summary control follows the additional rows, placing `Show less` at the bottom of the composition table; collapsing returns `Show N more` below the initial eight rows. Pointer and keyboard disclosure behavior remains native and works without JavaScript. Repeated hidden column headings stay anchored to their own cells so the expanded table's horizontal overflow remains inside its local scroller. Aggregate freshness consumes the persistent latest source-health attempt, success, status, and bounded error plus source-file stale/error evidence. Completed/empty is current; unavailable, configuration error, or scan failure requires attention; legacy rows without a source-level result retain file-status fallback. Previously calculated records remain visible and the last source success remains distinct from the failed attempt.

The read model retains model-group Session evidence metadata for compatibility, but the composition table does not render an evidence column. A single-Session destination is exact only when a model group contains one distinct primary work Session in the selected usage rows. The Sessions inventory has source and current-workspace filters, not a model-usage filter, so the read model does not generate an inventory URL for model groups with multiple or no primary work Sessions.

Current-month projection remains a non-persisted compatibility calculation in the full read model and is not requested or rendered by the Sessions Dashboard route. `calendar-elapsed-v1` divides source-scoped compatible MTD estimated cost by the timezone-aware fraction elapsed between local month start and next local month start. It requires three complete local days, a Cost view whose range contains today, and at least one priced Usage Record. Calculation time, source scope, input total, elapsed fraction, formula version, coverage, and freshness state travel with the internal value. It never updates Usage Records or their price snapshots and never runs for a historical-only range.

### Synchronization And Session Inventory Read Models

[Session Synchronization](#session-synchronization) owns collection, repair,
source transactions and scheduling. This section owns the inventory and
Chart read projections that consume those normalized records.

Sessions browsing derives its ordered peer source controls from the same registry
and uses the numeric source ID, never provider kind, as GET and query identity.
`all` plus each source-specific view share one primary-work/primary-role
denominator across headline count, inventory, pagination, and Project grouping;
the inventory adds no timestamp cutoff. Unknown source IDs and missing workspace
IDs normalize to a valid URL while preserving the other valid scope. Ordinary
inventory and Pinned cards expose provider `CL` or `CX` cues with
the configured display label in accessible text instead of repeating it visibly.
Detail headings and normalized or lazy Subsession projections derive the same
provider cue and the registered profile’s accessible name; numeric source IDs
continue to identify filters and data. Their configured source display label remains in accessible cue text rather
than being repeated visibly in detail headings or parent-detail Subsession rows.
The child projection carries the existing `user_message_count` beside
`event_count`; a lazy Claude child derives the same question count from its
source events. The detail row renders question, event, then activity date.
Detail links retain the selected source/workspace only as return orientation.

The additive Sessions Chart uses `display=chart`; `display=list` or an absent or
unrecognized display value selects the existing paginated List. Scope repair and
the Session-only sync redirect retain Chart state. The full Chart projection
selects primary work metadata without pagination, age cutoff or body/source-file
reads. `parse_timestamp` normalizes valid `started_at`/`last_event_at` to UTC;
the latest valid value anchors the point. Only metadata-undated rows need an
Event-time fallback query. The Chart never calls activity-segment construction.

`GET /sessions/{id}/chart-activity` admits only an existing primary work Session
and returns ordered timestamp occurrences, total/undated Event counts and labeled
valid metadata times with `Cache-Control: no-store`. It selects no Event body,
tool argument or opaque source identity and performs no database mutation.
Initial Chart metadata carries only ID, title, source cue fields, recorded
execution path/branch, lexically normalized folder key/name/display path,
earliest/latest valid observed time and provenance. `~` uses the local home;
normalization never reads Git history, resolves symlinks or groups by Git root.
Timestamp fallback continues to read only Event times when metadata is unusable.
The template additionally projects IDs from the already-loaded complete eligible
pin inventory; no new SQL, limit or mutation is introduced. Chart intersects these
identities with scoped records. A static pin cue reflects any pinned member of a
pixel aggregate; the selector and preview use the exact original member's status.
The browser builds case-insensitive folder-name/full-path ordered bands, missing
folder last, and stored-branch membership once per scope. Observed master/main owns
the baseline; feature-only data has a neutral structural guide. Missing branch
data never acquires a branch identity. Guide joins terminate at the first retained
observation, without asserting a Git fork, merge or Session relationship.

Only viewport points are rendered, with same-track pixel buckets exposing exact
counts and all original Session identities through a native selector; mixed
sources use a neutral aggregate cue. No footer totals/legend/help are rendered.
A native Project checkbox/search disclosure controls local visibility by known
folder key. Filter changes repack homes and clear hidden selection/activity;
ordinary camera/zoom/resize only change projection. Reading track pitch is 48px,
heading 40px and Project gap 8px. A separate bounded vertical scale allows all
visible rows to fit; overview plot targets and Project/branch names scale while
crowded Session titles and the held preview are withheld. Project/Session focus
restores reading scale. Node hover/focus renders original metadata in a separate
temporary instance of the native preview without moving the camera, reserving
space, persisting hover or loading activity. Node/card/facing-edge passage share
geometric hover ownership; exit outside both pointer and keyboard focus closes
it after native state-duration grace. Reentry cancels the callback. The gap adds
no hit overlay; the focusable card accepts text reading/selection and local
scrolling without selection actions or canvas dragging, including narrow widths.
New hovered metadata resets local scroll; only visible keyboard focus retains
the card after pointer exit, so mouse text clicks do not hold it.
Activation
holds selection, with repeat/blank/close/Escape dismissal. Hovering another node
keeps the held Session and activity intact. Blank click clears temporary-only
hover too, and cancellation clears pending exit callbacks. A cursor
guard prevents stationary-pointer hover reappearance after reprojection; genuine
movement resumes it. Small transient drag offsets couple only
same-track neighbors; a damped spring returns to exact anchors with no idle
simulation or persisted layout. Guides/activity times stay fixed. Cancellation,
camera change, resize or page hiding clears capture/offsets, and reduced motion
omits coupling and returns immediately. Selected Event points may
share a pixel bucket, whose exact count and observed endpoint times remain
inspectable; no duration bar or Session edge is produced. Camera, selection ID,
vertical scale and List page use scope-specific version-four sessionStorage, which
also carries visibility as a navigation fallback. The dedicated
`session_chart_preferences` table owns durable visibility per logical source and
workspace scope; empty workspace scope means all workspaces. It has no cascading
FK and stores only sorted hidden-folder keys and update time. DB state, including
an empty all-selected list, overrides browser state. Only known keys affect the
screen; absent hidden keys remain available when their folders return. An absent
DB row permits migration from valid
`localbrain:session-chart-projects:1:<source>:<workspace>` localStorage, then legacy
tab visibility, through create-if-absent. Clear the old browser key only after DB
confirmation. Server load failure never triggers automatic migration.

`PUT /sessions/chart/project-visibility` validates local same-origin access,
source/workspace query scopes and a JSON body of at most 65,536 bytes. The payload
admits only `hidden_projects` and optional Boolean `only_if_missing`; hidden keys
must be a list of at most 2,000 strings, each at most 4,096 characters, with at most
60,000 encoded UTF-8 bytes after deduplication. Empty keys represent missing cwd.
A transaction replaces one current preference or preserves an existing migration
row, and commits before acknowledgment. Invalid inputs/scopes return 400, invalid
workspace query types or values outside SQLite signed-integer range 422, non-JSON 415, oversized bodies 413 and unavailable DB
writes 503. DB work runs in the thread pool. These writes never alter Sessions,
pins, membership or source files. Browser writes are serialized and retain the
newest pending choice; bounded keepalive requests support navigation, while load/save
failure exposes a native contextual retry and preserves in-memory use. Only confirmed
writes are durable; abrupt closure with unconfirmed queued work is not a save receipt.
Preference writes occur on filter changes rather than camera rendering. Browser
storage denial keeps filtering/navigation usable in memory. Earlier valid camera
time/scale/selection migrates but old-spacing Y is discarded. The toolbar has the
Project filter and zoom/fit/focus; directional/date controls are omitted while
axis dates and drag/keyboard navigation remain. Initial
reading entry fits time and starts at the alphabetical top; whole fit also scales
Y and brings the canvas into view. Bounds use visible first/latest observations
and selected visible activity; internal time origin remains fixed. Filtering refits
a whole-time overview, retains endpoint anchoring, or preserves a middle camera's
time anchor and clamps it. Both ends account for the centered projected 40px target
and reserve 64px, capped at 20% usable width and free target space; guide ends use
the same frame inset. Fit retains the existing base reading-scale/one-day cap, so
short periods can underfill the right side. Floating preview width is reserved.
Blank pan uses an 80px resistance limit capped at half usable plot width; the existing
on-demand spring returns the camera, with immediate reduced-motion restoration and
no saved overshoot or idle loop. Point-pull limits are unchanged.
Ordinary detail's Chart backlink adds return state only;
Workflow links and projection/correction contracts are unchanged.

### Session Conversation And Identity Reading

Session detail exposes the retained source-native `sessions.external_id` as **Session ID** in the first metadata cell. A read-only abbreviation starts at eight characters and extends on collisions with different stored IDs across sources; identical native IDs retain the same abbreviation. The complete value is preserved in accessible metadata and copied by an explicit browser action, with a success check and `Copied!` state for two seconds after the clipboard write succeeds, or a selectable full-value fallback and anchored recovery message on failure. One custom tooltip supplies both hover/focus help and result feedback, centered on the owning button rather than the pointer; native button titles and footer copy toasts are not used. It stays outside the clipped metadata frame, remains within the horizontal viewport and flips above when bottom space is insufficient. Pointer exit, blur, Escape, scroll and resize dismiss the tooltip without cancelling the copied-state deadline. Reentry before that deadline retains confirmation; expiration restores the glyph and label and returns an open tooltip to its copy explanation. Repeated success restarts the deadline without an idle-glyph flash, and stale asynchronous results cannot overwrite the latest attempt. Copy results alone have live announcements. Control geometry and surrounding metadata remain stable. This does not change Session identity, ingestion, navigation URLs, or start a resume command. Activity-time width follows its content, branch metadata receives remaining wide-layout space, and the strip reflows within the available reading column.

Session detail presentation selects normalized `message` events in source sequence for primary Sessions and eligible direct children.
The [Session normalization contract](data-model/workspace-and-session-activity.md#conversation-normalization-and-empty-sources) owns authored-message preservation, generated-context and reply-envelope handling, native counterpart precedence and parsed-empty ownership checks. The [Activity Event phase contract](data-model/workspace-and-session-activity.md#assistant-response-phase-provenance) owns completion evidence for both providers.

Conversation cards use this phase only for a stronger neutral result frame, with a very light blue surface and a left accent for user inputs, no added phase text and no task-success claim.
Ordinary commentary and unmarked assistant cards keep their existing treatment.

A copied presentation view renders only user and assistant text through the shared Markdown contract without an owning Local Context source; raw source JSONL, source-relative unresolved references, `tool_call` rows, tool names, and the Session's complete retained event count remain unchanged.
Parent details list same-source direct children as Subsessions; child details resolve only to a same-source primary parent.
`/sessions/{id}/subsessions/{file}` is the canonical lazy compatibility route.
Existing Claude `/subagents/` links redirect to that route, which still reads the source-native `subagents/` directory and uses the same message-only Markdown presentation.

### Session Insights

The Insights database projection groups all observed evidence once per source, native Session and normalized skill, independently of requests and event count. Its compatible fields carry Session counts and latest admitted reference times under the ledger contract. GET does not reread transcripts or join current Sessions for row details, and Usage & Cost remains independent. This measures use/reference reach rather than successful application.

### Personal Insight Evidence

`personal_insight_evidence.py` owns the read-only current evidence producer and
reference reviewer. `build_insight_evidence_manifest(connection, *, mode,
requested_at, question=None, source_ids=None, date_from=None, date_to=None,
timezone="Asia/Seoul")` returns `personal-insight-evidence-v2`.
`resolve_insight_evidence_reference(connection, reference)` checks a frozen
reference against current normalized records. Neither function opens native
files, collects a source, creates a Run, invokes a model or external service,
or persists an evidence archive.

#### Evidence Eligibility And Scope

- `mode` is `ask` or `discover`. `ask` requires a trimmed nonempty question of
  at most 2,000 Unicode code points; `discover` requires `question=None`.
  `requested_at` must be a timezone-aware `datetime` and is retained as UTC.
- `source_ids=None` selects the supplied database's Source rows with
  `provider_kind IN ('claude', 'codex')`. An explicit collection must be nonempty
  and contain only positive integers: `type(id) is int and id > 0`, so booleans
  are invalid. Duplicates collapse, IDs sort, and an unknown or other-provider
  ID fails. This producer uses retained normalized Source rows; it does not
  add the collection/search registry's TOML-enabled-source filter.
- Dates are optional strict valid `YYYY-MM-DD` values in an IANA time zone.
  `date_from > date_to` fails. Inclusive local dates become an inclusive UTC
  start and an exclusive UTC start of the day after `date_to`.
- A Session must have `session_class='work'`, `session_role='primary'`,
  `index_policy='full'`, an admitted Source ID, and at least one in-scope Event
  with `event_type='message'`, `role IN ('user', 'assistant')`, and
  `text IS NOT NULL AND length(trim(text)) > 0`.
  Event occurrence time owns the date scope, not the Session's last activity.
  Known times after `requested_at` are excluded. Undated/unparseable times are
  eligible only with no date bound; bounded dates exclude and count them.
  Eligibility uses SQLite `julianday(occurred_at)` for these time predicates.
- Mode, question, time zone, dates and Source selection are validated before
  message evidence is selected. A valid empty scope returns
  an empty manifest with `no_eligible_messages`. A SQLite read savepoint keeps
  registry, counts, selection and excerpts in one database state. With the same
  state and supplied inputs, selection has no ambient clock or random choice.

#### Evidence Selection And Excerpts

Count every eligible Session and message before sampling. `discover` round-robins
Source/local-month buckets, using each Session's latest eligible message time
to choose its month. Known months sort newest first, then Source ID descending;
unknown-time buckets follow. Within a bucket, latest eligible activity comes
first, with ascending Session ID for ties. Stop after 100 Session picks.

`ask` takes at most the first 16 distinct casefolded Unicode word terms from the
question, builds a parameterized token-OR query over `search_index.body`, and
takes up to 70 eligible Sessions in `bm25(search_index)`, then stored `entity_id`
order. Fill the remaining
slots to 100 using the same Source/month spread without repeats. No usable term
or indexed match still permits spread evidence; it never proves that no useful
improvement exists. A Session-level indexed hit is only a candidate, not proof
that a selected message contains a question term. Project balance and prior
recommendation history are not selection inputs.

Within an ask-mode selected Session, prefer matching messages by distinct term
overlap, then user role, then source sequence and Event ID. Take at most three.
If no message matches, or in discovery mode, choose unique first, middle and
last eligible positions in source order. Final output follows Session selection
rank and then Event sequence/ID.

| Limit or address | Current contract |
| --- | --- |
| Selected population | At most 100 Sessions and 300 excerpts |
| Excerpt size | At most 600 Unicode code points per excerpt and 120,000 total |
| Lexical window | Start up to 120 original code points before the earliest matched term, then obey both character bounds |
| Spread window | Start at original character zero |
| Frozen message position | Zero-based index among all eligible messages in that Session and frozen scope, before sampling; not raw Event sequence |
| Source address | Full-text UTF-8 SHA-256, full text length, exact character start/end, Event ID, role, sequence and occurrence time |

#### Evidence Manifest And Reference Review

The manifest contains `version`, caller-supplied UTC `generated_at`, normalized
`scope`, `selection`, `coverage`, and ordered `sessions`:

| Object | Fields |
| --- | --- |
| `scope` | `mode`, `question`, numeric `source_ids`, `date_from`, `date_to`, `timezone`, `event_from_utc`, `event_to_exclusive_utc`, `requested_at` |
| `selection` | `method`, `indexed_session_count`, `lexical_excerpt_count`, `lexical_match_state` |
| Session | `source_id`, `provider_kind`, `session_id`, `session_url`, full eligible `message_count`, ordered `events` |
| Event | `source_id`, `provider_kind`, `session_id`, `event_id`, `sequence`, frozen `message_index`, `role`, `occurred_at`, `text_revision`, `text_length`, `excerpt`, `excerpt_start`, `excerpt_end`, `selection_basis`, `session_url` |
| `coverage` | `eligible_sessions`, `eligible_messages`, `selected_sessions`, `selected_excerpts`, `excerpt_characters`, `truncated_excerpts`, `eligible_undated_messages`, `undated_messages_excluded`, `selected_undated_messages`, `selected_first_at`, `selected_last_at`, `sources`, `omission_reasons` |
| Each `coverage.sources` entry | Numeric Source-ID key; `provider_kind`, `eligible_sessions`, `eligible_messages`, `selected_sessions`, `selected_excerpts`, `selected_undated_messages`, `selected_first_at`, `selected_last_at` |

Selection method is `source_month_spread_v1` or
`fts70_plus_source_month_spread_v1`; lexical state is `matched`, `none` or
`not_applicable`. Event basis is `lexical` or `spread`. Native source paths and
native Session IDs are not returned. Coverage keeps selected time bounds and
clipping separate from the full eligible population.
Omissions distinguish `no_eligible_messages`, `session_sample_limit`,
`message_sample_limit`, `character_limit`, `no_indexed_lexical_match`,
`no_selected_message_lexical_match`, and
`undated_messages_excluded_by_date_scope`. Selected coverage is never described
as exhaustive when eligible material or source text was omitted.

Reference review requires provider, positive non-boolean local Session ID,
Event ID, sequence, role, occurrence time and full-text revision. A missing
Session returns `unavailable` with no destination; a missing Event returns
`unavailable` with its surviving Session destination. A present row is `current`
only if work/primary/full classification, optional Source ID, provider, message
Event type, admitted user/assistant role, role equality, sequence, occurrence
time and full-text digest all agree. Otherwise it is `stale`. For legacy
references that omit `source_id`, the remaining frozen identities/checks still
apply; no string Source alias is inferred. Review returns only `status` and
`session_url`; it does not reapply the frozen date selection or a registry
enablement filter. Review never rewrites the frozen manifest or substitutes a
current excerpt for its retained evidence.

### Personal Improvement Analysis Runs

The Insights route separately browses `personal_insight_runs`. A submitted question or discovery request freezes at most 100 eligible primary-work Sessions, 300 excerpts, and 120,000 excerpt characters into a private evidence manifest. The current versioned core supplies all eleven detailed playbooks and selects a finding type from the owner's goal and observed friction, rather than excluding types through lexical cues. The exact prompt, core/playbook versions and digests, and report-v3 JSON schema are frozen for that Run; historical core v2/v3 keeps the v2 result shape. Additive eligible-message positions and counts allow the validator to reject conversation requests for fully supplied messages. Reports explain candidate/type selection and show frozen source, count, time, and truncation coverage. Conversation requests are rendered from validated missing-message targets; no automatic expansion or paid retry occurs. Codex CLI uses the Run's frozen local `CODEX_HOME` profile, no native Session persistence, and no model tools, so the analysis conversation does not enter ordinary Session evidence or feed later analysis. The home is chosen from `LOCALBRAIN_INSIGHT_CODEX_HOME`, `CODEX_HOME`, an existing `~/.codex-company`, or `~/.codex`, in that order. A validated result has at most three findings, an explicit no-finding outcome, or a bounded request for more evidence. Findings must cite IDs from the frozen manifest; recurrence requires independent Sessions. The Run stores CLI-observed usage before report validation and retains the private validated value, Markdown report, and source excerpts outside Git. `personal_insight_usage.py` projects one latest usage summary per Run into canonical Usage Records using a metadata-only Maintenance Session with external identity `localbrain-insight:<Run ID>`. This accounting parent contains no messages, events, workspace, or search entry and remains excluded from work-Session counts and future analysis. Source attribution matches the frozen Codex home to the registered sessions root; Project attribution is unassigned because execution occurs in the private Run artifact directory, not an originating work repository. The dashboard excludes this Maintenance accounting from Project composition while retaining it in overall usage, history and Source/Model. Frozen attribution stays unchanged. New Runs explicitly select Standard service tier. Historical unmarked Runs use a labeled default-tier assumption. Input includes cache reads, so normalization subtracts cached input before pricing it separately; reasoning stays within output. Aggregate inputs above a request-price threshold remain partial because request-level context is unavailable. Failure, cancellation, and interruption preserve any emitted usage; startup can recover retained summaries or terminal stream evidence without a provider call. Stable identities and frozen snapshots prevent replay double counting. It never starts implementation work. Opening Insights, downloading a report, or syncing a source starts no model Run. The Usage & Cost opening query remains independent of this path.

#### Guide Bundle And Result Contract

`personal_insight_guidance.py` selects the bounded package catalogue and validates
the report value. New Runs freeze core `personal-improvement-core-v8`, report
`personal-improvement-report-v3`, all eleven playbooks, exact trusted text, a
`route_reason='owner_goal_and_observed_friction'`, and separate SHA-256 digests
for the core and each playbook.
`request_feedback` uses v4; every other current playbook uses v1. The catalogue is
`task_framing`, `request_feedback`, `context_recovery`, `repeatable_procedure`,
`learning_explanation`, `verification_rework`, `information_access`,
`decision_memory`, `task_fit_effort`, `personal_value`, and
`assistant_configuration`. Quoted vocabulary does not remove a type before the
model considers the owner's goal and observed friction.

Bundle fields are `core_version`, `report_version`, `core_sha256`, exact `core`,
`playbooks` and `route_reason`. Each playbook freezes its own `id`, `version`,
`sha256` and exact `content`; a core fingerprint never replaces a playbook's.

Core v2/v3 retain report v2, and historical core v4/v5/v6/v7 retain report v3.
Guide/report mismatches fail. Historical resources and reports are preserved;
`personal_insight_guide.md` remains the historical v1 resource. A changed package
guide, profile or environment affects future Runs only. Per-Run versions and
content digests are compatibility/provenance facts, not proof that a generated
recommendation is correct or effective. [Product Model](product.md#insights)
owns current decision, application and previous-proposal duties.

The strict current report contains `result_version`, `title`, `summary`,
`outcome`, `findings`, `no_finding_reason`, `additional_evidence`, `limits`,
`selection_reason` and `selection_evidence_ids`. Outcomes are `findings`,
`no_actionable_finding` or `needs_evidence`; only `findings` has a nonempty
finding list, with at most three entries. A no-finding or needs-evidence result
requires a nonempty reason. Candidate selection explains relevance and competing
interpretation without claiming exhaustive ranking or guaranteed novelty.

Each finding has `title`, selected `type_id`, `owner_goal`,
`pattern_scope` (`single_observation` or `recurring_pattern`), `observation`,
`evidence_ids`, `counterevidence_ids`, `counterexample_status`,
`counterexample_check`, benign `alternative`,
`coverage_limit`, `action`, `benefit_hypothesis`, `effort_or_tradeoff`, `follow_up`,
`handoff`, `outcome_state` and `type_reason`. Supporting IDs are required and must
name unique selected Event IDs. A recurring pattern requires two distinct
Sessions. Supporting and counterevidence IDs cannot overlap; `observed`
counterexample status requires counterevidence, while `not_observed` and
`not_available` require none. `outcome_state` is always `not_confirmed`.
Handoff has exactly `goal`, `proposed_change`, `scope`, `constraints`,
`first_steps` and `success_check`. After validation, a 16-hex `finding_id` hashes
the finding and its one-based position. The returned result also adds `guide`
with `core_version`, `core_sha256` and playbook `id`/`version`/`sha256` metadata.
These local identities do not confirm an owner outcome.

| Validated text/reference limit | Bound |
| --- | --- |
| Report title, summary, limits; no-finding reason | 8,000 code points per field; required fields are nonblank |
| Selection reason / selected evidence | 2,000 code points / at most five unique Event IDs; findings and evidence requests require selection evidence |
| Finding title / other ordinary finding text / type reason | 160 / 4,000 / 1,000 code points |
| Supporting and counterevidence | At most 12 unique admitted IDs each |
| Each handoff field | Nonblank, at most 1,000 code points |
| Additional-evidence question and anchors | At most 1,000 code points and five unique admitted Event IDs |

Additional-evidence kinds are `none`, `conversation_neighbors`,
`independent_session`, `owner_goal` and `outcome`. The exact request fields are
`kind`, `question`, `evidence_ids` and `message_requests`. Only `needs_evidence`
may request evidence, with a nonempty bounded question; other outcomes carry
`{"kind":"none","question":"","evidence_ids":[],"message_requests":[]}`.
Current conversation requests have one to five
`{anchor_evidence_id, message_index}` targets, anchored in the request's admitted
IDs. Uniqueness is `(session_id, message_index)` after resolving each anchor's
Session: distinct anchors in the same Session cannot request the same position.
Both index and frozen `message_count` must have `type(value) is int`
(booleans are invalid), with
`0 <= message_index < message_count`; the anchor also needs a valid frozen
position. A supplied complete message cannot be requested again; a clipped one
may be requested in full. Other request kinds carry no message targets.

The product renders conversation requests from those validated targets and
nearby source anchors. Positions count frozen eligible messages, not provider
sequence; absent position metadata cannot support an indexed request. Model
prose identifies content/date/anchor relationships rather than publishing numeric
message positions or assuming an omitted message's speaker. Unknown goals or
outcomes use their own bounded factual question, not a bypass for supplied-message
refusal. The trusted guide requires Korean JSON text without Markdown links or
raw HTML and treats limits as ceilings, not targets to fill. Invalid values fail
without automatic paid retry, retaining emitted
usage and diagnostics. Structural/ID/position checks do not prove semantic
specificity, eliminate every redundant question, establish applicability or
confirm benefit; the trusted guide and behavior evaluation own those checks.

## Explicit Experimental Tools And Contracts

Pure candidate normalization and isolated reconstruction retain their own
evidence/admission limits. The full-history simulation produces private
similarity reports for the admitted observation-only reader, without
admitting product work identity or organization changes.

### Workstream Candidate Contract

- `workstream_candidates.py` owns `localbrain.workstream-candidate.v1`.
  Producers supply canonical artifact/Session/reference facts and proposed
  pairs. The module validates their evidence; it neither enumerates a corpus
  nor resolves a URL, path, Site, or alias through I/O.
- Artifact keys hash kind, source scope, and canonical identity with length
  delimiters. Producers map Context Documents to stable source plus relative
  path, Jira/Wiki Items to normalized Site plus canonical issue key/Page ID,
  and other existing Resources to their canonical path/URL namespace. Known
  Resource aliases use the resolved Document/Item owner. SQLite IDs and raw
  Session-reference target keys containing row IDs are not stable identities.
- Session keys reuse `workflow_episode_key`; the factory validates primary
  work/full-index and supplied meaningful Event/Usage evidence. Reference keys
  hash the Episode, artifact, and source-native occurrence identity. Each member
  independently supports both anchors through mentions or successful reads.
- Identical facts/pairs collapse; conflicting facts with one stable identity
  are excluded with fixed diagnostics. Weak, missing, disabled, container, or
  insufficient evidence cannot be repaired through title, workspace, existing
  organization, a mixed Session, or transitive graph membership.
- Candidate identity hashes contract version and sorted anchors. Membership
  revision observes all admitted supporting references, including those beyond
  the response sample. A separate result revision includes presentation,
  coverage, source state, and diagnostics. Source change may invalidate an
  inferred candidate but never transfers future user assertions to another key.
- Hard input/output bounds raise `CandidateLimitError` instead of returning an
  order-dependent prefix. Evidence and overlap samples retain complete totals
  for the supplied scope. Coverage defaults to partial and cannot claim global
  discovery. The current shapes, bounds and producer duties below complete
  this pure contract.
- Import, normalization, and serialization perform no application I/O and own
  no table, cache, route, scheduled work, model, or current product consumer.

#### Candidate Inputs And Producer Duties

The current factories accept normalized mappings and produce frozen descriptors;
`normalize_workstream_candidates(artifacts, sessions, references, pairs, *,
coverage=None)` validates the supplied scope. Factories reject malformed values
with fixed `ValueError` text. Batch normalization counts invalid, excluded and
conflicting individual facts/pairs with sorted fixed diagnostic codes rather
than choosing values by input order. Invalid top-level iterables, coverage or
hard overflow fail; strings, bytes and mappings are not fact iterables.

| Factory input | Mapping fields |
| --- | --- |
| `candidate_artifact_from_record` | Required `kind`, `source_scope`, `source_identity`; optional `title`, `identity_state`, `enabled`, `is_container`, `availability`, `freshness` |
| `candidate_session_from_record` | Required `id`, `source_id`, `external_id`, `session_class`, `session_role`, `index_policy`; meaningful-evidence inputs `event_count`, `has_activity_events`, `has_usage_records`; optional `title` |
| `candidate_reference_from_record` | Required `episode_key`, `artifact_key`, `reference_identity`, `evidence_kind`; optional `read_outcome`, `observed_at` |
| Proposed pair | A tuple/list of exactly two valid distinct Artifact keys |

- Artifact kinds are `context-document`, `wiki-item`, `jira-item`,
  `local-resource` and `external-resource`. Producers resolve aliases first:
  Context uses stable source plus relative path, Jira/Wiki uses normalized Site
  plus canonical Issue/Page identity, and other Resources use their canonical
  path/URL namespace. Known Document/Item aliases use that resolved owner's
  identity. The normalizer performs no fuzzy match, URL/Site inference or I/O.
- Identity strings are nonempty trimmed UTF-8 text, at most 4,096 code points;
  after trimming, reject characters where `ord(char) < 32 or ord(char) == 127`.
  Source scopes are at most 300. Attributed titles
  collapse whitespace and retain at most 500 code points; absent/invalid titles
  remain absent. Raw identities never serialize. Opaque Artifact, Episode and
  Reference keys use their validated namespace and 64-hex digest.
- Artifact identity is `resolved`, `unresolved` or `ambiguous`; enablement and
  container flags are actual booleans. Only resolved, enabled, non-container
  facts qualify. Availability (`available`, `unavailable`, `missing`, `unknown`)
  and freshness (`current`, `stale`, `unknown`) stay separate; retained stale or
  missing facts do not acquire false freshness.
- Artifact factory defaults are identity `unresolved`, `enabled=False`,
  `is_container=False`, and availability/freshness `unknown`. A Session's
  `event_count` defaults to zero and both meaningful-evidence flags to false.
  These conservative defaults do not admit an otherwise unknown fact.
- A Session fact requires work/primary/full, a positive non-boolean local ID,
  a positive integer numeric `source_id`, source-native identity and meaningful
  supplied evidence: `event_count > 0 OR has_activity_events OR has_usage_records`.
  `event_count` is a nonnegative non-boolean integer and both flags are strict
  booleans. Unknown eligibility never defaults true. Episode identity uses the
  [pure workflow identity contract](#workflow-projection-contract), not local ID.
- Reference kinds are `user_mention`, `assistant_mention`, `resource_read` and
  `tool_result`. A mention qualifies only with `read_outcome is None`; a read
  qualifies only with `read_outcome == 'success'`. Failed/missing read outcomes,
  absent endpoints and excluded anchors cannot support membership. The producer
  supplies source-native occurrence identity and observed time; local reference
  row IDs and import time are not source occurrence identity.
- Proposed pairs contain two distinct resolved Artifact keys; reversed/duplicate
  pairs collapse. Each admitted member independently supports both anchors,
  with at least two distinct stable Episode keys. Shared Sessions/anchors do
  not merge seeds transitively. Organization, workspace, Git, wording and recency
  cannot repair missing direct evidence.

#### Candidate Result, Bounds And Coverage

| Descriptor | Returned contract |
| --- | --- |
| Artifact | `artifact_key`, `kind`, hashed `source_scope_key`, optional `display_title`, `identity_state`, `enabled`, `is_container`, `availability`, `freshness` |
| Session | Stable `episode_key`, current local `session_id`, numeric `source_id`, optional `display_title`, `destination` |
| Reference | `reference_key`, `episode_key`, `artifact_key`, `evidence_kind`, `read_outcome`, UTC-or-unknown `observed_at`, `authority='observed'` |
| Anchor support | `artifact_key`, sampled `references`, full `reference_count`, `observed_start_at`, `last_observed_at`, `unknown_time_count` |
| Membership | `session`, both anchor `supports`, `authority='deterministic-candidate'` |
| Overlap | Other `candidate_key`, `shared_artifact_count`, `shared_session_count` |
| Candidate identity/presentation | `candidate_key`, `anchors`, `label`, `label_authority`, `label_artifact_key`, `members`, `membership_revision` |
| Candidate evidence | `observed_start_at`, `last_observed_at`, `latest_observations`, `latest_observation_count`, `unknown_time_count`, sampled `overlaps`, full `overlap_count` |
| Candidate status | `authority='deterministic-candidate'`, `outcome=None`, `next_action=None`, `activity_state='unknown'`, `lifecycle_state='unknown'`, `closure_reason=None`, `contract_version` |
| Whole result | `candidates`, sorted `diagnostics` (`code`, `count`), `coverage` (`complete`, `unexamined_session_count`), separate `revision`, `scope='supplied-facts'`, `contract_version` |

Seed identity hashes the version and sorted anchor keys. Membership revision
observes every admitted supporting reference, including evidence beyond samples;
it excludes title, local navigation ID and source freshness. Result revision
also observes presentation, source state, coverage and diagnostics. Added members
or changed labels do not rename a seed or retarget future assertions.

Label precedence is Context Document, Wiki, Jira, local Resource, external
Resource, then Artifact key. The first available attributed title wins with
`source-metadata` authority; otherwise `Unnamed work candidate` uses `fallback`.
No goal or confirmed Workstream name is inferred. Only admitted source-observed
reference times determine bounds/latest observations; missing or invalid time
stays unknown. Session end/start, import and wall-clock time do not prove progress.
Outcome/next action and closure reason remain absent; activity/lifecycle stay
`unknown`. Overlap reports shared anchors/Sessions without redefining membership.

| Hard input/output bound | Maximum |
| --- | ---: |
| Artifact facts / Session facts | 2,000 each |
| Reference facts | 20,000 |
| Proposed pairs | 200 |
| Memberships across the whole result | 2,000 |

The normalizer reads at most each input bound plus one and raises fixed
`CandidateLimitError` on overflow, returning no order-dependent partial prefix.
Each member samples at most five references per anchor, by known observed time
descending then opaque key, while retaining full counts, bounds and unknown-time
counts. Latest-reference ties sample at most five with their full total; overlaps
sample at most 20 with full counts. All admitted references still affect revisions
and time bounds. Coverage defaults to partial with unknown unexamined count;
`complete=True` requires an explicit zero unexamined Session count. An empty
partial result never means that the corpus has no candidate.

`coverage` must be a `CandidateCoverage` value, with an actual boolean `complete`
and an unknown or nonnegative non-boolean integer `unexamined_session_count`.
Fixed diagnostics distinguish `invalid-artifact`, `invalid-session`,
`invalid-reference`, `conflicting-artifact`, `conflicting-session`,
`conflicting-reference`, `ineligible-session`,
`disabled-artifact`, `unresolved-artifact`, `ambiguous-artifact`,
`container-artifact`, `missing-session`, `missing-artifact`, `excluded-reference`,
`weak-reference`, `invalid-pair`, `missing-pair-anchor`, `excluded-pair` and
`insufficient-sessions`; codes and counts never copy rejected input text.

This remains a pure supplied-fact contract, with no admitted discovery/review/
promotion consumer, table, route, cache, schedule, model or organization mutation.

### Quoted Work-Context Model Contract

The quoted extractor and pair-relation validator consume supplied conversation
packets; they do not discover private input. `extract` accepts exactly
`{"messages": [...]}`; `relate` accepts exactly `{"left": [...], "right": [...]}`.
Each message has exactly `id`, `role`, `at` and `text`: the ID matches
`[A-Za-z0-9_-]{1,64}`, role is `user` or `assistant`, `at` is null or a string,
and text is a nonblank string. Each admitted message collection contains 1–128
messages with unique IDs and at most 40,000 total text characters. A pair must
also satisfy these bounds and ID uniqueness across the combined left/right
collection. Source records are untrusted evidence, never instructions.

The `quoted-work-context.v2` prompt distinguishes independently resumable
outcomes from messages, references and phases: investigation, implementation and
testing of one goal stay together. Requests/plans do not establish completion;
assistant claims are not user confirmation. Unknown fields remain null or empty.

| Wire object | Current contract |
| --- | --- |
| Free-form model response | One JSON object, at most 24,000 characters; duplicate keys, non-finite constants and invalid JSON refuse |
| Evidence | Exactly `message` and `quote`; an admitted message ID and a nonblank exact original substring of 1–600 characters occurring exactly once in that message |
| Extract response | Exactly `units`; at most eight units. Each has exactly `goal`, `target`, `progress`, `results`, `remaining`; goal/target are null or evidence objects, each list has at most eight evidence objects and no repeated `(message,start,end)` span |
| Unit validity | At least one populated field; duplicate grounded unit identities refuse. Grounding adds exact start/end, speaker, time and `source-attributed` authority; unit IDs hash the grounded fields and retain `inferred-work-unit` authority |
| Pair response | Exactly `relation`, `evidence`, `link`; relation is `continues`, `related`, `independent` or `uncertain`, with at most eight distinct grounded evidence spans |
| Pair evidence | Every non-uncertain label cites both conversations. `continues` requires a grounded link in the right conversation whose message is also cited; all other labels require `link=null` |

Continuation semantically requires compatible goals and an explicit right-side
link to earlier work. Shared words, artifacts, repositories or nearby dates are
insufficient; a time gap alone does not disprove continuation. `related` records
a shared topic without established same-goal continuity or distinct outcomes;
`independent` needs distinct goals/targets or an explicit denial; insufficient
evidence remains `uncertain`. Structural quote validation cannot prove these
semantic judgments. Output retains `authority: inferred` and the prompt version.

The generator verifies an installed allowlisted model/revision and its assets
before use. `auto` selects MPS when available, otherwise CUDA, otherwise CPU;
explicit `mps`, `cuda` and `cpu` remain available. CPU uses float32, other devices
bfloat16; MPS uses eager attention and other devices use SDPA. Model/revision,
asset fingerprint, device, dtype, attention, Python/Torch/Transformers versions,
generation settings, strategy prompts/projection/bounds and output protocol are
part of the compatible inference identity. Public pinned 4B and 8B installations
retain separate identities; neither a default model label nor cache relocation
can substitute for verified assets.

| Generation setting | Current accepted value |
| --- | --- |
| `thinking` / decoding | Actual boolean; `greedy` or `sampled`, with thinking allowed only with sampled decoding |
| Non-thinking token budgets | Combined default/ceiling 8,192; generated default/ceiling 2,048 |
| Thinking token budgets | Combined default/ceiling 16,384; reasoning-plus-final generated default/ceiling 8,192 |
| Reduced budgets | Actual integers: combined at least 1,024, output at least 128, each within its mode ceiling, and output strictly below combined |
| Call time | Soft generation limit: actual integer 1–180 seconds, default 180; operation-specific smaller limits still apply; no hard preemption of an in-flight model call |
| Sampling | Non-thinking: temperature 0.7/top-p 0.8; thinking: 0.6/0.95; top-k 20 and stable `sha256-system-and-content-prefix32` seed; greedy has no sampling object |
| Output protocol | `qwen-final-only.v1`; reasoning is counted but never decoded or retained, and only the final answer is validated/stored |

Tokenization never truncates: rendered input tokens plus the reserved
`max_output` must not exceed `max_tokens`, otherwise generation refuses with
`CONTEXT_TOO_LARGE`. Constrained choice reserves its finite code/EOS grammar
instead. A free-form response must finish with EOS; missing EOS is
`OUTPUT_TRUNCATED`. Thinking output requires exactly one closing `</think>`
token and at least one final-answer token before EOS; non-thinking output refuses
thinking delimiters. Reasoning token IDs are counted without decoding them.
These checks enforce protocol and bounds, not semantic truth.

`single`, `staged`, `classified`, `selected` and `evidence` keep separate
fingerprints and failure behavior. Source-choice modes serialize only explicitly
model-selected original quotes, never repair missing citations or turn syntax
into truth. Their packet/case bounds and protocol/admission operations are in the
[Developer Guide](developer-guide.md#local-work-context-model-trial). No quoted
strategy is admitted to a private-history or product reconstruction consumer.

### Isolated Work Reconstruction Experiment

- The `work_reconstruction*` modules own only the versioned experimental
  `localbrain.work-reconstruction.v1` shape. Their only app consumer is the
  current sample-mode Auto Work inspection adapter below. They have no schema,
  migration, schedule, production identity, or assertion-ledger ownership.
- Extraction consumes supplied bounded text. Evidence keys and offsets retain
  source attribution; normalized goal identity is separate from wording, labels,
  revisions, and experimental exact-scope corrections. Unknown goals and
  lifecycle remain unknown. Shared references cannot force a semantic merge.
- The comparator receives metadata and admitted record spans, never body text.
  It enumerates all qualifying bounded pairs through the unchanged candidate
  normalizer. Local canonical keys use Context source/relative-path and
  Atlassian Site/remote identity, not raw row-based target keys.
- Private input requires an explicit existing database and frozen source/time/
  record manifest. A read-only URI, query-only transaction, and SQLite authorizer
  prohibit mutation, attachment, and extension loading. Eligibility is checked
  before bounded body selections and hash verification. No application database
  helper, source parser, connector, model, or external operation is used.
- Once the owner selects current LocalBrain data, the operator may resolve its
  configured database without asking for a manual path. Explicit preparation
  samples the approved existing-history scope before prediction, keeps
  per-snapshot omissions in the manifest, and revalidates hashes/permissions
  through the same adapter. `--unassessed` leaves every quality answer unknown;
  it is execution evidence only, never generated truth or a viability gate pass.
- Each analysis/admission worker is a spawn-free supervised process on macOS or
  Linux. Its own peak RSS covers that single-process worker tree; an in-worker
  watcher and parent completion check enforce the memory bound, and the parent
  enforces wall time and reaps cancelled/failed workers. Unavailable monitoring
  fails closed; the command does not inspect unrelated processes.
- Results and independent expectations stay local. New owner-only output outside
  the repository is bounded, never overwrites an existing result, and records
  its owner and expiry. The tool adds no retention scheduler or whole-DB copy.
  Quality and stability measurements do not automatically approve viability.
#### Reconstruction Input And Bounds

The pure snapshot has `version: 1`, a nonempty name, `sessions`, `records`,
`artifacts`, `references`, `coverage` and `organization_links`; unknown
fields refuse. Identifiers are nonempty strings of at most 500 characters unless
an explicit integer identity is required below. Supplied timestamps are aware
ISO timestamps of at most 80 characters. A Session record uses positive actual
integer `id`/`source_id`, nonempty `external_id`, nonnegative actual integer
`event_count`, eligibility fields `session_class`, `session_role`, `index_policy`,
and optional `title`, `workspace_id`, `ended_at`, `has_activity_events`,
`has_usage_records`; titles are null or at most 500 characters. Session IDs are
unique. Artifact/reference field allowlists and semantic validation reuse
[Candidate Inputs And Producer Duties](#candidate-inputs-and-producer-duties).

| Boundary | Current hard limit |
| --- | --- |
| Snapshot history | 1–12 distinct named snapshots |
| Sources / Sessions per snapshot | At most eight Sources and 60 Sessions; work/primary/full eligibility remains mandatory for private admission |
| Records / total text | At most 12,060 records and 2,500,000 text characters |
| Session evidence | At most 200 records and 32,000 characters per Session; each selected message span at most 4,000 characters |
| Other evidence | At most 20 Documents, 20 Items and 20 organization records; each Document/Item span at most 8,000 characters, organization span at most 2,000 |
| Metadata | At most 2,000 artifacts, 12,000 references and 200 organization links |
| Metadata comparator pairs | At most 4,096 qualifying pairs; overflow fails rather than clipping |
| Corrections | At most 100 unique correction IDs; each names at most 12,060 unique statement keys, with no key reused across corrections; optional label is null or 1–500 characters |
| File / worker | Input and encoded output at most 10 MiB; each admission/analysis/scoring worker at most 120 seconds and 512 MiB peak RSS |

Every text record has a unique `key`, a `kind` (`session`, `document`, `item`,
`organization`), `session_id`, `role`, nonnegative actual integer `offset`,
nullable aware `at`, and text. Session records require a selected Session ID and
user/assistant role; other records require a null Session ID and document/owner
role. Coverage has actual boolean `complete` and nonnegative actual integer
`unexamined`; complete coverage requires zero unexamined items. Bounds do not
convert omitted or unsupported source into a complete reconstruction.

A private selection manifest has exactly `version: 1`, `source_ids`, `start`,
`end`, `snapshots`, `owner`, `expires_at`. Source IDs are 1–8 unique positive
actual integers. Its aware start is no later than end. Each snapshot has unique
`name`, ordered `as_of` within that interval, `session_ids`, `events`,
`documents`, `items`, `organization`, `organization_links`, and optional explicit
coverage. Session/link IDs are unique positive actual integers. A text selection
has `id`, `start`, `end`, `sha256`, plus `table` only for organization:
`id` is an actual integer or nonempty string whose spelling is at most 500
characters; offsets are actual integers with `0 <= start < end`, obey their
kind's span limit, and use a lowercase 64-hex UTF-8 SHA-256. Only one selection
per record identity is allowed. Organization tables are exactly `workstreams`,
`threads`, `checkpoints`. No arbitrary table/column is admitted.

The explicit database must be an existing absolute nonsymlink file. A URI
`mode=ro` connection, `query_only`, memory-only temporary storage, one read
transaction, SQLite authorizer and deadline prohibit writes/attachment/extension
loading. Session admission requires a registered Source in the selected set and
work/primary/full classification. Selected Events must be user/assistant
messages in that Session. Documents require an enabled, readable, ready root;
Items require indexed content and no disabled bound Source. Organization uses
current summary/goal text and user-created links to selected Sessions only.
Each selected record's relevant occurrence/import/application/update/link time
must lie within start and snapshot cutoff. Bounds and permission checks precede
selected text reads; exact selected substrings must still match their hashes.

Reference projection reads persisted evidence only, capped at 12,000 rows across
selected Sessions. Missing/non-ok scans, missing times or unresolved canonical
references make coverage partial; known out-of-scope references are excluded.
Only selected Documents/Items participate. Document identity uses Context scope
and relative path; Jira uses Site/issue key, Wiki Site/page identity; generic
references require safe persisted credential-free HTTP(S) URLs. The comparator
receives canonical metadata and admitted source spans, never text. It enumerates
artifact pairs independently supported by two Sessions through the unchanged
candidate normalizer; references cannot force goal identity.

Explicit preparation uses `localbrain.chronological-spread.v1`: metadata selects
up to 60 Sessions evenly across their earliest eligible message times, including
both chronological endpoints, before predictions or body reads. It selects up
to 32 evenly spread message records per selected Session, at most the first
1,000 characters each; up to 20 referenced Documents and 20 referenced Items,
8,000 characters each; up to 20 linked organization records, 2,000 each, and
200 user links. It creates up to three distinct chronological cutoffs, records
outside-sample/omitted/truncated/unknown-time counts and revalidates the frozen
manifest through the same permission/hash adapter. No eligible population or
more than eight Sources refuses. This bounded preparation is distinct from the
full-history simulation below. Unassessed expectations have no groups or
negative answer key and at least one unresolved item, so they cannot pass quality.

#### Reconstruction Output And Assessment

Sentence/newline extraction retains original record offsets and wording.
NFKC/casefold/whitespace normalization affects identity, never source coordinates.
The bounded Korean/English action vocabulary supports reduce/increase/improve/
fix/add/remove/replace/enable/disable. Unsupported negation, goals or subjects
remain explicit unassigned spans; subjects over 300 characters, URLs and braces
are unsupported. Investigation/implementation/verification are subordinate
phases. A reported `completed`/`done`/`완료` statement remains a source outcome,
not verified completion. Flow identity hashes normalized subject/change and a
compatible explicit completion criterion; a missing criterion stays unassigned
when several explicit criteria conflict. Lifecycle remains unknown.

Output `localbrain.work-reconstruction.v1` has `flows`, `unassigned`, `coverage`,
`corrections` and `routine_confirmations: 0`. Each flow retains `flow_id`,
subject/change/completion, derived label, nullable user label, inferred authority,
unknown lifecycle, ordered members and content revision. Members retain statement
key, exact record/start/end, Session/kind/role/time, normalized fields, original
wording and field evidence. Statement identity includes exact wording, so an
equal-length source edit is new evidence; unrelated appended text does not
invalidate an unchanged statement. Exact-scope corrections move only named
currently present statements into a correction-ID flow, mark those members
`user-corrected` and report their active count; the flow remains inferred, and
absent keys cannot target new claims.
The metadata arm retains spans and candidate identity/revision, not goal labels.

Independent expectations bind each snapshot digest before either arm executes.
A version-1 expectation supplies at most 100 distinct keyed groups with subject,
change, nullable completion, member spans and nullable acceptable labels (at most
20 nonempty labels, each at most 500 characters), `negative` spans and a
nonnegative unresolved count. Each group/negative list has at most 12,060 unique
exact record/start/end spans; spans must be inside admitted text, and negative
spans cannot overlap positives. Expected labels and unresolved assignments remain
unassessed when missing; predictions never supply the key. A predicted member
must be contained in an expected record/span and match its normalized
subject/completion and exact change value; Session overlap or a generated label
is not enough.
Every emitted assignment is correct, wrong or unassessed. Recovery, wrong
assignments, excess/unsupported groups, assessed correction freedom and stability
retain exact integer numerators/denominators; no rounding or zero denominator
can manufacture a pass. Correction-free requires one correctly supported flow,
an independently acceptable label, no assignment error and all expected member
contributions; an unknown label or missing contribution is not success.

The report compares text/metadata arms both with and without organization,
replays text deterministically, and reports per-arm resources/scores, source and
expectation digests, sample sufficiency and consecutive-snapshot identity,
assignment and label stability. Score gates require at least 80% goal recovery,
at most 10% incorrect membership, at most one excess/unsupported group per ten
recovered goals, no incompatible-outcome merges, at least 90% correction-free
recovered goals, and zero routine confirmations. Incomplete coverage, unresolved
expectations, unknown assignments, unassessed labels, no expected groups or no
members make quality insufficient rather than pass. Private sufficiency also
requires 40–60 eligible Sessions, at least ten expected efforts, an expected
effort spanning more than 24 Sessions and at least three snapshots. The report
lists independent local expectations, mandatory synthetic safety witnesses and
weak-reference/unrelated-append assessment as required evaluator checks. The
evaluator must verify at least 95% identity/assignment preservation after
unrelated append, without harmful reassignment. Source rename/loss and exact-scope
correction behavior also require separate synthetic witnesses. These evaluator
duties are not automatically computed CLI gates. Both arms use identical input; the metadata arm's poor quality does
not excuse a failed absolute text gate. Do not resample or tune against the
private answer key. These are separate checks, not an automatic viability
decision: reports retain `viability: unverified`.
The [privacy policy](privacy-and-data.md#local-persistence) owns the finite
human-review allowance and unknown/spent-budget refusal. No technical pass,
unassessed execution, reproduction or replay authorizes a new review batch,
production transition or product identity.

### Full-History Simulation Producer

`session_simulation.py`, its verified local encoder and ordered grouping engine
produce the private input for observation-only affinity inspection. Preparation
is explicit; browsing cannot invoke it. It accounts for all stored Sessions and
processes all nonempty user/assistant messages of admitted primary/full work
Sessions. Maintenance, Subsessions, metadata-only and missing-source Sessions,
non-message Events, empty messages and unknown dates retain separate counts;
an unknown date does not remove otherwise eligible text. This is experimental
similarity grouping, not admitted work identity or causal lineage.

Character windows are exhaustive and non-overlapping: default 1,800 code points,
accepted integer range 128–16,000. Source text is reread only for verified spans;
stored inventory holds identity, hashes, role, offsets and observed time, not a
full-body copy. Stable source/native Session identity and Event/span coordinates
address occurrences; repeated embedding inputs may share a vector while every
source occurrence survives. Complete source inventory is revalidated before
publication, so concurrent change refuses a new current report.

| Producer parameter | Current default / accepted values |
| --- | --- |
| Embedding batch size | 16; 1–256 |
| `neighbors` | 8; integer 1–64 |
| `similarity` | 0.65; `0 < value <= 1` |
| `area_resolution` / `work_resolution` | 0.6 / 1.2; each `0 < value <= 10` |
| `seed` | Integer 0 by default |

An encoding execution verifies model files before private input is read;
inventory-only/status/purge do not invoke an encoder. Local-files-only,
offline/telemetry controls and the existing outbound Python socket guard precede
inference; they are not an OS network sandbox. No model download, training,
external inference or source modification follows from simulation. New vectors
are finite, correctly dimensioned and normalized. Cache reads check dimension
times four bytes, finite values and a nonzero norm. Missing/corrupt vectors are
recomputed in committed bounded batches; unchanged compatible vectors are reused.
Changing grouping parameters can reuse vectors; source/model/chunk/runtime
identity controls compatibility. A fixed seed alone is insufficient: the current
`cosine-knn-louvain-v2-ordered` engine canonicalizes node/neighbor order in both
coarse and within-parent passes, preserves disconnected components/singletons,
and emits undirected similarity rather than causal edges.

#### Simulation Store And Report

The existing `localbrain.session-simulation.v1` owner binds its private directory
to the database's resolved path, device and inode. The database must be an
existing absolute regular non-symlink file. Output must be an absolute resolved
private runtime directory outside the repository/package and distinct from the
database directory, with an existing parent. Private ownership/permissions,
recognized files and no symlink/hardlink substitution are checked before use;
unknown/unowned output refuses adoption or cleanup. A nonblocking exclusive
`writer.lock` serializes producer/purge work. Atomic owner-only JSON publication
never treats an unfinished write as a valid result.

| Owned file or report field | Contract |
| --- | --- |
| `owner.json`, `writer.lock` | Marker fields `owner`, `database`, `expires_at` bind the source and 30-day inactivity expiry; the separate lock serializes work; both survive purge |
| `state.sqlite3` and its rollback journal | Rebuildable current inventory, unique content-addressed vectors and compatibility metadata; no second authoritative application DB |
| `progress.json` | Fixed prepared/inventory/embedding/grouping/complete or failed/interrupted state and aggregate progress; normal CLI stdout stays fixed codes unless counts are explicitly requested |
| Report identity | `owner`, UTC `created_at`, source `manifest`, `model` contract, `namespace`, `parameters`, `configuration` digest |
| Report authority | `processing_complete=true`, `quality='unassessed'`, `lineage_status='not_inferred'`; completion is not semantic quality |
| Source `manifest` | `extraction='all-message-character-windows-with-session-context.v1'`, `chunk_chars`, complete `coverage`, `digest`, `sampled=false` |
| `sessions` / `chunks` | Session `key`, local `id`, at-most-300-character `title`, `status`; each original-address chunk's `key`, `session_key`, `event_id`, `start`, `end`, `content_hash`, `input_hash`, `role`, `at` |
| `grouping` | `engine`, `authority='inferred-affinity-only'`, `areas` (ID/members and complete within-parent `work_groups`), `node_count`, `edge_count`, `singleton_areas`, finite undirected `edges` (`left`, `right`, `similarity`) |
| `inspection` | `areas`, `single_session_areas`, `cross_session_areas`, `sessions_in_multiple_areas`; each area's `area_id`, `session_keys`, `representative_title`, `label_basis='source-session-title-not-area-name'`, `representative_chunk`, known `observed_dates`, `lifecycle='unknown'` |
| `cache` / `comparison` | `reused`, `encoded`, `total`; `previous_available`, `same_input`, `same_configuration`, `same_grouping` |
| Published files | Atomic `report.json` and at most one `previous-report.json`; no full raw message-body backup |

Namespace hashes model contract, extraction version and chunk size; configuration
also hashes grouping parameters and engine identity. Content changes replace
current inventory atomically and remove unused vectors. Only after successful
report publication are old model namespaces pruned. Interrupted work retains
checkpoints, and a failed run does not publish an incomplete current report.
After 30 inactive days, the next explicit execution/startup/owned storage cleanup
enforces expiry; status rejects expired state. Explicit purge removes only known
derived files under lock, preserving sources, shared public weights and marker/
lock. Recognized abandoned atomic-write scratch is removed only inside this
validated owner. There is no new scheduler, private corpus or automatic model run.

Manifest coverage names `total_sessions`, `eligible_sessions`,
`excluded-maintenance_sessions`, `excluded-subsession_sessions`,
`excluded-metadata-only_sessions`, `excluded-missing-source_sessions`,
`excluded_nonmessage_events`, `message_events`, `empty_events`,
`unknown_date_events`, `admitted_characters`, `chunks`, `sessions_with_text` and
`sessions_without_text`. Session status uses the same eligible/excluded vocabulary.
The grouping parameter mapping contains exactly `neighbors`, `similarity`,
`area_resolution`, `work_resolution` and `seed`. The engine records `method` and
`numpy`, `sklearn`, `networkx` versions for replay compatibility. After publication,
the private checkpoint DB is vacuumed; no full-text copy is retained there.

The [Developer Guide](developer-guide.md#full-history-simulation-and-model-trials)
owns invocation and replay operation. Frozen experiment/evaluation records retain
their original processing/replay evidence; neither an exhaustive run nor a valid
report admits production work semantics, organization changes or a new extractor.

## Observation-Only Work Inspection

### Auto Work Inspection Read Model

`GET /auto-work` defaults to the current `session_affinity.py` consumer. The
server renders complete native text navigation and exact evidence; optional
`affinity-map.js` draws a viewport-bounded temporal SVG and owns zoom/pan plus cancellable
same-route navigation. History retains only viewport/Trace coordinates and edge
visibility preferences and text-list disclosure, not evidence. Reader `v2`
separates 24-row `nodes` from full matching-scope `map_nodes` and edges. Map
scope includes snapshot/hierarchy/search, never a text/evidence page or selection.
Native scroll extents move a sticky SVG viewport; horizontal movement traverses
time and vertical movement reaches every strand. List paging keeps geometry and
camera. Initial inspection is 200%; whole-time fit is 100%. Adjacency indexing
avoids per-knot whole-edge scans and repeated all-node sorting.
Selection never changes the layout input. The read model derives a common absolute-time
domain before search/paging, comparing timezone-aware observations as instants.
Serialized occurrence times retain admitted offsets; the renderer uses epoch
milliseconds and a UTC-labeled axis. Period boundaries start at midnight in
the earliest observation's retained offset.
The read model supplies at most 64 day-multiple activity periods per strand,
exact occurrence counts and existing-edge witness dates. Optional `period`
selection filters original evidence without changing snapshot identity or storage.
At the selected hierarchy level, each knot aggregates one group's occurrences
within one time period, not a single embedding point or a distinct Session.
Knot radius grows logarithmically with occurrence count and is capped; it is not
a cohesion, confidence or importance score. A group observed in only one period
can therefore remain a lone point even after both grouping stages. Neither the
generative work-context trials nor the source-claim/state projector feeds this
reader. The rule-based sample is a separate consumer, not a third merge.
Unknown times stay outside the dated plane. The renderer locks x to time and
uses deterministic affinity ordering/vertical attraction, curved strands and
explicit empty-period gaps; dates and labels remain readable under zoom. A
selected-neighborhood lens and short reduced-motion-aware camera transitions
provide observation rather than editing or perpetual physics.
Browsing cannot invoke the producer. The reader validation, payload bounds
and states are defined below.

#### Affinity Reader Contract And States

The current reader emits `localbrain.session-affinity.v2` from the existing
simulation store. A nonblocking shared writer lock protects passive reads. The
directory must be resolved, user-owned and private; the lock, owner marker and
report must be safe owned regular files. `owner.json` is bounded to 64 KiB and
`report.json` to 128 MiB. Validate the simulation owner, exact database path/
device/inode binding and unexpired marker before consuming the report.

The report must be processing-complete, unassessed and lineage-not-inferred, with
the current extraction and ordered grouping engine, an unsampled manifest,
valid parameters, matching namespace/configuration digests over the recorded
model contract, complete source coverage,
valid occurrence identities and exact coarse/within-parent membership partitions.
Finite unique undirected edges and coverage/count identities are checked; a
well-formed JSON object alone is insufficient.

- Session keys are unique 64-hex digests; local IDs are positive actual integers,
  titles are strings of at most 300 characters, and statuses use the producer's
  eligible/excluded vocabulary.
- Each chunk belongs to an eligible Session, has integer
  `0 <= start < end` with `end - start <= chunk_chars`, a string Event ID of at
  most 1,000 characters, user/assistant role, valid content/input hashes, a
  matching occurrence key and an at-most-80-character timezone-aware time or
  unknown. Chunk keys are unique.
- Every distinct embedding input belongs to exactly one coarse group and one
  subgroup within that parent. Groups have nonempty unique members and matching
  kind/member-derived IDs. Unique undirected edge endpoints are ordered, weights
  are finite with `0 <= similarity <= 1`, and stored totals/counts agree.

One derived index may live only in process memory, keyed by report signature and
source DB/WAL signatures. A changed key triggers exhaustive current source
inventory, not a sample; signatures must remain stable through validation.
Current manifest mismatch withholds old map/evidence and reports old/current
coverage plus added/changed/removed occurrences. Exact displayed passages are
independently resolved from current SQLite and checked for source/role/time,
span length and content/embedding-input hashes. No persistent reader cache or
new owner is created. An evidence row starts `available=False`; only a passing
current source check adds literal `wording`, Session `href` and `focus_href`.
Missing/changed evidence stays unavailable without a replacement quote or anchor.

The public payload groups these fields:

| Family | Fields |
| --- | --- |
| Identity and coverage | `version`, `state`, `snapshot`, `created_at`, `coverage`, `counts`, `model`, `parameters`, `configuration` |
| Scope and selection | `level`, `map_scope`, `scope_title`, `crumbs`, `q`, `base`, `selection`, `timeline`, `period` |
| Matching map and text | Whole matching `map_nodes`, `edges`; paged `nodes`, `total`, `matched`, `page`, `pages`, `previous`, `next` |
| Exact source evidence | `evidence`, `evidence_total`, `evidence_page`, `evidence_pages`, `evidence_previous`, `evidence_next` |
| Local recovery/navigation | `clear_url`, `overview_url`, `inventory_url` |

URL inputs are `snapshot`, `group`, `subgroup`, `pick`, `inventory=all`, `q`,
`page`, `evidence_page` and `period`. `q` is trimmed to at most 120 characters and
matched case-insensitively against group/constituent Session titles across the
complete selected level. Page input must be digit text of at most six characters;
otherwise it defaults to one. Valid numbers clamp to available pages. Snapshot
identity hashes the source-manifest digest and grouping
configuration; group and membership identities stay snapshot-scoped. Text lists
have 24 rows; evidence has eight occurrence rows. Title search covers the whole
selected level. Inventory includes stored excluded/no-text Sessions. Selection
is separate from expansion; observed role, offsets and time accompany literal
text. Undirected edge maxima are similarity, not confidence or causation.

Refusal states carry `version`, `state`, `title` and `explanation`.
`selection-stale` also supplies a valid `overview_url`; `stale` carries the old
`coverage`, `current_coverage`, `created_at` and `delta` counts for `added`,
`changed` and `removed` occurrences.

| Reader state | Predicate and consequence |
| --- | --- |
| `missing` | No owned result directory or no published report; no preparation starts |
| `busy` | Shared lock unavailable or source DB/WAL changes during validation; wait/retry without trusting a mixed snapshot |
| `current` | Complete validated source-bound report matches current inventory; a zero-match title query is still a current search result |
| `stale` | Current complete source manifest differs; hide old map/evidence and expose coverage/deltas without rerunning |
| `expired` | Owner expiry is at or before the read time; do not renew it on GET |
| `invalid` | Ownership/shape/size/version/configuration/coverage/partition or value validation fails; never overwrite or repair it on browse |
| `unavailable` | Database is absent/unsafe or local filesystem/SQLite access fails; source evidence is unavailable |
| `empty` | A valid current report contains no coarse groups; not a synonym for no title-search matches |
| `selection-stale` | Snapshot, hierarchy, selected membership or period is obsolete/invalid; return to valid overview rather than remapping selection |

Missing/stale/expired/invalid results never fall back silently to the prior sample.
GET neither creates/renews/deletes store artifacts nor computes vectors/groups,
collects sources, calls a model/external service or changes organization. Current
v2 keeps every matching strand and connection on one map regardless of text or
evidence page; the former graph paging is not a current contract.

### Previous Sample Inspection

The separate `auto_work.py` preview adapter consumes the experimentally verified
preparation/extraction shape, not the Focus projection. `GET /auto-work?mode=sample` reads
one owner-checked, 10-MiB-bounded, seven-day runtime file, revalidates current
source eligibility and frozen hashes through the read-only input adapter, and
binds displayed wording to admitted spans. Server-side pages expose every group
and unassigned statement with constructed local source destinations. Unknown
assessment remains unknown. It owns no DB table, production flow ID or correction.

`POST /auto-work/refresh` requires same-origin loopback access and an empty body.
It redirects back to the labeled sample mode, never refreshes the full-history map.
The server invokes the explicit preview command in a separate subprocess with
fixed configured input paths, quiet output and a 300-second outer timeout;
preparation and extraction retain their own 120-second/512-MiB limits. An
advisory lock makes refresh single-flight. Atomic, owner-only replacement retains
the prior valid result on failure; staging is removed on every write outcome.
Expired valid owned output is removed on a subsequent visit under that lock.
There is no startup/GET analysis, background job, source sync, model, migration,
or organization write. The sidebar link is capability-gated during mixed-version
template/server updates; a server restart activates the new route.

<a id="current-implementation-baseline"></a>

## Current Capabilities And Owners

This map locates current behavior; each linked owner retains its detailed
contract, permission and admission limits.

| Current capability | Owning contract |
| --- | --- |
| Additive SQLite startup migrations over the local index | [Persistence Model](#persistence-model) |
| User-created Workstreams and nested Threads | [Product organization](product.md#workstream-centered-organization) |
| Versioned checkpoints with linked-resource snapshots | [Product organization](product.md#workstream-centered-organization) |
| Thread-first links to Sessions, Local Contexts, projects, local paths and external references | [Product organization](product.md#workstream-centered-organization) |
| Workstream-level links for resources shared by multiple Threads | [Product organization](product.md#workstream-centered-organization) |
| Manual Jira, Wiki, Slack, Git, document and generic URL references | [Product domain](product.md#domain-boundaries) |
| Reversible keyword-based Session and Document link Suggestions | [Product Suggestions](product.md#automatic-capture-explicit-organization) |
| Reviewed work-based learning article home, library and reader from explicit reviewed imports, with separate Workstream routes and Sessions Dashboard | [Learning Home](product.md#learning-home) |
| Maintenance Session exclusion and source-neutral Claude/Codex subsession normalization | [Session Eligibility](#session-eligibility) and [Session Policies](#session-policies) |
| Source-neutral Claude/Codex Usage Records with immutable local trend-cost snapshots | [Usage Normalization And Repair](#usage-normalization-and-repair) |
| Reproducible Sessions Dashboard usage summary, GET scope and Daily/Weekly/Monthly token/cost history | [Analytical Read Models](#analytical-read-models) |
| All-time Session Insights use/reference Session ranking with durable source-backed evidence | [Session Insights](#session-insights) |
| Durable Maintenance Task Runner history, Claude/Codex external-sync parity, streaming result handling, cancellation and reviewable structured output | [Task Runner](../operations/claude-task-runner.md) |
| Deterministic SQLite/FTS5 retrieval without hard candidate or evidence-count caps | [Search and retrieval](#package-ownership) |
| Normalized many-to-many Thread resource matches with reusable fingerprints and deduplicated evidence | [Persistence Model](#persistence-model) and [Product Suggestions](product.md#automatic-capture-explicit-organization) |
| Source browsing for folders, files and Apple Notes | [Local Context Sources](#local-context-sources) |
| Context-aware full Document reading with an owning FOLDERS tree, bounded non-FOLDERS fallback and source-preserving Markdown presentation | [Document reading](#local-context-sources) and [Markdown rendering](markdown-rendering.md) |
| Safe Markdown conversation reading for visible Session/Subsession user and assistant messages without Local Context source guessing | [Session Conversation And Identity Reading](#session-conversation-and-identity-reading) |
| Atlassian stable source memory; bounded Session/Local Context URL evidence; strict zero-configuration local Site/Item admission; Site-first Explorer hierarchy with read-only canonical-URL container hints; grouped local search; Item detail, notes and Topic/Tag classification; exact Workstream/Thread links; explicit partial Space discovery and known-Item refresh previews without implicit remote ingestion or model calls | [Reference Evidence And Reconciliation](#reference-evidence-and-reconciliation) and [External Access And Synchronization Constraints](#external-access-and-synchronization-constraints) |

Implementation priorities and unresolved work belong in the [Project Backlog](../../plans/project/backlog.md).

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

### Persistence And Portability Constraints

- User review state and source provenance must survive rescans and suggestion refreshes.
- A failed maintenance Run must not clear the existing review queue.
- Historical source paths must remain visible when their current Project relation is missing or changes.
- The SQLite schema and runtime data must remain portable to a later desktop wrapper.
- Desktop packaging must not obscure data location, permissions, backup, or shutdown behavior.

## Google Drive Synchronization Boundary

The approved [Drive sync contract](google-drive-sync.md) adds explicit selected external writes. `google_drive/` owns the gcloud authentication adapter, separate private SQLite state, directional engines and backend-lifetime scheduler; `google_drive_web.py` exposes Settings-only local routes. The existing Session/Context collectors and clocks are unchanged. Fixed wall-clock jobs use one serialized worker, per-item verified checkpoints and cancellation between operations. The Drive synchronization path does not route OAuth or received material through a model, gateway executor, search index or automatic source registration. Separately approved [Context Search](context-search.md) may read already received copies within its explicit source boundary. Opening Settings reads cached state; explicit root browse and selected manual/automatic jobs perform real API operations. Native loopback authentication and the existing local same-origin boundary still apply.
