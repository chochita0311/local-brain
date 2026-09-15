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

### Session Identity And Hierarchy

- Original Claude and Codex metadata owns whether a Session is primary or a subsession and which source parent it reports.
- LocalBrain retains both the source parent identity and the resolved internal parent relation. An unresolved child remains a subsession and never falls back to a primary Session.
- A recognized Codex guardian Session is provider-internal approval activity rather than user work. LocalBrain retains its source identity, parent relation, and directly observed Usage Records as metadata-only maintenance activity, but does not expose its prompts, decisions, or counters as an ordinary Subsession.
- Current Session browsing exposes only direct children of a primary Session. Deeper hierarchy remains preserved but is not flattened into user-facing lists.
- Work Subsessions remain outside global Search, Session-derived statistics, Workstream organization candidates, and Workstream Claude maintenance evidence. Their stored source and events remain available through approved parent-owned browsing; provider-internal metadata-only children are excluded from that browsing surface.

### Usage And Cost Semantics

- Usage and cost totals intentionally use a different scope from workflow statistics: every direct real-model primary, maintenance, and subsession Usage Record is eligible once. Claude's source-generated `<synthetic>` assistant and API-error records remain stored as Session evidence but are not usage; they do not enter periods, totals, price coverage, breakdowns, or usage-linked Session counts. This does not make maintenance or subsession content eligible for Search, Workstream organization, or Session-count metrics.
- Estimated cost is one locally reproducible USD trend value tied to the Usage Record's original price snapshot. Unknown or incomplete pricing remains visibly unavailable and never becomes a synthetic zero, invoice, quota, budget, or actual-payment value.
- A price snapshot may define a model-specific input-context threshold. Each Usage Record selects its own tier from non-cached input plus cache read; the exact threshold remains base-priced and only a strictly greater context uses the long-context rates. A crossing never reprices an entire Session, day, or month.
- Claude cache creation prefers a positive internally consistent ephemeral breakdown over a contradictory zero aggregate. Codex usage prefers every positive direct `last_token_usage` event, uses Session-cumulative subtraction only when the direct event value is absent, excludes copied spawned or forked replay prefixes, and ignores repeated zero deltas.
- Session synchronization owns normalizer-version repair. A changed Usage
  contract automatically reparses every current file for the affected source and
  transactionally replaces only that source's derived Usage Record set with the
  complete file union while retaining historical price and Project snapshots.
  It does not replace unchanged Session, Activity Event, search, or reference
  evidence merely because Usage pricing or normalization changed. Users do not
  manage this with an aggregate-reset button.

### Session Detail And Related Evidence

- Primary and valid direct-child detail views are conversation-reading surfaces: they show source-ordered user and assistant messages through the shared safe Markdown presentation, omit visible tool-call rows, and preserve source JSONL and normalized tool events. Codex-expanded repository/environment instructions and `<skill>` bodies do not become visible user messages, titles, search text, or reference evidence; the original user-authored prompt, including its literal `$skill` invocation, remains visible. Session text has no owning Local Context source, so source-relative references remain visibly unresolved rather than using a global guess.
- A primary detail keeps a Subsessions section for its direct children. Detail
  headings and direct-child rows use the stable `CL`, `CX`, or `CC` cue with the
  configured source label in accessible text instead of repeating that label
  visibly. Each direct-child row shows its source-native external ID and aligns
  question, event, and date metadata in the Sessions inventory reading order. A
  child detail keeps explicit orientation back to its eligible primary parent.
- A persisted primary Session detail projects a bounded `관련 자료` rail from
  existing local data. `이 세션의 참조` uses source-neutral Session reference
  evidence and Session-observed identity for explicit Markdown/URL mentions and
  approved MCP read outcomes; `연결된 작업` follows only Documents or Resources
  sharing an explicit user-managed Thread or Workstream. A target in both
  groups remains once under the direct group, and successful reads take
  precedence over failure-only attempts.
