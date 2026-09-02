# FIX-0077: Atlassian Structural Scope Parity

## Metadata

- ID: `fix-0077`
- Status: `complete`
- Feature: [FEAT-0077](../feature/feat-0077-atlassian-explorer-inventory-and-search.md)
- Run: [RUN-20260829-87](../run/run-20260829-87-atlassian-explorer-inventory-and-search.md)
- Spec: [SPEC-0077](../spec/spec-0077-atlassian-explorer-inventory-and-search.md)
- Trigger: post-pass canonical contract audit
- Created: `2026-08-29`
- Updated: `2026-08-29`

## Findings

- A Site is service-independent and may own Jira and Confluence Items. All view
  groups that Site under both service branches, but the emitted Site URL kept
  `view=all`. Selecting either branch therefore returned both services, marked
  both duplicate Site nodes active, and made node count differ from list count.
- `structural_scope=unclassified` was accepted without `site_id`, creating a
  global state that has no approved hierarchy node. Unclassified is Site-local.

## Required Correction

- In combined All hierarchy, make each service-branch Site/Space/Unclassified
  destination enter that branch's canonical Jira or Wiki view. In a specific
  service view, keep the current service view.
- Require `site_id` whenever `structural_scope=unclassified`; reject the invalid
  combination before query/list projection.
- Keep the explicit-service requirement at the Explorer route boundary so
  global Search retains independent Site/Space filters. Reject a selected Site
  or Space that belongs only to a different explicit service, and qualify
  active-structure lookup by service.
- Remove the unreachable `All Sites / Unclassified` active-state fallback.
- Add synthetic coverage for one canonical Site shared by both services and for
  rejected Site-less Unclassified route/read-model input.
- Recheck count/list parity, single active node, exact-query/filter preservation,
  direct URLs, owner docs, four-width rendering, and all required evaluators.

## Scope Guard

- Do not add a new URL parameter, duplicate Site identity, global Unclassified
  node, schema change, nested hierarchy, external call, or FEAT-0078 behavior.

## Validation

- Attempt 2 passed: 15 focused Browse tests, the 88-test Atlassian/UI suite,
  shared-Site and global-Search Chrome checks, invalid return-path fallback,
  four R2 evaluators, and the final independent contract audit all passed.

## Continuity Notes

- `2026-08-29`: opened after the canonical audit invalidated Attempt 1's
  incomplete structural-edge coverage.
