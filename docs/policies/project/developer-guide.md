# Developer Guide

## Prerequisites

- macOS for the current Apple Notes integration and default data location
- Python 3.9 or later
- `uv` for dependency and virtual environment management
- Claude CLI only when exercising the Claude Task Runner

## Setup And Run

Activate the repository-owned pre-commit hook after cloning:

```bash
git config core.hooksPath .githooks
```

Install dependencies:

```bash
uv sync
```

Initialize or refresh indexed sources:

```bash
uv run localbrain scan --full
```

Run the development server:

```bash
uv run uvicorn localbrain.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Dependency Certificate Troubleshooting

The default `uv sync` command verifies PyPI with uv's bundled certificate roots and should work on a normal network. If it fails with `UnknownIssuer` on a managed network, a proxy or security product may be using a certificate authority trusted by macOS but not included in uv's bundled roots.

Retry the failed installation using the macOS system certificate store:

```bash
uv sync --system-certs
```

The flag applies to that command only. If later `uv` commands also need network access through the same managed network, set `UV_SYSTEM_CERTS=true` for the current shell before running them. Do not disable TLS verification. This setting affects dependency downloads only; it does not change where LocalBrain stores or processes indexed data.

## Configuration

LocalBrain reads these environment variables at process startup:

| Variable | Default | Responsibility |
| --- | --- | --- |
| `LOCALBRAIN_DATA_DIR` | `~/Library/Application Support/LocalBrain` | SQLite database and Run artifacts |
| `LOCALBRAIN_CONTEXT_ROOT` | `~/Projects/context` | Initial Local Context folder discovery |
| `LOCALBRAIN_CLAUDE_ROOT` | `~/.claude/projects` | Claude session history root |
| `LOCALBRAIN_CODEX_ROOT` | `~/.codex/sessions` | Codex session history root |
| `LOCALBRAIN_CLAUDE_BIN` | resolved from `PATH` | Claude CLI executable used by the Task Runner |
| `LOCALBRAIN_MCP_CALL_BUDGET` | `20` | Advisory MCP call budget per maintenance Run |

Do not place secrets in tracked environment files. See [Privacy And Data Handling](privacy-and-data.md) before changing data locations or persistence behavior.

## Change Approach

- Read the touched modules, tests, and owner docs first.
- Reuse current FastAPI, SQLite, Jinja2, and local helper patterns before introducing a new abstraction.
- Keep migrations additive until a deliberate migration framework replaces the current startup migration path.
- Preserve source IDs, timestamps, provenance, and user review state when changing ingestion or relationships.
- Keep maintenance artifacts excluded from ordinary Session and Local Context ingestion.

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
- Update [Claude Task Runner](../operations/claude-task-runner.md) for in-app maintenance execution or review semantics.
- Update [Project Roadmap](../../plans/project/roadmap.md) for sequencing and [Project Backlog](../../plans/project/backlog.md) for unresolved work.
