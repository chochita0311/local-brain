# SPEC-0015: Session And Subsession Source Contract

## Metadata

- ID: `spec-0015`
- Status: `approved`
- Run ID: `run-20260717-15`
- Attempt: `1`
- Parent Feature: [feat-0015-session-subsession-source-contract](../feature/feat-0015-session-subsession-source-contract.md)
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lane: contract → ingestion and identity → consumer exclusion
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Source Set

- Human request: normalize Claude and Codex parentage, retain source and internal parent IDs, expose one direct-child depth later, isolate all subsessions from Workstream maintenance, Search, and statistics, and move branch ownership from workspace to Session.
- Parent Feature and PRD.
- `src/localbrain/schema.sql`, `db.py`, Claude and Codex parsers, scanner, read models, retrieval, runner, Workstream consumers, and current synthetic tests.
- [Product Model](../../policies/project/product.md), [Project Architecture](../../policies/project/architecture.md), [Claude Task Runner](../../policies/operations/claude-task-runner.md), and [Privacy And Data Handling](../../policies/project/privacy-and-data.md).

## Implementation Goal

- Persist source-neutral Session hierarchy and per-Session branch metadata, reconcile existing sources deterministically, remove workspace branch state, and make every approved exclusion consumer use the same primary-Session predicate.

## In-Scope Behavior

- Add Session hierarchy and branch fields to fresh and upgraded SQLite databases.
- Import Claude subagent JSONL as subsessions rather than lazy-only unindexed files.
- Read Codex parent and branch values only from the primary first `session_meta` record.
- Reconcile parents after all files for a source have been processed, including unchanged rows.
- Keep unresolved, unsafe, and nested child records as subsessions while preventing top-level fallback.
- Reprocess unchanged Claude and Codex source files once when the new contract is installed.
- Remove `workspaces.git_branch` from fresh and upgraded schemas and all read, retrieval, runner, manifest, and resource payloads.
- Exclude all subsessions from global Search, Session-derived statistics, Workstream pickers and generated organization candidates, and Workstream Claude maintenance candidate/evidence/manifest/Suggestion inputs.
- Preserve existing user-confirmed Session links and Suggestion decisions by retaining stable Session IDs during reclassification.
- Align Product Model, Project Architecture, and Claude Task Runner durable contracts.

## Out-Of-Scope Behavior

- Sessions/Projects navigation, pagination, dropdown presentation, detail timeline filtering, or replacement of existing Claude subagent routes.
- Persisted depth or root caches, recursive tree presentation, content-based parent inference, source mutation, or Git commands.
- Deleting subsession events, JSONL, links, reviewed Suggestions, or Run history.

## Affected Surfaces

- `src/localbrain/schema.sql`, `db.py`
- `src/localbrain/ingest/common.py`, `claude.py`, `codex.py`, `scanner.py`
- `src/localbrain/queries.py`, `retrieval.py`, `runner.py`, `workstreams.py`
- parser, migration, ingestion, query, retrieval, runner, and Workstream tests
- Product Model, Project Architecture, and Claude Task Runner policy

## Surface Lanes

- Contract lane:
  - dependency order: first
  - responsibility: exact values, ownership, source evidence, migration, exclusion, and fallback rules
  - validation evidence: Feature, Spec, schema, and durable policies agree
- Ingestion and identity lane:
  - dependency order: after contract lane
  - responsibility: producers, persistence, migration, reprocessing, parent reconciliation, and stable identity
  - validation evidence: synthetic Claude and Codex parser, scan, migration, orphan, cycle, branch, and rescan tests
- Consumer exclusion lane:
  - dependency order: after ingestion and identity lane
  - responsibility: Search, statistics, Workstream organization, retrieval, evidence, manifest, and resource payload predicates
  - validation evidence: synthetic query and candidate bundles contain primary Sessions only

## State And Interaction Contract

- Primary: `session_role = 'primary'`, `parent_external_id IS NULL`, and `parent_session_id IS NULL`.
- Resolved subsession: `session_role = 'subsession'`, source parent identity retained, and `parent_session_id` points to another Session from the same source.
- Unresolved or unsafe subsession: role and source evidence remain, `parent_session_id IS NULL`, and the record is ineligible for top-level, Search, statistics, Workstream candidate, or maintenance consumers.
- Nested subsession: parentage remains stored, but later UI consumers admit only a child whose parent is primary.
- Parent deletion: `ON DELETE SET NULL` clears only the internal FK; role and source parent identity remain.
- Re-scan: stable `(source_id, external_id)` identity updates the same row and deterministically repairs a resolvable parent relation.

