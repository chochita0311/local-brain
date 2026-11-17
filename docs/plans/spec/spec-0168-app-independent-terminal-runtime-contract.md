# SPEC-0168: App-Independent Terminal Runtime Contract

## Metadata

- ID: `spec-0168`
- Status: `approved`
- Run: [RUN-248](../run/run-20261112-248-app-independent-terminal-runtime-contract.md)
- Attempt: `1`
- Parent Feature: [FEAT-0168](../feature/feat-0168-app-independent-terminal-runtime-contract.md)
- Parent PRD: [PRD-0030](../prd/prd-0030-macos-terminal-work-area.md)
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Surface Lane: contract; read-only backend/integration/infra; docs
- Required Evaluators: contract
- Created: `2026-11-12`
- Updated: `2026-11-12`

## Source Set

Human explicitly approves completing both created Features. [FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md)
and its [core/host contract](../project/rust-core-and-host-contract.md) passed Run247.
Current evidence is terminal runtime/manager/processes/ownership/settings/CLI,
desktop host/build/backend.spec/tauri config and terminal/desktop/storage/privacy
policies. Actual Node24.15.0 arm64 reports modules137/N-API10; optional engine lock
pins node-pty1.1.0/headless6/serialize0.14/unicode11-addon0.9. Official
[Node24.15 platform/build matrix](https://github.com/nodejs/node/blob/v24.15.0/BUILDING.md)
and [Tauri resources](https://v2.tauri.app/develop/resources/) inform packaging.

## Implementation Goal

Deliver [App-Independent Terminal Runtime Contract](../project/app-independent-terminal-runtime-contract.md)
with exact scope/label/path/manifest/helper/management/lifetime and adverse-case
rules. This Feature establishes a target contract, not a packaged runtime or
actual Quit/sleep/stop test.

## In-Scope Behavior

- Keep selected Quit/sleep retention and shutdown termination with existing visible
  New, Hide/Open, scoped ×,32 records/4 panes and memory-only/no-replay semantics.
- Fix portable bundled Node/manager/helper resources, verified private immutable
  runtime payload, state/identity/build correlation and explicit lazy preparation.
- Fix full configured scope and current path/launchd label derivation, known
  legacy management/unsupported identity, locks and destructive confirmation.
- Fix Python-independent process-snapshot schema, bounded asynchronous Node use,
  positive ownership and failure semantics.
- Fix app-less management, cache/update/remove/rollback and actual later evidence gates.

## Out-Of-Scope Behavior

No process/binary/manager/helper implementation, artifact download/build, user
service start/stop, app install/update/remove, new GUI/group/status or HTTP/WS
authentication implementation. No login/root agent, remote, transcript/VT restore,
automatic shell recreation or public release. App access remains separate parent C-02.

## Affected Surfaces And Lanes

| Lane | Responsibility / order | Evidence |
| --- | --- | --- |
| contract | First: target manifest/scope/helper and lifetime/management decisions | target owner, source predicates, state/adverse-case tables; contract |
| data/contract | Private deployment/control metadata owner/schema/atomicity/retention and backup exclusion; no data writes in this Run | runtime metadata owner table and unknown-version refusal; contract |
| backend/integration/infra | Read current Node/Python/helper/launchd/CLI and package exclusions; follow core contract | field/callsite map, existing locks/options, exact versions and platform declarations; contract |
| docs | After contract: Feature/PRD/phase plan/index/Run/evaluation and artifact hygiene | links/catalog, unchanged code/current-owner bytes; contract |

## State And Interaction Contract

Separate process lifetime from view selection/hide/OS minimize and input connection.
No screen change in this Run. Actual app-only read/list/settings must remain
non-starting; valid bundle enables an explicit first-New offline preparation,
not page-open installation. Failures/unknown do not disappear into empty state.

## Data And Contract Assumptions

Use existing data/cache owners and transient per-user GUI launchd domain. Store
only private installation/scope/identity/control metadata, never raw terminal
commands/output/environment/credentials or VT. New scope/payload metadata is
internal protocol2 deployment state, not a DB/schema/group persistence change.

## Contract Surfaces

- Producers: future builder/installer, Rust core/helper, manager protocol2.
- Consumers: both web/app host adapters, Node processTable, exact-scope management
  CLI, storage cleanup/migration and manual app replacement.
- Source-of-truth: target runtime contract; core contract owns host protocol;
  current policies/code still describe actual delivery.
- Stale checks: frozen Python cannot be an interpreter helper; `.app`/checkout
  paths cannot own a surviving manager's executable/helper; missing receipt or
  socket/PID is not proof that old descendants have ended.

## Acceptance Mapping

| Feature guarantee | Concrete target / review |
| --- | --- |
| Per-action lifetime and actual wake/relaunch | Lifetime Transition Table, bound to actual liveness/unknown, not continuous sleep computation |
| Executable/helper available without app | Bundle And Stable Paths, atomic payload preparation and app-less launcher |
| Scope/domain/lock/generation/birth/payload | Scope And Identity and Artifact Manifest; same/different/mismatch/collision cases |
| Manager vs terminal/job / partial failure | Helper And Termination plus transition/edge cases; no PID-only or empty-list proof |
| Update/restart/cache/remove | Retention Update And Removal; scope snapshot, stop confirmation and protected unknown state |
| Privacy/no persistence/replay | Storage metadata allowlist; no shell/VT restoration after loss/reboot |

## Evaluation Focus

Trace an app-only supported installation from explicit New through copied absolute
payload/Node/helper paths and same-generation management after app removal. Review
same data/different cache, hash prefix collision, incompatible/legacy/unknown,
PID reuse, helper EPERM/timeout, changed confirmation, partial descendants, interrupted
payload copy, actual sleep/force-Quit, cleanup/update/remove and current CLI semantics.
Contract examples/fields/predicates must be complete; none of these scenario
reviews is a claim that actual future executables were run.

## Open Blockers

None for contract completion. Release tarball/signature/ABI/payload build, actual
native Quit/sleep/physical input and product access/group/status/results remain
explicit later evidence/Feature gates; no requested deployment is left half performed.

## Continuity Notes

- `2026-11-12`: Run248 starts only after the required Run247 contract passed.
  Primary performs sequential roles under the existing batch approval.
