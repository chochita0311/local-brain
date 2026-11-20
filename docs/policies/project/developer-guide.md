# Developer Guide

## Prerequisites

- Apple Silicon macOS 14+ for the currently supported source, web-bundle and native-app delivery
- Rust/Cargo with workspace minimum 1.90 and Xcode Command Line Tools for source builds
- Python3.11+ for repository build/check scripts, which use the standard library only
- Node/npm for browser-asset, public Terminal-payload and Tauri builds
- Claude CLI only for Claude-backed maintenance Runs
- Codex CLI for personal improvement analysis Runs or when selecting Codex for external synchronization

The application backend, CLI, settings, ingestion and local inference are native
Rust. Running a finished app or web bundle requires no Python, virtual environment,
PyTorch, Transformers or Sentence Transformers. Python is a repository build/check
tool, not a runtime prerequisite. The source runtime uses Unix facilities and the
current native builders target Apple Silicon macOS; these facts do not establish
Windows or Intel-Mac support.

## Setup And Run

Use [macOS Installation And Local Storage](installation-and-storage.md) for a
new machine, packaged app installation, optional model assets and recovery retention.
Activate the repository-owned pre-commit hook after cloning:

```bash
git config core.hooksPath .githooks
```

Build the locked native workspace:

```bash
cargo build --workspace --locked
```

Inspect readiness, then start the development web server:

```bash
./target/debug/localbrain doctor
./target/debug/localbrain serve --access-log
```

Open `http://127.0.0.1:8000`. The server accepts loopback hosts only. With registered
sources, explicitly initialize or refresh their collected content using:

```bash
./target/debug/localbrain scan --full
```

The same commands are available through
`cargo run --locked -p localbrain-api --bin localbrain -- <command>` or an installed
native bundle's `bin/localbrain`. `lb` is the corresponding CLI alias. Rebuild and
restart after source changes; the native host has no Uvicorn/Python reload process.
The root workspace contains the shared core, pinned-model crate, Terminal helper
and API/CLI host. Normal settings execute in process; no separate common-runtime
build, interpreter callback or Python dependency installation is required.

A successful web server start prints its listening URL and the `access log: on`
or `access log: off` state to the terminal. Plain `serve` writes access logs to
stderr by default. Each line shows the client socket address, method, actual request path,
HTTP version, status and time until response headers are ready. Path parameters
and paths returning 404 are visible. A session request produces a line like this.

```text
INFO:     127.0.0.1:53218 - "GET /sessions/123 HTTP/1.1" 200 OK 1.234ms
```

`serve --no-access-log` disables request logs. The older `--access-log` flag works
with existing aliases, and the quiet flag takes precedence if both are supplied.
Restart the rebuilt executable to use the current format. Existing aliases work
as written. Query strings, headers, cookies and bodies stay out of the logs. The
server creates no log file. Desktop uses its structured readiness protocol.
In the example, `53218` is the client's TCP port. The server listens on the
port in the startup banner.

The browser reads Session sync status from `GET /api/sessions/sync/status`.
It schedules the next read after 1.5 seconds while work is running or queued
and after 15 seconds when idle. A manual POST or the application scheduler
starts collection. The separate `/api/health` endpoint serves host health
checks.

Source edits do not update a running backend or a previously built `LocalBrain.app`.
App and development-web backends using the same data directory share normalized
records and synchronization health, while their writer lock serializes collection.
Current runtimes refuse a source whose stored numeric Session revision is newer;
unmodified older builds lack that admission check and can still reparse newer
results. After a parser update, stop incompatible older backends or rebuild and
restart the app before allowing both to collect into the same store. Then run
ordinary Session Sync with the updated backend. One successful web Sync does not
update the packaged app or prevent a later old-version reparse.

