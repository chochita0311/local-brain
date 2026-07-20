# EVAL-0042: Context-Aware Full Document Reading — Functional

## Metadata

- ID: `eval-0042-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260720-47`
- Attempt: `1`
- Feature: [feat-0042-context-aware-full-document-reading](../feature/feat-0042-context-aware-full-document-reading.md)
- Spec: [spec-0042-context-aware-full-document-reading](../spec/spec-0042-context-aware-full-document-reading.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-context`, `frontend-reading`
- Evidence Coverage: `complete`
- Created: `2026-07-20`

## Scope

- Evaluated direct and refreshed full Document identity, exact owning-source context, FOLDERS and non-FOLDERS routes, shared rendering, partial full-view navigation, history, fragments, focus, disclosure, scroll, race handling, fallback, and inherited Document behavior.

## Checks And Evidence

- Route tests confirm that only the Document's exact enabled FOLDERS root can produce a tree and that selected ancestors are materialized from the authoritative Document ID.
- File, Apple Notes, disabled-root, and missing-root states produce no tree while retaining a safe Local Context return path and unchanged source body.
- The full route reuses the FEAT-0038/0039 rendered result and source-local reference context, retains memberships, and preserves the existing missing-Document `404` response.
- The shared tree macro emits ordinary full-document anchors. The progressive controller replaces only the reader content and leaves the mounted tree, disclosure state, scroll, and delegated handlers intact.
- Chrome MCP confirmed direct FOLDERS entry and refresh with matching body, selected tree row, open ancestors, source count, return destination, title, and URL.
- Actual sibling selection retained full-view mode, exact tree scroll and disclosure state, focused and revealed the selected row, synchronized the return link, and moved new content to its reading start.
- Browser back and forward restored matching body, URL, tree selection, selected-row focus, return destination, and tree state without replacing the tree.
- A source-local internal reference to a hidden tree target opened only required ancestors, retained prior disclosures, revealed and focused the selected row, and stayed on `/documents/{id}`.
- A cross-document heading fragment preserved the encoded URL fragment and positioned the generated target heading below the sticky shell offset.
- Rapid consecutive selections aborted the superseded request; final URL, selected row, heading, status, and non-busy state all matched the last selection.
- A live non-FOLDERS Document rendered no tree or empty column and retained Markdown, source metadata, return context, bounded width, and no horizontal page overflow.
- Chrome MCP verified `1440`, `920`, `700`, and emulated `320` containment. The compact tree and reader remained sequential and tables stayed locally contained.
- An intentional missing-record request returned `404`. A subsequent clean reload reported no console errors, warnings, issues, or failed network requests.
- `uv run --no-sync python -m unittest discover -s tests -v` passed all 166 tests. `node --check`, repository privacy, and diff whitespace checks also passed.

## Evidence Gaps

- None.

## Findings

- No remaining route, ownership, renderer, navigation, focus, history, responsive, fallback, or regression defect was found.

## Regression Notes

- Database schema, source registration and scanning, Document storage, memberships, Search and Workstream destinations, and the shared shell were not changed.

## Route

- Next action: release Functional evaluation for FEAT-0042 and Run acceptance.

## Post-Pass Correction

- `2026-07-20`: [FIX-0006](../fix/fix-0006-context-reading-follow-up.md) changed initial tree disclosure so no unselected top-level directory opens by default and a selected Document opens only its required ancestor chain.
- Chrome MCP confirmed the direct glossary route opened only `onboarding`, desktop table headers filled through the last column, and narrow multi-column tables scrolled inside their wrappers without page overflow.
