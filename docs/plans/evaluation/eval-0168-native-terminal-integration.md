# EVAL-0168: Native Terminal Integration And Reference Comparison

- Status: `complete`
- Result: `PASS` for observed package/host checks; this is not whole-Feature acceptance.
- Evidence Coverage: `partial` at the initial delivery; see the subsequent window acceptance below.
- Feature: [FEAT-0171](../feature/feat-0171-native-terminal-integration.md)
- Spec: [SPEC-0171](../spec/spec-0171-native-terminal-integration.md)
- Run: [Run252](../run/run-20261113-252-native-terminal-integration.md)
- Profile: `fullstack-product`; contract, functional, design and interaction evaluation.

Subsequent [Run253/Eval0169](eval-0169-terminal-everyday-interactions.md) verifies
the rebuilt app's actual window/close/relaunch boundary and records its new build
identity. FEAT0171 now passes technical integration. The observations and build
figures below belong to the original locked-session delivery; native IME automation
did not pass in the subsequent attempt and physical/input readiness remains open.

The app contains the common Terminal workspace, fonts, authenticated routes and
self-contained Rust/Node/PTY payload. Packaging and actual Tauri-host lifecycle
checks passed at the initial delivery. Feature acceptance then remained pending actual window close/reopen;
physical Korean IME, shortcuts/clipboard, VoiceOver, real Mac sleep, minimum-OS
hardware, recipient use and sustained performance remain distinct unverified
claims. The Mac was screen-locked then, directly observed through the OS session
flag. The task did not unlock it or request new accessibility permissions.

## Initial Delivery Build And Actual Host Evidence

The final Apple Silicon app is under `dist/LocalBrain-apple-silicon/LocalBrain.app`
and its test ZIP under `dist/LocalBrain-apple-silicon.zip`. Ad-hoc signing passes
deep/strict verification; public signing/notarization is not requested. The app
contains 988,172,224 regular-file bytes, including existing optional local-model
libraries; this is not a memory measurement. Minimum macOS14 is declared while
the actual build/test host is 26.5.1, arm64, Python 3.11.15 and Rust 1.99.1.

Final payload ID is
`66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8`.
The source/build-input identity is
`46e0aacfeaa75dd7be5d27bc1c34ab27b7917f4fecbea300119465037a0a1d45`;
HEAD remains the recorded dirty-source baseline. The manifest identifies official
Node 24.15.0 darwin-arm64/ABI137/N-API10, pinned engine versions and upstream archive
SHA256. It lists 319 final files with exact signed bytes, sizes and modes.

A bounded read-only verifier executed the primary's fixed artifact script and
checked canonical payload identity, exact tree/no links, every file digest/size/
mode, actual Node ABI, arm64 executables, deep signing, process snapshot shape,
packaged Terminal/font bytes and source/build identity. It found a real late
license-file mode mismatch; finalization now normalizes all final file modes and
manifest mode, covered by a synthetic regression. A separate script expectation
incorrectly expected a dictionary snapshot instead of the defined list and was
corrected without changing product behavior. Final permitted verification passes.
The worker supplies command evidence, not semantic acceptance.

Final host packaging also includes the credential-free Rust child environment.
The app's per-launch credential stays in the HTTP/WS host; helpers receive only
launch keys and the terminal/HF/XDG paths needed for operation and public-cache
protection. The final rebuilt app repeats the artifact and actual host checks.

The final relocated signed app was actually launched through macOS LaunchServices
with synthetic data/cache/ingest roots and a synthetic shell HOME. Its seven
compound host checks pass:

1. Actual Tauri wrapper and packaged backend start in the selected isolated scope.
2. HTTP rejects a missing per-launch credential.
3. Cold API create prepares the bundled payload offline without user Node/npm;
   repeated last-stop/recreate and two groups with tab sizes1/1/4 work.
4. Real WS rejects missing credentials and accepts the current per-launch cookie
   with exact loopback Origin. Source/tests separately reject stale/query-only/
   cross-origin access before spawning the Rust stream.
5. Normal native Quit and temporary source-app removal retain exact manager
   generation and terminal IDs/PIDs; the stable cached launcher manages them.
6. Manager process suspension/resume and actual app relaunch retain those same
   executions without replay. SIGSTOP/SIGCONT is not physical Mac sleep evidence.
7. Explicit service stop with exact generation/IDs ends only the synthetic work.

The harness quits its app, stops its scoped manager and removes its copied app
and runtime. The actual user's jobs and installed app are untouched. The final
common browser 54, real Rust/PTY 14, Node 73 and full-Python evidence in
[Eval0167](eval-0167-rust-terminal-runtime.md) cover shared flows, not native UI.

