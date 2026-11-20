# Rust Common Settings Runtime Increment

## Log Type

- Type: `Implementation`
- Date: `2026-11-18`
- Related track: [REFACTOR-0006](../refactor-0006-rust-core-transition.md)
- Scope: approved [FEAT-0179](../../feature/feat-0179-rust-common-settings-runtime.md), [RUN-260](../../run/run-20261118-260-rust-common-settings-runtime.md)

## Summary

Phase3B's common-settings increment is complete and passes
[EVAL-0176](../../evaluation/eval-0176-rust-common-settings-runtime.md).
Phase3 and the whole Rust transition remain partial. General and Terminal
settings share Rust rules/merge/revision/normal publication; exact Python syntax,
OS-zone lookup, host adapters, explicit recovery and other-store helpers remain.
The base source/platform wheel/frozen app consume a separate common executable
without Terminal preparation. No user app/service/job replacement or Git write.

## Responsibility And Structural Result

Before: general rules and TOML publication lived in Python preferences;
Terminal used the optional control runtime for validation and Python for commit.
After: `localbrain-core::preferences` separates typed values, closed wire and
semantic/transaction ownership; `foundation.rust` owns neutral verified transport
and child lifecycle; `preferences_codec` owns only fixed syntax/zone callbacks;
feature facades retain public exception/output contracts. The existing lock owner
exposes its inherited description and remains held until reap, including outer
callers. Normal publication has one Rust owner; restore is a distinct retained
transaction rather than a second success fallback.

A representative general save is facade preflight→parent operation lock→verified
child/inherited lease→current decode and validation→revision/merge→exact encode→
private atomic publication→reap/release→readback→host notification. Terminal's
readback instead stays under the lock. Changing a known-field predicate has one
core owner; changing TOML syntax has one retained adapter owner. Delivered binary
compatibility is recorded in a closed manifest, not inferred from PATH or the
presence of a Terminal installation. The additional bridge/codec files reflect
different authority and lifetimes, with no new framework or registry.

The necessary consumer sweep handles temporary runtime failure in both sync
daemons and outer native middleware, fixed startup diagnostics, and worker-pool
rendering for async consumers exposed to the new child wait. Existing ingestion,
data/auth/notification and template outputs retain their owners and stages.

## Behavior And Parity

- Preserved: seven common defaults/predicates, schema1, ordered unknown/retired
  typed values, exact serializer bytes/error order, SHA revision, private save,
  shared source/sync/backup/restore serialization and distinct readback stages.
- Explicit approved deltas:40-second common-operation deadline, unavailable503
  and startup refusal, verified required executable and first platform-specific
  macOS14/arm64 wheel. These are interface/delivery changes, not old Python parity.
- Actual old/new277 cases agree; lease/process/fault/timeout and delivered
  source/wheel/native checks support the bounded result. Whole-backend parity
  remains **Provisional**; no merge-safety or blanket Python-removal decision.
- Per-operation child/callback cost makes sampled reads/saves slower: final
  median11.208/41.029ms versus baseline0.036/0.485ms. Empty Sessions HTML median
  17.182ms versus2.690ms. No performance budget or speedup is inferred.

## Validation And Independent Challenge

Baseline actual commit `e6958df0813b8652074c68a73ac61a8b551e59a8`,13 existing
planning edits preserved. Candidate5 manifest
`767a0a8e0962ea5979841fd8b25ecdc1d9f77e3379f253a37ceba5eda17a2e1d`
freezes1,969 files; final636 other non-document inputs match it. A later
Korean-guide-only recovery-text delta renews delivery/native/doc checks without
changing executable/build/test code. Full Python1,731
run/49 skipped passes, Rust11 and formatter pass, differential277 and browser70
pass. Installed base wheel, sdist rebuild, final signed relocated native app
General/Terminal save/reopen/Quit/relaunch and outage/recovery pass. Final
artifact digests, scoped contention/fault results, resource/minimum-version
limits and document/privacy checks are recorded by Eval0176/Run260.

Required fresh read-only challenge found scheduler liveness and native500
omissions; primary reproduced/repaired them. Informed followups identified
remaining blocking async callers and confirmed the bounded fixes. Primary
also repaired real long-path/temp-cleanup, signed-NaN, fd, packaging-path,
startup and standalone-under-`payloads` counterexamples. Final informed review
found no further concrete issue in its delta; it did not execute reviewed code,
see final native results, or grant acceptance. Initial author reasoning was
withheld; later rationale, shared fixture/codec lineage and other independence
limits are explicit in Eval0176/private receipt. Actual reviewer token/cost and
provider execution details are unobservable. No arbitrary attempt quota or user
hard deadline was supplied; concrete new evidence justified each repair check.

## Remaining Work And Handoff

Python TOML/zone/HTTP/CLI/template and optional model responsibilities, Node
PTY/VT and the inventory's remaining database/ingestion/reader/retrieval families
remain. Next proposed dependency is persistence/identity/recovery boundary
planning under the [inventory](../../project/rust-backend-migration-inventory.md),
followed by separately approved coherent writer/read slices. This completion
does not approve a new Feature boundary or start its code.

Rust1.90/Python3.9 minima, macOS14 hardware/other platforms, recipient installation,
physical input/IME/VoiceOver/sleep and long-soak/resource guarantees were not
established. Terminal177's latest actual-window packet is still pending; this
native Settings pass does not close it. Durable evidence is retained privately;
task-owned synthetic processes and temporary staging are cleaned at Run closeout.
