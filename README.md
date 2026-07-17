# LocalBrain

LocalBrain is a local-first developer work context hub. It reconnects AI sessions, local projects, files, notes, Git activity, and external references around user-defined Workstreams so interrupted work can be understood and resumed.

The current MVP runs as a FastAPI web application on the local machine. A native macOS wrapper remains a later packaging step after the workflow is validated.

## Current Capabilities

- Ingest local Claude and Codex session history.
- Register and browse folders, individual files, and Apple Notes as Local Context sources.
- Organize work into user-created Workstreams and Threads.
- Link sessions, documents, local paths, projects, and external references to Threads.
- Maintain versioned checkpoints and review reversible resource Suggestions.
- Run Claude maintenance tasks for resource organization, checkpoint drafting, and priority review.
- Inspect session activity and source health through separate operational dashboards.

See [Project Architecture](docs/policies/project/architecture.md) for the implementation boundary and current feature baseline.

## Quick Start

LocalBrain currently targets macOS and requires Python 3.9 or later and [uv](https://docs.astral.sh/uv/). Claude CLI is optional unless the Task Runner is used.

From the project root, install the Python dependencies and start LocalBrain:

```bash
uv sync
uv run --no-sync uvicorn localbrain.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The local database is created automatically on first startup. Stop the server with `Ctrl+C`.

To import local Claude and Codex sessions, open the **Sources** page and run a scan. Local Context folders, files, and Apple Notes are added explicitly from the same page. The initial `uv sync` downloads Python packages, but LocalBrain's indexed content and runtime data remain on the local machine.

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
- [Claude Task Runner](docs/policies/operations/claude-task-runner.md): in-app Claude maintenance execution and review contract
- [Agent Workflow](docs/agents/README.md): PRD, feature, spec, build, screen-surface evaluation, and fix roles
- [Project Roadmap](docs/plans/project/roadmap.md): phased product direction and current priorities
- [Project Backlog](docs/plans/project/backlog.md): unresolved implementation work and decisions

Repository-local agent instructions are in [AGENTS.md](AGENTS.md).

## Project Status

Current phase status and priorities are maintained in the [Project Roadmap](docs/plans/project/roadmap.md#current-direction).
