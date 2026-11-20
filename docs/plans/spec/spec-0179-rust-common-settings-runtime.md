# SPEC-0179: Rust Common Settings Runtime

## Metadata

- ID: `spec-0179`
- Status: `approved`
- Run: [RUN-260](../run/run-20261118-260-rust-common-settings-runtime.md)
- Attempt: `1`
- Parent Feature: [FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md)
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Surface: backend, common runtime packaging and existing settings consumers
- Execution Profile: backend-product
- Surface Lane: core/transaction → adapters/consumers → packaging/docs
- Required Evaluators: contract, functional
- Created: `2026-11-18`
- Updated: `2026-11-18`

## Source Set And Goal

Implement the approved Feature and [selected contract](../project/rust-common-settings-cutover-contract.md).
Its exact seven operations, closed frame/flat-value/codec schemas, validation and
error/readback order, inherited writer descriptor/lifetime, atomic transaction,
receipt/capability/discovery, target and40-second deadline are the writing/build
contract. Existing current settings/storage/terminal/architecture/privacy owners
remain binding outside the named cutover. User approved actual implementation,
not installation, live-service changes or Git publication.

Run260 implementation refinement: a fixed `json.measure` syntax callback
reconstructs the former Terminal control envelope with the same Python JSON/UTF-8
encoding. Rust still owns its128KiB admission and terminal rules. This retains
large/nonfinite/surrogate refusal order discovered by actual differential checks,
with no new file/command capability. Input-only `surrogate-string` nodes and
arbitrary-decimal conversion avoid losing invalid Unicode or readable large hex
integers at the private transport. Terminal identity also receives trusted
host package/original data paths, preserving the existing install/link boundary.

## In-Scope Implementation

1. Add a common Rust preferences module with separated flat-value/framing and
   semantic/transaction responsibilities. Reuse terminal path/value validation;
   preserve existing terminal control/stream/helper/manage modes and payload.
2. Extract unchanged TOML serialization plus lossless iterative flat-value codecs
   under foundation; retain Python TOML and OS zone syntax/platform duties only.
   Add neutral common child transport, strict receipt/capability checks and a
   bounded lifecycle with callbacks, concurrent stderr drain and explicit reap.
3. Extend existing operation-lock lifetime to expose/reuse its inherited fd;
   route common/terminal preferences facades through Rust. Preserve other helper
   callers and common-outside/terminal-inside-lock readback.
4. Preflight required common executable before backend startup writes; map
   unavailable to503 without presentation-default success. Keep unrelated CLI,
   public preferences/terminal shapes, auth and consumer notifications intact.
5. Build common executable/manifest without Node/models; add platform wheel
   inclusion and frozen backend assets/final-sign digest reconciliation. Existing
   source/installed/runtime privacy and binary provenance checks still apply.
6. Differentially characterize old/new with synthetic input, then test leases,
   races/failures/cancellation/large/deep values and producer/consumer paths.
   Freeze candidate and obtain independent data/concurrency omission challenge.
7. Verify actual source/wheel/frozen/native artifacts and existing browser settings
   workflow, record resource and minimum-compiler limits, update owning docs and
   close task-owned scratch only after preserved evidence and process cleanup.

## Out Of Scope

No DB/schema/ingestion/model/VT rewrite, other settings-store migration, UI design
or feature admission, user source collection/model download, default service/job
actions, installed-app replacement, deployment or commit/push. Native177's own
pending window evidence is not closed by this Feature.

## Surfaces And Lane Evidence

| Lane | Owning paths and dependencies | Evidence/evaluator |
| --- | --- | --- |
| core | `rust/`, foundation codec/operations; first | exact bytes/types/order, Rust tests, inherited fd and adversarial protocol; contract/functional |
| adapters | foundation preferences/transport, terminal settings, app startup/errors and direct consumers; after core | existing and differential API/startup/schedule/reading cases, origin/token and no side effects; contract/functional |
| delivery/docs | common builder/Hatch hook, PyInstaller/desktop builder and owners; after stable core/bridge | receipt/wheel/frozen final bytes, isolated app checks and current facts; contract/functional |

No visual layout or frontend behavior is intentionally redesigned. Existing
browser/native interaction checks are required consumers, with evidence phases
and scope explicit; visible changes would require design/interaction routing.

## State And Contract Preservation

- Read/default/preflight creates no settings/data/cache/service. Startup alone
  uses the exact missing-file predicate and existing onboarding correction.
- Preserve corrupt/future files, unknown typed/order values, error precedence,
  current common versus terminal file/size checks and all seven field predicates.
- Parent owns mutex/flock through child reap; inherited fd is never unlocked by
  child. Recovery/source/sync/helper owners retain the same shared lock semantics.
- Before publish, failures preserve old bytes; after possible publish, report
  commit uncertainty and require readback, without replay or automatic rollback.
- Runtime absence/mismatch/deadline is unavailable; no Python normal-writer
  fallback and no false saved/default presentation. Existing preferences errors
  retain their existing recovery UI and messages.

## Acceptance Mapping And Evaluation

| Feature points | Required witnesses |
| --- | --- |
| 1–2 | frozen baseline/candidate full-flow map, exact differential read/default/common+terminal save, byte serialization and rejected values; helper/other-store preservation |
| 3 | real outer-lock/two-thread/two-process and child/codec/parent-death/reply-loss/rename/fsync fault cases; safe temp cleanup/readback |
| 4–5 | strict protocol/capability/receipt/target and source/wheel/frozen resolution; absent Node/Terminal/model/cache; timeout and unavailable refusal before startup writes |
| 6 | settings/onboarding/template/time-zone/schedule and CLI/API/auth consumers with isolated synthetic roots; no user jobs/data effects |
| 7 | actual locked builds/tests, independent omission review/repair, browser and final packaged/native save/reopen, timing/resource observations and honest MSRV/platform gaps |

Run targeted checks first, then required privacy/full Python and relevant
Rust/build/asset checks. No test alone establishes whole-backend parity. Record
source/artifact/native/physical scope separately, and preserve unperformed gates.

## Open Blockers

None at implementation entry. Unexpected material scope/contract issues follow
normal governed routing; routine implementation and necessary compatible
dependent fixes are within this approval.
