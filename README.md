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
- Compare Sessions Dashboard usage by source and Daily, Weekly, or Monthly range; Monthly shows each month's total. Estimated cost uses dated OpenAI and Anthropic model rates, including GPT-6 Astra, GPT-6 Sol, and GPT-6.1 Sol. Eligible retained unpriced GPT-6.1 Sol usage is calculated once on startup using its dated Standard/Fast rate. Codex Standard/Fast is selected from recorded thread settings when available; early GPT-5.6 Priority prices use a marked historical 2x estimate. Spark uses an explicitly labeled ccusage 20.0.17 GPT-5.3-Codex proxy, and historical GPT-5.6 or GPT-5.5 Fast requests above 272K input tokens use a separate labeled ccusage-style long-context estimate where no applicable Fast rate was published. The USD amount is an API-equivalent trend estimate, not a subscription charge; other models without their own published rate remain unpriced, and unsupported model/tier/context combinations remain partial. Zero-token Codex snapshots are omitted from dashboard totals, partial pricing coverage remains marked, and source synchronization details remain on Sources.
- Change either Sessions Dashboard calendar date to show that period immediately; the history chart skips empty dates before the first and after the last value in a custom range, with daily labels at both ends and each month's 1st and 15th.
- Cost history opens first; the chart switch places Cost before Tokens, and bar-top labels use whole-number compact values.
- Compare Source, Model, and Project composition in one table with shared column headings for Tokens, Cost, Sessions, and share; expand the list to see additional groups.
- Switch the Sessions Dashboard heading between Usage & Cost and Insights. Insights ranks skills by the number of Sessions that used or referenced them, counting a skill at most once per source and native Session across repeated reads and requests. The list shows the latest reference time and retains history after a local file disappears. This measures use/reference reach, not execution frequency or successful application. See the [Insights contract](docs/policies/project/product.md#insights) for admitted evidence and coverage limits.
- The Insights improvement analyzer accepts a question or discovers opportunities from bounded primary-work Session excerpts. One explicit click starts one analysis-only Codex CLI Run; its status, observed usage, stored estimated cost, source-backed Markdown report, repeatable download, and earlier Runs remain available in Insights. Open the report settings to inspect its calculation state and frozen price basis; missing usage or prices remain explicitly unavailable. Reanalysis creates a new Run. Observed analysis tokens and estimated cost also enter Usage & Cost under the selected Codex source, with Project `Unassigned`; analysis remains outside ordinary Sessions and future analysis evidence. Each Run executes in its private runtime artifact directory. New Runs require that Codex home to be registered in Sources and explicitly use Standard service tier.
- Open `작업 흐름` from an eligible primary Session to inspect a deterministic
  Episode lineage, bounded branches, relation reasons, and grouped source
  evidence. Contextual Trace controls can preview and append reversible
  user-confirmed boundary corrections without changing Sessions or source
  evidence. The first Focus Map and correction path use no AI model.
- Explore the packaged data model, subject ERDs, and table contracts from the read-only **System > Schema** surface.

Detailed behavior belongs to the [Product Model](docs/policies/project/product.md), while implementation and I/O boundaries belong to [Project Architecture](docs/policies/project/architecture.md).

## Quick Start

LocalBrain currently targets macOS. The [macOS Installation And Local Storage
guide](docs/policies/project/installation-and-storage.md) covers a new Mac with
no Python or development tools, a dedicated application installation, optional
local models, updates, and bounded storage. Local models are optional feature
dependencies. Python 3.11 is recommended and can be installed by
[uv](https://docs.astral.sh/uv/); the base package supports Python 3.9+.
Claude CLI is required for Claude-backed maintenance Runs; Codex CLI is required
for personal improvement analysis Runs and when selected for external synchronization.

For an installed application, start it with:

```bash
localbrain doctor
localbrain serve
```

Use [the installation guide](docs/policies/project/installation-and-storage.md#install-a-distribution-wheel)
for a distribution wheel or a public source archive on a new Mac. The installed
package owns its code, templates, browser assets and commands; it can run without
a source checkout. Development setup belongs to the
[Developer Guide](docs/policies/project/developer-guide.md#setup-and-run).

Open `http://127.0.0.1:8000`. The local database is created automatically on first startup. Stop the server with `Ctrl+C`.

### Run a personal improvement analysis

Open **Sessions Dashboard → Insights**, enter a question and select **질문 분석**, or select **개선 기회 찾기** without a question. Starting a Run sends selected local Session excerpts to the model service through Codex CLI and may use substantial tokens. The report appears below the Run list when complete. Use **Markdown 다운로드** to save a copy for a separate work Session; repeating an analysis creates a new Run and preserves the earlier report. The default model is `gpt-6-astra`; the profile and model chosen for each Run are retained with its history. See the [Developer Guide](docs/policies/project/developer-guide.md#personal-improvement-analysis) for profile and model configuration.

Each suggested improvement should explain where and how to apply it, who acts, what setup is needed, and what work repeats. The handoff distinguishes a small trial from continued adoption and marks any unverified target or loading method for confirmation in the work Session.

When earlier advice appears in the supplied context, the report should distinguish what was proposed from what was applied or helped. It should carry forward a useful missing application step while respecting working methods and explicit deferral. Missing application evidence remains unknown; there is no automatic tracking of adoption.

Discovery samples work across sources and months, preferring recent Sessions within each group. It does not balance projects or rank all your work by improvement priority. A report can therefore focus on one project's workflow, and another Run can revisit the same candidate. The [evidence selection contract](docs/plans/spec/spec-0107-personal-insight-evidence-manifest.md#selection) describes the fixed sampling limits; a report's coverage and missing evidence determine how broadly its conclusions apply. Insights shows the actual sampled scope and source distribution. New reports explain why the candidate and improvement type fit the observed goal, and request only specific missing conversation messages after checking what was already supplied.

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

Prepare or update the private cached map explicitly with
[the local model commands below](#optional-local-models). Browsing
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
Local Context folders, files, and Apple Notes. Installation downloads public
Python packages; indexed content and runtime data remain on the local machine.

Sessions supports combined and per-source inventory scopes without an age cutoff. The [Session inventory contract](docs/policies/project/product.md#application-navigation-and-session-inventory), [analytical read models](docs/policies/project/architecture.md#analytical-read-models), and [Schema Explorer boundary](docs/policies/project/architecture.md#persistence-model) own the detailed behavior.

Installation and network-certificate troubleshooting belong to
[the installation guide](docs/policies/project/installation-and-storage.md).
Source development, configuration and verification belong to the
[Developer Guide](docs/policies/project/developer-guide.md).

<a id="experimental-work-reconstruction"></a>

## Optional Local Models

The base app runs without a local model. Preparing the full-history affinity map
requires the optional model runtime and Qwen3-Embedding-0.6B. Follow
[Optional Local Models](docs/policies/project/installation-and-storage.md#optional-local-models)
for the runtime installation, then run:

```bash
localbrain models install embedding
localbrain simulate
```

Public weights are verified and reused from the user-level Hugging Face cache.
LocalBrain keeps small model registration/verification files under its own
`models/` directory. Private embeddings and map results belong in its local
cache. Opening the map never downloads or runs a model. Preparation covers all
eligible stored primary-work messages, supports resume/reuse, and preserves the
source database. Results expire after 30 inactive days.

### Local work-context model trial

Qwen3-4B and Qwen3-8B remain optional development experiments. Their recorded
quality trials did not admit an automatic workflow producer. See the
[model development tools](docs/policies/project/developer-guide.md#local-model-development-tools)
for their installation, frozen candidates, gates, diagnostics and replay.

### Source-claim extraction and state trial

The [source-claim development trial](docs/policies/project/developer-guide.md#source-claim-extraction-and-state-trial)
remains an evaluation tool; its failed admission does not enable private
processing, organization writes or a product workflow extractor.

### Earlier model-free comparator

The [earlier development comparator](docs/policies/project/developer-guide.md#earlier-model-free-comparator)
accepts explicit fixtures or a selected local database and manifest. It is
separate from the packaged full-history map.

## Local Data

The primary database, private `session-sources.toml`, model registrations and saved
Run reports live under `~/Library/Application Support/LocalBrain`. Rebuildable
embeddings and previews live under `~/Library/Caches/LocalBrain`; public model
weights use the Hugging Face cache. Development evidence has a separate private
location. These paths are configurable and all runtime content stays outside
Git and installation packages. See [storage ownership](docs/policies/project/installation-and-storage.md#storage-ownership-and-configuration)
for retention, upgrades and cleanup.

Apple Notes indexing uses local macOS Automation and may trigger a permission prompt the first time it is connected. LocalBrain does not require Apple Notes access for its other sources.

Read [Privacy And Data Handling](docs/policies/project/privacy-and-data.md) before changing storage, export, logging, or external integration behavior.

## Documentation

- [macOS Installation And Local Storage](docs/policies/project/installation-and-storage.md): installation without a source checkout, optional models, updates and cleanup
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