One final synthetic host sample measured LaunchServices/backend/probe readiness
at 2.914s and 0.707s across the two launches. Cold create plus readback took 4.702s;
the next create after last-stop took 0.311s. With six idle synthetic shells,
20 sequential list requests had median 91.71ms and nearest-rank p95 = 100.86ms.
These are observations under the locked test session, not active WebView typing,
memory/CPU measurements, an approved resource budget or a Python/Rust comparison.

## Herdr Comparison

The named research worker read official Herdr app documentation/source and pinned
core v0.1.20 at `de97ea5ba5d6877a5e082316b4a1a5b4918e861f`.
This is source reference evidence, not a side-by-side installed Herdr UI test.

| Reference behavior | LocalBrain result and boundary |
| --- | --- |
| Spaces/folder work area, top tabs, split terminals | Shared upper folder groups, group-scoped tabs/+ and max4 panes; verified in common Chromium and native host API. One macOS app window, not multiple native windows. |
| Lower Agents status/attention; footer settings/update/machine actions | Lower cross-group terminal task/status list and footer settings/service recovery. LocalBrain lists generic terminals; remote machines, mods, agent launching and Herdr-specific automation are outside this Feature. |
| Put-away/settle and return to work | Hide/reopen preserves exact execution. LocalBrain hide removes its tab from the visible group strip; this is not a claim of identical Herdr put-away behavior. |
| Focused cwd can influence unnamed space/new tab | LocalBrain's canonical creation-folder group is immutable. New tab uses that group root; a split inherits focused pane cwd. This is the selected intentional difference. |
| Reported working/blocked/done/idle and agent metadata | LocalBrain supports explicit OSC133 command prompt/run/end, unknown fallback and rendered-input-focus attention. It does not implement Herdr OSC7501 blocked/question/auth/progress/child records; no wire/payload compatibility is claimed. |
| Restart/reboot may create fresh shells for retained records | LocalBrain does not restore processes or replay commands after system/service restart. Normal app Quit/relaunch reconnects surviving work. |

The pinned core encoder emits `ESC ]7501;key=value:key=value ESC \\`; title/msg
are base64 UTF-8. Callback states are idle/working/done/blocked/error/clear, with
unknown state enums discarded. Kind is absent/permission/question/auth, unknown
kind maps to absent, and progress must fit `u8`; callback strings use lossy UTF-8.
Raw parser handling before that callback is unverified. There are up to 255 child
records plus a root; a new child at capacity evicts the map iterator's first key,
while replacing an existing key does not. Empty-id clear removes all; an id clears
that record and its slash-descendants, not similarly prefixed siblings. Clear
still sets reported true. JSON status uses a nullable root plus records/reported
in a separate JSON-RPC event envelope; id is a records key. OSC itself is not JSON.
Schema requires only state, whose type is string rather than an enum. It describes
progress 0–100 but allows 0–255, so it does not prove raw acceptance of invalid state
or progress 101. Root newly entering blocked/error sets stuck; repeating that state
does not. Root leaving working increments turn, including blocked/clear/reset;
child-only changes do not. Seeing Done→Idle in a UI is not established by that code.
The bridge's 64KiB incomplete
sequence tracker is not established as an OSC payload limit. Raw parser acceptance
of terminators, invalid fields/base64/progress and total byte limits could not be
verified because the pinned Ghostty gitlink/parser was unresolved. Attention
across clients also remains unverified; another version was not substituted.
Evidence: [pinned status source](https://github.com/herdrdev/herdr-core/blob/de97ea5ba5d6877a5e082316b4a1a5b4918e861f/crates/herdr-core/src/status.rs),
[tagged bridge](https://github.com/herdrdev/herdr-core/blob/v0.1.20/crates/ghostty-vt/src/lib.rs),
[tagged schema](https://github.com/herdrdev/herdr-core/blob/v0.1.20/schema/hc.openrpc.json),
[official core guide](https://herdr.dev/core/).

## Initial Remaining Acceptance

The locked session returns an application reference where the AX window is
expected and refuses owned-window capture. Direct process/backend/API health
does not establish that a rendered window was operated. Early native QA attempts
therefore fail as unavailable UI evidence, not product success or proof of a
terminal rendering defect. The repeatable native harness detects lock before UI
work; `--backend-only` explicitly reports its narrower coverage. Once the user
unlocks the Mac, run it without that option to exercise actual last-pane close/
New, window minimize/red-close/Dock reopen, native Korean IME and reconnect.
Until then Run252 stays blocked and FEAT0171 stays approved, not passed.

That required window gap is now closed by Eval0169; the paragraph above preserves
the original stop condition. Native IME/physical input and the other platform
limits have not been accepted by that window result.
