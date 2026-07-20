# FEAT-0042: Context-Aware Full Document Reading

## Metadata

- ID: `feat-0042`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Created: `2026-07-19`
- Updated: `2026-07-20`

## Goal

- Make full Document reading preserve the owning FOLDERS tree and full-view mode as users enter directly, refresh, follow internal references, or select sibling Documents.

## Acceptance Contract

- Every full Document body consumes the passed FEAT-0038 and FEAT-0039 renderer and reference contracts without changing source content.
- A FOLDERS Document full-view route resolves its single owning source tree, expands required ancestors, and keeps the active Document selected and visible on direct entry, refresh, and in-app entry.
- Selecting a sibling from the tree or a source-local internal reference keeps full-view mode, replaces the body, updates URL and selected tree state, and preserves meaningful browser back and forward behavior.
- The source tree scrolls independently and the body remains within a bounded long-form reading width.
- A FILES, Apple Notes, or other non-FOLDERS Document retains the bounded full reading layout, source identity, and Local Contexts return path without an empty tree column.
- The layout becomes an intentional sequential tree-then-reading composition when side-by-side geometry would violate the supported reading width.
- Existing non-overlapping FOLDERS-root, unique Document-path, metadata, Workstream membership, return-link, and 404 contracts remain intact.

## Scope Boundary

- In:
  - `/documents/{document_id}` Markdown body rendering
  - owning FOLDERS source and tree resolution
  - selected ancestor disclosure and current-item visibility
  - full-view sibling and internal-reference navigation
  - URL, history, refresh, direct entry, and return orientation
  - non-FOLDERS full-reading fallback without an empty tree
  - independent tree scroll, bounded body width, and responsive sequential composition
- Out:
  - overlapping roots, duplicate Documents, source choosers, or invented hierarchy
  - persistent or resizable full-view tree width unless separately approved
  - Document editing, outline rail, previous or next note controls, sharing, or bookmarks
  - image and attachment rendering
  - changing Workstream membership, extraction, indexing, or source behavior

## Surface Lanes

- Backend context lane:
  - path roots: `src/localbrain/main.py`, `src/localbrain/contexts.py`, relevant queries, and route tests
  - dependencies: FEAT-0038 and FEAT-0039 passed; current unique source ownership
  - expected evidence: full-view route receives the correct rendered Document, owning FOLDERS source, tree, selected path, and non-FOLDERS state on direct and navigated entry
  - evaluator ownership: `contract`, `functional`
- Frontend reading lane:
  - path roots: `src/localbrain/templates/document.html`, reusable tree presentation, `src/localbrain/static/styles.css`, and browser navigation behavior
  - dependencies: backend context lane
  - expected evidence: selected tree, bounded Markdown reading, full-view sibling transitions, history, independent scroll, non-FOLDERS fallback, and responsive composition
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- `/documents/{document_id}` direct, refreshed, sibling-selected, and history-restored identity.
- Document `context_root_id`, non-overlapping FOLDERS roots, unique paths, and source-tree materialization.
- FEAT-0038 rendering and FEAT-0039 owning-source references.
- Selected item, ancestor disclosure, URL, browser history, return path, and Workstream membership destinations.
- FOLDERS versus non-FOLDERS layout selection.

## Required Evaluators

- `contract`: route identity, single source ownership, renderer context, tree selection, URL and history synchronization, and non-FOLDERS fallback.
- `design`: tree and reading hierarchy, bounded width, metadata priority, selection, independent scroll, long content, and responsive sequential composition.
- `functional`: direct entry, refresh, sibling selection, internal references, back and forward, return and membership links, non-FOLDERS Documents, missing records, and renderer failures.
- `ux-heuristic`: reading focus, source orientation, tree navigation, full-view continuity, and narrow-layout friction.

## User-Visible Outcome

- The user can read a full FOLDERS Document with its tree visible, move among related Documents without leaving full view, and still receive a clean reading surface for sources that have no folder tree.

## Entry And Exit

