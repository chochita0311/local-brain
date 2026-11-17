# FEAT-0176: Terminal Status Indicators

- ID: `feat-0176`
- Status: `passed`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Parent PRD: [PRD0030](../prd/prd-0030-macos-terminal-work-area.md)
- Required Evaluators: `design`, `functional`, `ux-heuristic`
- Authority: the user requests one consistent status-symbol standard, asks why the original terminal differs, and explicitly asks to inspect iTerm2's Dock menu for working, waiting, hidden and current-view distinctions.

The user specifies independent meanings: ✓ current selection, ● another open
foreground item, ◇ explicitly hidden/background. These view marks must be the
same for an old uninstrumented shell and a new integrated shell. Use a common20px
slot, a deliberately small filled foreground dot, a simple hollow rhombus and
the existing check shape. No question-mark or unknown-state default. Keep remembered selection
with quieter borders when the app window is inactive.

Separately pass through a leading braille activity glyph from the program's
reported OSC title, including live frame changes and removal. Preserve manual
tab names. A group represents its focused program when it reports a glyph,
otherwise the first reporting program. A long-lived agent process is not proof
that the agent is thinking; do not derive agent state from shell execution,
silence or output text. Show shell command state separately in the status bar
and descriptions, with result/fault attention as a separate badge. Existing
painted, input-focused acknowledgement and process lifetimes remain intact.
No backend/protocol migration, native Dock integration or OS multiwindow model.
The earlier question/circle proposals were an interpretation error and are
superseded; their verification does not accept this corrected implementation.

- Spec: [SPEC0176](../spec/spec-0176-terminal-status-indicators.md)
- Run: [Run257](../run/run-20261113-257-terminal-status-indicators.md)

- Evaluation: [Eval0173](../evaluation/eval-0173-terminal-status-indicators.md).
- Delivery: web130, Node76, desktop-build11 and actual native15 checks pass;
  final app/assets/runtime integrity verified. Physical IME/VoiceOver/sleep,
  minimum-platform/resource and human visual acceptance retain their prior scope.
