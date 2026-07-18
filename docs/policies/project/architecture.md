# Project Architecture

## Purpose

This document owns LocalBrain's durable implementation shape: runtime layers, package responsibilities, source adapters, persistence, ingestion behavior, and the current implementation baseline.

Product terminology and organization rules are defined in [Product Model](product.md). In-app Claude maintenance execution is defined in [Claude Task Runner](../operations/claude-task-runner.md).

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
- `src/localbrain/db.py` and `schema.sql`: connection lifecycle, schema, and additive startup migrations
- `src/localbrain/ingest/`: source parsing, normalization, scanning, and deduplication
- `src/localbrain/contexts.py`: Local Context source registration and browsing behavior
- `src/localbrain/queries.py`: read models for dashboards, sessions, sources, search, and detail views
- `src/localbrain/usage.py`: immutable price snapshots, model normalization, and per-fact estimated-cost calculation
- `src/localbrain/usage_queries.py`: Sessions Dashboard scope normalization, summary, MTD, history buckets, freshness, and limitation states
- `src/localbrain/workstreams.py`: Workstreams, Threads, checkpoints, resources, links, Suggestions, and retrieval mappings
- `src/localbrain/retrieval.py`: deterministic candidate selection and evidence preparation
- `src/localbrain/runner.py`: maintenance Run preparation, execution, streaming, and structured result processing
- `src/localbrain/subagents.py`: lazy Claude subagent discovery and parsing
- `src/localbrain/templates/`: server-rendered UI views
- `src/localbrain/static/`: browser behavior and visual presentation

Keep source-specific parsing inside adapters and keep persistence or domain behavior out of templates.

## Source Adapters

Current adapters:

- Claude local session history
- Codex local session history
- user-managed folders and individual files
- Apple Notes through local macOS Automation
- local project and Git metadata discovered during scans

### Adapter Extension Boundary

The [Project Roadmap](../../plans/project/roadmap.md) and [Project Backlog](../../plans/project/backlog.md) own adapter sequencing and named future targets. Any new external adapter must sit behind an approved connector boundary and follow the persistence modes in [Privacy And Data Handling](privacy-and-data.md).

## Persistence Model

The current schema groups data into these responsibilities:

| Responsibility | Current entities |
| --- | --- |
| Source inventory | `sources`, `source_files`, `context_roots`, `workspaces` |
| Indexed activity | `sessions`, `activity_events`, `usage_facts`, immutable usage price snapshots, `context_documents`, FTS5 search tables |
| User organization | `workstreams`, `threads`, `checkpoints` |
| Linkable resources | `local_resources`, `external_resources`, Workstream and Thread links |
| Review workflow | `suggestions`, checkpoint resource snapshots, Thread resource matches |
| Maintenance execution | `maintenance_runs` plus artifacts under the runtime data directory |

Resources are canonical entities. A Session or Document is stored once and may relate to any number of Threads. Relationship-specific evidence is stored separately so the resource payload is not duplicated.

Checkpoint records are versioned, user-confirmed resume states. Confirmation captures a snapshot of resources linked to the Workstream and its Threads at that time.

## Ingestion Contract

- Preserve raw source identity and timestamps.
- Prefer append-only normalized activity events.
- Deduplicate by stable source ID where available and deterministic fingerprint otherwise.
- Keep imported content separate from user-confirmed checkpoints.
- Make search indexes and statistics rebuildable from stored normalized data where possible.
- Record source check time, status, failures, and refresh requirements.
- Do not re-import maintenance Run artifacts as ordinary Sessions or Local Context documents.
- Treat generated titles and summaries as presentation, never as stable identifiers.

Original Claude and Codex JSONL remains the authoritative Session source. LocalBrain stores normalized searchable text, selected metadata, source paths, source line numbers, and deterministic IDs so the index can be rebuilt.

Token usage is a separate derived-fact lane from searchable Activity Events. Both adapters preserve one stable source-record identity, the raw model name, non-cached input, output, cache-write, cache-read, reasoning, source-total, and normalized-total semantics when those values are available. Claude input is already non-cached and its cache creation and cache read values remain additive. When Claude reports a zero cache-creation aggregate that contradicts a positive internally consistent ephemeral breakdown, the adapter uses the breakdown and records that bounded fallback. Each Codex `token_count` event contributes its direct `last_token_usage` when available; `total_token_usage` is Session-cumulative and is subtracted from the preceding observation only as a fallback. Spawned or forked subsession replay prefixes seed that cumulative baseline but do not produce copied facts. Unchanged zero deltas are ignored, source input has cached input subtracted, and reasoning output remains an informational subset of output rather than an additional total.

