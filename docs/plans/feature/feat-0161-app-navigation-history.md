# FEAT-0161: App Navigation History

## Metadata

- ID: `feat-0161`
- Status: `approved`
- Type: `product`
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Created: `2026-11-06`
- Authorization: owner explicitly approved shared Back, retained body titles/search and Docs contents label; requires chronological cross-screen traversal.

## Goal And Acceptance

Shared toolbar Back follows actual app visits across Sessions, detail, Context,
Documents, Dashboard, Search and Docs; it is disabled in its stable slot when no
managed predecessor exists. Retain body titles, search and explicit hierarchy/
source return links. Docs rail label becomes localized Contents/목차; language
option and guide bodies/locale boundaries stay intact.

Keep the latest 50 app history points including current (at most 49 previous points),
not an industry standard: Chromium currently keeps 50 entries per tab; WebKit's
C++ default is 100. Browser-native traversal remains the mechanism. New visit
following Back drops forward branch; reload/replace/background updates add no
point. Ignore startup handshake/external/unmanaged history when enabling Back.
Restore URL filters/selection, window and Context/reader pane scroll, and Chart
camera/selection. Existing partial-page history producers must join the same
owner without discarding their payloads. Back during pending reads cancels stale
view work, not user collection/model operations. Use per-window session metadata,
not DB/original content persistence, sync or telemetry.

## Scope And Validation

Frontend: shared toolbar/history owner, existing AJAX consumers and state producers,
Docs label, synthetic browser fixtures/tests and canonical Mac rebuild. No new
source feature, provider write, global language change or forward-button UI.
Validate real browser and WKWebView traversal, capacity/branch/reload, deep-link
first entry, async races, narrow view, preserved web/desktop and current package.
Fresh static omission challenge is required for the cross-consumer integration.
