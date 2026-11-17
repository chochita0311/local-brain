# EVAL-0163: Rust Core And Host Contract

## Metadata

- ID: `eval-0163`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-247](../run/run-20261112-247-rust-core-and-host-contract.md)
- Attempt: `1`
- Feature: [FEAT-0167](../feature/feat-0167-rust-core-and-host-contract.md)
- Spec: [SPEC-0167](../spec/spec-0167-rust-core-and-host-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: contract, source-only backend/integration/infra, docs
- Evidence Coverage: `complete` for the bounded contract outcome
- Created: `2026-11-12`

## Scope And Method

Evaluate the [target core/host contract](../project/rust-core-and-host-contract.md)
and [transition phase plan](../refactoring/refactor-0006-rust-core-transition.md),
not an executable Rust port. Primary performs sequential same-author Spec,
contract build and evaluation. No independent reviewer/runtime evaluation is claimed.
Current source/policies/manifests and pre-existing planning inputs were content-frozen
at Run start; contract candidates and checks are retained at the existing private owner.
This bounded documentation result has no executable/security/data mutation; the later
high-risk migration requires its own frozen comparison and independent challenge.

## Checks And Evidence

| Acceptance obligation | Observed contract/source evidence | Result |
| --- | --- | --- |
| Current/first/later/suspended inventory | Product-family ownership table reconciled to app/application.py, app/routes.py, feature availability and root CLI. Web-only Learning/Insights/Sources/Schema/resource gaps and10 root CLI commands remain explicit | PASS |
| Core and host ownership | One library + one executable, same binary for Python web/app/CLI/native management; no Tauri dependency in core, no second business implementation or always-on Rust daemon | PASS |
| Concrete operation/consumer shape | AST inspection mapped all11 terminal public HTTP/WS routes to the operation table; bounded UTF-8 JSON control example parses. Source map covers page/API/stream/CLI/manager/helper/writer/build registration | PASS |
| State/error/retry/stream semantics | Reviewed exact key/expected-set/generation, JSON bool/int, read-vs-launch defaults, public error status, ack/lease/cancellation/input failure and unknown/unclean cases against current source | PASS |
| Writer/transaction/rollback | Existing operations.lock, byte revision, common parser/serializer/atomic commit remain one Python owner; Rust prepares validated patch without a second lock. Response loss and later generic-writer cutover are explicit | PASS |
| Dependency/toolchain/API evidence | Actual Rust/cargo1.99.1/aarch64; current lock versions and cached upstream Cargo manifests/VCS/license requirements; official Rust/Tauri/serde/libc/sha2 references. Host1.77.2 declaration vs locked Tauri1.90 requirement disclosed | PASS |
| Resource and subsequent acceptance | Existing manager/input/flood bounds kept as web gates; native total-resource baseline/budget must be fixed before downstream product approval. No measured improvement is asserted | PASS |
| Scope and handoff | No executable Rust/dependency/schema/UI/native/service mutation; FEAT-0168 and separate app access/group/status prerequisites remain explicit; migration parity stays Provisional | PASS |

Static contract probe checks9 distinguishing clauses and11 routes, plus JSON syntax.
Those checks corroborate the manual requirement/producer/consumer reconciliation;
marker existence alone is not the completeness argument.

## Findings And Reconciliation

- Supported, fixed during contract review: an unchanged2MiB manager response can
  exceed2MiB after a host envelope is added. Internal control reply allows4KiB
  headroom; public manager/stream bounds remain unchanged. This avoids a false
  compatibility claim at the exact frame boundary.
- Supported, fixed: JS tab rename checks pre-trim UTF-16 length, then trimmed
  nonempty value. Contract now names that predicate, distinct from UTF-8 length
  or post-trim-only validation. Expected-scope duplicates are conflict409, not
  a new invalid400 response.
- Supported, fixed: retaining the Python common writer requires Rust prepare to
  run without reopening operations.lock. Missing/string/invalid section atoms
  prevent TOML dates/bools from being string-coerced; unknown values stay with the
  current writer. This is an explicit transitional ownership choice.

No material blocking contract finding remains. These are primary same-author
source adjudications, not independent code-review returns or observed runtime fixes.

Run248 consumer reconciliation added one closed internal `runtime.retire` operation
to the target host protocol and an independent payload-use lease note to settings
prepare. This is within the approved storage/lifetime ownership boundary and adds
no public route/CLI command. It prevents check-then-delete after releasing a guard,
self-image retirement and unlinking the currently used control.lock. The updated
operation/lock ownership and unchanged11 public routes/10 CLI commands are renewed
at the joint closeout; earlier candidate hashes remain historical snapshots.
Final adapter reconciliation also fixes explicit preferences-vs-terminal error kind
and settings' independence from optional engine/cache readiness, matching current
PreferencesError409/detail and pre-setup repair behavior rather than inventing a
new generic400 or making settings depend on a running manager.

## Regression And Evidence Limits

Current runtime/source/current-behavior policies are unchanged inputs. Existing
data/identity/Usage/model/storage/IME/font/lease/checkpoint/4-pane/32-record/stop/no-replay
requirements remain in the target and parent. Docs checks cannot establish executable
parity, minimum-Rust compilation, dependency binary integrity, native auth/IME/sleep,
Node ABI, performance, physical interaction or delivery. Those are unperformed future
product acceptance conditions, not missing evidence required by this contract-only Feature.

## Route

`pass` for FEAT-0167; proceed to the separately approved FEAT-0168 under the user's
instruction to finish both. Report both Runs together for human review. No merge,
deployment or whole-PRD completion is approved by this evaluation.

## Joint Artifact Verification

The two-Feature closeout passes2 catalog tests, fresh catalog/whitespace checks,
1363 local links including8 anchors across16 owned outputs and2 JSON examples.
Both Feature/Spec/Run/Evaluation chains use passed/approved/passed/complete-PASS
statuses. All662 frozen code/current-policy inputs and HEAD remain unchanged;
privacy passes1877 candidate files. These are contract/artifact/source checks,
not an executable Rust, PTY, browser, native/OS or performance run.
