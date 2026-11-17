# EVAL-0165: Terminal Workspace

- Status: `complete`
- Result: `PASS WITH LIMITS`
- Evidence Coverage: `partial` — selected Chromium/Node/Python cases complete; platform limits below remain explicit.
- Feature: [FEAT-0169](../feature/feat-0169-terminal-workspace.md)
- Spec: [SPEC-0169](../spec/spec-0169-terminal-workspace.md)
- Run: [Run249](../run/run-20261112-249-terminal-workspace.md)
- Profile: `fullstack-product`; contract/backend, frontend, integration, docs.

The actual common web Terminal workspace passes the bounded contract, design,
functional and interaction checks. A fresh read-only omission challenge found
four real defects; the primary repaired them and exercised their causal cases.
The informed repair recheck found no remaining material defect in those paths.
This is technical completion of this increment, not human visual acceptance or
delivery of the larger Rust/native PRDs.

## Delivered Behavior And Evidence

| Contract / evaluator | Observed evidence |
| --- | --- |
| Frame / design | Rendered baseline and final synthetic screenshots show the upper folder rail and lower cross-group task list directly beside shared navigation, top tabs/add/split, large canvas and bottom status. The large title/action row is removed while main and logical heading remain. Shared tokens, Material Symbols and D2Coding13px are retained. Actual1440×1000,920/700/320×800 geometry contains page overflow; narrow pane switching and closeable rail retain all PTYs. Long tab text scrolls inside its tab strip. Other routes keep normal page padding/layout. Herdr is a structural source reference, not an exact screenshot match. |
| Groups / contract + functional | Manager realpath creation cwd stays fixed while OSC7 pane cwd changes. New in group uses root/configured shell; splits inherit focused pane cwd/shell. Explicit folder opens a first terminal, group selection starts nothing, hidden/exited records retain membership, and removing the last retained tab removes only that derived group. No application Project/Source/Workstream/Session or persistent group store is created. |
| Hidden/close/lifetime / functional | Hide and task-row reopen retain terminal ID/PID and focus the exact pane. Narrow changes and navigation retain IDs/generation. A tab close confirms one terminal and ends exactly that scope. Explicit service restart confirms five remaining terminals, changes generation, clears groups/status and starts no replacement shells. The existing manager lifetime remains independent of web navigation/backend clients. |
| Status/attention / contract + functional | Plain shell stays unknown. Explicit OSC133 prompt/run/end metadata reaches list/checkpoint and the matching icons. New completion survives hide, non-input focus and pane-menu focus. It clears only after a matching full xterm render and following animation frame while its textarea has focus. DEC synchronized output visibly withholds the completion until rendering resumes. A held real periodic HTTP response predating a command cannot regress newer streamed running status; generation replacement clears prior view state. |
| Input/recovery / interaction | Real browser keyboard events execute a synthetic command. Tab Home navigation retains tablist focus; Shift+Escape reaches the pane menu. Font pending/failure/recovery, initial API failure/recovery, invalid folder repair and rail Settings entry are exercised. The status bar waits for restored input readiness. New/Retry affordances remain scoped to confirmed readiness. |
| Existing invariants / functional | Terminal regression suite passes with33 real isolated PTY cases; Node checkpoint/input/color/IME-adapter/state checks pass. No pinned engine/font/checkpoint bytes changed. Four-pane/32-record manager limits, input leases/backpressure/no replay and explicit termination remain in their existing owners. No fresh physical IME or launchd claim is inferred from this regression. |

## Findings And Repairs

