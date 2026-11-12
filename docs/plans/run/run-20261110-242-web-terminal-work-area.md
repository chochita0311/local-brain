# RUN-242: Web Terminal Work Area

- Status: `blocked`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Attempt: `1`; implementation and checked-scope evaluation completed `2026-11-11`.
- Profile: `fullstack-product`; primary owns requirements, contract/backend/infra,
  frontend/integration/docs and final adjudication. Required contract, design,
  functional and interaction evidence; independent code challenge at freeze.
- Authorization: human proceed after the reviewed PRD/menu/CLI/UI and lifetime
  decisions; no commit/push/native app delivery or external writes.
- Baseline: only terminal PRD, Plans Index and artifact catalog are pre-existing
  edits. Preserve them and all unrelated work. Existing Python/CLI/desktop/source
  contracts remain in force. No live personal DB or provider-original writes.
- Entry: retrieved configured experience; engine docs and actual pinned packages
  checked in isolated scratch. Node-pty spawn-helper executable permission required
  correction within its owned install. Real synthetic PTY plus headless alternate
  buffer, CJK and bracketed-paste restoration passed. This is not UI/stability pass.
- Current route: implementation available; performed evaluation PASS with partial
  coverage. Required physical macOS IME and remaining hidden-view/representative regression evidence
  prevent a whole-Feature pass. This is a technical evidence block, not a spec
  or planning return; no new product choice or permission is needed to use the
  local implementation. No hard caller deadline/budget was imposed.
- Evaluation owner: [EVAL-0158](../evaluation/eval-0158-web-terminal-work-area.md).

## Preservation And Evidence Plan

Existing ingestion/Session/Usage/search and shared navigation must retain their
results. No manager/assets/polling on unrelated pages or desktop. Start/stop/list
and process tests use isolated synthetic data/cache/HOME, stop only owned jobs
and remove exact scratch after all test processes finish. Public artifacts contain
no real terminal output, personal paths/environment or native session bodies.

## Progress

- `2026-11-10`: Orchestrator/Spec established the reviewed first-delivery boundary
  and explicit engine/lifetime/resource/retention contracts. Implementation active.

## Delivered Work And Ownership

- `terminal/manager.cjs` owns PTYs, tabs, bounded VT state and input leases;
  `ownership.cjs` owns signal eligibility; the short-lived `processes.py`
  supplies process identity. Python runtime owns optional setup, serialized
  control and transient launchd lifetime. CLI/web are consumers of that control
  contract, with exact-origin and bounded WebSocket transport in the web bridge.
- The browser owns rendering and focused interaction: compact tabs, up to four
  panes, background/reopen, distinct scope termination, management/service
  controls, read-only takeover and reconnect. Existing shell rules/tokens apply.
- Web composition admits the feature on macOS. Both CLI names share dispatch;
  desktop routes/startup/CLI/runtime/assets remain excluded. Terminal output
  has no Session/Usage/search consumer. No schema migration or personal runtime
  modification was required.
- Bilingual conditional Docs, README, lifecycle/storage/privacy/development and
  design owners describe the resulting behavior. Initial three planning files
  were advanced under the same authorization, preserving their decisions and
  dated planning history. Unrelated source changes were not absorbed.

## Evaluation And Repairs

[Eval0158](../evaluation/eval-0158-web-terminal-work-area.md) owns the complete
A-01–16 evidence map, component measurements and independent review receipt.
The primary performed contract, design, functional and interaction evaluation;
the code challenger supplied bounded read-only omission evidence, not acceptance.

Observed defects were repaired within this contract: destructive generation and
scope races, root/signal identity bypass, duplicate query replies and mouse bytes,
creation retry/cache lifetime, TUI focus, blocking inspection, launchd idle
respawn, failed setup readiness, compiled xterm mode-query failure, uncertain
manager-loss reporting and the CLI bulk-stop consumer. Final narrow repair review
confirmed unclean-stop refusal and Node20 module loading. A later primary
inspection found the management renderer omitted retained per-terminal failure
metadata; its cache/summary/detail now include that error and a synthetic real
browser response confirmed both failure display and recovery. The latter UI
repair is primary-validated, not independently confirmed by turn7.

No unresolved concrete supported defect remains in these checked paths. The
required real macOS IME observation remains absent; Unicode injection is not a
substitute. Warm browser/backend/manager/shell costs are measured separately;
truly hidden-view, realistic search/browse baseline and long-run evidence remain
qualified in the Evaluation. No feature acceptance
or every-environment stability is inferred from the passing automated checks.

## Verification And Delivery Boundary

- Final permitted full Python:1,618 tests OK,19 engine-opt-in skips. All19
  current real-PTY methods were observed passing across the focused/targeted
  runs; final terminal-only35 OK with19 skipped. No skipped case is presented
  as executed in the whole-suite run.
- Actual Chrome and launchd probes cover wide/narrow shells, vi/CJK alternate
  screen restore, lease/takeover, background, process scopes, independent client
  and backend lifetime, crash uncertainty and empty restart. Current manager
  build was loaded by explicit UI restart after a visible version conflict.
- Terminal/Mermaid assets, compiled parser under Node24/20.0.0, JS syntax,
  source-byte wheel admission and desktop data exclusion were checked. Final
  catalog/privacy/whitespace and temporary cleanup are closeout checks below.
- Initial unpermitted HTTP fixture bind failure and source-atime assertion did
  not recur in the permitted full run. Earlier fixture corrections and the
  restored37 optional packages are documented in Eval0158.

All implementation remains in the working tree at base HEAD
`4ff4a2daf6a714063b19ba077bb169711441bdaa`. No commit/push, default-user engine
setup, installed-app rebuild/relaunch or release is included. Restart the user's
web backend to load this source; the explicit Terminal setup installs its optional
engine once. Existing user services were not stopped or replaced.

## Remaining Review And Resume Condition

The agreed direction and product choices are unchanged. Code can be exercised
locally, including UI background/end and CLI service control. Formal Feature/Run
pass is withheld for the named required evidence; inspect Eval0158 rather than
reopening engine/menu/lifetime decisions. Human review should check actual IME
composition/cancellation and copy/paste in the user's macOS/browser/shell, then
route a verified-unblock continuation with representative resource/regression
evidence. Preserve this blocked Run and carry its observations/reviews forward;
do not silently convert partial coverage into acceptance or automatically start
another implementation/release.

## Closeout Checks

- Final repository privacy check passed for1,840 candidate files. Generated
  artifact catalog and whitespace checks passed; no unrelated file appeared in
  the final source footprint and HEAD remained the entry baseline.
- Final wheel matches12 selected live source files, including both CLI paths,
  updated management renderer and bilingual guide; both console entrypoints are
  present. Desktop data collection admits125 files and zero terminal assets.
  This is package admission, not an installed-native build.
- Additional Node20.0.0 real-PTY login/ZDOTDIR and child-stop/empty-restart probes
  passed. Browser parser checks passed on both supported minimum and host Node.
- All synthetic PTYs/managers and their launchd job were stopped; the isolated
  QA backend was stopped and owned browser pages closed. Source/default-user
  runtimes were not changed. Task-owned disposable files were removed before
  handoff; frozen review/measurement receipts remain at the configured private
  evidence owner, with no durable reference dependent on a temporary path.