Every directly observed usage fact is eligible regardless of Session class or role. Maintenance Sessions and subsessions therefore remain excluded from ordinary Search and workflow statistics while still contributing their own direct usage. Current Claude and Codex observations carry a `direct` aggregation scope. LocalBrain does not persist a second parent rollup, so parent and child direct facts are each counted once; the reserved `includes_children` scope requires a downstream rollup to exclude covered child facts if a future source explicitly provides such an aggregate. A repeated source record updates one deterministic fact, and malformed later evidence cannot erase a previously valid fact. Session source files record the usage normalizer contract that processed them, and each Usage Fact records its independent normalizer version. Unchanged file metadata is current only when this contract version also matches.

When a normalizer contract changes, ordinary Session synchronization performs a versioned repair rather than requiring a user-facing aggregate reset. If any current file for a source has an older contract version, synchronization reparses every current file for that source and reconciles their complete Usage Fact union inside one source-level savepoint: matching identities update, new identities insert, and obsolete source identities delete. This boundary preserves all observations when one Session identity spans several files. A repair identity inherits the closest prior price snapshot and frozen Project attribution unless an approved corrective producer explicitly assigns a new immutable snapshot to repair an invalid token or service-tier contract. Ordinary new facts under an unchanged contract receive the snapshot and current Project evidence available when first observed. Any parse or persistence failure rolls back the complete source replacement and does not advance its source-file contract versions. Source freshness retains the size and modification time observed before parsing, so bytes appended to an active JSONL during the read remain detectable on the next synchronization. The next unchanged synchronization skips all now-current files, making the repair idempotent.

Estimated USD cost is a local trend estimate, not billed spend. Each fact retains the immutable price-snapshot identifier, calculator version, calculation time, and explicit `priced`, `unpriced`, `partial`, or `failed` state used when it was first observed. A growing source record may be recalculated only against its retained snapshot. New prices require a new snapshot identifier and apply only to newly observed facts; historical facts are not repriced except for the explicit corrective-repair exception above. The embedded catalogs include the inspected ccusage 20.0.14 Claude-oriented reference and the approved ccusage 20.0.17-referenced Codex `fast` base and long-context rates. `usage_model_prices` stores optional threshold and above-threshold component rates. Calculator v2 evaluates each fact independently from non-cached input plus cache read, keeps the exact threshold on the base tier, and uses long-context rates only above it; compaction can return a later fact in the same Session to the base tier. This preserves trend semantics while matching the frozen request-price boundary. No catalog creates a runtime ccusage, network, or page-render dependency.

Each new usage fact also freezes its first-observation Project attribution. A currently discovered Git root produces a `git:<canonical-root>` key; otherwise a resolved workspace produces a `path:<canonical-path>` key; missing evidence stays `unassigned`. Workspace ID, name, canonical path, Git root, basis, and attribution time are snapshots rather than live Project joins. Conflict updates preserve them, so a later Git initialization, path move, or workspace enrichment can affect only new facts. Current `workspaces.git_root` follows current filesystem evidence and may change without rewriting historical usage. Legacy or previously unassigned facts are not reconciled automatically.

Activity time is derived separately from usage and cost. Valid Activity Event timestamps form per-Session segments: a gap of exactly 30 minutes remains continuous, while a greater gap starts a new segment. Segments end at the last observed event, are clipped with inclusive-start/exclusive-end range boundaries, and are merged across concurrent Sessions before estimated active seconds and the longest active segment are calculated. Observed Session span remains a separate first-to-last-event value. Single-event segments contribute zero inferred duration, and no value is extended to the current time. Local day and Monday-week boundaries use an explicit IANA timezone.

The Sessions Dashboard read model normalizes `view`, `source`, `metric`, `from`, and `to` GET state before querying facts. Daily uses 30 inclusive local days, Weekly uses 12 Monday-based local weeks, and Cumulative uses monthly running buckets from the earliest eligible real-model usage date. Valid paired custom dates replace only the bounds; malformed, partial, or reversed pairs retain the selected view, source, and metric while falling back to the view default. Token and priced-cost totals include every direct real-model fact, including maintenance and subsession facts, while the usage-linked Session denominator includes only primary work Sessions. Claude records whose raw model is exactly `<synthetic>` remain persisted but are removed at the dashboard query boundary from dates, totals, coverage, breakdowns, and Session counts. Facts without usable timestamps or supported pricing remain explicit coverage limitations rather than zero values.

