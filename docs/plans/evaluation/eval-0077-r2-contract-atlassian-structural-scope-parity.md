# EVAL-0077 R2 Contract: Atlassian Structural Scope Parity

## Metadata

- ID: `eval-0077-r2-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260829-87`
- Attempt: `2`
- Feature: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
- Spec: [SPEC-0077](../spec/spec-0077-atlassian-explorer-inventory-and-search.md)
- Fix: [FIX-0077](../fix/fix-0077-atlassian-structural-scope-parity.md)
- Evidence Coverage: `complete`
- Created: `2026-08-29`

## Scope

- Re-evaluated only the two blocking Attempt 1 findings and their effect on
  service/structure URL ownership, hierarchy counts, active state, and owner
  documentation.

## Checks And Evidence

- A synthetic canonical Site containing three Jira Items and one Confluence
  Item is projected independently under both service branches in combined All.
- The Jira Site destination is canonical `view=jira&site_id=1` and returns the
  three Jira Items; the Wiki destination is canonical
  `view=wiki&site_id=1` and returns its one Confluence Item. Each visible active
  node count equals list membership.
- Explorer All-plus-structure input is rejected as ambiguous. `Unclassified`
  requires both an explicit service and Site, while the Site/Space intersection
  remains unchanged for valid inputs. A Site or Space owned only by the other
  service is rejected, while global Search still accepts independent Site and
  Space filters with its service set to All.
- Product Model, Atlassian Source Memory, SPEC-0077, and focused synthetic tests
  now own the same service-qualified structural contract.
- Page routing and `return_to` sanitization share the same Explorer structural
  validator; All-plus-Site, All-plus-Space, and All-plus-Unclassified back
  targets fall back to `/atlassian` instead of preserving a future 400.
- The 88-test Atlassian/UI regression set passed, and `git diff --check` passed.

## Findings

- None.

## Route

- Next action: `pass`
