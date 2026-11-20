# REFACTOR-0006: Rust Core Transition

## Purpose

Track the approved shared Rust core direction from explicit contracts to bounded
product slices without losing existing data/GUI/terminal semantics. Parents are
[PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md) and the separate
[app terminal PRD-0030](../prd/prd-0030-macos-terminal-work-area.md).
Contracts own decisions; this plan owns phase/verification/handoff boundaries.

Final target clarified on2026-11-18: remove Python from the backend runtime,
including HTTP/CLI/template, syntax/zone and model-worker dependencies. Passed
Terminal/settings increments are intermediate. The
[current runtime exit conditions and approved apps layout](../project/python-free-backend-target.md)
supersede interpreting earlier Python retention as final completion. The
settings latency regression is resolved by Run261's matched packaged comparison;
its original measurements remain historical evidence.
The [goal/layout reconciliation log](logs/2026-11-18_refactor-0006_python-free-target.md)
preserves the change from earlier slice boundaries without rewriting their evidence.

[FEAT-0180/Run261](../run/run-20261118-261-python-free-backend.md) passes the
user's approved full backend removal and apps layout under
[Eval0177](../evaluation/eval-0177-python-free-backend.md). All 249 Python product
modules and obsolete interpreter packaging are retired; actual Rust 1.90 workspace 412,
app/API builds, native-window16, browser26, publication-fault6 and Python-denied
runtime checks pass. All four final measured HTTP surfaces improve on pure Python
and the child intermediate. This closes Phase3C's implementation/delivery target,
with platform, model, physical and strict-parity limits retained below.
The [functional stability follow-up](logs/2026-11-20_refactor-0006_functional-stability-merge-check.md)
owns the later parity repairs, complete dashboard entry and separately staged
verified release. [Run261](../run/run-20261118-261-python-free-backend.md#user-visible-stability-follow-up)
links the dated checkpoints without replacing the original phase evidence.

Earlier phase results: Phase0 contract readiness is complete in Run247/248 with
[Eval0163](../evaluation/eval-0163-rust-core-and-host-contract.md) and
[Eval0164](../evaluation/eval-0164-app-independent-terminal-runtime-contract.md).
The Phase1 Terminal Rust slice passes [Run251/Eval0167](../evaluation/eval-0167-rust-terminal-runtime.md).
Native implementation, final package and actual host checks are delivered in
[Run252/Eval0168](../evaluation/eval-0168-native-terminal-integration.md); its
required window gap is closed by [Run253/Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md).
Native IME automation remains unaccepted. [Run254](../run/run-20261113-254-persistent-terminal-workspaces.md)
adds the approved named/mixed-folder persistent workspace and new-zsh status
increment without changing the Rust/Node payload. The common workspace
passed [Eval0165](../evaluation/eval-0165-terminal-workspace.md); its New/version
recovery passes [Eval0166](../evaluation/eval-0166-terminal-reopen-recovery.md).

The later shared header, pane actions and state indicators pass their
[Run255–257 owners](../design/terminal-workspace-design-plan.md). Latest
[Run258/Eval0174](../evaluation/eval-0174-terminal-activity-and-background-rail.md)
delivers prompt/program marks and inline Background with browser/package/backend
evidence; Feature177 retains its separate Run258/Eval0174 acceptance owner. Run261 now
supplies a fresh16-check native-window pass, including title, inline Background
and focus states; it does not silently change that separate Run's acceptance.
The user checkpointed this work and selected Phase3 as the next-session priority.
Phase3 resumed on 2026-11-17 with the [backend inventory](../project/rust-backend-migration-inventory.md)
and the common-settings cutover Feature. The user approved that contract-only
boundary; [Run259/Eval0175](../evaluation/eval-0175-rust-common-settings-cutover-contract.md)
passes [FEAT-0178](../feature/feat-0178-rust-common-settings-cutover-contract.md).
The next [implementation FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md)
passes [Run260/Eval0176](../evaluation/eval-0176-rust-common-settings-runtime.md).
Common rules/normal commit, source/platform-wheel/frozen delivery and actual
native Settings save/reopen/restart pass with independent challenge and informed
repair checks. At Run260 closure Phase3 remained partial, with retained Python/Node and measured
latency. Run261 replaces that Python runtime and resolves the measured common-flow
regression; Node and platform/physical/model/Terminal177 limits stay explicit.

## Refactor Type

Structural and Interface transition. First contract phase changes no runtime.
App Quit/sleep retention, native admission, new folder groups/status/workspace are
intentional product deltas owned by PRD-0030, not hidden inside a parity claim.
Migration behavioral parity: **Unknown/Provisional** for an exhaustive whole-backend
audit. Eval0177 accepts Python-free implementation/delivery with bounded
source-to-target, failure, differential and actual runtime evidence plus named
interpreter-removal deltas. The earlier Terminal slice retains Eval0167's scope.
No merge-safety judgment is requested.

## Scope

Current baseline is the repository source and existing uncommitted planning input
at Run247 start, HEAD `b31f6c4a5b84d5eeb4b3e908e3fb84a3f7dd3390`.
First target: terminal control with one Rust library/runtime binary, shared host
adapters and unchanged Node/xterm/optional Python/model/DB contracts. Entire later
admitted feature parity remains PRD-0029's obligation; no timeline is promised.

Phase3 inventory baseline is the initially clean current source
`e6958df0813b8652074c68a73ac61a8b551e59a8`, separate from the original Run247
baseline above. Its first handoff is planning-only; comparison candidates must be
frozen separately when their actual implementation exists.

## Non-Goals

Earlier first slices excluded blanket Python removal; the user's clarified
final backend target now requires it. The remaining Python runs current
build, check and QA tools and their tests outside the shipped runtime. No automatic UI framework/
VT/model replacement, schema migration,
suspended-feature return, global service registry/login agent, implicit job stop,
app deployment/publication or warm engine replacement. These contract Runs do not
implement later phases or claim their tests passed.
Retained Python HTTP/CLI/settings adapters and model execution describe the
earlier intermediate implementation. Run261 replaces them natively; no permanent
Python model-worker exception is assumed by the final target.

## Invariants

- Preserve original IDs/source/revision/Usage/model/index and same data/cache/privacy owners.
- Core independent of Tauri; host adapters do not duplicate business rules.
- Preserve common settings one-writer lock/revision/unknown-field transaction.
- Preserve max4 panes/max32 records, fonts/IME/lease/checkpoint/bounds, New/Hide/Open/×,
  explicit scope/identity-safe termination, no replay/transcript and unknown states.
- Selected normal Quit/sleep retention differs from update/restart/shutdown; actual
  host evidence remains required. Existing web/native and supported/unverified states stay distinct.

## Planned Work

### Phase 0: Contract readiness

- Goal: fix [core/host](../project/rust-core-and-host-contract.md) and
  [independent runtime](../feature/feat-0168-app-independent-terminal-runtime-contract.md) boundaries.
- Why this grouping: runtime/helper/payload ownership must be known before adapting both hosts.
- Guardrails: [FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md) and
  [FEAT-0168](../feature/feat-0168-app-independent-terminal-runtime-contract.md) remain separate sequential Runs; no product code/services.
- Targets: typed calls, writer/lock, compatibility, dependency/build, payload identity, lifetime/management.
- Validation: source/consumer maps, adverse-case review, versions and contract/artifact checks.
- Exit gate: both contract evaluations pass; no unresolved first-slice ownership choice.

### Phase 1: Runtime and host implementation

- Goal: actual Rust control/helper through existing web/CLI, then packaged app under its access contract.
- Why this grouping: executable/wire/settings/helper and legacy management must work together before native admission.
- Guardrails: new product Feature boundaries required; no absorption of unresolved access/group/status foundation.
- Targets: rust workspace, Python adapters, Node protocol2, payload builder/management and native registration.
- Validation: locked Rust/ABI/package and differential settings/IPC/CLI/error tests, real PTY/launchd/WS/host checks and resource baseline.
- Exit gate: frozen old/new full-path evidence satisfies the scoped product and its intentional deltas; no inferred whole-repo parity.

Terminal control is implemented and passed. Eval0167 maps original scope/service/
process/settings/IPC/CLI consumers to Rust and the retained host/Node boundaries.
The final frozen core recheck and real fault/race/PTY cases support that bounded
result. Native registration/package/host lifecycle are implemented; Run253 supplies
the actual window close/reopen witness missing at Run252 closure. Physical/native
input acceptance remains a separate limit.

### Phase 2: Terminal-purpose product area

- Goal: deliver the selected one-window named workspaces/tabs/max4 and truthful state overview, including the user-approved mixed-folder/empty-group persistence correction.
- Why this grouping: group/state contracts precede the product's frame and attention interactions.
- Guardrails: [Terminal design plan](../design/terminal-workspace-design-plan.md) owns UI phasing; preserve recovery/input/lifetime and other screens.
- Targets: separately approved group/status/access foundations and compact workspace product Features.
- Validation: contract/design/functional/interaction, actual packaged app IME/minimize/Quit/sleep, same execution reopen and unknown-source states.
- Exit gate: actual product evidence accepted with native/physical/long-soak limits explicit.

### Phase 3: Remaining Rust common flows

- Goal: port other admitted web/app/CLI families without leaving hidden feature gaps.
- Why this grouping: Session/Context/Usage/search and common-writer transactions require their own complete data contracts.
- Guardrails: feature inventory and approved boundaries first, no automatic suspended-feature restoration.
- Targets: parent PRD's later storage/ingestion/model/GUI/compatible-delivery candidates.
- Validation: frozen source-to-target queries/writes/side effects/failure/CLI/GUI and actual delivery evidence.
- Exit gate: each accepted slice lists remaining parity debt; full migration requires complete inventory coverage.

The [Phase3 inventory](../project/rust-backend-migration-inventory.md) accounts for
all 246 Python modules/26 package-or-root groups, 128 explicit route registrations
(including conditional branches), CLI/module paths, jobs and delivered consumers at its frozen
source. It distinguishes current common flows, development-web app gaps,
suspended packages and parked experiments; source census is not per-flow parity.

#### Phase 3A: Common settings cutover contract — passed

- Goal: fix the single `settings.toml` transaction and Terminal-independent common runtime boundary before the first remaining backend port.
- Why this grouping: general and terminal saves share one revision/lock/file; the current host adapter depends on the optional Terminal runtime and cannot become a foundation dependency unchanged.
- Guardrails: human-approved [FEAT-0178](../feature/feat-0178-rust-common-settings-cutover-contract.md) was contract-only. No product code, DB migration, source/search/model-store port, native admission or service action.
- Targets: normal writer vs retained restore owner, raw TOML/type/format parity, parent/child/outer-lock behavior, closed common host errors, source/wheel/frozen runtime delivery and refusal/rollback.
- Validation: complete existing writer/consumer map; exact type/default/missing/unknown cases; lock/crash/lost-response/recovery contract cases; independent-of-Terminal packaging and dependency checks; docs/catalog/privacy.
- Exit gate: met by Run259/Eval0175 for the bounded contract. [Selected owner](../project/rust-common-settings-cutover-contract.md) fixes inherited lock, ordered typed codec, normal Rust commit and common runtime delivery/refusal. Python syntax/OS-zone adapters and recovery remain explicit; no future runtime pass is inferred.

#### Phase 3B: Common settings implementation — passed

- Goal: deliver existing general/Terminal settings read/save through common Rust semantic and normal-commit rules on the first macOS14/Apple Silicon target.
- Why this grouping: one settings file/revision/lock requires complete common and Terminal entrypoints plus a common executable that base source/wheel/app can actually consume.
- Guardrails: [FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md) received human implementation approval on2026-11-18 and owns Spec0179/Run260. Retain Python syntax/OS-zone adapters and recovery/shared helpers; no other settings-store/DB/UI migration or user service/app replacement.
- Targets: core rules/commit, inherited parent lease/lifetime, neutral host/codec channel, current consumer/error/startup wiring, independent source/platform-wheel/frozen receipt and owner docs.
- Validation: frozen old/new differential values/errors/bytes/readback, real race/crash/deadline/recovery cases, independent data/concurrency code challenge, source/wheel and actual packaged/native Settings behavior; report retained debt and resource/MSRV limits.
- Exit gate: met for FEAT-0179 in Run260/Eval0176. Actual old/new277 cases, lock/fault/deadline/consumer checks, installed base wheel and final signed native Settings save/reopen/restart pass. Full Python1,731 run/49 optional skips and Rust11 pass. Minimum-version/platform/physical and whole-backend evidence remains bounded; contract PASS alone was not used to close implementation.

#### Phase 3C: Python-free backend and application layout — passed on tested host

The user's explicit end-to-end implementation approval selects
[FEAT-0180/Spec0180/Run261](../run/run-20261118-261-python-free-backend.md), rather
than requiring a new approval for each implementation packet. The approved
`apps/api`, `apps/web`, `apps/desktop` and shared `crates/` moves are applied.
The user's2026-11-19 follow-up shortens the shared directories to `crates/core`,
`crates/runtime` and `crates/models`, retaining Cargo package/import/binary names.
Current generator/path consumers and native builds are renewed in
[Run261's follow-up](../run/run-20261118-261-python-free-backend.md#crate-directory-and-web-alias-follow-up).
Ordinary requests call common Rust functions in a persistent native backend;
Tauri owns window/OS/backend lifetime, and the independent Node PTY/VT engine
retains its own lifecycle. Native storage/recovery, source/Session/Usage/Context,
retrieval/models and other admitted service families are integrated. Suspended
features and experiments retain their original admission and private ownership.

The249-module actual dirty baseline and all175 non-product Python/spec consumer
dispositions have private evidence owners. Native replacements precede removal
of Python application code, old runtime tests and PyInstaller/wheel/bridge
packaging. Build/test scripts and explicit legacy research references remain;
they do not provide product fallback. The current inventory maps original
families to actual native owners and scoped evidence, without claiming an
assertion-for-assertion proof from source census.

[Run261/Eval0177](../evaluation/eval-0177-python-free-backend.md) closes the
implementation/delivery exit: actual Rust 1.90 formatter, warning-free all-target
Clippy and workspace 412/0fail/7ignored; final native web/CLI/app, sealed artifacts,
actual16-check native window,26-check Chrome, six publication faults and Python
execution/library-denial controls pass. Independent whole-candidate semantic and
retirement reviews and informed repair confirmations remain distinct from builders.
The final matched HTTP comparison improves all four measured medians/p95s. Shared
metadata/preferences use exact original POSIX fsync, with independent Terminal
writers, revisions, leases and readback unchanged. Final identity/owner/privacy
and cleanup receipts retain the tested boundary. Exhaustive strict parity and
parent platform/physical/resource/model-quality claims remain qualified.

The migration's first inference samples had mixed results and unequal first-call
verification boundaries. The profiling and scoped optimization later delivered
token ID reuse and CPU mask-buffer ownership. Successful vectors, search ranks,
source locators and index reuse matched on the checked inputs. Tokenization
improved on both devices. Whole-call results depend on the load and allocator
conditions. Broader speed and real large-model quality remain separate checks.
[Paired measurements](../run/run-20261118-261-python-free-backend.md#embedding-optimization-with-preserved-results) · [Model tools](../../policies/project/development/model-tools.md#native-inference-performance)

## Validation Gates

Before any migration parity/completion claim, freeze actual baseline/candidate and
dependencies/configuration/guidance; trace entry→rules→store/write→outputs→all consumers,
and include unknown/error/retry/concurrency/side effects. Required independent challenge
and re-review gates follow the selected refactor method and repo risk rules.
For Phase0, only contract completeness is judged; primary source checks are not an
independent code review or proof of future runtime behavior. Tests/format alone do not settle parity.

## Intentional Deltas

The earlier Phase3 common-settings contract introduced an internal40-second
operation deadline and explicit unavailable503/startup refusal for a missing or
mismatched required common runtime. Its first binary wheel is platform-specific
to macOS14/Apple Silicon. These are named interface/delivery deltas approved and
tested in FEAT-0179, not old Python timing/platform guarantees.
Its retained Python syntax/OS-zone adapters were debt. Run261 replaces them and
their per-call transport with native in-process calls; that transport deadline
no longer applies to an eliminated child. Earlier per-call child/callback cost
was higher: warm-cache median read11.208ms and
save/readback41.029ms versus baseline0.036/0.485ms; empty Sessions HTML17.182ms
versus2.690ms. That increment established no speed improvement or physical/soak
budget; final packaged native performance passes the separate matched Run261
comparison in Eval0177, with no universal inference/startup/UI/resource guarantee.

App terminal admission and app-independent Quit lifetime are selected product changes.
Manager protocol2/helper/payload and new internal host protocol are explicit interface
deltas; public terminal shapes/CLI/data semantics are preserved. Group/cwd/status changes
must be locked in their future foundations, not inferred from Herdr or this phase plan.

## Risks / Open Questions

No blocking question remains in the first two approved contract boundaries.
Final signed payload/tree/ABI/source integrity and native HTTP/WS admission pass.
Rust/Tauri declare1.90; Run261 actually compiles and checks that minimum, including
the app release build. Actual native-window lifecycle is covered in Run253; native
IME/physical input/sleep, minimum-OS hardware and resource budgets remain gates.
Common-browser group/status evidence does not
prove native physical interactions or a speed advantage.
Machine/process/path/version mismatches and helper loss must remain recoverable failures.
Phase3's writer/outer-lock/TOML/format/delivery contract is selected in Run259;
its bounded executable proof passes FEAT-0179/Run260/Eval0176, including the
platform wheel and new40-second common transport failure boundary. Actual native
Settings evidence closes this slice's window requirement. Python syntax/OS-zone
adapters were debt in that increment and are replaced in Run261; settings has no
Terminal/Node setup dependency.
No contract pass is permission to migrate every store sharing its lock/serializer.

## Exit Goal

First two foundation results are concrete enough for downstream Spec without new
ownership decisions. The selected Python-free backend implementation/delivery target passes Run261.
Broader Rust/app platform, physical, resource and separate product acceptance
remain scoped; no exhaustive runtime-parity or safe-to-merge claim follows.

## Handoff to Next Track

Run247/248 own passed contract history; Run249/250 own the common workspace and
recovery. Run251/FEAT0170 passes the first Rust product slice. Run252/FEAT0171's
required window gap is closed by [Run253/Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md),
which also delivers everyday interactions without changing the runtime payload.
Run254/FEAT0173 follows with independently named persistent workspaces, different-root
tabs/panes, compact controls and host zsh startup integration; it does not migrate
another Python application family.
Technical native integration passes; native IME automation did not pass, and
physical input, VoiceOver, Mac sleep and recipient/performance limits remain explicit.

The 2026-11-17 checkpoint selected Phase3 inventory/Feature planning first and
delivered no child Feature or implementation at that time. The subsequent user
continuation delivered the [inventory and dependency order](../project/rust-backend-migration-inventory.md)
and proposed FEAT-0178; its later approval and Run259 now complete the
[common-settings contract](../project/rust-common-settings-cutover-contract.md).
The [planning handoff log](logs/2026-11-17_refactor-0006_phase3-inventory.md)
retains that earlier boundary; Run259/Eval0175 own contract execution evidence.
The later2026-11-18 approval delivers [implementation FEAT-0179](../feature/feat-0179-rust-common-settings-runtime.md)
in Spec0179/Run260 with Eval0176 PASS. Its
[implementation log](logs/2026-11-18_refactor-0006_common-settings-runtime.md)
records structural/behavioral results and explicit resource/platform limits.
The user's later approval selects the complete native host/codec/rendering,
data-family/model and Python-free delivery work in Run261. Use the current
target's runtime exit conditions and approved apps layout; prior slice passes
do not establish whole-backend strict parity. Eval0177 now accepts native
implementation and Python-free delivery. Feature177 retains its separate
acceptance owner, with fresh Run261 native-window evidence available.

The inventory's native owners and Run261/Eval0177 record scoped source-to-target
query/write/error/side-effect/CLI/GUI and delivered evidence with explicit limits. Backend
Python removal is explicit user intent; no new GUI/VT
framework, suspended-feature return or data migration follows automatically.
