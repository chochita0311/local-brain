# EVAL-0148: Batched Metadata And Bounded Publisher I/O

## Metadata

- ID: `eval-0148-metadata`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0148](../feature/feat-0148-drive-local-publishing.md)
- Active Spec: [SPEC-0148](../spec/spec-0148-drive-local-publishing.md)
- Run: [Run220](../run/run-20261028-220-drive-local-publishing.md)
- Attempt: 3
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`

## Problem And Result

The prior repair reduced per-file media overhead but retained sequential metadata reads and independent item I/O. Small total byte size did not remove that network overhead. Raw originals are uploaded; this path performs no model/content extraction/indexing. This correction batches known selected-source metadata up to100per outer HTTPrequest and overlaps independent publisher items with at most4workers. Folder-depth barriers, fresh parent verification, copied checkpoint records and cancellation settlement preserve the approved source/copy/deletion boundaries. Per-account SDK single-flight prevents simultaneous media workers from duplicating token refresh and retains process shutdown ownership.

Batch GETs use only known IDs from currently selected sources after root/target validation. They carry fixed metadata fields, Shared Drive flags and per-member resource keys. MIME response correlation/status/file IDs are verified; malformed/unsupported batches fall back to ordinary reads. Cache is one-use and invalidated around writes; recovery checks fresh remote state. Missing/403/404/transient/auth results retain their ordinary meanings, never authorize deletion through batch absence. This is an observation snapshot, not a folder transaction or quota reduction. Media is not batched.

## Evaluator Results

Primary agent performed logical roles sequentially; no delegated agents or independent certification. Producer contract tests passed before consumer acceptance.

| Evaluator | Result | Evidence coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | complete for bounded repair | Request/cache/source isolation, independent-item dependency/checkpoint/cancellation and SDK lifecycle below. |
| Functional | PASS | partial |87Drive tests, synthetic browser/wheel and separate live read-only metadata sample. End-to-end optimized body-transfer duration/native/recipient not established. |
| Design | PASS | complete for source Settings | Existing Settings extend-mode controls/tokens; remote phase, active-item count and latest worker path/bytes;1440 and actual320 containment. |
| UX heuristic | PASS | complete for observed flow | Checked source items and remote responses stay distinct, latest-worker bytes/path remain coherent, old last success remains distinct from current completion. No new reusable promotion candidate. |

## Evidence

- Focused `.venv/bin/python -m unittest discover -s tests -p 'test_google_drive*.py' -v`:87PASS. Sixteen new cases:100metadata reads in1POST/one-use cache; bounded101-ID split/dedup/out-of-order response correlation; per-item404/permission; transient/auth revalidation; malformed/incomplete/wrong-ID fallback; unsupported endpoint fallback; per-member resource keys; fresh write recovery; cancel/endpoint boundaries; stopped-source isolation;4overlapping uploads with verified checkpoints; unverified parent blocking descendant writes/deletion; failed folder-to-file replacement preserving descendants; failed renamed-parent preparation preserving the previous copy; cancelled workers settling before deletion; SDK single-flight. Existing source mutation, interrupted media, integrity, receive/atomic recovery/scheduler/native-request contracts pass.
- Full suite1345:1340pass,5fail. Same existing Learning/schema owner-table/audit inventory, presentation/value-registry count failures; schema/registry/builder/test inputs match work-start fingerprints. Six guide tests pass. No whole-suite success claim.
- Synthetic production-service host with fake Drive and isolated Context originals: managed prior tree then local changes. Remote phase displays its own response count, then source processing shows at most4active items with latest worker path/acknowledged bytes, and final completion clears progress/sets last success. Existing Settings controls and long paths inspected at1440×1000 and actual320×800; no root overflow and last controls reachable. Inputs were DevTools script-dispatched; no native UI-host evidence inferred.
- Separate authorized live read-only probe: pinned configured account/root, current selected-source known completed file IDs only; root/target validated first. Same20existing metadata objects:20separate HTTPrequests took9.753s;1batch HTTPrequest cached all20 and took0.637s. This validates real batch response handling and that bounded sample's metadata latency, not overall upload speed. No file content uploaded/downloaded, Drive object created/modified/deleted, browser login started, or credential/identity printed. Account/root/source identifiers and inventory remain private.
- Actual user-owned transfer was observed complete through cached local status after the work began. That user-run result is not an independent audit of all remote content or proof that the new runtime has been adopted. User process was not stopped, restarted or replayed.
- Final wheel code/assets/guide match source; no runtime/credential artifacts. Catalog, links, syntax, diff, privacy and task cleanup recorded in Run220.

## Remaining Limits

Current user runtime requires restart to adopt this correction. Existing selections/checkpoints/copies remain intact; unchanged content is not blindly retransferred. Parallel body-transfer performance, full two-account My Drive/Shared Drive behavior, native rebuild/UI-host, recipient and final human/parent acceptance remain distinct open evidence. The live metadata sample does not justify a universal speed factor or completion-time estimate. No temporary artifact is required by this evaluation.
