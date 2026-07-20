# SPEC-0041: Local Context Markdown Preview And Resizable Explorer

## Metadata

- ID: `spec-0041`
- Status: `approved`
- Run ID: `run-20260719-46`
- Attempt: `1`
- Parent Feature: [feat-0041-local-context-markdown-preview-and-resizable-explorer](../feature/feat-0041-local-context-markdown-preview-and-resizable-explorer.md)
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-integration`, then `frontend-explorer`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-19`
- Updated: `2026-07-20`

## Source Set

- Human request and clarifications: prettier Markdown reading inspired by the owner-supplied local note reader and Obsidian; remove only add-control divider lines; preserve window position across FOLDERS source changes while resetting source-local explorer state; add a draggable tree/preview split; width is page-instance-only; keyboard resizing is supported; no reset control.
- Parent Feature: FEAT-0041 Local Context preview and continuity boundary.
- Passed dependencies: FEAT-0038 safe renderer, FEAT-0039 Obsidian syntax and one-root resolver, FEAT-0014 explorer continuity.
- Golden implementation source: current Local Context source rail, explorer card, tree, async preview replacement, history, focus, and narrow layout.
- Visual reference: owner-supplied local note-detail body hierarchy, prose rhythm, code frame, table containment, and link treatment only.
- Durable baseline: Design Constitution plus Design and Interaction Evaluation rules.
- Alignment skill: `screen-alignment` in `extend` mode.

## Implementation Goal

- Produce one shared LocalBrain Markdown reading surface and integrate it into `/context`, then add a semantic page-local splitter without rebuilding or persisting the inherited tree state.

## In-Scope Behavior

### Backend Integration Lane

- For a selected Document, copy the query row into a view model and leave `body` authoritative and unchanged.
- Build a `MarkdownReferenceContext` only when the selected Document belongs to an enabled FOLDERS source; file and Apple Notes sources render without an owning-source resolver.
- Call the shared `render_markdown` exactly once per selected preview and expose its trusted HTML, state, and ordered properties to Jinja.
- Keep no-source, no-document, empty-document, ready, and fallback states distinct.
- Preserve the existing validation that rejects a Document outside the selected `context_root_id`.
- Continue returning the complete page for normal and `X-Requested-With: LocalBrain-Context-Preview` requests; the client keeps extracting only the preview region.

### Frontend Explorer Lane

- Replace escaped/preformatted source output with the shared trusted result. Do not add a template `safe` filter.
- Render valid YAML properties in a semantic `<dl>` before body HTML; autoescape property names and values normally.
- Give the reading body a shared `.markdown-body` class reusable by later Document and Session Features.
- Translate only these reference traits into LocalBrain roles:
  - bounded prose measure and body-font reading rhythm
  - clear heading ladder with stable anchor scroll offsets
  - compact inline code and framed horizontally scrollable fenced code
  - contained tables, blockquotes/callouts, task lists, footnotes, tags, highlights, MathML, unresolved states, and note embeds
- Use only current LocalBrain semantic colors, typography, spacing, radii, borders, elevation, and focus roles. Do not import reference fonts, dark theme, code-window dots, shell, navigation, gradients, raw colors, or remote assets.
- Remove the top border from both `.context-root-add` instances at all widths. Retain spacing, both forms, Apple Notes action, and the `.files-group` structural top boundary.
- Insert one separator between tree and preview with:
  - `role=separator`, vertical orientation, `tabindex=0`, label, controlled pane IDs, and dynamic `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, and `aria-valuetext`
  - a 12px hit track with one semantic 1px visible boundary owned by the separator
  - col-resize cursor and focus-visible ring
- Default tree width is 300px when space permits.
- Normal safe bounds are 220–480px while reserving at least 42% or 360px, whichever is smaller, for preview. Just above the narrow breakpoint, the tree floor may contract to 160px and the preview floor to 180px so neither pane overflows.
- Pointer drag uses pointer capture, updates continuously, prevents selection while active, and cleans up on pointer up or cancellation.
- Left and Right arrows adjust by 16px per key event; no Home, End, double-click, button, menu, or reset gesture is added.
- Width exists only as an inline CSS variable and local JavaScript state on the current mounted explorer. Do not use localStorage, sessionStorage, cookies, URL state, database state, or a hidden reset value.
- Async same-source Document and internal-reference selection replaces only the preview, so the adjusted split, disclosure, and tree scroll remain mounted.
- Reload or leave-and-return constructs a new explorer at default width. Browser-tab blur/focus has no reset listener and retains the mounted width.
- At `max-width: 700px`, use the inherited sequential tree-then-preview layout, hide the separator, remove inline split influence through the responsive grid override, and keep touch-height tree targets.

### Same-Source Reference Continuity

- Delegate clicks from the replaceable preview for `.markdown-reference-internal` `/documents/{id}` links.
- Match the Document ID against an existing tree link in the current source. If absent, retain the normal full-Document anchor fallback.
- For a same-source match, convert the navigation destination to the tree link's `/context?root=&document=` URL while retaining a stable heading or block hash.
- For a different Document, use the existing abortable preview loader, push one history state, replace only preview, select and reveal the tree item, focus it without page scroll, then scroll the preview fragment into view.
- For a same-Document fragment, push history and scroll the current preview without a fetch or tree reset.
- Back and forward restore the matching preview, selection, necessary ancestors, focus, and fragment.
- Existing FOLDERS source links remain full navigations. A direct source-link transition preserves only `window.scrollY`; destination tree and preview scroll, disclosure, selection, and the default split width start fresh.

## Out-Of-Scope Behavior

- Full Document reader composition, Session messages, outline rail, editor, source search, note creation, lazy tree loading, or pagination.
- Image or attachment rendering, remote content, external math assets, or any new Markdown syntax.
- Persisted or cross-screen pane width, visible reset control, source-specific width, or width URL parameter.
- Source add/remove/scan semantics, root membership, source order, health statuses, file extraction, or the FOLDERS/FILES structural boundary.
- Rebuilding the source tree during same-source preview updates.

## Affected Surfaces

- `src/localbrain/main.py`
- `src/localbrain/contexts.py` only if the view-model adapter belongs there
- `src/localbrain/templates/context.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- Local Context backend, renderer, UI-contract, and continuity tests
- Markdown Rendering owner policy for the shared consumer class only when needed

