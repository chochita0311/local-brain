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

Workstream candidate descriptors follow the same private, ephemeral boundary.
Their pure normalizer accepts only supplied canonical metadata/reference facts
and proposed pairs. Artifact scope/identity and source occurrence identity are
hashed before serialization; raw paths, source-native Session/occurrence IDs,
bodies, excerpts, opaque payloads, and extra input fields are not copied.
Attributed bounded titles, Session source keys, local Session destinations,
opaque evidence keys, observation/source states, and coverage may be returned.
Candidate/membership authority remains inferred, distinct from source evidence.
Unknown timestamps and partial coverage never become fabricated progress or
global discovery claims. No candidate, review assertion, organization link,
cache, or feedback label is persisted by this contract, and no source, remote,
model, synchronization, or filesystem operation occurs. Its fixtures and
validation use synthetic data only.

The isolated work-reconstruction experiment is a separate, explicit bounded-text
boundary; it does not relax the metadata-only Focus or candidate contracts.
It accepts only a supplied fixture or an explicit existing database plus frozen
source/time/record manifest. After the owner selects current LocalBrain data,
the operator may resolve that named database from its configuration and explicitly
prepare a bounded chronological sample through the selected cutoff. There is no
default-open behavior on import, help, ordinary app entry, or command invocation.
Independent expectations are required for quality scoring; an explicit unassessed
execution check may retain unknowns but may never generate its own answer key.
Eligibility/permission checks
precede selected indexed-text reads; raw tool payloads, native source files,
metadata/reference-only bodies, disabled sources, and source-body payloads are
excluded. It performs no initialization, migration, synchronization, connector,
model, external request, source mutation, or legacy cleanup.

Private manifest values, expectations, evidence spans, generated labels, and
detailed results remain on the local machine outside Git and hosted-agent
inputs/tool output. Default command output is fixed status codes only; even
non-identifying aggregate sharing is explicit. All command-generated output,
including supplied-fixture results, belongs in a new owner-only directory outside
the repository, with an explicit owner/expiry and a bounded complete report.
Reruns cannot overwrite it. Task scratch is removed on completion/failure/cancel;
retained results need owner-managed expiry cleanup because no scheduler is added.
No full database copy or permanent archive is created. Synthetic tests alone
cannot establish private extraction quality or approve production transition.
The [experiment Feature](../../plans/feature/feat-0095-bounded-work-reconstruction-experiment.md)
owns the exact trial caps and limited review budget.

The separately approved [full-Session simulation](../../plans/feature/feat-0097-replayable-session-simulation.md)
removes those sampling limits only for its explicit CLI. It accounts for all
stored Sessions and reads all nonempty user/assistant message content of
primary/full work Sessions through a read-only SQLite connection. Maintenance,
subsession, metadata-only and non-message content remain excluded. No new source
ingestion or context-document body expansion is implied. Unknown dates do not
exclude otherwise admissible content.

Its explicitly selected private directory outside Git owns a source-bound
inventory/cache SQLite file, an ownership marker, progress, the current report
and at most one previous report. Locators, attributed titles, hashes, vectors
and inferred memberships are private; complete raw message bodies are not
copied. The cache expires after 30 inactive days, enforced on the next execution;
status rejects expired state. Purge removes only this owner's derived files
under its writer lock and retains the minimal ownership marker/lock. There is
no background cleanup scheduler or source-file deletion. Current inventory
replacement removes unused vectors; successful model replacement prunes old
namespaces. Interrupted work retains checkpoints until resumed or purged.

Only explicit local model inference is admitted, with verified already-installed
asset fingerprints, local-files-only loading, no remote code, offline/telemetry
controls and a Python outbound-socket guard. These controls are not an OS-level
network sandbox. No training, asset download, external inference or write to
Foundry state occurs. CLI output is fixed codes unless `--show-counts` explicitly
opts into aggregate disclosure. Model/library output is suppressed; private
results remain local. This simulation does not change the old sampled comparator or
authorize production organization, correction, migration or legacy retirement.

The separately approved full-history affinity viewer consumes this same finite
owner without creating another private store. A shared lock guards passive reads;
owner, expiry, source binding, bounded report shape and whole-source freshness are
checked before display. Exact quoted spans are independently verified against
current original records. Only one derived index may live in process memory,
invalidated by report or source DB/WAL changes; browser history holds viewport/
Trace coordinates and edge visibility, not evidence. GET never renews expiry, deletes artifacts, starts
model work, ingests or changes organization. Missing/stale/expired/invalid results
are explicit, not replaced by the previous sample. No private screenshot, title,
quote or inventory enters tracked/browser-test evidence; fixtures are synthetic.

The separately approved [work-context model trial](../../plans/feature/feat-0098-local-work-context-inference.md)
may install the pinned public Qwen3-4B and separately approved Qwen3-8B assets
into distinct explicitly selected owned model directories outside Git.
Unknown models, unpinned revisions and mismatched existing ownership are rejected;
installing the comparison does not replace or purge the baseline.
Installation takes no private-source arguments,
uses no authentication token, and contacts only the official public model host
and its asset delivery endpoints. Foundry code/assets are not modified. The
installation's content-addressed asset cache is its durable model storage;
verified assets are retained for reuse independently of evaluation expiry.
Interrupted public downloads are resumable installation state, not source data.
Optional Xet transport uses a new empty private task-owned directory, selected
before the client import, with chunk/shard caches disabled. Its public transfer
diagnostics are temporary: remove only the verified task-owned scratch after the
installer process exits. Durable model assets must not depend on that directory.

