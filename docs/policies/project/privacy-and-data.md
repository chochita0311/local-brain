# Privacy And Data Handling

## Purpose

LocalBrain can display highly sensitive local information. This policy defines the boundary between shareable source code and private runtime data and governs persistence, external access, and disclosure.

## Repository Boundary

The Git repository may contain:

- application source code
- schemas and migrations that contain no user data
- generated or synthetic tests and fixtures
- shareable documentation without private paths, source names, ticket identifiers, copied conversations, or credentials

The Git repository must not contain:

- SQLite databases or database journals
- Claude or Codex session JSONL
- indexed note or document contents
- Task Runner prompts, evidence, streams, or result artifacts
- exports, logs, credentials, tokens, or environment-specific secrets
- screenshots or fixtures containing real local or company information
- machine-specific workflow inventories and handoff context

`.gitignore` is a fallback guard. The primary protection is keeping runtime data physically outside the repository.

## Local Persistence

The default runtime directory is:

```text
~/Library/Application Support/LocalBrain
```

It contains `localbrain.db`, private `session-sources.toml`, guarded schema-migration backups such as `localbrain.db-pre-usage-attribution-check-v1.bak`, `localbrain.db-pre-maintenance-workstream-fk-v1.bak`, `localbrain.db-pre-maintenance-session-contract-v1.bak`, and `localbrain.db-pre-external-resource-url-scope-v1.bak`, and Run artifacts. `LOCALBRAIN_DATA_DIR` may override this location, but it should not point to a tracked repository path. A versioned migration backup is local-only, is validated before use, and is never overwritten by a later startup.

`session-sources.toml` stores only a stable local source key, display label,
provider kind, and local root path. It contains no credential, account identity,
or Session content, is created with owner-only permissions, and remains outside
Git. Removing or mistyping an entry is configuration state, not deletion
authority: the registry row and normalized descendants remain in SQLite.
Synchronization stores only application-generated, 500-character-bounded source
health explanations; raw parser exceptions and Session content do not enter the
health field or API report. A successful scan of an unchanged, present root may
still reconcile a disappeared native JSONL and remove only that Source's
normalized Session descendants. It may also remove the normalized projection of
a present metadata-only stub after confirming that parsing yields no Activity
Event and no Usage Record; LocalBrain never deletes that native file, and a later
sync can import it after meaningful growth.

An in-app Task Runner stream remains a private Run artifact used for the Run Console and result parsing. It must not be re-imported as a Session, Usage Record, Local Context document, Activity Event, or search row. The selected Claude or Codex runner's persisted native JSONL is the sole Session and Usage source for that execution; maintenance policy keeps its content and resolved child content out of ordinary activity and search consumers while their direct real-model Usage Records remain eligible for cost totals.

Recognized provider-internal Codex guardian JSONL follows the same content boundary without becoming a LocalBrain Run: LocalBrain retains only its normalized Session metadata, parent relation, and direct Usage Records. Approval-review prompts and decisions, including embedded Session history, remain outside Activity Events, search, question counts, and ordinary Session/Subsession presentation.

Workflow Episode and direction descriptors are ephemeral derived state. Their
opaque Episode key hashes only the length-delimited stable source key and
source-native Session ID, while serialized output excludes that native ID,
source paths, messages, document bodies, excerpts, and opaque provider payloads.
The pure contract persists no graph, reads no local or external source, and
starts no connector, model, embedding, scan, or maintenance work. Any later
projection may use only already-approved normalized metadata and evidence under
their existing retention rules.

The database-backed workflow Focus projection follows the same local boundary.
It may read normalized Session/source/workspace identity, privacy-minimized
reference keys, user organization links, bounded Related Materials, direct-child
metadata, and persisted Atlassian structure-reference identity. Serialized
reasons hash Git roots and never include a repository path, native Session ID,
source path, message or document body, excerpt, search text, opaque payload, or
credential. Safe external destinations already admitted by the Related
Materials contract may remain navigable evidence. The projection writes no
graph or cache and triggers no filesystem, connector, network, Refresh, model,
embedding, or synchronization operation.

Workflow assertions are private, user-owned runtime state in the local
database. They retain opaque stable Episode keys, optional current Session row
IDs, exact bounded relation/lifecycle values, supersession identity, UTC action
time, and an optional trimmed note of at most 1,000 code points. The optional
note is private local text and stays out of tracked fixtures, logs, telemetry,
prompts, and external requests. Assertions copy no Session message,
Document body, source path, native Session ID, opaque provider payload, or
credential. Session deletion nulls only lookup aids; it cannot delete the
ledger. Create, correction, reopen, undo, history, and projection overlay
perform no source, connector, network, model, embedding, training, Refresh, or
external-system operation.

