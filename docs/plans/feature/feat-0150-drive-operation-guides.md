# FEAT-0150: Drive Operation Guides

## Metadata

- ID: `feat-0150`
- Status: `in-loop`
- Type: `product`
- Surface: `mixed`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Created: `2026-10-28`
- Updated: `2026-10-28`
- Authorization: Owner approved the PRD and delegated Feature creation and development through completion. Boundaries derive only from that PRD; final human acceptance and live-account evidence remain separate.

## Goal And User-Visible Outcome

Ship usable authentication, synchronization and provider-operation guidance with checked runtime integration.

## Acceptance Contract

English installer guide; per-PC Google CLI setup/full-Drive scope and account/credential ownership guide; backend lifetime and independent fixed schedules; privacy/storage owners; regression/package/browser evidence with real Google and native gaps explicit.

## Scope Boundary

In: the outcome and acceptance contract above. Out: model/search/index integration, session replication, sharing-policy enforcement, aggregate quotas, permanent Drive deletion, separate recovery archive and release publication.

## Dependencies And Entry

FEAT-0145–0149. Execute after prerequisite contracts pass. Initial auto execution is OFF; manual selection and enablement persist until changed. Errors preserve selected targets and existing copies.

## Surface Lanes And Contract Surfaces

Primary agent owns all logical roles sequentially. Contract/data/backend: `src/localbrain/google_drive/`, tests and private state schema; producer before consumers; contract and functional evaluation. Frontend/integration: Settings templates, isolated script/styles and web routes; consume stable service state; rendered design, functional and interaction evaluation. Docs: current owners updated with implemented behavior. Likely files: content/docs/settings.md, docs/policies/project/google-drive-sync.md, main.py.

## Pass Or Fail Checks

Each clause of the acceptance contract is checked using isolated synthetic fixtures, deterministic clocks and injected Google transport. Browser checks cover visible states and repeated controls; they do not prove a Google account or native package. Live Google permissions and SDK/recipient readiness remain explicitly unverified until observed.

## Regression Surfaces

Local Context registration/collection, existing Session/Context timers, app lifecycle, local request boundary, installed Docs, privacy and unrelated in-flight changes.

## Harness Trace

- Active spec: [spec-0150](../spec/spec-0150-drive-operation-guides.md)
- Active run: [run-20261028-217](../run/run-20261028-217-drive-operation-guides.md)
- Latest evaluation: [Evaluation](../evaluation/eval-0150-gcloud-drive-operation-guides.md)

## Continuity

- `2026-10-28`: Boundary locked under the owner's end-to-end instruction; implementation and evaluation pending.

- `2026-10-28`: Code and scoped checks pass under [run-20261028-214](../run/run-20261028-214-drive-operation-guides.md). Bounded outcome passed; parent provider/release gates and final human acceptance remain separate.

## Approved Authentication Revision

- `2026-10-28`: Owner explicitly chose `gcloud auth login --enable-gdrive-access --force` and its full `https://www.googleapis.com/auth/drive` scope. This supersedes the app-owned Desktop Client and readonly+drive.file contract. Each PC supplies gcloud; no project/Client JSON is a setup prerequisite. Existing credentials may be connected explicitly; a separate deliberate login action runs the approved command with account pinning and no global account/ADC changes. Google CLI owns credentials/refresh; LocalBrain retains only account identity and short-lived in-memory access tokens. App traversal/writes remain within configured root/selection. No real login is launched by development verification.

## Revision Evaluation

- `2026-10-28`: [Run217](../run/run-20261028-217-drive-operation-guides.md) passes the bounded gcloud authentication revision and local/package checks;52Drive tests pass. The former Client/project prerequisite is superseded. Actual Google permissions, recipient/native UI-host and final owner acceptance remain open; retain `in-loop` for features awaiting those acceptance gates. See the latest evaluation for precise evidence limits.
