# FIX-0017: Numbered Pagination And Disclosure Polish

## Metadata

- ID: `fix-0017-pagination-disclosure-polish`
- Status: `complete`
- Run ID: `run-20260717-17`
- Attempt: `3`
- Feature: [feat-0017-paginated-session-inventory](../feature/feat-0017-paginated-session-inventory.md)
- Spec: [spec-0017-paginated-session-inventory](../spec/spec-0017-paginated-session-inventory.md)
- Created: `2026-07-17`

## Trigger

- Human runtime review requested direct numbered page reach in the `1 | 2 | … | 10` family, reported broken-looking dropdown corners once a long child list scrolled, and identified a hover seam between the Session link and its right disclosure cell.

## Bounded Fix

- Retained the fixed 20-row SQL `LIMIT ? OFFSET ?` slice and added a compact `page_items` presentation model with first, last, current-adjacent, and ellipsis entries.
- Rendered accessible page-number links plus current-page semantics while retaining previous and next controls and source/workspace query preservation.
- Made the outer dropdown own background, solid border, radius, and clipping; made only the inner child list own bounded vertical scrolling.
- Moved hover and focus-within tone to the Session row and mirrored it on the disclosure trigger without merging the sibling interactive destinations.
- At the 320px floor, centered page numbers above symmetric previous and next controls.

## Verification

- Query tests covered three-page inventory behavior and compact page entries for first, middle, and last positions in a ten-page result.
- Template tests rendered numbered links, current-page semantics, and two ellipses.
- The actual local route rendered page 1 and page 2 with distinct 20-row slices and valid prior/next destinations.
- Rendered inspection confirmed complete-row hover tone, inner-only disclosure scrolling, intact four-sided border and radius, and no horizontal overflow at 320px.
- All 40 tests, JavaScript syntax, Jinja loading, diff validation, and repository privacy validation passed.

## Route

- Result: `pass`