The Session Workflow Focus route serializes only that bounded projection plus
local presentation labels and correction metadata. The correction POST accepts
only exact bounded form fields; its optional note enters only the private
assertion ledger, and fixed error responses never reflect a submitted note,
exception, source-native identity, raw path, body, or connector detail. Its
browser controller derives coordinates and transient interaction state in
memory. For one enhanced success reload it may place only version, route path,
expiry, selected opaque Episode key, bounded disclosure keys, scale, pan,
scroll coordinates, opaque boundary focus, and a fixed result code in
`sessionStorage`; it stores no title, note, evidence content, URL destination,
source identity, native Session ID, or path, and consumes and removes the
record once. Focus changes and corrections fetch no second Session or source
body; evidence links use only destinations already admitted by the Focus
projection. Tracked route tests, browser fixtures, and screenshots use
synthetic records only.

Removing a source from LocalBrain must be distinguished from deleting the original local file or note. The application must not delete an original source as a side effect of unregistering or purging its index.

General backup, user-facing restore, retention, purge, encryption, and broader schema-recovery controls remain open work tracked in the [Project Backlog](../../plans/project/backlog.md); a migration-specific recovery copy does not close that wider requirement.

## Source Persistence Modes

External connectors should support explicit persistence behavior per source:

| Mode | Local persistence |
| --- | --- |
| `reference` | Identifier, link, and minimal metadata only |
| `cache` | Fetched content stored temporarily with an expiry policy |
| `index` | Approved content retained in the local search index |

No connector may silently promote content from `reference` or `cache` into durable `index` storage.

## External Access

- Company systems must be accessed only through approved connector or MCP Gateway capabilities.
- External integration begins read-only.
- Local Source Instance records may store a stable local key, provider/service identity, display name, and a shape-validated Gateway alias or canonical Atlassian Cloud ID, but never arbitrary opaque values, site URLs, credentials, access tokens, sampled content, or raw connector payloads.
- Capability observations retain only versioned logical-operation names, a schema fingerprint, availability, timestamps, invalidation, and bounded error evidence. They are refreshed explicitly rather than on startup, page load, search, or ordinary preview.
- A version-controlled allowlist must map logical reads to exact provider targets and validate bounded arguments before dispatch. Runtime rows, model output, prompts, or caller-supplied tool names cannot grant external writes.
- External synchronization requires a host-side executor that receives only a pre-authorized dispatch. Provider arguments and returned content stay in private Run artifacts; query projections and call-accounting rows contain no arguments or provider content. Claude or Codex receives only the validated local evidence and cannot access broad external tools in that Run.
- Applied Atlassian facts are private runtime data: manually registered or
  strict-Sync-created Site domains and Item identities, exact URLs, read-only
  URL container descriptors, remote identifiers, bounded metadata, source
  bodies, normalized text, hashes, freshness evidence, local notes, Topic/Tag
  vocabulary and assignments, and FTS rows remain outside Git. A derived URL
  descriptor is not persisted as Space identity and never changes `space_id`.
  Remote metadata cannot contain Jira description or Confluence body; approved
  body content is stored in its separate source-preserving table and reaches
  the content-role FTS row only under explicit indexed coverage.
- Derived Atlassian sightings are private runtime data. They may retain an eligible primary work Session or enabled Local Context Document identity, event/line/occurrence locator, an exact observed URL or a safe persisted normalized Session-projection locator, normalized URL, and optional bounded title/remote-ID observations from an approved read result. A projected locator must not be presented as unavailable original spelling. Sightings must not retain a Session or Document excerpt, opaque tool arguments/results, comments, attachments, command output, or maintenance/subsession content.
- Approved Atlassian structure-reference evidence is a separate private runtime
  owner from Item sightings. It may retain stable Site/service/reference
  identity, one canonical or alias safe locator, eligible Session or Context
  Document local identity, bounded event/line/ordinal location, optional
  non-authoritative container hint, and timestamps. It stores the privacy-safe
  locator for both Session and Document evidence, not an authoritative
  Document's arbitrary query spelling, source excerpt, raw query/JQL,
  credential, opaque payload, remote content, or Item local/organization state.
  Removing the last evidence may derive archived availability but does not
  require deleting the stable reference identity or safe locator history.
