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
`uv run --no-sync uvicorn localbrain.main:app --host 127.0.0.1 --reload`.
Install optional local-model dependencies with
`uv sync --python 3.11 --extra local-models --frozen`;
`uv run --no-sync localbrain models install embedding` verifies public model
assets and records LocalBrain's installation metadata. `uv run --no-sync localbrain doctor` and
`uv run --no-sync localbrain models status` inspect readiness without reading sources or
downloading/running models.

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

## Dependency Certificate Troubleshooting

The default `uv sync` command verifies PyPI with uv's bundled certificate roots and should work on a normal network. If it fails with `UnknownIssuer` on a managed network, a proxy or security product may be using a certificate authority trusted by macOS but not included in uv's bundled roots.

Retry the failed installation using the macOS system certificate store:

```bash
uv sync --system-certs
```

The flag applies to that command only. If later `uv` commands also need network access through the same managed network, set `UV_SYSTEM_CERTS=true` for the current shell before running them. Do not disable TLS verification. This setting affects dependency downloads only; it does not change where LocalBrain stores or processes indexed data.

## Python Runtime Compatibility

Use the uv-managed Python 3.11 environment shown above for installation and
verification. A forked reconstruction worker crashed while opening SQLite with
Apple Command Line Tools Python 3.9.6; the same check and full test suite passed
with uv-managed Python 3.11. Package metadata accepting an older interpreter
does not establish that every system-provided Python runtime has been verified.

## Configuration

LocalBrain reads these environment variables at process startup:

| Variable | Default | Responsibility |
| --- | --- | --- |
| `LOCALBRAIN_DATA_DIR` | `~/Library/Application Support/LocalBrain` | Primary DB, private configuration, model registrations and saved Runs |
| `LOCALBRAIN_CACHE_DIR` | `~/Library/Caches/LocalBrain` | Rebuildable simulation and preview results |
| `LOCALBRAIN_DEVELOPMENT_DIR` | `~/Library/Application Support/LocalBrain-Development` | Explicit development evaluations; never created by ordinary app startup |
| `LOCALBRAIN_CONTEXT_ROOT` | `~/Projects/context` | Initial Local Context folder discovery |
| `LOCALBRAIN_CLAUDE_ROOT` | `~/.claude/projects` | One-time Claude root seed when `session-sources.toml` is first absent |
| `LOCALBRAIN_CODEX_ROOT` | `~/.codex/sessions` | One-time personal Codex root seed when `session-sources.toml` is first absent |
| `LOCALBRAIN_CLAUDE_BIN` | resolved from `PATH` | Claude CLI executable used by the Task Runner |
| `LOCALBRAIN_CODEX_BIN` | resolved from `PATH` | Codex CLI executable available to source-neutral external synchronization |
| `LOCALBRAIN_INSIGHT_CODEX_HOME` | `CODEX_HOME`, then existing `~/.codex-company`, then `~/.codex` | Codex profile home for new personal improvement analysis Runs |
| `LOCALBRAIN_INSIGHT_CODEX_MODEL` | `gpt-6-astra` | Model identifier frozen for new personal improvement analysis Runs |
| `LOCALBRAIN_MCP_CALL_BUDGET` | `20` | Advisory legacy-task budget and hard selected-request ceiling for external synchronization |
| `LOCALBRAIN_TIMEZONE` | system IANA timezone, then `UTC` | Local calendar boundaries for usage and activity reports |