- Each group owns an independent total and shows up to 100 retained rows
  initially. When the rail contains related state, the `연결된 작업` heading and
  its zero total remain visible even when no organization-only target remains,
  preserving that exploration path. Material kinds appear once as
  alphabetically ordered sections, while direct references within each kind
  follow their oldest source occurrence so the rail progresses with the
  conversation.
- URL token boundaries exclude prose after an unmatched closing delimiter
  without removing valid non-ASCII URL paths. Retained overflow remains
  available through a reversible native disclosure whose collapse control
  follows the expanded rows in DOM, visual, and keyboard-focus order. Direct
  evidence retains the 100-target safety boundary with observed-versus-retained
  partial copy, while explicit organization lookup is independently bounded.
- Same workspace, directory, repository, path, and global recency never
  generate a candidate or fallback. Missing local paths and unsafe external
  destinations remain visible but inactive; unresolved polymorphic targets are
  omitted with a bounded count. Loading the projection reads only bounded
  SQLite identity/evidence metadata, copies no content body, writes no
  relationship, and starts no source parse, model, embedding, remote,
  capability, scan, or maintenance work. A projection error never blocks the
  conversation.
- At widths through `920px`, the rail follows Session identity and orientation
  in document order and precedes the conversation. Subsession detail has no rail
  and its evidence is not rolled up.

### Workflow Episode And Direction

- A workflow Episode is a rebuildable descriptor of one eligible primary work
  Session, not a new persisted resource or a replacement for the Session. Its
  stable derived key hashes the length-delimited source key and source-native
  Session ID; the current local Session ID remains navigation only. Subsessions
  remain evidence owned by their primary Session rather than peer Episodes.
- Episode observation bounds use the earliest and latest valid source-backed
  timestamps. Activity (`active`, `quiet`, `unknown`), lifecycle (`open`,
  `closed`, `unknown`), closure reason, and authority are separate axes. A
  Session ending is an observation and never proves that its work closed.
- Direction is intentionally limited to `continues`, `branches-from`, and
  `merged-into`. A retained relation must move strictly forward in observation
  time, avoid self-edges and directed cycles, and cite at least one strong
  reason: a direct source relation, a shared reference, explicit Thread or
  Workstream membership, or a user assertion. Workspace, Git, lexical, temporal,
  and similar proximity can support a relation but cannot establish one alone.
- Candidate, explicit-organization, and user-confirmed authority remain visibly
  distinct. Invalid or insufficient relations are omitted with bounded
  diagnostics; LocalBrain does not silently upgrade a candidate into user
  organization or invent intent, outcome, next action, or closure.
- The versioned Episode and direction contract is a pure in-memory projection.
  It reads no database or source, performs no remote or model work, persists
  nothing, and changes no existing Session, Workstream, or navigation behavior.
- The database-backed source and candidate Focus projection is derived on
  demand and read-only. It always returns an eligible selected Episode, then admits at most
  200 relation candidates through exact shared user Thread membership, or a
  documented combination of shared direct reference, user Workstream,
  workspace, and observed Git facts. One broad Workstream, workspace, Git root,
  branch, title, wording, or nearby time never creates a line alone.
- `continues` joins adjacent time-ordered Episodes inside one qualifying exact
  set. `branches-from` requires the same non-empty observed Git root, different
  non-empty observed branches, and a shared direct reference or user
  organization owner; it remains a deterministic candidate, not a claim about
  Git ancestry. A later return to `main`, `master`, or another branch name does
  not infer `merged-into`.
- A Focus result contains at most 24 Episodes, four outward side-branch roots,
  four Episodes reached within one side branch, and five expanded evidence
  items per source family. Candidate, Episode, branch, and evidence totals keep
  truncation visible. Jira, Wiki, Local Context, local/external Resources,
  Workstream/Thread memberships, and direct Subsessions attach as evidence;
  they do not become peer workflow nodes.
- Opening or recomputing Focus consumes only current normalized SQLite state.
  Stale or unavailable evidence stays labeled, and the read starts no Session
  synchronization, source scan, body parse, external discovery, Atlassian Sync
  or Refresh, model, embedding, or database write.