Native inference libraries are built with the application; optional weights remain
separate. `localbrain models install embedding` explicitly verifies/downloads the
pinned public assets and publishes LocalBrain's registration. `localbrain doctor`
and `localbrain models status` inspect readiness without collecting sources,
downloading assets or loading/running a model. Use the executable path above in a
checkout. A runtime fingerprint change refuses incompatible cached vectors; follow
[search preparation](#search-sessions-and-local-context) for rebuilding.

## Optional macOS Terminal

On Apple Silicon macOS, build the self-contained public payload with
`python3 scripts/build-terminal-runtime.py`; Cargo and Node/npm are build tools,
not installed-app requirements. The builder pins Node24.15.0, verifies its
official SHA256 list, installs the runtime lock with scripts disabled and signs
native bytes. `scripts/build-desktop.py` performs this step before packaging.
To reuse a verified official download, pass `--node-archive` and `--node-checksums`.
The checkout host discovers `apps/desktop/terminal/runtime`; a native web bundle
may carry `terminal/runtime` beside its `web` and `bin` directories. Trusted host
`LOCALBRAIN_TERMINAL_BUNDLE` and optional absolute `LOCALBRAIN_TERMINAL_RUNTIME`
select a separate verified bundle/helper, never browser-supplied context.

Rust owns Terminal setup, settings, service/control and HTTP/WebSocket/CLI
transports, manager IPC/stream and process inspection. The independent Node/PTY
manager and Rust helper retain their immutable payload and lifetime contracts.
Common/Terminal settings use native TOML and OS-zone adapters and publish under
the caller's operations lease. Explicit recovery and other files keep their own
writers. The [Terminal contract](terminal.md) owns lifetime, bounds, app-less
management and safe update/removal.

Use `cargo test --locked -p localbrain-core` and
`cargo test --locked -p localbrain-api` for native contracts. For isolated real
Rust/PTY browser cases, build the opt-in native fixture and supply the public
Terminal bundle:

```bash
cargo build --locked -p localbrain-api --example ui-state-fixture
LOCALBRAIN_TERMINAL_TEST_BUNDLE=/absolute/public/runtime node scripts/qa-terminal-workspace-browser.mjs
```

The native QA fixture isolates HOME/data/cache and cleans up its owned jobs.
For a built app, run
`python3 scripts/qa-terminal-native.py /absolute/LocalBrain.app --evidence /absolute/private-evidence`.
It copies the app, uses synthetic roots and shell HOME, and exercises the actual
macOS host. An unlocked screen and existing accessibility permission are needed
for UI/IME checks; the harness never requests grants or unlocks the Mac.
`--backend-only` covers packaged API, authentication and Quit/app-removal/relaunch
lifetime and explicitly excludes window/IME evidence. Neither mode proves
physical Mac sleep or recipient support.

Build/check shared browser assets with `npm run build:terminal` and
`npm run check:terminal` after `npm ci`; `npm run test:terminal` checks the pinned
renderer/state/input contracts. Runtime lock and browser lock remain separate.
The browser builder selects the published CommonJS entry before ESM output and
checks DECRQM, avoiding a pinned upstream ESM re-minification defect. No user rc,
global npm package, model download or personal-runtime copy is needed.

## Development Web Workflows

The development web server exposes the wider project workflows below. The
distributed macOS app has the narrower [desktop product boundary](desktop-app-and-settings.md#runtime-and-product-boundary).
Ordinary app usage belongs to the [bundled user guides](app-documentation.md).

| Workflow | Entry and owning contract |
| --- | --- |
| Reviewed learning | Dashboard and `/learning`; [Work-Grounded Learning](work-grounded-learning.md) owns reviewed imports, attempts and intervals, and [Code And Command Learning](code-command-learning.md) owns exact scenes and question depth. |
| Work organization | Workstreams and Threads; [Product Model](product.md#workstream-centered-organization) owns user-created organization, linked resources, checkpoints and reversible Suggestions. [Maintenance Task Runner](../operations/claude-task-runner.md) owns Claude-backed organization, checkpoint and priority tasks. |
| Atlassian references | Atlassian; [Explorer contract](atlassian.md#atlassian-explorer-add-connections-sync-and-refresh) distinguishes local Browse, Add and evidence Sync from Connections and remote Refresh. |
| Personal improvement | Sessions Dashboard → Insights; [Personal Improvement Analysis](#personal-improvement-analysis) covers configuration and explicit analysis Runs. |
| Affinity inspection | `/auto-work`; [Auto Work Inspection](auto-work.md#auto-work-inspection) owns the observation-only map and separate earlier sample. |
| Session workflow | Session detail → `작업 흐름`; [Episode and direction](workflow.md#workflow-episode-and-direction) and [correction](workflow.md#workflow-assertion-and-correction) contracts own deterministic lineage and reversible user assertions. |
| Schema reference | System → Schema; [Schema Presentation](schema-presentation.md) owns read-only access to the packaged data model, subject ERDs and table contracts. |

### Reviewed Learning

Open **Dashboard → 학습 목록** for reviewed lessons. Answer first or choose
**설명부터 읽을래요**, then compare the explanation and record your own assessment.
On an article, **읽은 내용을 내 말로 설명해 보기** is optional assisted practice;
**읽은 내용 기록** explicitly records reading and returns to its originating
home or article. **내일 보기**, **숨기기** and **다시 표시** change visibility while
preserving history, without counting as a wrong answer.

Prepare a reviewed JSON packet and import it explicitly:

```bash
localbrain learning import /path/to/lessons.json --reviewed
```

Use `./target/debug/localbrain` after a checkout build, or the native bundle’s
`bin/localbrain`. The
[learning contract and synthetic packet](work-grounded-learning.md) and
[version-2 scene contract](code-command-learning.md) own content, review and
version conditions; import validates structure rather than factual truth.
Source collection and embedding search do not generate or update lessons.

### Search Sessions And Local Context

Use the shared header or `/natural-search`. Keyword mode needs no model. For AI
search, use the included native [model runtime](installation-and-storage.md#native-local-model-runtime) and explicitly prepare its optional assets:

```bash
localbrain models install embedding
localbrain search prepare
localbrain search status
```

In a checkout, use `./target/debug/localbrain`; a native web bundle exposes the
same commands through `bin/localbrain`.
After preparation, select **AI 검색** and try `만들던 앱 관련 세션을 보여줘`.
Restart a running server after changing native code. An index built by the old
Python encoder has a different runtime identity and requires native preparation;
it cannot be silently reused. First
preparation reads all eligible primary-work Sessions and enabled, readable Local
Context bodies; long histories can take substantial time. Maintenance and
subsessions are excluded. Enabled search refreshes after collected material
changes. The [search contract](natural-language-search.md) owns query modes,
model roles, ranking, evidence navigation and recovery; [storage ownership](installation-and-storage.md#natural-language-search-storage)
owns its private index and public model cache.

### Browse The Full-History Affinity Map

Prepare the result with the [full-history simulation commands](development/session-simulation.md#operations),
then open **자동 작업** above **Workstreams**, or `/auto-work`.

- **전체 이력 지도** runs left-to-right in actual message time. Select a strand
  for its full evidence or a knot for that period's original passages.
- Use **선택 주변 확대** to bring the selected neighborhood closer, or
  **세부 묶음 펼치기 → 세션 가까이 보기** for a finer scope.
- Scroll horizontally through time and vertically to other strands, use the
  **← / →** controls, or drag to pan. Zoom/reset and **Ctrl/⌘ + wheel** change
  the view. **전체 기간** fits the full time axis; the initial view is 200%.
- Ordinary scrolling moves the map inside its bounded viewport and the document
  outside it. Back restores the selected view. Only the text list is paginated;
  its pages preserve the map and camera.

Curved strands group similar records, knots show observed activity and dashed
gaps show periods with no observed records. Unknown dates stay unplaced; none
of these marks establishes continuous work duration or causal work relationships.
The [product contract](auto-work.md#auto-work-inspection) owns whole-population
coverage, coarse/finer grouping, occurrence-based knot sizes, overlap and
fragmentation disclosures, title search and narrow/no-script evidence access.

Browsing never starts a model, ingestion or regrouping. Missing, changed or
expired results show recovery rather than a replacement sample. Restart an
already running server after code changes. **이전 표본 · 규칙 기반**
(`/auto-work?mode=sample`) keeps the earlier Session/document comparator; its
**결과 갱신** refreshes only that model-free sample. Its seven-day preview and
the simulation's 30-day derived state retain separate lifecycles.

## Build An Installable Distribution

Build a standalone native web directory from a reviewed source checkout:

```bash
./scripts/check-repo-privacy.sh
python3 scripts/build-api.py --output dist/api
```

The Apple Silicon builder produces `dist/api/bin/localbrain`, `bin/lb`, a sibling
`web/` asset tree, `BUILD-INFO.json` and dependency notices. The executable and
assets stay together. To include an already built public Terminal payload, pass
`--terminal-bundle /absolute/public/runtime`. Ordinary execution needs neither
a checkout nor Rust, Node/npm or Python installation; Terminal has its own
bundled Node runtime when supplied. No wheel or Python dependency environment is
part of native delivery.

Use [native web installation](installation-and-storage.md#alternative-prebuilt-app-and-native-web-installation)
to test the produced directory in a separate working location before publication.
Check startup, empty-source pages, static assets and optional model readiness
there; a checkout test alone does not establish distribution behavior. Runtime
data, local settings, exports, generated reports and weights stay outside the
checkout and deliverable. A local build does not publish a release or establish
that a downloadable artifact already exists.

### Build The macOS App

Build on an Apple Silicon Mac with Xcode Command Line Tools, Rust/Cargo, Node/npm
and Python for standard-library build scripts. The initial
[agent-assisted source installer](installation-and-storage.md#agent-assisted-local-build)
also needs Git. Finished-app users need none of these build tools. Windows builds
still require the planned runtime port and actual target validation.

Cargo must be available in the build shell's PATH. After a rustup installation,
open its configured shell or run `source "$HOME/.cargo/env"` before building;
the builder does not rewrite shell profiles. See the
[official Rust setup](https://rust-lang.github.io/rustup/installation/).

```bash
npm ci --prefix apps/desktop
python3 scripts/build-desktop.py
```

Outputs are `dist/LocalBrain-apple-silicon.zip`, its matching `.sha256`, and the
unpacked app folder. The builder assembles the public Terminal payload, native
`localbrain-backend`, shared web assets and Tauri shell. It includes native
inference code, without copying private runtime directories or shared model
weights. The [desktop runtime contract](desktop-app-and-settings.md#runtime-and-product-boundary)
owns private-path exclusion and absence of Python runtime content/linkage. Data
and settings remain under each user's home. Rust compilation remaps builder-home,
checkout and temporary paths while preserving configured compiler flags. Final
native bytes/resources are checked before ZIP publication; a detected private
build path fails the build.

The [test distribution guide](standalone-test-app-guide.md) owns first launch,
supported-environment evidence, manual replacement and recipient validation.
Uploading a ZIP and notifying others remain separate delivery actions.

After changing ingestion, rebuild/restart the development server and replace the
native app before testing both against the same data directory. Source edits do
not update a running process or packaged backend. Current Session revisions live
in `crates/core/src/backend/ingest/contracts.rs` as positive integers;
increase the affected provider's number when stored Session results require
repair. Explain the rule change in its owner and execution record rather than
inside the constant value. Usage and reference freshness remain independent.
Higher stored Session revisions refuse Sync and reconnection until the app is
updated; force does not bypass this check. See
[the storage contract](data-model/source-registry-and-scans.md#source_files) for
legacy-token conversion and [Architecture](architecture.md#package-ownership)
for native module ownership.

### Build Provenance

`BUILD-INFO.md` includes the Git commit, dirty state, build time and a SHA256
fingerprint of explicit application/build inputs. Packaging checks the same input
fingerprint and commit at completion; changed inputs require a rebuild. Runtime
data, toolchain/dependency caches and generated staging copies are not fingerprint
inputs. The recorded versions and target remain separate from runtime/browser or
recipient verification. A dirty build must not be described as the clean commit.

The builder verifies the candidate app, archive and checksum in an owned staging
directory before publishing them. Existing owned outputs are backed up during
publication and restored if replacement fails; an unowned destination is refused.

## Dependency Certificate Troubleshooting

Keep TLS verification enabled for Cargo/npm dependencies, the official public
Node payload and model downloads. On a managed network, use its approved local
certificate/trust configuration for the tool reporting the error; never disable
certificate checks. The native downloader uses the pinned reqwest/rustls platform
verifier and the OS trust store, without embedding a company certificate.
Python SSL, urllib3 and `uv` environment repair are not backend requirements.
Dependency-download trust does not change the private data/storage boundary.

## Native Runtime And Build-Tool Compatibility

The root workspace and Tauri host declare Rust 1.90 as their minimum. Verify that
minimum as well as the normal toolchain when changing native dependencies:

```bash
cargo +1.90.0 check --workspace --all-targets --locked
cargo +1.90.0 check --manifest-path apps/desktop/src-tauri/Cargo.toml --locked
```

Current build, generation and verification scripts and their tests use the
Python standard library. Historical research commands remain documented under
their retired procedures. Product tools must neither import nor launch an
application Python backend. Native runtime, model and packaging checks remain
required. Other architectures and operating systems need their own execution
evidence. [Retired research procedures](../../plans/research/retired-python-research-tools.md)

## Configuration

LocalBrain reads these environment variables at process startup:

| Variable | Default | Responsibility |
| --- | --- | --- |
| `LOCALBRAIN_DATA_DIR` | `~/Library/Application Support/LocalBrain` | Primary DB, private configuration, model registrations and saved Runs |
| `LOCALBRAIN_CACHE_DIR` | `~/Library/Caches/LocalBrain` | Rebuildable search indexes, simulation and preview results |
| `LOCALBRAIN_CONTEXT_ROOT` | `~/Projects/context` | Legacy Context migration/fallback root. Discovery may run only when no registrations exist, indexed documents already exist and this path is a directory. It selects non-hidden child directories containing Markdown; if none qualify, it selects the root only when top-level Markdown exists. Fresh installs require explicit registration. |
| `LOCALBRAIN_CLAUDE_ROOT` | `~/.claude/projects` | Legacy Claude reader root; new registrations are explicit in settings |
| `LOCALBRAIN_CODEX_ROOT` | `~/.codex/sessions` | Legacy Codex reader root; new registrations are explicit in settings |
| `LOCALBRAIN_CLAUDE_BIN` | resolved from `PATH` | Claude CLI executable used by the Task Runner |
| `LOCALBRAIN_CODEX_BIN` | resolved from `PATH` | Codex CLI executable available to source-neutral external synchronization |
| `LOCALBRAIN_INSIGHT_CODEX_HOME` | `CODEX_HOME`, then existing `~/.codex-company`, then `~/.codex` | Codex profile home for new personal improvement analysis Runs |
| `LOCALBRAIN_INSIGHT_CODEX_MODEL` | `gpt-6-astra` | Model identifier frozen for new personal improvement analysis Runs |
| `LOCALBRAIN_MCP_CALL_BUDGET` | `20` | Advisory legacy-task budget and hard selected-request ceiling for external synchronization |

General user preferences (startup screen, timezone and automatic sync) follow
`settings.toml`, with defaults only for missing fields. The former
`LOCALBRAIN_STARTUP_SCREEN`, `LOCALBRAIN_TIMEZONE`, `LOCALBRAIN_SESSION_SYNC_ENABLED`
and `LOCALBRAIN_SESSION_SYNC_MINUTES` overrides are ignored. The default timezone
comes from the Mac system zoneinfo setting, then UTC, independently of process `TZ`.

For a custom `LOCALBRAIN_DATA_DIR`, an unspecified cache root becomes the sibling
directory `<data-name>-cache`. An explicit `LOCALBRAIN_CACHE_DIR` overrides that
default. Stop the app before moving existing state; use
[the storage migration guide](installation-and-storage.md#upgrade-an-existing-storage-layout).

Do not place secrets in tracked environment files. See [Privacy And Data Handling](privacy-and-data.md) before changing data locations or persistence behavior.

### Personal Improvement Analysis

Open **Sessions Dashboard → Insights**, enter a question and select **질문 분석**,
or select **개선 기회 찾기** without a question. Starting a Run sends selected
local Session excerpts to the model service through Codex CLI and may use
substantial tokens. The report appears below the Run list when complete. Use
**Markdown 다운로드** for a copy to take into a separate work Session; repeating
analysis creates a new Run and preserves earlier reports. The selected profile
and model are retained with each Run; the default model is `gpt-6-astra`.

This optional development-web analyzer uses a Codex CLI execution profile.
`LOCALBRAIN_INSIGHT_CODEX_HOME` takes priority over `CODEX_HOME`; without either setting, an existing `~/.codex-company` home is preferred to `~/.codex`. A new Run freezes that home, selected model, exact prompt and the [guide/result bundle](personal-insights.md#guide-bundle-and-result-contract), including independent core/playbook versions and digests and the response schema. That canonical contract owns current versions and historical report compatibility. Changing environment settings or the package guide affects future Runs only. The guide sources are `crates/core/src/backend/insights/resources/`; private evidence, prompts, responses, validated results, diagnostics, and reports are kept under `<LOCALBRAIN_DATA_DIR>/personal-insight-runs/<id>/`, outside Git. An explicit Run start sends selected Session excerpts to the configured model service; opening the screen or a past report does not.

Run creation requires exactly one Codex Source row whose resolved root
matches the resolved `<selected-home>/sessions` path; missing or ambiguous matches
refuse creation. The [analysis contract](personal-insights.md#personal-improvement-analysis-runs)
also requires revalidating the frozen Source ID, provider and path binding before
CLI launch.

New findings use the existing work-session handoff to explain the proposed application mechanism, target, concrete content, actors, activation, setup and repeated work. The [application contract](personal-insights.md#concrete-application-handoff) distinguishes temporary trials, conditional adoption and unresolved placement facts. This guide requirement is evaluated semantically; the JSON validator only enforces its existing structural rules.

The [existing-proposal contract](personal-insights.md#existing-proposal-follow-through) distinguishes mention, application, outcome and deferral from supplied evidence. A useful next step can carry an earlier proposal forward without inventing a new method. These are generation rules; the product does not persist an adoption state or infer it from a report's existence.

The analysis launcher resolves the Codex executable before starting it and grants its sandboxed startup helpers read access to that exact binary. The profile home is used for client authentication and is not added to the command filesystem allowlist. Artifact writes and command network access remain blocked. Restart a server that was already running when runner code changed before submitting a new analysis.

Run detail displays the same stored estimated cost used by Usage & Cost, with its calculation state and frozen price basis in the existing settings disclosure. Missing usage or pricing stays explicitly unavailable, and any CLI-reported amount remains separately labeled. Estimates are API-equivalent trend costs, not subscription bills. Startup seeds exact GPT-6.1 Sol Standard/Fast snapshots effective 2026-09-29 and fills eligible previously unpriced records using retained evidence; already-priced records are preserved.

Discovery uses deterministic [source/month sampling](personal-insights.md#evidence-selection-and-excerpts), not a random project picker. Within each source/month group it prefers recently active Sessions; project balance and prior recommendation history are not selection inputs. The [current guide bundle](personal-insights.md#guide-bundle-and-result-contract) supplies all eleven bounded playbooks under the [Product decision rules](personal-insights.md#personal-improvement-finding-decisions). The model identifies the owner's goal and observed friction before choosing a type; incidental words in quoted source material do not exclude types before analysis. A reported candidate is not a global priority ranking, and repeating discovery does not promise a different project or a new recommendation. Insights shows frozen selected/eligible counts, sources, time coverage, and truncation; each new report explains the candidate and finding type with source anchors.

For conversation requests, report v3 identifies up to five missing messages by a supplied anchor and frozen eligible-message position. Local validation rejects requests for already supplied complete messages; a clipped message can be requested in full. The product renders the request from those validated positions, not free-form resend instructions. Unknown current goals/outcomes use separate bounded questions and are checked semantically by the guide; positional validation alone cannot detect every redundant factual question. Invalid results fail without automatic paid retry, retaining emitted usage and diagnostics.

### Session Source Configuration

Application startup creates `<LOCALBRAIN_DATA_DIR>/session-sources.toml` with
mode `0600` when it is first absent. The file is the established local AI
Session-source authority and contains an ordered `schema_version = 2` list:

```toml
schema_version = 2

[[session_sources]]
source_id = 1
provider_kind = "codex"
display_label = "Personal"
root = "/absolute/path/to/agent-home/sessions"
color = "green"
```

A fresh file contains `session_sources = []`; the example above is an explicitly
registered profile, not a default registration. The ID is the local `sources.id` PK; it is not
a provider code or editable nickname. An existing DB's registered
sources seed a missing file during upgrade. Existing files keep their IDs, roots
and order, independent of legacy root environment variables. Settings add optional
`agent_home` and `enabled` fields (`enabled` defaults to true for older files).

Missing roots retain imported data and report unavailability. Invalid files,
provider conflicts, manually omitted entries and unconfirmed root changes preserve
existing records. The settings UI coordinates confirmed same-source reconnection;
registration removal writes `enabled = false`, stops collection/search and retains
browseable imported records. Re-registering retains the original identity. See
[the source lifecycle contract](desktop-app-and-settings.md#source-lifecycle-contract).

Sessions synchronization dispatches every enabled, validated entry in file order, using
one transaction per Source. The structured report names every Source and records
latest attempt, latest success, outcome, counts, and a bounded consequence. A
missing or invalid root never authorizes stale deletion; only a completed scan of
the accepted, readable root can establish missing originals. The
[retained-history contract](session-ingestion.md#retained-native-history-and-presence)
owns that reconciliation and preserves collected Sessions and descendants. The
Sources scan applies the same Session-source behavior before scanning enabled
Local Context roots.

## Change Approach

Use [Change Scope And Regression Control](change-scope-and-regression.md) to decide
which dependent edits belong in the task and to diagnose unexpected behavior
changes. The implementation practices below remain owned by this guide.

- Read the touched modules, tests, and owner docs first.
- Reuse current Axum, SQLite, MiniJinja and shared Rust service patterns before introducing a new abstraction.
- Keep migrations additive by default. An approved structural repair must be separately bounded and supply backup, preflight, rollback, exact preservation, idempotency, and fresh/compatible parity evidence until a deliberate migration framework replaces the startup path.
- Preserve source IDs, timestamps, provenance, and user review state when changing ingestion or relationships.
- Keep maintenance artifacts excluded from ordinary Session and Local Context ingestion.

### Schema Documentation Changes

- `crates/core/resources/schema.sql` owns fresh-database DDL. `backend/storage/migrations.rs` orders startup, its `migrations/` modules own compatible changes and runtime-only indexes, and `backend/db.rs` retains public connection/initialization helpers. HTTP/CLI transaction boundaries remain host-owned. This split introduces no migration registry or new execution system.
- The [Data Model](data-model.md) and its subject-area catalogs are the complete current human-readable baseline.
- Keep later planning and execution artifacts delta-scoped: name only the affected schema objects, contract behavior, migrations, tests, and owner documents.
- Update the affected subject-area catalog in place so durable data-model documentation continues to describe the complete current state. Do not copy unrelated tables or domains into each later change artifact.
- Update the global ERD only for object additions or removals, subject-owner changes, or cross-domain relationship changes. Update a focused ERD only when its visible keys, constraints, relations, cascades, or ownership change.
- Update Project Architecture only when runtime ownership, persistence boundaries, or cross-domain behavior changes. A local table or column delta does not require restating the complete persistence model there.
- Complete schema and documentation changes in the same approved execution boundary, with focused contract tests and a fresh-schema versus compatible-migration parity check.

### Local Mermaid Browser Assets

- LocalBrain pins Mermaid `11.16.0` and the official `@mermaid-js/layout-elk` `0.2.2` loader as project dependencies and esbuild `0.28.1` as its build-only bundler in the repository-owned `package.json` and `package-lock.json`.
- The packages come from the public npm distributions named `mermaid`, `@mermaid-js/layout-elk`, `elkjs`, and `esbuild`. Mermaid, the layout loader, and esbuild are MIT-licensed; the transitive `elkjs` `0.9.3` engine is EPL-2.0. Reviewed copies of all four licenses are emitted with the browser asset and the lockfile retains exact integrity metadata.
- For Mermaid rendering, Node.js `20` or later and npm are required only when installing or updating its browser build inputs. This rendering path does not invoke Node, npm, a CDN, or an external renderer from the native backend, installed `localbrain` command, or web runtime. The [optional macOS terminal](#optional-macos-terminal) has a separate bundled Node runtime and explicit offline preparation.
- Install the exact lockfile graph and generate the reviewed output set with:

```bash
npm ci --no-audit
npm run build:mermaid
```

- Generated browser outputs belong under `apps/web/static/vendor/mermaid/`. The asset manifest records the lockfile digest, exact direct versions, licenses, and output digests. The native web/app builders include this directory through `apps/web/static/` ownership.
- Verify both freshness and the deliberate stale-output failure path with:

```bash
npm run check:mermaid
npm run test:mermaid
```

- Application screens consume `apps/web/static/mermaid-adapter.js`, not npm paths directly. The adapter initializes Mermaid once with strict security, registers the locally bundled official ELK loaders, never scans the page automatically, and renders only application-owned nodes marked `data-localbrain-mermaid="owned"` whose source is LocalBrain-authored markup. Schema-owned nodes additionally request ELK; one failed ELK attempt retries the unchanged source with Dagre, then preserves the textual fallback. Other Mermaid consumers remain on their existing default. Imported documents, Session content, persisted rows, request/query values, and arbitrary user text must never be inserted into those source nodes.
- To update Mermaid, change its exact version in `package.json`, regenerate `package-lock.json` against the public npm registry, run the build and test commands, review dependency and license changes, then commit the manifest and all generated outputs together. Never commit `node_modules`, npm caches, temporary builds, or browser downloads.

### Schema Presentation Data

- The complete semantic baseline remains in [Data Model](data-model.md); [Schema Presentation](schema-presentation.md) defines the package-owned v1 consumer shape.
- After an approved schema or Data Model change passes its owner checks, regenerate and verify the derived package data:

```bash
python3 scripts/check-data-model-docs.py
node scripts/check-data-model-mermaid.mjs
python3 scripts/build-schema-presentation.py build
python3 scripts/build-schema-presentation.py check
```

- Generation uses SQLite `:memory:` and invokes compatible structure/index migrations with data migrations disabled. It must not open the configured database, inspect Context roots, read runtime rows, or serialize machine state.
- Commit `crates/core/resources/schema-presentation.json` with the source change. Later application screens load it only through `backend::schema`; missing or invalid package data stays a bounded unavailable state and never triggers runtime introspection.

### Data Model Value Dictionaries

- `crates/core/resources/value-registry.json` is the executable authority for bounded physical values, logical axes, complete presentation modes, fallbacks, labels, and visible-consumer inventory.
- [Value Dictionaries](data-model/value-dictionaries.md) and its eleven subject companions are generated projections. Runtime templates and handlers use `backend::value_registry`; they do not parse Markdown.
- A family uses exactly one complete mode: `direct`, `logical-label`, or `internal-only`. If any allowed value needs interpretation, map the complete family. Missing values never fall back to raw tokens.
- After changing a covered schema constraint, application constant, derived family, boolean-like field, mapping, or visible consumer, rebuild and check:

```bash
python3 scripts/build-data-model-value-dictionaries.py build
python3 scripts/build-data-model-value-dictionaries.py check
python3 scripts/check-data-model-docs.py
```

- Commit the registry and all generated dictionaries together. `check-data-model-docs.py` compares schema `CHECK` vocabularies, selected application constants, required boolean and derived inventories, reciprocal links, consumer declarations, and generated bytes.

### Schema Explorer Verification

- With LocalBrain running locally, verify the read-only `/schema` route, exact supported widths, URL selection, history/focus, rapid selection, local Mermaid failure, and no-script fallback with the dependency-free Chrome QA harness:

```bash
node scripts/qa-schema-explorer-browser.mjs http://127.0.0.1:8000 /tmp/localbrain-schema-browser-qa
```

- The harness uses a temporary Chrome profile and writes synthetic schema-only screenshots to the requested output directory. Set `LOCALBRAIN_CHROME_PATH` only when Chrome is installed outside the normal macOS application path.
- Schema Explorer's browser rendering requires neither Node nor npm. Node is used in this verification workflow only by the repository harness and the Mermaid build/check commands.

## Verification

Run the repository privacy check before tests or staging:

```bash
./scripts/check-repo-privacy.sh
```

The check scans tracked and non-ignored untracked candidates, blocks runtime and credential file types, checks common personal-path and secret patterns, and requires explicit review for binary or media files. The repository's pre-commit hook runs the same command after `core.hooksPath` is configured as shown above.

For private names, project titles, URLs, or phrases that generic detection cannot identify, create `.privacy-patterns.local` from `.privacy-patterns.local.example`. The local denylist uses one literal phrase per line and is excluded from Git. Add a binary or media path to `.privacy-allowlist` only after verifying that its contents are synthetic or approved for publication.

Run the full current suite:

```bash
cargo +1.90.0 test --workspace --all-targets --locked
python3 -B -m unittest discover -s tests -v
npm run test:terminal
npm run test:workflow-map
```

For parser, schema, ingestion, retrieval, or Task Runner changes, add focused tests for the changed contract. For user-facing changes, start the server and verify affected routes and states in a browser.

For initial settings, setup recovery, long pinned paths and empty Run output, run
the synthetic browser regressions with Node 22+ and Chrome:

```bash
cargo build --locked -p localbrain-api --example ui-state-fixture
node scripts/qa-ui-states-browser.mjs
```

The command starts its own loopback backend with isolated settings, source files,
database and browser profile outside the repository. It does not use the running
app's data, collect personal sources, download models or execute agents. The
fixture is [apps/api/examples/ui-state-fixture.rs](../../../apps/api/examples/ui-state-fixture.rs),
launched by `scripts/native-qa-fixture.mjs`; its private test routes are absent
from production. Set `LOCALBRAIN_CHROME_PATH` or `LOCALBRAIN_QA_EXECUTABLE` only
when Chrome or the built native fixture is elsewhere.

The checks sample preference labels and content position before and after a held
read, real synthetic registry corruption and retry, model-read failure and polling
recovery, pending save/reopen, focus containment, setup asset failure/reload,
wizard draft/reduced motion, four viewport widths and Run output transitions.
Waiting only for the final screenshot misses these initial-state defects. The
test uses controlled delays and failures; its timing is not a universal animation
threshold or a claim about all application screens or the packaged native host.
The report retains the actual first-load, warm-reopen and shortcut frame samples.
Held-read checks require observed pending and ready phases; every anchor
comparison requires multiple samples. An empty or single sample cannot establish
stability. These are rendered DOM observations, not compositor-paint measurements.
Here, warm reopen means reopening Settings in the same page with retained client
state while the network cache remains disabled. Cache-enabled page revisits in
the broader audit matrix remain a separate condition. Selective-delay checks
also hold search readiness independently of settings and storage independently
of model cancellation; unrelated reads must not gate confirmed actions.
The same cases distinguish pending search from failure, an acknowledged synthetic
model action from its background refresh, and a failed model poll from a pending
search response. Model-action responses are intercepted; no model job is started.

By default it removes its temporary evidence after reporting the result. To
inspect screenshots and the JSON report, pass an explicit output parent outside
the repository. The script creates a new task-owned child directory, removes its
backend and browser state on exit, and retains only the report/captures there.
Review those artifacts locally and remove that child when the investigation ends.
For broader visual/state coverage, follow the
[initial-state audit plan](../../plans/design/initial-state-and-transition-audit-plan.md)
and record the checked routes, fixtures, host, input mechanism and remaining gaps.

Do not claim full verification when a required local source, macOS permission, Claude CLI, or external connector is unavailable.

## Documentation Updates

- Update `README.md` when the product overview, installation entry or first-use path changes. Keep it focused on the distributed app rather than adding development progress or detailed screen contracts.
- Update the owning [app guide](app-documentation.md) for user-visible screen usage, settings and recovery procedures. Keep development-web usage and build commands in this guide.
- Update [Product Model](product.md) for durable product and organization rules.
- Update [Project Architecture](architecture.md) for runtime ownership, source adapters, data model, or ingestion behavior.
- Update only the affected [data-model subject documents](data-model.md) for ordinary schema deltas; update their entry map when subject files or cross-domain ownership changes.
- Update [Maintenance Task Runner](../operations/claude-task-runner.md) for in-app maintenance execution or review semantics.
- Update [Project Roadmap](../../plans/project/roadmap.md) for sequencing and [Project Backlog](../../plans/project/backlog.md) for unresolved work.

## Local Model Development Tools

Use [Model Tool Operations](development/model-tools.md) for native model commands,
search verification, full-history simulation and inference-performance limits.
Current product regression tests are native Rust; Python tests cover the active
build/check tools. Obsolete Python research implementations, comparisons,
compatibility launchers and their tests are retired. Their former procedures live
in [the research record](../../plans/research/retired-python-research-tools.md),
not a runnable fallback. Retirement does not reactivate paused or blocked trials.
