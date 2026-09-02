# EVAL-0077 R2 UX: Atlassian Structural Scope Parity

## Metadata

- ID: `eval-0077-r2-ux`
- Status: `complete`
- Evaluator Type: `ux-heuristic`
- Result: `PASS`
- Run ID: `run-20260829-87`
- Attempt: `2`
- Feature: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
- Spec: [SPEC-0077](../spec/spec-0077-atlassian-explorer-inventory-and-search.md)
- Fix: [FIX-0077](../fix/fix-0077-atlassian-structural-scope-parity.md)
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- A Site shared by Jira and Wiki no longer produces a misleading mixed list
  after choosing one service branch. The displayed count, active node, service
  tab, and adjacent rows now describe the same scope.
- All remains a combined orientation surface. Choosing a structural child
  makes the otherwise implicit service choice visible and reversible through
  the existing All/Jira/Wiki control.
- Site-local Unclassified remains reachable from its hierarchy parent; the
  unsupported global form is rejected instead of presenting an orientation
  state with no matching node.
- Wide and compact/narrow flows retain the same labels and destinations, and
  the touch-emulated `320` flow exposes both shared-Site branches without
  overflow or a second search decision.

## Findings

- None.

## Route

- Next action: `pass`