- Entry point: Local Context preview, source-local internal link, Search or Workstream Document link, or direct full Document URL.
- Exit or transition behavior: tree and internal Document selections stay in full view; return and Workstream links retain their existing destinations.

## State Expectations

- Default FOLDERS: owning tree, selected item, metadata, and rendered body agree.
- Default non-FOLDERS: no tree column is reserved; source identity and return path remain present.
- Empty: an empty body uses the shared neutral state without hiding Document identity.
- Error: missing record retains current route error behavior; render or navigation failure does not show a mismatched tree and body.
- Success: body, URL, selected tree item, ancestors, history, source identity, and metadata remain synchronized.
- Narrow: tree and reading content remain reachable in sequential order without compressing typography below the constitution.

## Dependencies

- FEAT-0038 and FEAT-0039 must be `passed` before this Feature enters build.
- FEAT-0009 Document And Resource Details and FEAT-0014 Local Context Explorer must remain `passed`.
- FEAT-0041 must be `passed` before this Feature enters build and supplies the current Local Context tree and Markdown reading presentation reused by full view.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/contexts.py` and relevant Document queries
- `src/localbrain/templates/document.html`
- reusable source-tree template structure when selected by the Spec
- `src/localbrain/static/styles.css` and browser interaction code when partial full-view navigation is selected
- Document route, tree, history, responsive, and browser tests with synthetic sources

## Pass Or Fail Checks

- Pass if a direct or refreshed FOLDERS Document resolves one correct tree and reveals its selected item.
- Pass if sibling tree and same-source internal-link selections remain in full view and synchronize body, URL, tree, focus destination, and browser history.
- Pass if non-FOLDERS Documents render without an empty tree while retaining source, return, metadata, and membership context.
- Pass if tree scroll and bounded body reading coexist without page overflow at `1440`, `920`, `700`, and `320`.
- Pass if empty, malformed, unresolved, deferred image, and renderer-failure states follow the shared contracts.
- Fail if direct entry depends on visiting `/context` first, if tree and body identities diverge, or if existing Document and Workstream destinations regress.

## Regression Surfaces

- FEAT-0009 Document metadata, reading, return, membership, and 404 behavior
- FEAT-0014 source tree identity and selection semantics
- unique Document path and non-overlapping FOLDERS-root contracts
- Search and Workstream Document destinations
- shared shell and responsive reading-width behavior

## Harness Trace

- Active spec doc: [spec-0042-context-aware-full-document-reading](../spec/spec-0042-context-aware-full-document-reading.md)
- Active run: [run-20260720-47-context-aware-full-document-reading](../run/run-20260720-47-context-aware-full-document-reading.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports:
  - [Contract — PASS, complete](../evaluation/eval-0042-contract-context-aware-full-document-reading.md)
  - [Design — PASS, complete](../evaluation/eval-0042-design-context-aware-full-document-reading.md)
  - [Functional — PASS, complete](../evaluation/eval-0042-functional-context-aware-full-document-reading.md)
  - [UX Heuristic — PASS, complete](../evaluation/eval-0042-ux-context-aware-full-document-reading.md)
- Latest fix note: [FIX-0006 Context Reading Follow-Up](../fix/fix-0006-context-reading-follow-up.md)

## Continuity Notes

- `2026-07-19`: initial draft isolated context-aware full reading from the explorer preview because direct-entry data, full-view sibling navigation, history, and non-FOLDERS fallback form a separate route contract.
- `2026-07-20`: the owner resumed the previously authorized sequential PRD-0006 workflow after FEAT-0041 passed. FEAT-0042 is the only approved execution target under `fullstack-product`, with backend-context then frontend-reading lanes and `screen-alignment` extend mode.
- `2026-07-20`: backend, browser, responsive, contract, design, functional, and UX evidence passed. The Feature is released and PRD-0006 may advance to FEAT-0043.
- `2026-07-20`: FIX-0006 corrected selected-ancestor disclosure defaults, full-width Markdown table fill, and Markdown reading-code tone. The owner-reported glossary Document, code-heavy reading, and responsive table containment were revalidated through Chrome MCP.
