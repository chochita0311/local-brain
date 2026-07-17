# Project Roadmap

Status: Phase 1 complete; Phase 2 core vertical slice implemented

Last reviewed: 2026-07-17

## Current Direction

LocalBrain is validating the Workstream and Thread workflow as a local web application before expanding external connectors or desktop packaging.

The design-system realignment of the current screen families is complete and accepted. Near-term work remains focused on validating and extending the product workflow rather than starting another broad visual redesign.

Near-term priorities:

1. Use several real Workstreams through repeated daily context switches and evaluate whether Thread and checkpoint fields are sufficient.
2. Add the unified cross-source Workstream timeline and historical path reconciliation.
3. Improve source-aware matching, review ergonomics, and source controls.
4. Define approved external persistence behavior before implementing MCP Gateway ingestion.

Detailed implementation tasks and unresolved decisions live in the [Project Backlog](backlog.md). Durable product and technical contracts live under [Policies](../../README.md#policies).

## Phase Overview

| Phase | Goal | Status |
| --- | --- | --- |
| 0. Discovery and constraints | Verify source availability, policy, and representative workflows | Ongoing as new source types are added |
| 1. Local activity foundation | Reliably collect and inspect local activity | Complete |
| 2. Workstream and resume MVP | Find and resume interrupted work | Core vertical slice implemented |
| 3. Activity insights | Add reproducible cavemem-style workflow analysis | Planned |
| 4. External read-only sources | Connect approved ticket, conversation, Git, and document systems | Planned |
| 5. Context reconciliation | Produce reviewable current context while preserving uncertainty | Planned |
| 6. Handoff and controlled actions | Support low-friction AI handoff and explicitly approved actions | Planned |
| 7. macOS packaging | Package the validated workflow as a native-feeling application | Planned |

## Phase 0: Discovery And Constraints

**Goal:** verify data availability, policy, and the smallest useful workflow before committing to source-specific persistence.

Work:

- inspect installed Claude and Codex local formats and retention behavior
- inspect representative project, context-folder, Git, and Apple Notes layouts
- inspect cavemem schema and export formats when available
- inventory approved MCP Gateway tools, authentication, and read/write capabilities
- define reference, cache, and index policy for each external source type
- validate the product model against representative Workstreams

Exit criteria:

- source inventory and access constraints are documented without exposing private inventory in Git
- representative Workstreams fit the Workstream and Thread model without ambiguity
- persistence policy is explicit for each source type
- MVP inputs and exclusions are agreed

## Phase 1: Local Activity Foundation

**Goal:** establish reliable local collection before higher-level organization and intelligence.

Delivered:

- FastAPI, SQLite, FTS5, and a server-rendered local UI
- Source, Session, Activity Event, context document, and workspace storage
- Claude and Codex adapters
- source paths, timestamps, prompts, tool activity, and available Git metadata
- deterministic import, refresh, and deduplication
- source, project, Session, search, and activity inspection views

Exit criteria:

- repeated imports do not duplicate Sessions or events
- Claude and Codex activity is visible in one local store
- displayed activity retains source metadata
- raw activity can be reprocessed after parser or schema changes

Status: complete for the current local formats. Parser compatibility and source-health hardening remain ongoing maintenance.

## Phase 2: Workstream And Resume MVP

**Goal:** solve the primary problem of finding and resuming interrupted work.

Delivered:

- user-created Workstreams and nested Threads
- versioned checkpoints and resource snapshots
- links to Sessions, Local Contexts, projects, local paths, and external references
- deterministic Session and Document Suggestions with reject, restore, and refresh behavior
- Workstream-first Dashboard and separate Sessions Dashboard
- folder, individual file, and Apple Notes source browsing
- Claude maintenance Runs with structured reviewable output
- local full-text search and source filtering

Remaining:

- Workstream and Thread merge, split, move, and archive operations
- unified cross-source Workstream timeline
- historical path alias and repository identity reconciliation
- stronger source-aware suggestion scoring and batch review
- clearer current goal, blocker, next-action, and checkpoint-freshness presentation

Exit criteria:

- one Workstream can combine multiple folders, repositories, AI tools, and external references
- a paused Workstream can be understood and resumed from one screen
- incorrect Suggestions can be corrected without data loss
- the application is useful in daily work without external connector ingestion

## Phase 3: Activity Insights And cavemem Compatibility

**Goal:** provide useful workflow analysis from the same normalized events that power Workstreams.

Work:

- add optional cavemem database or JSONL import
- define reproducible Session duration and activity-count rules
- implement tool, project, file type, topic, and error statistics
- calculate context switching and Session fragmentation
- surface repeated errors, repeated questions, and idle Workstreams
- link every metric back to filtered timelines and Workstreams
- export user-owned normalized activity through a reviewed privacy flow

Exit criteria:

- statistics can be reproduced from stored events
- imported cavemem records are deduplicated against directly collected activity where possible
- metric definitions state source limitations and avoid false precision
- insights reveal at least one actionable repeated or forgotten work pattern

## Phase 4: External Read-only Sources

**Goal:** connect approved company context without creating an uncontrolled second data store.

Work:

- introduce a generic approved MCP Gateway client boundary
- discover available ticket, conversation, hosted Git, and document tools
- normalize source-specific results behind adapters
- support explicit reference, cache, and index persistence modes
- connect external resources to Workstreams and Threads
- add freshness, deep links, refresh, and unavailable-source states
- combine local and federated search results without hiding their storage boundaries

Exit criteria:

- external sources are accessed only through approved operations
- linked external resources retain provenance and freshness
- local persistence follows the configured policy for each source
- stale or inaccessible information is clearly identified
- no external source is modified

## Phase 5: Context Reconciliation

**Goal:** turn connected sources into reliable current context while preserving uncertainty.

Work:

- classify source role and source-of-truth priority per Workstream
- suggest related items using identifiers, paths, branches, content, and time
- extract candidate goals, decisions, facts, errors, and open questions
- distinguish generated Suggestions from user-confirmed checkpoints
- display disagreements between code, tickets, documents, and conversations
- track source changes since the previous checkpoint
- generate a reviewable checkpoint draft

Exit criteria:

- every extracted statement retains provenance
- conflicts remain visible until explicitly resolved
- generated content is never presented as user-confirmed fact
- a stale Workstream can be refreshed without rereading every source

## Phase 6: Handoff And Controlled Actions

**Goal:** make LocalBrain a practical entry and exit point for AI-assisted work.

Work:

- export a compact checkpoint for Claude or Codex
- open the relevant terminal, editor, repository, ticket, or source link
- capture end-of-session state with low friction
- refresh selected sources before work begins
- evaluate narrowly scoped external write-back
- require visible preview and confirmation for ticket, conversation, document, or Git mutations

Exit criteria:

- a Workstream can move between Claude and Codex with source links intact
- end-of-session state can be recorded in under a minute
- every external write is previewed, attributable, and explicitly approved

## Phase 7: macOS Packaging

**Goal:** package the validated workflow as a convenient macOS application.

Work:

- wrap the existing frontend with Tauri when feasible
- manage backend startup, shutdown, and local port lifecycle
- add launcher or menu-bar behavior only when it improves daily use
- expose data location, backup, export, and recovery controls
- evaluate signing, notarization, and updates when distribution expands

Exit criteria:

- the app launches from an icon without manual server commands
- existing SQLite data remains compatible
- shutdown does not corrupt active imports, indexes, or Runs
- local data location and permissions remain understandable and controllable

## MVP Boundary

The first usable release is Phases 0 through 2 plus only the normalized event foundations required for later Insights.

Deferred beyond that boundary:

- broad MCP integration
- automatic semantic linking across every source
- external write-back
- cloud sync and collaboration
- mobile support
- complex graph editing
- mandatory external AI or embedding APIs
- native packaging before workflow validation

## Validation Strategy

Primary scenarios:

1. Find which directory and AI tool were used most recently for a Workstream.
2. Reconstruct work spanning a repository and a separate context source.
3. Resume work after several days without rereading complete Sessions.
4. Find a repeated error or question across Claude and Codex.
5. Connect an external request, discussion, code change, and local implementation without losing provenance.
6. Identify stale or conflicting information before implementation begins.

Measures:

- time required to locate the correct past Session
- time required to resume a paused Workstream
- number of manual source searches required before resumption
- correction rate for automatic Suggestions
- percentage of active Workstreams with a current checkpoint
- usefulness of Insights in finding repeated or forgotten work

## Main Risks And Controls

| Risk | Control |
| --- | --- |
| Ingesting every source before proving the workflow | Keep early phases local and narrow |
| Incorrect automatic grouping | Keep Suggestions reversible and user-confirmed |
| Duplicate events from multiple collectors | Preserve source IDs and deterministic fingerprints |
| Stale external context | Track freshness and support explicit refresh |
| Informal discussion treated as official truth | Preserve source role, status, and conflicts |
| External content persisted beyond policy | Enforce per-source reference, cache, and index modes |
| AI summary invents certainty | Separate generated inference from confirmed facts |
| Statistics imply misleading precision | Document definitions and source limitations |
| Desktop packaging distracts from product validation | Defer packaging until the local workflow is useful |