For a custom `LOCALBRAIN_DATA_DIR`, unspecified cache/development locations are sibling directories named `<data-name>-cache` and `<data-name>-development`. Explicit variables override those defaults. Stop the app before moving existing state; use [the storage migration guide](installation-and-storage.md#upgrade-an-existing-storage-layout).

Do not place secrets in tracked environment files. See [Privacy And Data Handling](privacy-and-data.md) before changing data locations or persistence behavior.

### Personal Improvement Analysis

The Insights analyzer currently uses Codex CLI. `LOCALBRAIN_INSIGHT_CODEX_HOME` takes priority over `CODEX_HOME`; without either setting, an existing `~/.codex-company` home is preferred to `~/.codex`. A new Run freezes that home, selected model, exact prompt, core v8, all eleven playbook versions/digests, and the report-v3 response schema. Request-and-feedback uses v4; other playbooks use v1. Historical core v4/v5/v6/v7 retain report v3, and core v2/v3 retain report v2 and saved reports. Changing environment settings or the package guide affects future Runs only. The guide sources are `src/localbrain/personal_insight_guides/`; private evidence, prompts, responses, validated results, diagnostics, and reports are kept under `<LOCALBRAIN_DATA_DIR>/personal-insight-runs/<id>/`, outside Git. An explicit Run start sends selected Session excerpts to the configured model service; opening the screen or a past report does not.

New findings use the existing work-session handoff to explain the proposed application mechanism, target, concrete content, actors, activation, setup and repeated work. The [application contract](../../plans/spec/spec-0108-personal-improvement-guide-and-finding-contract.md#concrete-application-handoff) distinguishes temporary trials, conditional adoption and unresolved placement facts. This guide requirement is evaluated semantically; the JSON validator only enforces its existing structural rules.

The [existing-proposal contract](../../plans/spec/spec-0108-personal-improvement-guide-and-finding-contract.md#existing-proposal-follow-through) distinguishes mention, application, outcome and deferral from supplied evidence. A useful next step can carry an earlier proposal forward without inventing a new method. These are generation rules; the product does not persist an adoption state or infer it from a report's existence.

The analysis launcher resolves the Codex executable before starting it and grants its sandboxed startup helpers read access to that exact binary. The profile home is used for client authentication and is not added to the command filesystem allowlist. Artifact writes and command network access remain blocked. See [RUN-135](../../plans/run/run-20261001-135-personal-insight-cli-startup.md) for the macOS startup correction. Restart a server that was already running when runner code changed before submitting a new analysis.

Run detail displays the same stored estimated cost used by Usage & Cost, with its calculation state and frozen price basis in the existing settings disclosure. Missing usage or pricing stays explicitly unavailable, and any CLI-reported amount remains separately labeled. Estimates are API-equivalent trend costs, not subscription bills. Startup seeds exact GPT-6.1 Sol Standard/Fast snapshots effective 2026-09-29 and fills eligible previously unpriced records using retained evidence; already-priced records are preserved.

Owner-requested guide evaluations can retain frozen inputs, raw outputs, and review reports under `<LOCALBRAIN_DEVELOPMENT_DIR>/personal-insight-evaluations/<id>/`, with owner-only access. This private archive is separate from product Run records: subagent simulations do not create Insights history rows. Tracked evaluation documents contain only sanitized conclusions.

Discovery uses deterministic [source/month sampling](../../plans/spec/spec-0107-personal-insight-evidence-manifest.md#selection), not a random project picker. Within each source/month group it prefers recently active Sessions; project balance and prior recommendation history are not selection inputs. The [guide contract](../../plans/spec/spec-0108-personal-improvement-guide-and-finding-contract.md) supplies all eleven bounded playbooks. The model identifies the owner's goal and observed friction before choosing a type; incidental words in quoted source material no longer exclude types before analysis. A reported candidate is not a global priority ranking, and repeating discovery does not promise a different project or a new recommendation. Insights shows frozen selected/eligible counts, sources, time coverage, and truncation; each new report explains the candidate and finding type with source anchors.

For conversation requests, report v3 identifies up to five missing messages by a supplied anchor and frozen eligible-message position. Local validation rejects requests for already supplied complete messages; a clipped message can be requested in full. The product renders the request from those validated positions, not free-form resend instructions. Unknown current goals/outcomes use separate bounded questions and are checked semantically by the guide; positional validation alone cannot detect every redundant factual question. Invalid results fail without automatic paid retry, retaining emitted usage and diagnostics.

### Session Source Configuration

Application startup creates `<LOCALBRAIN_DATA_DIR>/session-sources.toml` with
mode `0600` when it is first absent. The file is the established local AI
Session-source authority and contains an ordered `schema_version = 1` list:

```toml
schema_version = 1

[[session_sources]]
source_key = "codex-company"
display_label = "Codex Company"
provider_kind = "codex"
root = "/absolute/path/to/.codex-company/sessions"
```

The bootstrapped file also contains explicit `claude` and `codex` peers. Once it
exists, changing the two legacy root environment variables does not override it.
Missing roots remain registered as unavailable. Malformed files, provider
conflicts, omitted entries, and changes to a root that already owns imported data
preserve the last registered Source and every normalized descendant; source
deletion and occupied-root relocation require separate future workflows.

Sessions synchronization dispatches every validated entry in file order, using
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
- The first approved [Data Model Visibility And Schema Cleanup](../../plans/prd/prd-0003-data-model-visibility-and-schema-cleanup.md) documentation Feature establishes the complete human-readable baseline.
- After that baseline, keep planning and execution artifacts delta-scoped: name only the affected schema objects, contract behavior, migrations, tests, and owner documents.
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
- [Value Dictionaries](data-model/value-dictionaries.md) and its ten subject companions are generated projections. Runtime templates and handlers use `localbrain.value_registry`; they do not parse Markdown.
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

- Update `README.md` for first-run or user-visible usage changes.
- Update [Product Model](product.md) for durable product and organization rules.
- Update [Project Architecture](architecture.md) for runtime ownership, source adapters, data model, or ingestion behavior.
- After the PRD-0003 baseline exists, update only the affected data-model subject documents for ordinary schema deltas; update their entry map when subject files or cross-domain ownership changes.
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

### Full-History Simulation And Model Trials

The model roles are separate:

| Model used in the recorded work | Purpose | Current map integration |
| --- | --- | --- |
| Qwen3-Embedding-0.6B | Encode source chunks for similarity-based grouping | Prepared embeddings feed the map; browsing runs no model |
| Qwen3-4B | Quoted work-context and relationship inference baseline | Synthetic trial failed admission; not connected to the map |
| Qwen3-8B | Separately installed inference comparison and later trials | Synthetic trials did not establish admission; not connected to the map |

These are pretrained models, not locally trained weights or LoRA adapters.
The installed 4B/8B assets are reusable independently of the embedding cache and
expiring evaluation reports. The [recorded 4B trial](../../plans/run/run-20260923-104-local-work-context-inference.md)
and [8B comparison](../../plans/run/run-20260923-106-work-context-model-size-comparison.md)
own installation and quality evidence; the commands below are explicit tools,
not an automatic pipeline for newly imported Sessions.

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
See [the simulation contract](../../plans/spec/spec-0097-replayable-session-simulation.md).

### Local Work-Context Model Trial

The separate generative trial uses pinned `Qwen/Qwen3-4B` and the separately
approved `Qwen/Qwen3-8B` comparison to extract quoted work units
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
MPS uses the installed library's eager attention after a fused-attention numerical
failure in the trial; no dependency update or changed weights are required.
Use distinct owned output folders for candidate/split comparisons; changing
configuration in one folder replaces that folder's previous evaluation state
for the historical strategies above (the evidence strategy below refuses it).
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
UI integration remain downstream of this admission test. See
[the context-inference contract](../../plans/spec/spec-0098-local-work-context-inference.md).

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

This runs the original four development cases and twelve new compositional
controls, with independent gates. It does not rerun the 288-cell diagnostic or
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
The completed [evidence-first trial](../../plans/run/run-20260923-109-evidence-first-work-context.md)
fails both development gates; this is an experimental, rejected candidate, not
an admitted workflow reconstruction engine.

The separate protocol diagnostic investigates answer-format, option-order and
answer-code sensitivity on twelve new synthetic cases. It does not consume the
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
the evaluation owner/lock/30-day expiry rules above. Unlike the historical
single/staged/classified/selected admission strategies,
diagnostic replay reuses completed wrong/invalid/refused observations too, and a
changed configuration refuses an unexpired folder instead of replacing evidence.
Clean interruption can resume missing observations within cumulative bounds;
an unclean in-flight crash refuses automatic restart because elapsed time is
unknown. No default strategy, model weights or embedding vectors are changed.

A separate matched formulation comparison tests sixteen fresh focused contexts
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

The separate [source-claim trial](../../plans/feature/feat-0100-source-claim-extraction-and-binding-trial.md)
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
Each call is bounded to 8,192 combined/2,048 generated tokens and 60 soft seconds;
the cumulative active-run launch budget is 120 minutes. Input is never truncated.

Reference-conditioned binding receives correct claims/targets for diagnosis;
end-to-end generation must discover them from raw source. Neither technical tests
nor conditional results establish extraction quality. Completed failures replay
without generation. The owned report uses the existing 30-day inactivity rule;
changed config, corrupt/unclean state and expired trial budgets refuse reuse.
No private input argument, all-Session job, server/UI update or organization write
is added. [RUN-112](../../plans/run/run-20260923-112-source-claim-extraction-and-binding-trial.md)
owns the actual measured result, not the presence of this command.
Its frozen candidate completed but failed admission: all 28 extraction responses
were rejected before binding, and only 3/28 reference-conditioned cases fully
passed. Zero-generation replay passes; holdout, private processing and UI updates
remain withheld. This command is an evaluation tool, not an admitted work extractor.

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
default, and predictions never become the answer key. See
[the input and command contract](../../plans/spec/spec-0095-bounded-work-reconstruction-experiment.md#local-invocation-and-file-shapes).
Synthetic correctness is not evidence that real work is reconstructed usefully.
