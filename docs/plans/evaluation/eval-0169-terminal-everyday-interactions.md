# EVAL-0169: Terminal Everyday Interactions

- Status: `complete`
- Result: `PASS` for the shared interaction increment and observed native window/package contracts.
- Evidence Coverage: `partial`; native OS input-method acceptance and human visual acceptance remain separate.
- Feature: [FEAT0172](../feature/feat-0172-terminal-everyday-interactions.md)
- Spec: [SPEC0172](../spec/spec-0172-terminal-everyday-interactions.md)
- Run: [Run253](../run/run-20261113-253-terminal-everyday-interactions.md)
- Related native integration: [FEAT0171](../feature/feat-0171-native-terminal-integration.md), [Run252](../run/run-20261113-252-native-terminal-integration.md).
- Profile: `fullstack-product`; contract, functional, design and interaction evaluation.

## Accepted Interaction Boundary

Confirmed shell exit removes its pane and empty tab/folder, regardless of exit
code; cleanup/input faults remain inspectable. A live shell's completed command
never closes it. Existing generation-bound stop retires records; observational
HTTP reads do not perform process actions. Background hides the whole tab from
the foreground task list and strip while retaining execution, with a separate
footer restore/end list and reported attention. Multi-pane scope is named.

Active title click/F2/menu edits inline, Enter/focus-out saves, Escape cancels,
composition is preserved and failed saves keep drafts. Pointer drag and keyboard/
menu alternatives reorder within a folder. Private generation-tagged tab IDs
preserve presentation across hosts without changing execution or hidden slots.
Snapshot validation and atomic publication are separate from manager metadata;
no cross-store transaction is claimed. Individual pane/tab/task End has no
confirmation; bulk/service operations retain exact confirmed scope. Task rows
have reachable focus/background/rename/end menus. Unknown state uses a neutral
terminal icon; explicit reported command states retain distinct meanings.

The primary inspected source responsibilities and actual flows. The host owns
only presentation order, the manager owns execution, and the shared GUI owns
interaction state. No Node/Rust protocol or runtime payload change was required.
Named source challenge findings and informed recheck repairs are recorded in
Run253. Browser witnesses cover rejected-End recovery both on an existing pane
and a pane recreated during a held recovery read, compact menu rename, and
failed order POST plus failed subsequent GET. Hidden-to-hidden swaps are rejected.

## Observed Verification

| Check | Result and limit |
| --- | --- |
| Shared Chromium, real synthetic PTYs |80 PASS: normal/nonzero/split/background exit, no individual dialogs, retained process IDs, inline save/IME composition/Escape/failure/blur, actual pointer drag/reload/keyboard, rollback and recovery races, fonts/unknown states, 4-pane limit and 1440/920/700/320px containment. Browser composition events are not OS IME evidence. |
| Presentation/API |6 PASS: no-write reads, generation/membership/folder/hidden slots, private/no-link/bounded files, atomic failure, same-origin routes and single-stop generation forwarding. Generation change just before publication is modeled synthetically; mutation RPC absence does not exclude observational IPC. Existing host route tests9 PASS. |
| Node |75 PASS; helper/status/order tests, not native keyboard evidence. |
| Full Python |1684 run, no failures,47 optional process tests skipped. |
| Actual Rust/PTY |Initial14-case run:13 pass and1 cold service-start confirmation timeout. That one case then passed three isolated repetitions. The failure overlapped an app build; causation is unproved, and there is no single all-pass14-case run in this attempt. The unchanged payload's earlier14-case pass stays historical. |
| Final packaged app |319 files, exact signed digests/sizes/modes, canonical manifest identity, Node ABI/platform, arm64 binaries, deep/strict signing, packaged UI/fonts, helper process snapshot shape and current source identity PASS. |
| Actual final native window/lifecycle |10 PASS with `--skip-ime`: relocated signed app/authenticated WebView cold create, direct last-close/recreate, two folders/three tabs/4 panes, host order save, minimize/red-close/Dock reopen, normal Quit/source-app removal, suspension/relaunch on a new port with identical generation/IDs/PIDs/order, and exact-scope stop. SIGSTOP is not Mac sleep. |
| Live development web |HTTP host restart preserves original argv/environment/cwd in memory and all4 existing terminal IDs/PIDs/generation. Final served CSS/cache version and presentation response confirmed. No terminal stop/update/install sent to user scope. |

