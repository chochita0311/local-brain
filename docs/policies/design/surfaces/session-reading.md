# Session Reading Design

This is the durable Session/Subsession reading companion of the [Design Constitution](../design-constitution.md).
[Sessions](../../project/sessions.md) owns source identity, normalized conversation
and direct-reference eligibility. This file owns metadata/copy presentation and
conversation role/completion appearance.

## Metadata And Conversation

- Session detail places the source-native identifier in the first metadata-strip
  cell under **Session ID**. Mono text shows at least eight characters, extending
  on collisions with different stored IDs; shorter IDs remain complete. Full
  values remain available through a hover tooltip and an accessible focus
  description; the adjacent ghost button copies the complete ID.
- The copy button uses one custom tooltip for hover/focus explanation and
  `Copied!` confirmation, with no native `title` tooltip. Pointer hover
  uses a short entry delay; keyboard focus also exposes the explanation.
  Both messages stay centered on the button rather than following pointer
  movement. The tooltip stays outside the clipped metadata frame, within
  horizontal viewport bounds, and flips above only when space below is
  insufficient.
- A successful clipboard write starts a two-second copied state: the glyph is
  a success check and the tooltip says `Copied!`. Leaving or blurring the
  button hides the tooltip without cancelling that state; reentry before its
  deadline still shows `Copied!`. At the deadline the glyph and accessible
  label reset together, and a still-hovered/focused button returns to its copy
  explanation. Repeated successful copying restarts the deadline without
  flashing the idle glyph. Escape, scrolling and resize dismiss the tooltip
  without resetting the copied state; Escape remains dismissed until a new
  entry, focus or copy action. Control geometry and surrounding metadata stay
  stable. Only copy outcomes receive live announcements, and no copy outcome
  uses the footer toast. Failure retains the idle glyph, exposes and selects
  the full value for manual copying, and uses the same anchored recovery
  message for up to five seconds.
- The Session metadata strip sizes activity time to its content and gives
  remaining wide-layout space to the branch. Its own reading-column width
  enables six columns from the existing 700px narrow threshold. Below that,
  up to three columns fit with a minimum cell width of four standard controls,
  reducing columns as needed; narrow viewports use two columns and touch targets.
  Source cues, shell, conversation frames and reading width retain their roles.

- Session and Subsession conversation cards distinguish user-authored inputs
  with a very light blue input surface, an inset left accent and a stronger
  speaker name. Assistant messages normalized to `final_answer` from explicit
  source completion signals receive a stronger neutral perimeter frame. Phase adds no visible label, badge or
  status copy and conveys no task-success state. Commentary and unmarked
  assistant messages retain their ordinary card treatment. Speaker/source and
  time labels, message order, reading width and responsive flow stay consistent;
  frame geometry as well as color distinguishes the two emphasized roles.

## Copy Request Ordering

Stale asynchronous clipboard results cannot replace the latest attempt. A copy
action never changes Session identity, ingestion, navigation URLs or starts a
native resume command.
