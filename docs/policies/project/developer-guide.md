# Developer Guide

## Prerequisites

- macOS for the current Apple Notes integration and default data location
- Python 3.11 recommended; package metadata accepts Python 3.9 or later
- `uv` for dependency and virtual environment management
- Claude CLI only for Claude-backed maintenance Runs
- Codex CLI for personal improvement analysis Runs or when selecting Codex for external synchronization

The source/web instructions below target macOS. The current runtime uses Unix
file-locking APIs, and the native builder targets Apple Silicon macOS. Python-version
compatibility does not establish Windows installation or execution support.

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
for legacy-token conversion and [Architecture](session-ingestion.md#ingestion-module-ownership)
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

This optional development-web analyzer uses a Codex CLI execution profile.
`LOCALBRAIN_INSIGHT_CODEX_HOME` takes priority over `CODEX_HOME`; without either setting, an existing `~/.codex-company` home is preferred to `~/.codex`. A new Run freezes that home, selected model, exact prompt and the [guide/result bundle](personal-insights.md#guide-bundle-and-result-contract), including independent core/playbook versions and digests and the response schema. That canonical contract owns current versions and historical report compatibility. Changing environment settings or the package guide affects future Runs only. The guide sources are `src/localbrain/personal_insight_guides/`; private evidence, prompts, responses, validated results, diagnostics, and reports are kept under `<LOCALBRAIN_DATA_DIR>/personal-insight-runs/<id>/`, outside Git. An explicit Run start sends selected Session excerpts to the configured model service; opening the screen or a past report does not.

Run creation requires exactly one Codex Source row whose resolved root
matches the resolved `<selected-home>/sessions` path; missing or ambiguous matches
refuse creation. The [analysis contract](personal-insights.md#personal-improvement-analysis-runs)
also requires revalidating the frozen Source ID, provider and path binding before
CLI launch.

New findings use the existing work-session handoff to explain the proposed application mechanism, target, concrete content, actors, activation, setup and repeated work. The [application contract](personal-insights.md#concrete-application-handoff) distinguishes temporary trials, conditional adoption and unresolved placement facts. This guide requirement is evaluated semantically; the JSON validator only enforces its existing structural rules.

The [existing-proposal contract](personal-insights.md#existing-proposal-follow-through) distinguishes mention, application, outcome and deferral from supplied evidence. A useful next step can carry an earlier proposal forward without inventing a new method. These are generation rules; the product does not persist an adoption state or infer it from a report's existence.

The analysis launcher resolves the Codex executable before starting it and grants its sandboxed startup helpers read access to that exact binary. The profile home is used for client authentication and is not added to the command filesystem allowlist. Artifact writes and command network access remain blocked. Restart a server that was already running when runner code changed before submitting a new analysis.

Run detail displays the same stored estimated cost used by Usage & Cost, with its calculation state and frozen price basis in the existing settings disclosure. Missing usage or pricing stays explicitly unavailable, and any CLI-reported amount remains separately labeled. Estimates are API-equivalent trend costs, not subscription bills. Startup seeds exact GPT-6.1 Sol Standard/Fast snapshots effective 2026-09-29 and fills eligible previously unpriced records using retained evidence; already-priced records are preserved.

Owner-requested guide evaluations can retain frozen inputs, raw outputs, and review reports under `<LOCALBRAIN_DEVELOPMENT_DIR>/personal-insight-evaluations/<id>/`, with owner-only access. This private archive is separate from product Run records: subagent simulations do not create Insights history rows. Tracked evaluation documents contain only sanitized conclusions.

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

- `src/localbrain/schema.sql` owns fresh-database DDL. `src/localbrain/persistence/bootstrap.py` orders startup and `persistence/migrations/` owns compatible changes and runtime-only indexes; `persistence/db.py` retains the public connection/init/transaction API. This split introduces no migration registry or new execution system.
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
- Commit `src/localbrain/schema-presentation.json` with the source change. Later application screens load it only through `localbrain.persistence.schema_presentation.load_schema_presentation`; missing or invalid package data stays a bounded unavailable state and never triggers runtime introspection.

### Data Model Value Dictionaries

- `src/localbrain/value-registry.json` is the executable authority for bounded physical values, logical axes, complete presentation modes, fallbacks, labels, and visible-consumer inventory.
- [Value Dictionaries](data-model/value-dictionaries.md) and its eleven subject companions are generated projections. Runtime templates and handlers use `localbrain.persistence.value_registry`; they do not parse Markdown.
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

Use [Model Tool Operations](development/model-tools.md) for optional-runtime setup,
private evaluation ownership, search comparisons, full-history simulation and
the separate quoted-context, source-claim and model-free reconstruction trials.
These guides retain each tool's source limits, invocation, replay and admission
conditions. Running a tool does not approve a product consumer or renew a closed
candidate's budget.

## Google Drive Development

Use [Google CLI authentication and distribution](google-drive-sync.md#google-cli-authentication-and-distribution) for the approved gcloud/full-Drive authentication flow, pinned accounts, SDK credential ownership and live validation boundaries. Run `uv run python -m unittest discover -s tests -p 'test_google_drive*.py' -v` for synthetic sync/transport/scheduler and SDK subprocess tests. These tests use synthetic executable helpers, do not launch real Google login and do not upload developer Contexts or use a real Google account.

Transport tests also own an ephemeral loopback-only HTTP/1.1 server for connection reuse, the eight-connection ceiling, streamed-response cleanup, status/retry and lifecycle checks. It never uses real Google credentials or files and is closed after the test class. Install the base dependencies from the current lock: urllib3 is directly declared for Drive pooling, with a compatible version resolved across the supported Python range. A full suite still does not establish live Google body-transfer timing or native/recipient behavior.
