# LocalBrain

LocalBrain is a local-first developer work context hub. It reconnects AI sessions, local projects, files, notes, Git activity, and external references around user-defined Workstreams so interrupted work can be understood and resumed.

The current MVP runs as a FastAPI web application on the local machine. A native macOS wrapper remains a later packaging step after the workflow is validated.

## Current Capabilities

- Ingest local Claude and Codex session history.
- Register and browse folders, individual files, and Apple Notes as Local Context sources.
- Read safe, locally rendered Markdown in Local Context previews, context-aware full Document views, and Session or Subsession conversations.
- Organize work into user-created Workstreams and Threads.
- Link sessions, documents, local paths, projects, and external references to Threads.
- Maintain versioned checkpoints and review reversible resource Suggestions.
- Run Claude maintenance tasks for resource organization, checkpoint drafting, and priority review.
- Register Jira tickets/projects and Confluence Pages/Spaces from real URLs in a local-only Atlassian inventory. A first URL can create its Source Instance and Site after one explicit local access-path choice; the connection may remain local-only until a Cloud ID or Gateway alias is bound. Browse and search known Items by Source, Site, Space, coverage, freshness, local Topic/Tag, and Workstream; keep local notes and open a remote URL only through an explicit link. Preview one Item, Space, Thread, Workstream, or all known Items locally; submitting the bounded maintenance refresh requires both a current capability observation and an approved host-side read executor. Ordinary browsing, setup, search, and local classification never contact Atlassian. Optional Space-candidate discovery uses the same connected preconditions, remains a separate bounded Run, and never registers results automatically.
- Inspect Claude and Codex tokens, estimated trend cost, primary-work Session volume, active days, and Daily, Weekly, or Cumulative history in Sessions Dashboard.
- Explore the complete schema, nine subject areas, Mermaid ERDs, and table contracts from the read-only **System > Schema** surface.

See [Project Architecture](docs/policies/project/architecture.md) for the implementation boundary and current feature baseline.

## Quick Start

LocalBrain currently targets macOS and requires Python 3.9 or later and [uv](https://docs.astral.sh/uv/). Claude CLI is required only for Claude-backed maintenance Runs; Codex CLI is required only when Codex is selected for external synchronization.

From the project root, install the Python dependencies and start LocalBrain:

```bash
uv sync
uv run --no-sync uvicorn localbrain.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The local database is created automatically on first startup. Stop the server with `Ctrl+C`.

To import local Claude and Codex sessions, use **동기화** on the Sessions page. The same action automatically repairs derived usage records when LocalBrain's source-normalizer contract changes; no aggregate-reset control is required. The **Sources** page keeps the wider scan across Session sources and enabled Local Context folders, files, and Apple Notes. The initial `uv sync` downloads Python packages, but LocalBrain's indexed content and runtime data remain on the local machine.

Sessions Dashboard defaults to the latest 30 inclusive local days. Its Source, Range, Tokens/Cost, and paired custom-date controls are ordinary GET state, so a filtered view can be bookmarked or reopened. Cost is a locally reproduced trend estimate from stored price snapshots, including model-specific request-context tiers when the frozen reference defines them; it is not billed spend, and unsupported pricing stays visibly unavailable.

Actual model usage from primary, maintenance, and subsession records contributes to dashboard tokens and cost. Claude's source-generated `<synthetic>` assistant or API-error records remain stored for Session evidence but are excluded from usage periods, totals, coverage, and breakdowns because they are not model usage.

The same selected records can be explained by Source, normalized Model, or first-observation Project snapshot. The composition list keeps compatible shares and evidence links separate from the trust region, which reports token and price coverage, source freshness, calculation time, and retained data when a source needs attention.

The dashboard deliberately stops at observed selected-period and month-to-date values. It does not surface a projected month-end cost, budget, cap, or billed amount.

**System > Schema** opens the complete packaged data-model overview without reading database rows. Subject and table selections use ordinary bookmarkable links, and the textual catalog remains available if local Mermaid rendering is unavailable. A rendered relationship map has visible zoom, reset, and width-fit controls; `Ctrl`/`Cmd` plus wheel or a browser-normalized trackpad pinch zooms in place, while an unmodified wheel keeps ordinary scrolling.

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

## Local Data

Runtime data is stored under `~/Library/Application Support/LocalBrain` by default. The SQLite database, indexed session and note content, task artifacts, exports, and logs stay outside the source repository.

Apple Notes indexing uses local macOS Automation and may trigger a permission prompt the first time it is connected. LocalBrain does not require Apple Notes access for its other sources.

Read [Privacy And Data Handling](docs/policies/project/privacy-and-data.md) before changing storage, export, logging, or external integration behavior.

## Documentation

- [Documentation Map](docs/README.md): owner and navigation map for all project docs
- [Product Model](docs/policies/project/product.md): product scope, terminology, and organization rules
- [Project Architecture](docs/policies/project/architecture.md): stack, source adapters, persistence, and implementation baseline
- [Markdown Rendering Contract](docs/policies/project/markdown-rendering.md): shared syntax, safety, local-reference, highlighting, and fallback rules
- [Maintenance Task Runner](docs/policies/operations/claude-task-runner.md): in-app Claude/Codex maintenance execution and review contract
- [Agent Workflow](docs/agents/README.md): PRD, feature, spec, build, screen-surface evaluation, and fix roles
- [Project Roadmap](docs/plans/project/roadmap.md): phased product direction and current priorities
- [Project Backlog](docs/plans/project/backlog.md): unresolved implementation work and decisions

Repository-local agent instructions are in [AGENTS.md](AGENTS.md).

## Project Status

Current phase status and priorities are maintained in the [Project Roadmap](docs/plans/project/roadmap.md#current-direction).