| Origin | Cause / correction | Discriminating witness |
| --- | --- | --- |
| Fresh challenger | First creation response loss changed activeFolder and could replace the retained request key. A pending creation now gates other creations and exposes explicit Retry with fixed key/values. | Fail the first POST response after server success, permit group discovery, retry, compare identical key/terminal ID/PID and one retained record. |
| Fresh challenger | Group/Open folder first validated an unused deleted default cwd. Launch read now accepts an unsaved actual-cwd override and still validates saved section/shell. | Delete saved default, verify default launch fails while group New and explicit folder succeed; invalid actual folder/shell and settings preservation stay covered. |
| Fresh challenger | Any descendant focus, including the pane menu, could mark completion seen. Require the current xterm textarea. | Complete a delayed command while the pane menu owns focus, then focus input. Attention persists until the latter. |
| Fresh challenger | Parser/import completion was treated as display completion. Use full onRender plus following animation frame, with connection/disposal guards. | DEC2026 output hold: completion remains unseen while its output is withheld, clears after released render with actual input focus. |
| Primary | Older HTTP list could replace newer WS status in rail/tabs. Merge only newer terminal sequences within one generation. | Hold an actual older periodic response, start a command through the focused terminal, deliver it after the newer stream and observe running status retained; clean generation replacement separately verified. |
| Primary | Initial writable control could label input ready before screen restoration. Show restoration until that prerequisite is met. SVG status needs actual title content; legacy xterm backdrop must not expose native horizontal scroll chrome. | Pending/ready browser phases, visible glyph/tooltip semantics and wide/narrow rendered captures; scoped viewport override follows pinned xterm6's real scroll owner. |

## Verification Receipt

- `uv run --offline python -m unittest discover -s tests -v`:1651 tests, PASS,33 real-PTY cases skipped in this broad invocation. This is not1651 real executed scenarios; the optional process class is covered separately below.
- `LOCALBRAIN_TERMINAL_TEST_ENGINE=… .venv/bin/python -m unittest discover -s tests -p 'test_terminal*.py' -q`:67 tests, PASS with no skips, including33 real synthetic PTY cases. This ran before the small launch-override correction; the updated settings boundary then passes13 focused tests and the1651 full-suite pass. Final localized error/hint copy also passes the focused settings checks.
- `npm run test:terminal`:73 tests, PASS. The prior67-test baseline and new OSC133/group/sequence tests retain separate scope from browser interaction.
- `npm run build:terminal` and `npm run check:terminal`:PASS. Existing vendor/font bytes remain unchanged; the new state helper import receives a content fingerprint through the existing asset builder, preventing an older cached helper from missing new named exports.
- `LOCALBRAIN_TERMINAL_TEST_ENGINE=… node scripts/qa-terminal-workspace-browser.mjs …`:47 checks, PASS, using an owned synthetic HOME/backend, real PTYs and isolated Chrome156. Final run includes Settings text, cache-versioned helper, background scope, renderer attention, delayed snapshot, long tabs, exact stop, generation reset and fault recovery. Final cases open a trailing-space folder without trimming into its sibling, reveal focused input after narrow rail dismissal, and verify computed essential-symbol contrast for failure on the dark pane. Shared light code colors provide the on-code blue/green/amber counterparts. The fixture cleans its own processes/runtime/profile.
- Plan catalog, local links/anchors, privacy and final whitespace checks are recorded by Run249 at closeout.

Initial browser driver failures are retained as diagnosis, not product PASSes:
waiting for complete document while deliberately withholding fonts, using
insertText/char without normal keyboard ordering in screen-reader mode, treating
focus emulation as a guaranteed blur, issuing keys before asynchronous pane focus,
and testing a selector during reload's temporary empty document. These oracles
were corrected and the final45-check run completed. The actual initial readiness
label defect was separately repaired; test-driver corrections are not additional
independent product findings.

## Review And Limits

One fresh named `review_challenger` inspected frozen source/contracts and relevant
unchanged settings/checkpoint/pinned-renderer paths without editing, execution,
dependency installation, runtime mutation, publication or delegation. Its first
four findings were independent; its second bounded repair check was informed,
not another fresh discovery. The primary retained scope, architecture, integration,
adjudication, execution and final semantic review. The later delayed-response and
generation witnesses close its stated integration gap; final narrow UI copy and
asset-helper cache versioning are primary-verified additions.

Actual packaged Tauri admission/authentication, bundled Node/helper delivery,
Rust executable parity, native minimize/Quit/sleep, physical Korean IME,
VoiceOver, Safari/WebKit geometry and long-duration/performance measurements
were not run. They remain later delivery/acceptance boundaries and block those
claims, not this explicitly scoped common web increment. Unsupported shell
integration remains visibly unknown, and agent waiting/done or unread-output
inference is not supplied. No new transferable design/harness policy candidate
needs promotion; owner-specific rules and the private stage record were updated.
