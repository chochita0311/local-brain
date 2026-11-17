# Run257: Terminal Status Indicators

- Status: `passed`
- Feature: [FEAT0176](../feature/feat-0176-terminal-status-indicators.md)
- Spec: [SPEC0176](../spec/spec-0176-terminal-status-indicators.md)
- Profile: `frontend-product`; frontend/integration/docs.

The user wants explicit criteria and a consistent symbol size, then adds iTerm2
Dock/current-window/hidden/working references. The selected correction uses the
existing icon family and keeps command state separate from view/attention. The
first observed legacy shell reports unknown while newer launcher shells report
prompt/completion; this is launch-integration provenance, not a first-tab rule.
Existing work remains intact. Primary owns design/implementation/evaluation;
no delegation, user command injection, manager restart, installed-app replacement
or Git write. Baseline127 dirty/new files are preserved in private owned scratch.

iTerm2 3.7.6's Dock menu was opened/read/cancelled through accessibility without
selecting windows or sending terminal input. Its local marks include bullets,
checks and minimized diamonds. Read-only window flags corroborate four minimized
diamonds; checks may override an edited marker. The matching official commit
[PseudoTerminal](https://github.com/gnachman/iTerm2/blob/7ce456b98db38d3f0bafd70ffec87752e69d5d58/sources/TerminalView/PseudoTerminal.m#L16237)
sets document-edited from a current-tab session's nontrivial job, excluding
custom-command/SSH profiles and clearing it when that indicator is disabled.
Apple's [Window menu update contract](https://developer.apple.com/documentation/appkit/nsapplication/updatewindowsitem(_:))
reflects edited status. This explains why a Dock bullet is not LocalBrain's
unknown-state dot. The reference informs state separation; no native Dock or
process-inference feature is copied. Raw local titles/screenshots stay private.

Use existing geometry/type/color/focus roles,20px icons, reported command signals,
painted-focus attention, tab grouping/four-pane/close/background behavior and the
shared48px header. No schema/runtime/input-adapter change. Inspect rendered before/
after, prove actual optical bounds rather than equal CSS boxes alone, and carry
the same assets into the app. Prior backend/native-input evidence keeps its scope.

## Corrected Interpretation And Verification Boundary

The initial question-mark proposal passed124 browser/14 native checks but was
rejected by the user. A subsequent neutral-circle proposal was also an
interpretation error. Its second browser attempt exposed an async QA-driver
race: it tried to type/click before the folder dialog opened. The driver now
waits for the actual open/enabled state rather than weakening hit testing.
Those proposal results remain historical, not final implementation acceptance.

The final user clarification is the original intended distinction: ✓ current,
small filled ● other foreground, ◇ background, plus a separate program-reported
braille title prefix. The local Dock read independently exposes window mark and
OSC title prefix, including a checked row with braille and bullets both with and
without braille. Shell command running is not agent activity. Feature/Spec and
current owners are corrected before final implementation validation.

Frontend uses existing OSC0/2 metadata, preserving aliases and title-animation
updates without replacing focused rename/menu DOM. Shell descriptions and
result/fault badges remain separate; no backend or runtime upgrade is needed.
Final synthetic stream/browser, source/package and native focus/lifetime checks
are pending. Existing physical IME/VoiceOver/sleep/resource limits remain.

The first corrected browser attempt exposed a tab-close target replacement
around command completion/acknowledgement. Tab status updates now replace only
the relevant badge/description, keeping tab buttons intact; the next129-check
browser run passes that boundary and the full prior interaction packet. The
final simple rhombus replaces the Material gem artwork. A later cold-setup run
hit the driver's former short readiness timeout without runtime exceptions;
QA now uses an explicit90-second cold-preparation bound and30-second normal
readiness bound, preserving state/hit-test assertions. Final frozen-source
browser/native validation remains the acceptance gate, not the intermediate pass.

The close failure recurred. A task-owned synthetic event trace established the
actual boundary: xterm focus acknowledged an unseen completion after click
coordinates were read; removing its badge shrank the tab, so the following
mousedown/up hit the empty strip. Stable DOM alone was insufficient. The final
CSS keeps the title control at the existing12rem bound with a flexible ellipsis
label. Program frames and result badges now change within that width, and QA
checks actual × position as well as node identity and the original stop action.
The Material `diamond` was gem artwork; the requested ◇ uses a simple unfilled
geometric rhombus in the same20px navigation slot.

## Final Delivery — 2026-11-14

The final frozen UI passes130 synthetic real-PTY Chromium checks and76 Node
checks;11 desktop-build checks pass. Actual packaged Tauri WebView passes15
checks, including three captured program-title frames (first/next/removed) while
the current check, alias and shell-running description remain independent;
active/inactive/restored borders; last-close/recreate; split/menu/move; normal
Quit/source removal and suspension/relaunch with preserved generation/PTY PIDs.
The first native title probe exceeded the ASCII keyboard driver's15-second
limit on a long command; the final probe types a short invocation of an owned
synthetic script. It does not relax input or state assertions. Physical IME is
explicitly skipped; native keyboard/suspension is not physical pointer/sleep or
assistive acceptance. Primary inspected final wide/narrow/background/title/focus
renders against the preserved before source and actual Dock reference.

Final app input fingerprint f3aa94d00d85d19dbac1bdeb5586f1cb0131776943b7b0fdded7529f078f8e66
(431 inputs); ZIP SHA256 d3251fab0af7fc1ace8e8f124685cc818e6c64951a1a96a2dedc81293c108a07,
309809532bytes. Deep strict signature, ARM64 executables, source asset bytes and
all319 payload entries pass. Runtime payload remains66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8
with Node24.15.0/ABI137/NAPI10. No user manager upgrade or installed-app replacement.

The original guarded HTTP host is restarted with its exact argv/environment,
without stopping the manager. Served HTML uses the final static version and all
three changed JS/CSS modules match source. Immediately before/after, the one
then-live user terminal retains the same generation, ID and PID. Earlier read
snapshots had more jobs; no job is stopped or altered by this UI correction.
Final Feature/Spec/policy/guides/evaluation/catalog reconciliation, privacy/link/
whitespace checks and private evidence/owned cleanup close this increment.
[Eval0173](../evaluation/eval-0173-terminal-status-indicators.md) owns calibrated
verification limits; earlier proposal passes and failed observations remain
historical evidence, never relabeled as final-artifact acceptance.
