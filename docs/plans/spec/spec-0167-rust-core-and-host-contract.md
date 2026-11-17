# SPEC-0167: Rust Core And Host Contract

## Metadata

- ID: `spec-0167`
- Status: `approved`
- Run: [RUN-247](../run/run-20261112-247-rust-core-and-host-contract.md)
- Attempt: `1`
- Parent Feature: [FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md)
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Surface Lane: contract; source inspection in backend/integration/infra; docs
- Required Evaluators: contract
- Created: `2026-11-12`
- Updated: `2026-11-12`

## Source Set

- Human approval: complete the two created Features, including their recommended boundaries.
- Parent Feature/PRD and [Terminal](../../policies/project/terminal.md),
  [Architecture](../../policies/project/architecture.md),
  [Desktop/settings](../../policies/project/desktop-app-and-settings.md),
  [Storage](../../policies/project/installation-and-storage.md),
  [Availability](../project/feature-availability.md).
- Current producers/consumers: terminal runtime/web/CLI/manager/helper/settings,
  foundation preferences/operations, app assembly/lifecycle, desktop host/build/locks.
- Versioned dependency manifests/VCS provenance from the existing local Cargo source cache,
  host Cargo.lock and actual Rust1.99.1/aarch64 toolchain; official
  [Rust Command](https://doc.rust-lang.org/1.99.1/std/process/struct.Command.html),
  [Tauri sidecar](https://v2.tauri.app/develop/sidecar/) guidance.

## Implementation Goal

Deliver [Rust Core And Host Contract](../project/rust-core-and-host-contract.md)
as the normative target for the first Rust terminal slice, and
[Refactor0006](../refactoring/refactor-0006-rust-core-transition.md) as its phase/parity
tracking owner. These are target contracts, not claims that the current Python
runtime or desktop terminal has changed.

## In-Scope Behavior

- Fix current/first-slice/later/suspended feature ownership without reducing long-term parity.
- Choose one Rust library and one executable boundary; fix Python web/CLI and Tauri
  consumption, one-shot/stream/helper modes, requests/results/errors and cancellation.
- Preserve the current shared Python settings writer while Rust owns terminal
  value interpretation/validation; document lock ordering, revision and response-loss rules.
- Fix old/new manager admission/management, schema/IDs/rollback, build/dependency/license
  constraints and future verification/performance gates.
- Name the exact separate runtime/access/group/status prerequisites and stop conditions.

## Out-Of-Scope Behavior

No executable Rust crate, dependency install/upgrade, port, DB migration, new product
UI, app build/install, user service manipulation, performance run or publication.
No new backend feature reactivation or VT/model-engine rewrite.

## Affected Surfaces

Target contract/transition plan, this Spec, Feature/PRD status and handoff,
Run/evaluation, Plans Index/catalog. Runtime source and current behavior policies
are evidence inputs and remain unchanged.

## Surface Lanes

| Lane | Order / responsibility | Evidence / evaluator |
| --- | --- | --- |
| contract | First: complete decisions and typed operation/lifecycle/writer ownership | source-to-target maps and adverse cases; contract |
| backend/integration/infra | Read only: trace actual callers, entrypoints, locks, helper, host and manifests | source locators, dependency declarations and version observations; contract |
| docs | After contract: phase plan, trace/status/index consistency | artifact ownership, links/catalog and preserved input bytes; contract |

## State And Interaction Contract

No screen changes. Current absent/running/incompatible/unknown/unclean/failed states
remain distinct; read-only operations do not install/start. Future adapters preserve
backpressure/ack/lease/cancellation, errors and selected lifetime. Contract status
`accepted` does not represent an implemented or measured product state.

## Data And Contract Assumptions

First slice changes no DB schema/IDs, model/index, original/Usage values or common
settings format. The existing Python common writer remains the sole file commit
owner in this slice. Core accepts only bounded typed snapshots, never a second
independent TOML writer or app credential forwarded into shell environment.

## Contract Surfaces

- Producer: future `localbrain-core` and `localbrain-runtime` protocol1.
- Consumers: current web/CLI adapters and packaged app backend/native management adapter.
- Generated artifacts: later Rust binary/lock/license/runtime manifests; none generated here.
- Source-of-truth owner: target contract for migration decisions; existing policies/code
  for current runtime; Refactor0006 for phases/parity; FEAT-0168 for payload lifetime.
- Stale check: current host `rust-version=1.77.2` is not proof that locked Tauri
  can build on it. Record actual dependency requirements and avoid a lower-MSRV claim.

## Acceptance Mapping

| Feature acceptance | Concrete contract target / witness |
| --- | --- |
| Inventory and full later parity | Current And Target Ownership table, including current web-only and suspended features |
| Shared core/host topology | Package And Call Ownership; diagram and HTTP/CLI/native/manager-helper paths |
| Terminal operation/compatibility | Host Protocol, Source To Target Map, compatibility and adverse-case table |
| Concrete Python/Tauri access | Same executable through private stdin/stdout; persistent child per stream; no app-only business copy |
| Writer/revision/rollback | Shared Settings Writer and Compatibility And Rollback; lock/response-loss/retry predicates |
| Dependencies/toolchain/license | Build And Dependencies table with lock/source observations and explicit unperformed build gate |
| Performance distinction | Measurement Contract separates input/paint/control and total subtree, inherited web limits and unmeasured native baseline |

## Evaluation Focus

Check every Feature clause against actual target text, operation and role ownership,
source predicate and distinguishing cases: invalid bool/path/empty defaults,
unknown TOML, stale revision, same-key different create, unsupported wire, wrong
generation, helper failure, late ack/claim, disconnect and existing manager.
Check that no current-runtime claim or future refactor parity is implied by a docs pass.

## Open Blockers

None for this bounded contract. Runtime implementation, binary/build integrity,
actual app/input/performance and future feature boundaries remain explicit downstream
acceptance, not unresolved choices inside this contract.

## Continuity Notes

- `2026-11-12`: approved for Run247 from the human-approved Feature. Primary performs
  sequential spec/contract/update/evaluation roles; no independent runtime proof is claimed.
