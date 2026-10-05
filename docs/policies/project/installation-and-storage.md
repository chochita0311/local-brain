# macOS Installation And Local Storage

## Supported Installation

LocalBrain runs as a local web application on macOS. uv installs its Python
environment and dependencies. Local models and authenticated CLI integrations
are optional feature prerequisites; the base application can start with an
empty database. Python 3.11 is the recommended installation and verification
target; the base package metadata accepts Python 3.9+.
Native app/binary packaging remains future work. A packaged wheel already owns
the web assets, schema, guides, and commands below; it does not need the source
checkout at runtime.

Distributions constrain the verified FastAPI/Uvicorn release lines; the source
lockfile additionally freezes exact dependency versions. Dependency upgrades
must repeat the standalone wheel startup/page checks before widening those
constraints, since an unconstrained newer framework can break template calls.

### A New Mac With No Development Tools

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
   `localbrain.db` and a private Session-source configuration outside the install
   directory. Empty or missing source directories do not prevent startup. Import
   Sessions through the explicit Sync action when sources are available.
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
| Session ingestion, reading, search, deterministic views | None | None |
| Prepared full-history affinity map | Qwen3-Embedding-0.6B | About 1.21 GB |
| Explicit experimental context trials | Qwen3-4B or Qwen3-8B | About 8.06 GB or 16.40 GB |

The 4B/8B candidates remain experiments; installing them does not admit a new
automatic workflow producer or enable an LLM on ordinary app startup.
Claude/Codex-backed actions have their own CLI/authentication requirements and
explicit external-service boundary; installing local models does not satisfy
those requirements.

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

| Storage | Default | Ownership |
| --- | --- | --- |
| Primary data | `~/Library/Application Support/LocalBrain` | One primary DB, source configuration, saved Runs/reports |
| Model metadata | `<data>/models/<model-slug>` | Small LocalBrain installation manifests/locks |
| Public pretrained assets | `~/.cache/huggingface/hub` | Shared within this PC's user account |
| Private derived cache | `~/Library/Caches/LocalBrain` | One simulation index and one preview; rebuildable and finite |
| Development evaluation evidence | `~/Library/Application Support/LocalBrain-Development` | Explicit development archives, separate from installed app data |

`LOCALBRAIN_DATA_DIR` selects private application state. Paths inside a Git
repository or the installed/source package are rejected before creating the DB.
New runtime directories use `0700`; the primary DB and private configuration
use `0600`. A future desktop wrapper must reuse this path resolver, command and
storage contract instead of introducing machine-specific project paths.

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

## Bounded Recovery And Cleanup

Ordinary startup does not make a database backup or persistent server log.
Schema migrations can create a recovery copy before a structural change.
Following a successful committed initialization, current migration contracts
and SQLite integrity are checked before retirement: at most the newest eligible
copy is kept, for seven days. Failed initialization, uncertain ownership, open
files, symlinks, hard links, or nonempty backup WALs preserve recovery copies.
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
they must not become automatic per-startup production output. General user-facing
backup/restore/export and native binary packaging remain separate future work.
