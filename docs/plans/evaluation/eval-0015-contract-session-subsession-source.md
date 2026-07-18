# EVAL-0015: Session And Subsession Source Contract

## Metadata

- ID: `eval-0015-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260717-15`
- Attempt: `1`
- Feature: [feat-0015-session-subsession-source-contract](../feature/feat-0015-session-subsession-source-contract.md)
- Spec: [spec-0015-session-subsession-source-contract](../spec/spec-0015-session-subsession-source-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: contract, ingestion identity, and consumer exclusion
- Created: `2026-07-17`

## Scope

- Compared the approved Feature and Spec with the fresh schema, compatible migration, Claude and Codex producers, reconciliation, and every Session or workspace-branch consumer.
- Checked Product Model, Project Architecture, and Claude Task Runner ownership language against implementation.

## Contract Evidence

- `sessions` owns nullable `git_branch`, `session_role`, source-backed `parent_external_id`, and an `ON DELETE SET NULL` self-reference through `parent_session_id`; neither depth nor root identity is persisted.
- `workspaces` retains `canonical_path` and `git_root` but no branch column. The compatible migration discards the ambiguous workspace value without rebuilding workspace IDs or user-curated relations.
- Claude emits hierarchy only from the parent-owned `subagents/` path, uses the `agent-*.jsonl` stem as child identity, and uses the last non-empty top-level `gitBranch`. Codex reads parent, subagent marker, and branch only from the first primary `session_meta` record.
- Reconciliation restricts parents to the same source map, rejects self and cyclic relations, and leaves missing parents classified as hidden subsessions.
- Search indexing, Dashboard and activity statistics, source and tool statistics, workspace and Project aggregates, Workstream pickers, generated Suggestions, retrieval evidence, and runner manifests all require `session_role = 'primary'`.
- A user-facing Session lookup admits a primary Session or one resolved direct child of a primary Session; orphan and deeper descendants do not fall back to ordinary details.
- Stale-assumption searches found no runtime `workspaces.git_branch` consumer and no work-Session aggregate or candidate producer missing the primary-Session predicate.

## Checks

- Fresh schema table and foreign-key introspection.
- Compatible migration fixture with an existing workspace ID, project link, source file, and legacy branch value.
- Repository-wide searches for workspace branch, Session class, Session role, and parent consumers.
- Full unit suite and diff whitespace check.

## Findings

- No blocking finding.

## Regression Notes

- Ordinary primary Session identity, maintenance classification, workspace identity, existing resource links, repository-root recognition, and source-local privacy boundaries passed.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-07-17`: contract passed after direct-detail fallback and all Session-derived statistical consumers were explicitly checked.
- `2026-07-17`: FEAT-0018 compatibility validation clarified that Claude child identity must remain the `agent-*.jsonl` stem when a record-level `sessionId` denotes the parent; parser regression coverage passed.