Inference is a separate operation with offline/telemetry controls, an outbound
Python socket guard, local-files-only safetensors and no remote code. The initial
evaluation accepts only repository-owned synthetic cases, not a database path.
Quoted outputs and model identity stay in an owner/lock-protected private report
and per-case checkpoint with 30-day inactivity expiry; unknown files prevent
cleanup or adoption. Fixed CLI diagnostics disclose no prompts/output. Every
thinking-mode response discards reasoning tokens without decoding or persistence;
only counts and the final answer are retained. Staged inference uses validated
source quotes, never reasoning traces or invented summaries as new evidence. Every
classified/selected-strategy decision selects a bounded answer code against original
context; only explicitly selected source evidence is projected into output.
Its trace contains span IDs, inferred categories and unit numbers, not private
prompt copies or hidden reasoning. Sentence enumeration imposes a finite packet
bound and refuses overflow rather than dropping source content. These inferred
choices carry no confirmation or instruction authority. Every
field retains its exact quote, speaker and locator; a valid quote does not prove
semantic entailment, completion or user confirmation. The synthetic quality
gate precedes any separately implemented private-corpus consumer. No training,
external inference, automatic source access or legacy/organization write occurs.

The separately approved evidence-first strategy uses semantic labels to assess
literal source facts and membership before projecting units/relations. Only
selected original spans become citations; relationships automatically abstain
when the model judges support missing or conflicting. This is not a guarantee
that all unsupported interpretations are recognized. No user-confirmation tasks
or source/organization writes are added. Its
content-free trace records derived span IDs, semantic assessments and withholding
reasons, never hidden reasoning or invented summaries as evidence. Synthetic
evaluation retains completed refusals and semantic failures for replay in the
same finite-lived evaluation owner. Changed/corrupt observations refuse reuse;
at most one extra incomplete-case attempt follows a clean interruption, while an
unclean in-flight crash refuses restart. The holdout prerequisite reads only a
complete same-candidate synthetic report and revalidates its observations/gates;
it neither discovers a private source nor grants production admission.

The separately invoked protocol diagnostic admits only its repository-owned
synthetic fixtures and the existing pinned 8B model. It shares the evaluation
directory ownership, exclusive lock, atomic checkpoints and finite expiry, but
keeps completed failures for replay and refuses changed configurations instead
of overwriting unexpired observations. Reports may contain those synthetic
prompts and final short answers, never private source text or hidden reasoning.
The command accepts no database, private input or holdout argument. Rendering
hashes, code token IDs and resource counters support diagnosis; completion never
authorizes a production consumer or relaxes model admission.

The separately invoked role-formulation comparison likewise accepts only its
frozen synthetic suite. It retains the same source attribution, installed-model
offline boundary and expiring evaluation owner; its recorded prompts, focused
spans, relation quotes and answer/token audits contain synthetic evidence only.
No reasoning traces are requested or retained. Every actual choice attempt is
reserved in the checkpoint, including choices inside the unchanged relation
pipeline. Completed incorrect/refused observations are preserved; changed config,
corruption, exhausted budgets or unknown in-flight duration cannot silently reset
the comparison. No private-input/DB/holdout path or product mutation is added.

The separately approved source-claim adapter trial uses one frozen installed-8B
candidate on synthetic records only. Native identity, source revision, speaker
and coordinates come from the host; model interpretations and scoped fulfillment
judgments retain distinct inferred provenance. It shares the evaluation-store
owner/lock/atomic/30-day inactive retention rules in a new namespace, without
adopting old reports. Completed invalid, refused and semantically wrong outputs
remain available for generation-free replay; changed configurations, corrupted
checkpoints, expired trials or unclean in-flight reservations cannot reset the
same trial. Caught interruptions consume their reserved attempt rather than retry
it. Default CLI diagnostics contain no source/output text. Original holdout is
reachable only after revalidated same-candidate development gates and a primary
semantic review receipt; it is still synthetic, never a private input path.
No training, download, private source/DB access, Foundry write, product consumer,
organization mutation or legacy deletion follows from the trial.

The previous-sample Auto Work viewer is a narrow local consumer of the
experimental extraction contract. A single `auto-work-preview/current.json`
under the configured runtime directory retains an owner/version, seven-day
expiry, bounded frozen manifest, digest, sample counts and extraction output.
It does not retain full source bodies, native files, a DB copy, source paths,
credentials, or a report history. This is purpose-owned product preview state,
not task scratch; refresh atomically replaces only valid owned output and a
subsequent visit removes expired owned output. Unknown files are never overwritten.

The viewer reads only current eligible indexed spans for provenance checks and
local presentation, then renders escaped evidence without browser storage or
external requests. GET starts no extraction; an explicit same-origin local
refresh uses fixed configured source paths and unchanged caps in an isolated
command. Responses are private/no-store, errors are bounded fixed messages,
and private content, group labels, counts and screenshots never enter hosted
agent output. Tracked fixtures and browser evidence remain synthetic. Neither
viewing nor refreshing changes Workstream/Thread, source, or legacy state.

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