- An eligible primary Session detail exposes one additive `작업 흐름` link to
  `/sessions/{id}/workflow`. The separate Focus surface keeps Episodes on a
  stable time-directed spine, places bounded side branches on deterministic
  lanes, and keeps Jira, Wiki, Local Context, Resource, organization, and
  Subsession records inside the selected Episode's evidence constellation and
  Trace rather than turning them into peer nodes. Selecting an Episode updates
  its canonical Workflow URL and reveals its supported ancestry, descendants,
  adjacent directions, complete reason list, and safe source destinations.
- Focus rendering is progressive enhancement over a server-rendered lineage.
  Wide layouts use a left-to-right time axis, compact layouts use the same
  relations top-to-bottom, and narrow, no-script, or render-failure states keep
  the text lineage and Trace usable. An unconnected Session remains a valid
  one-Episode result and never implies completion. Missing, ineligible,
  partial, stale, unavailable, and unexpected-error states preserve an honest
  local return path.
- Focus browsing remains read-only. A contextual correction form can append a
  user-confirmed relation or lifecycle assertion only after showing the exact
  consequence; it does not create or rename Workstreams, rewrite a candidate or
  its reasons, refresh a source, generate a summary, or use Qwen, embeddings, or
  another model. Existing Session conversation, pin, metadata, Subsession, and
  Related Materials behavior stays authoritative and unchanged.

### Workflow Assertion And Correction

- Consequential workflow correction belongs to one dedicated local assertion
  ledger, not to Sessions, candidate relations, Workstream/Thread membership,
  or Suggestions. It targets stable Episode keys and retains nullable current
  Session IDs only as lookup aids.
- The exact initial actions are `same-flow`, `split-here`, `merge-into`,
  `close`, and `reopen`. Close always requires one explicit reason:
  `completed`, `abandoned`, `superseded`, `merged`, or `other`; inactivity,
  Session end, and age never imply closure.
- User-confirmed assertions overlay the derived Focus projection after source
  and deterministic candidate assembly. They control the effective selected
  boundary while the complete base relation, evidence reasons, and base
  lifecycle stay available for Trace.
- Action, correction, reopen, and undo are append-only superseding records.
  Undo applies only to the current record in one boundary chain and restores
  the prior effective meaning without deleting history. Missing source Episodes
  retain unresolved assertions for later deterministic re-resolution.
- Mutation is explicit, local, revision-checked, and atomic. It never writes a
  source file or external system, starts Refresh or synchronization, changes
  Workstream organization, or calls Qwen, an embedding service, or another
  model.
- The selected Episode or relation Trace offers only currently valid actions.
  Each ordinary form exposes the exact before/after meaning, affected Episodes,
  user-confirmed authority, and supersession consequence before submission;
  choosing or cancelling a disclosure performs no write.
- Success reprojects the same bounded Focus and highlights the corrected
  boundary while restoring the selected Episode, branch disclosures, evidence
  disclosures, scale, pan, Trace and page scroll, and meaningful keyboard
  focus. A stale revision or validation failure keeps the prior map in place,
  restores the owning controls, and offers an explicit reload path. Narrow and
  no-script presentations retain the same sequential form and fixed result
  language.

### Git And Project Attribution

- Each Usage Record freezes its Project attribution when first observed. Historical usage groups by that snapshot rather than current workspace or Git metadata; later Git discovery and path changes affect only newly observed records, and unassigned history is not reconciled silently.
- Git branch metadata belongs to the Session that observed it. A workspace retains its working path and containing Git repository root, not one historical branch value.

The syntax, safety, local-reference, highlighting, and consumer boundaries for these reading surfaces are owned by the [Markdown Rendering Contract](markdown-rendering.md).

## User Experience Contract

Bounded database-backed state families use the executable value registry as their presentation authority. One family is either shown directly, mapped completely to logical labels, or kept internal-only; ordinary screens never translate only selected values or fall back to an unknown raw token. A complete logical mapping may exist without a current visible consumer and does not require an ordinary screen to expose state that adds no task value. Filters, forms, detail facts, empty/error states, and client-updated status copy use the same mapping when that family is shown. Short labels describe state, and registered help copy explains consequential scope, coverage, remote-read, or recovery behavior. Physical storage values, request payloads, API identity, and transition logic remain separate implementation contracts.

