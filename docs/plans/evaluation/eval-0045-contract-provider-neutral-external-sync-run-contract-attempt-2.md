# EVAL-0045: Provider-Neutral External Sync Run Contract — Contract Re-evaluation

## Metadata

- ID: `eval-0045-contract-attempt-2`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260723-50`
- Attempt: `2`
- Feature: [feat-0045-provider-neutral-external-sync-run-contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md)
- Spec: [spec-0045-provider-neutral-external-sync-run-contract](../spec/spec-0045-provider-neutral-external-sync-run-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: persistence → manifest and authorization → runner parity and recovery → durable docs and generated schema
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Re-evaluated the complete FEAT-0045 contract after the bounded metadata-coverage repair, including persistence ownership, source-fact authority, read-only execution, runner parity, lifecycle, maintenance exclusions, generated schema, and downstream readiness.

## Checks And Evidence

- `maintenance_runs` remains the generic lifecycle, Workstream, Usage, artifact, summary, error, and call-accounting ledger. Only `external_source_sync` preparation creates the one-to-one source-neutral `external_sync_runs` query projection.
- The private versioned manifest owns selected targets, locators, coverage, known remote evidence, field allowlists, and call budget. Preparation derives both persisted rows from that validated input under one savepoint, and artifact cleanup covers preparation failure.
- Loading exact-compares the database snapshot and private artifact, rebuilds the canonical current manifest, compares the derived projection, and reauthorizes every logical request against the current Source Instance capability and FEAT-0044 policy.
- The injected host executor receives immutable `ToolDispatch` values. Call evidence records only bounded request, target, logical-operation, tool, and outcome fields; it stores neither arguments nor returned content.
- Provider identity, selected metadata, selected eligible content, remote version or update evidence, and bounded errors come only from host-validated results. Metadata now requires metadata coverage, content requires content coverage plus an approved content operation, and LocalBrain computes the canonical content hash.
- The model accepts validated manifest and evidence solely to return a bounded summary. It cannot author or alter source identity, facts, hashes, outcomes, policy, or scope.
- Claude starts with no tools and an empty strict MCP configuration. Codex starts with isolated user configuration, disabled network and web search, no inherited shell environment, and read access restricted to the Run root. Both consume the same logical contract and preserve native session persistence.
- Completed, partial, failed, cancelled, and interrupted states preserve artifacts and observed call evidence without applying or clearing downstream Item state. Selected native Claude or Codex sessions are synchronized and retain the maintenance/primary/metadata-only contract.
- The durable owner documents and generated schema describe 23 ordinary tables, one FTS5 object, 23 physical foreign keys, 22 explicit indexes, and eight subject owners consistently.

## Evidence

- Environments checked: source inspection, fresh in-memory SQLite, compatible file-backed startup, synthetic Gateway dispatch and provider results, synthetic Claude and Codex processes, lifecycle recovery, deterministic generated schema, and repository owner documentation.
- Command option syntax was checked against the installed Claude and Codex CLIs without starting a model run.

## Evidence Gaps

- None for FEAT-0045's approved foundation boundary.
- No company content was retrieved and no paid model invocation was made. A concrete MCP/Gateway transport and application of validated results to Atlassian Items are intentionally downstream composition work, not acceptance claims of this Feature.

## Findings

- None remaining. [FIX-0045](../fix/fix-0045-metadata-coverage-enforcement.md) closed the Attempt 1 implementation bug.

## Regression Notes

- Existing non-external Claude maintenance preparation and execution remain on their prior command and behavior. External Atlassian records, local organization, search projection, and refresh UI were not introduced.

## Route

- Next action: `pass` and run Functional evaluation.
