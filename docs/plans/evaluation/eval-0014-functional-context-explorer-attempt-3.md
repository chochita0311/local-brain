# EVAL-0014: Local Context Explorer Functional Attempt 3

## Metadata

- ID: `eval-0014-functional-attempt-3`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260716-14`
- Attempt: `3`
- Feature: [feat-0014-local-context-explorer](../feature/feat-0014-local-context-explorer.md)
- Spec: [spec-0014-local-context-explorer](../spec/spec-0014-local-context-explorer.md)
- Execution Profile: `frontend-product`
- Surface Lane: source rail, tree, and preview
- Created: `2026-07-16`

## Scope And Checks

- Repeated direct nested entry, hierarchical document selection, deep tree scrolling, back, forward, and rapid consecutive selection in Chrome.
- Rechecked URL, preview identity, tree DOM, disclosure state, scroll, focus, selected semantics, live feedback, navigation entries, console, and network behavior.
- Ran the complete unit suite, JavaScript syntax check, Jinja parsing, privacy check, and diff whitespace check.

## Evidence

- Direct nested entry opened all three selected ancestors and exposed one visible current document.
- A selection made with tree scroll at `960px` preserved that exact value, disclosure state, tree DOM, and clicked-link focus while only the preview DOM changed.
- Back and forward preserved the tree and restored URL, preview, active item, visibility, and focus together.
- Rapid consecutive selection aborted the superseded request and settled on the last document with one current item.
- The browser kept one document navigation entry; preview requests returned `200`, and no console errors appeared.
- `node --check` passed, all 22 unit tests passed, and all 16 Jinja templates parsed.

## Findings And Regression

- No blocking functional defect remains.
- Normal link fallback, source selection, full-document destination, source management selectors, and index-only deletion language remain unchanged.

## Route

- Next action: `pass`