### Application Navigation And Session Inventory

The application uses a persistent left navigation boundary. Dashboard, Sessions Dashboard, Workstreams, Sessions, Atlassian, Local Contexts, and Sources have distinct responsibilities so source inspection does not overload the Session timeline. Sessions owns a local `Sessions | Projects` view switch: Sessions is the default individual history and Projects is its path-derived grouping, not a separate persistent destination or entity. Its peer source scopes derive from the ordered private registry: `전체` combines every retained meaningful primary work Session, and each stable source key—including Claude, personal Codex, and Codex Company—remains independently selectable. Meaningful requires at least one normalized Activity Event or direct Usage Record; a metadata-only native stub owns no normalized Session projection. The selected source constrains the headline count, rows, pagination, and Project grouping through the same denominator without an inventory age cutoff. Every Session and Subsession icon derives its compact `CL`, `CX`, or `CC` cue from stable source identity rather than provider kind. Ordinary cards, Pinned cards, detail headings, and detail Subsession rows omit the repeated visible source name and retain it for assistive technology. The shared inventory toolbar also owns a Session-only synchronization action for all registered local AI Session sources; its existing result region reports the current source, contract-upgrade reason, and bounded file progress before rendering the unchanged complete/partial/failed summary. The button keeps its busy, reload, retry, keyboard-focus, and no-script fallback behavior. Progress never exposes a local source path or content. Its source-status summary shows only those Session sources and does not expose the database path. The Sources destination retains the wider scan that includes enabled Local Context sources.

The Sessions inventory uses its secondary recall region for owner-curated `Pinned Sessions`, never recent Documents, inferred importance, or generated Suggestions. The panel is global across active Session filters and exposes every current pin without a product cap. It groups current workspace identities with Git-backed Projects first and non-Git working paths second, orders each section alphabetically by workspace display name, and orders Sessions inside one Project by displayed activity date (`last_event_at`, otherwise `started_at`) descending with `pinned_at DESC, session_id DESC` tie-breaks. The Project/path appears once as the group heading; each Session row shows its compact accessible source cue, title, optional Session-owned Git branch, and activity date without repeating the Project or configured source name. Only wide-layout height is bounded with an internal scroller. Persisted primary work Sessions can be pinned or unpinned from inventory and detail; Maintenance Sessions and Subsessions remain ineligible. Every inventory row reserves one utility layer: desktop and laptop place `질문 → 이벤트 → 날짜 → 핀` on the aligned upper edge, use stable left-aligned question and event columns across rows, and anchor optional Subsessions at the lower trailing edge; narrow layouts keep the pin upper trailing and the Subsession action lower trailing. Pin and Subsession controls remain outside the Session destination link. The fixed pin hit area has no visible outline border or independent background in idle, hover, or pinned state, so it follows the owning row or detail surface; pinning never changes that surface. An unpinned pin may use the ordinary hover emphasis, while an already pinned glyph retains its information color on hover. The filled glyph, accessible name, and `aria-pressed` expose state while keyboard focus retains its separate focus ring. Enhanced pin mutations update the control and Pinned Sessions panel in place, preserve document and panel scroll positions, keep the current inventory query state, and return focus to the changed control. Pin mutations remain local POST actions; they never write source files or imply native Claude/Codex process resume.

### Atlassian Explorer, Add, Connections, Sync, And Refresh

#### Scope, Terminology, And Retrieval

Atlassian is one local Explorer over persisted Jira links, Confluence
documents, and non-archived URL-derived structure references. The physical
data model retains `Item` as its internal stable identity term for links and
documents, but ordinary product copy uses `링크` in Jira-only context,
`문서` in Wiki-only context, and `링크/문서` in mixed context; structure
references retain their separate family and provenance labels. The
Explorer opens in `All`, with reversible `Jira` and user-facing `Wiki` scopes;
`Wiki` maps to stored `confluence` identity and does not rename persistence
vocabulary. One surface-local query owns Atlassian retrieval while the route is
active, and the shared-header global query is not simultaneously visible.
Local Browse and query work never call a model, provider, capability, or
maintenance runner.

