# Product Model

## Purpose

LocalBrain is a local-first developer work context hub. It connects development activity scattered across local projects, Claude and Codex sessions, Git, tickets, conversations, and documents into resumable Workstreams.

The distributable macOS product targets general Mac users as an independent public
app. Company accounts, networks, certificates and the developer's personal paths
are not prerequisites. Its public release must work under normal macOS security
settings without asking users to install certificates or make security exceptions;
standard first-open and requested data-access confirmations remain. Settings and
private runtime data stay local. The current macOS test artifact is ad-hoc signed
and not notarized; its first-launch procedure does not establish public-release
readiness. The [test distribution guide](standalone-test-app-guide.md) owns that
artifact's launch requirements and recipient-verification limits.

The current learning-home direction prioritizes understanding gained from the
user's own work. The product goals are:

1. **Learning:** connect work observations to reliable explanations, independent
   recall and later application, gradually reducing gaps in technical understanding.
2. **Continuity:** answer where work stopped, what is currently known, and what should happen next.
3. **Insights:** show which tools, projects, technologies, and work patterns occupy the user's attention.

Preserved work evidence supports learning and a reliable restart point. Personal
answers, reviewed source evidence and confirmed work organization retain their
separate meanings and ownership.

## Product Principles

### Learning Home

Dashboard shows the daily code/command scene in **오늘의 배움** as a work-based
technical article. Preserved code, connected explanatory sections, application
criteria and official references precede an optional question. Opening the article creates no learning record; an explicit
reading action stores `read`, and note-origin answers are assisted practice.
The library owns selection guidance and the reader exposes complete source evidence. It proposes at most one
reviewed scene total per local day, prioritizing earlier pending work, due reviews,
then new material under the [scene policy](code-command-learning.md). The library and reader connect personal
work evidence to official material, answer/confidence, explanation-first reading
and self-assessment. Code remains beside the question and feedback on desktop and
precedes them on compact screens. Concept depth and optional practice use explicit
self-reports; authoring is currently manual. Workstreams retain their dedicated organization routes.
The [learning policy](work-grounded-learning.md) owns source snapshots, immutable
revisions, review intervals, visibility and the no-generator pilot boundary.
Reading, AI-authored changes and self-assessment do not establish correctness or
mastery; delayed independent explanation and transfer remain benefit evidence.

### Workstream-Centered Organization

The primary organization unit is a **Workstream**, not a session, directory, repository, ticket, or daily note. A Workstream represents one user-defined area of work and may span any number of local and external sources.

A **Thread** is a smaller topic within a Workstream, such as one feature, integration, investigation, or retirement effort. Concrete resources normally attach to a Thread because their relevance is usually specific. Workstream-level resources are reserved for evidence shared by multiple Threads.

Workstreams are created and named by the user. LocalBrain may suggest relationships, but a directory or model inference must not silently define a Workstream.

### Automatic Capture, Explicit Organization

Raw activity should require little manual effort. Workstream assignments, resource links, and checkpoint drafts may be suggested automatically, but they remain pending until accepted. Rejected Suggestions remain reviewable and can be restored.

### Transient Context Questions

[Context Search](context-search.md) answers explicit questions over enabled Local Contexts and already received Drive copies using local4B/8B models and read-only tools. It is separate from Session/semantic search and needs no embedding preparation. Evidence stays inspectable; folder publishers do not automatically become document authors or contacts. Same-screen follow-ups are transient and clear on leaving, with no saved answer schema or automatic organizational change. Public model originals and app-private execution state have separate owners.

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
| `Usage Record` | One source-backed usage observation: a Claude record, positive Codex direct event delta with cumulative fallback when direct usage is absent, or retained ephemeral analysis CLI summary; includes explicit component semantics, model, normalizer version, capability, and immutable trend-cost provenance |
| `Resource` | Linkable session, document, path, project, ticket, message, or URL |
| `Suggestion` | Reversible proposed resource link or checkpoint draft |
| `Checkpoint` | Versioned, user-confirmed resume state with a resource snapshot |

The same Resource may relate to multiple Threads. Relationship-specific evidence belongs to the relationship rather than being copied into a new Resource.

### Feature Contracts

| Feature | Current owner |
| --- | --- |
| Native collection, eligibility, revisions and reference evidence | [Session Ingestion](session-ingestion.md) |
| Identity, inventory, pins, Chart, conversation and direct references | [Sessions](sessions.md) |
| Token/cost meaning, frozen Project attribution and Sessions Dashboard | [Usage And Cost](usage-and-cost.md) |
| Episode direction, Focus, assertions and correction | [Session Workflow](workflow.md) |
| Pure provisional artifact-pair descriptor | [Workstream Candidates](workstream-candidates.md) |
| Explicit model-free reconstruction comparison | [Work Reconstruction Experiment](work-reconstruction.md) |
| Quoted model protocols and synthetic diagnostics | [Work Context Inference](work-context-inference.md) |
| Explicit simulation and passive affinity/sample inspection | [Auto Work](auto-work.md) |
| Local Explorer, Add, optional access, Sync and Refresh | [Atlassian](atlassian.md) |
| Skill reach, improvement evidence, guide compatibility and analysis Runs | [Personal Insights](personal-insights.md) |
| Registered document collection and reading | [Local Context](local-context.md) |

These owners define current behavior and restrictions. Planning and execution
records own approval, delivery and evaluation chronology; they do not replace
these definitions.

## User Experience Contract

