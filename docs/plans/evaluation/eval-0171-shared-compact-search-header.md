# EVAL-0171: Shared Compact Search Header

- Status: `complete`
- Result: `PASS` for the shared compact header and preserved navigation.
- Evidence Coverage: `partial`; physical/assistive native acceptance remains separate.
- Feature: [FEAT0174](../feature/feat-0174-shared-compact-search-header.md)
- Spec: [SPEC0174](../spec/spec-0174-shared-compact-search-header.md)
- Run: [Run255](../run/run-20261113-255-shared-compact-search-header.md)
- Profile: `frontend-product`; design, functional and UX evaluation.

The shared stylesheet owns the48px desktop header and32px search field on all
sidebar destinations. Terminal inherits it. Narrow inputs preserve the existing
40px token. Native titlebars remove block padding so the input stays inside the
48px frame and body/sidebar offsets stay aligned. No route/query/shortcut,
data/schema, input-adapter or process contract changed. Primary inspected actual
Sessions Dashboard and native startup screenshots for density, readable labels,
containment and consistent shell placement.

| Verification | Observed result |
| --- | --- |
| Shared browser |121 PASS;11 sidebar routes at1440/320px, including both Sessions screens and Terminal; native-class titlebar at1440/920/700/640px, input vertical containment, body/rail offsets, short-window footer, Back/Forward, search, sidebar shortcuts, focus, modal guards and delayed navigation. No runtime exceptions or unexpected failed requests. |
| Actual candidate app |12 PASS: native startup/Terminal, authenticated cold creation, last-close/recreate, workspace/four panes, integrated zsh, minimize/red close/Dock, Quit/removal/relaunch and exact test-service stop. IME explicitly skipped. Screenshots support the common native startup header; browser class simulation is not physical window evidence. |
| Packaging |319 runtime entries, size/hash/mode/ABI/arm64/signature and current source/assets (including shared styles.css) pass. Payload unchanged.11 desktop-build tests, asset check, catalog/link/privacy/diff checks pass. |
| Backend regression reuse |Run254's1700 Python checks (49 opt-in skips) and separate zsh/Node/Terminal packets retain their original scope. Python/manager/Rust/input code is unchanged; this CSS-only increment did not rerun or rebrand that full suite. |
| Live development |HTTP host alone restarted with original argv/environment; all6 existing terminal IDs/PIDs and generation preserved. No user manager stop/upgrade. |

Earlier attempts exposed stale harness expectations for the Docs icon DOM and
removed `mode=keyword`, plus geometry values that needed58→48 updates. The first
narrow assertion incorrectly expected44px; same-screen before/after measurements
show40px in both. This corrects the documentation value in Eval0170 without a UI
size change. Newly visiting Terminal also exceeded macOS IPC-path limits in the
long evidence directory; the fixture now uses an owned short runtime path. Those
attempts remain failed observations; the final121-check run passes.

The Codex project investigation is a static package/screenshot/official-document
comparison recorded in the [design plan](../design/terminal-workspace-design-plan.md#codex-project-reference--2026-11-13).
It identifies a missing attached-folder registry/primary switcher in LocalBrain;
it does not implement that schema or claim runtime removal/permission behavior
was tested. No user Codex project or settings were changed.

Final build input:
`30daa684c6e187547587f22f657e1e7d6c8a008a159674459326516567a4512a`.
App regular-file bytes:988228391; ad-hoc signed. ZIP SHA256:
`014741ed85ec381d24682799cba2367e6165d967bbef21910505b14ed27f8678`.
Outputs remain `dist/LocalBrain-apple-silicon/LocalBrain.app` and
`dist/LocalBrain-apple-silicon.zip`; no installed-app replacement or Git write.
Prior native Korean IME failure/intermittence, external AX modal exposure,
VoiceOver/physical-input/real-sleep/minimum-OS/resource and human visual limits
remain with [Eval0170](eval-0170-persistent-terminal-workspaces.md).
