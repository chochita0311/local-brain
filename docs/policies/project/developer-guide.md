# Developer Guide

## Prerequisites

- macOS for the current Apple Notes integration and default data location
- Python 3.11 recommended; package metadata accepts Python 3.9 or later
- `uv` for dependency and virtual environment management
- Claude CLI only for Claude-backed maintenance Runs
- Codex CLI for personal improvement analysis Runs or when selecting Codex for external synchronization

## Setup And Run

Use [macOS Installation And Local Storage](installation-and-storage.md) for a
new machine, packaged app installation, optional models, and recovery retention.

Activate the repository-owned pre-commit hook after cloning:

```bash
git config core.hooksPath .githooks
```

Install dependencies:

```bash
uv sync --python 3.11 --frozen
```

Initialize or refresh indexed sources:

```bash
uv run localbrain scan --full
```

Run the development server:

```bash
uv run --no-sync localbrain serve
```

Open `http://127.0.0.1:8000`.

For source reload during development, use
`uv run --no-sync uvicorn localbrain.main:app --host 127.0.0.1 --reload --no-access-log`.

Source reload does not update the frozen backend inside a previously built
`LocalBrain.app`. App and web backends using the same data directory share the
normalized database and synchronization health. Their writer lock serializes
collection. Current runtimes additionally reject a source whose stored numeric
Session revision is newer; unmodified older builds lack that admission check and
can still reparse newer results. After a parser update,
stop incompatible older backends or rebuild and restart the app before allowing
both to collect into that store. Then run ordinary Session Sync with the updated
backend. A corrected source checkout or one successful web Sync alone does not
update the packaged app or prevent a later old-version reparse.

Install optional local-model dependencies with
`uv sync --python 3.11 --extra local-models --frozen`;
`uv run --no-sync localbrain models install embedding` verifies public model
assets and records LocalBrain's installation metadata. `uv run --no-sync localbrain doctor` and
`uv run --no-sync localbrain models status` inspect readiness without reading sources or
downloading/running models.

## Development Web Workflows

