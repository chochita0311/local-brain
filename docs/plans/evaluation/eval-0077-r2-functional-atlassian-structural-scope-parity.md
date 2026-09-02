# EVAL-0077 R2 Functional: Atlassian Structural Scope Parity

## Metadata

- ID: `eval-0077-r2-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260829-87`
- Attempt: `2`
- Feature: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
- Spec: [SPEC-0077](../spec/spec-0077-atlassian-explorer-inventory-and-search.md)
- Fix: [FIX-0077](../fix/fix-0077-atlassian-structural-scope-parity.md)
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- New integration coverage creates one domain-first Site reused by Jira and
  Confluence, asserts per-service node/list parity, verifies canonical rendered
  branch URLs, rejects ambiguous Explorer route input and cross-service
  structure, and proves global Search retains service-All Site/Space filters.
- The focused Browse module passed 15 tests. The combined persistence,
  registration, Browse, Refresh, and UI-contract suite passed 88 tests.
- Chrome confirmed All shows seven Items, Jira/shared-Site shows three, and
  Wiki/shared-Site shows one. Exactly one visible hierarchy node is active in
  each selected branch.
- Direct `/atlassian?view=all&site_id=1` returns bounded local HTTP `400` with
  no external work. A valid Site-local Unclassified link includes its service
  and Site.
- Chrome confirmed `/search` still returns the shared-Site Item for service-All
  `site_id=1` and `space_id=4`; Jira with the Wiki-only Site returns bounded
  local HTTP `400` instead of a false active scope.
- Unit coverage rejects three invalid All-plus-structure `return_to` variants,
  and Chrome confirmed the rendered detail Back link falls back to
  `/atlassian`.
- The current page reported no console warning, error, or issue after valid
  navigation; the deliberate invalid-route request was the only preserved 400.

## Findings

- None.

## Regression Notes

- Exact search, advanced filters, safe full-detail return, setup/registration,
  and Refresh behavior remain unchanged.

## Route

- Next action: `pass`
