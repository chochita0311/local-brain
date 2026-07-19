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
| `LOCALBRAIN_TIMEZONE` | system IANA timezone, then `UTC` | Local calendar boundaries for usage and activity reports |

Do not place secrets in tracked environment files. See [Privacy And Data Handling](privacy-and-data.md) before changing data locations or persistence behavior.

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

- LocalBrain pins Mermaid `11.16.0` as a project dependency and esbuild `0.28.1` as its build-only bundler in the repository-owned `package.json` and `package-lock.json`.
- The packages come from the public npm distributions named `mermaid` and `esbuild`. Both direct dependencies are MIT-licensed; reviewed license copies are emitted with the browser asset and the lockfile retains transitive package license metadata.
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

- Application screens consume `src/localbrain/static/mermaid-adapter.js`, not npm paths directly. The adapter initializes Mermaid once with strict security, never scans the page automatically, and renders only application-owned nodes marked `data-localbrain-mermaid="owned"` whose source is LocalBrain-authored markup. Imported documents, Session content, persisted rows, request/query values, and arbitrary user text must never be inserted into those source nodes.
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
- Update [Claude Task Runner](../operations/claude-task-runner.md) for in-app maintenance execution or review semantics.
- Update [Project Roadmap](../../plans/project/roadmap.md) for sequencing and [Project Backlog](../../plans/project/backlog.md) for unresolved work.
