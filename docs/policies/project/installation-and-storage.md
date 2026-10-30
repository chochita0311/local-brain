# macOS Installation And Local Storage

## Supported Installation

LocalBrain offers an Apple Silicon standalone test app and a Python/web installation.
The `.app` bundles Tauri, Python and optional-search execution libraries; recipients
unzip and launch it without installing development tools. Public model weights
remain an explicit optional download. Use the [test app guide](standalone-test-app-guide.md)
for first launch, ad-hoc signing, supported-environment evidence and manual updates.
The [settings contract](desktop-app-and-settings.md) owns the shared preferences,
source lifecycle and restart-only same-Mac recovery.

For the alternative local web installation, uv installs its Python
environment and dependencies. Local models and authenticated CLI integrations
are optional feature prerequisites; the base application can start with an
empty database. Python 3.11 is the recommended installation and verification
target; the base package metadata accepts Python 3.9+.
A packaged wheel also owns
the web assets, schema, guides, and commands below; it does not need the source
checkout at runtime.

Distributions constrain the verified FastAPI/Uvicorn release lines; the source
lockfile additionally freezes exact dependency versions. Dependency upgrades
must repeat the standalone wheel startup/page checks before widening those
constraints, since an unconstrained newer framework can break template calls.

### A New Mac With No Development Tools

Use the supplied `.app` ZIP for the standalone test edition. The following steps
install the alternative Python/web edition and its broader development features.

