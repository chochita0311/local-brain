# FEAT-0044: MCP Capability And Read-Only Policy

## Metadata

- ID: `feat-0044`
- Status: `passed`
- Type: `foundation`
- Surface: `infra`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Goal

- Establish one evidence-backed capability and enforceable read-only policy for every configured Atlassian Source Instance so downstream synchronization can select only supported reads and cannot invoke exposed external writes.

## Acceptance Contract

- Each configured Gateway Jira, Gateway Wiki, or official Atlassian Cloud connection has a stable local Source Instance identity independent of display labels such as old or new.
- A capability record distinguishes service availability, authentication state, metadata reads, content reads, hierarchy reads, field selection, body format, pagination, batching, version evidence, and bounded error behavior.
- The initial connected-state contract records Gateway Jira, Gateway Wiki, and official Atlassian Cloud Jira as separate Source Instances and records official Cloud Confluence as unavailable until its app or authorization changes.
- Stable Source Instance registration is durable user-managed state in SQLite. Capability observations are stored separately as rebuildable runtime facts with policy version, observed schema fingerprint, checked time, availability, and bounded failure evidence.
- Provider-specific logical-read-to-tool mappings and forbidden-write classifications are version-controlled application policy. A database row, runtime manifest, model response, or user-supplied tool name cannot grant a capability that the application policy does not permit.
- A private in-memory or filesystem cache may accelerate reads, but it is not the authority for Source Instance identity, latest durable observation, or the read-only policy.
- The synchronization boundary uses an explicit read-tool allowlist. Mutating tools remain unreachable even when the underlying MCP backend or access token exposes create, update, comment, transition, assignment, link, or attachment operations.
- Prompt wording is not treated as read-only enforcement.
- Metadata-only Jira access uses field-selective search when available and does not default to a detail operation that returns comments or unrelated development data.
- Confluence catalog and hierarchy access excludes comments and attachments and requests Page bodies only through the content coverage selected by PRD-0007.
- Capability inspection is explicit and cached. It runs for Source Instance registration, a user-requested capability recheck, or recovery after an authorization/schema mismatch; it does not poll on application startup, page load, local search, or ordinary synchronization preview.
- Capability checks retain only tool/schema facts, availability, checked time, and bounded errors. They do not persist credentials, access tokens, private tool payloads, or sampled company content in tracked artifacts.
- Missing or changed capability fails closed for the affected Source Instance without changing another Instance or silently selecting a direct connector.

## Scope Boundary

- In:
  - Source Instance identity for each configured Atlassian access boundary
  - capability inventory and freshness contract
  - durable Source Instance registration versus rebuildable capability-observation ownership
  - version-controlled logical-operation and tool-policy ownership
  - read versus write classification
  - enforceable synchronization allowlist
  - metadata, body, hierarchy, pagination, version, and error capability flags
  - unavailable official Cloud Confluence state
  - fail-closed behavior when tool schemas or authorization change
  - explicit recheck and cached-observation behavior
  - synthetic or metadata-only contract verification
- Out:
  - external-source Run manifests and structured synchronization results owned by FEAT-0045
  - Atlassian Item persistence and freshness owned by FEAT-0046
  - ticket or Page content synchronization
  - installing or authorizing an unavailable Atlassian app
  - changing company MCP Gateway configuration
  - invoking, dry-running, or testing any external write operation
  - UI for Source registration, refresh, or search

## Surface Lanes

- Capability contract lane:
  - path roots: provider or capability modules under `src/localbrain/`, approved runtime configuration, and external-access owner documentation
  - dependencies: approved PRD-0007 and the bounded capability evidence already recorded there
  - expected evidence: stable Source Instance vocabulary, capability value shape, availability semantics, checked time, and fail-closed fallback
  - evaluator ownership: `contract`
- Read-only enforcement lane:
  - path roots: provider dispatch boundary, configuration validation, and synthetic tests under `tests/`
  - dependencies: capability contract lane
  - expected evidence: only allowlisted read operations can be dispatched and every write-shaped operation is rejected before external invocation
  - evaluator ownership: `contract`, `functional`

## Contract Surfaces

- Source Instance identity and provider-kind vocabulary.
- Capability manifest shape and freshness.
- Durable Source Instance registration and rebuildable observation boundary.
- Version-controlled logical operation, provider mapping, and policy version.
- Allowed read-operation categories and provider-specific tool mapping.
- Forbidden write-operation categories.
- Dispatch-time fail-closed validation.
- Authentication, unavailable, schema-drift, and unsupported-capability results.
- Runtime versus tracked-artifact privacy ownership.

