# Product Model

## Purpose

LocalBrain is a local-first developer work context hub. It connects development activity scattered across local projects, Claude and Codex sessions, Git, tickets, conversations, and documents into resumable Workstreams.

The product has two equal goals:

1. **Continuity:** answer where work stopped, what is currently known, and what should happen next.
2. **Insights:** show which tools, projects, technologies, and work patterns occupy the user's attention.

LocalBrain is not only a chat history viewer, note-taking app, activity dashboard, or mirror of company systems. Its primary responsibility is to preserve relationships between work artifacts and maintain a reliable restart point.

## Product Principles

### Workstream First

The primary organization unit is a **Workstream**, not a session, directory, repository, ticket, or daily note. A Workstream represents one user-defined area of work and may span any number of local and external sources.

A **Thread** is a smaller topic within a Workstream, such as one feature, integration, investigation, or retirement effort. Concrete resources normally attach to a Thread because their relevance is usually specific. Workstream-level resources are reserved for evidence shared by multiple Threads.

Workstreams are created and named by the user. LocalBrain may suggest relationships, but a directory or model inference must not silently define a Workstream.

### Automatic Capture, Explicit Organization

Raw activity should require little manual effort. Workstream assignments, resource links, and checkpoint drafts may be suggested automatically, but they remain pending until accepted. Rejected Suggestions remain reviewable and can be restored.

### Preserve Provenance And Uncertainty

Every generated summary, relationship, decision, and claim should retain evidence linking it to its source. LocalBrain must distinguish:

- imported source data
- AI-generated inference
- user-confirmed relationships and checkpoints
- unavailable, stale, or conflicting information

Conflicting sources remain visible as conflicts or open questions rather than being silently collapsed into one answer.

### Treat Sources By Role

| Source | Default role |
| --- | --- |
| Runtime results and logs | Operational signal about current behavior |
| Current repository code | Implementation truth |
| Approved specifications and policies | Authoritative intended contract |
| Tickets | Planned work and tracked status |
| Pull requests and commits | Change history and implementation rationale |
| Conversations | Discussion, informal decisions, and historical context |
| Claude and Codex sessions | Investigation history and personal working context |
| Local Context documents | Curated personal memory and handoff context |

Source roles are defaults, not automatic conflict resolution. Provenance, freshness, and user judgment remain necessary.

### Resolve Sources Explicitly

When sources disagree, use these domain-specific interpretation orders:

| Domain | Interpretation order |
| --- | --- |
| Current repository behavior | Current repository code, then Session history, then planning notes |
| AI Session activity | Original Claude or Codex JSONL, then normalized LocalBrain records, then generated summaries |
| User-confirmed current state | Confirmed checkpoint, then source-linked evidence, then generated Suggestion |
| External context | Live approved source, then policy-approved cache, then local reference metadata |

Original source identity and historical paths remain evidence even when the current repository location changes. A stale, inaccessible, or conflicting source must be labeled instead of being treated as current.

### Local First And Policy Aware

Local activity remains on the local machine. External systems are accessed only through approved capabilities and persistence rules. LocalBrain must not transmit local data to an unapproved external AI, embedding service, or connector.

The complete storage and disclosure contract is owned by [Privacy And Data Handling](privacy-and-data.md).

## Domain Boundaries

| Concept | Responsibility |
| --- | --- |
| `Workstream` | User-defined area joining related work across sources |
| `Thread` | Specific topic or effort inside one Workstream |
| `Source` | Configured origin such as Claude, Codex, a folder, or an external service |
| `Source Item` | Imported item retaining source identity and freshness |
| `Session` | One source-backed Claude or Codex primary or child session |
| `Activity Event` | Normalized prompt, tool call, error, file action, or other event |
| `Usage Record` | One source-backed Claude usage record or positive Codex direct event delta, with cumulative fallback when direct usage is absent, plus explicit component, model, normalizer version, capability, and immutable trend-cost provenance |
| `Resource` | Linkable session, document, path, project, ticket, message, or URL |
| `Suggestion` | Reversible proposed resource link or checkpoint draft |
| `Checkpoint` | Versioned, user-confirmed resume state with a resource snapshot |

The same Resource may relate to multiple Threads. Relationship-specific evidence belongs to the relationship rather than being copied into a new Resource.

### Session Hierarchy And Consumption

