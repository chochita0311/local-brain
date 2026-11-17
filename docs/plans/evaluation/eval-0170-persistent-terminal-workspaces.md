# EVAL-0170: Persistent Terminal Workspaces And Shell Status

- Status: `complete`
- Result: `PASS` for the shared workspace/status increment and observed packaged-native contracts.
- Evidence Coverage: `partial`; physical native input and human visual acceptance remain separate.
- Feature: [FEAT0173](../feature/feat-0173-persistent-terminal-workspaces.md)
- Spec: [SPEC0173](../spec/spec-0173-persistent-terminal-workspaces.md)
- Run: [Run254](../run/run-20261113-254-persistent-terminal-workspaces.md)
- Profile: `fullstack-product`; contract, functional, design and interaction evaluation.

## Evaluated Boundary

Named workspaces have stable identity, an optional default cwd and generation-bound
tab membership. Different-folder tabs and split panes stay in one workspace;
explicit metadata movement preserves terminal IDs/PIDs. Empty groups survive
exit, app/service restart and generation reset without process replay. Legacy
tabs are adopted without stopping work. Empty removal deletes only the group,
and hidden tabs still prevent removal. The private app-data store joins bounded,
schema-validated same-installation backup/restore. GET does not publish metadata.

The runtime owns execution; the host owns durable grouping and generation-bound
presentation; the GUI owns selection, interaction and attention. These boundaries
are separate from generic settings and preserve the unchanged immutable Node/Rust
payload. Creation and metadata publication are not a cross-store transaction:
known creation identity is returned with a recoverable warning on subsequent
storage/manager-read failure. Retry does not silently reassign confirmed membership.

New host-created zsh terminals use verified private, versioned startup shims.
User rc files are unchanged; effective ZDOTDIR and existing hooks remain usable.
OSC133 prompt/running/result and OSC7 cwd use the existing parser. Existing work
receives no injected commands. Other/unreported shells retain a neutral dot.
HTTP defaulted shells are resolved before integration; GUI launches still capture
the configured paths. Standalone raw CLI creation is unchanged.

The expanded rail owns collapse; the toolbar owns reopen only when collapsed.
Terminal-only desktop header/search/group/task density is48px/32px; narrow touch
controls remain40px. Task names/context use one nonredundant line, preserving
tooltips, accessible state descriptions, menus and focus. Other routes retain
their density. Primary rendered inspection confirms the existing shell/type/icon
language, readable pane/tab states and available canvas at wide/compact/narrow
sizes; this is a bounded technical design judgment, not human visual acceptance.

## Observed Verification

| Check | Result and scope |
| --- | --- |
| Final Python suite |1700 tests, OK with49 opt-in process/runtime tests skipped. Actual opted-in zsh checks below ran separately. First1699-test run failed only the generated schema reference ledger; writer refreshed one reference row, six audit tests and final full suite passed. No schema/decision change. |
| Real synthetic Chromium/PTY |95 PASS: prior input/retry/close/background/title/order/completion/font regressions; one panel toggle,48px header and compact rows,40px touch/other-route preservation; empty workspace creation/reload/removal, mixed-root tabs/panes/order, metadata movement with unchanged execution and writable input, exit/reload persistence, actual new-zsh prompt/run/nonzero/Ctrl+C130. |
| Node terminal checks |75 PASS, including existing VT/input/status cases and workspace grouping with empty/mixed-folder hidden tabs. |
| Actual zsh5.9/PTY |5 PASS: three shim integrity/retry/partial-preparation cases and two actual PTY flows. Startup files/order/content, custom named/array hooks, success/failure, pipeline/PIPE_FAIL, Unicode/%/hash cwd and ZDOTDIR changes across all startup stages are covered. |
| Focused host and backup | Final full suite includes10 workspace tests and32 settings/backup tests. Default/empty/absent-SHELL HTTP launches converge on the verified zsh launcher; metadata backup restores the saved name, and invalid schema is rejected before replacing current metadata. |
| Frozen semantic challenge | Named review_challenger reviewed20 frozen files, then21 in one informed repair recheck. A supported post-create TerminalError escape was repaired and tested. Primary also resolved defaulted-shell integration and backup disposition gaps. Static repairs are supported; the worker ran no tests and did not approve completion. |
| Final actual native app |12 PASS on Apple Silicon/macOS26.5.1: authenticated cold New, last-close/recreate, keyboard-created empty named workspace/default folder, tabs/four panes, packaged integrated zsh status in another-folder split, same-workspace order, minimize/red close/Dock, Quit/source-app removal, suspension/relaunch and exact-scope stop with persistent empty metadata. The integrated zsh remains alive through Quit/removal/relaunch. IME explicitly excluded; suspension is not real sleep. |
| Final package |319 runtime entries match size/SHA/mode and payload identity; official Node24.15.0/ABI137/N-API10/arm64, runtime/app architecture, deep strict signature, copied frontend assets and current source/build inputs pass. |
| Development HTTP reflection | HTTP host restarted with its original argv/environment; the same generation and both existing terminal IDs/PIDs remained. New workspace API/template verified read-only; no user manager stop/upgrade. |

Earlier failed browser attempts exposed driver/oracle issues: responsive Sessions
header height versus its density token, retry-response readiness, delayed retired
row rendering with already-persistent groups, and a missing fixture variable.
They remain failed observations in private evidence; the final95-check run passes.
The reviewer-found exception path was a product defect, separately repaired.
Two native attempts remain failed observations: advancing before a control was
re-enabled, then a visible modal missing from the external AX child walk. Enabled
readiness and actual synthetic ASCII focus/Tab/Enter support the final run.
The modal's name-field width and wrapping picker were a real visual defect;
scoped CSS was corrected,95 browser checks repeated and the app rebuilt. Primary
inspected final native form/canvas screenshots: inputs and picker are contained,
the picker stays one line and header/rows/footer retain the compact geometry.

Official zsh5.9 startup/hook source and rolling VS Code wrapper source informed
the startup inquiry. VS Code is a comparison, not proof that every ZDOTDIR change
or OSC133 behavior is preserved. The actual local PTY evidence supports only the
tested configurations; arbitrary global rc/RCS arrangements are not certified.

## Retained Limits

No native Korean-input acceptance is claimed. [Eval0169](eval-0169-terminal-everyday-interactions.md)
retains the failed/intermittent OS input-method probe and unresolved ordinary
physical-input correctness. Physical keyboard/clipboard/shortcut behavior,
VoiceOver and the native modal's external-AX exposure remain unresolved; synthetic
keyboard form success does not establish assistive-technology support. Real Mac
sleep/wake, minimum macOS14 hardware, recipient use, long soak/resource
budgets and whole-backend Rust parity remain unaccepted. No active user service
upgrade, installed-app replacement, Git staging/commit/push or publication occurs.

Final source/build-input SHA256:
`01628f1b0bd1b48b7e93ff415dbbef0225b238415b7cbde0c4cda6416d3ac449`.
The ad-hoc signed app has988228537 regular-file bytes and unchanged payload
`66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8`.
The ZIP is `dist/LocalBrain-apple-silicon.zip`, SHA256
`9d86933a6322e0bc3b68abc90b4be00ac541bd0b5570aa673fca300f6d2372e1`.

Run255 measurement correction: this receipt previously spelled the narrow touch
minimum44px. The unchanged shared token and before/after rendered comparison
show40px; this corrects that documentation value, not the UI or prior test result.
