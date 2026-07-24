# FEAT-0045: Provider-Neutral External Sync Run Contract

## Metadata

- ID: `feat-0045`
- Status: `passed`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal

- Extend the existing maintenance execution model with one Claude/Codex-neutral external synchronization Run contract whose inputs, source-backed results, usage, exclusions, and partial-failure behavior do not depend on the selected runner.

## Acceptance Contract

- External synchronization uses a bounded maintenance task type such as `external_source_sync` and records runner, source kind, Source Instance, service, requested scope, selected target count, and read-only policy identity.
- `maintenance_runs` remains the source-neutral parent execution ledger. An external synchronization Run owns exactly one `external_sync_runs` extension row; non-external maintenance Runs own none.
- The extension row stores only the bounded query envelope: parent Run identity, Source Instance, source kind, service, requested scope kind, selected target count, input-manifest version, and read-policy version.
- One versioned input manifest represents Item, Space, Thread, Workstream, or all-known scope through selected target locators, requested coverage, known remote versions or timestamps, content hashes, field allowlists, and call budgets.
- The manifest excludes unrelated Session bodies, Local Context bodies, Workstream prose, credentials, and unselected external resources.
- Claude and Codex accept the same logical manifest and return one versioned structured-result shape.
- Per-target outcomes distinguish at least `resolved`, `unchanged`, `changed`, `unavailable`, `not_found`, and `error`, with source-backed identity, metadata, eligible content, version/timestamp evidence, content hash, and bounded error provenance when applicable.
- Model-authored summaries or explanations are not accepted as remote source facts.
- The Run can end completed, partially successful, failed, cancelled, or interrupted without clearing prior Item content or local organization.
- Tool dispatch is constrained by the passed FEAT-0044 read-only allowlist and records bounded tool-call accounting.
- The native linked Session remains `maintenance`, `primary`, and `metadata_only`; maintenance content and artifacts remain outside ordinary Search, workflow statistics, candidate evidence, and checkpoint Session resources.
- Direct real-model Usage Records remain eligible for the existing token and estimated-cost contract without counting the Run as a primary work Session.
- Existing non-external maintenance task behavior remains compatible.

## Scope Boundary

- In:
  - external synchronization maintenance task vocabulary
  - one-to-one source-neutral `external_sync_runs` execution envelope
  - runner-neutral manifest and structured-result versions
  - Claude and Codex execution parity
  - Source Instance and read-only policy binding
  - per-target result and partial-failure semantics
  - Run artifacts, call accounting, cancellation, interruption, and terminal reconciliation
  - native Maintenance Session linkage and Usage Record eligibility
  - privacy-safe bounded errors and provenance
- Out:
  - selecting provider tools outside FEAT-0044 policy
  - Atlassian Item tables, URL aliases, evidence, freshness, or FTS owned by FEAT-0046
  - applying structured results to Atlassian Items
  - visible refresh preview and progress owned by FEAT-0049
  - summaries, classification, Topic or Tag generation, and Workstream mutations
  - external writes of any kind

## Surface Lanes

- Run contract lane:
  - path roots: `src/localbrain/runner.py`, `src/localbrain/schema.sql`, `src/localbrain/db.py`, maintenance data-model and operations documentation
  - dependencies: FEAT-0044 read-only capability contract
  - expected evidence: task vocabulary, manifest and result schemas, lifecycle, partial-failure semantics, and exact ledger ownership
  - evaluator ownership: `contract`
- Runner parity lane:
  - path roots: runner adapters, Claude and Codex invocation or ingestion boundaries, and private runtime artifact handling
  - dependencies: Run contract lane
  - expected evidence: equivalent Claude/Codex logical input/output, native maintenance classification, and usage retention
  - evaluator ownership: `contract`, `functional`
- Recovery lane:
  - path roots: Run reconciliation, cancellation, interruption, result validation, and synthetic runtime tests
  - dependencies: Run contract and runner parity lanes
  - expected evidence: no-change, partial success, failure, cancellation, invalid result, restart, and idempotent recovery behavior
  - evaluator ownership: `functional`

## Contract Surfaces

- `maintenance_runs` task, runner, lifecycle, Workstream association, MCP accounting, summary, error, and artifact fields.
- `maintenance_runs` common lifecycle ownership versus the one-to-one `external_sync_runs` query envelope.
- Versioned external synchronization manifest.
- Versioned per-target structured result.
- Claude and Codex maintenance markers and native Session linkage.
- MCP call accounting and budget evidence.
- Run terminal and restart-reconciliation semantics.
- Usage Record inclusion versus work-content exclusion.

## Required Evaluators

- `contract`: ledger ownership, manifest/result schemas, source-backed field requirements, runner parity, policy binding, Session/Usage boundaries, and downstream readiness.
- `functional`: completed, no-change, partial, failed, invalid-result, cancelled, interrupted, and restart paths for both runner kinds with synthetic providers.

## Entry And Exit

- Entry point: an approved caller supplies a validated source scope and selected targets governed by one FEAT-0044 read-only policy.
- Exit or transition behavior: the Run retains a validated structured result and per-target outcomes or a bounded terminal failure without mutating Workstream organization or deleting previous source state.

## State Expectations

- Prepared: manifest and read-only policy validate before process launch.
- Prepared persistence: the common Run, external-sync envelope, and validated manifest snapshot are created from one validated input in one transaction.
- Running: progress and bounded call evidence accrue without exposing content to ordinary Session consumers.
- Partial: successful and failed targets remain separately attributable.
- Error: invalid output or provider failure preserves artifacts and rejects unvalidated source facts.
- Cancelled or interrupted: observed usage and evidence remain; no automatic process resume occurs.
- Success: one validated result can be consumed idempotently by FEAT-0046 and later product Features.

