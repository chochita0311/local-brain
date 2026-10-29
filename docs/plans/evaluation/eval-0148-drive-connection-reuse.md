# EVAL-0148: Bounded Connection Reuse

## Metadata

- ID: `eval-0148-connection-reuse`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0148](../feature/feat-0148-drive-local-publishing.md)
- Active Spec: [SPEC-0148](../spec/spec-0148-drive-local-publishing.md#connection-reuse)
- Run: [Run222](../run/run-20261028-222-drive-local-publishing.md)
- Attempt: 5
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-28`

## Result

The prior urllib opener created a fresh connection per outer request. The repaired transport reuses verified connections within an API instance and explicitly closes its concrete pools after authentication identity checks, root browsing and settled jobs. A shared internal constant now bounds publisher work and transport capacity at eight, superseding the earlier four-item limit after a scoped read-only comparison. Folder-depth dependencies, copied changed checkpoints, SDK single-flight and cancellation settlement remain binding. No user concurrency control, parallel backend job, archive format or selected-source expansion is added.

Streaming responses retain bounded caller reads without automatic preloading/decoding. Complete and empty bodies permit reuse; early close, truncated framing and read failures close the connection without unbounded draining and release capacity. Header-declared remaining bytes are checked through bounded reads rather than accepting a short, apparently valid JSON prefix. Redirects and library automatic retries are disabled. Existing safe API retries, accepted resumable statuses, known-ID/integrity verification and session recovery remain authoritative. Standard proxy/bypass and verified macOS system trust remain; proxy credentials stay out of origin headers and sanitized diagnostics. Injected opener ownership stays with its injector.

Primary performed logical orchestrator/spec/builder/contract/functional roles and final review. The previous worker's static transport inventory was reused as a starting hypothesis, not independent certification. No new worker or reusable design/interaction/common-source promotion candidate was required. This backend change preserves Settings payload/control/layout/style contracts; design and UX evaluators are omitted for this run, with parent fullstack acceptance unchanged.

| Evaluator | Result | Evidence coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | Complete for bounded code correction | Pool ownership/capacity, framing/streaming, no redirect or hidden retry, scoped TLS/proxies, SDK/checkpoint/dependency/cancellation and source/copy regression checks. |
| Functional | PASS | Partial | Synthetic TCP fixtures, two installed urllib3 versions, full suite, source-matching wheel and separate live read-only metadata samples. Real optimized media/upload duration and native/recipient behavior are not established. |

## Verification

- Final focused Drive suite: 121 pass with project Python 3.11.15 / urllib3 2.8.0. The same 121 pass with urllib3 2.6.3 isolated in task scratch, without changing the project environment. This tests library-version compatibility on Python 3.11, not actual execution on every supported Python version.
- Twenty new transport/lifecycle cases cover actual TCP reuse (20 responses/one connection), 16 concurrent requests/eight-connection ceiling, early-close non-drain/reconnect, empty bodies, redirect refusal, no automatic POST retry, truncated framing and capacity release, explicit concrete socket close, accepted308/header reuse, sanitized error-response reuse, four safe GET attempts, streaming/TLS/pool settings, proxy credentials/trust, bypass and malformed-proxy sanitization, nested certificate error semantics, injected ownership and identity/browse/job closure across success/partial/error/cancellation. Existing publisher concurrency, checkpoint, cancellation and SDK single-flight cases now exercise eight workers. Existing raw-file/recovery/receive/scheduler/Settings contracts pass.
- Final full suite: 1379 tests, 1374 pass and five existing unrelated schema/registry failures. Nine schema/registry/builder/test inputs match work-start hashes. Six bundled-guide tests pass as part of the suite. No full-suite success claim.
- `uv lock --check --offline` passes after normal network resolution. Package versions and sources match the work-start lock; urllib3 becomes directly required, with 2.6.3 for Python 3.9 and 2.8.0 for Python 3.10+. An initial fresh-cache offline solve lacked optional-package metadata; the normal solve succeeded without narrowing Python support or changing unrelated versions.
- Wheel build succeeds. Exact source-member/dependency/privacy/catalog/link/diff and owned scratch cleanup results are recorded in Run222. Native binaries were not rebuilt.

## Scoped Provider Timing

Two authorized read-only samples used the already bound account, validated configured root/target and known completed selected-source file IDs. They issued only metadata reads; no content upload/download, remote mutation, browser login or identity/credential output. Timing excludes initial SDK token acquisition, root validation and candidate selection. All timed requests in each comparison address the same 20 known objects.

| Ordered cohort | Outer GETs | Workers | Actual connection calls | Seconds |
| --- | --- | --- | --- | --- |
| Initial one-off transport | 20 | 4 | 20 | 2.513 |
| Initial pooled transport | 20 | 4 | 4 | 2.041 |
| Follow-up one-off transport | 20 | 4 | 20 | 3.144 |
| Follow-up pooled transport | 20 | 4 | 4 | 2.253 |
| Follow-up pooled candidate | 20 | 8 | 8 | 1.400 |

This demonstrates actual connection reuse and those limited metadata timings. Cohorts were ordered rather than counterbalanced; network/server conditions were not held constant, and media creation was not timed. It does not establish a universal speed factor, optimal worker count, overall upload duration or absence of account/organization quota limits. Fixed API operation count remains distinct from connection setup and concurrency.

## Runtime And Acceptance Boundary

The user-owned upload was left untouched. Its cached result later became partial with one network error; earlier successful transfers remain checkpointed for ordinary diff/recovery. That run did not use the new transport and is not this repair's performance evidence. The current non-reloading development server needs restart before adoption. No real body-transfer retry was initiated by verification. Optimized full publication, two-account My Drive/Shared Drive, native/recipient, and final owner/parent acceptance remain separate open evidence gates.
