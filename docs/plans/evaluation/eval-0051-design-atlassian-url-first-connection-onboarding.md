# EVAL-0051: Atlassian URL-First Connection Onboarding — Design

## Metadata

- ID: `eval-0051-design`
- Status: `complete`
- Evaluator Type: `design`
- Result: `PASS WITH SUGGESTIONS`
- Run ID: `run-20260724-56`
- Attempt: `1`
- Feature: [feat-0051-atlassian-url-first-connection-onboarding](../feature/feat-0051-atlassian-url-first-connection-onboarding.md)
- Spec: [spec-0051-atlassian-url-first-connection-onboarding](../spec/spec-0051-atlassian-url-first-connection-onboarding.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Atlassian Add/discover connection inventory and URL-first setup
- Evidence Coverage: `partial`
- Created: `2026-07-24`

## Scope

- Evaluated the extended setup surface against the Design Constitution and `screen-alignment` extend rules: service/task hierarchy, connection inventory, URL detection, provider choice, local-only state, edit disclosure, long values, and compact containment.

## Checks And Evidence

- Jira/Confluence and Browse/Add-discover remain two separate visible task selectors; the new connection UI stays inside the existing Add/discover surface.
- The Source Instance/Site inventory precedes registration so an existing access path can be judged and edited before adding another reference.
- Existing cards, badges, forms, disclosure rows, buttons, surfaces, borders, radii, typography, spacing, focus behavior, and semantic status roles are reused.
- Provider labels are human-readable access paths. Binding, enabled, capability, local-only, and no-remote-read states use text rather than color alone.
- Long Source names, Site names, and domains use bounded grid tracks plus wrapping. New connection and edit forms use existing stacked form behavior.
- At `700px` and below, each connection summary changes from content-plus-state columns to one column, state badges align to the start, and the existing Atlassian card family reduces padding.
- An isolated server rendered the empty Jira Add/discover document and route-scoped JavaScript with HTTP 200. The HTML contained the Source Instance/Site panel, first-use option, and official Atlassian MCP label.

## Evidence Gaps

- The in-app browser runtime required by the browser-control skill was not exposed, so direct pixel screenshots at `1440`, `920`, `700`, and `320` were not collected.
- This report does not claim unobserved pixel geometry. Source-level containment and responsive rules pass; exact rendered confirmation is a non-blocking suggestion for the user's first manual registration.
- Acceptance impact: non-blocking because the extension reuses the already rendered FEAT-0048/FEAT-0050 card and form families, introduces explicit compact stacking, and has no known layout defect.

## Findings

- No source-level hierarchy, semantic-state, containment, or design-system mismatch was found.
- Suggestion: during the first real registration, glance at the connection row and new-connection fields at the user's normal window width; capture the four-width sample in the next browser-enabled UI run.

## Route

- Next action: `pass`.
