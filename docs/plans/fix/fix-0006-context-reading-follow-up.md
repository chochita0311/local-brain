# FIX-0006: Context Reading Follow-Up

## Metadata

- ID: `fix-0006-context-reading-follow-up`
- Status: `complete`
- Parent PRD: [prd-0006-markdown-reading-and-context-continuity](../prd/prd-0006-markdown-reading-and-context-continuity.md)
- Related Features:
  - [feat-0041-local-context-markdown-preview-and-resizable-explorer](../feature/feat-0041-local-context-markdown-preview-and-resizable-explorer.md)
  - [feat-0042-context-aware-full-document-reading](../feature/feat-0042-context-aware-full-document-reading.md)
- Execution Profile: `fullstack-product`
- Alignment Mode: `screen-alignment adapt`
- Created: `2026-07-20`
- Updated: `2026-07-20`

## Input Reports

- Human post-run review reported that FOLDERS source selection resets the page scroll, while the intended follow-up behavior is to preserve the current page position across that source transition.
- FOLDERS source changes open every top-level directory even when no Document is selected; the reported source is one example of the shared tree behavior, not a root-specific exception.
- The full reader's compact two-column table shows header shading only across intrinsic cell widths instead of the whole table; the reported Document is one example of the shared Markdown table defect.
- Markdown code blocks reuse the near-black Run-console surface and status or brand colors, making note reading harsher than the approved local reader reference.

## Fix Scope

- Preserve window page scroll across ordinary FOLDERS source-link navigation without carrying tree or preview scroll, splitter width, or source disclosure state.
- For every FOLDERS root, render only selected-ancestor directory branches open; otherwise top-level folders begin closed.
- Give every shared Markdown table consumer a dedicated scroll wrapper and a full-width table layout so header and row surfaces fill the available reading region.
- Separate Markdown reading code tone from the Run console with durable semantic reading-code tokens and a calmer syntax palette.
- Preserve source identity, selected-item visibility, safe renderer output, responsive containment, progressive link fallback, and every non-overlapping PRD-0006 contract.

## Contract Correction

- The human owner's `2026-07-20` follow-up supersedes PRD-0006's earlier explicit source-switch page-scroll reset.
- The new contract preserves only `window.scrollY` for a direct FOLDERS source-link transition and clamps naturally to the destination page height.
- New source tree state remains fresh: tree scroll is zero, non-selected branches are closed, selected ancestors alone may open, and splitter width still resets.

## Changes

- FOLDERS source links carry a source-specific marker. Their ordinary primary-button navigation stores an exact destination, current `window.scrollY`, and short expiry in `sessionStorage`; the destination consumes the value once after layout. Storage denial during either handoff or cleanup preserves normal navigation.
- The shared source-tree macro opens a directory only when it contains the selected Document. With no selection, every root branch begins closed.
- The shared renderer wraps each table in `.markdown-table-scroll`; the wrapper owns borders and local overflow while the table fills the available width.
- Markdown fenced code consumes dedicated reading surfaces, border, text, and syntax roles. Run console tokens remain unchanged.
- The Design Constitution, Markdown Rendering Contract, PRD-0006, SPEC-0041, related Features, and evaluator continuity notes now own the corrected behavior.

## Browser Evidence

- A direct FOLDERS source change retained `window.scrollY = 200`, consumed the handoff, started tree scroll at `0`, restored the `300px` splitter default, and left all unselected top-level folders closed.
- Direct full-Document entry opened only the selected Document's required top-level ancestor; every unrelated top-level branch stayed closed.
- The reported two-column glossary table filled a `720px` reading wrapper, its last header edge matched the table edge, and the page had no horizontal overflow.
- At an emulated `320px`, wider Markdown tables overflowed only inside their wrappers while document width stayed equal to viewport width.
- A code-heavy Document rendered `33` fenced blocks on the softer reading surface with distinct syntax colors and no page overflow.
- Console inspection found no errors, warnings, or issues; the Document, stylesheet, and script requests all returned `200`.

## Verification

- Focused Markdown renderer, Context Root, and UI-contract suite: `39` tests passed.
- Full repository suite: `170` tests passed.
- JavaScript syntax: passed.
- Repository privacy: passed across `466` candidate files.
- Diff whitespace: passed.

## Result

- Complete. The four owner-reported follow-ups are corrected without reopening PRD-0006 or its passed Feature sequence. Markdown image and attachment rendering remains the separately deferred backlog item.
- The disclosure correction applies to every FOLDERS root through the common tree macro, and the table correction applies to every preview, full-Document, and conversation surface that consumes the shared Markdown renderer.