1. Install uv using its [official macOS installer](https://docs.astral.sh/uv/getting-started/installation/):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source "$HOME/.local/bin/env"
   uv python install 3.11
   ```

2. Install a supplied LocalBrain distribution wheel using the next section.
   If a wheel has not been published, use the public source archive fallback.
   These instructions do not imply that a release artifact already exists.
   Unpublished source changes are not included in GitHub downloads.

3. Start the installed application:

   ```bash
   localbrain doctor
   localbrain serve
   ```

   Open `http://127.0.0.1:8000`. The first startup creates one primary
   `localbrain.db`, default `settings.toml` and a private Session-source configuration
   outside the install directory. Empty or missing source directories do not prevent startup. Import
   Sessions after explicitly registering sources in settings; automatic collection
   defaults to 10 minutes after completion and the Sync action remains available.
   Stop the server with `Ctrl+C`. Port selection is available with
   `localbrain serve --port 8001`; the command permits only loopback addresses.

If the executable is not on `PATH`, run `uv tool update-shell`, then open a new
terminal. For a managed-network certificate error, add `--system-certs` to the
failed uv install command. Never disable certificate verification.

### Install A Distribution Wheel

Download the supplied public wheel, then replace the example path below with
its actual filename:

```bash
uv tool install --python 3.11 /absolute/path/localbrain-version-py3-none-any.whl
```

The tool environment owns the installed package, Python and dependencies.
Templates, browser assets, schema presentation, guides and executable commands
are package resources. Running the application needs no Git repository or source
checkout. Installation does not copy a developer's DB, configuration, reports,
model weights or evaluation archive. Updates and optional extras use the selected
distribution artifact, not a runtime dependency on its build checkout.

### Public Source Archive Fallback

Download the public source using GitHub's **Code → Download ZIP** and put the
extracted project folder at `~/Applications/LocalBrain`. Git and a development
checkout are not required. Then install it as an application:

```bash
uv tool install --python 3.11 "$HOME/Applications/LocalBrain"
```

The source archive is installation input; `uv tool install` builds and installs
the package. Normal execution uses that installed environment.

### Source Checkout And Development

From the repository root:

```bash
uv sync --python 3.11 --frozen
uv run --no-sync localbrain doctor
uv run --no-sync localbrain serve
```

`uv sync` owns this checkout's environment. `uv tool install` owns a separately
installed application. Choose one installation for normal use; installing the
package twice is not necessary. Both use the configured runtime data location.

### Repair An Existing LibreSSL-Based Environment

An urllib3 `NotOpenSSLWarning` identifying LibreSSL comes from the Python SSL
runtime in the active environment. Recreate that environment with the recommended
uv-managed Python 3.11. Suppressing server logs does not change its SSL library.
For a source checkout, stop its running server and model jobs first, then run:

```bash
uv python install 3.11
uv sync --python 3.11 --extra local-models --frozen
uv pip check --python .venv/bin/python --no-cache
uv run --no-sync python -c 'import ssl; print(ssl.OPENSSL_VERSION)'
uv run --no-sync localbrain serve
```

Keep the extras required by that installation; omit `--extra local-models` for a
base-only checkout. With the base dependencies installed, also check
`uv run --no-sync python -c 'import urllib3'` for the original warning; urllib3
is a base dependency for Drive transport. If the managed interpreter and locked distributions are
already cached, skip the Python download and add
`--no-python-downloads --offline` to `uv sync`. For a separately installed app,
repeat its selected wheel/archive installation with `--python 3.11` and the same
extras instead of editing a checkout's `.venv`.

This replaces Python packages, leaving the separately owned database, model
weights and search cache in place. A frozen sync preserves the lockfile; packages
selected by its Python-version conditions may differ. A running server must be
restarted to use the replacement environment. Successful imports do not establish
search quality or benchmark performance in the new runtime.

Uvicorn's startup `INFO` message is normal. A shell alias that invokes Uvicorn
directly can also keep its default request logging, including search URLs and
periodic status requests. Changing `.venv` does not alter that alias or disable
access logs. The packaged `localbrain serve` command owns its separate
`access_log=False` behavior.

### Updates And Removal

Stop the server before replacing the installed application. Preserve the
original Python and extras for both source archive and wheel updates. With an
updated source archive at the same location, repeat `uv tool install --reinstall`.
For a base installation from a built wheel, install that wheel with
`uv tool install --reinstall --python 3.11 /absolute/path/localbrain-version-py3-none-any.whl`.
For a model-enabled installation, append `[local-models]` to the selected archive
directory or wheel path and quote the complete argument, as shown under
[Install The Local Model Runtime](#install-the-local-model-runtime).
After an upgrade from the old storage layout, follow
[Upgrade An Existing Storage Layout](#upgrade-an-existing-storage-layout)
before restarting the app.

`uv tool uninstall localbrain` removes the executable/environment. It preserves
the primary database, private configuration, saved reports, and shared public
model weights. Deliberate data deletion is a separate local operation. Build and
release packages must contain code and reviewed public assets only; never copy
the runtime directory, local profiles, or model cache into a distribution.

## Optional Local Models

Each feature owns its requirements. Installing the base app downloads no model
weights. Opening a map or inspecting model status does not install or run a
model. Local inference does not train or update shared pretrained weights.

| Feature | Local model requirement | Asset download |
| --- | --- | --- |
| Session ingestion, reading, keyword search, deterministic views | None | None |
| Natural-language Session / Local Context search | Qwen3-Embedding-0.6B | Same shared asset as affinity |
| Prepared full-history affinity map | Qwen3-Embedding-0.6B | About 1.21 GB |
| Context Search read-only folder questions | Qwen3-4B or Qwen3-8B | About8.06GB or16.40GB; reuse existing shared assets |
| Explicit experimental context trials | Qwen3-4B or Qwen3-8B | About 8.06 GB or 16.40 GB |

Qwen3-Embedding-0.6B is the document/query encoder used by natural search.
The4B/8B generation models also power explicitly submitted Context Search questions;
installing them does not enable an LLM on ordinary app startup or an automatic workflow producer.
Settings → Search Model offers installation/verification for both. Public originals
remain in the resolved shared Hub cache, including `~/.cache/huggingface/hub` by
default. App-owned registration manifests stay under data/models; Context Search
kernel caches belong under cache/context-search. No prompt/answer file or private
weight fine-tuning is created. Complete public caches can be registered locally
without downloading; status checks are presence checks, while use verifies integrity.
See [Context Search](context-search.md) for scope and ephemeral conversation contracts.
Claude/Codex-backed actions have their own CLI/authentication requirements and
explicit external-service boundary; installing local models does not satisfy
those requirements.

Laya multilingual and Qwen3-Reranker-0.6B are separate optional development assets
for natural-search comparisons. Their pinned snapshots
use the same resolved public Hub cache as the Qwen embedding and 4B/8B assets,
with separate model directories and weights. They are not part of the app's
`local-models` extra or its default search path. The comparison's Python packages
and private hash manifests have a separate development lifecycle. See the
[comparison setup](developer-guide.md#natural-language-search-comparisons) for
explicit installation and offline reproduction; a retained checkpoint alone is
not a ready-to-run comparison environment.

### Install The Local Model Runtime

For the installed application:

```bash
uv tool install --reinstall --python 3.11 "/absolute/path/localbrain-version-py3-none-any.whl[local-models]"
localbrain models status
```

For a source archive installation, use
`uv tool install --reinstall --python 3.11 "$HOME/Applications/LocalBrain[local-models]"`.
Use the same package version when adding extras.

For a source checkout:

```bash
uv sync --python 3.11 --extra local-models --frozen
uv run --no-sync localbrain models status
```

These commands install LocalBrain's PyTorch, Transformers, Sentence
Transformers, and grouping dependencies in its application environment.
The lockfile separates Intel macOS PyTorch/NumPy compatibility from Apple
Silicon. Apple Silicon is the locally verified model runtime; Intel dependency
resolution is covered, but model execution on an Intel Mac is not verified.
The inference device is selected automatically, with CPU fallback. Large models
need sufficient RAM in addition to the asset sizes above; CPU execution can be
slow. Use `--device cpu` with simulation when necessary.

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
| Private derived cache | `~/Library/Caches/LocalBrain` | Simulation, preview and natural-search generations; rebuildable |
| Development evaluation evidence | `~/Library/Application Support/LocalBrain-Development` | Explicit development archives, separate from installed app data |

`LOCALBRAIN_DATA_DIR` selects private application state. Paths inside a Git
repository or the installed/source package are rejected before creating the DB.
New runtime directories use `0700`; the primary DB and private configuration
use `0600`. The desktop wrapper reuses this path resolver, command and storage
contract. Application files can move independently of these user data locations.

General preferences live in `<data>/settings.toml`; Session registration stays in
`session-sources.toml`, search choices in `natural-search.json`, and Context
registration in the DB. Rebuildable synchronization health is separate
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

`LOCALBRAIN_CACHE_DIR` selects private rebuildable state;
`LOCALBRAIN_DEVELOPMENT_DIR` selects the private development archive. With a
custom `LOCALBRAIN_DATA_DIR`, unspecified cache/development roots become sibling
directories named `<data-name>-cache` and `<data-name>-development`. Explicit
variables override those locations. Keep all roots outside Git repositories and
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
persist search-query history; the packaged server disables URL access logging.
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

### Upgrade An Existing Storage Layout

Stop the server and development jobs first. Preview the moves, then apply:

```bash
localbrain storage migrate
localbrain storage migrate --apply
```

This moves recognized old simulation/preview state to the cache root and model
registrations under `models/`. Add `--include-development` to both commands when
explicitly moving existing development archives to the development root.
Ordinary installations do not create those archives. Original private evaluation
files, modification times and content hashes are preserved; they keep their existing owner
and retention contract. Historical paths in archived diagnostics describe the
original execution, not current runtime dependencies.

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
compression or apply its migration-backup cleanup policy to them. The current
Session scanner accepts `.jsonl`; it does not ingest `.jsonl.zst` directly.
A compressed-only rollout can therefore disappear from the normalized source
mirror without its conversation having been permanently deleted.

Session ingestion is scoped to native local Claude/Codex JSONL. Compressed-file
recovery is a separately authorized local maintenance operation; direct compressed
ingestion is outside this contract and is not a planned extension.

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
copy is kept, for seven days. Failed initialization, uncertain ownership, open
files, symlinks, hard links, or nonempty backup WALs preserve recovery copies.
The numeric Session-revision migration uses
`<database>-pre-session-revision-v1.bak` under this same lifecycle.
This policy covers only enumerated LocalBrain migration suffixes. Arbitrary
manual backups and unrelated files are never discovered for automatic deletion.

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
Development experiments retain their existing owned
expiry/cleanup rules. Saved user reports remain available until a separate
user-authorized removal; backup cleanup does not erase them.

Before a new feature writes files, specify its owner, path, whether it is user
data or rebuildable output, retention, cleanup trigger, and behavior after
failure. Development diagnostics must have a private owner and cleanup condition;
they must not become automatic per-startup production output. User-facing backup,
restore and cache cleanup follow the [local recovery contract](desktop-app-and-settings.md#local-recovery);
their procedures belong to the [Settings guide](../../../src/localbrain/content/docs/settings.md#storage).
Native packaging and its verification limits belong to the
[test distribution guide](standalone-test-app-guide.md). General export remains
separate future work.

## Google Drive Storage

[Google Drive synchronization](google-drive-sync.md) stores private configuration, selections, cached results and per-file checkpoints in `<data>/google-drive/sync.sqlite3` (schema1). Google Cloud CLI owns credentials and refresh; access tokens are memory-only in LocalBrain. Received copies are `<data>/external-sources/google-drive/<connection-id>/<publisher-id>/`; directories0700/files0600. `<data>/google-drive/staging/` holds bounded immutable upload snapshots, removed after use and recovered on backend restart. Download staging uses private sibling files and atomic replacement. Built-in backup/restore does not include these connection/copy/checkpoint trees or gcloud credentials; restoring ordinary app settings does not restore or revoke Google access. Users may back up received files separately. Do not classify these copies or the sync database as rebuildable cache, publish them or implicitly index them.
