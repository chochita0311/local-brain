# EVAL-0044: MCP Capability And Read-Only Policy — Functional

## Metadata

- ID: `eval-0044-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260723-49`
- Attempt: `1`
- Feature: [feat-0044-mcp-capability-and-read-only-policy](../feature/feat-0044-mcp-capability-and-read-only-policy.md)
- Spec: [spec-0044-mcp-capability-and-read-only-policy](../spec/spec-0044-mcp-capability-and-read-only-policy.md)
- Execution Profile: `foundation-contract`
- Surface Lane: registration and observation → authorization states → compatibility and regression
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated registration identity, observation replacement and invalidation, all bounded capability states, provider-specific allowed-read descriptors, denial paths, instance isolation, startup compatibility, generated artifacts, privacy, and repository-wide regressions.

## Checks And Evidence

- Twenty focused tests passed for all four provider/service pairs, stable re-registration and one-time Cloud ID binding, identity conflicts, observation replacement and cascade, explicit invalidation, capability bootstrap, and disabled isolation.
- Synthetic Gateway Jira tests proved exact nested dispatch, selected metadata and description fields, bounded pagination, and rejected comment-shaped JQL. Official Jira tests proved configuration injection and field rejection.
- Synthetic Confluence tests proved regular-Page-only search, exact Page and hierarchy targets, fixed expansions, and rejection of excluded content types. Official Confluence unavailability remained an explicit no-authority state.
- Unknown and write-shaped operations were rejected before descriptor construction. Noncanonical capability JSON, missing or malformed fingerprints, invalid configuration references, raw failure-shaped error codes, and direct configuration corruption all failed closed.
- A temporary file-backed startup added the new tables while preserving a pre-existing External Resource. Direct invalid provider and availability rows remained constrained by SQLite.
- Twenty-two focused schema-presentation, explorer, and cleanup-audit tests passed. Data Model parity, current generated schema, the 350-object ledger, nine Mermaid diagrams, and whitespace checks passed.
- The complete Python suite passed 190 tests. Repository privacy passed across 479 candidate files.

## Evidence

- Environments checked: fresh in-memory SQLite, temporary file-backed startup, synthetic provider/service descriptors, deterministic generated artifacts, and the complete local test suite.
- External tools were not invoked because FEAT-0044 ends at a validated `ToolDispatch`; this is the required functional boundary rather than missing runtime evidence.

## Evidence Gaps

- None.

## Findings

- None.

## Regression Notes

- Existing Runner, ingestion, retrieval, schema migration, UI contract, Usage, Workstream, and Markdown suites passed. One existing Starlette template deprecation warning remains unrelated and non-blocking.

## Route

- Next action: `pass` and return FEAT-0044 to the Orchestrator for human acceptance.