The Explorer's exact query trims surrounding whitespace and treats an empty
value as unfiltered local Browse. A complete case-normalized Jira key or stored
remote/Page ID, or an exactly normalized canonical/alias URL, is an identity
match. Other text uses NFKC-plus-casefolded Unicode word tokens and matches only
when the complete token phrase is contiguous inside one owned value: a local
or approved remote title, one approved remote-metadata scalar, indexed
normalized content, the local note, one Topic name/description, or one Tag
name. Separate values never combine. Identity results precede title results,
which precede other owned-value results; ties use ascending stable local Item
ID. Evidence/source text, opaque payloads, Workstream names, Site/Space labels,
and unavailable remote bodies are not query owners. The shared cross-source
Search retains separately owned local FTS behavior. The passed
structure-reference contract adds one independently typed result from reference
identity, generated family label, and privacy-safe locator only. It does not
index source text, hint, remote content, Item local memory, or organization
state, and the surface is not relabeled as Atlassian exact retrieval.

#### Site-First Hierarchy And Counts

Every service scope projects the hierarchy under the `모든 도메인` root by
normalized Site domain first; Service is never a hierarchy parent. `All` keeps Jira and Wiki records under
the same canonical Site, while the top `Jira` and `Wiki` scopes reversibly
filter that population. Each Site has only three kinds of child structure:

- a persisted Jira project or Confluence Space, whose `space_id`, stored
  service, key, and display name remain authoritative;
- for a record with null `space_id`, a read-only container hint derived from
  exactly one canonical URL when a strict Jira Issue URL exposes its project
  key or a strict Confluence Page URL exposes its Space path segment; or
- one Site-local `소속 미확인` child when neither persisted containment nor
  an eligible canonical-URL hint exists.

Alias URLs, evidence URLs, titles, body text, nearby prose, and source paths do
not own hierarchy grouping. A URL hint never creates a Space, writes
`space_id`, merges into a same-labeled persisted Space, or represents remote
confirmation. Persisted containment always wins. Equal child labels remain
separate when service or persisted-versus-derived provenance differs and use a
compact non-color-only cue. The hierarchy does not claim a nested Confluence
Page or Jira issue tree. Its adjacent inventory keeps stable internal Item
identity, Site or Space context, and independent coverage, freshness,
attention, classification, organization, and provenance cues without
compressing those axes into one status. Identical keys on different Site
domains remain distinct. Archived records stay outside the default population
but remain recoverable through explicit state or direct detail.

Hierarchy counts and the adjacent list share one eligible population after
service, exact query, archived-default, and advanced filters. The current Site,
persisted child, URL child, or `소속 미확인` constraint applies only after
that population is formed, so the active node count equals list membership and
sibling counts stay navigable. In `All`, selecting only a Site intersects both
services; a persisted child carries its stored service, a URL child carries its
descriptor service, and `소속 미확인` intersects both services for that Site.
Jira/Wiki scopes apply their service before the same structure. Root and sibling
projections remain backed by eligible records. A narrow action-integration
exception keeps a valid explicitly selected persisted Project/Space or known
canonical-URL child, or a previously valid Site-local `소속 미확인`
selection reachable at count zero after filters: only that active node and its
Site ancestor are projected, the adjacent list remains empty, and no remote
discovery or new record is implied. The one advanced disclosure
contains only coverage, freshness, attention, Topic, Tag, and Workstream.
Source Instance remains a Connections or diagnostic concern, and internal Item
type derives from service.

#### URL State, Selection, And Detail

The Explorer has one URL-backed state contract:

