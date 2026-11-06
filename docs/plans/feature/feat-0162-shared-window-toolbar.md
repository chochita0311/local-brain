# FEAT-0162: Shared Window Toolbar

## Metadata

- ID: `feat-0162`
- Status: `passed`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-11-06`
- Authorization: owner approved implementing the described desktop titlebar/web toolbar layout after explicitly clarifying both execution environments.

## Approved Boundary

macOS app: preserve OS traffic-light controls and integrate one shared toolbar
into the titlebar. Back and Forward at left; global search and shortcut hint at
right. The sidebar toggle sits beside the brand, outside its home link, and
collapse retains the compact icon rail. Remove the extra content-header row by moving that same
bar into window chrome. Browser: retain the page toolbar with the same controls.
Body starts with its existing h1. Native window drag/double-click/close/minimize
and resize must remain usable, with no duplicate window buttons.

Shared controls own real bounded app-history traversal, sidebar collapse and
search focus/submission; hover tooltips show the actual shortcuts. Keep the
latest50 history contract, URL/filter/reader/camera state, onboarding/modal
isolation and app-only Docs language behavior. Sidebar visibility is per-window
session metadata, retained across page navigation but not a new global setting.

No source/model/backend API, DB, collection, external write, new dependency or
Windows native-support claim. Existing unsupported app routes remain excluded.
Reuse the installed Tauri2 macOS overlay titlebar and shared web controls, not a
separate native widget/search/history implementation. Actual Windows execution
remains outside this Mac environment; browser shortcut presentation is checked.

## Delivered Result And Evidence Boundary

[Run238](../run/run-20261106-238-shared-window-toolbar.md) records implementation,
automated evaluation and normal-path app replacement/relaunch. Native titlebar
layout, real host bootstrap/read-only IPC, sidebar and search focus were observed
with a synthetic profile; browser navigation and modal/shortcut ownership passed.
Physical dragging/double-click, native window-button hit testing/minimize and
recipient/Windows execution remain separate human/environment checks. This status
does not claim those checks or public-distribution readiness.

## Owner-approved Sidebar/Tooltip Follow-up

The owner replaces hidden sidebar collapse with a compact menu icon rail, moves
the toggle beside the brand, requests Google icons instead of numbers/Docs ?, and
requires stable control-anchored hover/focus help with individual keycaps. Real
menu destinations and active/keyboard state remain; no native/data scope expands.
Run238 owns follow-up evaluation and canonical delivery.
