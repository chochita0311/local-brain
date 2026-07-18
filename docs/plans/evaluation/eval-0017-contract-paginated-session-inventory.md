# EVAL-0017: Paginated Session Inventory Contract

## Metadata

- ID: `eval-0017-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260717-17`
- Attempt: `1`
- Feature: [feat-0017-paginated-session-inventory](../feature/feat-0017-paginated-session-inventory.md)
- Spec: [spec-0017-paginated-session-inventory](../spec/spec-0017-paginated-session-inventory.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Session query and route read model
- Created: `2026-07-17`

## Contract Evidence

- `session_inventory_page` counts eligible primary work Sessions before applying `LIMIT 20 OFFSET`, orders by effective activity and stable ID, and returns bounded page metadata.
- Source and workspace predicates are applied to both total and page rows. Previous and next destinations retain valid filters.
- `/sessions` canonicalizes missing, non-numeric, zero, negative, and out-of-range page state through a `303` while preserving valid source and workspace scope.
- Child attachment requires a direct normalized parent ID, matching source, `work` classification, and `subsession` role. Grandchildren, unresolved parents, cross-source children, and maintenance Sessions are absent.
- User-facing Session detail lookup continues to accept a primary Session or its direct eligible child only.

## Automated Evidence

- `tests/test_session_inventory.py` passed multi-page `20 / 20 / 5`, filter-before-bound, direct-child-only, and detail-gating cases.
- The full 32-test suite passed.

## Findings And Regression

- No blocking contract finding.
- Existing unbounded helper behavior remains available to unrelated consumers; `/sessions` now owns the bounded inventory contract.

## Route

- Next action: `pass`
