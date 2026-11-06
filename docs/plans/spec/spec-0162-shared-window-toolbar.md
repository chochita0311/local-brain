# SPEC-0162: Shared Window Toolbar

## Metadata

- ID: `spec-0162`
- Status: `approved`
- Feature: [FEAT-0162](../feature/feat-0162-shared-window-toolbar.md)
- Run: [Run238](../run/run-20261106-238-shared-window-toolbar.md)
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`

## Implementation Contract

One set of DOM controls and existing GET search form serve both hosts. macOS
Tauri2.12.4 overlays its hidden titlebar, retains OS decorations, positions native
traffic lights and injects a host-only root marker before rendering. Native CSS
fixes the common toolbar to the window top with reserved traffic-light space;
body/sidebar start beneath it. Browser retains its sticky page header. No titlebar
marker comes from edition alone; standalone HTTP and missing host stay usable.
Official installed drag-region handling plus its minimal capability own window
movement; buttons/inputs must be excluded from drag targets. Preserve640px minimum
Mac window and320/700/920/1440 browser layouts. Respect reduced motion and visible
focus. No independent page-level scroll container.

Navigation owns backward/forward eligibility and serializes native traversal for
both buttons. Unknown and evicted entries cannot enable a direction. Shell owns
only collapsed sidebar state and shortcut/tooltip presentation. Restore sidebar
state before page paint using bounded sessionStorage metadata, catch denial and
keep controls usable. No app DB/preference change. A collapsed sidebar retains icon-only menu destinations, accessible labels and
hover/focus help, with the expand control in the rail header. Resize-dependent
views must update normally.

Shortcuts: Mac Cmd+[ / Cmd+] (Back/Forward), Cmd+Shift+S (sidebar), Cmd+K(search);
other desktop browsers Alt+Left/Right, Ctrl+Shift+S, Ctrl+K. Tooltips and accessible
shortcut names use the actual platform mapping. Use capture-phase ownership for recognized window combinations so focused view
arrow handlers cannot consume them. Skip composition; prevent global
shell commands from escaping a modal/onboarding owner. Existing IME Enter guard,
query mode, maxlength, submission and settings shortcut remain intact. Search
shortcut focuses the existing input or existing Search destination when the
optional web Atlassian surface has no global input.

## Validation

Meaningful actual browser scenarios for both host modes, Back/Forward, branch and
capacity, selected reader/scroll/camera, Ctrl/Cmd shortcuts, disabled states,
sidebar collapse/reload/history, source-scope/global query and modal isolation.
Test storage denial and shell asset failure, not just static placement. Measure
native insets, body/title/header geometry, drag target versus control separation,
responsive and collapsed states. Compile/package real Mac host and verify frozen
assets, host marker/permissions and actual controls where available. A hidden
engine/synthetic host is not physical foreground/native dragging evidence.
Obtain one frozen competent static omission challenge for cross-consumer history
and native-drag capability changes; reviewer never executes or edits. Final
canonical app/ZIP/checksum and source identity must match; no source commit/push.

## Owner-approved Sidebar/Tooltip Refinement

The owner replaces hidden-rail behavior with a compact icon rail. The expanded
toggle sits at the brand’s right, outside its home link; collapsed mode retains
home, expand, all available menu destinations, Docs and Settings. Use bundled
Google Material Symbols for numbers/question-mark replacements. Navigation,
active state, keyboard/touch reachability, modal isolation and short/narrow
window access must survive.

One control-anchored tooltip owns shell hints, with separate action text and
individual shortcut keycaps. No parentheses or competing native title. Verify
delayed hover, focus, stable coordinates inside one control, peer changes,
Escape, entry into the tooltip, blur, scroll/resize/pagehide, modal ownership,
viewport bounds and repeated state changes. Hints never take focus or move layout.

Owner’s later hint correction: no help popup on query input or Search submit/link.
Disabled Back/Forward keep a not-allowed cursor and the same short action/keycap
hover hint as enabled directions, without no-screen explanations. A disabled
button must remain non-actionable while its normal wrapper receives hover. Omit decorative
footer online/privacy copy. Native CSS readiness and valid, invisibly measured
layout-viewport geometry precede hint visibility.
