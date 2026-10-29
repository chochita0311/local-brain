# FEAT-0148: Drive Local Publishing

## Metadata

- ID: `feat-0148`
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

Publish selected Local Context filesystem items and keep their managed Drive copies synchronized.

## Acceptance Contract

All regular files including hidden files; local authority; diff-based transfer and structure changes; source deletion to Google Trash; uncheck retains copies; oversize/failure retains prior copy; manual and independent 6h-default auto schedule.

## Scope Boundary

In: the outcome and acceptance contract above. Out: model/search/index integration, session replication, sharing-policy enforcement, aggregate quotas, permanent Drive deletion, separate recovery archive and release publication.

## Dependencies And Entry

FEAT-0145, FEAT-0146, FEAT-0147. Execute after prerequisite contracts pass. Initial auto execution is OFF; manual selection and enablement persist until changed. Errors preserve selected targets and existing copies.

## Surface Lanes And Contract Surfaces

Primary agent owns all logical roles sequentially. Contract/data/backend: `src/localbrain/google_drive/`, tests and private state schema; producer before consumers; contract and functional evaluation. Frontend/integration: Settings templates, isolated script/styles and web routes; consume stable service state; rendered design, functional and interaction evaluation. Docs: current owners updated with implemented behavior. Likely files: engine.py, service.py, static/google-drive.js.

## Pass Or Fail Checks

Each clause of the acceptance contract is checked using isolated synthetic fixtures, deterministic clocks and injected Google transport. Browser checks cover visible states and repeated controls; they do not prove a Google account or native package. Live Google permissions and SDK/recipient readiness remain explicitly unverified until observed.

## Regression Surfaces

Local Context registration/collection, existing Session/Context timers, app lifecycle, local request boundary, installed Docs, privacy and unrelated in-flight changes.

## Harness Trace

- Active spec: [spec-0148](../spec/spec-0148-drive-local-publishing.md)
- Active run: [run-20261028-222](../run/run-20261028-222-drive-local-publishing.md)
- Latest evaluation: [Evaluation](../evaluation/eval-0148-drive-connection-reuse.md)

## Continuity

- `2026-10-28`: Boundary locked under the owner's end-to-end instruction; implementation and evaluation pending.

- `2026-10-28`: Code and scoped checks pass under [run-20261028-212](../run/run-20261028-212-drive-local-publishing.md). Real Google/provider integration acceptance is blocked on Desktop Client preparation and live verification; final human acceptance remains open.

## Authentication Dependency Update

- `2026-10-28`: The owner-approved gcloud/full-Drive revision in [Run215](../run/run-20261028-215-drive-oauth-adapter.md) supersedes the historical Desktop Client prerequisite above. Publishing/receiving semantics and selections are unchanged. Real Google operations and recipient validation remain open evidence gates; development verification does not log into a user account or transfer their files.

## Throughput And Progress Repair

- `2026-10-28`: [Run219](../run/run-20261028-219-drive-local-publishing.md) passes bounded small-file request optimization, resumable no-progress/recovery and truthful runtime upload progress.71Drive tests pass; source browser/wheel evidence is separate from real-provider/native acceptance. Existing user upload is left unchanged and restart/new selected run is required for the repair.

## Metadata And Independent-I/O Repair

- `2026-10-28`: [Run220](../run/run-20261028-220-drive-local-publishing.md) passes scoped metadata batching and bounded4-item publication with verified dependencies/checkpoints/cancellation,87Drive tests and source UI/wheel checks. A separate live read-only metadata sample supports that limited latency/response claim. Current user operation was not restarted or replayed; real optimized body-transfer/native/recipient and final acceptance remain open.

## Missing-Copy And Repeat-Work Repair

- `2026-10-28`: [Run221](../run/run-20261028-221-drive-local-publishing.md) follows the owner's remote-deletion report and explicit subagent performance audit. It repairs missing managed copies under verified writable/listable parents and removes unchanged staging/checkpoint writes while retaining content hashing. This backend continuation preserves the existing Settings consumer contract. Runtime adoption and actual reconstructed-tree/body-transfer/native/recipient acceptance remain separate.

## Connection Reuse And Eight-Item Bound

- `2026-10-28`: [Run222](../run/run-20261028-222-drive-local-publishing.md) implements owned verified connection reuse and raises the shared publisher/connection cap from four to eight after a scoped read-only comparison. 121 Drive tests pass with current and minimum urllib3 versions on the project runtime. Actual connection counts and metadata timings support that bounded result; real optimized body-transfer time, native/recipient and final acceptance remain unverified. The user-owned upload was not restarted or replayed.
