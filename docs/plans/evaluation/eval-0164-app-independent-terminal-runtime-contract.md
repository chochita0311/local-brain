# EVAL-0164: App-Independent Terminal Runtime Contract

## Metadata

- ID: `eval-0164`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-248](../run/run-20261112-248-app-independent-terminal-runtime-contract.md)
- Attempt: `1`
- Feature: [FEAT-0168](../feature/feat-0168-app-independent-terminal-runtime-contract.md)
- Spec: [SPEC-0168](../spec/spec-0168-app-independent-terminal-runtime-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: contract/data ownership, source-only backend/integration/infra, docs
- Evidence Coverage: `complete` for the bounded contract outcome
- Created: `2026-11-12`

## Scope And Method

Evaluate the [runtime target contract](../project/app-independent-terminal-runtime-contract.md)
against the approved Feature and passed [core/host contract](../project/rust-core-and-host-contract.md).
Primary performs sequential same-author roles. The result is contract completeness,
not independent code review, actual helper/launchd/packaging behavior or migration
parity. Frozen source/owner inputs and candidate artifacts are retained with the
existing private evidence owner; current code/current policies remain unchanged.

## Checks And Evidence

| Feature acceptance | Actual evidence and distinguishing cases | Result |
| --- | --- | --- |
| Every lifetime event / selected policy | Transition table covers initial read, New/Split, Hide/Open, hidden/minimized/navigation, window/Cmd+Q/force death, sleep/wake, program exit, scoped/global stop/restart, exact idle predicate, manager loss, shutdown/reboot, update and uninstall | PASS |
| App-independent executables/helper | Resource vs immutable private payload vs stable launcher paths are fixed. Node/helper/engine do not depend on `.app`, checkout, user Node/Python. Preparation is explicit/offline with manifest/ABI/signature/relocation gates | PASS |
| Scope/identity and lock ownership | Actual current constructor executed with pure path/UID stubs in4 cases: same paths, different cache, different data; exact suffix/root/GUI domain/label matched. Full hash/receipt, legacy version, collision, private owner and payload-use protections are explicit | PASS |
| Helper and process termination | Synthetic JSON helper example matches all6 current process-record fields; whitespace shape corrected. Current ps/options/getSid/locale/errors,2s/3s/8MiB/shared-fresh inspection and exact PID/birth/group/session/ancestry/force/partial-exit rules are mapped | PASS |
| Manager vs job/unknown | No PID-only/empty-list/protocol guessing; partial failures retain evidence. Unclean predecessor payload remains protected across an explicitly permitted fresh generation, without restoring/adopting old jobs | PASS |
| Update/cache/backup/remove | Internal receipt-bound retirement holds control/use guards through actual deletion, refuses self-image/unknown/changed tree, never unlinks its held control.lock; app/checkout removal leaves explicit app-less status/stop available | PASS |
| App-less management and CLI compatibility | Exact generated launcher path/argv/quoting, no PATH/npm/Python/jq requirement, existing list/stop/service and TTY/--yes/--force/JSON/exit rules; absent payload requires explicit preparation | PASS |
| Privacy/provenance/scope | Only scope/installation/identity/leases/unresolved-loss metadata; no transcript/command/VT/environment/credential dump. Exact Node24.15/ABI137/N-API10, current engine pins and actual later release/archive/native evidence are separated | PASS |

Static checks parse the helper example, derive its fields from source AST, evaluate
the existing constructor without filesystem/process effects, exercise2 synthetic
manifest-identity equations and inspect11 named contract discriminants. These
support the manual owner/shape/transition review, not future runtime execution.

## Findings And Reconciliation

- Supported, fixed: cleanup could otherwise check inactivity then lose the guard
  before deleting an executable, or delete its own image/held lock. The target now
  defines closed `runtime.retire` preview/receipt/apply shapes, foreign-use shared
  leases, nonblocking/exclusive apply, unchanged-tree predicates, execution outside
  retired trees and no control.lock unlink. Core/host operation/source map and
  Eval0163 consumer reconciliation were updated together.
- Supported, fixed: hashing a manifest's own file recursively has no finite
  ordinary construction. `manifest.json` is special, excluded from its own files
  list; canonical body hash excludes payloadId, while retirement treeHash separately
  includes actual manifest bytes. Mode is an octal string and floating values are
  forbidden, removing ambiguous serialization inputs.
- Supported, fixed: a fresh explicit generation after unclean manager loss cannot
  prove old descendants exited. Minimal per-payload/legacy loss metadata protects
  the predecessor from automatic retirement; no transcript or auto-clear/history
  product is added. This preserves fresh explicit Start without erasing uncertainty.
- Supported, fixed: the synthetic born example now uses the current single-space
  C/UTC field join, and launcher spelling fixes its internal terminal/root prefix
  so the user does not have to type terminal twice.

No blocking ownership/lifetime/helper/payload/management ambiguity remains in this
contract. These findings are primary source/contract adjudications, not runtime
bugs reproduced in a new Rust implementation.

## Regression And Evidence Limits

No running service/job, Node PTY, app package or private settings/data was started,
stopped, installed or altered. The real future tarball SHA was not verified, addon
ABI/signature/relocation and minimum-OS/Rust builds were not run, and packaged
Quit/sleep/IME/physical/VoiceOver/resource/long-soak/recipient acceptance is not
established. They are explicit later product gates, not acceptance requirements
for this documentation-only foundation. Existing web pass is not native proof.

The bundle/scope/helper/management recommendations are now approved target decisions,
while current native exclusion and code remain actual implementation truth.
Shared source-byte, links/catalog/privacy checks are renewed at the joint closeout.

## Route

`pass` for FEAT-0168. Both requested contract Features have completed their bounded
outcomes. Handoff to the separately scoped access/group/status foundations and first
Rust terminal product, without automatic new Feature/implementation/release authority.

## Joint Artifact Verification

The two-Feature closeout passes2 catalog tests, fresh catalog/whitespace checks,
1363 local links including8 anchors across16 owned outputs and2 JSON examples.
Both Feature/Spec/Run/Evaluation chains use passed/approved/passed/complete-PASS
statuses. All662 frozen code/current-policy inputs and HEAD remain unchanged;
privacy passes1877 candidate files. These are contract/artifact/source checks,
not an executable Rust, PTY, browser, native/OS or performance run.