## Dependencies

- FEAT-0044 must be `passed`.
- Existing Maintenance Session and Usage contracts from FEAT-0036 and FEAT-0037 remain implementation truth and regression requirements.

## Likely Affected Surfaces

- `src/localbrain/runner.py`
- `src/localbrain/config.py`
- `src/localbrain/main.py` for internal Run composition boundaries only
- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- `src/localbrain/ingest/common.py`
- `src/localbrain/ingest/claude.py`
- `src/localbrain/ingest/codex.py`
- `tests/test_runner.py`
- parser, Session-contract, Usage, schema-upgrade, and recovery tests
- `docs/policies/project/data-model/maintenance-execution.md`
- `docs/policies/operations/claude-task-runner.md` or a source-neutral replacement owner

## Pass Or Fail Checks

- Pass if one logical manifest and result contract works through synthetic Claude and Codex runner paths.
- Pass if a non-external maintenance Run receives no external-sync row and every external synchronization Run receives exactly one row linked to its common Run.
- Pass if list/filter queries use the bounded envelope while detailed target selection, freshness evidence, coverage, hashes, and field allowlists remain owned by the versioned manifest.
- Pass if the envelope is derived from the same validated manifest in one transaction and a mismatch fails closed.
- Pass if the Run cannot start without a current read-only policy and valid target scope.
- Pass if every target outcome and source fact is schema-validated and traceable to an approved provider result.
- Pass if partial, invalid, cancelled, interrupted, and restart paths preserve prior state and directly observed Usage Records.
- Pass if maintenance content remains absent from ordinary Search, statistics, retrieval candidates, and checkpoint Session resources.
- Pass if existing non-external maintenance tasks retain their behavior.
- Fail on runner-specific source identity, unvalidated prose persistence, write-tool reachability, usage loss or duplication, work-content leakage, or destructive partial failure.

## Regression Surfaces

- Existing Claude maintenance tasks, manifests, console artifacts, Suggestions, and Workstream associations.
- FEAT-0036 native Maintenance Session classification and FEAT-0037 Workstream FK behavior.
- Session ingestion, Usage dashboard totals, and primary-work denominators.
- Runner cancellation, restart reconciliation, and privacy-safe artifact storage.

## Harness Trace

- Active spec doc: [spec-0045-provider-neutral-external-sync-run-contract](../spec/spec-0045-provider-neutral-external-sync-run-contract.md)
- Active run: [run-20260723-50-provider-neutral-external-sync-run-contract](../run/run-20260723-50-provider-neutral-external-sync-run-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [Contract Attempt 2 — PASS](../evaluation/eval-0045-contract-provider-neutral-external-sync-run-contract-attempt-2.md), [Functional — PASS](../evaluation/eval-0045-functional-provider-neutral-external-sync-run-contract.md)
- Latest fix note: [Metadata Coverage Enforcement](../fix/fix-0045-metadata-coverage-enforcement.md)

## Open Review Decisions

- None. The owner confirmed the one-to-one source-neutral extension boundary on `2026-07-23`.

## Confirmed Persistence Boundary

- `maintenance_runs` remains the generic ledger for every maintenance execution and owns runner, process lifecycle, Workstream association, Usage linkage, MCP accounting, artifact paths, summary, and bounded errors.
- `external_sync_runs` is a source-neutral one-to-one extension used only when `task_type = external_source_sync`. Its projected fields are:
  - `maintenance_run_id`
  - `source_instance_id`
  - `source_kind`
  - `service`
  - `requested_scope_kind`
  - `selected_target_count`
  - `manifest_schema_version`
  - `read_policy_version`
- Detailed selectors and source-specific inputs remain in the versioned manifest:
  - Item, Space, Thread, Workstream, or all-known target locators
  - requested content coverage
  - known remote version or updated time
  - content hash
  - field allowlist
  - call budget and other schema-versioned source parameters
- The extension row is a bounded persisted query projection, not an independent authoring surface. Preparation derives it from the same validated manifest and inserts both rows atomically.
- Provider-specific schema columns do not enter `maintenance_runs` or `external_sync_runs`. Generic `source_kind` and `service` discriminators identify Atlassian, Slack, Email, and later sources, while source-specific identity and payload contracts remain in their Source Item hierarchy, versioned manifest, and validated results.
- Exact Item- or Space-to-Run relations remain downstream of the stable external Item identity contract. FEAT-0045 does not invent polymorphic URL or remote-ID columns before FEAT-0046.

## Continuity Notes

- `2026-07-23`: initial draft separated runner-neutral execution and result validation from provider capability policy and from Atlassian Item persistence.
- `2026-07-23`: the owner confirmed a generic `maintenance_runs` parent plus one-to-one source-neutral `external_sync_runs` envelope and a versioned detailed manifest, preserving future Atlassian, Slack, and Email expansion without adding provider-specific columns to the common Run ledger.
- `2026-07-23`: the human owner approved the complete Feature boundary and requested execution; status advanced through approval to `in-loop` under RUN-20260723-50.
- `2026-07-23`: Contract Attempt 1 found one bounded metadata-coverage implementation bug; FIX-0045 closed it without changing the approved boundary.
- `2026-07-23`: Contract Attempt 2 and Functional evaluation passed with complete foundation evidence; status advanced to `passed`, while FEAT-0046 remains draft pending separate human approval.
