# EVAL-0148: Upload Throughput And Progress Repair

## Metadata

- ID: `eval-0148-throughput`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0148](../feature/feat-0148-drive-local-publishing.md)
- Active Spec: [SPEC-0148](../spec/spec-0148-drive-local-publishing.md)
- Run: [Run219](../run/run-20261028-219-drive-local-publishing.md)
- Attempt: 2
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`

## Observed Problem And Bounded Correction

Private read-only checkpoint samples advanced while the UI displayed only running status. This disproves a complete stall during those sampled intervals; it does not prove constant progress at all times or completion. Actual identifiers, source inventory/counts and file contents are not copied into this report. Code showed avoidable per-file ID generation, fresh-ID existence lookup, and session probes before every chunk. This repair reduces request overhead, preserves resumable recovery and exposes truthful progress; it does not introduce concurrency, aggregate quotas, new filtering or an ETA.

Files up to5,000,000bytes use metadata+media multipart unless recovering a matching stored session; larger files keep resumable streaming. Generated IDs are batched100at a time and assigned/checkpointed before mutation. Only a newly allocated ID skips initial remote lookup. Lost multipart responses verify the same ID and hash/size; pending identities are reconciled. Fresh resumable sessions start at zero without a probe, acknowledged ranges advance later chunks, uncertain writes probe before resend, and three non-advancing chunk acknowledgements stop while retaining the session. Missing final metadata is verified by known ID. These retain source authority/integrity/cancellation and copy/deletion contracts.

Transient upload progress names preparation/scan/sync/source-check/cleanup/finish phases, checked/total items, new file transfers, errors, current relative path, acknowledged bytes and last real activity. Checked includes folders, unchanged entries and handled errors. Progress is not persisted, fabricated by polling or used to advance last success. Prior run totals do not appear as current progress. Post-transfer validation/deletion may still be pending after all source items are checked. Receive behavior remains unchanged.

## Evaluator Results

Primary agent performed logical roles sequentially without delegated agents or independent certification. Backend/contract tests passed before dependent frontend acceptance.

| Evaluator | Result | Evidence coverage | Witness |
| --- | --- | --- | --- |
| Contract | PASS | complete for bounded repair | Known-ID checkpoints, multipart thresholds, source-authority invariants, transient progress producer/consumer and recovery below. |
| Functional | PASS | partial |71Drive tests and synthetic browser; live account permissions/throughput/native release not exercised. |
| Design | PASS | complete for source Settings | Existing Settings controls/tokens in screen-alignment extend mode;1440×1000 and actual320×800; current path/progress contained, last result and footer reachable. |
| UX heuristic | PASS | complete for observed flow | Advancing item/byte/activity values distinguish running work from an unchanged label; old success remains explicitly last success, final completion replaces progress. No new reusable promotion candidate. |

## Evidence

- Focused command `.venv/bin/python -m unittest discover -s tests -p 'test_google_drive*.py' -v`:71PASS. Sixteen new throughput/progress cases cover batched IDs; exact binary MIME metadata/content; empty files; same-ID PATCH; dynamically discovered parent resource keys in multipart headers; inclusive5MB method boundary; lost create-response reconciliation; wrong checksum; old small-session recovery; acknowledged chunks without extra probes; bounded no-progress; expired session; missing final metadata; fresh versus pending existence lookup; checked versus transferred counts; cache-only transient runtime progress and last-success gating. Existing interrupted upload, source mutation, integrity, deletion/receive/scheduler/native boundary contracts pass.
- Full suite1329tests:1324pass,5fail. Same existing Learning/schema owner-table/audit inventory, presentation count and value-registry count failures; schema/registry/builder/test inputs retain work-start fingerprints. Six bundled-guide tests pass after guide edits. No whole-suite success claim.
- Same synthetic short binary and injected HTTP responses through the captured prior API and revised API: upload phase uses3requests before (session create, status probe, media PUT) versus1after (multipart POST), with the same checksum/size result. This is protocol-request evidence, not a real network speed benchmark. Batched-ID test allocates100unique IDs from1request. Fresh-versus-pending test preserves uncertain-write recovery while skipping only the known-new read.
- Synthetic backend host uses isolated Context files, private SQLite and fake Drive; no actual account token, destination, document bytes or Google calls. A run displayed phase, checked/total items, current path, acknowledged bytes and activity while last success remained unset. Completion cleared runtime progress, enabled manual action and displayed final counts/success time. A later changed-file run displayed previous last success distinctly without presenting old transfer totals as current. An unchanged-file run skipped body transfers while checked items advanced.
- DevTools script-dispatched controls and observed DOM plus visual1440/actual320 screenshots: long synthetic relative path wraps, count/byte/activity text stays contained, no root horizontal overflow, controls/footer reachable. Source Settings family reused without new CSS. Local cached status polling did not create Google/SDK requests. Expected local API diagnostics and source/native evidence remain separately scoped.
- Wheel contains matching API/engine/service/JS/guide source; runtime/credential artifacts absent. JS syntax, artifact links, catalog, diff and privacy checks recorded in closing Run.

## Limits And Handoff

User-owned runtime/upload is left unchanged; this repair takes effect after restarting the backend and starting a selected run. Existing verified checkpoints/copies are retained, unchanged files are compared rather than blindly reuploaded, and pending sessions reconcile by known identity. No current real transfer was cancelled, resumed or replayed by the agent. No actual Google permission, two-account My Drive/Shared Drive, real latency improvement, native rebuild/UI-host or recipient acceptance is inferred from synthetic tests or a wheel. Parent/provider/final human acceptance remain separate from the bounded local PASS. No temporary evidence path is a durable dependency.