| Transition | Preserve | Reset or normalize |
| --- | --- | --- |
| open Atlassian without explicit state | shell and navigation continuity | `All`, hierarchy root, empty query, no advanced filters, no link/document or structure-reference selection |
| change `All / Jira / Wiki` scope | query and compatible advanced filters | structural scope, selected entry, result-local scroll, and unsupported hierarchy disclosure |
| change Site/child/`소속 미확인` scope | current top service scope, query, advanced filters, and reachable hierarchy orientation; `All` remains `All` while child service stays in persisted or descriptor identity | selected entry and result-local scroll |
| change query or advanced filters | service and structural scope plus entered URL-backed values | selected entry and result-local scroll |
| select a link/document or structure reference | service, structure, query, filters, hierarchy disclosure, and practical list position | only the mutually exclusive detail identity and its pane state advance |
| refresh or direct entry | every valid explicit URL-backed value | omitted values use defaults; forged, stale, repeated, mismatched, or otherwise invalid structure fails with a bounded visible validation state rather than hidden normalization |
| browser back or forward | the historical service, structure, query, filters, selection, and supported pane orientation | focus and each scroll owner restore to the nearest reachable historical anchor |
| cross a responsive breakpoint | eligible service, structure, query, filters, selection, and practical list position | unsupported persistent panes become explicit disclosures, sheets, or sequential destinations |

Wide Explorer state keeps hierarchy, list, and read-first detail adjacent with
intentional independent scroll ownership. Compact state keeps the list primary
and moves hierarchy and detail into bounded disclosures. Narrow state is
list-first and exposes hierarchy, filters, and detail as explicit sheets or
sequential destinations. Full-detail link/document routes remain the
direct-entry, local-edit, and no-script fallback; the separate read-only
structure-reference detail route provides the equivalent direct-entry and
no-script recovery without acquiring Item edit authority. Remote facts/content,
user-owned notes and
Topic/Tag classification, Session/Local Context evidence, Workstream/Thread
membership, and maintenance history remain separate authority regions.

One optional positive local internal Item ID or one optional positive local
structure-reference ID owns the selected Explorer state; the two identities
are mutually exclusive. Direct and enhanced selection use the same
server-authored, read-only preview contract for the selected entity, and the
enhanced response replaces only that preview without rebuilding hierarchy or
inventory. Unknown identities produce a bounded missing state. Known records
outside the active scope retain concise identity and explain that scope instead
of exposing unrelated detail; archived references remain a separately named
bounded direct-history state. Invalid structural combinations remain visible
local validation errors. Selection never starts a provider, model, capability,
source scan, Refresh, or maintenance action, and Setup never accepts selection
state. Both full-detail families remain executable without JavaScript; only
the link/document family owns local editing.

#### Static Locator Admission

Static URL recognition and product admission are separate authorities. One
shared, pure Atlassian locator contract classifies bounded standard Jira and
Confluence URL families as `item`, `structure`, `site`, `unsupported`, or
`unsafe`. Recognized results carry service, family, normalized domain/base, and
a privacy-minimized safe locator. An Item carries exact Issue/Page identity; a
structure result carries a stable reference kind/identity and optional
non-authoritative Project/Space hint; a Site result carries no selectable
identity. Path or approved-query Item identity wins over structure/site, and an
exact structure identity wins over the family root. The safe locator removes
fragment, JQL, and arbitrary query while retaining only canonical allowlisted
identity projection: for example RapidBoard retains positive `rapidView` and
may retain one normalized `projectKey` only as a grouping hint. Each action must
explicitly admit its subset. The passed foundation changed no structure/Site
persistence, Atlassian screen, or Sync report beyond already passed explicit
Add authority; normal Session reference repair may deduplicate an existing
generic URL by semantic target and navigate it through the canonical safe
locator. Passed SPEC-0083 owns the current successor product boundary: persist
structure identity, safe locator aliases, and source evidence under separate
owners from Item and Space; report Site-family roots without a selectable
zero-count row; and expose non-archived reference rows through Site-first
Explorer and the narrow shared-Search projection. Zero retained evidence keeps
stable identity direct-only as archived; retained but currently unusable
evidence is shown as unavailable rather than deleted or treated as fresh.

#### Action Consequences

Atlassian actions have distinct consequences:

