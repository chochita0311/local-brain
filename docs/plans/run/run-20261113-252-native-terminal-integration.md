# Run252: Native Terminal Integration

- Status: `passed`
- Feature: [FEAT-0171](../feature/feat-0171-native-terminal-integration.md)
- Spec: [SPEC-0171](../spec/spec-0171-native-terminal-integration.md)
- PRD: [PRD-0030](../prd/prd-0030-macos-terminal-work-area.md)
- Profile: `fullstack-product`; contract/backend/native/frontend/infra/integration/docs.

Approved sequential consumer of actual Rust runtime Run251. Entry follows its
contract/build/parity gate, not only the earlier documentation Runs247/248. User
requests subagent functionality/payload verification; primary retains decisions,
integration, exact runtime target selection and final evaluation. Existing user
data/jobs/app installation are preserved; test/relocated app scopes are synthetic.

## Implemented And Observed

Terminal-only native admission, HTTP/WS auth, exact loopback Origin, WebKit WS CSP,
shared UI/assets/fonts, offline immutable payload, cached manager/helper/launcher
and identity-safe cleanup/update are implemented. The final ad-hoc signed app and
ZIP are built under dist. Exact319-file payload/ABI/modes/digests/signature/assets/
source identity passed a bounded verifier after the discovered late license mode
mismatch was repaired. [Eval0168](../evaluation/eval-0168-native-terminal-integration.md)
owns exact artifact identities, official Herdr comparison and evidence limits.

Seven actual packaged-host checks pass using the final relocated app with
synthetic roots: LaunchServices/Tauri/backend start, HTTP admission, offline
cold/last-stop/recreate/groups/panes, actual authenticated WS, normal native Quit
plus source-app removal retaining exact execution IDs/PIDs, suspension/resume and
relaunch with no replay, and exact-scope explicit stop. Harness cleanup stops only
its jobs and removes its copy/runtime. SIGSTOP/SIGCONT is not physical Mac sleep.
Browser54 covers common rendered flows; it is not a native-window substitute.

## Initial Block And Resume Condition

At the initial attempt the OS reported the Mac screen locked. Native AX returned an application reference
instead of an operable window and owned-window capture is refused. Earlier
driver exploration is retained as failed/unavailable evidence, not a rendering
defect or PASS. Required actual window close/Dock reopen and native last-pane
close/New remain unobserved. Physical Korean IME, shortcuts/clipboard, VoiceOver,
real sleep/wake, minimum-OS hardware, recipient use and sustained performance also
retain their separate limits. Source, package, API or shared-browser success
cannot close that acceptance gap; FEAT0171 remains approved, not passed.

The user was asked asynchronously to report unlocking; no OS lock/settings were
changed. Other feasible implementation, host checks and documentation proceeded.
Resume the native UI harness without `--backend-only` after an unlocked session
is available; it now refuses locked UI attempts before creating app copies.
Use the final app and fresh synthetic scope, preserve this Run's observations,
and record the subsequent attempt under normal workflow resumption rules.

## Resumed Window Acceptance

[Run253/Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md) resumed
the check in the unlocked session. The final rebuilt app's ten actual native
window/lifecycle checks pass, including last-pane close/New, red-close/Dock return,
Quit/source-app removal, exact generation/IDs/PIDs/order retention after relaunch
and explicit scoped stop. A real footer clipping defect was repaired and observed
in the final app. This satisfies the required window boundary above; the earlier
locked attempt remains historical evidence, not a retroactive PASS.

The final native10 explicitly skips OS IME. Separate attempts produced one valid
Korean string but also doubled jamo or ASCII, with non-composing events observed
in the diagnostic copy. Eval0169 preserves that unresolved input observation.
FEAT0171 passes technical integration, while physical/native Korean readiness,
human visual/shortcut/clipboard/VoiceOver/sleep/recipient/minimum-OS/performance
acceptance remains unaccepted. Parent PRD0030 stays approved, not complete.
