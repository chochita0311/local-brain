# EVAL-0062: Atlassian Local Site And Access-Binding Contract — Functional

## Metadata

- ID: `eval-0062-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260727-67`
- Attempt: `1`
- Feature: [feat-0062-atlassian-local-site-and-access-binding-contract](../feature/feat-0062-atlassian-local-site-and-access-binding-contract.md)
- Spec: [spec-0062-atlassian-local-site-and-access-binding-contract](../spec/spec-0062-atlassian-local-site-and-access-binding-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: local registration, access resolution, and regressions
- Evidence Coverage: `complete`
- Created: `2026-07-27`

## Scope

- Evaluated zero-binding URL registration, binding creation/reuse, local
  evidence attachment, connected discovery, and refresh readiness.

## Checks And Evidence

- Jira Item/project and Confluence Page/Space URLs create or reuse local records
  without creating a Source Instance.
- URL-derived titles use Jira keys, project/Space keys, decoded Page slugs, and
  Page ID fallback.
- Separate access setup requires a real validated reference and creates or
  reuses one Source Instance/binding without changing Site identity.
- Generated compatibility display names cannot be edited through current
  registration or connection-update APIs.
- An unbound target uses one enabled same-service binding only; none or several
  remain safely unavailable for refresh.
- Local-only registered URLs participate in Session/Local Context evidence
  reconciliation without a remote call.

## Evidence Gaps

- None.

## Findings

- None.

## Regression Notes

- Focused Atlassian registration, evidence, refresh, browse, migration, and
  external-access suites passed.

## Route

- Next action: `pass`.
