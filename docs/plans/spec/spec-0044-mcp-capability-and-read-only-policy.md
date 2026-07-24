# SPEC-0044: MCP Capability And Read-Only Policy

## Metadata

- ID: `spec-0044`
- Status: `approved`
- Run ID: `run-20260723-49`
- Attempt: `1`
- Parent Feature: [feat-0044-mcp-capability-and-read-only-policy](../feature/feat-0044-mcp-capability-and-read-only-policy.md)
- Parent PRD: [prd-0007-atlassian-source-memory-and-refresh](../prd/prd-0007-atlassian-source-memory-and-refresh.md)
- Surface: `infra`
- Execution Profile: `foundation-contract`
- Surface Lanes: persistence → policy and authorization → durable docs and generated schema
- Required Evaluators: `contract`, `functional`
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Source Set

- Human request and approval: approve FEAT-0044 and run it sequentially before later PRD-0007 Features.
- Parent Feature and PRD: FEAT-0044 and approved PRD-0007.
- Operational capability evidence: bounded Gateway Jira/Wiki tool catalogs and schemas plus official Atlassian accessible-resource metadata checked on `2026-07-23`; no ticket or Page body was retrieved.
- Implementation truth: `schema.sql`, compatible startup behavior in `db.py`, current `config.py` and `runner.py`, and existing schema-presentation generation.
- Durable contracts: Architecture, Privacy And Data Handling, Data Model, Source Registry And Scans, Maintenance Execution, and Claude Task Runner.

## Implementation Goal

- Add a local, provider-neutral Source Instance and capability-observation foundation whose static policy can authorize only known bounded Atlassian reads, rejects arbitrary or write-shaped dispatch before invocation, and performs no external call itself.

## In-Scope Behavior

1. Add `external_source_instances` as durable user-managed registration state:
   - stable integer ID and unique local `instance_key`
   - provider kind, service, display name, optional shape-validated external configuration reference, enabled state, and timestamps
   - provider/service identity cannot be changed by an idempotent re-registration
   - no credential, token, sampled content, or arbitrary opaque field; `config_ref` accepts only a Gateway alias or Atlassian Cloud ID
   - an unbound Instance may perform static capability inspection and bind a validated configuration reference once; binding invalidates an existing observation and a bound reference cannot be replaced
2. Add `external_source_capabilities` as one replaceable latest observation per Source Instance:
   - policy version, observed schema fingerprint, availability, canonical capability JSON, bounded error code and application-generated safe message, checked time, invalidated time, and updated time
   - physical cascade relation to the Source Instance
   - capability rows are rebuildable and cannot mutate Source Instance identity
3. Add a version-controlled policy registry for the supported provider/service pairs:
   - Gateway Jira
   - Gateway Confluence/Wiki
   - official Atlassian Cloud Jira
   - official Atlassian Cloud Confluence
4. Map logical read operations to exact provider targets:
   - Jira field-selective metadata and selected description reads
   - Jira project metadata where supported
   - Confluence regular-Page search, Page body read, and child hierarchy where supported
   - official accessible-resource inspection as a capability-check operation
5. Validate provider-specific arguments before returning a dispatch:
   - reject arbitrary tool names and methods
   - reject Jira comment, worklog, attachment, and development queries or fields, unrestricted fields, and write-shaped fields
   - reject Confluence comment, attachment, blog, and unrestricted body expansion
   - enforce bounded page sizes and regular-Page CQL for catalog search
6. Authorize only the intersection of:
   - enabled registered Source Instance
   - current matching policy version
   - available, non-invalidated observation
   - observed logical operation
   - statically known read policy
7. Represent unknown, stale, unavailable, unauthorized, and error states without broadening access.
8. Provide explicit registration, observation recording, invalidation, state lookup, and authorization functions for later Features. This Feature launches no MCP, model, or maintenance Run itself.
9. Update durable schema ownership, global Data Model counts and relationships, Architecture/privacy contracts, deterministic schema presentation, and synthetic tests in the same change.

## Out-Of-Scope Behavior

- Calling Gateway or official Atlassian tools from LocalBrain.
- Persisting the current user's company Source Instances in tracked files or synthetic fixtures.
- Credentials, OAuth tokens, company domains, cloud IDs, private tool payloads, tickets, or Pages.
- FEAT-0045 external synchronization manifests and runner execution.
- FEAT-0046 Atlassian Item identity, content, freshness, evidence, or FTS.
- Source Instance registration UI, Space selection, refresh controls, or search.
- Background capability polling, startup inspection, page-load inspection, or automatic retry.
- Any external write invocation, including write-tool dry runs.

## Affected Surfaces

- `src/localbrain/schema.sql`
- `src/localbrain/db.py`
- new `src/localbrain/external_access.py`
- new `tests/test_external_access.py`
- schema-upgrade tests
- `docs/policies/project/architecture.md`
- `docs/policies/project/privacy-and-data.md`
- `docs/policies/project/data-model.md`
- `docs/policies/project/data-model/source-registry-and-scans.md`
- `scripts/check-data-model-docs.py`
- deterministic schema-presentation artifacts and checks

