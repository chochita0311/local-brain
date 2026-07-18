# FIX-0017: Fifteen-Item Responsive Pagination

## Metadata

- ID: `fix-0017-fifteen-item-responsive-pagination`
- Status: `complete`
- Run ID: `run-20260717-17`
- Attempt: `4`
- Feature: [feat-0017-paginated-session-inventory](../feature/feat-0017-paginated-session-inventory.md)
- Spec: [spec-0017-paginated-session-inventory](../spec/spec-0017-paginated-session-inventory.md)
- Created: `2026-07-17`

## Trigger

- Human review changed the default Session page size from 20 to 15 and approved different maximum numbered-pagination densities for desktop and narrow screens.

## Bounded Fix

- Changed the fixed query slice to 15 while retaining filtered count, stable order, SQL `LIMIT ? OFFSET ?`, canonical page bounds, and source/workspace query preservation.
- Retained the desktop page model with at most seven numeric or ellipsis tokens.
- Added a narrow page model with at most five tokens: first, current context, last, and ellipses where required.
- Rendered both semantic models through one Jinja macro and used the existing 700px breakpoint to expose exactly one model at a time.
- Preserved the centered number row and symmetric previous/next row at the 320px viewport floor.

## Verification

- Synthetic query evidence covered a `15 / 15 / 15 / 2` slice, filters, page bounds, direct children, and desktop/mobile page models for first, middle, and last positions.
- Template evidence covered both responsive groups, current-page semantics, last-page destinations, and ellipses.
- The actual route rendered 15 rows on the default and next pages and a shorter bounded final page.
- At 320px, only the five-token compact group rendered and remained contained without horizontal document overflow.
- All 41 tests, JavaScript syntax, Jinja loading, diff validation, and repository privacy validation passed.

## Route

- Result: `pass`
