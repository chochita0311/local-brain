# EVAL-0175: Rust Common Settings Cutover Contract

## Metadata

- ID: `eval-0175`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-259](../run/run-20261117-259-rust-common-settings-cutover-contract.md)
- Attempt: `1`
- Feature: [FEAT-0178](../feature/feat-0178-rust-common-settings-cutover-contract.md)
- Spec: [SPEC-0178](../spec/spec-0178-rust-common-settings-cutover-contract.md)
- Execution Profile: foundation-contract
- Surface Lane: transaction, common host/delivery, consumers/handoff
- Evidence Coverage: `complete` for the bounded contract outcome
- Created: `2026-11-17`

## Scope And Method

Evaluate [the selected contract](../project/rust-common-settings-cutover-contract.md)
against the approved Feature, current source and baseline observations. Primary
performs sequential Spec, contract Builder and same-author Contract Evaluator
roles. No independent discovery/code review, new Rust execution path, packaged
artifact, browser/native or performance validation is claimed.

Baseline is HEAD `e6958df0813b8652074c68a73ac61a8b551e59a8` plus the seven
preserved inventory-handoff planning paths. Exact before/contract identities are
retained privately; no fictitious candidate commit is used. Source/policies and
manifest/lock semantics remain inputs, not authorized runtime changes.

## Acceptance Checks

| Feature obligation | Contract/source evidence and distinguishing case | Result |
| --- | --- | --- |
| 1: one writer and current/target consumers | Ownership table maps common/terminal facades, lifecycle/edition/templates/Usage/schedulers, recovery and shared helper callers. Rust owns semantic merge/normal commit; Python codec/time-zone and recovery duties remain explicit. No claim that the whole settings stack is already Rust. | PASS |
| 2: shared lock across hosts/outer callers | Actual operations.py mutex/flock/reentrant map; inherited description/parent-lifetime rule, close-not-unlock, nonblocking contention and retained recovery. Current-Mac probe confirms inherited fd works while reopened fd blocks, survives parent-reference close and releases after final close. | PASS |
| 3: value/error/format compatibility | Ordered tagged tree separates bool/int and date/time/datetime; integer strings and float hex/nonfinite values avoid JSON narrowing. Current codec and serializer are retained, including read-valid/write-refused mixed arrays. Host zone provider preserves actual installed-zone behavior. | PASS |
| 4: exact state and transaction | Seven-field Feature table, integer schema1, defaults/retired/env/read/init rules, byte revision/order/atomic permissions, current error precedence and distinct common-outside/terminal-inside-lock readback are explicit. | PASS |
| 5: common runtime independent of Terminal | Neutral foundation bridge and separate preferences mode/capabilities, closed operations/frames/callbacks, independent source/wheel/frozen receipt/discovery. No Node/launchd/cache/Tauri prerequisite or foundation→terminal import. | PASS |
| 6: compatibility, refusal, dependencies | Contract/codec/build/target/post-sign binary identity; explicit old/absent/mismatch refusal and recorded-version rollback. Existing crate manifests/toolchain observed; no new TOML dependency selected, declared minimum not claimed tested. New 40-second common transport failure boundary is named for downstream approval. | PASS |
| 7: usable downstream handoff | Whole normal-settings product scope, retained codec/recovery and separate source/search/model/Context stores, adverse cases, source/wheel/native/independent code gates and owner updates are concrete. No unapproved runtime implementation is folded into this foundation. | PASS |

The pass rests on actor/value/stage/consumer reconciliation above, not the
presence of headings or matching keywords. Later implementation must still
demonstrate the contract, including its newly introduced transport failures.

## Current-Baseline Evidence

- Python3.11.15 on the current Mac: existing `test_desktop_settings.py`32,
  `test_preferences_startup.py`2 and `test_terminal_settings.py`13 all pass
  (47 tests). These include current shared-save/unknown/revision/lock/recovery,
  first-start/partial/future-file, terminal settings/launch/origin/assembly cases.
  Terminal settings use the existing executable; no manager/shell job is started.
- Eleven isolated synthetic probes pass: absent read without file creation;
  large integer; float overflow; date/time precision; nested tables/arrays-of-tables;
  nonfinite/signed zero; read-valid/write-refused mixed array; exact schema;
  exact interval predicate; existing same-thread/other-process lock behavior;
  inherited-description lifetime/reopen/final-close kernel premise.