## Surface Lanes

- Persistence lane:
  - path roots: schema, compatible startup, Source Registry And Scans ownership, schema tests
  - dependency order: first
  - implementation responsibility: stable registrations, replaceable observations, constraints, FK, lifecycle and recovery
  - validation evidence: fresh and upgraded SQLite shapes, idempotency, cascade, integrity, owner-doc parity
- Policy and authorization lane:
  - path roots: `external_access.py` and focused tests
  - dependency order: after persistence contract
  - implementation responsibility: versioned provider policy, logical operations, argument validation, state projection, fail-closed dispatch construction
  - validation evidence: allowed reads, denied writes/arbitrary targets, stale/unavailable/disabled isolation, no external invocation
- Durable docs and generated schema lane:
  - path roots: architecture/privacy/data-model owners, schema-presentation generator and package
  - dependency order: after effective schema and policy behavior stabilize
  - implementation responsibility: one current source of truth and deterministic generated consumer parity
  - validation evidence: data-model, generated-schema, link, privacy, and stale-assumption checks

## State And Interaction Contract

- `unknown`: no capability observation; authorize nothing.
- `current`: matching policy version, available, non-invalidated observation; authorize only observed static reads.
- `stale`: policy mismatch or invalidated observation; authorize nothing until explicit replacement.
- `unavailable`: service cannot be used; retain registration and observation evidence, authorize nothing.
- `unauthorized`: provider authentication or scope is absent; authorize nothing.
- `error`: bounded inspection failure; retain registration, authorize nothing.
- Disabled Source Instances authorize nothing without deleting observations.
- No function in this Feature performs network, MCP, model, filesystem-cache, or background work.

## Data And Contract Assumptions

- `instance_key`, provider kind, service, and external configuration reference form local registration identity; later Site and remote Item identity remain FEAT-0046 concerns.
- Registration is non-rebuildable user-managed state. Capability observation is rebuildable operational state.
- Static application policy is the sole authority that can turn a logical operation into a dispatch target.
- Capability JSON may remove observed support but cannot add a target absent from static policy.
- Error codes are bounded identifiers and messages are generated from availability by application policy; raw provider error text, payloads, and credentials are not accepted.
- The schema uses synthetic values only in tests and docs.

## Contract Surfaces

- Producer expectations:
  - registration callers provide stable non-secret local identity
  - later capability inspectors provide canonical logical operations and schema fingerprint
  - later runners request a logical operation, never an arbitrary provider tool name
- Consumer expectations:
  - FEAT-0045 consumes a validated dispatch descriptor or a typed fail-closed exception
  - FEAT-0046 consumes stable Source Instance IDs without depending on capability-row lifetime
- Generated artifacts:
  - schema presentation is regenerated only from fresh in-memory schema and owner docs
- Source-of-truth owner:
  - DDL in `schema.sql`; compatible startup in `db.py`; static policy in `external_access.py`; semantic ownership in Source Registry And Scans and Architecture/privacy docs
- Stale-assumption check:
  - scan Runner, configuration, source adapters, Data Model counts/ERDs/checks, schema-presentation artifacts, and existing external-resource behavior for assumptions invalidated by the two new tables

## Required Evaluators

- Contract:
  - schema ownership, lifecycle, provider policy, operation/target mapping, argument constraints, fail-closed intersection, generated parity, and downstream readiness
- Design:
  - not applicable
- Functional:
  - registration, observation, invalidation, allowed reads, denied writes/arbitrary requests, isolation, compatibility, and regression tests
- UX heuristic:
  - not applicable

## Acceptance Mapping

- Stable Source Instance and separate observation ownership → tables, service functions, schema/owner docs, fresh and compatible tests.
- Explicit read allowlist and unreachable writes → immutable policy registry, logical-operation-only API, provider argument validators, denial tests.
- Jira and Confluence bounded reads → provider-specific synthetic capability and authorization tests.
- Current Gateway/official connection shapes → all four provider/service policy pairs are representable; unavailable official Confluence is a supported state.
- Cached explicit inspection policy → observation lookup/invalidation functions and explicit no-network module boundary.
- Privacy and isolation → no secret/content columns, bounded errors, synthetic fixtures, per-instance FK/state tests.
- Downstream readiness → typed validated dispatch consumed later by FEAT-0045.

## Evaluation Focus

- Confirm no observation or caller input can invent a provider target or authorize a write.
- Confirm Gateway nested dispatch validates exact method and backend target.
- Confirm official direct targets remain exact and provider-specific.
- Confirm metadata/content argument paths exclude comments and other over-broad fields.
- Confirm stale, unavailable, unauthorized, error, disabled, and cross-instance states fail closed.
- Confirm existing External Resources and maintenance execution remain unchanged.
- Confirm every schema owner, count, relationship, digest, and generated artifact is current.

## Open Blockers

- None. The human owner approved the persistence/policy split and started the Run.

## Continuity Notes

- `2026-07-23`: Spec approved for RUN-20260723-49 after bounded operational capability review and explicit human Feature approval.
