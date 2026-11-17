# EVAL-0172: Terminal Action Hierarchy

- Status: `complete`
- Result: `PASS` for the approved action hierarchy and technical web/app integration.
- Evidence Coverage: `partial`; physical/assistive native acceptance remains separate.
- Feature: [FEAT0175](../feature/feat-0175-terminal-action-hierarchy.md)
- Spec: [SPEC0175](../spec/spec-0175-terminal-action-hierarchy.md)
- Run: [Run256](../run/run-20261113-256-terminal-action-hierarchy.md)
- Profile: `frontend-product`; primary design, functional and UX evaluation.

The tab toolbar owns group creation/actions; each pane header owns its exact
split source, folder-choice menu and close action. A workspace move is a checked
same-panel action list with back, rather than an OS select layered over the
menu. Rendered row height changes37.6875→32px on desktop through shared label
type/compact padding; narrow rows retain40px. No Settings selector, shared header,
backend/API/schema, input adapter or runtime payload source changed.

| Verification | Observed result |
| --- | --- |
| Chromium with real synthetic PTYs |118 PASS, no runtime exceptions/interception failures. Pane source cwd/shell despite another focused pane; initial down/four-pane grid; tab/menu hierarchy; row/trigger geometry, clipping and keyboard/back/Tab; long names/list end reachability; polling focus, stale-context dismissal, failed move/retry and exact IDs/PIDs/writable input; previous close/background/reorder/settings/recovery/zsh/viewport cases; confirmed peer-removal focus. |
| Viewports and visual inspection |1440/920×400 and700/320×800 for menu geometry, plus existing wide/narrow packet. Primary inspected synthetic before/after tab menus, Settings family, wide checked chooser, narrow long list and live zsh pane header. This is no claim for every tiny-height combination. |
| Configured checks |75 Node terminal tests and11 desktop-build tests pass. Asset/syntax/docs/privacy/diff checks pass at the browser boundary; final owner docs will be checked again. No backend/input implementation change requires a fresh full Python suite; earlier evidence retains its original scope. |
| Development host |Current host already serves the new template and byte-identical JS/CSS. All3 freshly observed execution IDs/PIDs and generation are identical after verification. No restart/manager update. |
| Final app/package |319 runtime entries match manifest size/hash/mode; Node24.15 arm64 ABI137/NAPI10, helper architecture, deep/strict signature, bundled template/JS/CSS and431-input source identity pass. App and ZIP rebuilt at the existing dist owner. |
| Packaged host |10 PASS with `--backend-only`: isolated relocated app, auth HTTP/WS, cold offline creation/four-pane API, new-zsh prompt/running/error, presentation order, Quit/source-app removal/app-less management, process suspend/resume/relaunch, exact stop and retained empty workspace metadata. This is not WebView, physical sleep or active typing evidence. |
| Actual new native window |13 PASS after owner unlock, with IME explicitly skipped. Real Tauri pane splits/max-four, last-close/recreate, named groups, checked workspace moves in both directions with exact PIDs, zsh, minimize/red close/Dock, Quit/path removal/relaunch and exact stop. The new chooser uses OS keyboard focus/Space/arrows/Enter. Primary inspected actual chooser and four-pane screenshots. Previous candidate's12 checks remain historical evidence. |

The focus fix moves recovery to actual confirmed pane unmount: a later poll can
supersede the stop caller's read, so the initiating callback alone cannot own it.
Layout/workspace unmounts with still-present terminal records remain distinct.
The peer-removal case and last-shell close/busy-retry cases pass. Original failure
attempts and the Enter event diagnostic remain private evidence; the latest pass
does not relabel those failed attempts as successful.

The package/host and required actual native-window gates pass. Initial screen
lock was resolved by the owner. All3 observed user execution IDs/PIDs and generation are preserved,
with no HTTP restart. Primary's semantic review traced pane action ownership,
one menu position/keyboard owner, move failure/retry and actual removal focus;
no independent-worker approval or human visual acceptance is claimed.

Build input: `67d304d404b0865b1f510d38e8e87ad493f14cc51114a71a32e43c32f04bcad1`;
app988233819 regular-file bytes; ZIP SHA256:
`fad443a9af9e7cab78f02d73e590794fb3858b8eb5227025867328746b4ecc43`.
Payload remains `66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8`.
No installed-app replacement, notarization or publication.

Prior native Korean IME intermittence/failure,
external AX modal exposure, physical input/VoiceOver/real sleep/minimum OS/resource
and human visual acceptance remain with [Eval0170](eval-0170-persistent-terminal-workspaces.md).
This increment does not add Codex's proposed multi-folder registry or complete
the remaining Python-to-Rust migration.

The initial lock preflight and resumed driver failures remain separate evidence:
AXPress-only disclosure activation failed; process-targeted pointer input did not
open the menu; the guarded WindowServer-pointer probe refused its covered target.
Those unused driver paths were removed. The final13-check packet uses OS keyboard
navigation and the unchanged delivered app. This neither proves physical pointer
or VoiceOver behavior nor relabels the earlier attempts as successful.
