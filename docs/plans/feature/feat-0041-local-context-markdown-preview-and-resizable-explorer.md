# FEAT-0041: Local Context Markdown Preview And Resizable Explorer

## Metadata

- ID: `feat-0041`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Created: `2026-07-19`
- Updated: `2026-07-20`

## Goal

- Turn the Local Context preview into a polished Markdown reader with a cleaner source rail and an accessible page-local source-tree split while preserving existing source, tree, scroll, focus, and history continuity.

## Acceptance Contract

- The selected Document preview consumes the passed FEAT-0038 and FEAT-0039 renderer and reference contracts without changing its authoritative body.
- Same-source internal Markdown links and wikilinks select the target Document inside the current explorer, reveal its required ancestors, update the URL, and preserve the current source-tree continuity contract.
- The decorative separator immediately above FOLDERS `경로 추가` and FILES `파일 추가` is absent, while the structural FOLDERS-versus-FILES boundary and every add action remain unchanged.
- A pointer-operable separator resizes the source tree and preview continuously within Design Constitution-derived safe bounds without selecting text or tree items.
- The focused separator exposes appropriate semantics and supports equivalent directional-key resizing without a separate visible control.
- Adjusted width remains only in the current Local Context screen instance; reload, new entry, or leaving for another LocalBrain screen and returning restores the default, while a browser-tab focus change alone does not reset it.
- No width persistence or reset control, menu, or dedicated reset gesture is introduced.
- At `700px` and below, the resize affordance is absent and tree then preview remain sequential and reachable.
- Same-source Document selection retains disclosure, tree scroll, focus, selected-item visibility, and history; FOLDERS source switching preserves the current window position while starting destination-local explorer state fresh.

## Scope Boundary

- In:
  - `/context` Markdown preview consumption of the shared renderer
  - same-source internal-link selection and explorer synchronization
  - FOLDERS and FILES add-control separator removal
  - pointer and keyboard pane resizing with bounded geometry
  - current-screen-only width lifetime and narrow-layout normalization
  - same-source selection and source-switch scroll regression protection
  - plain, empty, malformed, unresolved, and renderer-fallback presentation
- Out:
  - changing source add, remove, scan, health, extraction, or membership behavior
  - removing the FOLDERS-versus-FILES structural boundary
  - persistent width preferences or reset controls
  - full Document layout owned by FEAT-0042
  - image and attachment rendering
  - in-source search, lazy tree loading, pagination, editor, or note creation

## Surface Lanes

- Backend integration lane:
  - path roots: `src/localbrain/main.py`, Local Context queries or resolver integration, and route tests
  - dependencies: FEAT-0038 and FEAT-0039 passed
  - expected evidence: selected source and Document supply the correct bounded renderer context and safe same-source reference destination
  - evaluator ownership: `contract`, `functional`
- Frontend explorer lane:
  - path roots: `src/localbrain/templates/context.html`, `src/localbrain/static/styles.css`, `src/localbrain/static/app.js`
  - dependencies: backend integration lane and FEAT-0014 continuity contract
  - expected evidence: readable Markdown, separator removal, pointer and keyboard resizing, page-local lifetime, narrow normalization, bounded source-switch continuity, and same-source continuity
  - evaluator ownership: `design`, `functional`, `ux-heuristic`

## Contract Surfaces

- `/context?root=&document=` source and Document selection.
- FEAT-0038 renderer and FEAT-0039 owning-source reference context.
- Same-source link selection, tree disclosure, selected state, focus, scroll, and browser history.
- Resizable separator semantics, geometry bounds, page-instance lifetime, and narrow disablement.
- Existing FOLDERS and FILES add-control forms and structural group boundary.

## Required Evaluators

- `contract`: renderer consumption, owning-source resolution, route selection, width lifetime, and inherited explorer-state contract.
- `design`: Markdown reading hierarchy, pane geometry, divider affordance, add-control spacing, containment, and responsive sequential layout.
- `functional`: Markdown states, internal links, pointer drag, keyboard resize, reload and re-entry reset, browser-tab continuity, source switching, history, focus, and add forms.
- `ux-heuristic`: reading comfort, resize discoverability, tree orientation, scroll continuity, and narrow-flow friction.

## User-Visible Outcome

- The user can navigate a Local Context tree, read polished Markdown, allocate space between tree and content for the current visit, and change source or Document without losing the intended orientation.

## Entry And Exit

- Entry point: Local Contexts navigation, a direct `/context` query, or an existing Local Context destination.
- Exit or transition behavior: same-source selections stay in the explorer; source changes start the new scope intentionally; full-view and other application destinations leave the page-local width behind.

