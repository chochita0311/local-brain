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
- Register and browse Jira and Confluence records locally, with optional access and explicit bounded remote actions.
- Inspect source-aware Session inventory, pinned recall, related evidence, and token or estimated-cost history.
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
