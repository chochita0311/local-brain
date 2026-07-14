# Claude Task Runner

## Purpose

The Task Runner starts a local Claude maintenance process from a Workstream for resource organization, checkpoint drafting, or priority review. LocalBrain owns the durable Run record; Claude execution is ephemeral and must not become an ordinary indexed work Session.

## Execution Contract

- Each Run starts a new top-level Claude process rather than resuming an ordinary work Session.
- The default working directory is the user's home directory, expanded from `~`, so approved local sources can be discovered beyond an already linked project.
- The process uses `--print --no-session-persistence --output-format stream-json --json-schema`.
- The permission mode is read-only planning.
- FastAPI launches the CLI as a background child process so request handling remains non-blocking.
- The top-level agent may use subagents only when broader exploration is necessary.
- Cancellation, completion, failure, and observed tool usage are persisted in `maintenance_runs`.
- Run state is one of `queued`, `running`, `completed`, `failed`, `cancelled`, or `interrupted`.
- The Run Console polls live status and output, exposes artifacts, and supports cancellation without blocking FastAPI requests.

`LOCALBRAIN_CLAUDE_BIN` may select the Claude executable. `LOCALBRAIN_RUN_ID` is provided to the child process for Run attribution.

## Local Retrieval First

Before Claude starts, LocalBrain performs deterministic SQLite and FTS5 retrieval without an AI call.

- The context manifest contains Session, Document, Project, local-path, and external-reference candidates.
- Candidate resources and matching evidence have relevance criteria but no hard count cap.
- A resource is represented once even when it is relevant to multiple Threads.
- Many-to-many Thread assignments and evidence IDs are stored separately.
- Full evidence is written as one deduplicated file per candidate and opened only when needed.
- An unchanged candidate fingerprint carries forward the previous structured result so Claude can avoid repeated investigation.

Claude should use external MCP tools only to fill gaps that remain after local evidence review.

## MCP Budget

`LOCALBRAIN_MCP_CALL_BUDGET` sets the advisory MCP call budget for one Run and defaults to `20`.

The current Claude CLI can cap monetary spend but does not expose a hard MCP call-count limit. LocalBrain therefore:

- states the budget in the prompt
- records observed `mcp__*` stream events
- reports budget overruns after calls occur

This is a soft policy, not strict enforcement. A future MCP proxy or broker boundary is required for a hard call-count limit.

## Persistence

Run metadata is stored in `maintenance_runs` inside `localbrain.db`. Artifacts are stored under:

```text
~/Library/Application Support/LocalBrain/runs/<run-id>/
```

Artifacts include the generated prompt, manifest and fingerprints, stream output, structured result, and per-resource evidence. They are private runtime data and must remain outside Git.

## Review And Mutation Rules

- Structured Resource and Checkpoint candidates are saved as pending Suggestions.
- A Resource candidate targets the most relevant Thread by default.
- A Workstream-level target is reserved for evidence genuinely shared by multiple Threads.
- Accepting a Resource materializes its local path or external reference and then creates the link.
- Accepting a Checkpoint creates a versioned confirmed state with the current resource snapshot.
- Rejected Suggestions remain visible and can be restored.
- Refresh replaces eligible pending Claude Run Suggestions only after a new structured result succeeds.
- Accepted and rejected decisions survive refresh.
- A failed or cancelled Run must not clear the review queue or silently mutate Workstream organization.

Only explicit user acceptance may change Workstream organization.

## Index Exclusion

Maintenance prompt headers identify housekeeping activity:

```text
[LOCALBRAIN_RUN: lb-<12 hex characters>]
[MODE: maintenance]
```

Sessions beginning with this exact marker retain source metadata but are excluded from activity events, full-text search, and Sessions Dashboard statistics. Run artifacts and lazy subagent evidence must also remain outside ordinary Session and Local Context ingestion.

## Required Follow-up

Queue recovery, concurrency limits, process timeout, orphan detection, hard MCP enforcement, and child-process shutdown tests remain open in the [Project Backlog](../../plans/project/backlog.md).
