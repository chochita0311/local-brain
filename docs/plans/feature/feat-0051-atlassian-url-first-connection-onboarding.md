# FEAT-0051: Atlassian URL-First Connection Onboarding

## Metadata

- ID: `feat-0051`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Let the user start with an Atlassian URL, review the locally parsed Item and access boundary, and create the required Source Instance, Site, and Item without encountering a dead-end prerequisite message.

## Acceptance Contract

- The registration form parses an HTTP(S) Atlassian URL locally and visibly identifies service, normalized Site domain, Item or Space kind, and remote key or ID when present.
- An already configured enabled Site is reused under the existing unambiguous selection rules.
- When no Site matches, the user can choose `MCP 연결 (Provider)` as official Atlassian MCP or company MCP Gateway and confirm one atomic Source Instance, Site, and Item or Space registration.
- URL shape never determines provider. Provider represents the stable LocalBrain access path, not the remote domain or one transient search invocation.
- A new Source Instance may remain unbound when no Cloud ID or Gateway alias is supplied. Local reference registration still succeeds, while remote discovery and refresh remain visibly unavailable until capability setup is complete.
- Source and Site display names, enabled state, and a previously absent configuration reference can be edited later. Provider, service, bound configuration reference, normalized Site domain, and stable local IDs are not silently rewritten.
- Registration, preview, editing, page load, and view switching perform no remote call.
- Existing duplicate reuse, cross-Instance isolation, local fields, relations, shell, and responsive behavior remain intact.

## Scope Boundary

- In:
  - local URL preview
  - atomic Source Instance, Site, and Item or Space onboarding
  - human-readable provider/access-path selection
  - unbound local-only Source Instances
  - Source/Site connection inventory and bounded editing
  - empty, invalid, duplicate, ambiguous, bound, unbound, disabled, and success states
- Out:
  - automatic inspection of Codex or Claude connector inventories from the web process
  - implicit capability checks or remote ticket/Page reads
  - credentials, tokens, OAuth, or connector installation
  - changing a bound provider/configuration identity in place
  - cross-provider or cross-domain Item merge

## Surface Lanes

- Registration contract lane:
  - URL preview projection, deterministic Source key generation, atomic creation/reuse, one-time binding, validation, and tests
- Route and interaction lane:
  - preview, registration, and edit routes with no-script fallback and bounded errors
- Atlassian UI lane:
  - URL detection state, access-path fields, connection inventory, edit disclosure, responsive containment, and focus/feedback
- Durable contract lane:
  - product, privacy, architecture, Source Registry, Atlassian owner docs, PRD trace, and regression evidence

## Contract Surfaces

- `/api/atlassian/registration-preview`
- `/atlassian/register`
- `/atlassian/connections/{source_instance_id}/sites/{site_id}`
- `external_source_instances` and `atlassian_sites` existing ownership contracts
- `register_source_instance`, `bind_source_instance_config_ref`, `register_atlassian_site`, and `register_atlassian_url`

## Pass Or Fail Checks

- Pass if the first valid URL can create its missing Source/Site and local reference atomically without remote I/O.
- Pass if invalid, service-mismatched, or failed onboarding creates none of the three records.
- Pass if a matching configured Site is reused and ambiguous matches still require explicit selection.
- Pass if unbound connections are visibly local-only and cannot imply refresh readiness.
- Pass if only permitted editable fields change and stable identity/relations remain unchanged.
- Pass if populated and empty states remain usable at `1440`, `920`, `700`, and `320`.
- Fail on provider inference from URL alone, hidden connector calls, partial persistence, bound identity mutation, or cross-Instance merge.

## Regression Surfaces

- FEAT-0044 capability and read-only policy
- FEAT-0046 Source/Site/Item identity
- FEAT-0048 direct URL registration and Space discovery
- FEAT-0049 explicit refresh gating
- FEAT-0050 browse and local classification

## Harness Trace

- Active spec: [spec-0051-atlassian-url-first-connection-onboarding](../spec/spec-0051-atlassian-url-first-connection-onboarding.md)
- Active run: [run-20260724-56-atlassian-url-first-connection-onboarding](../run/run-20260724-56-atlassian-url-first-connection-onboarding.md)
- Latest evaluations:
  - [contract](../evaluation/eval-0051-contract-atlassian-url-first-connection-onboarding.md) — `PASS`
  - [design](../evaluation/eval-0051-design-atlassian-url-first-connection-onboarding.md) — `PASS WITH SUGGESTIONS`
  - [functional](../evaluation/eval-0051-functional-atlassian-url-first-connection-onboarding.md) — `PASS`
  - [ux heuristic](../evaluation/eval-0051-ux-atlassian-url-first-connection-onboarding.md) — `PASS`

## Open Review Decisions

- None. The owner approved URL-first creation and later editing on `2026-07-24`; provider remains an explicit local access-path choice when no configured Site can be matched.

## Continuity Notes

- `2026-07-24`: live first-use review found that FEAT-0048's configured-Site prerequisite had no user-facing creation path.
- `2026-07-24`: the owner approved URL-first onboarding and clarified that provider should describe the local MCP access route.
- `2026-07-24`: Attempt 1 passed 260 tests, isolated local HTTP checks, schema/privacy guards, and all required evaluators. Direct rendered viewport capture remains a non-blocking evidence suggestion.
- `2026-07-24`: first-use copy review renamed the ambiguous `로컬 접근 경로` field to `MCP 연결 (Provider)`; the persistence field remains `provider_kind`.
