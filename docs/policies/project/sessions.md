# Sessions

This contract owns Session identity, inventory, pins, Chart data and conversation/reference reading. [Session Ingestion](session-ingestion.md) owns collection, and [Sessions Chart Design](../design/surfaces/sessions-chart.md) owns Chart geometry and interaction presentation.

## Session Identity And Hierarchy

- Original Claude and Codex metadata owns whether a Session is primary or a subsession and which source parent it reports.
- LocalBrain retains both the source parent identity and the resolved internal parent relation. An unresolved child remains a subsession and never falls back to a primary Session.
- A recognized Codex guardian Session is provider-internal approval activity rather than user work. LocalBrain retains its source identity, parent relation, and directly observed Usage Records as metadata-only maintenance activity, but does not expose its prompts, decisions, or counters as an ordinary Subsession.
- Current Session browsing exposes only direct children of a primary Session. Deeper hierarchy remains preserved but is not flattened into user-facing lists.
- Work Subsessions remain outside global Search, Session-derived statistics, Workstream organization candidates, and Workstream Claude maintenance evidence. Their stored source and events remain available through approved parent-owned browsing; provider-internal metadata-only children are excluded from that browsing surface.

## Session Detail And Related Evidence

- Primary and valid direct-child detail views are conversation-reading surfaces: they show source-ordered user and assistant messages through the shared safe Markdown presentation, omit visible tool-call rows, and preserve source JSONL and normalized tool events. Codex-expanded repository/environment instructions and `<skill>` bodies do not become visible user messages, titles, search text, or reference evidence; the original user-authored prompt, including its literal `$skill` invocation, remains visible. Session text has no owning Local Context source, so source-relative references remain visibly unresolved rather than using a global guess.
- A primary detail keeps a Subsessions section for its direct children. Detail
  headings and direct-child rows use the provider cue `CL` or `CX`; numeric
  Source IDs distinguish separate registrations, and the configured source label
  stays in accessible text instead of repeating that label
  visibly. Each direct-child row shows its source-native external ID and aligns
  question, event, and date metadata in the Sessions inventory reading order. A
  child detail keeps explicit orientation back to its eligible primary parent.
- A persisted primary Session detail projects a bounded `관련 자료` rail from
  existing local data. `이 세션의 참조` uses source-neutral Session reference
  evidence and Session-observed identity for explicit Markdown/URL mentions and
  approved MCP read outcomes. Successful reads take precedence over failure-only
  attempts. Session detail does not query or display Thread/Workstream memberships,
  their indirect materials, or organization badges on direct references. Existing
  user-managed relationships remain owned by Workstreams and Threads.
- Links and local paths have shared resource identities; each Session keeps its own discovery/read evidence pointing to them. Jira and Confluence URL families are recognized by URL grammar even without an Atlassian tab registration, and open their safe external destination in both web and Desktop editions. Equal item IDs on different domains are not merged; no redirect lookup is performed. Bare IDs require one unambiguous already-known URL.
- Local Context remains the indexed document owner. A local path bookmark does not import a Markdown file, and its title/notes remain separate from Document content even when both share one resource. Removing a Document index or optional Atlassian registration preserves Session evidence; unavailable Documents are inactive, and same-path reindexing restores their links. Workstream/Thread mappings remain optional consumers of those resources.
- The direct-reference group owns its total and shows up to 100 retained rows
  initially. Material kinds appear once as
  alphabetically ordered sections, while direct references within each kind
  follow their oldest source occurrence so the rail progresses with the
  conversation.
- URL token boundaries exclude prose after an unmatched closing delimiter
  without removing valid non-ASCII URL paths. Retained overflow remains
  available through a reversible native disclosure whose collapse control
  follows the expanded rows in DOM, visual, and keyboard-focus order. Direct
  evidence retains the 100-target safety boundary with observed-versus-retained
  partial copy.
