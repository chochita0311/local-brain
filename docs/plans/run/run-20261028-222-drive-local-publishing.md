# Run222: Reuse Drive Transport Connections

## Metadata

- ID: `run-20261028-222`
- Status: `passed`
- Feature: [FEAT-0148](../feature/feat-0148-drive-local-publishing.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Active Spec: [SPEC-0148](../spec/spec-0148-drive-local-publishing.md#connection-reuse)
- Attempt: 5
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-28`

## Controlled Continuation

The owner continues reporting excessive small-original upload duration. Run221's audit identified a new connection per outer urllib request; this run implements bounded connection reuse rather than treating total bytes or file count as a sufficient performance explanation. The original selected raw-folder, checkpoint, checksum, cancellation and bounded-worker dependency semantics remain binding. Primary owns architecture, dependency, implementation and final review; existing user operation is neither stopped nor replayed.

Use a directly declared urllib3 runtime dependency compatible with the repository's Python range, a per-API verified-SSL connection pool, and explicit transport ownership/close in authentication identity checks, browsing and sync jobs. Initial four-connection reuse was measured separately, then a scoped read-only four-versus-eight comparison supported raising the shared publisher/pool ceiling to eight. This is an internal bound change, with no user concurrency setting or parallel backend jobs. Preserve system/environment HTTP(S) proxies and bypass, disabled redirects, endpoint pinning, bounded streamed reads and existing Google error/recovery behavior. Disable transport-level automatic retries so uncertain creates/media retain the existing known-ID/session reconciliation. Never drain an unbounded discarded response just to reuse its connection.

Backend-only contract and functional evaluators; Settings payload/layout/controls are unchanged, so parent design/UX acceptance remains separate. Evidence: deterministic synthetic connection reuse/concurrency/error/early-close/proxy/TLS/lifecycle checks; focused/full regressions; separately authorized scoped live read-only metadata timing if available. Measure that bounded sample only, not full original uploads or minimum possible time. Native/recipient/live-body and final owner acceptance remain open.

## Result And Closing Checks

[Evaluation](../evaluation/eval-0148-drive-connection-reuse.md): contract and functional PASS, partial live/native/recipient coverage. The original four-item limit is superseded by one shared eight-worker/eight-connection constant after the read-only comparison. Trusted TLS/proxy/bypass and status/error boundaries, no hidden redirect/retry, bounded framing/streaming cleanup and explicit socket ownership are preserved. No format, selection, account, scheduler or Settings control migration is included.

- 121 focused Drive tests pass with urllib3 2.8.0 and the same 121 with isolated minimum 2.6.3 on project Python 3.11.15. Final full suite: 1379 tests, 1374 pass and the same five unrelated schema/registry failures; nine failure inputs match work-start hashes. Guide tests pass in that suite. No all-Python or whole-suite success claim.
- Live read-only ordered cohorts, same 20 objects per comparison: initial four-worker one-off/pool 2.513/2.041 seconds with 20/4 actual connections. Follow-up one-off4/pool4/pool8: 3.144/2.253/1.400 seconds with 20/4/8 connections. No content transmission, remote mutation, browser login or credential/identity output. This is metadata-only timing under varying network/server conditions, not full-upload speed or universal optimality.
- Normal network lock resolution and offline lock check pass. Package versions/sources match work start; the declared urllib3 dependency retains the Python floor. Wheel build succeeds and eight code/asset/guide members match source; direct urllib3 metadata and Python >=3.9 are present; no runtime/log/credential artifacts. Native binary was not rebuilt.
- Twenty artifact links resolve; catalog and diff checks pass. Final privacy check passes for 1551 candidate files. Task scratch was removed after all tests, probes, build and readers completed; no durable output depends on temporary files. Test HTTP servers were loopback-only, temporary and process-owned; no real user process was restarted.
- The earlier actual upload ended partial with one network error. Prior successful items retain their normal checkpoints. That run used the earlier runtime; new-source adoption requires restarting the current non-reloading server. No actual transfer replay occurred. Optimized media duration, native/recipient, two-account and final parent/human acceptance remain open.

No reusable common-harness/design/interaction promotion candidate established. Primary retained all source-of-truth, architecture, dependency, concurrency, persistence and final semantic decisions. Library connection/response ownership was tested directly rather than assuming that sharing an opener provides reuse or that pool-cache removal immediately closes retained sockets.
