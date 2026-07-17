# EVAL-0014: Local Context Explorer Design Re-evaluation

## Metadata

- ID: `eval-0014-design-attempt-2`
- Status: `complete`
- Evaluator Type: `design`
- Result: `FAIL`
- Run ID: `run-20260716-14`
- Attempt: `2`
- Feature: [feat-0014-local-context-explorer](../feature/feat-0014-local-context-explorer.md)
- Spec: [spec-0014-local-context-explorer](../spec/spec-0014-local-context-explorer.md)
- Execution Profile: `frontend-product`
- Surface Lane: source rail, tree, and preview
- Created: `2026-07-16`

## Scope

- Re-evaluated the live `/context?root=&document=` explorer with Chrome DevTools at `1440`, `920`, `700`, and `320` widths.
- Checked source/tree/preview containment, nested selection visibility, responsive composition, touch geometry, accessible selection semantics, and contrast.
- Used synthetic descriptions in this tracked report; no private runtime paths or document content were persisted.

## Checks And Evidence

- The explorer had no page-level horizontal overflow at any evaluated width.
- At `1440` and `920`, source tree and preview remained side by side; at `700` and `320`, they became sequential regions in the required order.
- Expanding two nested directories and selecting their document caused a full document navigation. The selected link retained its `.active` class in the rebuilt DOM, but both selected ancestors returned closed, so the active item was no longer visible in the tree.
- At `320`, document links in the tree rendered at `29px` high instead of the constitution's `40px` narrow touch-control role.
- Lighthouse mobile accessibility scored `96`. The 10px tertiary source path/count text measured `4.32` to `4.43:1` against its surfaces, below the required `4.5:1` ratio.
- The selected document link had no `aria-current` or equivalent semantic selected state.

## Findings

### High: selected tree location becomes visually unavailable

- Classification: `implementation bug`
- The approved explorer pattern requires the tree and preview to preserve selection context. A nested document can be selected while its ancestor directories are closed, leaving the active item outside the visible tree.
- Fix hint: preserve the existing tree DOM while updating the preview, or deterministically reopen every selected ancestor and restore the prior tree scroll position before presenting the selected state.

### Medium: narrow document targets do not use touch geometry

- Classification: `implementation bug`
- Tree document links remain `29px` high at the `320px` viewport even though essential narrow controls use the `40px` touch minimum.
- Fix hint: apply the existing narrow touch-control role to tree document links without changing desktop density.

### Medium: small tertiary metadata misses AA contrast

- Classification: `implementation bug`
- Source paths, counts, the empty file-source label, and the explorer path use the tertiary foreground at 10px and miss the constitution's WCAG AA contract.
- Fix hint: use an existing stronger semantic text role or revise the reusable tertiary role through design governance if it is intended for essential small text.

### Medium: document selection is visual-only

- Classification: `implementation bug`
- `.active` supplies a background treatment, but assistive technology receives no selected/current semantic for the active tree document.
- Fix hint: add `aria-current="page"` or the appropriate tree selection semantic while retaining the visible active treatment.

## Regression Notes

- Source rail selection, status badge containment, long preview text wrapping, and sequential responsive ordering passed.
- No screenshot or audit artifact was written into the repository.

## Route

- Next action: `fix`

## Continuity Notes

- `2026-07-16`: Attempt 2 replaced the source-only graphical suggestion with live browser evidence and invalidated the earlier visual pass for this Feature.
