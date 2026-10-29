# FEAT-0149: Drive Folder Receiving

## Metadata

- ID: `feat-0149`
- Status: `in-loop`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Created: `2026-10-28`
- Updated: `2026-10-28`
- Authorization: Owner approved the PRD and delegated Feature creation and development through completion. Boundaries derive only from that PRD; final human acceptance and live-account evidence remain separate.

## Goal And User-Visible Outcome

Keep checked publisher folders synchronized into private local copies with independent schedules.

## Acceptance Contract

Root folder checkboxes excluding own publisher; whole-folder receive; per-folder 24h default; remote authority including confirmed trash/deletion; no deletion from inaccessible/partial listings; bounded atomic download; deselect retains copies.

## Scope Boundary

In: the outcome and acceptance contract above. Out: model/search/index integration, session replication, sharing-policy enforcement, aggregate quotas, permanent Drive deletion, separate recovery archive and release publication.

## Dependencies And Entry

FEAT-0145, FEAT-0146, FEAT-0147, FEAT-0148. Execute after prerequisite contracts pass. Initial auto execution is OFF; manual selection and enablement persist until changed. Errors preserve selected targets and existing copies.

## Surface Lanes And Contract Surfaces

Primary agent owns all logical roles sequentially. Contract/data/backend: `src/localbrain/google_drive/`, tests and private state schema; producer before consumers; contract and functional evaluation. Frontend/integration: Settings templates, isolated script/styles and web routes; consume stable service state; rendered design, functional and interaction evaluation. Docs: current owners updated with implemented behavior. Likely files: engine.py, service.py, static/google-drive.js.

## Pass Or Fail Checks

Each clause of the acceptance contract is checked using isolated synthetic fixtures, deterministic clocks and injected Google transport. Browser checks cover visible states and repeated controls; they do not prove a Google account or native package. Live Google permissions and SDK/recipient readiness remain explicitly unverified until observed.

## Regression Surfaces

Local Context registration/collection, existing Session/Context timers, app lifecycle, local request boundary, installed Docs, privacy and unrelated in-flight changes.

## Harness Trace

- Active spec: [spec-0149](../spec/spec-0149-drive-folder-receiving.md)
- Active run: [run-20261028-213](../run/run-20261028-213-drive-folder-receiving.md)
- Latest evaluation: [Evaluation](../evaluation/eval-0149-drive-folder-receiving.md)

## Continuity

- `2026-10-28`: Boundary locked under the owner's end-to-end instruction; implementation and evaluation pending.

- `2026-10-28`: Code and scoped checks pass under [run-20261028-213](../run/run-20261028-213-drive-folder-receiving.md). Real Google/provider integration acceptance is blocked on Desktop Client preparation and live verification; final human acceptance remains open.

## Authentication Dependency Update

- `2026-10-28`: The owner-approved gcloud/full-Drive revision in [Run215](../run/run-20261028-215-drive-oauth-adapter.md) supersedes the historical Desktop Client prerequisite above. Publishing/receiving semantics and selections are unchanged. Real Google operations and recipient validation remain open evidence gates; development verification does not log into a user account or transfer their files.
