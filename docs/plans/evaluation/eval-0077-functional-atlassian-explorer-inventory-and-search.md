# EVAL-0077 Functional: Atlassian Explorer Inventory And Search

## Metadata

- ID: `eval-0077-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `FAIL`
- Run ID: `run-20260829-87`
- Attempt: `1`
- Feature: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
- Spec: [SPEC-0077](../spec/spec-0077-atlassian-explorer-inventory-and-search.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `local read model -> route state -> server-rendered interaction`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Active feature: local combined inventory, exact search, structural navigation,
  advanced filters, and full-detail handoff.
- Active spec: SPEC-0077.
- Evaluated build: backend projection, route/context adapters, HTML/CSS, and
  no-script/browser behavior.

## Checks And Evidence

- Synthetic Jira and Wiki Items rendered together in default `All`; Jira and
  Wiki scopes selected their correct service without changing persisted data.
- Hierarchy/list tests covered combined service, Site, Space, null-Space,
  duplicate key across Sites, unavailable Item, default archive exclusion, and
  advanced-filter intersection.
- `TEAM-42` exact search returned the two identity matches in stable ID order and
  showed per-row exact-role excerpts. Selecting the long-domain Site retained
  `q=TEAM-42`, returned one Item, and kept its source identity visible.
- The optional filter disclosure exposed exactly six selects. It was closed on
  entry and remained independent from the structural hierarchy disclosure.
- Every result was an ordinary server-executable link. The clicked Item detail
  exposed a safe `← Atlassian inventory` link and returned to the original
  service, query, and Site state.
- At `1440` the rail was visible and compact hierarchy hidden. At `920`, `700`,
  and `320` those states inverted. The 320 touch-emulated hierarchy opened and
  exposed all eligible Site/Space links.
- Chrome reported one local search input, zero visible global search inputs,
  no horizontal overflow, and no console warning/error/issue messages.

## Evidence

- `.venv/bin/python -m unittest tests.test_atlassian tests.test_atlassian_registration tests.test_atlassian_browse tests.test_atlassian_refresh tests.test_ui_contract -v` — 86 passed.
- Chrome DevTools isolated synthetic runtime: `1440`, `920`, `700`, and `320`;
  exact search, structural selection, detail navigation/back, filter disclosure,
  compact hierarchy, computed overflow, accessibility tree, and console checked.
- `git diff --check` — passed.

## Evidence Gaps

- None.

## Findings

- Blocking implementation findings are shared with the contract evaluation:
  service-branch Site counts diverged from an All/Site list for a shared Site,
  and Site-less global Unclassified was accepted without a matching node.

## Regression Notes

- Registration/setup remains reachable for FEAT-0079, Refresh behavior remains
  unchanged for FEAT-0080, and full-detail editing remains owned by FEAT-0078.

## Route

- Next action: `fix`