- Original Claude and Codex metadata owns whether a Session is primary or a subsession and which source parent it reports.
- LocalBrain retains both the source parent identity and the resolved internal parent relation. An unresolved child remains a subsession and never falls back to a primary Session.
- Current Session browsing exposes only direct children of a primary Session. Deeper hierarchy remains preserved but is not flattened into user-facing lists.
- Subsessions remain outside global Search, Session-derived statistics, Workstream organization candidates, and Workstream Claude maintenance evidence. Their stored source and events remain available through approved parent-owned browsing.
- Usage and cost totals intentionally use a different scope from workflow statistics: every direct real-model primary, maintenance, and subsession Usage Record is eligible once. Claude's source-generated `<synthetic>` assistant and API-error records remain stored as Session evidence but are not usage; they do not enter periods, totals, price coverage, breakdowns, or usage-linked Session counts. This does not make maintenance or subsession content eligible for Search, Workstream organization, or Session-count metrics.
- Estimated cost is one locally reproducible USD trend value tied to the Usage Record's original price snapshot. Unknown or incomplete pricing remains visibly unavailable and never becomes a synthetic zero, invoice, quota, budget, or actual-payment value.
- A price snapshot may define a model-specific input-context threshold. Each Usage Record selects its own tier from non-cached input plus cache read; the exact threshold remains base-priced and only a strictly greater context uses the long-context rates. A crossing never reprices an entire Session, day, or month.
- Claude cache creation prefers a positive internally consistent ephemeral breakdown over a contradictory zero aggregate. Codex usage prefers every positive direct `last_token_usage` event, uses Session-cumulative subtraction only when the direct event value is absent, excludes copied spawned or forked replay prefixes, and ignores repeated zero deltas.
- Session synchronization owns normalizer-version repair. A changed contract automatically reparses every current file for the affected source and transactionally replaces that source's derived Usage Record set with the complete file union while retaining historical price and Project snapshots. Users do not manage this with an aggregate-reset button.
- Each Usage Record freezes its Project attribution when first observed. Historical usage groups by that snapshot rather than current workspace or Git metadata; later Git discovery and path changes affect only newly observed records, and unassigned history is not reconciled silently.
- Primary and valid direct-child detail views are conversation-reading surfaces: they show source-ordered user and assistant messages through the shared safe Markdown presentation, omit visible tool-call rows, and preserve raw text, the complete source event count, and normalized tool events. Session text has no owning Local Context source, so source-relative references remain visibly unresolved rather than using a global guess.
- A primary detail keeps a Subsessions section for its direct children. Detail
  headings and direct-child rows use the stable `CL`, `CX`, or `CC` cue with the
  configured source label in accessible text instead of repeating that label
  visibly. Each direct-child row shows its source-native external ID and aligns
  question, event, and date metadata in the Sessions inventory reading order. A
  child detail keeps explicit orientation back to its eligible primary parent.
- A persisted primary Session detail projects a bounded `관련 자료` rail from existing local data. `이 세션의 참조` uses source-neutral Session reference evidence and Session-observed identity for explicit Markdown/URL mentions and approved MCP read outcomes; `연결된 작업` follows only Documents or Resources sharing an explicit user-managed Thread or Workstream. A target in both groups remains once under the direct group, and successful reads take precedence over failure-only attempts. Each group owns an independent total and shows at most 10 rows initially; retained overflow remains available through a reversible native disclosure. Direct evidence retains the 100-target safety boundary with observed-versus-retained partial copy, while explicit organization lookup is independently bounded. Same workspace, directory, repository, path, and global recency never generate a candidate or fallback. Missing local paths and unsafe external destinations remain visible but inactive; unresolved polymorphic targets are omitted with a bounded count. Loading the projection reads only bounded SQLite identity/evidence metadata, copies no content body, writes no relationship, and starts no source parse, model, embedding, remote, capability, scan, or maintenance work. A projection error never blocks the conversation. At widths through `920px`, the rail follows Session identity and orientation in document order and precedes the conversation; Subsession detail has no rail and its evidence is not rolled up.
- Git branch metadata belongs to the Session that observed it. A workspace retains its working path and containing Git repository root, not one historical branch value.

The syntax, safety, local-reference, highlighting, and consumer boundaries for these reading surfaces are owned by the [Markdown Rendering Contract](markdown-rendering.md).

## User Experience Contract

Bounded database-backed state families use the executable value registry as their presentation authority. One family is either shown directly, mapped completely to logical labels, or kept internal-only; ordinary screens never translate only selected values or fall back to an unknown raw token. A complete logical mapping may exist without a current visible consumer and does not require an ordinary screen to expose state that adds no task value. Filters, forms, detail facts, empty/error states, and client-updated status copy use the same mapping when that family is shown. Short labels describe state, and registered help copy explains consequential scope, coverage, remote-read, or recovery behavior. Physical storage values, request payloads, API identity, and transition logic remain separate implementation contracts.

### Navigation

