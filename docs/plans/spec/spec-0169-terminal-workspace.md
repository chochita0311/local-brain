# SPEC-0169: Folder Terminal Workspace

## Metadata

- Status: `approved`
- Feature: [FEAT-0169](../feature/feat-0169-terminal-workspace.md)
- Run: [Run249](../run/run-20261112-249-terminal-workspace.md)
- Profile: `fullstack-product`; lanes: contract/backend → frontend → integration/docs.
- Authority: current human continuation of the discussed screen and existing approved PRD boundary.

## Producer Contract

Each newly created tab publishes `cwd`, the realpath of its creation folder. It is immutable for that tab; OSC 7 updates only a pane's current cwd. Groups are the distinct tab cwd values, including hidden/exited retained tabs. Existing legacy snapshots without the field use the first pane's cwd only for display and remain subject to existing build incompatibility guards for creation.

Each terminal publishes `activity: {state, exitCode, completion}`. State is `unknown` until OSC 133; A/B means `prompt`, C means `running`, D after C means `finished` with a validated 0–255 exit code or null. D after B is aborted input and adds no completion; duplicate/out-of-order or malformed D is ignored. Completion is a monotonic in-memory counter on valid command-end transitions. No command text or output history is added. Shell exit/termination/error takes precedence over command metadata. OSC handlers consume only supported metadata and never execute shell code. Manager source fingerprints include the new producer module.

`GET /api/terminal/settings?launch=true` accepts an optional cwd override for an existing group or explicit folder. Validate the actual folder with the saved shell without persisting it; a deleted unrelated default does not block it. Pending creation retains its exact key/values and exposes Retry while gating other creations, including after first-group discovery. Older list sequences cannot regress newer stream metadata in one generation; generation replacement clears prior view state.

## View Contract

Keep an accessible logical Terminal heading and main landmark while removing the large heading/action row. Scope viewport containment to Terminal. The second rail has scrollable folder groups above cross-group task rows, then hidden recovery/settings/management. Top tabs belong to the selected folder; + creates a visible focused tab. Inline split actions target the focused pane; pane menus retain exact-target actions and Shift+Escape. Bottom status gives focused cwd, connection/control and live count.

Use shared tokens/icons/controls. The Terminal rail can collapse without mutating global navigation preferences; narrow layouts start collapsed. A native dialog opens a folder path with existing path picker support and manual entry; submit explicitly creates the first terminal, with validation errors leaving the dialog available. Hidden recovery is distinct from cross-group work status.

Local completion attention is keyed by manager generation + terminal ID + completion counter. Clear only after a frame carrying that counter is rendered, document is visible, window has focus, and xterm's input textarea has focus. Observe a full onRender and following animation frame; parser/import completion or pane-menu focus is insufficient. DEC synchronized output must retain attention until the matching render. Reconnect/minimize/selection alone is insufficient. No output text or process-alive inference marks command success/idle/needs-input.

## Validation And Invariants

Verify isolated real PTYs, cross-group creation/split inheritance, stable cwd after OSC 7, explicit OSC 133 lifecycle, silent shell unknown, unseen/seen completion, hide/reopen same IDs, narrow pane retention, exact stop, setup/font/API faults, keyboard focus and wide/920/700/320 geometry. Run configured terminal Python/Node tests, asset check, privacy and repository checks. Native physical IME/sleep/Quit performance remain unverified by browser checks.
