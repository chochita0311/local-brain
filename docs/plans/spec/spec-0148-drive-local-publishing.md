# SPEC-0148: Drive Local Publishing

## Metadata

- ID: `spec-0148`
- Status: `approved`
- Run: [run-20261028-222](../run/run-20261028-222-drive-local-publishing.md)
- Attempt: 5
- Parent Feature: [feat-0148](../feature/feat-0148-drive-local-publishing.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`
- Updated: `2026-10-28`

## Implementation Goal And Acceptance Mapping

Publish selected Local Context filesystem items and keep their managed Drive copies synchronized.

All regular files including hidden files; local authority; diff-based transfer and structure changes; source deletion to Google Trash; uncheck retains copies; oversize/failure retains prior copy; manual and independent 6h-default auto schedule.

## State And Data Contract

Use the shared [Drive sync contract](../../policies/project/google-drive-sync.md). Private SQLite owns connection selection, manifests and per-job observations; Google CLI owns OAuth credentials and refresh. A connection/root change has a new namespace. Received copies never enter indexing implicitly. Mutations are serialized against settings changes and cancellation is checked between operations. No local failure, access loss, partial listing, oversize rejection or stopped selection authorizes deletion. Persist checkpoints per verified item; do not claim folder-wide atomicity.

## Surface Lanes And Evaluation Focus

engine.py, service.py, static/google-drive.js. Dependency order: contract, producer implementation, consumers, evaluator and regression. Primary agent performs logical roles sequentially. Validate with the focused Drive suite, existing Settings/Docs/boundary tests and rendered Settings at desktop/320px where applicable. Verify outgoing local authority, incoming remote authority and actual-operation errors independently.

## Open Blockers And Evidence Limits

The owner-approved gcloud/full-Drive revision supersedes the former app-owned Desktop Client, readonly+drive.file and Keychain prerequisites. The current producer contract is SPEC-0146 and Run215. Live two-account My Drive/Shared Drive operations and installed-recipient/native UI-host behavior remain unverified; synthetic tests or a wheel build do not establish those gates. The publishing/receiving contract itself is unchanged.

## Scope Exclusions

All exclusions and regression surfaces in the parent Feature remain binding.

## Throughput And Runtime Progress Repair

Run219 addresses reported apparent stalls within the existing contract. Files up to5,000,000bytes use multipart upload unless an existing matching resumable session must be recovered; larger files retain bounded resumable streaming. Batch generated IDs at100per request; checkpoint each assigned ID before mutation, and skip a remote existence GET only for an ID newly allocated in this attempt. Prior pending/completed identities are always reconciled. Lost upload responses are verified by the same known ID, size and hash before success; no blind duplicate create. Resumable responses advance from acknowledged ranges; probe on recovery/uncertain writes, bound repeated zero progress and retain resumable state. No integrity relaxation or new file filtering/concurrency policy.

Upload progress is transient runtime state: stage, processed/total source items, file transfer/structural-change/error counts, current relative path/byte acknowledgement and last activity. A processed item is checked/handled, not necessarily newly transferred; failures stay distinct. Scan/check/cleanup phases are named; no ETA or synthetic heartbeat. Opening/status polling remain local/cache-only, progress never marks a job complete, and last success advances only on a fully completed run. Existing errors, snapshots/checkpoints and stop/copy semantics remain binding. Receive behavior is preserved; upload progress alone is in this repair. All tracked fixtures/examples remain synthetic. Current active user upload is not cancelled or replayed by verification; changes require a backend restart before a new run.

## Batched Metadata Repair

Run220 reduces known-file status lookups without changing raw-folder synchronization. After root/own-target validation, prefetch metadata only for remote IDs belonging to currently selected source IDs. Use Google Drive multipart batch GETs, at most100per batch, pinned `/batch/drive/v3`, fixed metadata subpaths/fields, Shared Drive flags and relevant per-item resource keys. Validate MIME part IDs, HTTP status and returned file ID before caching. Cache results once per known ID; malformed/missing/duplicate parts or unsupported batch fall back to individual reads. Per-item404/permission errors preserve their ordinary non-deletion behavior. Authentication/transient errors are individually revalidated. Writes invalidate any snapshot for that ID before recovery/integrity reads. This is a metadata observation snapshot, not a folder transaction or an assurance against later concurrent remote edits.

Progress names remote batch verification separately from source-item processing. Cache/status remains local, last success requires the normal completed result, and no fake heartbeat/ETA is added. HTTP connection count is reduced; API quota still counts the inner operations. Media is not batched. Current user transfer is not cancelled or replayed; adopted runtime and real latency need their own evidence. Existing files/structure/deletion/copy/source authority and per-file limits stay binding.

Independent publisher items run with at most4workers. Folder depth barriers establish verified parents before descendants; file processing follows folder preparation. Record preparation and checkpoint snapshots are serialized under a run lock, while independent HTTP/media operations may overlap. Each checkpoint copies the worker-local record, preventing another worker from serializing an in-flight mutation. Cancellation stops new submissions, settles owned workers and never enters deletion while work is uncertain. Counts are synchronized; current-path/bytes identify the latest worker event and `active_items` exposes concurrency. SDK token refresh uses per-account single-flight without holding the process-lifecycle lock. No new user concurrency setting, backend job parallelism or receive change is introduced.

## Missing-Copy Recovery And Repeat Work

Run221 is a backend-only continuation; its contract/functional evaluators cover recovery and local work, while existing fullstack consumer/parent acceptance remains separate. A completed managed item whose known ID is unavailable can be rebuilt only under a freshly verified, non-trashed parent with explicit list/create capabilities, after a complete listing contains neither that ID nor a normalized same-name child. Parent/listing/permission/auth/network errors or name conflicts preserve the prior mapping/copies. Rebuilding allocates and checkpoints a new ID before create, resets old upload-session/content/version state, and never trashes the inaccessible old object. Pending assigned IDs retain ordinary retry/recovery semantics; a newly failed create retries its new assigned ID rather than allocating again. Parents precede descendants, including recovery; a restored folder must not leave stale descendant metadata snapshots in use.

Unchanged regular files still receive bounded stable-source content hashing. Avoid writing a staging copy when matching remote checksum/size establishes no body transfer; changed files still use an immutable verified snapshot. Skip identical manifest checkpoint writes, retaining atomic rename/remap and every changed identity/session/completion checkpoint before their dependent operation. No timestamp-only comparison or weakened integrity/deletion/cancellation rule is introduced. Transport reuse or higher concurrency is not automatically admitted by a static audit; retain verified TLS, disabled redirects, Google endpoint pinning, bounded bodies, per-worker ownership and SDK cancellation boundaries.

## Connection Reuse

Run222 admits bounded connection reuse to address the owner's continuing speed report. Use urllib3 with an explicit compatible base dependency and the existing verified SSL context (system trust on supported macOS). Following a scoped read-only comparison of four versus eight workers, this run supersedes Run220's internal four-item limit with a shared maximum of eight publisher workers and eight pooled connections; no concurrency setting or parallel backend jobs are added. Folder-depth dependencies, serialized changed checkpoints and cancellation settlement remain binding. Respect standard HTTP(S) proxy discovery/bypass and proxy credentials without logging or forwarding them to the origin. Disable redirects and transport-level retries; API-level safe-read/backoff and known-ID/resumable uncertain-write handling remain authoritative. Stream responses without automatic decoding/preloading. Return a fully consumed response's connection for reuse; close an unread/failed response without unbounded draining and release its pool capacity. Preserve accepted308/404/410 and sanitized TLS/network diagnostics. Explicitly close owned pools after identity verification, root browsing and settled synchronization, including errors/cancellation; injected opener ownership remains with the injector. Settings consumer/media/checkpoint/source-copy contracts remain unchanged. Compare actual connection counts and separately bounded metadata timings without claiming a full-upload speed factor.
