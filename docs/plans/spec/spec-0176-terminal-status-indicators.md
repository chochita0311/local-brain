# SPEC-0176: Terminal Status Indicators

- Status: `approved`
- Feature: [FEAT0176](../feature/feat-0176-terminal-status-indicators.md)
- Profile: `frontend-product`; frontend → integration/docs.
- Design: `screen-alignment`, `extend`; existing shared Material icons and constitution.

Primary marks describe view state only: existing `check` for the selected tab /
focused pane and task, a small filled `view_dot` for other foreground items,
simple outlined `view_diamond` rhombus for hidden tabs. All use the20px navigation slot;
their intentional optical differences carry meaning, independently of shell
integration, execution or result. Labels name current/open/background. There
is no default unknown/question icon.

`programTitle` splits only a leading reported braille character followed by
whitespace from the OSC0/2 title, preserving the remaining title. Show that
exact glyph in a separate mono slot next to tab/pane/task/hidden names, and
remove it when the program removes it. Preserve user tab names. A grouped tab
uses the focused pane's reported glyph when available, otherwise its first
reporting pane. Update indicators from current stream metadata without
rebuilding rename editors, drag targets or focused list actions on every frame.
Keep the tab title control at its existing12rem bound with ellipsis so program
glyphs and completion acknowledgement cannot move its separate × hit target.
This is title presentation, not an agent-state protocol or an inference from
process liveness / quiet output. Ordinary long commands do not fabricate an
agent spinner. Existing manager OSC titles already supply the data; no backend,
protocol, schema, API, shell hooks or input-adapter changes.

Keep explicit shell metadata and priority/result counters. The status bar and
descriptions name shell command running, prompt waiting or unknown separately.
Unseen completion, faults and termination can add a result/status badge without
replacing the view mark or program glyph. Hidden rows keep their ◇ and reported
program/result indications. Preserve restore/end actions and refresh/focus.

Track document/window focus in a page-local class. Keep selected IDs/ARIA and
live glyphs unchanged on blur/visibility changes, but use shared neutral borders
for the remembered selected tab/pane while inactive. Focus restores selection
emphasis. Reuse existing painted/input-focused completion acknowledgement;
header/menu focus, selection and hiding alone do not acknowledge completion.

Verify view marks independently of unknown/prompt/running/result, actual OSC title
frame changes/removal while shell execution remains running, preserved aliases
and focused rename/menu DOM, unseen/seen results, hidden activity/completion, and
inactive/active view cues. Reuse the
everyday synthetic PTY browser packet and Node state checks, then rebuild the
app and verify native focus/menu/lifetime against the same assets. Preserve
existing physical IME/VoiceOver/sleep/platform/resource limits.
