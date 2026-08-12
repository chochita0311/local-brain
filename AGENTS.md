# Repository Guidelines

## Purpose

- Build a local-first developer work context hub for reconnecting sessions, projects, documents, and external references.
- Preserve provenance and user control while making interrupted work easier to resume.
- Keep private runtime content on the local machine and outside the Git repository.

## Use This File For

- quick repository orientation
- top-level working and privacy rules
- source-of-truth routing into `README.md`, `docs/policies/`, and `docs/plans/`

## Product Scope

In scope:

- local Claude and Codex session ingestion
- user-managed Local Context sources
- Workstream, Thread, checkpoint, and resource organization
- local retrieval, reviewable Suggestions, and workflow insights
- approved read-only external source integration

Out of scope unless explicitly planned:

- cloud sync or multi-user collaboration
- silent external writes or unreviewed relationship changes
- mandatory external AI or embedding services
- native macOS packaging before the local web workflow is validated

## Codebase Map

- `src/localbrain/`: FastAPI application, SQLite access, ingestion, retrieval, and Task Runner
- `src/localbrain/templates/`: server-rendered Jinja2 views
- `src/localbrain/static/`: browser assets
- `tests/`: unit and integration-oriented behavior tests
- `docs/agents/`: planning and execution roles, flows, operations, and profiles
- `docs/policies/`: durable product, architecture, privacy, development, and operations contracts
- `docs/plans/`: roadmap, backlog, PRDs, features, specs, Runs, evaluations, and fix artifacts
- `DESIGN.md`: creative design intent and source interpretation
- `README.md`: user-facing overview and quick start

Runtime data belongs under `~/Library/Application Support/LocalBrain` by default and is not part of the codebase.

## Source Of Truth

- Keep `AGENTS.md` short and operational.
- Keep product overview and first-run commands in `README.md`.
- Keep durable rules, definitions, contracts, and guides under `docs/policies/`.
- Keep sequencing, priorities, unresolved work, and roadmaps under `docs/plans/`.
- Treat code and database schema as implementation truth; update their owner docs when behavior changes.

## Working Rules

- Read touched modules and their owner docs before changing behavior.
- Prefer existing patterns and narrowly scoped changes.
- Preserve provenance for imported, inferred, and user-confirmed information.
- Keep generated Suggestions reversible and require explicit acceptance before changing Workstream organization.
- Do not revert unrelated user changes.
- Run the smallest relevant verification and state clearly when required checks cannot run.

## Planning And Execution Gate

- Use [Agent Workflow](docs/agents/README.md) when a request enters the shared PRD, feature, spec, or execution-loop process.
- Before delegating bounded work, apply [Competence-First Delegation](docs/policies/harness/competence-first-delegation.md) for admission, worker selection, context transfer, fallback, and primary-agent ownership.
- When prior context materially affects an orientation, work start, direction change, review boundary, block, or handoff, apply [Operator Briefing And Review Receipts](docs/policies/harness/operator-briefing-and-review-receipts.md) without changing the underlying workflow or approval state.
- A PRD request is planning-only until the human owner approves its boundary.
- A `draft` PRD or unapproved Feature must not trigger spec work, code changes, or evaluation.
- If an open point can change scope, acceptance, dependency, or user-visible behavior, stop and ask instead of carrying the ambiguity into implementation.
- For visible screen or interaction work, read the [Design Constitution](docs/policies/design/design-constitution.md), declare the Frontend or Fullstack profile and affected surface lanes, and apply [Design Evaluation](docs/policies/design/design-evaluation.md), functional evaluation, and [Interaction Evaluation](docs/policies/experience/interaction-evaluation.md).

## Privacy And Data Rules

- Never commit databases, session JSONL, note contents, task artifacts, exports, logs, credentials, or machine-specific workflow context.
- Keep runtime and indexed personal data outside the repository; `.gitignore` is only a fallback guard.
- Use synthetic data in tracked tests, examples, screenshots, and documentation.
- Do not transmit local content to an external service unless the user explicitly requests it and the integration is approved.
- Keep credentials in existing operating-system or approved gateway facilities rather than LocalBrain storage.
- Run `scripts/check-repo-privacy.sh` before staging or committing repository changes.
- Treat unreviewed images, PDFs, archives, and fonts as private until their path is explicitly added to `.privacy-allowlist`.
- Follow [Privacy And Data Handling](docs/policies/project/privacy-and-data.md) for storage and integration changes.

## Documentation Rules

- Update the document that owns a changed fact in the same turn as the behavior change.
- Use kebab-case filenames under `docs/`.
- Remove duplicate guidance by linking to one canonical owner.
- Update `README.md` for user-visible setup or usage changes.
- Update `docs/policies/` for durable behavior, constraints, and contracts.
- Update `docs/plans/` for priorities, sequencing, and unresolved work.
- Keep machine-specific workflow inventories and handoff context out of Git; tracked owner docs are the repository source of truth.

## Verification

```bash
./scripts/check-repo-privacy.sh
uv run python -m unittest discover -s tests -v
```

For UI behavior, also run the local server and verify the affected route in a browser.
