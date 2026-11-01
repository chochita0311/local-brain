# RUN-20261101-230: Feature Availability And Documentation Boundary

## Metadata

- Run ID: `run-20261101-230`
- Status: `passed`
- Execution Profile: `fullstack-product`
- Surface lanes: assembly/lifecycle/API; shared shell/Settings/guides; documentation; contract/functional/design/interaction verification
- Related Features: [Context Search](../feature/feat-0153-context-search-conversation.md), [Drive Settings](../feature/feat-0147-drive-settings-connection.md)
- Existing contracts: [Context Search](#archived-context-search-contract), [Google Drive](#archived-google-drive-contract), [Settings](../../policies/project/desktop-app-and-settings.md)
- Authorization: owner directly requested temporary hiding in app and development web and removal of private development-record references from canonical guides, including the Developer Guide. Run/Feature and comparable development-history records may retain those references.
- Closeout authorization: the owner subsequently requested whole-session reconciliation, two independent documentation reviews, relevant code/test checks, and commit/push of only this session's changes after blocking findings are resolved.

## Approved Boundary

Suspend Context Search and Google Drive from default delivery while retaining
their implementations, tests, models and private state. Exclude their entry
points, model controls and background jobs together; keep core Session/Context
collection, keyword/embedding search, settings and recovery intact. Do not infer
reactivation or further feature development from historical pass states.

Canonical guides must not inventory or instruct use of the developer's existing
evaluation archive. Generic, caller-selected private output examples remain
tool documentation. Retain necessary past storage context here rather than
moving it into another canonical guide. No original-data deletion or Git-history
rewrite is authorized. The later closeout request authorizes publication of the
reviewed source/documentation changes, without publishing private runtime data.

## Settings And Storage Findings

The initial request placed `onboarding_completed` immediately after
`schema_version` in saved TOML. The serializer now pins those first two fields,
retains supported values and unknown fields, and keeps revision checks, validation
and atomic private replacement. The owner's existing local file was reordered
without changing its values. This does not introduce new preference defaults.
[Common Settings](../../policies/project/desktop-app-and-settings.md#common-settings-contract)
owns the serialization and first-start contract: Sessions, the Mac's time zone
(UTC fallback), enabled Session sync every 10 minutes, enabled Context sync every
30 minutes and incomplete onboarding on a fresh installation. Existing registered
sources can mark a missing-file upgrade as already onboarded; later launches
preserve an existing file and apply defaults only to missing fields in memory.

The storage explanation distinguished the primary DB and its live WAL/SHM,
schema-migration recovery copies, preferences and source/search configuration,
independent sync-health files, model registrations/locks, durable Run artifacts
and rebuildable private caches. Ordinary startup does not produce a full DB
backup, a persistent server log or original evaluation records. The
[installation/storage owner](../../policies/project/installation-and-storage.md)
retains the installed-user lifecycle and recovery guidance; machine-specific
file inventories and private contents are not publication artifacts.

The separately configured development archive holds explicitly produced model,
search, work-context/role, source-claim and personal-insight evaluation evidence.
It is not required by ordinary installations, not created by the tested normal
startup, and not disposable under the migration-backup retention rule. Source
history introduces `DEFAULT_DEVELOPMENT_DIR` in commit `d75af64` on 2026-10-05;
that dates the namespace in code, not the birth or first use of any local folder.
Original private directories, DB copies and evaluation outputs were neither
moved nor deleted. The current-tree privacy findings below do not certify all
prior Git history or future publication candidates.

The existing migration-retirement code was inspected rather than changed.
After a committed initialization, it checks current migration contracts and
SQLite integrity before deleting recognized owned, unchanged, inactive backup
groups. It preserves the newest eligible copy through seven days measured from
its modification time; older eligible copies can retire sooner. Uncertain
ownership, links, active files and nonempty backup WALs preserve the group.
Backend startup and actual automatic/manual Session or Context scans invoke
initialization, so an eligible expired copy can retire without a restart; there
is no independent seven-day cleanup timer. Preparing the existing DB/schema
does not clear stored user data. Live DB sidecars and arbitrary manual backups
are outside this automatic retirement.

## Historical References Removed From Canonical Guides

Earlier configuration/storage guides listed `LOCALBRAIN_DEVELOPMENT_DIR`, whose
default was `~/Library/Application Support/LocalBrain-Development`; with a custom
data root its unspecified counterpart was the sibling `<data-name>-development`.
The explicit environment variable selected another location. These references
described development work, not ordinary installed-app output.

Earlier model-tool guidance directed comparison reports/checkpoints to that
archive outside Git, creating the chosen private parent before explicit output.
The prior Developer Guide allowed owner-requested guide evaluations to retain
frozen inputs, raw outputs and reviews under
`<LOCALBRAIN_DEVELOPMENT_DIR>/personal-insight-evaluations/<id>/` with owner-only
access. Those records were separate from product Run rows; subagent simulations
did not create Insights history, and tracked evaluations held sanitized conclusions.
Prior privacy guidance placed private benchmark queries, judgments and raw
results only in an explicitly selected private archive while tracked fixtures
remained authored synthetic material. Comparison guidance required explicit
retirement of its reports, synthetic DBs and isolated runtimes when no longer
needed, separately from shared public model checkpoints.

The legacy explicit `storage migrate --include-development` path recognized
owned historical records, including `personal-insight-evaluations` and
`work-context-*`/`work-role-*`/`source-claim-*` records. Its operation required
stopping app/development jobs, distinct non-overlapping roots on one filesystem,
owner/inactivity/unchanged-tree checks and no destination collision. Rename
preserved original contents, modification times, hashes, ownership and retention
meaning without copying the primary DB or weights. Archived diagnostic paths
described original execution rather than current runtime dependencies. This
compatibility implementation remains; it is no longer an installed-user or
canonical Developer Guide procedure. No original archive was moved or removed.

## Verification

Initial working changes were the preceding settings serialization/order fix;
those changes are preserved.

Result: passed for the requested suspension and canonical-guide boundary.
Evidence Coverage: source contracts, real isolated startup/HTTP behavior,
rendered browser controls and the rebuilt bundled backend. Native macOS physical
input, recipient execution, live Google accounts and answer quality are not
certified by this Run and remain outside the suspended delivery.

- Full discovery exercised 1,509 tests without an assertion failure. The sandbox
  blocked the loopback-server setup for 11 additional transport tests; the exact
  11 passed in a separately authorized local-only run, for 1,520 distinct tests.
- Omitted-package startup runs cover both editions, including Drive omission.
  Default-delivery probes reject Context Search/Drive page/API/model-action
  entry points, start neither service, retain core collection/search/settings,
  and leave saved automatic Drive jobs and received-copy bytes unchanged.
  Positive registered/cached answer-model state stays excluded from Settings.
- Canonical installation, developer, storage/privacy and model-tool guidance no
  longer names the old archive namespace or its retained-record operations.
  The documentation map was corrected too. Generic caller-selected private
  output examples and the harness's separate general privacy rules remain.
  Historical Run/Feature records and original private files were not removed.
- Current tracked-tree checks found no DB/SQLite/JSONL/log payload files. Exact
  private-archive content matches were empty files and snapshots of already
  tracked source/guide/plan documents, not original nonempty trial inputs,
  outputs or logs. This is a current-tree check, not a complete history audit.
- A freshly built wheel contains six user guides and no development-history
  tree or runtime record files. Those guides contain no old archive reference
  or Context Search/Drive usage instructions.
- Browser automation checked 1,440/700/320px layouts, the unchanged bounded
  Settings shell, seven available categories, horizontal narrow navigation,
  preserved embedding-model controls, category switching, modal close/focus
  restoration and Local Context navigation. No horizontal body overflow or
  JavaScript errors occurred in the checked ordinary flows. Screenshots were
  visually inspected; only synthetic application state was used.
- The Apple Silicon test app and ZIP were rebuilt with the configured offline
  toolchain. Deep strict codesign, private build-path inspection, ZIP CRC and
  SHA-256 checks pass. Its actual bundled backend served the authenticated
  Sessions/Settings UI with no hidden-feature controls, matching Settings JS
  bytes, excluded endpoints returning 404 and no new Drive/development state.
  This browser witness uses the bundled backend, not physical Tauri-window input.
- A final active-runtime check found that an already running development server
  still held the older route/service composition while reading updated templates.
  With no active maintenance, Insights, Context Search or Drive job and no pending
  restore, it was gracefully restarted with the same arguments, environment,
  working directory and standard streams. Its actual Settings response then
  excluded both features and their entry points returned 404. Settings, source
  registration and natural-search configuration bytes were preserved. The
  maintained server uses the durable checkout/environment, not task scratch;
  an already open browser document needs a refresh.
- Privacy, whitespace and generated catalog checks pass. Local build, browser
  and test scratch is removed after all task-owned processes stop.

## Return Boundary

[Feature Availability](../project/feature-availability.md) owns the suspension,
preserved state, parked evidence and return decision. Earlier technical pass
states and parent acceptance gaps remain distinct. No merge, publication,
feature reactivation or new product acceptance is implied.

## Related Documentation Removed — 2026-11-01

The owner requested removal of the suspended features' related explanations,
including their current policy pages and shared-guide descriptions. This is
an incremental docs-content follow-up. Current guides no longer teach or
advertise them; implementation, stored data and prior evaluation outcomes
are unchanged. Their full former contracts and complete shared source units
are retained below as history for a later owner-selected return or replacement.
Snapshot wording records the prior requirements and facts; it does not
reactivate a feature or make the snapshots current product guidance.

Historical references now resolve to these snapshots rather than deleted
policy files. The current suspension and return decision remain owned by
[Feature Availability](../project/feature-availability.md).

The backup call-path check also confirmed that backend startup and actual
Session/Context scans call `init_db()`, which retires eligible migration
copies after committed DB preparation. Scheduled or manual sync can thus
retire a seven-day-old copy without restarting the backend. There is no
independent seven-day timer, no database clearing and no per-launch new
backup. The storage owner now names these triggers explicitly.

### Follow-Up Verification

- Removed the two policy pages, their entries in the current documentation map,
  and related product, installation, architecture, developer, privacy, settings,
  data-model, rendering and design-guide descriptions. A scan of all 81 canonical
  guide/policy files found no remaining feature-specific references. The natural
  language Local Context search documentation remains a separate active feature.
- The current Plans Index and roadmap now reflect the suspension. Feature
  Availability retains the return decision; prior PRD/Feature/Spec/Run/evaluation
  outcomes remain historical evidence. Complete former policy bodies and shared
  source units are preserved below with their original conditions and force.
- Verified 41 preserved source units and 1,069 line/sentence assertions against
  the actual Run text. Checked 8,246 local links across 1,240 Markdown files,
  including 44 snapshot-fragment links: no new broken links were introduced.
  The check also found 32 pre-existing link issues outside this change.
- The first full run exposed the expected stale source digest after removing
  the data-model guide's separate feature section. Rebuilt schema presentation
  using the configured generator and reviewed the complete JSON delta: only
  that document's source hash changed. Refreshed the dependent audit fingerprint
  and generated ledger; schema, presentation content and all 758 audit decisions
  are unchanged. Data-model, presentation and cleanup-audit checks pass.
- Rebuilt the wheel offline: its 345 files include the exact updated manifest
  and six bundled guides without suspended-feature instructions or private
  runtime/history files. The extracted package loads its manifest with checkout,
  database, network and subprocess access blocked.
- Final full discovery passes all 1,520 tests. The local-only synthetic HTTP
  transport fixture ran with loopback binding enabled. Catalog, privacy and
  whitespace checks pass. This follow-up changes documentation and derived
  fingerprints, with no additional route, UI, DB or service behavior change;
  the earlier browser/native witnesses remain evidence for the preceding code
  change. Task-owned working files are removed at closeout.

### Independent Reviews And Session Closeout

The owner requested reconciliation of the complete session into the existing
settings/storage, current-work and evidence owners, followed by reviewed
commit/push. The initial settings and storage discussion is recorded above;
Feature Availability continues to own the undecided return/extension/replacement
boundary. No separate session log or broad documentation restructure was added.

- Two independent read-only reviewers used Docs Structuring and Docs Shaping,
  respectively, against frozen candidate hashes and the resolved scope. They
  reviewed the complete Run and availability record, affected current guides,
  entrances/plans, removed-source preservation and decisive implementation paths.
  Their static reviews do not independently reproduce runtime or test evidence.
- The ownership review found a historical introduction separated from its model
  table and shared qualifications. The original model-purpose/admission rows,
  pretrained status, asset reuse and explicit-tool boundary now remain together.
  The unchanged command procedures retain their current owner. Unique source
  headings were reattached to their bodies; only two exact duplicate lead-ins
  were removed. The reviewer verified these repairs and their links.
- The composition review found a leftover development-root configuration
  paragraph in the canonical Developer Guide. Its cache-only guidance, explicit
  cache override and stop/migration requirements remain there; the complete
  original compound paragraph is preserved below as history. The reviewer
  verified the replacement, preserved original and rebased links.
- Primary code review covered preference serialization/unknown-field retention,
  feature assembly/import boundaries, service failure isolation and lifecycle,
  Settings APIs, templates/JS and synthetic regression assertions. No blocking
  code finding remained. A fresh full discovery passes all 1,520 tests; an
  additional synthetic preference probe passes field ordering, unchanged values,
  nested unknown-field preservation, stale-revision refusal and private mode.
  Settings JS syntax, data-model parity, generated presentation, schema audit,
  catalog, privacy and whitespace checks pass. No code changed during this
  closeout; earlier wheel/native/browser evidence keeps its stated limits.
- Across 1,240 Markdown files, 8,250 local links have no new broken targets or
  fragments relative to the pre-session HEAD. The current 32 issues predate this
  session and remain outside its scope. Expanded canonical scans cover both
  feature names and indirect development-root wording. The maintained development
  server's actual Settings page still excludes both features and three checked
  page/API entry points return 404; this was a read-only check, not a restart.
- Physical native-host input, recipient-Mac execution, live two-account Google
  permissions and broad answer quality remain unverified. Suspension supplies
  none of those acceptance results or permission to resume development. The
  archive namespace's source-introduction date does not establish any local
  directory's birth, and current-tree checks are not a complete Git-history audit.
  Original private data and the maintained server are preserved; no task scratch
  is retained as required evidence. Publication is limited to the reviewed
  session source/docs candidate under the explicit closeout authorization.

## Archived Context Search Contract

Former source: `docs/policies/project/context-search.md`; pre-removal SHA-256: `7eb8cc4a615340f5e13eb1040d00f918f06043889c2412f37f20e053552b347e`.

This contract applies when the optional Context Search package is included in
application assembly. [Feature Availability](../project/feature-availability.md)
owns current delivery suspensions; an excluded package provides no page/API,
answer-model controls or generation service.

Context Search is a local, transient question/answer surface over enabled readable Local Contexts and already received Drive publisher copies. It does not widen ordinary natural-search corpus admission or register application data as Contexts. File-backed sources expose bounded UTF text; already collected non-filesystem documents expose their current readable normalized body. Binary/unreadable/limited results are explicit. Paths remain inside enumerated source roots, symlink traversal is refused, and no shell, write, external search or republishing tool exists.

Models choose structured list/search/read requests. The app validates and executes them, returns bounded evidence and permits a bounded continuation. Source publisher, author and mentioned/contact person remain distinct. Responses identify evidence or insufficient/partial support; document instructions never grant new authority. No embedding preparation is required.

Each turn permits8model rounds and12tool calls; the native protocol admits at most4calls per output. File enumeration is capped at5000files, with directory-count/time stopping checks. Search checks global5000attempts/32MiB of processed text/6second stopping thresholds between files; a last read or filesystem call can cross a threshold, so these are bounded-work stopping checks, not hard filesystem latency guarantees. Reads use at most2MiB of UTF text (or a bounded collected-body prefix) and200lines; tool serialization is further bounded. Search evidence includes a matching line and nearby context, not an assertion about the whole folder. Missing/unreadable/changed/binary items and limits remain distinct from absence. Status/answer events stream over a no-store JSON-lines response; model text renders through the shared safe Markdown renderer and evidence excerpts use plain text.

Only browser user/assistant turns enter the request (at most13messages/24000characters,4000per user question); client system/tool/root authority is refused. The current client sends at most3prior successful turn pairs. A missing model never triggers a download; no-source/busy/protocol/time/input failures have actionable states. One request runs at a time, with a360second lifecycle ceiling; parent disconnect, abort, model switch and shutdown terminate owned workers. Public model presence discovery is not integrity or quality certification.

Public Qwen originals stay in the existing resolved Hugging Face Hub cache. Existing cache precedence and pinned ID/revision/hash verification apply; app setup does not move, overwrite or purge another consumer's assets. Small app installation manifests remain under `<data>/models/<slug>`. Worker/compiler caches use `<cache>/context-search/`, never the public Hub or repository. Private sources, prompts, tool results and answers never enter the public cache.

The two generation choices are Qwen3-4B and Qwen3-8B. Settings → Search Model owns explicit public installation/verification and cached-asset reuse. The embedding setup remains independent. A question never starts a public download; existing complete public assets can be registered locally. One isolated generation worker may retain model weights; switching/aborting/shutdown releases it. Offline/network blocking is worker-local and does not affect Drive or the web process.

Conversation exists only in current-page/request memory. The client sends its bounded displayed history with each turn; no conversation table, transcript file, browser storage or answer cache is created. Leaving the screen, opening settings, hiding the browser tab, pagehide and back/forward restoration clear conversation and cancel in-flight work. Refresh starts empty. Evidence details are transient. Selected model may be chosen for a subsequent turn; no cross-model server conversation is retained.

The route and APIs inherit loopback/same-origin and native-token boundaries, bounded JSON input and no-store responses. Errors are sanitized without prompt/path/raw model stderr. Runtime quality, actual hardware/model performance, source formats and native-host evidence must be reported separately from synthetic checks. Delivery/approval/evaluation history belongs to PRD026 and its Features/Runs.

## Archived Google Drive Contract

Former source: `docs/policies/project/google-drive-sync.md`; pre-removal SHA-256: `70ba66a79dc1e14cfee041d479af4241829036acf548f07f5f06b1c8d10255dd`.

### Ownership

This policy owns the approved Drive integration contract. [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md) and its Features own delivery and evidence, not runtime truth.

The contract below applies when the optional Google Drive package is included
in application assembly. [Feature Availability](../project/feature-availability.md)
owns current delivery suspensions; exclusion provides no Settings category/API
or background service and preserves existing state and copies.

### Sync Contract

Settings has a separate Google Drive tab. A full Google Drive folder URL identifies the root; optional resource keys are parsed internally. Each installation supplies Google Cloud CLI (`gcloud`) and logs into its own Google account using `gcloud auth login --enable-gdrive-access --force`. This explicitly requests full `https://www.googleapis.com/auth/drive` access. Google CLI owns credentials and refresh; LocalBrain retains only the selected account identity and a short-lived memory-only access token. No app-owned OAuth Client, Client JSON or project creation is a setup prerequisite. Tokens/SDK credentials never enter the app database, logs or backups.

Local selected filesystem contexts are authoritative for their own managed publisher subtree. All regular files, hidden entries and structure are included, without collector or extension filtering. Remote selected publisher folders are authoritative for private received copies. Incremental sync compares content and metadata; rename/move does not imply retransferring identical bytes. Stop/deselect preserves copies. Outgoing confirmed source deletion uses Google Trash; incoming confirmed remote deletion/trash removes only tracked local copies. Access errors, missing permissions, incomplete inventories and size rejection are never deletion evidence.

The app cap is 100,000,000 bytes per file in both directions, inclusive. Check before content/hash on upload and before media request on download; bounded streaming enforces it even with inaccurate/missing metadata. Excluded files preserve prior copies, eligible peers continue and the job is partial, not fully current. No app aggregate quota or extension blacklist.

A private Drive SQLite database owns connections, selections, per-file identity/content checkpoints and cached operation results. Tokens are separate. Per-file verified completion survives interruption; no folder-wide atomic commit is claimed. Received copies live under `<data>/external-sources/google-drive/<connection-id>/<publisher-id>/`, directories0700/files0600, with no automatic Context registration, indexing or republishing.

Automatic execution defaults OFF. Upload defaults to360minutes, each publisher receive to1440. Choices:15,30,60,180,360,720,1440minutes. Compute wall-clock slots in the configured IANA timezone, midnight phase. Manual runs do not shift slots. Missed slots after sleep/restart wait for the next; no catch-up. Existing Session/Context schedules remain unchanged. Backend exit stops sync; hiding the native window or closing a browser does not itself exit the backend.

User-saved selection plus manual sync or auto enablement authorizes continued writes in that scope. No extra sharing-consent dialog, ACL management, synthetic permission probe or per-file approval is added. Page opening reads cached state only. OAuth, API, root access, last observation, last successful sync and next slot remain distinct. Actual errors carry an actionable sanitized message without guessed invitation/role causes.

### Google CLI Authentication And Distribution

Each PC installs [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk) and authorizes its own account with:

```bash
gcloud auth login --enable-gdrive-access --force
```

The Google-documented [Drive scope flow](https://docs.cloud.google.com/sdk/docs/authenticate#add_google_drive_to_your_scope) reuses the SDK's OAuth client. Creating a Cloud project or LocalBrain Desktop Client is not a prerequisite for this flow. A real API response can still require investigation of account, service or organization restrictions; do not automatically create a project or change Google permissions. The owner expressly approved this authentication route and its full `drive` scope, superseding the former readonly+drive.file/app-owned-Client design.

Google's grant covers all Drive files accessible to that account, including write operations; it is broader than the configured root. LocalBrain confines actual traversal, media and managed updates to the configured root and selected targets. Folder sharing/capabilities still determine whether a real operation is allowed. No added ACL, people/organization limit, share dialog or per-file approval is imposed.

The explicit **Save and check connection** action saves the destination, connects the existing gcloud login and browses the configured root in sequence without uploading. Saved destinations use **Check connection** to retry the same checks. First successful root verification reveals initial sync controls; previously selected/configured targets remain accessible after later errors. Only selected receive rows expose their run/schedule/result controls, and empty timestamps are omitted. The account field and **Google login** remain under **Account and login options**; separate auth/API/root observations remain in **Connection diagnostics**. Existing-login connection uses an explicitly supplied account, otherwise the already-bound account, or the current/unambiguous SDK account for a new connection. A different Google identity cannot replace an existing binding. It never opens a browser. Google login is a deliberate action that runs the approved command with `--no-activate`, `--quiet` and a pinned account when known; this leaves the SDK's globally active account and ADC unchanged. First login may bind the single newly registered account. Ambiguous account selection asks for the account field. The Drive API's user identity is checked before connection commit; another account cannot inherit a prior account's manifest or last success.

After connection, every token request specifies the pinned account with `gcloud auth print-access-token --account=...`. Changing gcloud's active account never switches an existing connection. The SDK owns persistent credentials and refresh. The app uses a brief memory cache, invalidates it after an actual401, and asks the SDK once more; failures preserve configuration/copies and never run browser login from a schedule. The app never reads/copies the SDK credential database, writes refresh tokens, calls `gcloud auth revoke` or updates ADC. Legacy app-Keychain records, if any, are not automatically deleted or used.

SDK discovery uses `LOCALBRAIN_GCLOUD_PATH` if explicitly configured; otherwise PATH and standard per-user/Homebrew locations, including GUI-app environments without shell initialization. No shell profile is sourced and no command string is passed to a shell. Private paths are not baked into builds. Each subprocess disables usage reporting, update checks, HTTP/file credential logging and inherited credential/impersonation overrides. Frozen-app Python/library paths are removed so gcloud selects its own supported runtime. Owned SDK processes use bounded timeouts and are cancelled on backend shutdown. Errors are sanitized; addresses, tokens and raw stderr are never copied into diagnostics.

Drive transport uses a scoped `truststore.SSLContext` on macOS with Python3.10+, retaining hostname/certificate verification and disabled redirects without global SSL injection. `truststore` is a base dependency for that platform, including browser-only installs. Other supported runtimes retain their default verified SSL context. The directly declared urllib3 dependency supports bounded connection reuse; its compatible release is resolved for each supported Python version. Certificate-validation failures have a distinct `tls` diagnostic and never request OAuth login or disable verification. No organizational certificate is bundled. [Truststore context API](https://truststore.readthedocs.io/en/stable/#user-guide).

Browser and native distributions use this same adapter and require an installed SDK. Builds contain no embedded Client JSON, personal account token, credential store or gcloud installation. Installer instructions belong in the bundled Settings guide; this policy and the developer guide own custom-path overrides and packaging checks. Normal Google login/consent and actual folder capabilities remain authoritative. [Login flags](https://docs.cloud.google.com/sdk/gcloud/reference/auth/login), [Token helper](https://docs.cloud.google.com/sdk/gcloud/reference/auth/print-access-token).

### Transfer And Recovery Details

The separate schema1 SQLite stores JSON values in `state` and per-item values in `items(namespace,key,value)`; every verified item checkpoint is transactional. Preallocated Drive IDs are saved before create, avoiding duplicate names after a lost response. Files up to5,000,000bytes use one multipart request for metadata and content; an already recorded matching resumable session is recovered instead. Larger files use resumable media. Generated IDs are fetched in batches of100; each assigned ID is checkpointed before mutation, and only a newly allocated ID skips an initial existence GET. Pending and completed identities still reconcile remote state. A lost multipart-create response is verified by that same ID and content hash/size before success, never duplicated by a blind create. Resumable upload session state is private and scoped to an immutable snapshot hash; interrupted or uncertain requests are queried with `Content-Range: bytes */size`. Fresh sessions send their first chunk directly; acknowledged ranges advance later chunks without an extra status probe each time. Three repeated non-advancing chunk acknowledgements stop with a diagnostic and retain the session for a later selected run. Expired sessions return to comparison on a later selected execution, rather than a duplicate blind create. Unchanged content can still require metadata updates. [Create IDs](https://developers.google.com/workspace/drive/api/guides/create-file), [Resumable uploads](https://developers.google.com/workspace/drive/api/guides/manage-uploads).

Before comparing a selected publisher source, known remote IDs from only the selected-source manifest are fetched with read-only [Drive batch metadata requests](https://developers.google.com/workspace/drive/api/guides/performance#batch_requests), up to100members per outer HTTPrequest. Root/target validation precedes this snapshot. Fixed GET subpaths/fields, Shared Drive flags, per-member resource keys, response Content-ID/file-ID validation and ordinary per-item permission/unavailable semantics are retained. The cache is consumed once; missing/invalid/unsupported batches fall back to individual reads rather than inferring absence. Transient/auth parts are individually revalidated. All mutations invalidate that ID's snapshot before recovery/integrity verification. This reduces connection round trips, not API quota units, and does not batch media or guarantee against concurrent edits after the observation.

Publishing has at most eight independent item workers within the existing single-job scheduler. Folder-depth barriers establish parents freshly in this run; failed/unverified parents block descendant writes and deletion of their old copies. Worker-local records are copied/checkpointed under a run lock before remote mutation and after verified steps. Failure of a folder-to-file replacement preserves prior descendants. Cancellation stops submission, settles owned workers and bypasses deletion. Token reads share per-account SDK single-flight without holding the process-lifecycle lock. No new concurrency setting or received-copy policy is introduced.

Each API instance owns a verified HTTP pool capped at eight connections, matching publisher concurrency. Standard HTTP(S) proxy discovery/bypass is retained; proxy credentials are scoped to the proxy and never copied to origin headers or diagnostics. Redirects, transport-level automatic retries, decoding and preloading are disabled. The existing API retries and known-ID/resumable recovery remain authoritative. Fully consumed responses release reusable connections; unread, truncated or failed responses close without unbounded draining and release pool capacity. Empty response bodies and accepted resumable statuses retain their headers and status semantics. Owned pools and concrete idle sockets are explicitly closed after identity verification, browsing and settled jobs, including error/cancellation. Injected openers remain injector-owned. This reduces connection setup; it does not combine originals or reduce Google's per-file operation count. [urllib3 pooling and streaming](https://urllib3.readthedocs.io/en/stable/advanced-usage.html).

A completed published item whose recorded ID becomes unavailable can be rebuilt as a new managed copy only under a freshly verified, non-trashed parent with explicit `canListChildren` and `canAddChildren` capabilities, after a complete parent listing contains neither the old ID nor a normalized same-name child. This is additive recovery of the local-authoritative copy, not evidence that the old object was deleted: the app never trashes the inaccessible old object or removes a local source through this branch. Permission/auth/network/listing failures and name/identity conflicts preserve the previous mapping. A replacement ID is allocated and checkpointed before create, with old session/hash/version state cleared; interrupted replacement creation retains its new pending ID for retry. Newly created parent listings are known empty at creation. A readable trashed folder is restored under its existing ID, and its descendants' pre-restore metadata snapshots are discarded before they reconcile. The configured shared root and own publishing target still require their ordinary access/position checks.

Repeat publishing continues to hash regular-file contents using the same bounded read and before/after source checks. A matching remote size/checksum avoids a staging write; changed content uses an immutable snapshot for upload. Identical manifest records do not trigger checkpoint transactions; changed IDs, mappings, sessions and verified completion remain durable before dependent work. File timestamps alone never establish content equality. Initial small-file transfers still use one media request per file on ordinary success; this optimization does not bundle originals into an archive or promise the minimum possible elapsed time.

A complete paginated metadata inventory is required before deletion reasoning. An item missing from a listing is checked by known ID; explicit Trash or a verified move outside the selected publisher is deletion evidence. A `404` or inaccessible parent alone preserves the copy, including when permanent deletion cannot be distinguished from permission loss. Google-native documents and shortcuts are reported as unsupported without automatic export or traversal. Duplicate case/Unicode-normalized paths and unsafe names fail rather than overwrite unrelated files. Existing unmanaged local files are preserved. Download staging is bounded, checksum/version checked and atomically replaces a file only after verification. Upload snapshots and known download temporary files are cleaned after use or backend recovery. No folder-wide atomicity or byte-level delta is promised.

The scheduler computes strictly future UTC instants matching local wall-clock boundaries, including DST gaps/folds. It records each dispatched slot, serializes jobs, skips an already-active job, queues independently due peers and recalculates on restart/sleep/time-zone or clock changes. Missed slots are not replayed. Backoff for transient read/update errors is bounded to four attempts; resumable media uses status queries after uncertain writes. Persistent errors are cached beside that job and do not spawn repeated browser windows.

### Validation Boundary

Injected Google transport and isolated local fixtures establish the app's state/transfer contracts. They cannot establish real Google permissions, live Google consent/account policies or recipient behavior. Installed-SDK/frozen-host checks and live two-account My Drive/Shared Drive validation must be recorded separately before calling those integration/release gates passed. Current delivery evidence belongs to Features0145–0150 and their Runs.

### Settings API Contract

All routes are under `/api/settings/google-drive`, behind the existing loopback/same-origin boundary and native per-launch authentication. The returned connection includes its private `gcloud_account` binding. `auth_mode` is `gcloud`, `auth_scope` is the full Drive scope, and `gcloud_ready`/`gcloud_message` describe local executable availability only; availability is not a successful Google login or folder-permission result. JSON bodies use the existing64KB Settings limit. No endpoint accepts arbitrary provider URLs, scopes or tool names.

| Method and suffix | Input | Result and effect |
| --- | --- | --- |
| GET (base) | none | Cached `connections`, filesystem `sources`, seven `intervals`, `max_file_bytes`, `timezone`, local SDK readiness, auth mode/scope and current worker. No CLI, Google call or token read. |
| POST `/connections` | `{url: fullFolderURL, target: folderName}` | New connection identity and independent namespace. Duplicate registered roots and unsafe names are rejected. |
| POST `/{connection}/connect` | Optional `account: string`, `login: boolean` (default false) | Existing-login verification binds a pinned account; `login:true` deliberately launches the approved gcloud/browser flow. Credentials never returned. |
| POST `/{connection}/browse` | none | Actual root metadata and completely paginated child publisher folders, excluding own target. Failure preserves cached choices/copies. |
| PATCH `/{connection}/jobs/{job}` | Both: `auto`, `interval`; receive: `selected`; upload: `sources: [integer Context ID]` | Validate and persist only supported fields. Upload selection derives from filesystem source IDs. Receive selection must reference a browsed publisher or existing saved job. A change cancels current work between operations and does not delete copies. |
| POST `/{connection}/jobs/{job}/run` | none | Start one selected manual job, or409 if another is active. No auto enablement or slot shift. |

Job keys are `upload` and `receive:<publisher-id>`. While an upload is running, `active.progress` provides transient stage, processed/total source-item counts, transferred/changed/excluded counts, latest worker relative path/byte acknowledgement, `active_items`, remote-batch response counts and `last_activity_at`. Progress is copied under the service lock and never persisted in manifests or credential logs. Processed items include folders, unchanged files and handled failures; this count is not a successful-transfer count. Activity advances on actual engine/API progress, not a polling heartbeat. Remote batch verification, scanning and post-transfer deletion checks are distinct phases; no ETA or time-based completion is inferred. Prior run totals are not displayed as current progress. Current worker cleanup clears progress; only the existing complete-result condition advances last success. Receive behavior remains unchanged.

Job observations distinguish `running`, `complete`, `partial`, `error`, `stopped` and `interrupted`; never-run jobs retain no success timestamp. `observed_at` is the latest result, `last_success` only advances on a fully completed run, and `next_slot` is shown only for selected automatic jobs. Reports carry actual `transferred`, structure/deletion `changed`, `excluded`, per-item `{path,message}` errors and the received destination. Cancelled/failed runs with unknown final counts do not invent zero counts. HTTP errors are sanitized; no raw Google body, authorization code or token is returned.

## Shared Descriptions At Removal

These complete source units retain their original qualifications and any
unchanged surrounding context. They are frozen excerpts, not additional
current owners for the remaining active topics.

### Former AGENTS.md

In scope:

- local Claude and Codex session ingestion
- user-managed Local Context sources
- work-grounded learning with reviewed source evidence and private review history
- Workstream, Thread, checkpoint, and resource organization
- local retrieval, reviewable Suggestions, and workflow insights
- approved read-only external source integration
- explicitly selected Google Drive sync under [its approved contract](#archived-google-drive-contract)

### Former AGENTS.md

Out of scope unless explicitly planned:

- other cloud sync or multi-user collaboration
- silent external writes or unreviewed relationship changes
- mandatory external AI or embedding services
- native macOS packaging before the local web workflow is validated

### Former docs/README.md

| Guide | Responsibility |
| --- | --- |
| [Getting Started](../../../src/localbrain/content/docs/getting-started.md) | Setup, first use, quitting and updates |
| [Settings](../../../src/localbrain/content/docs/settings.md) | Preferences, source registration, synchronization, backup and recovery |
| [Sessions](../../../src/localbrain/content/docs/sessions.md) | Conversations, projects, pins and Chart |
| [Sessions Dashboard](../../../src/localbrain/content/docs/sessions-dashboard.md) | Usage, cost estimates and coverage |
| [Local Contexts](../../../src/localbrain/content/docs/local-contexts.md) | Document sources, reading and format limits |
| [Search](../../../src/localbrain/content/docs/search.md) | Keyword/meaning search, Context Search answers, models and readiness |

### Former docs/README.md

- [Product Model](../../policies/project/product.md): product purpose, scope, terminology, source roles, and user-facing organization rules
- [Project Architecture](../../policies/project/architecture.md): stack, runtime boundaries, source adapters, storage model, and current capability ownership
- [macOS Installation And Local Storage](../../policies/project/installation-and-storage.md): installed wheel/archive setup, optional models, configurable private storage, updates, migration and cleanup
- [Local Natural Language Search](../../policies/project/natural-language-search.md): eligible sources, molecularization, model roles, query interpretation, ranking, refresh and evidence navigation
- [Context Search](#archived-context-search-contract): read-only folder questions, selectable4B/8B, shared-model/private-cache separation, evidence and transient dialogue
- [Source Claims And Work State](../../policies/project/source-claims-and-work-state.md): pure supplied-claim state projection and inferred provenance; not an admitted source extractor or map producer
- [Data Model](../../policies/project/data-model.md): complete effective SQLite map, global and subject ERDs, table/column catalogs, relationships, lifecycle, recovery, and delta maintenance ownership
- [Value Dictionaries](../../policies/project/data-model/value-dictionaries.md): generated subject map from physical and derived bounded values to complete presentation modes, labels, fallbacks, and consumer ownership
- [Schema Presentation](../../policies/project/schema-presentation.md): deterministic package manifest, source ownership, loader/failure behavior, and downstream Schema consumer contract
- [Google Drive Synchronization](#archived-google-drive-contract): selected directional sync, private state, Google CLI authentication and distribution/live-validation boundaries.
- [Privacy And Data Handling](../../policies/project/privacy-and-data.md): repository boundary, local persistence, external access, and disclosure constraints
- [Developer Guide](../../policies/project/developer-guide.md): source setup, development-web workflows, distribution builds, configuration, model-tool usage and verification
- [Markdown Rendering Contract](../../policies/project/markdown-rendering.md): shared syntax, trust, local-reference, highlighting, consumer, and fallback rules
- [Maintenance Task Runner](../../policies/operations/claude-task-runner.md): in-app Claude/Codex maintenance execution, retrieval, external-sync boundaries, persistence, and review behavior
- [Harness Policies](../../policies/harness): planning approval, execution routing, profiles, delegation, operator continuity, and traceability
- [Competence-First Delegation](../../policies/harness/competence-first-delegation.md): delegation admission, worker suitability, context transfer, fallback, and binding lifecycle
- [Operator Briefing And Review Receipts](../../policies/harness/operator-briefing-and-review-receipts.md): orientation, work-start, direction-change, review, block, and handoff continuity
- [Harness Improvement](../../policies/harness/harness-improvement.md): configured private stage experience, reusable improvement records, comparisons, and reviewed common export
- [Interaction Evaluation](../../policies/experience/interaction-evaluation.md): reusable interaction continuity and UX checks

### Former docs/policies/project/product.md

##### Transient Context Questions

[Context Search](#archived-context-search-contract) answers explicit questions over enabled Local Contexts and already received Drive copies using local4B/8B models and read-only tools. It is separate from Session/semantic search and needs no embedding preparation. Evidence stays inspectable; folder publishers do not automatically become document authors or contacts. Same-screen follow-ups are transient and clear on leaving, with no saved answer schema or automatic organizational change. Public model originals and app-private execution state have separate owners.

### Former docs/policies/project/product.md

The standalone test edition exposes Sessions, Sessions Dashboard, Local Context,
search, Context Search, first-run setup, categorized settings and bundled Docs. Its menu, HTTP and runtime
boundaries exclude Dashboard/learning, Workstreams, Auto Work, Atlassian, Insights,
Session workflow and Schema. The broader navigation below describes development
web. Both editions use the [common local settings contract](../../policies/project/desktop-app-and-settings.md),
model-free keyword search with explicit AI mode, and completion-based 10-minute
Session synchronization. The gear and ⌘, open the shared settings dialog.

### Former docs/policies/project/product.md

The standalone test app exposes Sessions, Sessions Dashboard, Local Contexts,
search, Context Search, settings, onboarding and bundled Docs. Its runtime boundary
excludes the other development surfaces; user settings cannot enable them.
The [desktop contract](../../policies/project/desktop-app-and-settings.md#runtime-and-product-boundary)
owns the exact admission and lifecycle rules. An ad-hoc test artifact is separate
from the normal-security signed/notarized public-release goal.

### Former docs/policies/project/product.md

Broad external ingestion/write-back, cloud sync beyond the approved selected
Drive contract, multi-user collaboration, mobile support, automatic semantic
linking across every source, and mandatory external AI/embedding APIs require
separate explicit planning. Existing approved CLI-backed analysis and read
integrations retain their narrower contracts.

### Former docs/policies/project/product.md

##### Selected Google Drive Transfer

[Google Drive synchronization](#archived-google-drive-contract) is managed in a separate Settings tab. User-selected local filesystem contexts publish into the configured root, and selected publisher folders receive into private external-source storage. The source is authoritative in each direction; stop preserves copies, while confirmed active-source deletion follows Drive Trash/outgoing and direct local removal/incoming rules. This transfer adds no model, search membership, organization-sharing controls or shared database replication.

### Former docs/policies/project/architecture.md

- Runtime: local web server with browser UI, or Tauri window with a bundled backend
- Backend: Python and FastAPI
- Database: SQLite
- Search: existing SQLite FTS5 plus optional local Qwen semantic ordering and lexical exact-identifier admission
- Optional Context Search package: isolated Qwen4B/8B native tool loop over admitted Local Context and received copies; request/page-memory dialogue, no embedding prerequisite or chat schema
- Frontend: server-rendered Jinja2 with small JSON API interactions
- External integration boundary: optional feature-specific adapters and approved authorization contracts
- Desktop packaging: Tauri 2 and a PyInstaller Python 3.11 bundle, Apple Silicon

### Former docs/policies/project/architecture.md

External integrations follow separate feature contracts. Optional
[Atlassian reads](../../policies/project/atlassian.md#external-access-foundation) use registered provider
dispatch contracts and an injected host-side read executor. The default
application leaves that executor unconnected; local URL registration, Browse and
evidence Sync remain available in development web without remote access.
[Google Drive](#archived-google-drive-contract) uses gcloud authentication and direct API
transfers in its separate synchronization path. Those transfers do not
automatically register, collect or index received files.

### Former docs/policies/project/architecture.md

#### Package Ownership

```text
localbrain/
├── main.py, cli.py, desktop.py       # public entrypoints
├── app/                             # application assembly and shared HTTP support
│   └── storage/                     # backup/restore and layout operations
├── foundation/                      # configuration, files, clocks, validation
├── persistence/                     # connection API, bootstrap and schema metadata
│   └── migrations/                  # schema history grouped by data owner
├── models/                          # asset installation, embedding and generation
├── references/                      # pure URL grammar, normalization and identity
├── ingest/                          # provider parsing, evidence and source synchronization
├── sources/                         # source registry/settings and sync services
├── sessions/                        # activity, queries, reading, pins, references, web
├── local_context/                   # document sources, queries, references, web
├── usage/                           # records, pricing, aggregation, web
├── resources/                       # resource identity/store and related-resource reads
├── rendering/                       # shared Markdown rendering
├── search/, natural_search/          # keyword/legacy search and optional AI search
├── context_search/, google_drive/    # existing separate feature packages
├── workstreams/, maintenance/        # organization/review and maintenance execution
├── workflow/, auto_work/             # workflow projections/correction and explicit previews
├── experiments/                     # context, reconstruction and claims experiments
├── insights/, learning/              # analysis and reviewed learning
└── atlassian/                       # catalog, evidence, access, sync, browse and web
```

### Former docs/policies/project/architecture.md

`maintenance/service.py` owns task/process tracking, ledger recovery, cancellation
and terminal state helpers; `maintenance/streams.py` owns shared runner output
decoding. Workstream preparation, commands and pending Suggestions belong to
`workstreams/runner.py`; approved external reads and atomic Atlassian result
application belong to `atlassian/runner.py`. Each feature submits its own execution
coroutine to Maintenance. Maintenance imports neither feature implementation.
The app connects Maintenance recovery/shutdown only when a Run-producing feature
is included, and calls those hooks only in the development web edition.
Auto Work cache maintenance, Context Search construction and Google Drive
construction/route registration are
also explicit contributions. Existing schema history, Run-to-Workstream FK and
Run display-name query remain database contracts; code detachment does not drop
their tables or delete private artifacts.

### Former docs/policies/project/architecture.md

| Current capability | Owning contract |
| --- | --- |
| Session collection, inventory, pins, Chart and direct evidence | [Session Ingestion](../../policies/project/session-ingestion.md) and [Sessions](../../policies/project/sessions.md) |
| Common preferences, source lifecycle, onboarding and native admission | [Desktop App And Settings](../../policies/project/desktop-app-and-settings.md) |
| Local keyword/semantic retrieval and grounded transient folder answers | [Natural-Language Search](../../policies/project/natural-language-search.md) and [Context Search](#archived-context-search-contract) |
| Selected directional publishing/receiving | [Google Drive Synchronization](#archived-google-drive-contract) |
| Frozen personal-improvement evidence, guide/report values and analysis accounting | [Personal Insights](../../policies/project/personal-insights.md) |
| Deterministic Episode Focus, user corrections and passive affinity inspection | [Session Workflow](../../policies/project/workflow.md) and [Auto Work](../../policies/project/auto-work.md) |
| Pure provisional candidates and separately bounded experimental contracts | [Candidates](../../policies/project/workstream-candidates.md), [Work Reconstruction](../../policies/project/work-reconstruction.md), [Work Context Inference](../../policies/project/work-context-inference.md), and [Source Claims](../../policies/project/source-claims-and-work-state.md) |
| Additive SQLite startup migrations over the local index | [Persistence Model](../../policies/project/architecture.md#persistence-model) |
| User-created Workstreams and nested Threads | [Product organization](../../policies/project/product.md#workstream-centered-organization) |
| Versioned checkpoints with linked-resource snapshots | [Product organization](../../policies/project/product.md#workstream-centered-organization) |
| Thread-first links to Sessions, Local Contexts, projects, local paths and external references | [Product organization](../../policies/project/product.md#workstream-centered-organization) |
| Workstream-level links for resources shared by multiple Threads | [Product organization](../../policies/project/product.md#workstream-centered-organization) |
| Manual Jira, Wiki, Slack, Git, document and generic URL references | [Product domain](../../policies/project/product.md#domain-boundaries) |
| Reversible keyword-based Session and Document link Suggestions | [Product Suggestions](../../policies/project/product.md#automatic-capture-explicit-organization) |
| Reviewed work-based learning article home, library and reader from explicit reviewed imports, with separate Workstream routes and Sessions Dashboard | [Learning Home](../../policies/project/product.md#learning-home) |
| Maintenance Session exclusion and source-neutral Claude/Codex subsession normalization | [Session Eligibility](../../policies/project/session-ingestion.md#session-eligibility) and [Session Policies](../../policies/project/session-ingestion.md#session-policies) |
| Source-neutral Claude/Codex Usage Records with immutable local trend-cost snapshots | [Usage Normalization And Repair](../../policies/project/usage-and-cost.md#usage-normalization-and-repair) |
| Reproducible Sessions Dashboard usage summary, GET scope and Daily/Weekly/Monthly token/cost history | [Analytical Read Models](../../policies/project/usage-and-cost.md#analytical-read-models) |
| All-time Session Insights use/reference Session ranking with durable source-backed evidence | [Session Insights](../../policies/project/personal-insights.md#session-insights) |
| Durable Maintenance Task Runner history, Claude/Codex external-sync parity, streaming result handling, cancellation and reviewable structured output | [Task Runner](../../policies/operations/claude-task-runner.md) |
| Deterministic SQLite/FTS5 retrieval without hard candidate or evidence-count caps | [Search and retrieval](../../policies/operations/claude-task-runner.md#local-retrieval-first) |
| Normalized many-to-many Thread resource matches with reusable fingerprints and deduplicated evidence | [Persistence Model](../../policies/project/architecture.md#persistence-model) and [Product Suggestions](../../policies/project/product.md#automatic-capture-explicit-organization) |
| Source browsing for folders, files and Apple Notes | [Local Context Sources](../../policies/project/local-context.md#local-context-sources) |
| Context-aware full Document reading with an owning FOLDERS tree, bounded non-FOLDERS fallback and source-preserving Markdown presentation | [Document reading](../../policies/project/local-context.md#local-context-sources) and [Markdown rendering](../../policies/project/markdown-rendering.md) |
| Safe Markdown conversation reading for visible Session/Subsession user and assistant messages without Local Context source guessing | [Session Conversation And Identity Reading](../../policies/project/sessions.md#session-conversation-and-identity-reading) |
| Atlassian stable source memory; bounded Session/Local Context URL evidence; strict zero-configuration local Site/Item admission; Site-first Explorer hierarchy with read-only canonical-URL container hints; grouped local search; Item detail, notes and Topic/Tag classification; exact Workstream/Thread links; explicit partial Space discovery and known-Item refresh previews without implicit remote ingestion or model calls | [Reference Evidence And Reconciliation](../../policies/project/session-ingestion.md#reference-evidence-and-reconciliation) and [External Access And Synchronization Constraints](../../policies/project/atlassian.md#external-access-and-synchronization-constraints) |

### Former docs/policies/project/architecture.md

External source dispatch and synchronization follow [Atlassian](../../policies/project/atlassian.md#external-access-and-synchronization-constraints) and the [Maintenance Task Runner](../../policies/operations/claude-task-runner.md). Approved selected Drive writes follow [Google Drive Synchronization](#archived-google-drive-contract).

### Former docs/policies/project/architecture.md

#### Google Drive Synchronization Boundary

The approved [Drive sync contract](#archived-google-drive-contract) adds explicit selected external writes. `google_drive/` owns the gcloud authentication adapter, separate private SQLite state, directional engines and backend-lifetime scheduler; `google_drive/web.py` exposes Settings-only local routes. The existing Session/Context collectors and clocks are unchanged. Fixed wall-clock jobs use one serialized worker, per-item verified checkpoints and cancellation between operations. The Drive synchronization path does not route OAuth or received material through a model, gateway executor, search index or automatic source registration. Separately approved [Context Search](#archived-context-search-contract) may read already received copies within its explicit source boundary. Opening Settings reads cached state; explicit root browse and selected manual/automatic jobs perform real API operations. Native loopback authentication and the existing local same-origin boundary still apply.

### Former docs/policies/project/desktop-app-and-settings.md

- The settings dialog is capped at 720 by 560px at the default scale and shrinks
  within the viewport. Its 160px desktop category rail becomes a horizontal row
  at 700px. Header/close stay visible; the content pane owns vertical scrolling.
  Switching categories reveals the new pane's top. Leaving the Session-source
  category closes its editor and discards unsaved inputs; general choices use autosave and
  stored-value recovery below. Errors scroll into view; general saves stay quiet.
  Geometry and typography follow the [Design Constitution](../../policies/design/design-constitution.md#dialogs-and-drawers).
- Startup is a dropdown ordered Sessions Dashboard, Sessions, Local Context,
  matching the sidebar. Ordering does not change the default/saved Sessions choice.
  Its menu opens directly below the displayed control, with matching width and
  a stable downward cue; selecting an item closes the menu.
- Time zone uses the same dropdown with exactly `UTC` and `Asia/Seoul` (KST).
  Display these literal names. There is no city search or expanded zone catalog.
  A previously stored different valid zone stays displayed and is preserved
  until explicitly replaced; it does not add a third selectable option.
- General dropdowns cap at 240px, shrinking within
  narrow panes. Menus match their trigger width and open below it. Desktop form
  fields and action buttons share the 32px control height and centered action
  labels; narrow panes use 40px touch controls. Helper text retains its wider
  reading measure. Source tool/name columns share equal control dimensions;
  source tool and Context kind reuse the below-trigger selector and keyboard
  behavior. Existing source identity locks the tool in Edit.
- Context and storage use compact grouped information rows, consistent headings,
  path type and secondary metadata. Model download/status stays in one quiet
  group; preparation requires an installed model, cancellation appears during
  downloading/preparation, and an already disabled AI search cannot be disabled
  again. Model storage details and backup restoration use disclosures. All model
  actions and backup/restore/cache operations retain explicit invocation and
  existing consequences; collapsed restore still requires its ZIP and replacement
  confirmation. Browsing settings never downloads a model. When Context Search
  is included in application assembly, Search Model also
  offers pinned4B/8B answer-model cards with independent public-cache connection,
  installation verification and cancellable worker status; generation-model
  setup never prepares the embedding index. [Context Search](#archived-context-search-contract)
  owns the separate selector, read-only tools and transient dialogue surface.
- There is no project-display dropdown, display-root list or root-add action.
  Sessions, Chart, Dashboard, Context and read-only settings path labels use the
  common home formatter. Path editing/selection retains the actual registered
  value; source registration remains independent of display. A workspace at
  `~/Projects` displays `~/Projects` rather than `.`. No historical Usage
  reassignment is performed. Dashboard Project
  composition includes work Sessions and work subsessions; it excludes all analysis
  and Maintenance records from rows, total and shares. Overall usage/history and
  Source/Model keep their usage. Preserve By Project / Project labels, Git/folder
  grouping including home, unknown-work `프로젝트 미지정`, and hidden desktop Insights.
  The [Usage contract](../../policies/project/data-model/usage-and-cost-records.md#usage_records) owns membership.
- Keyboard users can open, navigate and choose an option; Escape dismisses
  without changing the value. Only one menu opens at a time. Dismiss on outside
  interaction, tab change and dialog close; keep the trigger and menu visible
  within the settings scroll area. General options persist on confirmed selection;
  highlighting, Escape and selecting the current value do not save. Source forms
  retain explicit Save. General saves patch only the selected field
  with the existing revision; Sync uses that same autosave/readback boundary.
  Turning either source schedule off preserves its interval.
  General help says only `설정은 이 Mac에 저장됩니다.`; no override explanation or
  saved-versus-applied value rows are shown.
- General choices briefly disable during one local write so requests do not race.
  Closing does not cancel the write; reopening waits before loading preferences.
  Success is quiet, with no Save button, success notice or forced page reload.
  Failed saves reread the file: use actual stored values, confirm an ambiguous
  successful write by value, otherwise show a retryable error. If readback fails,
  disable choices until a successful settings reload. Preserve concurrent edits
  and unknown settings. Keep time-zone impact help without application-timing
  notices; startup still applies on next launch and time zone on the next view.
- The time-zone preference controls Session/activity/conversation timestamps,
  Session chart date labels and the Sessions Dashboard's
  local date range and day/week/month grouping. Crossing a date boundary can
  change which period contains a usage record. It does not rewrite original
  timestamps, Usage facts or source attribution, change the Mac clock, or change
  the saved elapsed synchronization interval. Page displays apply on the
  next navigation/reload; startup choice still applies on app relaunch.

### Former docs/policies/project/desktop-app-and-settings.md

- Settings order is General, Session sources, Local Context, Search model, Sync,
  Storage, About. An included Google Drive package adds its category before
  Storage. General contains startup/timezone. Source categories own which
  locations to read; Sync owns when. Storage remains a separate category.
- Sync contains Session and Local Context groups. Each has one content-sized dropdown (about 79px at the default scale):
  10/20/30/60 minutes, then Off. Off saves only enabled=false, preserving the interval
  and imported records. Choosing minutes atomically saves enabled=true and the
  interval for that group. Each selection autosaves; the other group is unchanged.
  Existing valid custom intervals remain displayed until explicitly replaced;
  integer 10–1440 validation remains compatible. No timestamp/history card,
  manual settings button, range/runtime help or AI-index placeholder is shown.
- Session defaults/saved values remain; Context defaults to enabled every 30
  minutes. Missing fields use defaults without rewriting an existing file.
  Both app and web backend run the same services while alive. Each next run is
  measured from its own completion. Sleep/restart coalesces overdue work, not a
  replay of missed intervals. Empty registries do not start collection.
- Collect only enabled registered sources through existing adapters. Context
  reuses folder/file/Apple Notes scope and macOS permission boundaries. Originals
  stay read-only. Neither schedule changes originals, refreshes Git or external
  services, or starts an agent task. Folder/file scans reuse unchanged entries;
  Notes retains its existing snapshot reader. One local writer lock excludes
  concurrent collection/settings/recovery writers across domains and backends.
  A busy writer retains one pending manual request until its own domain completion
  satisfies it. Context cancellation rolls back its transaction; directory/note
  iteration checks cancellation and the Notes reader subprocess is stopped on exit.
- Health files retain the latest separate outcomes; source/file/root health stays
  in the existing DB tables. Failed collection preserves imported records and the
  latest successful collection time. No new data root or DB schema. AI-index
  scheduling has no independent controls; enabled search still observes normalized DB
  changes and does not download a model implicitly.
- The common shell has no sync-status strip or updated-records link. Sessions
  retains its manual sync button and running state. Background completion preserves
  the current page, filters, focus and scroll; navigation/reload displays new data.

### Former docs/policies/project/desktop-app-and-settings.md

- Common web execution and the Tauri app use the same settings and periodic sync.
  Closing a browser does not stop its independent server; stopping that server
  stops scheduling. The packaged app owns its backend, closes windows without
  quitting, and shuts down the backend on explicit app quit.
- The packaged edition exposes Sessions, Sessions Dashboard, Context, search,
  onboarding, settings and bundled Docs. Dashboard/learning, Workstreams, Auto Work, Atlassian,
  Insights, Session workflow and Schema cannot be enabled by user settings or
  direct HTTP access. The normal development web edition keeps its other routes.
  Optional Context Search and Google Drive routes, settings and lifetime services
  are installed only when selected in application assembly. The default delivery
  set is shared by both editions; [feature availability](../project/feature-availability.md)
  owns temporary suspension and resumption decisions. Exclusion preserves stored
  data and model files and is not a user preference.
- The desktop server binds loopback on an available port, authenticates its
  window with a per-launch secret and rejects cross-origin mutations. Native
  commands expose only explicit path selection and approved app actions.
- The initial `tauri://localhost` → loopback handshake sets an HttpOnly,
  `SameSite=Lax` session cookie before redirecting to the saved start page.
  `Strict` prevents WKWebView from sending that cookie on this initial
  cross-scheme top-level redirect. Lax preserves the first GET while token,
  loopback and mutation-origin checks remain required. The handshake is not
  cached and sends no referrer; boundary JSON errors explicitly declare UTF-8.
- No autostart, background daemon, other cloud sync, app encryption, paid signing or
  automatic updater is introduced. Approved selected Google Drive synchronization follows its [separate contract](#archived-google-drive-contract). Program ZIPs contain no personal runtime data.
- Frozen Python installation metadata resolves against the running bundled
  interpreter prefix. Build-time user-home and checkout paths must not remain
  in shipped metadata, including compressed Python constants. Packaging checks
  raw files and compressed Python/stdlib archives before creating the ZIP.
  This does not change application data/settings ownership under each user's home.
- On macOS/Python 3.10+, the dedicated UI model-download worker uses the OS trust
  store through truststore, while retaining TLS certificate verification. This
  honors locally trusted managed-network certificates without bundling a company
  certificate or disabling HTTPS checks. The worker owns the early application-level
  initialization recommended by [truststore](https://truststore.readthedocs.io/en/stable/).
  A parent-lifetime pipe ends the download worker if the backend exits or crashes.

### Former docs/policies/project/desktop-app-and-settings.md

#### Google Drive Settings

When the Google Drive package is included in application assembly, its independent tab follows the [Drive contract](#archived-google-drive-contract). It does not merge Drive management into Local Context registration. The backend owns fixed wall-clock jobs until Quit/server exit; window hiding does not stop them. Local SDK readiness, Google authentication, API/root observations and per-job success/next slot remain distinct. Explicit save/check reuses the SDK login then checks the root; initial sync controls appear after root verification, and selected targets reveal schedules/actions. Account/login options and detailed observations remain in disclosures. A later access failure preserves configured controls. Drive transport uses the system trust store on macOS with Python 3.10+, and the default SSL context on other runtimes; HTTPS verification stays enabled and certificate errors remain distinct from OAuth login errors.

### Former docs/policies/project/installation-and-storage.md

Keep the extras required by that installation; omit `--extra local-models` for a
base-only checkout. With the base dependencies installed, also check
`uv run --no-sync python -c 'import urllib3'` for the original warning; urllib3
is a base dependency for Drive transport. If the managed interpreter and locked distributions are
already cached, skip the Python download and add
`--no-python-downloads --offline` to `uv sync`. For a separately installed app,
repeat its selected wheel/archive installation with `--python 3.11` and the same
extras instead of editing a checkout's `.venv`.

### Former docs/policies/project/installation-and-storage.md

| Feature | Local model requirement | Asset download |
| --- | --- | --- |
| Session ingestion, reading, keyword search, deterministic views | None | None |
| Natural-language Session / Local Context search | Qwen3-Embedding-0.6B | Same shared asset as affinity |
| Prepared full-history affinity map | Qwen3-Embedding-0.6B | About 1.21 GB |
| Context Search read-only folder questions | Qwen3-4B or Qwen3-8B | About8.06GB or16.40GB; reuse existing shared assets |
| Explicit experimental context trials | Qwen3-4B or Qwen3-8B | About 8.06 GB or 16.40 GB |

### Former docs/policies/project/installation-and-storage.md

Qwen3-Embedding-0.6B is the document/query encoder used by natural search.
The4B/8B generation models also power explicitly submitted Context Search questions;
installing them does not enable an LLM on ordinary app startup or an automatic workflow producer.
Settings → Search Model offers installation/verification for both. Public originals
remain in the resolved shared Hub cache, including `~/.cache/huggingface/hub` by
default. App-owned registration manifests stay under data/models; Context Search
kernel caches belong under cache/context-search. No prompt/answer file or private
weight fine-tuning is created. Complete public caches can be registered locally
without downloading; status checks are presence checks, while use verifies integrity.
See [Context Search](#archived-context-search-contract) for scope and ephemeral conversation contracts.
Claude/Codex-backed actions have their own CLI/authentication requirements and
explicit external-service boundary; installing local models does not satisfy
those requirements.

### Former docs/policies/project/installation-and-storage.md

#### Google Drive Storage

[Google Drive synchronization](#archived-google-drive-contract) stores private configuration, selections, cached results and per-file checkpoints in `<data>/google-drive/sync.sqlite3` (schema1). Google Cloud CLI owns credentials and refresh; access tokens are memory-only in LocalBrain. Received copies are `<data>/external-sources/google-drive/<connection-id>/<publisher-id>/`; directories0700/files0600. `<data>/google-drive/staging/` holds bounded immutable upload snapshots, removed after use and recovered on backend restart. Download staging uses private sibling files and atomic replacement. Built-in backup/restore does not include these connection/copy/checkpoint trees or gcloud credentials; restoring ordinary app settings does not restore or revoke Google access. Users may back up received files separately. Do not classify these copies or the sync database as rebuildable cache, publish them or implicitly index them.

### Former docs/policies/project/installation-and-storage.md

Ordinary startup does not make a database backup or persistent server log.
Schema migrations can create a recovery copy before a structural change.
Following a successful committed initialization, current migration contracts
and SQLite integrity are checked before retirement: at most the newest eligible
copy is kept, for seven days. Failed initialization, uncertain ownership, open
files, symlinks, hard links, or nonempty backup WALs preserve recovery copies.
The numeric Session-revision migration uses
`<database>-pre-session-revision-v1.bak` under this same lifecycle.
This policy covers only enumerated LocalBrain migration suffixes. Arbitrary
manual backups and unrelated files are never discovered for automatic deletion.
The automatic check runs during successful DB initialization, not on an
independent seven-day timer. A continuously running backend does not delete a
copy merely because its age crosses seven days; the next successful
initialization or an explicit eligible cleanup performs retirement.

### Former docs/policies/project/privacy-and-data.md

##### Transient Questions And Reviewed Learning

Context Search follows its [source and transient-dialogue contract](#archived-context-search-contract): explicit questions may read enabled Local Context and already received Drive copies through bounded read-only tools. Public originals remain in the shared Hub; app metadata and compiler/kernel caches have separate private owners. No answer table, transcript file or browser persistence is created. Conversation clears on screen/tab leave, and isolated inference network blocking never changes web/Drive networking. This scoped bridge does not admit all application data into ordinary indexing.

Reviewed learning lessons, source snapshots, answer/confidence/self-assessment
history and visibility choices are durable private DB content. Importing a local
packet does not send it elsewhere or train a model. Learning routes make no
external calls; an official-source link opens only by explicit user navigation
with referrer suppression. Private lesson packets and captures stay outside Git.

### Former docs/policies/project/privacy-and-data.md

- External systems must be accessed only through capabilities approved for the selected integration.
- Atlassian external integration begins read-only. Approved Google Drive synchronization has the separate selected read/write contract below.
- Local Source Instance records may store a stable local key, provider/service identity, display name, and a shape-validated Gateway alias or canonical Atlassian Cloud ID, but never arbitrary opaque values, site URLs, credentials, access tokens, sampled content, or raw connector payloads.
- Capability observations retain only versioned logical-operation names, a schema fingerprint, availability, timestamps, invalidation, and bounded error evidence. They are refreshed explicitly rather than on startup, page load, search, or ordinary preview.
- A version-controlled allowlist must map logical reads to exact provider targets and validate bounded arguments before dispatch. Runtime rows, model output, prompts, or caller-supplied tool names cannot grant external writes.
- The external-sync maintenance path requires a host-side executor that receives only a pre-authorized dispatch. Provider arguments and returned content stay in private Run artifacts; query projections and call-accounting rows contain no arguments or provider content. Claude or Codex receives only the validated local evidence and cannot access broad external tools in that Run.
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
- Source-neutral Session reference evidence is private, source-derived runtime data with retained historical reference identity. It may retain an eligible primary work Session and source path, event/line/ordinal locator, opaque grouping key, shared resource FK independent of Document or Atlassian registration rows, bounded observed issue/file/host-path identity, safe normalized HTTP(S) destination, approved tool name/call identity, completed success/failure outcome, extractor fingerprints, counts, and bounded diagnostics. Visible generic URLs discard credentials, fragments, and all query material. The shared static Atlassian locator may inspect only its bounded family-specific query allowlist ephemerally, then retain a canonical safe locator containing only the identity projection needed to distinguish the reference. Jira Issue query identity canonicalizes to a query-free `/browse/{ISSUE_KEY}` path. A Confluence Page keeps its valid Space/Page path when available; otherwise it may retain only canonical positive `pageId` on `pages/viewpage.action`. RapidBoard may retain canonical positive `rapidView` plus one validated `projectKey` grouping hint; Filter and Dashboard may retain only canonical positive `filter` or `selectPageId`. It never retains raw query, JQL, arbitrary filter text, tokens, or unrelated parameters. Semantic Session grouping excludes locator spelling and container hint. Approved Atlassian calls correlate only bounded call/result identity fields and never initiate a provider request. It must not retain message excerpts, credentials, URL fragments, unapproved query material, opaque arguments/results, remote content, Maintenance content, or Subsession content. Reconciliation may delete only these source-derived evidence rows; shared Resources, Documents, remote facts, notes, classifications, and organization links remain separate owners. Removing a Document binding or optional Atlassian registration does not cascade into Session evidence; the [Session reference contract](../../policies/project/data-model/workspace-and-session-activity.md#session_reference_evidence) owns reconciliation and retained-evidence lifecycle.
- Atlassian browse, Add orientation, URL preview and registration, access setup,
  search, detail reading, local classification, local relationship edits, local
  evidence Sync, and refresh preview use only persisted local state and explicitly
  supplied, locally validated action inputs. They must not send a query, result, or local content to Atlassian or an AI service. Strict
  Jira Issue or Confluence Page recognition may create a local Site, Item, URL,
  and evidence rows during Sync, but never a binding, credential, Source
  Instance, remote fact, or persisted Space inference. Each source is atomic;
  a failed source publishes neither partial rows nor a resolver-cache identity
  for later sources. Local evidence Sync receipts contain only bounded counts,
  fixed reason codes, source kind, and local numeric ID; they remain
  process-local, expire, and are never persisted. Provider is never inferred
  from URL content; credentials and tokens are never accepted. Invalid input or
  failed local setup creates no partial rows and triggers no remote lookup. The
  [Atlassian product flow](../../policies/project/atlassian.md#atlassian-explorer-add-connections-sync-and-refresh)
  owns the user-visible flow, and [Atlassian access constraints](../../policies/project/atlassian.md#external-access-and-synchronization-constraints)
  owns request limits, dispatch, and transaction boundaries.
- Connected candidate discovery and refresh require explicit submission through an authorized Source Instance. Candidate results and per-target manifests are private runtime evidence, never authorize automatic bulk registration, and must not imply complete company-wide enumeration.
- Validated remote results may update only their approved remote-state and content owners. They must not overwrite local attention, notes, Topics, Tags, Workstream/Thread relations, or other user-owned organization state.
- Reference coverage rejects remote metadata and body persistence; metadata coverage rejects bodies. Explicitly downgrading indexed coverage removes the stored body and rebuilds the remaining eligible identity/local FTS roles, while ordinary failure or unavailability never performs that destructive downgrade.
- Due timestamps are local advisory state and perform no external or model call. Failed, unavailable, and not-found checks retain last-known content and local organization until an explicit destructive local action.
- External writes require a visible preview, attribution, and explicit user confirmation unless a separately approved integration defines persistent selection as authorization. Google Drive synchronization uses the owner-approved [Drive contract](#archived-google-drive-contract): saved destination and targets plus manual run or automatic enablement authorize subsequent sync within that scope, without repeated sharing or per-file approval. Other integration write boundaries remain unchanged.
- Local content must not be sent to an unapproved AI, embedding service, website, repository, or person.
- Generated summaries must preserve provenance and must not present inference as confirmed fact.
- Connector failures, stale content, and inaccessible sources must remain visible rather than being represented as current data.

### Former docs/policies/project/developer-guide.md

Outputs are `dist/LocalBrain-apple-silicon.zip`, its matching `.sha256`, and the
unpacked app folder. The build includes the source package and execution
libraries without copying private runtime folders or shared public model weights.
The [desktop runtime contract](../../policies/project/desktop-app-and-settings.md#runtime-and-product-boundary)
owns bundled Python path resolution and rejection of private build paths,
including compressed Python code. Data and settings stay under each user's home.
Rust compilation also remaps builder-home, checkout and temporary paths while
preserving configured compiler flags. The resulting app is scanned before ZIP
creation; a detected private path fails the build rather than producing a new archive.
The [test distribution guide](../../policies/project/standalone-test-app-guide.md) owns first launch,
supported-environment evidence, manual replacement and recipient validation.
Uploading the program ZIP to internal Drive and notifying teammates are separate
delivery actions.

### Former docs/policies/project/developer-guide.md — Configuration

For a custom `LOCALBRAIN_DATA_DIR`, unspecified cache/development locations are sibling directories named `<data-name>-cache` and `<data-name>-development`. Explicit variables override those defaults. Stop the app before moving existing state; use [the storage migration guide](../../policies/project/installation-and-storage.md#upgrade-an-existing-storage-layout).

### Former docs/policies/project/developer-guide.md

#### Google Drive Development

Use [Google CLI authentication and distribution](#google-cli-authentication-and-distribution) for the approved gcloud/full-Drive authentication flow, pinned accounts, SDK credential ownership and live validation boundaries. Run `uv run python -m unittest discover -s tests -p 'test_google_drive*.py' -v` for synthetic sync/transport/scheduler and SDK subprocess tests. These tests use synthetic executable helpers, do not launch real Google login and do not upload developer Contexts or use a real Google account.

Transport tests also own an ephemeral loopback-only HTTP/1.1 server for connection reuse, the eight-connection ceiling, streamed-response cleanup, status/retry and lifecycle checks. It never uses real Google credentials or files and is closed after the test class. Install the base dependencies from the current lock: urllib3 is directly declared for Drive pooling, with a compatible version resolved across the supported Python range. A full suite still does not establish live Google body-transfer timing or native/recipient behavior.

### Former docs/policies/project/data-model.md

#### Google Drive Private State

Drive synchronization uses a separate schema1 SQLite under the app data root; it does not add source documents to the main database. `state(key,value)` owns connection/job selections and cached observations; `items(namespace,key,value)` owns per-file logical identity, relative path, remote ID, checksum/version and incomplete upload state. Google Cloud CLI owns OAuth credentials; the app stores only a pinned account identity and keeps short-lived access tokens in memory. See [Drive ownership and lifecycle](#archived-google-drive-contract). Received files are filesystem copies without automatic Context or search membership.

### Former docs/policies/project/app-documentation.md

#### Google CLI Setup Links

The Settings guide includes authored links to the official Google Cloud CLI installation and authentication guides because Drive connections depend on that installed CLI. These open only by user choice, do not preload remote content or carry account data, and do not add source registration, indexing or model work. The six guide routes remain fixed.

### Former docs/policies/project/markdown-rendering.md

- Consumers pass authoritative text to `render_markdown` and render only its trusted result.
- Reviewed learning articles are a consumer of this shared renderer. Each article's intro, section bodies and takeaway remain authoritative private packet text; their HTML is ephemeral and uses no local-reference context.
- Context Search renders transient generated answer text through this same renderer, without local-reference authority. Active HTML remains escaped and images deferred; evidence excerpts use plain text. It creates no answer record or page-local Markdown parser.
- Visible readers use the shared `.markdown-body` semantic class for prose, headings, code, tables, callouts, footnotes, math, references, embeds, and deferred states; page containers own only composition and scrolling.
- The renderer owns a non-semantic table scroll wrapper so tables retain native table layout, fill the available reading width, and overflow locally when their minimum column geometry exceeds it.
- Shared presentation bounds generated MathML and CommonMark indented code blocks inside the owning reading container. Wide technical content scrolls locally and never widens the outer page.
- Consumers may provide page-owned empty or failure copy from the returned state, but they must not reparse the output or mark source text as trusted.
- Consumer CSS may style shared semantic classes under the Design Constitution but must not change syntax, trust, source, or fallback meaning.
- Unsupported syntax stays safe and understandable until an approved extension adds it to this allowlist.

### Former docs/policies/project/development/session-simulation.md

The following table describes simulation and work-reconstruction experiments. [Context Search](#archived-context-search-contract) separately admits local4B/8B read-only questions; that approval does not admit a rejected work extractor or reconstruction producer. The experimental model roles remain separate:

| Model | Current purpose | Consumer/admission boundary |
| --- | --- | --- |
| Qwen3-Embedding-0.6B | Encode source chunks for similarity-based grouping | Prepared embeddings feed the observation-only map; browsing runs no model |
| Qwen3-4B | Explicit quoted work-context and relationship inference baseline | Synthetic-only quoted trials; no admitted map or private-history reconstruction consumer |
| Qwen3-8B | Explicit quoted work-context, protocol and source-claim diagnostics | No admitted work extractor/reconstruction producer or generative map |

These are pretrained models, not locally trained weights or LoRA adapters.
The installed 4B/8B assets are reusable independently of the embedding cache and
expiring evaluation reports. The commands below are explicit tools, not an
automatic pipeline for newly imported Sessions.

The command reference in this frozen excerpt refers to the unchanged procedures
in [Session Simulation Operations](../../policies/project/development/session-simulation.md#operations);
those independent procedures are not repeated here.

### Former docs/policies/design/design-constitution.md

The persistent navigation has three groups and ten stable destinations:

- **Overview:** Dashboard, Sessions Dashboard, Context Search
- **Workspace:** 자동 작업, Workstreams, Sessions, Atlassian, Local Contexts
- **System:** Sources, Schema

## Planning Descriptions At Removal

These frozen planning excerpts record the earlier feature position; the current
index and roadmap now use the suspension boundary above. Other table rows and
list members remain here only to preserve the original shared context.

### Former docs/plans/README.md

| Boundary | Current position and next review |
| --- | --- |
| [Context Search](../prd/prd-0026-context-search-grounded-local-answers.md) | Approved bounded delivery and native integration are implemented; broader model quality, native recipient and release evidence remain separate. |
| [Google Drive](../prd/prd-0025-google-drive-connection-and-incremental-sync.md) | Approved Features 0145–0150 and gcloud revision are implemented; final two-account My Drive/Shared Drive acceptance remains open. |
| [In-app Docs](../prd/prd-0024-deployed-app-docs.md) | Six English guides are delivered; PRD remains in-loop for human acceptance. Native recipient execution is separate. |
| [Code/command learning](../prd/prd-0023-code-and-command-learning.md) | Reviewed manual reader is implemented; required functional transitions remain untested and block formal pass. Automatic discovery, official updates and generation are not running. |
| [Work-grounded learning](../prd/prd-0022-work-grounded-learning-dashboard.md) | Pilot returned to planning for the code/command successor; preserved contracts are reused and the earlier functional gap remains open. Learning benefit is unproven. |
| [Standalone test app](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md) | Local implementation is complete; final native/recipient acceptance remains blocked. Signed/notarized public release is separate from the ad-hoc test ZIP. |
| [Natural-language search](../prd/prd-0020-local-natural-language-search.md) | Approved local baseline is implemented; additional tuning depends on observed burden. Quality evidence retains its recorded source/hardware/holdout limits. |
| [Observed Sessions Chart](../prd/prd-0019-observed-session-chart.md) | First-phase documentation/verification closeout is complete; physical wheel-gesture evidence remains unverified. Relationship proposals need separate approval. |
| [Workflow reconstruction and map](../prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md) | Owner-paused after continuous-map inspection. [Design handoff](../design/workflow-map-design-plan.md#handoff-to-next-track) owns resumption; failed extraction trials are not queued to restart. |
| [Workflow/skill intelligence](../prd/prd-0005-workflow-and-skill-intelligence.md) | Approved for later proposals; bounded skill ranking passed. The analyzer has its own PRD below. |
| [Personal improvement](../prd/prd-0018-personal-ai-use-improvement-insights.md) | First analysis-only Run increment and corrections are delivered; actual intervention benefit and later review-state features remain open. [Backlog](../project/backlog.md#personal-improvement-insights) owns follow-up. |
| [Atlassian UI reconciliation](../prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md) | Current child Features are passed; the approved incremental boundary remains open for later owner observations. |

### Former docs/plans/project/roadmap.md

Exit criteria:

- a Workstream can move between Claude and Codex with source links intact
- end-of-session state can be recorded in under a minute
- every external write is previewed, attributable, and explicitly approved. The separately approved [selected Drive synchronization](#archived-google-drive-contract) uses saved destinations/targets plus manual run or automatic enablement as continuing authorization; actual Google authentication/permissions still apply, and other integrations retain the general gate.

### Former docs/plans/project/roadmap.md

Deferred beyond that boundary:

- broad MCP integration
- automatic semantic linking across every source
- external write-back
- other cloud sync and collaboration; selected Drive synchronization follows its separately approved contract
- mobile support
- complex graph editing
- mandatory external AI or embedding APIs
- broader packaging and identified distribution beyond the approved three-area test app
