# App Navigation And History

## Ownership And Scope

The shared shell owns Sidebar, Back, Forward and global search; the body owns its h1. Docs contents
use Contents/목차 beside their existing scoped language option. Explicit Session
list/parent/search-return links remain distinct destinations. `navigation.js` owns
per-window app history; feature controllers keep URL, selection and render rules.

## Traversal Contract

Back follows actual chronological app visits across modules, including supported
partial-page updates. It uses native session-history traversal, not a replacement
URL stack or hierarchy shortcut. The shared control displays only a left arrow, retaining its accessible Back name
and its short action/keycap tooltip in either availability state. Its hit area follows desktop/touch control-size tokens.
The same-position control is disabled at the
first retained app point and when traversal is pending. Startup handshake and
unknown/external entries are not eligible predecessors. Keep both controls disabled
until its requested marker activates, a document is actually displayed, or that
request is observably cancelled;
elapsed time does not prove completion. An unambiguous Navigation API traverse
abort releases only its matching request. A same-document update can abort that
API signal while the document traversal keeps loading, so it must not unlock the
controls; hash-only activation also preserves the pending request. When a usable
signal is absent or same-document changes make cancellation ambiguous, native
History and links remain available, and full-document navigation or reload
restores the controls. A partial view switch alone is not that recovery.
[HTML navigation events](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-navigateevent-interface)
own the optional cancellation signal; no modern API is required for traversal.

Keep the latest 50 points including current (at most 49 backward steps). This is the
LocalBrain limit, not a universal UI rule: current [Chromium source](https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/public/common/history/session_history_constants.h)
uses 50 entries per tab; [WebKit C++ source](https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebKit/UIProcess/WebBackForwardList.cpp)
has default capacity 100. New navigation after Back discards its future branch.
Reload and replace keep the entry; polling and modal-only changes add none.
Onboarding completion uses an explicit full-document replacement and preserves
that entry identity, rather than creating an onboarding predecessor. Native
traversal into an evicted marker starts a fresh disabled root.
Closing the window keeps its app/history alive; complete Quit starts a new app
window history next launch. A Forward control traverses only retained known successors and is disabled at
the newest entry; browser-native Forward remains compatible.

## State And Privacy

A namespaced opaque marker is merged with existing feature-owned `history.state`.
Bounded metadata in `sessionStorage` stores URLs, numeric window/marked-pane scroll
and feature view coordinates/selection. It contains no page-body snapshots and
creates no DB record, source registration, model operation, sync or telemetry.
Filters and selected documents remain URL-owned; Chart global visibility remains
DB/scoped-preference-owned, while per-entry camera/selection is separate.

Capture outgoing state before replacing the DOM; restore only after the target
view settles, including asynchronous initial layout. Initial pageshow must not
release a feature render wait; superseded initial work cannot settle a newer view.
After document/font/view readiness, a hidden webview applies coordinates directly
because native animation frames are suspended; two queued frames reapply the
same guarded snapshot after feature scroll callbacks resume. Visible views use
that same two-frame path. Partial readers signal pending/settled and abort abandoned GET
requests on pagehide. A later traversal supersedes stale restoration. Browser
storage denial cannot break ordinary links or legacy partial navigation; unknown
predecessors disable the custom Back utility rather than guessing a target.

## Implementation

- `navigation.js`: bounded registry, native markers/traversal, scroll restoration,
  utility state and optional per-entry view state.
- `app.js`: existing Dashboard, inventory, Context preview and document reader
  history/render integration, with native History fallback if controller fails.
- Schema, Atlassian, Workflow and Affinity controllers use the same marker-aware
  history methods while retaining their renderers, URL and feature state.
- `session-chart.js`: entry camera/selection, preserving global visibility meaning.
- `base.html` / shared styles: stable disabled/available Back slot and search.
- Marked pane attributes belong to Context/Document templates; bodies/filters are
  still rendered by their existing server owners, including their existing local
  reads. The shared controller adds no source scan, model operation or provider
  original write.


## Shared Window Toolbar

macOS Tauri2.12.4 uses its overlay titlebar, hidden native title and retained OS
traffic-light controls. One shared HTML toolbar occupies that titlebar with
reserved OS-control space; there is no separate in-content toolbar row. The
host injects a marker before rendering. Edition alone never enables this layout;
browsers and unsupported native hosts retain the page toolbar. Startup/recovery
also has an empty draggable strip. Official Tauri drag-region handling owns
movement/double-click and excludes interactive children; only start-dragging is
added to existing main-window capabilities. No custom OS close/minimize buttons.

`shell.js` owns per-window sidebar visibility and platform shortcut hints. It
restores one bounded collapsed/expanded sessionStorage value before paint; denial
keeps controls usable. Collapse retains an icon-only rail with real destinations and accessible names,
preserves an available expand control and notifies resize consumers. The expanded
control sits beside the brand; the compact control remains in the rail header. It adds no database or
global preference. Navigation still owns both direction eligibility and native
traversal; search retains its current form/mode, IME and URL semantics.

Mac uses Cmd+[ / Cmd+], Cmd+Shift+S and Cmd+K for Back/Forward, sidebar and search.
Other desktop browsers use Alt+Left/Right, Ctrl+Shift+S and Ctrl+K. Tooltips and
aria-keyshortcuts reflect that mapping. Recognized window shortcuts run in capture phase before view-local arrow handlers.
Composition, an inert toolbar ancestry and native/custom modal owners
(including aria-modal sheets) block global shell commands; a disabled direction cannot traverse. Keyboard
search targets the existing input or the web Atlassian Search destination.

Shell hints use tooltips.js, one fixed control-anchored hover/focus surface with
separate shortcut keycaps. Navigation publishes current eligibility/help text;
shell.js owns platform key metadata. Pointer movement inside one control cannot
move its hint. Escape, blur, viewport movement, pagehide and modal ownership
dismiss pointer help; hovering the help itself keeps it readable. Automatic
keyboard scrolling reanchors a focused menu hint; explicit wheel/key movement
dismisses it. Composition keys remain owned by the input/IME. Native title hints do
not compete. Google Material Symbols SVGs and license are bundled locally.

Tooltip geometry is measured only after its fixed-position stylesheet applies.
WKWebView may run the controller before CSS is ready: do not cache an absent
custom-property value at initialization. Read timing on demand and resolved pixel
insets at display time, keep measurement invisible, validate numeric coordinates,
and use the layout viewport excluding scrollbars. Loading CSS resumes the current
hover/focus owner. The footer contains Docs and Settings without decorative local
status/privacy slogans.

Search input and Search submit/link have no hover hints; the visible keyboard
badge and existing accessible shortcut metadata remain. Disabled Back/Forward
keep their muted stable slots and use a not-allowed cursor while retaining the
same short action/keycap hint. Omit no-screen explanations. Disabled buttons use
a normal wrapper hit target so pointer hover remains available in WebKit without
enabling activation. Their wrappers explicitly disable the titlebar drag region,
so a disabled-direction press cannot start window dragging.