The development web server exposes the wider project workflows below. The
distributed macOS app has the narrower [desktop product boundary](desktop-app-and-settings.md#runtime-and-product-boundary).
Ordinary app usage belongs to the [bundled user guides](app-documentation.md).

| Workflow | Entry and owning contract |
| --- | --- |
| Reviewed learning | Dashboard and `/learning`; [Work-Grounded Learning](work-grounded-learning.md) owns reviewed imports, attempts and intervals, and [Code And Command Learning](code-command-learning.md) owns exact scenes and question depth. |
| Work organization | Workstreams and Threads; [Product Model](product.md#workstream-centered-organization) owns user-created organization, linked resources, checkpoints and reversible Suggestions. [Maintenance Task Runner](../operations/claude-task-runner.md) owns Claude-backed organization, checkpoint and priority tasks. |
| Atlassian references | Atlassian; [Explorer contract](product.md#atlassian-explorer-add-connections-sync-and-refresh) distinguishes local Browse, Add and evidence Sync from Connections and remote Refresh. |
| Personal improvement | Sessions Dashboard → Insights; [Personal Improvement Analysis](#personal-improvement-analysis) covers configuration and explicit analysis Runs. |
| Affinity inspection | `/auto-work`; [Auto Work Inspection](product.md#auto-work-inspection) owns the observation-only map and separate earlier sample. |
| Session workflow | Session detail → `작업 흐름`; [Episode and direction](product.md#workflow-episode-and-direction) and [correction](product.md#workflow-assertion-and-correction) contracts own deterministic lineage and reversible user assertions. |
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

Prefix the command with `uv run --no-sync` in a source checkout. The
[learning contract and synthetic packet](work-grounded-learning.md) and
[version-2 scene contract](code-command-learning.md) own content, review and
version conditions; import validates structure rather than factual truth.
Source collection and embedding search do not generate or update lessons.

### Search Sessions And Local Context

Use the shared header or `/natural-search`. Keyword mode needs no model. For AI
search in a source checkout, install the [optional model runtime](installation-and-storage.md#install-the-local-model-runtime), then run:

```bash
uv run --no-sync localbrain models install embedding
uv run --no-sync localbrain search prepare
uv run --no-sync localbrain search status
```

Installed Python/web applications use the same commands without `uv run --no-sync`.
After preparation, select **AI 검색** and try `만들던 앱 관련 세션을 보여줘`.
Restart a running server after changing code or model dependencies. First
preparation reads all eligible primary-work Sessions and enabled, readable Local
Context bodies; long histories can take substantial time. Maintenance and
subsessions are excluded. Enabled search refreshes after collected material
changes. The [search contract](natural-language-search.md) owns query modes,
model roles, ranking, evidence navigation and recovery; [storage ownership](installation-and-storage.md#natural-language-search-storage)
owns its private index and public model cache.

### Browse The Full-History Affinity Map

Prepare the result with the [full-history simulation commands](#full-history-simulation-and-model-trials),
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
The [product contract](product.md#auto-work-inspection) owns whole-population
coverage, coarse/finer grouping, occurrence-based knot sizes, overlap and
fragmentation disclosures, title search and narrow/no-script evidence access.

Browsing never starts a model, ingestion or regrouping. Missing, changed or
expired results show recovery rather than a replacement sample. Restart an
already running server after code changes. **이전 표본 · 규칙 기반**
(`/auto-work?mode=sample`) keeps the earlier Session/document comparator; its
**결과 갱신** refreshes only that model-free sample. Its seven-day preview and
the simulation's 30-day derived state retain separate lifecycles.

## Build An Installable Distribution

Build from a reviewed source checkout:

```bash
./scripts/check-repo-privacy.sh
uv build
```

The wheel and source archive are written to `dist/`. The wheel contains the
application code, templates, browser assets, schema and package guides. Runtime
data, model weights and private evaluation archives stay outside the checkout
and distribution. Do not add local settings, exports or generated reports to a
package. Follow the [standalone installation guide](installation-and-storage.md#install-a-distribution-wheel)
to install the wheel in a separate environment and working directory before
publishing it. Check startup, the empty-source pages, static assets and optional
model prerequisites from that environment; a source-checkout run alone does not
establish that a distribution works. Building a wheel does not publish a release
or provide a native macOS executable.

### Build The macOS App

Build on an Apple Silicon Mac with Xcode Command Line Tools, Rust stable and
Node. Recipients do not need these build tools.

Cargo must be available in the build shell's PATH. After a rustup installation,
open its configured shell or run `source "$HOME/.cargo/env"` before building;
the build does not rewrite shell profiles. See the [official Rust setup](https://rust-lang.github.io/rustup/installation/).

```bash
uv sync --python 3.11 --extra local-models --extra desktop-build --frozen
npm ci --prefix desktop
uv run --no-sync python scripts/build-desktop.py
```

Outputs are `dist/LocalBrain-apple-silicon.zip`, its matching `.sha256`, and the
unpacked app folder. The build includes the source package and execution
libraries without copying private runtime folders or shared public model weights.
The [desktop runtime contract](desktop-app-and-settings.md#runtime-and-product-boundary)
owns bundled Python path resolution and rejection of private build paths,
including compressed Python code. Data and settings stay under each user's home.
Rust compilation also remaps builder-home, checkout and temporary paths while
preserving configured compiler flags. The resulting app is scanned before ZIP
creation; a detected private path fails the build rather than producing a new archive.
The [test distribution guide](standalone-test-app-guide.md) owns first launch,
supported-environment evidence, manual replacement and recipient validation.
Uploading the program ZIP to internal Drive and notifying teammates are separate
delivery actions.

After changing ingestion, restart the development server unless it runs with
reload, and rebuild/replace the native app before testing against the same data
directory. A source edit does not update an already running process or frozen
backend. Current Session revisions live in `ingest/contracts.py` as positive
integers; increase the affected provider's number when stored Session results
must be repaired. Explain the rule change in its owner document and execution
record rather than encoding that description into the constant value. Usage and
reference freshness remain independent. Higher stored Session revisions refuse
Sync and reconnection until the running application is updated; force does not
bypass this check. See [the storage contract](data-model/source-registry-and-scans.md#source_files)
for legacy-token conversion and [Architecture](architecture.md#ingestion-module-ownership)
for module ownership.

## Dependency Certificate Troubleshooting

The default `uv sync` command verifies PyPI with uv's bundled certificate roots and should work on a normal network. If it fails with `UnknownIssuer` on a managed network, a proxy or security product may be using a certificate authority trusted by macOS but not included in uv's bundled roots.

Retry the failed installation using the macOS system certificate store:

```bash
uv sync --system-certs
```

The flag applies to that command only. If later `uv` commands also need network access through the same managed network, set `UV_SYSTEM_CERTS=true` for the current shell before running them. Do not disable TLS verification. This setting affects dependency downloads only; it does not change where LocalBrain stores or processes indexed data.

## Python Runtime Compatibility

Use the uv-managed Python 3.11 environment shown above for installation and
verification.
Package metadata accepts Python 3.9 or later; it does not establish that every
system-provided runtime has been verified. See [LibreSSL environment repair](installation-and-storage.md#repair-an-existing-libressl-based-environment)
when the interpreter, rather than server logging, needs replacement.

## Configuration

LocalBrain reads these environment variables at process startup:

| Variable | Default | Responsibility |
| --- | --- | --- |
| `LOCALBRAIN_DATA_DIR` | `~/Library/Application Support/LocalBrain` | Primary DB, private configuration, model registrations and saved Runs |
| `LOCALBRAIN_CACHE_DIR` | `~/Library/Caches/LocalBrain` | Rebuildable search indexes, simulation and preview results |
| `LOCALBRAIN_DEVELOPMENT_DIR` | `~/Library/Application Support/LocalBrain-Development` | Explicit development evaluations; never created by ordinary app startup |
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

For a custom `LOCALBRAIN_DATA_DIR`, unspecified cache/development locations are sibling directories named `<data-name>-cache` and `<data-name>-development`. Explicit variables override those defaults. Stop the app before moving existing state; use [the storage migration guide](installation-and-storage.md#upgrade-an-existing-storage-layout).

Do not place secrets in tracked environment files. See [Privacy And Data Handling](privacy-and-data.md) before changing data locations or persistence behavior.

### Personal Improvement Analysis

Open **Sessions Dashboard → Insights**, enter a question and select **질문 분석**,
or select **개선 기회 찾기** without a question. Starting a Run sends selected
local Session excerpts to the model service through Codex CLI and may use
substantial tokens. The report appears below the Run list when complete. Use
**Markdown 다운로드** for a copy to take into a separate work Session; repeating
analysis creates a new Run and preserves earlier reports. The selected profile
and model are retained with each Run; the default model is `gpt-6-astra`.

The Insights analyzer uses Codex CLI. `LOCALBRAIN_INSIGHT_CODEX_HOME` takes priority over `CODEX_HOME`; without either setting, an existing `~/.codex-company` home is preferred to `~/.codex`. A new Run freezes that home, selected model, exact prompt and the [guide/result bundle](architecture.md#guide-bundle-and-result-contract), including independent core/playbook versions and digests and the response schema. That canonical contract owns current versions and historical report compatibility. Changing environment settings or the package guide affects future Runs only. The guide sources are `src/localbrain/personal_insight_guides/`; private evidence, prompts, responses, validated results, diagnostics, and reports are kept under `<LOCALBRAIN_DATA_DIR>/personal-insight-runs/<id>/`, outside Git. An explicit Run start sends selected Session excerpts to the configured model service; opening the screen or a past report does not.

New findings use the existing work-session handoff to explain the proposed application mechanism, target, concrete content, actors, activation, setup and repeated work. The [application contract](product.md#concrete-application-handoff) distinguishes temporary trials, conditional adoption and unresolved placement facts. This guide requirement is evaluated semantically; the JSON validator only enforces its existing structural rules.

The [existing-proposal contract](product.md#existing-proposal-follow-through) distinguishes mention, application, outcome and deferral from supplied evidence. A useful next step can carry an earlier proposal forward without inventing a new method. These are generation rules; the product does not persist an adoption state or infer it from a report's existence.

The analysis launcher resolves the Codex executable before starting it and grants its sandboxed startup helpers read access to that exact binary. The profile home is used for client authentication and is not added to the command filesystem allowlist. Artifact writes and command network access remain blocked. Restart a server that was already running when runner code changed before submitting a new analysis.

Run detail displays the same stored estimated cost used by Usage & Cost, with its calculation state and frozen price basis in the existing settings disclosure. Missing usage or pricing stays explicitly unavailable, and any CLI-reported amount remains separately labeled. Estimates are API-equivalent trend costs, not subscription bills. Startup seeds exact GPT-6.1 Sol Standard/Fast snapshots effective 2026-09-29 and fills eligible previously unpriced records using retained evidence; already-priced records are preserved.

Owner-requested guide evaluations can retain frozen inputs, raw outputs, and review reports under `<LOCALBRAIN_DEVELOPMENT_DIR>/personal-insight-evaluations/<id>/`, with owner-only access. This private archive is separate from product Run records: subagent simulations do not create Insights history rows. Tracked evaluation documents contain only sanitized conclusions.

Discovery uses deterministic [source/month sampling](architecture.md#evidence-selection-and-excerpts), not a random project picker. Within each source/month group it prefers recently active Sessions; project balance and prior recommendation history are not selection inputs. The [current guide bundle](architecture.md#guide-bundle-and-result-contract) supplies all eleven bounded playbooks under the [Product decision rules](product.md#personal-improvement-finding-decisions). The model identifies the owner's goal and observed friction before choosing a type; incidental words in quoted source material do not exclude types before analysis. A reported candidate is not a global priority ranking, and repeating discovery does not promise a different project or a new recommendation. Insights shows frozen selected/eligible counts, sources, time coverage, and truncation; each new report explains the candidate and finding type with source anchors.

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
the accepted, present root may reconcile disappeared JSONL for that Source. The
Sources scan applies the same Session-source behavior before scanning enabled
Local Context roots.

## Change Approach

- Read the touched modules, tests, and owner docs first.
- Reuse current FastAPI, SQLite, Jinja2, and local helper patterns before introducing a new abstraction.
- Keep migrations additive by default. An approved structural repair must be separately bounded and supply backup, preflight, rollback, exact preservation, idempotency, and fresh/compatible parity evidence until a deliberate migration framework replaces the startup path.
- Preserve source IDs, timestamps, provenance, and user review state when changing ingestion or relationships.
- Keep maintenance artifacts excluded from ordinary Session and Local Context ingestion.

### Schema Documentation Changes

- `src/localbrain/schema.sql` owns fresh-database DDL, and `src/localbrain/db.py` owns compatible startup migrations and runtime-only indexes until an approved migration system replaces that split.
- The [Data Model](data-model.md) and its subject-area catalogs are the complete current human-readable baseline.
- Keep later planning and execution artifacts delta-scoped: name only the affected schema objects, contract behavior, migrations, tests, and owner documents.
- Update the affected subject-area catalog in place so durable data-model documentation continues to describe the complete current state. Do not copy unrelated tables or domains into each later change artifact.
- Update the global ERD only for object additions or removals, subject-owner changes, or cross-domain relationship changes. Update a focused ERD only when its visible keys, constraints, relations, cascades, or ownership change.
- Update Project Architecture only when runtime ownership, persistence boundaries, or cross-domain behavior changes. A local table or column delta does not require restating the complete persistence model there.
- Complete schema and documentation changes in the same approved execution boundary, with focused contract tests and a fresh-schema versus compatible-migration parity check.

### Local Mermaid Browser Assets

- LocalBrain pins Mermaid `11.16.0` and the official `@mermaid-js/layout-elk` `0.2.2` loader as project dependencies and esbuild `0.28.1` as its build-only bundler in the repository-owned `package.json` and `package-lock.json`.
- The packages come from the public npm distributions named `mermaid`, `@mermaid-js/layout-elk`, `elkjs`, and `esbuild`. Mermaid, the layout loader, and esbuild are MIT-licensed; the transitive `elkjs` `0.9.3` engine is EPL-2.0. Reviewed copies of all four licenses are emitted with the browser asset and the lockfile retains exact integrity metadata.
- Node.js `20` or later and npm are required only when installing or updating browser build inputs. The Python application, installed `localbrain` command, and web runtime do not invoke Node, npm, a CDN, or an external renderer.
- Install the exact lockfile graph and generate the reviewed output set with:

```bash
npm ci --no-audit
npm run build:mermaid
```

- Generated browser outputs belong under `src/localbrain/static/vendor/mermaid/`. The asset manifest records the lockfile digest, exact direct versions, licenses, and output digests. The Python package includes this directory through `src/localbrain/static/` ownership.
- Verify both freshness and the deliberate stale-output failure path with:

```bash
npm run check:mermaid
npm run test:mermaid
```

- Application screens consume `src/localbrain/static/mermaid-adapter.js`, not npm paths directly. The adapter initializes Mermaid once with strict security, registers the locally bundled official ELK loaders, never scans the page automatically, and renders only application-owned nodes marked `data-localbrain-mermaid="owned"` whose source is LocalBrain-authored markup. Schema-owned nodes additionally request ELK; one failed ELK attempt retries the unchanged source with Dagre, then preserves the textual fallback. Other Mermaid consumers remain on their existing default. Imported documents, Session content, persisted rows, request/query values, and arbitrary user text must never be inserted into those source nodes.
- To update Mermaid, change its exact version in `package.json`, regenerate `package-lock.json` against the public npm registry, run the build and test commands, review dependency and license changes, then commit the manifest and all generated outputs together. Never commit `node_modules`, npm caches, temporary builds, or browser downloads.

### Schema Presentation Data

- The complete semantic baseline remains in [Data Model](data-model.md); [Schema Presentation](schema-presentation.md) defines the package-owned v1 consumer shape.
- After an approved schema or Data Model change passes its owner checks, regenerate and verify the derived package data:

```bash
uv run python scripts/check-data-model-docs.py
node scripts/check-data-model-mermaid.mjs
uv run python scripts/build-schema-presentation.py build
uv run python scripts/build-schema-presentation.py check
```

- Generation uses SQLite `:memory:` and invokes compatible structure/index migrations with data migrations disabled. It must not open the configured database, inspect Context roots, read runtime rows, or serialize machine state.
- Commit `src/localbrain/schema-presentation.json` with the source change. Later application screens load it only through `localbrain.schema_presentation.load_schema_presentation`; missing or invalid package data stays a bounded unavailable state and never triggers runtime introspection.

### Data Model Value Dictionaries

- `src/localbrain/value-registry.json` is the executable authority for bounded physical values, logical axes, complete presentation modes, fallbacks, labels, and visible-consumer inventory.
- [Value Dictionaries](data-model/value-dictionaries.md) and its eleven subject companions are generated projections. Runtime templates and handlers use `localbrain.value_registry`; they do not parse Markdown.
- A family uses exactly one complete mode: `direct`, `logical-label`, or `internal-only`. If any allowed value needs interpretation, map the complete family. Missing values never fall back to raw tokens.
- After changing a covered schema constraint, application constant, derived family, boolean-like field, mapping, or visible consumer, rebuild and check:

```bash
uv run python scripts/build-data-model-value-dictionaries.py build
uv run python scripts/build-data-model-value-dictionaries.py check
uv run python scripts/check-data-model-docs.py
```

- Commit the registry and all generated dictionaries together. `check-data-model-docs.py` compares schema `CHECK` vocabularies, selected application constants, required boolean and derived inventories, reciprocal links, consumer declarations, and generated bytes.

### Schema Explorer Verification

- With LocalBrain running locally, verify the read-only `/schema` route, exact supported widths, URL selection, history/focus, rapid selection, local Mermaid failure, and no-script fallback with the dependency-free Chrome QA harness:

```bash
node scripts/qa-schema-explorer-browser.mjs http://127.0.0.1:8000 /tmp/localbrain-schema-browser-qa
```

- The harness uses a temporary Chrome profile and writes synthetic schema-only screenshots to the requested output directory. Set `LOCALBRAIN_CHROME_PATH` only when Chrome is installed outside the normal macOS application path.
- Browser runtime still requires neither Node nor npm. Node is used here only by the repository verification harness and by the existing Mermaid build/check workflow.

## Verification

Run the repository privacy check before tests or staging:

```bash
./scripts/check-repo-privacy.sh
```

The check scans tracked and non-ignored untracked candidates, blocks runtime and credential file types, checks common personal-path and secret patterns, and requires explicit review for binary or media files. The repository's pre-commit hook runs the same command after `core.hooksPath` is configured as shown above.

For private names, project titles, URLs, or phrases that generic detection cannot identify, create `.privacy-patterns.local` from `.privacy-patterns.local.example`. The local denylist uses one literal phrase per line and is excluded from Git. Add a binary or media path to `.privacy-allowlist` only after verifying that its contents are synthetic or approved for publication.

Run the full current suite:

```bash
uv run python -m unittest discover -s tests -v
```

For parser, schema, ingestion, retrieval, or Task Runner changes, add focused tests for the changed contract. For user-facing changes, start the server and verify affected routes and states in a browser.

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

These tools require a source checkout. A normal installed application uses the
packaged commands in [the installation guide](installation-and-storage.md).
From the repository root, install the optional development runtime with
`uv sync --python 3.11 --extra local-models --frozen`.

Public model weights stay in the shared Hub cache. Model registrations belong
under `<LOCALBRAIN_DATA_DIR>/models/<model-slug>`. Put comparison reports and
checkpoints under `<LOCALBRAIN_DEVELOPMENT_DIR>/`, outside all Git repositories.
The default development archive is `~/Library/Application Support/LocalBrain-Development`.
Create the chosen private parent before invoking a script with explicit output
paths. Such scripts never create development archives during normal app startup.

Migrating an archive preserves its original files and hashes. Historical paths
inside frozen logs or diagnostic snapshots describe their original execution;
they are evidence, not live commands or dependencies on those locations.

### Natural-Language Search Comparisons

The product uses only the existing `local-models` extra and verified
Qwen3-Embedding-0.6B checkpoint for natural search. Qwen3-Reranker-0.6B is a
separate candidate scorer; Qwen3-4B/8B generation trials do not run in this path.
The [search contract](natural-language-search.md) owns the current default;
public synthetic comparisons and private full-index measurements have distinct
evidence scope. No private corpus is required to reproduce the public comparison.
Use fresh private output directories for each command. Run GPU measurements
sequentially without another model job; timings include completed MPS work.

```bash
uv run --no-sync python scripts/benchmark-natural-search.py --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/retrieval"
uv run --no-sync python scripts/benchmark-search-runtime.py --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime"
uv run --no-sync python scripts/benchmark-search-throughput.py --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/throughput"
```

The first command compares 256/512/768 body targets, 512/1024 dimensions, lexical,
dense and hybrid retrieval including cutoff 0.7. It reuses full-dimension model
outputs for the pinned model's Matryoshka prefix comparison; accuracy-loop query
caching is disabled for latency. The runtime command evaluates the frozen default
on separate authored topic families, then measures unchanged/incremental refresh
and foreground searches during actual model preparation. The optional throughput
command compares batch sizes and float16 explicitly; it does not alter app settings.

Current `hybrid` uses the original query and a conservative topic/action
view, orders by their mean cosine and retains exact-identifier lexical admission.
These commands use the current implementation. `dense` remains the original-query
baseline. The dedicated precision comparator reconstructs the RRF and
single-view cosine orderings on identical fragment scores, using dense mode plus
unchanged hybrid admission for single identifiers:

```bash
uv run --no-sync python scripts/benchmark-search-precision.py --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/precision"
```

This compares the fixed0/0.03/0.05/0.08 lexical-bonus grid on authored development
and prior selection cases, then the frozen zero-bonus choice against the historical
baseline on the fixed observed and holdout topic cohorts. It caches query vectors only
for quality comparison and makes no query-latency claim. Synthetic indexes live
in task-owned temporary directories and are removed automatically. The fresh
private output retains fixture hashes, runtime and complete per-query judgments;
these are authored labels, not private human ground truth.

The general-work comparator covers broad purposes, conversational descriptions,
ambiguous terms and multiple relevant activities across work domains:

```bash
uv run --no-sync python scripts/benchmark-search-general.py --stage development --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/general-development"
uv run --no-sync python scripts/benchmark-search-general.py --stage holdout --selected equal --device mps --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/general-holdout"
```

Freeze the selection after development and before observing a fresh holdout.
The shipped holdout is now observed regression evidence, not an unseen test for
future tuning. `equal` is the admitted default: original/focused cosine mean,
with admission from either view. The script checks comparator/engine agreement
and reports per-query/category metrics, including topic coverage for broad queries.
It reuses vectors only for quality comparison; measure latency with fresh encoding.

Laya and Qwen Reranker are optional development-only dependencies. Create a separate
Python 3.11 environment outside the repository; do not replace the application's
runtime. The frozen reproduction configuration uses `laya==0.4.4`, `torch==2.8.0`,
`transformers==4.57.6`, `huggingface-hub==0.36.2`, `numpy==1.26.4` and
`truststore==0.10.4`. The following setup downloads only pinned public assets into
the shared Hub cache and writes a local hash manifest; `--offline` reuses existing
assets. This explicit setup is the only network stage.

The paths below describe a reproducible environment to create, not an inventory
claim that a previous comparison environment is still installed. Shared public
checkpoint retention and private comparison-runtime retention are independent.

```bash
uv venv --python 3.11 "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime-judge"
uv pip install --system-certs --python "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime-judge/bin/python" laya==0.4.4 torch==2.8.0 transformers==4.57.6 huggingface-hub==0.36.2 numpy==1.26.4 truststore==0.10.4
"$HOME/Library/Application Support/LocalBrain-Development/search-comparison/runtime-judge/bin/python" scripts/prepare-search-comparison-models.py --output "$HOME/Library/Application Support/LocalBrain-Development/search-comparison/assets"
```

Use that environment's Python to run `scripts/benchmark-search-judges.py` with
`--assets <assets>/assets.json --candidates <retrieval>/candidates.json
--output <fresh-private-output> --role laya --device mps --laya-fp32`; repeat with
`--role reranker` and omit `--laya-fp32`. Both score the same frozen parent texts
at K10/20/50. Full-path measurement uses the application Python and
`scripts/benchmark-search-pipeline.py --assets <assets>/assets.json
--output <fresh-private-output> --judge-python <runtime-judge>/bin/python
--role laya` (then `--role reranker`). This measures retrieval and the resident
judge through local pipes, not an external service. Full-path trials use K20,
retrieval cutoff0 and judge threshold0.5; their scores have a different contract
from the product's cosine cutoff0.45.

A checkpoint/runtime producing non-finite scores fails that attempt. Use
`--laya-fp32` to disable Laya's MPS autocast explicitly; the Qwen Reranker uses float32
and eager attention. Reports record these conditions, input budgets and truncation
refusal. Laya's loader adaptation copies only metadata into its private evaluation
owner and links immutable public weights; shared downloaded files stay unchanged.

`tests/standalone_natural_search.py --output <fresh-private-output>` is an
explicit real-model smoke for the installed wheel environment. Run it with the
installed environment's Python from outside the checkout, after adding the
`local-models` extra and caching the public embedding checkpoint. It uses the
installed schema/code, registers assets offline, builds only its authored Session
and Context data and asserts actual semantic matches. It refuses an existing
output or an editable source import. It is separate from ordinary unit discovery.

No script writes personal content to Git, collects background query history or
changes source organization. Development archives are deliberate evidence owners;
retire their reports, synthetic DBs and isolated runtimes explicitly when no longer
needed. Shared public checkpoints have a separate lifecycle.

### Full-History Simulation And Model Trials

The following table describes simulation and work-reconstruction experiments. [Context Search](context-search.md) separately admits local4B/8B read-only questions; that approval does not admit a rejected work extractor or reconstruction producer. The experimental model roles remain separate:

| Model | Current purpose | Consumer/admission boundary |
| --- | --- | --- |
| Qwen3-Embedding-0.6B | Encode source chunks for similarity-based grouping | Prepared embeddings feed the observation-only map; browsing runs no model |
| Qwen3-4B | Explicit quoted work-context and relationship inference baseline | Frozen work-extraction candidate remains rejected; no map or private-history reconstruction consumer |
| Qwen3-8B | Explicit quoted work-context, protocol and source-claim diagnostics | No admitted work extractor/reconstruction producer or generative map |

These are pretrained models, not locally trained weights or LoRA adapters.
The installed 4B/8B assets are reusable independently of the embedding cache and
expiring evaluation reports. The commands below are explicit tools, not an
automatic pipeline for newly imported Sessions.

Install LocalBrain's optional runtime and embedding model, then explicitly
prepare the full-history result:

```bash
uv sync --python 3.11 --extra local-models --frozen
uv run --no-sync localbrain models install embedding
uv run --no-sync localbrain simulate
```

Public model files already in the shared cache are verified and reused. New
metadata belongs to LocalBrain. The [installation guide](installation-and-storage.md#optional-local-models)
also covers installed-app commands and offline adoption. The full-data,
replayable semantic simulation additionally supports explicit paths:

```bash
uv run --no-sync python scripts/simulate-work-sessions.py --help
uv run --no-sync python scripts/simulate-work-sessions.py \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation --inventory-only
uv run --no-sync python scripts/simulate-work-sessions.py \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation \
  --model-manifest /absolute/private/models/qwen3-embedding-0-6b/model.json
```

Use LocalBrain's `local-models` environment and its installed embedding manifest.
Set the same `HF_HUB_CACHE` as the installer when using a non-default cache.
The simulation reads verified installed assets and keeps private embeddings in
its output directory. All eligible stored primary-work Session messages are
processed, with no 60-Session, 32-message or prefix sampling cap.
Excluded and empty Sessions are accounted
for. Original data is unchanged. `/auto-work` reads the prepared full-history
result; the earlier sampled comparator is explicitly `mode=sample`.

Repeat the same command to resume or reuse cached embeddings. Change
`--neighbors`, `--similarity`, `--area-resolution` or `--work-resolution` to rerun
grouping with compatible vectors. `--force-reembed` explicitly recomputes
embeddings. Source/model/chunking changes are fingerprinted; a concurrent source
change prevents publication. `--status` reports a fixed state code;
`--show-counts` explicitly exposes aggregate progress. Private `report.json`
contains coverage, source locators, communities and replay comparison, not a
semantic-quality verdict or a finished workflow map. Results expire after 30
inactive days; `--purge` removes the owned derived state, never source data.
The [current simulation producer contract](architecture.md#full-history-simulation-producer)
owns report, source-binding, parameter and lifecycle definitions. `--chunk-chars`
changes the exhaustive window size, `--batch-size` controls committed embedding
batches and `--device` selects `auto`, `cpu`, `mps` or `cuda`. The script's
`--help` lists these controls; `--inventory-only`, `--status` and `--purge` are
mutually exclusive. Inventory/status/purge need no encoder invocation. CLI grouping
uses seed zero; its accepted numeric bounds and defaults are in that contract.
Use [reader states](architecture.md#affinity-reader-contract-and-states) to
distinguish missing, busy, stale, expired or invalid preparation from a current
map or an obsolete selection; browsing does not repair or rerun them.

### Local Work-Context Model Trial

The separate generative experiment uses the allowlisted pinned `Qwen/Qwen3-4B`
and `Qwen/Qwen3-8B` models to extract quoted work units
and assess explicit continuation. It does not train the model or replace the
embedding cache. Installation is an explicit public download (about 8.1 GB for
4B or an additional 16.4 GB / 15.3 GiB for 8B; about 24.5 GB for both);
choose a new dedicated installation-metadata folder outside the repository with
an existing parent. Public weights use the user-level Hugging Face Hub cache,
normally `~/.cache/huggingface/hub`.
Use LocalBrain's optional `local-models` environment. Installed applications can
use `localbrain models install 4b` or `8b` with default private metadata locations;
the source scripts also accept explicit roots:

```bash
uv run --no-sync python scripts/install-work-context-model.py --root /absolute/private/models/qwen3-4b
uv run --no-sync python scripts/install-work-context-model.py --root /absolute/private/models/qwen3-4b --verify
uv run --no-sync python scripts/install-work-context-model.py --model Qwen/Qwen3-8B --root /absolute/private/models/qwen3-8b
uv run --no-sync python scripts/evaluate-work-context-model.py \
  --model-root /absolute/private/models/qwen3-4b \
  --output /absolute/private/work-context-evaluation --split development
```

The default installation remains 4B. `--verify` and evaluation infer the model
only from its allowlisted ownership/revision and verified manifest; they do not
discover arbitrary models. Reusing a model folder for a different model is
rejected. `--root` / `--model-root` selects LocalBrain's private metadata folder
(`owner.json`, `install.lock`, `model.json`); new v2 model manifests refer to the
shared cache. Existing v1 app-local installations remain readable. Model snapshots
link to public blobs within their model repository; the 4B baseline is not
automatically removed, and no app cleanup purges shared weights.

The [shared cache configuration](installation-and-storage.md#storage-ownership-and-configuration)
owns cache precedence and relocation settings. Use the same cache setting across
consumers. A cache relocation with
unchanged assets/runtime does not require re-embedding.

Private databases, generated embeddings, prompts, reports and inference caches
remain project-owned. Future LoRA adapters/checkpoints belong in a durable private
project directory with backups, their base model ID/revision and training
configuration. A merged model is likewise a derived artifact and must not replace
shared pretrained weights. This storage contract adds no training behavior.

HTTP transfer is the default. An optional `--xet-cache /absolute/new-empty-private-dir`
uses an already-installed official Xet downloader with task-scoped diagnostics and
chunk/shard caches disabled. Remove only that owned transfer directory after the
installer process exits; it is not model storage and no durable output depends on it.

`--decoding sampled` selects the separately fingerprinted official non-thinking
sampling settings with a stable per-packet seed; the default is greedy.
Add `--thinking` with sampled decoding for the official reasoning-mode settings
and a bounded 8,192-token reasoning-plus-answer budget. Only the final answer is
decoded/stored; reasoning is counted, not retained. `--strategy staged` first
inventories source-backed work anchors or pair evidence, then extracts/judges
against the original messages. The default `single` strategy is one pass.
The opt-in `--strategy classified --decoding greedy` instead asks the model to
select source roles, work membership, targets and relationship evidence using
bounded answer codes. It requires non-thinking greedy decoding. A token-prefix
constraint enforces codes plus EOS; code serializes the selected original quotes,
never repairs a failed free-form answer or chooses missing citations. A well-formed
choice can still be semantically wrong. This experimental strategy refuses more
than 64 sentence/line spans, ambiguous multi-goal spans, excess output or uncertain
membership; it does not silently truncate inputs or declare one unit per sentence.
`--strategy selected --decoding greedy` uses the same code decoder but selects
whole-conversation work anchors first, then selects each anchor's field evidence.
It preserves the anchor and rejects a ninth unit/item instead of truncating.
These two source-choice variants are experimental alternatives, not admitted automatic workflow producers.
All original messages remain in each decision's context. The case budget is 144
choices/180 seconds, checked between and after calls rather than hard cancellation
of an in-flight model call. Strategy prompts/projection/bounds govern cache identity.
MPS uses the installed library's eager attention; this requires no dependency
update or changed weights.
Use distinct owned output folders for candidate/split comparisons; changing
configuration in one folder replaces that folder's previous evaluation state
for single/staged/classified/selected (the evidence strategy below refuses it).
After selecting a frozen development-passing configuration, `--split holdout`
runs the untouched cases. `--split all` runs both splits, but each split must
pass independently; do not tune on holdout failures. The command opens no private
source DB. It runs the installed model
offline and records per-case checkpoints, evidence validation, quality failures
and timing in an owned private report; repeating the same configuration reuses
validated results. Evaluation state expires after 30 inactive days. Installed
public model assets are separately owned and retained for reuse, not deleted
with an expired evaluation. A completed evaluation is not a passing quality
gate; a development-only pass is not a holdout pass. Whole-history inference and
UI integration remain unadmitted. The current
[context-inference contract](architecture.md#quoted-work-context-model-contract)
owns packet/output shapes, generation bounds and model identity.

`--strategy evidence` is a separate, opt-in 8B/MPS-eager/non-thinking/greedy
candidate. It assesses source-backed goals/actions/results/pending work before
grouping, and requires recoverable goals, compatible scope and a selected link
before continuing work. Model judgments of missing/conflicting support
automatically withhold the relationship; this does not create an owner
confirmation queue or guarantee that semantic mistakes are recognized.
Semantic labels use an explicit
32-character bound with the same eight-token/EOS limit; older codes keep their
eight-character default. Source citations are assembled from selected originals,
not generated or repaired quotations. Same-model audits remain inferred safeguards,
not proof of semantic correctness.

```bash
uv run --no-sync python scripts/evaluate-work-context-model.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/evidence-development \
  --strategy evidence --split development
```

This runs the fixed four-case development cohort and twelve-case compositional
cohort, with independent gates. It does not rerun the 288-cell diagnostic or
read private Sessions. Case attempts are bounded to 32 spans, 96 choices and 120
soft seconds (30 per generation). Same-config replay retains completed failures
as well as successes; changed configurations and corrupt cached observations
refuse without replacement. A clean interruption allows at most one additional
attempt for its incomplete case; an unclean in-flight crash refuses automatic
resume. Existing storage ownership, writer lock and 30-day expiry still apply.

Only after both development gates **and primary semantic review** pass may this
candidate run `--split holdout` once, in a separate output folder, with
`--development-report /absolute/private/evidence-development/report.json`.
The command revalidates the report's identity, observations and both split scores;
an aggregate PASS is insufficient. `--split all` is refused for this strategy.
Neither this candidate nor its gate starts private backfill or changes the UI.
The frozen evidence-first candidate remains rejected and ineligible for holdout
or workflow reconstruction. Reproduction and replay do not renew its consumed
attempts, reset its budget or authorize another model run.

The separate protocol diagnostic investigates answer-format, option-order and
answer-code sensitivity on twelve fixed synthetic cases. It does not consume the
admission holdout or open private Sessions:

```bash
uv run --no-sync python scripts/diagnose-work-context-protocol.py --describe
uv run --no-sync python scripts/diagnose-work-context-protocol.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/work-context-protocol-diagnostic
```

This fixed 8B/MPS-eager comparison has 288 conditions, a 300-attempt/1,200-second
cumulative budget and 30-second soft generation limits. It compares numeric
choices, semantic-label choices and short text; meaning, format and literal
grounding are scored separately. The twelve cases, not the correlated conditions,
are the evidence units. Completion never means model admission. Results retain
the evaluation owner/lock/30-day expiry rules above. Unlike the
single/staged/classified/selected admission strategies,
diagnostic replay reuses completed wrong/invalid/refused observations too, and a
changed configuration refuses an unexpired folder instead of replacing evidence.
Clean interruption can resume missing observations within cumulative bounds;
an unclean in-flight crash refuses automatic restart because elapsed time is
unknown. No default strategy, model weights or embedding vectors are changed.

A separate matched formulation comparison tests sixteen fixed focused contexts
with independent property questions versus direct selection of the complete role
set. Both use the same source and facet definitions, with canonical/reversed
option orders. Compound action/result statements can keep both roles. Six separate
controls run the unchanged evidence-first relationship pipeline; better role
classification alone does not establish correct work continuity.

```bash
uv run --no-sync python scripts/compare-work-role-formulations.py --describe
uv run --no-sync python scripts/compare-work-role-formulations.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/work-role-comparison
```

The command accepts no private input or tuning/holdout options. It preflights the
semantic vocabulary, uses the installed 8B offline, and reports 166 observations
(160 focused choices plus six multi-call controls). The whole comparison has a
512-choice-attempt/1,200-soft-second budget and at most two attempts for an
incomplete observation. Completed wrong/refused answers replay without generation;
changed configurations, corrupt records and unclean in-flight state refuse.
It shares the existing evaluation owner/lock/atomic/30-day expiry contract.
Exact role-set matches, extra/missing roles, order changes and relationship errors
are separate findings, never an automatic extraction admission or UI update.

### Source-Claim Extraction And State Trial

The separate [source-claim adapter](source-claims-and-work-state.md#model-aware-v2-and-synthetic-adapter)
extracts historical claims, proposes scoped work bindings and lifecycle effects,
then computes reported state with a pure deterministic projector. Model-inferred
fulfillment is distinct from a source explicitly reporting completion. A completed
check does not complete its parent effort.

```bash
uv run --no-sync python scripts/evaluate-source-claims.py --describe
uv run --no-sync python scripts/evaluate-source-claims.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/source-claim-trial
uv run --no-sync python scripts/evaluate-source-claims.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/source-claim-trial --replay
```

Use the existing compatible model runtime. This is one frozen 8B/MPS-eager,
non-thinking candidate, not training or a new model installation. Twenty-eight
synthetic development histories allow at most 84 generation calls; the original
ten holdout cases allow 20 additional calls only after all development gates and
a report-bound primary semantic review. `--holdout` cannot bypass that gate.
Each call is bounded to 8,192 combined/2,048 generated tokens and 60 soft seconds.
The whole candidate allows at most 104 generation calls, including the gated
holdout allowance, and a 120-minute cumulative active-run launch gate, including model load,
verification and preflight. Reservations and elapsed time survive clean resume;
these ceilings are not a fresh allowance for a closed or exhausted candidate.
Input is never truncated.

Reference-conditioned binding receives correct claims/targets for diagnosis;
end-to-end generation must discover them from raw source. Neither technical tests
nor conditional results establish extraction quality. Completed failures replay
without generation. The owned report uses the existing 30-day inactivity rule;
changed config, corrupt/unclean state and expired trial budgets refuse reuse.
No private input argument, all-Session job, server/UI update or organization write
is added. The frozen candidate remains rejected for admission; holdout, private
processing and UI updates remain withheld. A replay or documentation cleanup
does not reopen the candidate, renew consumed calls or reset its budget. This
command is an evaluation tool, not an admitted work extractor.

### Earlier Model-Free Comparator

An isolated non-model tool compares reference-pair grouping with explicit
Korean/English goal extraction. It does not replace the current Workstream UI
or change its data. Inspect its options without opening runtime storage:

```bash
uv run --no-sync python scripts/experiment-work-reconstruction.py --help
```

Execution accepts an explicit supplied fixture or an existing database plus a
frozen selection manifest. After selecting an existing database and through-time,
`--prepare-through <UTC> --unassessed` can prepare a deterministic bounded sample
and check execution without an answer key. It covers the selected population's
whole existing time range, not every record, and reports omissions explicitly.
Scored quality still requires separate source-bound expectations. Results need
a new private output directory outside the repository and an owner/expiry;
default output contains status codes only. No private database is opened by
default, and predictions never become the answer key. The current
[Architecture contract](architecture.md#isolated-work-reconstruction-experiment)
owns the wire shapes, caps, source permissions and assessment boundaries; the
invocation and file shapes below describe this command.
Synthetic correctness is not evidence that real work is reconstructed usefully.

#### Model-Free Invocation And Files

Choose exactly one input mode. All paths below are explicit local paths; use a
new absolute output directory with an existing canonical nonsymlink parent
outside the repository. Set `RECONSTRUCTION_EXPIRES_AT` to an explicit future
aware ISO timestamp before a supplied-fixture or preparation invocation.

```bash
uv run --no-sync python scripts/experiment-work-reconstruction.py \
  --fixture /absolute/private/fixture.json \
  --expectations /absolute/private/expectations.json \
  --output-dir /absolute/private/new-fixture-result \
  --owner reconstruction-review --expires-at "$RECONSTRUCTION_EXPIRES_AT"

uv run --no-sync python scripts/experiment-work-reconstruction.py \
  --database /absolute/private/localbrain.db \
  --manifest /absolute/private/selection.json \
  --expectations /absolute/private/expectations.json \
  --output-dir /absolute/private/new-scored-result

uv run --no-sync python scripts/experiment-work-reconstruction.py \
  --database /absolute/private/localbrain.db \
  --prepare-through '2026-09-15T00:00:00+00:00' --unassessed \
  --output-dir /absolute/private/new-unassessed-result \
  --owner reconstruction-review --expires-at "$RECONSTRUCTION_EXPIRES_AT"
```

The preparation cutoff is an explicit scope choice, not a default or permission
to open another database. Preparation requires database mode, `--unassessed`,
and no manifest or expectations. Other database runs require a manifest;
supplied-fixture and scored database runs require an independent expectations
file. The selected manifest supplies database-mode owner/expiry. Fixture and
preparation modes require explicit owner/expiry arguments. Expiry must be later
than the current time, and preparation also requires expiry after its cutoff.
No invocation creates missing database/schema/source state.

| File | Current shape and validation |
| --- | --- |
| Supplied fixture | Exactly `{"version":1,"snapshots":[...]}`; 1–12 distinct named snapshots obey the [current snapshot contract](architecture.md#reconstruction-input-and-bounds) |
| Private selection | Exactly `version`, `source_ids`, `start`, `end`, `snapshots`, `owner`, `expires_at`; version 1, ordered snapshot cutoffs, one bounded hash-verified selection per record and the source/permission predicates in Architecture |
| Expectations | Exactly `{"version":1,"snapshots":{"snapshot-name":...}}`; names exactly match all supplied snapshots. Each version-1 answer key binds `snapshot_digest` and independently supplies `groups`, `negative`, `unresolved`; group/member/label bounds and contradictory-span refusal are in [assessment](architecture.md#reconstruction-output-and-assessment) |
| Result | One new `comparison.json`, encoded at most 10 MiB, wrapped as `owner`, `expires_at`, `report`; directory mode 0700/file mode 0600. Existing output is never replaced; a failed write removes only paths created by that invocation |

JSON inputs must be existing nonsymlink files no larger than 10 MiB; duplicate
keys, non-finite constants, malformed data and hard-bound overflow refuse.
Answer keys are validated against every frozen snapshot before either arm runs.
The command compares text and metadata with/without organization, checks
unchanged replay, and records scores, source/expectation digests, resource
measurements and chronological stability. Results include `technical`,
`input_kind`, `private_quality`, `viability`, `snapshots`, `history`, `sample`,
`required_review`, `admission_resources` and `assessment`; preparation adds its
frozen `input_manifest` and omission/sample metadata. `assessment: unassessed`
retains unknown expectations and cannot pass quality; fixture execution cannot
establish private quality. `viability` remains `unverified` even after technical
success. The [finite human-review allowance](privacy-and-data.md#local-persistence)
is separate and is never renewed by these commands.

Each admission, extraction, comparator or scoring worker has a 120-second wall
limit and 512-MiB peak-RSS bound, with monitor availability checked fail-closed;
cancellation/failure terminates and reaps only its task-owned worker. The command
opens no native file, source parser, connector or model. It adds no background
retention scheduler or full database copy. Owner-managed expiry cleanup remains
required for retained results. Standard output is only `EXPERIMENT_RECORDED`
(exit 0), `EXPERIMENT_FAILED` (exit 2), or `EXPERIMENT_CANCELLED` (exit 130).
Only explicit `--share-summary` replaces the success code with the non-identifying
`technical`/`private_quality`/`viability` summary; private payloads never print.

## Google Drive Development

Use [Google CLI authentication and distribution](google-drive-sync.md#google-cli-authentication-and-distribution) for the approved gcloud/full-Drive authentication flow, pinned accounts, SDK credential ownership and live validation boundaries. Run `uv run python -m unittest discover -s tests -p 'test_google_drive*.py' -v` for synthetic sync/transport/scheduler and SDK subprocess tests. These tests use synthetic executable helpers, do not launch real Google login and do not upload developer Contexts or use a real Google account.

Transport tests also own an ephemeral loopback-only HTTP/1.1 server for connection reuse, the eight-connection ceiling, streamed-response cleanup, status/retry and lifecycle checks. It never uses real Google credentials or files and is closed after the test class. Install the base dependencies from the current lock: urllib3 is directly declared for Drive pooling, with a compatible version resolved across the supported Python range. A full suite still does not establish live Google body-transfer timing or native/recipient behavior.
