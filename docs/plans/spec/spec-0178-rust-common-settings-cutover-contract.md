# SPEC-0178: Rust Common Settings Cutover Contract

## Metadata

- ID: `spec-0178`
- Status: `approved`
- Run: [RUN-259](../run/run-20261117-259-rust-common-settings-cutover-contract.md)
- Attempt: `1`
- Parent Feature: [FEAT-0178](../feature/feat-0178-rust-common-settings-cutover-contract.md)
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Surface: mixed, contract-only
- Execution Profile: foundation-contract
- Surface Lane: settings transaction, common host/delivery, consumers/handoff
- Required Evaluators: contract
- Created: `2026-11-17`
- Updated: `2026-11-17`

## Source Set

- Human approved the preceding FEAT-0178 contract-only proposal with “진행”.
- Feature acceptance points 1–7 and pass/fail checks 1–6 own this bounded outcome.
- [Existing core/host contract](../project/rust-core-and-host-contract.md),
  [Phase3 inventory](../project/rust-backend-migration-inventory.md),
  [common settings](../../policies/project/desktop-app-and-settings.md#common-settings-contract),
  [storage](../../policies/project/installation-and-storage.md),
  [architecture](../../policies/project/architecture.md) and
  [regression control](../../policies/project/change-scope-and-regression.md).
- Current `foundation/preferences.py`, `operations.py`, config, terminal
  settings/core/errors, settings/lifecycle/edition/templates, sources sync/settings,
  Usage and storage recovery; their direct shared serializer/atomic-write callers.
- Actual Python/Cargo manifests/locks and packaging paths; official Python3.11
  subprocess/TOML/fcntl and Apple flock documentation. Third-party TOML candidates
  are evidence to compare, not selected dependencies merely because cached.

## Implementation Goal

Deliver [the common-settings cutover contract](../project/rust-common-settings-cutover-contract.md)
with one complete normal writer/lock/call/value/delivery model and a bounded
downstream product Feature. The Builder here authors a contract, not runtime code.
Current Python commits and runtime availability remain unchanged.

## In-Scope Behavior

1. Trace current read/default/save/terminal/initialization/recovery producers to
   all direct API, CLI/startup, template, schedule/time-zone and shared-helper
   consumers. Record actual validation and post-write read timing.
2. Select the inherited lock-file-description handoff, including nested caller,
   child lifetime and pre/post-rename failure outcomes; preserve operations.lock
   serialization with scans/source edits/backup/restore.
3. Select a lossless ordered typed value exchange. Compare actual Python large
   integers, dates/time precision, nonfinite floats, arrays/tables and read-valid
   but write-refused input. Keep known-value business rules in Rust; declare every
   retained syntax/platform adapter rather than claiming complete Python removal.
4. Define a closed common runtime API independent of Terminal assembly, Node,
   cache or launchd, preserving existing terminal protocol/control lifetime.
5. Fix source/wheel/frozen runtime discovery/provision, package/contract/build
   refusal and rollback. Identify any new internal transport failure mode
   explicitly for downstream approval and verification.
6. Run meaningful synthetic baseline/kernel-premise probes and existing relevant
   tests where available. They establish current facts and contract feasibility;
   they do not validate an unimplemented Rust writer or packaging hook.
7. Evaluate the complete contract and stale consumer assumptions; produce a
   reviewable product Feature only after the foundation contract passes.

## Out-Of-Scope Behavior

No source/runtime/build-hook/manifest/lock changes, actual writer port, database or
other settings-store migration, UI/native admission, service/app installation,
personal data/model use, signed distribution, commit/push or executable parity.
Do not restart or evaluate the separately pending Terminal177 native packet.

## Affected Surfaces

New contract, this Spec/Run/Evaluation, approved Feature, parent/refactor/inventory
status and downstream product proposal. Existing current-behavior policies and
all code are preserved inputs. Update the old project contract only to route the
later selected cutover; retain its historical first-slice Python-writer facts.

## Surface Lanes

| Lane | Dependency and owner | Expected evidence |
| --- | --- | --- |
| transaction | first; primary as Spec/contract Builder | old-to-target map, exact predicates, ordering, shared lock and adverse cases |
| host/delivery | after transaction choice; primary | closed operations/value/codec boundaries, independent runtime package identity and refusal |
| consumers/handoff | after both; primary | complete acceptance mapping, preservation checks, contract evaluation and proposed product boundary |

## State And Interaction Contract

- Contract-only stage changes no rendered state or interaction.
- Target read/default calls do not create settings, locks, caches or services.
  First startup alone retains absent-file creation and existing-registration
  onboarding behavior; existing partial/invalid files remain untouched.
- Distinguish malformed/unsupported settings, stale revision, busy operation,
  unavailable common executable and commit uncertainty. Pre-commit failure
  preserves old bytes; possible/known post-commit failure requires readback,
  never stale replay or blind rollback.
- Preserve existing common-save readback after releasing the operation lock,
  terminal-save readback while it is held, and presentation fallback only for
  preferences errors; a missing runtime must not look like valid defaults.

## Data And Contract Assumptions

Schema1, the seven common values/defaults/exact predicates in the approved
Feature, byte SHA256 revision, unknown/retired fields, ordering and private atomic
save are binding. No database/schema/model/index change is a prerequisite.
Keep separate source TOML/search/model JSON/Context stores and retained recovery
writes. The first product is an incremental Rust semantic-rule/commit cutover;
retained Python codec/platform functions must be explicitly listed as remaining debt.

## Contract Surfaces

- Producers: common/terminal wrappers, startup and recovery, trusted host context.
- Consumers: HTTP shapes/errors/auth, raw Python compatibility, schedulers,
  Dashboard time zone, native startup, templates and existing CLI/build entrypoints.
- Generated outputs: catalog plus future common runtime manifest/wheel/app receipt
  rules; no executable artifact is generated by this foundation.
- Owner: new project-specific common-settings contract. Current policies own
  present behavior; the existing terminal/core contract still owns its first slice.
- Stale-assumption check: no foundation→terminal import; no reentrant reopened
  flock, i64-only unknown JSON, inferred whole-settings Rust completion, terminal
  payload prerequisite or unsupported-target wheel.

## Required Evaluators

- Contract: required, sequential primary review; explicitly same-author.
- Design/functional/UX: not applicable to this contract-only change. Later code
  must have contract/functional and applicable browser/native interaction evidence.
- Independent code challenge: due for later data/concurrency implementation, not
  claimed or replaced by this source/contract review.

## Acceptance Mapping

| Feature acceptance | Required contract evidence |
| --- | --- |
| 1 | current/target owner and consumer maps, normal Rust commit vs retained codec/recovery |
| 2 | inherited operations.lock lease, nesting, close-not-unlock, crash/cancel and existing competing operations |
| 3 | ordered tagged values, exact baseline codec/platform provider, read/write distinctions and callback errors |
| 4 | exact values/defaults/schema/revision/order, read/init/save timing and atomic transaction |
| 5 | common runtime source/wheel/frozen discovery and no Terminal/Node/cache prerequisite |
| 6 | closed capabilities/build/refusal/rollback, selected existing crates and explicit new transport limits |
| 7 | concrete downstream scope, producer/consumer/witness map, artifact/native and independent-review gates |

## Evaluation Focus

Read the complete selected contract against the original paths and synthetic
counterexamples. Verify selection predicates and errors before/after lock and
rename, retained syntax versus migrated business ownership, missing runtime
versus corrupt-file fallback, packaging tags and terminal-manager independence.
Check all due qualifiers and each consumer's actual role, not only marker presence.
Document future evidence limits separately from this foundation's result.

## Open Blockers

None requiring a new product decision within the approved contract-only boundary.
Implementation and its operational acceptance remain separately approved work;
unverified future code/packaging is not a passed runtime result.

## Continuity Notes

- `2026-11-17`: Spec prepared from approved FEAT-0178. Runtime implementation is
  excluded; the selected contract must state retained Python syntax/platform debt.
