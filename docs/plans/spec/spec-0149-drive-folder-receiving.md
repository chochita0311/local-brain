# SPEC-0149: Drive Folder Receiving

## Metadata

- ID: `spec-0149`
- Status: `approved`
- Run: [run-20261028-213](../run/run-20261028-213-drive-folder-receiving.md)
- Attempt: 1
- Parent Feature: [feat-0149](../feature/feat-0149-drive-folder-receiving.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`
- Updated: `2026-10-28`

## Implementation Goal And Acceptance Mapping

Keep checked publisher folders synchronized into private local copies with independent schedules.

Root folder checkboxes excluding own publisher; whole-folder receive; per-folder 24h default; remote authority including confirmed trash/deletion; no deletion from inaccessible/partial listings; bounded atomic download; deselect retains copies.

## State And Data Contract

Use the shared [Drive sync contract](../../policies/project/google-drive-sync.md). Private SQLite owns connection selection, manifests and per-job observations; Google CLI owns OAuth credentials and refresh. A connection/root change has a new namespace. Received copies never enter indexing implicitly. Mutations are serialized against settings changes and cancellation is checked between operations. No local failure, access loss, partial listing, oversize rejection or stopped selection authorizes deletion. Persist checkpoints per verified item; do not claim folder-wide atomicity.

## Surface Lanes And Evaluation Focus

engine.py, service.py, static/google-drive.js. Dependency order: contract, producer implementation, consumers, evaluator and regression. Primary agent performs logical roles sequentially. Validate with the focused Drive suite, existing Settings/Docs/boundary tests and rendered Settings at desktop/320px where applicable. Verify outgoing local authority, incoming remote authority and actual-operation errors independently.

## Open Blockers And Evidence Limits

The owner-approved gcloud/full-Drive revision supersedes the former app-owned Desktop Client, readonly+drive.file and Keychain prerequisites. The current producer contract is SPEC-0146 and Run215. Live two-account My Drive/Shared Drive operations and installed-recipient/native UI-host behavior remain unverified; synthetic tests or a wheel build do not establish those gates. The publishing/receiving contract itself is unchanged.

## Scope Exclusions

All exclusions and regression surfaces in the parent Feature remain binding.