## Required Evaluators

- `contract`: Source Instance identity, capability ownership, allowlist completeness, unavailable behavior, privacy boundary, and downstream readiness.
- `functional`: synthetic allowed-read dispatch, denied-write dispatch, stale schema, missing authorization, unavailable provider, and isolation between Source Instances.

## Entry And Exit

- Entry point: LocalBrain resolves a configured Source Instance or prepares an external-source operation that requires one or more capabilities.
- Exit or transition behavior: the capability boundary returns an approved read capability set or a bounded unavailable/unsupported result before any external call is attempted.

## State Expectations

- Default: a configured Instance has a current capability record and an explicit read allowlist.
- Unknown: an uninspected Instance exposes no synchronization tools until checked.
- Stale: an observed schema or authorization mismatch requires an explicit capability recheck before the affected operation can run again.
- Unavailable: the provider or service remains registered but cannot be selected for content operations.
- Error: capability inspection failure retains the last-known record as stale and does not broaden access.
- Success: downstream Features can select supported reads without seeing or invoking write tools.

## Dependencies

- PRD-0007 must remain `approved`.
- Connected provider configuration and authentication remain externally owned; this Feature records capability and policy without persisting credentials.

## Likely Affected Surfaces

- `src/localbrain/config.py`
- `src/localbrain/runner.py` or a provider-neutral external-access module selected by the Spec
- private runtime configuration and manifest validation
- `tests/test_runner.py` and new provider-policy contract tests
- `docs/policies/project/architecture.md`
- `docs/policies/project/privacy-and-data.md`
- external-access and maintenance owner documentation selected by the Spec

## Pass Or Fail Checks

- Pass if every configured Atlassian boundary has a stable Source Instance identity and explicit service availability.
- Pass if durable registrations, rebuildable observations, optional private cache, and version-controlled policy cannot overwrite or impersonate one another.
- Pass if currently connected Gateway Jira, Gateway Wiki, and official Cloud Jira reads are representable while unavailable Cloud Confluence remains explicit.
- Pass if field-selective metadata, selected content, Page hierarchy, pagination, version, and error capabilities have deterministic values or unsupported fallbacks.
- Pass if every write operation is rejected before dispatch regardless of prompt text or backend exposure.
- Pass if stale, unavailable, unauthorized, and schema-drift states cannot silently inherit broader permissions.
- Pass if application startup, browse, search, and refresh preview do not perform capability inspection and an explicit recheck can replace only the affected Instance's observation.
- Pass if tracked evidence contains only synthetic data and capability facts.
- Fail if downstream synchronization can call a backend tool by arbitrary name, if a write-capable tool remains reachable, or if one Source Instance's capability state leaks into another.

## Regression Surfaces

- Existing Claude maintenance Run preparation and MCP call accounting.
- Existing credentials and MCP configuration ownership outside LocalBrain content storage.
- Privacy checks and runtime-artifact exclusion.
- Non-Atlassian maintenance tasks and their current tool policy.

## Harness Trace

- Active spec doc: [spec-0044-mcp-capability-and-read-only-policy](../spec/spec-0044-mcp-capability-and-read-only-policy.md)
- Active run: [run-20260723-49-mcp-capability-and-read-only-policy](../run/run-20260723-49-mcp-capability-and-read-only-policy.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [Contract — PASS](../evaluation/eval-0044-contract-mcp-capability-and-read-only-policy.md), [Functional — PASS](../evaluation/eval-0044-functional-mcp-capability-and-read-only-policy.md)
- Latest fix note: not created

## Open Review Decisions

- None. The human owner confirmed the proposed persistence and policy ownership boundary on `2026-07-23`.

## Continuity Notes

- `2026-07-23`: initial draft split capability discovery and enforceable read-only policy from the provider-neutral synchronization Run so write-capable connected backends cannot leak into later product work.
- `2026-07-23`: bounded capability review confirmed mixed read/write Gateway catalogs, field-selective Jira search, bounded Wiki search/page/hierarchy reads, Jira-only availability on the official Cloud connection, and no current official Cloud Confluence access; no ticket or Page body was retrieved.
- `2026-07-23`: proposed split ownership between durable Source Instance registration, rebuildable SQLite capability observations, version-controlled read-only policy, and an optional non-authoritative private cache.
- `2026-07-23`: the human owner approved the boundary and started RUN-20260723-49; status advanced through approval to `in-loop`.
- `2026-07-23`: RUN-20260723-49 passed Contract and Functional evaluation with complete evidence; status advanced to `passed` with no fix loop.
