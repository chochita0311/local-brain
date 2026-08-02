# FEAT-0062: Atlassian Local Site And Access-Binding Contract

## Metadata

- ID: `feat-0062`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [prd-0010-atlassian-ui-and-interaction-reconciliation](../prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
- Created: `2026-07-27`
- Updated: `2026-07-27`

## Goal

- Make normalized domain the Site identity and make MCP access an optional
  explicit binding so local-only Atlassian records require no Provider.

## Acceptance Contract

- A Site can exist without a Source Instance, Provider, reference, capability,
  or remote read.
- Site bindings relate a Site to one existing Source Instance and preserve that
  instance's Provider, Jira/Confluence service, reference, enabled state, and
  capability evidence.
- Existing Site/Source relationships become bindings without losing registered
  Items, Spaces, URLs, local state, remote state/content, evidence, or
  Workstream/Thread/checkpoint relations.
- Local Item and Space records keep their service and may have no usable access
  binding.
- Generated connection display values remain compatibility projections, not
  user-managed identity.
- Fresh and compatible databases expose the same effective contract.

## Scope Boundary

- In:
  - Site and binding schema, compatible migration, identity operations, and
    access resolution
  - URL-derived Site and bootstrap-title helpers
  - current registration, browse, evidence, discovery, and refresh consumers
  - Data Model and architecture ownership
  - focused migration and contract tests
- Out:
  - visible Add composition and form-copy changes
  - product-wide select styling
  - new remote writes or automatic remote reads
  - interactive selection among several equivalent same-service bindings

## Surface Lanes

- Schema lane:
  - path roots: `src/localbrain/schema.sql`, `src/localbrain/db.py`
  - dependencies: current Source Instance and Atlassian identity contracts
  - expected evidence: fresh/compatible parity and retained row relationships
  - evaluator ownership: `contract`
- Domain lane:
  - path roots: `src/localbrain/atlassian*.py`
  - dependencies: schema lane
  - expected evidence: zero-binding local registration and deterministic
    compatible binding resolution
  - evaluator ownership: `contract`, `functional`
- Documentation lane:
  - path roots: `docs/policies/project/`
  - dependencies: fixed schema and domain behavior
  - expected evidence: identity, lifecycle, deletion, and recovery parity
  - evaluator ownership: `contract`

## Contract Surfaces

- `atlassian_sites`, `atlassian_site_bindings`, Source Instance references on
  Item/Space access ownership, registration APIs, refresh target resolution,
  migration and generated Schema Presentation.

## Dependencies

- PRD-0010 is approved.
- FEAT-0063 cannot enter build until this Feature passes.

## Pass Or Fail Checks

- Pass if a URL creates/reuses Site and Item/Space with zero Source Instances.
- Pass if adding access creates a binding without changing Site identity.
- Pass if existing access, local/remote state, and relations survive migration.
- Pass if Jira and Confluence records can share one normalized-domain Site.
- Fail if local-only registration creates a placeholder Provider or binding.

## Regression Surfaces

- PRD-0007 Atlassian identity, evidence, browse, search, and refresh.
- PRD-0008 connected discovery and registered-scope behavior.
- Fresh schema, compatible startup migration, Schema Presentation, and privacy.

## Harness Trace

- Active spec doc: [spec-0062-atlassian-local-site-and-access-binding-contract](../spec/spec-0062-atlassian-local-site-and-access-binding-contract.md)
- Active run: [run-20260727-67-atlassian-local-site-and-access-binding-contract](../run/run-20260727-67-atlassian-local-site-and-access-binding-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract](../evaluation/eval-0062-contract-atlassian-local-site-and-access-binding-contract.md), [functional](../evaluation/eval-0062-functional-atlassian-local-site-and-access-binding-contract.md)
- Latest fix note: not required

## Continuity Notes

- `2026-07-27`: owner approved sequential implementation through the current
  PRD boundary; this Foundation Feature entered the first loop.
- `2026-07-27`: passed after fresh/compatible schema parity, backup-backed
  retained-row migration, zero-binding local registration, explicit access
  resolution, local evidence, generated-schema parity, and regressions.