## State Expectations

- Default: source, tree selection, preview identity, rendered body, and default split agree.
- Empty: no source, empty source, and no selected Document remain distinct existing states.
- Unresolved or deferred: links, images, attachments, and unsupported constructs use the shared bounded presentation.
- Error: renderer or preview-update failure retains a safe readable fallback and does not leave tree and preview identity mismatched.
- Success: Markdown, tree, split width, focus, scroll, selection, and URL remain synchronized.
- Narrow: tree and preview are sequential and no unsupported resize state remains active.

## Dependencies

- FEAT-0038 and FEAT-0039 must be `passed` before this Feature enters build.
- FEAT-0014 Local Context Explorer must remain `passed` and supplies the inherited source, tree, preview, focus, scroll, and history behavior.

## Likely Affected Surfaces

- `src/localbrain/main.py`
- Local Context query or resolver integration under `src/localbrain/`
- `src/localbrain/templates/context.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- Local Context route, UI contract, interaction, accessibility, and browser tests with synthetic Markdown

## Pass Or Fail Checks

- Pass if the selected preview renders every shared supported syntax and retains authoritative source text.
- Pass if same-source internal references select and reveal their target without losing tree disclosure, scroll, focus, selected state, or history.
- Pass if only the two add-control separators disappear and both add actions and the group boundary remain unchanged.
- Pass if pointer and keyboard resizing obey safe bounds and do not select content or lose active Document state.
- Pass if width survives same-screen selection but resets on reload, new entry, or leave-and-return, with no reset control or persistent preference.
- Pass if browser-tab focus change alone retains width and `700px` or narrower removes resize state while preserving sequential access.
- Pass if direct FOLDERS source changes retain `window.scrollY` while destination tree scroll, preview scroll, disclosure, selection, and splitter width start fresh.
- Fail on page overflow, unsafe output, stale tree or preview identity, source-management regression, or loss of FEAT-0014 continuity.

## Regression Surfaces

- FEAT-0014 source rail, tree, preview, add/remove, health, disclosure, scroll, focus, history, and narrow layout
- `/context` direct query and same-source partial update behavior
- FOLDERS and FILES forms and original-source preservation
- shared shell and reading-width containment

## Harness Trace

- Active spec doc: [spec-0041-local-context-markdown-preview-and-resizable-explorer](../spec/spec-0041-local-context-markdown-preview-and-resizable-explorer.md)
- Active run: [run-20260719-46-local-context-markdown-preview-and-resizable-explorer](../run/run-20260719-46-local-context-markdown-preview-and-resizable-explorer.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [Contract — PASS, complete](../evaluation/eval-0041-contract-local-context-markdown-preview-and-resizable-explorer.md), [Design — PASS, complete](../evaluation/eval-0041-design-local-context-markdown-preview-and-resizable-explorer.md), [Functional — PASS, complete](../evaluation/eval-0041-functional-local-context-markdown-preview-and-resizable-explorer.md), [UX — PASS, complete](../evaluation/eval-0041-ux-local-context-markdown-preview-and-resizable-explorer.md)
- Latest fix note: [FIX-0006 Context Reading Follow-Up](../fix/fix-0006-context-reading-follow-up.md)

## Continuity Notes

- `2026-07-19`: initial draft combined Markdown preview, the requested add-control cleanup, and pane resizing because they form one Local Context explorer outcome and share the inherited selection and scroll contract.
- `2026-07-19`: FEAT-0041 entered the sequential loop under `fullstack-product`; Orchestrator declared backend-integration then frontend-explorer lanes and `screen-alignment` extend mode.
- `2026-07-20`: source, live-route, complete regression, JavaScript, privacy, and contract evidence pass. The Feature is technically blocked only on its explicitly required rendered pointer, keyboard, history, focus, scroll, and viewport evidence because the in-app browser capability is unavailable; no implementation finding is open.
- `2026-07-20`: Chrome MCP completed the blocked rendered evidence across pointer and keyboard resizing, bounds, focus, same-source and internal-reference navigation, fragments, history, disclosure, scroll, lifetime resets, source switching, and `1440`/`920`/`700`/`320` containment. All required evaluators now pass with complete coverage and FEAT-0041 is `passed`.
- `2026-07-20`: owner post-pass review superseded source-switch page reset. FIX-0006 preserves only window position, closes unselected root branches, and retains fresh source-local explorer state; focused and rendered regression evidence passed.
