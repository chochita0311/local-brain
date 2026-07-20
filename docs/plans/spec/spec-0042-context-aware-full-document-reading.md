# SPEC-0042: Context-Aware Full Document Reading

## Metadata

- ID: `spec-0042`
- Status: `approved`
- Run ID: `run-20260720-47`
- Attempt: `1`
- Parent Feature: [feat-0042-context-aware-full-document-reading](../feature/feat-0042-context-aware-full-document-reading.md)
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lane: `backend-context`, then `frontend-reading`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-20`
- Updated: `2026-07-20`

## Source Set

- Approved FEAT-0042 full Document boundary and PRD-0006 acceptance contract.
- Passed FEAT-0038 renderer, FEAT-0039 source-local references, FEAT-0041 source-tree and `.markdown-body` reading presentation, FEAT-0009 Document details, and FEAT-0014 explorer continuity.
- Current `/documents/{id}` route, Document heading, metadata, membership, return link, and 404 behavior.
- Current `/context` tree family, progressive async selection, history, focus, disclosure, and source-local internal-reference behavior.
- Design Constitution detail-and-read and Explorer families, Design Evaluation, and Interaction Evaluation.
- Alignment mode: `screen-alignment` `extend`; no exact target replaces current LocalBrain product truth.

## Implementation Goal

- Turn `/documents/{id}` into the full-reading counterpart of the Local Context preview: preserve existing Document context, render shared Markdown, and add the single owning FOLDERS tree when one exists without inventing a source chooser or leaving full-view mode.

## In-Scope Behavior

### Backend Context Lane

- Build one derived full-reader view from the authoritative Document row by reusing `context_document_preview`; leave `body`, path, metadata, membership, and storage unchanged.
- Resolve the enabled `context_root` from the Document's existing `context_root_id`.
- Supply a tree only when that root has `source_type = folder`; FILES, Apple Notes, disabled roots, and Documents without a root receive no tree column.
- Materialize the folder tree with selected-branch metadata so direct entry and refresh render every required ancestor open before client enhancement.
- Supply the owning source identity, Document count, selected Document, rendered state, properties, and return destination to the template.
- Keep missing Documents on the existing `404 Document not found` path.
- Continue returning a complete HTML page for ordinary and `X-Requested-With: LocalBrain-Document-Reader` requests; the client extracts only the replaceable reader content.

### Frontend Reading Lane

- Share one source-tree macro between `/context` and the full Document reader. Context links remain `/context?root=&document=`; full-reader links remain progressive `/documents/{id}` anchors.
- Preserve the existing back link, Document heading, source/path/size detail strip, memberships, and active Local Contexts shell destination.
- Render properties and the trusted shared Markdown result through the same `.markdown-properties` and `.markdown-body` families as FEAT-0041. Do not use a template `safe` filter or add a page parser.
- Use one fixed FOLDERS tree column at the existing `300px` family width above the compact breakpoint. The tree owns independent bounded scrolling and selected-item visibility; no splitter, persistence, source chooser, or new control is introduced.
- Keep the body within the existing reading/prose measures while allowing the metadata composition to use the available reader column.
- At `920px` and below, move the tree before the body in one sequential flow, cap tree height, retain touch-height links, and keep the body readable at `700px` and `320px` without page overflow.
- For non-FOLDERS Documents, omit the tree entirely and retain the existing bounded detail-and-read composition.

### Full-View Continuity

- Delegate FOLDERS tree clicks from the mounted reader. Fetch the full destination page, replace only `[data-document-reader-content]`, select and reveal the matching tree item, retain tree DOM, disclosure, scroll, and bindings, then update title, URL, history, return destination, and bounded status feedback.
- A sibling selection without a fragment moves the new reading content to its intentional start while preserving independent tree scroll.
- Delegate source-local `.markdown-reference-internal` links when their target exists in the current tree. Keep `/documents/{id}` full-view mode, preserve stable heading or block fragments, and focus the selected tree item.
- Back and forward restore body, URL, tree selection, required ancestors, return destination, focus, and fragment or reading-start position.
- Rapid selections abort or ignore superseded work. Fetch, parse, or replacement failure follows the normal destination link through full navigation.
- Normal anchors remain executable without JavaScript; modified clicks retain browser behavior.

## Out-Of-Scope Behavior

- Overlapping-root support, duplicate Document identity, root selection, a FOLDERS source chooser, tree resizing, or a persisted tree preference.
- Document editing, outline rail, previous/next buttons, bookmarks, sharing, search, images, attachments, or new Markdown syntax.
- Source scan, registration, removal, extraction, Workstream membership mutation, search indexing, or database schema changes.
- Rendering source-local Session links or globally guessing an owning source for non-FOLDERS Documents.

## Affected Surfaces

- `src/localbrain/contexts.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/context.html`
- shared source-tree template under `src/localbrain/templates/`
- `src/localbrain/templates/document.html`
- `src/localbrain/static/styles.css`
- `src/localbrain/static/app.js`
- Context helper and UI contract tests
- Project Architecture current implementation baseline

## Surface Lanes

- Backend context:
  - producer: authoritative Document, optional enabled owning root, selected tree, shared renderer result, memberships
  - consumer: server-rendered full-reader template and partial content response
  - validation: synthetic folder, file, selected-branch, render-state, ownership, and 404-compatible tests
  - evaluator ownership: Contract, Functional
- Frontend reading:
  - producer: shared tree markup and rendered full-reader content
  - consumer: page layout plus route-scoped progressive navigation controller
  - validation: template/CSS/JavaScript contracts, active runtime, rendered four-width, navigation, history, focus, scroll, and overflow evidence
  - evaluator ownership: Design, Functional, UX Heuristic

## Screen-Alignment Consistency List

- Retain literally: shared shell, Local Contexts active state, global search, back action, Document title/path, source/path/size metadata, membership destinations, and 404 behavior.
- Reuse natively: FEAT-0041 source-tree rows, directory disclosure, selected state, pane heading, properties, `.markdown-body`, code, table, callout, reference, and focus families.
- New compatible composition: fixed contextual tree beside the existing detail-and-read content, with the Constitution's `920px` compact breakpoint converting it to tree-then-reading flow.
- Preserve product truth: only an enabled FOLDERS root produces a tree; no target-only metadata, chooser, sort, resize, or navigation control is added.
- Style categories: structure owns the reader grid and replaceable content boundary; shared component rules own tree and Markdown presentation; semantic tokens own spacing, border, focus, type, and containment.

## Contract Surfaces

- `/documents/{document_id}` direct, refreshed, sibling-selected, internal-reference, and history-restored identity.
- Document `context_root_id` and enabled root `source_type` determine optional tree eligibility.
- FEAT-0038/0039 renderer input and one-root reference context remain unchanged.
- Shared tree macro emits route-correct progressive anchors and matching visible/programmatic selection.
- Replaceable reader content contains heading, metadata, memberships, properties, and Markdown; the mounted tree and route controller remain outside it.
- Return link stays synchronized to `/context?root={root}&document={id}` when a current context source exists and falls back to `/context` otherwise.

## Acceptance Mapping

- Direct FOLDERS entry maps to server-selected tree ancestors plus rendered body and source identity.
- Sibling and internal-reference navigation maps to mounted-tree partial replacement, URL/history, focus, fragment, and return synchronization.
- Independent tree scrolling maps to a sticky bounded desktop pane and preserved DOM across content swaps.
- Non-FOLDERS fallback maps to a no-tree class with the same bounded Markdown and existing metadata/membership context.
- Responsive behavior maps to the Constitution's `920`, `700`, and `320` transformations with no private breakpoint.
- Existing contracts map to unchanged authoritative rows, membership links, return semantics, and 404 response.

## Evaluation Focus

- Confirm the route never guesses a tree outside the Document's exact enabled FOLDERS root.
- Confirm the source body remains unchanged and only the shared renderer output is trusted.
- Confirm direct entry opens required ancestors before enhancement and selected state has matching `aria-current`.
- Confirm content replacement does not replace the tree, lose disclosure/scroll/bindings, or allow stale responses to win.
- Confirm full-view links and internal references never fall back into `/context` mode.
- Confirm return link, page title, metadata, memberships, selection, focus, URL, history, and fragments advance coherently.
- Confirm non-FOLDERS Documents reserve no empty tree space.
- Confirm long body, code, tables, paths, and headings remain contained at `1440`, `920`, `700`, and `320`.

## Open Blockers

- None.

## Continuity Notes

- `2026-07-20`: Attempt 1 selects `screen-alignment` extend mode, backend-context then frontend-reading lane order, a shared tree macro, fixed desktop tree, `920px` sequential composition, and replace-only reader content navigation.
