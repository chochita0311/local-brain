# EVAL-0077 Contract: Atlassian Explorer Inventory And Search

## Metadata

- ID: `eval-0077-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `FAIL`
- Run ID: `run-20260829-87`
- Attempt: `1`
- Feature: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
- Spec: [SPEC-0077](../spec/spec-0077-atlassian-explorer-inventory-and-search.md)
- Execution Profile: `fullstack-product`
- Surface Lane: `read-model -> route/shell -> presentation -> docs`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Active feature: responsive Atlassian Explorer inventory and exact search.
- Active spec: SPEC-0077.
- Evaluated build: hierarchy projection, canonical route state, shared-shell
  handoff, server-rendered Explorer, responsive styling, tests, and owner docs.

## Checks

- Verified `/atlassian` defaults to `All` and maps `All / Jira / Wiki` to
  `None / jira / confluence` without coercing combined inventory to Jira.
- Verified one local exact query consumes FEAT-0076 results without a fuzzy,
  model, provider, or global-FTS fallback.
- Verified Site, Space, and `Unclassified` are structural scope while coverage,
  freshness, attention, Topic, Tag, and Workstream are the only advanced axes.
- Verified hierarchy counts and adjacent list membership derive from the same
  query/service/advanced-filter/archive-default eligible population.
- Verified service changes preserve query and advanced filters while resetting
  incompatible structure; hierarchy changes preserve compatible query/filter
  state; clear and reset have distinct canonical URLs.
- Verified Item destinations receive one bounded local `return_to`; scheme,
  host, unknown parameter, and oversized input cannot become a back target.
- Verified Atlassian owns one visible query while its Explorer is active and
  the global Search destination remains available without changing other routes.
- Verified Product Model and Atlassian Source Memory describe the implemented
  hierarchy, exact-query consumer, and six-filter ownership.

## Evidence

- Environments checked: source inspection, synthetic SQLite integration tests,
  isolated synthetic runtime, and Chrome DevTools rendered interaction.
- Commands:
  - `.venv/bin/python -m unittest tests.test_atlassian tests.test_atlassian_registration tests.test_atlassian_browse tests.test_atlassian_refresh tests.test_ui_contract -v` — 86 passed
  - `git diff --check` — passed
- Browser contract evidence: exact `TEAM-42` returned two same-key Items from
  distinct Sites; selecting one Site reduced the list to one and retained the
  query; detail then returned to the exact `/atlassian?view=all&q=TEAM-42&site_id=2`
  state.

## Evidence Gaps

- None.

## Contract Evidence

- Producer surfaces: persisted Atlassian Items, Sites, Spaces, classifications,
  Workstream links, and FEAT-0076 exact result annotations.
- Consumer surfaces: `browse_inventory()`, `/atlassian`, the Explorer template,
  hierarchy and service links, filter forms, and Item back links.
- Schemas, payloads, generated artifacts, commands, routes, config, or policy
  docs checked: existing SQLite schema, route query parameters, Jinja context,
  Product Model, Atlassian Source Memory, and shared-shell state.
- Stale-assumption check: global Search remains historical FTS; Browse no longer
  defaults to Jira; Source Instance and Item type are not primary filters; no
  nested remote hierarchy or external call was introduced.

## Findings

- Severity: blocking; classification: `implementation bug`. A canonical Site
  shared by Jira and Confluence appears once in each All-service branch, but
  either Site link selected both services. Each active node count could be one
  while the adjacent list count was two.
- Severity: blocking; classification: `implementation bug`. A Site-less
  `structural_scope=unclassified` value produced a global Unclassified list even
  though the approved hierarchy exposes only Site-local Unclassified nodes.

## Regression Notes

- Existing registration, refresh, full-detail, global UI-token, and Atlassian
  persistence tests passed. No schema or remote integration behavior changed.

## Route

- Next action: `fix`

## Continuity Notes

- `2026-08-29`: contract evaluation passed with complete automated and rendered
  evidence.
- `2026-08-29`: post-pass canonical audit added the missing shared-Site and
  Site-less-Unclassified evidence, changed the result to FAIL, and routed
  FIX-0077 plus Attempt 2.