The same read model normalizes `breakdown=source|model|project`. It groups by source kind, normalized model while retaining raw identities, or the immutable usage-fact Project key; current workspace joins may enable a browse link but never change a historical group. Compatible shares use the selected supported token total or priced-cost total. The first eight ranked groups remain visible and additional groups use native disclosure. Source trust derives current, stale, and error state from source-file status; when the latest attempt has errors, the latest healthy file time is the bounded last-success proxy and previously calculated facts remain visible.

Current-month projection remains a non-persisted compatibility calculation in the read model but is not rendered by the Sessions Dashboard. `calendar-elapsed-v1` divides source-scoped compatible MTD estimated cost by the timezone-aware fraction elapsed between local month start and next local month start. It requires three complete local days, a Cost view whose range contains today, and at least one priced fact. Calculation time, source scope, input total, elapsed fraction, formula version, coverage, and freshness state travel with the internal value. It never updates Usage Facts or their price snapshots and never runs for a historical-only range.

The Sessions inventory owns a Session-only incremental synchronization action. It scans the configured Claude and Codex roots, reconciles normalized Sessions and parent relations, and does not scan Local Context sources. The Sources inventory owns the wider scan that includes those Session sources plus every enabled Local Context root. Both web actions retain the source-file freshness check and skip unchanged healthy Session files.

### Adapter-specific Rules

- Import Claude primary and nested `subagents/` files with distinct Session roles and a source-backed parent relation. Use the nested `agent-*.jsonl` filename stem as child identity; its record-level `sessionId` may denote the owning parent.
- Use the first Codex `session_meta` record as the file identity because a rollout file may contain older embedded metadata.
- Read Codex parent and Git context from that same primary metadata record; later embedded metadata never replaces the file identity.
- Index human and assistant message text plus tool names; do not index opaque tool arguments or result payloads by default.
- Preserve historical `cwd_raw` independently from an optional resolved current Project relation.
- Handle a Session file that is still growing or partially written without discarding previously valid records.

### Session Policies

Claude and Codex histories are parsed into normalized Sessions and Activity Events. A maintenance marker at the beginning of a user message keeps source metadata but excludes the Session from events, search, workflow statistics, and the Sessions Dashboard primary-work Session denominator; its direct Usage Facts remain eligible for token and estimated-cost totals:

```text
[LOCALBRAIN_RUN: lb-<12 hex characters>]
[MODE: maintenance]
```

Claude and Codex subsessions are normalized as source-backed Session rows with a retained source parent identity and a nullable resolved parent self-reference. Unresolved, unsafe, and deeper child relations remain stored but do not fall back to top-level presentation. Only primary Sessions contribute to global Search, Session-derived statistics, Workstream organization candidates, or Workstream maintenance retrieval.

Session detail presentation selects normalized `message` events in source sequence for primary Sessions and eligible direct children. This is a read-model filter only: `tool_call` rows, tool names, source JSONL, and the Session's complete event count remain unchanged. Parent details list same-source direct children; child details resolve only to a same-source primary parent. Existing Claude lazy-subagent paths remain bounded compatibility routes and use the same message-only presentation.

Session branch metadata is stored per Session from authoritative JSONL. Workspaces retain the currently discovered canonical `git_root` of the containing repository and do not store a branch value; historical Project attribution belongs to usage-fact snapshots instead.

### Local Context Sources

The `context_roots` registry owns folders, individual files, and Apple Notes sources shown in Local Contexts.

- Folder registration scans supported content recursively.
- Overlapping parent and child folder roots are rejected to keep document ownership unambiguous.
- Hidden and generated directories such as `.git`, `node_modules`, `dist`, and `build` are excluded.
- Removing a source disables browsing and search without deleting original local files.
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
- source-neutral Claude/Codex usage facts with immutable local trend-cost snapshots
- reproducible Sessions Dashboard usage summary, MTD context, GET scope, and Daily, Weekly, or Cumulative token/cost history
- durable Claude Task Runner history, streaming result display, cancellation, and reviewable structured output
- deterministic SQLite/FTS5 retrieval without hard candidate or evidence-count caps
- normalized many-to-many Thread resource matches with reusable fingerprints and deduplicated evidence
- source browsing for folders, files, and Apple Notes
- Atlassian navigation shell without external ingestion

Open implementation work is tracked in the [Project Backlog](../../plans/project/backlog.md).

## Architectural Constraints

- LocalBrain remains local-first and single-user during the MVP.
- External integration starts read-only.
- User review state and source provenance must survive rescans and suggestion refreshes.
- A failed maintenance Run must not clear the existing review queue.
- Historical source paths must remain visible when their current Project relation is missing or changes.
- The SQLite schema and runtime data must remain portable to a later desktop wrapper.
- Desktop packaging must not obscure data location, permissions, backup, or shutdown behavior.