- Three additional reference-exchange probes pass: exact scalar/order/codec
  roundtrip, 200-level arrays and common TOML larger than8MiB. The selected flat
  node representation survives strict JSON and reproduces the current
  serializer's bytes; these are representation/current-code checks, not a Rust
  codec or new framing implementation test.
- `2**100` survives current save. `1e10000` becomes infinity and saves under the
  current Python codec; the sampled Rust TOML scalar decoder's i64/overflow
  behavior is therefore insufficient evidence for a transparent replacement.
  This counterevidence selects retained syntax adapters, not a weakened data contract.
- cargo/rustc1.99.1 are accessible at the installed absolute toolchain path;
  plain shell `cargo` was absent from PATH. No installation or shell mutation
  occurred. Workspace declares1.90; that compiler was not tested.
- Current serde/serde_json/libc/sha2 pins, declared MSRVs/licenses were checked in
  actual locks/cached upstream manifests. Official Python/Apple/PyPA evidence is
  linked beside the relevant contract claims. No dependency or Hatch-hook build
  compatibility is asserted without future implementation/build evidence.

## Findings And Reconciliation

| Candidate | Evidence, disposition and limit |
| --- | --- |
| Generic Rust TOML value parser can be substituted without drift | Refuted by actual large-integer/float-overflow behavior and cached scalar conversion source. Retain exact Python syntax codec; Rust owns business merge/commit. Pure Rust codec replacement remains explicit debt. |
| Parent-held lock can be reopened by a settings child | Refuted by actual isolated lock probe and Apple/Python API semantics. Selected inherited file description, same-thread lease reuse and child close without LOCK_UN. |
| Any save may read back before releasing its lock | Refuted by actual common `save_preferences` versus terminal `save_launch_settings`. Selected their distinct existing readback stages; no hidden timing change. |
| All settings can use terminal file/type/size checks | Refuted by separate generic read behavior. Common read keeps existing semantics and no new total-size ceiling; terminal keeps its existing8MiB/identity rules. |
| Every CLI command should preflight the new runtime | Rejected as needless scope expansion. Only consumers of migrated settings require it; unrelated existing CLI dispatch stays unchanged. |
| Retaining Python codec means no remaining migration debt | Refuted. Codec/time-zone provider and optional models/current HTTP/CLI hosts are named retained owners, separate from the normal writer being proposed. |

These are same-author contract adjudications, not independent review findings or
new product defects repaired in source. Post-contract stale-assumption review
also checks ordered tables/deep structures, lifetime pipe vs codec stdin,
missing-runtime vs corrupt-file fallback, platform-wheel tags and terminal
payload independence. No material contract choice remains unresolved.
Final representation reconciliation uses a flat ordered node list with forward
child indexes and one-parent/reachability checks, so neither recursive raw JSON
nor Rust map ordering narrows deep/ordered TOML. The reference probes above
renew the affected value/encoding witness; the full contract was reread after it.

## Evidence Gaps And Acceptance Impact

No gap blocks this contract-only outcome. Future Rust commit/codec protocol and
error/framing implementation, actual wheel hooks/binary artifacts, minimum Rust
compilation, browser/native workflows, performance/resources and independent
data/concurrency code challenge are **unperformed product gates**. They are not
promoted from current-source tests or kernel-premise probes. Existing physical
IME/sleep/VoiceOver/recipient/platform limits and Terminal177's native-window
packet remain with their owners. No whole-backend parity or merge claim is made.

## Route

Final artifact closeout also passes two existing catalog tests, catalog
freshness, 1,426 local links/anchors across13 changed/new planning documents,
privacy1,956 and whitespace. The21 captured source/build/dependency inputs and
all product source/build/test/policy paths remain unchanged; HEAD remains the
same baseline. These are source/artifact preservation checks, not code parity.

`pass` for FEAT-0178's bounded contract. Complete artifact/source-preservation
closeout in Run259, then present the separately drafted implementation Feature
for human boundary approval. This pass authorizes neither its code execution,
deployment, Git publication nor whole-PRD acceptance.
