# EVAL-0075 Contract: Atlassian Explorer Family And State Contract

## Metadata

- ID: `eval-0075-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260829-85`
- Attempt: `1`
- Feature: [FEAT-0075](../feature/feat-0075-atlassian-explorer-family-and-state-contract.md)
- Spec: [SPEC-0075](../spec/spec-0075-atlassian-explorer-family-and-state-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: `durable-design -> product-interaction -> consumer-audit`
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Active feature: durable Atlassian Explorer family and state ownership.
- Active spec: SPEC-0075.
- Evaluated build: working-tree policy and planning changes for RUN-85.

## Checks

- Confirmed Atlassian moved from Browse/inventory to Explorer in exactly one
  durable family table.
- Confirmed the Explorer law distinguishes Local Context containment from
  Atlassian Service/Site/Space-or-project/Unclassified structure.
- Confirmed Product Model owns one query, `All / Jira / Wiki`, every requested
  state transition, responsive normalization, and four distinct actions.
- Confirmed stored `confluence`, optional Space, local-first, read-only, and
  explicit Refresh contracts remain intact.
- Confirmed the Design Governance version log records v15.
- Audited current consumers and confirmed their known mismatches are assigned
  to FEAT-0076 through FEAT-0080 rather than silently changed here.
- Confirmed no runtime or test file changed in RUN-85.

## Evidence

- Environments checked: policy source inspection, feature/spec/run trace,
  current route/template/Local Context consumer inspection, and `git diff`.
- The shared owners are the Design Constitution family/search/pattern rules and
  Product Model Atlassian state/action section; representative consumers were
  the current `/atlassian` route, shared header, Atlassian template, and Local
  Context Explorer implementation.
- `git diff --check` passed.
- `git diff -- src/localbrain tests` was empty.

## Evidence Gaps

- None. Rendered runtime evidence is not an acceptance requirement for this
  documentation-only foundation Feature and no rendered behavior is claimed.

## Contract Evidence

- Producer surfaces:
  - `docs/policies/design/design-constitution.md`
  - `docs/policies/design/design-document-governance.md`
  - `docs/policies/project/product.md`
- Consumer surfaces:
  - FEAT-0076 through FEAT-0080
  - current Atlassian route, shared header, template, query, interaction, and
    style owners as staged downstream adoption points
- Schemas, payloads, generated artifacts, commands, routes, config, or policy
  docs checked: Design Constitution family table and patterns, governance v15,
  Product Model state/action table, current `/atlassian` route parameters and
  service coercion, shared global-query markup, Atlassian selectors/links, and
  Local Context browse-to-preview behavior.
- Stale-assumption check:
  - Jira default and service coercion -> FEAT-0077
  - simultaneous global/local query and selector matrix -> FEAT-0077
  - token-AND retrieval -> FEAT-0076
  - full-page-only detail -> FEAT-0078
  - Add/setup/discovery composition -> FEAT-0079
  - absent explicit persisted-evidence Sync action -> FEAT-0080

## Findings

- None.

## Regression Notes

- Local Context and Schema remain Explorer members with their own containment.
- Search outside Atlassian remains in the shared header.
- PRD-0007/0008 identity, access, evidence, discovery, and Refresh constraints
  remain explicit.

## Route

- Next action: `pass`

## Continuity Notes

- `2026-08-29`: contract evaluation passed with complete policy and consumer
  evidence; runtime adoption remains intentionally staged.
