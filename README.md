# LocalBrain

LocalBrain is a local-first developer work context hub. It reconnects AI sessions, local projects, files, notes, Git activity, and external references around user-defined Workstreams so interrupted work can be understood and resumed.

The current MVP runs as a FastAPI web application on the local machine. A native macOS wrapper remains a later packaging step after the workflow is validated.

## Current Capabilities

- Ingest local Claude and Codex session history.
- Register and browse folders, individual files, and Apple Notes as Local Context sources.
- Read safe, locally rendered Markdown in Local Context previews, context-aware full Document views, and Session or Subsession conversations.
- Browse Jira and Confluence links plus URL-derived Project, Board, Filter,
  Dashboard, portal, and Space references in a Site-first Explorer. Local Add
  registers one known link, document, Project, or Space URL; explicit local
  Sync reconciles persisted Session and Local Context evidence, while optional
  Connections and bounded remote Refresh remain separate actions.
- Organize work into user-created Workstreams and Threads.
- Link sessions, documents, local paths, projects, and external references to Threads.
- Maintain versioned checkpoints and review reversible resource Suggestions.
- Run Claude maintenance tasks for resource organization, checkpoint drafting, and priority review.
- Inspect source-aware Session inventory, pinned recall, related evidence, and token or estimated-cost history.
- Open `작업 흐름` from an eligible primary Session to inspect a deterministic
  Episode lineage, bounded branches, relation reasons, and grouped source
  evidence. Contextual Trace controls can preview and append reversible
  user-confirmed boundary corrections without changing Sessions or source
  evidence. The first Focus Map and correction path use no AI model.
- Explore the packaged data model, subject ERDs, and table contracts from the read-only **System > Schema** surface.

Detailed behavior belongs to the [Product Model](docs/policies/project/product.md), while implementation and I/O boundaries belong to [Project Architecture](docs/policies/project/architecture.md).

## Quick Start

