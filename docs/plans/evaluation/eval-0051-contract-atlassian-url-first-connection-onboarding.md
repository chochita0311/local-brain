# EVAL-0051: Atlassian URL-First Connection Onboarding — Contract

## Metadata

- ID: `eval-0051-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260724-56`
- Attempt: `1`
- Feature: [feat-0051-atlassian-url-first-connection-onboarding](../feature/feat-0051-atlassian-url-first-connection-onboarding.md)
- Spec: [spec-0051-atlassian-url-first-connection-onboarding](../spec/spec-0051-atlassian-url-first-connection-onboarding.md)
- Execution Profile: `fullstack-product`
- Surface Lane: URL preview → Source Instance/Site creation → stable Item reuse
- Evidence Coverage: `complete`
- Created: `2026-07-24`

## Scope

- Evaluated local URL recognition, explicit provider ownership, atomic Source/Site/reference creation, exact reuse, one-time configuration binding, bounded editing, no-hidden-I/O behavior, and durable documentation parity.

## Checks And Evidence

- Provider remains a stable LocalBrain access path: `atlassian_cloud` means the official Atlassian MCP connector and `mcp_gateway` means the company Gateway. URL domain, remote Site ownership, and one transient search invocation do not select or rewrite it.
- Source Instance remains the stable provider/service/configuration boundary. Site remains the concrete normalized Atlassian domain below it, and the existing schema continues to allow one Source Instance to own multiple Sites.
- The preview endpoint returns service, kind, normalized URL/domain, identifier, bounded matching Site projections, and a suggested display name. It returns no configuration reference and performs no remote call.
- New onboarding uses one SQLite savepoint for Source Instance, Site, and Item or Space creation. Invalid input or a late registration failure rolls back all three layers.
- Exact compatible Source/Site identity is reused; incompatible key collisions receive a deterministic bounded local key instead of mutating another connection.
- Unbound Source Instances are valid local-only containers. Binding can fill a previously absent configuration reference once; provider, service, existing binding, Site domain, and stable IDs remain immutable.
- Remote metadata/content, local classification, evidence, Workstream/Thread relations, refresh readiness, and existing Item identity remain under their prior owners.
- Product, Architecture, Privacy, Source Registry, Atlassian Source Memory, README, PRD, Feature, and Spec language match the implemented boundary.

## Evidence Gaps

- No company ticket or Page body was read. The official Atlassian accessible-Site metadata observed during planning informed the provider/Site distinction but is not persisted by this Feature.
- Acceptance impact: not applicable; live remote content is outside this local-onboarding contract.

## Findings

- None.

## Regression Notes

- The complete 260-test suite, current schema presentation, nine data-model owners, 512-object schema cleanup audit, repository privacy check, Python compilation, JavaScript syntax, and diff whitespace checks passed.

## Route

- Next action: `pass`.
