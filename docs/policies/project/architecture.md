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
Claude / Codex / local files / Git / cavemem / MCP Gateway
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
| Indexed activity | `sessions`, `activity_events`, `context_documents`, FTS5 search tables |
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

The Sessions inventory owns a Session-only incremental synchronization action. It scans the configured Claude and Codex roots, reconciles normalized Sessions and parent relations, and does not scan Local Context sources. The Sources inventory owns the wider scan that includes those Session sources plus every enabled Local Context root. Both web actions retain the source-file freshness check and skip unchanged healthy Session files.

### Adapter-specific Rules

- Import Claude primary and nested `subagents/` files with distinct Session roles and a source-backed parent relation. Use the nested `agent-*.jsonl` filename stem as child identity; its record-level `sessionId` may denote the owning parent.
- Use the first Codex `session_meta` record as the file identity because a rollout file may contain older embedded metadata.
- Read Codex parent and Git context from that same primary metadata record; later embedded metadata never replaces the file identity.
- Index human and assistant message text plus tool names; do not index opaque tool arguments or result payloads by default.
- Preserve historical `cwd_raw` independently from an optional resolved current Project relation.
- Handle a Session file that is still growing or partially written without discarding previously valid records.

### Session Policies

Claude and Codex histories are parsed into normalized Sessions and Activity Events. A maintenance marker at the beginning of a user message keeps source metadata but excludes the Session from events, search, and Sessions Dashboard statistics:

```text
[LOCALBRAIN_RUN: lb-<12 hex characters>]
[MODE: maintenance]
```

Claude and Codex subsessions are normalized as source-backed Session rows with a retained source parent identity and a nullable resolved parent self-reference. Unresolved, unsafe, and deeper child relations remain stored but do not fall back to top-level presentation. Only primary Sessions contribute to global Search, Session-derived statistics, Workstream organization candidates, or Workstream maintenance retrieval.

Session detail presentation selects normalized `message` events in source sequence for primary Sessions and eligible direct children. This is a read-model filter only: `tool_call` rows, tool names, source JSONL, and the Session's complete event count remain unchanged. Parent details list same-source direct children; child details resolve only to a same-source primary parent. Existing Claude lazy-subagent paths remain bounded compatibility routes and use the same message-only presentation.

Session branch metadata is stored per Session from authoritative JSONL. Workspaces retain `git_root` as the filesystem root of the containing repository and do not store a branch value.

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