- Source-neutral Session reference evidence is private, fully derived runtime data. It may retain an eligible primary work Session and source path, event/line/ordinal locator, opaque grouping key, exact Document or configured Atlassian Item FK, bounded observed issue/file/host-path identity, safe normalized HTTP(S) destination, approved tool name/call identity, completed success/failure outcome, extractor fingerprints, counts, and bounded diagnostics. Visible generic URLs discard credentials, fragments, and all query material. The shared static Atlassian locator may inspect only its bounded family-specific query allowlist ephemerally, then retain a canonical safe locator containing only the identity projection needed to distinguish the reference. Jira Issue query identity canonicalizes to a query-free `/browse/{ISSUE_KEY}` path. A Confluence Page keeps its valid Space/Page path when available; otherwise it may retain only canonical positive `pageId` on `pages/viewpage.action`. RapidBoard may retain canonical positive `rapidView` plus one validated `projectKey` grouping hint; Filter and Dashboard may retain only canonical positive `filter` or `selectPageId`. It never retains raw query, JQL, arbitrary filter text, tokens, or unrelated parameters. Semantic Session grouping excludes locator spelling and container hint. Approved Atlassian calls correlate only bounded call/result identity fields and never initiate a provider request. It must not retain message excerpts, credentials, URL fragments, unapproved query material, opaque arguments/results, remote content, Maintenance content, or Subsession content. Reconciliation may delete only these derived rows; shared Resources, Documents, remote facts, notes, classifications, and organization links remain separate owners.
- Atlassian browse, Add orientation, URL preview and registration, access setup,
  search, detail reading, local classification, local relationship edits, local
  evidence Sync, and refresh preview use only persisted local state and must not
  send a query, result, or local content to Atlassian or an AI service. Strict
  Jira Issue or Confluence Page recognition may create a local Site, Item, URL,
  and evidence rows during Sync, but never a binding, credential, Source
  Instance, remote fact, or persisted Space inference. Each source is atomic;
  a failed source publishes neither partial rows nor a resolver-cache identity
  for later sources. Local evidence Sync receipts contain only bounded counts,
  fixed reason codes, source kind, and local numeric ID; they remain
  process-local, expire, and are never persisted. Provider is never inferred
  from URL content; credentials and tokens are never accepted. Invalid input or
  failed local setup creates no partial rows and triggers no remote lookup. The
  [Product Model](product.md#atlassian-explorer-add-connections-sync-and-refresh)
  owns the user-visible flow, and [Project Architecture](architecture.md#external-access-and-synchronization-constraints)
  owns request limits, dispatch, and transaction boundaries.
- Connected candidate discovery and refresh require explicit submission through an authorized Source Instance. Candidate results and per-target manifests are private runtime evidence, never authorize automatic bulk registration, and must not imply complete company-wide enumeration.
- Validated remote results may update only their approved remote-state and content owners. They must not overwrite local attention, notes, Topics, Tags, Workstream/Thread relations, or other user-owned organization state.
- Reference coverage rejects remote metadata and body persistence; metadata coverage rejects bodies. Explicitly downgrading indexed coverage removes the stored body and rebuilds the remaining eligible identity/local FTS roles, while ordinary failure or unavailability never performs that destructive downgrade.
- Due timestamps are local advisory state and perform no external or model call. Failed, unavailable, and not-found checks retain last-known content and local organization until an explicit destructive local action.
- Any future external write requires a visible preview, attribution, and explicit user confirmation.
- Local content must not be sent to an unapproved AI, embedding service, website, repository, or person.
- Generated summaries must preserve provenance and must not present inference as confirmed fact.
- Connector failures, stale content, and inaccessible sources must remain visible rather than being represented as current data.

## Credentials

Credentials should remain managed by the operating system, Claude CLI, or an approved gateway. LocalBrain must not copy credentials into its SQLite database, Run evidence, logs, tracked configuration, or documentation.

## Source Consent And Permissions

- Sources should be explicit and inspectable, including indexed paths, files, note accounts, and external scopes.
- Apple Notes access is optional and uses local macOS Automation. The operating system may request permission on first connection.
- Source-specific exclusions and retention controls must be implemented before broad automatic indexing.
- Error pages and logs should avoid full prompts, note bodies, session excerpts, credentials, and connector payloads by default.

## Tracked Examples

Tracked examples, tests, screenshots, and documentation must use synthetic names and content. Real Workstream titles, local absolute paths, ticket identifiers, Slack links, note text, and session excerpts belong only in local runtime data or ignored working context.

## Repository Enforcement

- `scripts/check-repo-privacy.sh` scans every tracked and non-ignored untracked candidate before commit.
- `.githooks/pre-commit` runs the same check through the repository-local `core.hooksPath` configuration.
- `.privacy-patterns.local` provides a local-only literal denylist for private names and phrases that generic detection cannot identify.
- `.privacy-allowlist` contains only exact paths of reviewed binary or media files approved for tracking.
- The scanner reports matching file paths without printing sensitive matching content.
- Passing the scanner reduces accidental disclosure risk but does not replace human review of newly approved media, external connector output, or export behavior.
