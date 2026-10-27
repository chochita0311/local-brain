Sessions lets you revisit imported Codex and Claude Code conversations. Use the list for reading and the chart for a view of recorded activity over time.

## Find and read a conversation

1. Open [Sessions](/sessions), choose **All** or a source profile, and narrow the working path if needed.
2. Keep **List** selected to browse conversations. Use **Projects** for the Session-derived working-path grouping.
3. Open a Session to read its conversation and inspect its native Session ID, last activity, path, and recorded branch.
4. Follow a **Subsessions** entry to read a child conversation, then use the parent or inventory return link to go back.

The conversation view shows messages. Original event counts also include tool activity that the reading view hides, so they need not match the message count. A missing current working folder does not by itself erase an imported conversation.

The Session ID display is shortened for reading; use its copy control when you need the full native identifier.

Path labels use `~` for the home directory and `~/…` for folders within it; paths elsewhere are shown in full. Saved locations and historical Project attribution remain unchanged. For example, `~/Projects/app`, `~/Project1`, and `~/Project2` all follow the same home-directory rule.

## Keep a Session handy

Use a pin control in List or Session detail to add a primary work Session to **Pinned Sessions**. Unpinning removes that shortcut, not the original conversation. Subsessions are reached through their parent rather than pinned independently.

## Explore Chart

Switch **List → Chart** while retaining the source and working-path scope. The chart uses recorded times, launch folders, and branch metadata.

- Use the Project selector to show or hide folders. Choices are saved for the current scope; they do not delete Sessions.
- Use **− / +** to change scale and **Fit all** (`전체 보기`) to see the whole chart.
- Hover or focus a node to inspect its preview; selecting it keeps the preview open. Use the preview's **Session detail** action to read it, or **Show activity times** to inspect its recorded events.
- Use **Go to selection** (`선택으로 이동`) when you want to return to a selected Session at a readable scale. Use **Shift + wheel** to move horizontally; **⌘/Ctrl + Shift + wheel** adjusts time spacing.

This is an observation chart, not a Git ancestry graph or an inferred work plan. Recorded branch labels do not prove that two Sessions are causally related. If Chart cannot load, use its List fallback.

## Keep the inventory current

The **Sync** (`동기화`) button requests collection of registered Session sources. Automatic collection also runs on the interval in [Settings](/help/settings). Background completion does not interrupt the current reading view; reopen or reload it for new records.

Before collecting a source, confirm its registration, record-folder location, and read access in Settings. Selecting a folder or a detected candidate is not registration. If records have moved, reconnect the same profile rather than adding an overlapping copy. Check source and working-path filters when locating an imported Session.

For a remembered phrase, try [Search](/help/search). For usage totals rather than conversation browsing, see [Sessions Dashboard](/help/sessions-dashboard).
