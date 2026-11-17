# SPEC-0175: Terminal Action Hierarchy

- Status: `approved`
- Feature: [FEAT0175](../feature/feat-0175-terminal-action-hierarchy.md)
- Profile: `frontend-product`; frontend → integration/docs.
- Design: `screen-alignment`, `extend`; current constitution and Settings/menu family.

The tab toolbar creates/manages terminal groups. Each pane header owns compact
right/down split icon buttons and its existing folder-choice menu/close action.
The selected source is that pane, even when another pane previously held input.
At two or more panes, Add split keeps the current2×2 behavior; four disables
creation. Shift+Escape retains its pane-menu focus target and TUI Escape is unchanged.

The tab menu has a Move to workspace action. It replaces that panel's contents
with a back control and workspace action rows; current membership has a check.
There is one popup surface, no OS select or overlapping nested popup. Rows use
shared type, padding, focus, disabled and control-height roles. Long names remain
readable in bounded viewport width; a long list scrolls to its last item.
Pointer, Arrow keys/Home/End, Enter/Space, Escape, outside click/focus and peer
menu switching work consistently. Refresh must preserve an open chooser and its
focused destination; a changed active tab invalidates that old action context.

Position all Terminal action menus with one implementation, anchored to their
own trigger and bounded by the viewport. Prefer below, flip above only when
necessary, and scroll when neither side fits. Do not alter Settings controls.

Verify real synthetic PTYs in Chromium, exact source cwd/shell, four-pane bounds,
tab move preserving IDs/PIDs and input, compact row geometry, viewport edges,
refresh/focus/dismissal and preserved everyday Terminal behavior. Verify the
packaged app's actual split/menu/move controls and lifetime after rebuild. Keep
earlier physical IME, AX, VoiceOver, sleep/platform/resource evidence limits.
