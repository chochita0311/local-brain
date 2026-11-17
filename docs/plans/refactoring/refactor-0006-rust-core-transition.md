# REFACTOR-0006: Rust Core Transition

## Purpose

Track the approved shared Rust core direction from explicit contracts to bounded
product slices without losing existing data/GUI/terminal semantics. Parents are
[PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md) and the separate
[app terminal PRD-0030](../prd/prd-0030-macos-terminal-work-area.md).
Contracts own decisions; this plan owns phase/verification/handoff boundaries.

Current position: Phase0 contract readiness is complete in Run247/248 with
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
evidence; Feature177 remains in-loop because its latest actual-window UI packet
has not passed. Earlier native-window passes do not close that later gate.
The user has checkpointed this work and selected Phase3 as the next-session
priority. The completed Rust scope is still Terminal control, not the whole
Python application backend.

## Refactor Type

Structural and Interface transition. First contract phase changes no runtime.
App Quit/sleep retention, native admission, new folder groups/status/workspace are
intentional product deltas owned by PRD-0030, not hidden inside a parity claim.
Migration behavioral parity: **Provisional** for the whole backend; the selected
Terminal control slice has bounded executable parity evidence in Eval0167.
No merge-safety judgment is requested.

## Scope

Current baseline is the repository source and existing uncommitted planning input
at Run247 start, HEAD `b31f6c4a5b84d5eeb4b3e908e3fb84a3f7dd3390`.
First target: terminal control with one Rust library/runtime binary, shared host
adapters and unchanged Node/xterm/optional Python/model/DB contracts. Entire later
admitted feature parity remains PRD-0029's obligation; no timeline is promised.

## Non-Goals

No blanket Python removal, UI framework/VT/model rewrite, schema migration,
suspended-feature return, global service registry/login agent, implicit job stop,
app deployment/publication or warm engine replacement. These contract Runs do not
implement later phases or claim their tests passed.
Retained Python HTTP/CLI/settings adapters describe the current first-slice
boundary; they do not mark the remaining application-backend migration complete.
Optional model-worker retention is a separate contract decision, not a promise
to rewrite every Python dependency.

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

## Validation Gates

Before any migration parity/completion claim, freeze actual baseline/candidate and
dependencies/configuration/guidance; trace entry→rules→store/write→outputs→all consumers,
and include unknown/error/retry/concurrency/side effects. Required independent challenge
and re-review gates follow the selected refactor method and repo risk rules.
For Phase0, only contract completeness is judged; primary source checks are not an
independent code review or proof of future runtime behavior. Tests/format alone do not settle parity.

## Intentional Deltas

App terminal admission and app-independent Quit lifetime are selected product changes.
Manager protocol2/helper/payload and new internal host protocol are explicit interface
deltas; public terminal shapes/CLI/data semantics are preserved. Group/cwd/status changes
must be locked in their future foundations, not inferred from Herdr or this phase plan.

## Risks / Open Questions

No blocking question remains in the first two approved contract boundaries.
Final signed payload/tree/ABI/source integrity and native HTTP/WS admission pass.
Rust/Tauri now declare1.90 and compile with available1.99.1; the minimum compiler
itself is untested. Actual native-window lifecycle is covered in Run253; native
IME/physical input/sleep, minimum-OS hardware and resource budgets remain gates.
Common-browser group/status evidence does not
prove native physical interactions or a speed advantage.
Machine/process/path/version mismatches and helper loss must remain recoverable failures.

## Exit Goal

First two foundation results are concrete enough for downstream Spec without new
ownership decisions. Full Rust/app product completion requires later accepted slices;
this contract milestone does not make a runtime-parity or safe-to-merge claim.

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

Next-session target, confirmed by the user on 2026-11-17: begin Phase3 for the
remaining application backend. Start with the complete feature/consumer inventory
and dependency order, then create the bounded Feature/Spec handoff for the first
coherent family under PRD-0029. No Phase3 implementation or child execution
Features are delivered by this checkpoint. The outstanding Feature177 actual-window
packet retains its own acceptance owner and is not silently waived or declared
passed by this sequencing decision.

Phase3 has not started. Remaining Python owners include Session ingestion and
normalization, database/schema/repositories, Context/source readers, Usage,
retrieval/models/indexes, work organization, settings' generic TOML writer and
application jobs/feature assembly. Each admitted family needs its own complete
source-to-target query/write/error/side-effect/CLI/GUI inventory and approved
Feature boundary. No new native framework, blanket Python removal, suspended
feature return or data migration is inferred from this Terminal delivery.