The native screenshot revealed a real footer/statusbar clipping defect: the
native titlebar class is on `html`, while Terminal's selector expected it on
`body`. Correcting that selector restores the available height. Final Chromium
geometry and the final app's owned-window screenshot show the footer/statusbar
inside the viewport. Shared shell/other routes retain their existing rules.
Screen-alignment extend mode preserves the constitution, tokens, Sessions title
interaction and existing compact frame. Visual inspection covers these synthetic
states, not product-wide design or human preference acceptance.

## Benchmark Evidence And Decisions

Named research_worker compared four official product source sets under the
primary's research-sadr packet. These are documentation/source observations,
not side-by-side installed-app tests or proof of universal defaults.

- Exit policies vary: [Ghostty](https://ghostty.org/docs/config/reference#wait-after-command)
  documents close/wait behavior; [Apple](https://support.apple.com/guide/terminal/change-profiles-shell-settings-trmlshll/2.15/mac/27)
  and [iTerm2](https://iterm2.com/documentation-preferences-profiles-session.html)
  offer alternative exit actions. LocalBrain follows the user's explicit exit behavior.
- [iTerm2 Buried Sessions](https://iterm2.com/documentation-buried-sessions.html)
  continue outside windows with a separate restore list. LocalBrain retains its
  existing whole-tab hide scope and makes that scope explicit.
- [iTerm2](https://iterm2.com/documentation-general-usage.html) and
  [VS Code](https://code.visualstudio.com/docs/terminal/basics#groups-split-panes)
  document mouse reorder. [VS Code context actions](https://code.visualstudio.com/docs/terminal/basics#managing-terminals)
  include rename/kill/split/move. Inline rename follows this user's Sessions
  consistency request; visible row ellipsis is a LocalBrain choice.
- [VS Code appearance](https://code.visualstudio.com/docs/terminal/appearance#icons)
  distinguishes icons/status. The neutral terminal icon does not infer prompt or
  success. [Ghostty confirmation](https://ghostty.org/docs/config/reference#confirm-close-surface)
  and other products expose different policies; no-confirm individual End follows
  explicit user instruction, not an asserted industry default.

Apple evidence is guide2.15/macOS27, whereas the actual host is26.5.1. Rolling
documentation/source was not version-fingerprinted. Existing pinned Herdr
structural/payload comparison remains in [Eval0168](eval-0168-native-terminal-integration.md):
OSC7501, remote/agent automation and reboot replay were not added.

## Native Input Counterevidence And Remaining Acceptance

Do not count the native IME probe as passed. One early automated Tauri attempt
produced `한글`, but repeated attempts produced doubled standalone jamo or
`gksrmf`. In an instrumented, separately re-signed diagnostic app copy, the
12ms driver generated ordinary non-composing Hangul keydown/insertText events,
without composition/replacement events. Slower45ms delivery also failed the
expected string, producing ASCII. This establishes an unreliable input-method
test path and an unresolved duplicate-input observation; it does not establish
whether ordinary physical Korean input is correct or whether the underlying
cause is solely the driver. No input-adapter/runtime change is hidden here.

Prior six-scenario WKWebView evidence used an in-process AppKit event queue and
readiness/keydown observation; it cannot certify this Tauri path. Final native10
explicitly excludes IME. Valid target-app OS IME/rapid-input/clipboard/shortcut/
VoiceOver checks, human visual review, real sleep/wake, minimum macOS14 hardware,
recipient use, long-soak/resource budgets and whole-backend Rust parity remain
unaccepted. Revisit the input observation with a verified native event driver or
human keyboard evidence before claiming native Korean-input readiness.

Final source/build-input SHA256:
`21aebabf5689c7bb807f8faf39fd164fa9a161315802ab5758c4112a815634d1`.
App regular-file bytes:988200896, ad-hoc signed; no public notarization or installed
app replacement. Payload remains
`66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8`.
App/ZIP are under `dist/LocalBrain-apple-silicon/LocalBrain.app` and
`dist/LocalBrain-apple-silicon.zip`. Private stage evidence preserves frozen
sources, benchmark/review provenance, failed probes, final results and owned
synthetic screenshots; no durable reference depends on task scratch.
