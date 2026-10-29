# FEAT-0145: Drive Sync Contract

## Metadata

- ID: `feat-0145`
- Status: `passed`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract, functional
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Created: `2026-10-28`
- Updated: `2026-10-28`
- Authorization: Owner approved the PRD and delegated Feature creation and development through completion. Boundaries derive only from that PRD; final human acceptance and live-account evidence remain separate.

## Goal And User-Visible Outcome

Persist source authority, safe manifests, file limits and wall-clock schedule as a shared contract.

## Acceptance Contract

URL-only roots; 100,000,000-byte inclusive cap; seven wall-clock intervals; private durable state; stop preserves copies; no incomplete scan deletion.

## Scope Boundary

In: the outcome and acceptance contract above. Out: model/search/index integration, session replication, sharing-policy enforcement, aggregate quotas, permanent Drive deletion, separate recovery archive and release publication.

## Dependencies And Entry

None. Execute after prerequisite contracts pass. Initial auto execution is OFF; manual selection and enablement persist until changed. Errors preserve selected targets and existing copies.

## Surface Lanes And Contract Surfaces

Primary agent owns all logical roles sequentially. Contract/data/backend: `src/localbrain/google_drive/`, tests and private state schema; producer before consumers; contract and functional evaluation. Docs: current owners updated with implemented behavior. Likely files: policy.py, store.py.

## Pass Or Fail Checks

Each clause of the acceptance contract is checked using isolated synthetic fixtures, deterministic clocks and injected Google transport. Browser checks cover visible states and repeated controls; they do not prove a Google account or native package. Live Google permissions and SDK/recipient readiness remain explicitly unverified until observed.

## Regression Surfaces

Local Context registration/collection, existing Session/Context timers, app lifecycle, local request boundary, installed Docs, privacy and unrelated in-flight changes.

## Harness Trace

- Active spec: [spec-0145](../spec/spec-0145-drive-sync-contract.md)
- Active run: [run-20261028-209](../run/run-20261028-209-drive-sync-contract.md)
- Latest evaluation: [Evaluation](../evaluation/eval-0145-drive-sync-contract.md)

## Continuity

- `2026-10-28`: Boundary locked under the owner's end-to-end instruction; implementation and evaluation pending.

- `2026-10-28`: Code and scoped checks pass under [run-20261028-209](../run/run-20261028-209-drive-sync-contract.md). Bounded outcome passed; parent provider/release gates and final human acceptance remain separate.
