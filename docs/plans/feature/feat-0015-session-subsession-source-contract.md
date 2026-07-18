# FEAT-0015: Session And Subsession Source Contract

## Metadata

- ID: `feat-0015`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0002-session-browsing-and-subsession-organization](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Created: `2026-07-17`
- Updated: `2026-07-17`

## Goal

- Establish one source-neutral contract for primary Sessions, child subsessions, unresolved-parent subsessions, Session-owned read-only branch metadata, rescan reconciliation, and Workstream Claude maintenance exclusion across Claude and Codex.

## Acceptance Contract

- Parentage comes only from authoritative source evidence: Claude's parent-owned subagent directory structure or Codex metadata such as `source.subagent`, `parent_thread_id`, and compatible fork identity.
- A zero-question count, fallback title, timestamp proximity, tool-only activity, or content similarity never establishes parentage by itself.
- Valid child records retain their source identity and a resolvable parent relationship but are distinguishable from top-level Sessions for downstream consumers.
- A child whose parent cannot be resolved remains recoverable from authoritative source data but is classified as non-displayable and cannot fall back to an ordinary top-level Session.
- The normalized Session relation uses an orthogonal `session_role` value of `primary` or `subsession`, a source-backed nullable `parent_external_id`, and a resolved nullable self-reference `parent_session_id` with `ON DELETE SET NULL` behavior.
- `session_class` continues to own the existing `work` versus maintenance policy and is not overloaded with hierarchy meaning.
- A primary Session has no parent relation. A resolved subsession points to a different Session from the same source; a source-identified subsession with no resolved parent remains a subsession and is therefore hidden rather than falling back to primary.
- Self-parent, cross-source parent, and cyclic relations are not materialized as displayable hierarchy. Reconciliation preserves the subsession classification and leaves an unsafe relation unresolved.
- The schema does not persist redundant `depth` or `root_session_id` values. Consumers derive ancestry from `parent_session_id`; current UI consumers expose only subsessions whose direct parent has `session_role = 'primary'`.
- Repeated synchronization deterministically reconciles previously imported Codex child records without duplicating Sessions, deleting source JSONL, or losing stable source identity.
- Workstream Claude maintenance retrieval excludes every subsession from candidate counts, evidence materialization, manifests, and Suggestions; eligible parents do not inherit child content.
- Global Search and Session-derived Dashboard, source, tool, workspace, Project, and activity statistics consume primary Sessions only.
- `workspaces.git_root` remains the filesystem root of the Git repository containing the workspace path; it does not describe branch ancestry or a default branch.
- Nullable `sessions.git_branch` is the sole persisted branch value for an individual Session. Claude supplies the last non-empty top-level `gitBranch`; Codex supplies `payload.git.branch` from the primary first `session_meta` identity record.
- Branch values are trimmed, empty values become `NULL`, and missing history is not inferred from the repository's current checkout, workspace state, `main`, or `master`.
- `workspaces.git_branch` is removed from the canonical and upgraded runtime schema and from Project, retrieval, Task Runner, manifest, and resource payload consumers.
- Existing Sessions are reprocessed from authoritative source JSONL for branch backfill. The ambiguous workspace branch is never copied into a Session, and unavailable source history leaves the value `NULL`.
- Branch normalization and migration do not change a project working tree, current branch, Git configuration, workspace identity, user-curated workspace links, or external source state.
- The contract is documented in the owning Product Model and Project Architecture surfaces so later inventory and detail Features do not depend on source-specific assumptions.

## Scope Boundary

- In:
  - source-neutral primary, subsession, and unresolved-parent classification
  - Claude directory-based and Codex metadata-based parent relation production
  - stable parent identity and source provenance across rescans
  - `session_role`, `parent_external_id`, and `parent_session_id` Session hierarchy value shapes
  - self-reference indexing and safe same-source, non-self, non-cyclic resolution
  - reconciliation of already indexed Codex child Sessions
  - Workstream Claude maintenance retrieval, evidence, manifest, and Suggestion exclusion
  - global Search and Session-derived statistics exclusion for all subsessions
  - read-only Claude and Codex branch extraction into `sessions.git_branch`
  - preservation of `workspaces.git_root` as repository-root identity
  - physical removal of `workspaces.git_branch` and every producer or consumer contract that exposes it
  - source-backed Session branch reprocessing without workspace-value fallback
  - durable product and architecture contract alignment
- Out:
  - Session pagination, list-row layout, dropdown presentation, or view switching
  - Session and subsession conversation-detail presentation
  - deletion or mutation of Claude, Codex, project, or Git source data
  - content-based or AI-generated parent inference
  - a recursive user-facing hierarchy for arbitrary child depth

## Surface Lanes

- Contract lane:
  - path roots: `docs/policies/project/`, `docs/policies/operations/`
  - dependencies: approved parent PRD
  - expected evidence: explicit source ownership, classification, unresolved-parent, branch, reconciliation, and Workstream maintenance consumer rules
  - evaluator ownership: `contract`
- Ingestion and identity lane:
  - path roots: `src/localbrain/ingest/`, `src/localbrain/schema.sql`, `src/localbrain/db.py`, `src/localbrain/subagents.py`
  - dependencies: contract lane
  - expected evidence: synthetic Claude and Codex fixtures covering parent, child, nested metadata, unresolved parent, repeated scan, and branch extraction
  - evaluator ownership: `contract`, `functional`
- Consumer exclusion lane:
  - path roots: `src/localbrain/queries.py`, `src/localbrain/retrieval.py`, `src/localbrain/runner.py`, `src/localbrain/workstreams.py`
  - dependencies: ingestion and identity lane
  - expected evidence: top-level, global Search, statistics, and Workstream maintenance consumers cannot admit subsessions or attribute child content to a parent
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- `ParsedSession` or successor normalized Session identity shape
- SQLite Session identity, parent relationship, classification, and compatible migration behavior
- `session_role`, `parent_external_id`, `parent_session_id`, self-reference deletion behavior, and direct-child consumer predicate
- Claude and Codex source adapter producer rules
- synchronization and stale-record reconciliation behavior
- `sessions.git_branch` producer, normalization, persistence, reprocessing, and consumer ownership
- `workspaces.git_root` repository-root meaning and removal of `workspaces.git_branch`
- compatible migration behavior that preserves workspace IDs and user-curated relations
- top-level Session consumer predicate
- global Search indexing and Session-derived statistics predicates
- Workstream retrieval bundle, candidate counts, evidence artifacts, context manifest, and Resource Suggestion inputs
- Product Model, Project Architecture, and Claude Task Runner ownership boundaries

## Required Evaluators

- `contract`: source authority, normalized identity, value shape, fallback, migration, producer/consumer parity, and stale-assumption checks.
- `functional`: repeated scans, parent resolution, unresolved-parent exclusion, branch extraction, Workstream retrieval exclusion, and non-mutation evidence.

## User-Visible Outcome

- This foundation Feature does not introduce a new screen. It prevents source-format differences from leaking into later Sessions UI and Workstream maintenance behavior.

## Entry And Exit

- Entry point: Claude or Codex Session synchronization and Workstream Claude maintenance candidate retrieval.
- Exit or transition behavior: normalized primary Sessions remain eligible for existing consumers; classified subsessions follow the approved child and exclusion contract.

## State Expectations

- Default: a primary Session has no parent and remains eligible for existing top-level consumers.
- Child: a valid parent relation is preserved and does not create a second top-level Session.
- Unresolved parent: source evidence is retained locally, but the child remains non-displayable and maintenance-ineligible.
- Nested child: source-backed parentage may be preserved, but current user-facing consumers admit only a subsession whose direct parent is primary.
- Malformed or partial metadata: ingestion preserves previously valid records and does not guess parentage.
- Re-scan: unchanged source identity produces the same classification and relation without duplication.
- Branch unavailable: `sessions.git_branch` remains `NULL` rather than inheriting a workspace value or querying the current checkout.
- Success: all declared producers, Search and statistics consumers, and Workstream maintenance consumers apply the same source-neutral contract.

## Dependencies

- Parent PRD `prd-0002` must remain `approved`.
- No product Feature in this PRD may enter build until this Feature is `passed` when it depends on subsession identity or branch normalization.

## Likely Affected Surfaces

- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `src/localbrain/ingest/scanner.py`
- `src/localbrain/subagents.py`
- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/queries.py`
- `src/localbrain/retrieval.py`
- `src/localbrain/runner.py`
- `src/localbrain/workstreams.py`
- `src/localbrain/templates/session.html`
- `src/localbrain/templates/sessions.html`
- `tests/test_parsers.py`
- `tests/test_ingest_policy.py`
- retrieval, runner, query, migration, and reconciliation tests
- `docs/policies/project/product.md`
- `docs/policies/project/architecture.md`
- `docs/policies/operations/claude-task-runner.md`

## Pass Or Fail Checks

- Pass if synthetic Claude and Codex primary and child fixtures produce the same source-neutral relationship semantics.
- Pass if fresh and upgraded databases provide `session_role`, `parent_external_id`, and indexed `parent_session_id`, with `parent_session_id` referencing `sessions(id)` using `ON DELETE SET NULL`.
- Pass if top-level selection uses `session_role = 'primary'` rather than treating every `NULL parent_session_id` row as top-level.
- Pass if deleting or losing a parent leaves the child classified as a hidden subsession and if self-parent, cross-source, or cyclic source metadata never becomes a displayable hierarchy.
- Pass if no persisted depth or root field can drift from the self-referential relation and direct-child consumers exclude descendants whose parent is itself a subsession.
- Pass if Codex child metadata is not imported as an ordinary top-level Session after synchronization.
- Pass if an unresolved-parent child is not returned by any user-facing Session lookup intended for later inventory or detail consumption.
- Pass if repeated scans reconcile prior Codex child rows without duplication or source deletion.
- Pass if Workstream Claude maintenance manifests, counts, evidence, and Suggestions contain no subsessions and no implicitly merged child content.
- Pass if no subsession from either source produces a global Search result or contributes to Session, event, tool, source, workspace, Project, recent-activity, daily-activity, or context-switch statistics.
- Pass if Claude's last non-empty top-level `gitBranch` and Codex's primary first `session_meta.payload.git.branch` normalize to the matching `sessions.git_branch` value.
- Pass if empty or unavailable source branch metadata produces `NULL` without current-checkout inference or a workspace fallback.
- Pass if `workspaces.git_root` continues to identify the containing repository root while `workspaces.git_branch` is absent from fresh and upgraded databases and from every Project, retrieval, Task Runner, manifest, and resource payload contract.
- Pass if existing Sessions can be reprocessed from authoritative JSONL without copying the prior workspace branch, changing workspace IDs, or breaking user-curated workspace relations.
- Pass if verification proves the source repository and Git state are untouched.
- Pass if producer and consumer fixtures make the parent and classification contract explicit enough for Features 0017 and 0018 to proceed without guessing.
- Fail if classification relies on content heuristics or source-specific UI behavior.
- Fail if a child can silently become top-level because its parent is missing.

## Regression Surfaces

- ordinary Claude and Codex Session identity and deduplication
- maintenance Session exclusion
- source file scan status and malformed JSONL tolerance
- existing Session, workspace, Workstream Resource, and retrieval identities
- Git-backed Project recognition through `workspaces.git_root`
- Workstream Claude Run candidate generation and accepted or rejected Suggestion preservation
- local-only privacy and no-external-write boundaries

## Feature Review Questions

- User-facing terminology does not block the data relation. Human review fixed current presentation at one direct-child depth; deeper hierarchy remains source-backed and non-displayable.

## Harness Trace

- Active spec doc: [spec-0015-session-subsession-source-contract](../spec/spec-0015-session-subsession-source-contract.md)
- Active run: [run-20260717-15-session-subsession-source-contract](../run/run-20260717-15-session-subsession-source-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [eval-0015-functional-session-subsession-source](../evaluation/eval-0015-functional-session-subsession-source.md)
- Latest fix note: not created

## Continuity Notes

- `2026-07-17`: initial draft separated the source and consumer invariant from downstream Sessions navigation, inventory, and detail presentation.
- `2026-07-17`: human review assigned branch ownership to `sessions.git_branch`, retained repository identity in `workspaces.git_root`, and required physical removal of `workspaces.git_branch` and all of its consumers without ambiguous backfill.
- `2026-07-17`: human review fixed one-depth presentation and the hierarchy contract now uses `session_role`, source parent identity, and a nullable self-reference without redundant stored depth.
- `2026-07-17`: human review excluded all subsessions from global Search and Session-derived statistics, resolving the final consumer-policy ambiguity for this Feature.
- `2026-07-17`: human owner requested sequential execution of Features 0015 through 0018; this Feature entered `in-loop` as the first run.
- `2026-07-17`: Contract and Functional evaluation passed; downstream Session navigation, inventory, and detail Features may now execute against the normalized hierarchy contract.
