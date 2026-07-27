# FEAT-0053: Connected Atlassian First-Use Validation

## Metadata

- ID: `feat-0053`
- Status: `passed`
- Type: `foundation`
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Goal

- Establish direct, owner-reviewed evidence for the implemented Atlassian first-use paths through the configured official Atlassian MCP and company MCP Gateway boundaries without treating synthetic coverage as connected proof or changing product behavior during discovery.

## Acceptance Contract

- One approved inventory names every Source Instance, Site, service, operation, and synthetic or private fixture permitted in the Run before any connected request occurs.
- The inventory distinguishes the target Site, MCP connection, Claude or Codex runner, and requested logical read.
- Every connected operation is allowed by the passed FEAT-0044 read-only policy, uses an explicit current capability observation, and remains inside the configured MCP boundary.
- Local-only page load, registration preview, browse, search, classification, and no-change paths are verified separately from remote discovery or refresh.
- Required first-use, successful read, no-change, unavailable, unauthorized, stale-capability, partial-failure, and retry states have direct or explicitly justified substitute evidence.
- Connected results are compared with the rendered LocalBrain state without copying private URLs, titles, content, screenshots, credentials, or identifiers into tracked artifacts.
- Every observation is classified as `no defect`, `implementation bug`, `spec gap`, `planning gap`, or `environment limitation`.
- Validation does not silently patch code, alter PRD-0007 contracts, register candidates, refresh unrelated Items, or invoke an external write.

## Scope Boundary

- In:
  - approved connected fixture and operation inventory
  - official Atlassian MCP and company MCP Gateway paths that are currently configured and relevant
  - bounded capability freshness checks required by the inventory
  - connected Space or project discovery and explicit refresh scenarios
  - local registration, browse, search, classification, and no-hidden-read checks
  - rendered first-use, error, unavailable, and recovery evidence
  - privacy-safe finding classification and routing
- Out:
  - broad Site, Space, project, Page, or ticket crawling
  - external writes or write-shaped tool invocation
  - credential, OAuth, MCP installation, or Gateway configuration changes
  - production-data copies in tracked tests or reports
  - fixes to behavior found during validation
  - Atlassian Add redesign owned by FEAT-0054

## Surface Lanes

- Test-boundary lane:
  - path roots: this Feature, the active Spec, private runtime inventory, and approved external-access policies
  - dependencies: owner-approved exact fixtures and FEAT-0044 through FEAT-0051
  - expected evidence: enumerated targets, permitted reads, privacy handling, expected state, and stop conditions
  - evaluator ownership: `contract`
- Connected-operation lane:
  - path roots: configured official Atlassian MCP and company MCP Gateway host boundaries
  - dependencies: current applicable capability observations and the test-boundary lane
  - expected evidence: bounded request/result metadata and isolation by Source Instance without retained private payload
  - evaluator ownership: `contract`, `functional`
- Local-product lane:
  - path roots: `/atlassian`, `/atlassian/refresh`, Item detail, local search, relevant templates, routes, and client behavior
  - dependencies: the connected-operation lane only for scenarios that explicitly require a remote read
  - expected evidence: local-only versus remote-triggered behavior, visible provenance, feedback, recovery, and no-hidden-read behavior
  - evaluator ownership: `functional`, `design`, `ux-heuristic`
- Finding lane:
  - path roots: Run and evaluation artifacts
  - dependencies: all executed scenarios
  - expected evidence: one classification, owner, reproduction boundary, and next planning target per finding
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- FEAT-0044 capability observation and read-only dispatch policy.
- FEAT-0045 external synchronization manifest and result contract.
- FEAT-0046 Source Instance, Site, Space, Item, and freshness identity.
- FEAT-0048 through FEAT-0051 registration, refresh, browse, classification, and onboarding behavior.
- Private runtime evidence versus tracked synthetic evidence boundary.
- Finding classification and routing contract.

## Entry And Exit

- Entry point: the owner approves the exact connected test inventory and starts the validation Run.
- Exit or transition behavior: the Run closes with privacy-safe scenario evidence and a classified finding ledger. Any behavior change returns to FEAT-0054, Spec review, or a new corrective Feature.

## State Expectations

- Default: no remote request occurs while the Feature remains draft or while the inventory is incomplete.
- Ready: every selected operation has an enabled Source Instance, explicit Site, current applicable capability, and expected result boundary.
- Unavailable: the registered target remains identifiable and the affected scenario records an environment limitation or product-visible recovery result.
- Error: failure evidence is bounded, contains no private payload, and does not broaden scope or retry automatically.
- Success: all required scenarios have direct or justified substitute evidence and every finding is classified.

## Dependencies

- PRD-0008 is `approved`.
- FEAT-0044 through FEAT-0051 remain `passed`.
- The human owner must approve the exact connected fixture and read inventory before this Feature may become `approved`.

## Likely Affected Surfaces

- `docs/plans/spec/`, `run/`, and `evaluation/` artifacts for FEAT-0053
- `src/localbrain/external_access.py`
- `src/localbrain/external_sync.py`
- `src/localbrain/atlassian*.py`
- `src/localbrain/main.py`
- `src/localbrain/templates/atlassian*.html`
- focused Atlassian route, policy, and UI tests

## Pass Or Fail Checks

- Pass if every remote request maps to one pre-approved inventory row and current allowed capability.
- Pass if local-only scenarios prove page load, preview, browse, search, and classification do not contact Atlassian.
- Pass if official MCP and Gateway evidence remains isolated by Source Instance and visible provenance identifies the selected access path.
- Pass if unavailable, stale, failure, retry, and no-change states are exercised at the approved boundary.
- Pass if tracked artifacts contain only synthetic or redacted structural evidence.
- Pass if every observation is classified and no code or persistent record changes occur outside the scenario's approved action.
- Fail on an unlisted read, any write-shaped invocation, broad discovery, private tracked evidence, or an opportunistic fix.

## Regression Surfaces

- FEAT-0044 through FEAT-0051.
- Read-only external access and explicit capability refresh.
- Local-only Atlassian browse and registration.
- Source Instance isolation, MCP call accounting, and maintenance Session ownership.
- Repository privacy checks.

## Harness Trace

- Active spec: [spec-0053-connected-atlassian-first-use-validation](../spec/spec-0053-connected-atlassian-first-use-validation.md)
- Active run: [run-20260724-58-connected-atlassian-first-use-validation](../run/run-20260724-58-connected-atlassian-first-use-validation.md)
- Execution profile: `foundation-contract`
- Latest evaluations:
  - [contract](../evaluation/eval-0053-contract-connected-atlassian-first-use-validation.md) — `PASS WITH SUGGESTIONS`
  - [design](../evaluation/eval-0053-design-connected-atlassian-first-use-validation.md) — `PASS WITH SUGGESTIONS`
  - [functional](../evaluation/eval-0053-functional-connected-atlassian-first-use-validation.md) — `PASS`
  - [ux heuristic](../evaluation/eval-0053-ux-connected-atlassian-first-use-validation.md) — `PASS WITH SUGGESTIONS`
- Latest fix note: not created

## Open Review Decisions

- None. The owner authorized the private alias inventory and sequential execution on `2026-07-24`; unavailable connector paths use explicitly classified synthetic substitutes without claiming live execution.

## Continuity Notes

- `2026-07-24`: initial draft split direct connected evidence from Atlassian product corrections so validation cannot silently change passed PRD-0007 behavior.
- `2026-07-24`: Attempt 2 passed with a bounded official Jira metadata read, explicit official Confluence and Gateway environment limitations, 78 focused tests, aggregate-only local runtime inspection, and no external or persistent write.
