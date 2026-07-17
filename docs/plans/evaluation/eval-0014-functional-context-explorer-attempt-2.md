# EVAL-0014: Local Context Explorer Functional Re-evaluation

## Metadata

- ID: `eval-0014-functional-attempt-2`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL`
- Run ID: `run-20260716-14`
- Attempt: `2`
- Feature: [feat-0014-local-context-explorer](../feature/feat-0014-local-context-explorer.md)
- Spec: [spec-0014-local-context-explorer](../spec/spec-0014-local-context-explorer.md)
- Execution Profile: `frontend-product`
- Surface Lane: source rail, tree, and preview
- Created: `2026-07-16`

## Scope

- Reproduced link-driven and direct-query document selection in the live Local Context explorer.
- Checked document identity, URL state, tree disclosure state, tree scroll, DOM continuity, focus continuity, selected visibility, responsive ownership, console, and network behavior.
- Did not submit add or remove actions and did not mutate indexed local data.

## Checks And Evidence

- A nested document selection returned the correct preview and updated the URL to the expected `root` and `document` query values.
- The click issued a new top-level `GET /context?root=…&document=…` followed by static-asset requests instead of updating the preview region in place.
- A marker placed on the tree DOM before selection disappeared after navigation, proving the tree was reconstructed.
- A tree scroll position prepared before selection changed after navigation, and the two user-opened ancestor directories returned closed.
- Focus reset to `body` after selection instead of remaining on the selected tree item or moving intentionally into the updated preview.
- Direct query entry reproduced the same hidden-selected-item state because the server renders only depth-zero directories open.
- All observed requests returned `200`, and no console errors were emitted.

## Findings

### Blocking: document selection destroys explorer orientation

- Severity: high
- Classification: `implementation bug`
- The Feature and Spec already require synchronized source, tree item, preview, and document identity without losing location. The selected document is correct, but disclosure, scroll, DOM, and focus state are not preserved.
- Reproduction:
  1. Open a hierarchical Local Context source.
  2. Expand two nested directories.
  3. Scroll the source tree and select a document inside the nested branch.
  4. Observe a full page navigation, closed ancestors, changed tree scroll, reset focus, and a selected link hidden inside the closed branch.
- Fix hint: progressively enhance tree document links so selection fetches and swaps only the preview region, updates active/accessible selection and browser history atomically, preserves disclosure and scroll state, supports `popstate`, and retains normal link navigation as a no-JavaScript or failed-fetch fallback.

## Regression Notes

- Correct preview content, full-document destination, source selection, responsive stacking, HTTP success, and static asset loading passed.
- Source registration, scanning, removal, and original-file preservation behavior were not mutated or re-executed during this read-only validation.

## Route

- Next action: `fix`

## Continuity Notes

- `2026-07-16`: live interaction evidence invalidated Attempt 1's functional pass; the failure remains inside the approved Feature and Spec boundary.
