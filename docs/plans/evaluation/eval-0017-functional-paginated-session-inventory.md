# EVAL-0017: Paginated Session Inventory Functional

## Metadata

- ID: `eval-0017-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL`
- Run ID: `run-20260717-17`
- Attempt: `1`
- Feature: [feat-0017-paginated-session-inventory](../feature/feat-0017-paginated-session-inventory.md)
- Spec: [spec-0017-paginated-session-inventory](../spec/spec-0017-paginated-session-inventory.md)
- Execution Profile: `fullstack-product`
- Surface Lane: route and browser integration
- Created: `2026-07-17`

## Browser Evidence

- Page one rendered 20 of 25 eligible primary Sessions and page two rendered the remaining five. Subsessions did not consume primary page slots.
- The only disclosure trigger in the synthetic first page contained exactly two direct children; its grandchild and unresolved sibling were absent.
- Parent identity and child disclosure remained separate destinations.
- Pointer activation opened the disclosure, an outside click dismissed it, keyboard Enter opened it, and Escape dismissed it while restoring focus to the trigger.
- Invalid page inputs followed canonical redirects: non-numeric and negative inputs resolved to page one, and an out-of-range filtered request resolved to its last valid filtered page.
- Source-filter links reset page state. Filtered result counts and page bounds reflected the filter before slicing.

## Automated Evidence

- JavaScript syntax, Python compilation, all Jinja templates, the 32-test suite, and the repository privacy check passed.

## Findings And Regression

- Later actual-runtime evidence invalidated this initial result: a long-running pre-change Python process auto-reloaded the new template without the new pagination context and returned `500` from `/sessions`.
- The fresh synthetic server had no browser console regression, but it did not cover the mixed-version deployment boundary.

## Route

- Next action: route to [FIX-0017](../fix/fix-0017-live-runtime-pagination-context.md) and Functional Attempt 2

## Continuity Notes

- `2026-07-17`: initial synthetic result recorded as pass.
- `2026-07-17`: actual `:8000` evidence invalidated the result; [Functional Attempt 2](eval-0017-functional-live-runtime-attempt-2.md) is the current passing report.
