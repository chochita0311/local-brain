# SPEC-0045: Provider-Neutral External Sync Run Contract

## Metadata

- ID: `spec-0045`
- Status: `approved`
- Run ID: `run-20260723-50`
- Attempt: `1`
- Parent Feature: [feat-0045-provider-neutral-external-sync-run-contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Surface Lanes: persistence → manifest and authorization → runner parity and recovery → durable docs and generated schema
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Source Set

- Human request and approval: use a source-neutral maintenance Run for Claude or Codex synchronization, keep source and scope outside the generic parent ledger, and execute FEAT-0045 now.
- Parent Feature and PRD: approved FEAT-0045 and PRD-0007.
- Dependency truth: passed FEAT-0044 Source Instance, capability-observation, logical-operation authorization, and read-only dispatch policy.
- Implementation truth: current `maintenance_runs`, Claude Task Runner, native Claude/Codex Session parsers, Usage Records, cancellation, and restart reconciliation.
- Current CLI evidence checked on `2026-07-23`: Claude supports schema-bound stream output and tool restriction; Codex `exec` supports JSONL events, output schemas, native session persistence, and read-only sandboxing.
- Governing contracts: Architecture, Privacy And Data Handling, Maintenance Execution, Source Registry And Scans, schema presentation, and execution-loop governance.

## Implementation Goal

- Add one source-neutral external synchronization extension and runtime contract that atomically records a validated manifest, authorizes every external read through FEAT-0044, runs the same logical input and output through Claude or Codex, retains only host-validated source facts, and preserves existing maintenance behavior.

## In-Scope Behavior

1. Add `external_sync_runs` as a one-to-one extension of `maintenance_runs`:
   - parent Run primary key with cascade deletion
   - Source Instance foreign key with `ON DELETE SET NULL` for retained execution history
   - source kind, service, requested scope kind, selected target count, manifest schema version, read-policy version, and creation time
   - indexes for Source Instance and scope-oriented Run lookup
2. Keep `maintenance_runs` generic:
   - `task_type = external_source_sync`
   - selected runner remains `claude` or `codex`
   - common process lifecycle, Workstream association, usage linkage, MCP accounting, artifacts, summary, and bounded errors remain parent-owned
   - non-external maintenance Runs create no extension row
3. Define and validate `localbrain.external-sync-manifest.v1`:
   - one enabled Source Instance and its source kind/service
   - one requested scope kind from Item, Space, Thread, Workstream, or all-known
   - bounded selected targets with typed locators
   - requested metadata/content/hierarchy coverage
   - optional known remote version, updated time, and content hash
   - one or more logical FEAT-0044 requests with field selection and a total call budget
   - no credentials or unrelated local Session, Local Context, or Workstream bodies
4. Derive the `external_sync_runs` projection from that validated manifest and insert the parent plus extension in one database transaction. Preparation failure removes newly created private artifacts.
5. Pre-authorize every logical request with `authorize_external_read`. No caller- or model-supplied provider tool name is accepted.
6. Execute approved descriptors through an injected host-side read executor:
   - no external-sync Run starts without this enforceable executor boundary
   - the selected model process receives bounded local evidence only
   - broad MCP/Gateway tools are unavailable to that model process
   - call accounting stores request/tool identity and outcome but not arguments or returned private content
7. Define `localbrain.external-sync-result.v1`:
   - host-owned source, scope, policy, and per-target request facts
   - request and target outcomes from `resolved`, `unchanged`, `changed`, `unavailable`, `not_found`, and `error`
   - bounded source identity, metadata, eligible content, remote version/update evidence, host-computed content hash, and safe error provenance
   - a model-authored summary is optional presentation metadata and cannot replace or alter source facts
8. Derive terminal state deterministically:
   - all selected targets successful: `completed`
   - mixed successful and unsuccessful targets: `partial`
   - no successful target or invalid runner output: `failed`
   - explicit stop: `cancelled`
   - restart/shutdown while active: `interrupted`
9. Add Claude and Codex adapters:
   - same prompt markers, logical manifest, evidence, and summary schema
   - persistent native model sessions
   - no-tool Claude invocation and run-root-only, network-disabled, user-config-isolated Codex invocation
   - runner-specific stream parsing hidden behind the common result contract
10. Synchronize the selected native Session source after terminal state so its Session remains `maintenance`, `primary`, and `metadata_only`; directly observed Usage Records remain eligible.
11. Update maintenance/data-model/operations owners, compatible startup behavior, deterministic schema presentation, and synthetic tests.

## Out-Of-Scope Behavior

- A live company Source Instance registration, live ticket or Page retrieval, credentials, private domains, or captured provider payloads.
- A general-purpose MCP client or a provider tool selected outside FEAT-0044.
- Allowing Claude or Codex to see a broad Gateway and relying on prompt wording for read-only behavior.
- Atlassian Item identity, URL aliases, content application, freshness rows, or FTS owned by FEAT-0046.
- URL evidence extraction, registration UI, preview/progress UI, browse/search, summaries, Topics, Tags, and Workstream relationship mutation.
- External writes, background synchronization, automatic retry, or automatic destructive cleanup.
- Refactoring the existing non-external Claude maintenance task's current MCP gap-fill policy.

## Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- new source-neutral external-sync contract module under `src/localbrain/`
- `src/localbrain/runner.py`
- `src/localbrain/ingest/scanner.py`
- focused external-sync, runner, parser, schema-upgrade, usage, and recovery tests
- `docs/policies/project/data-model.md`
- `docs/policies/project/data-model/maintenance-execution.md`
- source-neutral maintenance runner operations owner
- schema-presentation and schema-decision generated artifacts

## Surface Lanes

- Persistence:
  - path roots: schema, compatible startup, schema presentation, maintenance data model
  - dependency order: first
  - implementation responsibility: exact one-to-one envelope, FK lifecycle, indexes, atomic projection
  - validation evidence: fresh and upgraded SQLite, cascade/SET NULL behavior, non-external absence, generated parity
- Manifest and authorization:
  - path roots: external-sync contract and FEAT-0044 integration
  - dependency order: after persistence
  - implementation responsibility: bounded schema validation, projection derivation, logical-operation-only authorization, fact validation
  - validation evidence: accepted manifests, mismatch and policy failure, field/call bounds, source-fact provenance
- Runner parity and recovery:
  - path roots: runner adapters, scanner entry points, lifecycle and recovery
  - dependency order: after manifest and authorization
  - implementation responsibility: Claude/Codex commands and streams, executor boundary, result assembly, partial state, cancellation/interruption, native session sync
  - validation evidence: synthetic model/provider paths for both runners and regression coverage for existing Claude tasks
- Durable docs and generated schema:
  - path roots: owner docs, schema presentation, decision ledger
  - dependency order: after behavior stabilizes
  - implementation responsibility: one current contract and deterministic generated consumers
  - validation evidence: data-model, audit, generated-schema, link, privacy, Mermaid, and diff checks

## State And Interaction Contract

- Prepared: source, capability observation, policy, target shape, and every request validate before execution.
- Queued: parent and extension rows plus private artifacts exist consistently.
- Running: approved host reads and model summary work accrue bounded accounting.
- Completed: every target has a successful source-backed outcome and result validation passes.
- Partial: at least one target succeeded and at least one did not.
- Failed: all targets failed, the safe executor is missing, launch fails, or model output is invalid; no prior external Item state is mutated.
- Cancelled: queued/running work is stopped and observed evidence remains.
- Interrupted: startup or shutdown reconciliation records terminal interruption and does not auto-resume.

## Data And Contract Assumptions

- `external_sync_runs` is a query projection, never a second editable source for scope or policy.
- Source Instance provider/service identity and capability state come from FEAT-0044; the manifest cannot override them.
- A host executor is trusted only to invoke the supplied immutable `ToolDispatch` and return the documented bounded evidence shape. Its concrete MCP/Gateway transport remains externally configured.
- Provider evidence is private runtime data. Tracked tests and docs use synthetic hosts, URLs, keys, text, and identities.
- Content hashes are computed by LocalBrain from canonical returned content rather than accepted from a model.
- The model can explain validated outcomes but cannot create identity, metadata, content, version, timestamp, hash, or provider errors.
- Exact Atlassian Item relation and content-application idempotency remain FEAT-0046.

## Contract Surfaces

- Producer expectations:
  - callers supply one runner, Source Instance, scope, bounded target set, logical operation requests, and call budget
  - host executors accept only FEAT-0044 `ToolDispatch` values
  - model adapters return only the common schema-bound presentation result
- Consumer expectations:
  - FEAT-0046 consumes validated per-target source results and never raw model prose
  - UI Features query the bounded extension envelope without parsing detailed manifests
- Generated artifacts:
  - schema presentation and schema decision ledgers are regenerated from current DDL and owner docs
- Source-of-truth owner:
  - DDL in `schema.sql`; compatible startup in `db.py`; manifest/result validation in the external-sync module; process lifecycle in `runner.py`; semantics in Maintenance Execution and runner operations docs
- Stale-assumption check:
  - scan current runner, both native parsers, Usage, retrieval exclusions, checkpoint references, schema counts/ERDs, schema presentation, and all non-external maintenance tests

## Required Evaluators

- Contract:
  - parent/extension ownership, manifest and result versions, FEAT-0044 enforcement, source-fact provenance, Claude/Codex parity, Session/Usage boundaries, and downstream readiness
- Design:
  - not applicable
- Functional:
  - preparation, authorization, completed/no-change/partial/all-failed/invalid-output/cancelled/interrupted behavior for both runner kinds with synthetic executors
- UX heuristic:
  - not applicable

## Acceptance Mapping

- Generic parent plus one-to-one query envelope → DDL, atomic preparation API, compatible startup, schema and lifecycle tests.
- Detailed versioned input → exact manifest validation and private artifact tests.
- Read-only enforcement → FEAT-0044 authorization for every request plus injected immutable-dispatch executor; model commands expose no external tools.
- One Claude/Codex contract → shared manifest/result schemas, adapter commands, stream parsing, and synthetic parity tests.
- Source-backed results → host validation/assembly and model-field isolation tests.
- Partial/recovery semantics → deterministic status derivation, cancellation and restart tests.
- Maintenance exclusion and Usage inclusion → selected native scanner sync plus parser, retrieval, checkpoint, and usage regressions.
- Downstream readiness → validated result retained on `maintenance_runs` without applying FEAT-0046 data.

## Evaluation Focus

- Confirm a manifest, model response, or executor cannot invent a provider target or bypass FEAT-0044.
- Confirm model commands cannot reach broad Gateway or external write tools.
- Confirm no arguments or private provider content enters the query envelope or tool-call accounting.
- Confirm every source fact in the final result is copied from host-validated evidence and hashes are locally computed.
- Confirm exact terminal status and artifact retention for mixed outcomes, invalid output, cancellation, and restart.
- Confirm native Claude and Codex maintenance Session/Usage behavior and all existing Claude maintenance behavior.
- Confirm schema owners, counts, ERDs, generated packages, and decision ledgers remain current.

## Open Blockers

- None. The human owner approved the complete Feature boundary and the host-executor enforcement design stays within the approved read-only contract.

## Continuity Notes

- `2026-07-23`: Spec approved for RUN-20260723-50 after the owner approved FEAT-0045 and requested execution.