- Same workspace, directory, repository, path, and global recency never
  generate a candidate or fallback. Retained direct references whose targets
  are unavailable and unsafe external destinations remain visible but inactive.
  Loading the projection reads only bounded
  SQLite identity/evidence metadata, copies no content body, writes no
  relationship, and starts no source parse, model, embedding, remote,
  capability, scan, or maintenance work. A projection error never blocks the
  conversation.
- At widths through `920px`, the rail follows Session identity and orientation
  in document order and precedes the conversation. Subsession detail has no rail
  and its evidence is not rolled up.

## Session Inventory And Chart

The application uses a persistent left navigation boundary. Dashboard, Sessions Dashboard, Workstreams, Sessions, Atlassian, Local Contexts, and Sources have distinct responsibilities so source inspection does not overload the Session timeline.

Sessions owns a local `Sessions | Projects` view switch: Sessions is the default individual history and Projects is its path-derived grouping, not a separate persistent destination or entity. Its peer source scopes derive from the ordered private registry: `전체` combines every retained meaningful primary work Session, and each numeric source ID remains independently selectable, even when several profiles share one adapter. Meaningful requires at least one normalized Activity Event, direct Usage Record, or admitted skill observation; a metadata-only native stub owns no normalized Session projection. The selected source constrains the headline count, rows, pagination, and Project grouping through the same denominator without an inventory age cutoff. Every Session and Subsession icon uses the provider cue `CL` or `CX`, while configured profile names and numeric source IDs retain the distinction between separate registrations. Ordinary cards, Pinned cards, detail headings, and detail Subsession rows omit the repeated visible source name and retain it for assistive technology.

The shared inventory toolbar also owns a Session-only synchronization action for all registered local AI Session sources; its existing result region reports the current source, contract-upgrade reason, and bounded file progress before rendering the unchanged complete/partial/failed summary. The button keeps busy, retry, keyboard-focus and no-script behavior. Completion offers an explicit refresh with the existing URL scope; background collection does not reset focus, filters or reading position. Progress never exposes a local source path or content. Its source-status summary shows only those Session sources and does not expose the database path. The Sources destination retains the wider scan that includes enabled Local Context sources.

The Sessions inventory uses its secondary recall region for owner-curated `Pinned Sessions`, never recent Documents, inferred importance, or generated Suggestions. The panel is global across active Session filters and exposes every current pin without a product cap. It groups current workspace identities with Git-backed Projects first and non-Git working paths second, orders each section alphabetically by the displayed home-abbreviated workspace path (falling back to the workspace label only when no path exists), and orders Sessions inside one Project by displayed activity date (`last_event_at`, otherwise `started_at`) descending with `pinned_at DESC, session_id DESC` tie-breaks. The Project/path appears once as the group heading; each Session row shows its compact accessible source cue, title, optional Session-owned Git branch, and activity date without repeating the Project or configured source name. Only wide-layout height is bounded with an internal scroller. Its offscreen accessibility labels stay within that scroller and must not extend the document below the visible content; narrow layouts retain normal document flow.

Persisted primary work Sessions can be pinned or unpinned from inventory and detail; Maintenance Sessions and Subsessions remain ineligible.

Every inventory row reserves one utility layer: desktop and laptop place `질문 → 이벤트 → 날짜 → 핀` on the aligned upper edge, use stable left-aligned question and event columns across rows, and anchor optional Subsessions at the lower trailing edge; narrow layouts keep the pin upper trailing and the Subsession action lower trailing. Pin and Subsession controls remain outside the Session destination link.

The fixed pin hit area has no visible outline border or independent background in idle, hover, or pinned state, so it follows the owning row or detail surface; pinning never changes that surface. An unpinned pin may use the ordinary hover emphasis, while an already pinned glyph retains its information color on hover. The filled glyph, accessible name, and `aria-pressed` expose state while keyboard focus retains its separate focus ring.

Enhanced pin mutations update the control and Pinned Sessions panel in place, preserve document and panel scroll positions, keep the current inventory query state, and return focus to the changed control. Pin mutations remain local POST actions; they never write source files or imply native Claude/Codex process resume.

