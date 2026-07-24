# EVAL-0044: MCP Capability And Read-Only Policy — Contract

## Metadata

- ID: `eval-0044-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260723-49`
- Attempt: `1`
- Feature: [feat-0044-mcp-capability-and-read-only-policy](../feature/feat-0044-mcp-capability-and-read-only-policy.md)
- Spec: [spec-0044-mcp-capability-and-read-only-policy](../spec/spec-0044-mcp-capability-and-read-only-policy.md)
- Execution Profile: `foundation-contract`
- Surface Lane: persistence → policy and authorization → durable docs and generated schema
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated stable Source Instance registration, replaceable capability observation, the version-controlled provider policy, logical-operation authorization, provider argument construction, generated schema ownership, and the FEAT-0045 consumer boundary.

## Checks And Evidence

- Fresh DDL creates `external_source_instances` as durable registration state and `external_source_capabilities` as one replaceable observation per Instance with a physical cascading relation. Normal startup adds both tables without rewriting an existing External Resource.
- The policy registry represents Gateway Jira, Gateway Confluence, official Atlassian Cloud Jira, and official Atlassian Cloud Confluence independently. It contains only known read and capability-inspection operations.
- Gateway data reads return a validated nested `tools/call` descriptor with an exact backend target. Official connector reads return exact direct-tool descriptors. Callers provide a logical operation and cannot supply a provider tool or method.
- Data reads require an enabled Instance, a current matching policy version, a valid schema fingerprint, an available non-invalidated observation, an observed operation, and a matching static policy entry. Unknown, stale, unavailable, unauthorized, error, disabled, malformed, and unobserved states fail closed.
- Capability inspection can bootstrap an enabled unknown or stale Instance through static discovery operations, but it does not grant source-data reads. The module constructs descriptors and performs no MCP, network, model, background, or filesystem-cache call.
- Jira fields and JQL exclude comments, worklogs, attachments, and development data. Confluence CQL is constrained to regular Pages and fixed expansions omit comments and attachments.
- `config_ref` accepts only a bounded Gateway alias or canonical Atlassian Cloud ID. An unbound Instance can inspect static capabilities and bind once; binding stales any earlier observation, and registration, binding, and dispatch validate the value so a site URL or direct database corruption cannot become a `cloudId` argument.
- Capability payloads are canonical operation lists only. Available observations require a SHA-256 schema fingerprint; raw provider payloads and messages are not accepted, and failure evidence is reduced to a bounded code plus application-generated safe text.
- Data Model ownership is current at 22 ordinary tables plus one FTS5 object, 21 physical foreign keys, 20 explicit indexes, eight subject owners, and 263 columns. The deterministic schema presentation digest and 350-object cleanup ledger agree.

## Evidence

- Environments checked: source inspection, fresh in-memory SQLite, temporary file-backed compatible startup, deterministic generated schema, synthetic provider-policy fixtures, and repository owner documentation.
- No ticket or Page body was retrieved. Connected capability shape had already been bounded before implementation; this evaluator exercised only local synthetic descriptors and state.

## Evidence Gaps

- None. Live provider invocation is intentionally outside FEAT-0044; FEAT-0045 consumes the validated descriptor and owns execution evidence.

## Contract Evidence

- Producer surfaces: `schema.sql`, Source Instance registration, capability observation recording and invalidation, static policy, and dispatch authorization in `external_access.py`.
- Consumer surfaces: FEAT-0045 external synchronization execution and FEAT-0046 stable Source Instance references.
- Schemas, payloads, generated artifacts, commands, routes, config, or policy docs checked: SQLite DDL, canonical capability JSON, `ToolDispatch`, Architecture, Privacy And Data Handling, Data Model, Source Registry And Scans, schema-presentation JSON, and cleanup audit.
- Stale-assumption check: current Runner, configuration, External Resource persistence, maintenance exclusion, Data Model counts, and generated consumers remain compatible. No existing path bypasses or invokes the new policy module.

## Findings

- None.

## Regression Notes

- Existing External Resources, maintenance Runs, application startup, and non-Atlassian behavior remain unchanged. The two new tables are additive and the policy module has no autonomous execution path.

## Route

- Next action: `pass` and run Functional evaluation.