Bounded database-backed state families use the executable value registry as their presentation authority. One family is either shown directly, mapped completely to logical labels, or kept internal-only; ordinary screens never translate only selected values or fall back to an unknown raw token. A complete logical mapping may exist without a current visible consumer and does not require an ordinary screen to expose state that adds no task value. Filters, forms, detail facts, empty/error states, and client-updated status copy use the same mapping when that family is shown. Short labels describe state, and registered help copy explains consequential scope, coverage, remote-read, or recovery behavior. Physical storage values, request payloads, API identity, and transition logic remain separate implementation contracts.

### Application Navigation

The standalone test edition exposes Sessions, Sessions Dashboard, Local Context,
search, Context Search, first-run setup, categorized settings and bundled Docs. Its menu, HTTP and runtime
boundaries exclude Dashboard/learning, Workstreams, Auto Work, Atlassian, Insights,
Session workflow and Schema. The broader navigation below describes development
web. Both editions use the [common local settings contract](desktop-app-and-settings.md),
model-free keyword search with explicit AI mode, and completion-based 10-minute
Session synchronization. The gear and ⌘, open the shared settings dialog.

Session inventory, pins, Chart and detail follow [Sessions](sessions.md).

### Dashboard

The primary Dashboard shows one **오늘의 배움** article. Its title, introduction,
preserved code, numbered explanatory sections and takeaway form a continuous
reading surface. A contents/References rail sits alongside on desktop; compact
screens place references below the article. A labeled, numbered code excerpt uses
the native dark reading surface, mono type and safe local syntax highlighting.
Section references connect explanations to their sources. A collapsed optional
question follows the takeaway. Reading width is bounded; the original page
heading remains. The library opens `/learning/{id}/note` for reviewed articles,
and the source/question reader links back to the same article. Lessons without
an article retain their complete explanation and existing library/reader entry.
Selection-reason, recent-work and evidence widgets are absent from Dashboard.
Source titles, checked dates, declared versions, review responsibility and
applicability accompany the article; complete evidence remains in the library/reader.
With no selected lesson the empty state links to the library.
The finite daily selection follows [Learning Home](#learning-home). Additional
widgets require a separate product decision. Widget movement, resizing and
user-saved layouts are not available. Workstream goals, Thread state,
blockers and checkpoints remain available on their existing dedicated surfaces.

Session activity and usage statistics belong to the separate Sessions Dashboard.

The [Usage And Cost contract](usage-and-cost.md#sessions-dashboard) owns Sessions Dashboard periods, totals, composition and estimate semantics.

### Workstream

A Workstream view provides connected Threads, resources, checkpoints, Suggestions, maintenance Runs, source freshness, and conflicts. It should make the current state understandable without requiring the user to reread every source.

### Timeline And Search

Timeline and search span sessions, questions, errors, files, commands, tickets,
messages, decisions, and documents while preserving filters, source identity,
and deep links. Atlassian Item matches group identity, eligible remote
metadata/body, and local note/Topic/Tag roles back to one stable Item result
with its Source domain, coverage, and freshness. A non-archived Atlassian
structure reference remains a separately typed result projected only from its
reference identity, generated family label, and privacy-safe locator. Atlassian
browsing and exact retrieval are local reads that invoke no remote service or
model. Shared-header keyword and AI search follow the
[search contract](natural-language-search.md): keyword queries need no model;
explicit AI search encodes queries locally with the prepared embedding model.
These searches send neither user queries nor source text to a remote service.

## Current Scope

The development-web core includes:

- local Claude and Codex Session ingestion and reading;
- folders, individual files and Apple Notes as user-managed Local Context sources;
- Workstream, Thread, checkpoint and resource organization;
- local search and deterministic resource retrieval;
- reviewable Suggestions and maintenance Runs; and
- source-backed activity retention for future reproducible insights, under the
  ingestion and privacy contracts.

Sessions Dashboard, reviewed learning, Atlassian local memory, experimental Auto
Work, Session Workflow and Insights follow their linked current feature contracts.
A route's presence does not establish model quality, learning benefit or release
acceptance. Original source material and normalized activity retain their separate
owners; “activity retention” does not admit opaque tool payloads into the index.

The standalone test app exposes Sessions, Sessions Dashboard, Local Contexts,
search, Context Search, settings, onboarding and bundled Docs. Its runtime boundary
excludes the other development surfaces; user settings cannot enable them.
The [desktop contract](desktop-app-and-settings.md#runtime-and-product-boundary)
owns the exact admission and lifecycle rules. An ad-hoc test artifact is separate
from the normal-security signed/notarized public-release goal.

Broad external ingestion/write-back, cloud sync beyond the approved selected
Drive contract, multi-user collaboration, mobile support, automatic semantic
linking across every source, and mandatory external AI/embedding APIs require
separate explicit planning. Existing approved CLI-backed analysis and read
integrations retain their narrower contracts.

### Selected Google Drive Transfer

[Google Drive synchronization](google-drive-sync.md) is managed in a separate Settings tab. User-selected local filesystem contexts publish into the configured root, and selected publisher folders receive into private external-source storage. The source is authoritative in each direction; stop preserves copies, while confirmed active-source deletion follows Drive Trash/outgoing and direct local removal/incoming rules. This transfer adds no model, search membership, organization-sharing controls or shared database replication.

## Success Criteria

- Relevant past context is faster to find than through manual directory and session browsing.
- A paused Workstream can be resumed with less rereading and repeated explanation.
- Incorrect Suggestions can be corrected without losing source data or user decisions.
- Statistics remain traceable to stored events and reveal actionable work patterns.

## Naming Status

`LocalBrain` is the working name. The name emphasizes private local memory for day-to-day development context; final product naming is not an implementation dependency.
