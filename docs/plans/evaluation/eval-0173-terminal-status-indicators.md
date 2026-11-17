# EVAL-0173: Terminal Status Indicators

- Status: `complete`
- Result: `PASS` for the approved view/program separation and technical web/app integration.
- Evidence Coverage: `partial`; physical/assistive and human visual acceptance remain separate.
- Feature: [FEAT0176](../feature/feat-0176-terminal-status-indicators.md)
- Spec: [SPEC0176](../spec/spec-0176-terminal-status-indicators.md)
- Run: [Run257](../run/run-20261113-257-terminal-status-indicators.md)
- Profile: `frontend-product`; primary design, functional and UX evaluation.

The corrected legend separates ✓ current, small filled ● other open foreground
and simple outlined ◇ hidden/background from the program's reported leading
braille title glyph. Old uninstrumented and new integrated shells use the same
view criteria. Actual title frames/removal preserve manual tab names; neither a
live agent CLI nor shell execution/text/silence implies agent thinking or input
need. Shell command descriptions and relevant result/fault badges stay separate.
Completion attention still requires actual painted input focus in an active
window. No backend/API/protocol, runtime or input-adapter migration.

A synthetic event trace identified × movement when focus acknowledged completion
between coordinate lookup and mousedown: the disappearing badge shrank the tab.
The title control now retains its existing12rem bound with ellipsis and stable
buttons. Both target identity and painted position are verified across program
frames and command completion/acknowledgement. View glyphs share20px slots; the
small foreground dot and larger hollow rhombus differ intentionally by meaning.
The Material gem is not used for the rhombus.

| Verification | Final observation |
| --- | --- |
| Chromium, real synthetic PTYs |130 PASS. Independent current/open/background marks; program first/next/removed frames while shell remains running; alias, rename/task DOM and close-position stability; hidden program/completion, painted-focus acknowledgement, real zsh, four panes, menus, close/recreate, drag/order/move/recovery and320/700/920/1440px containment. No runtime exceptions/interception failures. |
| State/assets/build checks |76 Node tests, terminal asset build/check and11 desktop-build tests PASS. |
| Actual packaged WebView |15 PASS using AX and process-targeted OS keyboard actions in a relocated synthetic app. Captured title frames distinguish program glyph from current check and shell running; native alias/PID, new/last-close, split/workspace/menu move, focus, minimize/close/reopen, normal Quit/source-app removal and suspension/relaunch retain their stated scope. |
| Design/interaction inspection |Primary inspected final wide/narrow, hidden running/completed, actual native program-frame and active/inactive/restored screenshots. Inactive borders are neutral; current selection remains and emphasis restores. Shared shell, type/control/color roles and source contracts preserved. |
| Bundle integrity |ARM64/signature/source assets and all319 runtime files verified. Final source fingerprint f3aa94d00d85d19dbac1bdeb5586f1cb0131776943b7b0fdded7529f078f8e66,431 inputs. Runtime66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8 unchanged. |
| Live development delivery |Guarded HTTP-only restart preserves the then-live terminal's generation/ID/PID. HTML asset version and all changed served module bytes match final source. No user terminal input, hook injection, service stop/upgrade or installed-app replacement. |
| Reference |Explicit local iTerm2 3.7.6 Dock inspection/cancel shows independent AX window mark and title braille, including a checked row with braille. Pinned official code qualifies its native edited/job bullet; LocalBrain follows the user's explicit view legend. Raw local titles/images stay private; no native Dock implementation/equivalence claim. |

ZIP SHA256 d3251fab0af7fc1ace8e8f124685cc818e6c64951a1a96a2dedc81293c108a07,
309809532bytes. The question-mark and neutral-circle proposals and their passes
are superseded interpretation errors. The retained attempts also record an async
folder-dialog QA race, close-position failures, a short cold-preparation timeout
and a long native synthetic typing timeout. Final checks use actual dialog
readiness, bounded cold preparation, stable close geometry and a short owned
script invocation; state/hit-test assertions remain intact.

Native15 uses `--skip-ime`. Physical Korean IME, pointer interaction, VoiceOver,
real Mac sleep, minimum-OS/resource and human visual acceptance retain the
explicit limits in [Eval0170](eval-0170-persistent-terminal-workspaces.md). Process
suspension is not physical sleep. No new full backend-suite, typed agent-state
protocol, live-agent internal-state certification or whole-Rust completion claim.
