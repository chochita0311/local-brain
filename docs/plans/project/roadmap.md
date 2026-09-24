# Project Roadmap

## Current Increment — 2026-09-24

The owner stopped implementation and calculations after inspecting the delivered
continuous map. Keep it available for observation; the
[design-plan handoff](../design/workflow-map-design-plan.md#handoff-to-next-track)
owns the resume boundary. Session documentation and publication are not approval
to launch the next model trial or production transition.

Owner review returned the freeform map's visual direction to planning. The
current [FEAT-0104 temporal correction](../feature/feat-0104-temporal-affinity-flow.md)
uses actual left-to-right time, similarity strands, activity gaps and period
evidence, with interactive neighborhood zoom. RUN-117 corrects RUN-116's map
paging: one continuous scrollable canvas, independent text pages and stable
cross-page connections/camera. It reuses the reader
without re-embedding, new training, identity inference or organization changes.
RUN-115 below is historical technical evidence, not acceptance of its geometry.

The owner-requested
[relation-first planning review](../design/workflow-map-design-plan.md#relation-first-inspection-track)
is complete. The owner's subsequent continuous-through-UI authorization delivered
real replay verification (RUN-113), the passed whole-history reader under
[FEAT-0101](../feature/feat-0101-full-history-affinity-inspection-contract.md)
(RUN-114), and the passed
[FEAT-0102](../feature/feat-0102-full-history-affinity-map.md) observation map
(RUN-115). The local screen now supports group/subgroup/Session/evidence
inspection, stable zoom/history and complete native fallback. The independent
[FEAT-0103](../feature/feat-0103-direct-context-work-relation-trial.md) proposes one
direct-context relation trial with a fixed stop, not another open-ended extractor
iteration. That trial remains draft and unexecuted. Affinity inspection no
longer waits for complete claim/state extraction, but it does not claim enduring
areas, same-work lineage or replacement viability. Current policies and old trial
failures remain unchanged.

### Preceding Evidence And Remaining Gaps

[FEAT-0098](../feature/feat-0098-local-work-context-inference.md) installs and
evaluates the approved local Qwen3-4B model for quoted work-context extraction and
continuity judgments. Installation/runtime checks passed, but its development
quality gate failed (goal omission and incomplete grounding). Private processing
remains blocked after the same-model reasoning/staged comparison also fails
admission (3/4 and 2/4 automated cases, with additional semantic errors). Holdout
is untouched. The approved Qwen3-8B comparison in RUN-106 is now also complete:
installation succeeded, but thinking passes 1/4 and staging 2/4 fixed cases.
The owner approved the bounded extraction/protocol redesign in RUN-107. It compares
source-selected inference mechanics without changing embeddings or downloading
another model. Both baselines and existing admission criteria are retained.
RUN-107 is now complete but also admission-blocked: source-choice mechanics
stabilize output structure, not goal extraction/association. Its three candidates
pass 3/4, 2/4 and 3/4 content cases; holdout/private execution remain unperformed.
The subsequent owner-requested
[method review](../research/workflow-reconstruction-method-review.md) is complete.
Its controlled protocol/semantic diagnostic was subsequently approved and
completed under [RUN-108](../run/run-20260923-108-work-context-protocol-diagnostic.md).
All 288 conditions and zero-generation replay complete, but meaning labels do
not remove unsupported continuity. That diagnostic PASS leaves model admission
blocked. The owner-approved evidence-first follow-up now also completes under
[RUN-109](../run/run-20260923-109-evidence-first-work-context.md): 3/4 original
development and 4/12 new composition passes, with field-role confusion and false
continuation surviving the same-model audit. Both gates fail. Contract/replay
pass, but no holdout or private run is admitted. A matched direct-role/property
comparison was the next proposed bounded decision. The owner has now approved
that synthetic diagnostic under
[RUN-110](../run/run-20260923-110-work-role-formulation-comparison.md), now complete.
Direct role sets improve exact matches (15/32 versus 8/32 order conditions), but
omit claims and keep completed work pending; a relation control still falsely
continues topic-only work. No extractor is admitted. The subsequent owner-approved
structure review is complete and proposes
[FEAT-0099: Source Claims And Work State Projection](../feature/feat-0099-source-claims-and-work-state-projection.md)
instead of continuing prompt/choice variants. The owner then approved its pure
synthetic implementation under [RUN-111](../run/run-20260923-111-source-claims-and-work-state-projection.md),
now `passed`: 50 tests and full 900-test regression (one optional skip). It projects
reported state from supplied claims/bindings; it neither extracts them nor admits
a model. The subsequent adapter review produced
[FEAT-0100](../feature/feat-0100-source-claim-extraction-and-binding-trial.md),
subsequently approved and completed under
[RUN-112](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md).
Its model-aware adapter and zero-generation replay pass their contract, but all
28 extractions are protocol-rejected and conditioned binding fully passes only
3/28. No end-to-end call is eligible, so all quality gates fail and the original
holdout remains unconsumed. The subsequent output/evidence-interface review
produced the planning split above; no automatic new trial or private job follows.
No production persistence or UI change belongs to that completed Run.
Production area/effort identity and replacement remain later evaluated boundaries.
[FEAT-0097](../feature/feat-0097-replayable-session-simulation.md) completed the
full-Session affinity backfill and actual zero-encoding unchanged/grouping-only
replay. The read consumer revalidates report freshness before display.
Enduring work areas and subordinate outcome-oriented work are separate levels;
semantic communities do not prove temporal lineage. The earlier bounded
model-free sample is a comparator. A stable time-axis map with evidence zoom,
implemented under FEAT-0104, is available now; semantic quality, stable identity,
automatic updates and finite legacy retirement remain downstream increments.

Status: Phase 1 complete; Phase 2 whole-history affinity inspection delivered under passed FEAT-0101/0104 and further development stopped by owner; previous sample and Session Focus/corrections retained, relation trial draft and replacement quality outstanding; Phase 4 Atlassian structure-reference product delivered

Last reviewed: 2026-09-24

## Current Direction

### Current Validation State

LocalBrain is validating how to move from manually maintained Workstream and
Thread organization toward a source-backed directional Workflow Map while
expanding approved external connectors one bounded read-only source at a time.
The existing Workstream product remains current behavior while the delivered
Session Workflow Focus and correction path is evaluated through real use. The
earlier Session Focus map is a useful Session Lineage surface, not yet the intended
Workstream discovery or replacement experience.
The separate default Auto Work surface now provides whole-history temporal
affinity inspection as described in [Current Increment](#current-increment--2026-09-24).
The owner rejected reference-pair proliferation and repeated candidate review/
promotion. The current replan targets automatically usable and maintained
outcome-level flows, with corrections as exceptions. Existing organization is
protected temporarily for development/transition validation and recovery, not
the mandatory final hierarchy or permanent storage. Retiring unused/orphaned
legacy data, obsolete tables, and expired backups is part of the
[transition endpoint](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md#legacy-transition-boundary).

### Delivered Baselines

The design-system realignment of the current screen families is complete and
accepted. [PRD-0017](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
is the approved analysis/validation planning boundary for automatic reconstruction. Its first
approved chain, FEAT-0085 through FEAT-0089, passed in dependency order and
delivered the Episode/direction contract, bounded cross-source projection,
Session Focus map, append-only assertion ledger, and contextual corrections.
FEAT-0090 retains its tested pure pair contract, but
[RUN-20260915-100](../run/run-20260915-100-workstream-candidate-discovery-contract.md)
returned to planning after the owner rejected its product-level continuation.
Neither that contract nor the Focus map establishes useful automatic grouping.
PRD-0014 and FEAT-0075 through FEAT-0080
remain the passed Atlassian Explorer baseline. PRD-0015 and FEAT-0081 also
remain the passed bounded follow-up for domain-first hierarchy, strict
empty-inventory local Sync admission, and ordinary link/document terminology.
PRD-0016 is passed after its dependency-ordered standard-URL
structure-reference chain completed: FEAT-0082 owns semantic taxonomy,
query-safe Session projection, and identity precedence; FEAT-0083 owns durable
structure-reference Sync and Explorer/Search behavior.

### Remaining Validation After Resumption

FEAT-0091 through FEAT-0094 remain superseded. The owner approved
[FEAT-0095: Bounded Work Reconstruction Experiment](../feature/feat-0095-bounded-work-reconstruction-experiment.md),
and [RUN-20260915-101](../run/run-20260915-101-bounded-work-reconstruction-experiment.md)
implemented its minimal non-model extractor, matched metadata/text comparison,
scoring, and read-only local command. Synthetic technical checks passed; the
owner selected current LocalBrain data through now, and bounded preparation plus
an unassessed private comparison succeeded. Feature/Run remain `blocked` on
independent quality evidence, not DB/period selection.

The owner then approved [Auto Work inspection](../feature/feat-0096-auto-work-inspection.md)
before that verdict. Its previous-sample view at `/auto-work?mode=sample` exposes
groups, source evidence, unassigned wording, and sampled coverage. The narrow
[UI Run](../run/run-20260916-102-auto-work-inspection.md) verifies presentation
and transport, not semantic reconstruction quality. Post-run review can now use
the actual local screen; no whole-sample assignment or approval queue is required.

Its independent quality gap remains open, but it is not a blocker on the
separately passed full-history reader and temporal observation map. Production
identity/update/correction ownership, replacement overview/detail and legacy
cutover still require their own relevant quality and transition evidence.
FEAT-0103 is the separately proposed relation trial, not an active calculation;
existing 4B/8B failures do not require more downloads or routine owner labeling.

### Explicitly Deferred

Global Atlas rendering, topic terrain, AI retrieval, new source adapters, model
execution beyond the explicitly approved trials, and desktop packaging remain deferred without separately approved
Features. Automatic overview/flow detail and replacement of manual organization
are proposed core outcomes, not post-promotion extras.

Priorities after an owner-requested resumption (not active execution):

1. Prepare independent local assessment for the now-executed bounded experiment,
   then measure goal coverage, false grouping,
   fragmentation, stability, and correction burden without existing organization.
   Keep partial or failing local evidence distinct from synthetic technical PASS;
   no whole-sample naming/assignment task should be imposed on the owner.
2. Use the passed deterministic Session Workflow Focus and corrections across
   several real efforts and record where its reconstructed story, branch choice,
   or evidence coverage is insufficient.
3. Review the separately proposed direct-context relation boundary against the
   completed 4B/8B extraction evidence before selecting another trial. Do not
   repeat unchanged comparisons, make a candidate-review UI a prerequisite, or
   treat affinity grouping as proof of work continuity.
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
- representative work can be expressed at outcome and contribution levels
  without forcing it into manually maintained containers
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

- automatic outcome-level reconstruction and low-burden exception correction
- controlled treatment of legacy Workstream/Thread merge, split, move, and
  archive needs during replacement, followed by finite-retention expiry and
  eligible unused-data/table cleanup; no independent expansion of manual forms
- a unified cross-source flow history and direct resumption path
- historical path alias and repository identity reconciliation
- stronger source-aware suggestion scoring and batch review
- clearer current goal, blocker, next-action, and checkpoint-freshness presentation

Completed planning increment:

- [PRD-0009: Data Model Value Dictionaries And Pinned Session Recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md) (`passed`; FEAT-0057 through FEAT-0061 `passed`)

Open planning increment:

- [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
  (`approved` for bounded analysis/validation planning; Session Focus/corrections
  remain delivered and FEAT-0091–0094 are superseded. FEAT-0095 is implemented
  with synthetic and unassessed current-data execution evidence, but blocked
  on independent quality assessment;
  production ownership and replacement UI wait for useful extraction evidence.)

Exit criteria:

- one outcome-level flow combines supporting work across folders,
  repositories, AI tools, and admitted external references
- a flow can be understood and resumed without manual container setup or
  routine approval; optional corrections preserve evidence and recovery
- legacy transition transfers still-needed data and completes agreed
  finite-retention cleanup, including storage reclamation and a minimal record
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