## Surface Lanes

- Backend integration:
  - producer: selected authoritative Document plus optional one-root resolver
  - consumer: context template render view model
  - validation: synthetic selected, cross-root rejection, folder resolver, file no-source, empty, ready, and fallback tests
  - evaluator ownership: Contract, Functional
- Frontend explorer:
  - producer: trusted renderer result and existing tree markup
  - consumer: shared Markdown body, splitter, delegated async navigation
  - validation: template/CSS/JS contracts, active local runtime, interaction-state invariants, full suite
  - evaluator ownership: Design, Functional, UX Heuristic

## Screen-Alignment Consistency List

- Retained components: Local Context page heading, metric band, source rail, FOLDERS and FILES groups, root rows, forms, explorer card, toolbar, status badge, source tree, details disclosure, preview header, async status region, full-view link.
- Retained interaction patterns: ordinary source navigation, progressive anchor fallback, preview-only replacement, AbortController race protection, pushState/popstate, focus-without-page-scroll, active plus `aria-current`, and 700px sequential layout.
- Adapted reading traits: bounded measure, body rhythm, heading hierarchy, link emphasis, framed code, contained table, and calm callouts from the designated local reader.
- Deliberate LocalBrain translation: current light surfaces, semantic tokens, restrained border/elevation, SF/system typography, existing focus system, no decorative code dots or foreign shell.
- New compatible pattern: one standard ARIA separator and shared `.markdown-body` consumer class.
- Intentional deviations: none.

## Contract Surfaces

- Producer expectations: route supplies the selected Document unchanged and exactly one optional source-scoped resolver.
- Consumer expectations: template renders only `MarkdownRenderResult.html`; client never reparses Markdown or rewrites trusted HTML.
- Route identity: tree and same-source references settle on `/context?root={root}&document={id}` with an optional stable fragment.
- Progressive fallback: tree links remain normal context URLs; renderer links remain normal `/documents/{id}` anchors when enhancement cannot match a tree item.
- Width lifetime: mounted explorer only, represented by one CSS custom property, no storage or URL contract.
- Separator ownership: the separator owns the sole tree/preview boundary; tree border is removed to avoid a double line.

## Required Evaluators

- Contract: renderer input/output ownership, reference context, route identity, safe trusted output, no persistence, tree continuity boundary.
- Design: prose hierarchy, code/table/callout containment, splitter geometry and affordance, removed versus retained boundaries, default/dragged/narrow states.
- Functional: selected/empty/fallback render states, same-document and cross-document references, failure fallback, abort race, history, focus, tree scroll/disclosure, pointer and keyboard bounds, reload/re-entry/tab-focus lifetime, bounded source-switch continuity, add forms.
- UX Heuristic: reading comfort, affordance clarity, orientation, feedback, same-source continuity, and narrow sequential friction.

## Acceptance Mapping

- Shared Markdown preview maps to one backend integration helper plus `.markdown-body` and property markup.
- Same-source links map to delegated preview anchors, tree-ID matching, inherited loader, fragment scroll, history, and progressive fallback.
- Divider cleanup maps to removal of `.context-root-add` border only, with `.files-group` boundary retained.
- Resizing maps to ARIA separator, pointer capture, 16px arrow steps, dynamic clamps, one inline variable, and no storage/reset APIs.
- Lifetime maps to mounted-node preservation, no blur reset, fresh document default, and source navigation reload with default splitter width.
- Narrow maps to separator hidden and one-column grid at 700px.
- Scroll continuity maps to preview-only replacement for Documents and ordinary full source navigation for FOLDERS with one short-lived, exact-destination `window.scrollY` handoff.

## Evaluation Focus

- Confirm no source body is marked trusted or mutated and no second parser runs in JavaScript.
- Confirm preview replacement does not replace the explorer body, tree, or separator.
- Confirm the exact separator nodes and handlers persist across repeated async selections.
- Confirm a dragged width survives same-screen selection and browser-tab focus but not reload or leave-and-return.
- Confirm source switching still uses ordinary links, preserves the current window position, and produces a new default explorer with fresh tree-local state.
- Confirm internal reference hashes survive the context-route conversion and point to generated anchors.
- Confirm the two add lines are gone while the FOLDERS/FILES group boundary remains.
- Confirm content and code do not overflow dragged, compact, or narrow panes.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-19`: Attempt 1 locked shared Markdown consumption, progressive same-source reference interception, a mounted page-local splitter, 16px arrow steps, dynamic safe bounds, and exact reset semantics.
- `2026-07-20`: owner follow-up superseded the original source-switch page reset. FIX-0006 preserves only window position across direct FOLDERS source links while keeping the destination tree, preview, disclosure, selection, and splitter state fresh.
