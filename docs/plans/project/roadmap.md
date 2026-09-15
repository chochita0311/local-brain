# Project Roadmap

Status: Phase 1 complete; Phase 2 deterministic Session Workflow Focus and correction chain delivered; Workstream candidate discovery is the next planning boundary; Phase 4 Atlassian structure-reference product delivered

Last reviewed: 2026-09-15

## Current Direction

### Current Validation State

LocalBrain is validating how to move from manually maintained Workstream and
Thread organization toward a source-backed directional Workflow Map while
expanding approved external connectors one bounded read-only source at a time.
The existing Workstream product remains current behavior while the delivered
Session Workflow Focus and correction path is evaluated through real use. The
delivered map is a useful Session Lineage surface, not yet the intended
Workstream discovery or replacement experience.

### Delivered Baselines

The design-system realignment of the current screen families is complete and
accepted. [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
defines the upper product boundary for a source-backed Workflow Map. Its first
approved chain, FEAT-0085 through FEAT-0089, passed in dependency order and
delivered the Episode/direction contract, bounded cross-source projection,
Session Focus map, append-only assertion ledger, and contextual corrections.
PRD-0014 and FEAT-0075 through FEAT-0080
remain the passed Atlassian Explorer baseline. PRD-0015 and FEAT-0081 also
remain the passed bounded follow-up for domain-first hierarchy, strict
empty-inventory local Sync admission, and ordinary link/document terminology.
PRD-0016 is passed after its dependency-ordered standard-URL
structure-reference chain completed: FEAT-0082 owns semantic taxonomy,
query-safe Session projection, and identity precedence; FEAT-0083 owns durable
structure-reference Sync and Explorer/Search behavior.

### Next Approval Decision

No Feature is currently in-loop. The next product-planning decision is a bounded
Workstream Candidate Discovery and Review increment: derive provisional,
many-to-many work candidates from source-backed evidence, explain why evidence
was grouped, and require explicit user promotion rather than silently changing
the current Workstream hierarchy.

### Explicitly Deferred

Workstream Lens composition, Atlas, topic terrain, AI retrieval, Workflow Map
model use, and desktop packaging remain deferred without separately approved
Features.

Near-term priorities:

1. Define and review the smallest Workstream Candidate Discovery boundary,
   including evidence admission, candidate confidence and explanation, and
   rename, merge, split, ignore, and promote controls.
2. Use the passed deterministic Session Workflow Focus and corrections across
   several real efforts and record where its reconstructed story, branch choice,
   or evidence coverage is insufficient.
3. Evaluate topic terrain or Qwen only if the deterministic baseline exposes a
   measurable semantic-orientation gap that explicit evidence cannot resolve.
4. Improve source-aware matching, review ergonomics, and source controls.
5. Exercise the completed Site-first Explorer, Add, local Sync, Connections,
   and explicit Refresh workflow through repeated daily use.
6. Evaluate pinned Session recall and deterministic related context through
   repeated work resumption before expanding into native process resume or
   user-curated context relations.

Detailed implementation tasks and unresolved decisions live in the [Project Backlog](backlog.md). Durable product and technical contracts live under [Policies](../../README.md#policies).

Recently completed cross-surface reconciliation:

- [PRD-0011: Shared Native Select Control Geometry](../prd/prd-0011-shared-native-select-control-geometry.md) (`passed`; shared native-select geometry verified across Atlassian, Workstream, and Search)

## Phase Overview

| Phase | Goal | Status |
| --- | --- | --- |
| 0. Discovery and constraints | Verify source availability, policy, and representative workflows | Ongoing as new source types are added |
| 1. Local activity foundation | Reliably collect and inspect local activity | Complete |
| 2. Workstream and resume MVP | Find and resume interrupted work | Core vertical slice implemented |
| 3. Activity insights | Add reproducible usage, cost, workflow, and skill intelligence | Usage and cost dashboard implemented; workflow intelligence planned |
| 4. External read-only sources | Connect approved ticket, conversation, Git, and document systems | Atlassian local vertical slice, Site-first follow-up, and standard-URL structure references implemented; connected validation and other sources planned |
| 5. Context reconciliation | Produce reviewable current context while preserving uncertainty | Planned |
| 6. Handoff and controlled actions | Support low-friction AI handoff and explicitly approved actions | Planned |
| 7. macOS packaging | Package the validated workflow as a native-feeling application | Planned |

## Phase 0: Discovery And Constraints

**Goal:** verify data availability, policy, and the smallest useful workflow before committing to source-specific persistence.

Work:

- inspect installed Claude and Codex local formats and retention behavior
- inspect representative project, context-folder, Git, and Apple Notes layouts
- review activity-analysis tools such as cavemem as reference implementations, not LocalBrain sources or connectors
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
- shared safe Markdown reading across Local Context previews, context-aware full Documents, and Session or Subsession conversations
- passed source-neutral Session/Subsession browsing, parent-owned child disclosure, and conversation-focused detail behavior
- Claude maintenance Runs with structured reviewable output
- local full-text search and source filtering

Remaining:

- Workstream and Thread merge, split, move, and archive operations
- unified cross-source Workstream timeline
- historical path alias and repository identity reconciliation
- stronger source-aware suggestion scoring and batch review
- clearer current goal, blocker, next-action, and checkpoint-freshness presentation

Completed planning increment:

- [PRD-0009: Data Model Value Dictionaries And Pinned Session Recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md) (`passed`; FEAT-0057 through FEAT-0061 `passed`)

Open planning increment:

- [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
  (`approved`; FEAT-0085 through FEAT-0089 passed in dependency order for
  deterministic Session-anchored projection, all-current-source evidence
  admission, Focus-first map interaction, reversible corrections, and no
  required AI model; product review retained this as Session Lineage and
  returned Workstream Candidate Discovery to planning before any lens, Atlas,
  or model boundary)

Exit criteria:

- one Workstream can combine multiple folders, repositories, AI tools, and external references
- a paused Workstream can be understood and resumed from one screen
- incorrect Suggestions can be corrected without data loss
- the application is useful in daily work without external connector ingestion

## Phase 3: Activity Insights And Workflow Intelligence

**Goal:** provide trustworthy usage, cost, and workflow analysis from the same source-backed activity that powers Workstreams.

Planning tracks:

- [PRD-0004: Session Usage And Cost Dashboard](../prd/prd-0004-session-usage-and-cost-dashboard.md) (`passed`)
- [PRD-0005: Workflow And Skill Intelligence](../prd/prd-0005-workflow-and-skill-intelligence.md) (`draft`)

Executed PRD-0004 Features:

All implementation, corrective, and combined synthetic responsive-evidence checks are passed.

- [FEAT-0020: Usage And Cost Fact Contract](../feature/feat-0020-usage-and-cost-fact-contract.md) (`passed`, direct-event-first normalization, request-tier pricing, and source-level repair)
- [FEAT-0021: Activity And Project Attribution Contract](../feature/feat-0021-activity-and-project-attribution-contract.md) (`passed`)
- [FEAT-0022: Usage Summary And History](../feature/feat-0022-usage-summary-and-history.md) (`passed`)
- [FEAT-0023: Usage Breakdown And Trust](../feature/feat-0023-usage-breakdown-and-trust.md) (`passed`)
- [FEAT-0024: Current-Month Projection](../feature/feat-0024-current-month-projection.md) (historical `passed`; visible presentation retired by RUN-20260718-28)

Work:

- define source-neutral token components, model identity, cost basis, price provenance, and source-coverage rules
- present period-scoped usage and cost history plus Source, Model, and Project breakdowns without implying calculated cost is actual billing
- derive insights directly from LocalBrain's normalized Claude and Codex Session records
- use cavemem only as a reference for lifecycle coverage, health reporting, and candidate metric patterns; do not import its database or JSONL and do not expose it as a connector
- define reproducible Session duration and activity-count rules
- implement tool, project, file type, topic, and error statistics
- calculate context switching and Session fragmentation
- surface repeated errors, repeated questions, repeated workflows, skill usage, and idle Workstreams
- keep explicitly observed skill use separate from inferred skill candidates and attach evidence to every generated Suggestion
- link every metric back to filtered timelines and Workstreams
- export user-owned normalized activity through a reviewed privacy flow

Exit criteria:

- usage and cost metrics state their inclusion scope, calculation basis, price provenance, freshness, and unavailable fields
- statistics can be reproduced from stored events
- insights depend only on source-backed LocalBrain records and remain usable without cavemem installed
- metric definitions state source limitations and avoid false precision
- insights reveal at least one actionable repeated or forgotten work pattern

## Phase 4: External Read-only Sources

**Goal:** connect approved company context without creating an uncontrolled second data store.

Planning tracks:

- [PRD-0007: Atlassian Source Memory And Explicit Refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md) (`passed`)
- [PRD-0008: Connected Atlassian Validation And Schema ERD Routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md) (`passed`; FEAT-0053 through FEAT-0056 `passed`)
- [PRD-0010: Atlassian UI And Interaction Reconciliation](../prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md) (`approved`; FEAT-0062 and FEAT-0063 passed, boundary remains open for later owner observations)
- [PRD-0014: Atlassian Explorer And Unified Retrieval](../prd/prd-0014-atlassian-explorer-and-unified-retrieval.md) (`passed`; FEAT-0075 through FEAT-0080 passed, AI retrieval deferred)
- [PRD-0015: Atlassian Site-First URL Organization](../prd/prd-0015-atlassian-site-first-url-organization.md) (`passed`; FEAT-0081 passed RUN-91 Attempt 1)
- [PRD-0016: Atlassian Standard URL Structure References](../prd/prd-0016-atlassian-standard-url-recognition.md) (`passed`; FEAT-0082 passed RUN-92 and FEAT-0083 passed RUN-93)

Executed PRD-0007 Features:

- [FEAT-0044: MCP Capability And Read-Only Policy](../feature/feat-0044-mcp-capability-and-read-only-policy.md) (`passed`)
- [FEAT-0045: Provider-Neutral External Sync Run Contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md) (`passed`)
- [FEAT-0046: Atlassian Source Item Identity And Freshness Contract](../feature/feat-0046-atlassian-source-item-identity-and-freshness-contract.md) (`passed`)
- [FEAT-0047: Bounded Atlassian URL Evidence Extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md) (`passed`)
- [FEAT-0048: Atlassian Item And Space Registration](../feature/feat-0048-atlassian-item-and-space-registration.md) (`passed`)
- [FEAT-0049: Explicit Atlassian Refresh And Preview](../feature/feat-0049-explicit-atlassian-refresh-and-preview.md) (`passed`)
- [FEAT-0050: Atlassian Browse, Search, And Local Classification](../feature/feat-0050-atlassian-browse-search-and-local-classification.md) (`passed`)
- [FEAT-0051: Atlassian URL-First Connection Onboarding](../feature/feat-0051-atlassian-url-first-connection-onboarding.md) (`passed`)

Delivered for Atlassian:

- approved read-only capability policy and a source-neutral Claude/Codex maintenance Run boundary
- stable Source Instance, Site, Space, Item, URL, remote-state/content, local-memory, and evidence ownership
- URL-first local setup, reference/metadata/indexed coverage, Workstream and Thread links, freshness, explicit refresh preview, and local search
- Site-first domain Explorer with `All / Jira / Wiki`, persisted or canonical-URL child groups, honest `소속 미확인`, one exact-first query, compact link/document detail, one-URL Add, empty-inventory local evidence Sync, separate Connections and discovery, and explicit remote Refresh
- deterministic standard Jira/Confluence URL recognition and durable local
  structure references for Project, Board, Filter, Dashboard, service portal/
  project, and Wiki Space URLs, with separate evidence provenance, Search,
  preview/detail, count, and no-script behavior
- bounded direct official Jira evidence plus explicit official Confluence and company Gateway environment-limit classifications
- locally packaged official ELK routing for every Schema ERD with Dagre and textual fallback

Remaining work:

- evaluate the completed Atlassian Explorer and local Sync workflow in repeated real use before approving any further retrieval mode
- recheck official Confluence or company Gateway only after those host capabilities become available and a new bounded validation inventory is approved
- discover and normalize approved conversation, hosted Git, email, and other document sources behind source-specific adapters
- combine local and federated results only where storage and freshness boundaries remain visible

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
