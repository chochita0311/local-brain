# EVAL-0014: Local Context Explorer UX Re-evaluation

## Metadata

- ID: `eval-0014-ux-attempt-2`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `FAIL`
- Run ID: `run-20260716-14`
- Attempt: `2`
- Feature: [feat-0014-local-context-explorer](../feature/feat-0014-local-context-explorer.md)
- Spec: [spec-0014-local-context-explorer](../spec/spec-0014-local-context-explorer.md)
- Execution Profile: `frontend-product`
- Surface Lane: source rail, tree, and preview
- Created: `2026-07-16`

## Scope

- Evaluated hierarchical browse-to-read continuity, repeated document exploration, orientation, selection feedback, focus ownership, and narrow-screen reachability in the live browser.

## Findings

### Blocking: repeated document exploration causes severe orientation loss

- Severity: high
- Classification: `implementation bug`
- Selecting a document visually refreshes the entire explorer, closes the branch the user just opened, changes the tree scroll position, resets focus, and can hide the selected item. Repeated comparison of sibling documents therefore requires reopening and relocating the same branch after every selection.
- This contradicts the approved outcome that the user can navigate the tree and preview evidence without losing location, so it is a blocking UX failure rather than an optional enhancement.
- Fix hint: keep the source rail and source tree stable while swapping only the document preview; preserve user-owned disclosure, scroll, and focus state and make the updated document identity programmatically clear.

### Moderate: active selection lacks nonvisual confirmation

- Severity: medium
- Classification: `implementation bug`
- The visible active background is useful when the item remains visible, but there is no accessible current-state semantic and no bounded announcement of the updated preview.
- Fix hint: expose current selection semantically and use a deliberate preview heading/focus or live-region strategy that does not interrupt rapid browsing.

### Moderate: narrow tree rows are unnecessarily hard to target

- Severity: medium
- Classification: `implementation bug`
- At the 320px touch viewport, document rows remain 29px high even though the sequential layout otherwise remains contained and usable.

## Positive Evidence

- The source rail clearly marks the selected source.
- Preview content, title, path, and full-document action remain visually distinguishable.
- The 700px and 320px layouts keep sources, tree, and preview in the expected sequence without page-level horizontal overflow.
- No console errors or failed requests obscured feedback.

## Route

- Next action: `fix`

## Continuity Notes

- `2026-07-16`: Chrome-based interaction testing invalidated the earlier heuristic pass because the approved no-location-loss outcome is contradicted in hierarchical sources.