LocalBrain currently targets macOS and requires Python 3.9 or later and [uv](https://docs.astral.sh/uv/). Claude CLI is required only for Claude-backed maintenance Runs; Codex CLI is required only when Codex is selected for external synchronization.

From the project root, install the Python dependencies and start LocalBrain:

```bash
uv sync
uv run --no-sync uvicorn localbrain.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The local database is created automatically on first startup. Stop the server with `Ctrl+C`.

### Explore The Full-History Affinity Map

Select **자동 작업** immediately above **Workstreams** in the sidebar, or open
`/auto-work`. **전체 이력 지도** places actual message time from left to right.
Curved strands group similar records; knots show observed activity and dashed
gaps mark periods with no observed records. Select a strand for its full evidence
or a knot for that period's original passages. **선택 주변 확대** brings the
selected period/neighborhood closer. Scroll horizontally to travel through time
and vertically to reach other strands; the entire matching scope shares one
canvas, not 24-item slides. The ←/→ buttons also move through time. Drag to pan,
use zoom/reset or Ctrl/⌘ + wheel, and expand **세부 묶음 펼치기** →
**세션 가까이 보기** for a finer scope.
Back restores the selected view. **전체 기간** fits the full time axis; the initial
view is 200%. Ordinary scrolling moves the map when over its bounded viewport
and the document outside it. Only the text list is paginated; changing its page
preserves the map and camera. Unknown dates stay explicitly unplaced; period
grouping never implies continuous work duration.

All eligible indexed primary-work history is included, not the first 60 Sessions.
The prepared result already groups embedded message chunks into coarse
communities, then finer communities within each parent. This is a two-level
hierarchy, not two successive merges into larger work units. At the selected
level, a knot aggregates one group's chunk occurrences in a time period; its
capped, logarithmic size reflects occurrences, not distinct Sessions or cohesion.
Complete paged lists, title search, exclusions/empty records and exact evidence
remain available on narrow screens or without JavaScript. The coverage disclosure
shows whole-population totals, overlap and single-Session fragmentation. Titles
are source examples, not generated categories; time-anchored undirected similarity is **not**
proof of the same work, continuation, branching or completion. No classification
or approval is required, and existing Workstreams/Threads are unchanged.

Prepare or update the existing runtime `session-simulation` directory explicitly
with the [simulation command below](#experimental-work-reconstruction). Browsing
never starts a model, ingestion or regrouping. Changed, missing or expired results
show a recovery state, not a silently substituted sample. Restart an already
running server after updating the code.

**이전 표본 · 규칙 기반** (`/auto-work?mode=sample`) retains the earlier
Session/document comparator. Its **결과 갱신** action updates only that bounded
model-free sample, never the whole-history map. Its separate seven-day preview
and the simulation's 30-day derived-state owner retain their existing lifecycles.

### Import Local Sessions

On first startup, LocalBrain creates a private `session-sources.toml` beside
`localbrain.db`. It registers Claude, personal Codex, and Codex Company
(`~/.codex-company/sessions`) as peer local Session sources and can hold future
roots. This runtime configuration must not be committed. See
[Configuration](docs/policies/project/developer-guide.md#configuration) for its
schema, bootstrap behavior, and safe-change rules.

To import local AI sessions, use **동기화** on the Sessions page. One action scans
every validated registry entry; a missing or invalid source keeps its existing
indexed data and appears as needing attention. Longer contract upgrades show the
current source, repair reason, and file progress in the existing result area.
The **Sources** page keeps the wider scan across Session sources and enabled
Local Context folders, files, and Apple Notes. The initial `uv sync` downloads
Python packages, but indexed content and runtime data remain on the local
machine.

Sessions supports combined and per-source inventory scopes without an age cutoff. The [Session inventory contract](docs/policies/project/product.md#application-navigation-and-session-inventory), [analytical read models](docs/policies/project/architecture.md#analytical-read-models), and [Schema Explorer boundary](docs/policies/project/architecture.md#persistence-model) own the detailed behavior.

Certificate configuration is not required on a normal network. If `uv sync` fails with an `UnknownIssuer` error, retry the installation with the macOS system certificate store:

```bash
uv sync --system-certs
```

See [Dependency Certificate Troubleshooting](docs/policies/project/developer-guide.md#dependency-certificate-troubleshooting) for details.

Run the test suite with:

```bash
uv run python -m unittest discover -s tests -v
```

Configuration, environment variables, and verification guidance live in the [Developer Guide](docs/policies/project/developer-guide.md).

## Experimental Work Reconstruction

The model roles are separate:

| Model used in the recorded work | Purpose | Current map integration |
| --- | --- | --- |
| Qwen3-Embedding-0.6B | Encode source chunks for similarity-based grouping | Prepared embeddings feed the map; browsing runs no model |
| Qwen3-4B | Quoted work-context and relationship inference baseline | Synthetic trial failed admission; not connected to the map |
| Qwen3-8B | Separately installed inference comparison and later trials | Synthetic trials did not establish admission; not connected to the map |

These are pretrained models, not locally trained weights or LoRA adapters.
The installed 4B/8B assets are reusable independently of the embedding cache and
expiring evaluation reports. The [recorded 4B trial](docs/plans/run/run-20260923-104-local-work-context-inference.md)
and [8B comparison](docs/plans/run/run-20260923-106-work-context-model-size-comparison.md)
own installation and quality evidence; the commands below are explicit tools,
not an automatic pipeline for newly imported Sessions.

The full-data, replayable semantic simulation is a separate explicit command:

```bash
python scripts/simulate-work-sessions.py --help
python scripts/simulate-work-sessions.py \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation --inventory-only
python scripts/simulate-work-sessions.py \
  --database /absolute/private/localbrain.db \
  --output /absolute/private/session-simulation \
  --model-manifest /absolute/private/semantic/models/model-name/model.json
```

Use an existing Python runtime with Sentence Transformers, PyTorch, NumPy,
scikit-learn and NetworkX, and an already-installed verified Foundry-format model
manifest. The command installs nothing and writes no Foundry state. All eligible
stored primary-work Session messages are processed, with no 60-Session,
32-message or prefix sampling cap. Excluded and empty Sessions are accounted
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
See [the simulation contract](docs/plans/spec/spec-0097-replayable-session-simulation.md).

### Local work-context model trial

The separate generative trial uses pinned `Qwen/Qwen3-4B` and the separately
approved `Qwen/Qwen3-8B` comparison to extract quoted work units
and assess explicit continuation. It does not train the model or replace the
embedding cache. Installation is an explicit public download (about 8.1 GB for
4B or an additional 16.4 GB / 15.3 GiB for 8B; about 24.5 GB for both);
choose a new dedicated model folder outside the repository with an existing
parent. Use an existing compatible PyTorch/Transformers/Hugging Face runtime:

```bash
python scripts/install-work-context-model.py --root /absolute/private/qwen3-4b
python scripts/install-work-context-model.py --root /absolute/private/qwen3-4b --verify
python scripts/install-work-context-model.py --model Qwen/Qwen3-8B --root /absolute/private/qwen3-8b
python scripts/evaluate-work-context-model.py \
  --model-root /absolute/private/qwen3-4b \
  --output /absolute/private/work-context-evaluation --split development
```

The default installation remains 4B. `--verify` and evaluation infer the model
only from its allowlisted ownership/revision and verified manifest; they do not
discover arbitrary models. Reusing a model folder for a different model is
rejected. Each installation keeps one content-addressed asset copy, not another
full copy for its snapshot; the 4B baseline is not automatically removed.
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
[the context-inference contract](docs/plans/spec/spec-0098-local-work-context-inference.md).

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
python scripts/evaluate-work-context-model.py \
  --model-root /absolute/private/qwen3-8b \
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
The completed [evidence-first trial](docs/plans/run/run-20260923-109-evidence-first-work-context.md)
fails both development gates; this is an experimental, rejected candidate, not
an admitted workflow reconstruction engine.

The separate protocol diagnostic investigates answer-format, option-order and
answer-code sensitivity on twelve new synthetic cases. It does not consume the
admission holdout or open private Sessions:

```bash
python scripts/diagnose-work-context-protocol.py --describe
python scripts/diagnose-work-context-protocol.py \
  --model-root /absolute/private/qwen3-8b \
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
python scripts/compare-work-role-formulations.py --describe
python scripts/compare-work-role-formulations.py \
  --model-root /absolute/private/qwen3-8b \
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

### Source-claim extraction and state trial

The separate [source-claim trial](docs/plans/feature/feat-0100-source-claim-extraction-and-binding-trial.md)
extracts historical claims, proposes scoped work bindings and lifecycle effects,
then computes reported state with a pure deterministic projector. Model-inferred
fulfillment is distinct from a source explicitly reporting completion. A completed
check does not complete its parent effort.

```bash
python scripts/evaluate-source-claims.py --describe
python scripts/evaluate-source-claims.py \
  --model-root /absolute/private/qwen3-8b \
  --output /absolute/private/source-claim-trial
python scripts/evaluate-source-claims.py \
  --model-root /absolute/private/qwen3-8b \
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
is added. [RUN-112](docs/plans/run/run-20260923-112-source-claim-extraction-and-binding-trial.md)
owns the actual measured result, not the presence of this command.
Its frozen candidate completed but failed admission: all 28 extraction responses
were rejected before binding, and only 3/28 reference-conditioned cases fully
passed. Zero-generation replay passes; holdout, private processing and UI updates
remain withheld. This command is an evaluation tool, not an admitted work extractor.

### Earlier model-free comparator

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
[the input and command contract](docs/plans/spec/spec-0095-bounded-work-reconstruction-experiment.md#local-invocation-and-file-shapes).
Synthetic correctness is not evidence that real work is reconstructed usefully.

## Local Data

Runtime data is stored under `~/Library/Application Support/LocalBrain` by default. The SQLite database, private `session-sources.toml`, indexed session and note content, task artifacts, exports, and logs stay outside the source repository.

Apple Notes indexing uses local macOS Automation and may trigger a permission prompt the first time it is connected. LocalBrain does not require Apple Notes access for its other sources.

Read [Privacy And Data Handling](docs/policies/project/privacy-and-data.md) before changing storage, export, logging, or external integration behavior.

## Documentation

- [Documentation Map](docs/README.md): owner and navigation map for all project docs
- [Product Model](docs/policies/project/product.md): product scope, terminology, and organization rules
- [Project Architecture](docs/policies/project/architecture.md): stack, source adapters, persistence, and implementation baseline
- [Markdown Rendering Contract](docs/policies/project/markdown-rendering.md): shared syntax, safety, local-reference, highlighting, and fallback rules
- [Maintenance Task Runner](docs/policies/operations/claude-task-runner.md): in-app Claude/Codex maintenance execution and review contract
- [Agent Workflow](docs/agents/README.md): PRD, feature, spec, build, screen-surface evaluation, and fix roles
- [Plans Index](docs/plans/README.md): open planning boundaries, active execution, and recently completed chains
- [Project Roadmap](docs/plans/project/roadmap.md): phased product direction and current priorities
- [Project Backlog](docs/plans/project/backlog.md): unresolved implementation work and decisions

Repository-local agent instructions are in [AGENTS.md](AGENTS.md).

## Project Status

Current phase status and priorities are maintained in the [Project Roadmap](docs/plans/project/roadmap.md#current-direction).