## Data And Contract Assumptions

- `sessions` adds:
  - `git_branch TEXT NULL`
  - `session_role TEXT NOT NULL DEFAULT 'primary' CHECK(session_role IN ('primary', 'subsession'))`
  - `parent_external_id TEXT NULL`
  - `parent_session_id INTEGER NULL REFERENCES sessions(id) ON DELETE SET NULL`
- Add indexes for primary recent-session filtering and `parent_session_id` child lookup.
- `session_class` remains `work` or maintenance policy and is independent of hierarchy.
- `parent_external_id` is source evidence. `parent_session_id` is the resolved LocalBrain relation. Neither `depth` nor `root_session_id` is persisted.
- Claude hierarchy comes from the parent-owned `subagents/` path and resolves to the owning parent Session external identity. A child uses its `agent-*.jsonl` filename stem as its external identity because a record-level `sessionId` may identify the owning parent.
- Codex hierarchy uses primary `session_meta.payload.parent_thread_id`, compatible `forked_from_id`, and `source.subagent` evidence. Later embedded `session_meta` records never replace primary identity or Git context.
- Claude uses the last non-empty top-level `gitBranch`. Codex uses primary `session_meta.payload.git.branch`. Values are trimmed and empty values become `NULL`.
- Existing Session source files are marked stale only when the new columns are first installed so one normal synchronization backfills the new contract.
- Existing `workspaces.git_branch` values are discarded, never copied into Sessions. Dropping the column preserves workspace IDs and all referencing user organization.
- A Session is eligible for global Search, Session-derived statistics, Workstream candidate generation, or maintenance retrieval only when `session_role = 'primary'` and its existing consumer-specific policy also passes.

## Contract Surfaces

- Producer expectations: parsers emit stable role, source parent identity, and Session branch values from authoritative source metadata only.
- Consumer expectations: top-level and exclusion consumers explicitly require `session_role = 'primary'`; direct-child consumers introduced later join through `parent_session_id`.
- Generated artifacts: maintenance manifests, evidence, fingerprints, counts, and Suggestions contain no subsession or workspace branch field.
- Source-of-truth owner: original JSONL for Session metadata; `schema.sql` plus compatible migrations for normalized persistence.
- Stale-assumption check: every `sessions.session_class = 'work'` consumer and every `git_branch` consumer is reviewed and classified rather than updated mechanically without purpose.

## Required Evaluators

- Contract: schema parity, migration preservation, source producer shape, parent resolution, primary predicate, payload removal, and durable policy alignment.
- Design: not required; no new visual surface.
- Functional: parser behavior, fresh and upgraded DBs, rescan reconciliation, orphan/cycle handling, Search/statistics exclusion, and maintenance bundle exclusion.
- UX heuristic: not required for this foundation run.

## Acceptance Mapping

- Source-neutral relationship semantics map to parser fields, Session columns, reconciliation, and same-source safety tests.
- Orphan non-fallback maps to `session_role`-based top-level predicates and parent deletion tests.
- Per-Session branch ownership maps to parser fixtures, Session persistence, query/resource payloads, and workspace-column removal tests.
- Workstream isolation maps to candidate bundle, evidence, manifest, and generated-Suggestion tests.
- Search/statistics isolation maps to search index and every Session-derived aggregation test.
- Non-mutation maps to synthetic fixtures and absence of Git or source write operations.

## Evaluation Focus

- Fresh versus upgraded schema parity, including a pre-contract database with existing workspace references.
- Unchanged Codex files are actually reprocessed once and existing row IDs survive.
- A child whose parent disappears never becomes top-level.
- No workspace branch key survives in Project or maintenance resource payloads.
- No subsession evidence leaks through confirmed links, FTS matches, derived Projects, counts, or fingerprints.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-17`: approved after human review fixed both parent identifiers, one-depth presentation, per-Session branch ownership, and complete Search/statistics exclusion.
