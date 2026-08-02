# SPEC-0062: Atlassian Local Site And Access-Binding Contract

## Metadata

- ID: `spec-0062`
- Status: `approved`
- Run ID: `run-20260727-67`
- Attempt: `1`
- Parent Feature: [feat-0062-atlassian-local-site-and-access-binding-contract](../feature/feat-0062-atlassian-local-site-and-access-binding-contract.md)
- Parent PRD: [prd-0010-atlassian-ui-and-interaction-reconciliation](../prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Surface Lanes: schema → domain/access resolution → consumers → docs/parity
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-27`
- Updated: `2026-07-27`

## Implementation Goal

- Introduce explicit optional Site bindings, make local registration independent
  of Source Instances, and preserve existing connected behavior.

## In-Scope Behavior

- Add a Site-binding relation between canonical domain Site and Source Instance.
- Permit zero-binding Sites and nullable Item/Space access ownership.
- Backfill bindings and Item/Space access ownership from legacy Site parents.
- Resolve local Site by normalized domain and connected work by explicit or
  unambiguous compatible binding.
- Generate bootstrap titles from Jira key/project key, Confluence Space key, or
  decoded Page slug with Page ID fallback.
- Update every current Atlassian read/refresh consumer to avoid requiring Site
  parent ownership.

## Data And Contract Assumptions

- Site local identity is normalized domain.
- Source Instance owns Provider, service, actual reference, enabled state, and
  capability.
- Binding joins access to Site; it does not change Site identity.
- Existing generated display fields may remain for compatibility but are not
  identity or user input.
- No implementation path performs a remote call.

## Verification

- Focused Atlassian, external-access, migration, schema, and documentation tests.
- Complete unit suite, Schema Presentation freshness, Data Model parity, and
  repository privacy check before closure.

## Open Blockers

- None.
