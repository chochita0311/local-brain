# FEAT-0175: Terminal Action Hierarchy

- ID: `feat-0175`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Parent PRD: [PRD0030](../prd/prd-0030-macos-terminal-work-area.md)
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Authority: the user explicitly distinguishes tab groups from individual terminals, requests pane-level split controls, compact menu spacing and an aligned workspace move chooser that does not obscure its trigger.

Keep the tab toolbar's + and tab actions. Put right/down split controls in the
individual pane header, inheriting that pane's cwd/shell. Preserve the four-pane
limit and balanced layout. Compact Terminal action menus to the shared32px
desktop/40px narrow roles. Replace the native workspace move select with a
same-panel action list, with current workspace, back, keyboard and dismissal
behavior. Anchor menus below their trigger when space permits and contain them
within the viewport, including rail and lower-pane menus.

No process, API, persistence, input-adapter or multi-folder registry change.
Existing execution identity, close/background semantics, state signals, tab
editing/reorder, shared header and native lifetime remain in force.

- Spec: [SPEC0175](../spec/spec-0175-terminal-action-hierarchy.md)
- Run: [Run256](../run/run-20261113-256-terminal-action-hierarchy.md)
- Evaluation: [Eval0172](../evaluation/eval-0172-terminal-action-hierarchy.md)

Implementation, browser118/Node75/desktop-build11, rebuilt app319-file integrity,
packaged host10 and actual new native-window13 checks pass. The initial screen
lock was resolved by the owner. Actual pane splits and keyboard-driven workspace
moves preserve exact processes; lifetime/relaunch checks pass. Native IME/AX/
physical-input/VoiceOver/sleep/platform/resource and human visual limits remain
explicit in the evaluation. No installed-app replacement was made.
