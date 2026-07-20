# EVAL-0041: Local Context Markdown Preview And Resizable Explorer — Functional

## Metadata

- ID: `eval-0041-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260719-46`
- Attempt: `1`
- Feature: [feat-0041-local-context-markdown-preview-and-resizable-explorer](../feature/feat-0041-local-context-markdown-preview-and-resizable-explorer.md)
- Spec: [spec-0041-local-context-markdown-preview-and-resizable-explorer](../spec/spec-0041-local-context-markdown-preview-and-resizable-explorer.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `frontend-explorer`
- Evidence Coverage: `complete`
- Created: `2026-07-20`

## Scope

- Evaluated selected, empty, ready, fallback, and source-scoped Markdown integration; splitter semantics and state ownership; same-source link routing; progressive fallback; add actions; and inherited Local Context regression surfaces.

## Checks And Evidence

- A synthetic FOLDERS source rendered the selected Markdown body, ordered YAML properties, resolved sibling reference with fragment, callout, highlighted code, table, tasks, and local MathML while preserving authoritative source content.
- A live local request for the sibling Document returned matching source, tree selection, preview identity, heading fragment target, versioned stylesheet, and current JavaScript asset. The response remains a complete page as specified, allowing the existing client to extract only the preview region.
- The source tree and separator remain outside the replaceable preview node. Delegated handlers operate from the mounted Explorer and keep normal anchors as progressive fallbacks.
- The separator exposes vertical ARIA semantics, controlled pane IDs, default and bounded values, and a 16px keyboard step.
- JavaScript source owns width only in mounted local state and one inline CSS variable; it contains no width storage, URL value, reset control, blur reset, or visibility reset.
- Pointer handling uses capture, continuous clamping, selection suppression, and pointer-up, cancellation, and lost-capture cleanup. Responsive normalization removes active resize influence at the supported narrow breakpoint.
- Same-source reference logic maps an existing `/documents/{id}` target back to its tree URL, retains stable fragments, uses the abortable preview loader, updates history, selection, ancestors, focus, and fragment position, and preserves a full-Document fallback when no tree target exists.
- Existing source links remain ordinary full navigations, so FOLDERS source switching constructs a fresh page and preserves the intended destination scroll and default-width reset boundary.
- Both add forms and Apple Notes action remain present; only their approved decorative borders changed.
- Chrome MCP directly exercised pointer drag to both `220px` and `480px` bounds, confirmed continuous geometry and post-drag selection cleanup, and exercised the focused separator's `16px` ArrowRight step with synchronized ARIA values.
- Same-source tree selection retained the mounted tree and separator, adjusted width, disclosure state, exact tree scroll, selected-item visibility, focus, URL, and history. Back and forward restored matching selection and focus without replacing the mounted explorer.
- A source-local internal reference stayed in `/context`, selected its target, preserved the split, and focused the matching tree item. A reference with a heading fragment landed on the generated target inside the preview, and a hidden target opened only its required ancestor while retaining prior disclosures and tree scroll.
- Rapid consecutive same-source selections settled on the final Document without a tree/preview identity mismatch.
- Adjusted width survived a browser-tab switch, reset to `300px` on reload and leave-and-return, and reset with `scrollY = 0` on an ordinary FOLDERS source switch.
- Rendered `1440` and `920` layouts clamped the split to available geometry without page overflow. At `700` and emulated `320`, the separator was hidden, removed from tab order, and tree then preview remained sequential and reachable; returning wide restored the page-instance width within current bounds.
- Chrome reported no console errors, warnings, issues, or failed network requests during the exercised flow.
- The complete 165-test suite passed, including Context Root, renderer, reference, Obsidian, Local Context preview-replacement, responsive-contract, source-management, and shared-shell regressions. JavaScript syntax, privacy, and diff checks also passed.

## Evidence Gaps

- None. Chrome MCP directly covered the previously blocked pointer, keyboard, navigation, fragment, history, focus, disclosure, scroll, lifetime, source-switch, and responsive interactions.

## Findings

- No tested route, renderer, source-management, template, script-contract, or regression defect was found.
- No implementation bug, spec gap, planning gap, or remaining evidence blocker was found.

## Regression Notes

- No database, source scanning, source membership, add/remove, extraction, Workstream, Session, Search, or global shell behavior changed.

## Route

- Next action: release Functional evaluation for FEAT-0041 and Run acceptance.

## Post-Pass Correction

- `2026-07-20`: the original source-switch observations above remain historical evidence for Run 46. The owner subsequently superseded the page-reset requirement through [FIX-0006](../fix/fix-0006-context-reading-follow-up.md).
- Chrome MCP then confirmed a direct FOLDERS link retained `window.scrollY = 200`, consumed the short-lived destination handoff, reset the destination tree scroll to `0`, restored the default `300px` split, and left all unselected top-level branches closed.
- Focused renderer, Context Root, and UI-contract regression tests passed after the correction.
