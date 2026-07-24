# RUN-20260723-50: Provider-Neutral External Sync Run Contract

## Metadata

- ID: `run-20260723-50`
- Status: `passed`
- Feature: [feat-0045-provider-neutral-external-sync-run-contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Active Spec: [spec-0045-provider-neutral-external-sync-run-contract](../spec/spec-0045-provider-neutral-external-sync-run-contract.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal And Selected Loop

- Establish the source-neutral external synchronization maintenance envelope, validation, read-only execution boundary, Claude/Codex parity, and recovery behavior without implementing Atlassian Item persistence.
- Route: `Orchestrator → Spec Agent → Builder → Contract Evaluator → Functional Evaluator → Fix Agent if required`.

## Surface Lanes

- Persistence:
  - path roots: schema, compatible startup, schema presentation, maintenance data model
  - dependencies: approved FEAT-0045 and SPEC-0045
  - validation evidence: fresh/upgrade schema, one-to-one ownership, FK lifecycle, atomic projection
  - evaluator ownership: `contract`, `functional`
- Manifest and authorization:
  - path roots: source-neutral external-sync module and FEAT-0044 integration
  - dependencies: persistence lane and passed FEAT-0044
  - validation evidence: bounded schemas, mismatch rejection, exact logical-operation dispatch, host-owned facts
  - evaluator ownership: `contract`, `functional`
- Runner parity and recovery:
  - path roots: runner adapters, native scanner entry points, lifecycle
  - dependencies: validated manifest and authorization
  - validation evidence: synthetic Claude/Codex complete, unchanged, partial, failed, invalid, cancelled, and interrupted paths
  - evaluator ownership: `contract`, `functional`
- Durable docs and generated schema:
  - path roots: owner docs, schema presentation, decision ledger
  - dependencies: stable implementation
  - validation evidence: counts, relationships, generated parity, privacy, Mermaid, and diff checks
  - evaluator ownership: `contract`

## Contract Surfaces

- Generic `maintenance_runs` ownership and one-to-one `external_sync_runs` projection.
- Versioned external-sync manifest and structured result.
- FEAT-0044 logical-operation authorization and immutable host dispatch.
- Claude and Codex command, stream, structured-output, and native Session boundaries.
- Provider evidence privacy, call accounting, Usage retention, and work-content exclusion.
- Partial, failed, cancelled, interrupted, and restart-reconciliation semantics.

## Invocation Context

- Golden sources: approved FEAT-0045, SPEC-0045, PRD-0007, passed FEAT-0044, current maintenance Session/Usage implementation.
- Relevant policies: Architecture, Privacy, Data Model, Maintenance Execution, Source Registry And Scans, execution-loop governance.
- Optional skills or tools expected: current official Codex manual was checked for non-interactive structured-output and session-persistence flags; no live external content call is required.

## Current Artifacts

- Spec: [spec-0045-provider-neutral-external-sync-run-contract](../spec/spec-0045-provider-neutral-external-sync-run-contract.md)
- Contract evaluation: [Attempt 1 — FAIL](../evaluation/eval-0045-contract-provider-neutral-external-sync-run-contract.md), [Attempt 2 — PASS](../evaluation/eval-0045-contract-provider-neutral-external-sync-run-contract-attempt-2.md)
- Functional evaluation: [Attempt 2 — PASS](../evaluation/eval-0045-functional-provider-neutral-external-sync-run-contract.md)
- Fix log: [Metadata Coverage Enforcement](../fix/fix-0045-metadata-coverage-enforcement.md)

## Evaluation Coverage

- Contract:
  - Result: `PASS` on Attempt 2
  - Evidence Coverage: `complete`
  - Environments or states checked: source inspection, fresh SQLite, compatible file startup, synthetic Gateway dispatch and provider results, synthetic Claude/Codex processes, generated schema, and owner docs
  - Unverified claims: no live company retrieval or paid model invocation was claimed; concrete transport and Item application remain downstream
  - Acceptance impact: none after FIX-0045 closed the bounded Attempt 1 implementation bug
- Functional:
  - Result: `PASS`
  - Evidence Coverage: `complete`
  - Environments or states checked: 14 focused external-sync tests, complete 204-test suite, schema and generated checks, privacy, Mermaid, compilation, and diff checks
  - Unverified claims: live provider transport, company content, Item persistence, and visible UI are outside FEAT-0045
  - Acceptance impact: none

## Current Route

- Next role: Human owner for result acceptance, then Orchestrator for FEAT-0046 boundary review if requested.
- Current blocker classification: none.
- In-run route: Attempt 1 Contract failure → bounded Fix Agent repair → Attempt 2 Contract and Functional pass.
- Post-run recommendation for human review: accept FEAT-0045; do not start FEAT-0046 without separate approval.

## Attempts

- Attempt 1:
  - status: failed Contract evaluation
  - outcome: implementation otherwise satisfied the approved boundary, but provider-result validation accepted metadata without selected metadata coverage
  - notes: classified as an `implementation bug` inside the approved manifest and authorization lane
- Attempt 2:
  - status: passed
  - outcome: targeted metadata-coverage enforcement passed Contract and Functional evaluation with complete evidence
  - notes: FIX-0045 changed only provider-result validation; 14 focused tests and the complete 204-test suite passed

## Post-Contract Regression Check

- Needed: yes.
- Result: passed.
- Notes: existing Claude maintenance tasks, parsers, Usage, retrieval/checkpoint exclusions, schema owners, generated artifacts, privacy, Mermaid, compilation, diff checks, and the complete suite passed.

## Human Review Outcome

- Decision: Feature boundary was approved and the Run requested on `2026-07-23`; the passing result is ready for human acceptance.
- Returned layer if any: none.
- Follow-up run: none.

## Continuity Notes

- `2026-07-23`: Run initialized after explicit human approval of the generic parent, source-neutral extension, versioned manifest/result, and Claude/Codex maintenance boundary.
- `2026-07-23`: Contract Attempt 1 found a bounded metadata-coverage implementation bug and routed it to FIX-0045.
- `2026-07-23`: Attempt 2 passed both required evaluators with complete evidence; no live company content or paid model run was needed for this foundation contract.
