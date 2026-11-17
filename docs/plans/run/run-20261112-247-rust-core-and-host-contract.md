# RUN-247: Rust Core And Host Contract

## Metadata

- ID: `run-20261112-247`
- Status: `passed`
- Feature: [FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md)
- Parent PRD: [PRD-0029](../prd/prd-0029-rust-core-and-responsive-gui.md)
- Active Spec: [SPEC-0167](../spec/spec-0167-rust-core-and-host-contract.md)
- Execution Profile: `foundation-contract`
- Required Evaluators: contract
- Attempt: `1`
- Created: `2026-11-12`
- Updated: `2026-11-12`

## Goal And Selected Loop

Complete the first approved contract, then hand off to FEAT-0168. Primary performs
orchestrator→Spec→contract updater→contract evaluator sequentially. One active Run,
no delegated work. Selected surface lanes: contract, read-only backend/integration/
infra, docs. No code/UI/runtime behavior changes; functional/design/UX evaluators
are not required for this bounded foundation result.

## Boundary And Baseline

User explicitly directs completion of both created Features. Approved recommendation
is terminal-control-first Rust, shared GUI/HTTP, retained Node/optional Python and
existing data compatibility. HEAD is `b31f6c4a5b84d5eeb4b3e908e3fb84a3f7dd3390` plus
seven pre-existing planning files. Source/current-policy inputs are frozen by content
for unchanged-input checks; no commit or user runtime mutation is required.

## Current Artifacts

- Target: [core/host contract](../project/rust-core-and-host-contract.md)
- Phase owner: [Refactor0006](../refactoring/refactor-0006-rust-core-transition.md)
- Contract evaluation: [EVAL-0163](../evaluation/eval-0163-rust-core-and-host-contract.md), PASS / complete for the contract scope

## Contract And Resource Controls

Check host/core boundaries, requests/results/errors, settings one-writer transaction,
manager compatibility/helper/scope, dependency/toolchain provenance and future
verification. No caller time/token/cost ceiling supplied. Planning checkpoints are
contract draft→source/consumer/adverse-case review→artifact verification→closeout;
they are revisable checkpoints, not task stop/acceptance limits. No pending worker
commitments; provider-internal usage is unobserved. Reserve time for both Runs,
semantic/source verification, docs checks and task-owned scratch cleanup.

## Review Method And Limits

Foundation completeness is primary same-author source/adverse-case review plus
objective artifact/source-byte checks. This is not independent code omission review,
actual Rust/Node/app execution or a future migration parity judgment. Risk assessment:
no executable/dependency/runtime mutation; no high-risk code completion being approved.
Future implemented multi-consumer/control/auth migration needs the normal frozen
comparison/independent challenge gates. No new common-harness candidate/comparison is required.

## Current Route

- Phase: passed contract; handoff
- Blocker: none
- Next: handoff completed in Run248 under the same batch authority; both contract results go to human review together
- Post-run human review: report both contract outcomes together; downstream product acceptance remains separate

## Continuity Notes

- `2026-11-12` outcome: contract PASS. Static source/contract inspection maps all11
  terminal routes and10 root CLI commands;36 local artifact links and JSON example
  pass;662 code/current-owner inputs remain byte-equal. Eval0163 reconciles all
  Feature acceptance points and boundary repairs. Shared catalog/privacy/link
  verification will also be renewed at the two-Run closeout. No executable port,
  actual runtime/GUI/native/performance or human product-use acceptance is implied.

- `2026-11-12`: Run started from the approved Feature; Spec fixes exact bounded
  deliverables. A missing login PATH entry was resolved by invoking the existing
  Rust toolchain's absolute path; no toolchain install/upgrade occurred.

## Joint Artifact Verification

The two-Feature closeout passes2 catalog tests, fresh catalog/whitespace checks,
1363 local links including8 anchors across16 owned outputs and2 JSON examples.
Both Feature/Spec/Run/Evaluation chains use passed/approved/passed/complete-PASS
statuses. All662 frozen code/current-policy inputs and HEAD remain unchanged;
privacy passes1877 candidate files. These are contract/artifact/source checks,
not an executable Rust, PTY, browser, native/OS or performance run.
