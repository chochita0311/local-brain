# SPEC-0145: Drive Sync Contract

## Metadata

- ID: `spec-0145`
- Status: `approved`
- Run: [run-20261028-209](../run/run-20261028-209-drive-sync-contract.md)
- Attempt: 1
- Parent Feature: [feat-0145](../feature/feat-0145-drive-sync-contract.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract, functional
- Created: `2026-10-28`
- Updated: `2026-10-28`

## Implementation Goal And Acceptance Mapping

Persist source authority, safe manifests, file limits and wall-clock schedule as a shared contract.

URL-only roots; 100,000,000-byte inclusive cap; seven wall-clock intervals; private durable state; stop preserves copies; no incomplete scan deletion.

## State And Data Contract

Use the shared [Drive sync contract](../../policies/project/google-drive-sync.md). Private SQLite owns connection selection, manifests and per-job observations; Google CLI owns OAuth credentials and refresh. A connection/root change has a new namespace. Received copies never enter indexing implicitly. Mutations are serialized against settings changes and cancellation is checked between operations. No local failure, access loss, partial listing, oversize rejection or stopped selection authorizes deletion. Persist checkpoints per verified item; do not claim folder-wide atomicity.

## Surface Lanes And Evaluation Focus

policy.py, store.py. Dependency order: contract, producer implementation, consumers, evaluator and regression. Primary agent performs logical roles sequentially. Validate with the focused Drive suite, existing Settings/Docs/boundary tests and rendered Settings at desktop/320px where applicable. Verify outgoing local authority, incoming remote authority and actual-operation errors independently.

## Open Blockers And Evidence Limits

No remaining blocker to this bounded contract. Provider/live Google, native UI-host and public OAuth validation remain owned by the parent integration/release gates, not implied by this result.

## Scope Exclusions

All exclusions and regression surfaces in the parent Feature remain binding.
