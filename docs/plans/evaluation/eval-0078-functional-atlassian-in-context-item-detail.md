# EVAL-0078 Functional: Atlassian In-Context Item Detail

## Metadata

- ID: `eval-0078-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260829-88`
- Attempt: `2`
- Feature: [FEAT-0078](../feature/feat-0078-atlassian-in-context-item-detail.md)
- Spec: [SPEC-0078](../spec/spec-0078-atlassian-in-context-item-detail.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `preview read model; selection/history; presentation`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Checks And Evidence

- Synthetic projection tests cover every bounded group, deterministic metadata
  path escaping/order, exact-query and filter eligibility, missing and
  ineligible Items, targeted structural normalization, and the explicitly
  incomplete recent-200 maintenance history.
- Route tests prove full and partial states share one preview contract, partial
  reads avoid broad inventory loaders, invalid selection is bounded, clear
  state remains executable, and semantic `return_to` canonicalization rejects
  or repairs unsafe structure.
- Full-detail local forms and Item Refresh preserve the selected Explorer
  return through validation, execution redirects, polling/retry, and final
  navigation without changing Refresh eligibility or batching.
- Chrome click selection replaced only the preview and kept all seven rows
  mounted. Same-row activation did not add duplicate history; rapid Item 2 then
  Item 4 selection settled on Item 4 only.
- Back and forward restored selected row, URL, title, preview identity, focus,
  and practical list position. Direct selected entry oriented the list to its
  row; close restored row focus. Missing entry closed to the results heading.
- Result-list and page scroll update the current history entry. Pending scroll
  frames are cancelled on `popstate` and guarded by URL/DOM identity, so rapid
  traversal cannot overwrite the destination entry with a prior snapshot.
- A forced selection fetch failure used the ordinary full-detail row link. A
  forced close fetch failure navigated to the canonical clear-selection URL.
  Cross-service partial input returned local `400`, while a known Space without
  Site returned canonical state with its owner Site.
- The focused command ran 72 preview/Browse/Refresh/UI-contract tests with no
  failures. `node --check src/localbrain/static/atlassian.js` and
  `git diff --check` also passed.

## Findings

- None.

## Regression Notes

- FEAT-0077 hierarchy, exact query, filters, full-detail local edits, existing
  Refresh execution, and shared global Search remain executable.

## Route

- Next action: `pass`
