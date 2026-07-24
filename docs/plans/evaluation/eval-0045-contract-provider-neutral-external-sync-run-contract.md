# EVAL-0045: Provider-Neutral External Sync Run Contract — Contract

## Metadata

- ID: `eval-0045-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `FAIL`
- Run ID: `run-20260723-50`
- Attempt: `1`
- Feature: [feat-0045-provider-neutral-external-sync-run-contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md)
- Spec: [spec-0045-provider-neutral-external-sync-run-contract](../spec/spec-0045-provider-neutral-external-sync-run-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: persistence → manifest and authorization → runner parity and recovery → durable docs and generated schema
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Evidence Invalidation

- This Attempt 1 failure is historical execution evidence.
- The targeted repair is recorded in [FIX-0045](../fix/fix-0045-metadata-coverage-enforcement.md), and [Contract Attempt 2](./eval-0045-contract-provider-neutral-external-sync-run-contract-attempt-2.md) is the current evaluator result.

## Scope

- Evaluated generic Run and extension ownership, manifest and result schemas, FEAT-0044 reauthorization, provider-fact ownership, Claude/Codex isolation, lifecycle, native maintenance linkage, generated schema, and downstream FEAT-0046 readiness.

## Checks And Evidence

- The common `maintenance_runs` ledger and one-to-one `external_sync_runs` projection were derived atomically from one validated manifest, and incompatible envelope or artifact state failed closed.
- Every logical request was reauthorized through FEAT-0044 before execution; the model received only host-validated evidence and had no broad MCP, Gateway, network, or write-tool path.
- Content facts required selected content coverage and an approved content operation, hashes were host-computed, and raw provider error messages were replaced with bounded application text.
- Claude and Codex shared the same logical manifest and model-result schema while retaining runner-specific process adapters and native maintenance Session synchronization.
- Schema owners, generated presentation, cleanup audit, privacy rules, and the FEAT-0046 handoff remained aligned.

## Findings

### Blocking: metadata facts did not require metadata coverage

- Classification: `implementation bug`
- `validate_provider_result` enforced the field allowlist when present but did not reject a non-empty metadata object when the target selected content-only coverage and therefore had an empty metadata allowlist.
- This contradicted the approved manifest boundary because a trusted executor response could retain source metadata that the caller had not selected.
- Required fix: reject non-empty metadata unless `metadata` is in the target coverage and add focused regression evidence.

## Regression Notes

- No spec or planning gap was found. The defect was bounded to provider-result validation and did not change the approved Feature boundary.

## Route

- Next action: `fix`, then repeat Contract and Functional evaluation.
