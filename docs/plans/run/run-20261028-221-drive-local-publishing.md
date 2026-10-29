# Run221: Recover Missing Published Copies And Reduce Repeat Work

## Metadata

- ID: `run-20261028-221`
- Status: `passed`
- Feature: [FEAT-0148](../feature/feat-0148-drive-local-publishing.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Active Spec: [SPEC-0148](../spec/spec-0148-drive-local-publishing.md#missing-copy-recovery-and-repeat-work)
- Attempt: 4
- Execution Profile: `backend-product`
- Required Evaluators: contract, functional
- Created: `2026-10-28`

## Controlled Continuation

The owner reports that deleting a published source folder remotely makes the next local-authoritative synchronization fail. Cached result and a scoped read-only metadata probe show the managed source ID is unavailable while the root/own target are readable, writable and correctly positioned; the complete parent listing contains neither the known ID nor a same-name child. No private account, publisher, source or object identifiers are copied into this record.

Primary owns requirements, recovery/concurrency/persistence decisions, implementation and final evaluation. A user-requested `evidence_scout` performs bounded read-only request/local-I/O inventory with no inherited history, runtime access or editing. Its output is evidence, not acceptance. Existing selected root and local authority remain binding; a missing-copy repair must never delete an inaccessible old object or a local source.

This run narrows FEAT-0148's fullstack work to backend recovery and repeat-work reduction. Settings contracts/layout/styles/controls remain unchanged; design and UX evaluators are omitted for this bounded backend run, with parent feature acceptance unchanged. Contract evaluation precedes functional acceptance. The user-owned server is not restarted and real content transfers are not replayed during verification.

## Verification Plan

Synthetic cases: missing source/nested folders and files, writable/listable verified parent and name/identity absence checks, permission/partial-listing/collision refusal, retry after failed replacement creation, no stale-ID reuse, trashed-folder restoration, checkpoint-before-create and no-op repeat work. Preserve existing cancellation, stable-scan deletion, integrity, rename/stop boundaries. Run focused Drive tests, relevant service/docs/boundary regressions, full suite and repository privacy checks. Record synthetic performance counters separately from actual provider timing; no universal optimality or full-upload latency claim.

## Result And Closing Verification

[Evaluation](../evaluation/eval-0148-drive-recovery.md): contract and functional PASS with partial live/native/recipient evidence. Missing managed copies can be reconstructed only after verified-parent/capability/complete-listing checks, with a new durable ID and no deletion of an inaccessible old object. Readable trashed folders restore with the same ID and fresh descendant observations. Unchanged files retain content hashing but avoid staging and equal-record checkpoint transactions. No transport/dependency/concurrency or Settings consumer migration is included.

- Focused Drive: 101 pass; guide tests: six pass. Final full suite: 1359 tests, 1354 pass, five existing unrelated failures. Exact existing failures: `test_effective_schema_and_owner_docs_remain_in_sync`, `test_audit_checker_and_resolved_ledger_are_current`, `test_manifest_inventory_matches_audit_boundary`, `test_manifest_has_complete_versioned_baseline`, `test_registry_covers_eleven_subjects_and_current_required_inventories`. Nine unrelated schema/registry/builder/test input hashes match work start.
- A bounded verification worker independently read these saved results and compared those fingerprints, six code/asset/guide wheel members and forbidden-artifact patterns; all requested comparisons and `git diff --check` passed. It did not rerun tests or approve semantic completion. Concurrent creation of the evaluation record was observed as expected primary work.
- Wheel builds and matches source; no packaged databases, session/log or credential artifacts. The sandboxed first build could not resolve public PyPI; the approved network-enabled build succeeded. Native package/host and real reconstruction were not exercised.
- Nineteen relative links resolve; catalog and diff checks pass. Final repository privacy check passes for 1547 candidate files. Owned scratch was removed after all tests, build, probe and verification readers finished; no owned server/browser fixture was started.
- Final cached real operation remains the earlier partial result; the user-owned development server has no reload option and requires restart to adopt the repaired source. It was not stopped/restarted, and real body transfers were not replayed. No common-harness/design/interaction promotion candidate was established. Final parent/human and provider/native/recipient acceptance remain separate.

## Performance Follow-Up

The user-requested read-only audit confirms remaining per-request connection setup in this project's Python 3.11.15 `urllib.request` transport. HTTP connection reuse is an unimplemented, unmeasured candidate with TLS/proxy/streaming/shutdown boundaries to validate. Increasing worker count was not benchmarked. Initial upload, metadata batching, unchanged local work and actual end-to-end/provider timing remain separate claims; this run does not call the implementation universally optimal.
