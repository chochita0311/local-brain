# macOS Installation And Local Storage

## Supported Installation

The initial trial installation is **Git checkout → coding agent → local native
build and installation → app launch**. Use [Agent-Assisted Local Build](#agent-assisted-local-build)
below. This source installer needs build tools. The current native build is
Apple Silicon macOS only; planned Windows x86_64 support remains unimplemented
and unverified until its port and actual Windows checks are complete.

LocalBrain also offers an Apple Silicon standalone test artifact and a native
web/CLI bundle. The `.app` contains Tauri, the Rust backend and the independent
Terminal payload. A finished app or web bundle runs without Python, development
tools or a source checkout. Public model weights remain explicit optional
downloads. The [test app guide](standalone-test-app-guide.md) owns ad-hoc signing,
first launch, supported-environment evidence and manual updates; the
[settings contract](desktop-app-and-settings.md) owns preferences, source lifecycle
and restart-only same-Mac recovery.

The web edition can start with an empty database. Local models and authenticated
CLI integrations have separate optional prerequisites. Cargo lockfiles freeze
native dependencies, and desktop/Terminal Node lockfiles freeze their packages.
Dependency upgrades must repeat native startup, route/template and delivered
artifact checks before changing those locks. Python is a standard-library
repository build/check tool; the product and native model execution need no
Python research environment or optional Python model dependencies.

### Agent-Assisted Local Build

Clone the repository or update an existing checkout, open that folder in your
coding agent, and use the request in the [README](../../../README.md#install-from-source-with-an-agent).
The agent follows the repository's existing native build commands rather than
starting the broader development web edition as the installed trial app.

| Stage | Expected action and result |
| --- | --- |
| Check the checkout | Identify the intended source revision and local changes. Preserve unrelated edits when updating; report dirty source as such. A pull does not replace or update a frozen app. |
| Prepare tools | On Apple Silicon macOS, check Git, Python3.11+ for build/check scripts, Xcode Command Line Tools, Rust/Cargo1.90+ and Node/npm. Cargo must be available in the build shell. Install missing prerequisites as needed; an OS installer or permission prompt may need user participation. |
| Build | Use [Build The macOS App](developer-guide.md#build-the-macos-app) and its frozen dependencies. Build the native app, including the Rust backend and native optional-model execution code, without downloading model weights or collecting personal sources. |
| Install and launch | Fully quit an existing LocalBrain before replacing it. Open the generated `LocalBrain.app`; the existing output can run from its build folder or be placed in Applications. Record the actual app location and verify that the native app, rather than a separately running development server, launched. |
| Check first use | Open Docs/settings, connect sources explicitly, synchronize and open a Session, and try model-free keyword search. Model download/index preparation stays an explicit optional action. Keep successful build, native launch and a usable first task as separate results. |
| Report | Give the source revision/dirty state, OS/architecture, app version/location, actual build/installation/launch results and anything unverified. BUILD-INFO records the source commit, dirty state and a SHA256 fingerprint of explicit app/build inputs; it rejects inputs changed during packaging. Report actual native launch separately. |

Build environments, dependency downloads and outputs need space in addition to
the running app's storage. The checkout's optional build/test environment, `apps/desktop/node_modules`, Cargo
target and `dist` are build/install inputs or outputs, not the user's database,
settings or search index. Keep private runtime state under its
[storage owners](#storage-ownership-and-configuration). Shared public model
weights also remain separate; building optional-model execution code is not permission
to download a model. Settings storage totals do not include all build-tool caches.

For updates, quit the app and any separate backend using the same data, preserve
local changes while updating to the chosen source revision, then repeat the
build and app replacement. Retain the database, settings, originals and public
model cache. Reopen and check the same installation's sources and records.
Neither `git pull` nor a development-server reload replaces the frozen backend.

The current builder uses ad-hoc signing and does not submit the app to Apple.
Paid Developer Program enrollment and notarization are not prerequisites for
this local-build trial. This does not establish the normal-security acceptance
of a future downloadable public binary; its
[separate release goal](../../plans/prd/prd-0021-macos-standalone-test-app-and-local-settings.md#public-distribution-goal--2026-10-20)
and the test artifact's launch/evidence limits remain in force.

For Windows, keep the [expected paths and later checks](../../plans/research/early-access-distribution-readiness.md#windows-expected-paths-and-storage--not-implemented-or-verified)
as preparation guidance. An agent's presence does not make the current Mac-only
builder or Unix-dependent runtime work on Windows. Report that boundary rather
than silently offering the development web server or a speculative installer as
a completed Windows app.

### Alternative Prebuilt App And Native Web Installation

Use the supplied `.app` ZIP for the standalone test edition. The alternative
native web bundle exposes the broader development-web feature set; it is not the
installed trial app. Its current target is Apple Silicon/macOS14+. These
instructions do not imply that a public release artifact has been published.
Unpublished source changes are absent from downloaded archives.

Place a supplied native web bundle in a chosen application folder, keeping its
`bin/`, `web/`, notices and `BUILD-INFO.json` together. Add its `bin` directory to
the current shell's `PATH`, or invoke that absolute binary path:

```bash
localbrain doctor
localbrain serve
```

Open `http://127.0.0.1:8000`. First startup creates the primary `localbrain.db`,
default `settings.toml` and private Session-source configuration outside the
installation. Empty or missing source directories do not prevent startup.
Register sources explicitly in Settings; automatic collection defaults to10
minutes after completion and Sync remains available. Stop with `Ctrl+C`.
`localbrain serve --port 8001` selects another port; only loopback addresses are
accepted. No Python environment or package installer is involved in execution.

### Optional macOS Terminal

The app and development web share [Terminal](terminal.md). The Apple Silicon app
includes Node24.15.0, Rust control/helper and pinned PTY/headless packages; users
need no Node/npm installation. Checkout builders run
`python scripts/build-terminal-runtime.py` with Cargo and Node/npm available.
The app builder performs that step automatically. The native web bundle can include that public payload with `scripts/build-api.py --terminal-bundle PATH`; otherwise set the trusted `LOCALBRAIN_TERMINAL_BUNDLE` host environment to a separately verified bundle. The API/CLI remains independent of the Node/PTY execution payload.

New/Start/install explicitly verifies and copies the offline bundle to
`<private-cache>/terminal-<scope>/payloads/<payloadId>`. Startup/list/status/page
visits do not copy/download/start it. Browser assets and licensed D2Coding fonts
ship in both hosts. Keep cache paths below the macOS104-byte socket-path limit.
The scope uses the resolved data and cache identity; stop the service before
changing those paths. The independent transient launchd job and cached helper
survive browser/backend/app Quit and app/checkout removal; no login agent is
installed. Sleep can suspend computation; wake checks actual liveness.

Before replacing the app/runtime, explicitly stop affected work, then replace,
reopen and start an empty service when needed. An incompatible service disables
new work and exposes explicit Update; confirmation binds the generation and exact
terminal set. Ordinary Quit never substitutes for this update step. A stable
`<terminal-cache>/localbrain-terminal` launcher supports list/stop/service commands
without Python or the app after preparation. No PATH or shell rc file is modified.
Terminal screens/layouts remain bounded memory-only and are outside backups;
shutdown/reboot/explicit restart never replay commands. Named workspaces and their
optional default folders survive in `<data>/terminal-workspaces.json`, including
empty groups. This file joins same-installation backup/restore with schema
validation; generation-bound membership never restores a process. New zsh launches
prepare verified private startup shims under `<data>/terminal-shell/` without
editing user rc files. Their immutable versioned paths remain available to live
shells independently of the app; these reconstructible scripts are excluded from
backups. Generic cache cleanup preserves both data locations and
uses the Rust retirement transaction only for verified, inactive payloads and
reports protected live/unknown/loss-marked state while clearing eligible other caches.


### Build A Native Web Distribution

From a prepared source checkout or source archive with Cargo, Xcode Command Line
Tools and build-script Python available:

```bash
python3 scripts/build-api.py --output dist/api
./dist/api/bin/localbrain doctor
./dist/api/bin/localbrain serve
```

Keep the complete output directory together when moving it. It owns native
executables, web assets, schema/guide resources, notices and source/build identity;
it includes no developer DB, configuration, reports or weights. The source archive
is build input, and unpublished changes are not present in a public archive.
An archive without Git metadata records its commit as unavailable instead of
inventing provenance. No compiler or checkout is needed to run the finished bundle.

### Source Checkout And Development

```bash
cargo build --locked -p localbrain-api
./target/debug/localbrain doctor
./target/debug/localbrain serve
```

See the [Developer Guide](developer-guide.md) for source setup, native optional
model behavior, Terminal payload preparation and all configured checks. Choose
one app or web installation for normal use; both use the configured runtime data
location. Rebuilding a checkout does not update an installed app.

### TLS And Historical Python Environments

Native downloads use certificate-verified HTTPS with platform trust. Keep managed
certificates in the OS facility; never disable verification or bundle a private
certificate. Old Python LibreSSL/urllib3 warnings and Uvicorn aliases belong to a
retired Python installation or an explicitly selected historical research runtime,
not the native backend. Use the native executable to identify the running version.
Old Python environment changes do not update the native app, change model/index
identity, establish search quality or alter a shell alias. A successful native
web start prints its listening URL and request logging state to stderr.
`localbrain serve` logs the client socket address, method, requested path, HTTP
version, status and elapsed time to response headers by default. The requested
path includes IDs, filenames and paths that return 404. `--no-access-log` disables
these lines.
The older `--access-log` remains accepted, with `--no-access-log` taking precedence
if both are supplied. Query strings, headers and bodies stay out of the access
logs. The server creates no log file. Existing processes keep their loaded
executable. Rebuild and restart to use a changed native host.

Saved web links to Sessions, Projects, session detail, Sessions Dashboard,
Local Contexts, documents and Natural Search redirect from a trailing slash to
the canonical path with the original query string. The desktop host also
redirects its Local Contexts and Natural Search links after authentication.

### Updates And Removal

Stop the app/backend using that data before replacement. Replace the complete
native application or web bundle, preserving data, settings, originals and shared
public weights. Source installs rebuild from the intended revision; a pull alone
does not replace delivered bytes. Follow
[Upgrade An Existing Storage Layout](#upgrade-an-existing-storage-layout) when
upgrading an old data layout before normal use.

Removing application files removes code and bundled resources, leaving the
primary DB, private configuration, saved reports and shared public weights.
Deliberate data deletion is a separate operation. Terminal services have their
own lifetime: explicitly stop affected work before removing or updating their
runtime. Distributions contain code and reviewed public assets only, never the
runtime directory, local profiles or a model cache.

## Optional Local Models

Each feature owns its requirements. Installing the base app downloads no model
weights. Opening a map or inspecting model status does not install or run a
model. Local inference does not train or update shared pretrained weights.

| Feature | Local model requirement | Asset download |
| --- | --- | --- |
| Session ingestion, reading, keyword search, deterministic views | None | None |
| Natural-language Session / Local Context search | Qwen3-Embedding-0.6B | Same shared asset as affinity |
| Prepared full-history affinity map | Qwen3-Embedding-0.6B | About 1.21 GB |
| Explicit native generation model setup | Qwen3-4B or Qwen3-8B | About 8.06 GB or 16.40 GB |

Qwen3-Embedding-0.6B is the document/query encoder used by natural search.
Installing a generation model leaves ordinary app startup and workflow
production passive. Public originals remain in the resolved
shared Hub cache, including `~/.cache/huggingface/hub` by default. App-owned
registration manifests stay under `data/models`. Complete public caches can be
registered locally without downloading; status checks are presence checks,
while use verifies integrity. Local inference does not fine-tune private weights.
Claude/Codex-backed actions have their own CLI/authentication requirements and
explicit external-service boundary; installing local models does not satisfy
those requirements.

The former Laya and Qwen3-Reranker-0.6B comparison tools are retired. Their
separate pinned public snapshots may remain in the shared Hub cache. The
historical procedures record their Python dependencies, model-specific
manifests and offline reproduction controls. [Retired comparisons](development/search-comparisons.md#retired-comparison-procedures)

### Native Local Model Runtime

Model installation and execution code is included in the native backend. Inspect
readiness without loading weights or downloading anything:

```bash
localbrain models status
```

No PyTorch, Transformers, Sentence Transformers or Python extras are needed by
the product. The original pinned safetensors and tokenizer assets are consumed
by Candle and Rust tokenizers. Apple Silicon CPU/Metal are the current native
execution target; other platforms and real minimum-OS model execution require
their own checks. Device selection supports automatic selection and CPU fallback.
Large models need RAM beyond their asset sizes and can be slow on CPU; simulation
accepts `--device cpu`. Historical Python comparison tools are retired; they are
not an alternative product model runtime.
Native runtime/index identity changes require rebuilding incompatible cached
vectors; existing weights and private records are preserved.

### Install And Verify A Selected Model

```bash
localbrain models install embedding
localbrain models verify embedding
```

`models install 4b` and `models install 8b` are separate explicit downloads.
The installer pins the public model ID, revision, and asset hashes and uses the
official Hugging Face endpoint without an account token. It accepts no database,
source, prompt, or conversation argument. A complete cached snapshot is verified
and reused; an interrupted download can resume its missing files.

When the public snapshot already exists, `localbrain models install embedding
--offline` registers it without network access. The same option supports 4B/8B.
Installation failure leaves owned metadata so the command can be retried;
public model assets are retained.

Prepare the full-history result after importing Sessions:

```bash
localbrain simulate --inventory-only
localbrain simulate
localbrain simulate --status
```

The packaged command defaults to the configured primary DB, the single
`<cache>/session-simulation` directory, and LocalBrain's embedding manifest. The source
script also supports explicitly supplied database/output paths and compatible
installed-asset manifests with app-local or Hub-relative snapshots.
Rerunning simulation reuses compatible vectors; model, runtime, source, and
chunking changes can require recomputation. Cache location alone does not change
model identity.
Ctrl+C cancels active inventory and result verification before publication.
The interrupted attempt is visible in `--status`, and the last successful
report remains available. Once publication begins, the command finishes
recording the result and reports its outcome once.

## Storage Ownership And Configuration

Reviewed learning lessons, immutable source snapshots, personal attempts and
visibility choices live in the primary private SQLite database. They require DB
backup for full recovery and are not part of rebuildable search-cache cleanup.
`localbrain learning import PATH --reviewed` reads a bounded local packet and
does not fetch sources or require a model; see [Learning](work-grounded-learning.md).

| Storage | Default | Ownership |
| --- | --- | --- |
| Primary data | `~/Library/Application Support/LocalBrain` | One primary DB, source configuration, saved Runs/reports |
| Model metadata | `<data>/models/<model-slug>` | Small LocalBrain installation manifests/locks |
| Public pretrained assets | `~/.cache/huggingface/hub` | Shared within this PC's user account |
| Private derived cache | `~/Library/Caches/LocalBrain` | Rebuildable dashboard summary, simulation, preview and natural-search generations |

`LOCALBRAIN_DATA_DIR` selects private application state. Paths inside a Git
repository or the installed/source package are rejected before creating the DB.
New runtime directories use `0700`; the primary DB and private configuration
use `0600`. The desktop wrapper reuses this path resolver, command and storage
contract. Application files can move independently of these user data locations.

General preferences live in `<data>/settings.toml`; Session registration stays in
`session-sources.toml`, search choices in `natural-search.json`, and Context
registration in the DB. Terminal workspace identity/name/default/membership lives
in `terminal-workspaces.json`; generated zsh launch shims live in `terminal-shell/`.
[Terminal](terminal.md#folder-workspace-and-status) owns their validation,
generation and lifetime contracts. Rebuildable synchronization health is separate
`session-sync-state.json` and `context-sync-state.json`, so health-only writes do
not invalidate search input. Their completion clocks and intervals are independent.
General preferences follow `settings.toml`; missing fields use defaults. Environment
variables do not override these preferences. The UI edits that same local value set.
The app and web server create the file with default values on first startup if it
does not exist. Later startups preserve the saved file; initial creation does not
require completing onboarding or saving the settings screen.

Confirmed Sessions Chart Project visibility belongs to the primary DB's
`session_chart_preferences` table, per logical source/workspace scope. It is user
intent rather than a rebuildable cache and requires DB backup or reselection after
DB loss. Browsers using the same LocalBrain DB share this choice; clearing browser
site data does not delete it. Camera, selection and vertical scale remain browser
tab navigation state. No new file root, cloud sync or automatic backup is added.
[Workspace And Session Activity](data-model/workspace-and-session-activity.md#session_chart_preferences)
owns its row and recovery semantics.

`LOCALBRAIN_CACHE_DIR` selects private rebuildable state. With a custom
`LOCALBRAIN_DATA_DIR`, an unspecified cache root becomes the sibling directory
named `<data-name>-cache`. An explicit cache variable overrides that location.
Keep runtime and cache roots outside Git repositories and
the installed package. Storage migration requires distinct, non-overlapping
roots on the same filesystem. Cache contents derived from private Sessions are
private, even though they can be rebuilt; they never enter the public model cache.
The private runtime path resolver rejects overlap with the public Hub cache.

Public cache precedence is `HF_HUB_CACHE`, `HUGGINGFACE_HUB_CACHE`, `HF_HOME/hub`,
`XDG_CACHE_HOME/huggingface/hub`, then `~/.cache/huggingface/hub`. Set
`HF_HUB_CACHE` in the process environment to relocate public assets, using the
same value for installation and inference. Prefer it over `HF_HOME`, which also
controls other Hub state. Each Mac downloads its own public assets. No machine
sync, private-data sharing, or automatic Git publishing is performed.

### Natural-Language Search Storage

`<data>/natural-search.json` holds explicit activation and the selected search
profile. `<cache>/natural-search/` owns one readable `index.sqlite3`, one resumable
`building.sqlite3`, a writer lock and bounded aggregate `status.json`. Molecules,
original-text pointers, lexical terms and binary vectors are private derived
data. Deleting this cache preserves original Sessions, Contexts and settings;
an enabled running app rebuilds it from eligible normalized sources. An update
keeps the prior complete generation readable until atomic publication; changed
or removed originals are excluded even before rebuilding finishes. Budget for
both generations and SQLite rebuild overhead. An interrupted staging generation
is retained for explicit retry, with compatible vectors reused.

Storage follows ownership and recoverability, not the `.sqlite3` extension.
The primary DB contains durable user state; the search DB can be recreated from
eligible normalized originals and the selected profile. Rebuilding can still be
costly, and cached excerpts/vectors remain private. Public model download caches
have a different owner and never receive those private derived contents.

Let the current index size be A and the staging database size be B. SQLite's
`VACUUM` can require up to another `2 × B` of free space for its temporary database
and journal, so `A + 3 × B` is a planning allowance for these files, not merely
`A + B`. This
does not include public model assets or other application data. Actual sampled
peaks and allocated bytes are recorded separately; they are not a universal cap.
See [SQLite VACUUM storage behavior](https://www.sqlite.org/lang_vacuum.html#how_vacuum_works).

Install the optional runtime and `localbrain models install embedding`, then
use `localbrain search prepare` or the natural-search preparation action. There
is no download on page opening. Once enabled, the app refreshes after normalized
Sync changes; `localbrain scan` also refreshes an enabled index. The enabled app prepares the query model after checking its index and keeps it
loaded in the app process. Empty corpora do not load weights. Local inference uses verified public assets in
offline mode; private inputs and results never enter the shared Hub cache.

`localbrain search status` reports aggregate coverage; `localbrain search query
"만들던 앱 관련 세션 보여줘"` explicitly prints local results. The engine does not
persist search-query history. Console access logs omit the query string from
the request path.
Browser history still contains submitted queries. An unchanged refresh preserves
the current generation without tokenizing or embedding it again.
`localbrain search prepare --rebuild` recomputes an owned index when its vector
contents need recovery; it preserves the previous complete generation until
publication and does not remove unrelated caches. [Natural-Language Search](natural-language-search.md)
owns admission, molecularization, score and recovery semantics.

### Model Registration Information

All newly selected models register under `<data>/models/<model-slug>`.
`model.json` records the pinned public model, revision, Hub-relative snapshot,
asset hashes and verification identity; `owner.json` bounds ownership and
`install.lock` prevents concurrent installation. These small files contain no
Session content or model-weight copy. The current implementation reads them to
use and verify a local model; the base app needs none of them.

The old root-level `qwen3-4b`/`qwen3-8b` locations remain readable for upgrades.
Storage migration groups their shared-cache registrations under `models/`.
App-local legacy weights and unfinished installations are preserved for separate
explicit handling. Only selected models get registrations. Moving registration
files does not download weights, change model identity or require re-embedding.

Settings' embedding-model folder selection stores an absolute canonical
`cache_root` in that model's `model.json`, alongside the existing Hub-relative
snapshot. This explicit registration root takes precedence for that model's
installation, verification and offline inference. Registrations without the field
retain the existing `HF_HUB_CACHE` → `HUGGINGFACE_HUB_CACHE` → `HF_HOME/hub` →
`XDG_CACHE_HOME/huggingface/hub` → `~/.cache/huggingface/hub` precedence. Legacy
app-local registrations remain readable and are not moved. Generation models and
other tools retain their own existing roots; selecting an embedding folder never
changes a process-wide Hugging Face cache variable.

Folder checking reads the pinned revision and complete asset hashes without
registering or downloading. Connecting revalidates those assets under the
existing model installation lock, compares the captured registration revision,
and atomically publishes the new registration only after verification. Missing or
partial assets require explicit download to the chosen root. That worker carries
the target and expected revision, keeps the old registration until success, and
preserves partial public files for retry at the same location. After interruption
or app restart, choosing that location again can reuse those pieces. No source
file is moved or deleted. The private data/cache roots and their ancestors or
descendants, the installed package and Git worktrees are ineligible destinations.
Existing registrations retain their model identity and unrelated metadata fields;
folder selection refuses an unsupported registration schema or identity instead
of upgrading a model or rewriting an unknown format.
A location change reloads the search
encoder while retaining the pinned model/index contract; an enabled search can
reuse unchanged vectors and a disabled search stays disabled when connecting an
already downloaded model. Successful explicit model downloads retain their
existing automatic search-preparation behavior.

Natural search excludes both the default Hub cache and the active selected
embedding cache from source admission. Storage measures a separate selected root
alongside the shared default when they are disjoint, and avoids duplicating nested
root measurements. Public assets remain outside app backup/cache cleanup; backup
includes their registration pointer, and restore does not copy or download them.

### Upgrade An Existing Storage Layout

Stop the server and development jobs first. Preview the moves, then apply:

```bash
localbrain storage migrate
localbrain storage migrate --apply
```

This moves recognized old simulation/preview state to the cache root and model
registrations under `models/`.

Feature-cache moves use ownership checks supplied by the included feature.
If Auto Work is excluded from application composition, its old simulation/preview
directories stay in place without being decoded or moved.

Moves use filesystem rename, without copying the DB, weights or derived index.
Unknown, linked or unowned content is preserved. Open files, destination
collisions, changed files and cross-filesystem moves refuse; existing destinations
are never merged or overwritten. Each successful rename is durable: after an
interruption, rerunning processes the remaining source directories. The primary
DB, source configuration, saved Runs and shared public weights are not moved.

Use `localbrain models verify <model>` for each installed model, inspect
`localbrain storage status`, then restart with `localbrain serve`.

## Native Session Compression And Recovery

Native Session files are owned by Claude/Codex. LocalBrain does not request their
compression or apply its migration-backup cleanup policy to them. Codex collection
accepts both `.jsonl` and `.jsonl.zst`, streaming compressed input without writing
an extracted transcript. Ordinary synchronization and stored reading need no
manual decompression. Claude retains its own native JSONL admission rules.

Collected Sessions, conversations, Usage, pins and relationships remain in SQLite
when accepted originals disappear; linked file evidence records original presence
independently from parsing errors. Missing originals prevent source-dependent
reprocessing, not stored reading or DB-supported calculations. Reappearing inputs
merge into the same source/native identity. The ingestion owner defines exact
presence, replacement, eligibility and repair rules. This preserves normalized
history, not bytes that were never collected. Manual provider-file recovery or
rewriting remains a separately authorized operation; the optional procedure below
is not required by LocalBrain's compressed ingestion.

Codex's [versioned compression implementation](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/rollout/src/compression.rs)
examines active and archived rollouts, selects files at least seven days old by
modification time, verifies decoded output before retiring the plain file, and
uses a six-hour worker-start cooldown rather than a periodic deletion timer.
In that version the [startup feature defaults to false](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/features/src/lib.rs).
A client can separately request [`rollout/compress`](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/app-server/README.md#local-rollout-compression)
without enabling the startup feature. A current disabled flag does not establish
which process triggered a past compression pass. These are version-scoped
upstream observations, not a LocalBrain retention guarantee.

For bounded manual recovery, preserve the compressed source, decode into a
separate private staging file, verify successful complete decoding, and publish
the matching `.jsonl` without overwriting any existing plain file. Sync that
registered Session source afterward. Original timestamps and source-native
identity should be preserved. Removal of a compressed duplicate requires a
separate user request, matching decoded/plain byte counts and SHA-256 hashes,
and unchanged regular files at the deletion boundary; changed or uncertain
pairs stay preserved. This operation creates no new ingestion format support
and never places native files or recovery manifests in Git.

## Bounded Recovery And Cleanup

Ordinary startup does not make a database backup or persistent server log.
Schema migrations can create a recovery copy before a structural change.
Following a successful committed initialization, current migration contracts
and SQLite integrity are checked before retirement: at most the newest eligible
copy is kept, for seven days measured from its file modification time. Older
eligible copies can be retired before seven days when a newer copy is retained.
Failed initialization, uncertain ownership, open
files, symlinks, hard links, or nonempty backup WALs preserve recovery copies.
The numeric Session-revision migration uses
`<database>-pre-session-revision-v1.bak` under this same lifecycle.
This policy covers only enumerated LocalBrain migration suffixes. Arbitrary
manual backups and unrelated files are never discovered for automatic deletion.
The automatic check runs after successful DB initialization. Backend startup
and actual Session/Local Context scans, including scheduled and manual sync,
call native `db::initialize()`. An eligible copy can therefore be retired during a later sync
while the app remains running; restarting is not required. A due timer with no
scan does not initialize the DB, and no independent seven-day cleanup timer is
installed. Explicit eligible cleanup can also perform retirement. Initialization
prepares the existing database and schema; it does not clear stored user data.

Inspect aggregate usage and preview/apply eligible retirement while the server
is stopped:

```bash
localbrain storage status
localbrain storage cleanup
localbrain storage cleanup --apply
```

`localbrain.db-wal` and `localbrain.db-shm` are SQLite transaction helpers, not
extra complete databases. These commands never delete the live DB or its
sidecars. Simulation has one private derived `state.sqlite3` in the cache alongside its
result; it is a rebuildable index, separate from the single primary DB. Its
30-day inactivity lifecycle and explicit `localbrain simulate --purge` remain
owned by the simulation. The sample preview has a seven-day result lifetime.
Startup and `storage cleanup` retire expired, inactive, recognized cache result
files under their writer locks; ownership markers and locks remain. Malformed,
unknown or busy cache state is preserved. There is no background cleanup daemon.
Only included features contribute cache cleanup to startup, Settings and CLI.
Excluding a feature preserves its existing cache files and does not prevent
common search-cache cleanup. This is an internal composition boundary, not a
user setting; the default application still includes the existing features.
Development experiments retain their existing owned
expiry/cleanup rules. Saved user reports remain available until a separate
user-authorized removal; backup cleanup does not erase them.

Before a new feature writes files, specify its owner, path, whether it is user
data or rebuildable output, retention, cleanup trigger, and behavior after
failure. Development diagnostics must have a private owner and cleanup condition;
they must not become automatic per-startup production output. User-facing backup,
restore and cache cleanup follow the [local recovery contract](desktop-app-and-settings.md#local-recovery);
their procedures belong to the [Settings guide](../../../apps/web/content/docs/settings.md#storage).
Native packaging and its verification limits belong to the
[test distribution guide](standalone-test-app-guide.md). General export remains
separate future work.

## Storage Measurement

Settings measures configured data, private cache and shared Hub roots separately,
adding a selected embedding-model root when it is disjoint from the shared Hub.
Nested model roots are counted through the containing configured root, without a
second total.
It reports logical regular-file bytes (GiB), deduplicates hardlinks within each
location and skips nested symlinks. A selected root symlink still refers to its
configured directory. Missing roots are empty, permission/read failures are
unavailable or partial, and capacity is resolved per actual filesystem (nearest
existing parent for future directories). Repeated volume free space is displayed
once. Shared Hub totals include other tools/models. App binaries, checkout,
toolchains and build/dependency caches are outside these storage totals. Reading
storage never migrates or removes material. Backup/restore and cache cleanup keep
their existing eligibility and preservation rules.
