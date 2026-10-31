# Session Ingestion

This contract owns native Session capture, provider normalization, eligibility, independent repair lanes, reference evidence and synchronization. [Sessions](sessions.md) owns reading; [Usage And Cost](usage-and-cost.md) owns token and pricing semantics.

## Ingestion Contract

This family owns source capture, normalization, reconciliation and explicit
collection. [Session Workflow](workflow.md) owns projections and user corrections;
[Usage And Cost](usage-and-cost.md) and [Personal Insights](personal-insights.md)
own their analytical consumers.

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
  `ingest/sync/contexts.py` owns folder/file/Notes ingestion; `storage.py` owns shared
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
- Route standard Atlassian URL-family recognition through the shared
  `references/atlassian.py` owner before consumer-specific admission. The owner performs no
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
- `references/urls.py::parse_url` recognizes URL forms without registered Sites, bindings or items. Sessions store only a shared `resource_id` plus their own observed evidence and safe locator; an Atlassian registration cannot replace the identity or destination. A bare tool ID resolves only when exactly one known shared URL matches the product/key; all admitted URLs in the bounded candidate set participate before resolving hints. Different domains remain distinct. The optional Atlassian ingestion observer records its own sightings on the caller connection, independently from Session resolution. Savepoint failure retains prior Session evidence and records error/stale state. Additional grammars can be added to `references/`; Slack classification is not implemented.
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
- Compose primary Session `관련 자료` only at the bounded SQLite read layer. It consumes directly observed Session evidence, shared resource identity and Local Context availability without organization-membership reads, hidden query expansion, writes, parsing, model work, or external I/O; the [Session detail contract](sessions.md#session-detail-and-related-evidence) owns group eligibility, ordering, counts, and disclosure behavior.
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

[Session Conversation And Identity Reading](sessions.md#session-conversation-and-identity-reading)
owns detail/copy presentation. [Skill Observation Capture](#skill-observation-capture)
owns source signals; the analytical sections own ranking and analysis Runs.

### Skill Observation Capture

Session Insights retains native invocation/context, completed instruction reads, named references and identifiable skill script executions. `ingest/evidence/skill_loads.py` correlates calls/results and request provenance. `ingest/evidence/skill_usage.py` matches source-established skill identifiers and unambiguous plugin aliases in normalized visible user/assistant messages without interpreting use wording or language. Generated catalogs/instructions and tool-output text are not conversation references. Script evidence uses completed native Codex CommandExecution records or non-error Claude Bash results, checking a literal executable or supported interpreter script argument within a known skill root's `scripts/` directory. Dynamic commands and heredoc bodies are excluded from this bounded command grammar; logged commands are never executed. Names/locators come from the same Session's native loads or completed reads, not current installed inventory.

Scanner persists source-scoped evidence during changed-file ingestion, and Session parser upgrades backfill available files without recomputing Usage prices. The [skill observation ledger](data-model/workspace-and-session-activity.md#skill_observations) owns native/fallback identity, request provenance, signal vocabulary, row-preserving migration, corrections, maintenance exclusion and retained history. Historical declarations remain references; the parser generates no new declarations. Source message text is not copied into this ledger.

## Source Registry And Profiles

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

## Reference URL Grammar

`references/` recognizes URL syntax locally; a product label does not verify a
remote server, page existence, access permission or redirect. Jira's issue-link
shape is documented by [Atlassian's Jira link guidance](https://support.atlassian.com/jira-align/kb/view-in-jira-links-fail-with-cannot-open-project-issue-with-characters-in-the-url-on-jira-align/).
For Confluence, [Cloud page-ID guidance](https://support.atlassian.com/confluence/kb/find-the-page-storage-format-in-confluence-cloud-as-a-non-admin/)
identifies the numeric segment in `/wiki/spaces/SPACE/pages/123/Title`;
[Atlassian's public Cloud issue](https://jira.atlassian.com/browse/CONFCLOUD-82707)
also shows the title-free `/wiki/spaces/SPACE/pages/123` form in its custom-domain
example. [Data Center URL guidance](https://support.atlassian.com/confluence/kb/the-differences-between-various-url-formats-for-a-confluence-page/)
separately documents `pages/viewpage.action?pageId=123` and page-ID paths.
LocalBrain admits its tested title/no-title and legacy forms without registration,
but does not merge equal page IDs across domains or infer that a particular old
link redirects to a Cloud link. The parser and `test_reference_urls.py` /
`test_shared_resources.py` define the supported subset; these examples are not an
exhaustive URL grammar for every Atlassian deployment.

## Implementation Ownership

- `src/localbrain/ingest/`: source parsing, normalization, scanning, and deduplication

- `src/localbrain/sources/registry.py`: private TOML bootstrap, validation, bounded
  diagnostics, and non-destructive local Session-source registry reconciliation

- `src/localbrain/references/`: pure URL interpretation shared by ingestion,
  Sessions and optional integrations. `urls.py` owns generic HTTP(S) safety,
  token trimming and the common parse result; `atlassian.py` owns Jira/Confluence
  URL grammar and its existing versioned identity; `contracts.py` owns the
  storage-independent locator description. It imports no feature, DB or ingest code.

- `src/localbrain/resources/catalog.py`: common URL/path/note identities and existing-document/bookmark/external-ID bindings; no optional feature imports.

- `src/localbrain/sessions/references.py`: shared-resource resolution, file-scoped observation replacement, Session-level bounds/fingerprints, and database-only detail projection.

- `src/localbrain/ingest/extensions.py`: scoped optional observers; `atlassian/ingestion.py` owns source-specific evidence maintenance and `app/reference_integrations.py` owns explicit installation and read callbacks.

- `src/localbrain/persistence/migrations/resources.py`: preserving shared-identity migration and verified recovery copy.