### Chart Behavior

List is the default; Chart retains the same complete source/workspace scope
independently of List pages and age. It represents retained timestamp, launch
folder and branch observations, not Git ancestry, duration or inferred work
identity. The complete [Chart presentation contract](../design/surfaces/sessions-chart.md)
owns Project visibility controls, overlap selectors, hover/held previews, pin
cues, zoom/pan, labels, reduced motion and recovery. The read and preference
contracts below define the data and persistence behind those interactions.
List retains its ordering, pagination, source filters, pins and child disclosures.
Chart controls do not change Session Workflow Focus or Auto Work.

## Synchronization And Session Inventory Read Models

[Session Synchronization](session-ingestion.md#session-synchronization) owns collection, repair,
source transactions and scheduling. This section owns the inventory and
Chart read projections that consume those normalized records.

Sessions browsing derives its ordered peer source controls from the same registry
and uses the numeric source ID, never provider kind, as GET and query identity.
`all` plus each source-specific view share one primary-work/primary-role
denominator across headline count, inventory, pagination, and Project grouping;
the inventory adds no timestamp cutoff. Unknown source IDs and missing workspace
IDs normalize to a valid URL while preserving the other valid scope. Ordinary
inventory and Pinned cards expose provider `CL` or `CX` cues with
the configured display label in accessible text instead of repeating it visibly.
Detail headings and normalized or lazy Subsession projections derive the same
provider cue and the registered profile’s accessible name; numeric source IDs
continue to identify filters and data. Their configured source display label remains in accessible cue text rather
than being repeated visibly in detail headings or parent-detail Subsession rows.
The child projection carries the existing `user_message_count` beside
`event_count`; a lazy Claude child derives the same question count from its
source events. The detail row renders question, event, then activity date.
Detail links retain the selected source/workspace only as return orientation.

The additive Sessions Chart uses `display=chart`; `display=list` or an absent or
unrecognized display value selects the existing paginated List. Scope repair and
the Session-only sync redirect retain Chart state. The full Chart projection
selects primary work metadata without pagination, age cutoff or body/source-file
reads. `parse_timestamp` normalizes valid `started_at`/`last_event_at` to UTC;
the latest valid value anchors the point. Only metadata-undated rows need an
Event-time fallback query. The Chart never calls activity-segment construction.

`GET /sessions/{id}/chart-activity` admits only an existing primary work Session
and returns ordered timestamp occurrences, total/undated Event counts and labeled
valid metadata times with `Cache-Control: no-store`. It selects no Event body,
tool argument or opaque source identity and performs no database mutation.
An explicit activity action presents retained Event-time occurrences, undated
counts and a separately labeled metadata-only time fallback. Points indicate
observations, never continuous duration, inactivity or completion.
Initial Chart metadata carries only ID, title, source cue fields, recorded
execution path/branch, lexically normalized folder key/name/display path,
earliest/latest valid observed time and provenance. `~` uses the local home;
normalization never reads Git history, resolves symlinks or groups by Git root.
Timestamp fallback continues to read only Event times when metadata is unusable.
The template additionally projects IDs from the already-loaded complete eligible
pin inventory; no new SQL, limit or mutation is introduced. Chart intersects these
identities with scoped records. A static pin cue reflects any pinned member of a
pixel aggregate; the selector and preview use the exact original member's status.
The browser builds case-insensitive folder-name/full-path ordered bands, missing
folder last, and stored-branch membership once per scope. Observed master/main owns
the baseline; feature-only data has a neutral structural guide. Missing branch
data never acquires a branch identity. Guide joins terminate at the first retained
observation, without asserting a Git fork, merge or Session relationship.
Guides begin at the first retained metadata observation, with Event timestamp
fallback only when metadata is unusable.

The browser constructs folder/branch membership once per scope, renders only
viewport points and exposes all original identities in same-track pixel
aggregates. Current observations and exact counts remain inspectable through
the [Chart presentation contract](../design/surfaces/sessions-chart.md).

Camera, selection ID,
vertical scale and List page use scope-specific version-four sessionStorage, which
also carries visibility as a navigation fallback. The dedicated
`session_chart_preferences` table owns durable visibility per logical source and
workspace scope; empty workspace scope means all workspaces. It has no cascading
FK and stores only sorted hidden-folder keys and update time. DB state, including
an empty all-selected list, overrides browser state. Only known keys affect the
screen; absent hidden keys remain available when their folders return. An absent
DB row permits migration from valid
`localbrain:session-chart-projects:1:<source>:<workspace>` localStorage, then legacy
tab visibility, through create-if-absent. Clear the old browser key only after DB
confirmation. Server load failure never triggers automatic migration.

`PUT /sessions/chart/project-visibility` validates local same-origin access,
source/workspace query scopes and a JSON body of at most 65,536 bytes. The payload
admits only `hidden_projects` and optional Boolean `only_if_missing`; hidden keys
must be a list of at most 2,000 strings, each at most 4,096 characters, with at most
60,000 encoded UTF-8 bytes after deduplication. Empty keys represent missing cwd.
A transaction replaces one current preference or preserves an existing migration
row, and commits before acknowledgment. Invalid inputs/scopes return 400, invalid
workspace query types or values outside SQLite signed-integer range 422, non-JSON 415, oversized bodies 413 and unavailable DB
writes 503. DB work runs in the thread pool. These writes never alter Sessions,
pins, membership or source files. Browser writes are serialized and retain the
newest pending choice; bounded keepalive requests support navigation, while load/save
failure exposes a native contextual retry and preserves in-memory use. Only confirmed
writes are durable; abrupt closure with unconfirmed queued work is not a save receipt.
Preference writes occur on filter changes rather than camera rendering. Browser
storage denial keeps filtering/navigation usable in memory. Earlier valid camera time/scale/selection migrates; old-spacing Y is discarded.
The [Chart design](../design/surfaces/sessions-chart.md) owns toolbar, scaled
geometry, fit/endpoint behavior and bounded transient panning. Ordinary detail's
Chart backlink adds return state only; Workflow projection/correction is unchanged.

## Session Conversation And Identity Reading

Session detail exposes `sessions.external_id` as **Session ID**. Abbreviation
starts at eight characters and extends on collisions with different stored IDs
across sources; identical native IDs retain the same abbreviation. The full ID
remains available for explicit copy. [Session Reading Design](../design/surfaces/session-reading.md)
owns exact clipboard feedback, timing, focus/recovery and metadata geometry.

Session detail presentation selects normalized `message` events in source sequence for primary Sessions and eligible direct children.
The [Session normalization contract](data-model/workspace-and-session-activity.md#conversation-normalization-and-empty-sources) owns authored-message preservation, generated-context and reply-envelope handling, native counterpart precedence and parsed-empty ownership checks. The [Activity Event phase contract](data-model/workspace-and-session-activity.md#assistant-response-phase-provenance) owns completion evidence for both providers.

Conversation cards use this phase only for a stronger neutral result frame, with a very light blue surface and a left accent for user inputs, no added phase text and no task-success claim.
Ordinary commentary and unmarked assistant cards keep their existing treatment.

A copied presentation view renders only user and assistant text through the shared Markdown contract without an owning Local Context source; raw source JSONL, source-relative unresolved references, `tool_call` rows, tool names, and the Session's complete retained event count remain unchanged.
Parent details list same-source direct children as Subsessions; child details resolve only to a same-source primary parent.
`/sessions/{id}/subsessions/{file}` is the canonical lazy compatibility route.
Existing Claude `/subagents/` links redirect to that route, which still reads the source-native `subagents/` directory and uses the same message-only Markdown presentation.

## Implementation Ownership

- `src/localbrain/sessions/subagents.py`: lazy Claude Subsession compatibility discovery over the source-native `subagents/` directory

- `src/localbrain/sessions/chart_preferences.py`: scoped, bounded user-selected Chart visibility in the private primary DB, independent of observations and browser camera state
