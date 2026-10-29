# EVAL-0148: Missing Published Copies And Repeat Work

## Metadata

- ID: `eval-0148-recovery`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0148](../feature/feat-0148-drive-local-publishing.md)
- Active Spec: [SPEC-0148](../spec/spec-0148-drive-local-publishing.md#missing-copy-recovery-and-repeat-work)
- Run: [Run221](../run/run-20261028-221-drive-local-publishing.md)
- Attempt: 4
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-28`

## Problem And Result

A published source folder became unavailable under an accessible writable target. The publisher retained its completed remote identity, so the known-ID GET failed and descendants failed their parent prerequisite instead of reconstructing the local-authoritative copy. A scoped live read-only probe observed readable, correctly placed root/target folders with list/create capabilities and a complete parent listing containing neither the source ID nor its name. It did not establish whether the unavailable object was permanently deleted or inaccessible, and performed no content transfer or remote mutation.

The repair can add a replacement managed copy only after the verified parent/capability/full-listing/name checks. A new ID is checkpointed before create; old session/hash/version state is cleared. Failure retries that pending replacement ID. No inaccessible old object or local original is deleted by this branch. Readable trashed folders retain their IDs on restoration; pre-restore descendant metadata is invalidated. Pending-create recovery does not incorrectly assume an existing recovered folder is empty. Permission/auth/network/partial-listing/conflict cases preserve prior mappings and copies.

Repeat sync still hashes source contents with size/type/link and before/after stamp checks. Matching remote size/hash avoids a staging write, and equal manifest records avoid checkpoint transactions. Changed bytes still use a verified immutable snapshot; timestamp equality alone never establishes content equality. Existing four-worker folder dependencies, cancellation settlement, stable-scan deletion and upload integrity remain binding.

## Evaluator Results

Primary performed orchestrator/spec/builder/contract/functional decisions and final semantic review. The user-requested named read-only evidence worker gathered code/request/local-work evidence without runtime data, edits or inherited history. A separate bounded verification worker checks fixed logs/fingerprints/package/diff only; neither worker grants implementation or acceptance approval. This backend run changes no Settings payload, control, layout or styling, so its design/UX evaluators are omitted; parent fullstack acceptance remains open.

| Evaluator | Result | Evidence coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | Complete for the bounded code correction | Verified-parent and full-listing predicates, new durable identity, session reset, no deletion inference, pending retry, stale descendant cache and unchanged checkpoint boundaries. |
| Functional | PASS | Partial | 101 Drive tests and six guide tests, full-suite regression and source-matching wheel. Actual repaired-tree publication, native host and recipient behavior were not executed. |

## Checks

- Focused `.venv/bin/python -m unittest discover -s tests -p 'test_google_drive*.py' -v`: 101 pass. Fourteen new cases cover missing source/nested folders/files; explicit parent capabilities; incomplete listings; same-name or same-ID conflicts; permission/network/auth refusal; durable failed replacement retry; nonempty recovered pending parent; trash restoration with stale descendant snapshots; unchanged staging/checkpoint elimination; same-size changes with restored mtime; source mutation during hash-only comparison; scoped cache invalidation. Existing integrity/resumable/rename/source/cancellation/receive/SDK/scheduler/Settings contracts pass.
- Full final suite: 1359 tests, 1354 pass and five existing unrelated schema/registry failures. Nine schema/registry/builder/test input fingerprints remain identical to work start. No complete-suite success claim. Six bundled-guide tests pass after the guide update.
- The source wheel builds. Code/assets/guide byte equality, packaged-runtime exclusion, catalog/link/diff/privacy and task cleanup are recorded in Run221. The first isolated build could not reach PyPI in the sandbox; an approved build with normal network access succeeded. No native rebuild or live-server restart was performed.

## Performance Review

The bounded audit covers outgoing publication only. It distinguishes HTTP round trips from API quota, body transfers, source hashing/staging and SQLite checkpoints:

- Initial originals already use batched generated IDs and one multipart media request per file up to 5,000,000 bytes on ordinary success, without a new-ID existence GET. Folder creation and verified parent dependencies remain necessary. Larger or interrupted files retain resumable recovery.
- Known selected-source status checks already use up to 100 members per batch and at most four independent workers. An unchanged run requires no body transfer. It still verifies remote metadata and reads source contents; this repair eliminates that run's staging writes and equal-record checkpoint transactions. The synthetic unchanged-tree case observes zero staging creations and zero checkpoint calls while retaining a hash comparison.
- The project virtual environment is Python 3.11.15. Installed `urllib.request.AbstractHTTPHandler.do_open` creates a connection per outer request, sets `Connection: close`, and closes the socket. Sharing the opener across workers therefore does not provide HTTP connection reuse. No direct pooled HTTP transport is currently declared in the base dependency set. Reuse is a concrete further candidate, not an implemented or timed improvement in this run. A change must preserve trusted system TLS, redirects/endpoint boundaries, proxy behavior, bounded streaming, cancellation and owned resource shutdown. Actual TCP/TLS timing, pool size and a higher-concurrency comparison were not measured.

This evidence does not establish universal optimality, minimum possible elapsed time, a speed factor for real uploads or recipient performance. A transport-reuse follow-up should compare a controlled synthetic transport and separately authorized real selected transfer before claiming a timing benefit. No new dependency or transport architecture is introduced by this audit.

## Acceptance Limits

Current user runtime retains its cached prior partial result until it adopts the repaired source and executes again. No user-owned process was restarted and no real upload replayed by verification. Actual reconstructed-tree/body-transfer timing, two-account My Drive/Shared Drive operations, native/recipient and final owner/parent acceptance remain open. Those integration/release gates are not inferred from this code-level PASS. No temporary artifact is required by this evaluation.