The application uses a persistent left navigation boundary. Dashboard, Sessions Dashboard, Workstreams, Sessions, Atlassian, Local Contexts, and Sources have distinct responsibilities so source inspection does not overload the Session timeline. Sessions owns a local `Sessions | Projects` view switch: Sessions is the default individual history and Projects is its path-derived grouping, not a separate persistent destination or entity. Its peer source scopes derive from the ordered private registry: `전체` combines every retained meaningful primary work Session, and each stable source key—including Claude, personal Codex, and Codex Company—remains independently selectable. Meaningful requires at least one normalized Activity Event or direct Usage Record; a metadata-only native stub owns no normalized Session projection. The selected source constrains the headline count, rows, pagination, and Project grouping through the same denominator without an inventory age cutoff. Every Session and Subsession icon derives its compact `CL`, `CX`, or `CC` cue from stable source identity rather than provider kind. Ordinary cards, Pinned cards, detail headings, and detail Subsession rows omit the repeated visible source name and retain it for assistive technology. The shared inventory toolbar also owns a Session-only synchronization action for all registered local AI Session sources; its source-status summary shows only those Session sources and does not expose the database path. The Sources destination retains the wider scan that includes enabled Local Context sources.

The Sessions inventory uses its secondary recall region for owner-curated `Pinned Sessions`, never recent Documents, inferred importance, or generated Suggestions. The panel is global across active Session filters, exposes every current pin by displayed activity date (`last_event_at`, otherwise `started_at`) descending with `pinned_at DESC, session_id DESC` tie-breaks, and bounds only wide-layout height with an internal scroller. Persisted primary work Sessions can be pinned or unpinned from inventory and detail; Maintenance Sessions and Subsessions remain ineligible. Every inventory row reserves one utility layer: desktop and laptop place `질문 → 이벤트 → 날짜 → 핀` on the aligned upper edge, use stable left-aligned question and event columns across rows, and anchor optional Subsessions at the lower trailing edge; narrow layouts keep the pin upper trailing and the Subsession action lower trailing. Pin and Subsession controls remain outside the Session destination link. The fixed pin hit area has no visible outline border or independent background in idle, hover, or pinned state, so it follows the owning row or detail surface; pinning never changes that surface. An unpinned pin may use the ordinary hover emphasis, while an already pinned glyph retains its information color on hover. The filled glyph, accessible name, and `aria-pressed` expose state while keyboard focus retains its separate focus ring. Enhanced pin mutations update the control and Pinned Sessions panel in place, preserve document and panel scroll positions, keep the current inventory query state, and return focus to the changed control. Pinned entries show their compact accessible source cue and activity date without repeating the configured source name visibly. Pin mutations remain local POST actions; they never write source files or imply native Claude/Codex process resume.

Atlassian owns separate Jira and Confluence inventories. `Browser` is the default local-read mode and `Add` is its explicit neighbor. Add first summarizes only Site and Space/project records already persisted in LocalBrain, grouped by recognizable Site/domain; unregistered candidates and URL evidence that has not produced the owning record remain absent. URL registration and connected candidate search are two methods in one Add flow. A ticket, Page, project, or Space starts from a real URL; key-only text is not treated as evidence. Local-only Add asks for that URL alone, parses service, normalized-domain Site, kind, and available identifier locally, and derives a compact Item/Space title from the key, Page slug, or Page ID. It creates no Source Instance, Provider, configuration reference, capability, or remote read.

Optional remote access is a distinct adjacent task: the user chooses a registered Site, official Atlassian MCP or company MCP Gateway, and the actual validated Cloud ID or Gateway configuration alias. That action creates or reuses the Source Instance and binds it to the Site without changing Site identity or inspecting capability. Source Instance remains the internal access, capability, and policy boundary; generated connection display text is compatibility presentation, not a user-managed alias.

Connected search selects the target Site first, then an eligible bound access path, then the Claude or Codex runner. A Site reachable through multiple paths remains one target rather than connection-specific duplicate tabs. Jira projects default to selected content, while regular Confluence Spaces default to full Page content. Connected candidate discovery is a bounded maintenance action whose result may be partial and requires confirmation before registration.

The local inventory keeps Source, Site, Space, Item type, coverage, freshness, attention, Topic, Tag, Workstream, and text filters as bookmarkable GET state. Archived Items are excluded by default but remain recoverable through direct detail or an explicit archived/all filter. Identical ticket keys on different Site domains never collapse into one Item. Each detail separates remote facts/content, user-owned notes and Topic/Tag classification, Session/Local Context evidence, Workstream/Thread membership, and latest refresh Run evidence. Topics are reusable and may carry a local description; Tags are reusable lightweight labels. Both are independent from remote labels and Workstream membership.