- `Sync` deterministically reconciles recognized Atlassian URL evidence from
  the retained safe-URL projection of eligible primary work Sessions and the
  persisted bodies of enabled, readable, ready Local Context Documents. Session
  evidence is merge-only because the authoritative Session scanner remains its
  cleanup owner; a completely read Document owns bounded replace-derived
  evidence. A strict Jira Issue or Confluence Page URL may create or reuse one
  normalized-domain Site and one Site-scoped normalized-URL record even when no
  Site, binding, or inventory existed at action start. The same normalized
  domain is one Site across Jira and Wiki; service qualifies URL admission, not
  Site identity. Each source is atomic: a new Site is source-local until that
  source transaction commits, then becomes available to later sources; rollback
  discards both the rows and its resolver overlay. Explicit Sync Document
  currentness is owned by content/source fingerprint, successful status, and
  the current extractor/resolver version, not by registered Site/service
  fingerprint. Sync imports no authoritative source content and performs no
  external or model work. Under passed SPEC-0083 it reconciles eligible
  structure descriptors into separately owned references, safe URLs, and
  evidence while a `site` result remains report-only. Reports keep bounded
  source, link/document, structure-reference, evidence, Site-only, and
  candidate-skip outcomes distinct. Unchanged repeat Sync is read-only reuse,
  and retry repeats the whole local scope.
- `Add` registers or reuses one real Jira link, Confluence document, Jira
  project, or Confluence Space URL locally. Key-only text is not evidence.
  Service, Site, kind, and available identity are inferred locally; Provider,
  Source Instance, capability,
  runner, and remote readiness are not prerequisites.
- `Connections` owns optional Site access bindings, Provider/configuration
  references, readiness, and connected discovery. Connected discovery selects
  Site, eligible bound access path, and Claude or Codex runner, may return
  partial candidates, and registers nothing without explicit confirmation.
- `Refresh` is the existing explicit remote maintenance path. Link/document,
  Space, Thread, Workstream, and all-known entry points first resolve a local
  preview
  with no external or model call. The preview shows exact known targets,
  Source Instance, Site/Space, coverage, freshness, timestamps, and calculated
  reads; unknown, due, stale, and unavailable targets default selected while
  current targets remain opt-in. A Run selects at most 20 pre-authorized reads.
  “All known” means only records already in LocalBrain. Jira Space refresh
  checks selected known links only. A Confluence full-content Space may additionally
  request one explicit catalog page of at most 200 regular Pages; cataloged
  Pages are indexed-intent stale stubs whose bodies require later explicit
  batches.

#### Access And Entity Boundaries

Optional access failure never blocks Explorer Browse, local query,
link/document detail, local classification, Add, or Sync. Source Instance remains the internal
access, capability, and policy boundary; Site remains domain identity, and a
Site reachable through several access paths remains one target rather than
connection-specific duplicate inventory.

A structure reference is a distinct read-only Explorer/Search entity, not an
Item or persisted Space. Its optional container hint owns presentation grouping
only. It has no local note, attention, Topic/Tag, Workstream/Thread,
Connections, Refresh, remote-fact, or content authority. A Site-only recognition
is report-only. Item and structure-reference selection are mutually exclusive;
known filtered references produce an out-of-scope state without widening the
current population, while unknown and archived identities remain separately
named bounded states.

The `링크` / `문서` / `링크/문서` mapping applies to Explorer rows and
counts, Add, preview, full detail, Sync reports and announcements, Connections,
Refresh, and shared global Search. Physical schema, internal APIs and routes,
data attributes/selectors, diagnostics, value-registry keys, and historical
artifacts retain `Item` where it is the stable engineering identity.

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

Timeline and search span sessions, questions, errors, files, commands, tickets,
messages, decisions, and documents while preserving filters, source identity,
and deep links. Atlassian Item matches group identity, eligible remote
metadata/body, and local note/Topic/Tag roles back to one stable Item result
with its Source domain, coverage, and freshness. A non-archived Atlassian
structure reference remains a separately typed result projected only from its
reference identity, generated family label, and privacy-safe locator. Browsing
and search are local reads and never trigger remote or model work.

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
