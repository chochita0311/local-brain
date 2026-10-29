# FEAT-0146: Drive OAuth Adapter

## Metadata

- ID: `feat-0146`
- Status: `in-loop`
- Type: `foundation`
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract, functional
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Created: `2026-10-28`
- Updated: `2026-10-28`
- Authorization: Owner approved the PRD and delegated Feature creation and development through completion. Boundaries derive only from that PRD; final human acceptance and live-account evidence remain separate.

## Goal And User-Visible Outcome

Provide gcloud-backed OAuth and a bounded Google Drive API adapter with Google CLI-owned credentials.

## Acceptance Contract

Approved full-Drive gcloud login; pinned account token helper; explicit login and SDK-owned refresh; no app Client/Keychain dependency; complete pagination; Shared Drive flags; sanitized real-operation errors; resumable upload and bounded media.

## Scope Boundary

In: the outcome and acceptance contract above. Out: model/search/index integration, session replication, sharing-policy enforcement, aggregate quotas, permanent Drive deletion, separate recovery archive and release publication.

## Dependencies And Entry

FEAT-0145. Execute after prerequisite contracts pass. Initial auto execution is OFF; manual selection and enablement persist until changed. Errors preserve selected targets and existing copies.

## Surface Lanes And Contract Surfaces

Primary agent owns all logical roles sequentially. Contract/data/backend: `src/localbrain/google_drive/`, tests and private state schema; producer before consumers; contract and functional evaluation. Docs: current owners updated with implemented behavior. Likely files: auth.py, api.py.

## Pass Or Fail Checks

Each clause of the acceptance contract is checked using isolated synthetic fixtures, deterministic clocks and injected Google transport. Browser checks cover visible states and repeated controls; they do not prove a Google account or native package. Live Google permissions and SDK/recipient readiness remain explicitly unverified until observed.

## Regression Surfaces

Local Context registration/collection, existing Session/Context timers, app lifecycle, local request boundary, installed Docs, privacy and unrelated in-flight changes.

## Harness Trace

- Active spec: [spec-0146](../spec/spec-0146-drive-oauth-adapter.md)
- Active run: [run-20261028-215](../run/run-20261028-215-drive-oauth-adapter.md)
- Latest evaluation: [Evaluation](../evaluation/eval-0146-gcloud-drive-oauth-adapter.md)

## Continuity

- `2026-10-28`: Boundary locked under the owner's end-to-end instruction; implementation and evaluation pending.

- `2026-10-28`: Code and scoped checks pass under [run-20261028-210](../run/run-20261028-210-drive-oauth-adapter.md). Real Google/provider integration acceptance is blocked on Desktop Client preparation and live verification; final human acceptance remains open.

## Approved Authentication Revision

- `2026-10-28`: Owner explicitly chose `gcloud auth login --enable-gdrive-access --force` and its full `https://www.googleapis.com/auth/drive` scope. This supersedes the app-owned Desktop Client and readonly+drive.file contract. Each PC supplies gcloud; no project/Client JSON is a setup prerequisite. Existing credentials may be connected explicitly; a separate deliberate login action runs the approved command with account pinning and no global account/ADC changes. Google CLI owns credentials/refresh; LocalBrain retains only account identity and short-lived in-memory access tokens. App traversal/writes remain within configured root/selection. No real login is launched by development verification.

## Revision Evaluation

- `2026-10-28`: [Run215](../run/run-20261028-215-drive-oauth-adapter.md) passes the bounded gcloud authentication revision and local/package checks;52Drive tests pass. The former Client/project prerequisite is superseded. Actual Google permissions, recipient/native UI-host and final owner acceptance remain open; retain `in-loop` for features awaiting those acceptance gates. See the latest evaluation for precise evidence limits.