Remote refresh is always explicit. Item, Space, Thread, Workstream, and all-known entry points first resolve a local preview that performs no external or model call. The preview identifies exact known targets, Source Instance, Site/Space, coverage, freshness, timestamps, and calculated provider reads; unknown, due, stale, and unavailable targets default selected, while current targets remain opt-in. One action may combine several Source Instances into one inspectable maintenance Run, but at most 20 pre-authorized reads are selected. “All known” means only Items already present in LocalBrain, never the accessible company estate. Jira Space refresh checks selected known Items only. A Confluence full-content Space may additionally request one explicit catalog page of at most 200 regular Pages; newly cataloged Pages are indexed-intent stale stubs whose bodies require later explicit batches.

### Dashboard

The primary Dashboard should summarize current work rather than duplicate session statistics. It prioritizes active or interrupted Workstreams and should surface:

- current goal and Thread state
- recent activity and source changes
- unresolved next action or blocker
- checkpoint freshness
- evidence requiring review or organization

Session activity and usage statistics belong to the separate Sessions Dashboard.

The Sessions Dashboard must keep three time concepts distinct: observed Session span, estimated active time, and any source-supplied running-turn duration. Estimated active time uses event segments whose consecutive gaps are at most 30 minutes, merges concurrent overlap once, and ends at the last observed event. Longest active segment is an estimate under that same rule and is not Codex's longest-running-turn metric.

Sessions Dashboard defaults to Daily with the latest 30 inclusive local-calendar days. Weekly shows the current and previous 11 Monday-based weeks, while Cumulative starts at the earliest eligible real-model usage date and presents monthly running totals. `All` and the ordered registered local AI Sources are peer scopes; personal Codex and Codex Company are independent even though both use the Codex adapter. Source, range, Tokens/Cost, composition, and paired custom dates are reproducible GET state, and changing Source preserves the other valid analytical controls. The four-metric overview reports estimated cost, total normalized tokens, usage-linked primary-work Sessions, and active days; only the Session denominator excludes maintenance and subsession records. MTD values and data freshness remain subordinate context rather than a second KPI wall.

`Usage Record` is the canonical term across the Sessions Dashboard, persistence, parser, query, and engineering documentation. It does not mean one Session, request, invoice line, or Activity Event.

One composition family explains the selected records by Source, normalized Model, or first-observation Project snapshot. Source composition groups by stable source identity with its configured readable label and provider cue, so `All` is traceable and its compatible total equals the exact source-row sum. Shares use only the compatible selected token or priced-cost denominator, while unsupported values remain unavailable. Raw model identity remains inspectable, Project attribution never changes through a current-path lookup, and `Unassigned` stays visible. A separate trust region owns the latest per-source synchronization result and success, retained stale/error data, token and price coverage, calculation state, and price-snapshot explanation; source failure never hides previously calculated Usage.

The Sessions Dashboard does not surface a projected month-end cost. Cost mode stays limited to observed selected-period and month-to-date estimates, coverage, and freshness so the summary does not add a speculative secondary figure.

### Workstream

A Workstream view provides connected Threads, resources, checkpoints, Suggestions, maintenance Runs, source freshness, and conflicts. It should make the current state understandable without requiring the user to reread every source.

### Timeline And Search

Timeline and search span sessions, questions, errors, files, commands, tickets, messages, decisions, and documents while preserving filters, source identity, and deep links. Atlassian matches group identity, eligible remote metadata/body, and local note/Topic/Tag roles back to one stable Item result with its Source domain, coverage, and freshness. Browsing and search are local reads and never trigger remote or model work.

### Insights

Insights may include context switching, tool usage, project and topic distribution, repeated errors or questions, session fragmentation, and idle Workstreams. Metrics should lead back to underlying timelines and actionable context rather than rewarding raw activity volume.

## Current Scope

Included in the local MVP:

- local Claude and Codex session ingestion
- folders, individual files, and Apple Notes as user-managed Local Context sources
- Workstream, Thread, checkpoint, and resource organization
- local search and deterministic resource retrieval
- reviewable Suggestions and maintenance Runs
- raw activity retention for future reproducible insights

Deferred until explicitly planned:

- broad external-source ingestion and write-back
- cloud sync and multi-user collaboration
- mobile support
- automatic semantic linking across every source
- mandatory external AI or embedding APIs
- native macOS packaging before workflow validation

## Success Criteria

- Relevant past context is faster to find than through manual directory and session browsing.
- A paused Workstream can be resumed with less rereading and repeated explanation.
- Incorrect Suggestions can be corrected without losing source data or user decisions.
- Statistics remain traceable to stored events and reveal actionable work patterns.
- The local web workflow proves useful before desktop packaging begins.

## Naming Status

`LocalBrain` is the working name. The name emphasizes private local memory for day-to-day development context; final product naming is not an implementation dependency.
