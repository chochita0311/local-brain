# Rust Phase3 Inventory And First Feature Handoff

## Log Type

- Type: `Handoff`
- Date: `2026-11-17`
- Related track: [REFACTOR-0006](../refactor-0006-rust-core-transition.md)
- Scope: remaining application-backend inventory, dependency order and first Feature proposal; planning only

## Summary

- Goal: resume the checkpointed Rust transition from the existing Phase3 handoff.
- Outcome: `Partial` for Phase3; inventory/first-boundary planning delivered, human approval pending.
- Conclusion: [inventory](../../project/rust-backend-migration-inventory.md)
  accounts for all 246 Python modules/26 package-or-root groups, 128 explicit
  conditional/unconditional HTTP/WS registration expressions, CLI/module
  entrypoints, lifecycle/jobs and delivery consumers. [Draft FEAT-0178](../../feature/feat-0178-rust-common-settings-cutover-contract.md)
  proposes the common-settings transaction/host/delivery contract before a separate
  writer implementation. There is no new approved Feature, Spec, Run or port.

## What Changed

- Added the planning inventory with 20 responsibility families, current
  web/native/suspended/experimental admission, old-to-proposed responsibility
  maps, full route-registration snapshot and dependency ordering.
- Added the first foundation Feature proposal with writer/outer-lock ownership,
  exact common value predicates/defaults, TOML compatibility, terminal-independent
  runtime delivery, error/recovery and downstream acceptance boundaries.
- Updated the existing refactor plan, parent PRD continuity and Plans Index;
  the generated artifact catalog includes the new draft Feature.
- No product code, manifest/lock, database, personal runtime or installed app changed.

## Behavior / Parity Notes

- Intent: structural/interface migration with existing behavior preserved in
  future approved slices; this handoff changes planning artifacts only.
- Intentional runtime deltas in this handoff: none.
- Current common/terminal `settings.toml` writer remains Python. Separate source
  TOML, search/model JSON and Context DB retain their owners; shared locking or
  serializer usage is not permission to migrate them together.
- The first foundation must fix parent/child/outer `operations.lock` behavior
  and common Rust delivery without creating a Terminal/Node dependency. The
  existing terminal bridge cannot become a foundation import unchanged.
- Parity claim status: `Provisional` for migration; no Phase3 implementation
  candidate exists. Static family/route coverage is not complete execution-flow
  parity, an independent code review or a safe-to-merge decision.
- Terminal Feature177/Run258 actual-window acceptance remains pending. Existing
  physical/native/IME/sleep/recipient/minimum-OS/MSRV/performance limits remain.

## Validation

- Initially clean baseline: `e6958df0813b8652074c68a73ac61a8b551e59a8`.
  Original Run247 baseline remains in the active plan; no comparison candidate
  commit or runtime result is invented for this docs-only continuation.
- Static census: AST parse of every Python source module and explicit route
  registration; each maps to a family. Source settings/lock/recovery, assembly,
  edition/CLI/lifecycle and selected consumer/test paths were read directly.
- Build/compile and runtime/UI checks: not run; no implementation or visible
  interaction changed. Later product slices still require source/wheel/native
  delivery and meaningful behavior/failure/concurrency checks.
- Closing checks: artifact catalog build/check and its two existing unit tests
  passed. Local link/anchor validation passed 1,367 references in seven changed/new
  documents including the catalog; all 128 registration rows/26 group counts
  match the 246-module static census. The 261 captured code/dependency inputs
  are unchanged, and no source/build/test path has a task diff.
- `scripts/check-repo-privacy.sh` passed (1,951 candidate files);
  `git diff --check` passed. Full application/Rust/Node suites were not run for
  this docs-only planning handoff. These results establish document/census
  consistency, not runtime parity or native acceptance.

## Risks / Limitations

The foundation is proposed, not approved or executed. Its transport/value/lock/
delivery choices are the concrete contract output, not settled implementation.
No new dependencies are selected or compatibility inferred from current crates.
Per-family query/write/side-effect/failure and actual delivery audits remain due;
enumerating all source files and registrations does not establish their parity.

## Next Action

Later same-day follow-up: the human approved FEAT-0178 and
[Run259](../../run/run-20261117-259-rust-common-settings-cutover-contract.md)
passed the contract. Its own Run/evaluation retain execution evidence. The new
[implementation FEAT-0179](../../feature/feat-0179-rust-common-settings-runtime.md)
is draft and awaits approval. The paragraphs below preserve this earlier
planning return's next action at its original boundary.

Human reviews FEAT-0178's contract-only boundary. After approval, create its
Spec and bounded contract Run, resolve the listed choices, then evaluate the
contract. A separately approved product Feature implements the passed result.
The request to continue Phase3 does not auto-approve this newly drafted boundary
under [PRD And Feature Management](../../../policies/harness/prd-feature-management.md#planning-gate-summary).
