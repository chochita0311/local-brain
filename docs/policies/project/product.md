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
| `Session` | One Claude or Codex work session |
| `Activity Event` | Normalized prompt, tool call, error, file action, or other event |
| `Resource` | Linkable session, document, path, project, ticket, message, or URL |
| `Suggestion` | Reversible proposed resource link or checkpoint draft |
| `Checkpoint` | Versioned, user-confirmed resume state with a resource snapshot |

The same Resource may relate to multiple Threads. Relationship-specific evidence belongs to the relationship rather than being copied into a new Resource.

## User Experience Contract

### Navigation

The application uses a persistent left navigation boundary. Dashboard, Sessions Dashboard, Workstreams, Sessions, Atlassian, Local Contexts, Projects, and Sources have distinct responsibilities so source inspection does not overload the Session timeline.

### Dashboard

The primary Dashboard should summarize current work rather than duplicate session statistics. It prioritizes active or interrupted Workstreams and should surface:

- current goal and Thread state
- recent activity and source changes
- unresolved next action or blocker
- checkpoint freshness
- evidence requiring review or organization

Session activity and usage statistics belong to the separate Sessions Dashboard.

### Workstream

A Workstream view provides connected Threads, resources, checkpoints, Suggestions, maintenance Runs, source freshness, and conflicts. It should make the current state understandable without requiring the user to reread every source.

### Timeline And Search

Timeline and search span sessions, questions, errors, files, commands, tickets, messages, decisions, and documents while preserving filters, source identity, and deep links.

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
