# SPEC-0177: Terminal Activity And Background Rail

- Status: `approved`
- Feature: [FEAT0177](../feature/feat-0177-terminal-activity-and-background-rail.md)
- Run: [Run258](../run/run-20261114-258-terminal-activity-and-background-rail.md)
- Profile: `frontend-product`; frontend → integration/docs.
- Design: `screen-alignment`, `extend`; shared rail/control/type/focus roles.

The pure frontend indicator owns precedence: hidden ◇, current ✓, any live
pane reporting OSC133 command running ●, all panes live and reporting prompt ◦,
otherwise no painted glyph in the reserved20px slot. A live shell/process alone
does not establish a command. Ring and dot both paint a320-unit outer diameter
inside960-unit SVGs; the ring's radius128 plus64-unit stroke matches the dot's
radius160. Preserve labels for absent signals, and separate completion/fault
badges. Update nonselected tab indicators in place before rename/drag/cache
guards, preserving tab buttons and their12rem title width/close targets.
Program title braille remains exact pass-through, not inferred agent activity.

The rail footer owns a button disclosure and an independently scrolling hidden
tab list. Reuse native button keyboard behavior, `aria-expanded`/`aria-controls`,
shared32px desktop/40px narrow targets and the existing rail overlay. No modal
remains. A row restores its exact tab and focuses input; its × ends only that
tab's expected generation/terminal scope without confirmation. Include group
context/count when useful and accessible explicit restore/end names. Retain
program glyphs, unread results/errors and aggregate header attention/counts.

On the first successful model, expand if hidden work exists. Explicit Hide or
the all-background empty-state action expands/reveals the rail; ordinary refresh
does not override manual collapse. Restoring on narrow widths returns to the
canvas. Refresh preserves surviving row focus; removing the focused last row
returns focus to the disclosure. Closing from Management retains modal focus.
The footer is bounded by the available rail height; hidden rows scroll while
the disclosure and utility controls remain reachable. No new persisted setting.

Verify actual ring/dot painted size, old unknown versus reported prompt, running
and grouped precedence, exact program frame changes/removal, stable rename/menu/
close targets, inline reveal/collapse across polling, hidden attention/restore/
end and many-row/short/narrow containment. Reuse the real synthetic PTY browser
packet and Node checks, then rebuild the app and test the actual native inline
hide/restore and existing lifecycle. Existing physical IME/VoiceOver/sleep,
minimum-platform/resource and human visual limits remain explicit. No backend,
schema, protocol, runtime payload, input adapter or user-process change.
